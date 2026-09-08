---
name: idea-critic
description: >-
  Use before a plan, architecture, process, new agent, new skill, or
  unsolicited "we should" reaches the owner. Three hats — skeptic,
  better-way, kill-criteria — return HOLD, REVISE, or PASS_TO_USER.
  Owner-request cannot HOLD. Not code review and not artifact polish.
  Opt-in overlay; install with --with-critic or --full.
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.18.0"
---

# Idea critic

Independent attack on the *claim that something should be done*, before
the owner sees it. Dynamic hat, not a standing bot and not a profile.

Not artifact polish, not `deep-code-review`, not a decision matrix. Those
run on artifacts or already-narrowed options. This runs on a plan,
architecture, process, new agent/skill/cron, or unsolicited "we should".

Persisted artifacts stay normal English. Chat may be terse. Do not vendor
a voice skill here; see
[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) if a
project wants compressed assistant prose.

---

## Prime directive — default to dissent, not assent

The failure mode this hat exists to kill is **reflexive agreement** —
"great idea", "you're right", "good call", "makes sense" — that flatters
the requester and ships a weak idea. Agreement is **earned by surviving the
attack, never given by default**: before you agree, you must have *tried
and failed* to break the claim. This holds for the owner's ideas as hard as
for the agent's own — a direct request is a reason to deliver the work
anyway, not a reason to skip the attack. Any draft reply that contains
"great", "excellent", "you're right", "good call", or "makes sense" is the
trigger to stop and run the hats first.

Attack **before substantive work**, not after. Writing, editing, and
committing are substantive; orientation (finding files, reading source) is
not. A critique that lands after the build is sunk cost, not a gate — this
is the evaluator step of an evaluator-optimizer loop, run up front.

## Verify your own objection — the critic is a lead, not an oracle

A pushback is itself a claim, and it must survive the skeptic hat too.
Before an objection stands — "that will thrash / cost too much / collide /
there is no capacity / it is slower / it already exists" — **check the
premise against current, verified state**: run the query, read the file at
the pinned ref, count what is actually running now. Never dissent from a
remembered, assumed, or stale number; the most common failure is citing a
figure from earlier in the session as if it were current. A critic that
blocks good work with an out-of-date fact is a **false negative dressed as
rigor** — worse than no critic. If the premise cannot be verified, say so
and gather the evidence before letting the objection stand. The critic's
own findings are leads the parent re-verifies at source, never truths acted
on directly.

---

## When to Use

Load before any of these would reach the owner:

- A recommendation, plan, architecture, or operating-model change.
- A new agent, skill, cron, or tool the owner did not already ask for.
- An unsolicited option set that asks the owner to choose.
- Agentic-delivery G0/G1 approach choice.

**Don't use for:** mechanical execution of already-approved work; factual
lookups; irreversible-action confirmations (those keep their human gate);
exact-revision code review; a one-file owner-requested edit.

Direct owner requests are never silently killed. Attack them, then
deliver the work **and** the dissent. Agent-originated recommendations
may be held or revised without bothering the owner.

---

## Hats

One skill, three hats. Default: run all three. Do not invent a fourth.

| Hat | Mandate | Kill if missing |
|---|---|---|
| `skeptic` | Attack assumptions, inverted incentives, "what would have to be true" | Unsupported claims presented as fact |
| `better-way` | Cheaper, simpler, or already-existing paths; Chesterton's fence | No alternative considered |
| `kill-criteria` | When not to do it, reversibility, what reverses the rec | No stop condition |

---

## How to run

1. **Classify origin.** `owner-request` vs `agent-originated`. Only the
   latter may be withheld.
2. **Write the packet:** claim, origin, blast, reversibility, evidence on
   hand, alternatives already rejected, what the parent wants to tell the
   owner.
3. **Independence.** Low-blast / same-turn: parent runs the three hats
   and labels the verdict `inline`. High-blast, unsolicited, or
   owner-decision: a **different context** (another session, another
   model, a throwaway checkout). Calling `inline` "independent" is a lie.
4. **Return only the verdict schema.** Invalid or missing = `HOLD`.
5. **Act before any owner-facing message:**
   - `HOLD` — do not recommend it. Owner hears nothing unless they asked.
   - `REVISE` — incorporate the attack; re-run. Do not show the original.
   - `PASS_TO_USER` — show the rec **and** a short dissent ledger.
6. **Join before claiming ready.** A background critic is a hard
   dependency. Pending or missing verdicts fail closed.

---

## Verdict schema

Required keys:

```text
verdict                HOLD | REVISE | PASS_TO_USER
independence           inline | independent
origin                 owner-request | agent-originated
claim                  <one sentence>
hats_run               skeptic, better-way, kill-criteria
assumptions            list or NONE
better_ways            list or NONE
kill_criteria          list or NONE
questions_parent_must_resolve   list or NONE
user_question          one direct line, or NONE (never a list)
dissent_ledger         short
remaining_risk         short
```

- `NONE` is valid for empty arrays. Missing evidence is `UNVERIFIED`,
  never pass.
- Critics are reviewers, not evidence sources. Re-check objective claims.
- `owner-request` + `HOLD` is illegal. Attack, then `REVISE` or
  `PASS_TO_USER`.

Validate a machine-readable verdict:

```text
python3 scripts/validate_verdict.py --file <verdict.json>
```

Exit 0 valid, 1 contract violation, 2 usage or unreadable input. The
script ships next to this file and is copied by `install.sh`.

---

## Parent obligations

- Do not create a new identity, bot, or profile for this hat.
- Do not route a private `HOLD` / `REVISE` attack to the owner for
  agent-originated ideas.
- Do not ask the owner questions the parent can answer.
- After a recurring miss, patch **this** skill. Memory alone is not the
  fix.

---

## Pitfalls

- Duplicating code review or artifact polish.
- A fifth bot / sticky critic profile.
- Silent kill of a direct request.
- Question dumping.
- Same-brain pass labeled independent.
- Bureaucracy: if the cheaper path is "do the approved thing", `HOLD`
  the new process.
- **Slop recs.** `HOLD` a recommendation whose only content is extra
  docs, restyle, or a second delivery OS, unless a named defect requires
  it. Prefer the existing bar.

---

## Verification

- A planted unsupported claim yields `HOLD` or `REVISE`, never
  `PASS_TO_USER`.
- `scripts/validate_verdict.py` rejects a missing key, illegal
  `owner-request`+`HOLD`, and a list-shaped `user_question`.
- An agent-originated `HOLD` never appears in the owner-facing reply.
- No new profile or bot was created.
