#!/usr/bin/env bash
# janitor.sh [--apply] REPO... — scheduled cleanup that runs without any agent (install_janitor.sh schedules it).
# Per repo: clean_finished.sh (worktrees whose PR is merged/closed: dirty ones archived first, unpushed or still-in-use
# ones kept) after killing agent-spawned dev servers / test runners / headless browsers whose cwd is inside a finished
# worktree, then reap_own.sh on every remaining linked worktree (same processes, age > threshold). Kills are verified
# (SIGTERM, kill -0 poll, SIGKILL after 5s). Scope is strictly the linked worktrees of the given repos: the main checkout,
# other users' processes and anything whose cwd is elsewhere are never touched.
# Default is a dry run that prints the plan; --apply acts. Every action is appended to the ledger.
# Env: JANITOR_MAX_AGE_S (default 7200), JANITOR_PATTERN (pgrep -f regex of killable process kinds),
# JANITOR_LEDGER (default ${XDG_STATE_HOME:-$HOME/.local/state}/perun/janitor.ledger), GH, ARCHIVE_DIR.
set -euo pipefail
D=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DRY_RUN=1; [ "${1:-}" = --apply ] && { DRY_RUN=0; shift; }
[ $# -gt 0 ] || { echo "usage: janitor.sh [--apply] REPO..." >&2; exit 2; }
export DRY_RUN LEDGER=${JANITOR_LEDGER:-${XDG_STATE_HOME:-$HOME/.local/state}/perun/janitor.ledger}
export REAP_PATTERN=${JANITOR_PATTERN:-'next-server|next dev|vite|webpack|vitest|jest|playwright|pytest|mocha|http\.server|npm run dev|npm test|--headless|headless_shell'}
mkdir -p "$(dirname "$LEDGER")"
[ "$DRY_RUN" = 1 ] && echo "janitor: dry run (pass --apply to act)"
for repo in "$@"; do
  top=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) || { echo "janitor: not a git repo: $repo" >&2; continue; }
  top=$(cd "$top" && pwd -P)
  # linked worktrees only (the first entry is the main checkout)
  wts=$(git -C "$top" worktree list --porcelain | awk '/^worktree /{n++; if(n>1) print substr($0,10)}')
  for r in $(printf '%s\n' "$wts" | while IFS= read -r w; do [ -z "$w" ] || dirname "$w"; done | sort -u); do
    (cd "$top" && ROOT=$r bash "$D/clean_finished.sh")
  done
  printf '%s\n' "$wts" | while IFS= read -r w; do
    [ -d "$w" ] || continue
    ROOT=$w PATTERN=$REAP_PATTERN MAX_AGE_S=${JANITOR_MAX_AGE_S:-7200} bash "$D/reap_own.sh" >/dev/null
  done
done
