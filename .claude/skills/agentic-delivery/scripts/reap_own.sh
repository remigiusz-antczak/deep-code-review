#!/usr/bin/env bash
# reap_own.sh — kill your own dev servers older than MAX_AGE_S whose cwd is under ROOT (your own lane or
# session tree). Never kills by name alone: a process must be owned by the current user AND have its cwd
# under ROOT, so other lanes' and other users' servers are untouchable. Safe to run on every tick.
# A kill is verified: SIGTERM, wait up to KILL_WAIT_S (default 5) polling kill -0, then SIGKILL; a process still
# alive after that is not counted as reaped (a warning goes to stderr). Prints "reaped=N".
#
# Env: ROOT (required, absolute dir), PATTERN (pgrep -f regex, default 'next-server|next dev'),
# KEEP (optional dir under ROOT whose servers are spared), MAX_AGE_S (default 7200: idle for 2 hours),
# QA_PORTS (optional space-separated TCP ports: an own listener there with cwd under ROOT is reaped too,
# since a leftover server on a QA port makes the QA script skip its browser half), KILL_WAIT_S.
#
# ALLOW (space-separated executable names, janitor): replaces PATTERN. A process matches only when its argv0 basename is in ALLOW,
# or argv0 is an interpreter (sh bash node python python3 bun deno npx) and argv1's basename is; a browser (chrome chromium
# headless_shell ...) additionally needs an exact --headless argument. Editors and shells that merely mention a name never match.
# Before each kill the pid's cwd and start time are re-read and must equal the values seen when it was selected (PID reuse).
# DRY_RUN=1: print "would reap ..." instead of killing. LEDGER=file: append one tab-separated line per kill.
#
# --report: cross-session, read-only, never kills. Lists every own process matching PATTERN or listening on a
# TCP port as "<cwd> pid=<n> age=<s>s" sorted by worktree path (ROOT optional: unset = all of them), then
# "orphans=N", the free RAM, and a "FINDING hot" line for each own process using >= CPU_HOT percent CPU
# (default 50) for more than MAX_AGE_S. Use it as the hand-back check (ROOT=<lane worktree>: orphans=0 means no
# server or listener is left under it) and as the coordinator-wake check.
set -euo pipefail
REPORT=0; [ "${1:-}" = "--report" ] && REPORT=1
if [ $REPORT = 1 ]; then ROOT=${ROOT:-}; else : "${ROOT:?set ROOT to your own tree}"; fi
[ -z "$ROOT" ] || ROOT=$(cd "$ROOT" && pwd -P)  # lsof reports resolved paths; a symlinked ROOT would match nothing
KEEP=${KEEP:+$(cd "$KEEP" && pwd -P)}; PATTERN=${PATTERN:-next-server|next dev}; KEEP=${KEEP:-}
MAX=${MAX_AGE_S:-7200}; WAIT=${KILL_WAIT_S:-5}
alive() { kill -0 "$1" 2>/dev/null && [ "$(ps -o stat= -p "$1" 2>/dev/null | cut -c1)" != Z ]; }
age() { { ps -o etime= -p "$1" 2>/dev/null || true; } | tr -d ' ' | awk -F'[-:]' '{n=NF; s=$n+60*$(n-1); if(n>=3)s+=3600*$(n-2); if(n>=4)s+=86400*$(n-3); print s}'; }
cwd_of() { lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -1; }
same() { [ "$(cwd_of "$1")" = "$2" ] && [ "$(ps -o lstart= -p "$1" 2>/dev/null)" = "$3" ]; }
allowed() {  # $1 pid
  local a0 a1 rest args b0 b1; args=$(ps -o args= -p "$1" 2>/dev/null) || return 1
  read -r a0 a1 rest <<<"$args"; b0=$(basename -- "${a0:-x}"); b1=$(basename -- "${a1:-x}")
  case " $ALLOW " in *" $b0 "*) ;; *) case "$b0" in sh|bash|node|python|python3|bun|deno|npx) case " $ALLOW " in *" $b1 "*) ;; *) return 1 ;; esac ;; *) return 1 ;; esac ;; esac
  case "$b0$b1" in *chrom*|*headless*) case " $args " in *" --headless "*|*" --headless="*|*" --headless=new "*) ;; *) return 1 ;; esac ;; esac
}
kill_verified() {  # $1 pid, $2 cwd, $3 start time seen at selection
  local i; same "$1" "$2" "$3" || return 1; kill "$1" 2>/dev/null || true
  for ((i = 0; i < WAIT * 4; i++)); do alive "$1" || return 0; sleep 0.25; done
  same "$1" "$2" "$3" && kill -9 "$1" 2>/dev/null || true; sleep 0.2
  if alive "$1"; then echo "WARN: pid $1 survived SIGKILL" >&2; return 1; fi
}
ALLOW=${ALLOW:-}
if [ -n "$ALLOW" ]; then   # cheap pre-filter on the names, then the exact argv check per candidate
  PIDS=$(ps -u "$(id -u)" -o pid=,args= | grep -F $(for a in $ALLOW; do printf -- '-e %s ' "$a"; done) | awk '{print $1}' | while read -r q; do allowed "$q" && echo "$q"; done || true)
else PIDS=$(pgrep -u "$(id -u)" -f "$PATTERN" || true); fi
if [ $REPORT = 1 ]; then PIDS="$PIDS $(lsof -t -a -u "$(id -u)" -iTCP -sTCP:LISTEN 2>/dev/null || true)"; fi
for q in ${QA_PORTS:-}; do PIDS="$PIDS $(lsof -t -a -u "$(id -u)" -iTCP:"$q" -sTCP:LISTEN 2>/dev/null || true)"; done
n=0; rows=""
for P in $(printf '%s\n' $PIDS | sort -u); do
  [ "$P" != "$$" ] || continue
  C=$(cwd_of "$P"); S=$(ps -o lstart= -p "$P" 2>/dev/null || true)
  if [ -n "$ROOT" ]; then
    case "$C" in "$ROOT"|"$ROOT"/*) ;; *) continue ;; esac
  fi
  if [ -n "$KEEP" ]; then case "$C" in "${KEEP%/}"|"${KEEP%/}"/*) continue ;; esac; fi
  E=$(age "$P")
  if [ $REPORT = 1 ]; then rows="$rows$C pid=$P age=${E:-0}s"$'\n'; n=$((n+1)); continue; fi
  if [ "${E:-0}" -gt "$MAX" ]; then
    if [ "${DRY_RUN:-0}" = 1 ]; then echo "would reap pid=$P cwd=$C age=${E}s" >&2; n=$((n+1))
    elif kill_verified "$P" "$C" "$S"; then n=$((n+1)); [ -z "${LEDGER:-}" ] || printf '%s\treap\t%s\tpid=%s age=%ss\n' "$(date -u +%FT%TZ)" "$C" "$P" "$E" >>"$LEDGER"; fi
  fi
done
if [ $REPORT = 0 ]; then echo "reaped=$n"; exit 0; fi
printf '%s' "$rows" | sort
echo "orphans=$n"
if [ -r /proc/meminfo ]; then echo "ram_free_mb=$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)"
elif command -v vm_stat >/dev/null; then
  echo "ram_free_mb=$(vm_stat | awk '/page size of/{s=$8} /Pages (free|inactive)/{p+=$3} END{print int(p*s/1048576)}')"
fi
ps -u "$(id -u)" -o pid=,pcpu=,comm= | while read -r p c m; do
  [ "${c%.*}" -ge "${CPU_HOT:-50}" ] 2>/dev/null || continue
  e=$(age "$p"); if [ "${e:-0}" -gt "$MAX" ]; then echo "FINDING hot pid=$p cpu=$c% age=${e}s $m"; fi
done
