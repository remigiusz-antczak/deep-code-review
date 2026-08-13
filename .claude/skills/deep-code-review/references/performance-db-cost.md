# Performance, database & cost review

Read this when the target has a database, makes external/API/LLM calls, runs
batch jobs, or has any hot path where latency or spend matters. Expands section
E of `SKILL.md`. The lens is two-sided: **is it fast enough, and does each unit
of work earn its keep?**

---

## Algorithmic

- No accidental O(n²)+ on a hot path (nested scans over the same collection,
  `list.contains` in a loop, repeated sort). Right structure: set/map for
  membership and lookup, not a linear scan.
- Compute-once: hoist invariant work out of loops; memoize pure results with a
  correct key; don't recompute what you already have.
- Bound the work: an operation whose cost scales with untrusted input needs a
  cap (page size, max depth, max iterations).

## Database

- **N+1**: a query issued per row of a previous result (query inside a `for`/
  `map`/serializer). Detect by reading the data-access path and by counting
  queries per request in a test. Fix with a join, an `IN (…)` batch, or the
  ORM's eager-load.
- **Indexes**: the columns in `WHERE`/`JOIN`/`ORDER BY` on hot queries are
  indexed and the index is actually used — confirm with the query plan
  (`EXPLAIN`/`EXPLAIN ANALYZE`); a seq scan on a large table is the finding.
  Watch for indexes made unusable by a function/cast on the column, or by
  leading-wildcard `LIKE`.
- **Over-fetch**: no `SELECT *` when a few columns are needed; select only what
  is used. Result sets are bounded and paginated (keyset/seek pagination over
  large `OFFSET`).
- **Push work to the DB**: filter/aggregate/join in SQL, not by pulling rows into
  app memory and looping. But don't hide an unbounded computation behind a view.
- **Connections & transactions**: a pooled connection (not one per call);
  transactions scoped as tightly as correctness allows; no long transaction held
  across a network/LLM call (lock contention); no application logic inside a DB
  lock window.

## Schema & data migrations (safety)

A migration is a deploy-time hazard, not just a query. Check:
- **Locking**: `ALTER TABLE` / `CREATE INDEX` on a large table without the
  non-blocking variant (`CREATE INDEX CONCURRENTLY`, safe column-add order)
  locks writes and can take an outage. 
- **Backward compatibility during rolling deploy**: old and new code run
  simultaneously mid-deploy — a migration must be compatible with both. Follow
  expand → migrate → contract: add the new column/table (nullable), backfill,
  switch reads/writes, then remove the old — across separate deploys, never in
  one destructive step.
- **`NOT NULL` without a default** on an existing table breaks inserts from old
  code and can rewrite the whole table; add nullable + default first, backfill,
  then enforce.
- **Backfill** runs **outside** the DDL transaction, in bounded batches, so it
  doesn't hold a lock or blow up the transaction log.
- **Rollback path** exists and is tested; the migration is idempotent/resumable.
- **Take the rollback snapshot before the mutation, not after.**
- A migration that transforms data must not degrade it — cross-reference the
  monotonic-quality invariant in `data-quality.md`.

## External / API / LLM calls — the cost-and-value lens

Every billable or slow call must map to value delivered.
- **Necessity**: is the call needed *now*, or is it "call it every run/every
  request" out of habit? Unchanged inputs should not be re-fetched, re-embedded,
  or re-scraped. Cache by a correct key with correct invalidation.
- **Batch** where the API allows (one request for N items beats N requests);
  **de-dupe** identical concurrent calls (single-flight).
- **Events over polling**: replace tight polling with webhooks/streaming where
  available; if polling, back off and use conditional requests
  (ETag/If-None-Match/If-Modified-Since).
- **Spend governance**: enforce caps in code **before** the call — per-call,
  per-session/request, **and** a global/daily/monthly cap for scheduled or
  unattended jobs (a per-run cap alone won't stop a runaway schedule). Circuit
  breakers on 402/429; bounded retries with exponential backoff + jitter.
- **The spend-safety holes** (verify each — two unrelated engagements independently
  hit them):
  - **A cap that defaults to off is not a cap.** Check the *default value* of
    every spend/row/rate cap; a per-run cap whose env var defaults to
    `0`/unlimited leaves a bare, freshly-configured run bounded only by the global
    aggregate. A paid pass with **no dry-run/apply switch at all** is the same
    gap.
  - **A ledger loader that fails open.** `try { readWholeFile } catch {
    events = [] }` on a spend/rate accumulator zeroes month-to-date on *any* read
    fault (permissions, IO, truncation) and disables the ceiling. Branch
    **ENOENT** (absent → empty is correct) vs a fault on a **present** file (fail
    closed).
  - **`SELECT sum()` then check-then-act is not atomic.** Concurrent callers each
    read the pre-spend total and both spend. Use an atomic reservation
    (insert-the-charge-first, or a transactional decrement/lock).
  - **An in-process singleton guard does not hold across processes.** A
    `globalThis` "is a job running?" flag or single-flight promise is per-process;
    if a second process (scheduler, worker, replica) shares the datastore, the
    guard is an illusion — verify it against the real process model (e.g. an
    entrypoint that runs `worker &` alongside the server).
- **Calibrate before a big paid run**: dry-run a small **zero-write** sample,
  measure real cost-per-call and failure rate, then extrapolate and get sign-off
  before the full apply. Don't discover the bill after the batch.
- **LLM specifics**: `max_tokens` and `timeout` set; prompt/response sizes
  bounded; a deterministic fallback path for when generation fails, with a
  counter reporting how often the fallback fired; don't ask the model to do work
  a function can do (see `security-ai-agents.md`).

## Caching & memoization

- Correct key (includes every input that changes the result; per-user/tenant
  where results differ) and correct **invalidation** (a stale-cache bug is worse
  than no cache). No caching of sensitive/per-user data in a shared cache.
- Bounded size / TTL / eviction; a cache that only grows is a leak.

## Concurrency, memory & payloads

- I/O-bound work is async/parallel where safe; CPU-bound work isn't blocking the
  event loop / request thread. Backpressure and timeouts on every external call.
- No unbounded growth: ever-growing lists/maps/caches, accumulating `defer`s,
  unclosed resources. Stream large data instead of buffering it all in memory.
- Payloads are reasonable; no shipping a megabyte to render a number.

**🚩 grep**: queries inside `for`/`map`/`.each`; `SELECT *`; missing `LIMIT`;
large `OFFSET`; `.all()` then filter in code; identical HTTP/LLM calls with the
same args; no `timeout=`/`AbortController` on network calls; `while True` poll
loops; `CREATE INDEX` without `CONCURRENTLY`; `ADD COLUMN … NOT NULL` with no
default; unbounded in-memory caches/dicts as module globals; retry loops with no
cap; a per-run cap whose default is `0`/unlimited; a `catch` that sets a spend
accumulator to empty; `SELECT sum(...)` then an app-side spend decision; a
`globalThis`/in-process job guard shared across processes.
