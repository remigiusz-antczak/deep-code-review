# Data integrity & data quality review

Read this when the target produces, transforms, enriches, scrapes, merges, or
serves a **dataset** — any pipeline, ETL, enrichment, entity-resolution, or
scoring system where the value of the product is the correctness of the data it
emits. Expands section D of `SKILL.md`. Here, "better code" and "better outcome"
diverge: **judge the output, not just the source.**

The governing rule: **good data can only be kept or improved, never silently
degraded.** Everything below serves that.

---

## 1. The monotonic-quality invariant (hard)

A write or merge may **never** replace a populated, higher-confidence value with
an empty, lower-confidence, or duplicate one.

- **Upsert must field-merge with preserve-if-absent semantics — never
  wholesale-replace a record.** A pass that recomputes only some fields must not
  wipe expensive derived fields it never touched. This is the single most common
  way a "harmless" enrichment run destroys data.
- **Persist expensive derived output to the system of record.** A disposable
  cache must never be its only home, or a rebuild loses it unrecoverably.
- **Require a regression test that fails on this exact failure mode** — e.g.
  "an existing verified email must survive an enrichment run that returns blank
  for that field." The test fails on the old code, passes after the fix.
- **A degraded/fallback/timeout result written as valid-but-empty** (e.g.
  `status: complete` with all fields blank / `NO_PUBLIC_INFO`) is the same breach
  when a **"latest/max" read surfaces it over a good prior record** — *even
  though no overwrite occurred*, so a naive "did we UPDATE a good row?" check
  misses it entirely. Tag it (`degraded: true`) and have latest/best reads skip
  or de-prioritize it, or do not persist it as the newest record. This is
  precisely why the pinned populated→worse regression test is mandatory and a
  runtime echo-verify **cannot** replace it: some stores omit empty fields from a
  write's response, so an empty write **reads back as equal to absent** and the
  clobber passes echo-verification silently.

### The two-part non-regression gate

1. **Within-dataset invariant (needs no baseline):** a value that must be unique
   to one entity (a handle, email, canonical id) appearing on two entities is
   corruption — detect it in the artifact itself.
2. **Against-baseline check:** populated→empty / higher→lower-confidence /
   count-drop, compared to an **explicitly pinned prior baseline** — never the
   live/current artifact, which may already be the corrupted one. Fail closed
   (exit non-zero) on a regression.

Also run a **run-over-run drift guard** on derived-field population counts:
enrichment is additive, so any populated-column count that falls beyond known
record attrition is a regression.

**A uniqueness violation is corruption only if the value was *absorbed from a
now-departed distinct record* — not when it is newly and legitimately *shared*.**
The within-dataset invariant above false-positives during legitimate coverage
expansion: many related entities newly and correctly sharing one value (sub-teams
adopting a parent org's handle — co-branding) each trip the fanout arm. Hard-block
only the collapse-of-two-distinct-records shape; for a newly-shared *standing*
value among related entities keep a human at the gate or a small reviewed
allowlist, and never re-refuse an unchanged standing shared value every run (that
just gets the gate switched off) — and don't relax the gate's baseline to pass,
which the never-lower-a-baseline rule under *Scoring & config discipline* already
governs.

**Grade-monotonic write-authority — arbitrate a non-empty *overwrite*, not just a blanking.** The
against-baseline check blocks populated→empty and the fanout arm blocks collapse; neither arbitrates
a **value-A → different-value-B overwrite**, so a lower-grade source can silently replace a
higher-grade value while the field stays populated, just **wrong** (a "did a good row go empty?"
check waves it through). Attach a **source grade** to every asserted value (an authored,
deterministic per-source table, not an inferred judgement) and refuse a write when `new.grade <
incumbent.grade`; keep the incumbent on ties. Additive to the populated→empty and fanout checks,
never a replacement (grade-gating alone won't stop an equal-grade blanking). Record each refused /
accepted overwrite with the grades, so the arbitration is auditable.

## 2. No fabrication in the data itself

- **Skip a field rather than guess it.** An empty cell beats a confident-looking
  wrong one. Omit an unverifiable claim entirely rather than softening it into a
  hedge.
- **Corroboration = two or more distinct, independent sources.** Label
  self-attested facts `inferred`, never `sourced`. One source is a lead, not a
  fact. **Independence means independent *origins*, not distinct domains:** a
  conference page, the speaker's blog on another domain, an aggregator that scraped
  it, and a repost are four domains but **one** origin — three *derive from* the
  first, and counting them as four inflates confidence with derivative echoes.
  Collapse **derivation** (a source that cites or derives from another is the same
  origin), not just same-domain duplicates; where derivation cannot be established
  deterministically (no citation / link / "via" signal, no known-aggregator list),
  prefer the **conservative** count over assuming independence. (This is source *independence* — how many origins exist; a separate rule governs what a corroboration count may *promote*: occurrence, never entity-attribution, §7.)
- **Provenance + confidence per record/field:** where a value came from and how
  sure you are (a deterministic score is preferred over a model-assigned one).
  Keep provenance tags honest — "live-queried" (a command that returns the same
  answer on re-run) is not the same as counting a static document.
- **UI chrome is itself a claim.** A tab, heading, count, or label asserts that
  something sits beneath it — render it only when backing data exists. "Empty
  beats fabricated" applies to layout, not just fields.

## 3. Entity resolution — bias false-exclude over false-merge

- **Identity requires a stable id or same-person/same-entity proof — never a
  name-only match.** Two distinct records wrongly merged is worse than two left
  separate.
- **Resolution order when no stable id exists:** normalized domain/handle first,
  then a name **only as a last resort behind a collision (namesake) guard** — and
  surface the **unresolved/ambiguous count as a first-class output**, never a
  silent drop.
- Matches must clear a threshold on **multiple independent signals**; ambiguous
  or conflicting matches are **flagged for review, never auto-merged**.
- **Grade a shared value by frequency; don't treat it as all-or-nothing.** A value's
  weight as a match / join key is **inversely related to how common it is**: a field
  shared by two entities is signal (two co-founders, one company); shared by forty it
  is a role / vendor / generic value to **demote** as a key. Binary include/exclude is
  wrong both ways — it drops legitimate rare-value signal and trusts generic-value
  collisions. Compute a **deterministic value-commonness table** (distinct entities per
  normalized value) from data on hand — below a small **named** frequency band a value
  still counts, above it is demoted — and **scale the required corroboration by
  commonness** (a rare value clears a lower bar; a common one demands more independent
  evidence, since the chance it silently collapses two distinct entities rises with
  frequency). Thresholds are named constants with a rationale, never a tuned magic
  number; route any demotion that empties a field through the non-regression gate (§1).
- Prefer revealed-preference, hard-to-game, multi-signal evidence over a single
  vanity/attention signal.
- Temporal claims (a prior role, a past affiliation) require an explicit
  temporal anchor — don't write a current attribute as a historical one.
- Free-text→structured extraction reliably captures **descriptors, not
  entities** (a category or adjective lands where a name belongs). It needs a
  structured source, not a regex; treat its bulk writes as unsafe by default.

## 4. The six data-quality dimensions — measure separately

Completeness (fill rate), accuracy (vs a source of truth), consistency
(cross-field / cross-source agreement), timeliness/freshness, uniqueness (dedup
rate), validity (schema/format/range). For each:

- **Mark a structurally-inapplicable metric `N/A` — never score it `0`.** A `0`
  silently penalizes rank and pollutes aggregates. Make penalties grain-aware.
- **Denominator integrity:** every entity type that can fail a check must be
  eligible for the denominator (`checks_total` / coverage base). Scoring failures
  against a narrower type set than the failure set understates or misstates
  coverage.
- **Empty-shape honesty:** distinguish **absent**, **expected-empty**,
  **false**, and **empty-list** when completeness or compare-and-swap logic
  collapses them — treating "blank field" as "no check" or "no prior" mis-scores
  and loses races.
- **A named quantity must carry the same value everywhere** it appears; add a
  check that flags stale duplicates. Repetition is not corroboration.
- **Freshness is computed from the subject's own newest activity**, never your
  crawl/fetch timestamp (re-crawling otherwise makes dormant records look
  permanently fresh). Treat "undated" as a flagged third state, never silently
  fresh or stale.
- Derived trend/velocity metrics have a **cold start** — don't emit a value
  until enough snapshots exist; handle the warm-up window explicitly.
- **Validate what lands in a field:** reject your own pipeline labels leaking in
  as a subject's name; reject shape mismatches (an email in a name field is both
  a quality defect and an unintended PII exposure).

## 5. Deduplication & consistency

- Exact **and** near-duplicate detection; canonicalize (normalize case,
  whitespace, unicode NFC, punctuation) **before** comparing. No duplicate
  columns; no near-duplicate rows.
- Stable join/dedup keys are snapshot-tested so a normalization change is caught
  (a NFC/NFD or casing change silently splits or merges keys — see the i18n note
  in `SKILL.md`).
- **Every consumer, renderer, and export calls the same shared quality/noise
  filter as the upstream pipeline.** A surface that skips it silently re-admits
  already-filtered junk.
- **Artifact → consumer census:** for each file/table/topic a pipeline writes,
  find the readers and exports that consume it. An artifact with **zero
  consumers** is dead pipe (honest comment or wire it); a consumer that reads a
  sibling path skipping the stated guard/filter is the bypass-census miss from
  Phase 2. When testing degraded/empty output, confirm consumers treat
  present-empty as empty — not as valid data (cross-ref
  `reliability-error-handling.md` soft-no-op persistence).
- **A write/erosion guard must intercept every mutation primitive the storage
  layer offers** (update AND clear AND append AND delete), not just the common
  one — a cleanup pass that blanks populated cells via an unguarded `clear`/
  `batchClear` bypasses a guard that only wraps `update`/`batchUpdate`, and its
  only remaining protection is a volume ceiling, not the erosion check. Enumerate
  the primitives and check each. The test that proves guard coverage must
  **discover** write-sites (grep/AST), never hardcode a list that goes stale as
  new sites are added.

## 6. Idempotency, ownership & lifecycle

- Idempotent, safe to run twice; last-write-wins **only** by a stable key and
  **only** when it does not violate §1.
- **Batch membership is an explicit batch id, never a shared timestamp.**
  Selecting "the latest batch/generation" via `WHERE col = max(col)` (or
  `ORDER BY col DESC LIMIT`-as-batch) is silently repointed by *any* single-row
  write to `col` — collapsing the view to one row. Stamp an explicit
  generation/batch id and select on it (cross-ref A in `SKILL.md`).
- **Machine-computed fields are owned by the pipeline** — never hand-edited.
  Reject any change or proposal that mutates them.
- **Never mass-close, expire, or delete records on a failed or partial upstream
  fetch.** Mutate status only when the refresh provably ran. Prefer insert-only
  / least-mutation with an explicit, documented edit allow-list; fail-fast on
  schema drift at boot.
- Deletes are soft status changes; support subject erasure-on-request; a
  rejected record re-enters the active set only on a material, tracked quality
  improvement, never silently.

## 7. Scoring & config discipline

- **Scoring is deterministic, explainable code — never a model-authored
  number.** The model may return at most a coarse tier; deterministic code
  computes the score and does all gating.
- Weights and thresholds live in **version-stamped, version-controlled config**
  and are **pinned in a snapshot test**, so a change shows up as a reviewed diff,
  not a silent behavior shift. Bump the version to mark stored derived values
  stale and trigger a backfill.
- New signals are **additive** (a badge, a tie-break, a secondary rank) and are
  never folded into a pinned score without a version bump.
- **Never lower a coverage floor, threshold, or golden baseline just to make a
  build pass.** An intended drop is acknowledged explicitly, per field, with a
  stated reason. (This is the monotonic invariant applied to the *gates
  themselves*.)
- **Never sum heterogeneous constructs into one composite score.** A blended
  "urgency"/"risk" number often merges constructs that imply *opposite* actions —
  raise-timing overdue (introduce to investors) vs distress/contraction (triage) —
  so summing them manufactures false positives and hides which action is warranted.
  Score each construct separately and derive the action from the combination (a
  2×2 / tiering), never from one blended number.
- **Name a derived field for what it measures, not for the conclusion you want it
  to support.** A column called `relationship_strength` that is really a
  co-occurrence *count* (co-authored papers, shared events) is a schema-level
  overclaim — it asserts a synthesized "strength" the data never measured. Surface
  the **corroborating evidence** (co-authored 4 papers; met at 3 events), not a
  manufactured score, and require **multiple independent signals** before asserting
  a tie at all — a lone co-mention or co-attendance is a lead, not a relationship.
  A relationship is often **two-sided**: dropping its edge from one endpoint's
  view erases a real connection, so reconcile the edge from both endpoints (this
  holds for a directional edge too — record the adjacency at each end). (The UI
  half — never
  render a bare synthesized "strength" number as fact — is the confidence-tier
  false-precision rule in `product-ux-quality.md`.)
- **Corroboration raises only the component it evidences — never the entity-attribution.** An
  event/activity confidence often fuses three independent propositions: *occurrence* (did it
  happen), *role*, and *entity-attribution* (whose is it). Cross-source corroboration — N
  independent publishers naming the same event — evidences **occurrence** (and role); it says nothing
  about whether **entity X** was involved. A promotion that lifts the *whole* fused confidence to
  "fact-grade" on an agreement count therefore **silently promotes a weakly-matched
  attribution** — the worst axis, since a confident false attribution is worse than publishing
  nothing (§2). The tell: a confidence computed as `min(identity_match, occurrence, role)`
  **raised** by a corroboration count that only evidences occurrence — `identity_match` was the
  binding minimum *because* attribution was uncertain, and the promotion overrides exactly that.
  Rule: corroboration may raise only occurrence/role, **never past the entity-attribution
  component's own value** — it answers "did it happen," never "whose is it." Safest default:
  carry the corroboration **count as unrendered evidence** (the derived-field rule above) and
  don't promote a fused confidence at all.
- **When the anti-fabrication rule forbids an invented score, the constructive escape is a
  *published standard* — checked at both the definition *and* the selection layer.** A data
  product barred from an "invented composite index" or an inferred human-judgment score can turn a
  forbidden invented metric into a **cited third-party primitive** by adopting an external published
  standard whose *definition* is the spec, not the tool's judgment — e.g. **CHAOSS** (community
  activity/health), **Fellegi-Sunter** (record-linkage match tiers), **W3C PROV** (lineage),
  **rel=me / ORCID / schema.org `sameAs`** (identity), **network-science centrality** (e.g. Freeman
  betweenness), **ESCO / O\*NET** (skills) — each looked up at its own spec (named here **by name
  only**; verify the current spec before citing a version or a specific claim). **The subtle trap:**
  citing each metric's spec while **hand-picking which metrics to include** re-introduces the
  invented index **one level up** — the *selection* is now editorial judgment, hidden because every
  row still carries a spec URL. So the check is two-layer, plus observability: (1) is each metric an
  external, cited **definition**? (2) is the metric **selection** itself a cited published **model**,
  not a set the tool chose? (3) is each metric's **input actually observable** by the product (else
  it is redundant with a system that already observes it)? Where the product must deviate from a published model, it **records the
  deviation per metric, with a reason**. Corollary: a standard often supplies the honest **skip
  band** for free — Fellegi-Sunter's *possible-match* middle tier is literally "skip rather than
  guess" (§2).
- **Test every enum/config mapping against the source's *real* value
  distribution.** A lookup keyed on the wrong domain — a geography→multiplier map
  keyed on region names while the source emits ISO-3166 alpha-2 codes (plus
  lowercase and placeholder values) — silently no-ops: it carries its cost and
  delivers nothing, and unit tests pass because they feed the map the literals it
  expects. `SELECT DISTINCT` the real values and test against them before trusting
  the map.
- **A boolean / categorical parser accepts every shape the source emits — and an
  exclusion gate fails *closed*.** `bool(v) = v === true || String(v) === "true"`
  silently maps a warehouse `1`, `"yes"`, `"y"`, `"t"` to `false`; a row with
  `is_fund: 1` or `is_discontinued: "yes"` then reads as operating and reaches a
  live shortlist — a dead or ineligible entity presented as a target. Accept the
  full shape set (`true/false`, `1/0`, `yes/no`, `y/n`, `t/f`), and for a gate that
  **excludes** (`is_fund`, `is_discontinued`, `is_deleted`) treat an unrecognised
  non-empty value as **exclude / unknown**, never a silent `false` — fail closed,
  and test the parser against the values the source actually emits (as with the
  config maps above).
- **A deserializer re-enforces every invariant its builder guarantees — never trust
  the serialized form.** In a build → serialize → parse pipeline, a serialized line
  can be violated by a torn append, a hand edit, an older schema version, or a
  different writer, so "the builder guarantees X" does **not** mean a parsed object
  satisfies X. The parse path must independently **re-derive computed fields** (a
  count re-derived from the validated collection, not read verbatim) and **validate
  element shape** (not just a primitive type) against the same invariants the builder
  and the type's docstring claim. A parser weaker than its own builder reintroduces,
  at the deserialize trust boundary, the exact fabrication the builder prevents (a
  stored count that exceeds its evidence) — invisible to a builder-only test suite,
  since the builder is correct and the parser silently downgrades the guarantee.
  Prove it with property tests: `parse(serialize(x))` preserves the invariant, and
  `parse(torn / adversarial input)` **drops or rejects, never emits** an
  invariant-violating object (a generator that bakes in the invariant can't produce
  the violation, so it exercises only round-trip fidelity, never the violation path
  — `testing-and-evals.md`). This is the
  data-integrity face of untrusted deserialization (CWE-502, `security-appsec.md`).
- **Any ranking, scoring, or leaderboard gates on an *observed* liveness signal;
  a missing liveness field is a blocker, not a nice-to-have.** Ranking an entity
  set with no liveness gate puts dead or discontinued entities on a live shortlist
  — the same failure the exclusion gate above catches at parse time, here as an
  affirmative *input requirement*. Liveness comes from the subject's **own recent
  activity** (cf. §4 freshness — from the subject's own newest activity, never your
  fetch timestamp), not from the record merely existing; if the source emits no
  liveness signal, that is fail-closed — exclude or flag `unknown`, never rank as
  live. (A covered-but-dead entity is distinct from an uncovered one — §8
  observed-low vs unobserved on the data side, and the honest-empty rule in
  `product-ux-quality.md` on the UI side.)
- **A suppression / allow-list / status match compares an *exact value set*, never
  a substring.** `status.toLowerCase().includes("pass")` matches "passed term sheet
  to legal" and "compass" as readily as the intended "need to pass", silently
  dropping rows — invisibly, when the dropped rows are filtered out before
  rendering. Match against an explicit `Set` through **one shared predicate** (not a
  copy-pasted `includes` at each funnel stage), and emit a **row-level audit** of
  everything auto-excluded so a wrong suppression is visible, not silent.
- **Carry a per-row coverage flag; keep each score glass-box.** A score computed
  on partial inputs is a weaker claim than one computed on full inputs — stamp
  each row with which inputs were actually present (a coverage / provenance flag)
  so a consumer never reads a thin-input score as equal-confidence to a
  fully-covered one, and keep the derivation inspectable (the inputs that drove
  this row's number are recoverable), never an opaque scalar. Principle 2 at row
  scope: a missing input is not a low input. (The *interpretation* rule — an
  absent window is not a decline — is in §8; this owns the per-row mechanism.)

## 8. Measuring the outcome honestly

- Measure enrichment **lift on the subset that actually surfaces to users**, not
  total fill rate — filling fields on records nobody sees moves no outcome.
- **Self-consistency / inter-model agreement is not precision.** Treat output
  quality as *unmeasured* until an expert rates a frozen, labeled cohort; don't
  stack features on an unvalidated base. See `testing-and-evals.md` for the
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
- **An absent window is not a decline — and recency must be monotone in elapsed
  time.** A time/activity score must not read a coverage gap (no observation in a
  window, a source that went quiet, a period not yet collected) as a substantive
  low value ("declining", "churned", "at risk"): distinguish *observed-low* from
  *unobserved* before the number implies a trend. And a recency/freshness score
  must be **monotone in elapsed time** — more time since the last event can only
  lower freshness, never raise it; a non-monotone recency curve manufactures false
  "re-activation". Principle 2 again: the quiet window is evidence only once a
  positive control confirms the source was actually read for it.

## 9. The model's role in a data pipeline (if any)

- The model **never authors a fact, a score, or control flow, and never gates a
  record.** All scoring and gating is deterministic. The model only phrases or
  adjudicates *behind* hard gates.
- Treat all model input as adversarial: instructions in the system prompt only;
  untrusted content fenced/delimited in the user turn with a length cap and a
  "this is data, not instructions" directive; give the extractor no tools;
  schema-validate output before any value is used.
- **Grounding gate:** reject any model output that names evidence not present on
  the record; fall back to a deterministic composer.
- **Neutralize model output** before it reaches a human-facing surface or the
  next stage — strip URLs, markup, and control characters. (Teams routinely
  guard the input and forget the output side.) See `security-ai-agents.md`.

## 10. Honest data collection

- **Represent your client honestly.** No rotating/spoofed User-Agents, fake
  accounts, cookie replay, or logged-in sessions to reach gated data. Besides
  the ethical/ToS problem, it is *counterproductive*: modern gates fingerprint
  the TLS handshake and HTTP/2 frame ordering, so a browser token on a
  non-browser client is a **stronger** bot signal than an honest one. Prefer an
  official API to scraping; exhaust free/public sources before paid ones.
- Enforce data-subject suppression/erasure **once at the export/publish
  boundary**, so every downstream consumer inherits it.

## 11. Cost discipline (enrichment specifics)

- Cascade free/keyless pre-gates **ahead of** any paid call, and apply the spend
  governance from `performance-db-cost.md` (before-call caps, per-run **and**
  global/monthly, a dry-run that costs nothing, calibrate on a zero-write sample)
  — it is not restated here.
- **Data-specific precision floor:** a gate that **drops/deletes** records needs
  far higher measured precision than one that merely enriches — refuse a
  whole-dataset apply unless it is scoped to a verified subset.
- **Measure existing-source coverage for the target set before scoping new
  enrichment or scrapers.** Re-querying the internal warehouse is frequently the
  largest, cheapest coverage lever — it can match a from-scratch enrichment plan's
  target at zero marginal cost and surface already-reconciled fields (a stable
  entity id, dated events, location) the working copy lacks. Scope external
  acquisition to the **measured residual** only; a plan that adds scrapers before
  measuring over-scopes.
- **A feasibility probe for a *current-state* signal gates on freshness, not just
  schema and match-rate.** An external source can pass API-works, has-the-fields,
  and adequate identity-match yet still describe *last year's* state. Query the
  **max timestamp per metric** (`... MAX(sample_date) ... GROUP BY metric` —
  per-metric, since columns in one table lag differently) and compare to today
  **before** designing anything on it. Label a derived signal by the recency of the
  metric it is **actually computed from**, not the freshest column in the table
  (overstating freshness in a deliverable is a silent correctness bug; the freshness
  dimension itself is §4). Run the **cheapest decisive go/no-go query first** —
  match-rate can look like the kill-question while staleness is the real one — and
  keep the probe **re-runnable**: a finding of *too stale to use* outvalues a
  polished pipeline built on a stale signal.

## 12. Data contracts & the train/serve seam

- **A data contract is a declared, versioned agreement** between a data **producer** and its
  **consumers** — the schema, the quality/SLA guarantees (freshness, null-rate, distribution
  bounds), the **semantics** (what each field means and its unit), and an **owner**. It is the
  data-plane sibling of the API/message contract in `api-contracts.md` (consumer-driven contract),
  not restated here — a data contract adds **quality/SLA + semantic meaning**, not just shape. A
  producer schema/semantic change that breaks a **declared** consumer expectation is a finding
  *even when the row still parses* — a currency silently switched from cents to dollars passes
  every type check. Look for the contract expressed **as code** (a schema-plus-expectations
  fixture, e.g. Great Expectations or dbt tests) so a breach fails CI, not a downstream dashboard.
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
- **Training/serving skew.** When an ML feature is computed one way for **training** (batch, full
  history, post-hoc) and another for **serving** (online, partial, real-time), the model meets a
  different distribution in production than it trained on and degrades **silently, with no error**.
  The fix is a **single feature definition** both paths derive from (one shared transform or a
  feature store), and a **point-in-time / as-of** join in training so a feature never uses data
  that would not have been available at prediction time (label leakage's cousin). Flag a feature
  transformed in two places, a training join with no as-of bound, or no monitoring of the
  train-vs-serve feature distribution.

---

**🚩 red flags**: unconditional `UPDATE`/upsert that ignores existing
confidence; `merge` on a single fuzzy field; dedup on non-normalized keys;
"latest wins" clobbering verified data; a metric scored `0` where it doesn't
apply; failure types excluded from the denominator; absent/empty/false/list
collapsed in completeness or CAS; freshness derived from `fetched_at`; a model
call that returns a score or a boolean gate; weights inlined in code with no
snapshot; a consumer/export that re-queries raw instead of the filtered set;
written artifact with no reader; mass status-change on an upstream error; live
counts hard-coded into docs; a coverage threshold lowered in the same diff that
would otherwise fail it; a composite score that **sums** heterogeneous
constructs; a ranker validated with **MAE** instead of concordance, or a "±N"
band wider than the decision range; a config/enum map never tested against a
`SELECT DISTINCT` of real source values; a fanout/uniqueness gate that
blanket-blocks a newly-shared standing value; new enrichment scoped before
existing-source coverage was measured; a per-row score with no coverage/provenance
flag or no recoverable derivation; a time/activity score that reads an unobserved
window as a decline; a non-monotone recency curve; a boolean parser that recognises
only `"true"`, or an exclusion gate defaulting an unrecognised value to `false`; a
substring `includes`/`indexOf` driving a categorical status / suppression decision;
an external-source feasibility sign-off with no max-timestamp freshness check; a
producer schema/semantic change with no declared consumer data contract (breaks a
consumer even though the row still parses); an ML feature transformed differently
for training vs serving, or a training join with no as-of/point-in-time bound; a
derived field named for a conclusion it did not measure (a co-occurrence count
called a "strength"/"relationship" score); a ranking/leaderboard with no
observed-liveness gate (a missing liveness field ranked as live); a data provider
that ships raw events where the consumer scores on aggregates, or a claimed
provider-input never reconciled against the provider's live output before it feeds a
downstream score; a deserializer that trusts a serialized computed field (a count
read verbatim, not re-derived from the validated collection) or checks only a
primitive type, not element shape — weaker than its own builder; a corroboration / fusion step that raises a fused confidence past its **entity-attribution** component on agreement that only evidences occurrence; a hand-rolled composite / score / tiering where a citable external standard exists and wasn't used, or per-metric spec URLs over a **tool-chosen metric set** (the invented index one level up); a non-empty value-A→value-B overwrite with no source-grade arbitration; a join / corroboration key not weighted by value-commonness (a value shared by dozens treated as a confirming match); a corroboration count that collapses same-domain duplicates but not derivation.
