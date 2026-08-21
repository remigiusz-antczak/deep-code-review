# Example review report (fictional)

Read this when you want to see what a finished `FULL` deliverable looks like —
confidence markers (`CONFIRMED` / `CORROBORATED` / `PLAUSIBLE` / `latent`), the
machine + plain-language split, and Phase-0 surface pinning. **Not a live audit.**
All names, paths, and findings are invented fixtures (`Acme Capital`,
`jane@example.com`).

---

## Session preamble (first response)

```
Scope: FULL · START_SHA=a1b2c3d · worktree: /tmp/dcr-wt-a1b2c3d (default) ·
history: 187 commits · triage-first: doctor + documented tenant-isolation invariant
```

---

## Findings report — Acme Capital agent platform (fictional)

```
# Code review — Acme Capital agent platform — DIFF/FULL/FILE: FULL
Reviewed: START_SHA a1b2c3d (dedicated worktree) · 2026-08-17
Reviewer: deep-code-review 1.10.0

## Summary
🟡 Needs attention — tenant isolation holds on live routes; two Highs
(hermetic-test shared writes; webhook signature gap) and one latent Critical
(SSRF sink behind a dead flag) before enabling the unused egress tool.

## Findings

### F1 — Critical · latent · CORROBORATED
**SSRF/exfil sink in unused tool runner**
- Evidence: `lib/tools/fetch-url.mjs:88` fetches caller-supplied URL with no
  allowlist; only registered when `ENABLE_URL_TOOL=1` (default off).
- Impact: would reach link-local / cloud metadata if the flag flips.
- Fix: allowlist + resolve-validate-pin before enable; regression test.
- Confidence: CORROBORATED (LLM-security + route-auth audits); lead re-verified
  at START_SHA. Gate: blocks enabling the subsystem, not unrelated merges.

### F2 — High · CONFIRMED
**Tests write the real shared data dir**
- Evidence: `test-store.mjs:40` boots server without `DATA_DIR` override;
  restore only in `finally` (`test-store.mjs:120`) — skipped on `process.exit`.
- Impact: intermittent corruption of tracked `data/accounts.json` under parallel
  CI / SIGINT.
- Fix: inject temp store root; unique per-run dir; signal-safe cleanup.
- Cross-ref: domains J, G.

### F3 — High · CONFIRMED
**Inbound webhook accepts unsigned body**
- Evidence: `routes/hooks.mjs:22` parses JSON; no HMAC verify; trusts
  `body.accountId`.
- Impact: forged events can mutate another tenant's job queue.
- Fix: verify signature (timing-safe); bind account to verified context;
  idempotency key store.
- Cross-ref: domain I / `api-contracts.md`, B.

### F4 — Medium · PLAUSIBLE
**Retry loop without jitter on paid enrichment**
- Evidence: subagent cited `lib/enrich.mjs:55` `while (true)` + fixed 100ms sleep.
- Impact: thundering herd + spend amplification on 429.
- Status: PLAUSIBLE — lead not yet byte-checked; artifact to confirm: run under
  mocked 429. Routed to Decisions needed until CONFIRMED.

## What's good
- Tenant isolation invariant SAFE with evidence on live routes.
- Distinguishable-from-design discipline avoided false Criticals on intentional
  single-tenant admin CLI.

## Branch & merge triage
N/A for this fixture (see domain S on a real FULL with open branches).

## Decisions needed (owner)
- Enable `ENABLE_URL_TOOL`? If yes, F1 must ship first.
- Confirm F4 under a 429 fixture or drop as unverified.

## Standards imprint
not requested

## Definition of done — status
- ✅ Review surface pinned
- ❌ Zero Blocker/Critical — F1 latent Critical remains
- ❌ High fixed or owner-accepted — F2, F3 open
```

---

## Human-readable companion (same run)

Would land at `code-review/review-2026-08-17.md` when the checkout is idle; if
occupied, same body out-of-tree / on a dedicated review branch (Phase 5 escape
hatch).

```
# Code review — Acme Capital agent platform, 2026-08-17

## In one line
🟡 Needs attention — strangers cannot read each other's data today, but tests
can corrupt shared files and an unsigned webhook can queue forged jobs.

## Health at a glance
| Area | Status | In plain words |
|---|---|---|
| Security | 🟡 | Live tenant walls hold; unused URL tool + unsigned webhook need fixes |
| Correctness | 🟢 | Core flows match intent |
| Data quality | 🟡 | Test suite can overwrite real account files |
| Tests | 🟡 | Not hermetic on the store path |
| Documentation | 🟢 | Setup works |

## The most important things to fix (plain language)
1. **Stop tests from writing real account files** — a crashed test can leave bad
   data on disk. *(F2.)*
2. **Verify webhook signatures** — forged messages must not move jobs. *(F3.)*
3. **Before turning on the URL tool** — lock down where it can fetch. *(F1.)*
```
