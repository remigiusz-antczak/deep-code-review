### Added
- `train_flake.sh` baselines now carry the host and an invocation hash (`--record`); a baseline from another host or invocation, or one without the header, is refused (exit 2) instead of creating phantom new failures. `FLAKE_SETUP_CMD` gives every per-test-title re-run a fresh `FLAKE_STORE`.
- `merge_train.py` `default_runner` runs each gate in its own process group and stops that group on timeout, so a browser grandchild cannot outlive the timebox.
- Doctrine: no weaker-proof gate swap, train by footprint, one-at-a-time merges under churn, contract-pinned guards, lanes decide reversible choices, and no self-hosted runner on a developer machine (checklist row plus evals, including an idea-critic HOLD case).

size-budget-raise: .claude/skills/deep-code-review/references/domain-k.md 4865→5078 one self-hosted-runner checklist row
size-budget-raise: .claude/skills/agentic-delivery/references/unattended-operating-mode.md 26509→26732 one reversible-choice doctrine line
size-budget-raise: .claude/skills/agentic-delivery/references/merge-queue-worktrees.md 68717→69576 one fleet-rules section
