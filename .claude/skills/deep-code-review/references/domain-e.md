# Domain E checklist

Read this when domain E (Performance, efficiency & cost) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### E. Performance, efficiency & cost → `references/performance-db-cost.md`
- **Algorithmic**: no accidental O(n²)+ on hot paths; right data structure;
  compute-once.
- **Database**: no N+1; needed indexes exist and are used (check the query plan);
  no `SELECT *`; results bounded/paginated; work pushed to the DB; pooled
  connections; tight transactions (no lock held across a network/LLM call).
- **Schema & data migrations**: expand → migrate → contract (backward-compatible
  with old + new code mid rolling-deploy); non-blocking index/column ops
  (`CONCURRENTLY`); `NOT NULL` only after backfill+default; backfill in bounded
  batches **outside** the DDL transaction; a tested rollback path; **snapshot
  before the mutation, not after**; a data-transforming migration must not
  violate D. `CONCURRENTLY` runs **outside** a transaction block (a migration runner that wraps
  each migration in one must opt out) and a failed concurrent build leaves an **invalid** index to
  drop or `REINDEX`, not silently absent.
- **External / API / LLM calls — cost-and-value lens**: is each call *necessary*
  now? cache with a correct key + invalidation (invalidate every *derived*/composite entry, not
  just the entity key; bound key *cardinality*; a shared cache keys on `Vary`); batch;
  single-flight duplicates;
  events over polling; don't re-fetch/re-embed unchanged inputs. Enforce spend
  caps **before** the call — per-run **and** a global/monthly cap (from an
  append-only ledger); a **dry-run must cost nothing** (gate the call, not just
  the write); calibrate a big paid run on a small zero-write sample first. For
  model calls, cache the longest stable prompt prefix, bill each token class at
  its real rate, and don't wrap an auto-retrying SDK in a second retry loop. Spend
  caps have subtle holes — a per-run cap whose default is `0`/unlimited is not a
  cap, a ledger loader that resets to empty on a read fault fails **open**, and a
  `SELECT sum()` then check-then-act (or an in-process singleton shared across
  multiple processes) is not concurrency-safe: the spend-safety checklist is in
  `references/performance-db-cost.md`.
- 🚩 queries in a loop, `SELECT *`, missing `LIMIT`, identical repeated
  HTTP/LLM calls, an external call in a `no-store`/dynamic render body, a fresh
  SDK/HTTP client per call, a prompt-cache marker on per-call-varying content, no
  timeout, `CREATE INDEX` without `CONCURRENTLY`, `ADD COLUMN
  … NOT NULL` w/o default, unbounded caches, per-run cap but no global cap, a
  per-run cap defaulting to 0/unlimited, a spend ledger that fails open on a read
  error, a `SELECT sum()`-then-act spend check, no dry-run/apply switch at all.
