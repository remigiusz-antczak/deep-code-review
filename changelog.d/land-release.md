### Added
- `scripts/land-release.sh`: parallel lanes no longer bump the version. A lane adds `changelog.d/<slug>.md` and runs `--regen`; at merge time the land step (under a lock shared by all worktrees) merges `origin/main`, stamps the next minor across the lockstep set, folds the fragments into `CHANGELOG.md`, and regenerates INDEX.md, `SHA256SUMS` and `size-budgets.tsv`, so a lane that lands second needs no rebump or force-push. Closes #1353.
- `scripts/test-land-release.sh` (wired into `test-ci-gates.sh`): two fragment branches landed back-to-back, then the version, size, index and checksum gates.
- `CONTRIBUTING.md` "Releasing without version collisions" documents the flow and the one `Closes #N` line per issue rule (`Closes #a, #b` closes only the first).
- `size-budgets.tsv` rows regenerated to current sizes: 12 rows that had drifted above their file's actual size (frozen slack) are ratcheted down; no row rose.
