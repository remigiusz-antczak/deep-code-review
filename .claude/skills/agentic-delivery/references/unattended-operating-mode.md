# The unattended / autonomous operating mode

Read this when: an agent or a Conductor is granted a block of **unattended time to
work a backlog** — an overnight or multi-hour autonomous run — and needs the whole
run's shape: how the mode composes the other skills, the delivery loop it runs, the
run-start checklist and run-end self-audit that bound it, what "done" it may claim,
the default set of recurring loops, and the churn / priority-inversion / owner-focus gates. This
file **names and wires together** doctrine that already lives in the sections it
points to; it adds only the connective mode-framing, the run-start/run-end gate,
the default loop set, and the routing to the gate scripts. It does **not**
restate the depth it routes to — follow the pointer.

This is **not a new runtime or a standing swarm** (`SKILL.md` intro) — it is how
the same opt-in, one-Conductor, hats-not-headcount pattern operates *as a loop*
while no human is watching. Every gate (G0–G10, Human gates, Gate epistemology)
still applies unchanged.

## The mode: a default loop, and stopping is the exception

An unattended grant is a **work loop over a ranked backlog, not a single task** —
the substance is `unattended-trackers.md` **An unattended time budget is a work
loop, not a single task**. Frame it as the default stance:

- **Starting the loop never needs a reason; stopping does.** The loop runs until a
  **named termination condition** fires (backlog empty; every remaining item blocked
  on another party or on a Human gate no owner-authored standing grant covers
  (`SKILL.md` **Human gates**); the granted window / appetite spent; a
  resource ceiling hit), each reported **with the evidence that it holds** — never a
  drift into silence. Depth + the four conditions: `unattended-trackers.md` **An
  unattended time budget is a work loop** (termination-conditions bullet).
- **A go-faster tick is not a demand for busywork; holding can be correct.**
  `unattended-trackers.md` **A go-faster signal fires on a clock, not on state**.
- **A question for an absent owner is deferred, not waited on.** Record it with
  `agentic-ceo/scripts/task_ledger.py defer --id T-### --question "<q>"`. A
  reversible choice takes a default (`--default "<choice>"`), stated in the
  handback. A Human gate (shared push, deploy, external send, secret/scope
  change) or a destructive/irreversible choice without an owner-authored
  standing grant: never default, always `--park`. Parking blocks that one item,
  not the run; `unblock` is refused until `answer` records the reply. Continue
  with `task_ledger.py next`, which skips parked items. The owner gets one batch
  from `task_ledger.py questions` and can still stop the run or answer at any
  time. Optional hooks (a model-visible turn-start line, an owner notice on
  `Stop`): `host-enforcement.md` **Deferred-question hooks**.
- **Measure delivery, not activity.** Report the **operator's own metric** and grade
  against durable output. Useful signals — **no** target thresholds (fabricated
  otherwise): merged-**to-default** per window, base-red **minutes-to-green**,
  **fix-forward share**. Routing: `fanout-host-sizing.md` **Report the artifact,
  not the activity** and `unattended-trackers.md` **reconcile status against the
  operator's open-issue metric**; DORA: `deep-code-review`'s `release-engineering.md`.

## What it composes (three skills, three gates, one bounded loop)

The mode is not new machinery — it is the suite's existing gates run continuously:

- **`idea-critic` = the decision gate.** Every agent-originated approach choice
  (a new approach, an A/B fork) is attacked before it is acted on — not routine
  execution or gate confirmations (`idea-critic` **Don't use for**) — with
  **premises verified against live data, not memory** — `SKILL.md` G0/G1 + Gate
  epistemology principle 3 (a surprising conclusion re-fetches the state) and
  `fanout-host-sizing.md` **A remembered constraint-state is a guess**.
- **`deep-code-review` = the review gate.** Independent of the builder at G6
  (`SKILL.md` Gates; `roles.md`).
- **`agentic-delivery` = the gated delivery.** G2–G8 with the Human gates intact.

The **bounded-and-reversible spine** holds throughout: every gate **fails closed**
(a gate that cannot run is `UNVERIFIED` / could-not-check, never a pass — `SKILL.md`
Gate epistemology principle 3), and nothing irreversible or outward happens without
the reversibility boundary or a human tap (`SKILL.md` **Human gates**).

## The delivery loop (five rungs — depth routed, not restated)

Each rung is a name and a pointer; the mechanism lives at the pointer.

1. **Keep the base green.** `merge-queue-worktrees.md` **A load-flaky required gate
   is not a confirmed red** + `deep-code-review` `merge-operations.md`
   **Red base: discharge the deadlock with a train**; `SKILL.md` principle 3.
2. **Land every green PR** — a **single merge seat**, back-to-back inside one
   not-red window (default a small batch, ~3-ready), a **union-proven train** when
   members might interact. `merge-queue-worktrees.md` **Parallelizing the merge
   seat backfires**, **The window's admission check is not-red**, **An
   independent-PR-queue cascade is a cadence choice**; `SKILL.md` principle 6;
   `merge-operations.md` Merge trains.
3. **Turn red / conflicting PRs green by conflict TYPE, not file count** —
   already-applied vs diverged vs regenerable-artifact vs true textual conflict,
   each resolved by its type. `deep-code-review` `branch-and-merge-hygiene.md` §4
   decision tree, `merge-operations.md` **Never hand-resolve a conflict inside a generated file**;
   `merge-operations.md` **Merge trains**; the zero-checks / `mergeable_state` re-fire case is
   `merge-queue-worktrees.md` **Absent checks are a third state**.
4. **Deliver open issues in verify-first waves** — the fix may already be on the
   base. `unattended-trackers.md` **An open tracker issue is not proof the fix is
   absent**, **reproduce an inbound bug on current HEAD**; `verification-handback.md`
   **A hard-to-write test must not hold a ready fix hostage**.
5. **Fill to measured machine headroom** — free RAM + swap **trend**, not `load1`;
   spawn one, re-sample, keep a burst reserve; cheap read-only lanes effectively
   unbounded. `SKILL.md` **Environment probe** + `fanout-host-sizing.md` **Gate
   on free RAM and the swap trend**.

**Two sequencing rules over the rungs:**

- **FREEZE-THEN-TRAIN** — while a resolver rebases a cluster against the base,
  freeze merges into that base and land only non-overlapping surgical merges
  meanwhile. `merge-operations.md` **freeze the sweep while a resolver
  runs**; `merge-queue-worktrees.md` **Parallelizing the merge seat backfires** and
  `dev-env-ownership.md` **An ownership map blocks a dual write, not dual work** (a shared artifact in
  flight blocks only the lanes that touch it).
- **SIZE-TO-MEASURED-HEADROOM-AND-SCALE-UP** — the ceiling is a **back-off trigger,
  not a licence to under-fill**; a chain of individually-correct holds must not
  ratchet the machine to idle. `unattended-trackers.md` **The owner's message
  cadence is not the loop's clock**, **A chain of individually-correct holds can
  still drift the machine to idle**, and `fanout-host-sizing.md`'s free-RAM **veto,
  not a licence** rule.
  On a shared host, read the gates as **machine-wide aggregates**
  (`multi-session-coordination.md` **Every peer honoring its own heavy-lane cap
  still oversubscribes the machine**).

## Two mechanical gates on what the loop ships: churn and priority inversion

A loop graded on activity drifts to cheap, visible work. One private audit
(generalized): 86% of commits reworked earlier work, 26 files were fixed ten or
more times at a median 22.5 h apart, and presentation PRs rose to 48% while
feature work fell to 9%, with every P0 / mechanism issue still open and cited by
zero PRs. Attention caught neither drift. Two opt-in stdlib gates make each a
blocking fact (`--selftest`; fail closed on unresolvable input; wired into a
target's CI behind env flags by `deep-code-review`'s `templates/dcr-gates.sh`):

- `scripts/refix_gate.py` — **use this when** a lane re-touches a file a recent
  `fix:` commit touched. A range doing so inside `--window-hours` (default 72)
  must add a test/eval path matching `--class-glob` or carry a `Refix-Reason:`
  trailer; output names the file, prior fix SHA, and age. It forces a
  class-level artifact to exist; it cannot judge class completeness (that stays
  the reviewer's — `deep-code-review` `method.md`, class discipline).
- `scripts/priority_gate.py` — **use this when** ordering dispatch or reviewing a
  presentation PR (by label, or every path matching a presentation glob). It
  fails that PR while any P0 / mechanism issue older than `--min-age-hours` has
  no other open or merged PR citing it; `--budget` caps the presentation share of the
  last 24 h of merges. Pure over a JSON document (`--labels-json`), or fetched by
  paginated `gh api` (`--repo`). It proves a citing PR exists, not that the PR
  advances the issue.

## An open owner priority outranks every other item

Fleets left the owner's main priority before it was done: every move-on rule —
*pull the next item*, *self-source rather than stop*, refill an idle slot, the
go-faster tick, *every remaining item blocked* — read as permission to leave it.
This section is the one binding over all of them (`unattended-trackers.md`
defers here):

- **An OPEN owner priority outranks every other item** — backlog rank, a
  self-sourced finding, a cheap cosmetic fix. "The next item" means the next
  item **inside its scope**.
- **Work outside it only when it is DONE or BLOCKED.** DONE = the owner's
  acceptance command exits 0 on a clean checkout, never a lane's "mostly done".
  BLOCKED = an owner-accepted row naming **another party** plus an evidence
  link; a hard sub-problem or a red test is not a blocker. Neither → keep at it
  (split, re-approach, spike) and report OPEN with the acceptance output.
- **The record is owner-authored** — the owner's own commit to
  `.claude/PRIORITY.md`, the standing-grant rule (`SKILL.md` **Human gates**).
  An agent never creates, widens, narrows, closes, or deletes it; a change is an
  ask.
- **Design alignment is done** only when `deep-code-review`'s parity differ
  reports inventory MATCH for every in-scope screen (`rendered-parity.md`) —
  never a size, height, or screenshot judgement. That is its acceptance command.
- `scripts/focus_gate.py` — **use this when** picking the next item, dispatching,
  or reviewing a change. `status` prints state and evidence; `check` (item,
  paths, or commit range) is NO-GO outside scope while OPEN. Fails closed: a
  non-owner record or deletion, a `**` scope, or a trivially-true acceptance is
  never DONE; no record ever → GO with a notice. CI: `DCR_FOCUS_GATE=1`
  (`dcr-gates.sh`).

## The run-lifecycle gate: a run-start checklist and a run-end self-audit

This is the genuinely-new normative addition — everything the items reference
exists; the **bundling into a run-lifecycle gate** is what this section adds.

**Run-start checklist** (before the first lane; each unset item fails the start
closed):

- **Spend ceiling** — a per-lane token / dollar budget for any paid call; a lane
  with a paid call and no budget is **BLOCKED, not unlimited** (`SKILL.md` G2; "we
  will watch it" is not a budget).
- **Reversibility boundary** — the actions that need a human tap, restated for
  this run (`SKILL.md` **Human gates**).
- **Durable state confirmed** — the ranked backlog **and** the ask-ledger (one row
  per owner request) live in a file / tracker, never only in scrollback, so a
  compaction or reset loses nothing (`project-state.md`; `unattended-trackers.md`
  **An unattended time budget is a work loop** and the ask-indexed read-first
  ledger bullet).
- **Concurrency cap** — sized from a live environment probe, not habit (`SKILL.md`
  **Environment probe**).
- **Wake model** — event-driven (task-notifications + a heartbeat), **no idle
  polling**; a monitor emits on transition only (`SKILL.md` **Conductor operating
  rhythm**; `unattended-trackers.md` **A monitor emits on state-transition or
  terminal state only** and **A loop's own wake/poll cadence is not the work
  cadence**).

**Run-end self-audit** (at every termination and at hand-off):

- **What landed** — on the **canonical surface** (merged-to-default SHA or a live
  URL), never a proxy.
- **What is staged / in-flight** — pushed branches, open PRs.
- **What is blocked, and on whom** — each owner-gated next step named.
- **Spend used vs the ceiling.**
- **Net removal vs a protected baseline** — the checks above measure
  activity, not value; diff the run's cumulative surface and data inventory
  against a committed must-keep baseline each cycle, and flag a cycle that
  removed more than it added as a regression to reverse, not progress to
  report — removal needs a logged acknowledgement, never a silent side effect.

Depth: `unattended-trackers.md` **If the loop is idling, say so loudly** (report
the window, not the item) and the honest-reporting ladder below.

## Honest reporting: running ≠ merged ≠ live

A proxy is never a completion claim. Keep the three rungs distinct, each verified
on its own surface:

- **running** — a spawned / computing lane is **not started** until it has a durable
  artifact (`unattended-trackers.md` **Progress is a durable artifact, not a
  spawned lane**; `SKILL.md` **Failure** — a running lane is not a finished one).
- **merged** — integrated is G7, and a merge **off the default branch is
  done-in-tree but still open** (`SKILL.md` — *A work item's own completion is G7*;
  `unattended-trackers.md` **An open tracker issue is not proof the fix is
  absent**).
- **live** — rendered on the owner's own surface and verified there, not inferred
  (`SKILL.md` Gate epistemology principle 11; G9).

## The default loop set (distinct loops at offset cadences)

The genuinely-new **architecture**: run a set of **distinct recurring loops at
offset cadences** so one stalled thread never stalls delivery — a stalled producer
must not hold up merges, a stalled merge must not hold up hygiene. A cadence is the
**maximum latency before that thread is re-checked, not the work quantum**: on any
wake, take **every** currently-admissible action of that loop's kind before ending
the turn — never one action per tick (`unattended-trackers.md` **A loop's own
wake/poll cadence is not the work cadence**). A worked default set:

| Loop | Cadence | On each wake (routed rule) |
|---|---|---|
| PUSH | ~10m | push ready branches / open PRs — **Progress is a durable artifact, not a spawned lane** |
| MERGE / train-drain | ~15m | single-seat drain of the green queue — **Parallelizing the merge seat backfires**; **A serial queue-drainer must advance past a blocked head** |
| PRODUCER | ~15m (phase-offset from MERGE) | pull the next backlog wave (an OPEN owner priority's scope first), verify-first — **An open tracker issue is not proof the fix is absent** |
| HYGIENE | ~30m | worktree / process reaping, stale-claim reconcile — **A worktree is a resource with a lifecycle** |
| QUALITY / UX-VERIFY | ~20m | central browser / UX verification of landed UI — **Draft-gated heavy checks hide a UI-regression wave** |
| LEARNINGS | ~2/hr | capture standing findings as tracked items — **Research is not delivery**; `SKILL.md` G10 |

- **Same-period loops carry an explicit phase offset** (MERGE and PRODUCER both
  ~15m wake roughly 7m apart) so they do not land on one tick; when loops *do*
  co-fire, **consolidate the fires into one reconciliation pass**
  (`unattended-trackers.md` **A go-faster signal fires on a clock** — the
  multiple-loops-compound / consolidate-overlapping-fires paragraphs).
- **Add a non-overlapping loop rather than raise a loop's frequency** to close a
  gap; the operator-visible loop set is **add-only** unless a decrement is named
  (`unattended-trackers.md` **The loop set is add-only when the operator asked
  for "more"**).
- A degradation workaround inside any loop is **temporary by default** — tie its
  removal to the blocker clearing (`unattended-trackers.md` **A degradation
  workaround is temporary by default**).

## A loop that duplicates another loop's scope is a design defect — collapse it, don't stagger it

Phase offsets and fire-consolidation fix loops that land on the same tick, not
loops that sweep the same scope at different cadences: every wake past the
tightest one is a guaranteed no-op that still burns a full sweep. Run that scope
at its own tightest useful cadence and drop the duplicates at design time. The
add-only policy (`unattended-trackers.md` **The loop set is add-only when the
operator asked for "more"**) does not protect them: a same-scope duplicate was
never a separate job.

## A stuck trivial change gets one recovery attempt, then is recorded and passed — never a nursing loop

**A small change failing to commit/push on an environment issue (a hung hook, a
missing binary, a worktree race) gets exactly one recovery attempt from the main
loop; on a repeat failure, record the item (ledger / state record: what, the
failing command as evidence, the next step) and move to the next item — never
another retry, never silently drop.** A fault that blocks every commit (a hung
hook) is systemic: escalate it as a blocker with one root-cause lane, not a
per-item skip. The original failure plus the recovery are `SKILL.md`
**Failure**'s two equivalent failures; the recorded item satisfies the logged
acknowledgement the run-end self-audit requires. Same bound as
`verification-handback.md` **Bound every flaky finalize step**, applied to the
loop's own commit/push; recovery spend must not exceed the change's worth.

## The Human-gate boundary (unchanged)

The mode changes **what stopping requires a reason for**, never **what needs a
human**. An item whose next step is a Human gate (push, merge, deploy, external
send, secret / scope change) is **parked, not self-authorized**, and the loop
continues on the rest — surface a one-action, self-updating human escape hatch up
front rather than narrating "holding". The autonomous **PUSH** and **MERGE** loops
above are the un-gated half only — a lane's own **feature-branch** push and the
**G7 integration** merge. A **shared-branch** push or a **merge-to-default**
stays a Human gate unless an owner-authored standing grant covers it — never one
the agent wrote, widened, or re-dated, and never a merge that triggers deploy or
publish; a deploy or an external send stays gated always (`SKILL.md` **Human gates**);
`merge-queue-worktrees.md` **When no autonomous path exists, surface the human-run
escape hatch** and `unattended-trackers.md`'s termination-conditions bullet. Never silently reverse a
dated / ratified decision (`SKILL.md` Gate epistemology principle 12).

## Less talk, more work

Default to **one line per material landing**, no status essays; raise verbosity
only when the operator cannot otherwise see enough. An idle loop still **says so
loudly** — silence reads as working. `communication-structure` (BLUF);
`fanout-host-sizing.md` **Report the artifact, not the activity** and
`unattended-trackers.md` **If the loop is idling, say so loudly**.

## Cross-references

- `SKILL.md` — Gates (G0–G10), Human gates, Gate epistemology (principles 3, 6,
  11, 12), Environment probe, Conductor operating rhythm: the invariants this mode
  runs as a loop.
- `references/fast-agentic-delivery.md` — the index of the five themed lesson
  files (concurrency, merge cadence, verification, ownership, work loop) every
  rung and loop above points into.
- `references/multi-session-coordination.md` — when the unattended run is one of
  several peer sessions on a shared host / account.
- `references/project-state.md` — the durable backlog / ask-ledger the run-start
  checklist requires.
- `deep-code-review`'s `branch-and-merge-hygiene.md` + `merge-operations.md` — the conflict-classification,
  merge-train, and red-base mechanics rung 3 and FREEZE-THEN-TRAIN route to;
  `release-engineering.md` — the review-side delivery-metric (DORA) depth.
