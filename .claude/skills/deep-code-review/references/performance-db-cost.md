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
- **Connections & transactions**: a pooled connection (not one per call) — and
  likewise reuse one HTTP/SDK client per process, since constructing a fresh
  client per call throws away its connection pool; transactions scoped as tightly
  as correctness allows; no long transaction held across a network/LLM call (lock
  contention); no application logic inside a DB lock window.

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
  or re-scraped. Cache by a correct key with correct invalidation. The sharpest
  version is an external call in the render body of a dynamic / `no-store` page
  (or a hot handler): it fires on *every* view, bounded only by how often humans
  or bots hit it — invisible until the bill or a rate-limit lands. Data identical
  for all viewers is cached globally, not per user.
- **Near-static config**: schema, field definitions, enum/dropdown options,
  feature flags, and other slowly-changing config fetched at request rate are
  effectively constants pulled over the wire on every call. Cache with a long TTL,
  or promote genuinely fixed values to committed configuration with a startup
  check that they still match the source — so drift fails loudly at boot instead
  of silently.
- **Redundant full-collection scans**: "fetch the whole list/table to find or
  dedupe one item" is O(collection) calls (pagination) for an O(1) need; doing the
  *same* scan twice in one logical operation (a handler scans, then a helper it
  calls scans it again) doubles it. Fetch once and pass the result down, or use a
  targeted lookup. Do **not** cache a scan whose purpose is dedupe or a freshness
  check — correctness needs current data there; remove the redundancy, don't stale
  it.
- **Batch** where the API allows (one request for N items beats N requests);
  **de-dupe** identical concurrent calls (single-flight).
- **Events over polling**: replace tight polling with webhooks/streaming where
  available; if polling, back off and use conditional requests
  (ETag/If-None-Match/If-Modified-Since).
- **Spend governance**: enforce caps in code **before** the call — per-call,
  per-session/request, **and** a global/daily/monthly cap for scheduled or
  unattended jobs (a per-run cap alone won't stop a runaway schedule). Circuit
  breakers on 402/429; bounded retries with exponential backoff + jitter that
  honor `Retry-After`, kept to **one** layer — a custom retry loop wrapping an SDK
  that already retries multiplies requests (N × M) on every transient error.
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
    (insert-the-charge-first, or a transactional decrement/lock) — and a
    reservation a crashed worker never settles must **fail closed** (keep counting
    it against the budget) until a TTL or reconciliation reclaims it, or the
    ceiling leaks upward one dead worker at a time.
  - **Inaccurate cost math silently mis-drives the gate.** If the number feeding a
    spend cap charges cache-read / cache-write tokens at the full input rate (or
    ignores each token class's real price), it overstates spend and throttles or
    degrades work early — sometimes burning budget on a fallback that then blocks
    the real result; an *understated* number lets spend run past the cap. Bill
    each token class at its documented rate.
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
  a function can do (see `security-ai-agents.md`). On cost:
  - **Prompt-cache breakpoint**: put the cacheable marker on the longest *stable*
    prefix (system prompt, instructions, schema, few-shot) and keep per-call
    content after it; a marker on content that varies per call caches nothing, and
    a prefix below the provider's minimum cacheable token count is a silent no-op
    — verify the threshold against the provider's current docs.
  - **Cache TTL vs inter-call latency**: a short cache TTL can expire *between*
    reuses when slow work (another call, a tool loop, research) runs in the gap,
    wasting the cache. Match the TTL to the real gap, or reorder work so cached
    calls sit close together.
  - **Token-count round-trips**: a separate `countTokens`-style call before each
    generation adds a round-trip and another rate-limited request (usually free of
    token charges, but latency and a failure point) — justify it or drop it.

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
same args; an external call in the render body of a `no-store`/dynamic page; the
same full-collection scan run twice in one operation; a fresh SDK/HTTP client
constructed per call; no `timeout=`/`AbortController` on network calls; `while
True` poll loops; `CREATE INDEX` without `CONCURRENTLY`; `ADD COLUMN … NOT NULL`
with no default; unbounded in-memory caches/dicts as module globals; retry loops
with no cap; a custom retry loop wrapping an auto-retrying SDK; a prompt-cache
marker on per-call-varying content (or a long static prefix with none); a
`countTokens` call before every generation; cost math charging cache-read/write
tokens at the full input rate; a per-run cap whose default is `0`/unlimited; a
`catch` that sets a spend accumulator to empty; `SELECT sum(...)` then an
app-side spend decision; a `globalThis`/in-process job guard shared across
processes.
