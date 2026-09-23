# Domain D checklist

Read this when domain D (Data integrity & data quality) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### D. Data integrity & data quality → `references/data-quality.md`
Apply to any pipeline, ETL, enrichment, scraping, or dataset producer. Judge the
**output**, not just the code.
- **Monotonic quality (hard invariant)**: a write/merge never replaces a
  populated, higher-confidence value with an empty/lower/duplicate one — upserts
  **field-merge with preserve-if-absent**, and a degraded/fallback surfaced by a
  **"latest/max" read is the same breach** even when nothing was overwritten. The
  full invariant and the two-part non-regression gate (within-dataset uniqueness
  **plus** a populated→worse check against a pinned baseline) live in
  `references/data-quality.md` §1; the write-erosion guard's every-mutation-primitive
  coverage + discover-write-sites test are in its §5 — walk it for any data producer.
- **No fabrication in the data**: skip a field rather than guess; corroboration =
  **two+ independent sources**; `inferred` ≠ `sourced`; omit the unverifiable.
- **Entity resolution biases false-exclude over false-merge**: stable-id/proof
  match, never name-only; ambiguous → flag, never auto-merge.
- Measure the six dimensions separately; mark an inapplicable metric **`N/A`, not
  `0`**; freshness from the subject's own activity; a named quantity carries one
  value everywhere (repetition ≠ corroboration); every consumer/export calls the
  **same shared filter**; machine-computed fields are pipeline-owned (never
  hand-edited); **never lower a baseline just to pass a build**.
- 🚩 unconditional upsert ignoring confidence, fuzzy single-field merge, dedup on
  non-normalized keys, "latest wins" clobbering verified data, a metric scored
  `0` where N/A, freshness from `fetched_at`, a model call returning a score/gate,
  a guard that watches one write API but not its siblings, a fallback/empty record
  a "latest" read surfaces over a good one.
