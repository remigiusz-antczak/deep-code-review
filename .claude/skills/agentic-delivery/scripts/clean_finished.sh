#!/usr/bin/env bash
# clean_finished.sh — remove your own finished worktrees and scratch. Safe to run on every tick.
# A worktree under ROOT is finished when its branch's PR is MERGED or CLOSED (gh pr view), or its branch is
# listed in HANDED_BACK (optional file, one branch per line: lanes that handed back). It is removed unless:
#   - a process has it open (lsof +D), or
#   - it has unpushed commits (commits not on any remote; a MERGED PR whose head is exactly HEAD counts as
#     pushed, since squash-and-delete-branch leaves no remote ref).
# Anything not in git is archived first: `git diff --binary HEAD` goes to ARCHIVE_DIR/<name>.patch and a tar of every
# untracked AND ignored file to <name>.tar (or <name>.N.* when taken; default ${XDG_STATE_HOME:-~/.local/state}/perun/archive,
# mode 0700). Both are written to temp names, read back (tar -t) and only then moved into place; a worktree whose
# archive fails is skipped, never removed. The main worktree and the one you run from are never removed.
# Detached-HEAD worktrees have no branch to judge and are left alone.
# SCRATCH (optional, space-separated absolute paths, no globs): deleted only when it resolves strictly under
# SCRATCH_PREFIX (default ${TMPDIR:-/tmp}) and is neither a repo/worktree path nor an ancestor of one; honours DRY_RUN.
# Env: ROOT (required, absolute dir: only worktrees under it are touched), GH (default gh).
# DRY_RUN=1: print what would happen (in-use checks included), change nothing. LEDGER=file: one tab-separated line per action.
# REAP_PATTERN / REAP_ALLOW: kill matching own processes whose cwd is inside a finished worktree (reap_own.sh, verified kill)
# before the in-use check; any other holder (an editor, a shell) still blocks removal.
# STRICT=1 (janitor): finished means PR MERGED with headRefOid == local HEAD (CLOSED and HANDED_BACK do not count), no file
# changed in the last IDLE_MIN minutes (default 60; 0 disables; .git, node_modules, .next ignored), and no `.lane-lock`,
# `.lane-heartbeat` or `git worktree lock` marker. Every condition is re-checked right before removal.
# Prints "removed=N skipped=M archived=K".
set -euo pipefail
: "${ROOT:?set ROOT to your own worktree tree}"
ROOT=$(cd "$ROOT" && pwd -P); GH=${GH:-gh}; STRICT=${STRICT:-0}; IDLE=${IDLE_MIN:-60}
AR=${ARCHIVE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/perun/archive}; DRY=${DRY_RUN:-0}
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
top=$(git rev-parse --show-toplevel); top=$(cd "$top" && pwd -P)
main=$(git worktree list --porcelain | awk 'NR==1{print substr($0,10)}'); main=$(cd "$main" && pwd -P)
command -v lsof >/dev/null || { echo "clean_finished: lsof missing; cannot tell if a worktree is in use, removing nothing" >&2; exit 2; }
rm=0 sk=0 ar=0
led() { [ -z "${LEDGER:-}" ] || [ "$DRY" = 1 ] || printf '%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$1" "$2" "${3:-}" >>"$LEDGER"; }
# 0 = no live-agent sign: no marker file, nothing modified within IDLE minutes
quiet() {
  local gd; gd=$(git -C "$1" rev-parse --absolute-git-dir)
  { [ ! -e "$1/.lane-lock" ] && [ ! -e "$1/.lane-heartbeat" ] && [ ! -e "$gd/locked" ]; } || return 1
  [ "$IDLE" -gt 0 ] || return 0
  [ -z "$(find "$1" \( -name .git -o -name node_modules -o -name .next \) -prune -o -type f -mmin "-$IDLE" -print -quit 2>/dev/null)" ] &&
    [ -z "$(find "$gd/index" "$gd/HEAD" -mmin "-$IDLE" -print 2>/dev/null)" ]
}
proof() {  # $1 wt, $2 branch; sets state/head; 0 = finished
  state="" head=""
  read -r state head < <("$GH" pr view "$2" --json state,headRefOid -q '.state+" "+.headRefOid' </dev/null 2>/dev/null || true) || true
  if [ "$STRICT" = 1 ]; then
    [ "$state" = MERGED ] && [ "$head" = "$(git -C "$1" rev-parse HEAD)" ] && quiet "$1"; return
  fi
  if [ "$state" != MERGED ] && [ "$state" != CLOSED ]; then
    { [ -n "${HANDED_BACK:-}" ] && grep -qxF "$2" "$HANDED_BACK" 2>/dev/null; } || return 1
  fi
}
archive() {  # $1 wt: 0 = nothing to save, or saved and verified
  local wt=$1 n f i=0 t; n=$(basename "$wt")
  [ -n "$(git -C "$wt" status --porcelain --ignored)" ] || return 0
  mkdir -p -m 700 "$AR"; chmod 700 "$AR"
  f="$AR/$n"; while [ -e "$f.patch" ] || [ -e "$f.tar" ]; do i=$((i+1)); f="$AR/$n.$i"; done  # same-named worktrees must not overwrite
  t=$(mktemp -d "$AR/.tmp.XXXXXX")
  if git -C "$wt" diff --binary HEAD >"$t/p" && git -C "$wt" ls-files -z --others >"$t/l" &&
     { echo "# untracked and ignored (contents in the .tar):"; tr '\0' '\n' <"$t/l"; } >>"$t/p" &&
     { [ ! -s "$t/l" ] && tar -cf "$t/t" -T /dev/null || (cd "$wt" && tar -cf "$t/t" --null -T "$t/l"); } &&
     tar -tf "$t/t" >/dev/null; then
    mv "$t/p" "$f.patch" && mv "$t/t" "$f.tar" && rm -rf "$t" && ar=$((ar+1)) && led archive "$wt" "$f" && return 0
  fi
  rm -rf "$t"; return 1
}
while IFS=$'\t' read -r wt br; do
  wt=$(cd "$wt" 2>/dev/null && pwd -P) || continue
  [ "$wt" != "$top" ] && [ "$wt" != "$main" ] || continue
  case "$wt" in "$ROOT"/*) ;; *) continue ;; esac
  proof "$wt" "$br" || continue
  h0=$(git -C "$wt" rev-parse HEAD)
  if [ "$STRICT" != 1 ] && { [ "$state" != MERGED ] || [ "$head" != "$h0" ]; }; then
    [ "$(git -C "$wt" rev-list --count HEAD --not --remotes)" = 0 ] || { sk=$((sk+1)); led skip "$wt" unpushed; continue; }
  fi
  reaped=""
  if [ -n "${REAP_PATTERN:-}${REAP_ALLOW:-}" ]; then
    reaped=$(ROOT=$wt PATTERN=${REAP_PATTERN:-} ALLOW=${REAP_ALLOW:-} MAX_AGE_S=0 bash "$HERE/reap_own.sh" 2>&1 >/dev/null | sed -n 's/^would reap pid=\([0-9]*\) .*/\1/p') || true
  fi
  holders=$(lsof -t +D "$wt" 2>/dev/null || true)
  if [ -n "$holders" ] && [ -n "${REAP_PATTERN:-}${REAP_ALLOW:-}" ]; then
    if [ "$DRY" = 1 ]; then   # would-be-killed servers and their direct children do not count as holders
      keep=""; for h in $holders; do
        case " $(echo $reaped) " in *" $h "*|*" $(ps -o ppid= -p "$h" 2>/dev/null | tr -d ' ') "*) ;; *) keep="$keep $h" ;; esac
      done; holders=$keep
    else   # a killed server's children exit a moment later
      for _ in 1 2 3 4 5 6; do [ -n "$holders" ] || break; sleep 0.5; holders=$(lsof -t +D "$wt" 2>/dev/null || true); done
    fi
  fi
  if [ -n "$holders" ]; then sk=$((sk+1)); led skip "$wt" in-use; [ "$DRY" != 1 ] || echo "would skip $wt (in use)"; continue; fi
  if [ "$DRY" = 1 ]; then echo "would remove $wt"; rm=$((rm+1)); continue; fi
  archive "$wt" || { sk=$((sk+1)); led skip "$wt" archive-failed; continue; }
  # last look: still finished, same HEAD, still quiet, nobody opened it meanwhile
  if ! proof "$wt" "$br" || [ "$(git -C "$wt" rev-parse HEAD)" != "$h0" ] || [ -n "$(lsof -t +D "$wt" 2>/dev/null | head -1)" ]; then
    sk=$((sk+1)); led skip "$wt" changed-before-removal; continue
  fi
  if git worktree remove --force "$wt" >/dev/null 2>&1; then rm=$((rm+1)); led remove "$wt"; else sk=$((sk+1)); led skip "$wt" remove-failed; fi
done < <(git worktree list --porcelain | awk '/^worktree /{w=substr($0,10)} /^branch /{print w "\t" substr($0,19)}')
set -f
for s in ${SCRATCH:-}; do
  case "$s" in /*) ;; *) continue ;; esac
  [ -d "$s" ] || continue
  r=$(cd "$s" && pwd -P); P=$(cd "${SCRATCH_PREFIX:-${TMPDIR:-/tmp}}" && pwd -P)
  case "$r" in "$P"/?*) ;; *) echo "clean_finished: SCRATCH $s not under $P, kept" >&2; continue ;; esac
  keep=0
  while IFS= read -r w; do
    case "$w/" in "$r"/*) keep=1 ;; esac   # a worktree (or ROOT) lives at or under it
    case "$r/" in "$w"/*) keep=1 ;; esac
  done < <(git worktree list --porcelain | sed -n 's/^worktree //p'; echo "$ROOT")
  [ $keep = 0 ] || { echo "clean_finished: SCRATCH $s holds or sits in a worktree, kept" >&2; continue; }
  if [ "$DRY" = 1 ]; then echo "would delete scratch $r"; else rm -rf "$r"; led scratch "$r"; fi
done
echo "removed=$rm skipped=$sk archived=$ar"
