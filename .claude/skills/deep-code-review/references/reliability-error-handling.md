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
   mark skipped; present-empty ≠ absent. And a **downstream consumer gates on the producing step's
   SUCCESS, not the mere existence** of its artifact — existence ≠ freshness ≠ success, so a
   half-written or stale file from a crashed/aborted producer is present-but-invalid. (Adding an
   abort to a formerly-hanging step is itself a **write-path change**: it must preserve last-good
   and signal failure, never write-then-throw.) Cross-ref `data-quality.md` artifact→consumer census.

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
  reaches an external dependency — **or launches its own harness (a headless browser, a
  dev/preview server, a probe)** — and hits a **persistent** cannot-check — an outage,
  a timeout after bounded retry, a retired endpoint, **or a crash during harness setup,
  before it takes the first measurement** — **does not block work and is not reported as
  a finding**; it fails closed only on a problem it actually
  observed (retry a *transient* error a bounded number of times first). **Exception —
  a security / authz / integrity / spend attestation fails closed on a can't-verify,
  not open:** a CVE / secret / banned-terms / authz check whose input or dependency is
  unreachable — **including its own harness failing to launch** — **blocks** (the missing-input fail-closed rule, `domain-checklists.md`;
  "Fail closed on authz/crypto/integrity errors" below; a fail-open there is the bug,
  `security-appsec.md`). Never point a gate at a **retired or unversioned endpoint**,
  and **bound the gate's own runtime**
  — a silent hang blocks work with no error trail, worse than a clean failure. **A gate
  that exits the *same* failure code for a setup/harness crash as for a real violation is
  itself the defect** — consumers can't tell an outage from a finding, so a flaky harness
  blocks everything and trains blanket-overrides (which then suppress the real findings too);
  require **distinct exit semantics + a distinct message** for could-not-check vs
  found-a-problem, and flag any gate whose pre-measurement crash is indistinguishable from a
  real finding. (This
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

## Bulkheads — isolate resource pools so one saturated dependency can't sink the rest

A shared resource pool (a connection pool, an outbound HTTP/SDK client, a worker/thread pool, a
semaphore) is a **single point of coupling**: if one dependency saturates it — a slow or failing
downstream holding every connection while its calls time out — every *other* caller of that pool,
including healthy critical paths, starves behind it. That is a **cascading failure** (Release It!,
*Bulkheads*), and it is the enforcement the architecture lens already promises (`role-coverage.md`:
a failure "bounded by timeouts, **bulkheads**, and circuit breakers").

**Scope:** a service with a *shared* resource pool, client, or semaphore serving more than one
dependency or traffic class. A single-dependency CLI, a serverless function with one client per
invocation, or a process already using one pool per dependency has nothing to partition — say so
and move on.

Review:

- **Partition the pool by dependency / traffic class.** For every shared pool, list what draws from
  it; one pool serving both a slow/optional call and a fast/critical one is unpartitioned — give the
  risky dependency its own bounded pool so its saturation can't consume the critical path's capacity.
- **Fail fast when the resource is exhausted or the breaker is already open.** A new request to a
  *different, healthy* dependency should reject immediately, not queue behind requests that will time
  out anyway — an admission check before expensive work, not an unbounded wait that becomes blocked
  threads.
- **A fixed downstream capacity divides per replica — with a floor.** When the caller scales out, a
  fixed connection limit / per-key rate budget split across N instances can starve each; size it
  per-replica with a floor, don't assume the single-instance budget survives fan-out, and alert when
  replica-count × per-replica size approaches the downstream ceiling, so scale-out can't silently
  oversubscribe it.
- **Under self-overload, shed or degrade low-priority work.** A synchronous service with no path to
  shed low-priority load under overload collapses *all* callers uniformly (critical and optional
  alike) instead of protecting the critical ones (the queue/async shed-load case is in
  `domain-checklists.md` §W; this is the synchronous-service case).
- **🚩** one global pool/client shared by a critical and a background/optional call; no admission
  check before expensive work when that dependency's breaker is already open; a fixed downstream
  capacity silently shrinking per replica with no floor; a synchronous service with no self-overload
  shed/degrade path. (Sibling to the circuit-breaker rule above; distinct from tenant-vs-tenant
  noisy-neighbour isolation in domain T — a different axis.)

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

## The dual-write problem — a local write + a remote publish are not atomic

A handler that **persists state and then publishes an event / calls another
service** as two separate steps (`db.save(x); queue.publish(e)`) has no atomicity
across the two systems. A crash, timeout, or deploy **between** them — or a publish
that fails after the commit — diverges them: the state exists but no event fired
(**lost**), or the event fired but the transaction rolled back (**phantom**).
Retrying naively double-publishes.

- **Transactional outbox / CDC.** Write the event to an **outbox row in the same
  transaction** as the state change; a relay publishes from the outbox and marks it
  sent (at-least-once), so the event is durable **iff** the state committed. Or
  capture the DB change log (**CDC**) for the same guarantee without app-side dual
  writes.
- **Order: commit first, publish after** — never publish before the local commit (a
  phantom event on rollback).
- **Fallback when an outbox is impractical:** an **idempotent consumer** (dedup by a
  stable key — `api-contracts.md`: design for at-least-once + idempotent consumer)
  **and** a **reconciliation** path that detects and repairs divergence — never rely
  on both writes "usually" succeeding.
- **Scope:** applies when one logical operation spans two systems that cannot share
  a transaction (DB + bus, DB + third-party API, two datastores); a single-store /
  single-transaction operation does not need this. Distinct from multi-step **saga**
  compensation (`domain-checklists.md`), which sequences several operations — this is
  the atomicity of **one** write plus **one** publish.

## State-machine / lifecycle correctness — model transitions, guard them, leave no impossible or stuck state

Any entity with a **status / lifecycle** (`order: pending→paid→shipped→refunded`, a
subscription, a document draft→published, a job, a ticket) is a state machine, usually
**implicit**. Review it as one — distinct from multi-step **saga** compensation
(`domain-checklists.md`) and from the dual-write atomicity above; this is the correctness of
the entity's own transitions.

- **Model the valid transition set.** Are the legal `from→to` transitions explicit (a table,
  a typed union, a guard), or can the field be set to any value? A bare `UPDATE status = ?`
  with no from-state check lets `refunded → shipped` happen.
- **Guard each transition atomically — compare-and-set, not read-then-write.** The transition
  asserts its current state **in the write** (`UPDATE … SET status='shipped' WHERE
  status='paid'`, then check rows-affected), never read-state-then-write — which races two
  concurrent transitions into a double effect (pay twice, ship twice). This is the
  state-machine face of the concurrency CAS rule (`concurrency-shared-state.md`).
- **Make impossible states unrepresentable.** Prefer one state enum over a soup of booleans
  (`isPaid`, `isShipped`, `isRefunded`) that admits contradictions (`isRefunded && !isPaid`);
  where the language allows, encode the state so an illegal combination cannot be constructed
  (genuinely orthogonal flags like `isArchived` + `isFeatured` are not soup — the smell is
  booleans that jointly encode one entity's **mutually exclusive** lifecycle stages).
- **No stuck / orphan states.** Every non-terminal state has an exit that does **not depend on
  one specific actor** always acting — a timeout / escalation, a reclaim / reassignment path any
  eligible actor can take, or a deadline. A "someone will get to it" path assigned to one person
  is **not** an exit: a `processing` with no timeout, or an approval assigned to one person that
  never expires, silently strands the entity. Terminal states are truly terminal (nothing
  transitions out of `refunded`).
- **Transition side effects fire once.** The effect on a transition (charge, email, webhook)
  is guarded so a re-entered or retried transition does not double-fire — cross-ref the
  idempotency-key rule above and the dual-write section (a publish on a transition is itself a
  cross-system write).

**Scope:** applies when the target has an entity with a status / lifecycle field or an explicit
state machine; if none, say so and move on (do not invent a state machine to audit).

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

## Graceful shutdown & disposability — a listening service is not a batch job

The crash/resume rules above are the **batch/cron** shape (flush a cursor, exit, re-run). A
long-running **listening service or queue worker**, disposed on every deploy / scale-down /
preemption, needs a different, *ordered* shutdown (12-Factor *Disposability*: a web process shuts
down by "ceasing to listen on the service port … allowing any current requests to finish, and then
exiting"; a worker by "returning the current job to the work queue"). Behind a load balancer or orchestrator
the ordering below adds a step 12-Factor does not state — a readiness flip *first* — because the LB's
view of the instance lags its socket state.

- **Order: fail readiness *before* you stop accepting.** On SIGTERM the readiness probe flips to
  **unready first**, so the load balancer takes the instance out of rotation; only then does the
  listener stop accepting. The reverse (close the listener first) leaves the LB routing to a closed
  socket — connection-refused/reset on every rolling deploy or scale-down.
- **Drain is bounded.** After going unready, let in-flight requests finish, but with a **timeout ≥
  the slowest legitimate request** (p99); force-close the survivors and **log the count**. Unbounded
  drain hangs the deploy; zero drain is not graceful.
- **The platform grace window is a separate, additive clock.** The platform's kill-after grace period
  and the LB's deregistration-propagation delay are **not** the app's drain budget — size the drain
  against the real in-flight duration and ensure the platform window exceeds it, or the very race the
  handler exists to prevent reappears (`terminationGracePeriodSeconds` / `preStop` on Kubernetes are
  examples, not a pinned spec).
- **A worker returns (nacks) its in-flight job, it doesn't drop it.** On shutdown a queue consumer
  nacks/returns the current message (or finishes it if short and safely resumable) so an
  at-least-once queue redelivers it; "exit after whatever was in memory" silently drops or
  double-processes work on every deploy (make processing idempotent so redelivery is safe).
- **Release the lease and flush before exit.** A shutting-down replica releases any lock/lease/claim
  it holds (e.g. a distributed lock or a leader-election lease) and flushes buffered telemetry — else a scaled-down
  instance blocks its replacement for the lease TTL and loses its last logs/metrics.
- **A request killed mid-write at shutdown must be retry-safe** — the same idempotency-key discipline
  the retry rules above require, applied at the shutdown boundary.
- **🚩** a SIGTERM handler that stops the listener before failing readiness; an unbounded or zero
  drain; a worker that exits without nacking its in-flight job; a readiness endpoint hardcoded to
  `200` (it can neither gate a drain nor signal unhealthy — the always-200 health check flagged in
  `observability.md` breaks safe rolling deploys, not just monitoring).

**Scope:** a long-running listening service or
queue worker (load-balanced / orchestrated); a standalone process with no LB or readiness probe needs
only the finish-in-flight goal above.

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
  **staleness-tolerant** downstream gate (degrade to last-good instead); a local
  write followed by a separate publish / remote call with no transactional outbox,
  idempotent consumer, or reconciliation (a dual-write that loses or phantoms an
  event on a crash between the two); a status/lifecycle transition via a bare `UPDATE status = ?`
  with no from-state guard (read-then-write, not compare-and-set); a boolean soup encoding one
  entity's mutually-exclusive lifecycle stages (admits impossible combinations); a non-terminal
  state whose only exit depends on one specific actor (no timeout / reassignment); a listening service
that closes its listener before failing readiness, or drains unboundedly; a worker that exits without
nacking its in-flight job; one pool/client/semaphore shared by a critical and a background call with
no partition, admission check, or per-replica floor; a downstream consumer that gates on an artifact's
**existence** rather than the producing step's **success** (an abort added to a formerly-hanging step
must preserve last-good and signal failure, not write-then-throw).
