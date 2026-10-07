#!/usr/bin/env bash
# clean_finished.sh — remove your own finished worktrees and scratch. Safe to run on every tick.
# A worktree under ROOT is finished when its branch's PR is MERGED or CLOSED (gh pr view), or its branch is
# listed in HANDED_BACK (optional file, one branch per line: lanes that handed back). It is removed unless:
#   - a process has it open (lsof +D), or
#   - it has unpushed commits (commits not on any remote; a MERGED PR whose head is exactly HEAD counts as
#     pushed, since squash-and-delete-branch leaves no remote ref).
# A dirty worktree is archived first: `git diff HEAD` plus the untracked-file list go to
# ARCHIVE_DIR/<name>.patch, or <name>.N.patch when that exists (default $TMPDIR/worktree-archive), and it is removed only after the write succeeded.
# The main worktree and the one you run from are never removed. Untracked file CONTENTS are listed, not saved.
# Detached-HEAD worktrees have no branch to judge and are left alone.
# SCRATCH (optional, space-separated absolute paths): deleted outright (never "/" or $HOME).
# Env: ROOT (required, absolute dir: only worktrees under it are touched), GH (default gh).
# DRY_RUN=1: print "would remove ..." lines, change nothing. LEDGER=file: append one tab-separated line per action.
# REAP_PATTERN (pgrep -f regex): before the in-use check, kill matching own processes whose cwd is inside a finished
# worktree (reap_own.sh, verified kill); any other holder (an editor, a shell) still blocks removal.
# Prints "removed=N skipped=M archived=K".
set -euo pipefail
: "${ROOT:?set ROOT to your own worktree tree}"
ROOT=$(cd "$ROOT" && pwd -P); GH=${GH:-gh}; AR=${ARCHIVE_DIR:-${TMPDIR:-/tmp}/worktree-archive}
top=$(git rev-parse --show-toplevel); top=$(cd "$top" && pwd -P)
command -v lsof >/dev/null || { echo "clean_finished: lsof missing; cannot tell if a worktree is in use, removing nothing" >&2; exit 2; }
rm=0 sk=0 ar=0
led() { [ -z "${LEDGER:-}" ] || [ "${DRY_RUN:-0}" = 1 ] || printf '%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$1" "$2" "${3:-}" >>"$LEDGER"; }
while IFS=$'\t' read -r wt br; do
  [ "$wt" != "$top" ] || continue
  case "$wt" in "$ROOT"/*) ;; *) continue ;; esac
  state="" head=""
  read -r state head < <("$GH" pr view "$br" --json state,headRefOid -q '.state+" "+.headRefOid' </dev/null 2>/dev/null || true) || true
  if [ "$state" != MERGED ] && [ "$state" != CLOSED ]; then
    { [ -n "${HANDED_BACK:-}" ] && grep -qxF "$br" "$HANDED_BACK" 2>/dev/null; } || continue
  fi
  if [ "$state" != MERGED ] || [ "$head" != "$(git -C "$wt" rev-parse HEAD)" ]; then
    [ "$(git -C "$wt" rev-list --count HEAD --not --remotes)" = 0 ] || { sk=$((sk+1)); led skip "$wt" unpushed; continue; }
  fi
  if [ -n "${REAP_PATTERN:-}" ]; then
    ROOT=$wt PATTERN=$REAP_PATTERN MAX_AGE_S=0 bash "$(dirname "${BASH_SOURCE[0]}")/reap_own.sh" >/dev/null || true
  fi
  if [ "${DRY_RUN:-0}" != 1 ] && [ -n "$(lsof -t +D "$wt" 2>/dev/null | head -1)" ]; then sk=$((sk+1)); led skip "$wt" in-use; continue; fi
  if [ "${DRY_RUN:-0}" = 1 ]; then echo "would remove $wt"; rm=$((rm+1)); continue; fi
  if [ -n "$(git -C "$wt" status --porcelain)" ]; then
    mkdir -p "$AR"; f="$AR/$(basename "$wt").patch" i=0
    while [ -e "$f" ]; do i=$((i+1)); f="$AR/$(basename "$wt").$i.patch"; done  # same-named worktrees must not overwrite an archive
    { git -C "$wt" diff HEAD; echo "# untracked:"; git -C "$wt" ls-files --others --exclude-standard; } >"$f" || { sk=$((sk+1)); continue; }
    ar=$((ar+1)); led archive "$wt" "$f"
  fi
  if git worktree remove --force "$wt" >/dev/null 2>&1; then rm=$((rm+1)); led remove "$wt"; else sk=$((sk+1)); led skip "$wt" remove-failed; fi
done < <(git worktree list --porcelain | awk '/^worktree /{w=substr($0,10)} /^branch /{print w "\t" substr($0,19)}')
for s in ${SCRATCH:-}; do
  case "$s" in /|"$HOME"|"$HOME"/|"") continue ;; /*) rm -rf "$s" ;; esac
done
echo "removed=$rm skipped=$sk archived=$ar"
