#!/usr/bin/env bash
# Tests for pre-push-verify.sh's mechanism gate (#1380): a SKILL.md-only follow-up commit is refused over the
# whole branch range, the squashed (test included) branch passes. Plain bash; fixture repo under $WORK.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PPV="$ROOT/.claude/skills/deep-code-review/templates/pre-push-verify.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/dcr-test-prepush-fc.XXXXXX")"
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
pass=0 fail=0
ok() { if [ "$1" -eq 0 ]; then echo "PASS  $2"; pass=$((pass + 1)); else echo "FAIL  $2"; fail=$((fail + 1)); fi; }
R="$WORK/local"
g() { git -C "$R" -c user.email=t@example.com -c user.name=T "$@"; }
git init -q --bare "$WORK/remote.git" -b main
git clone -q "$WORK/remote.git" "$R" 2>/dev/null
mkdir -p "$R/.github/workflows" "$R/.claude/skills/deep-code-review/scripts" "$R/.claude/skills/x"
cp "$ROOT/.github/workflows/ci.yml" "$R/.github/workflows/"
cp "$ROOT/.claude/skills/deep-code-review/scripts/fix_class_gate.py" "$R/.claude/skills/deep-code-review/scripts/"
printf 'v1\n' >"$R/.claude/skills/x/SKILL.md"
g add -A; g commit -q -m base; g push -q origin HEAD:main; g remote set-head origin main >/dev/null 2>&1
B=$(g rev-parse HEAD)
run() { # run <sha>: feed a pre-push line for a new branch
  (cd "$R" && printf 'refs/heads/b %s refs/heads/b 0000000000000000000000000000000000000000\n' "$1" |
    DCR_PREPUSH_ALLOW_UNSET=1 bash "$PPV" origin) >"$WORK/log" 2>&1
}

# Branch: a commit that edits SKILL.md and adds an eval, then a follow-up that edits SKILL.md alone.
g checkout -q -b b; mkdir -p "$R/.claude/skills/x/evals"
printf 'v2\n' >"$R/.claude/skills/x/SKILL.md"; printf '[]\n' >"$R/.claude/skills/x/evals/evals.json"
g add -A; g commit -q -m "lesson with eval"
printf 'v3\n' >"$R/.claude/skills/x/SKILL.md"; g commit -q -am "follow-up prose only"
run "$(g rev-parse HEAD)"; rc=$?
{ [ "$rc" -ne 0 ] && grep -q 'add the test/eval to the same commit, or squash' "$WORK/log"; }
ok $? "SKILL.md-only follow-up commit is refused with the fix hint"

# Squash the branch onto the base: one commit carrying prose + eval passes.
g reset -q --soft "$B"; g commit -q -m "lesson squashed"
run "$(g rev-parse HEAD)"; rc=$?
ok $rc "squashed commit (SKILL.md + eval together) passes"
# Pushing another branch's sha while HEAD (and any receipt for it) is elsewhere must be refused: the hook
# verifies each pushed local_sha, never just HEAD.
g checkout -q -b other "$B"; printf 'o\n' >"$R/o.txt"; g add -A; g commit -q -m other; O=$(g rev-parse HEAD)
g checkout -q b; git -C "$R" rev-parse HEAD >"$R/.git/qa-receipt"
(cd "$R" && printf 'refs/heads/other %s refs/heads/other 0000000000000000000000000000000000000000\n' "$O" |
  DCR_PREPUSH_CMD=true bash "$PPV" origin) >"$WORK/log" 2>&1; rc=$?
{ [ "$rc" -ne 0 ] && grep -q 'does not match the commit being pushed' "$WORK/log"; }
ok $? "non-HEAD branch push with a HEAD receipt is refused"
echo "Tests: $pass/$((pass + fail))"
[ "$fail" -eq 0 ]
