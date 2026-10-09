### Added
- deep-code-review FULL audits: whole-repo lenses in `references/full-audit.md` (guard added later, access matrix with secondary read surfaces, external retry/replay, fail-closed switches and readiness) and per-path timeout sums in the entry-point table; `references/nextjs-app-router.md` gains per-page server-action serialization and non-void action returns. Default single-pass review text unchanged.
- agentic-delivery: QA on a fresh database per branch (`verification-handback.md`).

size-budget-raise: .claude/skills/deep-code-review/references/full-audit.md 2290→4172 FULL-audit lenses
size-budget-raise: .claude/skills/deep-code-review/references/nextjs-app-router.md 1391→2111 server-action footguns
size-budget-raise: .claude/skills/agentic-delivery/references/verification-handback.md 58477→58759 fresh DB QA rule
