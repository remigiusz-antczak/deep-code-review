#!/usr/bin/env bash
# Tests for janitor.sh and install_janitor.sh: temp repos, fake processes (a sleep-loop script named next-server
# whose cwd is inside a worktree), dry-run vs apply, unpushed-commit skip, out-of-scope process untouched, idempotent install.
# Plain bash; prints PASS/FAIL lines and "N passed, M failed"; exits non-zero on any failure. Writes only under $WORK.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SC="$ROOT/.claude/skills/agentic-delivery/scripts"
WORK="$(cd "$(mktemp -d "${TMPDIR:-/tmp}/dcr-test-janitor.XXXXXX")" && pwd -P)"
PIDS=""
cleanup() { for p in $PIDS; do kill -9 "$p" 2>/dev/null; done; rm -rf "$WORK"; }
trap cleanup EXIT
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
pass=0 fail=0
ok() { if [ "$1" -eq 0 ]; then echo "PASS  $2"; pass=$((pass + 1)); else echo "FAIL  $2"; fail=$((fail + 1)); fi; }
alive() { kill -0 "$1" 2>/dev/null; }
R="$WORK/clone"
g() { git -C "$R" -c user.email=t@example.com -c user.name=T "$@"; }
git init -q --bare "$WORK/origin.git" -b main; git clone -q "$WORK/origin.git" "$R" 2>/dev/null
g commit -q --allow-empty -m base; g push -q origin HEAD:main; B=$(g rev-parse HEAD)
mkdir -p "$WORK/bin" "$WORK/wts" "$WORK/outside"
# gh stub: branch "live" is OPEN, "unp" is CLOSED at an unknown head, everything else MERGED at its head
cat >"$WORK/bin/gh" <<'EOF'
#!/usr/bin/env bash
case "$3" in live) echo "OPEN x" ;; unp) echo "CLOSED deadbeef" ;;
  *) wt=$(git worktree list --porcelain | awk -v b="refs/heads/$3" '/^worktree /{w=substr($0,10)} $0 == "branch " b {print w}'); echo "MERGED $(git -C "$wt" rev-parse HEAD)" ;; esac
EOF
chmod +x "$WORK/bin/gh"
g worktree add -q -b done "$WORK/wts/done" "$B"
g worktree add -q -b unp "$WORK/wts/unp" "$B"; git -C "$WORK/wts/unp" -c user.email=t@example.com -c user.name=T commit -q --allow-empty -m local
g worktree add -q -b live "$WORK/wts/live" "$B"
spawn() { printf '#!/bin/sh\nwhile :; do sleep 1; done\n' >"$1/next-server"; chmod +x "$1/next-server"; (cd "$1" && exec ./next-server) >/dev/null 2>&1 & echo $!; }
PD=$(spawn "$WORK/wts/done"); PU=$(spawn "$WORK/wts/unp"); PL=$(spawn "$WORK/wts/live"); PO=$(spawn "$WORK/outside")
PIDS="$PD $PU $PL $PO"; sleep 2
export GH="$WORK/bin/gh" ARCHIVE_DIR="$WORK/ar" JANITOR_LEDGER="$WORK/ledger" JANITOR_MAX_AGE_S=100000

out=$(bash "$SC/janitor.sh" "$R" 2>&1)
[ -d "$WORK/wts/done" ] && alive "$PD" && alive "$PL" && [ ! -e "$WORK/ledger" -o ! -s "$WORK/ledger" ] && grep -q "would remove $WORK/wts/done" <<<"$out"
ok $? "dry run (default): prints plan, removes nothing, kills nothing, writes no ledger"

bash "$SC/janitor.sh" --apply "$R" >/dev/null 2>&1
[ ! -d "$WORK/wts/done" ]; ok $? "apply: finished worktree removed"
sleep 0.5; ! alive "$PD"; ok $? "apply: process with cwd in the finished worktree killed (verified dead)"
[ -d "$WORK/wts/unp" ] && alive "$PU"; ok $? "apply: unpushed-commit worktree kept, its process untouched"
[ -d "$WORK/wts/live" ] && alive "$PL"; ok $? "apply: live worktree process younger than threshold kept"
alive "$PO"; ok $? "apply: out-of-scope process (cwd outside every worktree) untouched"
grep -q "remove	$WORK/wts/done" "$WORK/ledger" && grep -q "reap	" "$WORK/ledger" && grep -q "skip	$WORK/wts/unp	unpushed" "$WORK/ledger"
ok $? "ledger records removal, process reap and the unpushed skip"

JANITOR_MAX_AGE_S=1 bash "$SC/janitor.sh" --apply "$R" >/dev/null 2>&1
sleep 0.5; ! alive "$PL" && alive "$PO" && [ -d "$WORK/wts/live" ]; ok $? "idle live-worktree process past threshold reaped; worktree and outsider kept"

# --- install_janitor ---
I="$SC/install_janitor.sh"; export JANITOR_HOME="$WORK/home" JANITOR_NO_LOAD=1
JANITOR_KIND=launchd bash "$I" --check >/dev/null 2>&1; [ $? -eq 1 ]; ok $? "check: reports not installed (exit 1)"
JANITOR_KIND=launchd bash "$I" "$R" >/dev/null; P="$WORK/home/Library/LaunchAgents/com.perun.janitor.plist"; s1=$(cksum <"$P")
JANITOR_KIND=launchd bash "$I" "$R" >/dev/null; s2=$(cksum <"$P")
[ "$s1" = "$s2" ] && grep -q "<integer>900</integer>" "$P" && grep -q "janitor.sh" "$P" && grep -q -- "--apply" "$P"; ok $? "launchd: plist written, 15-minute interval, idempotent"
JANITOR_KIND=launchd bash "$I" --check >/dev/null 2>&1; ok $? "check: reports installed"
JANITOR_KIND=launchd bash "$I" --uninstall >/dev/null; [ ! -e "$P" ]; ok $? "launchd: uninstall removes the plist"
JANITOR_KIND=systemd bash "$I" "$R" >/dev/null; U="$WORK/home/.config/systemd/user"
grep -q "OnUnitActiveSec=15min" "$U/com.perun.janitor.timer" && grep -q "ExecStart=.*janitor.sh" "$U/com.perun.janitor.service"; ok $? "systemd: timer and service written"
JANITOR_KIND=systemd bash "$I" --uninstall >/dev/null; [ ! -e "$U/com.perun.janitor.timer" ]; ok $? "systemd: uninstall removes the unit files"
JANITOR_KIND=cron bash "$I" "$R" | grep -q '^\*/15 \* \* \* \* '; ok $? "cron: prints the 15-minute crontab line"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
