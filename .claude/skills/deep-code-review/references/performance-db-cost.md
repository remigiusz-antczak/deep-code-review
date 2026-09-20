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
  ORM's eager-load. A **GraphQL resolver** N+1 is the *structural* variant this
  textual grep misses: a field resolver invoked once per parent node in a list
  fires N nested fetches with **no loop visible at any single call site** — the
  fix is a per-request batch/cache seam (the **DataLoader** pattern), and the same
  queries-per-request test catches it.
- **Indexes**: the columns in `WHERE`/`JOIN`/`ORDER BY` on hot queries are
  indexed and the index is actually used — confirm with the query plan
  (`EXPLAIN`/`EXPLAIN ANALYZE`); a seq scan on a large table is the finding.
  Watch for indexes made unusable by a function/cast on the column, or by
  leading-wildcard `LIKE`.
- **Over-fetch**: no `SELECT *` when a few columns are needed; select only what is used.
  Result sets are bounded and paginated. Prefer **keyset/seek** pagination over a large
  `OFFSET` — which is not only a scan-cost problem but a **correctness** one: `LIMIT/OFFSET`
  is *positional*, so a row inserted before the window between two page fetches shifts
  everything down and **duplicates a row across pages** (a delete before it **skips** one);
  a `(sort_key, id)` cursor is stable under concurrent writes (the cursor key must be
  unique/tie-broken — see the non-unique-timestamp-cursor trap in
  `time-date-correctness.md`). (use-the-index-luke, *no-offset*.)
- **Push work to the DB**: filter/aggregate/join in SQL, not by pulling rows into
  app memory and looping. But don't hide an unbounded computation behind a view.
- **Connections & transactions**: a pooled connection (not one per call) — and
  likewise reuse one HTTP/SDK client per process, since constructing a fresh
  client per call throws away its connection pool; transactions scoped as tightly
  as correctness allows; no long transaction held across a network/LLM call (lock
  contention); no application logic inside a DB lock window. A borrowed/checked-out pool connection must be
  **released on every path including the error/throw path** (the general form is `security-appsec.md`
  A10) — a leaked checkout starves the pool under load; watch **pool exhaustion** (active connections
  trending toward max with checkouts never returned) as its own symptom, distinct from constructing a
  fresh client per call above.
- **Hot partition / partition-key design (NoSQL)**: a low-cardinality or skewed
  partition key (a status enum, a single active tenant, a monotonically increasing
  timestamp prefix) concentrates traffic on one physical partition regardless of the
  table's overall provisioned or on-demand capacity. DynamoDB caps throughput **per
  partition**, not just per table: "Every partition in a DynamoDB table is designed to
  deliver a maximum capacity of 3,000 read units per second and 1,000 write units per
  second" (AWS, DynamoDB partition-key best practices) — a hot key throttles long before the
  table-level limit is anywhere near reached, and raising table-level provisioned or
  on-demand capacity does not fix a single-partition hotspot. Fix: choose a
  high-cardinality key that spreads access evenly, or shard a naturally hot key with a
  random or calculated suffix (write sharding) and fan the read back in.

## Schema & data migrations (safety)

A migration is a deploy-time hazard, not just a query. Check:
- **Locking**: `ALTER TABLE` / `CREATE INDEX` on a large table without the
  non-blocking variant (`CREATE INDEX CONCURRENTLY` in Postgres — use the engine's
  online-DDL equivalent elsewhere, e.g. MySQL `ALGORITHM=INPLACE` or gh-ost; plus
  safe column-add order) locks writes and can take an outage.
- **A failed or transaction-wrapped `CONCURRENTLY` build is its own hazard.** On Postgres a
  failed concurrent index build "will fail but leave behind an 'invalid' index" — one "ignored
  for querying purposes" that "will still consume update overhead" (Postgres docs); recover by
  dropping and retrying, or `REINDEX INDEX CONCURRENTLY`, never by assuming the index is simply
  absent. And `CREATE INDEX CONCURRENTLY` **cannot run inside a transaction block** (a regular
  `CREATE INDEX` can), so a migration runner that wraps each migration in one transaction by
  default must use its escape hatch or the concurrent build fails outright.
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
- **Lock *acquisition* is a hazard, not only lock *duration*.** Even an instant, metadata-only DDL
  must first **acquire** its lock; in PostgreSQL `ALTER TABLE` takes an `ACCESS EXCLUSIVE` lock that
  conflicts with every other mode. A single long-running transaction on the target makes the fast
  DDL wait — and because the lock manager grants a request only if it conflicts with no existing
  **or already-waiting** lock (`src/backend/storage/lmgr/README`), the pending `ACCESS EXCLUSIVE`
  then makes **every later request queue behind it** — a fast migration becomes a table-wide stall
  (the wait-queue / FIFO rule; the user-facing `explicit-locking` docs describe the wait but not
  this queue effect by name). Check: run DDL with a bounded `lock_timeout` + retry/backoff, and
  confirm no long transaction is open on the target.
- **Backfill throttles on an observed backpressure signal, not just batch size.** Bounded batches
  cap transaction-log growth, not replica lag or I/O saturation; the loop reads a live signal
  (replication lag, load, error rate) and pauses above a documented ceiling — a fixed inter-batch
  sleep with no signal is not a throttle (gh-ost's replica-lag throttling, already named above, is
  the reference shape).
- **The constraint-add hazard is a family, not just `NOT NULL`.** Adding `UNIQUE` / `FOREIGN KEY` /
  `CHECK`, or changing a column type, on a populated table triggers the same full-table
  validation-scan-under-lock already flagged for `NOT NULL` — a reviewer matching the literal
  `NOT NULL` misses the siblings. Use the two-phase form: `ADD CONSTRAINT … NOT VALID` (commits
  immediately, no scan) then a separate `VALIDATE CONSTRAINT` (weaker `SHARE UPDATE EXCLUSIVE` lock,
  existing rows only); for uniqueness, `CREATE UNIQUE INDEX CONCURRENTLY` then `ADD CONSTRAINT …
  USING INDEX`; treat a type change as a rewrite hazard on the same expand-contract path. (Distinct
  from the soft-delete `UNIQUE` partial-index rule in `data-quality.md`, a NULL-semantics bug, not a
  lock/scan-cost one.)
- **`migrate` is dual-write plus a completion proof, not one step.** While the backfill runs, every
  write path writes **both** the old and new location so no row lands only in the old shape; before
  cutting reads over, the two are verified to **agree** with an explicit zero-remaining-gap check —
  not "the backfill job exited 0" — gating the enforce/contract step. Distinct from the cross-system
  dual-write in `reliability-error-handling.md` (DB + bus atomicity); this is the same-table case.

## External / API / LLM calls — the cost-and-value lens

The org-level frame is **FinOps** — cost as a continuous practice, not a one-time audit:
**inform** (tag/allocate spend to a team, feature, or environment so it is *visible* and
attributable), **optimize** (rightsize, commit/reserve steady load, kill idle or orphaned
resources), **operate** (a budget with an **anomaly alert** and a named **owner**). A cloud bill
with no allocation/tagging, no owner, or no anomaly alert is a finding independent of any one
call's cost — and, per `release-engineering.md`, buying a cost tool before the spend is allocated just
visualizes an unattributed bill.

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
    closed). **Test the present-fault branch:** unreadable path (`EACCES`), path
    is a directory (`EISDIR`), truncated/invalid body — `guard` must refuse the
    paid call, not proceed as if spend were zero.
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
- **Invalidate every *derived* entry, not just the entity's own key.** The correct-key rule
  above covers one entry; a write must also invalidate every composite / aggregate / list /
  rendered-fragment entry that *embeds* the mutated entity (a user's name cached inside a
  rendered comment, a row inside a cached list or count). HTTP caches make the split explicit:
  a cache "MUST invalidate the target URI" on an unsafe method but treats related URIs only as
  *candidates* for invalidation (RFC 9111 §4.4) — derived-key fan-out is the application's job,
  not the protocol's. Tag each entry with a surrogate key per entity it depends on and purge by
  tag, or keep an explicit dependency index; a write that clears only `entity:{id}` and leaves
  the entries embedding it is a stale-read bug no single-key test catches.
- Bounded size / TTL / eviction; a cache that only grows is a leak.
- **Bound key *cardinality*, not just total size.** A key built from an unbounded or
  high-cardinality input — raw free text, a full query string with volatile params, a
  per-request timestamp — makes almost every lookup miss while filling the cache with
  single-use entries, so it adds latency and memory pressure for no hit-rate benefit.
  Normalize and allow-list the key inputs to the dimensions that actually recur. Distinct from
  a *wrong* key (correctness, above) and from unbounded *total size* (the eviction bullet) —
  here the key *space* is too large to ever reuse.
- **Stampede / thundering herd on expiry.** A hot key expiring lets N concurrent
  misses all hit the origin at once — an outage amplifier on an expensive origin.
  Require **single-flight** (coalesce concurrent recomputes behind one lock/lease)
  or a **soft-TTL / early-recompute** with jitter; the de-dupe under *External
  calls* above is the same mechanism applied at cache-expiry.
- **Cache-aside write race.** Read-miss → load → set can interleave with a
  concurrent write so the cache ends up holding a value already superseded. Order
  it **write-store-then-invalidate** (not set-after-write), use versioned keys, or
  a delayed double-delete — a naive read-through caches a stale value with no
  conflict to warn.
- **Negative caching.** Caching a not-found / error masks a later create or a
  transient failure (stale 404s, cached errors); give negatives a **short,
  re-checkable TTL**, never the positive TTL.
- **Authoritative vs advisory — state which.** A cache treated as **source of
  truth** (write-only-to-cache, no durable store behind it) turns an eviction into
  **data loss**. (Identity-keyed caching as an authorization surface —
  `private`/`no-store`, per-principal keys — is `security-appsec.md` A01.)
- **A shared cache must key on whatever varies the representation.** When a response differs by
  request header — `Accept-Language`, `Accept-Encoding`, a currency/tenant negotiated from a
  header — a shared or CDN cache that ignores it serves one visitor's variant to another
  (English to a German reader, gzip to a client that can't decode it). HTTP formalizes the key
  rule: a cache "MUST NOT use that stored response without revalidation unless all the presented
  request header fields nominated by that Vary field value match" (RFC 9111 §4.1), and `Vary: *`
  never matches. Include every representation-varying dimension in the cache key (a correct
  `Vary`, or explicit key dimensions). Distinct from the identity/authz `Vary` rule in
  `security-appsec.md` (threat: a cross-user *auth* leak) — this is content-negotiation
  correctness.

## Concurrency, memory & payloads

- I/O-bound work is async/parallel where safe; CPU-bound work isn't blocking the
  event loop / request thread. Backpressure and timeouts on every external call.
- **Sequential `await`s with no data dependency are an accidental serialization, not
  a design choice.** A request handler / page data loader / GraphQL resolver that
  assembles one response from a few independent backend calls (a main entity fetch
  plus an unrelated sidebar, count, or config read) is often written in natural
  top-to-bottom order, `await`-ing each call before the next line runs. A call that
  reads nothing produced by an earlier call has no data reason to wait for it, yet
  still runs last — the handler pays the *sum* of every call's latency instead of
  the *max*, adding a full extra round-trip to time-to-first-byte on every request.
  The code stays correct (right data, right shape), so nothing fails; it surfaces
  only as a slow-page field report or a TTFB regression, not a test. Detect by
  listing, for each `await` in the function, whether its arguments (or a variable it
  closes over) trace back to a *preceding* `await`'s result in that same function —
  any call whose inputs don't is a parallelization candidate regardless of what it
  does. Fix by starting every mutually-independent call together
  (`Promise.all`/`Promise.allSettled`, `asyncio.gather`, an errgroup) and keeping
  sequential only the calls that truly consume a prior call's output — a call that
  reads `main.ids` after fetching `main` is a genuine dependency and correctly stays
  sequential; that shape is not the anti-pattern. Distinct from **N+1** above (a
  query *per row* of an existing result — this is a handful of independent
  *top-level* calls, present even for a single row/request) and from the
  client-side critical-request-chain waterfall in `frontend-a11y.md`'s Core Web
  Vitals section (the browser's dependent-fetch chain hurting LCP/TTI, versus the
  server handler's own `await` ordering hurting TTFB here). And distinct from the
  terse `async/parallel where safe` line above, which states the principle: this
  names the concrete failure shape (sum-vs-max latency), the detection trace (each
  `await`'s arguments back to a prior `await`'s result), and the genuine-dependency
  carve-out that one-liner leaves implicit.
- No unbounded growth: ever-growing lists/maps/caches, accumulating `defer`s,
  unclosed resources. Stream large data instead of buffering it all in memory.
- **Every append-only store on disk names a reaper — unbounded growth fills the disk, a
  total outage.** Distinct from the in-memory growth above: logs, temp/scratch files, an
  audit/event table, a dead-letter queue, a metrics/trace store, or an uploads / on-disk
  artifact directory — a filesystem path with no eviction primitive, distinct from the
  in-memory/Redis cache under *Caching & memoization* above — that only ever grows will
  eventually **fill the disk and take the whole host down** (a slow-motion, time-triggered
  outage no single request reveals; a full disk can also halt the database). For each, confirm a **retention/rotation policy with an actual
  reaper** (log rotation with a size+age cap; a TTL / partition-drop on the audit/event
  table; DLQ trimming with depth alerting; temp-file cleanup that also runs on the **crash
  path**, since a crashed process skips its own `finally`) and a **disk-headroom
  monitor/alert ahead of full** (a free-space threshold, not the outage). A store that grows
  with traffic with no bounding mechanism is the finding. (Outage consequence →
  `reliability-error-handling.md`; alert wiring → `observability.md`.)
- Payloads are reasonable; no shipping a megabyte to render a number.

**🚩 grep**: queries inside `for`/`map`/`.each`; `SELECT *`; missing `LIMIT`;
large `OFFSET`; `.all()` then filter in code; identical HTTP/LLM calls with the
same args; an external call in the render body of a `no-store`/dynamic page; the
same full-collection scan run twice in one operation; a fresh SDK/HTTP client
constructed per call; a pool checkout not returned on the error path (connections trending to max =
pool exhaustion); no `timeout=`/`AbortController` on network calls; `while
True` poll loops; `CREATE INDEX` without `CONCURRENTLY`; `ADD COLUMN … NOT NULL`
with no default; `ADD CONSTRAINT` with no `NOT VALID`; `ALTER COLUMN … TYPE` on a big table; DDL with
no `lock_timeout`; a backfill loop with a fixed `sleep` and no lag/health read; a
low-cardinality or skewed NoSQL partition key (single-tenant, status enum, monotonic
timestamp prefix) concentrating traffic on one partition; unbounded in-memory caches/dicts as module globals; a write invalidating only the
entity's own cache key with no derived-key fan-out; a cache key built from raw/unbounded input; a
shared/CDN cache with no `Vary` or key dimension for `Accept-Language`/`Accept-Encoding`; `CREATE
INDEX CONCURRENTLY` inside a transaction block or a left-behind invalid index; retry loops
with no cap; a custom retry loop wrapping an auto-retrying SDK; a prompt-cache
marker on per-call-varying content (or a long static prefix with none); a
`countTokens` call before every generation; cost math charging cache-read/write
tokens at the full input rate; a per-run cap whose default is `0`/unlimited; a
`catch` that sets a spend accumulator to empty; `SELECT sum(...)` then an
app-side spend decision; a `globalThis`/in-process job guard shared across
processes; a cache read → origin recompute with no single-flight (stampede on
expiry); a cache that stores a not-found/error under the positive TTL; a
handler/loader with independent `await`s run in top-to-bottom order where none
reads an earlier call's result (accidental serialization, not a genuine
dependency).
