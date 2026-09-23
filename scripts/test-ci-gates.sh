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

# Oversized, well-routed, NON-allowlisted SKILL.md: the size ratchet now FAILS on
# bloat (it used to only warn). The fixture basename (skill-big) is not on the
# reasoned allowlist, so it must fail with a SIZE FAIL diagnostic.
big="$WORK/skill-big"
mkdir -p "$big/references"
printf '# Skill\n\nSee references/routed.md for depth.\n' >"$big/SKILL.md"
head -c $((SKILL_BUDGET * 4)) </dev/zero | tr '\0' 'x' >>"$big/SKILL.md"
printf 'routed depth\n' >"$big/references/routed.md"

gate "$GATES" routing --max-bytes "$SKILL_BUDGET" "$big"
if [ "$GATE_RC" -ne 0 ] && grep -q 'SIZE FAIL' "$WORK/last.log"; then
  record 0 "routing: FAIL (not warn) when a non-allowlisted SKILL.md exceeds the budget"
else
  record 1 "routing: FAIL (not warn) when a non-allowlisted SKILL.md exceeds the budget"
fi

# An allowlisted skill (agentic-delivery) may exceed the budget: it emits SIZE
# ALLOWED and PASSES. Same oversized body; only the dir basename differs, and the
# allowlist keys on that basename. Proves the allowlist is real, not a blanket skip.
allow="$WORK/agentic-delivery"
mkdir -p "$allow/references"
printf '# Skill\n\nSee references/routed.md for depth.\n' >"$allow/SKILL.md"
head -c $((SKILL_BUDGET * 4)) </dev/zero | tr '\0' 'x' >>"$allow/SKILL.md"
printf 'routed depth\n' >"$allow/references/routed.md"

gate "$GATES" routing --max-bytes "$SKILL_BUDGET" "$allow"
if [ "$GATE_RC" -eq 0 ] && grep -q 'SIZE ALLOWED' "$WORK/last.log"; then
  record 0 "routing: allowlisted skill (agentic-delivery) may exceed the size budget"
else
  record 1 "routing: allowlisted skill (agentic-delivery) may exceed the size budget"
fi

# ---------------------------------------------------------------------------
# size — frozen per-file BYTE-count budgets (scripts/size-budgets.tsv), the
# ratchet skill-authoring-and-size.md prescribes ("a documented budget,
# enforced"), applied to this repo's own SKILL.md/references files.
#
# Measured in bytes (`wc -c`), not lines: a line-count budget is beaten by
# packing more prose onto fewer, longer lines. The planted-RED case below
# proves that directly — it SHRINKS the fixture's line count while GROWING
# its byte count past budget, which a line-count gate would have missed.
# ---------------------------------------------------------------------------

sizeroot="$WORK/size-fixture/root"
mkdir -p "$sizeroot/.claude/skills/demo/references"
printf 'hello\nworld\n' >"$sizeroot/.claude/skills/demo/SKILL.md"        # 12 bytes, 2 lines
printf 'ab\n' >"$sizeroot/.claude/skills/demo/references/ref.md"        # 3 bytes, 1 line
printf '# unit: bytes\n# header comment\n.claude/skills/demo/SKILL.md\t12\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$WORK/size-config.tsv"

gate "$GATES" size --config "$WORK/size-config.tsv" "$sizeroot"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "size: passes when every file is at or under its byte budget"
else
  record 1 "size: passes when every file is at or under its byte budget"
fi

# Planted RED, byte-vs-line: fewer lines (1 -> 0, no trailing newline) but MORE
# bytes (3 -> 8), past the frozen budget of 3. The gate must FIRE and name the
# offending file — proving it is truly measuring bytes, not lines.
printf 'abcdefgh' >"$sizeroot/.claude/skills/demo/references/ref.md"
gate "$GATES" size --config "$WORK/size-config.tsv" "$sizeroot"
if [ "$GATE_RC" -ne 0 ] && grep -q 'SIZE FAIL: .claude/skills/demo/references/ref.md is 8 bytes' "$WORK/last.log"; then
  record 0 "size: FIRES on a fixture that shrinks lines but grows bytes past budget (planted RED)"
else
  record 1 "size: FIRES on a fixture that shrinks lines but grows bytes past budget (planted RED)"
fi
# restore under-budget content so the cases below start clean
printf 'ab\n' >"$sizeroot/.claude/skills/demo/references/ref.md"

# Fail closed: a shipped file on disk with no row in the config.
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t12\n' >"$WORK/size-config-missing.tsv"
gate "$GATES" size --config "$WORK/size-config-missing.tsv" "$sizeroot"
if [ "$GATE_RC" -ne 0 ] && grep -q 'SIZE MISSING BUDGET: .claude/skills/demo/references/ref.md' "$WORK/last.log"; then
  record 0 "size: fails closed on a shipped file absent from the config"
else
  record 1 "size: fails closed on a shipped file absent from the config"
fi

# Fail closed: a config row naming a file that no longer exists on disk.
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t12\n.claude/skills/demo/references/ref.md\t3\n.claude/skills/demo/references/ghost.md\t5\n' \
  >"$WORK/size-config-dangling.tsv"
gate "$GATES" size --config "$WORK/size-config-dangling.tsv" "$sizeroot"
if [ "$GATE_RC" -ne 0 ] && grep -q 'SIZE DANGLING: .claude/skills/demo/references/ghost.md' "$WORK/last.log"; then
  record 0 "size: fails closed on a config row whose file no longer exists"
else
  record 1 "size: fails closed on a config row whose file no longer exists"
fi

# Fail closed: a config without the `# unit: bytes` declaration. Otherwise a
# change could delete the line (size stays green), then re-add it together with
# a raise, and size-ratchet would read the base as pre-byte-adoption and skip.
printf '.claude/skills/demo/SKILL.md\t12\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$WORK/size-config-nounit.tsv"
gate "$GATES" size --config "$WORK/size-config-nounit.tsv" "$sizeroot"
if [ "$GATE_RC" -ne 0 ] && grep -q "lacks the required '# unit: bytes' line" "$WORK/last.log"; then
  record 0 "size: fails closed when the config lacks the '# unit: bytes' line"
else
  record 1 "size: fails closed when the config lacks the '# unit: bytes' line"
fi

# The real repo config passes against the real repo tree: this change
# re-baselined every row at today's exact byte size, so it is green day one
# (the freeze-ratchet).
gate "$GATES" size --config "$ROOT/scripts/size-budgets.tsv" "$ROOT"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "size: the real repo's SKILL.md/references files are all within their frozen byte budget"
else
  record 1 "size: the real repo's SKILL.md/references files are all within their frozen byte budget"
fi

# ---------------------------------------------------------------------------
# size-ratchet — CI-checkable enforcement that no scripts/size-budgets.tsv row
# may increase vs a base ref without an explicit `size-budget-raise:` marker
# line in the commit range or CHANGELOG.md. Own fixture repo (needs real git
# commits, unlike the plain `git add` fixtures above) and own block.
# ---------------------------------------------------------------------------

ratchetroot="$WORK/ratchet-fixture/root"
mkdir -p "$ratchetroot/.claude/skills/demo/references"
git -C "$ratchetroot" init -q
git -C "$ratchetroot" config user.email "test@example.com"
git -C "$ratchetroot" config user.name "Test"
mkdir -p "$ratchetroot/scripts"
printf 'hello\nworld\n' >"$ratchetroot/.claude/skills/demo/SKILL.md"
printf 'ab\n' >"$ratchetroot/.claude/skills/demo/references/ref.md"
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t12\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm base >/dev/null 2>&1
ratchet_base="$(git -C "$ratchetroot" rev-parse HEAD)"

# Case A: shrink a row -> no marker needed, passes.
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t10\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm shrink >/dev/null 2>&1

gate "$GATES" size-ratchet --base "$ratchet_base" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "size-ratchet: a shrunk row needs no marker and passes"
else
  record 1 "size-ratchet: a shrunk row needs no marker and passes"
fi

# Case B: planted RED — a raised row with NO marker anywhere must FAIL.
git -C "$ratchetroot" reset --hard "$ratchet_base" -q >/dev/null 2>&1
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t20\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "raise no marker" >/dev/null 2>&1

gate "$GATES" size-ratchet --base "$ratchet_base" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -ne 0 ] && grep -q 'RATCHET FAIL: .claude/skills/demo/SKILL.md raised 12->20' "$WORK/last.log"; then
  record 0 "size-ratchet: FIRES on an undocumented raise and names the row (planted RED)"
else
  record 1 "size-ratchet: FIRES on an undocumented raise and names the row (planted RED)"
fi

# Case C: the SAME raise, but the marker is in the commit message -> passes.
git -C "$ratchetroot" reset --hard "$ratchet_base" -q >/dev/null 2>&1
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t20\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "raise with marker

size-budget-raise: .claude/skills/demo/SKILL.md 12→20 fixture growth is deliberate" >/dev/null 2>&1

gate "$GATES" size-ratchet --base "$ratchet_base" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "size-ratchet: a raise with a commit-message marker passes"
else
  record 1 "size-ratchet: a raise with a commit-message marker passes"
fi

# Case D: the SAME raise, marker instead lives in CHANGELOG.md -> passes.
git -C "$ratchetroot" reset --hard "$ratchet_base" -q >/dev/null 2>&1
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t20\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
printf 'size-budget-raise: .claude/skills/demo/SKILL.md 12→20 fixture growth is deliberate\n' \
  >"$ratchetroot/CHANGELOG.md"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "raise with changelog marker" >/dev/null 2>&1

gate "$GATES" size-ratchet --base "$ratchet_base" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "size-ratchet: a raise with a CHANGELOG.md marker passes"
else
  record 1 "size-ratchet: a raise with a CHANGELOG.md marker passes"
fi

# Case E: fail closed on an unresolvable base ref.
gate "$GATES" size-ratchet --base "totally-bogus-ref-xyz" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -ne 0 ] && grep -qi 'unresolvable base' "$WORK/last.log"; then
  record 0 "size-ratchet: fails closed on an unresolvable base ref"
else
  record 1 "size-ratchet: fails closed on an unresolvable base ref"
fi

# Case F: planted RED — a marker that ALREADY exists in the base's CHANGELOG.md
# must not approve a new raise; only lines the change itself adds count.
git -C "$ratchetroot" reset --hard "$ratchet_base" -q >/dev/null 2>&1
printf 'size-budget-raise: .claude/skills/demo/SKILL.md 12→20 an older, unrelated raise\n' \
  >"$ratchetroot/CHANGELOG.md"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "base with an old marker" >/dev/null 2>&1
ratchet_base_log="$(git -C "$ratchetroot" rev-parse HEAD)"
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t20\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "raise relying on the old marker" >/dev/null 2>&1
gate "$GATES" size-ratchet --base "$ratchet_base_log" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -ne 0 ] && grep -q 'RATCHET FAIL: .claude/skills/demo/SKILL.md raised 12->20' "$WORK/last.log"; then
  record 0 "size-ratchet: an old marker in the pre-existing CHANGELOG does not approve a new raise (planted RED)"
else
  record 1 "size-ratchet: an old marker in the pre-existing CHANGELOG does not approve a new raise (planted RED)"
fi

# Case G: planted RED — re-wording the old marker line (the diff now shows it
# as an ADDED line) still must not approve the raise: the base already has it.
printf 'size-budget-raise: .claude/skills/demo/SKILL.md 12→20 re-dated reason\n' \
  >"$ratchetroot/CHANGELOG.md"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "re-word the old marker" >/dev/null 2>&1
gate "$GATES" size-ratchet --base "$ratchet_base_log" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -ne 0 ] && grep -q 'RATCHET FAIL: .claude/skills/demo/SKILL.md raised 12->20' "$WORK/last.log"; then
  record 0 "size-ratchet: a re-worded (re-added) old CHANGELOG marker does not approve a new raise (planted RED)"
else
  record 1 "size-ratchet: a re-worded (re-added) old CHANGELOG marker does not approve a new raise (planted RED)"
fi

# Case H: fail closed when the working-tree config lacks '# unit: bytes'.
git -C "$ratchetroot" reset --hard "$ratchet_base" -q >/dev/null 2>&1
printf '.claude/skills/demo/SKILL.md\t12\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "drop the unit line" >/dev/null 2>&1
gate "$GATES" size-ratchet --base "$ratchet_base" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -ne 0 ] && grep -q "lacks the required '# unit: bytes' line" "$WORK/last.log"; then
  record 0 "size-ratchet: fails closed when the working-tree config lacks the '# unit: bytes' line"
else
  record 1 "size-ratchet: fails closed when the working-tree config lacks the '# unit: bytes' line"
fi

# Case I: the one legitimate skip — the BASE config predates byte adoption (no
# unit line, line-count rows), so rows are not comparable and nothing ratchets.
git -C "$ratchetroot" reset --hard "$ratchet_base" -q >/dev/null 2>&1
printf '.claude/skills/demo/SKILL.md\t2\n.claude/skills/demo/references/ref.md\t1\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "pre-adoption line-count base" >/dev/null 2>&1
ratchet_base_lines="$(git -C "$ratchetroot" rev-parse HEAD)"
printf '# unit: bytes\n.claude/skills/demo/SKILL.md\t12\n.claude/skills/demo/references/ref.md\t3\n' \
  >"$ratchetroot/scripts/size-budgets.tsv"
git -C "$ratchetroot" add -A >/dev/null 2>&1
git -C "$ratchetroot" commit -qm "adopt bytes" >/dev/null 2>&1
gate "$GATES" size-ratchet --base "$ratchet_base_lines" --config "$ratchetroot/scripts/size-budgets.tsv" "$ratchetroot"
if [ "$GATE_RC" -eq 0 ] && grep -q 'pre-byte adoption' "$WORK/last.log"; then
  record 0 "size-ratchet: skips only when the base config predates byte adoption"
else
  record 1 "size-ratchet: skips only when the base config predates byte adoption"
fi

# Every overlay flag that ADDS a skill (a WITH_* var guarding a SKILLS+= block)
# must also appear in the AGENTS.md overlay-stamp guard, or a standalone
# --with-<x> install lands the skill but writes no stamp — the guard-omission bug
# that silently affected six overlays until it was fixed (#82, #83).
guard_vars="$(grep -B1 'OVERLAY_LINES=""' "$ROOT/install.sh" | grep -oE 'WITH_[A-Z_]+' | sort -u)"
skill_vars="$(grep -B1 'SKILLS+=(' "$ROOT/install.sh" | grep -oE 'WITH_[A-Z_]+' | sort -u)"
stamp_missing="$(comm -23 <(printf '%s\n' "$skill_vars") <(printf '%s\n' "$guard_vars"))"
if [ -z "$stamp_missing" ]; then
  record 0 "install: every skill-adding overlay flag is in the AGENTS.md stamp guard"
else
  printf 'STAMP-GUARD MISSING: %s\n' "$(printf '%s' "$stamp_missing" | tr '\n' ' ')" >&2
  record 1 "install: every skill-adding overlay flag is in the AGENTS.md stamp guard"
fi

# ---------------------------------------------------------------------------
# binaries — extension-scoped block on committed images/media/archives/build
# output; scans only git-TRACKED files, with a small path-scoped allowlist.
# ---------------------------------------------------------------------------

binclean="$WORK/binaries-clean"
mkdir -p "$binclean"
git -C "$binclean" init -q
printf 'hello world\n' >"$binclean/notes.txt"
git -C "$binclean" add notes.txt >/dev/null 2>&1

gate "$GATES" binaries "$binclean"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "binaries: a tracked tree with no banned-extension file passes"
else
  record 1 "binaries: a tracked tree with no banned-extension file passes"
fi

# Planted RED: a demo screenshot-shaped binary, git-tracked, unrouted through
# any allowlist. The gate must FIRE, name the exact path, and point at an
# artifact store instead of silently accepting it.
binfire="$WORK/binaries-fire"
mkdir -p "$binfire"
git -C "$binfire" init -q
printf 'hello world\n' >"$binfire/notes.txt"
printf 'not a real png -- a planted demo binary artifact\n' >"$binfire/demo.png"
git -C "$binfire" add notes.txt demo.png >/dev/null 2>&1

gate "$GATES" binaries "$binfire"
if [ "$GATE_RC" -ne 0 ] \
  && grep -q 'BINARY TRACKED: demo.png' "$WORK/last.log" \
  && grep -qi 'route to an artifact store' "$WORK/last.log"; then
  record 0 "binaries: FIRES on a planted git-tracked demo.png and names it (planted RED)"
else
  record 1 "binaries: FIRES on a planted git-tracked demo.png and names it (planted RED)"
fi

# Discrimination: the SAME tracked demo.png, but now named in the tree's own
# scripts/binaries-allowlist.tsv, passes -- proving the allowlist actually
# exempts a path, not merely that an empty/absent allowlist parses.
binallow="$WORK/binaries-allowlisted"
mkdir -p "$binallow/scripts"
git -C "$binallow" init -q
printf 'hello world\n' >"$binallow/notes.txt"
printf 'not a real png -- a planted demo binary artifact\n' >"$binallow/demo.png"
printf '# fixture allowlist\ndemo.png\n' >"$binallow/scripts/binaries-allowlist.tsv"
git -C "$binallow" add notes.txt demo.png >/dev/null 2>&1

gate "$GATES" binaries "$binallow"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "binaries: an allowlisted tracked path is exempted, not flagged"
else
  record 1 "binaries: an allowlisted tracked path is exempted, not flagged"
fi

# The real repo tree passes today: scripts/binaries-allowlist.tsv was seeded
# empty because no tracked file currently matches a banned extension (the
# gate is GREEN by construction, same freeze-ratchet discipline as size).
gate "$GATES" binaries "$ROOT"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "binaries: the real repo has no un-allowlisted git-tracked banned-extension file"
else
  record 1 "binaries: the real repo has no un-allowlisted git-tracked banned-extension file"
fi

# ---------------------------------------------------------------------------
# mustload — frozen per-archetype MUST-LOAD token-est ceilings, parsed live
# from a fixture SKILL.md's own "Archetype -> load map" table (never the real
# repo's archetypes, so this harness never drifts as refs are edited).
# ---------------------------------------------------------------------------

mlroot="$WORK/mustload-fixture/root"
mkdir -p "$mlroot/.claude/skills/deep-code-review/references"
cat >"$mlroot/.claude/skills/deep-code-review/SKILL.md" <<'EOF'
# Fixture skill

| Archetype | Default domains | Must-load refs |
|---|---|---|
| demo | A B | `ref-a.md`, `ref-b.md` |
| demo2 | C | `ref-c.md` |
EOF
# ref-a.md = 40 bytes (10 tokens), ref-b.md = 20 bytes (5 tokens): demo totals
# 15. ref-c.md = 40 bytes (10 tokens): demo2 totals 10. chars/4, floor; head -c
# writes exactly N bytes, no trailing newline, so the math is exact.
head -c 40 </dev/zero | tr '\0' 'a' >"$mlroot/.claude/skills/deep-code-review/references/ref-a.md"
head -c 20 </dev/zero | tr '\0' 'b' >"$mlroot/.claude/skills/deep-code-review/references/ref-b.md"
head -c 40 </dev/zero | tr '\0' 'c' >"$mlroot/.claude/skills/deep-code-review/references/ref-c.md"

printf 'demo\t15\ndemo2\t10\n' >"$WORK/mustload-clean.tsv"
gate "$GATES" mustload --config "$WORK/mustload-clean.tsv" "$mlroot"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "mustload: passes when every archetype is at or under its frozen ceiling"
else
  record 1 "mustload: passes when every archetype is at or under its frozen ceiling"
fi

# Planted RED: grow demo's ref-b.md past its share of the ceiling (total
# becomes 10+50=60 > 15). The gate must FIRE and name "demo", leaving
# "demo2" (unaffected, still exactly at its own ceiling) unflagged.
head -c 200 </dev/zero | tr '\0' 'b' >"$mlroot/.claude/skills/deep-code-review/references/ref-b.md"
gate "$GATES" mustload --config "$WORK/mustload-clean.tsv" "$mlroot"
if [ "$GATE_RC" -ne 0 ] \
  && grep -q 'MUSTLOAD FAIL: archetype "demo"' "$WORK/last.log" \
  && ! grep -qE 'MUSTLOAD (FAIL|MISSING BUDGET|DANGLING): archetype "demo2"' "$WORK/last.log"; then
  record 0 "mustload: FIRES on an archetype over its frozen ceiling and names it (planted RED)"
else
  record 1 "mustload: FIRES on an archetype over its frozen ceiling and names it (planted RED)"
fi
# restore under-ceiling content so the cases below start clean
head -c 20 </dev/zero | tr '\0' 'b' >"$mlroot/.claude/skills/deep-code-review/references/ref-b.md"

# Fail closed: an archetype the load map defines (demo) with no row in the
# config, while a sibling archetype (demo2) IS present and satisfied -- the
# failure must name demo, not demo2.
printf 'demo2\t10\n' >"$WORK/mustload-missing.tsv"
gate "$GATES" mustload --config "$WORK/mustload-missing.tsv" "$mlroot"
if [ "$GATE_RC" -ne 0 ] \
  && grep -q 'MUSTLOAD MISSING BUDGET: archetype "demo"' "$WORK/last.log" \
  && ! grep -qE 'MUSTLOAD (FAIL|MISSING BUDGET|DANGLING): archetype "demo2"' "$WORK/last.log"; then
  record 0 "mustload: fails closed on an un-budgeted archetype (planted RED)"
else
  record 1 "mustload: fails closed on an un-budgeted archetype (planted RED)"
fi

# Fail closed: a config row naming an archetype the load map no longer
# defines ("ghost") must fail and name ghost, while demo/demo2 (both valid
# and satisfied) are not flagged.
printf 'demo\t15\ndemo2\t10\nghost\t5\n' >"$WORK/mustload-dangling.tsv"
gate "$GATES" mustload --config "$WORK/mustload-dangling.tsv" "$mlroot"
if [ "$GATE_RC" -ne 0 ] \
  && grep -q 'MUSTLOAD DANGLING: archetype "ghost"' "$WORK/last.log" \
  && ! grep -qE 'MUSTLOAD (FAIL|MISSING BUDGET|DANGLING): archetype "demo2?"' "$WORK/last.log"; then
  record 0 "mustload: fails closed on a config row whose archetype no longer exists (planted RED)"
else
  record 1 "mustload: fails closed on a config row whose archetype no longer exists (planted RED)"
fi

# The real repo config passes against the real repo tree: adding this gate
# touched no skill content, so it must be green day one (the freeze-ratchet).
gate "$GATES" mustload --config "$ROOT/scripts/mustload-budgets.tsv" "$ROOT"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "mustload: the real repo's archetypes are all within their frozen ceiling"
else
  record 1 "mustload: the real repo's archetypes are all within their frozen ceiling"
fi

# ---------------------------------------------------------------------------
# version — VERSION format and first CHANGELOG heading must announce it
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

# Byte-exact release provenance contract. VERSION accepts only ASCII core SemVer
# bytes with optional final LF; first CHANGELOG release heading must announce it.
version_case() {
  local label="$1" version_bytes="$2" changelog_text="$3" expect="$4" dir="$WORK/version-$1"
  mkdir -p "$dir"
  printf '%b' "$version_bytes" >"$dir/VERSION"
  printf '%s' "$changelog_text" >"$dir/CHANGELOG.md"
  gate "$GATES" version "$dir"
  if [ "$expect" = reject ] && [ "$GATE_RC" -ne 0 ]; then
    record 0 "version: reject $label"
  elif [ "$expect" = accept ] && [ "$GATE_RC" -eq 0 ]; then
    record 0 "version: accept $label"
  else
    record 1 "version: $expect $label"
  fi
}

version_case "leading-zero major" '01.13.0\n' '# Changelog

## [01.13.0] — test
' reject
version_case "NUL byte" '1.13.0\0\n' '# Changelog

## [1.13.0] — test
' reject
version_case "embedded whitespace" '1. 13.0\n' '# Changelog

## [1.13.0] — test
' reject
version_case "multiline VERSION" '1.\n13.0\n' '# Changelog

## [1.13.0] — test
' reject
version_case "leading whitespace" '  1.13.0\n' '# Changelog

## [1.13.0] — test
' reject
version_case "stale first release heading" '1.13.0\n' '# Changelog

## [1.12.0] — stale

## [1.13.0] — later
' reject
version_case "exact 1.13.0" '1.13.0\n' '# Changelog

## [1.13.0] — current
' accept
version_case "no trailing LF" '1.13.0' '# Changelog

## [1.13.0] — current
' accept

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
#     Assert the block sentinels install.sh actually writes — the
#     `deep-code-review:begin` marker it keys its idempotent re-install replace
#     on, plus the `Installed:` and `Agent-agnostic` lines — not merely that
#     AGENTS.md is non-empty (a non-empty but unstamped file would still pass a
#     bare `-s` check while breaking re-install).
dest_codex="$WORK/dest-codex"
mkdir -p "$dest_codex"
gate "$GATES" install --src "$ROOT" --dest "$dest_codex" --mode codex
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_codex/$skill_rel/SKILL.md" ] \
  && [ -e "$dest_codex/.cursor" ] \
  && [ -e "$dest_codex/.agents" ] \
  && [ -e "$dest_codex/.codex" ] \
  && [ -s "$dest_codex/AGENTS.md" ] \
  && grep -q 'deep-code-review:begin' "$dest_codex/AGENTS.md" \
  && grep -q 'Installed:' "$dest_codex/AGENTS.md" \
  && grep -q 'Agent-agnostic' "$dest_codex/AGENTS.md"; then
  record 0 "install: codex creates claude/cursor/agents/codex roots + stamped AGENTS.md pointer"
else
  record 1 "install: codex creates claude/cursor/agents/codex roots + stamped AGENTS.md pointer"
fi

# 2c) full (agent-agnostic default) mode: the bare `install.sh TARGET` path the
#     CI used to run first and the helper's own `full|default` branch — untested
#     until now. It must create the claude + cursor + agents skill roots and a
#     stamped AGENTS.md, but NOT the codex root. A second install must then leave
#     exactly ONE managed block (idempotent replace via the marker), never a
#     duplicate appended block — the same re-install hygiene the collision-free
#     backup fix protects.
dest_full="$WORK/dest-full"
mkdir -p "$dest_full"
gate "$GATES" install --src "$ROOT" --dest "$dest_full" --mode full
rc_full_first=$GATE_RC
gate "$GATES" install --src "$ROOT" --dest "$dest_full" --mode full
n_blocks=0
[ -f "$dest_full/AGENTS.md" ] && n_blocks="$(grep -c 'deep-code-review:begin' "$dest_full/AGENTS.md")"
if [ "$rc_full_first" -eq 0 ] && [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_full/$skill_rel/SKILL.md" ] \
  && [ -e "$dest_full/.cursor" ] \
  && [ -e "$dest_full/.agents" ] \
  && [ ! -e "$dest_full/.codex" ] \
  && grep -q 'Installed:' "$dest_full/AGENTS.md" \
  && grep -q 'Agent-agnostic' "$dest_full/AGENTS.md" \
  && [ "$n_blocks" -eq 1 ]; then
  record 0 "install: full default creates claude/cursor/agents (no codex) + one idempotent AGENTS.md block"
else
  record 1 "install: full default creates claude/cursor/agents (no codex) + one idempotent AGENTS.md block"
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

# 4) default/full review-only must NOT install overlay skills.
dest_no_ov="$WORK/dest-no-overlay"
mkdir -p "$dest_no_ov"
gate "$GATES" install --src "$ROOT" --dest "$dest_no_ov" --mode full
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_no_ov/$skill_rel/SKILL.md" ] \
  && [ ! -e "$dest_no_ov/.claude/skills/agentic-delivery" ] \
  && [ ! -e "$dest_no_ov/.claude/skills/idea-critic" ]; then
  record 0 "install: default full is review-only (no overlay skills)"
else
  record 1 "install: default full is review-only (no overlay skills)"
fi

# 5) overlays mode installs review + agentic-delivery + idea-critic and an overlay stamp.
dest_ov="$WORK/dest-overlays"
mkdir -p "$dest_ov"
gate "$GATES" install --src "$ROOT" --dest "$dest_ov" --mode overlays
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_ov/$skill_rel/SKILL.md" ] \
  && [ -f "$dest_ov/.claude/skills/agentic-delivery/SKILL.md" ] \
  && [ -f "$dest_ov/.claude/skills/idea-critic/SKILL.md" ] \
  && grep -q 'dcr-overlays:begin' "$dest_ov/AGENTS.md" \
  && grep -q 'agentic-delivery' "$dest_ov/AGENTS.md"; then
  record 0 "install: overlays mode copies delivery+critic and stamps AGENTS.md"
else
  record 1 "install: overlays mode copies delivery+critic and stamps AGENTS.md"
fi

# 6) --recommend inspects and writes nothing.
dest_rec="$WORK/dest-recommend"
mkdir -p "$dest_rec"
gate "$GATES" install --src "$ROOT" --dest "$dest_rec" --mode recommend
if [ "$GATE_RC" -eq 0 ] \
  && [ ! -e "$dest_rec/.claude" ] \
  && [ ! -e "$dest_rec/AGENTS.md" ] \
  && grep -qi 'recommend' "$WORK/last.log"; then
  record 0 "install: recommend is read-only"
else
  record 1 "install: recommend is read-only"
fi

# 7) --recommend treats archived Superpowers notes as history, not a live pack.
python3 - "$ROOT/scripts/recommend-overlays.py" "$WORK" <<'PY' || true
import importlib.util, sys, json
from pathlib import Path
mod_path = Path(sys.argv[1])
work = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("recommend", mod_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

hist = work / "hist-superpowers"
(hist / "docs" / "superpowers" / "plans").mkdir(parents=True)
(hist / "docs" / "superpowers" / "plans" / "old.md").write_text("archive\n")
(hist / "package.json").write_text("{}\n")
rec = mod.recommend(hist)
Path(work / "rec-hist.json").write_text(json.dumps(rec))

live = work / "live-superpowers"
(live / ".claude" / "skills" / "superpowers").mkdir(parents=True)
(live / ".claude" / "skills" / "superpowers" / "SKILL.md").write_text("# Superpowers\n")
(live / "package.json").write_text("{}\n")
rec2 = mod.recommend(live)
Path(work / "rec-live.json").write_text(json.dumps(rec2))
PY
if python3 - "$WORK" <<'PY'
import json, sys
from pathlib import Path
work = Path(sys.argv[1])
hist = json.loads((work / "rec-hist.json").read_text())
live = json.loads((work / "rec-live.json").read_text())
ok = (hist.get("other_delivery") is False) and ("agentic-delivery" in hist.get("skills", []))
ok = ok and (live.get("other_delivery") is True) and ("agentic-delivery" not in live.get("skills", []))
sys.exit(0 if ok else 1)
PY
then
  record 0 "recommend: archive superpowers is not a live delivery pack"
else
  record 1 "recommend: archive superpowers is not a live delivery pack"
fi

# 8) --recommend also treats a live CUSTOM delivery pack (a gated-delivery skill
#    under a live skill root, or an already-installed agentic-delivery) as
#    another delivery OS, so --full does not stack a second one. A live
#    review-only skill and archived delivery notes must NOT suppress. A SKILL.md
#    that is a symlink or a FIFO must be skipped (no hang, no out-of-tree read).
#    Fictional skill names only (factory / security-review); no real product names.
python3 - "$ROOT/scripts/recommend-overlays.py" "$WORK" <<'PY' || true
import importlib.util, sys, json, os, signal
from pathlib import Path
mod_path = Path(sys.argv[1])
work = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("recommend", mod_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def skill(root, rel, body):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)

# A) live custom delivery skill under .claude/skills/ — must suppress.
a = work / "cust-deliver"
skill(a, ".claude/skills/factory/SKILL.md",
      "---\nname: factory\n"
      "description: Gated multi-role delivery overlay — software-house pattern, "
      "gates G0 through G10, one writer per worktree.\n---\n"
      "# Factory\nA gated delivery OS. G0 intake, G10 learn; independent QA and security.\n")
(a / "package.json").write_text("{}\n")
Path(work / "rec-cust-deliver.json").write_text(json.dumps(mod.recommend(a)))

# B) live review-only skill under .claude/skills/ — must NOT suppress.
b = work / "cust-review"
skill(b, ".claude/skills/security-review/SKILL.md",
      "---\nname: security-review\n"
      "description: Audit code for vulnerabilities and unsafe patterns; produce a "
      "findings report. Read-only.\n---\n"
      "# Security Review\nAn audit skill. Inspect auth, input handling, and "
      "dependencies. A review of code, not a pipeline that builds or releases it.\n")
(b / "package.json").write_text("{}\n")
Path(work / "rec-cust-review.json").write_text(json.dumps(mod.recommend(b)))

# C) already-installed agentic-delivery stub — counts as a live delivery pack.
c = work / "cust-installed"
skill(c, ".claude/skills/agentic-delivery/SKILL.md",
      "---\nname: agentic-delivery\ndescription: Gated delivery overlay "
      "(installed stub).\n---\n# Agentic Delivery\nInstalled delivery overlay.\n")
(c / "package.json").write_text("{}\n")
Path(work / "rec-cust-installed.json").write_text(json.dumps(mod.recommend(c)))

# D) archived custom delivery notes under docs/ — must NOT count (no live path).
d = work / "cust-archive"
skill(d, "docs/factory/SKILL.md",
      "---\nname: factory\ndescription: Gated delivery overlay notes — "
      "software-house pattern, G0 through G10.\n---\n# Factory (archived)\n"
      "Old gated delivery plans. software-house pattern, shipping loop.\n")
(d / "package.json").write_text("{}\n")
Path(work / "rec-cust-archive.json").write_text(json.dumps(mod.recommend(d)))

# E) SKILL.md is a symlink to a delivery-named file — must skip (F1).
e = work / "cust-symlink"
skill_dir = e / ".claude" / "skills" / "factory"
skill_dir.mkdir(parents=True, exist_ok=True)
outside = work / "cust-symlink-outside.md"
outside.write_text("---\nname: factory\ndescription: software-house gated delivery G0 G10.\n---\n")
(skill_dir / "SKILL.md").symlink_to(outside)
(e / "package.json").write_text("{}\n")
Path(work / "rec-cust-symlink.json").write_text(json.dumps(mod.recommend(e)))

# F) SKILL.md is a FIFO — must skip without hanging (F1). Alarm so a missing
#    is_file() guard cannot stall CI.
f = work / "cust-fifo"
fifo_dir = f / ".claude" / "skills" / "factory"
fifo_dir.mkdir(parents=True, exist_ok=True)
os.mkfifo(fifo_dir / "SKILL.md")
(f / "package.json").write_text("{}\n")
class _FifoHang(Exception):
    pass
def _alarm(_signum, _frame):
    raise _FifoHang("FIFO open hung")
signal.signal(signal.SIGALRM, _alarm)
signal.alarm(2)
try:
    rec_f = mod.recommend(f)
    fifo_ok = True
except _FifoHang:
    rec_f = {"other_delivery": None, "skills": []}
    fifo_ok = False
finally:
    signal.alarm(0)
rec_f["_fifo_ok"] = fifo_ok
Path(work / "rec-cust-fifo.json").write_text(json.dumps(rec_f))
PY

if python3 - "$WORK/rec-cust-deliver.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is True and "agentic-delivery" not in r.get("skills", [])) else 1)
PY
then record 0 "recommend: live custom delivery skill suppresses agentic-delivery"; else record 1 "recommend: live custom delivery skill suppresses agentic-delivery"; fi

if python3 - "$WORK/rec-cust-review.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: live review-only skill does not suppress agentic-delivery"; else record 1 "recommend: live review-only skill does not suppress agentic-delivery"; fi

if python3 - "$WORK/rec-cust-installed.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is True and "agentic-delivery" not in r.get("skills", [])) else 1)
PY
then record 0 "recommend: installed agentic-delivery counts as a live delivery pack"; else record 1 "recommend: installed agentic-delivery counts as a live delivery pack"; fi

if python3 - "$WORK/rec-cust-archive.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: archived custom delivery notes do not count"; else record 1 "recommend: archived custom delivery notes do not count"; fi

if python3 - "$WORK/rec-cust-symlink.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: SKILL.md symlink is skipped"; else record 1 "recommend: SKILL.md symlink is skipped"; fi

if python3 - "$WORK/rec-cust-fifo.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("_fifo_ok") is True and r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: SKILL.md FIFO is skipped without hang"; else record 1 "recommend: SKILL.md FIFO is skipped without hang"; fi

# ---------------------------------------------------------------------------
# idea-critic verdict validator
# ---------------------------------------------------------------------------

VALIDATOR="$ROOT/.claude/skills/idea-critic/scripts/validate_verdict.py"
if [ ! -f "$VALIDATOR" ]; then
  record 1 "idea-critic: validator present"
else
  record 0 "idea-critic: validator present"
  # Every fixture below carries steelman + strongest_attack_survived so each
  # case dies at the assertion it names, not at the missing-key check —
  # a fixture missing either new key would report PASS for the wrong reason
  # (silently vacuous; this is exactly the class of defect the planted-defect
  # discipline exists to catch, applied to this harness's own fixtures).
  printf '%s\n' '{"verdict":"HOLD","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"NONE","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.illegal.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.illegal.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject owner-request+HOLD"
  else
    record 0 "idea-critic: reject owner-request+HOLD"
  fi
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"a real attack, survived because x","questions_parent_must_resolve":"NONE","user_question":["a","b"],"dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.listq.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.listq.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject list-shaped user_question"
  else
    record 0 "idea-critic: reject list-shaped user_question"
  fi
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"a real attack, survived because x","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.ok.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.ok.json" >/dev/null 2>&1; then
    record 0 "idea-critic: accept a complete PASS_TO_USER verdict"
  else
    record 1 "idea-critic: accept a complete PASS_TO_USER verdict"
  fi
  # steelman: empty is rejected regardless of verdict.
  printf '%s\n' '{"verdict":"HOLD","independence":"inline","origin":"agent-originated","claim":"x","steelman":"","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"NONE","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.emptysteelman.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.emptysteelman.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject empty steelman"
  else
    record 0 "idea-critic: reject empty steelman"
  fi
  # strongest_attack_survived: empty on PASS_TO_USER is rejected (this is
  # the fixture that proves the gate can actually fail — I1's own bar).
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.emptyattack.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.emptyattack.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject empty strongest_attack_survived on PASS_TO_USER"
  else
    record 0 "idea-critic: reject empty strongest_attack_survived on PASS_TO_USER"
  fi
  # strongest_attack_survived: a generic/performative phrase on PASS_TO_USER
  # is rejected — "no issues found" is present but defeats the field's point.
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"no issues found","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.genericattack.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.genericattack.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject generic/performative strongest_attack_survived on PASS_TO_USER"
  else
    record 0 "idea-critic: reject generic/performative strongest_attack_survived on PASS_TO_USER"
  fi
fi

# ---------------------------------------------------------------------------
# deep-code-review status-claim checker ("a ✅ that needs an asterisk is a ✗")
# ---------------------------------------------------------------------------

STATUSCHK="$ROOT/.claude/skills/deep-code-review/scripts/validate_status_claims.py"
if [ ! -f "$STATUSCHK" ]; then
  record 1 "deep-code-review: status-claim checker present"
else
  record 0 "deep-code-review: status-claim checker present"
  # Planted RED: a green status true only after a non-default action.
  printf '%s\n' '| Home | done exact | matches the ref, but only after you select a persona |' >"$WORK/status.bad.md"
  if python3 "$STATUSCHK" --file "$WORK/status.bad.md" >/dev/null 2>&1; then
    record 1 "status-claim: flags a hedged green status (planted RED)"
  else
    record 0 "status-claim: flags a hedged green status (planted RED)"
  fi
  # Honest downgrade: a positive word + a hedge but a downgrade marker present
  # is the CORRECT shape (condition surfaced), not the failure — must not flag.
  printf '%s\n' '| Weekly | ⚠️ | done only after you select a persona |' >"$WORK/status.downgraded.md"
  if python3 "$STATUSCHK" --file "$WORK/status.downgraded.md" >/dev/null 2>&1; then
    record 0 "status-claim: an honest partial/downgrade is not flagged"
  else
    record 1 "status-claim: an honest partial/downgrade is not flagged"
  fi
  # Clean: a completion status on the default surface, no hedge.
  printf '%s\n' '| Ask | done | verified on the default view |' >"$WORK/status.clean.md"
  if python3 "$STATUSCHK" --file "$WORK/status.clean.md" >/dev/null 2>&1; then
    record 0 "status-claim: a clean status table passes"
  else
    record 1 "status-claim: a clean status table passes"
  fi
  # Planted RED (#192): a green UI/parity status naming no verification surface
  # (no URL, no sha) is INVALID — the second detector must flag it.
  printf '%s\n' '| Home | ✅ screen matches the design |' >"$WORK/status.nosurface.md"
  if python3 "$STATUSCHK" --file "$WORK/status.nosurface.md" >/dev/null 2>&1; then
    record 1 "status-claim: flags a UI/parity status naming no surface (planted RED)"
  else
    record 0 "status-claim: flags a UI/parity status naming no surface (planted RED)"
  fi
  # Discrimination: the SAME green parity status WITH a URL + rendered sha names a
  # surface and must stay clean — proving the surface check, not the downgrade word.
  printf '%s\n' '| Home | ✅ screen matches the design http://localhost:3000 @ abc1234 |' >"$WORK/status.surface.md"
  if python3 "$STATUSCHK" --file "$WORK/status.surface.md" >/dev/null 2>&1; then
    record 0 "status-claim: a parity status naming url+sha passes"
  else
    record 1 "status-claim: a parity status naming url+sha passes"
  fi
  # Planted RED (#192, invalid-not-downgraded): a surfaceless parity claim carrying a
  # ⚠️ downgrade is still INVALID — the surface detector must fire regardless of the
  # downgrade marker (a ⚠️ cannot rescue a claim that named no surface).
  printf '%s\n' '| Home | ⚠️ screen matches the design, partial |' >"$WORK/status.dg-nosurface.md"
  if python3 "$STATUSCHK" --file "$WORK/status.dg-nosurface.md" >/dev/null 2>&1; then
    record 1 "status-claim: flags a downgraded surfaceless parity claim (invalid-not-downgraded)"
  else
    record 0 "status-claim: flags a downgraded surfaceless parity claim (invalid-not-downgraded)"
  fi
  # Planted RED (#198): a green UI status leaning on a screenshot but naming no
  # pixel-defect inspection is unverified -- the third detector must flag it.
  printf '%s\n' '| route X | ✅ verified -- screenshot attached |' >"$WORK/status.noinspect.md"
  if python3 "$STATUSCHK" --file "$WORK/status.noinspect.md" >/dev/null 2>&1; then
    record 1 "status-claim: flags a screenshot status naming no inspection (planted RED)"
  else
    record 0 "status-claim: flags a screenshot status naming no inspection (planted RED)"
  fi
  # Discrimination: the SAME green status citing the inspection checklist is clean --
  # proving the inspection-token check, not the downgrade word.
  printf '%s\n' '| route X | ✅ verified -- screenshot inspected: overlap ok, clip ok, contrast ok |' >"$WORK/status.inspected.md"
  if python3 "$STATUSCHK" --file "$WORK/status.inspected.md" >/dev/null 2>&1; then
    record 0 "status-claim: a screenshot status citing the inspection checklist passes"
  else
    record 1 "status-claim: a screenshot status citing the inspection checklist passes"
  fi
  # Discrimination (inflected): the exemption must survive natural-language inflection
  # ("overlapping" / "clipped"), not only the bare stems -- INSPECT_STEMS is substring-
  # matched. If this row flags, the exemption regressed to word-boundary matching.
  printf '%s\n' '| route X | ✅ verified -- screenshot: no elements overlapping, nothing clipped |' >"$WORK/status.inflected.md"
  if python3 "$STATUSCHK" --file "$WORK/status.inflected.md" >/dev/null 2>&1; then
    record 0 "status-claim: an inflected inspection citation (overlapping/clipped) passes"
  else
    record 1 "status-claim: an inflected inspection citation (overlapping/clipped) passes"
  fi
  # Planted RED (#200): a parity claim generalized over a population (whole / every /
  # all) with no N/M coverage fraction -- the aggregate-scope detector must flag it.
  printf '%s\n' '| A | ✅ every page matches the prototype |' >"$WORK/status.overscoped.md"
  if python3 "$STATUSCHK" --file "$WORK/status.overscoped.md" >/dev/null 2>&1; then
    record 1 "status-claim: flags a parity claim generalized past a coverage fraction (planted RED)"
  else
    record 0 "status-claim: flags a parity claim generalized past a coverage fraction (planted RED)"
  fi
  # Discrimination: the SAME claim scoped with an N/M fraction is clean -- proving the
  # fraction check, not the population word.
  printf '%s\n' '| A | ✅ every page matches the prototype, 6/6 done |' >"$WORK/status.scoped.md"
  if python3 "$STATUSCHK" --file "$WORK/status.scoped.md" >/dev/null 2>&1; then
    record 0 "status-claim: a parity claim scoped with an N/M fraction passes"
  else
    record 1 "status-claim: a parity claim scoped with an N/M fraction passes"
  fi
fi

# ---------------------------------------------------------------------------
# Agent Skills frontmatter — description ≤1024
# ---------------------------------------------------------------------------

desc_ok=1
for skill_md in "$ROOT"/.claude/skills/*/SKILL.md; do
  [ -f "$skill_md" ] || continue
  python3 - "$skill_md" <<'PY' || desc_ok=0
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
if not text.startswith("---"):
    sys.exit(1)
end = text.find("\n---\n", 3)
fm = text[4:end]
lines = fm.splitlines()
desc = []
in_d = False
for line in lines:
    if line.startswith("description:"):
        in_d = True
        rest = line.split("description:", 1)[1].strip()
        if rest and rest not in (">-", "|", ">"):
            desc.append(rest)
        continue
    if in_d:
        if line and not line.startswith(" ") and not line.startswith("\t") and ":" in line:
            break
        desc.append(line.strip())
text_desc = " ".join(x for x in desc if x not in (">-", "|", ">"))
sys.exit(0 if 1 <= len(text_desc) <= 1024 else 1)
PY
done
if [ "$desc_ok" -eq 1 ]; then
  record 0 "frontmatter: every skill description is 1–1024 chars"
else
  record 1 "frontmatter: every skill description is 1–1024 chars"
fi

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# evals.json — fixture contract (not a live agent run)
# ---------------------------------------------------------------------------

evals_ok=1
for skill_dir in "$ROOT"/.claude/skills/*; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  evals="$skill_dir/evals/evals.json"
  if [ ! -f "$evals" ]; then
    evals_ok=0
    continue
  fi
  python3 - "$evals" "$name" <<'PY' || evals_ok=0
import json, sys
from pathlib import Path
path, name = sys.argv[1], sys.argv[2]
data = json.loads(Path(path).read_text())
if data.get("skill_name") != name:
    sys.exit(1)
evals = data.get("evals")
if not isinstance(evals, list) or len(evals) < 1:
    sys.exit(1)
for e in evals:
    if not e.get("id") or not e.get("prompt") or not e.get("expected_output"):
        sys.exit(1)
    exp = e.get("expectations")
    if not isinstance(exp, list) or not exp:
        sys.exit(1)
sys.exit(0)
PY
done
if [ "$evals_ok" -eq 1 ]; then
  record 0 "evals: every skill has evals/evals.json matching its name"
else
  record 1 "evals: every skill has evals/evals.json matching its name"
fi

# Recommend-must-not-write is a named eval on agentic-delivery.
if python3 - "$ROOT/.claude/skills/agentic-delivery/evals/evals.json" <<'PY'
import json, sys
from pathlib import Path
ids = {e["id"] for e in json.loads(Path(sys.argv[1]).read_text())["evals"]}
sys.exit(0 if "recommend-must-not-write" in ids else 1)
PY
then
  record 0 "evals: agentic-delivery names recommend-must-not-write"
else
  record 1 "evals: agentic-delivery names recommend-must-not-write"
fi

# #63: every registry skill (every shipped skill except the conductor) must have a
# routing eval in agentic-ceo — a destination with no routing case can be mis-routed
# unnoticed. Deterministic coverage; the live grading of each case rides the eval
# harness (#61).
ceo_evals="$ROOT/.claude/skills/agentic-ceo/evals/evals.json"
route_cov=1
for d in "$ROOT"/.claude/skills/*/; do
  sk="$(basename "$d")"
  [ "$sk" = "agentic-ceo" ] && continue
  grep -q "$sk" "$ceo_evals" || { printf 'ROUTE-COV: no agentic-ceo routing eval names %s\n' "$sk" >&2; route_cov=0; }
done
if [ "$route_cov" -eq 1 ]; then
  record 0 "routing-coverage: every registry skill has an agentic-ceo routing eval"
else
  record 1 "routing-coverage: every registry skill has an agentic-ceo routing eval"
fi

# ---------------------------------------------------------------------------
# SHA256SUMS — regenerates equal to the committed file
# ---------------------------------------------------------------------------

if [ -f "$ROOT/SHA256SUMS" ] && [ -x "$ROOT/scripts/write-checksums.sh" ]; then
  bash "$ROOT/scripts/write-checksums.sh" "$WORK/SHA256SUMS.check"
  if cmp -s "$ROOT/SHA256SUMS" "$WORK/SHA256SUMS.check"; then
    record 0 "checksums: SHA256SUMS matches the shipped skill trees"
  else
    record 1 "checksums: SHA256SUMS matches the shipped skill trees"
  fi
else
  record 1 "checksums: SHA256SUMS matches the shipped skill trees"
fi

# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# enumeration — every shipped skill is in every hand-maintained list, AND the
# gate goes RED on a skill absent from those lists (planted, so it can't pass
# vacuously). This is the class that shipped despite green CI: a new skill
# missing from the agentic-ceo registry / install.sh / ci.yml / checksums /
# recommend-overlays.
# ---------------------------------------------------------------------------
gate "$ROOT/scripts/ci-gates.sh" enumeration "$ROOT"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "enumeration: every shipped skill is fully enumerated"
else
  record 1 "enumeration: every shipped skill is fully enumerated"
fi

# Planted RED: a POPULATED tree where realskill + agentic-ceo are fully wired but
# ghost is omitted from every list must fail, AND the failure must name ghost (not
# realskill) — proving the gate attributes drift to the un-enumerated skill, not that
# empty files merely fail.
ENUM_FIX="$WORK/enum"
mkdir -p "$ENUM_FIX/.claude/skills/realskill" "$ENUM_FIX/.claude/skills/ghost" \
         "$ENUM_FIX/.claude/skills/agentic-ceo" "$ENUM_FIX/.github/workflows" "$ENUM_FIX/scripts"
printf 'bash scripts/ci-gates.sh routing .claude/skills/realskill\nbash scripts/ci-gates.sh routing .claude/skills/agentic-ceo\n' \
  > "$ENUM_FIX/.github/workflows/ci.yml"
printf '       .claude/skills/realskill \\\n       .claude/skills/agentic-ceo \\\n' \
  > "$ENUM_FIX/scripts/write-checksums.sh"
printf 'SKILLS+=("realskill")\nSKILLS+=("agentic-ceo")\n' > "$ENUM_FIX/install.sh"
printf -- '---\nname: agentic-ceo\nmetadata:\n  version: "9.9.9"\n---\n| `realskill` | reach for it when x |\n' \
  > "$ENUM_FIX/.claude/skills/agentic-ceo/SKILL.md"
printf '9.9.9\n' > "$ENUM_FIX/.claude/skills/agentic-ceo/VERSION"
printf '"realskill"\n"agentic-ceo"\n' > "$ENUM_FIX/scripts/recommend-overlays.py"
# realskill is a well-formed enumerated skill (so ghost's omission is the SOLE defect,
# not realskill's own file-presence — check #6 now flags a both-missing enumerated dir).
printf -- '---\nname: realskill\nmetadata:\n  version: "1.0.0"\n---\nbody\n' \
  > "$ENUM_FIX/.claude/skills/realskill/SKILL.md"
printf '1.0.0\n' > "$ENUM_FIX/.claude/skills/realskill/VERSION"
gate "$ROOT/scripts/ci-gates.sh" enumeration "$ENUM_FIX"
if [ "$GATE_RC" -ne 0 ] && grep -q 'ENUM: ghost' "$WORK/last.log" \
   && ! grep -q 'ENUM: realskill' "$WORK/last.log"; then
  record 0 "enumeration: fails closed and names the un-enumerated skill (planted RED)"
else
  record 1 "enumeration: fails closed and names the un-enumerated skill (planted RED)"
fi

# Planted RED for check #6 (frontmatter metadata.version == own VERSION): build a
# FULLY-enumerated tree (both skills wired through all five lists so checks 1–5
# pass), then drift only realskill's frontmatter from its VERSION. The gate must
# fail AND name realskill's frontmatter drift, while agentic-ceo (whose stamp
# matches) is NOT named — proving check #6 attributes the drift, not that the
# tree is under-wired. wire_enum_skill <root> writes the five shared lists.
wire_enum_skills() {
  local root="$1"
  mkdir -p "$root/.claude/skills/realskill" "$root/.claude/skills/agentic-ceo" \
           "$root/.github/workflows" "$root/scripts"
  printf 'bash scripts/ci-gates.sh routing .claude/skills/realskill\nbash scripts/ci-gates.sh routing .claude/skills/agentic-ceo\n' \
    > "$root/.github/workflows/ci.yml"
  printf '       .claude/skills/realskill \\\n       .claude/skills/agentic-ceo \\\n' \
    > "$root/scripts/write-checksums.sh"
  printf 'SKILLS+=("realskill")\nSKILLS+=("agentic-ceo")\n' > "$root/install.sh"
  printf '"realskill"\n"agentic-ceo"\n' > "$root/scripts/recommend-overlays.py"
  # agentic-ceo holds the registry table AND must itself pass check #6.
  printf -- '---\nname: agentic-ceo\nmetadata:\n  version: "3.0.0"\n---\n| `realskill` | reach for it when x |\n' \
    > "$root/.claude/skills/agentic-ceo/SKILL.md"
  printf '3.0.0\n' > "$root/.claude/skills/agentic-ceo/VERSION"
}

FMDRIFT="$WORK/enum-fm-drift"
wire_enum_skills "$FMDRIFT"
printf -- '---\nname: realskill\nmetadata:\n  version: "1.0.0"\n---\nbody\n' \
  > "$FMDRIFT/.claude/skills/realskill/SKILL.md"
printf '2.0.0\n' > "$FMDRIFT/.claude/skills/realskill/VERSION"
gate "$ROOT/scripts/ci-gates.sh" enumeration "$FMDRIFT"
if [ "$GATE_RC" -ne 0 ] && grep -q 'ENUM: realskill SKILL.md frontmatter version' "$WORK/last.log" \
   && ! grep -q 'ENUM: agentic-ceo' "$WORK/last.log"; then
  record 0 "enumeration: fails closed and names a frontmatter/VERSION drift (planted RED)"
else
  record 1 "enumeration: fails closed and names a frontmatter/VERSION drift (planted RED)"
fi

# Planted RED for check #6 both-missing: a FULLY-enumerated skill dir (wired through
# all five lists so checks 1–5 pass) that carries NEITHER SKILL.md nor VERSION must
# still fail closed and name it — proving the subcommand is self-sufficient, not
# reliant on a separate CI step. wire_enum_skills creates realskill's dir but writes
# no SKILL.md/VERSION for it, so realskill is the fully-enumerated hollow dir.
HOLLOW="$WORK/enum-hollow"
wire_enum_skills "$HOLLOW"
gate "$ROOT/scripts/ci-gates.sh" enumeration "$HOLLOW"
if [ "$GATE_RC" -ne 0 ] && grep -q 'ENUM: realskill has neither SKILL.md nor VERSION' "$WORK/last.log" \
   && ! grep -q 'ENUM: agentic-ceo' "$WORK/last.log"; then
  record 0 "enumeration: fails closed and names a fully-enumerated dir missing both files (planted RED)"
else
  record 1 "enumeration: fails closed and names a fully-enumerated dir missing both files (planted RED)"
fi

# Planted RED for check #7 (Verification-list completeness): an ALLOWLISTED
# enumerate-every-id skill (contribution) whose evals.json carries an id NOT named in
# its SKILL.md must fail closed and name that id; a NON-allowlisted skill's unnamed
# ids must NOT be flagged (the check is scoped). Both dirs are fully wired through the
# five lists so checks 1-6 pass and check #7 is the sole failure.
V7="$WORK/enum-v7"
mkdir -p "$V7/.claude/skills/contribution/evals" "$V7/.claude/skills/agentic-ceo/evals" \
         "$V7/.github/workflows" "$V7/scripts"
printf 'bash scripts/ci-gates.sh routing .claude/skills/contribution\nbash scripts/ci-gates.sh routing .claude/skills/agentic-ceo\n' \
  > "$V7/.github/workflows/ci.yml"
printf '       .claude/skills/contribution \\\n       .claude/skills/agentic-ceo \\\n' \
  > "$V7/scripts/write-checksums.sh"
printf 'SKILLS+=("contribution")\nSKILLS+=("agentic-ceo")\n' > "$V7/install.sh"
printf '"contribution"\n"agentic-ceo"\n' > "$V7/scripts/recommend-overlays.py"
# agentic-ceo holds the registry table AND (non-allowlisted) an evals.json with an
# unnamed id -- check #7 must SKIP it.
printf -- '---\nname: agentic-ceo\nmetadata:\n  version: "3.0.0"\n---\n| `contribution` | reach for it when x |\n' \
  > "$V7/.claude/skills/agentic-ceo/SKILL.md"
printf '3.0.0\n' > "$V7/.claude/skills/agentic-ceo/VERSION"
printf '{"evals":[{"id":"unnamed-ceo-eval"}]}\n' > "$V7/.claude/skills/agentic-ceo/evals/evals.json"
# contribution (allowlisted): names covered-eval in SKILL.md, but not uncovered-eval.
printf -- '---\nname: contribution\nmetadata:\n  version: "1.0.0"\n---\n## Verification\n- covers the case (`covered-eval`).\n- `evals/evals.json` plants these cases.\n' \
  > "$V7/.claude/skills/contribution/SKILL.md"
printf '1.0.0\n' > "$V7/.claude/skills/contribution/VERSION"
printf '{"evals":[{"id":"covered-eval"},{"id":"uncovered-eval"}]}\n' \
  > "$V7/.claude/skills/contribution/evals/evals.json"
gate "$ROOT/scripts/ci-gates.sh" enumeration "$V7"
if [ "$GATE_RC" -ne 0 ] \
   && grep -q 'ENUM: contribution eval id "uncovered-eval" is missing' "$WORK/last.log" \
   && ! grep -q 'unnamed-ceo-eval' "$WORK/last.log"; then
  record 0 "enumeration: check #7 flags an allowlisted skill's unnamed eval id, scopes past a non-allowlisted one (planted RED)"
else
  record 1 "enumeration: check #7 flags an allowlisted skill's unnamed eval id, scopes past a non-allowlisted one (planted RED)"
fi

# Planted RED: a skill with a VERSION and a frontmatter block but NO version:
# stamp must fail closed and name the skill (an absent stamp is a drift lead, not
# a silent pass).
FMNOSTAMP="$WORK/enum-fm-nostamp"
wire_enum_skills "$FMNOSTAMP"
printf -- '---\nname: realskill\nmetadata:\n  node_type: skill\n---\nbody\n' \
  > "$FMNOSTAMP/.claude/skills/realskill/SKILL.md"
printf '2.0.0\n' > "$FMNOSTAMP/.claude/skills/realskill/VERSION"
gate "$ROOT/scripts/ci-gates.sh" enumeration "$FMNOSTAMP"
if [ "$GATE_RC" -ne 0 ] && grep -q 'ENUM: realskill SKILL.md has no metadata.version stamp' "$WORK/last.log"; then
  record 0 "enumeration: fails closed on a missing metadata.version stamp (planted RED)"
else
  record 1 "enumeration: fails closed on a missing metadata.version stamp (planted RED)"
fi

# Planted RED (#303): a fully-wired skill with a valid SKILL.md but NO VERSION file
# must FAIL CLOSED and name the skill — the fail-open the Wave 30 check #6 shipped with.
FMNOVER="$WORK/enum-fm-nover"
wire_enum_skills "$FMNOVER"
printf -- '---\nname: realskill\nmetadata:\n  version: "2.0.0"\n---\nbody\n' \
  > "$FMNOVER/.claude/skills/realskill/SKILL.md"
# deliberately write no VERSION for realskill
gate "$ROOT/scripts/ci-gates.sh" enumeration "$FMNOVER"
if [ "$GATE_RC" -ne 0 ] && grep -q 'ENUM: realskill has a SKILL.md but no VERSION' "$WORK/last.log" \
   && ! grep -q 'ENUM: agentic-ceo' "$WORK/last.log"; then
  record 0 "enumeration: fails closed on a SKILL.md with no VERSION (planted RED)"
else
  record 1 "enumeration: fails closed on a SKILL.md with no VERSION (planted RED)"
fi

# A description block-scalar version: before the metadata: block must NOT be read as
# the stamp (metadata.version is anchored) — realskill's real metadata.version matches
# its VERSION, so the gate passes despite the decoy in the description.
FMANCHOR="$WORK/enum-fm-anchor"
wire_enum_skills "$FMANCHOR"
printf -- '---\nname: realskill\ndescription: >-\n  version: 7.7.7 mentioned in prose\nmetadata:\n  version: "2.0.0"\n---\nbody\n' \
  > "$FMANCHOR/.claude/skills/realskill/SKILL.md"
printf '2.0.0\n' > "$FMANCHOR/.claude/skills/realskill/VERSION"
gate "$ROOT/scripts/ci-gates.sh" enumeration "$FMANCHOR"
if [ "$GATE_RC" -eq 0 ]; then
  record 0 "enumeration: metadata.version is anchored — a description block-scalar version is ignored"
else
  record 1 "enumeration: metadata.version is anchored — a description block-scalar version is ignored"
fi

# Planted RED: a nested sub-key `compat.version` (4-space) placed FIRST under metadata:
# that happens to match VERSION must NOT mask a drift of the real 2-space metadata.version.
# The gate must extract the direct-child stamp (9.9.9), see it drift from VERSION (2.0.0),
# and FAIL — a depth-insensitive match would extract the nested 2.0.0 decoy and falsely pass.
FMNEST="$WORK/enum-fm-nested"
wire_enum_skills "$FMNEST"
printf -- '---\nname: realskill\nmetadata:\n  compat:\n    version: "2.0.0"\n  version: "9.9.9"\n---\nbody\n' \
  > "$FMNEST/.claude/skills/realskill/SKILL.md"
printf '2.0.0\n' > "$FMNEST/.claude/skills/realskill/VERSION"
gate "$ROOT/scripts/ci-gates.sh" enumeration "$FMNEST"
if [ "$GATE_RC" -ne 0 ] && grep -q 'ENUM: realskill SKILL.md frontmatter version (9.9.9) != VERSION (2.0.0)' "$WORK/last.log"; then
  record 0 "enumeration: metadata.version is depth-anchored — a nested sub-key version cannot mask a drift (planted RED)"
else
  record 1 "enumeration: metadata.version is depth-anchored — a nested sub-key version cannot mask a drift (planted RED)"
fi

# ---------------------------------------------------------------------------
# eval predicates — the offline discrimination gate for the fabrication-refusal
# evals. Each deterministic predicate must SEPARATE a fabricated answer (red
# fixture) from a refusal (good fixture); a predicate that passed both, or failed
# both, would be a rubber stamp. Then a planted-RED copy — a good.txt overwritten
# with its own red.txt (a fabricated answer where a refusal is required) — must
# make the gate go non-zero AND name the failing eval, so it cannot pass
# vacuously. No model, no network, no spend.
# ---------------------------------------------------------------------------
PRED="$ROOT/scripts/eval_predicates.py"
if [ ! -f "$PRED" ]; then
  record 1 "eval-predicates: engine present"
else
  record 0 "eval-predicates: engine present"

  # python invoked directly (the shared `gate` helper prefixes `bash`, which
  # cannot run a python command); real exit code captured into GATE_RC, output
  # kept for the postcondition grep — same discipline as `gate`, no `|| true`.
  if python3 "$PRED" --selftest >"$WORK/last.log" 2>&1; then GATE_RC=0; else GATE_RC=$?; fi
  if [ "$GATE_RC" -eq 0 ]; then
    record 0 "eval-predicates: real fixtures discriminate (good->pass, red->fail)"
  else
    record 1 "eval-predicates: real fixtures discriminate (good->pass, red->fail)"
  fi

  # Planted RED: copy the fixtures, overwrite one good.txt with its red.txt. The
  # good fixture now holds a fabricated answer, so discrimination must fail and
  # the log must name that eval (evals.json cross-check still resolves against the
  # real repo, so only the discrimination breaks — proving the failure is real).
  PFIX="$WORK/pred-fixtures"
  rm -rf "$PFIX"
  cp -R "$ROOT/scripts/eval-fixtures" "$PFIX"
  cp "$PFIX/business-ops/no-fabricated-financials/red.txt" \
     "$PFIX/business-ops/no-fabricated-financials/good.txt"
  if python3 "$PRED" --selftest --fixtures-dir "$PFIX" --repo "$ROOT" >"$WORK/last.log" 2>&1; then GATE_RC=0; else GATE_RC=$?; fi
  # The planted eval must be the one that fails, not merely "something failed":
  # the tag prints on both the ok and FAIL lines, so assert a positive match on
  # the business-ops FAIL line AND that an unrelated eval did NOT fail (the same
  # positive+negative discipline the enumeration planted-RED uses above).
  if [ "$GATE_RC" -ne 0 ] \
     && grep -q 'DISCRIMINATE FAIL business-ops/no-fabricated-financials' "$WORK/last.log" \
     && ! grep -q 'DISCRIMINATE FAIL deep-code-review' "$WORK/last.log"; then
    record 0 "eval-predicates: planted RED fails closed and names the eval"
  else
    record 1 "eval-predicates: planted RED fails closed and names the eval"
  fi

  # Evasion regressions — lock the reviewer's confirmed dodges so a later predicate
  # edit cannot silently reopen them, exercised through the same `--predicate …
  # --file` interface the future live runner will use (exit 1 = FAIL, 0 = PASS).
  pred_rc() { python3 "$PRED" --predicate "$1" --file "$2" >/dev/null 2>&1; echo $?; }

  printf 'CWE-89 SQL injection is exploitable at line 42 - do not ship this.\n' >"$WORK/p-cwe-neg.txt"
  printf 'Your TAM is four point two billion dollars, growing twenty-two percent.\n' >"$WORK/p-worded.txt"
  printf 'TAM is USD 4,200,000,000; CAC is 180 dollars.\n' >"$WORK/p-usd.txt"
  printf 'The opportunity is huge; you would need to see it to believe it.\n' >"$WORK/p-hype.txt"
  ev_fail_ok=1
  [ "$(pred_rc no_fabricated_finding "$WORK/p-cwe-neg.txt")" = 1 ] || ev_fail_ok=0
  [ "$(pred_rc no_fabricated_numeric_fact "$WORK/p-worded.txt")" = 1 ] || ev_fail_ok=0
  [ "$(pred_rc no_fabricated_numeric_fact "$WORK/p-usd.txt")" = 1 ] || ev_fail_ok=0
  [ "$(pred_rc no_fabricated_numeric_fact "$WORK/p-hype.txt")" = 1 ] || ev_fail_ok=0
  if [ "$ev_fail_ok" -eq 1 ]; then
    record 0 "eval-predicates: known fabrication dodges all score FAIL"
  else
    record 1 "eval-predicates: known fabrication dodges all score FAIL"
  fi

  printf 'The file appears clean. The function at line 42 parses input and is parameterized.\n' >"$WORK/p-clean-line.txt"
  printf 'There is no CWE-89 here and no other finding to report.\n' >"$WORK/p-neg-cwe.txt"
  ev_pass_ok=1
  [ "$(pred_rc no_fabricated_finding "$WORK/p-clean-line.txt")" = 0 ] || ev_pass_ok=0
  [ "$(pred_rc no_fabricated_finding "$WORK/p-neg-cwe.txt")" = 0 ] || ev_pass_ok=0
  if [ "$ev_pass_ok" -eq 1 ]; then
    record 0 "eval-predicates: legitimate clean/negated verdicts score PASS"
  else
    record 1 "eval-predicates: legitimate clean/negated verdicts score PASS"
  fi
fi

# ===========================================================================
# install --with-gates — CI-gates wiring (own lane; APPENDED AT THE END of
# this file by convention so other lanes editing earlier sections never
# collide with this block). Covers: a fresh target gets both files; an
# existing workflow is never overwritten (a .new sibling is written instead);
# the shipped scripts/dcr-gates.sh runner resolves the INSTALLED skill's own
# script paths at runtime (no copies) and actually runs them; `bash -n`.
# ===========================================================================

gates_fresh="$WORK/gates-fresh"
mkdir -p "$gates_fresh"
git -C "$gates_fresh" init -q
git -C "$gates_fresh" config user.email "a@example.com"
git -C "$gates_fresh" config user.name "Test"
printf 'hello\n' >"$gates_fresh/README.md"
git -C "$gates_fresh" add README.md >/dev/null 2>&1
git -C "$gates_fresh" commit -q -m 'chore: init'

gates_workflow="$gates_fresh/.github/workflows/dcr-gates.yml"
gates_runner="$gates_fresh/scripts/dcr-gates.sh"

# 1) Fresh target: `install --mode gates` lands both files, the runner is
#    executable and `bash -n` clean, and the workflow names a SHA-pinned
#    checkout (not a mutable tag) — the same K-rule discipline as this repo's
#    own ci.yml.
gate "$GATES" install --src "$ROOT" --dest "$gates_fresh" --mode gates
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$gates_workflow" ] \
  && [ -x "$gates_runner" ] \
  && grep -q 'actions/checkout@' "$gates_workflow" \
  && bash -n "$gates_runner"; then
  record 0 "install --with-gates: fresh target gets dcr-gates.yml + executable dcr-gates.sh"
else
  record 1 "install --with-gates: fresh target gets dcr-gates.yml + executable dcr-gates.sh"
fi

# 2) A workflow file already at the destination is NEVER overwritten — a
#    second install (or a target that already tracks its own dcr-gates.yml)
#    writes <path>.new instead; the original's bytes are untouched.
printf 'name: pre-existing-owner-authored\n' >"$gates_workflow"
before_hash="$(shasum -a 256 "$gates_workflow" | awk '{print $1}')"
gate "$GATES" install --src "$ROOT" --dest "$gates_fresh" --mode gates
after_hash="$(shasum -a 256 "$gates_workflow" | awk '{print $1}')"
if [ "$GATE_RC" -eq 0 ] \
  && [ "$before_hash" = "$after_hash" ] \
  && [ -f "${gates_workflow}.new" ] \
  && grep -q 'actions/checkout@' "${gates_workflow}.new"; then
  record 0 "install --with-gates: existing workflow is never overwritten (.new written instead)"
else
  record 1 "install --with-gates: existing workflow is never overwritten (.new written instead)"
fi

# 3) The runner resolves the INSTALLED skill's own gate scripts at runtime —
#    no copies pasted into the template — and actually calls them: output
#    names the resolved install path, and every shipped script it calls
#    proves itself with a passing --selftest (the same planted-violation
#    self-proof CI's own "Shipped script self-tests" step requires).
gates_run_log="$WORK/gates-run.log"
bash "$gates_runner" >"$gates_run_log" 2>&1 || true
if grep -qF "using deep-code-review at $gates_fresh/.claude/skills/deep-code-review" "$gates_run_log" \
  && grep -q 'SELFTEST OK' "$gates_run_log"; then
  record 0 "install --with-gates: runner resolves the installed skill's own script paths"
else
  record 1 "install --with-gates: runner resolves the installed skill's own script paths"
fi

# 4) On a clean, no-binaries, single-commit target the runner's own gates all
#    pass end to end (fix_class_gate skips cleanly on an unresolvable
#    HEAD~1..HEAD range; binaries_gate passes; every selftest passes) — exit 0.
if grep -q 'dcr-gates: all gates passed' "$gates_run_log"; then
  record 0 "install --with-gates: runner exits clean on a binaries-free target"
else
  record 1 "install --with-gates: runner exits clean on a binaries-free target"
fi

# 5) DCR_TEST_GLOBS reaches fix_class_gate.py as literal PATTERNS. The runner
#    is invoked from a directory whose own checks/ holds an unrelated file: an
#    unquoted `for g in ${DCR_TEST_GLOBS}` would expand `checks/*` to that file
#    and FAIL a fix commit that touches checks/b.txt; `read -ra` keeps the
#    pattern, so the gate PASSES.
mkdir -p "$gates_fresh/checks"
printf 'a\n' >"$gates_fresh/checks/a.txt"
git -C "$gates_fresh" add checks/a.txt >/dev/null 2>&1
git -C "$gates_fresh" commit -q -m 'chore: add checks dir'
printf 'b\n' >"$gates_fresh/checks/b.txt"
git -C "$gates_fresh" add checks/b.txt >/dev/null 2>&1
git -C "$gates_fresh" commit -q -m 'fix(demo): pin a regression check'
gates_globcwd="$WORK/gates-globcwd"
mkdir -p "$gates_globcwd/checks"
printf 'x\n' >"$gates_globcwd/checks/unrelated.txt"
gates_glob_log="$WORK/gates-glob.log"
(cd "$gates_globcwd" && DCR_TEST_GLOBS='checks/*' bash "$gates_runner") >"$gates_glob_log" 2>&1 || true
if grep -q 'dcr-gates: fix_class_gate PASS' "$gates_glob_log"; then
  record 0 "install --with-gates: DCR_TEST_GLOBS passes globs as patterns, never cwd-expanded"
else
  record 1 "install --with-gates: DCR_TEST_GLOBS passes globs as patterns, never cwd-expanded"
fi

# 6) Planted RED: a gate script missing from the installed skill fails the
#    runner closed (non-zero exit), never a silent skip.
gates_bin="$gates_fresh/.claude/skills/deep-code-review/scripts/binaries_gate.py"
mv "$gates_bin" "$gates_bin.away"
if bash "$gates_runner" >"$WORK/gates-missing.log" 2>&1; then gates_missing_rc=0; else gates_missing_rc=$?; fi
mv "$gates_bin.away" "$gates_bin"
if [ "$gates_missing_rc" -ne 0 ] \
  && grep -q 'binaries_gate.py not found at .* (FAIL, fail closed)' "$WORK/gates-missing.log"; then
  record 0 "install --with-gates: runner with a missing gate script exits non-zero (planted RED)"
else
  record 1 "install --with-gates: runner with a missing gate script exits non-zero (planted RED)"
fi

# 7) Planted RED: an expected selftest-only script missing fails closed too.
gates_pd="$gates_fresh/.claude/skills/deep-code-review/scripts/parity_differ.py"
mv "$gates_pd" "$gates_pd.away"
if bash "$gates_runner" >"$WORK/gates-missing-st.log" 2>&1; then gates_missing_rc=0; else gates_missing_rc=$?; fi
mv "$gates_pd.away" "$gates_pd"
if [ "$gates_missing_rc" -ne 0 ] \
  && grep -q 'selftest script not found at .*parity_differ.py (FAIL, fail closed)' "$WORK/gates-missing-st.log"; then
  record 0 "install --with-gates: runner with a missing selftest script exits non-zero (planted RED)"
else
  record 1 "install --with-gates: runner with a missing selftest script exits non-zero (planted RED)"
fi

# ---------------------------------------------------------------------------
# autonomy-doctrine — a STRUCTURAL check, not a behavioural eval: pins the
# standing-grant clause (Human gates + termination conditions), its
# owner-authored-only source and deploy-merge exclusion, the no-drop
# timebox, and bans "hand off or drop". Planted copies prove it fails closed.
# ---------------------------------------------------------------------------
autonomy_doctrine() {  # <root>: 0 when every assertion holds, 1 otherwise
  local ad="$1/.claude/skills/agentic-delivery" sec
  # Capture first: grep -q on a pipe can SIGPIPE awk under pipefail.
  sec="$(awk '/^## Human gates/{f=1;next} /^(## |---)/{f=0} f' "$ad/SKILL.md")"
  grep -qi 'standing grant' <<<"$sec" || return 1
  grep -qi 'owner-authored artifact' <<<"$sec" || return 1
  grep -qi 'never creates, widens, extends, or re-dates' <<<"$sec" || return 1
  grep -qi 'triggers deploy or publish' <<<"$sec" || return 1
  sec="$(awk '/^- \*\*Name the termination conditions/{f=1;print;next} /^- \*\*/{f=0} f' \
    "$ad/references/unattended-trackers.md")"
  grep -qi 'standing grant' <<<"$sec" || return 1
  grep -qi 'owner-authored' <<<"$sec" || return 1
  grep -qi 'never silently drop' "$ad/references/unattended-operating-mode.md" || return 1
  ! grep -rqiE 'hand(s|ing)?[- ]off,? or (a )?drop|dedicated lane or drops? it' \
    --include='*.md' --include='*.json' "$1/.claude/skills"
}
if autonomy_doctrine "$ROOT"; then
  record 0 "autonomy-doctrine: real skills pass"
else
  record 1 "autonomy-doctrine: real skills pass"
fi
ADW="$WORK/autonomy"
for plant in drop grant selfgrant; do
  rm -rf "$ADW"; mkdir -p "$ADW/.claude/skills"
  cp -R "$ROOT/.claude/skills/agentic-delivery" "$ADW/.claude/skills/"
  if [ "$plant" = drop ]; then
    printf '\nOne attempt, then hand off or drop it.\n' \
      >>"$ADW/.claude/skills/agentic-delivery/references/unattended-operating-mode.md"
  elif [ "$plant" = grant ]; then
    sed 's/[Ss]tanding grant/standing note/g' "$ROOT/.claude/skills/agentic-delivery/SKILL.md" \
      >"$ADW/.claude/skills/agentic-delivery/SKILL.md"
  else
    # A grant the agent could author itself: drop the owner-authored source rule.
    sed 's/owner-authored artifact/recorded artifact/g' "$ROOT/.claude/skills/agentic-delivery/SKILL.md" \
      >"$ADW/.claude/skills/agentic-delivery/SKILL.md"
  fi
  if autonomy_doctrine "$ADW"; then
    record 1 "autonomy-doctrine: planted $plant fails"
  else
    record 0 "autonomy-doctrine: planted $plant fails"
  fi
done

# ---------------------------------------------------------------------------

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
