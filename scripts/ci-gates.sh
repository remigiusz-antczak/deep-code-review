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
#   routing [--max-bytes N] <skill-dir>  every references/*.md routed from SKILL.md; size WARNs (non-failing)
#   version <root>                       VERSION is semver and announced in CHANGELOG.md
#   install --src <dir> --dest <dir> --mode <claude|minimal|full|codex>
#                                        run the real installer, then verify vendored docs are real (not placeholders)
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
  ci-gates.sh install --src <dir> --dest <dir> --mode <claude|minimal|full|codex>
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
# route named in SKILL.md must resolve to a file. An oversized SKILL.md WARNs
# (documented budget) but never fails — size is advice, broken routing is a bug.
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

  # 3) Optional, non-failing size budget.
  if [ -n "$max_bytes" ]; then
    local size
    size="$(wc -c < "$skill_md" | tr -d '[:space:]')"
    if [ "$size" -gt "$max_bytes" ]; then
      printf 'WARN: SKILL.md is %s bytes (exceeds %s-byte budget); not a failure\n' \
        "$size" "$max_bytes" >&2
    fi
  fi

  [ "$fail" -eq 0 ] || die "routing: unrouted and/or dangling references present"
  printf 'routing: ok\n'
}

# ---------------------------------------------------------------------------
# version — VERSION is semver and the CHANGELOG announces it.
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

  local ver
  ver="$(tr -d '[:space:]' < "$version_file")"
  [ -n "$ver" ] || die "version: VERSION file is empty: $version_file"
  printf 'VERSION=%s (from %s)\n' "$ver" "$version_file"

  printf '%s\n' "$ver" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$' \
    || die "version: VERSION is not semver MAJOR.MINOR.PATCH: $ver"

  # Match "## <ver>" or "## [<ver>]" with the version terminated by ']', space,
  # or end of line, so 1.2.3 never matches a longer 1.2.30. Dots are escaped.
  local ver_re="${ver//./\\.}"
  grep -qE "^## \[?${ver_re}(\]| |\$)" "$changelog" \
    || die "version: no CHANGELOG heading announces $ver in $changelog"

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
  [ -n "$mode" ] || die "install: --mode <claude|minimal|full|codex> is required"
  [ -d "$src" ]  || die "install: --src not found: $src"
  [ -d "$dest" ] || die "install: --dest not found: $dest"

  local installer="$src/install.sh"
  [ -f "$installer" ] || die "install: real installer not found: $installer"

  local -a mode_flags=()
  case "$mode" in
    claude)       mode_flags=(--claude-only) ;;
    minimal)      mode_flags=(--minimal) ;;
    codex)        mode_flags=(--with-codex) ;;   # multi-path plus codex adapter
    full|default) : ;;   # agent-agnostic multi-path default
    *) die "install: unsupported mode: $mode (want claude|minimal|full|codex)" ;;
  esac

  # Run the REAL installer; set -e preserves its exit code (no || true).
  bash "$installer" ${mode_flags[@]+"${mode_flags[@]}"} "$dest"

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

  printf 'install: ok (%s mode; docs vendored and verified)\n' "$mode"
}

# ---------------------------------------------------------------------------
[ "$#" -gt 0 ] || { usage; exit 2; }
subcmd="$1"; shift
case "$subcmd" in
  privacy) cmd_privacy "$@" ;;
  routing) cmd_routing "$@" ;;
  version) cmd_version "$@" ;;
  install) cmd_install "$@" ;;
  -h|--help) usage; exit 0 ;;
  *) printf 'ci-gates: unknown subcommand: %s\n' "$subcmd" >&2; usage; exit 2 ;;
esac
