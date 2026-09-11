---
name: product-discovery
description: >-
  Use when deciding whether something is worth building, what to build
  first, or whether what already shipped is working — by structuring
  evidence gathered from real users and real usage, never by asserting
  it. Designs Mom-Test / Jobs-to-be-Done interviews and fake-door /
  concierge experiments, runs the riskiest-assumption gate before a
  build, reads product-market fit from the very-disappointed survey and
  retention cohorts, and prioritizes with ICE — always on the user's own
  inputs. Never fabricates findings, quotes, personas, market size,
  scores, or a "validated" verdict; routes what it cannot know to the
  owner. Opt-in overlay, default off; install with --with-discovery.
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.0.0"
---

# Product discovery

Structure the outside evidence that says whether to build, what to build
first, and whether what shipped works. A coding agent now builds the
*wrong thing* faster than ever; the seat it does not fill is "is this
worth building?" This skill fills that seat with method, not opinion.

Persisted artifacts stay normal English. Chat may be terse. Do not vendor
a voice skill here.

---

## The boundary (what this is, and is not)

- **vs `idea-critic`:** the critic attacks a claim *you already hold*,
  from the inside, before it reaches the owner. This skill structures the
  *outside* evidence — real users, real usage — that says whether the
  claim is true. The critic reasons; discovery gathers and reads.
- **vs the coding agent / `deep-code-review` / `agentic-delivery`:** those
  build and harden the thing. This decides *whether and what* to build,
  and *whether it worked* — before and after the build, not during.
- **Not** market research you can invent, a business plan, or a substitute
  for talking to users. It designs the research the **user runs** and
  interprets what the user brings back.

## Prime directive — evidence comes from outside the model

The failure mode this skill exists to kill is **fabricated validation**: a
fluent, realistic-sounding finding, persona, quote, market number, or
"validated" verdict that the model invented and that then becomes fake
evidence a real decision is built on. A fluent fabrication passes a human
skim and an LLM judge; only a hard rule stops it.

- **Never invent** interview findings, customer quotes, personas, market
  size / TAM, competitor facts, adoption numbers, or a PMF verdict.
- **Refuse to emit an "example finding."** When asked for a finding,
  persona, or result with no user data behind it, return an **empty-slot
  template** with the slots the user must fill and *how to obtain each* —
  never a plausible-looking fill. A realistic example is the fabrication.
- **A scoring table has blanks, not guesses.** Own the question,
  structure, and arithmetic; **route for every input**; never print a
  reach/impact/confidence number the user did not supply.
- **Route the unknowable.** Market size, competitor claims, legal/tax
  questions, anything the repo and the user do not hold → real research or
  a licensed professional. Surface it as a routed open question; never
  conclude it. Empty beats fabricated.

## The four moves

### 1. Riskiest-assumption gate (before you build)
Name the assumptions the idea depends on (desirability, viability,
feasibility, usability). Rank by **impact × uncertainty**. Take the single
riskiest, and define the **cheapest test that could disconfirm it**. If
that test has not been run, the output is a **refusal to build yet**: name
the assumption, name the cheap test, run it first. Stage-aware — at
`prototype`/`mvp` this gate dominates; a coding agent building polished
infra on an untested assumption is the over-engineering to stop.

### 2. Discovery interviews (design, then interpret)
Design the interview guide and interpret the transcripts the **user runs**:
- **The Mom Test** — ask about past specific behavior, not future
  hypotheticals; never pitch; dig for what they already do and pay for.
- **Jobs-to-be-Done switch interview** — the four forces (push of the
  situation, pull of the new, anxiety, habit) around a real recent switch.
- **Continuous discovery** (opportunity–solution tree) — a habit, not a
  one-off; map opportunities before solutions.
The skill produces the guide and structures the user's real answers. It
**does not** invent quotes or synthesize a persona from nothing.

### 3. Cheap experiments (behavioral evidence, not stated intent)
Design fake-door, concierge, and Wizard-of-Oz tests so the signal is what
users *do*, not what they *say*. Define the metric and the disconfirming
threshold **before** the test. Interpret the user's real results; never
report a result that was not measured.

### 4. Read the state honestly
- **PMF read:** the "very-disappointed" survey (share who would be very
  disappointed to lose it — a commonly-cited signal threshold; verify the
  exact figure before asserting it) **and** a **flattening retention
  cohort** (the strongest early signal). PMF is an **empirical threshold
  on the user's real data** — never declared from a conversation, a demo,
  or vibes. Without the data, the verdict is `UNVERIFIED`.
- **Prioritization:** **ICE** (Impact × Confidence × Ease) over RICE for a
  solo/small builder — fewer inputs to source. The table ships with
  **blank inputs and a how-to-obtain note per column**; the user supplies
  the numbers, the skill does the arithmetic and orders the list.

## Stage-awareness
Keys to the stage model in `deep-code-review` (the `STAGE` field and the
*Project stage* section). `prototype` → riskiest-assumption + discovery
dominate; hold polish and infra. `mvp` → first PMF read begins; instrument
the one question that matters. `growth` → retention cohorts + prioritization
drive the backlog. `mature` → discovery continues for new bets; do not let
it justify gold-plating the core.

## Definition of done
- Every output is either the **user's own evidence, structured**, or an
  **empty-slot template** with how-to-obtain each slot — never a realistic
  fabrication.
- No interview finding, quote, persona, market number, or PMF verdict that
  the user did not supply or that real data did not establish.
- Scoring tables carry blank inputs + sourcing notes, never invented
  numbers.
- The riskiest assumption is named with the cheapest test before any
  build-recommendation.
- Unknowable inputs are routed (owner / real research / professional), not
  concluded. Uncertainty is surfaced, not smoothed over.

## Anti-rationalization (excuse → rebuttal)

| Excuse | Rebuttal |
|---|---|
| "Just fill in a plausible persona / quote to illustrate." | An illustration becomes evidence the moment it is read. Return an empty-slot template, not a fill. |
| "Estimate the ICE / reach numbers to move fast." | Invented inputs produce a confidently wrong order. Blanks + how-to-obtain; the user supplies the numbers. |
| "The demo felt great, call it product-market fit." | PMF is a threshold on real retention / survey data, not a feeling. Without data, `UNVERIFIED`. |
| "Give me the market size so we can decide." | Market size is outside the model. Route to real research; never print a TAM you cannot source. |
| "Skip the assumption test, we're confident." | Confidence is the thing under test. Name the riskiest assumption and the cheapest test; build after, not instead. |

## Standards (by name; verify a figure/URL before citing one)
The Mom Test (Fitzpatrick); Jobs-to-be-Done and the switch interview /
four forces (Christensen; Moesta & Spiek); continuous discovery and the
opportunity–solution tree (Torres); the riskiest-assumption test and
experiment design (Bland & Osterwalder, *Testing Business Ideas*);
fake-door / concierge / Wizard-of-Oz experiments; the "very-disappointed"
product-market-fit survey (Ellis); retention cohort analysis; ICE and RICE
prioritization. Named leads only — fetch and log a source before citing a
specific figure or URL (repo convention; nothing added to
`docs/standards-index.md` unfetched).

## Verification
- A request for a finding / persona with no user data yields an empty-slot
  template, never a realistic fabrication (`refuses-example-finding`).
- A prioritization request yields a table with blank inputs + sourcing
  notes, never invented scores (`no-invented-scores`).
- "Do we have PMF?" from a conversation is not answered "yes"; it requires
  survey + retention data or returns `UNVERIFIED` (`pmf-not-declared-from-chat`).
- A build request on an untested riskiest assumption returns a refusal
  naming the assumption + the cheap test (`riskiest-assumption-gate`).
- A market-size / competitor-fact request is routed, not fabricated
  (`routes-unknowable-to-owner`).
- `evals/evals.json` plants these cases.
