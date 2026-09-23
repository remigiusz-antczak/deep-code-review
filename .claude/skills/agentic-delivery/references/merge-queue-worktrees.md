# Fast agentic delivery — merge-queue cadence and worktree isolation

Read this when: draining a ready queue or a single merge seat, scoping an auto-merger, hitting a permission
asymmetry or a human-run escape hatch, reading a fleet-wide, load-flaky, contention-red, or absent check,
offloading a heavy gate to CI, or isolating a lane's worktree (stale refs, `git stash`, out-of-tree scratch, an
assignment path). Part of the `fast-agentic-delivery.md` lesson ledger — its index, sources, and cross-references
live there; an "above"/"below" pointer to a section not in this file resolves through that index.

---

## Sweep the whole ready queue on every trigger, not just the triggering item

The Conductor's attention is correctly event-driven, not polled — but a Conductor that reacts only to the
specific thing it is waiting on (one lane's own completion, say) can sit through several such events while a
**different, already-green, already-mergeable** PR sits idle in the same queue, simply because nothing about
that other PR generated an event. The fix: whenever the Conductor's attention *is* triggered by any of the four
named events, spend one cheap pass over the **entire** ready queue (a status check per candidate PR) before
returning to waiting — not only the item that triggered the check. This is a completeness fix to what a
checkpoint covers, not a change to the event-driven model itself.

## A serial queue-drainer must advance past a blocked head, not re-select it — head-of-line starvation

A serial auto-processor — a **merge-drainer, a retry queue, a task poller** — that picks the **first eligible**
item each cycle and retries it will **spin forever on one item blocked for a persistent reason**, starving
everything queued behind it. The tell is a loop that looks **idle** but is actually **starving**: an auto-merge
drainer picks the first **green + mergeable** PR each loop, but that PR is refused by a **stricter final gate**
(a PR-body lint, say) it cannot pass as-is — so the drainer re-picks the *same* head every cycle and never
reaches the others. The **cheap pre-filter is not the final admission gate**: an item can pass
*green + mergeable* forever while failing the final gate, so "retry the front of the queue" is a starvation bug,
not a queue.
- **Iterate all candidates per cycle; on a refusal, advance to the *next*** — never break the loop and re-select the same head. This completes the *sweep
  the whole ready queue* rule above: that says *scan the whole
  queue* (don't miss a ready item); this says *don't let one blocked item stop the drain* (don't get stuck on
  the head you did find).
- **Keep a cooldown / skip-set** for persistently-refused items so cycles aren't burned re-checking them, with
  **periodic re-evaluation** — the block may clear (the refusing gate gets fixed, a dependency lands).
- **Log the outcome per item** — `refused → advancing` vs `merged` vs `cycle idle` — so a spin is visible at a
  glance instead of reading as healthy idle (the *idle, say so loudly* discipline below, at the item grain).
- **🚩 tell:** a drain/retry loop that `break`s or `return`s on the first refusal, or re-selects `queue[0]` each
  cycle; or a *cheap* pre-filter (green + mergeable) used as the loop's selection key while a stricter final
  gate does the real admission.

## An auto-merger scopes by a manufactured ownership signal, not by author — shared identity makes authorship useless

The drainer above iterates the candidate set; this decides **which** PRs are *in* it. An auto-merge (or
auto-rebase) system must act on **agent-produced** PRs and **never** on a **human's own** (a human may be
mid-work, want to self-review, or own the domain — a large design build). The obvious scope — "only merge PRs
**authored by the bot**" — **fails when agents authenticate as the human**: agent lanes run `gh` under the
owner's token, so every PR, agent- or human-made, shows the **same author**. Authorship is then useless as a
discriminator, and an auto-merger keyed on it merges a human's unfinished PR the moment it goes mergeable
(observed: a drainer excluded a risky set by PR *number*, but a human-owned design PR shared the agent author —
only a semantic read of branch / diff / subject told them apart).
- **Give agents a distinct identity** — a bot account or a separate `GITHUB_TOKEN` — so authorship is a *real*
  discriminator. The clean fix.
- **With a distinct identity, filter by the author-identity match itself — never hand-maintain a list.** Once
  agents have their own account, the reliable ownership signal *is* the author field: scope the auto-merger to
  PRs whose author **positively matches the automation's own account** and default-deny every other, so a
  human's PR is out of scope *by construction*, not by having been listed. Do **not** substitute a hand-kept
  exclusion/allow list of PR numbers or branches for that match — a manual list is only as current as its last
  edit, and the PR it never learned about is the *next* human PR, so it goes stale and eventually auto-merges a
  human's mid-review work the moment that unlisted PR is mergeable. A list is the right tool only in the
  shared-identity case below, where there is *no* author signal to key on; where a distinct identity exists the
  author match strictly dominates it. Verify the match against the PR's real author, not an assumed token
  identity (a green-looking identity is a floor, not proof).
- **If identity must be shared, key the auto-merger on an explicit convention** — an allowlist of agent-created
  PRs, a denylist of human-owned branches, a label (`agent-mergeable`), or a branch prefix (agents `bot/*`,
  humans `feat/*`). **Default-deny anything not positively marked agent-owned;** never act on a PR you cannot
  *positively confirm* is agent-owned and safe.
- The general rule: automation acting on **shared artifacts** needs a **reliable ownership signal**, and when
  identity is shared you must **manufacture** one (a convention/label), never infer ownership from a field every
  actor shares.
- **🚩 tell:** an auto-merger scoped by PR author (`author:@me` / `gh pr list --author @me`) in a repo where
  agents run under the owner's token; or any auto-merge/auto-rebase with no positive agent-ownership mark (label
  / branch-prefix / allowlist) and no default-deny; or, where agents **do** have a distinct account, an
  auto-merger keyed on a hand-maintained exclusion/allow list of PR numbers or branches instead of the
  author-identity match — a stale list that auto-merges the next human PR it never learned about.

## An auto-mode permission gate that denies the orchestrator but allows a sub-agent is a false "stuck"

An unattended orchestrator draining a queue of green, mergeable, un-held PRs can hit a permission classifier
that **denies its own `merge`** ("merge without review") while
**allowing the identical merge from a spawned sub-agent**. The loop then runs every tick and lands nothing — the
operator sees "stuck / not pushing" when the work is done and gated only by the classifier, and all real
throughput is silently forced onto sub-agent delegation (fine for a *clean* merge of a PR that already
independently passed the gate — but delegating a **workaround** for an action the orchestrator was just denied
is itself catchable as laundering, not a loophole, and a single-PR merge does not warrant a heavyweight
isolated-worktree lane). The asymmetry is the trap: it is surprising, usually unlogged, and reads as a pace
regression rather than a gate. Resolve it explicitly instead of letting the loop burn ticks retrying a
structurally-blocked call: (1) a **preflight-keyed allow-rule** — permit the orchestrator to merge a PR whose
repo-defined green-gate / `merge_preflight` has just passed deterministically (the deterministic portion of the
review the classifier wants already ran); or (2) **symmetry + transparency** — if merges must be delegated, deny
them for sub-agents too and surface the reason ("merges routed to a delegated lane in auto mode") rather than a
bare denial the loop swallows; and (3) **document the routing** so the orchestrator delegates merges by design,
not by trial-and-error. **🚩** an auto-mode loop whose merge tick runs but lands zero PRs while sub-agent merges
succeed — a classifier asymmetry, not a slow agent.

**A second, compounding denial: the dirty-working-tree preflight (and its bypass flag) is itself denied to the orchestrator.**
An orchestrator that must hold uncommitted state for its own work — a WIP commit, edits mid-task — while also
draining the merge queue can face two stacked denials, not one: the classifier above denies its own `merge`, and
a dirty-working-tree preflight (plus whatever flag would skip it) is *also* orchestrator-denied. Both routes
close on the same tick, and the orchestrator can **land nothing across many ticks** while the queue sits green
and ready — the same classifier-denies-orchestrator asymmetry, compounded rather than resolved by either single
fix. The doctrine fix (not a script):
**delegate the merge itself to a subagent in its own clean, isolated worktree.** This does not need a second
laundering test: the existing carve-out just above already covers the merge itself (these PRs already
independently passed the gate); what the clean tree adds is the other half — its dirty-tree preflight predicate
becomes genuinely true rather than skipped through a passed-along bypass flag, so nothing is laundered there
either. Don't let this become a heavyweight lane per PR either — the caution above still holds:
**size the delegated lane to the batch, not to one merge.** Amortize one clean-worktree lane across 2-3 small,
disjoint, already-green PRs that merge in sequence through it, rather than spinning a fresh isolated worktree
per PR. Whether that batch also clears the project's own merge-authority bar as a train or a cascade is the
cascade section's question (below), not this one — this only sizes the lane doing the merging, never the
authority that admits what merges.

## When no autonomous path exists, surface the human-run escape hatch up front — don't narrate "holding"

Distinct from the delegation asymmetry above (where a sub-agent *can* act): when an agent is blocked from a
gated terminal step (a merge, a deploy, a paid call) and has **no autonomous route** — its own call denied *and*
delegation unavailable or also gated — a closed gate with verified work piled behind it is an
**escalation, not a hold** (distinct from "holding is a valid response" below: that rule forbids *manufacturing*
new work at a terminus; this governs what the *truthful status* must contain when banked-verified work is
stacked behind the gate). The failure mode is looping "gated / holding" every scheduler tick while banked,
green, mergeable work stays at **zero landed** — invisible to an operator who watches only the integration
branch, so a done-but-unlanded agent reads as slow or idle. On the **first** denial, convert the block into a
**one-action ask**: a single copy-pasteable command the human runs themselves (in host CLIs that provide a
user-executed shell prefix — e.g. Claude Code's `! <command>` — that command executes as the *user*, outside the
agent's own auto-mode classifier: a legitimate escape hatch, **not** permission-laundering, because the human
issues it — the agent must not run the prefix itself or re-route the denied action through any agent-controlled
path) or one GUI action, surfaced prominently and repeated, not buried under status ticks.
**Make the one action a query the human can re-run, not a snapshot list that goes stale.** A command hard-coded
to today's green PR numbers is correct once and wrong an hour later, forcing a re-issued command every batch —
the repeated pinging this section exists to stop. Hand over a **self-updating, idempotent** command instead:
discover the eligible set at run time (open PRs on the target branch, minus a named held/owner-gated set,
filtered to checks-green), merging each with a mergeability-recompute retry. This shifts what the human approves
from *this list* to *this policy* (merge whatever is green, now and on every re-run) — the named
held/owner-gated exclusion set is now the load-bearing part, since it is what the human is actually vetting once
they stop reviewing each PR number. The human runs the command once and re-runs it later to sweep whatever has
since turned green. **Track banked-verified vs landed**: when banked>0 and landed=0 for more than a tick or two,
escalate the human ask rather than re-reporting the block. Never let "the gate is closed" become a steady state
the agent narrates. **🚩** an unattended run reporting "holding / gated" across many ticks with a growing pile of
verified-but-unlanded work and no single human-runnable unblock surfaced.

## A third gate-epistemology case: a correct, external, fleet-wide finding

Principle 3 separates *the check could not run* (`UNVERIFIED` — never a pass, and a *required* missing check
still blocks its gated action) from *a real defect the diff introduced* (fail closed). A newly-published,
correctly-detected dependency-vulnerability advisory is neither: the gate is right, the finding is real, and it
is shared across every open change **and the mainline itself**, with no relationship to any one diff. One
observed instance: a real advisory reddened the mainline and every open PR in a queue at once with zero code
change from any of them; the fix that actually unblocked the fleet was
**one coordinated dependency-lockfile bump**, landed as a fix-forward, after which the rest of the queue needed
to resync against the new mainline rather than each independently rediscover the same fix. Name this case
explicitly — it saves the diagnosis time of treating a fleet-wide, external-cause red as N unrelated
regressions. It is a **diagnosis shortcut, not a new merge authority**: it does not license merging onto a red
mainline beyond whatever narrow, human-approved change-control path a project already has for exactly this case
(one reviewed, unblocking fix).

## An independent-PR-queue cascade is a cadence choice, not a new authority

Gate epistemology principle 6 requires union proof before a merge train — not restated here. A related but
distinct situation: a **queue of PRs that are each already independently green**, with no known interaction
between them (typically right after the single common blocker above is fixed and the whole queue needs to
resync). Landing that queue does not need a new, lighter-weight merge authority — it needs **cadence**: run the
project's own merge-authority check against every queued PR on a short interval, rather than merging one PR and
waiting for the mainline's full CI resolution before even looking at the next.
**The one thing this must not become:** a second, separate pre-check (e.g., asking the forge "is this
mergeable?" through a different call than the authoritative merge gate itself) that races the platform's own
status — mature merge tooling names this exact anti-pattern from a past incident and refuses it by design,
calling only the one authoritative gate, every attempt, never pre-checking through a second path. A cascade is
**weaker evidence than a union-proven train**: a train proves the *combination* is sound before any member
merges; a cascade only proves each member was independently green and re-confirms that at each step. Defensible
specifically right after a single common blocker clears and every queued PR was already independently green —
not a general substitute for a train when queued PRs might still conflict with each other.

## Parallelizing the merge *seat* backfires under a base-sensitive gate — single-seat back-to-back draining is the real lever

The scaling reflex — more agents doing the bottleneck action (merging) ship more PRs per minute — is **wrong**
when the merge action is not merely contended but **self-invalidating for the whole queue**. Every merge
advances the base head, and every *other* open PR's base-diffing gate state is valid only against one specific
`base.sha`. A **second merger** does not halve the work — it **doubles the rate of base-invalidating events**
hitting every other open PR, compounding two failures: (a) a base-sha-sensitive gate that **fails closed** (a
misleading "no result," not an honest "stale — recheck") when it cannot cleanly resolve its diff against a
rapidly-moving base, and (b) concurrency-cancellation groups discarding in-flight check runs that were about to
pass, as competing merges churn shared state faster than runs complete. Net **slower**, not faster. The real
merge-rate lever is **single-seat, back-to-back draining**: one merger takes **all** currently-green PRs inside
one green-base window (many in a short burst — the wait only bites *between* windows; what the window's own
admission check does with a base run still in flight *between* members is sharpened just below), plus CI
speed-ups, plus a **union-proven merge train** (above) where queued PRs might still conflict. Keep the merge
seat a single `exclusive_role` in the claim registry (`multi-session-coordination.md`) — a second seat is not
throughput, it is base churn. Distinct from `branch-and-merge-hygiene.md`'s
*freeze merges while a resolver is active* rule — that is merger-vs-**resolver** (protecting the resolver's own
just-computed rebase); this is merger-vs-**merger** (protecting every *other* open PR's base-diff gate and
in-flight runs). This is the flip side of the merge-train rule: back-to-back draining from *one* seat is the
win; a *second* seat is the loss. **🚩 tell:** two agents offering to "split merge duty to go faster," then a
wave of PRs failing a base-diff gate closed and in-flight runs cancelled — the seat was split, the
base-invalidation rate doubled.

## The window's admission check is not-red, not fully-green-between-members — a base run still in flight is not a hold

This sharpens the single-seat, back-to-back draining lever above: that lever names *who* holds the seat and
*when* it drains (one green-base window — it **opens** on a known-green base and **closes** on the post-batch
green re-confirmation below), not what the window's own admission check does, in its interior, with a base run
still in flight *between* members. Pending is admissible *inside* the window; only its open and close are
required to read green. It is not a new claim so much as the same logic `branch-and-merge-hygiene.md`'s
merge-train section already states for the *union* branch's CI: treating "union CI still pending or red" as a
reason to hold members that are each already green re-serializes the very wait the train exists to remove.
Applied here to the **integration base's own post-merge run** instead of a union's: a shared base commonly
triggers a multi-minute CI run on every new head. If the seat's admission check demands that run
**resolve green** before it will admit the *next* member, the seat pays the base's own CI cycle once per merge,
and throughput serializes at (batch size) / (CI-cycle time) — the identical per-PR base-CI wait the merge-train
lever (above) exists to remove, reappearing *inside* the single seat instead of between competing seats.

The fix is the admission predicate, not a new draining mechanism: gate the window on the base reading merely
**not red** — pending / in-progress is admissible, only a **confirmed-failing** check on the base blocks — and
drain every member that is (a) own-green on its own required checks and (b) still mergeable, re-checked per PR
since a sibling landing can flip one to `CONFLICTING` (`branch-and-merge-hygiene.md`'s
mergeability-is-a-snapshot rule; not restated here). Where the queue might interact, prove the union once up
front, exactly as the merge-train lever above already directs (`SKILL.md` gate epistemology principle 6; not
restated). Close the window with **one post-batch check**: re-confirm the base actually resolved green after the
drain, so a combination that reds it despite every member's own green is caught and fixed forward — never
assumed safe merely because no single merge paused to watch its own run resolve.

This does not loosen the **red-base discharge** floor: a base already **confirmed** red is a deadlock that needs
a proven union to discharge (`branch-and-merge-hygiene.md` §5), not a not-red-gate bypass — not-red admission
covers the ordinary *pending* case that rule doesn't address, never a base already known to have failed. Nor
does it touch *cadence* (the independent-queue-cascade section above, on how **often** the seat re-evaluates the
queue) — this is the check's **threshold** (which base state admits the next merge); the two **compose** — a
not-red threshold applied at whatever cadence — they do not overlap. It is exactly as narrow as the
serial-fallback carve-out already states: wait for the base between merges only where a true dependency stack
cannot share one union.

**🚩** a seat that requeries the base's full check suite to **green** before admitting each next member — paying
a base-CI cycle per merge inside what was supposed to be one draining window — or a batch that closes with no
post-drain check confirming the union of merges actually landed green.

## Flipping the whole draft stack to ready at once floods the shared runner pool without feeding the serial seat any faster — stagger the ready-flips

The two sections above govern the merge **seat** — one serial holder, admitting the next merge on a not-red
base. This governs the step *upstream* of the seat: the draft→ready flip that makes a PR eligible in the first
place. The reflex, once a wave of lanes is done, is to flip **every** draft to ready at once "so the seat can
start merging them" — but that buys no throughput and courts an incident.

- **The flip is not the merge, and the seat is the bottleneck.** Readying a PR does not merge it; it only makes
  it a *candidate*. The seat still merges one at a time (*single-seat, back-to-back draining* above), so the
  merge rate is capped by the seat and the base's CI cycle, not by how many PRs are ready. Twenty ready PRs and
  four ready PRs drain through one serial seat at the same rate.
- **What flipping to ready *does* fire is the heavy CI suite — per PR, into a shared pool.** Draft PRs commonly
  run only the fast tier; the browser / a11y / visual / E2E matrix is gated on ready-for-review or a label
  (*Draft-gated heavy checks*, below). So flipping N drafts to ready at once dispatches
  **N heavy check-suites into a shared runner pool simultaneously**. The pool has a fixed concurrency, so the
  surplus past it **queues**: every check on every PR sits `pending` for many minutes, the fast checks that
  would have gone green quickly are stuck behind the flood, and the seat is *starved* anyway because nothing
  reaches green promptly. Pushed far enough it is a self-inflicted **runner-drain incident** — the shared pool
  is exhausted for every other lane and repo on the account, not just this queue.
- **Stagger the flips to a small in-flight window; drain, then flip the next.** Hold the count of *ready*
  (CI-running) PRs to a small window sized to the runner pool — a low default such as 3–4 — flip that many
  draft→ready, let their suites finish and the seat drain them, then flip the next batch. Same eventual
  throughput (the serial seat was always the cap), a steady green pipeline the seat consumes at its own rate,
  and no pool exhaustion. This is the WIP-cap-by-landed-artifacts discipline (above) applied to the
  **ready-flip** admission point and bounded by the **runner** budget rather than local RAM.

Distinct from *single-seat, back-to-back draining* and *the window's admission check is not-red* (both above):
those govern the **merge** action — how many *seats* (one) and which base state admits the next *merge*
(not-red, so "take all currently-green in a burst" is right *for merging*). This governs the **ready-flip**
action upstream of the seat — how many PRs have their heavy CI *in flight* at once — whose cost falls on the
shared runner pool, not the base-diff gate; readying all at once and merging all already-green at once are
different actions on different resources. Same shape as
*a shared API/model quota is a fan-out ceiling no local probe can see* (above) — a shared external budget a
local box cannot observe — but the resource is the **CI runner pool** and the lever is staggering
**ready-flips**, not narrowing model lanes, and the failure is checks **pending** (queued), not lanes
**erroring** on a rate limit. **🚩 tell:** a wave of lanes finished, all drafts flipped to ready in one sweep "so
the seat can merge them," then every PR's checks sit `pending` for many minutes while the serial seat merges
them one at a time no faster than a staggered flip would have — and other work on the account stalls on a
drained runner pool.

## A load-flaky required gate is not a confirmed red — bounded-rerun the same commit to reclassify it before concluding a regression

This expands `SKILL.md` gate-epistemology principle 3 ("if the shape matches a known-flaky
browser/probe/hydration check, rerun and recheck **before** reverting") to the verdict an
**autonomous merge-drainer** draws from a required check's pass/fail bit after each merge. Principle 3 carries
the discriminator — identify the failing job **and step**, match it against a known-flaky signature, revert only
once the failure **reproduces** and is causally tied to the change — and the rerun **mechanics** live in
`branch-and-merge-hygiene.md` §5: diagnose a slow/stuck shard by its log, **rerun at most once, only after**
diagnosis, no *rerun-storm*, and retry only an indeterminate result (an `UNKNOWN`), never a **definite**
failure, as if it were transient. Neither is restated here. What the drainer case adds is the **verdict layer**:
a first red is not a regression conclusion, the premature *halt* is as costly as the premature *revert*, and an
auto-rerun that keeps working is itself a tracked defect.

The trap is specific: a required gate that shells out to an external probe under a tight timeout is
deterministic in isolation but **load-sensitive** under merge volume, so a busy runner reddens the trunk with no
code change from any diff. From the bit alone the drainer cannot separate this **load-flake** from a real
regression, and both naive reactions are wrong — **halt** the whole queue (throughput collapses and an innocent
PR is blamed, sometimes auto-reverted) or **force through** (a genuinely broken trunk is hidden for the next
contributor). Principle 3 governs the premature *revert*; the premature *halt* is the other face of the same
misread and is just as costly.

- **A first non-green is a candidate to reclassify, not a verdict.** If its shape is on the known-flaky list,
  rerun the gate on the **identical commit** — never a silent rebase, which changes what is tested and can
  launder a real failure into a "pass" — within the bounded rerun budget §5's slow-shard-diagnosis rule sets
  (para 1). Green on rerun confirms the flake; proceed. This is how a first red *becomes* a **confirmed** red:
  only after the bounded reruns still fail is the trunk a confirmed-failing base, at which point the
  **red-base discharge floor** applies (a confirmed red is a real deadlock needing a proven union to discharge —
  the floor above, and `branch-and-merge-hygiene.md` §5) and a revert is warranted — name the candidate commits.
  The first red is never itself the confirmed red.
- **Only a known-flaky shape is a rerun candidate; everything else is real immediately.** A shape *not* on the
  list — a real assertion, a type error, a lint — is deterministic and reproduces, so it is a real regression on
  the **first** red; never rerun it blind. This is §5's
  *retry only an `UNKNOWN`, never a definite `CONFLICTING`* rule read at the required-check layer (and the
  lane-level twin, *an ENOSPC is a sizing bug, not a flaky lane to retry*, above). The cap does double duty in
  the drainer: past it the verdict **flips** to suspected regression — it does not merely stop the retrying.
- **The auto-rerun is a stopgap, not the fix — track it as a defect.** File the flaky gate for a **durable fix**
  (make the probe fail-open on a can't-check, widen the timeout, or de-parallelize it) and watch the
  **fraction of reruns that go green**: a rising ratio means the flaky-signature list is outgrowing the fixes
  and the drainer is leaning on a crutch, each entry a gate that still needs its own repair.

Distinct from **"bound every flaky finalize step"** (below): there the bound's expiry falls back to a text
`Verify:` report and the change still lands; here the bound's expiry **flips the verdict on the code** — flake
to suspected real regression — and gates the halt/revert decision itself. Distinct too from the
**fleet-wide external advisory** (above): that is a *real* finding shared by every open change, fixed by one
coordinated bump; a load-flake is **not a real finding at all**, and the remedy is a rerun, not a fix-forward.

**🚩** a drainer that concludes "regression" — halts the queue or auto-reverts the last merge — on the **first**
non-green of a load-/infra-shaped required check without a bounded same-commit rerun; or one that reruns a
**deterministic** assertion failure instead of treating it as real; or a rising rerun-went-green ratio nobody is
converting into durable gate fixes.

## A local pre-push gate reddened by machine contention is not a regression — re-run the failing check in isolation before concluding one

The load-flaky-required-gate rule above is the CI/merge-drainer sibling of this one: it reads a
*required check's* pass/fail bit and reruns the **identical commit** to reclassify a first red. The same
discipline governs the **local build/test/lint gate** several lanes — or peer sessions
(`multi-session-coordination.md`) — run before push on **one shared machine**, with one constraint the CI
wording leaves open: the rerun must also be **isolated**, because the contention that reddened the gate is
*on that box*, so a same-commit rerun taken while the other heavy lanes still run reproduces the contention, not
the code. The canonical rule — a failure appearing only under fan-out concurrency is contention, not a defect,
until reproduced at low concurrency, and its "re-run the specific failing check in isolation" step — is
`parallel-audit.md` §0 (in the `deep-code-review` sibling) and is **not restated here**; this applies it to the
delivery gate's own verdict.

- **A first red under aggregate load is a candidate to reclassify, not a regression conclusion — and bypassing the gate is not the alternative.**
  Several full local gates at once can exhaust the shared box's CPU / RAM / file descriptors, so a
  headless-browser render times out, a latency/timing assertion trips, or a suite flakes — indistinguishable,
  from inside one lane, from a real regression the diff introduced. Concluding "regression" burns a fix cycle
  chasing a non-bug; `--no-verify`-ing past the red defeats the gate. Do neither on the first red.
- **The disambiguator is a rerun *in isolation*, not merely on the same commit.** Quiesce the box first — pause
  or kill the other heavy lanes, shedding the test runner's own browsers but not the app's dev server
  (*CI-offload the heavy gate* above) — then re-run the **specific failing check** on the identical commit. A
  pass on the quiesced box proves the red was contention; only a failure that
  **still reproduces at low concurrency** is a candidate regression and enters the fix queue. A same-commit
  rerun taken *without* quiescing is not a valid disambiguation: under sustained contention it keeps failing and
  wrongly flips the verdict to "regression" — the exact wasted cycle the load-flaky rule's bounded rerun assumes
  it has already ruled out.
- **Prevent the misread by sizing, not only by diagnosing it after.** Throttle heavy gate lanes by *measured*
  load (free RAM + the swap trend, *Gate on free RAM and the swap trend* above; the peer-aggregate form is
  `multi-session-coordination.md`'s shared heavy-lane reservation), and run locally only the gate CI actually
  enforces (*CI-offload the heavy gate* above) — so fewer contention-flakes reach the verdict step at all.

Distinct from *Gate on free RAM and the swap trend* and *CI-offload the heavy gate* (#935): those decide
**whether and how heavily** to run the local gate (sizing) — prevention; this decides
**how to read a red the gate already produced** — interpretation. Distinct from the load-flaky-required-gate
rule above: that is the CI required-check verdict with a same-commit rerun; here the shared-machine gate's rerun
must *also* be **isolated**. **🚩 tell:** a lane opening a fix or reverting on the **first** red of a heavy local
gate — or bypassing the gate — while other heavy lanes are live on the same box, with no isolated re-run of the
failing check to separate contention from a defect.

## Absent checks are a third state, not a slow "pending" — an uncomputable merge ref suppresses the run; bounded-wait then re-trigger, never wait forever

The two sections above are how an autonomous drainer reads a check-state bit at two of the places it reads one:
the *not-red* section sets the **base-admission threshold** (a base run still in flight is admissible — pending
is not a hold), and the *load-flaky* section sets the **red-verdict rule** (a first red is a candidate to
reclassify, not a regression conclusion). This is the third place — a **member PR's own** readiness — and its
rule is that **absent ≠ slow**: a PR reporting *zero* checks (none at all — not one in flight, not one red) is
not a check that is merely early, and a drainer that treats it as one waits forever.

The mechanism is that CI runs against a **computed merge ref** (the PR merged into its base), not the raw head.
When the PR is non-mergeable — `mergeable_state=dirty`: a real conflict, or its base advanced past what it last
merged — the forge **cannot compute that ref, so it never dispatches CI for the head at all** (a runner-queue
backlog can suppress the dispatch the same way, transiently). The PR then shows **no checks**, which is fatally
easy to misread: a human or drainer sees "no failures" and reads it as *still pending*, or even *clean*, when in
fact the run never started and never will for that SHA without intervention. A drainer whose rule is "poll until
the checks appear and go green" then polls a PR whose checks will never appear — the same starvation as the
blocked-head case above, but from a head that was never *checked* rather than one checked and *refused*.

- **Read `mergeable` / `mergeable_state` alongside the check list — it is the discriminator.** Zero checks +
  non-mergeable (`dirty` / `CONFLICTING`) = **stalled**: the run was suppressed and needs a re-fire. Zero checks
  + `MERGEABLE` = **genuinely just-triggered**: a bounded wait is correct. The two act on
  **different fields, and neither is wait-forever**: poll the *mergeability* field until it settles (the brief
  `UNKNOWN`-while-recomputing state `branch-and-merge-hygiene.md` bounds to 2–4 tries), then apply
  bounded-wait-then-re-fire to the *check list*. The check list alone cannot split stalled from fresh; the
  mergeability field is what does.
- **Recover by re-triggering, not waiting.** A fresh fetch + merge-of-base + push (or a rebase) recomputes the
  merge ref; if the re-merge is conflict-free, `mergeable` flips and CI fires within seconds — the rebase /
  re-run-CI mechanics are `branch-and-merge-hygiene.md`'s, not restated here. A true `dirty` from a real
  conflict needs that conflict resolved first; either way the move is an **action**, never more polling.
- **Time-box zero-checks, and never read it as a verdict.** Past a short dispatch-delay threshold **and** while
  non-mergeable → escalate to a re-merge; do not keep polling. Never interpret zero-checks as an implicit
  **pass** (the run never ran) or as a stable **pending** (it will never resolve on its own). Track PRs sitting
  at zero checks while non-mergeable past a normal dispatch delay — a nonzero count is work stalling invisibly
  on uncomputable merge refs.

Distinct from the **config-unsatisfiable required check** (`branch-and-merge-hygiene.md`'s
*a required check must be satisfiable* rule, the #262 *no-status* case): there a required check **name** never
gets a job to report because the workflow is wired wrong (a path filter, a trigger-event gap, a missing
`on.pull_request.branches` base entry), and the fix is **config-side** and permanent — a pass-through job or a
corrected `on:` block. Here the workflow is correctly wired; a re-merge makes the *same* job fire. Same surface
symptom (no status looks like pending), opposite remedy — a config fix vs a re-trigger. Distinct too from the
**serial-drainer spins on a blocked head** rule (above): there the head is green + mergeable but refused by a
*stricter final gate*, so the drain **advances past** it; here the head was never checked at all, so the drain
**re-fires** it — advance-past abandons a genuinely-blocked item, re-fire rescues a never-started one.

**🚩** an orchestrator turn history that is a run of near-identical "still waiting for CI" ticks on a PR that
shows **no checks at all** and is non-mergeable — the *emit-on-transition-only* tell (below) applied to a state
that will **never** transition without a re-merge; the loop is not waiting, it is stuck, and the run it is
waiting for was never dispatched.

## An opt-in throughput lever is inert until the default path takes it — attribute the gain to what runs by default, not to the merge

The throughput-lever instance of `SKILL.md` G2's "a cap that defaults to off is not a cap": when a CI/delivery
optimization ships as an **opt-in** capability — a `test:affected` script, an `--affected` flag, a gate mode
gated behind an env var — *merging* it speeds nothing up. The number moves only once the capability is wired
into the **default** path the pipeline actually runs: the CI job, the default gate script, the drainer's own
gate invocation (the diff-affected lever named above is the concrete case this attaches to — run only
diff-affected tests **by default**, not as a flag a caller must remember). This is the general
**beware-the-proxy** discipline — a merged PR is a proxy for the outcome, not the outcome itself
(`deep-code-review`'s `report-format.md`; gate epistemology principle 11 lists "Integrated to the mainline (G7)"
among the same proxy states) — applied to a throughput lever specifically, not a restatement of it. The
identical shape already gates a *safety* control elsewhere in this suite: "a shipped default or an opt-in
example — a demo gate that lives in `examples/` and is never loaded is not a control" (`deep-code-review`'s
`security-ai-agents.md`). An opt-in throughput lever left unwired is the same non-control, priced in CI minutes
instead of risk.

- **Attribute the gain to the default path, not the merge.** Confirm the actually-run surface takes the fast
  path **now, by default** — not merely that the capability exists behind a flag someone could pass.
- **Name the wiring-in as its own tracked deliverable.** If it is blocked — a held PR that owns the workflow
  file, an owner-gated config change — the merged capability is **inert**: real spend already paid, zero
  throughput gain realized. Say so; don't count an inert capability as the delivered speedup.
- **Measure before/after on the real job's window, not the capability in isolation** — the same
  p50/p95-of-time-to-green, attribute-the-percentile-to-a-stage discipline this suite already requires before
  adopting a build/CI platform (`deep-code-review`'s `release-engineering.md`; not re-taught here). If a speedup
  *did* show up that session, trace it to a specific, named change before crediting the opt-in lever for it — a
  different change landing the same session is the more common explanation than an inert flag that nothing's
  default path invokes yet, and mis-attributing it buries the change that actually worked.

**🚩** a status update crediting "we shipped the `--affected` flag, CI is faster now" without ever confirming the
default job invocation passes `--affected` (or equivalent) — the merge got credited; the wiring, which is what
would have actually moved the number, did not happen.

## CI-offload the heavy gate by default — lane weight, not lane count, drives memory cost

A lane that runs a project's full local aggregate gate — a real build plus the complete browser/E2E suite plus
any slow lint/audit step — boots many headless-browser processes per run and is the dominant memory cost on a
shared machine, not merely "one more lane." A lane running only the fast tier (lint, unit, type-check, at most
one targeted spec relevant to the diff) costs a small fraction of that. With several full-gate lanes running at
once, the machine's memory gets consumed even when each lane's own resource check passed at spawn time, because
the check ran before the browser-heavy phase started, not during it. Default a lane's own local verification to
the fast tier, and let CI's own — ideally already-parallelized — jobs carry the full matrix. This sharpens
"verify on CI, treat a local run as the pre-check, never the evidence": defaulting every lane to the light tier
is the actual concurrency unlock — it is what lets several lanes run inside the RAM budget one full-gate lane
alone would otherwise consume — not a smarter resource-gate formula (previous section).

- **Run neither less nor more than the gate that actually admits your change.** The offload above trims a lane
  *down* to the fast tier; its converse trims *out* a suite CI does **not gate merges on at all**. A heavy local
  suite (a full browser/E2E run) absent from CI's required-check set is not a merge gate anywhere — running it
  locally as a blocking lane gate is **pure thrash**, spending the machine's scarcest resource (the
  headless-browser processes that drive the swap trend, *Gate on free RAM and the swap trend* above) for zero
  merge-safety (#935). Mirror of the delegated-green rule below (brief a lane with the **root** gate it is
  judged by at land): there a lane runs *narrower* than the real gate and false-passes; here it runs *wider*
  than any gate and thrashes. Match the local blocking gate to CI's **actually-enforced** set — no less, no
  more.
- **When a heavy run still thrashes the box, shed by process class, not blindly.** A lane tearing down its
  **own** helpers the moment their step ends (*kill a lane-owned helper*, below) has a selection rule to get
  right under memory pressure: the test-runner's **managed/headless browser** processes are the disposable mass
  to kill, while the **app's own dev server** is load-bearing for the UX gate and must be
  **protected by its port/PID**, never swept with them. This adds only **which** processes are safe to shed on a
  lane's own live-teardown path; the **orchestrator-level** sweep of *orphaned* processes stays advisory and
  approval-gated (*the orchestrator also owns reaping orphaned heavy processes*, above), and the kill mechanics
  (own a process group, terminate by pgid) stay in `deep-code-review`'s `concurrency-shared-state.md` — not new
  authority to kill.

## Draft-gated heavy checks hide a UI-regression wave — run them somewhere while the draft is open

The section above offloads the heavy gate to CI — but CI commonly runs those expensive jobs (headless-browser,
a11y, visual/hydration, UX audit) only on ready-for-review or a label, with drafts running the fast tier alone.
When a large change lives as a long-lived **draft** across many sub-lanes, every lane reads fast-tier-green
(lint / unit / type-check) while a whole class of **browser-only** defects — responsive breakage, focus-visible
/ keyboard, truncation without an accessible name, SSR hydration mismatches — accumulates unobserved. Flipping
to ready then surfaces the whole wave at once, late, as a regression. Fast-tier-green is **not UI-correct**; no
unit/typecheck gate observes those signals. Two fixes: (a) run the heavy/browser gates on the
**integration branch periodically** while the draft is open, or (b) explicitly
**budget for a late regression wave** and never present a stack of fast-tier-green lanes as demo-ready.
Browser-only signals are the **coordinator's** to verify centrally on the rendered page, not delegated to lanes
whose own gates cannot observe them.

## A worktree's own gate can fire on a file it does not own

A definitions- or content-only change can rebuild a generated artifact that is *mirrored* into a directory owned
by a different toolchain (for example, a compiled data file synced into an application directory whose own
pre-commit gate fires on any staged path under it). In a **fresh** isolated worktree — before that toolchain's
own install step has run — the mirrored file alone can trip that gate and fail closed, even though the change
never touched that toolchain's code. Two portable fixes, either sufficient: (a) provision the *whole* worktree's
toolchain (run every subtree's own install step) before the first commit, even when the change looks confined to
one subtree; or (b) scope a definitions/content-only lane to skip staging the generated mirror at all, letting a
downstream build step regenerate it. This is a **provisioning gap, not a defect in either gate** — each gate
does exactly what it is supposed to; the worktree was simply not fully set up for the one it tripped.

## An isolation worktree inherits the parent clone's stale refs — verify freshness, or query the server

A worktree branched off the local clone's **remote-tracking ref** runs whatever version of the build / CI /
merge scripts that ref points at. If the clone has not fetched recently, the worktree silently runs **stale**
scripts and produces **false** results — a merge-preflight that still requires a CI job the current workflow has
since **removed** will refuse every PR with "required job never ran," while the fixed script on the true remote
HEAD passes. It looks like a live gate bug; it is a stale checkout, and it can flip a diagnosis back and forth.
Two fixes: (1) **fetch the base ref immediately before creating the worktree** (or hard-reset / rebase the
worktree onto the freshly-fetched remote ref before running any script); (2) for any check that must reflect
**current** remote / CI state — merge gates, required-check verification —
**query the forge/server API for the actual check-runs** — immune to local staleness — rather than trusting a
local script copy (the same "trusted evidence is a forge run pinned to the reviewed SHA" discipline in
`deep-code-review`'s `branch-and-merge-hygiene.md`). **🚩** an agent that infers "the gate is broken" from a
worktree without confirming its base ref is current; a merge or CI decision made from a local script in a
worktree of unknown freshness.

## Out-of-tree shared scratch crosses commit metadata — worktree-per-lane doesn't cover it

Concurrent write-lanes that each generate per-lane content — a commit-message file, a plan/notes file, a
screenshots / evidence dir — and write it to the **same hardcoded path in a shared temp/scratch directory**
collide: lane B overwrites lane A's file before lane A consumes it, so lane A commits with **B's message**
(`git commit -F <shared-path>`) or attaches the wrong note. Each branch's **code diff is correct**; only the
**metadata** is crossed — and metadata crossing is **invisible to a diff-scoped review**, which reads the tree,
not the message the tree ships under. The usual mitigations miss it: a git **worktree per lane** isolates the
branch, index, and deps, but a scratch path in a shared temp dir is **not part of any worktree**, and the
collision travels through `git commit -F <path>`, so "stage explicit paths, never `git add -A`" doesn't reach it
either.

- **Give every lane a unique scratch path** (suffix by lane id / worktree / PID), or keep per-lane content
  **inside the lane's own worktree**.
- **Verify metadata ownership, not just the diff** — before finalizing a lane, confirm the committed
  message/note belongs to *that* lane.
- **🚩 grep:** `git commit -F <path>` / `--file=<path>` where `<path>` is **fixed across lanes** (no lane-unique
  component), or multiple lanes referencing one hardcoded scratch/temp path for per-lane content.

Same root cause as `deep-code-review`'s `concurrency-shared-state.md` (two writers, one path) but where its
mitigations don't reach: **out-of-tree** scratch, and the corrupted thing is **commit metadata** a diff review
never sees.

## A worktree does not isolate repo-global refs — never bare `git stash` across lanes

A `git worktree` per lane isolates HEAD, the index, the working tree, and (with a copied deps dir)
`node_modules` — but **not** repo-global plumbing that lives in the one shared `.git`. `refs/stash` is the sharp
case: **`git stash` is a single repo-wide stack, not per-worktree**, so lane B's `stash push` and later `pop`
can consume or reorder an entry lane A pushed — silent cross-lane WIP loss, and the popped changes may not even
apply cleanly onto B's tree. (Other repo-global state — branches under `refs/`, config — shares the hazard; the
stash is just the one lanes reach for reflexively.) Never run a bare `stash push` / `stash pop` in a lane that
runs concurrently with siblings off the same repo: **commit-then-reset** onto the lane's own branch, use a
**second worktree** for throwaway state, or — if you must stash — use `git stash create` (it returns a
**dangling commit SHA** and never touches the shared `refs/stash` stack), record that SHA in a lane-private
file, and reapply with `git stash apply <sha>`. Avoid bare `stash push`/`pop` and `stash@{N}` **by index**
entirely: the index is positional on the shared stack, so a sibling's push between your lookup and your pop
shifts it and you pop the wrong entry — the same race, one level down. Complements the foreign-WIP rule below
(*don't stash another lane's uncommitted work*) with the deeper reason: the stash **stack itself** is shared, so
even your own push/pop is unsafe under concurrency.

## A worktree assignment is a path, not an adjective — an integrator on a shared branch detaches

Brief N lanes with *"work in an isolated worktree off `<branch>`"* and the phrase splits two ways: one lane
creates a fresh worktree, another reads it as *the* worktree where `<branch>` is already checked out and writes
straight into that tree. They never collide on a file — their file sets are disjoint — they collide on the
**tree**. The occupied tree then carries a second lane's *uncommitted* work, and the first lane's own gate trips
on it: a fully verified merge is blocked by a foreign half-written test file it must not touch. A git-diff
review sees nothing — the foreign edits are unstaged, so the committing lane's own diff is clean; the failure
surfaces only as a confusing unrelated test failure. And "just make your own worktree" fails for exactly the
lane that most needs one: `git worktree add <path> <branch>` **refuses a branch already checked out elsewhere**
(`fatal: '<branch>' is already used by worktree at …`), which is precisely the integrator's situation.

The topology is fixed: N lanes plus one integrator all want a checkout of the *same* integration branch — N+1
agents, one branch. State it explicitly, one line per brief:

- **Name the exact path; "isolated" is not an instruction.** The brief gives the path the lane creates
  (`<scratch>/wt-<lane>`), and the lane writes **only** under it. "An isolated worktree off X" is a hope; a path
  is an assignment.
- **The integrator folds in on a *detached* worktree.** `git worktree add --detach <path> <branch>` — detach at
  the **local** `<branch>` tip, not `origin/<branch>`: detaching does not occupy the ref, so it succeeds even
  though the branch is checked out elsewhere, and it lands on the verified local tip; `origin/<branch>` bases
  off the **stale** remote tip (dropping the merge you just verified) and does not exist at all for a local-only
  integration branch. Then merge the finished lane, verify, publish, and remove the worktree. A detached
  checkout is immune to the same-branch refusal above and cannot be squatted by a lane that believes it owns
  `<branch>`'s tree. How the result is *published* is a separate choice — a direct
  `git push origin HEAD:<branch>` from the detached tree, or a PR from the merged result — under whatever
  publish gate the project already applies (a push to a shared branch is itself an owner-approved action); the
  detach is what makes the *integration step* itself collision-proof either way.
- **Verify tree ownership before the first write.** `git status --short` in the target tree: if it shows changes
  the lane did not make, the tree is **occupied** — stop and report, do not write into it. Foreign dirt is an
  occupancy signal, not noise.
- **A gate failing on a file the lane never touched is the environment, not the code.** This is the collision
  twin of *a worktree's own gate can fire on a file it does not own* above: there the unowned file is a mirrored
  artifact, here it is another lane's uncommitted WIP — either way, re-run the gate in a clean or detached tree
  to tell an environment fault from a code fault before chasing a bug that does not exist.
- **Never resolve it by stashing.** `git stash` on another lane's uncommitted work removes it from that lane's
  tree silently and is unrecoverable from the lane's point of view — a data-loss fix for a coordination bug.
  Reassign the path instead.
- **A `git worktree add` failure is fail-loud, never a silent degrade to the shared tree.** Whatever the cause —
  the branch-in-use refusal above, disk, permissions, an unsupported git version — a write-lane that catches the
  error and keeps going by writing straight into the shared/main checkout trades an unannounced collision with the
  owner's or a sibling lane's tree for the honest option: report **BLOCKED: worktree creation failed — `<error>`**
  and stop; never retry into the shared tree as a fallback. If a step genuinely cannot avoid the shared tree, `git
  status --short` it first (as above): foreign lane WIP is still never stashed (the rule just above); the **owner's
  own** uncommitted work is preserved first with `git stash create` (the dangling-SHA, shared-stack-safe mechanic
  above), never a bare `stash push`, rather than left to be silently overwritten.
