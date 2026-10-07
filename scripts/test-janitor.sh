#!/usr/bin/env bash
# Tests for janitor.sh, install_janitor.sh and the clean_finished.sh / reap_own.sh hardening they rely on: temp repos, fake
# processes (shell scripts named like dev servers whose cwd is inside a worktree), dry-run vs apply, the enable gate, strict
# finished-proof (stale PR, idle time, lock marker), full archive (untracked + ignored), SCRATCH guards, argv allowlist,
# scheduler files and their escaping. Plain bash; prints PASS/FAIL lines and "N passed, M failed"; writes only under $WORK.
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
mkrepo() {  # $1 dir
  git init -q --bare "$1.git" -b main; git clone -q "$1.git" "$1" 2>/dev/null
  git -C "$1" -c user.email=t@example.com -c user.name=T commit -q --allow-empty -m base; git -C "$1" push -q origin HEAD:main
}
R="$WORK/clone"; mkrepo "$R"; B=$(git -C "$R" rev-parse HEAD)
g() { git -C "$R" -c user.email=t@example.com -c user.name=T "$@"; }
mkdir -p "$WORK/bin" "$WORK/wts" "$WORK/outside"
# gh stub: live is OPEN, unp is CLOSED, stale is MERGED at an old head, everything else MERGED at its own head
cat >"$WORK/bin/gh" <<'EOF'
#!/usr/bin/env bash
case "$3" in live) echo "OPEN x" ;; unp) echo "CLOSED deadbeef" ;; stale) echo "MERGED deadbeef" ;;
  *) wt=$(git worktree list --porcelain | awk -v b="refs/heads/$3" '/^worktree /{w=substr($0,10)} $0 == "branch " b {print w}'); echo "MERGED $(git -C "$wt" rev-parse HEAD)" ;; esac
EOF
chmod +x "$WORK/bin/gh"
for b in done unp live stale lock busy; do g worktree add -q -b $b "$WORK/wts/$b" "$B"; done
git -C "$WORK/wts/unp" -c user.email=t@example.com -c user.name=T commit -q --allow-empty -m local
touch "$WORK/wts/lock/.lane-lock"
echo secret >"$WORK/wts/done/notes.txt"; echo TOKEN=1 >"$WORK/wts/done/.env"; echo .env >>"$R/.git/info/exclude"
# fake processes: a dev server (matches the allowlist), an editor merely mentioning vite, a server outside every worktree
spawn() { printf '#!/bin/sh\nwhile :; do sleep 1; done\n' >"$1/$2"; chmod +x "$1/$2"; (cd "$1" && exec ./"$2" "${@:3}") >/dev/null 2>&1 & echo $!; }
PD=$(spawn "$WORK/wts/done" next-server); PU=$(spawn "$WORK/wts/unp" next-server); PL=$(spawn "$WORK/wts/live" next-server)
PV=$(spawn "$WORK/wts/busy" vim vite.config.ts); PO=$(spawn "$WORK/outside" next-server)
PIDS="$PD $PU $PL $PV $PO"; sleep 2
export GH="$WORK/bin/gh" JANITOR_STATE="$WORK/state" JANITOR_MAX_AGE_S=100000 JANITOR_IDLE_MIN=0
LED="$WORK/state/janitor.ledger"

out=$(bash "$SC/janitor.sh" "$R" 2>&1)
[ -d "$WORK/wts/done" ] && alive "$PD" && [ ! -s "$LED" ] && grep -q "would remove $WORK/wts/done" <<<"$out"
ok $? "dry run (default): prints plan, removes nothing, kills nothing, writes no ledger"
grep -q "would skip $WORK/wts/busy (in use)" <<<"$out" && ! grep -q "would remove $WORK/wts/busy" <<<"$out"
ok $? "dry run is truthful: a worktree an editor holds open is planned as skipped, not removed"

JANITOR_IDLE_MIN=60 bash "$SC/janitor.sh" --apply "$R" >/dev/null 2>&1
[ -d "$WORK/wts/done" ] && alive "$PD"; ok $? "recently modified worktree is not finished (idle minimum), nothing killed"

bash "$SC/janitor.sh" --apply "$R" >/dev/null 2>&1
[ ! -d "$WORK/wts/done" ]; ok $? "apply: finished worktree removed"
sleep 0.5; ! alive "$PD"; ok $? "apply: dev server with cwd in the finished worktree killed"
[ -d "$WORK/wts/unp" ] && alive "$PU"; ok $? "apply: worktree with an unpushed/closed PR kept, process untouched"
[ -d "$WORK/wts/stale" ]; ok $? "apply: stale MERGED PR (head != local HEAD) is not proof; worktree kept"
[ -d "$WORK/wts/lock" ]; ok $? "apply: .lane-lock marker keeps the worktree"
[ -d "$WORK/wts/busy" ] && alive "$PV"; ok $? "apply: editor whose argv merely mentions vite is never killed; its worktree is kept"
alive "$PL" && alive "$PO"; ok $? "apply: young process in a live worktree and an out-of-scope process untouched"
A=$(ls "$WORK"/state/archive/done.tar 2>/dev/null)
[ -n "$A" ] && tar -tf "$A" | grep -q notes.txt && tar -tf "$A" | grep -q '\.env' && [ -f "$WORK/state/archive/done.patch" ]
ok $? "archive holds untracked and ignored file contents plus the binary patch"
perm() { python3 -c 'import os,sys;print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$1"; }
[ "$(perm "$WORK/state/archive")" = 0o700 ] && [ "$(perm "$WORK/state")" = 0o700 ]
ok $? "archive and state dirs are mode 0700"
grep -q "remove	$WORK/wts/done" "$LED" && grep -q "reap	" "$LED" && grep -q "archive	$WORK/wts/done" "$LED"
ok $? "ledger records archive, reap and removal"

JANITOR_MAX_AGE_S=1 bash "$SC/janitor.sh" --apply "$R" >/dev/null 2>&1
sleep 0.5; ! alive "$PL" && alive "$PO" && alive "$PV" && [ -d "$WORK/wts/live" ]; ok $? "idle live-worktree dev server past threshold reaped; editor, worktree, outsider kept"

# enable gate for the scheduled path
g worktree add -q -b sched "$WORK/wts/sched" "$B"
bash "$SC/janitor.sh" --scheduled "$R" >/dev/null 2>&1
[ -d "$WORK/wts/sched" ] && grep -q "would remove $WORK/wts/sched" "$WORK/state/janitor.dryrun.log"; ok $? "scheduled run before --enable only dry-runs and saves the plan"
bash "$SC/janitor.sh" --enable >/dev/null; bash "$SC/janitor.sh" --scheduled "$R" >/dev/null 2>&1
[ ! -d "$WORK/wts/sched" ]; ok $? "scheduled run applies after --enable"

# clean_finished: failed archive keeps the worktree; SCRATCH guards; symlinked worktree path
g worktree add -q -b bad "$WORK/wts/bad" "$B"; echo x >"$WORK/wts/bad/f"; git -C "$WORK/wts/bad" add f
g config diff.external /bin/false
o=$(cd "$R" && ROOT="$WORK/wts" ARCHIVE_DIR="$WORK/ar2" STRICT=1 IDLE_MIN=0 bash "$SC/clean_finished.sh" 2>/dev/null)
g config --unset diff.external
[ -d "$WORK/wts/bad" ] && grep -q "removed=0" <<<"$o"; ok $? "failing archive (diff error) keeps the worktree instead of removing it"
mkdir -p "$WORK/pfx/sc/a" "$WORK/pfx/sc/b"
(cd "$R" && ROOT="$WORK/wts" GH="$WORK/bin/gh" STRICT=1 IDLE_MIN=0 SCRATCH_PREFIX="$WORK/pfx" SCRATCH="$WORK/pfx/sc/*" bash "$SC/clean_finished.sh" >/dev/null 2>&1)
[ -d "$WORK/pfx/sc/a" ] && [ -d "$WORK/pfx/sc/b" ]; ok $? "SCRATCH glob is not expanded"
(cd "$R" && ROOT="$WORK/wts" GH="$WORK/bin/gh" SCRATCH_PREFIX="$WORK" SCRATCH="$WORK/wts" bash "$SC/clean_finished.sh" >/dev/null 2>&1)
[ -d "$WORK/wts/unp" ]; ok $? "SCRATCH equal to the worktree root is refused"
(cd "$R" && ROOT="$WORK/wts" GH="$WORK/bin/gh" SCRATCH_PREFIX="$WORK/pfx" SCRATCH="$WORK/wts/unp $WORK" bash "$SC/clean_finished.sh" >/dev/null 2>&1)
[ -d "$WORK/wts/unp" ] && [ -d "$WORK/pfx" ]; ok $? "SCRATCH outside the prefix, a worktree, or an ancestor of one is refused"
(cd "$R" && ROOT="$WORK/wts" GH="$WORK/bin/gh" DRY_RUN=1 SCRATCH_PREFIX="$WORK/pfx" SCRATCH="$WORK/pfx/sc/a" bash "$SC/clean_finished.sh" >/dev/null 2>&1)
[ -d "$WORK/pfx/sc/a" ]; ok $? "SCRATCH honours DRY_RUN"
(cd "$R" && ROOT="$WORK/wts" GH="$WORK/bin/gh" SCRATCH_PREFIX="$WORK/pfx" SCRATCH="$WORK/pfx/sc/a" bash "$SC/clean_finished.sh" >/dev/null 2>&1)
[ ! -d "$WORK/pfx/sc/a" ] && [ -d "$WORK/pfx/sc/b" ]; ok $? "SCRATCH under the prefix is deleted"
mkdir -p "$WORK/real"; ln -s "$WORK/real" "$WORK/link"
g worktree add -q -b symw "$WORK/link/symw" "$B"
(cd "$R" && ROOT="$WORK/link" GH="$WORK/bin/gh" STRICT=1 IDLE_MIN=0 ARCHIVE_DIR="$WORK/ar3" bash "$SC/clean_finished.sh" >/dev/null 2>&1)
[ ! -d "$WORK/real/symw" ]; ok $? "worktree registered through a symlinked path is still cleaned"

# whitespace in a worktree parent dir must not abort the run or skip later repos
R2="$WORK/clone2"; mkrepo "$R2"; B2=$(git -C "$R2" rev-parse HEAD); mkdir -p "$WORK/my wts"
git -C "$R2" worktree add -q -b ws "$WORK/my wts/feat" "$B2"
bash "$SC/janitor.sh" --apply "$R2" "$R" >/dev/null 2>&1; [ ! -d "$WORK/my wts/feat" ]; ok $? "janitor handles a worktree parent dir containing spaces"
bash "$SC/janitor.sh" --apply "$WORK/not-a-repo" "$R2" >/dev/null 2>&1; [ $? -eq 1 ]; ok $? "janitor exits non-zero for an unusable repo but still visits the rest"
PATH=/usr/bin:/bin GH=nonexistent-gh bash "$SC/janitor.sh" --apply "$R" >/dev/null 2>&1; [ $? -eq 1 ]; ok $? "janitor fails loudly when gh is missing"

# --- install_janitor ---
I="$SC/install_janitor.sh"; export JANITOR_HOME="$WORK/home" JANITOR_NO_LOAD=1 JANITOR_STATE="$WORK/istate"
JANITOR_KIND=launchd bash "$I" --check >/dev/null 2>&1; [ $? -eq 1 ]; ok $? "check: reports not installed (exit 1)"
JANITOR_KIND=launchd bash "$I" "$R" >/dev/null; P="$WORK/home/Library/LaunchAgents/com.perun.janitor.plist"; s1=$(cksum <"$P")
JANITOR_KIND=launchd bash "$I" "$R" >/dev/null; s2=$(cksum <"$P")
[ "$s1" = "$s2" ] && grep -q "<integer>900</integer>" "$P" && grep -q -- "--scheduled" "$P" && ! grep -q -- "--apply" "$P" && ! grep -q RunAtLoad "$P"
ok $? "launchd: 15-minute plist, scheduled (enable-gated) mode, no run at load, idempotent"
grep -q StandardErrorPath "$P" && grep -q "/opt/homebrew/bin" "$P"; ok $? "launchd: stdout/stderr go to a log and PATH covers Homebrew"
JANITOR_KIND=launchd bash "$I" "$R2" >/dev/null; [ "$(wc -l <"$WORK/istate/janitor.repos")" -eq 2 ]; ok $? "installing a second repo adds it instead of replacing the first"
JANITOR_KIND=launchd bash "$I" --check >/dev/null 2>&1; ok $? "check: reports installed"
JANITOR_KIND=launchd bash "$I" --uninstall "$R2" >/dev/null; [ -e "$P" ] && [ "$(wc -l <"$WORK/istate/janitor.repos")" -eq 1 ]; ok $? "uninstall with a repo removes only that repo"
cp -R "$SC" "$WORK/sc-copy"; JANITOR_KIND=launchd bash "$WORK/sc-copy/install_janitor.sh" "$R" >/dev/null; rm -rf "$WORK/sc-copy"
JANITOR_KIND=launchd bash "$I" --check >/dev/null 2>&1; [ $? -eq 1 ]; ok $? "check: an entry pointing at a deleted janitor.sh is reported stale"
JANITOR_KIND=launchd bash "$I" --uninstall >/dev/null; [ ! -e "$P" ] && [ ! -e "$WORK/istate/janitor.repos" ]; ok $? "launchd: uninstall removes plist and repo list"
W="$WORK/we ird %h \$HOME 'q"; mkdir -p "$W"
JANITOR_KIND=systemd bash "$I" "$W" >/dev/null; U="$WORK/home/.config/systemd/user"
grep -q "OnUnitActiveSec=15min" "$U/com.perun.janitor.timer" && grep -q '^ExecStart="/bin/bash" ".*janitor.sh" "--scheduled" "--repos-file" ".*janitor.repos"$' "$U/com.perun.janitor.service"
ok $? "systemd: timer and quoted ExecStart written"
JANITOR_STATE="$WORK/ist%\$'x" JANITOR_KIND=systemd bash "$I" "$R" >/dev/null
grep -q 'ist%%\$\$' "$U/com.perun.janitor.service"; ok $? "systemd: % and \$ in paths are doubled"
JANITOR_KIND=systemd bash "$I" --uninstall >/dev/null; [ ! -e "$U/com.perun.janitor.timer" ]; ok $? "systemd: uninstall removes the unit files"
JANITOR_STATE="$WORK/ist%\$'x" JANITOR_KIND=cron bash "$I" "$R" | grep -q '^\*/15 \* \* \* \* .*ist\\%\$'"'"'\\'"''"'x'; ok $? "cron: single-quoted, % escaped, quote escaped"

echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
