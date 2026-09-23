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
- **Distinguish a timeout-abort from a user-cancel before suppressing the error.** An `AbortController`
  fires for *both* a deadline timeout and a deliberate user cancel (navigation away, a cancel button), so
  code that blanket-swallows an `AbortError` as "cancelled, ignore" **hides a real timeout** — a timed-out
  request looks identical to a user who walked away. Tag the cause (`AbortSignal.reason`, or a separate
  controller per cause): a **user-cancel** is expected (drop silently — no error, no retry); a **timeout**
  is a failure (surface/log it, and it is the retry-eligible case). A bare
  `if (err.name === 'AbortError') return` with no reason check is the finding.
- **Propagate the deadline; don't reset it at each hop.** A service handling a
  request that arrived with a deadline must pass the *remaining* time down to its
  own calls, not start each one on a fresh full timeout — otherwise a chain of N
  hops that each allow T seconds lets one request run up to N×T while the original
  caller already gave up at T (work continues that nobody is waiting for). Derive
  each downstream timeout from the time left on the inbound deadline (minus a small
  buffer), and **check the deadline still has room before a retry** — a retry begun
  after the budget is spent only adds load for a discarded result. This is the
  wall-clock cousin of bounding an agent's recursion tree by depth/steps/spend
  (`security-ai-agents.md`), and distinct from merely *having* a timeout (above):
  here each downstream timeout is a function of the caller's remaining one.
- **Retry only what is safe.** Idempotent GETs / put-with-idempotency-key: OK
  with jittered backoff and a hard cap. Non-idempotent POST/charge/send: retry
  only behind an idempotency key or after echo-verify that nothing applied.
  **Retry-forever** and **retry-without-jitter** are findings.
- **An idempotent-retry existence check must scope to *success* states.** Before
  re-doing work, code that asks "did a prior attempt already do this?" must match
  only **completed/succeeded** records — a status-agnostic lookup (`state=all`, or
  any row with the key) also matches a **reverted, cancelled, or failed** prior
  attempt (a closed-not-merged PR, a cancelled-not-fulfilled order) and misreports
  the work as done, so the retry silently **skips real work**. Filter the existence
  query by a terminal-**success** status, and test it against a key whose only prior
  record is non-success (confirm the work re-runs).
- **Cap retries with an aggregate budget, not only a per-request limit.** A
  per-request hard cap (above) bounds a single call, but if *every* failing call
  retries during a partial outage the combined retry traffic multiplies load on an
  already-struggling dependency and tips a brown-out into an outage. Add a process-
  or client-wide **retry budget** — a ceiling on the retry *rate* (a fixed cap per
  process, or a bounded fraction of live request volume above a small floor) — and
  once it is exceeded, **fail fast instead of retrying**. Distinct from the circuit
  breaker below (which trips on a *destination's* health) and from keeping retries to
  one layer (`performance-db-cost.md`, which stops a single request's attempts from
  multiplying): the budget caps *this* client's own aggregate retry rate across all
  requests, regardless of any one destination's state.
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
  unreachable — **including its own harness failing to launch** — **blocks** (the missing-input fail-closed rule, `domain-b.md`;
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
- **A changed-files / diff gate is a *detective* control — resolve its base by a ref,
  and treat an unreadable diff as could-not-check, never as an empty diff.** A gate that
  decides *what to check* by diffing against the PR base first has to **obtain** that base.
  Resolving it by an **exact commit SHA** (`git fetch origin <base-sha>`) fails on a
  **shallow CI checkout** (a small `fetch-depth`/`--depth`, common to keep CI fast) whenever
  that commit sits outside the truncated history — a base older than the clone depth, a moved
  or force-pushed base, a rewritten head. The fetch errors and the diff cannot be computed;
  the defect is what the gate does **next**. Because a diff/changed-files gate is a
  **detective** control — its job is to *find* what changed, not to attest a safety property —
  an unreadable diff is **unknown → could-not-check → fail open**: emit a distinct
  skipped/neutral status and, where the gate routes other checks, **run them conservatively**
  (treat everything as in scope). Never fabricate an **empty** diff that silently passes or
  skips the downstream checks (a false green), and never — the opposite error — hard-fail the
  PR as if a violation were found. Two fixes, both needed: **fetch the base by ref** (the
  branch name, `git fetch origin <base-branch>`, or `--deepen`/`--unshallow`) so resolution
  survives a moved SHA and a shallow clone; and give the can't-read-the-diff path a **distinct
  could-not-check exit and message** (the rule above), so it reads as *skipped*, not *clean*.
  This is the diff-detector inversion of the security / authz / integrity / spend **exception**
  above: *those* fail **closed** on an unreadable input; a change **detector** fails **open**,
  because "found nothing because it could not look" must not read as "found nothing." (Whether
  the *repository history itself* is shallow — `git rev-parse --is-shallow-repository`,
  `git fetch --unshallow` — is `branch-and-merge-hygiene.md`; this bullet is the **gate** that
  consumes that history.)
- **A gate whose input is an *allow-list of file extensions* silently under-covers the committable
  surface — a green then means "clean within the subset I scanned," not "clean."** A name / secret /
  banned-token grep-gate that selects files by an **include-list** of extensions
  (`ts,js,md,json,sh,yml,txt`) never scans a committable type omitted from it (`*.py`, `*.ipynb`,
  `*.env.example`): a banned token there is invisible and the gate still prints `clean`, exit `0` —
  **false confidence, worse than no gate**, because it trains the team to trust a no-op. Distinct
  from the skipped-*scope* and unenumerated-*surface* rules in `method.md` (there a missing
  pattern-list disables one scan, or a route the sweep never hit): here the gate's single scan
  **ran**, but its **input file-set** is an allow-list that is a **subset** of what the repo can
  commit. Fix — make coverage a **superset of the committable surface**: derive the file set from
  `git ls-files` (scan-all-then-exclude / deny-list), not a hand-maintained include-list; and for a
  **security / secret / identifier** gate treat an **unrecognized committable type as
  could-not-check → fail closed**, never a silent pass (the fail-closed exception above — a
  name/secret gate is exactly the case the detective-control rule above does *not* fail open). Prove
  it with a **negative control per committable type**: plant a banned token in a throwaway file of
  each type the repo commits and assert the gate catches **every** one — a gate with no such
  self-test is `unverified`, not clean. (The reviewer-side reading — a green clears only the surface
  it enumerated — is `method.md`; this is the gate-*design* fix.)
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
  `domain-w.md`; this is the synchronous-service case).
- **🚩** one global pool/client shared by a critical and a background/optional call; no admission
  check before expensive work when that dependency's breaker is already open; a fixed downstream
  capacity silently shrinking per replica with no floor; a synchronous service with no self-overload
  shed/degrade path. (Sibling to the circuit-breaker rule above; distinct from tenant-vs-tenant
  noisy-neighbour isolation in domain T — a different axis.)

---

## Partial failure & persisted state

- Batch loops: **per-item** try/catch (or equivalent); one poison item must not
  abort the whole run unless the product explicitly requires all-or-nothing —
  and then that must be transactional. **On a batch-triggered event-source handler
  (a queue/stream trigger invoking the code with a batch of records), this per-item
  guard bounds only what your code does; whether the *platform* treats the batch as
  a partial or total failure — and so retries/deletes only the failed items versus
  the whole batch — is a separate response contract, set by the invocation's
  response shape plus an event-source-mapping config flag, not by this try/catch**
  (depth, failure modes, and the config-flag fix: `domain-w.md`).
- **A "never throws" function must guard every throwing call it makes — not lean on
  one outer `try`.** A parse/identity helper whose contract is "returns a default,
  never throws" is only as safe as its coverage: a `decodeURIComponent` (URIError on
  a stray `%`), `JSON.parse`, `atob`/base64, or `new URL()` sitting in a `.map`
  callback, a default-argument expression, or any statement **outside** the guarded
  block throws **past** the contract and crashes the caller that trusted it and
  omitted its own guard. Wrap each decode/parse in its own try/catch (or prove it
  sits inside the outer one), and test the helper with malformed input for every
  such call.
- **In a parallel fan-out whose contract is "every read fails soft," one read left unguarded takes the whole page down — find it by diffing the siblings, not by trusting the repeated shape.**
  A server-rendered page (or any loader) that starts N independent reads — `Promise.all`, or N promises kicked off then awaited later — often documents a **whole-function** contract in a docstring or comment: *every read degrades to an empty/fallback result on failure rather than taking the page down*.
  The fail-soft wrapper (`.catch(err => { log(err); return <safe fallback> })`) tends to be added **read-by-read** across several change sets, each closing one incident, so N-1 reads carry it and exactly **one** is left bare and `await`ed unguarded — often the **first** promise started (textually distant from the cluster) or the one whose failure "obviously can't happen" (a store that is "always up"). When that read's I/O rejects (a transient DB blip, a timeout, a flaky upstream) the rejection propagates out of the loader — past any local try/catch, which the doc's own promise usually means there is none — and one transient failure crashes the **entire** page, taking down the N-1 siblings that would have degraded invisibly. It is invisible on the happy path (every test resolves), so it defeats the exact resilience it was reviewed for, and a reviewer scanning the block sees `.catch` repeated four times and pattern-matches the whole fan-out as safe.
  **Detect it by diffing the fan-out against its stated contract:** for any function whose doc claims "every read degrades," list every promise it starts and confirm each has its **own** `.catch`/try resolving to a safe fallback (not a re-throw) — a `.catch` chained after the `await` still leaves a window if the promise is also awaited elsewhere unguarded. Don't stop at "most of them do."
  **Verify before filing:** confirm the underlying call genuinely **can** reject (a bare `pool.query`/`fetch` with no guard anywhere down its own chain, not one already fail-soft two levels down), the value is actually consumed downstream (not dead code), and no wrapping try/catch higher in the same function already neutralizes it. **The fix** is the same one-line `.catch(fallback)` the siblings use; the value is in **finding** it — add a regression test that stubs the one read to reject and asserts the loader still resolves with a degraded-but-honest result instead of throwing.
  Distinct from the *"never throws" helper* bullet above (a **single** helper whose own `decodeURIComponent`/`JSON.parse` throws past its contract — here the siblings' wrappers *establish* the fail-soft pattern and the gap is the one outlier that diverges from them), from the *find-the-house-primitive / uniform-routing* bullet above (which greps a **shared** retry/timeout wrapper and confirms every I/O site routes through it — here the "pattern" is a per-function repeated `.catch` keyed on a stated whole-function contract, not a house wrapper), and from `testing-and-evals.md`'s *diff-the-guard-conditions-across-N-sibling-copies* rule (which diffs a **logic guard clause** across N reconciliation checks, harm = an inflated miscount — this diffs an **error-handling wrapper** across N I/O reads, harm = a crash that violates a stated fail-soft contract).
- **The near-inverse of the unguarded read: a fail-soft `.catch` that returns a bare
  *empty* value launders a failed load into a legitimate-looking empty state — every read
  is guarded, yet a failure is indistinguishable from a genuinely-empty section.** Harden
  the fan-out above the way it prescribes — wrap **every** read in its own `.catch` — and a
  subtler defect reappears whenever the fallback is an *empty* result the surface treats as
  real data: `.catch(err => { log(err); return [] })` (or `return null` / `{ items: [] }` /
  `0`). The page no longer crashes, but a transient failure of one read (a DB blip, a
  timed-out upstream, a throttled API) now renders as **"0 items / nothing here"** —
  indistinguishable, to a viewer *and* to any downstream count/total, from the section being
  **genuinely empty**. On a shared multi-viewer dashboard that is worse than the crash it
  replaced: the crash was loud and got fixed; the false-empty is silent, shows the same "0"
  to everyone, and under-reports live data as absence. The resilience the fan-out was
  reviewed for (don't take the page down) is present; the **honesty** — saying *why* a
  section is empty — is missing. It is a **data-state** defect, not a control-flow one.
  **Fix: the fallback must carry a distinguishable failed/degraded signal, not an empty that
  reads as "nothing here."** Return a tagged result — `{ status: 'error' }`,
  `{ stale: true, lastGood }`, or a sentinel the renderer maps to an error/stale marker —
  and render "couldn't load" (or last-good behind a stale badge) for a *failed* read,
  reserving the empty state for a read that **succeeded with no rows**. Test the fork: stub
  the read to **reject** and assert an error/stale marker (not the empty state); stub it to
  **resolve empty** and assert the empty state — the two must diverge. **Discriminator vs
  the unguarded-read bullet above:** that one is a **missing** guard → one rejection crashes
  the loader (fix: add the guard the siblings have); this one is a **present** guard whose
  fallback *value* **erases the error/empty distinction** (fix: make the fallback honest).
  They are a matched pair — the sibling's one-line `.catch(() => [])` *closes* the crash and
  *opens* this false-empty, so guard every read **and** make each guard's fallback
  distinguishable from success-with-no-rows. Distinct from the *present-empty ≠ absent* rule
  in the Detection procedure (that bars **writing** an empty artifact over last-good *bytes*;
  this bars **displaying** a failed read as empty) and from the fail-closed-to-last-good
  preflight below (which degrades to a cached snapshot; a bare read fan-out usually has none,
  so the honest fallback here is an explicit error/stale marker, or last-good only where one
  exists).
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
- **A UI backed only by a volatile local cache blanks on every routine rebuild, not an
  outage — the fix is architectural, not a longer timeout.** Unlike the last-good preflight
  above (a *live-read failure* falling back to an existing snapshot), here the cache itself
  does not survive the rebuild — an ephemeral disk, a fresh container, a cleared build cache —
  so the very first request after every deploy has no last-good to serve, renders blank, and
  reads as "flaky prod" that never reproduces locally (the cache there is never wiped). Fix
  needs three parts together: a **committed fallback** dataset in the repo so a cold cache
  never renders bare-blank; **idempotent auto-rehydration** that repopulates it on boot with
  no manual step; and a **data-freshness gate** alerting when served data exceeds an age
  bound, so a silently-broken rehydration is caught before a user notices. Cross-ref
  `data-quality.md`'s disposable-cache rule — there the fix is a system-of-record; here, often
  a store-less front-end/edge surface, the durable copy is the one committed to git.

---

## The dual-write problem — a local write + a remote publish are not atomic

A handler that **persists state and then publishes an event / calls another
service** as two separate steps (`db.save(x); queue.publish(e)`) has no atomicity
across the two systems. A crash, timeout, or deploy **between** them — or a publish
that fails after the commit — diverges them: the state exists but no event fired
(**lost**), or the event fired but the transaction rolled back (**phantom**).
Retrying naively double-publishes.

The **same-table** analogue — a schema-migration backfill that must write both the
old and the new column shape until cutover — is a deploy-time hazard reviewed in
`performance-db-cost.md` §"Schema & data migrations (safety)", which distinguishes
it from this cross-system case; that section is the home of migration safety even
when the PR carries no query-performance change.

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
  compensation (`domain-w.md`), which sequences several operations — this is
  the atomicity of **one** write plus **one** publish.

## State-machine / lifecycle correctness — model transitions, guard them, leave no impossible or stuck state

Any entity with a **status / lifecycle** (`order: pending→paid→shipped→refunded`, a
subscription, a document draft→published, a job, a ticket) is a state machine, usually
**implicit**. Review it as one — distinct from multi-step **saga** compensation
(`domain-w.md`) and from the dual-write atomicity above; this is the correctness of
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
- **Redelivery isn't only shutdown- or failure-triggered — a slow-but-*successful* invocation can
  lose the visibility-timeout race.** A slow invocation (cold start, a slow downstream, a GC pause)
  can still be mid-flight when its message's visibility timeout expires, letting a second worker pick
  up and process the same message concurrently before the first deletes it (a wall-clock race between
  the visibility timeout and the processing duration, distinct from the *scheduler*-level
  overlapping-run case in `domain-w.md`), so the idempotent-processing requirement
  above must also hold against this non-failed concurrent duplicate, not only a post-shutdown or
  post-failure retry.
- **Release the lease and flush before exit.** A shutting-down replica releases any lock/lease/claim
  it holds (e.g. a distributed lock or a leader-election lease) and flushes buffered telemetry — else a scaled-down
  instance blocks its replacement for the lease TTL and loses its last logs/metrics.
- **A request killed mid-write at shutdown must be retry-safe** — the same idempotency-key discipline
  the retry rules above require, applied at the shutdown boundary.
- **Startup is the mirror of shutdown: gate readiness until dependencies are reachable, and
  wait-with-backoff for them at boot — don't crash-loop.** On boot a service must **not
  report ready until its critical dependencies (DB, cache, broker, downstream API) are
  actually reachable**, and must **retry connecting with bounded backoff** rather than exit
  on the first failure — where *bounded* means **capped and observable**: a dependency that is
  merely **not yet up** (a transient blip or start-order race) is worth retrying, but one that
  is **definitively broken** (rejected credentials, an unresolvable host, invalid config)
  should **escalate/alert**, not retry silently forever — an uncapped silent loop only trades a
  visible `CrashLoopBackOff` for a pod stuck **Running but never Ready**, so emit a log/metric
  on each failed attempt. A boot path that assumes a dependency is up and `exit(1)`s when it
  isn't **crash-loops** under an orchestrator (restart → fail → CrashLoopBackOff), turning a
  transient blip or a deploy-ordering race (the app rolled out before its DB/migration) into
  a self-inflicted outage; keep **liveness separate from readiness** (a `startupProbe` gives a
  slow boot its own budget so the liveness probe doesn't kill it mid-start — a native example,
  not a pinned spec) so a slow dependency doesn't get the pod killed while it waits. Don't
  assume strict cross-service start-order —
  each service tolerates a not-yet-ready peer.
- **🚩** a SIGTERM handler that stops the listener before failing readiness; an unbounded or zero
  drain; a worker that exits without nacking its in-flight job; a readiness endpoint hardcoded to
  `200` (it can neither gate a drain nor signal unhealthy — the always-200 health check flagged in
  `observability.md` breaks safe rolling deploys, not just monitoring); a boot path that connects
  to a dependency once and `exit(1)`s on failure (crash-loop), or a readiness probe that passes
  before dependencies are wired.

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
- **A build/codegen step keyed on an explicit source allow-list silently emits
  *nothing* for an input outside the list — the build-time face of the silent
  no-op.** A generator that scans only an enumerated set of dirs/globs (a
  utility-CSS **content** scanner, a codegen input list, an asset glob) produces
  **zero output** for a file outside that scope with **no build error, lint, or
  console warning** — the omitted file's tokens still ride the source (a
  `className` string, a symbol), so every catch layer stays quiet and only the
  missing *effect* shows. It recurs because the list is configured once over the
  dirs that existed then, and a later new subtree / package / route-group falls
  outside it unnoticed: "scanned a dir, found nothing to emit" is
  indistinguishable from "never scanned the dir." A **source-text-presence test**
  (grep that the token appears in a file) passes and **proves nothing** — the
  string is there; it just maps to no emitted rule. Fix: assert the **produced
  effect**, not the source token (a canary that reads the real generated
  artifact — a computed style, an emitted symbol — for one input per top-level
  source dir), and add a CI guard that enumerates every dir holding recognizable
  source files and **fails the build when one is outside the configured scan
  scope** — the coverage-superset move a gate needs for its own input file-set
  (verification-gate family above), here for a build input set. Whole-tree
  auto-detection avoids the omission but has its own failure mode (sweeping a
  build-output / `dist` dir into the scanner corrupts the emitted set — often
  *why* an explicit list was chosen), so it is not a free win. Sibling to the
  registration/flag cases above: there a subsystem never *runs*; here a build
  step *runs but covers a subset of its inputs*.

---

**🚩 red flags**: swallowed exceptions; one read in a documented fail-soft parallel fan-out left
without its own `.catch` while its siblings have one (one transient reject crashes the whole loader); a
fail-soft fan-out whose per-read `.catch` returns a bare **empty** value (`[]`/`null`/`0`) so a failed
read renders as a legitimate empty state indistinguishable from success-with-no-rows (return a tagged
error/stale fallback, not a silent empty);
retry-forever; no timeout; a per-request
retry cap with no aggregate retry budget; a downstream call started on a fresh full
timeout instead of the caller's remaining deadline; non-idempotent
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
must preserve last-good and signal failure, not write-then-throw); a build / codegen step keyed on an
explicit source allow-list (a scanned-dirs/globs list) that silently emits nothing for a file outside
it — no error or warning, and a source-text-presence test still passes; a name / secret grep-gate
whose scanned file set is an include-list of extensions (a **subset** of the committable surface)
reporting `clean` while an omitted committable type (a `*.py`) is never scanned.
