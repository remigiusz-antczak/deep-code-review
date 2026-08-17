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
- **Non-atomic read-modify-write** (`x = load(); x.f++; store(x)`) under
  concurrency needs a lock, atomic primitive, or single-writer queue.
- **Lock held across I/O** — latency multiplies; deadlock risk rises when a
  second lock is taken inside. Prefer: lock, copy/mutate small state, unlock,
  then I/O.
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
- Concurrent agents/workers **claim a lane** (file set + expiring claim/
  lease) before editing; commit **explicit paths** — never `git add -A` /
  stage-all from a shared tree (cross-ref principle 7 / Phase 0 occupied
  checkout).

---

## DB / store TOCTOU

- `SELECT` then act without `UNIQUE`/transaction/`SELECT … FOR UPDATE` (or
  compare-and-swap version column) → lost update or double spend.
- "Insert if not exists" without a uniqueness constraint is still racy under
  concurrency — the constraint is the source of truth.
- Idempotency keys for charges/sends: store the key uniquely; retries return
  the first result.

---

## Tests & jobs vs real shared paths

A high-damage pattern: suite or job writes the **default production/shared data
directory** because no temp-root seam exists; "restore" in `finally`/`afterEach`
is skipped by `process.exit`, SIGINT, worker crash, or overlapping runs.

- Require an injectable store root; tests default to OS temp + unique suffix.
- Cleanup must be signal-safe or unnecessary (ephemeral dirs).
- Rate by consequence (operator data loss, PII mix-up, flaky CI) — often High
  or Critical. Depth and fix pattern: `testing-and-evals.md`.

---

**🚩 red flags**: shared mutable globals; missing `await`; non-atomic
read-modify-write; lock held across I/O; two writers on one file; check-then-act
without a constraint/transaction; tests/jobs writing a real tracked/shared data
path; stage-all from a multi-agent checkout.
