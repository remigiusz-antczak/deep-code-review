#!/usr/bin/env bash
# install_janitor.sh [--uninstall|--check] [REPO...] — schedule `janitor.sh --scheduled` every 15 minutes, idempotently.
# macOS: LaunchAgent plist; Linux with systemctl: systemd --user timer; otherwise prints the crontab line.
# Repos are kept in $STATE/janitor.repos (the entry never changes when repos do): install ADDS the given repos, --uninstall
# with repos removes only those, --uninstall alone removes the schedule and the list. The scheduled run only dry-runs (plan in
# $STATE/janitor.dryrun.log) until you review it and run `janitor.sh --enable` once.
# --check exits 1 and says why when no entry exists or the one installed points at a missing janitor.sh.
# Env: JANITOR_HOME (default $HOME; entry files go under it), JANITOR_NO_LOAD=1 (write files only, skip launchctl/systemctl/crontab),
# JANITOR_KIND (launchd|systemd|cron: override detection), JANITOR_STATE (see janitor.sh).
set -euo pipefail
D=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); H=${JANITOR_HOME:-$HOME}
STATE=${JANITOR_STATE:-${XDG_STATE_HOME:-$H/.local/state}/perun}; LIST=$STATE/janitor.repos
mode=install; case "${1:-}" in --uninstall) mode=uninstall; shift ;; --check) mode=check; shift ;; esac
[ "$mode" != install ] || [ $# -gt 0 ] || { echo "usage: install_janitor.sh [--uninstall|--check] [REPO...]" >&2; exit 2; }
L=com.perun.janitor; PLIST=$H/Library/LaunchAgents/$L.plist; UD=$H/.config/systemd/user
kind=${JANITOR_KIND:-}
if [ -z "$kind" ]; then
  if [ "$(uname)" = Darwin ]; then kind=launchd; elif command -v systemctl >/dev/null; then kind=systemd; else kind=cron; fi
fi
nl() { [ -n "${JANITOR_NO_LOAD:-}" ] || "$@" >/dev/null 2>&1 || true; }
# escaping per consumer: XML text; systemd ExecStart (double-quoted, % and $ doubled); cron (single-quoted, % escaped)
xml() { printf '%s' "$1" | sed 's/&/\&amp;/g;s/</\&lt;/g;s/>/\&gt;/g'; }
sd() { printf '"%s"' "$(printf '%s' "$1" | sed 's/\\/\\\\/g;s/"/\\"/g;s/%/%%/g;s/\$/$$/g')"; }
cr() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g;s/%/\\\\%/g")"; }
cronline() { echo "*/15 * * * * $(cr /bin/bash) $(cr "$D/janitor.sh") --scheduled --repos-file $(cr "$LIST")"; }
case $mode in
  check)
    case $kind in
      launchd) f=$PLIST ;; systemd) f=$UD/$L.timer ;;
      *) f=/nonexistent; if crontab -l 2>/dev/null | grep -q 'janitor\.sh'; then echo "janitor: installed (crontab)"; exit 0; fi ;;
    esac
    [ -e "$f" ] || { echo "janitor: NOT installed; cleanup will not run unattended. Run: bash $D/install_janitor.sh <repo>..." >&2; exit 1; }
    [ "$kind" = launchd ] && g=$f || g=$UD/$L.service
    j=$(grep -o '/[^"<>]*janitor\.sh' "$g" | head -1 || true)
    [ -n "$j" ] && [ -f "$j" ] || { echo "janitor: entry $f is stale (janitor.sh missing: ${j:-unknown}); re-run install_janitor.sh" >&2; exit 1; }
    [ -s "$LIST" ] || { echo "janitor: entry installed but $LIST has no repos" >&2; exit 1; }
    [ -e "$STATE/janitor.enabled" ] && e=enabled || e="dry-run only until: bash $j --enable"
    echo "janitor: installed ($f; $e)"; exit 0 ;;
  uninstall)
    if [ $# -gt 0 ]; then   # drop only the named repos; keep the schedule while any remain
      for r in "$@"; do r=$(cd "$r" 2>/dev/null && pwd -P || echo "$r"); grep -vxF -- "$r" "$LIST" >"$LIST.new" 2>/dev/null || true; mv "$LIST.new" "$LIST"; done
      [ -s "$LIST" ] && { echo "janitor: repos removed; schedule kept for the rest"; exit 0; }
    fi
    case $kind in
      launchd) nl launchctl remove "$L"; rm -f "$PLIST" ;;
      systemd) nl systemctl --user disable --now $L.timer; rm -f "$UD/$L.timer" "$UD/$L.service"; nl systemctl --user daemon-reload ;;
      *) if [ -z "${JANITOR_NO_LOAD:-}" ] && crontab -l 2>/dev/null | grep -q 'janitor\.sh'; then crontab -l | grep -v 'janitor\.sh' | crontab -; fi ;;
    esac
    rm -f "$LIST"; echo "janitor: uninstalled"; exit 0 ;;
esac
mkdir -p -m 700 "$STATE"
for r in "$@"; do (cd "$r" && pwd -P) >>"$LIST"; done
sort -u "$LIST" -o "$LIST"
cmd=(/bin/bash "$D/janitor.sh" --scheduled --repos-file "$LIST")
case $kind in
  launchd)
    mkdir -p "$(dirname "$PLIST")"
    { echo '<?xml version="1.0" encoding="UTF-8"?>'
      echo "<plist version=\"1.0\"><dict><key>Label</key><string>$L</string><key>ProgramArguments</key><array>"
      for a in "${cmd[@]}"; do printf '<string>%s</string>' "$(xml "$a")"; done
      echo '</array><key>StartInterval</key><integer>900</integer>'
      echo "<key>StandardOutPath</key><string>$(xml "$STATE/janitor.log")</string><key>StandardErrorPath</key><string>$(xml "$STATE/janitor.log")</string>"
      echo '<key>EnvironmentVariables</key><dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict></dict></plist>'; } >"$PLIST.tmp"
    mv "$PLIST.tmp" "$PLIST"
    nl launchctl remove "$L"; nl launchctl load "$PLIST" ;;
  systemd)
    mkdir -p "$UD"
    printf '[Unit]\nDescription=Perun janitor\n[Service]\nType=oneshot\nEnvironment=PATH=/usr/local/bin:/usr/bin:/bin\nExecStart=%s %s %s %s %s\n' \
      "$(sd "${cmd[0]}")" "$(sd "${cmd[1]}")" "$(sd "${cmd[2]}")" "$(sd "${cmd[3]}")" "$(sd "${cmd[4]}")" >"$UD/$L.service"
    printf '[Unit]\nDescription=Perun janitor every 15 min\n[Timer]\nOnBootSec=2min\nOnUnitActiveSec=15min\n[Install]\nWantedBy=timers.target\n' >"$UD/$L.timer"
    nl systemctl --user daemon-reload; nl systemctl --user enable --now $L.timer ;;
  *) echo "add this line via crontab -e:"; cronline; exit 0 ;;
esac
echo "janitor: installed ($kind, every 15 min, repos in $LIST). Scheduled runs only dry-run until enabled; the plan appears in $STATE/janitor.dryrun.log after the first run (or preview now: bash $D/janitor.sh --repos-file $LIST)."
echo "Review it, then run once: bash $D/janitor.sh --enable"
