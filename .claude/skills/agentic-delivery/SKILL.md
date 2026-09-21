---
name: agentic-delivery
description: >-
  Use when implementing a feature, migration, or end-to-end change that
  needs gated multi-role delivery — not a typo fix. Smallest-sufficient
  hats, independent QA and security, one writer per worktree, exact-SHA
  receipts, human approval on push/merge/deploy. Load deep-code-review
  at specification, review, and integrate. Opt-in overlay; do not install
  by default next to another delivery pack.
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.407.0"
---

# Agentic delivery

Public-safe delivery overlay for any coding agent — a **pattern**, not a
runtime or a standing swarm. Not installed by default; add it with
`./install.sh --with-delivery` or `--full` after the owner says yes (or after
`./install.sh --recommend` names it).

It does **not** replace `deep-code-review` — review is the bar, this is how work
reaches it. Do not run a second delivery OS (Superpowers, gstack `/ship`, a
private factory) on the same repo; compose those packs for TDD/brainstorm *or*
this pack for gated multi-role work, always `deep-code-review` for audit.

Persisted artifacts (code, PR bodies, ADRs, commits) are **normal English**;
chat may be terse. Don't vendor a chat-voice skill here — if compressed prose
is wanted, add [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman)
separately.

---

## When to Use

- A change spans implementation plus QA or security, or more than one writer
  would collide.
- The owner asked for a feature, migration, or release — not a one-line fix.
- `./install.sh --recommend` named this overlay for the target.

**Do not use** for a typo, a docs-only nit, or a repo that already runs another
delivery pack. One conductor. Hats, not headcount. Before any agent-originated
"we should" reaches the owner, load `idea-critic` if installed.

---

## Operating model

Smallest sufficient team. Hats fire from risk — not standing roles, never a
bot or profile per role; one worker wears several compatible hats on a small
change. The full roster (each hat's trigger, the gate it owns, its
build/product discipline, and the `deep-code-review` lens it maps to) is
`references/roles.md`. The core hats:

- **Conductor** — intent, scope, task graph, merge plan, evidence roll-up.
  Never self-approves.
- **Product Analyst** — turns a real signal (feedback, an owner goal) into a
  testable spec + feedback-coverage entry; enforces interaction-completeness,
  benchmarks against named comparable products. Recommends; owner decides
  scope. Feeds G0/G1.
- **Builder / Implementer** — implements in a dedicated worktree to the build
  bar in `references/roles.md`. Never wears independent QA, security, or
  release-approval.
- **Evil Twin** — attacks a plan or an agent-originated "we should" before the
  owner sees it (G0/G1); a lead to verify, not an oracle. Mechanism in the
  `idea-critic` skill.
- **QA** — independent, exact-revision functional / regression / a11y /
  state-coverage / performance verification.
- **Security** — independent AppSec / privacy / supply-chain (Red on paper +
  authorized testbeds; Blue fail-closed; White scope/ROE). Physical /
  social-engineering assessment is **human-led under written ROE**; an agent
  may only plan, tabletop, and analyse owner-supplied evidence.

Builder never reviews builder. Architect, UX & Design, Release, and Docs fire
from the same risk triggers — `references/roles.md` maps each to its gate and
lens.

### Conductor operating rhythm

The Conductor's attention is **event-driven, not polled.** It is triggered by
exactly four things: a lane blocking a gate, a lane returning a receipt (the
output contract, at an exact SHA), a lane exceeding its stated time/cost budget,
or a preflight collision (*Worktrees and occupancy*, below). Between those
events the Conductor reads status only — not a lane's raw tool-call transcript —
and does not do the lane's work itself, the same way a subagent returns a
distilled summary while its own context stays isolated from its parent's
(Anthropic, context engineering for AI agents).

**Size the fan-out to the decomposition, not to available concurrency** —
never spawn more lanes than there are independently-verifiable objectives —
and **pilot before full fan-out** on a wide, mechanical batch. Default tiers,
the duplicated-work failure mode, and the pilot procedure:
`references/fast-agentic-delivery.md`.

**Escalate a lane, don't just retry it.** After two equivalent failures on the
same lane, change approach — not the same fix again (*Failure*, below). In order
of cost: reframe the task boundary, decorrelate (fresh context or a different
model), or move to a stronger model tier (`model-tiering.md`) — start at the
stronger tier only when blast radius already calls for decorrelation
(`idea-critic`'s high-blast rule), not by default; a cheaper tier that clears the
gate is preferred.

**An independent, empirical check on this shape:** Cemri et al. (2025),
across 1600+ multi-agent traces, found failures cluster into three named
categories — system design, inter-agent misalignment, and task verification
(under-specified tasks, agents stepping on each other, results accepted
without real verification). They map onto this roster's own gates without
forcing a new one: system design → G0/G1, misalignment → G2 and the worktree
preflight, task verification → G5/G6 — confirmation the gate shape already
covers the failure surface that occurs, not a reason to add an eleventh gate.

**Sweeping the whole ready queue on every trigger** — a completeness fix to
this event-driven model, not a change to it: `references/fast-agentic-delivery.md`.

**Catch and reverse your own drift into a lane's work** — the completeness
fix applied to *action*, not only attention. Name the tell **behaviourally**:
the Conductor has drifted when its *own* recent turns are a **run of
consecutive tool calls that query, build, edit, or mutate the target** rather
than dispatch a lane, read a receipt, or decide. Two such turns in a row is
the signal; "delegating is slower than doing it myself" is the rationalisation,
not an exception. On the signal: **stop** before finishing the hands-on task;
**package** it as a lane brief (goal, exact scope, acceptance check, output
contract); **dispatch** it (a fresh, non-forked unit for narrow work —
*Worktrees and occupancy*); **resume** status-reading. The lone exception is
work only the Conductor's own session can perform (a connector, credential, or
surface no lane holds) — done **minimally** and handed straight back; a keyhole
for the irreducible step, never a licence to run the tactical job by hand.

---

## Gates (G0–G10)

Low-blast reversible work may collapse adjacent gates. It may not remove
independent verification or a human approval that actually applies.

| Gate | Input | Required output | Hard condition |
|---|---|---|---|
| G0 Intake | Owner goal | Brief | Goals, non-goals, constraints, and **appetite** (a stated time-box, not an estimate — Shape Up); `idea-critic` on any agent-originated approach before the owner sees it |
| G1 Spec | Brief | Testable spec | Acceptance criteria; names `deep-code-review` scope and pinned base SHA |
| G2 Plan | Spec | Acyclic work graph | Role triggers, one writer per worktree; **every lane with a paid model call names a per-lane token/dollar budget before G4 starts — no budget set is blocked, not unlimited** (a cap that defaults to off is not a cap) |
| G3 Design | Graph | ADRs / contracts | Interfaces, NFR budgets, data/security decisions explicit. Shape: `references/template-adr.md` |
| G4 Implement | Work packets | Patch/commit per lane | Tests before or with the change; packet names review skill + immutable base SHA |
| G5 Verify | Exact revision | Test receipts | **Local stack up** (project's one-command / compose / devcontainer) then build, lint, type, unit, and applicable integration/E2E **green at that SHA**. A gate that never started the app is `UNVERIFIED`, not pass. **UI change (domain P):** headed-browser evidence on the exact route after the action (screenshot or equivalent). Unit tests alone are not a UI gate |
| G6 Review | Exact revision + receipts | `deep-code-review` + QA + security verdicts | Independent of the builder; applies the `deep-code-review` severity rubric — Blocker/Critical block, High needs a named owner's acceptance, Medium is tracked and non-blocking (do not silently block on Medium) |
| G7 Integrate | Accepted lanes | Integration receipt + `deep-code-review DIFF` | One integration owner; rerun affected gates on the exact final SHA |
| G8 Release | Exact integrated SHA | Release manifest | Rollback proven; **owner approves** outward/production action |
| G9 Production verify | Deployed SHA | Verification receipt | Served behaviour and SLOs; rollback on breach |
| G10 Learn | Receipts | Retrospective | Escaped gap → regression test in this repo. Reusable lessons are generalized and stripped of third-party identifiers before leaving the project (the `contribution` overlay, if installed, is the mechanism to propose them upstream). Mandatory-trigger criteria, blameless shape, action-item-closure gate: `references/retrospective.md` + `references/template-postmortem.md` |

**Missing evidence is `UNVERIFIED`, never pass. Missing price is `UNPRICED`,
never zero. Missing spend cap is `BLOCKED`, never unlimited** — `UNPRICED` is a
labeling rule (report the cost honestly); the G2 budget is the bound itself, and
the two are not substitutes.

**Building a user-facing product surface (domain P, build side).** To build to
the quality bar in G3 rather than discover the gaps in G6 review:
`references/production-grade-product-playbook.md` — **read it when** shaping a
product surface's information architecture, ranking, relationship-vs-record
framing, or density. It is the positive, build-time companion to
`deep-code-review` domain P, which verifies each choice at G6.

**Durable state, recovery, and non-code receipts** — one canonical project
record with a single writer, the resume / crash-after-effect reconciliation
procedure, and the artifact-receipt contract for design/data/published
deliverables: `references/project-state.md` — **read it when** beginning
multi-step work, changing objectives, checkpointing, recovering after a
reset, or deciding what keeps an unattended run alive.

**Claimed vs enforced** — before asserting state, permission, or spend is
*enforced* rather than merely followed (or when designing a host adapter), grade
the claim against `references/host-enforcement.md` — **read it when** you would
otherwise write "the gate / budget / permission is enforced." Model-tier
selection (which tier, and when to escalate) is `model-tiering.md` in the
`deep-code-review` skill.

**Operational readiness — incidents and continuity (bus factor = 1).** The
binder that must exist *before* the system is on fire or the solo operator is
gone: `references/incident-response.md` — **read it when** drafting an incident
runbook (detect→triage→contain→eradicate→recover→review), severity levels,
comms templates, a break-glass path, a credential/renewal inventory with
dead-man reminders, or a succession note. It reuses the blameless
`references/template-postmortem.md`; **breach notification routes to G2 + counsel, never
asserted here**, and executing any notification or succession is the owner's.

**Support & feedback operations (the compounding solo time-drain).** When the
product has users filing tickets: `references/support-ops.md` — **read it when**
building an intake/triage taxonomy, an SLA, canned-response drafts, or the
ticket→work-item loop. **Hard gate:** never auto-send an external reply or make
a promise/refund/commitment — every outward reply is owner-approved, the same
gate this skill applies to push/deploy.

**Multi-session / peer coordination (independent sessions, no shared
conductor).** Two or more agent sessions coordinating over a shared async
channel instead of one orchestrator's own lanes:
`references/multi-session-coordination.md` — **read it when** designing a
claim/lock registry, a pre-write collision probe, a peer-liveness check, a
shared-board reader, reconciling two peers' crossed work-splits, coordinating
a shared machine-wide resource budget across peers, routing an action one peer
is persistently denied, vetting a peer's correction before acting on it, or breaking a
mutual pause where two peers each wait on the other, routing backlog items to the machine whose
resources fit, relaying a shared gate's accepted format to a peer, classifying who merged a PR
that landed under a peer's merge-hold before calling it a violation, or trusting
cross-peer convergence as a backlog-exhausted signal.

**Unattended / autonomous operating mode (an overnight or multi-hour autonomous
run).** When this skill runs as a **continuous loop over a backlog** rather than
one feature at a time: `references/unattended-operating-mode.md` — **read it when**
starting or shaping an unattended / overnight autonomous run. It composes
`deep-code-review` (review), `idea-critic` (decision), and this skill's own gates
into one bounded-and-reversible loop, and adds only the connective doctrine: the
default-mode framing (stopping needs a stated termination condition; the Human
gates below are unchanged), the five-rung delivery loop with its FREEZE-THEN-TRAIN
and SIZE-TO-MEASURED-HEADROOM sequencing rules, the **run-start checklist +
run-end self-audit** that bound a run, the running ≠ merged ≠ live reporting
ladder, and the default set of offset recurring loops. A **loop, not a standing
swarm**.

**A work item's own completion is G7, not G8.** Once a lane's change is
integrated (G7), the work item it closes is done; G8 Release is a separate,
later, **owner-gated** action on a different clock, often batched across many
G7s. Never park a G7-complete item as "blocked on deploy" — land it, close it,
and name G8 as downstream and pending, not as a reason the item isn't done.

---

## Exact revision

Every technical packet names `deep-code-review` + the required scope (`FULL` /
`DIFF <base>` / `FILE <paths>`) and the immutable base SHA (G1/G4) or exact
reviewed SHA (G6/G7). QA and security receive the **final SHA**, not the
builder's narrative; a stale SHA fails closed. Several green PRs still need one
throwaway integration SHA plus one aggregate gate before a merge train (G7).

---

## Worktrees and occupancy

- **One writer per worktree — and a worktree is not automatic.** A subagent or
  fork does **not** necessarily give a separate working tree: verify your host's
  isolation and **assume a shared tree until proven otherwise**. Branch, index,
  and installed dependencies are per-tree, so two writers in one tree collide
  even with disjoint file sets. Give every write-lane its own isolated worktree
  (or claimed branch), and **clean the base to the mainline before launching**.
  Read-only reviewers may share a pinned checkout.
- **Preflight before spawning any lane.** Enumerate what is already in flight —
  running workers, worktrees (`git worktree list`), open PRs — and claim the
  work (a draft PR or assigned issue) before starting. Never spawn a duplicate
  of a running lane, and never start on a branch that already carries commits
  without reading them first. One writer per file.
- **A context-inheriting fork is not a blank slate — a narrow instruction to
  it is ambiguous by construction.** Distinct from the tree-sharing risk
  above: a fork hands a subagent every prior instruction, not only the newest.
  A lane earlier told "file an issue for anything you find" and later forked
  with "return a table, create or change nothing" inherits both — the narrower
  ask does not erase the wider one still in its context, and it can act on the
  old brief. Two mitigations, both required for narrow or research-only work:
  prefer a **fresh, non-forked** unit (no inherited brief to fall back on);
  when a fork genuinely needs the parent's context, state the prohibition
  explicitly *and* verify compliance from what the lane actually called, not
  its own summary — `git status`/`git diff` proves no tracked file changed and
  proves nothing about an issue filed, a comment posted, or a message sent
  (`parallel-audit.md` §2 covers the read-only fan-out case; this is the
  general-lane case).
- Serialize shared-state edits, migrations, generated files, and the
  integration branch.
- Occupancy is **visibility, not a lock**. Say what is live or stale. Do
  not comment "do not merge" on a peer's PR after you stopped writing.

## Environment probe (before you size anything)

Probe the host before deciding lane count, the heavy/light split, or model
tier — a stated ceiling with no live check behind it is a guess, and
yesterday's number may not hold today. Probe free RAM, CPU cores, disk, and
which tools/connectors this session actually has usable auth for (a lane
dispatched against a connector it cannot authenticate fails after it already
holds a worktree slot). Decide HEAVY-lane count and model tier
(`model-tiering.md` in the `deep-code-review` sibling) from that, not from
habit. The probe commands, the decide-from-probe rules, the shell-semantics
check (`branch-and-merge-hygiene.md` §6), the contention-vs-defect rule
(`parallel-audit.md` §0), and CI-offload:
`references/fast-agentic-delivery.md`.

- **Free RAM and the swap *trend* are the primary gate — `load1` is not a
  reliable term.** Spawn another heavy lane only while free RAM >15% AND swap
  is not actively climbing (`sysctl vm.swapusage` on macOS — read it twice, a
  beat apart, for the trend, not only the level). CPU idle >25% (`top -l 1 -n
  0` on macOS, `mpstat`/`top` elsewhere) is a useful **secondary**
  confirmation. `load1` (`sysctl -n vm.loadavg`/`uptime` vs. `nproc`/`sysctl -n
  hw.ncpu`) is at most a **weak corroborating signal, never the deciding
  term** — it counts disk-I/O-wait, not only CPU. Throttle the instant free RAM
  or the swap trend trips; the numbers are a rule of thumb to recalibrate on
  the host in front of you. Why `load1` misleads, the worked example, and the
  swap-blowout case: `references/fast-agentic-delivery.md`.

## Local environment (own it)

Delivery owns the running stack, not only the diff.

1. **Discover** the project's one-command path (`README` / `package.json` /
   `compose.yaml` / `.devcontainer` / `Makefile`) — prefer what the repo
   documents; do not invent a second stack.
2. **Bring it up** in the writer's worktree; record the command, URL/port, and
   the health probe that returned 200. A missing prerequisite's `doctor` output
   is the receipt — do not skip to "tests passed on the host."
3. **Verify against the running process**, not only the repository: served
   smoke, empty/error UI states where a UI exists, the project's own
   `verify:served` if it has one.
4. **Tear down** with the matching command; leave no orphan listener.
5. **Never** `npm run build` (or equivalent) against a directory a running
   server is serving — that stale-asset bug is a known ship failure; use the
   project's isolated verify dir.

G5 is not green until step 3 ran or is `UNVERIFIED` with the missing
prerequisite named; for a change that can alter a rendered page, step 3's receipt
is the **headed-browser** evidence G5 requires (`product-ux-quality.md`).

---

## Human gates (never autonomous)

Agents prepare. Humans approve:

- push, open/merge a PR, publish a package, deploy;
- send an external customer reply, refund/credit, or public statement
  (`references/support-ops.md`);
- grant scopes, rotate secrets, change IAM, widen egress;
- destructive migrations, mass deletion, force-push, production rollback-forward;
- feature-flag flip, canary widen;
- waiving a Blocker/High security finding.

Shape every ask as one issue, two approaches:

```
Issue: <one line>
A: <approach> (recommended) — <why, ≤12 words>
B: <approach> — <why, ≤12 words>
```

Never a list of questions. `idea-critic` must have attacked A before it
is marked recommended. Before raising a gate, apply gate epistemology principle 12 below — a fork a ratified invariant already decides is not a human gate.

---

## Gate epistemology (public principles)

Copied as principles, not as anyone's private playbook:

1. **Publish boundary is the gate.** Private data may exist in a private
   checkout; the failure is *escape* into a public artifact, PR title,
   changelog, compiled bundle, or example. Scan those surfaces, not only
   file bodies.
2. **Banlist split.** Committed `.banlist.txt` = generic secret shapes.
   Gitignored local file = real identifiers. Fail closed if the committed
   list is missing or malformed. Report `file:line`, never echo the match.
3. **A gate can be wrong about why.** Real defect → fail closed. Check could
   not run → `UNVERIFIED` — neither a defect nor a pass; a *required* missing
   check still blocks its gated action even when authorization exists (evidence
   and permission are separate decisions). Applied to a red pipeline: identify
   the failing job **and step** before blaming the newest merge, and if the
   shape matches a known-flaky browser/probe/hydration check, rerun and recheck
   **before** reverting — a revert is warranted only once the failure
   reproduces and is causally tied to the change, not merely adjacent in time. And **a
   conclusion that surprises you** — a gate that flips, a count that jumps — **is the signal
   to re-fetch the specific state at decision time**, not to act on a snapshot remembered from
   earlier in the run (principles 9 and 11 apply the same discipline to a close and to the
   owner's rendered surface).
4. **Prove the gate can fail.** Plant, watch red, revert. Required for
   every new gate this project adds.
5. **Skip loudly over absent input.** Missing fixture ≠ pass.
6. **Union proof before a merge train.** G7.
7. **Test the failure, not only the feature.** Schema reject, authz deny,
   monotonic-quality overwrite.
8. **Definitions, not live values**, in any public or compiled artifact.
9. **Closing or deleting shared state needs evidence, not presumption** — the
   "skip rather than guess" bar (principle 5) applied to removal. A ticket
   closed as duplicate/invalid needs a reproducible reason (not "looks like the
   others"), and any unique context it carried migrates to the canonical item
   **before** it closes. A batch of presumed-junk items is a batch of
   `UNVERIFIED` closures until each is checked — a plausible pattern across many
   is not evidence for any one.
10. **A fleet-wide external advisory is a third case for principle 3, and an
    independent-queue merge cascade is a cadence choice subordinate to
    principle 6** — neither restated here; depth and the honest limits of
    each: `references/fast-agentic-delivery.md`.
11. **"Visible/done" is measured on the owner's own surface, never a proxy.**
    Integrated to the mainline (G7), a green branch build, a passing test, an
    insert/row count, a grep count are engineering states — real, but none is
    "the owner can see it." Before reporting a change as *visible*, fetch the
    specific rendered thing from the surface the owner actually uses (a running
    app, the deployed page — which may lag a pinned or cached serve *behind*
    the integrated code), confirm it, and report only what you observed. Keep
    the states distinct in words: **wired / defined / rendered ≠ has a real
    value**; "queryable" ≠ "query written"; "the code path exists" ≠ "it was
    proven to run" (principle 3's `UNVERIFIED`, stated for the liveness case;
    it is what G9 verifies against a deployed SHA).
12. **A fork a ratified invariant already decides is not an owner gate.** Before shaping a
    choice as a human gate, check whether a ratified invariant — no-data-loss, a security or
    accessibility floor, a monotonic-quality rule — already mandates the answer; if it does,
    applying it is a lane's **mechanical** job, and escalating spends an owner decision on a
    settled question while the lane stalls. Gate only the genuine forks the invariants leave open.
    Conversely, a change that would **reverse** a ratified invariant or decision is not a lane's
    mechanical call either — stop and queue it to the owner rather than silently applying it (the
    code-level instance — never loosening a ratified assert-absent test to ship a conflicting
    feature — is `deep-code-review`'s `testing-and-evals.md`).

---

## Output contract

Every worker returns: role, exact SHA, artifacts, acceptance covered,
commands actually run with exit status, findings with severity + location
+ evidence, remaining risk, cost/`UNPRICED`. `NONE` is a valid findings
result.

**Work-item contract (what the output is graded against).** A work item is
specified as **Where** (the area it touches), **Done-when** (observable
acceptance), **Verify** (how it's checked), and **Why** (so scope can be cut).
Missing *Done-when* or *Verify* is underspecified — sent back to be scoped, not
started.

---

## Failure

- Start/auth failure: do not claim work ran.
- **A running lane is not a finished one.** A spawned worker/worktree is work
  in progress; report what is *running*, and a lane's output as done only once
  verified — a green gate at the exact SHA, or a change confirmed in the running
  product. Never present "N lanes attacking it" as progress.
- **The converse: a lane's scope ends at its own finish line, not at the
  merge.** Once a lane's PR is open with its gates green, its job is done — it
  does not loop re-checking CI for a merge that is the Conductor's (or a merge
  guard's) job. Re-polling a green PR burns turns on unchanged news; report
  once, then stop — the "event-driven, not polled" discipline applied by a lane
  to itself.
- After two equivalent failures, change approach.
- Provider/model unavailable: fail that lane closed; no silent fallback.
- Owner-session end: no uncommitted writer work without a recovery
  record.

## Anti-rationalization (G4 / G5)

| Excuse | Rebuttal |
|---|---|
| "I'll add tests later." | Later is the load-bearing word. Tests before or with the change (G4). |
| "Too simple to spec." | Five lines of acceptance is a spec. Zero is not. |
| "Unit tests cover the UI." | Domain P needs headed-browser evidence on the route that renders. |
| "Green locally is green in CI." | Different OS, browser, secrets. Exact SHA in CI is the receipt. |
| "The stack didn't start; tests still passed." | G5 is `UNVERIFIED`, not pass. |

---

## Recommend vs install

`./install.sh --recommend <project>` inspects the target and prints a pack; the
agent may recommend `--full`, the owner decides. Never install delivery into a
repo that already has another delivery pack without saying so.

---

## Verification

- Default `./install.sh` does not copy this skill; `--with-delivery` / `--full`
  copies it next to `deep-code-review`.
- `references/roles.md` ships with the skill (whole-directory copy), routed from
  this file.
- A planted defect makes G5/G6 fail; a denied outward action remains blocked.
- `evals/evals.json` names `recommend-must-not-write` and
  `default-install-omits-delivery`.
- No third-party identifier, private intake, or operator preference appears in
  this file.
