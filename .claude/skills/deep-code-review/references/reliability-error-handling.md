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
- **A verification gate: a persistent cannot-check is not a finding.** A gate that
  reaches an external dependency and hits a **persistent** cannot-check — an outage,
  a timeout after bounded retry, a retired endpoint — **does not block work and is
  not reported as a finding**; it fails closed only on a problem it actually
  observed (retry a *transient* error a bounded number of times first). **Exception —
  a security / authz / integrity / spend attestation fails closed on a can't-verify,
  not open:** a CVE / secret / banned-terms / authz check whose input or dependency is
  unreachable **blocks** (the missing-input fail-closed rule, `domain-checklists.md`;
  "Fail closed on authz/crypto/integrity errors" below; a fail-open there is the bug,
  `security-appsec.md`). Never point a gate at a **retired or unversioned endpoint**,
  and **bound the gate's own runtime**
  — a silent hang blocks work with no error trail, worse than a clean failure. (This
  is the gate's *blocking* behaviour; an item a reviewer genuinely could not verify is
  a separate axis — marked `could-not-check`, never a silent pass, the sense in which
  "fails open" is used for a review status elsewhere.)
- **Find the house primitive; confirm *uniform* routing (the converse lens).**
  Don't only ask "does each I/O site have *some* handling?" — grep the project's
  **own** retry/backoff/timeout wrapper (`withRetry`, `fetchWithTimeout`, a
  pre-configured client, an `@retry`/`tenacity` decorator, a `p-retry` import) and
  confirm **every** external-I/O site on the critical / delivery path goes
  **through it**. A site that hand-rolls its own handling — or has none — while
  the primitive exists is the finding: the inconsistency proves the bypass is an
  oversight, not policy (same logic as inconsistent spotlighting in domain C). The
  fix is to **route the outlier through the existing primitive**, not to add a
  second one — two retry helpers become a future drift bug.

**Grep leads (tune to language):** empty `catch` / `except: pass` / `rescue nil`;
`retry` without sleep/jitter; `axios`/`fetch`/`got` without timeout; `setTimeout`
as the only cancel; `while (true)` around a paid call; a raw `fetch`/SDK call
sitting beside the project's own retry/timeout wrapper that every other call
uses.

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
- **Fail closed to last-good, not to abort, when the abort is stricter than the
  downstream trust model.** A preflight that does a **live** external read (refresh
  a mirror, pull shared state, resolve a known-set) and aborts the whole job on any
  failure — a 5xx, a rotated credential, a half-set env — looks prudent, but is a
  brittleness bug when the *same* data is consumed downstream through a
  **staleness-tolerant** gate (e.g. "accept a ≤48h snapshot"): a transient blip or
  a key rotation kills the run while a valid recent local snapshot the downstream
  would happily use sits unused. On a preflight read failure, **degrade to the
  last-good snapshot iff it passes the system's own downstream staleness gate**;
  fail closed only when none is valid (preserving "never operate on absent/stale
  data"). Reuse the exact downstream gate/`check` path so the two can't diverge.
  Distinct from retry — a persistent failure like a rotated key survives every
  retry; a valid cached snapshot does not.

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
  `finally`-only cleanup on a process that calls `exit`; a fail-closed preflight
  doing a **live** read that aborts on any failure while the same data feeds a
  **staleness-tolerant** downstream gate (degrade to last-good instead).
