# Coordinator loop

Fill `<angle-bracket>` placeholders. Cadence: every 30 minutes, or on an event (a lane hand-back, a PR going
ready). Never faster than 20 minutes: a tighter tick burns tokens for no new information.

## /loop prompt (copy-paste)

```
/loop 30m Coordinator wake. Run this checklist once, in order, then stop; do not re-poll inside a wake.
1. Activity: list new issue/PR activity since the last wake. Match on issue number plus a keyword set
   (URGENT, regression, blocked), never by author: peers share one account.
2. Peers: read each machine's free-lane count from the coordination issue. Run
   `ROOT=<repo-root> bash .claude/skills/agentic-delivery/scripts/reap_own.sh --report`; an idle peer while
   `lane:<machine>` issues wait is a finding: label or assign, per the pull-queue doctrine
   (references/multi-session-coordination.md). Host: `python3 .claude/skills/agentic-delivery/scripts/host_probe.py
   --lane-type cpu`; `HOLD` or `COULD_NOT_CHECK` means start no new lane this wake, and say so on the board.
3. Trains: for 2 or more green, reviewed PRs on one base, run
   `bash .claude/skills/agentic-delivery/scripts/train_land.sh <tag> <pr> <pr> ...`. A single PR takes the
   normal merge path.
4. Cleanup: `ROOT=<repo-root> bash .claude/skills/agentic-delivery/scripts/reap_own.sh` then
   `ROOT=<repo-root> bash .claude/skills/agentic-delivery/scripts/clean_finished.sh`. Verify servers are dead
   (`reap_own.sh --report` prints orphans=0), worktrees removed, merged branches deleted.
5. Board: post one status update (what landed, what is in flight, what is blocked, who owns each).
Idle with nothing to act on: say so in one line and end the wake.
```

## Scheduled-task template

```
name: coordinator-wake
schedule: every 30 minutes   # or trigger on lane hand-back; never under 20 minutes
prompt: <the text after "/loop 30m" above>
working_dir: <repo-root>
```
