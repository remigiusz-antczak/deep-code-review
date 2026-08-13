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

## 2. No fabrication in the data itself

- **Skip a field rather than guess it.** An empty cell beats a confident-looking
  wrong one. Omit an unverifiable claim entirely rather than softening it into a
  hedge.
- **Corroboration = two or more distinct, independent sources.** Label
  self-attested facts `inferred`, never `sourced`. One source is a lead, not a
  fact.
- **Provenance + confidence per record/field:** where a value came from and how
  sure you are (a deterministic score is preferred over a model-assigned one).
  Keep provenance tags honest — "live-queried" (a command that returns the same
  answer on re-run) is not the same as counting a static document.
- **UI chrome is itself a claim.** A tab, heading, count, or label asserts that
  something sits beneath it — render it only when backing data exists. "Empty
  beats fabricated" applies to layout, not just fields.

## 3. Entity resolution — bias false-exclude over false-merge

- **Identity requires a stable id or same-person/же-entity proof — never a
  name-only match.** Two distinct records wrongly merged is worse than two left
  separate.
- Matches must clear a threshold on **multiple independent signals**; ambiguous
  or conflicting matches are **flagged for review, never auto-merged**.
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

## 8. Measuring the outcome honestly

- Measure enrichment **lift on the subset that actually surfaces to users**, not
  total fill rate — filling fields on records nobody sees moves no outcome.
- **Self-consistency / inter-model agreement is not precision.** Treat output
  quality as *unmeasured* until an expert rates a frozen, labeled cohort; don't
  stack features on an unvalidated base. See `testing-and-evals.md` for the
  eval-harness pattern.

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

---

**🚩 red flags**: unconditional `UPDATE`/upsert that ignores existing
confidence; `merge` on a single fuzzy field; dedup on non-normalized keys;
"latest wins" clobbering verified data; a metric scored `0` where it doesn't
apply; freshness derived from `fetched_at`; a model call that returns a score or
a boolean gate; weights inlined in code with no snapshot; a consumer/export that
re-queries raw instead of the filtered set; mass status-change on an upstream
error; live counts hard-coded into docs; a coverage threshold lowered in the
same diff that would otherwise fail it.
