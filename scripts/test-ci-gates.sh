#!/usr/bin/env bash
#
# Contract self-tests for scripts/ci-gates.sh (Deep Code Review CI gates).
#
# Exercises scripts/ci-gates.sh with the subcommands `privacy`, `routing`,
# `version`, and `install`. That production helper exists at the current HEAD,
# so every case is expected to PASS (GREEN) here. The same cases still prove RED
# during TDD: run against a checkout without the helper (or one whose behaviour
# regresses) they FAIL. Real exit codes are always preserved — no `|| true`, no
# always-success fallback, and no pipeline that swallows the exit status of the
# command under test.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATES="$ROOT/scripts/ci-gates.sh"
WORK="$ROOT/.dcr-test-work"

# Documented SKILL.md size budget (bytes). Exceeding it must WARN, not fail.
SKILL_BUDGET=1024

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

rm -rf "$WORK"
mkdir -p "$WORK"

pass=0
fail=0
GATE_RC=0

# record <0|1> <label>  — 0 == case passed, non-zero == case failed.
record() {
  if [ "$1" -eq 0 ]; then
    printf 'PASS  %s\n' "$2"
    pass=$((pass + 1))
  else
    printf 'FAIL  %s\n' "$2"
    fail=$((fail + 1))
  fi
}

# gate <cmd...> — run the tested helper through bash, capturing its REAL exit code into
# GATE_RC without masking it. Output is kept for postcondition inspection.
gate() {
  if bash "$@" >"$WORK/last.log" 2>&1; then
    GATE_RC=0
  else
    GATE_RC=$?
  fi
}

# ---------------------------------------------------------------------------
# precondition — the helper under test must exist as a regular file.
#
# Without this guard a missing scripts/ci-gates.sh would silently corrupt the
# result: a command that cannot run exits non-zero, and every rejection case
# reads a non-zero exit as success. The RED harness would then falsely go
# green while proving nothing. Fail loudly and early instead, so a missing
# helper makes this harness FAIL.
# ---------------------------------------------------------------------------
if [ ! -f "$GATES" ]; then
  printf 'PRECONDITION FAIL: helper file not found: %s\n' "$GATES" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# privacy — banlist hygiene and secret detection
# ---------------------------------------------------------------------------

mkdir -p "$WORK/scan"
# Build the planted secret at runtime so this harness file itself never carries
# a literal match for the repo's pre-commit secret grep.
planted="AKIA$(printf 'X%.0s' {1..16})"
printf 'aws_key = %s\n' "$planted" >"$WORK/scan/planted.txt"

# A valid banlist: comment plus a real pattern (the pattern text below does not
# itself match AKIA[0-9A-Z]{16}, so it is safe to commit).
printf '# known secret shapes\nAKIA[0-9A-Z]{16}\n' >"$WORK/banlist.valid"
: >"$WORK/banlist.empty"
printf '# only comments\n#   nothing actionable\n' >"$WORK/banlist.comments"

gate "$GATES" privacy --banlist "$WORK/banlist.empty" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then record 0 "privacy: reject empty banlist"; else record 1 "privacy: reject empty banlist"; fi

gate "$GATES" privacy --banlist "$WORK/banlist.comments" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then record 0 "privacy: reject all-comment banlist"; else record 1 "privacy: reject all-comment banlist"; fi

gate "$GATES" privacy --banlist "$WORK/banlist.valid" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then record 0 "privacy: detect planted banned secret"; else record 1 "privacy: detect planted banned secret"; fi

# A banlist carrying an invalid extended regular expression (a lone opening
# bracket has no closing `]`). The gate must fail closed: an unusable pattern
# cannot be silently skipped, because a skipped pattern scans nothing and lets a
# banned string through undetected. Reject the run instead.
#
# It must also fail *privately*: the banlist may hold real secret shapes, so a
# diagnostic that echoes the offending pattern would leak banlist content into
# CI logs. The planted invalid pattern here is a lone opening bracket `[`; the
# gate must therefore (a) exit non-zero, (b) say the offending content was
# withheld, and (c) never reproduce the `[` in its output. Fixed-string greps
# (-F) are used so the bracket is matched literally, not as a regex.
printf '# broken pattern below\n[\n' >"$WORK/banlist.badregex"
gate "$GATES" privacy --banlist "$WORK/banlist.badregex" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ] \
  && grep -qiF 'content withheld' "$WORK/last.log" \
  && ! grep -qF '[' "$WORK/last.log"; then
  record 0 "privacy: reject banlist with invalid ERE (fail closed, without disclosing banlist content)"
else
  record 1 "privacy: reject banlist with invalid ERE (fail closed, without disclosing banlist content)"
fi

# The documented optional local override: a primary .banlist.txt is loaded
# together with its sibling .banlist.local.txt when that sibling exists, so an
# operator can extend the committed policy locally without editing it. This case
# proves BOTH files are loaded, not just the primary. The primary here carries a
# single valid pattern that deliberately does NOT match the planted secret, while
# the sibling local file carries the banned shape (the same AKIA[0-9A-Z]{16} regex
# already used above). If the gate read only the primary, the planted secret would
# slip through and the scan would report clean; the run must reject only because
# the sibling local banlist is loaded alongside the primary. Content stays hidden:
# no secret literal is written — the planted fixture is the runtime-built one from
# above, and only the regex shape (never a live key) is placed in the local file.
localdir="$WORK/banlist-local"
mkdir -p "$localdir"
printf '# primary policy (nonmatching)\nNOMATCH_[A-Z]+\n' >"$localdir/.banlist.txt"
printf 'AKIA[0-9A-Z]{16}\n' >"$localdir/.banlist.local.txt"

gate "$GATES" privacy --banlist "$localdir/.banlist.txt" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then
  record 0 "privacy: load optional sibling .banlist.local.txt alongside primary .banlist.txt"
else
  record 1 "privacy: load optional sibling .banlist.local.txt alongside primary .banlist.txt"
fi

# ---------------------------------------------------------------------------
# routing — every references/*.md must be routed from SKILL.md
# ---------------------------------------------------------------------------

unrouted="$WORK/skill-unrouted"
mkdir -p "$unrouted/references"
printf '# Skill\n\nSee references/routed.md for depth.\n' >"$unrouted/SKILL.md"
printf 'routed depth\n' >"$unrouted/references/routed.md"
printf 'orphaned depth\n' >"$unrouted/references/unrouted.md"

gate "$GATES" routing "$unrouted"
if [ "$GATE_RC" -ne 0 ]; then record 0 "routing: reject unrouted reference"; else record 1 "routing: reject unrouted reference"; fi

# Basenames must be matched literally, not as regexes. The reference file is
# references/literal.md, but SKILL.md only mentions references/literalXmd. If the
# gate treats the basename as a pattern, the `.` in `literal.md` matches the `X`
# in `literalXmd` and the orphan is falsely considered routed. A literal match
# sees no mention of literal.md, so the reference is unrouted and must be
# rejected.
literal="$WORK/skill-literal"
mkdir -p "$literal/references"
printf '# Skill\n\nSee references/literalXmd for depth.\n' >"$literal/SKILL.md"
printf 'literal depth\n' >"$literal/references/literal.md"

gate "$GATES" routing "$literal"
if [ "$GATE_RC" -ne 0 ]; then record 0 "routing: reject reference matched only via regex-meta basename"; else record 1 "routing: reject reference matched only via regex-meta basename"; fi

# Oversized SKILL.md that is otherwise well-routed: must PASS but emit a warning.
big="$WORK/skill-big"
mkdir -p "$big/references"
printf '# Skill\n\nSee references/routed.md for depth.\n' >"$big/SKILL.md"
head -c $((SKILL_BUDGET * 4)) </dev/zero | tr '\0' 'x' >>"$big/SKILL.md"
printf 'routed depth\n' >"$big/references/routed.md"

gate "$GATES" routing --max-bytes "$SKILL_BUDGET" "$big"
if [ "$GATE_RC" -eq 0 ] && grep -qi 'warn' "$WORK/last.log"; then
  record 0 "routing: warn (non-failing) when SKILL.md exceeds size budget"
else
  record 1 "routing: warn (non-failing) when SKILL.md exceeds size budget"
fi

# ---------------------------------------------------------------------------
# version — VERSION format and matching CHANGELOG heading
# ---------------------------------------------------------------------------

vbad="$WORK/ver-malformed"
mkdir -p "$vbad"
printf 'banana\n' >"$vbad/VERSION"
printf '# Changelog\n\n## banana\n' >"$vbad/CHANGELOG.md"

gate "$GATES" version "$vbad"
if [ "$GATE_RC" -ne 0 ]; then record 0 "version: reject malformed VERSION"; else record 1 "version: reject malformed VERSION"; fi

vnochg="$WORK/ver-nochangelog"
mkdir -p "$vnochg"
printf '1.2.3\n' >"$vnochg/VERSION"
printf '# Changelog\n\n## 9.9.9 - earlier\n' >"$vnochg/CHANGELOG.md"

gate "$GATES" version "$vnochg"
if [ "$GATE_RC" -ne 0 ]; then record 0 "version: reject missing matching CHANGELOG heading"; else record 1 "version: reject missing matching CHANGELOG heading"; fi

# ---------------------------------------------------------------------------
# install — behaviour of the real installer against the real repo
# ---------------------------------------------------------------------------

skill_rel=".claude/skills/deep-code-review"
# The installer vendors the repository's standards index into the skill. Pin the
# exact source path and destination name — no ls/head pipeline picking an
# arbitrary reference, and no always-success fallback that could mask a missing
# source. If the source is absent, cmp below fails and the case records FAIL.
ref_src="$ROOT/docs/standards-index.md"
ref_name="standards-index.md"

# 1) installer overwrites a placeholder reference with the real docs content.
dest1="$WORK/dest-placeholder"
mkdir -p "$dest1/$skill_rel/references"
printf 'PLACEHOLDER\n' >"$dest1/$skill_rel/references/$ref_name"
gate "$GATES" install --src "$ROOT" --dest "$dest1" --mode claude
installed="$dest1/$skill_rel/references/$ref_name"
if [ "$GATE_RC" -eq 0 ] && ! grep -q 'PLACEHOLDER' "$installed" && cmp -s "$installed" "$ref_src"; then
  record 0 "install: overwrite placeholder reference with real docs content"
else
  record 1 "install: overwrite placeholder reference with real docs content"
fi

# 2) claude-only mode preserves a preexisting AGENTS.md and creates no
#    cursor/agents paths of its own.
dest2="$WORK/dest-claude-only"
mkdir -p "$dest2"
printf 'PREEXISTING-AGENTS' >"$dest2/AGENTS.md"
gate "$GATES" install --src "$ROOT" --dest "$dest2" --mode claude
if [ "$GATE_RC" -eq 0 ] \
  && [ "$(cat "$dest2/AGENTS.md")" = "PREEXISTING-AGENTS" ] \
  && [ ! -e "$dest2/.cursor" ] \
  && [ ! -e "$dest2/.cursorrules" ] \
  && [ ! -e "$dest2/.agents" ]; then
  record 0 "install: claude-only preserves AGENTS.md, no cursor/agents paths"
else
  record 1 "install: claude-only preserves AGENTS.md, no cursor/agents paths"
fi

# 2a) minimal mode on a fresh destination installs the claude skill only and
#     creates none of the cursor/agents/codex skill roots.
dest_min="$WORK/dest-minimal"
mkdir -p "$dest_min"
gate "$GATES" install --src "$ROOT" --dest "$dest_min" --mode minimal
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_min/$skill_rel/SKILL.md" ] \
  && [ ! -e "$dest_min/.cursor" ] \
  && [ ! -e "$dest_min/.agents" ] \
  && [ ! -e "$dest_min/.codex" ]; then
  record 0 "install: minimal creates claude skill, no cursor/agents/codex roots"
else
  record 1 "install: minimal creates claude skill, no cursor/agents/codex roots"
fi

# 2b) codex mode on a fresh destination installs the claude skill plus the
#     cursor/agents/codex skill roots and leaves the managed AGENTS.md pointer.
dest_codex="$WORK/dest-codex"
mkdir -p "$dest_codex"
gate "$GATES" install --src "$ROOT" --dest "$dest_codex" --mode codex
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_codex/$skill_rel/SKILL.md" ] \
  && [ -e "$dest_codex/.cursor" ] \
  && [ -e "$dest_codex/.agents" ] \
  && [ -e "$dest_codex/.codex" ] \
  && [ -s "$dest_codex/AGENTS.md" ]; then
  record 0 "install: codex creates claude/cursor/agents/codex roots + AGENTS.md pointer"
else
  record 1 "install: codex creates claude/cursor/agents/codex roots + AGENTS.md pointer"
fi

# 3) rapid repeated installs create distinct backups of the prior skill.
dest3="$WORK/dest-backups"
mkdir -p "$dest3/$skill_rel"
printf 'v0\n' >"$dest3/$skill_rel/SKILL.md"
gate "$GATES" install --src "$ROOT" --dest "$dest3" --mode claude
rc_first=$GATE_RC
gate "$GATES" install --src "$ROOT" --dest "$dest3" --mode claude
rc_second=$GATE_RC
if [ "$rc_first" -eq 0 ] && [ "$rc_second" -eq 0 ]; then
  backups=( "$dest3/.claude/skill-backups/deep-code-review-"* )
  n_backups=0
  for b in "${backups[@]}"; do
    [ -e "$b" ] && n_backups=$((n_backups + 1))
  done
  if [ "$n_backups" -ge 2 ]; then
    record 0 "install: rapid repeated installs create distinct backups"
  else
    record 1 "install: rapid repeated installs create distinct backups"
  fi
else
  record 1 "install: rapid repeated installs create distinct backups"
fi

# ---------------------------------------------------------------------------

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
