#!/usr/bin/env bash
# janitor.sh [--apply | --scheduled | --enable] [--repos-file F] [REPO...] — cleanup that runs without any agent.
# Per repo: clean_finished.sh in STRICT mode (worktree removed only when its PR is MERGED at exactly the local HEAD, nothing
# modified for JANITOR_IDLE_MIN minutes, no .lane-lock/.lane-heartbeat/git lock; everything not in git archived and verified
# first; unpushed or in-use ones kept), after killing agent-spawned dev servers, test runners and headless browsers (exact
# executable allowlist, see reap_own.sh ALLOW) whose cwd is inside a finished worktree; then the same kill on every other
# linked worktree for processes older than the threshold. Kills are verified (SIGTERM, kill -0 poll, SIGKILL after 5s, pid
# identity re-checked). Scope is strictly the linked worktrees of the given repos: the main checkout, other users' processes
# and anything whose cwd is elsewhere are never touched. Every action goes to the ledger.
# Modes: default = dry run printing the plan. --apply = act now. --scheduled (what install_janitor.sh runs) = act only after
# `janitor.sh --enable` was run once; until then it dry-runs and saves the plan to $STATE/janitor.dryrun.log for review.
# Exit 1 when a repo was unusable or gh is missing (the scheduler's log then shows why).
# Env: JANITOR_MAX_AGE_S (7200), JANITOR_IDLE_MIN (60), JANITOR_ALLOW (executable names), JANITOR_STATE
# (default ${XDG_STATE_HOME:-$HOME/.local/state}/perun: ledger, archive/, enabled marker, repos list), GH.
set -uo pipefail
D=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin"   # launchd/cron start with a minimal PATH; gh usually lives here
STATE=${JANITOR_STATE:-${XDG_STATE_HOME:-$HOME/.local/state}/perun}
mkdir -p -m 700 "$STATE"; chmod 700 "$STATE"
mode=dry repos=()
while [ $# -gt 0 ]; do
  case $1 in
    --apply) mode=apply ;; --scheduled) mode=scheduled ;;
    --enable) : >"$STATE/janitor.enabled"; echo "janitor: enabled; scheduled runs now apply"; exit 0 ;;
    --repos-file) shift; while IFS= read -r l; do [ -z "$l" ] || repos+=("$l"); done <"$1" || exit 1 ;;
    -*) echo "usage: janitor.sh [--apply|--scheduled|--enable] [--repos-file F] [REPO...]" >&2; exit 2 ;;
    *) repos+=("$1") ;;
  esac
  shift
done
[ ${#repos[@]} -gt 0 ] || { echo "janitor: no repos given" >&2; exit 2; }
DRY_RUN=1
case $mode in
  apply) DRY_RUN=0 ;;
  scheduled) if [ -e "$STATE/janitor.enabled" ]; then DRY_RUN=0; else exec >>"$STATE/janitor.dryrun.log" 2>&1; echo "== $(date -u +%FT%TZ) (not enabled: run janitor.sh --enable after reviewing)"; fi ;;
esac
export DRY_RUN STRICT=1 LEDGER=$STATE/janitor.ledger ARCHIVE_DIR=${ARCHIVE_DIR:-$STATE/archive} GH=${GH:-gh}
export IDLE_MIN=${JANITOR_IDLE_MIN:-60}
export REAP_ALLOW=${JANITOR_ALLOW:-'next-server next vite vitest jest playwright pytest mocha webpack webpack-dev-server headless_shell chrome-headless-shell chrome chromium chromium-browser'}
rc=0
command -v "$GH" >/dev/null || { echo "janitor: gh not found on PATH; nothing can be judged finished" >&2; exit 1; }
[ "$DRY_RUN" = 0 ] || echo "janitor: dry run (nothing is changed)"
for repo in "${repos[@]}"; do
  top=$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null) && top=$(cd "$top" && pwd -P) || { echo "janitor: not a git repo: $repo" >&2; rc=1; continue; }
  # linked worktrees only (the first entry is the main checkout)
  wts=$(git -C "$top" worktree list --porcelain | awk '/^worktree /{n++; if(n>1) print substr($0,10)}')
  while IFS= read -r r; do
    [ -n "$r" ] || continue
    (cd "$top" && ROOT=$r bash "$D/clean_finished.sh") || rc=1
  done < <(printf '%s\n' "$wts" | while IFS= read -r w; do [ -z "$w" ] || dirname "$w"; done | sort -u)
  while IFS= read -r w; do
    [ -d "$w" ] || continue
    ROOT=$w ALLOW=$REAP_ALLOW MAX_AGE_S=${JANITOR_MAX_AGE_S:-7200} bash "$D/reap_own.sh" >/dev/null || rc=1
  done <<<"$wts"
done
exit $rc
