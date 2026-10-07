# Cleanup loop (standalone)

Fallback for a host with no OS scheduler: `scripts/install_janitor.sh` schedules the same cleanup without an agent and
supersedes this loop. For a machine with no coordinator or peer loop. Cadence: every 30 minutes or hourly. Never faster than 20
minutes.

## /loop prompt (copy-paste)

```
/loop 30m Cleanup wake. Run once, then stop.
1. `ROOT=<repo-root> bash .claude/skills/agentic-delivery/scripts/reap_own.sh` (own idle dev servers only).
2. `ROOT=<repo-root> bash .claude/skills/agentic-delivery/scripts/clean_finished.sh` (worktrees of merged or
   closed PRs; dirty ones are archived first, unpushed ones are kept).
3. `ROOT=<repo-root> bash .claude/skills/agentic-delivery/scripts/reap_own.sh --report`: orphans must be 0.
   Report any FINDING line; delete nothing by hand.
```

## Scheduled-task template

```
name: cleanup-wake
schedule: every 30 minutes   # never under 20 minutes
prompt: <the text after "/loop 30m" above>
working_dir: <repo-root>
```
