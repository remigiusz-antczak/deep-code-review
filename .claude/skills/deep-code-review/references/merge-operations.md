# Merge operations — landing PRs and merge-gate mechanics

Read this when landing or sequencing PRs, or when a merge gate or required check is stuck, stale, red, or in question. Split from `branch-and-merge-hygiene.md`; its triage, decision tree, and safety rails apply first, and every § number below refers to that file.

### Merge trains — landing several ready PRs without a platform merge queue

When several independently-green PRs are ready at once and no merge queue is available, merging one at a time
and waiting for the base's CI between each serializes for no benefit — the base was already known-green before
each subsequent PR's own checks ran. A **merge train** verifies the *combination* once instead:

1. Build a **throwaway integration branch** off the target with every candidate PR's head merged in. Resolve
   any collision **keep-both**, never dropping one side — a generated/compiled-file collision follows §6's
   regenerate-don't-hand-splice rule.
2. Run the **full aggregate gate once** on that union. Green means the combined tree is sound.
3. Merge the member PRs **individually and back-to-back**, preserving each one's own commits and issue-closing
   keyword. **Never squash the union into one commit** — that orphans every member PR's own issue and review
   thread instead of closing them.
4. Discard the integration branch; it's never itself merged.

**The union verifies the combination; it is not on the critical path.** Its CI aggregates every member's
checks, so it concludes no sooner than the slowest member and usually later — treating "union CI still pending
or red" as a reason to hold members already green re-serializes the very wait the train exists to remove. Once
the aggregate gate is green the proof is in hand: merge the green members (step 3) and **close the union with
a pointer to where they landed**. "Wait for union CI, then squash/merge the union" fails twice over — the wait
is redundant and merging the union orphans its members' issues (step 3).

**Sequence a gate-adding PR last within the batch.** A PR that adds a new required gate, merged first, forces
every other PR in the batch to retrofit a gate that didn't exist when it was authored — extra round-trips for
no benefit. When triaging several ready branches at once, check whether any changes required-CI/gate
configuration and put it at the back of the landing order.

### Mergeable is a snapshot against a moving base head — re-check before each merge; freeze the sweep while a resolver runs

"Green + mergeable" is a **snapshot against the current base head, not a durable property**. Landing PR A can
flip an overlapping PR B from MERGEABLE back to CONFLICTING — A touched a file B also touches, so B now needs
a rebase — while **B's checks stay green** (they ran against the old base; only its mergeability changed).
This bites at two scales:

- **Snapshot-then-batch (the coordinator *reads* staleness).** A coordinator that snapshots "these five are
  green + mergeable" and merges them one by one finds PRs 2..5 increasingly CONFLICTING as earlier ones land —
  then stalls, or (worse) force-merges onto a base the PR was never tested against. **Re-check mergeability
  immediately before *each* merge, never once at the top of the batch** — mergeable has a shelf life of "until
  the next overlapping merge." **Group the batch by the file sets each PR touches: serial-with-rebase *within*
  a group, parallel only *across* disjoint groups.** Merging two PRs that share a hot file as if independent
  is the bug. (The merge-train union above surfaces these collisions up front and proves the *combination
  builds* — but doesn't make a conflicting member mergeable: the union branch is thrown away and the member
  branches are left unchanged, so each member still resolves against the moving target and the per-merge
  re-check still applies at step 3. Sequence the resolver first, *then* run the train.)

- **Sweep-while-resolving (the coordinator *causes* the staleness).** Running a **merge sweep** (landing green
  PRs into a shared base) **concurrently with** a **resolver lane** (rebasing a conflict-prone set against
  that same base) makes the sweep the very thing re-dirtying the cluster it's trying to land: every merge
  moves the base head and invalidates the resolution the resolver just computed, so the PRs it was making
  mergeable flip back to conflicting — an unbounded treadmill where the broadest, hottest-file PRs never
  converge. **Freeze the *merge* step — not the build step — while a resolver is active against the base:**
  lanes keep taking PRs to green (no stall, no visible slowdown), green PRs **queue** instead of merging, the
  **hardest-to-rebase set lands first** against a now-stable base, then the queue drains back-to-back.
  Freezing the merge rather than pausing all work removes the invalidation without dropping throughput.

**A third state — `UNKNOWN` while the forge recomputes.** Distinct from the MERGEABLE↔CONFLICTING flip above:
**GitHub** computes mergeability **asynchronously** (not independently verified for other forges), so right
after any base-changing merge an overlapping PR's `mergeable` field is briefly **`null` / `UNKNOWN`** while
the recompute runs — that's *not-yet-known*, not CONFLICTING. A batch merger that treats `UNKNOWN` as
CONFLICTING skips a PR that's actually fine (landing only the **first** of a back-to-back set); one that
treats it as MERGEABLE merges blind. **Poll until it settles** to a definite state (a bounded 2–4 tries with
short backoff), retry **only `UNKNOWN`**, and never auto-retry a definite `CONFLICTING` as if transient.

Both value-flip cases above are the **stale-base failure below at the mergeability layer** — a quantity
computed against one base head, consumed against another — except the moving head breaks *mergeability* here,
not a gate's diff. A fleet coordinator applies this whenever it batches merges; `agentic-delivery`'s
`merge-queue-worktrees.md` cross-references here rather than restating it.

### A finished check's green can be stale off a prior evaluation — confirm it ran against the current head, and know each gate's trigger model

A green that already **finished** isn't durable either — the reviewed object can change under it, so the check
you see may not have run against what you're about to **merge**. Distinct from the moving-base cases (the
mergeability-snapshot above; the stale-base gate-diff below): here the base need not move at all. Two ways a
finished green goes stale:

- **Trigger coverage — the check never re-ran.** Most gates re-evaluate only on a **subset of events**
  (typically a new push / new head). A mutation **outside** that set — **editing the body or metadata**,
  **retargeting the base**, a bot **amending the description**, or a gate reading a **cached artifact / body**
  captured at an earlier run — never fires the check, so its last verdict certifies the **pre-mutation**
  state.
- **Timing — the check will re-run but has not yet.** A mutation that **does** fire the trigger — a **rebuild
  / rebase** that pushes a new head — has a run **still in flight**, so the green you currently see belongs to
  the **pre-rebuild** head. Merging now lands an **intermediate** state the gate never certified for the final
  head: wait for the fresh run to conclude, and don't merge a change another lane is still rebuilding.

Either way the green is real; it just certifies a state that no longer exists. So before merging, **confirm
the green reflects the current head / inputs**: read the **SHA (or input digest)** the passing check actually
ran against and compare it to what you're about to merge (the pin-the-verdict-to-the-exact-SHA discipline,
`method.md`). And **know each gate's trigger model** — which events re-evaluate it and which don't — so a
mutation the triggers **don't cover**, or a run **still in flight**, reads as **invalidating**, not trusted.
These are the verdict-staleness siblings of the moving-base cases: there the *base* moved under a still-valid
check; here the *reviewed object* changed — via an event the check never saw, or one whose run hasn't
concluded. (Distinct, too, from a required check that never ran at all for this PR — the config-gap blocker
below.)

- **🚩** merging on a green produced **before** a body/metadata edit, a base retarget, or a rebuild the gate's
  triggers ignore; a "these are green" batch snapshot consumed after any such mutation; trusting a check's
  **colour** without reading the head / input digest it actually ran against.

### Red base: discharge the deadlock with a train, never an override

When the target branch itself is red, a merge preflight requiring the base green refuses the very fix PRs that
would green it — a **deadlock**, not a per-PR failure. Agents stall, invent one-off exceptions, or serial-wait
forever. The escape is the merge train above, used deliberately as the *discharge* vehicle:

1. **Discharge (preferred).** Union the individually-green fix members, run the aggregate gate once, and on
   green merge them back-to-back (the merge-train procedure above). The union's green **is** the proof the
   preflight's "base green at head between merges" wait was asking for, so it **discharges** that wait — which
   the red base can't otherwise satisfy.
2. **Serial fallback.** Wait for the base to rebuild between merges only when a true dependency stack can't
   share one union.
3. **What the union green does *not* license.** Not merging a **red** member, not an `--admin` / force-merge
   past the gate, not an undocumented "just merge anyway." A red member is still red; only the
   *base-green-between-merges* wait is discharged, since the union already proved the combined tree.

Name this the **red-base discharge** and put one of the two vehicles on record; an oral-only exception ("we
just merged past it that once") is itself the finding. A red base is the release pipeline's blocked state, so
`release-engineering.md` cross-links here — but the discharge *mechanism* is the merge train, so it lives here
and that file never restates it.

### A union / merge-train gate that HANGS or is BROKEN in-env (not fails) silently stalls the pipeline

A train's aggregate gate can **hang** — a wedged runner, a deadlocked build, a lost webhook — rather than
fail, and a coordinator waiting on it stops merging everything queued behind it, with no red status to react
to. **Detect it by liveness, not elapsed time alone.** During the gate **run** the base head is stationary *by
design* (nothing lands until the gate concludes), so the live signal is the **gate job's own output** — no new
log output past ~2× its normal window is a hang (the *long `in_progress` shard* rule below, applied to the
conductor); cancel and root-cause, don't passively wait. During the merge **drain** (members landing
back-to-back), a **base head that stops advancing** past ~2× the per-member cadence is the hang signal there.
Emit progress (members landed / remaining) so a stall is visible instead of reading as healthy idle.

A hung heavy gate is a **can't-check (`UNVERIFIED`), not a pass** — it never authorizes the merge. But don't
block the queue forever: **timebox** it and fall back to the **deterministic runnable subset** (lint / unit /
type-check) as a **proof-of-record** for what *can* be checked, escalating the heavy gate's absence — that
subset is a degraded record, **not** the union's combined-build proof, so it doesn't license merging a member
the union never validated. Keep flaky / heavy browser / visual gates in **per-change pre-merge checks**, not
as a blocking term of the batch union, so one wedged heavy gate can't stall the whole train.

A heavy gate **broken in this environment** — its own harness crashes, a dependency it needs is down — is the
**crash cousin** of the hang above, and likewise a **can't-check, not a red**: "could not check" is not "found
a problem" (the gate discipline in `product-ux-quality.md`). It must **fail-open for the batch proof** — drop
that one broken term and run the deterministic runnable subset — so batching **continues** rather than
collapsing the whole train to serial merging; one broken tool must not halt all batching. Hang and crash
differ in the **response** and in **what evidence survives**: a hang is **timeboxed then escalated** (validity
genuinely unknown, the gate may still be running) and leaves *no* completed union run; a crash is
**definitively broken here and safe to route around now** and leaves the run's **other** terms genuinely
complete. Both keep the flaky / heavy gate out of the blocking union term, and both hold the **same floor at
the grain each leaves intact**: a hang validated nobody, so nobody merges on the reduced record (the floor
above); a crash validated everyone *except* a member whose essential check **was** the crashed term, so only
those members are held back. Fail-open means the tool's *own crash* is not a red — **never** that an
unvalidated member merges. **Treat a throughput-gating tool as P0:** a broken gate that fails one PR is a
normal bug, but one sitting in the batch-proof path throttles *every* merge — its blast radius is the whole
delivery rate, so it jumps the queue ahead of a gate that only affects one change's correctness.

### A required check must be *satisfiable* — pending forever blocks merge like a red

A branch-protection **required check** gates merges only if some job actually reports a conclusion for *this*
PR. When the required *name* isn't backed by a job that runs and concludes here, the check sits **pending
forever** — indistinguishable from a hang, and merge-blocked exactly as a failure is (its enforcing surface
never saw this PR — `SKILL.md` principle 2). Two ways it happens:

- **A required check with *no status* blocks merge — but distinguish "never ran" from "ran and reported
  skipped."** When `on: pull_request: paths:` filters a whole **workflow** out for an out-of-scope PR (only
  `units/**` changed, so the required `app-browser` workflow never triggers), the check gets **no run at
  all**; the enforcer reads "no status" as not-green and the PR is unmergeable without an override. Fix: give
  the required workflow a **pass-through job** that always triggers and exits 0 on out-of-scope paths (so it
  reports a conclusive Success), or don't name a legitimately-absent workflow in the required list.
  **Contrast** a **job** skipped by a job-level `if:` inside a workflow that *did* run — the forge reports it
  **skipped/Success**, which satisfies the required check and needs no pass-through. The trap is the **missing
  status**, not the skip itself. The pass-through **cuts both ways**: legitimate only when **nothing was in
  scope** (a path filter genuinely excluded this diff); a **false-green hole** when there **is** something to
  check and the *event* — not the paths — routed around the real checker: a required workflow whose real job
  runs on `push` / `synchronize` but whose pass-through also fires on an `edited` (title/body) event reports a
  conclusive **Success** for a PR whose code the checker never re-ran. Make the pass-through reachable
  **only** on the paths/events where the real check is genuinely N/A — never an unconditional `exit 0` that
  green-lights an event the real job ignores. A **locally-added merge preflight** can invert this: when the
  forge itself reports a job **skipped/Success** — a job-level cost-gate `if:` an agent can't flip without an
  owner-only label or a manual dispatch — a preflight that **refuses** that green verdict is *stricter than
  the required check it stands in for* and **deadlocks** anyone without the owner lever (the gate-vs-standard
  rule — a gate must never be stricter than the standard it enforces, `product-ux-quality.md` /
  `frontend-a11y.md` — applied to CI). Such a preflight must **diagnose why** a check is absent —
  *policy-declined* (cost gate: work exists, a human must grant the run) vs *nothing-to-run* (path filter: no
  in-scope change) — and **name the owner action**, not refuse blindly; conflating the two reports a false
  block and pushes the agent toward the very label it's barred from adding.
- **Trigger-event gap.** A required job whose workflow omits the event that fires the PR never starts *for
  this PR*: a `full-ci` job with no `labeled` trigger, in a label-driven flow, never begins; a
  `workflow_dispatch` run carries its own `run_id` and never attaches to the PR's check rollup, so the
  preflight never sees it. The workflow **existing** isn't the check **running** — verify the required name
  maps to a job whose triggers include how this PR is actually checked.
- **A required check that never runs on a PR — read the `on:` block FIRST, and name the right trigger key.** A
  PR's required check reports on the **PR head**, so the run that satisfies it is a
  **`pull_request`-triggered** run — filtered by **`on.pull_request.branches`, which matches the PR's *base*
  (target) branch**. So when PRs *targeting* a long-lived integration branch show the check as **no-run /
  Pending** (the #262 *no-status* case that blocks merge — not the *skipped/Success* case that satisfies it),
  the load-bearing key is the `pull_request` **base** filter: is the target branch in
  `on.pull_request.branches`? Absent = **structural** (the check can never report on those PRs), not a flake.
  A **distinct** concern in the same `on:` block: `on.push.branches` must list the integration branch to stamp
  *its own HEAD* green via a push run **after merge** — that HEAD-provability point does **not** unblock the
  open PRs. Diagnose in order: (1) target branch in `on.pull_request.branches`? — this unblocks the PRs; (2) a
  job-level cost-gate `if:` (label/dispatch, above); (3) a path filter (diff out of scope — OK); (4) *only
  then* rerun / flake / timeout — and separately, is the branch in `on.push.branches` so its HEAD is provable?
  Reading the `on:` block beats N PR-level reruns chasing the wrong key.
- **Stale-base fails the whole queue at once.** A gate diffing the PR head against **`origin/main`** (not the
  PR *base*) turns one additive commit on `main` — a new row, fixture, or schema entry the integration branch
  hasn't pulled — into a simultaneous failure of **every** PR queued against that branch, with no regression
  in any of them. When N PRs fail the *same* gate at once, check `git log HEAD..origin/main --oneline` for a
  stale base **before** triaging them individually; one `git merge origin/main` on the integration branch
  clears them all. Sync the integration branch on **each** additive `main` merge, not only before the final
  train; a new gate baselined on `origin/main` must **document that assumption** (prefer the PR base for a
  long-lived-branch workflow).
- **A change-detection gate's hardcoded base is the scope-selection sibling of stale-base — loud when the
  branch outruns the stale ref, silently skipped when that ref won't resolve.** The bug above corrupts a
  gate's *verdict*; the same mistake in a **change-detection** step — a path filter / "did `app/` change?" /
  "did any migration touch?" check deciding whether a downstream job **runs at all** — corrupts its *scope
  decision* instead. Anti-pattern: a diff pinned to a **hardcoded release-branch constant**
  (`git diff origin/release-v2...HEAD -- app/`) instead of the branch's actual base — its configured upstream
  `@{u}`, the PR's declared target (`github.event.pull_request.base.ref` in CI), or a computed merge-base
  (`git diff "$(git merge-base <base> HEAD)" HEAD`, i.e. `<base>...HEAD`) (the pinned *ref* is the defect;
  merge-base diff semantics are the right choice for a scope check, not the problem). A hardcoded constant
  fails **two** ways. **Loud:** once the branch runs **ahead** of the stale cut, the diff span balloons to the
  branch's whole history since the cut, so the filter reports every gated path touched on **every** push (a
  "changed" verdict that no longer reflects this push — noise and wasted CI, not a correctness bug by itself).
  **Silent (the dangerous one):** a literal ref is a **resolvability** hazard the computed forms mostly avoid
  — in a shallow / partial CI checkout (`fetch-depth: 1`, `origin/release-v2` never fetched)
  `git diff origin/release-v2...HEAD` **errors** (`fatal: bad revision`), and a naive
  `… | grep -q '^db/migrations/'` reads the empty/failed output as **no match**, so the job **skips** a real
  change with nothing turning red. (The positional "branch is *behind* the ref" case does **not** empty the
  diff — three-dot / merge-base semantics correctly report the branch's downstream commits; the silent skip
  comes from the ref failing to *resolve*, not the branch's position.) Fix: derive the base at run time (never
  a literal branch/tag name), **ensure that base ref is actually present in the checkout** (fetch it /
  adequate depth), **fail closed** — a change-detection diff that errors or can't resolve its base must run
  the job (or fail the run), never silently skip — and **have the gate name the base it diffed against** (and
  whether the diff resolved) in its output, so a bare true/false can't hide a wrong-base or unresolved-ref
  result behind a correct-looking "nothing in scope." Distinct from the PR-*targeting* wrong-base rule (below)
  and a pre-push hook's hardcoded range (below — fixed via stdin-derived pushed refs, since a hook has no
  upstream to read); three mechanisms, one root cause: a constant standing in for a computed base.
- **A long `in_progress` shard is diagnosed by its log, not by waiting or re-running.** Past ~2× a shard's
  normal duration, **read that shard's log before acting**: a **hang** (no new output for minutes — a
  deadlocked browser, a port that never opened) is cancelled and root-caused before any rerun; a **timeout**
  (the log shows a test hitting its limit) is left to fail cleanly, then the specific test is triaged. Rerun
  **at most once, only after** diagnosis — a rerun with no known cause is spend with no expected change, and
  parallel reruns (*rerun-storm*) multiply runner cost for zero new signal; treating an hour-long
  `in_progress` as normal (*passive wait*) is the mirror error. Cancel with a note naming the evidence (last
  log line, elapsed time) so the next reader knows it was a hang, not a flake or a stale push.

- **The branch-protection required-check *name* list and the workflow’s job names are two enumerations that
  drift.** Distinct from the trigger-config case above (a check that never fires for a PR): here a job is
  **renamed or retired** in the workflow while branch protection still *requires* the **old** status-check
  name — the old name now has no producer, reports no status forever, and blocks **every** PR (and the mirror:
  a check dropped from the workflow but left required). It reads as "a required check never ran," but the
  cause is a stale hardcoded name, not a trigger gap. Keep the two sets **in sync**: derive the required-check
  list from the workflow definition, or add a test asserting
  `{required-check names} ⊆ {job names the workflow can emit}` so a rename fails CI **loudly** instead of
  silently wedging the queue (the **Lockstep surfaces** discipline, `domain-h.md` — file sets that
  must change together). A retired check name often has **more than one consumer** — branch protection, a
  local merge-preflight script, a merge-queue config — so when a gate moves or is renamed, audit **every**
  consumer, not just the one that surfaced the block.

Read the check's **conclusion**, never the bare colour; a required check with no run for this PR is a **High**
merge-blocker in its own right — name it a config gap (unsatisfiable as wired), not a flake to wait out.

### A new PR-body / artifact gate is a contract with its producers — co-evolve them, or every automated PR silently fails it

Adding a gate that requires a convention in the PR **body** or a committed **artifact** — a `Verify:` line, a
changelog fragment, an evidence image, a commit trailer — silently fails **every producer that doesn't yet
emit it**. Sequencing the gate last in one landing batch (§5, *merge trains*) handles the PRs already *in
flight*; it does nothing for **standing** producers — the PR template, Dependabot / Renovate, a
release-drafter bot, an agent delivery swarm — which keep emitting the old shape on **every future run** until
their **definition** is updated. A human author adapts on their next PR; automation can't, and piles up
green-but-refused PRs until someone notices.

- **Co-evolve the gate and its producers in one change.** Landing a body / artifact gate means updating the PR
  template, the bot/agent prompts, and any PR-generating scaffolding **together** — the gate and every client
  of its contract move as one commit.
- **Grandfather or ramp.** A warn-only period — or a *future* cutover date *T* — buys time while producers
  catch up. A past-dated grandfather exempts only the in-flight backlog: a standing producer's next run is
  always after *T*, so it strands anyway.
- **Make the failure name the exact fix** — the literal line or field to add — so any producer, human or
  agent, can self-correct from the failure text alone.
- **Inventory the producers before adding the gate.** The template, Dependabot / Renovate, release bots, and
  agent swarms are each a **client** of the new convention; the one you don't list is the one that strands.

A gate is a contract with its producers: change the contract without moving them and you break them silently —
and an **automated** producer can't "just adapt" the way a human reviewer does. **In review**, a diff that
adds or tightens a PR-body / commit-trailer / committed-artifact requirement is incomplete unless the same
change updates that artifact's producers (or ramps the gate) — the standing-producer generalization of the
merge-train ordering rule (§5). The message-payload sibling — a new **required field** breaking old producers
and in-flight messages — is `api-contracts.md`.

### The merge gate verifies WHERE a PR merges, not only that it is green — check the base branch

A PR-open command run without an explicit base falls back to whatever the tool picks — for `gh pr create`, a
per-branch `gh-merge-base` git config if set, otherwise the **repo default branch** (the common case for a
lane that never configured that). When the intended integration branch is *not* the default (work lands on
`development`, but `main` is the protected / owner-gated default), a lane whose brief says "base
`development`" in prose but runs `gh pr create` / the API call **without the base flag** silently opens
against the protected branch — and a merge step verifying checks-green + mergeable but **not the base** then
merges it into the protected branch, a governance breach even when the code is green.

- **Every PR-open passes the base explicitly** (`--base <integration-branch>`); never rely on the command's
  default-to-repo-default behavior.
- **Base-branch identity is a merge-eligibility axis**, next to state / mergeable / checks-green: the gate
  reads the PR's *actual* base and **refuses** anything whose base isn't the expected integration branch — a
  green PR against the wrong branch is not mergeable.
- **Recovery when a PR already merged to the protected branch**: do **not** auto-revert the protected branch
  (itself a gated, owner-level change) — surface it for an owner decision, and separately port the change onto
  the integration branch so the two don't diverge.

### Self-reported evidence is not a trusted control; a local hook is advisory

A merge decision rests on **trusted** evidence — a run the forge verified on the **exact commit under review**
(a required check must actually report a conclusion for this PR, above; that conclusion names the SHA it
graded, `method.md`). Anything an author can produce or skip locally is **advisory**, never a passing control:

- **Self-report ≠ control.** A local hook (pre-commit / pre-push), a `Tests: N/N` line in a commit or PR body,
  and a checked PR-template box are all self-reported: `git commit` / `git push --no-verify` bypasses the hook
  with no trace in the result, and the text is typed, not executed. "The repo has hooks" or "the PR says tests
  pass" is **never** logged as a green control — record only a forge run pinned to the reviewed SHA (a
  required status that never ran is the merge-blocker above, not "the author ran it locally").
- **A conflict-free `git merge` never invokes `pre-commit` at all — this is not a bypass, it's a missing hook,
  verified against git's own behavior (a clean merge completes despite a `pre-commit` hook set to always
  fail).** Git's internal merge-commit codepath for a **clean** (non-conflicting) merge runs `commit-msg` but
  not `pre-commit`; only a project-installed **`pre-merge-commit`** hook fires there. A repo that wires
  `pre-commit` as its quality gate but never adds `pre-merge-commit` ships every merge-forward,
  sync-from-main, or integration-branch merge **ungated** — no `--no-verify`, no drift, no worktree
  misconfiguration required; the hook the repo relies on was simply never wired to that codepath (distinct
  from both the bypass and the drift bullets above and below — nothing was skipped or stale, the codepath
  never called it). **Compounds** with a custom merge driver that resolves a generated/compiled-file conflict
  by taking one side outright (the merge-driver mechanics are in §6 below, not restated here): a clean
  auto-merge can silently leave that generated file **stale** (missing the other side's regenerated
  contribution), and with no `pre-merge-commit` hook, nothing re-checks freshness before the merge commit
  lands. **Detect:** `git config --get-regexp '^merge\.'` for a take-one-side driver on a generated path, and
  confirm whether `pre-merge-commit` exists alongside `pre-commit` (`.git/hooks/` or the configured
  `core.hooksPath`). **Fix:** add a `pre-merge-commit` hook mirroring `pre-commit` — at minimum the cheap
  regenerate/freshness check for any generated artifact — and a test asserting a zero-conflict merge is
  actually gated; re-generate and diff generated files after any merge even when git reports no conflict.
- **A *drifted local copy* of a CI gate is a false green even when the author ran it in good faith.** The rule
  above covers a local check *skipped or bypassed*; the subtler case is one that **ran and passed and still
  means nothing** — the same gate lives as both a CI job and a local convenience copy (a `pre-push` script, a
  `make verify` / `scripts/check.sh` target, a vendored paste of the CI logic), and the local copy **drifts
  behind** the CI definition. It reports green on a change CI will reject; the author reasonably says "it
  passed locally" and reads the red CI as a flake — grounds for an `--admin` override that then merges what CI
  would have caught. Fix: **single-source the gate logic** — the local entry point **invokes the exact script
  the CI job runs** (one file, two callers), or a version/digest check **refuses to pass locally when the two
  diverge** — so a local pass can never mean *less* than a CI pass. This is the gate-logic case of *audit
  every consumer when a gate moves* above (a local merge-preflight is one such consumer) and of domain H's
  duplicate-source-drift (one source, not two copies that fall out of step); the trusted control stays the
  forge run pinned to the reviewed SHA. (The sibling **design** question — an evidence gate must require a
  source that *renders for the reviewer*, an uploaded attachment, not a raw-content-host link that only
  *looks* like evidence — is `product-ux-quality.md`'s "gate on visibility, not presence.")
- **The *absence* of a hold marker is not authorization — a mutable-text hold can be edited away.** The mirror
  of the rule above: where a merge is blocked by a "DO NOT MERGE" / hold marker in a **mutable** surface (a
  PR-body line, a checklist box, a label a bot can toggle), its **disappearance** is self-reported too —
  anyone, or an automated body-edit, can clear it with no approving review and no trace. A preflight that
  reads "no hold marker present → clear to merge" is fooled by deletion-by-edit. Back a hold **out of band**
  (a branch-protection rule, a required review, a status check the author can't toggle), never mutable body
  text alone; make body-editing automation **append/insert-only** with a before/after diff; and treat a
  hold-marker *disappearance with no corresponding approving review* as **STILL HELD** (fail closed).
- **Hooks under a worktree gate the wrong thing.** In a linked worktree (the multi-lane setup this file's red
  flags cover), a hook wired for the primary checkout misfires: an **absolute `core.hooksPath`** is shared by
  every worktree, so a hook authored for the primary checkout also fires in every sibling — one resolving
  paths from a hardcoded location rather than the invocation then examines the wrong tree; and a pre-push hook
  diffing a **hardcoded default branch** gates the wrong range. A pre-push hook's real range is the pushed
  refs it receives on **stdin** (`<local-ref> <local-sha> <remote-ref> <remote-sha>`) — derive scope from the
  event, not a constant, and don't bake an absolute hooks path a sibling worktree will inherit. A hook that
  silently gates the wrong files is worse than none: it reports green over unexamined changes — another reason
  the hook tier is advisory and the forge run is the trusted gate.
- **A git-tracked file the build regenerates poisons a clean-tree gate run in the same working tree.** If a
  build step rewrites a **committed, tracked** file (a generated bundle, a `dist/` artifact, a lockfile a
  postinstall touches), any gate asserting a clean working tree — a merge preflight, a pre-commit/pre-push
  hook, `git diff --exit-code` in CI — goes **red on a dirty tree the build itself created**, not a real
  defect, so running the build to satisfy one gate breaks the next. Fix at the source: **don't track a build
  output** (gitignore it, generate at build time), or if it must be tracked, regenerate deterministically and
  commit it as its own step, and scope the clean-tree check to **exclude the generated path**, or run the
  clean-tree check in a **fresh checkout the build never ran in** (the merge-train's throwaway integration
  branch, above, does exactly this) — never "run the build, then assert the tree is clean" in the same working
  tree. (Distinct from the run-twice idempotency check, about an *untracked* generated artifact polluting a
  later step across runs; this is a *git-tracked* artifact whose committed baseline the build invalidates on
  every run.)

### A worktree-relative hook runs its base's copy — land the safe hook everywhere first

Resolving hooks relative to the invoking worktree (the fix above) has a second-order failure: each worktree
then runs the hook **as checked out at its own base**. A worktree cut from an old commit or a long-lived
feature base runs *that base's* hook — not the one the team now intends — so if an older hook is slow, prompts
interactively, or hangs on a step the environment no longer satisfies, every lane off that base inherits the
breakage, misattributes it to "flaky / slow tooling," and bypasses the whole tier (worse than no tier —
everyone still believes it runs).
- **Hook content is fail-safe by default.** The committed hook runs a fast, always-safe core and makes every
  slow, environment-dependent, or interactive step **opt-in** (an env flag or a marker file), so an old copy
  can never hang or block a push on a step the environment can't satisfy. A hook that can hang is a hook that
  will be bypassed.
- **Order matters: land the safe hook on every base people branch from *before* normalizing the path.** Since
  a worktree-relative hook runs the base's copy, the fail-safe hook must already be merged into the default
  branch *and* every long-lived integration / feature base first; normalizing resolution while old bases still
  carry the old hook guarantees stale-hook execution.
- **"Which hook runs here" is base-dependent — verify it.** Confirm the worktree's hook matches the intended
  version; make hook installation idempotently re-assert the current version rather than trusting inheritance.
- **A push-blocking step needs an audited, reason-required escape hatch**, so a genuinely stuck lane is never
  forced into a traceless whole-tier bypass (which disables *every* step, not the one bad step).

### On a stacked PR, attribute a CI failure to the commit that owns it

A PR stacked on another (B's base is A's branch, not the mainline) contains A's commits, so B's own CI runs
them too — and a failure A introduced turns B red without B changing anything. Before diagnosing (or "fixing")
a red on a stacked PR, find which commit the failing step belongs to: `git log <merge-base>..<head>` is the
PR's **own** diff, and a failing step in an **ancestor** commit from the base branch is the **base PR's**
defect, not this one's. (Knowing which *run* the red is even for is the companion rule — a run's conclusion
names the SHA it graded, `method.md`.) Attribute it to the base PR and let it fix there; **never commit the
fix onto the downstream PR** — once the base merges, the same fix lands twice: a double-patch or a conflict. A
stacked PR is only truly green once its base has merged and it's been re-run on the mainline.

### A stop halts new work — a MERGEABLE PR and an unpushed rebase are not "new work"

`STOP` / interrupt means **no new lanes, no new commits, no new scope**. It does **not** pause landing a PR
already green and `MERGEABLE` against its intended base, and doesn't license leaving committed work stranded
off the remote. Two things must be true before a stop is actually complete:

- **The MERGEABLE set is not silently abandoned — but a stop grants no new merge approval.** Enumerate the
  open PRs that are green + `MERGEABLE`; finished work must not vanish because a stop arrived. Merging is a
  shared-state action, so §6's gate still holds: **merge only what already had standing approval** (per its
  preflight — the red-base discharge above governs *how* such a merge lands, not *whether* you may fire it),
  and for everything else the stop-complete step is to **hand it off by URL** to the next owner. A green PR
  left un-merged and handed off is not the loss; an irreversible merge fired *because* a stop arrived —
  approval a stop can't itself grant — is the §6 regression.
- **No unpushed commit is left silent.** An interrupted rebase/amend often leaves the new SHA **local only**;
  a stop taken there can strand it forever (a later push flake then loses it). Push before stopping, or print
  the recovery triple in the stop message — the **absolute worktree path**, the **branch**, and
  `git rev-parse HEAD` — so another lane can retrieve the tree. "Push failed / a flake" is not a completed
  stop: retry the push or hand off the path.
