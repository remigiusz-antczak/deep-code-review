# Reliability & error handling

Read this when reviewing failure paths, retries, timeouts, crash recovery,
idempotency, or "does a bad item / missing key / SIGINT corrupt or lose work."
Expands section F of `SKILL.md`. Procedures and greps — not a restatement of
the checklist.

---

## Detection procedure

1. **Enumerate every external I/O site** — HTTP/SDK calls, DB, filesystem,
   subprocess, queue publish/consume, LLM/tool calls. For each: where is
   status/error checked? timeout? abort/cancel signal? retry policy?
2. **Trace one failure through persistence.** Pick a write path. Inject (on
   paper or in a worktree probe): timeout, 5xx, empty body, partial JSON,
   duplicate delivery. Does persisted state stay consistent? Is the failure
   logged with a stable error *class* (not a secret-bearing body)?
3. **Crash mid-job.** For long runners: is there a cursor/checkpoint?
   append-only progress? resume that does not double-apply side effects?
4. **Missing credential / feature off.** Does the integration become a **clean
   no-op**, or does it throw halfway / write half a record / bill a partial call?
   **Soft-no-op persistence:** returning `[]` / empty rows is clean only if the
   CLI does **not** then write that empty artifact over last-good bytes that a
   merge or reader treats as present data. Skip the write (leave prior file) or
   mark skipped; present-empty ≠ absent. Cross-ref `data-quality.md`
   artifact→consumer census.

---

## Timeouts, aborts, retries

- **Timeout and abort are independent.** A `fetch` with only `AbortSignal` from
  a parent that never fires, or only a library default with no per-call bound,
  still hangs. Both must exist; the abort must be *wired* to the call site.
- **Retry only what is safe.** Idempotent GETs / put-with-idempotency-key: OK
  with jittered backoff and a hard cap. Non-idempotent POST/charge/send: retry
  only behind an idempotency key or after echo-verify that nothing applied.
  **Retry-forever** and **retry-without-jitter** are findings.
- **Circuit-break** on 402/429 / consecutive hard failures — stop amplifying
  spend and load; surface a clear "paused" state.
- **Check status before body.** `res.json()` on a 500 HTML page, or treating
  transport success as business success, hides outages as parse bugs.

**Grep leads (tune to language):** empty `catch` / `except: pass` / `rescue nil`;
`retry` without sleep/jitter; `axios`/`fetch`/`got` without timeout; `setTimeout`
as the only cancel; `while (true)` around a paid call.

---

## Partial failure & persisted state

- Batch loops: **per-item** try/catch (or equivalent); one poison item must not
  abort the whole run unless the product explicitly requires all-or-nothing —
  and then that must be transactional.
- **Echo-verify writes** when the cost of silent drift is high: compare the
  store's returned record to what was sent (field-by-field or hash), not only
  "HTTP 200."
- **"Blocked" ≠ "declined"** — permission/policy gates that stop a write must
  name the blocked operation and the unlock path; do not map them to a soft
  "user said no" or silent skip.
- Fail **closed** on authz/crypto/integrity errors; degrade cleanly on optional
  enrichments.

---

## Crash, SIGINT, resume

- Long jobs: catch SIGINT/SIGTERM (or platform equivalent), flush cursors,
  exit non-zero, and be **safe to re-run**. Cleanup that lives only in
  `finally`/`try` is not signal-safe if `process.exit`, hard kill, or OOM can
  skip it (cross-ref J / `testing-and-evals.md` for the test variant).
- Progress: append-only or transactional checkpoints keyed by a stable job id —
  not "overwrite a single status file" without fsync/replace discipline
  (cross-ref G).
- **Two-key confirmation** (or human approval) for the highest-consequence
  irreversible actions; control-plane routes (kill-switch, approval) must sit
  **above** the rate limiter so an emergency stop cannot be throttled away.

---

## Silent no-op of whole subsystems

A load-order, feature-flag, or registration bug can leave a paid/optional
subsystem never executing in production while local runs look fine.

- Assert registration in the deployed entrypoint (boot log, readiness probe, or
  a smoke test that hits the real wiring).
- Grep for optional `require`/`import` behind flags with no test that the flag
  path runs in CI for both states.

---

**🚩 red flags**: swallowed exceptions; retry-forever; no timeout; non-idempotent
retry; work lost on crash; status not checked before body read; emergency stop
  behind the rate limiter; missing-key path that corrupts state instead of clean
  no-op; missing-key path that **writes empty artifacts** over last-good data;
  `finally`-only cleanup on a process that calls `exit`.
