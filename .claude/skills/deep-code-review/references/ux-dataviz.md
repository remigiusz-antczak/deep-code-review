# Product UX depth — charts, metrics, scores, and progress displays

Read this when the target or diff renders a chart, sparkline, heat-map or calendar grid, a KPI / metric delta, a confidence / score / priority / tier, an aggregate count badge, or a progress / attainment / ratio tile. Split from `product-ux-quality.md`, whose stance, data-state rules, encoding rules, 🚩 grep, and pre-ship checklist apply to every UI review.

## The metric / KPI delta standard

A near-universal pattern with a right answer (Stripe, Google Analytics, Mixpanel, Amplitude,
Robinhood, Linear, Material) — inventing a novel one here is a cost:
- caret **▲▼** (or arrow ↑↓) **+ the magnitude** (`▲ 3`, `+2.1%`) — direction alone never says
  *how much*;
- colour by **sentiment, not direction** — "up" is not always good; a drop in churn / cost /
  latency / error-rate is **green**. Key the colour to the metric's polarity
  (direction-of-good), not to up/down. Backwards polarity actively misleads — a correctness
  defect, not a taste one;
- muted **`—`** when flat; anchor the delta to its period ("vs last month") in the
  tooltip/`aria`.

## Data visualization — a chart must answer a question, legibly

The delta standard above governs a single up/down number; a **plotted series** is its own surface, and a
chart can pass every other rule here — no overlap, no colour-only status — while still answering no
question ("what is this on that date?" has no on-screen answer) or overstating what is known. Rule each
chart:
- **Scale is legible.** A value axis with tick labels **or** direct labels; a bare shape with no scale
  is decorative, acceptable **only** when explicitly marked decorative (`aria-hidden`) **and** the exact
  number it illustrates is printed beside it.
- **A value + its anchor on demand.** Any non-trivial chart returns, on hover/focus, the **value and its
  date/category**, reachable by keyboard, not mouse-only (`frontend-a11y.md` owns the *a11y* of that
  interaction; this owns that a readout *exists and returns a value*).
- **Don't imply the unmeasured.** Mark real samples (a dot per reading) and never smooth or fill a
  **line across sparse points** — nothing between measured points is implied. Two or three readings
  drawn as a continuous trend (a **sparkline** on a handful of readings is exactly this) is a fabricated
  trajectory, the visual form of principle 3 (empty beats fabricated).
- **A grid / heat-map / calendar cell needs a third state — event, collected-zero, not-collected.** A
  per-cell colour scale painting an **uncollected** cell the same as a genuine **zero-activity** cell
  fabricates data: the viewer reads "quiet" where the truth is "unknown / not yet observed." Give the
  not-collected cell a distinct, non-scale encoding (hatch / blank / explicit "no data"), never the low
  end of the activity ramp — the grid form of *Every data state*'s honest-empty rule in `product-ux-quality.md` and of
  *observed-low vs unobserved* (`data-freshness.md`).
- **Non-visual access to the numbers.** The chart is *additive* to a table or an `aria` summary, never
  the only path to the data; series are distinguished by pattern/label, not colour alone (*Never colour
  alone*, `product-ux-quality.md`).

## Confidence shown as a bare number is false precision — flag it

A confidence, priority, or match score surfaced as a **raw number** ("87%", "score: 0.92") claims a
calibration the pipeline usually doesn't have, and invites over-trust. It belongs on a **small set of
labeled tiers** — text plus a colourblind-safe cue (see *Never colour alone*, `product-ux-quality.md`) — not a percentage or an
opaque point score. **🚩**: a `confidence` / `score` / `priority` value rendered directly as `{n}%` or a
raw float with no defined tier label beside it; a model-authored number published as precision. (How to
*define* the tiers, and why source reliability and claim corroboration stay independent axes, is a
data-product-output rule — `product-output-safety`'s — not restated here.)

**Measure the field's distribution before building the display at all.** Even a *tier* is false
precision if the underlying signal is **near-constant** — measure it first, on real data. A
`corroborationCount` that is `1` on 16,008 of 16,012 rows makes a "confirmed by N sources" badge fire on
~0.02% of rows and read "1 source" everywhere else; a match-confidence that is `0.9` on ~70% of rows and
`0.8` on the rest is effectively binary, so "90% / 80% confidence" manufactures precision the pipeline
lacks. If the field barely varies, **showing it is false precision, not transparency** — drop it, or
reframe to something that actually varies (e.g. *how* an entity was matched, not a number). A misleading
signal is worse than an honest blank — empty beats fabricated (`data-quality.md`).

## A rendered tier / score / aggregate encoding must invert to its source rows

A confidence tier, match label, or **aggregate visual encoding** — a sparkline tick, heat-map cell,
count badge, rolled-up score — asserts something about **specific underlying rows**, so it must
**invert**: the viewer can resolve it back to the exact source it summarizes. Compute the continuous
intermediate if you like, but **publish only the tier** (the confidence-tier rule above); the acceptance
test is separate — **can the rendered mark be drilled through to the N artifacts that produced it?** A
tier or cell mapping to nothing checkable is decoration wearing a data costume: a real 5-event cell is
indistinguishable from an off-by-one, and no one can audit the roll-up. Applies to **aggregate**
encodings, not only per-row chips — a `count: 12` badge, a sparkline's last tick, a calendar heat cell
each owe a path to their 12 / reading / day's events. Orthogonal to the *decorative-chart* exemption
above (`aria-hidden` with its exact number printed beside it is fine for **legibility**): invertibility
then applies to that printed number/tier itself — not a second drill-path on the decorative shape.
**🚩**: a score / tier / sparkline / heat cell / count with no drill-through to the exact rows it
aggregates (un-invertible — can't be verified or corrected).

## A progress/attainment display with no honest reading is a fabricated "done" — show coverage, not a grade

When a product visualizes **progress toward goals**, constant pressure pushes an **attainment %** or
**grade** even when honest inputs don't exist — no current reading, no ratified rule for *which* metric
counts, an undefined lower-is-better direction. **Distinct from the confidence-tier rule above**: there
a reading *exists* but is shown with false precision; here **no honest reading exists at all**, so any
attainment number fabricates a "done." Review lens: "what's the denominator/rule, and is the current
value **measured** or **inferred**?" The honest alternative is **coverage/readiness** — "**N of M** key
results are measurable/instrumented" — computable without inventing a reading (given an enumerable M and
a defined "measurable"); where a reading is genuinely absent, render **"awaiting reading / not yet
measurable"** (an honest empty state, per *Every data state* in `product-ux-quality.md`), never a manufactured value.
- **Enforce it structurally, not by convention.** A write-broker/observation gate that **refuses** (e.g.
  `422`) any claim asserting attainment or on-track status the system can't substantiate, so no path —
  human or agent — sneaks a fabricated grade in; and a **contract/doc stating "attainment is out of
  scope"** so a later "add progress bars" ask is triaged as *ratify a rule first*, not a quick UI edit.
- A display that would honestly render **"awaiting reading" on nearly every row is worse than no
  feature** — hold it (a legitimate BLOCKED-ON-OWNER: ratify the rule and instrument the inputs first)
  rather than ship a fabricated grade to fill it.
- **A ratio/coverage tile guarded by `total > 0 ? round(done / total * 100) : 0` renders a fabricated 0%
  for an *empty population* — "nothing to do" is drawn as "none done."** Mirror of the no-honest-reading
  rule above: there no current value exists, so *any* percent fabricates a "done"; here `done` and
  `total` are both real and measured, but the population is **empty** (`total === 0`), so the ternary's
  `: 0` sentinel paints a hard **0%** — the same alarming treatment a genuinely-behind row gets — when
  the honest reading is **not-applicable**: nothing to complete, not work left undone. The guard *looks*
  correct — it prevents a `NaN`/`Infinity` divide-by-zero, clears review, type-checks, never throws —
  the defect is its fallback **value** reads as an attainment, and seed/demo data usually has a non-zero
  `total`, so the empty branch rarely renders in dev. Fix: branch the *empty* denominator to a
  **non-numeric** state — `N/A`, a muted `—`, "nothing to do" — and reserve `0%` for
  `total > 0 && done === 0`, the real "has items, none done" a user can act on; a `100%`-for-empty
  fallback is the same fabrication, opposite sign. **Distinct** from the no-honest-reading rule above
  (reading *absent* — show coverage) and the honest-empty *list* rules under *Every data state* (`product-ux-quality.md`)
  (filtered vs genuinely-none over **rows**) — this is a **scalar ratio tile** whose zero denominator,
  not a hidden row, is the trap. **🚩**: a percentage/progress/ratio render whose denominator can be
  zero, guarded by `total > 0 ? … : 0` (or `|| 0` / `?? 0`), whose fallback renders as a real percentage
  rather than not-applicable.
- **🚩** a `%-complete` / grade / progress bar with no measured current value (a fabricated "done"); an
  attainment number the pipeline can't substantiate rendered instead of an "awaiting reading" state or a
  coverage ("N of M measurable") metric.
