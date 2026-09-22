# The unattended / autonomous operating mode

Read this when: an agent or a Conductor is granted a block of **unattended time to
work a backlog** — an overnight or multi-hour autonomous run — and needs the whole
run's shape: how the mode composes the other skills, the delivery loop it runs, the
run-start checklist and run-end self-audit that bound it, what "done" it may claim,
and the default set of recurring loops. This file **names and wires together**
doctrine that already lives in the sections it points to; it adds only the
connective mode-framing, the run-start/run-end gate, and the default loop set. It
does **not** restate the depth it routes to — follow the pointer.

This is **not a new runtime or a standing swarm** (`SKILL.md` intro) — it is how
the same opt-in, one-Conductor, hats-not-headcount pattern operates *as a loop*
while no human is watching. Every gate (G0–G10, Human gates, Gate epistemology)
still applies unchanged.

## The mode: a default loop, and stopping is the exception

An unattended grant is a **work loop over a ranked backlog, not a single task** —
the substance is `fast-agentic-delivery.md` **An unattended time budget is a work
loop, not a single task**. Frame it as the default stance:

- **Starting the loop never needs a reason; stopping does.** The loop runs until a
  **named termination condition** fires (backlog empty; every remaining item blocked
  on another party or on a Human gate; the granted window / appetite spent; a
  resource ceiling hit), each reported **with the evidence that it holds** — never a
  drift into silence. Depth + the four conditions: `fast-agentic-delivery.md` **An
  unattended time budget is a work loop** (termination-conditions bullet).
- **A go-faster tick is not a demand for busywork; holding can be correct.**
  `fast-agentic-delivery.md` **A go-faster signal fires on a clock, not on state**.
- **Measure delivery, not activity.** Report the **operator's own metric** and grade
  against durable output. Useful signals — **no** target thresholds (fabricated
  otherwise): merged-**to-default** per window, base-red **minutes-to-green**,
  **fix-forward share**. Routing: `fast-agentic-delivery.md` **Report the artifact,
  not the activity** and **reconcile status against the operator's open-issue
  metric**; DORA: `deep-code-review`'s `release-engineering.md`.

## What it composes (three skills, three gates, one bounded loop)

The mode is not new machinery — it is the suite's existing gates run continuously:

- **`idea-critic` = the decision gate.** Every non-trivial decision (an
  agent-originated approach, an A/B fork) is attacked before it is acted on, with
  **premises verified against live data, not memory** — `SKILL.md` G0/G1 + Gate
  epistemology principle 3 (a surprising conclusion re-fetches the state) and
  `fast-agentic-delivery.md` **A remembered constraint-state is a guess**.
- **`deep-code-review` = the review gate.** Independent of the builder at G6
  (`SKILL.md` Gates; `roles.md`).
- **`agentic-delivery` = the gated delivery.** G2–G8 with the Human gates intact.

The **bounded-and-reversible spine** holds throughout: every gate **fails closed**
(a gate that cannot run is `UNVERIFIED` / could-not-check, never a pass — `SKILL.md`
Gate epistemology principle 3), and nothing irreversible or outward happens without
the reversibility boundary or a human tap (`SKILL.md` **Human gates**).

## The delivery loop (five rungs — depth routed, not restated)

Each rung is a name and a pointer; the mechanism lives at the pointer.

1. **Keep the base green.** `fast-agentic-delivery.md` **A load-flaky required gate
   is not a confirmed red** + `deep-code-review` `branch-and-merge-hygiene.md` §5
   **Red base: discharge the deadlock with a train**; `SKILL.md` principle 3.
2. **Land every green PR** — a **single merge seat**, back-to-back inside one
   not-red window (default a small batch, ~3-ready), a **union-proven train** when
   members might interact. `fast-agentic-delivery.md` **Parallelizing the merge
   seat backfires**, **The window's admission check is not-red**, **An
   independent-PR-queue cascade is a cadence choice**; `SKILL.md` principle 6;
   `branch-and-merge-hygiene.md` §5 Merge trains.
3. **Turn red / conflicting PRs green by conflict TYPE, not file count** —
   already-applied vs diverged vs regenerable-artifact vs true textual conflict,
   each resolved by its type. `deep-code-review` `branch-and-merge-hygiene.md` §4
   decision tree, §5 Merge trains, §6 **Never hand-resolve a conflict inside a
   generated file**; the zero-checks / `mergeable_state` re-fire case is
   `fast-agentic-delivery.md` **Absent checks are a third state**.
4. **Deliver open issues in verify-first waves** — the fix may already be on the
   base. `fast-agentic-delivery.md` **An open tracker issue is not proof the fix is
   absent**, **reproduce an inbound bug on current HEAD**, **A hard-to-write test
   must not hold a ready fix hostage**.
5. **Fill to measured machine headroom** — free RAM + swap **trend**, not `load1`;
   spawn one, re-sample, keep a burst reserve; cheap read-only lanes effectively
   unbounded. `SKILL.md` **Environment probe** + `fast-agentic-delivery.md` **Gate
   on free RAM and the swap trend**.

**Two sequencing rules over the rungs:**

- **FREEZE-THEN-TRAIN** — while a resolver rebases a cluster against the base,
  freeze merges into that base and land only non-overlapping surgical merges
  meanwhile. `branch-and-merge-hygiene.md` §5 **freeze the sweep while a resolver
  runs**; `fast-agentic-delivery.md` **Parallelizing the merge seat backfires** and
  **An ownership map blocks a dual write, not dual work** (a shared artifact in
  flight blocks only the lanes that touch it).
- **SIZE-TO-MEASURED-HEADROOM-AND-SCALE-UP** — the ceiling is a **back-off trigger,
  not a licence to under-fill**; a chain of individually-correct holds must not
  ratchet the machine to idle. `fast-agentic-delivery.md` **The owner's message
  cadence is not the loop's clock**, **A chain of individually-correct holds can
  still drift the machine to idle**, and the free-RAM **veto, not a licence** rule.
  On a shared host, read the gates as **machine-wide aggregates**
  (`multi-session-coordination.md` **Every peer honoring its own heavy-lane cap
  still oversubscribes the machine**).

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
  compaction or reset loses nothing (`project-state.md`; `fast-agentic-delivery.md`
  **An unattended time budget is a work loop** and the ask-indexed read-first
  ledger bullet).
- **Concurrency cap** — sized from a live environment probe, not habit (`SKILL.md`
  **Environment probe**).
- **Wake model** — event-driven (task-notifications + a heartbeat), **no idle
  polling**; a monitor emits on transition only (`SKILL.md` **Conductor operating
  rhythm**; `fast-agentic-delivery.md` **A monitor emits on state-transition or
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

Depth: `fast-agentic-delivery.md` **If the loop is idling, say so loudly** (report
the window, not the item) and the honest-reporting ladder below.

## Honest reporting: running ≠ merged ≠ live

A proxy is never a completion claim. Keep the three rungs distinct, each verified
on its own surface:

- **running** — a spawned / computing lane is **not started** until it has a durable
  artifact (`fast-agentic-delivery.md` **Progress is a durable artifact, not a
  spawned lane**; `SKILL.md` **Failure** — a running lane is not a finished one).
- **merged** — integrated is G7, and a merge **off the default branch is
  done-in-tree but still open** (`SKILL.md` — *A work item's own completion is G7*;
  `fast-agentic-delivery.md` **An open tracker issue is not proof the fix is
  absent**).
- **live** — rendered on the owner's own surface and verified there, not inferred
  (`SKILL.md` Gate epistemology principle 11; G9).

## The default loop set (distinct loops at offset cadences)

The genuinely-new **architecture**: run a set of **distinct recurring loops at
offset cadences** so one stalled thread never stalls delivery — a stalled producer
must not hold up merges, a stalled merge must not hold up hygiene. A cadence is the
**maximum latency before that thread is re-checked, not the work quantum**: on any
wake, take **every** currently-admissible action of that loop's kind before ending
the turn — never one action per tick (`fast-agentic-delivery.md` **A loop's own
wake/poll cadence is not the work cadence**). A worked default set:

| Loop | Cadence | On each wake (routed rule) |
|---|---|---|
| PUSH | ~10m | push ready branches / open PRs — **Progress is a durable artifact, not a spawned lane** |
| MERGE / train-drain | ~15m | single-seat drain of the green queue — **Parallelizing the merge seat backfires**; **A serial queue-drainer must advance past a blocked head** |
| PRODUCER | ~15m (phase-offset from MERGE) | pull the next backlog wave, verify-first — **An open tracker issue is not proof the fix is absent** |
| HYGIENE | ~30m | worktree / process reaping, stale-claim reconcile — **A worktree is a resource with a lifecycle** |
| QUALITY / UX-VERIFY | ~20m | central browser / UX verification of landed UI — **Draft-gated heavy checks hide a UI-regression wave** |
| LEARNINGS | ~2/hr | capture standing findings as tracked items — **Research is not delivery**; `SKILL.md` G10 |

- **Same-period loops carry an explicit phase offset** (MERGE and PRODUCER both
  ~15m wake roughly 7m apart) so they do not land on one tick; when loops *do*
  co-fire, **consolidate the fires into one reconciliation pass**
  (`fast-agentic-delivery.md` **A go-faster signal fires on a clock** — the
  multiple-loops-compound / consolidate-overlapping-fires paragraphs).
- **Add a non-overlapping loop rather than raise a loop's frequency** to close a
  gap; the operator-visible loop set is **add-only** unless a decrement is named
  (`fast-agentic-delivery.md` **The loop set is add-only when the operator asked
  for "more"**).
- A degradation workaround inside any loop is **temporary by default** — tie its
  removal to the blocker clearing (`fast-agentic-delivery.md` **A degradation
  workaround is temporary by default**).

## The Human-gate boundary (unchanged)

The mode changes **what stopping requires a reason for**, never **what needs a
human**. An item whose next step is a Human gate (push, merge, deploy, external
send, secret / scope change) is a **termination condition to queue, not a task to
self-authorize** — surface a one-action, self-updating human escape hatch up front
rather than narrating "holding". The autonomous **PUSH** and **MERGE** loops above
are the un-gated half only — a lane's own **feature-branch** push and the **G7
integration** merge; a **shared-branch** push, a **merge-to-default**, a deploy, or
an external send stays a Human gate, and a loop only schedules the re-check — it
never authorizes a gated action. `SKILL.md` **Human gates**;
`fast-agentic-delivery.md` **When no autonomous path exists, surface the human-run
escape hatch** and the termination-conditions bullet. Never silently reverse a
dated / ratified decision (`SKILL.md` Gate epistemology principle 12).

## Less talk, more work

Default to **one line per material landing**, no status essays; raise verbosity
only when the operator cannot otherwise see enough. An idle loop still **says so
loudly** — silence reads as working. `communication-structure` (BLUF);
`fast-agentic-delivery.md` **Report the artifact, not the activity** and **If the
loop is idling, say so loudly**.

## Cross-references

- `SKILL.md` — Gates (G0–G10), Human gates, Gate epistemology (principles 3, 6,
  11, 12), Environment probe, Conductor operating rhythm: the invariants this mode
  runs as a loop.
- `references/fast-agentic-delivery.md` — the concurrency, merge-cadence,
  work-loop, and reporting depth every rung and loop above points into.
- `references/multi-session-coordination.md` — when the unattended run is one of
  several peer sessions on a shared host / account.
- `references/project-state.md` — the durable backlog / ask-ledger the run-start
  checklist requires.
- `deep-code-review`'s `branch-and-merge-hygiene.md` — the conflict-classification,
  merge-train, and red-base mechanics rung 3 and FREEZE-THEN-TRAIN route to;
  `release-engineering.md` — the review-side delivery-metric (DORA) depth.
