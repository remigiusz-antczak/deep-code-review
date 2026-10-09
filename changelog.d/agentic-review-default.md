### Changed
- Reviews run with repo access by default: `/review` and the opt-in PR workflow template run in a checkout with Read, Grep and Glob and trace callers and callees of every changed symbol (measured +28 points recall, +21 points precision against diff-only; 90 cases). Results added to `docs/bench/bench90-results.md` and the README. Refs #1380.
