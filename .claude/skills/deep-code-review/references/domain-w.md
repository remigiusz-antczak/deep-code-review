# Domain W checklist

Read this when domain W (Workflows, jobs & scheduling) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### W. Workflows, jobs & scheduling
Apply when the target runs scheduled jobs (cron), background queues/workers, or
multi-step/long-running workflows. **N/A by scope** on a purely synchronous
request/response app with no async work. Distinct from **F**, which owns whether
*one* call handles its own failure (timeout, retry, idempotent, circuit-break),
and from **G**, which owns races on shared state — **W owns the orchestration**:
whether scheduled, queued, and multi-step work runs correctly *as a system*.
(One-time schema/data migrations are **E**; deploy/rollout is **K** — not here.)
- **Never-runs**: a scheduled job that silently stops is invisible. Assert
  **liveness** — a heartbeat, a last-success timestamp, a dead-man alert — not just
  that the scheduler is "configured". A cron that never fired and a job that ran
  and did nothing are indistinguishable without it (cross-ref M observability). But those liveness
  signals are **end-of-window**: a heartbeat proves only that the process is alive, and a **stale
  last-success** catches a **zero-success** run only *after* its staleness window closes (on an
  overnight run, possibly the whole run) — while a run still landing **some** successes keeps
  last-success fresh, so the dead-man never fires at all. Catching a **systemic** fault (the upstream
  down, most items erroring) **while the window is still burning** — early enough to self-abort —
  needs **progress emission**: processed / total + a running **fault count** and a **fault-rate
  alert**, so a stalled-but-alive run is visible, not mistaken for healthy work.
- **Runs-twice / exactly-once**: overlapping runs (a slow job re-triggered before
  it finishes), at-least-once queue redelivery, and retries all fire the effect
  more than once. "Exactly-once *delivery*" is a myth — design for exactly-once
  **effect** on at-least-once delivery: make the effect **idempotent** (dedup key,
  upsert, processed-set) or guard it with a single-runner lock that has an expiry
  (cross-ref F idempotent retry, I webhook idempotency).
- **A signal→action system needs firing-suppression, distinct from delivery-idempotency.** The
  idempotency above stops a *duplicate delivery of the same message* firing an effect twice; it does
  **not** stop *repeated real firings of the same underlying condition* (an alert re-firing every
  poll while a metric stays over threshold; a "you have unread items" nudge every run). That needs a
  **cooldown window per (entity, signal type)** and **suppression-with-audit** — a suppressed firing
  increments a counter and records a last-suppressed timestamp, **never a silent drop** — so a
  genuine re-fire after the cooldown still gets through and an over-firing (or over-suppression) bug
  stays visible. Where firings must be deduped independent of timing, add a deterministic **firing
  key** over (entity, signal type, **event instance**) so repeated observations of *one real event*
  fold into a single firing before the cooldown even applies — distinct from the delivery-idempotency
  key above, which dedups re-execution of the *same message*, not re-observation of the same condition.
- **Failure escalates from the item (F) to the batch as a whole**: beyond F's
  per-item try/continue and cursor-resumability (cross-ref F), the job needs a
  **dead-letter / parking** path for items that keep failing and a **retry cap**
  so a poison message doesn't retry forever instead of quietly wedging the queue. And bound the **lane
  as a whole**, not only each item: a per-item retry cap still lets thousands of
  individually-bounded-but-failing items burn the entire run, so when a large *fraction of
  consecutive items* fault — the **upstream itself** is down, not one poison item — abort the
  remaining lane fast (a wall-clock and/or consecutive-fault budget), rather than exhausting every
  item's retries against a dead dependency.
- **On a batch-triggered handler, the platform — not the code — decides whether the whole
  batch or only the failed items get retried/deleted.** For a queue/stream event source that
  invokes the handler with a batch of records, the retry/delete unit is typically set by the
  invocation's **response shape** plus an **event-source-mapping config flag**, not by the
  code's control flow — F's per-item try/catch is necessary but not sufficient on this
  trigger shape (general per-item-guard rule: `reliability-error-handling.md`'s per-item
  try/catch bullet; the two failure modes and the config-flag fix are here in §W). Two opposite failures follow from getting only one half right: (a)
  catch every per-item error and return a bare success — the platform sees a clean
  invocation and **deletes the whole batch**, silently dropping every failure the code
  caught but never reported (data loss); (b) throw on any per-item failure with no
  partial-failure reporting — the platform treats the **entire batch as failed** and
  redelivers it whole, including the items that already succeeded (double-processing
  non-idempotent work). The fix needs **both** halves: the handler emits a per-item failure
  list **and** the deploy config enables partial-batch-failure reporting (AWS names this
  `ReportBatchItemFailures`/`batchItemFailures`: return a `batchItemFailures` list from the
  handler and set `ReportBatchItemFailures` on the event source mapping's
  `FunctionResponseTypes`) — the code change alone does nothing if the config flag is
  unset, and the flag alone does nothing if the handler never reports which items failed.
- **A trigger topology can cycle back on itself, invisibly to any one function's code** —
  a function whose output feeds the resource that triggers it (directly, or transitively)
  is a self-amplifying invocation loop with no call stack, distinct from the item/batch
  failure modes above; the cycle lives in a *separate resource's* trigger wiring in IaC
  (depth, detection-boundary caveats, and the review procedure: `infra-iac-containers.md`).
- **Schedule time is handled correctly**: cron runs in an **explicit timezone** —
  a local-time schedule shifts under DST, and a job "at 02:30" can run twice or
  zero times on a DST boundary; the **catch-up policy** on a missed window is
  deliberate (run-once vs backfill-each-miss), not accidental. (The clock
  primitives themselves — monotonic durations, UTC storage — are domain A.)
- **Ordering and dependencies are explicit** where relied on: a queue is not FIFO
  under retry, and a downstream job that assumes an upstream finished needs a real
  dependency/trigger, not a `sleep`. Fan-out/fan-in joins wait for actual
  completion, not an elapsed timer.
- **Long-running workflow state is durable and recoverable**: a multi-step saga
  persists each step's outcome and defines **compensation** for a step that fails
  *after* earlier steps committed; a process crash **resumes** the workflow — it
  does not double-apply a committed step or strand the workflow half-done
  (cross-ref F, G).
- **Backpressure and bounds**: queue depth is monitored and bounded; a producer
  faster than its consumer degrades deliberately (shed load, buffer-with-cap),
  never unbounded memory or spend growth (cross-ref E cost, M).
- 🚩 a cron with no liveness/heartbeat alert; a non-idempotent effect on an
  at-least-once queue or an overlapping schedule; no dead-letter path or retry cap
  (poison retries forever); a batch handler that swallows per-item errors and returns
  bare success (silent data loss) or throws with no partial-batch reporting enabled
  (whole-batch redelivery); cron in an implicit/local timezone; a downstream step
  that `sleep`s to wait for an upstream; a multi-step workflow with no persisted
  state or compensation; an unbounded queue or producer; a function whose output
  feeds back into its own trigger (a topology cycle in IaC, not in the function).
