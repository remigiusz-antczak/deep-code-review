---
name: positioning
description: >-
  Use when shaping how a product is positioned and described to its market —
  the value proposition, the target segment, the differentiation, the
  messaging — with the Value Proposition Canvas, a positioning statement, and
  a message house, always built on the USER's own inputs and validated with
  real buyers. Produces a hypothesis to test, never asserted market truth: it
  never fabricates market size / TAM, competitor claims, customer quotes,
  outcome numbers, or trademark / domain clearance — those route to the user
  or a licensed professional. Distinct from product-discovery (whether
  something is worth building) and growth-analytics (measuring usage). Opt-in
  overlay, default off; install with --with-positioning.
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.0.0"
---

# Positioning

Shape how a product is described to its market — value proposition, segment,
differentiation, message — as a **hypothesis the user validates**, never as
market truth the model asserts. This is the highest fabrication-risk area in the
suite (no ground truth lives in the repo or the model), so the guardrails are the
point, not an afterthought.

Persisted artifacts stay normal English. Chat may be terse.

---

## The boundary (what this is, and is not)

- **vs `product-discovery`:** discovery establishes *whether* there is a problem
  worth solving (evidence from real users). This shapes *how you describe* the
  solution to the market once that problem is real.
- **vs `growth-analytics`:** that measures what users do. This decides what you
  *say* to get the right users to try it.
- **Not** a source of market facts. Frameworks here yield a **hypothesis**; the
  evidence — that buyers agree, that the name is legally usable, that a claim is
  true — comes from **outside the model**.

## Prime directive — a framework yields a hypothesis, not a fact

Every output of this skill is a **hypothesis to test with real buyers**, phrased
as such. The failure mode is a confident, fabricated market "fact" — a TAM, a
competitor weakness, a customer quote, an outcome statistic, a "the name is
clear" — that reads as researched and becomes a decision the user pays for.

- **Never fabricate** market size / TAM, market-share or competitor claims,
  customer quotes or testimonials, outcome / ROI numbers, or trademark / domain
  availability or clearance.
- **Empty-slot templates, not plausible fills.** Asked for a positioning artifact
  with no user input behind it, return the **template with the slots to fill and
  how to obtain each** (which customers to ask, which data to pull) — never a
  realistic-looking example, which becomes fake evidence.
- **Route the unknowable.** TAM and market data → the user's real research;
  trademark / domain clearance → a search is *not* legal clearance, route to a
  professional; any factual claim in a message → the user's own proof. Never
  conclude these in the model.

## The method (on the user's own inputs)

### 1. Value Proposition Canvas
Map the **customer profile** (jobs, pains, gains — from real discovery, not
imagined) against the **value map** (pain relievers, gain creators). The fit is a
hypothesis until buyers confirm it. If the customer profile has no evidence
behind it, that is a discovery gap — route to `product-discovery`, do not invent
the profile.

### 2. Positioning statement
One structured hypothesis: *for [segment] who [need], [product] is a [category]
that [key benefit]; unlike [alternative], it [differentiator].* Every bracket is
the user's input or a flagged unknown — never a fabricated segment, benefit, or
competitor. Label it explicitly as a hypothesis to validate.

### 3. Message house
One core message, a few supporting pillars, and **proof under each pillar**. Proof
points are the user's real evidence (a shipped capability, a measured result the
user supplied); a pillar with no proof is marked `UNVERIFIED — needs proof`, never
propped up with an invented stat or quote.

### 4. Validate with real buyers
The positioning is a hypothesis until real buyers in the segment react to it
(message testing, sales conversations, landing-page signal). Design the test;
interpret the user's results; never report a reaction that was not gathered.

## Stage-awareness — the minimum-viable-brand rule
Keys to the stage model in `deep-code-review`. **Pre-PMF: a minimum viable brand.**
A name, a one-line value prop, a clear category — enough to test. Over-investing in
brand identity, visual systems, or a messaging bible before product-market fit is a
documented failure mode; premature scaling of positioning is the over-engineering to
stop. `growth`/`mature`: invest as the segment and message are proven.

## Definition of done
- Every artifact is the user's own inputs, structured, or an empty-slot template
  with how-to-obtain — never a realistic fabrication.
- The positioning statement is labelled a **hypothesis to validate**, not a fact.
- No TAM, competitor claim, customer quote, or outcome number the user did not
  supply; message pillars without proof are `UNVERIFIED`.
- Trademark / domain clearance is routed to a professional, never asserted.
- Pre-PMF work is held to a minimum viable brand.

## Anti-rationalization (excuse → rebuttal)

| Excuse | Rebuttal |
|---|---|
| "Estimate the TAM so the pitch has a number." | TAM is outside the model. Return the slot + how to size it from real sources; never print a figure. |
| "Write a couple of customer quotes as examples." | A quote is evidence the moment it is read. Empty-slot template; the user supplies real quotes. |
| "Say we're faster / cheaper than [competitor]." | A competitor claim needs the user's evidence. Mark it `UNVERIFIED — needs proof`, do not assert it. |
| "Is this product name free to use?" | A search is not legal clearance. Route to a trademark professional; never say "clear". |
| "Build the full brand system now." | Pre-PMF, that is premature scaling. Minimum viable brand until the segment and message are proven. |

## Standards (by name; verify a figure/URL before citing one)
Value Proposition Canvas and business-model design (Osterwalder & Pigneur);
positioning (Ries & Trout; and April Dunford's obviously-awesome positioning);
the message house / messaging framework; jobs-to-be-done as a positioning lens;
brand strategy and minimum-viable-brand. Named leads only — fetch and log a source
before citing a specific figure or claim (repo convention). Discovery inputs come
from `product-discovery`; output structure follows `communication-structure`.

## Verification
- A TAM / competitor-fact request yields an empty-slot template + how-to-obtain,
  never an invented figure (`refuses-fabricated-market-facts`).
- A positioning statement is returned as a labelled hypothesis to validate, not an
  asserted truth (`positioning-is-a-hypothesis`).
- A request for customer quotes / outcome stats with no data is refused with slots,
  never fabricated (`no-invented-quotes-or-outcomes`).
- "Is this name/domain clear?" is routed to a professional; a search is not
  clearance (`trademark-clearance-routed`).
- `evals/evals.json` plants these cases.
