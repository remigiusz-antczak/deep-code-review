# Fast agentic delivery — unattended mode and tracker hygiene

Read this when: deciding whether an open issue's fix is absent, placing an auto-close keyword or a gate-parsed
PR-body marker, closing an issue, stating a fan-out ETA, or running an unattended work loop (termination
conditions, go-faster ticks, monitors, the loop set, degradation workarounds, research vs delivery, terminus across
every queue, surface enumeration). Part of the `fast-agentic-delivery.md` lesson ledger — its index, sources, and
cross-references live there; an "above"/"below" pointer to a section not in this file resolves through that index.

---

## An open tracker issue is not proof the fix is absent — auto-close is default-branch-only

An issue's **OPEN** state is not evidence its fix is missing from the tree. Native auto-close fires narrowly:
GitHub closes a linked issue only "when you merge a linked pull request into the **default branch**," and the
`Closes #N` / `Fixes #N` / `Resolves #N` keywords are "interpreted only when the pull request targets the
repository's default branch." A fleet that merges day-to-day into a long-lived integration branch (`develop`,
`release/*`) running ahead of the default branch therefore accumulates issues that are
**done in the tree, open in the tracker** — the `Closes #N` was present and correct, but the branch it merged
into left it inert. Once "open" no longer means "not done," the queue stops being a source of truth: agents
re-pick shipped work and a coordinator's "what is left?" count is wrong.

Reading "open" as "not done" opens a lane to redo finished work — the duplicate-work failure one level up from
re-searching for code already present (*An ownership map blocks a dual write*, above).
**Before opening a fix lane for a tracked issue:**
- **Read the issue's comments, not just its title, body, and labels.** A later owner comment — an A/B decision,
  a narrowed scope, a "defer this," a repro correction, a "superseded by #M" — outranks the original body, and
  buildability and priority often live **only** in that thread. Classifying from body + labels alone re-opens a
  lane the owner already redirected or resolved in discussion, spending it on an unwanted or wrong-scoped change
  (`gh issue view <n> --comments`).
- **Reproduce the bug on the current integration HEAD before writing a fix.** An inbound bug report is a claim
  about a *past* build — a stale deploy, a cached bundle, or a report filed before an intervening fix merged.
  Reproduce the symptom against current HEAD first; one you cannot reproduce may already be fixed (grep for the
  guarding test / changed symbol, below) or be environment-specific — building a fix for a bug that no longer
  exists on HEAD is wasted work and a spurious diff. (Generalizes this section to *any* inbound bug: the trigger
  is deploy/report lag, not only off-default merges.)
- **Grep the branch you would actually base the fix on** — the integration branch, not just the default branch
  or the issue's state — for the fix's landmark: the changed symbol, the line, or the regression test that
  guards it (the grep-the-tree-not-the-claim check `deep-code-review` `branch-and-merge-hygiene.md` applies to
  "B included A", here run pre-laning).
- **Know the forge's auto-close scope** (`Closes #N` = default branch only) and cross-reference the integration
  branch's commit log and its merged PRs.
- **If the fix is already on the integration branch, stop.** Report "already delivered" with `file:line` + the
  commit SHA, and note it is on the integration branch but not yet on the default branch — so the open issue is
  *expected*, not a to-do. Do **not** re-lane. Do **not** hand-close it either — "done" means merged to the
  default branch. And do **not** assume promotion will close it: the original `Closes #N` was inert (it did not
  target the default branch), and a plain integration→default promotion PR carries no per-issue keyword, so
  nothing auto-closes on convergence — the issue closes only when a keyword-linked PR reaches the default
  branch, or via the supplied close step below. A wrong hand-close is silent tracker data-loss: skip rather than
  guess.

A team that merges off-default and wants a truthful queue must **supply** the close step native auto-close will
not: a scoped automation that, on a PR *merged* into the staging branch, closes only the issues that PR
*explicitly* linked with the keyword syntax — never a name / branch / title heuristic (a wrong auto-close is
silent tracker data-loss), least-privilege issue-write, idempotent. Building that automation is project tooling
and owner-gated; naming the discipline is not.

**Even before that automation exists, reconcile what you *report* against the operator's metric.** Their
headline number is usually the tracker's **open-issue count**, not the agent's own visible proxy (PRs merged) —
and the two diverge silently under this exact pattern: dozens of real merges can leave the open count **flat**,
reading as *stalled* to an operator who escalates ("why are you slow?") while the code is fine. Distinct from
*report the artifact, not the activity* above: there the proxy is the orchestrator's own busyness (N lanes
running); here the proxy is a real, landed outcome that simply isn't the number the operator tracks. State the
**operator's own metric** in every status line, not the proxy, and name the gap in one line when they diverge
("N merged to `<integration-branch>`, open count unchanged — auto-close is default-branch-only"). Run that
reconciliation **continuously**, the same byte-exact-per-issue discipline as the *already-delivered* report
above — not only at the eventual default-branch promotion, which leaves the queue reading false until then.

## The auto-close keyword fires on merge — do not write it where the issue should stay open

The section above governs a keyword that was **correct but inert** (a `Closes #N` that merged off the default
branch, so the issue is done-in-tree yet open). This is the mirror: the keyword **fires when it should not**,
silently closing an issue the merge does not actually complete. Two ways it over-fires:

- **The PR only partly advances the issue, or the issue is an umbrella/epic with open children.** A keyword
  closes the *whole* referenced issue on merge, so `Closes #N` on a parent buries its still-open sub-work. Use a
  **non-keyword** reference for anything the PR does not fully satisfy — `Part of #N`, `Advances #N`, `Re #N`
  link without closing. Reserve `Closes` / `Fixes` / `Resolves #N` for an issue whose acceptance **is** "this
  change, merged" (a G7-closeable work item — `SKILL.md`, *A work item's own completion is G7*; whether the
  feature is actually observable in production is a separate, later check at **G9**, not a reason to hold the
  ticket open). This does **not** license parking a G7-complete item as "blocked on deploy": when merge *is* the
  acceptance, close it and name G8 downstream. The over-close rule is about issues the merge genuinely leaves
  unfinished, not about deferring closable ones.
- **Treat the close keyword as textual — a mention may fire it.** GitHub's own docs do not specify whether the
  keyword is position-aware, and it is **widely observed** to match anywhere in the PR body or a commit message
  — inside a quote, a code fence, or a sentence *explaining* a defect (this suite hit it: a `Closes #N` quoted
  in a PR body to describe a bug auto-closed the issue it described). Since the docs will not promise it *won't*
  match a mention, treat any such keyword+number as live wherever it appears: keep it out of any body or commit
  unless you intend the close, and phrase around it otherwise (*the auto-close of #N*, *issue N*, split the `#`)
  — the same reflex a log line uses to describe a secret without printing a live one.

## A gate-parsed PR-body marker must be its own line — bury it in prose and a true claim still fails closed

A gate that greps the PR body for a specific marker (`No UX change: <reason>`, an explicit opt-out, a required
acknowledgment) typically requires the marker as a **standalone line** — a fixed prefix at line-start — not a
substring match anywhere in the text. A lane that states the same fact honestly but buries it mid-sentence
inside a BLUF paragraph ("since this PR only touches the retry constant, no UX change occurred here") gives the
gate nothing to match: the check looks for the **line shape**, not the semantic claim, so a **true** statement
of intent still reads as absent and the gate fails closed on a diff that never needed the UX-evidence path at
all. Distinct from #968's evidence-rendering gate (a screenshot or source that must actually **render** for the
reviewer, not merely exist) and from *a completion claim ... carries a `Verify:` line* above (evidentiary
sufficiency for a claim of **verified work**): this marker asserts no work was needed in the first place, and
the defect is **position/format**, not substance — the claim was true and stated, just unparseable by the check
reading it.

- **Brief every lane on the marker's exact required shape** — the literal prefix, on its own line, as a full
  sentence (`No UX change: <reason>`, not "no UX change here since…") — whichever gate in `roles.md`'s
  UX-evidence row or an equivalent project convention defines it.
- **Run the gate's own checker against the drafted body before marking the lane ready**, not after CI reds it —
  a body-format gate is cheap enough to run pre-flight, and a red discovered post-CI for a purely-textual miss
  is a wasted round trip the lane could have caught itself.
- **Generalizes to any gate that parses a structured marker out of free-form PR/commit text** — a co-author
  trailer, an opt-out flag, a required acknowledgment line: the shared failure is a **grep-shaped** check
  reading **prose-shaped** input.
- **Corollary, same "the gate — or the reader — only sees the literal surface" root cause:** a bare
  `raw.githubusercontent.com` image link in a PR body renders for the author (authenticated) and 404s for anyone
  else on a private repo; embed a repo-relative, **committed** path instead so the evidence renders for every
  reviewer, not only whoever was logged in when they clicked it.

**🚩 tell:** a gate-required marker present **somewhere** in the PR body — inside a paragraph, a quote, a code
fence — but never as the standalone line the check actually greps for, discovered only after CI reds a diff
whose intent was correctly stated in prose.

## Before closing an issue, verify every acceptance criterion against live code — not one representative check

The two keyword rules above govern *when* the tracker closes; this governs *whether it should*. Before a manual
or agentic `gh issue close` (or a `Closes #N` you intend to fire), enumerate **every** acceptance criterion the
issue states and verify **each** independently against the merged source — a `file:line` receipt per criterion,
not one representative check the issue's other criteria then ride on. A multi-criterion issue closed on a single
confirmed criterion silently drops the rest: they are now neither open (visible as a to-do) nor done (actually
shipped). If any criterion is unmet, leave the issue open with a named per-criterion gap ("1 and 3 shipped at
`file:line`; 2 not yet") or split it. This is the close-side companion to the review method's
*Intent-conformance* lens (`deep-code-review` `method.md`) and to grep-the-tree-not-the-claim
(`branch-and-merge-hygiene.md`). Verifying the criteria settles *whether* to close; it does not override *when*
— "done" still means merged to the **default branch** (the inert-keyword section above), so a fix that landed
only on an off-default integration branch stays open even with every criterion met.

## An ETA on a fan-out states its parallelism assumption — a serial estimate on parallel lanes is a fabrication

An estimated completion time for a multi-lane plan is meaningless without the assumption under it: "done in 20
minutes" assuming N lanes run in parallel is off by about N× when a resource cap (RAM, token budget, one CI slot
— the same ceilings that size the fan-out above) forces them serial. State three things with any fan-out ETA —
the **parallelism assumption** (N in parallel, or sequential), the **constraint that caps it**, and, when that
constraint is uncertain, both the **parallel-optimal and serial-fallback** numbers. A one-number ETA with an
unstated parallelism assumption is unearned precision: the owner schedules against it and is wrong, the same
over-claim as a status that names no surface. Prefer a stated **appetite** — a time-box the work is shaped to
fit (`SKILL.md` G0) — over a bare estimate wherever the work can be shaped.

## An unattended time budget is a work loop, not a single task — a milestone is not a stop

An agent holding a block of unattended time *to work a backlog* treats the *first* milestone it reaches — a
deliverable merged, the item it was pointed at finished — as the end of the assignment, goes quiet, and leaves
the rest of the granted window unspent. The grant was a loop; that milestone was one turn of it. Read a time
budget as *work the ranked backlog until a termination condition fires*, not *do the one thing, then wait*.
Every move-on rule here and in the next two sections yields to an OPEN owner priority:
`unattended-operating-mode.md` **An open owner priority outranks every other item**.

- **Keep the backlog outside the working context.** A ranked list of what to do next lives in a file or a
  tracker — not only in the conversation, which a compaction or a handoff can drop. The
  **queue-a-requirement-to-a-file** rule above is this same discipline applied to *incoming* scope; this applies
  it to the *standing* backlog.
- **Read a delta since the loop's own last tick by default, not the full tracker.** A recurring loop that
  re-reads the whole backlog/state file in full on every tick pays that cost every cycle regardless of how much
  changed, so token spend scales with tick-frequency × context-size rather than with actual new information. One
  observed run: a loop ticking every few minutes re-read a multi-thousand-line state file in full each time;
  across a day the cumulative re-read volume was many times the size of the actual changes made that day. Read
  what changed in the backlog or what new events arrived since the loop's own last tick instead. Reserve a
  **full** re-read for session start, a detected large gap (several missed ticks), a compaction, a handoff, any
  stop/idle/"all blocked" claim, or an explicit re-sync request — never the steady-state per-tick default. Where
  no delta mechanism exists yet, name that as a gap to fix, not a reason to keep re-reading in full. *Worked
  example:* a loop switched from re-reading its multi-
  thousand-line tracker in full on every tick to reading only the rows changed since its last recorded
  tick-timestamp — same tick cadence, a fraction of the read volume; the resulting spend reduction was not
separately measured, so state the change, not a number.
- **Index the backlog by the owner's ask, and answer "what's left" by reading it — never by reconstructing from the transcript.**
  The file above is a ranked *work* list; a long or unattended session also needs it to carry the **ask-set** —
  one row per distinct owner request (id, ask, status, evidence, next action) — updated **at each milestone**,
  not only at the end. When the owner asks "what's remaining" (often after a gap), the answer is
  *read the ledger*, answerable in one or two tool calls — not an O(N) re-scan of hundreds of turns that
  silently re-litigates settled items. A row is *done* only when its evidence points at the
  **canonical surface** — a merged-to-default SHA or a live URL — not a branch that merely contains the fix
  (`project-state.md`'s Acceptance and Artifacts receipts, and
  *a checkpoint is a recorded claim, not evidence*). This is the runtime, ask-indexed form of the
  feedback-coverage map (`roles.md`); it is distinct from the review-side reconciliation that audits a report's
  own claims against the artifact before closing (`method.md`, the `deep-code-review` skill), which runs
  **once at the end** rather than being read live throughout.
- **Name the termination conditions up front, each with its evidence.** The loop ends when the backlog is empty;
  when every remaining item is *blocked* on another party — including an item whose next step is a **Human
  gate** (`SKILL.md`), except a push or merge an owner-authored standing grant covers (never a self-written
  grant, never a deploy-triggering merge): that is not a stop, and the loop continues; when the granted window
  or stated **appetite** is spent (`SKILL.md` G0); or when a resource ceiling is hit (the environment-probe
  ceilings above). Each ending is stated with the evidence that it holds
  ("backlog re-read in full; the tracker shows only owner-approval-gated items"), never asserted bare.
- **A milestone is a cue to pull the next item, not to stop.** Finishing an item or hitting a checkpoint
  re-enters the loop: pull the next backlog item and re-check the termination conditions. Stopping is a
  *decision* that a termination condition fired, and it is reported as one — not a drift into silence. An owner
  *stop* or *redirect* is a different thing — a control signal that ends or repoints the loop, governed by the
  interrupt rule above, not a self-milestone to work through.
- **If the loop is idling, say so loudly, and report the window, not the item.** A status covers the whole grant
  — *what is left, what is blocked and on whom, what is next* — not just the task in hand; an agent out of ready
  work names the termination condition it is parked on rather than going quiet, because silence reads as
  *working* and the owner discovers the stall late.
- **Progress is a durable artifact, not a spawned lane — and the ETA follows the durable rate.** A lane
  computing locally with **nothing pushed** is, to the owner, in the same state as one never spawned: `spawned`
  ≠ `started` (the claim-side form is *assigned ≠ in-progress* above). Grade each lane on its durable output —
  **zero** (local only, no push: not-started, however long it has run), **in-flight** (a pushed branch or open
  draft PR: visible, recoverable), **done** (merged to the default branch or a filed issue: the canonical
  surface of the ask-ledger above). A status therefore **names each lane's push / PR / issue URL**; a lane with
  no URL is reported as *running, no output yet*, never as progress — and the window's ETA is projected from the
  **durable-output rate**, not the spawn rate, or it is fiction the moment a local lane stalls or resets.
- **The owner's message cadence is not the loop's clock.** A coordinator that acknowledges a completed lane and
  then **waits** for the next owner message before refilling the slot has made human message frequency an
  accidental concurrency controller — throughput sags exactly when the owner goes quiet while safe capacity sits
  idle. A completed lane refills on the coordinator's **own** cadence: hold target concurrency while
  **unblocked, non-owner-gated** backlog and headroom remain, and a quiet stretch **never lowers** it — but a
  stretch whose only remaining items are parked on a human gate (`SKILL.md` *Human gates*) is a
  *termination condition* (above), not a refill opportunity. Admission stays governed by the fan-out gates —
  disjoint surfaces, free RAM and the swap trend (*gate on free RAM and the swap trend* above), one lane then
  re-probe with a burst reserve (#239) — **never by message count**; and the target is a *maintained*
  concurrency with backpressure, never unbounded spawning (bounded by the WIP-cap above; an unbounded fan-out
  otherwise exhausts the box — the RAM/swap gate above — and stalls everything). On a shared host with
  **independent peer sessions**, read those resource gates as machine-wide aggregates, not this session's slice:
  a per-session WIP or concurrency target does not compose across peers — the caps **sum**
  (`multi-session-coordination.md`) — so bound refill by the shared reservation or a raw shared signal (worktree
  count, `load1` vs cores, swap-percent), and shed when the aggregate is distressed even while your own slice
  looks fine.
- **A loop's own wake/poll cadence is not the work cadence either.** The bullet above stops a *human's* silence
  from throttling refill; the identical coupling recurs with no human involved when an orchestrator treats its
  own scheduled wake — a ten-minute sync tick, a cron — as the unit of work itself: check the board, take one
  action, end the turn, and leave the next admissible action for the next scheduled wake. Throughput then tracks
  the **poll rate**, not the machine's capacity or the queue's depth — a run sitting on comfortable headroom for
  hours while ticking once every ten minutes to do one small thing under-delivers in proportion to how much
  capacity sits idle between ticks, and delivery visibly speeding up under faster polling (or slowing under
  slower polling) is the tell that the two are wrongly coupled. Decouple them: on any wake, for any reason, take
  **every** currently-admissible action before ending the turn — reconcile, refill, dispatch, verify, land, as
  far as admission allows — not one action with the rest deferred to the next tick. Admission is still governed
  by the same gates as ever — the WIP cap by landed artifacts, spawn-one-then-resample against the swap trend,
  disjoint-surface checks, all above — **never by tick count**, exactly as it is never by message count.

## A standing "keep producing" directive is not satisfied by the agent's own exhaustion read — wind-down needs the owner's confirmation, not just a thorough check

*Terminus is a claim about ALL work queues* (below) fixes **how thoroughly** to look. Separate axis: even a
thorough "empty" is only the **agent's own** read, and a **standing** owner instruction to keep producing is
discharged only by the owner. *Backlog empty* is an autonomous stop in the termination conditions above; under a
standing directive an empty *known* queue is a narrower claim than "the directive is satisfied."

- **Before winding down, self-source rather than stop on "empty."** A fresh-scope adversarial
  security/correctness review over code no open issue names, or a decision/spec lane that advances an
  owner-gated item toward ratification, is cheap, read-only-until-filed, and reliably turns up real,
  previously-unflagged work a name-only queue never listed — prefer both over idling, and over a speculative
  build lane that piles up unmerged work no one is reviewing (the same non-fan-out preference the go-faster
  section below states for a genuine terminus, applied here one step earlier — before the terminus is accepted,
  not only once a pressure tick questions it).
- **Report the check performed; let the owner confirm the stop.** "Queue exhausted, winding down" after a
  self-scan answers the directive with the agent's own state, not the owner's intent. Name what was (re-)checked
  and what was self-sourced; the directive stays live until the owner confirms it retired, so keep self-sourcing
  while that finds real work — never let a quiet "nothing left" stand in for it.
- **Scope: this governs only a *standing* directive against the *empty-queue* termination condition.** A spent
  time-box, a resource ceiling, or an owner-approval-gated block are still self-evident, unrelated stops;
  nothing here reopens those or asks a loop to keep running past a hard ceiling.

**🚩 tell:** a loop reporting "queue exhausted, winding down" against a still-standing "keep producing"
instruction, with no fresh self-sourced scan and no owner reply treated as confirmation.

## A go-faster signal fires on a clock, not on state — holding is a valid response, not a demand for busywork

The work-loop above runs *until a termination condition fires*; this is what to do **when one does**. An
unattended loop is usually driven by a **recurring pressure signal** — a cron, a "why are you stalling?"
supervisor prompt — that fires on a **clock, not on state**, so it keeps arriving when the correct action is to
**hold**: async work is still draining (a background merge-drainer, in-flight lanes), the buildable backlog is
**exhausted or parked on a human gate** (a *termination condition* above, not a refill opportunity), or the only
moves left are **risky** (a blind rebase of a large, possibly-active PR). The failure is to read every tick as a
demand for a **new visible action** and **manufacture low-value work** — spawning lanes that re-report
*already-delivered*, re-checking unchanged state, padding findings, forcing a risky change — burning budget and
adding risk to look busy.
- **Distinguish *stalled* from *correctly holding*.** Stalled = nothing is progressing, you are blocked on
  yourself → a new move is warranted. Holding = async work is progressing without a new action from you, or the
  rest is owner-gated (a push/merge an owner-authored standing grant covers is not: `SKILL.md` **Human gates**)
  → no new move.
  Only the first warrants motion.
- **Answer the pressure with the truth, not filler** — what's running, what's blocked and on whom, why holding
  is correct — in one line. This is the *if the loop is idling, say so loudly* rule above answered to an
  **external** trigger: same whole-window status, opposite failure — there the risk is **silence** (going quiet
  reads as working), here it is **filler** (motion to look busy).
- **At a genuine terminus the highest-value moves are non-fan-out** — drain the merge queue, close delivered
  items, surface the decisions that gate the rest, or turn spare capacity onto
  **verification/hardening of what already landed** (an adversarial re-review, added test coverage, an evidence
  receipt for a claim that shipped without one) — still not fan-out, and it only counts once it produces a
  genuinely **new** artifact, never a re-report of already-known-fine state (the 🚩 tell below). When even those
  are exhausted, **hold and say so**; busywork under observation is still busywork.
- **A chain of individually-correct holds can still drift the machine to idle — self-check the utilization ratchet.**
  *Distinguish stalled from correctly holding* judges one decision at a time; it doesn't catch **accumulation**
  — each hold above can be separately justified in the moment, and the sum can still ratchet toward near-zero
  utilization, because nothing re-examines the pattern itself. Make the drift visible instead of assumed-fine:
  track **active-lanes ÷ machine-capacity** alongside queue depth. This is an
  **orchestrator-internal diagnostic**, not the owner-facing status (*report the artifact, not the activity*,
  above, still governs what's said) and not an admission signal — a low ratio is a prompt to
  **re-examine why the holds accumulated**, never authorization to spawn past the WIP-cap-by-landed-artifacts
  gate, the free-RAM/swap-trend veto (*a veto, not a licence*, above), or a legitimate aggregate-distress shed
  (`multi-session-coordination.md`); a machine correctly held idle by any of those gates is not the drift this
  guards against, and this check never overrides them.
- **🚩 tell:** a new lane whose outcome is *already-delivered* / *nothing-changed*, or a finding filed only
  because a pressure prompt fired — activity manufactured to answer a clock.

A go-faster signal is about **outcomes, not activity**: when you are already maximally deployed and the rest is
blocked, the honest response is a precise status, not motion for its own sake. (A pressure cron ideally fires on
a state change, not a fixed clock — but the agent must behave correctly when it doesn't.) The counterweight to
the work-loop above — the mirror of its *the owner's message cadence is not the loop's clock* bullet: that stops
owner-quiet from throttling the loop **down** (*don't stop while the backlog has work*); this stops a pressure
tick from driving it **up** into busywork (*don't fake work once it doesn't*).

**Multiple such loops compound this at the point where their wakes overlap — the gap this section leaves open.**
A fleet commonly runs several recurring loops at once — merge, produce, hygiene, watchdog, review — and when two
or more land on the same tick, running each one's full sweep independently re-pays the same
re-probe-and-reconcile cost N times for what is, underneath, one answer: is there admissible work right now.
**Consolidate overlapping *fires* into a single reconciliation pass** rather than executing every loop
end-to-end — check once, act on the union, and let every loop that fired on that tick read the one result; this
is runtime behavior at the moment several loops wake together and leaves the loop set itself untouched, distinct
from the operator-visible loop *count* the next section says not to consolidate away. This is what makes a
**fast no-op** actually cheap: gate the **expensive** part — the full sweep the holding-vs-stalled judgment
above requires — behind a precondition check that runs **first**: is the delivery engine already covering this
tick's job (a merge train draining, producer lanes already at cap)? A covered tick then short-circuits before
paying the reconcile cost, not after paying it and discovering there was nothing to do. This is distinct from,
and does not restate, the already-covered preflight check that stops one spawn from duplicating one in-flight
objective (*an ownership map blocks a dual write, not dual work*, above): that rule protects **one** objective
from **one** duplicate spawn; this protects the coordinator from **N simultaneously-firing loops** each
re-deriving and re-paying for the same answer. Prefer **adding** a new, non-overlapping loop over raising an
existing one's frequency to close a gap — past the resource cap, more frequency only buys more reconcile
overhead, never more throughput.

## A monitor emits on state-transition or terminal state only — an unchanged poll is not an event

A lane arming a **background monitor** — watching a merge queue or another long local process on the
orchestrator's behalf, never CI status itself (`gh pr merge --auto` merges once required checks pass with no
polling at all; `host-enforcement.md` **Cost discipline**) — is a distinct, legitimate pattern from the lane
that keeps re-polling its *own* already-green PR past
its own finish line, which `SKILL.md`'s *Failure* section already bans as a **scope** violation ("re-polling a
green PR burns turns on unchanged news; report once, then stop"): that rule says watching CI after your finish
line isn't your job at all; this section assumes a monitor that **is** someone's job and governs how it emits.
The failure here is not that the monitor exists — it's that it reports its raw poll result **on every tick**,
"pending" indistinguishable from a real change, until the orchestrator's turns are a run of near-identical
"still pending… still pending…" notifications (and a lane that already delivered re-sends the identical final
handback on a later wake), burying the tick that is real: a new PR, a base gone green, a genuine block.

- **Emit on transition only.** A monitor holds its own last-*emitted* state and diffs the fresh poll against it:
  unchanged → stay silent, no output at all; changed → emit once, old → new; reaches a terminal state → emit
  once and **exit** (never re-arm). A `pending → pending` tick is not an event and produces no output — the
  emission is the state machine's edge, never its level.
- **The orchestrator retires the monitor once the lane reaches the state that monitor exists to detect** — for a
  build-to-PR lane that is the pushed branch or opened PR, the same artifact that already separates *in-flight*
  from *zero* (*progress is a durable artifact, not a spawned lane*, above); for a monitor watching *to* a
  terminal state (CI gone green, the merge landed) the branch/PR already exists, so the retirement trigger is
  that terminal state itself — which the monitor also self-signals by exiting under *emit on transition only*
  above. That is the **live teardown path** — the identical discipline
  *kill a lane-owned helper the moment its step ends* (above) already states for any lane-owned process, applied
  here to a monitor instead of a dev server — not the advisory, approval-gated sweep in
  *the orchestrator also owns reaping orphaned heavy processes* (above), which stays the **backstop** for a
  monitor that outlives this live path, the same relationship already holding between a worktree's own
  teardown-at-spawn contract and its GC backstop (*a worktree is a resource with a lifecycle*, above): a monitor
  is a lane resource with a lifecycle too, and creation without teardown leaks turns instead of disk.
- **A no-change wake is not itself a mandate to act.** When the orchestrator wakes on its own schedule and the
  monitor shows nothing new (a rule-1 monitor emits nothing on an unchanged poll, so there is nothing to react
  to), that is none of the four events the Conductor's attention is triggered by (`SKILL.md`,
  *Conductor operating rhythm*), so it carries no obligation of its own — note nothing changed and end the turn
  once no other admissible action is ready, not manufactured motion. This narrows only that no-change case: it
  does not relax *on any wake, for any reason, take every currently-admissible action before ending the turn*
  (above) for whatever other work is independently ready that same turn.

Distinct from *consolidate overlapping fires into a single reconciliation pass* (above: N loops on one tick;
this is one monitor's emission and lifecycle, which shrinks what that pass consolidates), from the enclosing
go-faster section (an external pressure cadence; here a monitor's own tick), and from *confirm a subagent is idle
before dispatching a duplicate* (above: the receiver-side defense; this is the source-side fix).

**🚩 tell:** an orchestrator turn history that is a run of near-identical "still pending" / "still waiting"
notifications from the same monitor, or a lane re-delivering its already-captured final handback on a later wake
— real signal buried in tick noise whose retirement condition (the artifact landed several ticks ago) already
held.

## The loop set is add-only when the operator asked for "more" — a decrement needs a stated reason, never a silent side effect

Editing **one existing loop's own instructions in place** is the default and moves no count — always fine, no
ceremony. This discipline is about the **operator-visible count**: when someone asks for **more** recurring
loops / self-reminders to sustain throughput, do not satisfy it by **consolidating** N loops into fewer "richer"
ones. That is *functionally* an upgrade but **reduces the count** — and operators often track the loop count as
a **proxy for delivery health**, so a drop reads as "you did the opposite of what I asked," whatever the intent.
Practices:
- **Improve by editing in place or adding** — never delete-then-recreate to "upgrade," and don't consolidate in
  response to a request for *more*.
- **Prune only a genuine, named defect** — an exact duplicate, a dead/broken loop, or two loops giving
  contradictory instructions — and **say so explicitly**, with the reason. Removing a broken loop is correct;
  the sin is removing it *silently* or as a *side effect* of an optimization nobody asked for.
- **Account for the count after any change**: it may hold or rise freely, and decreases **only** with a stated
  reason (prune-one-dup-and-add-one nets to zero — fine, because the prune was explained).

**General principle:** when a user's mental model tracks a **countable resource** (loops, open PRs, agents,
dashboards), never move that count the wrong way as a **silent or unexplained** side effect of an optimization
they did not ask for — the trust violation is the *surprise*, not the decrement itself. A justified,
explicitly-surfaced decrement is fine (closing a PR that leaks a secret; killing a genuinely dead loop).
Distinct from the go-faster-signal section above (which governs how to *respond* when a pressure tick fires):
this governs the **loop set itself**, independent of any tick.

## A degradation workaround is temporary by default — tie its removal to the condition that caused it

When a fast mechanism is blocked by a broken dependency, the reflex is a slower workaround: a merge-train whose
union-proof gate is unavailable falls back to serial merging; a saturated parallel stage drops to sequential.
Two traps follow, and the second is the expensive one.

First, the workaround is often **heavier than necessary**: a broken part need not collapse the whole vehicle to
serial — the fast batch mechanism can keep running on the **runnable subset**, skipping only the broken term,
rather than downgrading everything (a tool broken *in this environment* is a **can't-check, not a red** —
`SKILL.md` principle 3; and a merely **hung** gate is timeboxed and escalated, its reduced subset a
proof-of-record that does **not** license merging an unvalidated member — see `deep-code-review`'s
`merge-operations.md`). Downgrading the whole vehicle to serial is a bigger regression than routing
around the one broken piece.

Second — the costly one — **the workaround outlives the outage.** Momentum keeps the degraded mode running long
after the blocker clears: nothing is red (the slower path still "works"), so no failing gate prompts the
switch-back. The regression persists until a human notices the slowness — a failure of self-monitoring, not of
the mechanism. Discipline:

- A workaround adopted during a degradation is **temporary by default.** Tie it to the degradation explicitly at
  install time — *"revert to `<primary mechanism>` when `<blocker>` is fixed"* — not a vague intention to undo
  it later.
- **Track active workarounds** as open obligations (the same way a brief's follow-through is tracked, below).
  Fixing or noticing the blocker restored must trigger a *"what did I downgrade because of this?"* check, and
  restore the primary mechanism **in the same breath**.
- "It still works" ≠ "it's still the right mechanism." A slower-but-working fallback hides a regression
  *precisely because* nothing is red — so the switch-back needs an explicit trigger set when the workaround is
  installed, never the absence of an error to prompt it.

## Research is not delivery — a brief with no tracked follow-through is reported as unconsumed

A lane sent to investigate comes back with a thorough brief, the brief is pasted into the transcript, and the
loop moves on — and nothing downstream ever acts on it. Effort was spent; nothing was delivered. Research earns
its cost only when its conclusions become *tracked work*. The **cap-in-flight-by-landed-artifacts** rule above
owns the status discipline here: a brief is a transcript, not a landed artifact, so its honest status is
"researched, 0 items tracked," never "done."

- **End in an enumerated, trackable recommendation list, and open the items in the same step.** "Here is what I
  found" is not a queue; each recommendation becomes an issue, a backlog row, or a *recorded rejection* **now**,
  while the context is live — a conclusion that lives only in the transcript is lost at the next compaction or
  handoff.
- **Commission with a named downstream consumer.** Research is requested *for* something — a decision, a design,
  a fix. Name it at commission time; a brief with no consumer is one no one will act on.
- **Check the depth distribution before calling it consumed.** If only the cheap, obvious recommendations turned
  into tracked items and every expensive or structural one evaporated, the commissioned value did not land — the
  easy tail is not the reason the research was worth doing.
- **Watch research standing in for the delivery it was meant to inform.** A loop that keeps commissioning briefs
  while the thing they were supposed to unblock never moves is displacing delivery with investigation; the
  status that names *what shipped* (above) is what surfaces it.

## Terminus is a claim about ALL work queues — verify every one before declaring done

An agent working one backlog can declare "terminus — nothing left" while a **second, parallel work queue** sits
untouched because it was never checked. "I finished the queue I was working" is not "there is nothing to do."

- Before declaring terminus, **enumerate every work surface** the repo / product has — the issue tracker(s), a
  gaps / todo / next-actions queue, a debt / critique file, failing or skipped tests, TODO comments, an
  open-review backlog — and confirm each is **drained or blocked-with-reason**.
- **Name the queues you checked** when you claim done, so a missed surface is visible and auditable.
- The pressure to "keep delivering" is best answered by **widening the search for work** (a new surface), not
  re-scanning the one queue you already know.
- This is the delivery-side analog of the review's coverage-ledger reconcile (`deep-code-review` `method.md`:
  reconcile against the Phase 0 coverage ledger before you close); it **generalizes** this file's own
  *termination conditions* above ("the loop ends when the backlog is empty") from one tracked list to **every**
  work surface.
- **🚩 tell:** "terminus / nothing left" after checking only the assigned queue, with no enumeration of the other
  work surfaces (a parallel gaps / debt / test / TODO backlog never opened).

**A shared backlog split into named per-agent slices for load-balancing is a third axis, distinct from the surface-type gap above and the keyword-filter gap below.**
An agent that drains its own assigned slice — a named subset of the *same* tracker, not a different surface, and
not merely a narrower keyword match on it — and declares terminus has swept its assignment, not the queue: the
slice is a **floor on what it commits to deliver, never a ceiling on what it may pull**. A high already-done
rate found *inside* that slice (the verify-first-before-laning discipline, above) is evidence the slice is
drained, not that the shared backlog is; it means stop rebuilding *this* slice, not stop working. The correct
move is to broaden into the adjacent remainder of the same shared queue before concluding there is nothing left
— collision-freedom established by the occupancy check and announce-then-take claim
(*an ownership map blocks a dual write, not dual work*, above), not by assuming the partner's label is its only
reach. Whether there is currently room to act on that remainder is a separate, resource-gated question (the
swap-trend gate, above), never one the assignment boundary itself decides. Missing a **surface type** is not
checking a queue that exists; a **keyword filter** (below) checks the right queue too narrowly; an
**assignment partition** checks the right queue correctly and then stops at a boundary that was only ever a
coordination convenience between agents, not a statement of how much work exists.

## Discover work by enumerating the surface, not a keyword/title filter — filter only to order

Scanning a backlog for "what to build next" via a **keyword / title filter** (titles matching `app|ux|feat|fix`)
silently **misses every item whose title does not match** — and can conclude "nothing left" while a whole
category (docs, CI, security, tooling, API) remains, its titles simply lacking the keywords.

- **Enumerate the full list, then categorize** — never pre-filter by keyword to *discover* work. Count the total
  (**mind pagination** — a tracker's default page can hide the rest; confirm yours), bucket by type, confirm
  each bucket is drained or blocked. A keyword filter is fine to **prioritize within a known-complete set**,
  never to define the set.
- Titles are lossy: a CI / security / tooling / bug item may not contain your keywords — use the tracker's
  **labels / type field** as the axis, not a title regex.
- **State the filter when you claim done** — "I delivered everything matching my search" is not "nothing is
  left"; it is "nothing *matching my search* is left." The shape of your search is the shape of your "done."
- The intra-queue companion to the every-queue rule above: even one queue has categories a filter can hide.
- **🚩 tell:** a "what is next / terminus" decision driven by a title / keyword grep over the backlog rather than
  a full enumeration bucketed by label / type.
