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
  version: "1.21.0"
---

# Agentic delivery

Public-safe delivery overlay for any coding agent. It is a **pattern**, not
a runtime and not a standing swarm. Default install of this repository does
**not** include it — add it with `./install.sh --with-delivery` or `--full`
after the owner says yes (or after `./install.sh --recommend` names it).

This skill does **not** replace `deep-code-review`. Review is the bar;
this is how work reaches that bar. Do not also run a second delivery OS
(Superpowers shipping loop, gstack `/ship`, a private factory) on the same
repo. Compose: those packs for TDD/brainstorm *or* this pack for gated
multi-role work; always `deep-code-review` for audit.

Persisted artifacts (code, PR bodies, ADRs, commit messages) are **normal
English**. Chat may be terse. Do not vendor a chat-voice skill into this
tree; if compressed assistant prose is wanted, add
[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman)
separately.

---

## When to Use

- A change spans implementation plus QA or security, or more than one
  writer would collide.
- The owner asked for a feature, migration, or release — not a one-line
  fix.
- `./install.sh --recommend` named this overlay for the target.

**Do not use** for a typo, a docs-only nit, or a repo that already runs
another delivery pack. One conductor. Hats, not headcount.

Before any agent-originated "we should" reaches the owner, load
`idea-critic` if it is installed.

---

## Operating model

Smallest sufficient team. Hats fire from risk; they are not standing
roles, and never a bot or profile per role. One worker wears several
compatible hats on a small change. The full roster — each hat's trigger,
the gate it owns, the build/product discipline it carries, and the
`deep-code-review` review lens it maps to — is `references/roles.md`. The
core hats:

- **Conductor** — intent, scope, task graph, merge plan, evidence roll-up.
  Never self-approves.
- **Product Analyst** — turns a real signal (user/product feedback, an
  owner goal) into a testable spec and a feedback-coverage entry; enforces
  interaction-completeness and benchmarks solved elements against named
  comparable products. Recommends; the owner decides scope. Feeds G0/G1.
- **Builder / Implementer** — implements in a dedicated worktree to the
  build bar in `references/roles.md`. Never wears independent QA, security,
  or release-approval.
- **Evil Twin** — attacks a plan or an agent-originated "we should" before
  the owner sees it (G0/G1); a lead to verify, not an oracle. Mechanism in
  the `idea-critic` skill.
- **QA** — independent, exact-revision functional / regression / a11y /
  state-coverage / performance verification.
- **Security** — independent AppSec / privacy / supply-chain. Red attacks
  on paper and in authorized testbeds; Blue fail-closed; White scope/ROE.
  Physical / social-engineering assessment is **human-led under written
  ROE**. An agent may only plan, tabletop, and analyse owner-supplied
  evidence.

Builder never reviews builder. Architect, UX & Design, Release, and Docs
fire from the same risk triggers — `references/roles.md` maps each to its
gate and its review lens.

### Conductor operating rhythm

The Conductor's attention is **event-driven, not polled.** It is triggered
by exactly four things: a lane blocking a gate, a lane returning a receipt
(the output contract, at an exact SHA), a lane exceeding its stated
time/cost budget, or a preflight collision (*Worktrees and occupancy*,
below). Between those events the Conductor does not read a lane's raw
tool-call transcript and does not do the lane's work itself — it reads
status only, the same way a subagent's own context stays isolated from its
parent's (a worker "returns only a condensed, distilled summary of its
work," however much it explored to get there — Anthropic, context
engineering for AI agents).

**Size the fan-out to the decomposition, not to available concurrency.** A
lead that hands out vague, overlapping instructions gets duplicated work,
not more coverage — subagents given no clear boundary have been observed
independently re-investigating the same ground (Anthropic, multi-agent
research system). Default tiers: a single fact/lookup needs one lane; a
bounded comparison needs 2-4; only a genuinely decomposable task graph
justifies 10+, and each of those needs its own objective, output format,
and explicit boundary against its siblings. Never spawn more lanes than
there are independently-verifiable objectives — spawning dozens of
subagents for a simple query is a named failure mode, not a hypothetical
one. **Pilot before full fan-out:** on a wide, mechanical batch, run a
handful of lanes first, fix what the pilot exposes, then commit the rest
of the width — cheaper than discovering a bad task boundary after the full
width is already running.

**Escalate a lane, don't just retry it.** After two equivalent failures on
the same lane, change approach — not the same fix again (*Failure*,
below). "Change approach" in order of cost: reframe the task boundary,
decorrelate (fresh context or a different model), or move the lane to a
strictly stronger model tier (`model-tiering.md` in the `deep-code-review`
skill) — start at the stronger tier only when the lane's blast radius
already calls for decorrelation (`idea-critic`'s high-blast rule), not by
default; a cheaper tier that clears the gate is preferred.

**An independent, empirical check on this shape:** a 2025 study of 1600+
multi-agent traces across seven frameworks (Cemri et al., "Why Do
Multi-Agent LLM Systems Fail?") found real failures cluster into three
named categories — system design issues, inter-agent misalignment, and
task verification (under-specified tasks, agents stepping on each other,
and results accepted without real verification, in plain terms). They map
onto this roster's own gates without forcing a new one: system design
issues → G0/G1, inter-agent misalignment → G2 and the
worktree preflight, task verification → G5/G6. Read as confirmation the
gate shape already covers the failure surface that actually occurs, not as
a reason to add an eleventh gate.

---

## Gates (G0–G10)

Low-blast reversible work may collapse adjacent gates. It may not remove
independent verification or a human approval that actually applies.

| Gate | Input | Required output | Hard condition |
|---|---|---|---|
| G0 Intake | Owner goal | Brief | Goals, non-goals, constraints, and **appetite** (a stated time-box, not an estimate — Shape Up: "Appetites start with a number and end with a design"); `idea-critic` on any agent-originated approach before the owner sees it |
| G1 Spec | Brief | Testable spec | Acceptance criteria; names `deep-code-review` scope and pinned base SHA |
| G2 Plan | Spec | Acyclic work graph | Role triggers, one writer per worktree; **every lane with a paid model call names a per-lane token/dollar budget before G4 starts — no budget set is blocked, not unlimited** (mirrors the review bar's own LLM10 / `spend-cap` invariants back onto this skill: a cap that defaults to off is not a cap) |
| G3 Design | Graph | ADRs / contracts | Interfaces, NFR budgets, data/security decisions explicit. Shape: `template-adr.md` |
| G4 Implement | Work packets | Patch/commit per lane | Tests before or with the change; packet names review skill + immutable base SHA |
| G5 Verify | Exact revision | Test receipts | **Local stack up** (project's one-command / compose / devcontainer) then build, lint, type, unit, and applicable integration/E2E **green at that SHA**. A gate that never started the app is `UNVERIFIED`, not pass |
| G6 Review | Exact revision + receipts | `deep-code-review` + QA + security verdicts | Independent of the builder; no unresolved Blocker/High/Medium |
| G7 Integrate | Accepted lanes | Integration receipt + `deep-code-review DIFF` | One integration owner; rerun affected gates on the exact final SHA |
| G8 Release | Exact integrated SHA | Release manifest | Rollback proven; **owner approves** outward/production action |
| G9 Production verify | Deployed SHA | Verification receipt | Served behaviour and SLOs; rollback on breach |
| G10 Learn | Receipts | Retrospective | Escaped gap → regression test in this repo. Reusable lesson is generalized and stripped of third-party identifiers before it leaves the project. Mandatory-trigger criteria, blameless shape, and the action-item-closure gate: `retrospective.md` + `template-postmortem.md` |

**Missing evidence is `UNVERIFIED`, never pass. Missing price is
`UNPRICED`, never zero. Missing spend cap is `BLOCKED`, never unlimited** —
`UNPRICED` is a labeling rule (report the cost honestly); the G2 budget
above is the bound itself, and the two are not substitutes for each other.
Model-tier selection (which tier a lane runs on, and when to escalate) is
`model-tiering.md` in the `deep-code-review` skill.

**A work item's own completion is G7, not G8.** Once a lane's change is
integrated (G7), the work item it closes is done; G8 Release is a separate,
later, **owner-gated** action on a different clock, often batched across many
G7s. Never park a G7-complete item as "blocked on deploy" — land it, close it,
and name G8 as downstream and pending, not as a reason the item isn't done.

---

## Exact revision

Every technical packet names:

- `deep-code-review` and the required scope (`FULL` / `DIFF <base>` /
  `FILE <paths>`);
- the immutable base SHA (G1/G4) or the exact reviewed SHA (G6/G7).

QA and security receive the **final SHA**, not the builder's narrative.
A stale SHA fails closed. Several green PRs still need one throwaway
integration SHA plus one aggregate gate before a merge train (G7).

---

## Worktrees and occupancy

- **One writer per worktree — and a worktree is not automatic.** A subagent
  or fork mechanism does **not** necessarily give a separate working tree:
  verify your host's isolation semantics and **assume a shared tree until
  proven otherwise**. Branch, index, and installed dependencies are
  per-tree, so two writers in one tree collide even when their file sets are
  disjoint. Give every write-lane its own isolated worktree (or a claimed
  branch), and **clean the base to the mainline before launching** so lanes
  branch off a known-good state. Read-only reviewers may share a pinned
  checkout.
- **Preflight before spawning any lane.** Enumerate what is already in
  flight — running workers, existing worktrees (`git worktree list`), and
  open PRs (the forge's PR list) — and claim the work (a draft PR or an
  assigned issue) before starting. Never spawn a duplicate of a lane already
  running, and never start on a branch that already carries commits without
  reading them first. One writer per file.
- **A context-inheriting fork is not a blank slate — a narrow instruction to
  it is ambiguous by construction.** Distinct from the tree-sharing risk
  above: a fork mechanism that hands a subagent the parent conversation
  hands it every prior instruction too, not only the newest one. A lane
  earlier told "file an issue for anything you find" and later forked with
  "return a table of what you'd flag, create or change nothing" inherits
  both — the narrower ask does not erase the wider one still sitting in its
  context, and it can act on the old brief. Two mitigations, both required
  for narrow or research-only work: prefer a **fresh, non-forked** unit,
  which starts with no inherited brief to fall back on; when a fork is the
  right tool because the work genuinely needs the parent's context, state
  the prohibition explicitly *and* verify compliance from what the lane
  actually called, not its own summary — `git status`/`git diff` proves no
  tracked file changed and proves nothing about an issue filed, a comment
  posted, or a message sent (`parallel-audit.md` §2 covers this for
  read-only review fan-out specifically; this is the general-lane case).
- Serialize shared-state edits, migrations, generated files, and the
  integration branch.
- Occupancy is **visibility, not a lock**. Say what is live or stale. Do
  not comment "do not merge" on a peer's PR after you stopped writing.

## Environment probe (before you size anything)

Probe the host before deciding lane count, the heavy/light split, or model
tier — a stated ceiling with no live check behind it is a guess dressed as a
rule, and yesterday's number may not hold today.

- **Probe:** free RAM and CPU cores (`memory_pressure`/`vm_stat` or `free
  -h`; `nproc` or `sysctl -n hw.ncpu`), disk (`df -h`), and which
  tools/connectors this session actually has usable auth for. A lane
  dispatched against a connector that needs an auth flow it cannot complete
  fails at the worst point — after it already holds a worktree slot.
- **Decide from the probe, not from habit:** how many HEAVY lanes (a real
  build, browser test, or compute process) this run supports — tighten
  under memory pressure even where a core-count formula would allow more,
  since a machine can exhaust RAM before it exhausts CPU slots; which model
  tier a lane needs (`model-tiering.md` in this skill's `deep-code-review`
  sibling) — frontier only where the blast radius already calls for
  decorrelation, not by default; and whether a heavy gate runs locally at
  all or waits for CI/a shared runner when local capacity is short.
- **Shell semantics belong to the probe, not to guesswork mid-script.** Know
  which shell will actually run a script before writing a list-membership or
  exclusion check in it — `branch-and-merge-hygiene.md` §6 has the concrete
  failure mode and the portable fix; this step only says *check*, not what
  to write.
- A **failure that only appears under heavy fan-out concurrency is
  contention, not a defect, until reproduced at low concurrency**
  (`parallel-audit.md` §0) — probing capacity first is what keeps that
  distinction from being made after the fact, on a report already full of
  false timeouts.

## Local environment (own it)

Delivery owns the running stack, not only the diff.

1. **Discover** the project's one-command path (`README` / `package.json`
   scripts / `compose.yaml` / `.devcontainer` / `Makefile`). Prefer what
   the repo already documents. Do not invent a second stack.
2. **Bring it up** in the writer's worktree. Record the command, the
   URL/port, and the health probe that returned 200. If a prerequisite is
   missing, the `doctor` output is the receipt — do not skip to "tests
   passed on the host."
3. **Verify against the running process**, not only the repository:
   served smoke, empty/error UI states where a UI exists, and the
   project's own `verify:served` / equivalent if it has one.
4. **Tear down** the stack with the matching command. Leave no orphan
   listener on the worktree's ports.
5. **Never** `npm run build` (or equivalent) against a directory a
   running server is serving — that class of stale-asset bug is a known
   ship failure. Use the project's isolated verify dir when it has one.

G5 is not green until step 3 ran or is `UNVERIFIED` with the missing
prerequisite named.

---

## Human gates (never autonomous)

Agents prepare. Humans approve:

- push, open/merge a PR, publish a package, deploy;
- grant scopes, rotate secrets, change IAM, widen egress;
- destructive migrations, mass deletion, force-push, production
  rollback-forward;
- feature-flag flip, canary widen;
- waiving a Blocker/High security finding.

Shape every ask as one issue, two approaches:

```
Issue: <one line>
A: <approach> (recommended) — <why, ≤12 words>
B: <approach> — <why, ≤12 words>
```

Never a list of questions. `idea-critic` must have attacked A before it
is marked recommended.

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
3. **A gate can be wrong about why.** Real defect → fail closed. Check
   could not run → fail open with `UNVERIFIED`, never a fake pass. Applied to a
   red pipeline: identify the failing job **and step** before concluding the
   newest merge caused it, and if the shape matches a known-flaky
   browser/probe/hydration check, rerun that job and recheck **before**
   reverting on it — a revert is warranted only once the failure reproduces
   and is causally tied to the change, not merely adjacent to it in time.
4. **Prove the gate can fail.** Plant, watch red, revert. Required for
   every new gate this project adds.
5. **Skip loudly over absent input.** Missing fixture ≠ pass.
6. **Union proof before a merge train.** G7.
7. **Test the failure, not only the feature.** Schema reject, authz deny,
   monotonic-quality overwrite.
8. **Definitions, not live values**, in any public or compiled artifact.
9. **Closing or deleting shared state needs evidence, not presumption** — the
   same "skip rather than guess" bar as principle 5, applied to removal. A
   ticket/issue closed as duplicate or invalid needs a reproducible reason
   (not "looks like the others"), and any unique context it carried is
   migrated to the canonical item **before** it closes. Treat a batch of
   presumed-junk items as a batch of `UNVERIFIED` closures until each is
   actually checked — a plausible-looking pattern across many items is not
   evidence for any one of them.

---

## Output contract

Every worker returns: role, exact SHA, artifacts, acceptance covered,
commands actually run with exit status, findings with severity + location
+ evidence, remaining risk, cost/`UNPRICED`. `NONE` is a valid findings
result.

---

## Failure

- Start/auth failure: do not claim work ran.
- **A running lane is not a finished one.** A spawned worker/worktree is
  work in progress; report what is *running*, and report a lane's output as
  done only once it is verified — a green gate at the exact SHA, or a change
  confirmed in the running product. Never present "N lanes attacking it" as
  progress.
- **The converse: a lane's own scope ends at its own finish line, not at the
  merge.** Once a lane's PR is open with its own gates green, its job is
  done — it does not loop re-checking CI for a merge that is the
  Conductor's (or a merge guard's) job, not every lane's. Re-polling a green
  PR every few minutes burns turns on news that has not changed; report
  once, then stop, the same "event-driven, not polled" discipline the
  Conductor applies to lanes, applied by a lane to itself.
- After two equivalent failures, change approach.
- Provider/model unavailable: fail that lane closed; no silent fallback.
- Owner-session end: no uncommitted writer work without a recovery
  record.

---

## Recommend vs install

`./install.sh --recommend <project>` inspects the target and prints a
pack. The agent may recommend `--full`. The owner decides. An agent must
not install delivery into a repo that already has another delivery pack
without saying so.

---

## Verification

- Default `./install.sh` does not copy this skill.
- `--with-delivery` / `--full` copies it next to `deep-code-review`.
- `references/roles.md` ships with the skill (whole-directory copy) and is
  routed from this file.
- A planted defect makes G5/G6 fail.
- A denied outward action remains blocked.
- No third-party identifier, private intake, or operator preference
  appears in this file.
