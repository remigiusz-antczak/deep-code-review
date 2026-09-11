---
name: growth-analytics
description: >-
  Use when deciding what to measure and how to read it once you are building
  or shipping: choosing the one customer-value North Star metric (not a vanity
  count), reading the AARRR funnel bottom-up (retention first), designing the
  event taxonomy that answers a named question, and deciding what to instrument
  at each stage. Works on the user's own analytics data; never fabricates
  benchmarks, metrics, or "good" thresholds, and routes real figures to the
  user's analytics. Distinct from product-discovery (which decides whether to
  build and reads the product-market-fit threshold) and from the ops
  observability reference in deep-code-review (system health, not product
  behaviour). Opt-in overlay, default off; install with --with-growth.
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.0.0"
---

# Growth analytics

Decide what to measure, and read it honestly, once the product is being built
or shipped. The failure this kills is a dashboard full of numbers that rise
while the business does not: vanity metrics, instrument-everything noise, and
invented "good" thresholds. Measure the user's own data against the user's own
baseline; never assert a benchmark the model cannot source.

Persisted artifacts stay normal English. Chat may be terse.

---

## The boundary (what this is, and is not)

- **vs `product-discovery`:** discovery decides *whether* to build and reads
  the **product-market-fit threshold** (a verdict). This runs the *standing*
  measurement system afterward — the North Star, the funnel, the event
  taxonomy, what to instrument as the product grows.
- **vs `deep-code-review`'s `observability.md` (domain M):** that is **system
  health** — logs, traces, error rates, SLOs. This is **product behaviour** —
  what users do. They meet at one seam (below); do not restate ops observability
  here.
- **Not** a source of market benchmarks, and not the user's analytics tool. It
  designs *what to measure and how to read it*; the figures live in the user's
  analytics.

## Prime directive — the user's own data, never invented

- **No fabricated benchmarks.** Never assert "good retention is X%", "average
  conversion is Y%", or a competitor's numbers. Compare the user's metric to the
  **user's own prior baseline and trend**, not to a number the model made up.
- **No invented metrics.** A metric with no instrumentation behind it is
  `UNVERIFIED`; say so and name what to instrument, do not estimate the value.
- **Route real figures to the user's analytics.** "How are we doing?" is
  answered from the user's data; without it, return the *question to run*, not a
  number.

## The method

### 1. One North Star (customer value, not vanity)
Pick a single metric that rises only when a user gets **real value** and that
the business depends on (e.g. weekly active users completing the core action;
value delivered, not pageviews or raw signups). Vanity metrics (cumulative
signups, pageviews, downloads) go up regardless and mislead — reject them.
Pair the North Star with a small set of input metrics that move it.

### 2. Read AARRR bottom-up (retention first)
Acquisition → Activation → **Retention** → Revenue → Referral, but *read and
fix from the bottom*: retention leaks make acquisition spend wasted. Diagnose in
order — is the core action retained? then activated? then acquired? Pouring
acquisition into a leaky retention bucket is the classic waste.

### 3. Event taxonomy that answers a named question
Instrument **only what answers a question you can name** ("do users return to
the core action in week 2?"). Every event has a documented name, the question it
answers, and its properties. Not instrument-everything — unused events are cost
and noise. **The identifier seam:** product cohorts need a **stable per-user
identifier** (to follow a user across sessions) — this *inverts* the ops rule in
`observability.md`, which avoids high-cardinality per-user labels; state the seam,
do not restate observability. Keep that id **pseudonymous**; route PII, consent,
and retention limits to `deep-code-review`'s `privacy-compliance.md` (domain Q).

### 4. Instrument for the stage (do not over-measure early)
- `prototype` → almost nothing; talk to users (that is `product-discovery`).
- `mvp` → activation + retention of the **core action**, and the one question
  that tells you it is working.
- `growth` → the full funnel, the North Star + inputs, retention cohorts,
  experiment read-out.
- `mature` → guardrail metrics, an experimentation platform, and metric
  governance (retire dead events; one definition per metric).

## Stage-awareness
Keys to the stage model in `deep-code-review` (the `STAGE` field and *Project
stage*). Early, less instrumentation is correct; the cost of a metrics stack on a
`prototype` is the over-engineering to stop. `growth` is where the scoreboard
earns its keep.

## Definition of done
- One customer-value North Star named (vanity metrics rejected), with input
  metrics that move it.
- The funnel is read bottom-up (retention before acquisition).
- Every proposed event names the question it answers; nothing instrumented "just
  in case".
- No benchmark, threshold, or metric value is asserted that the user's data did
  not supply; unknowns are `UNVERIFIED` and routed to the user's analytics.
- The identifier seam and PII routing are stated, not restated from
  `observability.md` / `privacy-compliance.md`.

## Anti-rationalization (excuse → rebuttal)

| Excuse | Rebuttal |
|---|---|
| "What's a good retention rate?" | Not a number the model can source. Compare to the user's own baseline and trend; route to their analytics. |
| "Track everything so we have it later." | Unused events are cost and noise. Instrument only what answers a named question. |
| "Signups are up — we're growing." | Signups are vanity; they rise regardless. Read retention of the core action first. |
| "Estimate our conversion so the deck is done." | An un-instrumented metric is UNVERIFIED. Name what to instrument; do not invent the value. |
| "Use the raw user id for cohorts." | Cohorts need a *stable* id, but keep it pseudonymous; route PII/consent to `privacy-compliance.md`. |

## Standards (by name; verify a figure/URL before citing one)
AARRR / "Pirate Metrics" (McClure); the North Star Metric framework;
vanity-vs-actionable metrics; retention cohort analysis; "one metric that
matters"; activation / aha-moment analysis. Named leads only — fetch and log a
source before citing a specific figure or threshold (repo convention). The
product-analytics vs ops-observability identifier seam is described in
`observability.md` (domain M); privacy of user identifiers in
`privacy-compliance.md` (domain Q).

## Verification
- "What's a good retention rate?" is answered from the user's baseline, never a
  fabricated benchmark (`no-fabricated-benchmarks`).
- A North Star request rejects vanity metrics for a customer-value metric
  (`north-star-not-vanity`).
- "What should I track?" instruments only what answers a named question
  (`instrument-answers-a-named-question`).
- "How are we doing?" routes to the user's analytics / returns `UNVERIFIED`
  without data, never an invented number (`routes-real-figures-to-analytics`).
- `evals/evals.json` plants these cases.
