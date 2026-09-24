# Concurrency & shared state

Read this when reviewing races, TOCTOU, file/DB shared writers, async
fire-and-forget, agent/worker locking, or tests/jobs that touch real shared
paths. Expands section G of `SKILL.md`. Cross-ref J /
`testing-and-evals.md` for the hermetic-test special case.

---

## Detection procedure

1. **List shared mutable resources** — in-memory globals/singletons, files,
   directories, DB rows, caches, queues, locks, "current batch" pointers.
2. **For each, name the writers and readers** and whether they can overlap
   (multi-process, multi-request, parallel tests, cron + request, agent swarm).
3. **Find check-then-act** — `exists` then `write`, `SELECT` then `UPDATE` without
   a transaction/constraint, `mkdir` then `open`, claim-then-edit without an
   expiring lease.
4. **Async edges** — promises/tasks without `await`/join; errors swallowed on
   detached work; cancellation that does not reach in-flight I/O.

---

## In-process races

- Shared mutable globals / module-level caches mutated from request handlers or
  workers without synchronization → data race or cross-request leakage.
- **Lifetime mismatch on a long-lived object (fires *with* perfect
  synchronization).** A field on a framework singleton (NestJS `@Injectable`,
  Spring `@Component`) or any module-level global that holds data valid for **one
  request/run** — a per-user snapshot, a per-run cache, a "current batch" pointer —
  leaks into the next invocation even single-threaded, with no race at all. For
  every stateful field ask: *what is its lifetime, and does it match the lifetime
  of the data it holds?* Fix by threading a per-run value as a parameter (mirror
  any per-call cache the orchestrator already passes), not by adding a lock. A
  self-authored test that calls the method **once** is structurally blind to this —
  add a two-run regression test.
- **A subscription that outlives its subscriber is the same lifetime mismatch.** A listener,
  observer, or callback registered on a **longer-lived** emitter / event bus / store / signal, with
  no deregistration when the subscriber's own lifetime ends (a component unmounts, a request
  finishes, a worker is recycled), accumulates: the live emitter retains each dead subscriber (so it
  never gets collected) and its handler keeps firing on detached state. Same question — does the
  registration's lifetime match the subscriber's? — and same fix: pair every register with a
  deregister on teardown. The stack-agnostic form of the goroutine-leak footgun in
  `lang-go.md`: a spawned task or subscription with no cancellation reachable from
  its owner's teardown.
- **A connection/subscription registry lives in *one process* — it does not span horizontal
  replicas.** A WebSocket/SSE server that keeps its live-connection or subscription map in **local
  process memory** (`Map<userId, socket>`) is correct on a single instance and **silently wrong once
  scaled to N replicas**: a publish handled by replica A never reaches a subscriber whose socket happens
  to be held open on replica B — no error, no exception, just a message that never arrives. This is not
  the lifetime mismatch above (the registry's *lifetime* is fine; its **scope** is the bug — every
  replica holds a private, incomplete view of who's connected) and it is not a backpressure, liveness, or
  DoS finding (those all assume the message *would* reach the right process if sent). Fix: move the
  fan-out through a layer shared across processes — a pub/sub adapter (Redis pub/sub, NATS) every replica
  subscribes to, or a broker in front of the sockets — or pin each user's traffic to the one replica
  holding their socket with **sticky routing** (consistent-hash or session-affinity load balancing) so
  the single-process assumption becomes true by construction.
- **Non-atomic read-modify-write** (`x = load(); x.f++; store(x)`) under
  concurrency needs a lock, atomic primitive, or single-writer queue.
- **Memory visibility is a separate axis from atomicity — name the synchronization
  edge.** For every shared mutable field read by a thread / goroutine *other than its
  writer*, name the edge (lock, atomic, `volatile`, channel op, memory fence) that
  **orders the write before the read**. With none, the write has **no guaranteed
  visibility** — the reader may never observe it, or observe it reordered relative to
  what it depends on (a plain `bool` flag polled across threads, or a lazily-assigned
  singleton reference / broken double-checked locking, are the canonical cases). This
  needs **no interleaving at all**, so a check-then-act race hunt misses it entirely.
  And a data race (an unsynchronized conflicting access, ≥1 write) is not merely
  "sometimes wrong": in **C/C++ or Rust `unsafe`** it is **undefined behavior** — the
  compiler may assume it cannot happen and hoist / reorder / miscompile around it — and
  **Go** calls such a program **incorrect**, where a racy read of a multiword value
  (interface, map, slice, string) can observe a **torn** value and lead to memory
  corruption, not just a stale scalar. A green test proves little here — a race can be 1-in-N and
  CPU-architecture-dependent (weak ARM/POWER vs stronger x86); see `testing-situational.md`
  on why a nondeterministic green run is a sample, not a proof.
- **Lock held across I/O** — latency multiplies; deadlock risk rises when a
  second lock is taken inside. Prefer: lock, copy/mutate small state, unlock,
  then I/O.
- **Lock *ordering* — not just lock *scope* — is what prevents deadlock.** Two
  code paths that acquire the **same two-plus locks in different orders** deadlock
  under contention: A holds lock 1 waiting on lock 2 while B holds lock 2 waiting
  on lock 1. This fires even when each lock is held briefly with no I/O — distinct
  from the held-across-I/O case above — and is invisible to a single-threaded test
  or one that only ever exercises one acquisition order. Applies to in-process
  mutexes and to DB row/table locks alike (PostgreSQL's canonical case: two
  transactions updating the *same two* rows in opposite order). Fix: impose a
  **fixed global acquisition order** at every site holding two-plus locks (sort by
  a stable key — table name, primary key, mutex id) — "the best defense against
  deadlocks is generally to avoid them by being certain that all applications using
  a database acquire locks on multiple objects in a consistent order" (PostgreSQL)
  — or use a primitive that avoids deadlock for you regardless of acquisition order (C++ `std::scoped_lock`: "deadlock
  avoidance algorithm is used as if by `std::lock`"). Ordering is the
  **prevention**; the `40001`/deadlock-victim retry in *DB / store TOCTOU* below is
  the **recovery** — PostgreSQL names that retry only as the fallback "if it is not
  feasible to verify this in advance," so the two are complementary, not competing.
- Missing `await` / fire-and-forget: the caller returns success while work
  fails later; unhandled rejection may crash the process or vanish.

**Grep leads:** module-level `let`/`var` mutated in handlers; `Map`/`dict`
caches without eviction bounds (also E); `fs.readFile` + `fs.writeFile` on the
same path from two call sites; `setTimeout`/`queueMicrotask` without error path.

---

## Files & whole-document stores

Common in agent/tooling repos: JSON/YAML "DB" files, append logs, lockfiles.

- **Single writer per file** (or per-key file sharding). Two writers → last
  write wins / torn JSON.
- **Write atomically**: write temp + `rename` (same filesystem) or equivalent;
  never truncate-in-place as the only durability story.
- **Reload-before-access** for long-lived readers; a process that load-once at
  boot will serve stale or post-corruption state.
- Corrupt/torn read of a critical record → **fail closed**, do not guess.
- **Present-but-corrupt / unreadable must not wipe.** `JSON.parse` (or
  equivalent) failure, permission error, or truncated body on an existing store
  must not `catch → write []/{}` and clobber last-good bytes — fail closed or
  refuse the write; absent-file empty-init is a different branch.
- Concurrent agents/workers **claim a lane** (file set + expiring claim/
  lease) before editing; commit **explicit paths** — never `git add -A` /
  stage-all from a shared tree (cross-ref principle 7 / Phase 0 occupied
  checkout).
- **A claimed lane is not filesystem isolation — give each write-lane its own
  git worktree.** A shared working tree's index, staged changes, and even
  installed dependencies are single-writer resources: two lanes editing
  genuinely disjoint files can still collide on the tree itself (a `git add -A`
  from one lane stages another's WIP; a checkout in progress in one lane
  corrupts a build running in another). A worktree per lane is a stronger,
  simpler guarantee than a convention because it isolates at the filesystem
  level, not by agreement.
- **Preflight before spawning a new write-lane.** A cheap check — running
  agents/tasks, `git worktree list`, `gh pr list --state open` — prevents
  launching a duplicate of work already in flight, itself a common source of
  wasted effort and of two lanes silently fighting over the same files anyway.
  On review: stray/stale worktrees with no corresponding open PR, orphaned WIP
  on abandoned branches, or duplicate open PRs/branches targeting the same file
  set are direct evidence this preflight was skipped.

---

## DB / store TOCTOU

- `SELECT` then act without `UNIQUE` / `SELECT … FOR UPDATE` (or
  compare-and-swap version column) → lost update or double spend.
- "Insert if not exists" without a uniqueness constraint is still racy under
  concurrency — the constraint is the source of truth.
- **A conflict-swallowing write's reported count must come from what the statement actually
  affected, not from the size of the batch the app decided to insert.** The common batch-upsert
  shape — read existing rows, reconcile in app code (no row → insert; identical → no-op;
  different → conflict), then batch-insert the "new" set with `ON CONFLICT DO NOTHING` (or
  `INSERT ... IF NOT EXISTS`, `MERGE`, Mongo `insertMany({ordered: false})`) as a race backstop
  against a concurrent caller inserting the same natural key — gets the *data* right (the
  backstop does its job) but can still misreport the *outcome*: if the code reports
  `inserted: N` from the length of the array it decided to insert, that number survives
  unchanged even when the backstop actually fires. Two callers who both read the key as absent
  and both attempt the insert produce one genuine row and one DB-level no-op; the loser still
  returns "success, inserted: 1" while its write was silently dropped. When a write uses a
  conflict-swallowing clause specifically to survive a race, read the statement's *actual*
  affected-row count (driver rowcount, `RETURNING`, or `MERGE`'s output) and reconcile it
  against the intended count — a mismatch **is** the race outcome and must be surfaced (re-read
  and reconcile, report the delta, or fail), never reported as full success. Distinct from
  `data-quality.md`'s monotonic-quality invariant (§1) — that governs a write silently
  *degrading a value*; this is a write silently misreporting its own *count* at the exact moment
  its own concurrency guard does what it was built to do.
- Idempotency keys for charges/sends: store the key uniquely; retries return
  the first result.
- **An idempotency / no-op short-circuit must diff against the *real* current state, not a
  stubbed baseline.** A shared `apply(current, next)` that skips the write when `next` already
  equals `current` is only correct if `current` is the store's actual state. A DB/adapter path
  that passes an **empty array / `{}` / a fabricated blank** as `current` (a stub the in-memory
  path never hit) defeats the short-circuit — every apply looks like a change, re-writing rows
  and re-emitting events/webhooks on every run. Load the real current rows before the diff, and
  **test the DB path with a pre-seeded existing value** so the no-op branch is actually
  exercised: an in-memory test that also starts empty passes while the DB path is broken.
- **Stale RMW across `await`:** `load → await I/O → write computed snapshot`
  without re-reading (or versioning) after the suspension races with other
  writers — including single-process JSON/Postgres JSON stores. Re-read or CAS
  after the await before persisting.
- **A CAS / version guard must cover the field the decision depends on — not just a status
  column.** A transition guarded by `UPDATE … WHERE status = 'approved'` — a guard on the **state
  column only** — still races if the decision also read an **independently-mutable** field — an `amount`, an
  `approved_by`, an evidence/answer column — that another writer can change between the read and
  the CAS: the status CAS passes, but the action fires on **stale** decision inputs. A "does it
  have a CAS?" review waved through on the wrong column is the tell. Guard every field the
  decision consumed — a whole-row version / `updated_at` CAS, or re-read and compare each input
  under the same lock — not only the state enum.
- **A CAS placed *after* a non-idempotent side-effect does not guard that side-effect — only the
  state column recording it.** A transition that (1) performs a slow external side-effect — charges
  a card, sends an email, opens a PR, writes to a third-party API — and only *then* (2) runs a
  compare-and-swap to record the new state has already committed the side-effect by the time the CAS
  finds out it lost. Under concurrency (two transitions racing the same CAS) or after a lease expires
  mid-side-effect and the transition gets reassigned, **both** actors can run the side-effect while
  only one CAS wins — the loser's side-effect already happened: unrecorded (its losing branch has no
  field for "here's what I did before I found out I lost"), and on a non-idempotent operation,
  duplicated. Distinct from the CAS-covers-the-wrong-field bullet above (there the guard sits on the
  wrong column; here it sits on the right column and simply cannot retroactively cover an action that
  already fired) and from the paused-holder lock-liveness race below (`Distributed lock/lease
  TOCTOU`) — that's a holder losing exclusivity it still believes it has; this is ordering, where a
  guard placed after an irreversible action protects nothing about that action no matter how sound
  the guard itself is. **Fix, in order of preference:** (a) claim/CAS the transition *first* and run
  the side-effect only once the claim is won, so a loser never acts; (b) if the side-effect must run
  before the outcome is known, make it idempotent/keyed (the idempotency-key rule above — the same
  idempotency fallback the fencing-token bullet below reaches for when it can't instrument the
  resource, applied here to a different cause) so a duplicate run is harmless; (c) failing both,
  record the side-effect's outcome atomically with the state transition so a losing branch's result
  stays discoverable instead of silently dropped. Read the order top to bottom — "do the slow thing,
  then CAS" is the red flag, independent of how correct the CAS itself is.
- **A transaction boundary is not itself the concurrency guard.** Under the isolation level engines
  ship by default — **Read Committed** in PostgreSQL, **REPEATABLE READ** in MySQL/InnoDB — wrapping
  a check-then-act in `BEGIN`/`COMMIT` prevents neither a lost update (two read-modify-write cycles
  on a plain read) nor write skew; the **concurrency guard** comes from `UNIQUE` / `SELECT … FOR
  UPDATE` / a CAS version column above, or an explicitly elevated `SERIALIZABLE` — the `BEGIN` gives
  atomicity and durability, **not isolation** from a concurrent read-modify-write. And a
  serialization-failure or deadlock abort (PostgreSQL SQLSTATE `40001` — "applications … must be
  prepared to retry"; a MySQL/InnoDB deadlock-victim rollback) is an **expected, retryable** outcome
  whose retry unit is the **whole transaction** (re-run from `BEGIN` with fresh reads), not the one
  failed statement — retrying just the statement silently reintroduces the lost update.

---

## NoSQL / distributed-store TOCTOU

- **Lost update with no conditional write — no transaction/lock escape hatch on a
  single-item op.** A get-then-put with no conditional/optimistic-write clause silently
  clobbers a concurrent writer. This is sharper than the SQL CAS/version-column guard
  above: SQL can always escalate an insufficient single-statement CAS to `SELECT … FOR
  UPDATE` or `SERIALIZABLE` across an explicit multi-statement transaction, but a
  single-item **DynamoDB or Cassandra** write has no such escalation path — the conditional
  clause on the write itself is the only guard that exists, not a backstop on top of one.
  (MongoDB is the partial exception: a multi-document transaction *does* take a document
  lock and raise a write-conflict on a raced modify — but it's the costlier, time-capped
  tool from the batch-limit bullet below, not a first-class default the way SQL's `FOR
  UPDATE` is; the standalone `findOneAndUpdate` filter is still the right default guard.) Require it on
  every read-modify-write: DynamoDB `ConditionExpression` (`attribute_not_exists(pk)` for
  insert-once, or an equality check on the value/version just read) — "This allows the
  write to proceed only if the item in question does not already have the same primary
  key," and on a failed match "the condition is false and DynamoDB rejects the write,
  which prevents an overwrite" (AWS, DynamoDB condition expressions); Mongo a filter that
  repeats the just-read value or version inside `findOneAndUpdate`, so a raced write
  matches zero documents instead of overwriting; Cassandra a lightweight transaction
  (`IF` / `IF NOT EXISTS`, below).
- **Default-stale read / read-your-writes.** A read issued immediately after a write, with
  no strong-consistency opt-in, can return the pre-write value — no error, no signal.
  DynamoDB defaults every read to eventually consistent ("Eventually consistent is the
  default read consistent model for all read operations") and only returns the latest
  data when `ConsistentRead` is explicitly set to `true` ("DynamoDB returns a response
  with the most up-to-date data, reflecting the updates from all prior write operations
  that were successful" — AWS, DynamoDB read consistency). Cassandra's own default is the
  weakest per-query level: "The consistency level defaults to ONE for all write and read
  operations" (DataStax, Cassandra 3.0) — one replica's answer, no cross-replica
  agreement, unless the caller opts up to `QUORUM`/`LOCAL_QUORUM`. MongoDB's default read
  concern is `"local"`: "The query returns data from the instance with no guarantee that
  the data has been written to a majority of the replica set members. Data may be rolled
  back" (MongoDB Manual, Read Concern) — `"majority"`/`"linearizable"` must be requested
  explicitly. Check: a read-after-write test that never sets the strong-read option is
  exercising the silently-weaker default path, not the guaranteed one.
- **GSI / secondary-index lag — no strong-read escape hatch at all.** A DynamoDB Global
  Secondary Index has no consistency dial the base table has: "All reads from GSIs and
  streams are eventually consistent," and "Strongly consistent reads from a global
  secondary index or a DynamoDB stream are not supported" (AWS, DynamoDB read
  consistency) — there is no `ConsistentRead:true` to fall back on here. The index is
  populated out-of-band from the base-table write: "the global secondary indexes on that
  table are updated in an eventually consistent fashion ... your applications need to
  anticipate and handle situations where a query on a global secondary index returns
  results that are not up to date" (AWS, Global Secondary Indexes). An integration test
  that writes, then immediately queries the GSI, passes reliably in a low-latency
  dev/staging environment and fails intermittently once real propagation lag shows up in
  production. Fix: read the base table (or a strongly consistent LSI) for the item just
  written, or design the caller to tolerate and retry across a bounded staleness window —
  never assume GSI read-after-write.
- **Cassandra: mixing LWT and non-LWT writes on one partition bypasses the conditional
  guard** — the same "a guard must intercept every mutation primitive" shape as an
  app-level CAS bypassed by a direct write, just enforced at the storage-engine level.
  DataStax: "mixing LWTs and normal operations can result in errors. If lightweight
  transactions are used to write to a row within a partition, only lightweight
  transactions for both read and write operations should be used" (Cassandra 3.0) — a
  plain `INSERT`/`UPDATE`/`DELETE` (a one-off ops/cleanup script is the canonical
  offender) doesn't participate in the Paxos round the `IF`/`IF NOT EXISTS` guard relies
  on, so it can race past it and reintroduce the violation the guard exists to prevent.
- **Transaction/batch limits vs. assumed SQL-unlimited atomicity** — code ported from an
  RDBMS assumes one transaction can hold arbitrary writes; NoSQL multi-item transactions
  are capped and abort past the cap instead of scaling. DynamoDB `TransactWriteItems`
  groups "up to 100 write actions," targeting "up to 100 distinct items," aggregate size
  "cannot exceed 4 MB," and "You can't target the same item with multiple operations
  within the same transaction" (AWS, DynamoDB Transactions). MongoDB also caps by time:
  "a transaction must have a runtime of less than one minute" by default, or it is
  "aborted by a periodic cleanup process" (MongoDB Manual, Transactions in Production).
  Check: any loop building one transaction/batch payload with no chunking against the
  engine's own item-count/size/time ceiling.

---

## Distributed lock/lease TOCTOU — liveness is not exclusivity

- **A time-bounded distributed lock/lease does not guarantee exclusivity against a paused or
  clock-skewed holder** — distinct from this file's own "claim a lane" convention above
  (cooperative scheduling, not an adversarial paused holder). "I hold the lock, therefore
  only I write" is false once the holder can be paused past the lease TTL — GC
  stop-the-world, CPU starvation, or a network delay on the write itself — because a second
  node legitimately acquires the lease on expiry and now **both** write. Checking "is my
  lock still valid?" right before the write does not close this: GC "can pause a running
  thread at any point, including the point that is maximally inconvenient for you (between
  the last check and the write operation)" (Kleppmann). The TTL is not a shared fact either
  — holder and lock service each measure elapsed time with their **own clock**, so a holder
  can believe its lease is live after the service already revoked it: "the server revokes
  the lease but the client still claims it owns the lease" (etcd) — the **cross-node**
  clock-skew case; single-machine NTP/DST is `time-date-correctness.md`'s. The same
  stale-holder shape recurs in **leader election** (a deposed node that hasn't learned it
  lost) — a parallel this skill draws, not one etcd asserts (etcd lists leader election
  and locks only as common patterns built on it).
- **The fix lives at the resource, not the holder — a fencing token.** Issue a monotonically
  increasing token per acquisition (etcd: its revision number) that the resource itself
  checks on write: it "requires the storage server to take an active role in checking
  tokens, and rejecting any writes on which the token has gone backwards" (Kleppmann).
  **Scope caveat:** actionable only when the reviewed code controls the resource's write
  path — an internal DB row, service, or file store. When the resource is a third-party API
  or another team's managed service that can't validate a token, the finding is narrower:
  the lock still gives no exclusivity against a paused holder, so the operation itself must
  be **idempotent or compare-and-set** instead — etcd concedes the same limit for its own
  lock: "the lock feature of etcd itself cannot be used for protecting external resources."
  Distinct from the SQS visibility-timeout race in `reliability-error-handling.md` (one
  message replayed vs. here, typically **two different** writes) and from lock
  **ordering**/deadlock above — a different failure mode.

---

## Tests & jobs vs real shared paths

A high-damage pattern: suite or job writes the **default production/shared data
directory** because no temp-root seam exists; "restore" in `finally`/`afterEach`
is skipped by `process.exit`, SIGINT, worker crash, or overlapping runs.

- Require an injectable store root; tests default to OS temp + unique suffix.
- Cleanup must be signal-safe or unnecessary (ephemeral dirs).
- Rate by consequence (operator data loss, PII mix-up, flaky CI) — often High
  or Critical. Depth and fix pattern: `testing-and-evals.md`.

## Terminating work you own

Shedding load or aborting a lane means killing **only the processes you started**,
identified by **ownership**, never by a name/command pattern or a bare port.
`pkill -f <pattern>` / `killall <tool>` reaps a sibling lane's identically-named
process, a shared dev server, the reviewer's editor, or the orchestrator itself —
invisible in any diff. `lsof -ti tcp:PORT | xargs kill` has the same trap: it also
reaps a connected client, not only the listener.
Select the listener alone: `lsof -t -iTCP:PORT -sTCP:LISTEN` (macOS, verified).
Not flag order: `lsof -ti -sTCP:LISTEN tcp:PORT` puts `-s` between `-i` and its
address, so `tcp:PORT` is read as a file (`status error on tcp:PORT: No such file
or directory`) and `xargs kill` kills nothing.

- **Own a process group / job object.** Start each lane's work in its own process
  group (`setsid`, or spawn with a new pgid; a Job Object on Windows) and record
  the pgid/handle with the lane's claim. Terminate by that id (e.g. `kill -TERM
  -<pgid>`), so the whole subtree — the tool and every child it forked — dies
  together and no unrelated process is selected, unless a child started its own
  session/group (`setsid`) and escaped it — which the orphan bullet backstops.
- **Escalate, don't nuke.** Graceful stop (SIGTERM) → a bounded grace window for the
  child to flush and release locks → SIGKILL only if it outlives the window. A
  straight SIGKILL orphans children and skips the signal-safe cleanup the store-root
  section above requires.
- **Kill and reap orphans.** A parent that exits without waiting leaves children
  reparented to init/PID 1, still holding the lane's worktree, port, or lock.
  Reaping (`wait`) only collects already-dead children — a live orphan must first
  be **killed** (group-kill, or a signal-forwarding init/subreaper), not merely
  waited on.
- **Leave a teardown record.** Killing a lane must release its claim and mark its
  worktree/lock stale-and-recoverable (the stray-worktree red flag below), so the
  next scheduler pass reclaims it rather than trips on it.
- **A "reclaim memory"/cleanup script is the same bug at fleet scale.** Reap only
  what is provably the caller's own or orphaned — parent PID 1, a cwd inside the
  caller's own worktree, or a PID file the caller wrote — never "everything in a
  port range," a bare name/command-line match (`pkill -f`, `killall`), or a
  hard-coded "protected ports" literal (goes stale the moment an operator adds a
  real serving port; source exclusions from operator config instead); default to
  a dry run, requiring an explicit `--apply` to act. `scripts/reaper_lint.py
  <path>` statically flags the four concrete shapes (a port-range kill loop, a
  terse+network `lsof` selector left unfiltered to `-sTCP:LISTEN`, a broad
  `pkill`/`killall` match, a hard-coded protected-port list); `--selftest` proves
  it fires.
- **A test of a destructive reaper/cleanup script runs it stubbed or `--dry-run`
  by default, and a commit/push hook must never invoke a live reaper at all.** A
  test (or a hook) that calls the real script live reaps every sibling lane's dev
  server and headless browser on every commit, invisible until the whole fleet
  goes dark at once — the same "runs against the real shared path" failure
  `testing-and-evals.md`'s hermetic-test rule covers for data stores, applied to
  a destructive script instead of a store. Whatever keep-list an operator-config
  exclusion resolves to must always include the **shared/preview serving port**
  by name — the port every lane's UX gate and the owner's own preview depend on —
  not only each lane's own ephemeral ports. `scripts/reaper_lint.py` also flags a
  reaper-named invocation found inside a git hook file (`.githooks/*`,
  `.husky/*`, `.git/hooks/*`, `lefthook.yml`, a `.pre-commit-config.yaml`) that
  carries no `--dry-run`/`--stub` flag; `--selftest` proves it fires.

The shedding **trigger** (memory/swap or contention, never staleness) lives in
`agentic-delivery/references/fanout-host-sizing.md`; this file is the **mechanism**.

---

**🚩 red flags**: shared mutable globals; a per-request/run field held on a
singleton/long-lived object, or a subscription/listener outliving its subscriber (lifetime mismatch); an
in-process connection/subscription registry (`Map<userId, socket>`) with no shared fan-out or sticky
routing across replicas — a publish on one replica silently never reaching a subscriber on another (a
scope mismatch, not a lifetime one); missing `await`; non-atomic
read-modify-write; load→await→write without re-read/CAS; retrying only the failed statement after a `40001`/deadlock
instead of the whole transaction; lock held across I/O;
two-plus locks acquired in a different order across call sites (ordering deadlock);
two writers on one file; corrupt/unreadable store wiped to empty; check-then-act
without a constraint or row lock (a bare default-isolation transaction is not enough); a
conflict-swallowing upsert (`ON CONFLICT DO NOTHING` / `insertMany(ordered: false)`) whose
result rowcount is ignored, with the reported count taken from the pre-write app-side array
length instead; a
NoSQL get-then-put with no conditional/version clause on the write; a read relying on a
NoSQL store's eventually-consistent default immediately after a write; a DynamoDB GSI
query assumed read-after-write consistent; mixed lightweight-transaction and plain writes
on one Cassandra partition; a multi-item NoSQL transaction/batch assumed unbounded like a
SQL transaction; tests/jobs writing a real tracked/shared data
path; stage-all from a multi-agent checkout; multiple concurrent-agent write
lanes sharing one working tree with no worktree-per-lane isolation; a stray or
stale worktree with no corresponding open PR; duplicate open PRs/branches
targeting the same file set (no spawn-time preflight); load-shedding or lane-abort
by name/command-line/port match instead of an owned process group; a killed lane
whose children outlive it (orphaned worktree/port/lock); a
plain (non-atomic, non-`volatile`) flag or field shared across threads with no
named synchronization edge — a memory-visibility bug, not only an interleaving race; a
distributed lock/lease (Redis/Redlock, ZooKeeper, etcd, a DB-row lease) guarding a write to
a shared resource with no fencing token on the write path and no idempotency/CAS fallback —
especially a "re-check the lease, then write" pattern, which reads as safe but isn't; a
non-idempotent side-effect (a charge, a send, a third-party write) performed before the CAS/claim
meant to guard its transition — the guard covers the state, not the action that already fired.
