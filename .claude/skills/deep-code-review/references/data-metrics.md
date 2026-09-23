# Data quality depth — measuring the outcome

Read this when the target or diff measures its own output quality or enrichment lift, aggregates a sampled event stream, validates a score against labels or ground truth, or reports a per-group ratio (per team, segment, or cohort). Split from `data-quality.md`, whose core checks (monotonic writes, provenance, units, nulls, joins and keys, dedupe, freshness, idempotent writes) apply to every data review.

## Per-group ratios (depth of `data-quality.md` §4)

- **A per-group ratio's numerator and denominator must share one membership rule for a shared
  entity.** Denominator integrity (`data-quality.md` §4) is a **single-metric** property — is the failing type in
  the base at all. A **per-group** rate/score (a per-team, per-segment, or per-cohort ratio) has a
  distinct failure no single-row check can see: when the **numerator** attributes a shared or
  ownerless entity's failure under a **broad fan-out** rule (every group it touches gets charged)
  while the **denominator** attributes membership under a **strict single-owner** rule for that
  same entity, an ownerless entity has no single owner to credit — so it is **charged to every
  group's numerator while sitting in no group's denominator**, inflating the ratio for every group
  it fans out to (and leaving it **undefined** — divide-by-zero — for any group whose entities are
  *all* shared/ownerless, since the strict rule credits that group nothing). Each row's own
  increment is individually correct, which is why no single-row check catches it. Fix: derive the
  numerator and the denominator from the **same** attribution/membership rule for the same entity —
  both fan-out, or both single-owner, never mixed. Minimal-proof construction: one shared failing
  entity E with no single owner, fanning out to groups A and B (A otherwise has 8 owned entities
  with 1 failing; B has 6 owned entities with 1 failing). Hand-compute the ratio both ways: under
  the **mismatched** rule (E's failure fans into both numerators; E is excluded from both
  denominators since it has no owner) A reads 2/8 = 25% and B reads 2/6 ≈ 33%; under the
  **matched** fan-out rule (E also counted in both denominators) A reads 2/9 ≈ 22% and B reads
  2/7 ≈ 29% — both ratios move once numerator and denominator agree, proving the mismatch inflates
  every group that shares the entity.

## Measuring the outcome honestly (depth of `data-quality.md` §8)

- Measure enrichment **lift on the subset that actually surfaces to users**, not
  total fill rate — filling fields on records nobody sees moves no outcome.
- **A sampled event stream must record each event's inclusion probability and reweight before
  aggregating.** Sampling is fine — often *preferred*, to cheaply buy precision on a rare outcome
  (case-control / stratified sampling) — but a rate from **raw** sampled counts is biased whenever
  the rate differs by stratum (keep 100% of errors, 10% of successes → the naive success rate reads
  far too low). The fix is **not** "sample uniformly": every retained event carries a **known
  inclusion probability** and the metric **reweights by 1/probability** (inverse-probability /
  Horvitz–Thompson) before aggregating — then uniform *and* outcome-stratified sampling both recover
  the true rate. It is genuinely **unrecoverable** only when the probability is **unknown/unrecorded**
  (an unlogged adaptive or load-shedding sampler) or **zero for a stratum** (a hard drop — e.g. "drop
  the highest-volume users" — no weight resurrects a stratum never sampled). A pipeline that aggregates
  raw sampled counts with no reweighting and no recorded sampling design is the finding; state the
  design where the metric is defined.
- **Self-consistency / inter-model agreement is not precision.** Treat output
  quality as *unmeasured* until an expert rates a frozen, labeled cohort; don't
  stack features on an unvalidated base. See `testing-ai-evals.md` for the
  eval-harness pattern.
- **Requiring expert labels sets the bar; check the labels themselves are any
  good.** Label errors in a held-out set both distort the metric *and* re-rank
  models — test sets carry "an average of at least 3.3% errors" across the 10 benchmarks studied, and correcting them
  can flip which model wins (Northcutt et al., NeurIPS 2021). So measure
  **inter-annotator agreement** across independent labelers (it bounds label noise
  and caps the achievable metric — a model can't beat the label ceiling), spot-audit
  the flagged errors, and handle **class imbalance** honestly (99%-majority
  "accuracy" is the base rate, not skill). This is the *opposite* lesson from
  inter-**model** agreement above: agreement among independent *humans* is signal
  about the labels; agreement among *models* is not precision.
- **Backtest a proxy-derived metric against ground truth before shipping it — a
  plausible formula that passes unit tests can be near-useless.** For any
  derived/scored value built from indirect proxies (estimating runway from
  last-round size ÷ headcount × burn, say), require a ground-truth validation step
  in review — report MAE / correlation / base-rate against real actuals. Unit
  tests prove the math; only a backtest proves the *value*. On failure, **demote
  or gate** it (a coarse band + "corroboration-required"), never ship it as a
  ranker.
- **Match the validation metric to the claim the score makes.** A predictor whose
  correlation is weak but nonzero, with MAE too large to publish a point estimate,
  can still rank usefully — but validate ranking with **concordance / a C-index
  against an observable binary event** ("raised within 6 months", "shut down within
  6 months"), *not* MAE on the noisy latent quantity. Emit an ordinal tier, not a
  point estimate, when MAE is large relative to the decision range, and reject a
  self-refuting "±N" band — a band wider than the decision range is noise on
  screen.

**🚩 red flags** (this file):
a ranker validated with **MAE** instead of concordance, or a "±N" band wider than the decision range;
a per-group ratio whose numerator fans a shared/ownerless entity out to every group while its denominator credits it to a single owner (inflated, or undefined, for every group that shares it);
