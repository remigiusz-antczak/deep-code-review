---
name: contribution
description: >-
  Use when you have learned a genuinely reusable, generalizable lesson about
  the universal skillset itself while working on a project, and want to prepare
  a privacy-safe improvement back to the public repository. The agent drafts the
  skill edit, CHANGELOG, eval, and routing, runs the repo's own gates, and
  assembles a provenance-and-risk block — then hands it to a human to review and
  open the PR. Never pushes or opens a PR autonomously; the human is the privacy
  authority and the mechanical scrub is necessary, not sufficient. Not for
  project-specific lessons (imprint those locally) and not artifact polish.
  Opt-in overlay, default off; install with --with-contribution (deliberately
  not part of --full).
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.0.1"
---

# Contribution

Prepare — never send — a privacy-scrubbed, generalized improvement to the
*public* skillset, for a human to review and open as a PR. The agent drafts and
gates the change; a human is the privacy authority and the only one who pushes.

This is the mechanism the owner asked for: a skillset that improves from field
use. It is deliberately shaped so that improvement never becomes a private→public
leak or a self-reinforcing loop that games its own tests.

Persisted artifacts (the drafted skill edit, CHANGELOG, PR body) stay normal
English. Chat may be terse.

---

## Prime constraint — the human is the privacy authority (never auto-send)

The load-bearing safety property. The agent's scrub is **necessary, not
sufficient**: pattern-matching catches secrets and known identifiers, but a
paraphrased confidential fact — "a client retrains its model nightly" — leaks
strategy while matching no pattern and no banlist entry. Only a human who knows
the source context can clear that.

So the split is fixed: the agent **minimizes and flags** residual risk; a human
**clears** it and opens the PR. There is **no autonomous push, PR, or send** to
the public repository, ever. The skill is default **OFF**.

## When to use — the generality gate (or it is slop)

Prepare a contribution only when **both** hold:

1. **Generalizable.** The lesson is a defect-class or method-gap that reproduces
   beyond this one project, reduced to its underlying principle — not a
   project-specific quirk.
2. **Missing from the bar.** The universal skill does not already cover it.
   Re-read the exact target section first; if it is there, there is nothing to
   contribute (prefer the existing bar).

A **project-specific** lesson belongs in that project's own `AGENTS.md` via
`deep-code-review` **Phase 6** (imprint), not upstream. Do not open a
contribution for extra docs, a restyle, or a near-duplicate of an existing
principle — `idea-critic`'s slop-rec rule applies here verbatim.

**Origin.** The lesson usually surfaces at `agentic-delivery` **G10**
(retrospective — "generalized and stripped before it leaves the project") or
during a `deep-code-review`. This skill is the mechanism for the *upstream* case
specifically; it does not restate the generalize-and-strip mandate, it acts on
its output.

## The procedure (depth in the reference)

Map only. Full steps, worked leak examples, and the block template:
`references/contribution-procedure.md` — **read it when** preparing a
contribution.

1. **Detect + test generality** — the two gates above. Fail either → stop, or
   imprint locally.
2. **Generalize** — lesson → underlying principle; strip every project specific.
3. **Draft the full change** — in a checkout of the *public* repository (where the
   gate and the Definition of Done live), write the skill edit + CHANGELOG entry +
   eval + routing to the repo's Definition of Done (`CLAUDE.md`). No half-changes.
   Generalizing and stripping identifiers as you write (step 2) means the files
   already carry no third-party specifics.
4. **Scrub (mechanical floor).** Run the repo's own fail-closed privacy gate on the
   *drafted files*: `bash scripts/ci-gates.sh privacy --banlist .banlist.txt .`
   A hit blocks. This runs on what you actually wrote in step 3 — it is the floor,
   not the ceiling; see Prime constraint.
5. **Route through the bar** — `deep-code-review` on the diff; `idea-critic` on
   the "we should contribute this" claim.
6. **Run all gates green** — the gate list in `CONTRIBUTING.md`.
7. **Assemble the provenance-and-risk block** (below) and **hand to a human.**

## Provenance & risk block (the human signs this)

Every drafted contribution carries this block for the human reviewer. It is the
structural form of "necessary, not sufficient" — a reviewer handed a clean-looking
diff rubber-stamps it; one handed an itemized risk statement checks it.

```
SOURCE (internal only, stripped from the public artifact): <which project/context>
GENERALIZED-AWAY: <the project specifics removed to reach the principle>
RESIDUAL RISK I COULD NOT RULE OUT: <what a pattern scrub cannot clear —
    paraphrased facts, timing, roadmap, structural tells; or NONE, with why>
MECHANICAL SCRUB: <privacy-gate result at the drafted SHA>
```

A block that claims `NONE` for residual risk **without a reason** is rejected the
same way `idea-critic` rejects a generic `strongest_attack_survived`: the point is
to make the human check, not to wave a clean diff through.

## Protected core (immutable to the agent)

The agent drafts into a bounded surface — a branch and the skill files. It
**never**:

- edits the tests, the privacy gate, or the gate thresholds to make its own
  contribution pass (gaming the evaluator — `idea-critic`'s anti-gaming rule);
- pushes, opens, or merges a PR to the public repository;
- deletes an existing instrument to make room for its addition (do-no-harm; the
  review bar's principle 4).

Tests, the privacy gate, and merge authority sit outside the agent's reach by
design. That boundary is what makes "the agent improves the skillset" safe
rather than a loop that drifts.

## Pitfalls

- **Auto-PR / auto-push.** The one unforgivable failure.
- Slop contribution: extra docs, restyle, a second copy of an existing principle.
- Trusting the pattern scrub as sufficient — semantic leaks pass it.
- A `NONE` risk block with no reasoning.
- Contributing a project-specific quirk upstream instead of imprinting it locally.
- Editing a gate, test, or threshold to pass your own contribution.

## Verification

- A planted third-party identifier in a candidate lesson is caught by the privacy
  gate (fail-closed) and never reaches the drafted artifact.
- A project-specific quirk yields "imprint locally, do not contribute", not a PR
  draft.
- A semantic leak that passes pattern-matching is surfaced in the residual-risk
  block, not silently cleared.
- No autonomous push or PR occurs; the human opens it via `CONTRIBUTING.md`.
- `evals/evals.json` plants `third-party-identifier-blocked`,
  `non-generalizable-imprint-locally`, and `no-autonomous-push`.
