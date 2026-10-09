#!/usr/bin/env bash
# train_flake.sh — triage NEW gate failures into REAL vs FLAKE by re-running each alone.
# Usage: train_flake.sh <failed-ids-file> [baseline-ids-file]     (one test id per line)
# Env: RERUN_CMD (required; run via bash -c with TEST=<id>; exit 0 = pass), FLAKE_RUNS (default 3), FLAKE_REAL_AT (default 2).
# An id already failing on the base (baseline file) is skipped: it is not new. A new id is REAL only when it fails at least
# FLAKE_REAL_AT of FLAKE_RUNS isolated re-runs; stops early once the verdict is fixed. Prints "REAL <id>" / "FLAKE <id>"
# lines (flakes are reported separately, never blamed on a PR). Exit: 0 no REAL ids, 1 at least one REAL, 2 usage or bad FLAKE_RUNS/FLAKE_REAL_AT (fails closed).
# Same-host baseline: a non-empty baseline file must start with the header `# baseline host=<h> inv=<hash>` written by
# `train_flake.sh --record <failing-ids-file> > baseline` on the machine and invocation that measured it. The current host
# (FLAKE_HOST, default hostname -s) and invocation hash (sha256 of FLAKE_INVOCATION, default BROWSER_CMD) must match, else exit 2:
# a baseline from another machine or another command line makes failures look new (or hides new ones). Missing header = refused.
# Fresh store: FLAKE_SETUP_CMD (optional, via bash -c) runs before EVERY isolated re-run with TEST=<id>, FLAKE_RUN=<n> and
# FLAKE_STORE=<fresh path, not yet created>; it must create/seed that store, and RERUN_CMD sees the same FLAKE_STORE. A re-run that
# reuses the run's own store fakes real failures. Hook failure exits 2 (fails closed). Retries are per test title, never per file.
set -uo pipefail
inv=$(printf %s "${FLAKE_INVOCATION:-${BROWSER_CMD:-}}" | { shasum -a 256 2>/dev/null || sha256sum; } | cut -c1-16)
host=${FLAKE_HOST:-$(hostname -s)}
if [ "${1:-}" = --record ]; then
  [ -n "${2:-}" ] && [ -n "${FLAKE_INVOCATION:-${BROWSER_CMD:-}}" ] || { echo "usage: FLAKE_INVOCATION=<cmd> train_flake.sh --record <failing-ids-file>" >&2; exit 2; }
  echo "# baseline host=$host inv=$inv"; cat -- "$2"; exit 0
fi
[ $# -ge 1 ] && [ -n "${RERUN_CMD:-}" ] || { echo "usage: RERUN_CMD=... train_flake.sh <failed-ids> [baseline-ids]" >&2; exit 2; }
runs=${FLAKE_RUNS:-3} need=${FLAKE_REAL_AT:-2} real=0
case $runs$need in ''|*[!0-9]*) echo "train_flake: FLAKE_RUNS/FLAKE_REAL_AT must be integers" >&2; exit 2 ;; esac
[ "$runs" -ge 1 ] && [ "$need" -ge 1 ] && [ "$need" -le "$runs" ] || { echo "train_flake: need 1 <= FLAKE_REAL_AT <= FLAKE_RUNS" >&2; exit 2; }
if [ -s "${2:-/dev/null}" ] && [ "$(head -n1 "$2")" != "# baseline host=$host inv=$inv" ]; then
  echo "train_flake: baseline $2 not recorded on this host with this invocation (want '# baseline host=$host inv=$inv'); refusing to compare" >&2; exit 2
fi
store=${TMPDIR:-/tmp}/flake-store.$$ c=0
while IFS= read -r id; do
  [ -n "$id" ] || continue
  [ -z "${2:-}" ] || ! grep -qxF -- "$id" "$2" 2>/dev/null || continue
  f=0 p=0
  for n in $(seq "$runs"); do
    export TEST=$id FLAKE_RUN=$n FLAKE_STORE=$store.$((++c))
    [ -z "${FLAKE_SETUP_CMD:-}" ] || bash -c "$FLAKE_SETUP_CMD" >/dev/null 2>&1 </dev/null || { echo "train_flake: FLAKE_SETUP_CMD failed for $id" >&2; exit 2; }
    if bash -c "$RERUN_CMD" >/dev/null 2>&1 </dev/null; then p=$((p + 1)); else f=$((f + 1)); fi
    [ "$f" -ge "$need" ] || [ "$p" -gt $((runs - need)) ] && break
  done
  if [ "$f" -ge "$need" ]; then echo "REAL $id"; real=1; else echo "FLAKE $id (failed $f of $((f + p)) alone)"; fi
done <"$1"
exit $real
