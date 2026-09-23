# Data quality depth — the provider seam and percent units

Read this when the target or diff ships data another system consumes for scoring or automation (aggregates vs raw events, delivery cadence, per-field source of truth), or converts or renders a fraction, percent, or ratio. Split from `data-quality.md`, whose core checks (monotonic writes, provenance, units, nulls, joins and keys, dedupe, freshness, idempotent writes) apply to every data review.

## Percent units (depth of `data-quality.md` §4)

- **A percent-unit guard needs an upper bound, not just a lower one.** A guard written to catch an
  unconverted 0–1 fraction rendered under a percent unit (`0.5` shown as `0.5%` instead of `50%`)
  typically checks only a **lower** bound (`value < 1` ⇒ needs `* 100`); with no **upper** bound it
  is asymmetric by construction, and a value that lands **above 1** — a metric whose semantics can
  legitimately exceed 100% (an attainment, ratio, or index that can run over par), or an accidental
  **double conversion** (`0.5 * 100 * 100` = `5000`) — sails straight through and renders wildly
  wrong with **no error**. Extend the guard to a **plausible range check with a sane upper bound
  for that metric's own semantics**, and fail loud (flag, don't silently clamp) outside it. The
  question that sets the bound is: **can this metric legitimately exceed 100%?** — if no, cap at
  100 and treat anything above it as the same class of bug as the unconverted fraction below 1; if
  yes, name the ceiling the domain actually supports instead of leaving the guard one-sided.

## The provider seam (depth of `data-quality.md` §12)

- **A provider that feeds another system's scoring / automation owes the consumer's
  *inputs*, not its own raw output.** When the product's job is to be a data provider
  (its output is another system's scoring or automation input), the contract seam has
  four failure modes no shape-only check catches: (1) it **emits raw events when the
  consumer needs scoring inputs** — the consumer's rubric wants windowed aggregates and
  velocity ("≥2 events in 90d," a top-decile proxy), keyed on the **consumer's canonical
  ids** and carrying provenance + license/tier, not discrete triggers the consumer must
  re-aggregate (a join it does not want to own); (2) **static / manual delivery** (a
  hand-run dump) where the consumer needs a **live channel + cadence** (a table/feed read
  on a schedule); (3) **no per-field source-of-truth declaration** (authoritative /
  partial / never) — so the consumer wires fields the provider never ships and expects
  data it does not own; (4) **a claimed input stale or misclassified vs the provider's
  live artifact** — reconcile **every** claimed provider-input (count *and*
  classification) against the provider's current output **before it drives a downstream
  score/decision** (a pre-reclassification blend that inflated a category ~100× can
  silently drive a network-wide score). Pair with a gate: diff the consumer's declared
  provider-inputs against the provider's actual current output; a mismatch blocks
  sign-off. (Shape lives in `api-contracts.md` consumer-driven contract; this is the
  quality / semantics half at the provider seam.)

**🚩 red flags** (this file):
a data provider that ships raw events where the consumer scores on aggregates, or a claimed provider-input never reconciled against the provider's live output before it feeds a downstream score;
a percent-unit guard with a lower bound only, so a value above 1 (legitimate over-100% semantics, or a double conversion) renders wrong with no error;
