# Fast agentic delivery: concurrency, scheduling & merge cadence

Read this when: sizing a heavy-lane fan-out on a shared machine (the full
environment-probe procedure and the fan-out tiers live here), choosing between
a merge cascade and a merge train for a queue of already-green PRs, diagnosing
a fleet-wide red that no single diff caused, or reviewing (domain K/S in the
sibling `deep-code-review` skill) whether a target project's own fleet-scale
CI/merge behavior holds up under N-agent load. `SKILL.md` holds the act-on
predicate (free RAM + swap trend), the Conductor's event-driven rhythm and
drift rule, gate-epistemology principles 3 and 6, and the worktree/occupancy
rules; this file holds the procedure, mechanism, and worked examples behind
them, each section opening with a one-line anchor to the rule it expands.

---

## Environment probe procedure (host sizing before fan-out)

`SKILL.md` **Environment probe** states the act-on rule — probe before sizing,
and gate on free RAM and the swap trend. This is the full procedure it points
to.

- **Probe:** free RAM and CPU cores (`memory_pressure`/`vm_stat` or `free -h`;
  `nproc` or `sysctl -n hw.ncpu`), disk (`df -h`), and which tools/connectors
  this session actually has usable auth for. A lane dispatched against a
  connector that needs an auth flow it cannot complete fails at the worst
  point — after it already holds a worktree slot.
- **Decide from the probe, not from habit:** how many HEAVY lanes (a real
  build, browser test, or compute process) this run supports — tighten under
  memory pressure even where a core-count formula would allow more, since a
  machine can exhaust RAM before it exhausts CPU slots; which model tier a lane
  needs (`model-tiering.md` in the `deep-code-review` sibling) — frontier only
  where the blast radius already calls for decorrelation, not by default; and
  whether a heavy gate runs locally at all or waits for CI/a shared runner when
  local capacity is short.
- **Shell semantics belong to the probe, not to guesswork mid-script.** Know
  which shell will actually run a script before writing a list-membership or
  exclusion check in it — `branch-and-merge-hygiene.md` §6 has the concrete
  failure mode and the portable fix; this step only says *check*, not what to
  write.
- A **failure that only appears under heavy fan-out concurrency is contention,
  not a defect, until reproduced at low concurrency** (`parallel-audit.md` §0) —
  probing capacity first is what keeps that distinction from being made after
  the fact, on a report already full of false timeouts.

## Size the fan-out to the decomposition, not to available concurrency

`SKILL.md` states the rule — never more lanes than there are
independently-verifiable objectives, and pilot before full fan-out. The
detail: a lead that hands out vague, overlapping instructions gets duplicated
work, not more coverage — subagents given no clear boundary have been observed
independently re-investigating the same ground (Anthropic, multi-agent research
system). Default tiers: a single fact/lookup needs one lane; a bounded
comparison needs 2-4; only a genuinely decomposable task graph justifies 10+,
and each of those needs its own objective, output format, and explicit boundary
against its siblings — spawning dozens of subagents for a simple query is a
named failure mode, not a hypothetical one. **Pilot before full fan-out:** on a
wide, mechanical batch, run a handful of lanes first, fix what the pilot
exposes, then commit the rest of the width — cheaper than discovering a bad task
boundary after the full width is already running.

## Cap in-flight write lanes by landed artifacts, not lane count or headroom

The decomposition rule above sizes the *total* lanes against objectives; this caps
the *in-flight* write lanes against what has actually **landed**. Its failure is
**hours of real spend with the integration head unchanged** — many concurrent write
lanes spawned and re-prompted, yet only a fraction ever reach the remote. "N lanes
running" is the orchestrator's own activity, not delivery, and it worsens with
concurrency: each write lane pays env-setup + install + boot + (for UI) a browser
gate largely **serial on the machine**, so past a point a new lane delays every lane;
and routing/dedup/reconcile of N lanes consumes the coordinator — the only actor that
integrates.

- **Lane progress is a durable artifact** — a pushed branch, an opened PR, a committed
  diff on the integration branch — **never a running transcript** (the
  transcript-is-not-liveness rule below, applied to delivery rather than health). A
  lane with no artifact has produced nothing, however busy it looks.
- **Report the artifact, not the activity** — the status is "**M landed, K in flight,
  head at `<sha>`**", never "N lanes running."
- **Admission is earned by completion** — hold write lanes to a small WIP limit
  (default low; a WIP limit is an *enabling* constraint, Sources) and don't spawn lane
  N+1 while N are in flight with zero artifacts. Check the delivery ratio (landed ÷
  spawned) each interval; near-zero for a full interval means **stop spawning and
  drain** (finish or kill what's in flight and integrate what exists), never add lanes.

## Gate on free RAM and the swap trend — `load1` is not a reliable signal alone

`SKILL.md`'s environment probe states the act-on predicate — free RAM and the
swap trend primary, CPU idle secondary, `load1` a weak corroborating signal at
most. This section is the mechanism and the worked example behind it.
Linux/macOS load averages count threads in uninterruptible I/O-wait, not only
CPU-runnable ones — "adding the uninterruptible state means that Linux load
averages can increase due to a disk (or NFS) I/O workload, not just CPU
demand," with a worked example where "a heavily disk-bound system might be
extremely
sluggish but only have a TASK_RUNNING [CPU-runnable] average of 0.1" (Gregg;
source below). Observed directly on a 14-core host: `load1` sat at 7
(comfortably under an 18-ish `cores × 1.3` ceiling) while CPU idle read
81% — the elevated `load1` was disk I/O from several concurrent dependency
installs, not CPU contention, so it neither flagged the real problem nor
stayed a trustworthy "all clear." The actual failure was memory: swap grew
from roughly 4 GB to 12 GB, driven by the many headless-browser processes a
full local browser-suite lane boots (CI-offload, below), and lanes died on
their own timeout once swap pressure hit — independent of what `load1` read
at the time, and despite the host reporting a comfortable 86% free RAM
shortly before. **Corrected signal hierarchy:** free RAM and the **swap
trend** (is it climbing, not just its current level) are primary — spawn
while free RAM stays above a working buffer (~15%) and swap is not actively
growing; back off the instant swap starts ballooning, before free RAM alone
would look low. CPU idle is a useful secondary confirmation of real
headroom. **Do not gate on `load1` alone** — at most a weak corroborating
signal, never the deciding term, because it cannot distinguish CPU
contention from disk I/O. Whatever the exact predicate, **spawn one heavy
lane at a time, re-sample after a settle window, then decide on the next** —
never compute a ceiling and dispatch straight up to it, and **leave a burst reserve
even when the predicate says go** — a later spiky lane (a browser gate, a dependency
install, a test runner) must still fit without paging the box into thrash.

**Sharpenings from a later thrash — 84% free RAM while swap sat ~76% consumed and
nothing landed for hours.** The ~15%-free-RAM floor above is a **veto, not a licence**:
free RAM may *corroborate a stop* but must **never authorize a spawn** — it is a
post-mitigation number (paging, cache eviction, and compression have already run), so
under this kind of thrash, where dying lanes release RAM as the machine fails, it can
read healthiest exactly as delivery collapses. The swap trend (sampled twice for
direction, as above) stays the primary gate. Add to the probed predicate **free disk,
worktree count, and live-lane count** — a fan-out sized against memory alone dies of
disk (worktree lifecycle, below). And treat a collapse in observable **work rate** —
lanes not completing, tool calls timing out, nothing landing — as itself the resource
signal, outranking any green metric (distinct from the delivery-ratio drain above:
that asks whether lanes convert to artifacts, this asks whether the machine can still
run them; a nothing-landing stretch trips both).

## A worktree is a resource with a lifecycle — creation without teardown leaks it

Worktree-per-lane is the right isolation, but a worktree is a **resource with a
lifecycle**, and nothing in the fan-out pattern ends it. The failure is **disk
exhaustion that halts every lane at once — including the integration lane that would
have landed the work** — arriving without warning after a per-lane-creates,
nobody-destroys run accumulates hundreds of worktrees and tens of GB. Checkout and
status degrade as the registry grows; stale worktrees masquerade as in-flight work (an
entry in `worktree list` proves only that something *once* ran — cross-check a real
liveness signal, the transcript-is-not-liveness rule below); and worktree-held
branches escape the usual merged-branch cleanup.

- **Teardown is part of the lane contract, stated at spawn** — on success, after the
  artifact is pushed, the lane removes its worktree; on failure/abandonment it removes
  the worktree only after **capturing any uncommitted work** (the non-destructive rule
  below — committed work survives on the branch ref, but truly-uncommitted work is lost
  to `git worktree remove`). A lane that cannot guarantee teardown runs under a
  supervisor that does.
- **The orchestrator owns garbage collection**, because lanes die in ways that skip
  their own cleanup — but GC is **advisory and approval-gated, never an autonomous
  destructive sweep** (the same confirm-before-shared-state bar as any delete). At an
  interval it **proposes** removals with the exact command — registry entries whose
  directory is gone; worktrees whose branch is merged, whose PR is closed, or idle
  past a threshold **and** holding no uncommitted changes — and executes only on
  explicit approval.
- **GC is non-destructive toward uncommitted work** — a candidate holding uncommitted
  changes is refused (or its diff archived and reported first). Reclaiming space must
  never become the mechanism that loses a lane's only copy of its work.
- **Scratch is a probed resource** — free disk and worktree count are ceilings the
  spawn probe enforces (the swap-trend section above); this section keeps that term
  from going red, it does not re-specify how to read it.

## Sweep the whole ready queue on every trigger, not just the triggering item

The Conductor's attention is correctly event-driven, not polled — but a
Conductor that reacts only to the specific thing it is waiting on (one
lane's own completion, say) can sit through several such events while a
**different, already-green, already-mergeable** PR sits idle in the same
queue, simply because nothing about that other PR generated an event. The
fix: whenever the Conductor's attention *is* triggered by any of the four
named events, spend one cheap pass over the **entire** ready queue (a status
check per candidate PR) before returning to waiting — not only the item that
triggered the check. This is a completeness fix to what a checkpoint covers,
not a change to the event-driven model itself.

## A third gate-epistemology case: a correct, external, fleet-wide finding

Principle 3 separates *the check could not run* (`UNVERIFIED` — never a pass, and
a *required* missing check still blocks its gated action)
from *a real defect the diff introduced* (fail closed). A newly-published,
correctly-detected dependency-vulnerability advisory is neither: the gate is
right, the finding is real, and it is shared across every open change **and
the mainline itself**, with no relationship to any one diff. One observed
instance: a real advisory reddened the mainline and every open PR in a queue
at once with zero code change from any of them; the fix that actually
unblocked the fleet was **one coordinated dependency-lockfile bump**, landed
as a fix-forward, after which the rest of the queue needed to resync against
the new mainline rather than each independently rediscover the same fix.
Name this case explicitly — it saves the diagnosis time of treating a
fleet-wide, external-cause red as N unrelated regressions. It is a
**diagnosis shortcut, not a new merge authority**: it does not license
merging onto a red mainline beyond whatever narrow, human-approved
change-control path a project already has for exactly this case (one
reviewed, unblocking fix).

## An independent-PR-queue cascade is a cadence choice, not a new authority

Gate epistemology principle 6 requires union proof before a merge train —
not restated here. A related but distinct situation: a **queue of PRs that
are each already independently green**, with no known interaction between
them (typically right after the single common blocker above is fixed and the
whole queue needs to resync). Landing that queue does not need a new,
lighter-weight merge authority — it needs **cadence**: run the project's own
merge-authority check against every queued PR on a short interval, rather
than merging one PR and waiting for the mainline's full CI resolution before
even looking at the next. **The one thing this must not become:** a second,
separate pre-check (e.g., asking the forge "is this mergeable?" through a
different call than the authoritative merge gate itself) that races the
platform's own status — mature merge tooling names this exact anti-pattern
from a past incident and refuses it by design, calling only the one
authoritative gate, every attempt, never pre-checking through a second path.
A cascade is **weaker evidence than a union-proven train**: a train proves
the *combination* is sound before any member merges; a cascade only proves
each member was independently green and re-confirms that at each step.
Defensible specifically right after a single common blocker clears and every
queued PR was already independently green — not a general substitute for a
train when queued PRs might still conflict with each other.

## CI-offload the heavy gate by default — lane weight, not lane count, drives memory cost

A lane that runs a project's full local aggregate gate — a real build plus
the complete browser/E2E suite plus any slow lint/audit step — boots many
headless-browser processes per run and is the dominant memory cost on a
shared machine, not merely "one more lane." A lane running only the fast
tier (lint, unit, type-check, at most one targeted spec relevant to the
diff) costs a small fraction of that. With several full-gate lanes running
at once, the machine's memory gets consumed even when each lane's own
resource check passed at spawn time, because the check ran before the
browser-heavy phase started, not during it. Default a lane's own local
verification to the fast tier, and let CI's own — ideally
already-parallelized — jobs carry the full matrix. This sharpens "verify on
CI, treat a local run as the pre-check, never the evidence": defaulting
every lane to the light tier is the actual concurrency unlock — it is what
lets several lanes run inside the RAM budget one full-gate lane alone would
otherwise consume — not a smarter resource-gate formula (previous section).

## Draft-gated heavy checks hide a UI-regression wave — run them somewhere while the draft is open

The section above offloads the heavy gate to CI — but CI commonly runs those
expensive jobs (headless-browser, a11y, visual/hydration, UX audit) only on
ready-for-review or a label, with drafts running the fast tier alone. When a large
change lives as a long-lived **draft** across many sub-lanes, every lane reads
fast-tier-green (lint / unit / type-check) while a whole class of **browser-only**
defects — responsive breakage, focus-visible / keyboard, truncation without an
accessible name, SSR hydration mismatches — accumulates unobserved. Flipping to ready
then surfaces the whole wave at once, late, as a regression. Fast-tier-green is **not
UI-correct**; no unit/typecheck gate observes those signals. Two fixes: (a) run the
heavy/browser gates on the **integration branch periodically** while the draft is
open, or (b) explicitly **budget for a late regression wave** and never present a
stack of fast-tier-green lanes as demo-ready. Browser-only signals are the
**coordinator's** to verify centrally on the rendered page, not delegated to lanes
whose own gates cannot observe them.

## A worktree's own gate can fire on a file it does not own

A definitions- or content-only change can rebuild a generated artifact that
is *mirrored* into a directory owned by a different toolchain (for example, a
compiled data file synced into an application directory whose own
pre-commit gate fires on any staged path under it). In a **fresh** isolated
worktree — before that toolchain's own install step has run — the mirrored
file alone can trip that gate and fail closed, even though the change never
touched that toolchain's code. Two portable fixes, either sufficient: (a)
provision the *whole* worktree's toolchain (run every subtree's own install
step) before the first commit, even when the change looks confined to one
subtree; or (b) scope a definitions/content-only lane to skip staging the
generated mirror at all, letting a downstream build step regenerate it. This
is a **provisioning gap, not a defect in either gate** — each gate does
exactly what it is supposed to; the worktree was simply not fully set up for
the one it tripped.

## Out-of-tree shared scratch crosses commit metadata — worktree-per-lane doesn't cover it

Concurrent write-lanes that each generate per-lane content — a commit-message file, a
plan/notes file — and write it to the **same hardcoded path in a shared temp/scratch
directory** collide: lane B overwrites lane A's file before lane A consumes it, so
lane A commits with **B's message** (`git commit -F <shared-path>`) or attaches the
wrong note. Each branch's **code diff is correct**; only the **metadata** is crossed —
and metadata crossing is **invisible to a diff-scoped review**, which reads the tree,
not the message the tree ships under. The usual mitigations miss it: a git **worktree
per lane** isolates the branch, index, and deps, but a scratch path in a shared temp
dir is **not part of any worktree**, and the collision travels through
`git commit -F <path>`, so "stage explicit paths, never `git add -A`" doesn't reach it
either.

- **Give every lane a unique scratch path** (suffix by lane id / worktree / PID), or
  keep per-lane content **inside the lane's own worktree**.
- **Verify metadata ownership, not just the diff** — before finalizing a lane, confirm
  the committed message/note belongs to *that* lane.
- **🚩 grep:** `git commit -F <path>` / `--file=<path>` where `<path>` is **fixed
  across lanes** (no lane-unique component), or multiple lanes referencing one
  hardcoded scratch/temp path for per-lane content.

Same root cause as `deep-code-review`'s `concurrency-shared-state.md` (two writers, one
path) but where its mitigations don't reach: **out-of-tree** scratch, and the
corrupted thing is **commit metadata** a diff review never sees.

## A worktree assignment is a path, not an adjective — an integrator on a shared branch detaches

Brief N lanes with *"work in an isolated worktree off `<branch>`"* and the phrase splits
two ways: one lane creates a fresh worktree, another reads it as *the* worktree where
`<branch>` is already checked out and writes straight into that tree. They never collide
on a file — their file sets are disjoint — they collide on the **tree**. The occupied
tree then carries a second lane's *uncommitted* work, and the first lane's own gate trips
on it: a fully verified merge is blocked by a foreign half-written test file it must not
touch. A git-diff review sees nothing — the foreign edits are unstaged, so the committing
lane's own diff is clean; the failure surfaces only as a confusing unrelated test
failure. And "just make your own worktree" fails for exactly the lane that most needs
one: `git worktree add <path> <branch>` **refuses a branch already checked out
elsewhere** (`fatal: '<branch>' is already used by worktree at …`), which is precisely
the integrator's situation.

The topology is fixed: N lanes plus one integrator all want a checkout of the *same*
integration branch — N+1 agents, one branch. State it explicitly, one line per brief:

- **Name the exact path; "isolated" is not an instruction.** The brief gives the path
  the lane creates (`<scratch>/wt-<lane>`), and the lane writes **only** under it. "An
  isolated worktree off X" is a hope; a path is an assignment.
- **The integrator folds in on a *detached* worktree.** `git worktree add --detach
  <path> <branch>` — detach at the **local** `<branch>` tip, not `origin/<branch>`:
  detaching does not occupy the ref, so it succeeds even though the branch is checked out
  elsewhere, and it lands on the verified local tip; `origin/<branch>` bases off the
  **stale** remote tip (dropping the merge you just verified) and does not exist at all
  for a local-only integration branch. Then merge the finished lane, verify, publish, and
  remove the worktree. A detached checkout is immune to the same-branch refusal above and
  cannot be squatted by a lane that believes it owns `<branch>`'s tree. How the result is
  *published* is a separate choice — a direct `git push origin HEAD:<branch>` from the
  detached tree, or a PR from the merged result — under whatever publish gate the project
  already applies (a push to a shared branch is itself an owner-approved action); the
  detach is what makes the *integration step* itself collision-proof either way.
- **Verify tree ownership before the first write.** `git status --short` in the target
  tree: if it shows changes the lane did not make, the tree is **occupied** — stop and
  report, do not write into it. Foreign dirt is an occupancy signal, not noise.
- **A gate failing on a file the lane never touched is the environment, not the code.**
  This is the collision twin of *a worktree's own gate can fire on a file it does not
  own* above: there the unowned file is a mirrored artifact, here it is another lane's
  uncommitted WIP — either way, re-run the gate in a clean or detached tree to tell an
  environment fault from a code fault before chasing a bug that does not exist.
- **Never resolve it by stashing.** `git stash` on another lane's uncommitted work
  removes it from that lane's tree silently and is unrecoverable from the lane's point of
  view — a data-loss fix for a coordination bug. Reassign the path instead.

## Delegate visual / parity work by measured number, not adjective

A qualitative brief for visual/parity work handed to sub-agents ("make this match
that") does not converge: each lane guesses at values and returns output that needs
repeated re-fixing — the same eye-tuning oscillation a single reviewer would have had,
now distributed across lanes. Convert the acceptance criterion to **measured numbers
up front** — the reference's rendered device-pixels, the scale ratio between the two
renderers, the exact target per property (cross-ref `deep-code-review`'s
`product-ux-quality.md`, "match by measured device-pixels, not user-space units").
Hand the lane those numbers plus the instruction to **match by measurement, not tune
by eye**; the lane derives values deterministically and returns a measurement table.
The coordinator confirms that table against the reference's rendered output — never a
lane's self-assessed "matches now." If you cannot state the number, the orientation
step is to **measure it**, not to delegate "make it look right."

## Run verification in the foreground — a backgrounded gate loses its verdict

A sub-agent told to run the gate suite that launches the long command **in the
background** and then ends its turn "waiting for it to finish" loses the result: a
sub-agent's own background task does not reliably notify the **parent** once the
sub-agent has exited, and the turn ended before the run completed — the verdict
lands in a buffer nobody reads. Run gate/verification commands in the **foreground
(blocking)** so the result is in the agent's own report, or redirect output to a
file the parent **explicitly reads after** the process ends. Never end a turn
waiting on a background task whose completion notifies only the exited turn. A
machine-readable last-run status file (some runners write one) lets the parent read
the verdict without re-running.

## Confirm a subagent is idle before dispatching a duplicate — a "completed" is not proof of terminal completion

The watcher-side complement to the foreground rule above. A coordinator that
dispatches lanes off task-"completed" notifications can be told a subagent finished
**while it is still running**. The mechanism is concrete, not mysterious: on a harness
that fires "completed" **each time an agent stops with no live background children of
its own** — and can notify the **same task-id more than once** — a subagent that has
armed a background **monitor/watch** cycles stop→wake and emits "completed" on **each**
stop, none of them terminal until the agent truly exits. A single "completed" is
therefore **one of several**, not proof the work is done. **The tell:** a
repeated/duplicate "completed" for the **same task-id**, or the agent's own last report
still saying "waiting." The **defensive invariant**: before dispatching a duplicate
lane for the "remaining" work, **confirm the agent is actually idle** — check its live
state and those tells, not merely that a "completed" arrived — especially when the
duplicate would write into the **same worktree**, where a collision corrupts the run.
This is the dispatcher mirror of "a backgrounded gate loses its verdict": there the
*doer* drops a result; here the *watcher* acts on a not-yet-final one.

## A transcript's size or mtime is not a liveness signal — never kill a lane on staleness

The **inverse** error to the section above, with a worse blast radius. Judging whether a
background subagent is alive, stalled, or dead from the **`stat` of its transcript/output
file** (bytes unchanged for N seconds, mtime older than a threshold) reads a signal that is
not there: a transcript can lag the working agent by **many minutes** — a long tool call, a
quiet reasoning stretch, buffered/flushed-late output — and can look equally "recent" for an
agent that has already exited. Acting on the stat cuts both ways — it **kills a still-working
lane** (destructive: its in-flight work and worktree state are gone) or **trusts a dead one**
and waits forever / dispatches onto a corpse. Judge liveness from the agent's **actual
product**: a fresh work-tree diff or new commit, a live child process, an owned port/PID, or
a direct **ping it answers** — never from the transcript file's size or age. Killing a lane
is a **destructive, shared-state action** (principle 9 — closing or deleting shared state
needs evidence, not presumption): confirm the agent is genuinely idle by a *positive* signal
before terminating. If nothing but the transcript is observable, the
honest state is **`UNVERIFIED`**, not "dead." Distinct from the Conductor's context-isolation
rule ("read status, not the raw transcript" — do not consume the transcript as *context*):
this is not reading its **file stat** as *liveness*. And distinct from the idle-before-
duplicate section above: that is a false-**positive** "completed" leading to a duplicate
dispatch; this is a false-**negative** liveness read leading to a destructive **kill**.

## Release verification runs on a frozen, quiescent head — a discovery pass runs during integration

The heavy verification run (full browser suite + production build + audit) is the
longest-lived task in a fan-out, which makes it the most exposed to two things at once:
the integration branch **moving underneath it** as feature lanes fold in, and **resource
starvation** from those same lanes. Dispatched *alongside* active integration it maximises
both — and a verdict about head `A` delivered when the head is `A+9` describes a tree that
no longer exists. It is not wrong, it is *about something else*, and it is **worse than no
verdict** because it reads as reassurance and gets quoted downstream as "we verified it."

Two activities run the same commands but are different contracts — do not conflate them:

| | Defect discovery | Release verification |
|---|---|---|
| Purpose | find problems early | certify a specific tree |
| Target | any recent head | one **frozen** head |
| Timing | continuously, during integration | once, after integration **closes** |
| A stale result is | still useful as leads (re-confirm at the new head) | worthless (it certifies nothing) |
| Resource priority | yields to feature lanes | gets the machine to itself |

- **Gate release verification on quiescence.** Do not dispatch it while the integration
  branch is still accepting folds; gate it on the integrator reporting **no outstanding
  branches**. Run *discovery* passes during integration instead, and label their output
  **discovery, not certification**.
- **Freeze and name the head.** The lane records the SHA at start and re-checks it at
  finish; if the head moved, the verdict is **`STALE — tested <sha>, head is now <sha>`**,
  never a bare pass/fail (a verdict without its sha fails closed — `SKILL.md` *Exact
  revision*; and #192's verification surface, `deep-code-review`).
- **Give the heavy run the machine.** Schedule it when the fan-out is quiescent, or
  explicitly cut sibling concurrency for its duration; a verification run starved into a
  stall returns **no** information — the worst return on the most expensive task (the
  swap-trend and WIP-cap gates above size that quiescence).
- **Split the long run so partial progress survives.** unit/type/lint → browser → audit →
  deploy-preflight, each reporting independently; a stall in one phase must not destroy
  the earlier phases' results.
- **Discovery findings are durable as leads; a discovery verdict is disposable.** Harvest
  the defects a discovery pass surfaces, but **re-confirm each at the new head before acting
  on it** — a finding carried forward without a re-run is `unverified`, not still-open
  (`deep-code-review` `method.md`) — and **discard the pass/fail**, never filing it as
  certification.

This composes with *a worktree assignment is a path… an integrator on a shared branch
detaches* above: that fixes **where** the integrator merges (a detached tree at the tip),
this fixes **when** release verification runs against it (after the tip stops moving) —
different axes, not competing schedules.

## Boot-the-dev-server lanes need a copy, not a symlink, of the dependencies dir

Any worktree that runs the **heavy gates** needs its own real install — run
`npm ci` in it (or a **copy-on-write clone** of a real `node_modules` on the same
volume). To share one installed-dependencies directory across throwaway worktrees,
lanes sometimes **symlink** it; edit-only checks (typecheck/lint/unit) *seem* to
tolerate the symlink, but it breaks the heavy gates three ways:
- **Under-install** — a dep present in the lockfile but absent from the shared tree
  makes `tsc` fail with **TS2307** ("cannot find module") — a false type error, not
  a real one.
- **Bundler boot** — the **modern dev bundler** rejects a dependency path that
  resolves *outside* its inferred project root ("points out of the filesystem
  root"), so the dev server never starts and the browser/UX gate reports a **false**
  "could not run."
- **Warning drift** — a symlinked tree yields phantom lint warnings, so a
  `--max-warnings` ratchet false-fails on a count that isn't real.

The tell is **local QA red where CI is green**; `npm ci` on the same tree settles all
three — the fix is mechanical (install, don't link). Reserve the symlink for
edit-only fast-tier lanes. And a gate must distinguish **"could not run" (infra)**
from **"found a problem"** — a bundler-boot failure, or a TS2307 from an
under-installed symlink, is the former, never a content finding (the gate-epistemology
distinction, principle 3 above).

## Serve and commit from separate trees — a long-running process dirties a gate-asserted config

A long-running process — a dev server, a codegen/asset watcher — that **rewrites a tracked
config file on boot** (regenerates or normalizes in place a config the toolchain owns)
deadlocks the commit workflow when both share **one working tree**: a test or pre-commit gate
that pins that file's **exact content** sees it dirty for the process's **entire lifetime**,
so every commit from that tree fails on a "modified config" nobody edited — or forces a
stop-server / restore-file / re-commit dance. **Serve from a different tree than you commit
from** (a dedicated worktree/checkout for the running stack, so the commit tree stays clean);
if one tree is unavoidable, make the process write to a **gitignored/untracked** path, or stop
it and restore the file before committing. Where a legitimate tool rewrites the file, prefer a
gate that asserts its **shape/schema** over its exact bytes. Distinct from "never `build`
against a directory a running server is serving" (a stale-asset *ship* failure — wrong build
output) and from the out-of-tree-scratch metadata-crossing section above: this is a single-tree
**serve-vs-commit deadlock** where a running process dirties a **tracked, gate-asserted** file
so the commit gate itself fails.

## Acknowledge a live-feedback burst before dispatching — silent throughput reads as ignoring

When the owner is present and firing many separate pieces of feedback, silently
dispatching background work — producing no acknowledgement — reads as *not
listening* and escalates frustration, even when work is in fact running in
parallel. Throughput without a reply is indistinguishable from ignoring them. On
each burst, the **first** action is to capture every item into a visible tracked
list and reply with the ordered plan plus what is already in flight; **dispatch
second**. One honest "captured all N, here is the order, these three are already
running" beats silent parallelism. Acknowledge first, optimise throughput second.

## Queue new requirements to a file the lane polls — interrupt only to stop or redirect

The burst rule above captures incoming feedback to a tracked list; when that feedback
is **new scope for a running lane**, the list must be a **durable file the lane polls
at its own checkpoints**, not an interrupt. The failure it prevents is **a lane busy
for hours that ships nothing** — a single implementation lane interrupted and
re-briefed a half-dozen times, each ask legitimate, each landing mid-orient so the
lane restarts its orientation and never reaches a commit; and each message *grows*
scope while retiring none, so the definition of done recedes faster than the lane
implements.

- **New scope goes to a file, not a message** — a checklist in the repo or an agreed
  scratch path the lane reads at its checkpoints, finishing the unit it is on before
  picking up the queue. A requirement buried in a transcript is only as durable as the
  lane.
- **Interrupt only for a genuine control signal** — stop, abandon, or a correction
  that invalidates work in progress. "Also do X" is not a control signal.
- **Freeze scope per deliverable** — a lane ships against the scope it was given;
  later asks are the next increment. Prefer a **shippable slice that then stops** over
  a consolidated deliverable with no stopping point — the slice lands artifacts under
  exactly the conditions where the growing lane lands none.
- **Count the re-briefs** — more than one or two scope-extending messages to the same
  in-flight lane is the signal that the scope was mis-sized: **split it**, don't send a
  third.

## An ownership map blocks a dual *write*, not dual *work* — and "assigned" is not "in progress"

The *Worktrees and occupancy* rule in `SKILL.md` (claim the work before starting,
one writer per worktree) prevents two lanes **writing the same file**. It does not
prevent two lanes **working the same objective** from different files: a module-
ownership map saying "lane A owns `api/`, lane B owns `web/`" answers *who may write
where*, not *is anyone already building this*. Read as a work-lock, it spawns a
duplicate lane on a feature already in flight. Before starting, check for an
**active lane on the objective**, not just file ownership — and treat a forge
**assignment as intent, not progress**: an assigned issue with no draft PR, no
worktree, and no commits is unclaimed in practice (`assigned` ≠ `in-progress`).
**Announce-then-take:** claim the objective (a draft PR, or a posted "taking this")
**before** opening the worktree, never after — take-then-announce races two lanes
onto the same work.

**The converse over-caution: a shared artifact in flight blocks only the lanes that touch
it.** Withholding *every* lane because one in-flight branch edits a shared file (a
design-token file, a lockfile, a config) is the mirror error — disjoint-surface lanes that
never touch that artifact are safe to run in parallel, and pausing them idles capacity for
a conflict that cannot occur. Gate a lane on whether **its own** surface overlaps an
in-flight write, not on whether **any** shared write is open.

## An ETA on a fan-out states its parallelism assumption — a serial estimate on parallel lanes is a fabrication

An estimated completion time for a multi-lane plan is meaningless without the
assumption under it: "done in 20 minutes" assuming N lanes run in parallel is off by
about N× when a resource cap (RAM, token budget, one CI slot — the same ceilings
that size the fan-out above) forces them serial. State three things with any
fan-out ETA — the **parallelism assumption** (N in parallel, or sequential), the
**constraint that caps it**, and, when that constraint is uncertain, both the
**parallel-optimal and serial-fallback** numbers. A one-number ETA with an unstated
parallelism assumption is unearned precision: the owner schedules against it and is
wrong, the same over-claim as a status that names no surface. Prefer a stated
**appetite** — a time-box the work is shaped to fit (`SKILL.md` G0) — over a bare
estimate wherever the work can be shaped.

## An unattended time budget is a work loop, not a single task — a milestone is not a stop

An agent holding a block of unattended time *to work a backlog* treats the *first* milestone it reaches —
a deliverable merged, the item it was pointed at finished — as the end of the
assignment, goes quiet, and leaves the rest of the granted window unspent. The grant
was a loop; that milestone was one turn of it. Read a time budget as *work the ranked
backlog until a termination condition fires*, not *do the one thing, then wait*.

- **Keep the backlog outside the working context.** A ranked list of what to do next
  lives in a file or a tracker the loop re-reads each turn — not only in the
  conversation, which a compaction or a handoff can drop. The
  **queue-a-requirement-to-a-file** rule above is this same discipline applied to
  *incoming* scope; this applies it to the *standing* backlog.
- **Index the backlog by the owner's ask, and answer "what's left" by reading it — never by
  reconstructing from the transcript.** The file above is a ranked *work* list; a long or
  unattended session also needs it to carry the **ask-set** — one row per distinct owner
  request (id, ask, status, evidence, next action) — updated **at each milestone**, not only
  at the end. When the owner asks "what's remaining" (often after a gap), the answer is *read
  the ledger*, answerable in one or two tool calls — not an O(N) re-scan of hundreds of turns
  that silently re-litigates settled items. A row is *done* only when its evidence points at
  the **canonical surface** — a merged-to-default SHA or a live URL — not a branch that merely
  contains the fix (`project-state.md`'s Acceptance and Artifacts receipts, and *a checkpoint
  is a recorded claim, not evidence*). This is the runtime, ask-indexed form of the
  feedback-coverage map (`roles.md`); it is distinct from the review-side reconciliation that
  audits a report's own claims against the artifact before closing (`method.md`, the
  `deep-code-review` skill), which runs **once at the end** rather than being read live
  throughout.
- **Name the termination conditions up front, each with its evidence.** The loop ends
  when the backlog is empty; when every remaining item is *blocked* on another party —
  including an item whose next step is an owner-approved action (push, merge, deploy:
  the **Human gates**, `SKILL.md`), which an unattended run cannot self-authorize; when
  the granted window or stated **appetite** is spent (`SKILL.md` G0); or when a resource
  ceiling is hit (the environment-probe ceilings above). Each ending is stated with the
  evidence that it holds ("backlog re-read; the tracker shows only owner-approval-gated
  items"), never asserted bare.
- **A milestone is a cue to pull the next item, not to stop.** Finishing an item or
  hitting a checkpoint re-enters the loop: pull the next backlog item and re-check the
  termination conditions. Stopping is a *decision* that a termination condition fired,
  and it is reported as one — not a drift into silence. An owner *stop* or *redirect*
  is a different thing — a control signal that ends or repoints the loop, governed by
  the interrupt rule above, not a self-milestone to work through.
- **If the loop is idling, say so loudly, and report the window, not the item.** A
  status covers the whole grant — *what is left, what is blocked and on whom, what is
  next* — not just the task in hand; an agent out of ready work names the termination
  condition it is parked on rather than going quiet, because silence reads as
  *working* and the owner discovers the stall late.
- **The owner's message cadence is not the loop's clock.** A coordinator that acknowledges
  a completed lane and then **waits** for the next owner message before refilling the slot
  has made human message frequency an accidental concurrency controller — throughput sags
  exactly when the owner goes quiet while safe capacity sits idle. A completed lane refills
  on the coordinator's **own** cadence: hold target concurrency while **unblocked,
  non-owner-gated** backlog and headroom remain, and a quiet stretch **never lowers** it —
  but a stretch whose only remaining items are parked on a human gate (`SKILL.md` *Human
  gates*) is a *termination condition* (above), not a refill opportunity. Admission stays
  governed by the fan-out gates — disjoint surfaces, free RAM and the swap trend (*gate on
  free RAM and the swap trend* above), one lane then re-probe with a burst reserve (#239) —
  **never by message count**; and the target is a *maintained* concurrency with
  backpressure, never unbounded spawning (bounded by the WIP-cap above; an unbounded
  fan-out otherwise exhausts the box — the RAM/swap gate above — and stalls everything).

## Research is not delivery — a brief with no tracked follow-through is reported as unconsumed

A lane sent to investigate comes back with a thorough brief, the brief is pasted into
the transcript, and the loop moves on — and nothing downstream ever acts on it. Effort
was spent; nothing was delivered. Research earns its cost only when its conclusions
become *tracked work*. The **cap-in-flight-by-landed-artifacts** rule above owns the
status discipline here: a brief is a transcript, not a landed artifact, so its honest
status is "researched, 0 items tracked," never "done."

- **End in an enumerated, trackable recommendation list, and open the items in the
  same step.** "Here is what I found" is not a queue; each recommendation becomes an
  issue, a backlog row, or a *recorded rejection* **now**, while the context is live —
  a conclusion that lives only in the transcript is lost at the next compaction or
  handoff.
- **Commission with a named downstream consumer.** Research is requested *for*
  something — a decision, a design, a fix. Name it at commission time; a brief with no
  consumer is one no one will act on.
- **Check the depth distribution before calling it consumed.** If only the cheap,
  obvious recommendations turned into tracked items and every expensive or structural
  one evaporated, the commissioned value did not land — the easy tail is not the
  reason the research was worth doing.
- **Watch research standing in for the delivery it was meant to inform.** A loop that
  keeps commissioning briefs while the thing they were supposed to unblock never moves
  is displacing delivery with investigation; the status that names *what shipped*
  (above) is what surfaces it.

---

## Sources

Fetched fresh for this file, verified 2026-09-09:

1. Kanban University, *Kanban Guide*. A WIP limit's purpose, verbatim:
   "balance utilization and still ensure the flow of work"; "limiting the
   work that is allowed to enter the system is an important key to reducing
   delay and context switching"; a WIP limit as "an enabling constraint."
   https://kanban.university/kanban-guide/
2. Google Engineering Practices, *Small CLs*. "100 lines is usually a
   reasonable size for a CL, and 1000 lines is usually too large"; small
   changes are reviewed more quickly and thoroughly, introduce fewer bugs,
   and simplify rollback.
   https://google.github.io/eng-practices/review/developer/small-cls.html
3. Wikipedia, *Blast radius* (computing sense). "The impact that a security
   breach of one single component of an application could have on the
   overall composite application"; a sibling technical-debt sense naming
   lockstep-edit surfaces directly.
   https://en.wikipedia.org/wiki/Blast_radius
4. GitLab Docs, *Merge trains*. "Two merge requests can each pass their own
   pipeline, but their combined changes can still conflict"; each queued
   pipeline runs combined with the target branch **and** every earlier
   queued change.
   https://docs.gitlab.com/ci/pipelines/merge_trains/
5. Brendan Gregg, *Linux Load Averages: Solving the Mystery*. "Adding the
   uninterruptible state means that Linux load averages can increase due to
   a disk (or NFS) I/O workload, not just CPU demand"; worked example, "a
   heavily disk-bound system might be extremely sluggish but only have a
   TASK_RUNNING average of 0.1" — the basis for "don't gate on `load1`
   alone" above.
   https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html

## Cross-references

- `SKILL.md` **Environment probe** — states the act-on predicate (free RAM +
  swap trend); this file holds the full probe procedure and the load-average
  mechanism.
- `SKILL.md` **Conductor operating rhythm** — the event-driven attention model
  this file's queue-sweep and fan-out-sizing sections extend.
- `SKILL.md` **Gate epistemology**, principles 3 and 6 — the two existing
  cases this file adds a third case to, and the union-proof rule the cascade
  section stays subordinate to.
- `SKILL.md` **Worktrees and occupancy** / **Local environment (own it)** —
  where the worktree-provisioning gotcha's two fixes belong in practice.
- `deep-code-review`'s `release-engineering.md` — the review-time audit of a
  *target's* release pipeline (feature flags, canary, DORA); this file is the
  authoring-time counterpart for the project's own fleet, not a target's.
- `docs/standards-index.md` — fetch dates and full citations for the five
  sources above.
