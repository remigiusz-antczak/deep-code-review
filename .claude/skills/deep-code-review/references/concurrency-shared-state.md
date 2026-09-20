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
  `language-stack-redflags.md`: a spawned task or subscription with no cancellation reachable from
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
  CPU-architecture-dependent (weak ARM/POWER vs stronger x86); see `testing-and-evals.md`
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
identified by **ownership**, never by a name/command pattern. `pkill -f <pattern>`
(matched on the command line) or `killall <tool>` (matched on the process name)
reaps a sibling lane's identically-named process, a shared dev server, the
reviewer's editor, or the orchestrator itself — cross-lane collateral damage that
is invisible in any diff.

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
  Reaping (`wait`) only collects already-dead children — a live orphan must first be
  **killed** (a group-kill that reaches an escaped descendant, or a signal-forwarding
  init/subreaper that kills then reaps), not merely waited on.
- **Leave a teardown record.** Killing a lane must release its claim and mark its
  worktree/lock stale-and-recoverable (the stray-worktree red flag below), so the
  next scheduler pass reclaims it rather than trips on it.

The **trigger** for shedding — when memory/swap or contention says back off, and
never on staleness — lives in the `agentic-delivery` overlay
(`agentic-delivery/references/fast-agentic-delivery.md`); this is the **mechanism**
for acting on it without collateral damage.

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
without a constraint or row lock (a bare default-isolation transaction is not enough); tests/jobs writing a real tracked/shared data
path; stage-all from a multi-agent checkout; multiple concurrent-agent write
lanes sharing one working tree with no worktree-per-lane isolation; a stray or
stale worktree with no corresponding open PR; duplicate open PRs/branches
targeting the same file set (no spawn-time preflight); load-shedding or lane-abort
by name/command-line match (`pkill -f` / `killall`) instead of an owned process group;
a killed lane whose children outlive it (orphaned worktree/port/lock); a
plain (non-atomic, non-`volatile`) flag or field shared across threads with no
named synchronization edge — a memory-visibility bug, not only an interleaving race.
