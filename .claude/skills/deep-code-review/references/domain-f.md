# Domain F checklist

Read this when domain F (Reliability & error handling) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### F. Reliability & error handling → `references/reliability-error-handling.md`
- Every external call handles failure explicitly: **check status before reading
  the body**; API clients return null/empty and let the caller escalate; batch
  loops catch **per-item** errors, log, and continue so one bad item can't halt
  the run. Every call carries a **timeout and an independent abort signal**
  (one without the other leaves a hang path). Circuit-break on 402/429 or
  consecutive errors. A **shared pool** serving a slow/optional and a fast/critical dependency is a
  **bulkhead** gap — partition by dependency, fail fast on exhaustion, and size a fixed downstream
  budget per-replica with a floor on scale-out (`references/reliability-error-handling.md`).
- No silent swallow (`catch {}` / `except: pass` / `rescue nil`); fail **closed**
  on security-relevant errors, degrade cleanly elsewhere; partial failure never
  corrupts persisted state. **Echo-verify** a write (compare the response
  field-by-field to what was sent). **"Blocked" ≠ "declined"** — when a
  policy/permission gate stops a write/paid op, surface the exact blocked
  operation and how to run it; never route around it.
- Long jobs are SIGINT-clean, cursor-resumable, idempotent, with append-only
  progress so a crash loses no work; a **listening service or queue worker shuts down
  gracefully** — fail readiness before closing the listener, bound the drain, and a worker nacks its
  in-flight job (`references/reliability-error-handling.md`); a **two-key confirmation** guards the
  highest-consequence irreversible actions; every credentialed integration
  degrades to a **clean no-op** without its key — unsafe if the CLI still
  **persists an empty/zero artifact** that downstream merge/read treats as data — a downstream
  consumer must gate on the producing step's **success**, not the artifact's mere existence
  (procedure: `references/reliability-error-handling.md`). A **load-order/registration bug
  can silently no-op an entire subsystem** — assert each optional/paid subsystem
  actually executes in the deployed environment, not just locally, and that each
  security-critical gate is **proven live (a self-proof / health check) and fails
  closed when the proof is absent**, never assumed from a present code path (the
  runtime-proven-gate lens, domain B). Route control-plane traffic (kill-switch,
  approval) **above** the rate limiter.
- 🚩 swallowed exceptions, retry-forever, no timeout, non-idempotent retry, work
  lost on crash, status not checked before body read, an emergency stop behind
  the limiter.
