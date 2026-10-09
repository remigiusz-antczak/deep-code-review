### Added
- `land-release.sh publish`: after a land, pushes the annotated tag and creates (or re-notes) the GitHub release with the CHANGELOG section; no-op unless origin/main is at this version; never moves a tag. New policy key `release_every` (default 1) batches releases. Documented in agentic-delivery `merge-queue-worktrees.md`.
- size-budget-raise: .claude/skills/agentic-delivery/references/merge-queue-worktrees.md 69576→70720 release publishing section
