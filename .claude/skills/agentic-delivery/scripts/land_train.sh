#!/usr/bin/env bash
# land_train.sh <base-sha> <union-sha> — land every PR of a GREEN merge-train union, each pinned to the
# head SHA the union proved. A PR whose head moved since the union is skipped, never merged unproven.
#
# The union is found BY COMMIT among UNION_DIRS (a rerun after dropping a culprit gets a new worktree
# name, so a name is not a handle). Members are read from the union's merge commits, subject
# "merge-train: #N" (what merge_train.py writes; override the number regex with PR_RE).
#
# Env: UNION_DIRS (required, space-separated worktree paths), BASE_BRANCH (default main), REMOTE
# (default origin), CHANGELOG_DIR (default changelog.d: a PR touching no file under it is appended to
# BACKFILL_FILE as a backfill list, not skipped), BACKFILL_FILE (default ./changelog_backfill.txt),
# PR_RE (sed -E regex with one group, default 'merge-train: #([0-9]+)'), GH (default gh),
# LAND_CMD (default: gh pr merge N --merge --match-head-commit SHA; run via bash -c with $1=N $2=SHA),
# WAIT_TRIES/WAIT_SECS (mergeable=UNKNOWN retry, default 10 x 8s).
# Stacked children (open PRs based on a member's head branch) are retargeted to BASE_BRANCH before each merge.
# Refuses (skips) a PR whose base is not BASE_BRANCH. On every exit, linked worktrees in UNION_DIRS are removed
# (_clean_union.sh).
# Exit: 0 all landed or skipped-with-notice, 1 a merge command failed (see "FAILED rc=" lines), 2 usage/no union worktree.
set -euo pipefail
[ $# -eq 2 ] || { echo "usage: land_train.sh <base-sha> <union-sha>" >&2; exit 2; }
BASE=$1 U=$2
: "${UNION_DIRS:?set UNION_DIRS}"
BASE_BRANCH=${BASE_BRANCH:-main} REMOTE=${REMOTE:-origin} CHANGELOG_DIR=${CHANGELOG_DIR:-changelog.d}
BACKFILL_FILE=${BACKFILL_FILE:-./changelog_backfill.txt} PR_RE=${PR_RE:-merge-train: #([0-9]+)} GH=${GH:-gh}
export GH
LAND_CMD=${LAND_CMD:-'"$GH" pr merge "$1" --merge --match-head-commit "$2"'}
WAIT_TRIES=${WAIT_TRIES:-10} WAIT_SECS=${WAIT_SECS:-8}
. "$(dirname "$0")/_clean_union.sh"; trap clean_union_dirs EXIT

git fetch -q "$REMOTE" "$BASE_BRANCH"
[ "$(git rev-parse "$REMOTE/$BASE_BRANCH")" = "$(git rev-parse "$BASE")" ] || echo "WARN $BASE_BRANCH moved past $BASE"
W=""
for d in $UNION_DIRS; do git -C "$d" cat-file -e "$U^{commit}" 2>/dev/null && W=$d; done
[ -n "$W" ] || { echo "no worktree holds $U"; exit 2; }

# Each merge's 2nd parent is the member head the union proved; first-parent keeps member-internal merges out.
members=$(git -C "$W" log --merges --first-parent --reverse --format='%s %P' "$BASE..$U" \
  | sed -nE "s/^$PR_RE [0-9a-f]+ ([0-9a-f]+).*/\1 \2/p")
[ -n "$members" ] || { echo "no members found in $BASE..$U"; exit 2; }
fails=0
LAST=$(printf '%s\n' "$members" | tail -1 | cut -d' ' -f1)

while read -r N SHA; do
  cur=$("$GH" pr view "$N" --json headRefOid -q .headRefOid </dev/null)
  [ "$cur" = "$SHA" ] || { echo "SKIP #$N moved"; continue; }
  bb=$("$GH" pr view "$N" --json baseRefName -q .baseRefName </dev/null)
  [ "$bb" = "$BASE_BRANCH" ] || { echo "REFUSE #$N base is $bb, expected $BASE_BRANCH"; continue; }
  files=$("$GH" pr diff "$N" --name-only </dev/null)  # not piped to grep -q: its early exit + pipefail = false miss
  grep -q "^$CHANGELOG_DIR/" <<<"$files" \
    ||{ echo "$N" >>"$BACKFILL_FILE"; echo "NOTE #$N needs changelog backfill"; }
  [ "$("$GH" pr view "$N" --json isDraft -q .isDraft </dev/null)" != true ] || "$GH" pr ready "$N" </dev/null >/dev/null
  M=UNKNOWN
  for _ in $(seq "$WAIT_TRIES"); do
    M=$("$GH" pr view "$N" --json mergeable -q .mergeable </dev/null)
    [ "$M" = UNKNOWN ] || break
    sleep "$WAIT_SECS"
  done
  # Landing may delete this PR's head branch, and GitHub closes (unreopenably) any open PR based on it:
  # retarget those stacked children to the base branch first. Unconditional: harmless when nothing is stacked.
  hb=$("$GH" pr view "$N" --json headRefName -q .headRefName </dev/null)
  for c in $("$GH" pr list --base "$hb" --state open --json number -q '.[].number' </dev/null); do
    "$GH" pr edit "$c" --base "$BASE_BRANCH" </dev/null >/dev/null && echo "RETARGET #$c: $hb -> $BASE_BRANCH"
  done
  rc=0; out=$(bash -c "$LAND_CMD" _ "$N" "$SHA" </dev/null 2>&1) || rc=$?  # capture, then tail: a pipe would mask the merge's exit
  out=$(tail -1 <<<"$out")
  [ "$rc" -eq 0 ] || { fails=$((fails+1)); out="FAILED rc=$rc: $out"; }
  echo "#$N($M)$([ "$N" = "$LAST" ] && echo ' last'): $out"
done <<<"$members"
[ "$fails" -eq 0 ] || { echo "$fails PR(s) failed to land" >&2; exit 1; }
