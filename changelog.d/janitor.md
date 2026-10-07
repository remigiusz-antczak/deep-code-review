### Added
- `agentic-delivery/scripts/janitor.sh [--apply] REPO...`: unattended cleanup. Removes worktrees of merged or closed PRs (dirty ones archived first, unpushed or still-in-use ones kept), kills agent-spawned dev servers, test runners and headless browsers whose cwd is inside a finished worktree or that have run past `JANITOR_MAX_AGE_S` (default 2h) in any linked worktree, verifies each kill (SIGKILL after 5s), and appends every action to a ledger. Dry run by default; processes outside the given repos' linked worktrees are never touched.
- `agentic-delivery/scripts/install_janitor.sh [--uninstall|--check] REPO...`: idempotent 15-minute schedule (macOS LaunchAgent, Linux systemd user timer, else a printed crontab line); `--check` reports when it is not installed. `install.sh --with-delivery` prints both commands.
- `clean_finished.sh` and `reap_own.sh` gain `DRY_RUN` and `LEDGER`; `clean_finished.sh` gains `REAP_PATTERN`.
- Operating discipline item 9, "Cleanup is scheduled, not remembered"; the cleanup loop template now points to the janitor as the preferred path.

size-budget-raise: .claude/skills/agentic-delivery/references/operating-discipline.md 4875→5240 one new rule line (item 9) for the scheduled janitor
