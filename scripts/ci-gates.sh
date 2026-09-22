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
#   size --config <file> <root>          every shipped SKILL.md/references/*.md is within its frozen size-budgets.tsv byte budget
#   size-ratchet --base <ref> --config <file> <root>
#                                        no size-budgets.tsv row may increase vs <ref> without a `size-budget-raise:` marker (fail closed on unresolvable base)
#   binaries <root>                      no git-tracked file at a banned image/media/archive/build-output extension (allowlist: scripts/binaries-allowlist.tsv)
#   mustload --config <file> <root>      every SKILL.md load-map archetype's MUST-LOAD token-est total is within its frozen mustload-budgets.tsv ceiling
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
  ci-gates.sh size --config <file> <root>
  ci-gates.sh size-ratchet --base <ref> --config <file> <root>
  ci-gates.sh binaries <root>
  ci-gates.sh mustload --config <file> <root>
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
  local fail=0 d name sver fmver fmline has_skill has_ver vname
  # check #7 allowlist: the skills whose SKILL.md enumerates EVERY eval id.
  local verif_enum="business-ops contribution growth-analytics positioning product-discovery product-output-safety"
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
    # 6) A skill dir must carry BOTH a SKILL.md and a VERSION, and the SKILL.md
    #    frontmatter metadata.version must equal that VERSION. Fail closed: nothing
    #    reads the stamp at runtime, so without this check a drift — or a missing
    #    VERSION — is invisible to every other gate (the stamp slid on the lockstep
    #    skills for seven releases, v1.101.0–v1.107.0, before it existed). The stamp
    #    is read as metadata.version — the version: key inside the frontmatter
    #    metadata: block — so neither a body line nor a description block-scalar
    #    version: can satisfy it. A dir under skills/ with NEITHER file is a
    #    malformed (half-added or stray) skill dir — a *fully-enumerated* one still
    #    passes checks 1–5, so check #6 fails it closed here rather than relying on a
    #    separate CI step (the globbed name-matches-dir job and `routing`).
    has_skill=0; has_ver=0
    if [ -f "$d/SKILL.md" ]; then has_skill=1; fi
    if [ -f "$d/VERSION" ]; then has_ver=1; fi
    if [ "$has_skill" = 0 ] && [ "$has_ver" = 0 ]; then
      printf 'ENUM: %s has neither SKILL.md nor VERSION (fail closed)\n' "$name" >&2; fail=1
    elif [ "$has_skill" = 1 ] && [ "$has_ver" = 0 ]; then
      printf 'ENUM: %s has a SKILL.md but no VERSION (fail closed)\n' "$name" >&2; fail=1
    elif [ "$has_ver" = 1 ] && [ "$has_skill" = 0 ]; then
      printf 'ENUM: %s has a VERSION but no SKILL.md (fail closed)\n' "$name" >&2; fail=1
    elif [ "$has_skill" = 1 ] && [ "$has_ver" = 1 ]; then
      sver="$(LC_ALL=C tr -d '\n' < "$d/VERSION")"
      # Extract metadata.version, anchored to the metadata: block. `|| true`: no
      # match yields grep exit 1, which would abort under `set -o pipefail`; the
      # empty result is the signal the absent/unparseable branches act on.
      # Match version: only as a DIRECT child of metadata: (the repo's 2-space
      # convention, verified across all skills). A deeper-nested `sub:\n    version:`
      # is skipped, so a nested decoy cannot mask a drift of the real stamp; a skill
      # that deviates from 2-space reads as "no stamp" and fails closed.
      fmline="$(awk '
        /^---[[:space:]]*$/ {c++; next}
        c!=1 {next}
        /^metadata:[[:space:]]*$/ {inmeta=1; next}
        /^[^[:space:]]/ {inmeta=0}
        inmeta && /^  version:[[:space:]]/ {print; exit}
      ' "$d/SKILL.md" || true)"
      fmver="$(printf '%s' "$fmline" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
      if [ -z "$fmline" ]; then
        printf 'ENUM: %s SKILL.md has no metadata.version stamp\n' "$name" >&2; fail=1
      elif [ -z "$fmver" ]; then
        printf 'ENUM: %s SKILL.md metadata.version is unparseable (%s)\n' "$name" "$(printf '%s' "$fmline" | tr -s '[:space:]' ' ')" >&2; fail=1
      elif [ "$fmver" != "$sver" ]; then
        printf 'ENUM: %s SKILL.md frontmatter version (%s) != VERSION (%s)\n' "$name" "$fmver" "$sver" >&2; fail=1
      fi
    fi
    # 7) Verification-list completeness — a skill that enumerates EVERY eval id in
    #    its SKILL.md (one bullet per eval, ids in backticks, closed by "plants these
    #    cases") must name every id in evals/evals.json, so a later-added eval cannot
    #    leave its Verification bullet forgotten. Matches the backticked `id` so a bare
    #    substring elsewhere in the prose cannot satisfy it. CLOSED, MANUAL allowlist
    #    (`verif_enum`): the "plants" marker is ambiguous — idea-critic and agentic-ceo
    #    carry it but name only KEY cases, and the large skills (deep-code-review,
    #    agentic-delivery) do not enumerate, so an unscoped check would false-flag them
    #    (already-litigated). UNLIKE checks 1–5, this list does NOT self-gate: a new
    #    enumerate-every-id skill left off it is silently uncovered (fail-open on the
    #    ADDITION), so it must be added by hand. The resolves-check after the loop
    #    fail-closes a typo'd/stale entry, but cannot catch a missing addition. This
    #    doc-sync class surfaced FOUR times before this gate — product-output-safety
    #    (eval added v1.75.0, bullet forgotten until this wave found it), v1.125.0, and
    #    two caught in review at v1.133.0 — with nothing referencing eval ids.
    case " $verif_enum " in
      *" $name "*)
        if [ -f "$d/evals/evals.json" ]; then
          while IFS= read -r eid; do
            [ -n "$eid" ] || continue
            grep -qF -- "${bt}${eid}${bt}" "$d/SKILL.md" \
              || { printf 'ENUM: %s eval id "%s" is missing from its SKILL.md Verification list (doc-sync)\n' "$name" "$eid" >&2; fail=1; }
          done < <(grep -oE '"id"[[:space:]]*:[[:space:]]*"[^"]+"' "$d/evals/evals.json" | sed -E 's/.*"([^"]+)"$/\1/' || true)
        else
          printf 'ENUM: %s is Verification-enumerated but has no evals/evals.json (fail closed)\n' "$name" >&2; fail=1
        fi
        ;;
    esac
  done

  # check-#7 allowlist drift: on the real suite (guarded by the base skill's presence,
  # so a minimal test fixture that legitimately omits these overlays is skipped), every
  # name in verif_enum must resolve to a skill dir — else a typo or a post-rename stale
  # entry silently disables the check (fail-open on a fail-closed gate; the exact
  # hand-list drift cmd_enumeration exists to catch).
  if [ -d "$skills_dir/deep-code-review" ]; then
    for vname in $verif_enum; do
      [ -d "$skills_dir/$vname" ] \
        || { printf 'ENUM: check-#7 allowlist names "%s", not a skill dir (typo or stale — fix verif_enum)\n' "$vname" >&2; fail=1; }
    done
  fi

  [ "$fail" -eq 0 ] || die "enumeration: one or more skills are not fully enumerated"
  printf 'enumeration: ok\n'
}

# ---------------------------------------------------------------------------
# size — frozen byte-count budgets for shipped skill docs (dogfoods this
# repo's own skill-authoring-and-size.md: "A documented budget, enforced").
#
# Measured in BYTES (`wc -c`), not lines: a line-count budget can be beaten by
# packing more prose onto fewer, longer lines — the file gets bigger (more
# context tokens paid on load) while its line count goes down or holds still.
# Bytes track the actual on-load cost skill-authoring-and-size.md is pricing.
#
# POLICY = FREEZE-RATCHET: scripts/size-budgets.tsv pins each file's budget at
# its size when adopted; a budget only ever moves down (consolidation), never
# up (see cmd_size_ratchet below for the CI-checkable version of that rule).
# Fails closed in BOTH directions: a shipped SKILL.md/references/*.md with
# no row in the config is a failure (forces a new file to declare a budget,
# mirroring cmd_routing's "every reference is routed"), and a config row whose
# file no longer exists is also a failure (a stale entry cannot silently mask
# a rename/delete). Plain indexed arrays only (no `declare -A`): the repo's own
# local bash is 3.2, which has no associative arrays.
# ---------------------------------------------------------------------------
cmd_size() {
  local config="" root=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --config) config="${2:-}"; shift 2 ;;
      --config=*) config="${1#*=}"; shift ;;
      -*) die "size: unknown option: $1" ;;
      *) [ -z "$root" ] || die "size: unexpected extra argument: $1"; root="$1"; shift ;;
    esac
  done
  [ -n "$config" ] || die "size: --config <file> is required (fail closed)"
  [ -f "$config" ] || die "size: config not found: $config (fail closed)"
  [ -n "$root" ] || die "size: <root> directory is required (fail closed)"
  [ -d "$root" ] || die "size: root not found: $root (fail closed)"

  # Parse actionable rows (path<TAB>budget); blank/comment lines are skipped.
  # Plain parallel arrays, aligned by index — portable to bash 3.2.
  local -a cfg_paths=() cfg_budgets=()
  local _line _trimmed _path _budget
  while IFS= read -r _line || [ -n "$_line" ]; do
    _trimmed="${_line#"${_line%%[![:space:]]*}"}"   # strip leading whitespace
    case "$_trimmed" in
      ''|'#'*) continue ;;
    esac
    _path="${_trimmed%%$'\t'*}"
    [ "$_path" != "$_trimmed" ] \
      || die "size: malformed row (no TAB separator) in $config: $_trimmed"
    _budget="${_trimmed#*$'\t'}"
    case "$_budget" in
      ''|*[!0-9]*) die "size: malformed budget \"$_budget\" for $_path in $config (fail closed)" ;;
    esac
    cfg_paths+=("$_path")
    cfg_budgets+=("$_budget")
  done < "$config"

  [ "${#cfg_paths[@]}" -gt 0 ] \
    || die "size: config has no actionable rows (only blanks/comments): $config"

  local fail=0 f rel i found budget bytes
  # 1) Every shipped SKILL.md / references/*.md on disk must have a budget row.
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    rel="${f#"$root"/}"
    found=0
    for i in "${!cfg_paths[@]}"; do
      if [ "${cfg_paths[$i]}" = "$rel" ]; then found=1; break; fi
    done
    if [ "$found" -eq 0 ]; then
      printf 'SIZE MISSING BUDGET: %s has no row in %s (fail closed)\n' "$rel" "$config" >&2
      fail=1
    fi
  done < <(find "$root/.claude/skills" \( -name 'SKILL.md' -o -path '*/references/*.md' \) -type f 2>/dev/null | LC_ALL=C sort)

  # 2) Every budget row must resolve to a real file and stay within budget.
  for i in "${!cfg_paths[@]}"; do
    rel="${cfg_paths[$i]}"
    budget="${cfg_budgets[$i]}"
    f="$root/$rel"
    if [ ! -f "$f" ]; then
      printf 'SIZE DANGLING: %s in %s does not exist on disk (fail closed)\n' "$rel" "$config" >&2
      fail=1
      continue
    fi
    bytes="$(LC_ALL=C wc -c < "$f" | tr -d '[:space:]')"
    if [ "$bytes" -gt "$budget" ]; then
      printf 'SIZE FAIL: %s is %s bytes (budget %s) — consolidate; budgets ratchet down, never up\n' \
        "$rel" "$bytes" "$budget" >&2
      fail=1
    fi
  done

  [ "$fail" -eq 0 ] \
    || die "size: one or more files exceed their frozen budget, or are un-budgeted/dangling"
  printf 'size: ok (%d file(s) within budget)\n' "${#cfg_paths[@]}"
}

# ---------------------------------------------------------------------------
# size-ratchet — CI-checkable enforcement of cmd_size's freeze-ratchet POLICY:
# no row in a byte-budget config (e.g. scripts/size-budgets.tsv) may increase
# versus a base ref's copy of that same config, unless the commit range being
# checked (or CHANGELOG.md at the working tree) carries an explicit marker
# line naming the exact raise:
#
#   size-budget-raise: <path> <old-bytes>→<new-bytes> <reason>
#
# This is a separate, opt-in subcommand — NOT wired into ci.yml by this
# change; an orchestrator invokes it explicitly where it has a meaningful base
# ref (e.g. a release branch's merge-base with main), typically as:
#
#   bash scripts/ci-gates.sh size-ratchet --base <ref> \
#     --config scripts/size-budgets.tsv .
#
# Fails closed: an unresolvable --base (bad ref, shallow clone missing the
# commit, not a git repo) is a hard failure, never a silent skip. A config
# row that is new at HEAD (absent from the base ref's copy) has nothing to
# ratchet against and is not a violation. A row present in both that shrank
# or held steady is never a violation. Only a row present in both whose
# budget is strictly greater at HEAD than at the base ref requires the
# marker. Plain indexed arrays only (no `declare -A`/`local -n`): the repo's
# own local bash is 3.2, which has neither associative arrays nor namerefs —
# so the base-ref and working-tree configs are parsed with two separate
# inline loops into their own arrays, mirroring cmd_size's style.
# ---------------------------------------------------------------------------
cmd_size_ratchet() {
  local base="" config="" root=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --base) base="${2:-}"; shift 2 ;;
      --base=*) base="${1#*=}"; shift ;;
      --config) config="${2:-}"; shift 2 ;;
      --config=*) config="${1#*=}"; shift ;;
      -*) die "size-ratchet: unknown option: $1" ;;
      *) [ -z "$root" ] || die "size-ratchet: unexpected extra argument: $1"; root="$1"; shift ;;
    esac
  done
  [ -n "$base" ] || die "size-ratchet: --base <ref> is required (fail closed)"
  [ -n "$config" ] || die "size-ratchet: --config <file> is required (fail closed)"
  [ -f "$config" ] || die "size-ratchet: config not found: $config (fail closed)"
  [ -n "$root" ] || die "size-ratchet: <root> directory is required (fail closed)"
  [ -d "$root" ] || die "size-ratchet: root not found: $root (fail closed)"

  git -C "$root" rev-parse --git-dir >/dev/null 2>&1 \
    || die "size-ratchet: $root is not a git repository (fail closed)"
  git -C "$root" rev-parse --verify --quiet "${base}^{commit}" >/dev/null \
    || die "size-ratchet: base ref \"$base\" does not resolve to a commit (fail closed; unresolvable base)"

  # Resolve config's path relative to the repo top level, so it can be looked
  # up inside the base ref's tree via `git show <base>:<relpath>`.
  local config_abs root_abs relconfig
  config_abs="$(cd "$(dirname "$config")" && pwd)/$(basename "$config")" \
    || die "size-ratchet: cannot resolve config path: $config"
  root_abs="$(cd "$root" && pwd)" || die "size-ratchet: cannot resolve root path: $root"
  case "$config_abs" in
    "$root_abs"/*) relconfig="${config_abs#"$root_abs"/}" ;;
    *) die "size-ratchet: config ($config) must live under root ($root)" ;;
  esac

  # Parse the current (working-tree) config — same row grammar as cmd_size.
  local -a new_paths=() new_budgets=()
  local _line _trimmed _path _budget
  while IFS= read -r _line || [ -n "$_line" ]; do
    _trimmed="${_line#"${_line%%[![:space:]]*}"}"
    case "$_trimmed" in
      ''|'#'*) continue ;;
    esac
    _path="${_trimmed%%$'\t'*}"
    [ "$_path" != "$_trimmed" ] \
      || die "size-ratchet: malformed row (no TAB separator) in $config: $_trimmed"
    _budget="${_trimmed#*$'\t'}"
    case "$_budget" in
      ''|*[!0-9]*) die "size-ratchet: malformed budget \"$_budget\" for $_path in $config (fail closed)" ;;
    esac
    new_paths+=("$_path")
    new_budgets+=("$_budget")
  done < "$config"
  [ "${#new_paths[@]}" -gt 0 ] \
    || die "size-ratchet: config has no actionable rows (only blanks/comments): $config"

  # Parse the base ref's copy of the same config, if it existed there. A
  # config absent at base (new file since then) means every current row is
  # new — nothing to ratchet against, not a failure.
  local -a old_paths=() old_budgets=()
  local old_content
  if old_content="$(git -C "$root" show "${base}:${relconfig}" 2>/dev/null)"; then
    while IFS= read -r _line || [ -n "$_line" ]; do
      _trimmed="${_line#"${_line%%[![:space:]]*}"}"
      case "$_trimmed" in
        ''|'#'*) continue ;;
      esac
      _path="${_trimmed%%$'\t'*}"
      [ "$_path" != "$_trimmed" ] || continue
      _budget="${_trimmed#*$'\t'}"
      case "$_budget" in
        ''|*[!0-9]*) continue ;;
      esac
      old_paths+=("$_path")
      old_budgets+=("$_budget")
    done <<<"$old_content"
  fi

  local fail=0 i j p new_b old_b found marker
  for i in "${!new_paths[@]}"; do
    p="${new_paths[$i]}"
    new_b="${new_budgets[$i]}"
    found=0
    old_b=""
    for j in "${!old_paths[@]}"; do
      if [ "${old_paths[$j]}" = "$p" ]; then found=1; old_b="${old_budgets[$j]}"; break; fi
    done
    [ "$found" -eq 1 ] || continue
    [ "$new_b" -gt "$old_b" ] || continue

    marker="size-budget-raise: $p ${old_b}→${new_b}"
    if git -C "$root" log --format=%B "${base}..HEAD" 2>/dev/null | grep -qF "$marker" \
       || { [ -f "$root/CHANGELOG.md" ] && grep -qF "$marker" "$root/CHANGELOG.md"; }; then
      printf 'size-ratchet: %s raised %s->%s with a documented marker (ok)\n' "$p" "$old_b" "$new_b"
    else
      printf 'RATCHET FAIL: %s raised %s->%s bytes with no "%s <reason>" line in the %s..HEAD commit range or CHANGELOG.md\n' \
        "$p" "$old_b" "$new_b" "$marker" "$base" >&2
      fail=1
    fi
  done

  [ "$fail" -eq 0 ] \
    || die "size-ratchet: one or more budget rows increased vs $base with no documented size-budget-raise marker"
  printf 'size-ratchet: ok (no undocumented budget increases vs %s)\n' "$base"
}

# ---------------------------------------------------------------------------
# binaries — extension-scoped block on committed images/media/fonts/archives
# and common compiled build output, so the "committed screenshot" bloat class
# (and its cousins — 1.1GB of committed screenshots, a 3.75MB file committed
# 457 times, in the owner's separate audited project) can never land here.
#
# Deliberately NOT a raw-size check: a large but legitimate TEXT artifact (an
# evals.json fixture, a long transcript) is fine at any size; a screenshot is
# wrong at any size. Scans only git-TRACKED files (`git ls-files`), so an
# untracked/gitignored build directory never trips it — matching content is
# never read, only the tracked path's extension.
#
# A small, reasoned, path-scoped allowlist at <root>/scripts/binaries-allowlist.tsv
# exempts a genuinely-committed binary (one row per exact tracked path, blank/
# comment lines ignored); missing or empty means zero exemptions — the safe
# default, not a fail-closed condition (unlike cmd_privacy's banlist, an
# absent allowlist here is stricter, not weaker). Every other tracked file at a
# banned extension fails, naming the path and where it belongs instead.
# ---------------------------------------------------------------------------
cmd_binaries() {
  local -a roots=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -*) die "binaries: unknown option: $1" ;;
      *) roots+=("$1"); shift ;;
    esac
  done
  [ "${#roots[@]}" -eq 1 ] || die "binaries: exactly one root directory is required"
  local root="${roots[0]}"
  [ -d "$root" ] || die "binaries: root not found: $root (fail closed)"

  local tracked_raw
  tracked_raw="$(git -C "$root" ls-files 2>&1)" \
    || die "binaries: git ls-files failed for $root (fail closed; is it a git repo?): $tracked_raw"

  # Images, media, fonts, archives (explicitly named) + common compiled build
  # output (exe/dll/so/dylib/class/jar/pyc/pyo). Matched case-insensitively
  # against the tracked path's extension only.
  local ext_re='\.(png|jpg|jpeg|gif|webp|bmp|pdf|zip|tar|gz|tgz|mp4|mov|woff|woff2|exe|dll|so|dylib|class|jar|pyc|pyo)$'

  local allowlist="$root/scripts/binaries-allowlist.tsv"
  local -a allow_paths=()
  if [ -f "$allowlist" ]; then
    local _line _trimmed
    while IFS= read -r _line || [ -n "$_line" ]; do
      _trimmed="${_line#"${_line%%[![:space:]]*}"}"
      case "$_trimmed" in
        ''|'#'*) continue ;;
      esac
      allow_paths+=("$_trimmed")
    done < "$allowlist"
  fi

  local -a tracked=()
  local f
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    tracked+=("$f")
  done < <(printf '%s\n' "$tracked_raw" | LC_ALL=C sort)

  local fail=0 allowed a n_flagged=0
  # `${arr[@]+"${arr[@]}"}` (not bare `"${arr[@]}"`): bash 3.2 (this repo's own
  # local bash — see cmd_size) treats a zero-element array's `[@]` expansion as
  # an unbound variable under `set -u`; both tracked and allow_paths are
  # legitimately empty in real cases (a repo with no tracked files yet; no
  # allowlist configured), so this guard is required, not defensive
  # over-caution (matches the same guard cmd_install already uses for
  # mode_flags).
  for f in "${tracked[@]+"${tracked[@]}"}"; do
    printf '%s' "$f" | LC_ALL=C grep -qiE "$ext_re" || continue
    allowed=0
    for a in "${allow_paths[@]+"${allow_paths[@]}"}"; do
      [ "$a" = "$f" ] && { allowed=1; break; }
    done
    if [ "$allowed" -eq 0 ]; then
      printf 'BINARY TRACKED: %s (extension-banned; route to an artifact store, do not commit)\n' "$f" >&2
      fail=1
      n_flagged=$((n_flagged + 1))
    fi
  done

  [ "$fail" -eq 0 ] \
    || die "binaries: $n_flagged git-tracked file(s) at a banned extension (see paths above)"
  printf 'binaries: ok (%d tracked file(s) scanned, %d allowlisted)\n' "${#tracked[@]}" "${#allow_paths[@]}"
}

# ---------------------------------------------------------------------------
# mustload — frozen per-archetype MUST-LOAD token-est ceilings, extending the
# size gate's freeze-ratchet policy to deep-code-review/SKILL.md's
# "Archetype -> load map" table: every archetype names a set of MUST-LOAD
# references an agent reads before touching any project code. This gate sums
# each archetype's token-est (chars/4, matching skill-authoring-and-size.md's
# "a token estimate of chars/4 is enough") and pins it in
# scripts/mustload-budgets.tsv.
#
# POLICY = FREEZE-RATCHET, same as cmd_size: a ceiling is the archetype's
# CURRENT must-load total at adoption (GREEN today), and only ever moves DOWN
# as references are split/trimmed (P1b), never up. This makes the
# already-mandatory read cost visible and reducible — most notably the web
# archetype's ~93K-token must-load tax, the single biggest context-hoarding
# cost this suite measured. It does NOT replace the coverage floor
# (cmd_enumeration / cmd_routing's routed-reference check): no ref is ever
# dropped to satisfy a ceiling here, only measured.
#
# Fails closed in BOTH directions, mirroring cmd_size: an archetype in
# SKILL.md's load map with no row in the config is a failure (a new/renamed
# archetype must declare a ceiling), and a config row naming an archetype the
# load map no longer defines is also a failure (a stale entry cannot silently
# stop being checked). Plain indexed arrays only (no `declare -A`): the
# repo's own local bash is 3.2, which has no associative arrays.
# ---------------------------------------------------------------------------
cmd_mustload() {
  local config="" root=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --config) config="${2:-}"; shift 2 ;;
      --config=*) config="${1#*=}"; shift ;;
      -*) die "mustload: unknown option: $1" ;;
      *) [ -z "$root" ] || die "mustload: unexpected extra argument: $1"; root="$1"; shift ;;
    esac
  done
  [ -n "$config" ] || die "mustload: --config <file> is required (fail closed)"
  [ -f "$config" ] || die "mustload: config not found: $config (fail closed)"
  [ -n "$root" ] || die "mustload: <root> directory is required (fail closed)"
  [ -d "$root" ] || die "mustload: root not found: $root (fail closed)"

  local skill_md="$root/.claude/skills/deep-code-review/SKILL.md"
  local refs_dir="$root/.claude/skills/deep-code-review/references"
  [ -f "$skill_md" ] || die "mustload: SKILL.md not found: $skill_md (fail closed)"

  # Parse actionable config rows (archetype<TAB>ceiling-tokens); blank/comment
  # lines are skipped. Plain parallel arrays, aligned by index.
  local -a cfg_archetypes=() cfg_ceilings=()
  local _line _trimmed _a _c
  while IFS= read -r _line || [ -n "$_line" ]; do
    _trimmed="${_line#"${_line%%[![:space:]]*}"}"
    case "$_trimmed" in
      ''|'#'*) continue ;;
    esac
    _a="${_trimmed%%$'\t'*}"
    [ "$_a" != "$_trimmed" ] \
      || die "mustload: malformed row (no TAB separator) in $config: $_trimmed"
    _c="${_trimmed#*$'\t'}"
    case "$_c" in
      ''|*[!0-9]*) die "mustload: malformed ceiling \"$_c\" for $_a in $config (fail closed)" ;;
    esac
    cfg_archetypes+=("$_a")
    cfg_ceilings+=("$_c")
  done < "$config"
  [ "${#cfg_archetypes[@]}" -gt 0 ] \
    || die "mustload: config has no actionable rows (only blanks/comments): $config"

  # Parse SKILL.md's "Archetype -> load map" table: the ONLY definition of
  # which refs are must-load per archetype (never a second hardcoded copy in
  # this script). Every data row between the header and the first line that
  # is no longer part of the table.
  local -a disk_archetypes=() disk_totals=()
  local fail=0
  local rowline inrow=0 archetype refs_field refs_list rf rc rt total
  while IFS= read -r rowline; do
    case "$rowline" in
      '| Archetype | Default domains | Must-load refs |') inrow=1; continue ;;
    esac
    [ "$inrow" -eq 1 ] || continue
    case "$rowline" in
      '|---'*) continue ;;
      '|'*)
        archetype="$(printf '%s' "$rowline" | awk -F'|' '{print $2}' \
          | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
        refs_field="$(printf '%s' "$rowline" | awk -F'|' '{print $4}')"
        [ -n "$archetype" ] || die "mustload: unparseable load-map row in $skill_md: $rowline"
        disk_archetypes+=("$archetype")

        refs_list="$(printf '%s' "$refs_field" \
          | grep -oE '`[A-Za-z0-9._-]+\.md`' | tr -d '`')"
        total=0
        for rf in $refs_list; do
          if [ ! -f "$refs_dir/$rf" ]; then
            printf 'MUSTLOAD MISSING REF: archetype "%s" names references/%s, not on disk (fail closed)\n' \
              "$archetype" "$rf" >&2
            fail=1
            continue
          fi
          rc="$(LC_ALL=C wc -c < "$refs_dir/$rf" | tr -d '[:space:]')"
          rt=$(( rc / 4 ))
          total=$(( total + rt ))
        done
        disk_totals+=("$total")
        ;;
      *) inrow=0 ;;
    esac
  done < "$skill_md"
  [ "${#disk_archetypes[@]}" -gt 0 ] \
    || die "mustload: no Archetype -> load map table rows found in $skill_md (fail closed)"

  # 1) Every archetype the load map defines must have a config row.
  local i j found ceiling archetype2
  for i in "${!disk_archetypes[@]}"; do
    archetype="${disk_archetypes[$i]}"
    found=0
    for j in "${!cfg_archetypes[@]}"; do
      [ "${cfg_archetypes[$j]}" = "$archetype" ] && { found=1; break; }
    done
    if [ "$found" -eq 0 ]; then
      printf 'MUSTLOAD MISSING BUDGET: archetype "%s" has no row in %s (fail closed)\n' \
        "$archetype" "$config" >&2
      fail=1
    fi
  done

  # 2) Every config row must resolve to a load-map archetype and stay at/under
  #    its frozen ceiling.
  for j in "${!cfg_archetypes[@]}"; do
    archetype2="${cfg_archetypes[$j]}"
    ceiling="${cfg_ceilings[$j]}"
    found=0
    for i in "${!disk_archetypes[@]}"; do
      if [ "${disk_archetypes[$i]}" = "$archetype2" ]; then
        found=1
        total="${disk_totals[$i]}"
        break
      fi
    done
    if [ "$found" -eq 0 ]; then
      printf 'MUSTLOAD DANGLING: archetype "%s" in %s is not in SKILL.md'"'"'s load map (fail closed)\n' \
        "$archetype2" "$config" >&2
      fail=1
      continue
    fi
    if [ "$total" -gt "$ceiling" ]; then
      printf 'MUSTLOAD FAIL: archetype "%s" must-load totals %s tokens (ceiling %s) -- ratchet violated; shrink or split refs (P1b)\n' \
        "$archetype2" "$total" "$ceiling" >&2
      fail=1
    fi
  done

  [ "$fail" -eq 0 ] \
    || die "mustload: one or more archetypes exceed their frozen ceiling, or are un-budgeted/dangling"
  printf 'mustload: ok (%d archetype(s) within ceiling)\n' "${#cfg_archetypes[@]}"
}

[ "$#" -gt 0 ] || { usage; exit 2; }
subcmd="$1"; shift
case "$subcmd" in
  privacy) cmd_privacy "$@" ;;
  routing) cmd_routing "$@" ;;
  version) cmd_version "$@" ;;
  install) cmd_install "$@" ;;
  enumeration) cmd_enumeration "$@" ;;
  size) cmd_size "$@" ;;
  size-ratchet) cmd_size_ratchet "$@" ;;
  binaries) cmd_binaries "$@" ;;
  mustload) cmd_mustload "$@" ;;
  -h|--help) usage; exit 0 ;;
  *) printf 'ci-gates: unknown subcommand: %s\n' "$subcmd" >&2; usage; exit 2 ;;
esac
