### Added
- FULL-scope audits gain `references/full-audit.md` (entry-point table of server actions, routes, jobs and webhooks with auth, rate limit, external calls, timeout budget and idempotency; optional domains loaded only when a recorded grep probe finds the surface) and a conditional `references/nextjs-app-router.md`. New probes in existing references: handler latency budget, partial-success cursors, alert paths, audit coverage, shared fixed-name QA DB or port, config hygiene and fail-closed kill switches, delegated-session revocation. The DIFF `/review` path and `commands/review.md` are unchanged; the Phase 0-2 floors rise 21 tokens for one routing line (re-pinned with a comment). Refs #1380.

size-budget-raise: .claude/skills/deep-code-review/SKILL.md 23535→23657 field-audit probes
size-budget-raise: .claude/skills/deep-code-review/references/appsec-design.md 6796→7297 field-audit probes
size-budget-raise: .claude/skills/deep-code-review/references/appsec-login.md 4656→5160 field-audit probes
size-budget-raise: .claude/skills/deep-code-review/references/concurrency-shared-state.md 42331→42853 field-audit probes
size-budget-raise: .claude/skills/deep-code-review/references/observability.md 18418→19476 field-audit probes
size-budget-raise: .claude/skills/deep-code-review/references/reliability-error-handling.md 45745→46842 field-audit probes
