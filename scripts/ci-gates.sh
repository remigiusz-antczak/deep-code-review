#!/usr/bin/env bash
#
# ci-gates.sh — production helper enforcing this repo's documented gates.
#
# scripts/test-ci-gates.sh pins this contract; keep the two in sync. Every
# subcommand FAILS CLOSED: a missing input, an empty policy, or a real violation
# exits non-zero. There is deliberately no `|| true`, no always-success
# fallback, and no pipeline that swallows the exit status of the real work — the
# caller (CI, or the harness) sees the true result.
#
# Subcommands:
#   privacy --banlist <file> <path...>   scan paths for banned patterns (files only, never content)
#   routing [--max-bytes N] <skill-dir>  every references/*.md routed from SKILL.md; SKILL.md over N bytes FAILS (reasoned allowlist)
#   version <root>                       VERSION is byte-exact ASCII core semver; first CHANGELOG heading announces it
#   install --src <dir> --dest <dir> --mode <claude|minimal|full|codex|overlays|recommend>
#                                        run the real installer, then verify vendored docs are real (not placeholders)
#   enumeration <root>                   every shipped skill is present in all five hand-maintained lists
#
set -euo pipefail

die() { printf 'ci-gates: %s\n' "$*" >&2; exit 1; }

# collect_patterns <file> — append each actionable banlist pattern (non-blank
# line whose first non-space char is not '#') from <file> to the caller's
# `patterns` array. Bash's dynamic scoping makes that caller-local array visible
# here, so both the committed primary banlist and its optional sibling local
# override funnel through one collector.
collect_patterns() {
  local _line _trimmed
  while IFS= read -r _line || [ -n "$_line" ]; do
    _trimmed="${_line#"${_line%%[![:space:]]*}"}"   # strip leading whitespace
    case "$_trimmed" in
      ''|'#'*) continue ;;
    esac
    patterns+=("$_trimmed")
  done < "$1"
}

usage() {
  cat >&2 <<'EOF'
ci-gates.sh — enforce the deep-code-review repo's documented gates.

Usage:
  ci-gates.sh privacy --banlist <file> <path...>
  ci-gates.sh routing [--max-bytes N] <skill-dir>
  ci-gates.sh version <root>
  ci-gates.sh install --src <dir> --dest <dir> --mode <claude|minimal|full|codex|overlays|recommend>
  ci-gates.sh enumeration <root>
EOF
}

# ---------------------------------------------------------------------------
# privacy — banned-term hygiene + secret detection.
#
# Fails closed unless the banlist exists AND holds at least one actionable
# (non-blank, non-comment) pattern; a comments-only or empty policy is treated
# as "no policy", not "nothing banned". Reports matching FILE NAMES only, never
# the matched content, so a real secret is never echoed into a log.
# ---------------------------------------------------------------------------
cmd_privacy() {
  local banlist=""
  local -a targets=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --banlist) banlist="${2:-}"; shift 2 ;;
      --banlist=*) banlist="${1#*=}"; shift ;;
      --) shift; while [ "$#" -gt 0 ]; do targets+=("$1"); shift; done ;;
      -*) die "privacy: unknown option: $1" ;;
      *) targets+=("$1"); shift ;;
    esac
  done

  [ -n "$banlist" ] || die "privacy: --banlist <file> is required (fail closed)"
  [ -f "$banlist" ] || die "privacy: banlist not found: $banlist (fail closed)"
  [ "${#targets[@]}" -gt 0 ] || die "privacy: at least one scan path is required (fail closed)"

  # The committed primary banlist supplies the baseline policy and must, as
  # before, hold at least one actionable (non-blank, non-comment) pattern.
  local -a patterns=()
  collect_patterns "$banlist"
  [ "${#patterns[@]}" -gt 0 ] \
    || die "privacy: banlist has no actionable patterns (only blanks/comments): $banlist"

  local banlist_base
  banlist_base="$(basename "$banlist")"
  local -a exclude_args=( --exclude="$banlist_base" )

  # Optional sibling local override: insert '.local' before the primary's
  # extension (.banlist.txt -> .banlist.local.txt). Missing is normal; a present
  # sibling extends the committed policy for this run only. Its actionable
  # patterns join the scan set (an empty/comment-only sibling contributes
  # nothing), its EREs are validated on the same fail-closed, content-withheld
  # footing below, and its basename is excluded from the recursive scan so it
  # can never match itself.
  local banlist_local banlist_local_base
  banlist_local="${banlist%.*}.local.${banlist##*.}"
  if [ -f "$banlist_local" ]; then
    collect_patterns "$banlist_local"
    banlist_local_base="$(basename "$banlist_local")"
    exclude_args+=( --exclude="$banlist_local_base" )
  fi

  # Fail closed on a malformed policy: every actionable pattern must be a valid
  # ERE. Probe each against empty input BEFORE scanning so we can tell grep
  # exit 1 (valid pattern, simply no match) apart from exit 2 (invalid regex).
  local pat probe_status
  for pat in "${patterns[@]}"; do
    printf '' | grep -qE -e "$pat" 2>/dev/null && probe_status=0 || probe_status=$?
    [ "$probe_status" -le 1 ] \
      || die "privacy: a banlist pattern is not a valid ERE (content withheld); failing closed"
  done

  local hit=0 files status
  for pat in "${patterns[@]}"; do
    # -l: report file names only. -I: skip binaries. `--` guards dash-leading
    # target paths from being read as options. Capture grep's exit status
    # explicitly: 0 = matches, 1 = clean, anything else = gate error (no
    # always-success fallback, so a broken scan fails closed).
    files="$(grep -rIlE --exclude-dir=.git "${exclude_args[@]}" -e "$pat" -- "${targets[@]}" 2>/dev/null)" \
      && status=0 || status=$?
    case "$status" in
      0)
        printf 'BLOCK: a banned pattern matched (content withheld); files:\n' >&2
        printf '%s\n' "$files" | sed 's/^/  /' >&2
        hit=1 ;;
      1) : ;;  # clean: this pattern matched nothing
      *) die "privacy: grep failed while scanning (exit $status); failing closed" ;;
    esac
  done

  [ "$hit" -eq 0 ] || die "privacy: banned pattern(s) present (see files above)"
  printf 'privacy: clean (%d pattern(s) scanned)\n' "${#patterns[@]}"
}

# ---------------------------------------------------------------------------
# routing — progressive disclosure integrity.
#
# Every references/*.md must be routed by basename from SKILL.md, and every
# route named in SKILL.md must resolve to a file. An oversized SKILL.md FAILS the
# gate against the documented byte budget, unless it is on the reasoned size
# allowlist (a justified, comment-explained overage); broken routing always fails.
# ---------------------------------------------------------------------------
cmd_routing() {
  local max_bytes=""
  local -a dirs=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --max-bytes) max_bytes="${2:-}"; shift 2 ;;
      --max-bytes=*) max_bytes="${1#*=}"; shift ;;
      -*) die "routing: unknown option: $1" ;;
      *) dirs+=("$1"); shift ;;
    esac
  done

  [ "${#dirs[@]}" -eq 1 ] || die "routing: exactly one skill directory is required"
  local skill_dir="${dirs[0]}"
  local skill_md="$skill_dir/SKILL.md"
  [ -f "$skill_md" ] || die "routing: SKILL.md not found: $skill_md (fail closed)"

  local fail=0 f base p
  # 1) Every reference file is routed from SKILL.md.
  if [ -d "$skill_dir/references" ]; then
    for f in "$skill_dir"/references/*.md; do
      [ -e "$f" ] || continue   # nullglob-safe: skip the literal when no matches
      base="$(basename "$f")"
      # Fixed-string (-F) so a literal '.' in the basename matches only a dot;
      # a regex match would let 'literal.md' spuriously match 'literalXmd'.
      if ! grep -qF -e "$base" -- "$skill_md"; then
        printf 'UNROUTED: references/%s\n' "$base" >&2
        fail=1
      fi
    done
  fi

  # 2) Every route named in SKILL.md resolves to a file.
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    if [ ! -f "$skill_dir/$p" ]; then
      printf 'DANGLING ROUTE: %s\n' "$p" >&2
      fail=1
    fi
  done < <(grep -oE 'references/[A-Za-z0-9._-]+\.md' "$skill_md" | sort -u)

  # 3) Size budget — FAILS on bloat (the ratchet has teeth), except a small
  #    reasoned allowlist of skills whose size is justified. A pin is ALLOWED its
  #    overage, never required to keep it: an allowlisted skill that slims back
  #    under budget simply passes here.
  if [ -n "$max_bytes" ]; then
    local size
    size="$(wc -c < "$skill_md" | tr -d '[:space:]')"
    if [ "$size" -gt "$max_bytes" ]; then
      case "$(basename "$skill_dir")" in
        agentic-delivery)
          # The full gated G0–G10 delivery OS plus the software-house role overlay —
          # the largest SKILL.md by design. Trimming depth into references/ later is
          # welcome but not required. (ratchet allowlist)
          printf 'SIZE ALLOWED: %s SKILL.md is %s bytes (over %s-byte budget) — allowlisted\n' \
            "$(basename "$skill_dir")" "$size" "$max_bytes" >&2 ;;
        *)
          printf 'SIZE FAIL: %s SKILL.md is %s bytes (exceeds %s-byte budget)\n' \
            "$(basename "$skill_dir")" "$size" "$max_bytes" >&2
          fail=1 ;;
      esac
    fi
  fi

  [ "$fail" -eq 0 ] || die "routing: unrouted and/or dangling references present"
  printf 'routing: ok\n'
}

# ---------------------------------------------------------------------------
# version — VERSION is byte-exact ASCII core semver; first CHANGELOG heading announces it.
#
# Accepts a flat fixture root (<root>/VERSION) or the real repo, where VERSION
# lives nested in the skill and CHANGELOG.md sits at the repo root.
# ---------------------------------------------------------------------------
cmd_version() {
  local -a roots=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -*) die "version: unknown option: $1" ;;
      *) roots+=("$1"); shift ;;
    esac
  done
  [ "${#roots[@]}" -eq 1 ] || die "version: exactly one root directory is required"
  local root="${roots[0]}"

  # Prefer the real nested skill VERSION; fall back to a flat fixture root.
  local version_file=""
  if [ -f "$root/.claude/skills/deep-code-review/VERSION" ]; then
    version_file="$root/.claude/skills/deep-code-review/VERSION"
  elif [ -f "$root/VERSION" ]; then
    version_file="$root/VERSION"
  else
    die "version: no VERSION file found under $root (fail closed)"
  fi

  local changelog="$root/CHANGELOG.md"
  [ -f "$changelog" ] || die "version: no CHANGELOG.md under $root (fail closed)"

  # Validate raw bytes before converting them to a shell string. Bash command
  # substitution cannot carry NUL; the hexadecimal representation can. This
  # permits only ASCII core SemVer with no leading zero in any multi-digit part,
  # plus one optional terminal LF. No normalization is performed.
  local version_hex
  version_hex="$(LC_ALL=C od -An -v -tx1 "$version_file" | tr -d '[:space:]')"
  [[ "$version_hex" =~ ^(30|3[1-9](3[0-9])*)2e(30|3[1-9](3[0-9])*)2e(30|3[1-9](3[0-9])*)(0a)?$ ]] \
    || die "version: VERSION must be byte-exact ASCII core semver with optional final LF"

  # Safe only after raw-byte validation above: the input cannot contain NUL,
  # whitespace except an optional terminal LF, or more than one line.
  local ver
  ver="$(LC_ALL=C tr -d '\n' < "$version_file")"
  printf 'VERSION=%s (from %s)\n' "$ver" "$version_file"

  # The current release must be the first release heading. Searching later
  # headings would allow stale changelog ordering to pass provenance checks.
  local first_heading
  first_heading="$(LC_ALL=C grep -m1 '^## ' "$changelog" || true)"
  [ -n "$first_heading" ] || die "version: CHANGELOG has no release heading"
  case "$first_heading" in
    "## $ver"|"## $ver "*|"## [$ver]"|"## [$ver] "*) ;;
    *) die "version: first CHANGELOG release heading does not announce $ver" ;;
  esac

  printf 'version: ok (%s announced in CHANGELOG)\n' "$ver"
}

# ---------------------------------------------------------------------------
# install — drive the real installer and verify what it vendored.
#
# Calls the repo's own install.sh (never a reimplementation), then checks that
# the docs the skill cites were copied in as their REAL content, not left as a
# preexisting placeholder. Fails closed if either docs source or installed copy
# is missing or mismatched.
# ---------------------------------------------------------------------------
cmd_install() {
  local src="" dest="" mode=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --src) src="${2:-}"; shift 2 ;;
      --src=*) src="${1#*=}"; shift ;;
      --dest) dest="${2:-}"; shift 2 ;;
      --dest=*) dest="${1#*=}"; shift ;;
      --mode) mode="${2:-}"; shift 2 ;;
      --mode=*) mode="${1#*=}"; shift ;;
      -*) die "install: unknown option: $1" ;;
      *) die "install: unexpected argument: $1" ;;
    esac
  done

  [ -n "$src" ]  || die "install: --src <dir> is required"
  [ -n "$dest" ] || die "install: --dest <dir> is required"
  [ -n "$mode" ] || die "install: --mode <claude|minimal|full|codex|overlays|recommend> is required"
  [ -d "$src" ]  || die "install: --src not found: $src"
  [ -d "$dest" ] || die "install: --dest not found: $dest"

  local installer="$src/install.sh"
  [ -f "$installer" ] || die "install: real installer not found: $installer"

  local -a mode_flags=()
  case "$mode" in
    claude)       mode_flags=(--claude-only) ;;
    minimal)      mode_flags=(--minimal) ;;
    codex)        mode_flags=(--with-codex) ;;   # multi-path plus codex adapter
    full|default) : ;;   # agent-agnostic multi-path default (review only)
    overlays)     mode_flags=(--full) ;;         # review + delivery + critic
    recommend)    mode_flags=(--recommend) ;;    # inspect only; no writes
    *) die "install: unsupported mode: $mode (want claude|minimal|full|codex|overlays|recommend)" ;;
  esac

  # Run the REAL installer; set -e preserves its exit code (no || true).
  bash "$installer" ${mode_flags[@]+"${mode_flags[@]}"} "$dest"

  if [ "$mode" = "recommend" ]; then
    # Recommend must not create skill trees or AGENTS.md.
    if [ -e "$dest/.claude" ] || [ -e "$dest/AGENTS.md" ]; then
      die "install: --recommend wrote to the destination (must be read-only)"
    fi
    printf 'install: ok (recommend mode; no writes)\n'
    return 0
  fi

  # Postcondition: the installer vendors the repo's docs into the installed
  # skill's references/, and the result is the real content (not a placeholder).
  local skill_rel=".claude/skills/deep-code-review"
  local -a pairs=(
    "docs/standards-index.md:${skill_rel}/references/standards-index.md"
    "docs/example-review-report.md:${skill_rel}/references/example-review-report.md"
  )
  local pair srcdoc inst
  for pair in "${pairs[@]}"; do
    srcdoc="$src/${pair%%:*}"
    inst="$dest/${pair##*:}"
    [ -f "$srcdoc" ] || die "install: docs source missing in --src: $srcdoc"
    [ -f "$inst" ]   || die "install: installed reference missing: $inst"
    ! grep -q 'PLACEHOLDER' "$inst" \
      || die "install: installed reference is still a placeholder: $inst"
    cmp -s "$inst" "$srcdoc" \
      || die "install: installed reference does not equal docs source: $inst"
  done

  if [ "$mode" = "overlays" ]; then
    [ -f "$dest/.claude/skills/agentic-delivery/SKILL.md" ] \
      || die "install: overlays mode missing agentic-delivery"
    [ -f "$dest/.claude/skills/idea-critic/SKILL.md" ] \
      || die "install: overlays mode missing idea-critic"
  else
    # Default review-only modes must not dump overlays.
    if [ -e "$dest/.claude/skills/agentic-delivery" ] \
      || [ -e "$dest/.claude/skills/idea-critic" ]; then
      die "install: review-only mode installed an overlay skill"
    fi
  fi

  printf 'install: ok (%s mode; docs vendored and verified)\n' "$mode"
}

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# enumeration — every shipped skill is present in every hand-maintained list.
#
# Catches the drift class that shipped despite green CI: a new skill missing from
# agentic-ceo's registry (unroutable), from install.sh (uninstallable), from the
# ci.yml routing lines (ungated), from the checksum find-list (unpinned), or from
# recommend-overlays.py (mis-classified). These lists are hand-enumerated, so the
# globbed self-tests cannot see a gap. Fail closed. Directional: it catches a skill
# on disk that is missing from a list, not a stale list entry for a deleted skill.
# ---------------------------------------------------------------------------
cmd_enumeration() {
  local root="."
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -*) die "enumeration: unknown option: $1" ;;
      *) root="$1"; shift ;;
    esac
  done
  local skills_dir="$root/.claude/skills"
  [ -d "$skills_dir" ] || die "enumeration: no skills dir at $skills_dir (fail closed)"
  local ci="$root/.github/workflows/ci.yml"
  local checksums="$root/scripts/write-checksums.sh"
  local installer="$root/install.sh"
  local registry="$skills_dir/agentic-ceo/SKILL.md"
  local recommend="$root/scripts/recommend-overlays.py"
  local f
  for f in "$ci" "$checksums" "$installer" "$registry" "$recommend"; do
    [ -f "$f" ] || die "enumeration: missing required file: $f (fail closed)"
  done

  local bt='`'
  local fail=0 d name
  for d in "$skills_dir"/*/; do
    [ -d "$d" ] || continue
    name="$(basename "$d")"
    # 1) ci.yml routing INVOCATION (per-skill; enumerated, not globbed). Anchored to
    #    the `ci-gates.sh routing` call so a bare mention (a comment) cannot satisfy it.
    grep -qE "ci-gates\.sh routing .*\.claude/skills/${name}[[:space:]]*\$" "$ci" \
      || { printf 'ENUM: %s has no ci.yml routing line\n' "$name" >&2; fail=1; }
    # 2) write-checksums.sh find-list (else the skill tree is unpinned). The path
    #    followed by whitespace matches the `find` argument list; write-checksums.sh
    #    holds no other skill paths, so a bare-mention false-PASS has no vector here.
    grep -qE "\.claude/skills/${name}[[:space:]]" "$checksums" \
      || { printf 'ENUM: %s absent from write-checksums.sh find-list\n' "$name" >&2; fail=1; }
    # 3) install.sh — the base ships always; every overlay needs a SKILLS+= line
    if [ "$name" != "deep-code-review" ]; then
      grep -qF "SKILLS+=(\"${name}\")" "$installer" \
        || { printf 'ENUM: %s has no install.sh SKILLS+= line\n' "$name" >&2; fail=1; }
    fi
    # 4) agentic-ceo registry — a table ROW (^| `name` |...), not merely prose. Tolerates
    #    any cell padding before the closing pipe so a table reformat is not a false FAIL.
    if [ "$name" != "agentic-ceo" ]; then
      grep -qE "^\| ${bt}${name}${bt}[[:space:]]*\|" "$registry" \
        || { printf 'ENUM: %s has no agentic-ceo registry row\n' "$name" >&2; fail=1; }
    fi
    # 5) recommend-overlays.py knows the skill (else it mis-classifies at --recommend).
    #    Quoted set-literal form so a name is not a substring false-match ("critic" is
    #    not a substring of "idea-critic").
    grep -qF "\"${name}\"" "$recommend" \
      || { printf 'ENUM: %s not named in recommend-overlays.py\n' "$name" >&2; fail=1; }
  done

  [ "$fail" -eq 0 ] || die "enumeration: one or more skills are not fully enumerated"
  printf 'enumeration: ok\n'
}

[ "$#" -gt 0 ] || { usage; exit 2; }
subcmd="$1"; shift
case "$subcmd" in
  privacy) cmd_privacy "$@" ;;
  routing) cmd_routing "$@" ;;
  version) cmd_version "$@" ;;
  install) cmd_install "$@" ;;
  enumeration) cmd_enumeration "$@" ;;
  -h|--help) usage; exit 0 ;;
  *) printf 'ci-gates: unknown subcommand: %s\n' "$subcmd" >&2; usage; exit 2 ;;
esac
