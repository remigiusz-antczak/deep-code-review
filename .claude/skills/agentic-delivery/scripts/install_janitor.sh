#!/usr/bin/env bash
# install_janitor.sh [--uninstall|--check] REPO... — schedule `janitor.sh --apply` every 15 minutes, idempotently.
# macOS: LaunchAgent plist; Linux with systemctl: systemd --user timer; otherwise prints the crontab line.
# --check exits 1 (and says so) when no entry is installed; --uninstall removes it.
# Env: JANITOR_HOME (default $HOME; entry files go under it, so tests stay out of the real home),
# JANITOR_NO_LOAD=1 (write files only, skip launchctl/systemctl), JANITOR_KIND (launchd|systemd|cron: override detection).
set -euo pipefail
D=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); H=${JANITOR_HOME:-$HOME}
mode=install; case "${1:-}" in --uninstall) mode=uninstall; shift ;; --check) mode=check; shift ;; esac
[ "$mode" != install ] || [ $# -gt 0 ] || { echo "usage: install_janitor.sh [--uninstall|--check] REPO..." >&2; exit 2; }
L=com.perun.janitor; PLIST=$H/Library/LaunchAgents/$L.plist; UD=$H/.config/systemd/user
kind=${JANITOR_KIND:-}
if [ -z "$kind" ]; then
  if [ "$(uname)" = Darwin ]; then kind=launchd; elif command -v systemctl >/dev/null; then kind=systemd; else kind=cron; fi
fi
load() { [ -n "${JANITOR_NO_LOAD:-}" ] || "$@" 2>/dev/null || true; }
case $mode in
  check)
    case $kind in
      launchd) f=$PLIST ;; systemd) f=$UD/$L.timer ;;
      *) if crontab -l 2>/dev/null | grep -q janitor.sh; then echo "janitor: installed (crontab)"; exit 0; fi; f=/nonexistent ;;
    esac
    [ -e "$f" ] && { echo "janitor: installed ($f)"; exit 0; }
    echo "janitor: NOT installed; cleanup will not run unattended. Run: bash $D/install_janitor.sh <repo>..." >&2; exit 1 ;;
  uninstall)
    case $kind in
      launchd) load launchctl unload "$PLIST"; rm -f "$PLIST" ;;
      systemd) load systemctl --user disable --now $L.timer; rm -f "$UD/$L.timer" "$UD/$L.service" ;;
      *) echo "remove the janitor.sh line from your crontab (crontab -e)" ;;
    esac
    echo "janitor: uninstalled"; exit 0 ;;
esac
repos=(); for r in "$@"; do repos+=("$(cd "$r" && pwd -P)"); done
cmd=(/bin/bash "$D/janitor.sh" --apply "${repos[@]}")
case $kind in
  launchd)
    mkdir -p "$(dirname "$PLIST")"
    { echo '<?xml version="1.0" encoding="UTF-8"?>'
      echo "<plist version=\"1.0\"><dict><key>Label</key><string>$L</string><key>ProgramArguments</key><array>"
      for a in "${cmd[@]}"; do printf '<string>%s</string>' "$(printf '%s' "$a" | sed 's/&/\&amp;/g;s/</\&lt;/g;s/>/\&gt;/g')"; done
      echo '</array><key>StartInterval</key><integer>900</integer><key>RunAtLoad</key><true/></dict></plist>'; } >"$PLIST.tmp"
    mv "$PLIST.tmp" "$PLIST"
    load launchctl unload "$PLIST"; [ -n "${JANITOR_NO_LOAD:-}" ] || launchctl load "$PLIST" ;;
  systemd)
    mkdir -p "$UD"
    printf '[Unit]\nDescription=Perun janitor\n[Service]\nType=oneshot\nExecStart=%s\n' "$(printf '%q ' "${cmd[@]}")" >"$UD/$L.service"
    printf '[Unit]\nDescription=Perun janitor every 15 min\n[Timer]\nOnBootSec=2min\nOnUnitActiveSec=15min\n[Install]\nWantedBy=timers.target\n' >"$UD/$L.timer"
    load systemctl --user daemon-reload; [ -n "${JANITOR_NO_LOAD:-}" ] || systemctl --user enable --now $L.timer ;;
  *) echo "add this line via crontab -e:"; echo "*/15 * * * * $(printf '%q ' "${cmd[@]}")"; exit 0 ;;
esac
echo "janitor: installed ($kind, every 15 min, $# repo(s)); preview first: bash $D/janitor.sh ${repos[*]}"
