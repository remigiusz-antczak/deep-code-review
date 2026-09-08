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
  version: "1.15.0"
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

Smallest sufficient team. Hats fire from risk, they are not standing
roles.

- **Conductor** — intent, scope, task graph, merge plan, evidence roll-up.
  Never self-approves.
- **Builder** — implements in a dedicated worktree. Never wears independent
  QA, security, or release-approval.
- **QA** — independent, exact-revision functional / regression / a11y /
  performance verification.
- **Security** — independent AppSec / privacy / supply-chain. Red attacks
  on paper and in authorized testbeds; Blue fail-closed; White scope/ROE.
  Physical / social-engineering assessment is **human-led under written
  ROE**. An agent may only plan, tabletop, and analyse owner-supplied
  evidence.

One worker may wear several compatible hats on a small change. Builder
never reviews builder.

---

## Gates (G0–G10)

Low-blast reversible work may collapse adjacent gates. It may not remove
independent verification or a human approval that actually applies.

| Gate | Input | Required output | Hard condition |
|---|---|---|---|
| G0 Intake | Owner goal | Brief | Goals, non-goals, constraints; `idea-critic` on any agent-originated approach before the owner sees it |
| G1 Spec | Brief | Testable spec | Acceptance criteria; names `deep-code-review` scope and pinned base SHA |
| G2 Plan | Spec | Acyclic work graph | Role triggers, one writer per worktree |
| G3 Design | Graph | ADRs / contracts | Interfaces, NFR budgets, data/security decisions explicit |
| G4 Implement | Work packets | Patch/commit per lane | Tests before or with the change; packet names review skill + immutable base SHA |
| G5 Verify | Exact revision | Test receipts | Build, lint, type, unit, and applicable integration/E2E **green at that SHA** |
| G6 Review | Exact revision + receipts | `deep-code-review` + QA + security verdicts | Independent of the builder; no unresolved Blocker/High/Medium |
| G7 Integrate | Accepted lanes | Integration receipt + `deep-code-review DIFF` | One integration owner; rerun affected gates on the exact final SHA |
| G8 Release | Exact integrated SHA | Release manifest | Rollback proven; **owner approves** outward/production action |
| G9 Production verify | Deployed SHA | Verification receipt | Served behaviour and SLOs; rollback on breach |
| G10 Learn | Receipts | Retrospective | Escaped gap → regression test in this repo. Reusable lesson is generalized and stripped of third-party identifiers before it leaves the project |

**Missing evidence is `UNVERIFIED`, never pass. Missing price is
`UNPRICED`, never zero.**

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

- One writer per worktree. Read-only reviewers may share a pinned
  checkout.
- Serialize shared-state edits, migrations, generated files, and the
  integration branch.
- Occupancy is **visibility, not a lock**. Say what is live or stale. Do
  not comment "do not merge" on a peer's PR after you stopped writing.

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
   could not run → fail open with `UNVERIFIED`, never a fake pass.
4. **Prove the gate can fail.** Plant, watch red, revert. Required for
   every new gate this project adds.
5. **Skip loudly over absent input.** Missing fixture ≠ pass.
6. **Union proof before a merge train.** G7.
7. **Test the failure, not only the feature.** Schema reject, authz deny,
   monotonic-quality overwrite.
8. **Definitions, not live values**, in any public or compiled artifact.

---

## Output contract

Every worker returns: role, exact SHA, artifacts, acceptance covered,
commands actually run with exit status, findings with severity + location
+ evidence, remaining risk, cost/`UNPRICED`. `NONE` is a valid findings
result.

---

## Failure

- Start/auth failure: do not claim work ran.
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
- A planted defect makes G5/G6 fail.
- A denied outward action remains blocked.
- No third-party identifier, private intake, or operator preference
  appears in this file.
