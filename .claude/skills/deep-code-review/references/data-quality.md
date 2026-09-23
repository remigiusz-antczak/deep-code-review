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
- **A stated precedence must be enforced in the branch that sets the DECISION field — writing the
  higher-authority value into an adjacent column a reader never consults is precedence in name only.**
  When a doc / contract says one source **outranks** another (a human read > a model estimate, a
  manual correction > an automated guess), grep the field that actually **encodes the acted-on
  decision** (`status`, `verdict`, `recommendation`) and confirm the senior source is consulted
  **first in the branch that computes THAT field** — not merely written *somewhere* on the row. The
  breach: the override lands in a side `notes` / `read` / `urgency` column while the decision field is
  computed **purely from the junior (model) branch and never reads the override**, so a row shows
  `status="keep"` beside a human note that says "do NOT do this." This is the authority-**direction**
  complement to grade-monotonic write-authority above — that refuses a *junior* value from overwriting
  a senior one; this makes a *senior* value actually **reach** the decision — and a field-granularity
  case of the write-only-value defect (§7, an acknowledgment nobody reads). Distinct from §6's
  dual-registered write-target (which *store* holds a field) and from a compare-and-swap that guards
  the wrong column (`concurrency-shared-state.md`): here one store, one record — the write reaches the
  row, but the decision branch ignores it. Compounding tell: **truncating** the caveat-bearing field
  to a length that can cut the disqualifying clause (a read of "strong, but do NOT proceed —
  regulated" clipped to "strong") — never truncate a field whose job is to carry the reason; clip
  low-information display fields instead. Test the **conflict case**: a row where override and base
  disagree must render the **override's** verdict in the acted-on cell.
- **An identity / roster change re-attributes cached signals — classify the drop, don't blind-ack
  or blind-block.** A change that improves the entity roster or resolution (fills anchors, corrects
  matches) **re-keys attribution** across every cached downstream signal, so a per-dimension
  **volume drop** can be a **correction** (a signal re-attributed to a better-matched entity, or
  poisoned as newly-ambiguous — one handle now known to belong to two entities) rather than a
  **regression** (a valid attribution wrongly lost); the count alone cannot tell them apart. When an
  identity / roster / entity-resolution change is in the diff or ran in the pipeline, **investigate
  the fold** (which signals moved or dropped, and why) before acking (blind-ack ships a possible
  regression) or blocking (blind-block rejects a correctness improvement). The volume floor (and the run-over-run drift guard above) is the
  **trigger**; the fold investigation is the **adjudication** — after an identity/roster/ER change,
  "beyond-attrition drop = regression" names what to **investigate**, not the automatic verdict.

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
- **Backward lineage: a wrong output must be traceable to the transform that produced it.**
  Record/field provenance (above) says *where a value entered*; it does not say *which step made a
  wrong derived value*. When a downstream field is wrong, can you trace it back to the specific
  transform — and ideally the specific input columns — that produced it? Without that, every data
  bug is an unbounded search across every stage. The reviewable property is **column-level
  lineage**: each output column mapped to the input columns and the transformation (a direct copy
  vs. an aggregation / join / filter) that produced it, so "which root inputs construct column X?"
  and its inverse "what breaks if column Y changes?" are answerable — the backward, transform-level
  counterpart to forward provenance (origin, above) and the forward consumer census (§5).
- **UI chrome is itself a claim.** A tab, heading, count, or label asserts that
  something sits beneath it — render it only when backing data exists. "Empty
  beats fabricated" applies to layout, not just fields.
- **Make a dishonest value unrepresentable; don't rely on a render-time convention.** When an output
  must not assert what it can't back — an uncollected period shown as a measured zero, a fabricated
  score, a placeholder rendered as data — enforcing that with a *convention* ("remember not to draw a
  zero cell") lives in reviewers' heads and scattered call sites, and a later edit silently ships the
  fabrication. Prefer enforcing the invariant **by construction**: shape the type/return so the
  dishonest value has **no code path that can build it** (emit a bin only for an observed period, so a
  "collected-zero" cell has no constructor), then pin it with a "never emits X" test. This is
  `reliability-error-handling.md`'s *make impossible states unrepresentable* applied to data honesty —
  the how-to-guarantee behind the open-world third state (`ux-dataviz.md`) and "an absent
  window is not a decline" (§8). Reviewer check for each honesty invariant: *can the dishonest value
  even be constructed?* If yes, it rests on a convention a future edit can silently violate.

## 3. Entity resolution — bias false-exclude over false-merge

- **Identity requires a stable id or same-person/same-entity proof — never a
  name-only match.** Two distinct records wrongly merged is worse than two left
  separate.
- **Resolution order when no stable id exists:** normalized domain/handle first,
  then a name **only as a last resort behind a collision (namesake) guard** — and
  surface the **unresolved/ambiguous count as a first-class output**, never a
  silent drop.
- **Consume an external pre-computed identity cluster instead of running a forbidden internal model.**
  When resolving identity would need a model or number you are not allowed to run (a no-ML constraint,
  a spend gate, a privacy limit), the clean escape is to consume an **external, pre-computed** cluster
  or id — plus its **public artifact** (an authoritative registry id, a published disambiguation) — as
  the resolver, rather than fall back to a name-only match or ship the forbidden model anyway. Treat
  the external cluster as a **corroborating source** (§2 independence): record its provenance, and do
  not promote a lone external cluster to certainty. It keeps "skip rather than guess" intact when the
  in-house resolver is off the table.
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
- **Join on a normalized key or a resolved id — a *substring-containment* match (`a in b or b in a`)
  leaks one entity's row onto another, and over-correcting to bare exact-match silently drops
  legitimate rows.** Matching two datasets by bidirectional substring with no word-boundary or length
  guard is **worse than the name-only match** warned against above: a short name is a substring of an
  unrelated longer one (`"AV"` inside `"Haven"`), so the row **inherits a stranger's — often
  confidential — fields**, pasted into a human-facing output (a privacy leak, not just a quality
  defect). The reflexive fix — strict exact-match — then **over-corrects**: rows whose names differ
  only trivially (a legal suffix, `Inc`, `gmbh`, punctuation, case) stop matching and **vanish
  silently**. Fix both failure directions at once: match on a **normalized key** (case / whitespace /
  unicode-NFC / suffix-folded — the canonicalize-before-compare rule in §5) or a **resolved stable
  id**, and when overlaying one set onto another **emit every overlay entry as a matched-or-unmatched
  row** so a miss is a **visible unmatched row, never a silent drop** (the resolution-order *surface
  the ambiguous count* rule above, at row grain). Prove the join **both ways on real data** before
  trusting it — sweep for **false positives** (a wrong row attached) *and* **false negatives** (an
  expected row missing); a join is unproven until both counts are seen. Same substring-`includes`
  antipattern as the status / suppression rule in §7, on a different surface — a **join key** that
  leaks a whole row, not a categorical decision that drops one.
- Prefer revealed-preference, hard-to-game, multi-signal evidence over a single
  vanity/attention signal.
- Temporal claims (a prior role, a past affiliation) require an explicit
  temporal anchor — don't write a current attribute as a historical one.
- Free-text→structured extraction reliably captures **descriptors, not
  entities** (a category or adjective lands where a name belongs). It needs a
  structured source, not a regex; treat its bulk writes as unsafe by default.
- **Don't trust raw connected components — a bridge edge signals a false merge.** When clustering
  identities from pairwise links, taking **raw connected components** silently over-merges: one
  spurious `A~B` link plus a real `B~C` collapses two distinct entities (the transitive-chaining
  case a shared-key-collision gate never sees). Run **graph metrics** over the merge graph — a
  **bridge** edge (removing it splits the cluster), especially one backed by a **single artifact**
  joining two otherwise well-connected sub-clusters, is a prime false positive: flag or skip it and
  log why (skip-rather-than-guess); **low neighborhood overlap** (few shared neighbors between the
  edge's two endpoints — the weak-tie indicator) is a further false-link signal.
  Pure false-merge insurance — it does not conflict with monotonic-quality (§1); it keeps a bad
  merge from ever entering the bundle.

## 4. The six data-quality dimensions — measure separately

Completeness (fill rate), accuracy (vs a source of truth), consistency
(cross-field / cross-source agreement), timeliness/freshness, uniqueness (dedup
rate), validity (schema/format/range). For each:

- **Mark a structurally-inapplicable metric `N/A` — never score it `0`.** A `0`
  silently penalizes rank and pollutes aggregates. Make penalties grain-aware.
- **Denominator integrity:** every entity type that can fail a check must be
  eligible for the denominator (`checks_total` / coverage base). Scoring failures
  against a narrower type set than the failure set understates or misstates
  coverage. Conversely, **test / QA / staging / internal traffic reaching a production metric
  pollutes the denominator** the same way an ineligible type does — inflating the base and skewing
  every rate derived from it. Filter or tag it out at the **emitter / ingestion boundary**
  — the same single-enforcement-point discipline as the shared quality/noise filter below and
  `privacy-compliance.md`'s suppression boundary, not a per-dashboard filter a new consumer omits; an
  `is_test` / `environment` field that rides on the event but isn't enforced at the boundary is
  the red flag.
- **A per-group ratio's numerator and denominator must share one membership rule for a shared
  entity.** Denominator integrity (above) is a **single-metric** property — is the failing type in
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
- **Empty-shape honesty:** distinguish **absent**, **expected-empty**,
  **false**, and **empty-list** when completeness or compare-and-swap logic
  collapses them — treating "blank field" as "no check" or "no prior" mis-scores
  and loses races.
- **A named quantity must carry the same value everywhere** it appears; add a
  check that flags stale duplicates. Repetition is not corroboration.
- **A structural / topology validity gate on a graph *authored as data* never checks that a
  separate `anchor` / `startNode` field agrees with the declared entry — closure and
  start-designation are orthogonal, so a valid ring can still begin at the wrong step.** A
  diagram authored as data — an ordered node list, directed edges, a prose narrative of step
  order, and an explicit `anchor` / `startNode` a renderer reads to decide where to begin
  walking the cycle — carries that anchor as a **denormalized restatement** of *where the ring
  begins*, and nothing forces it to equal the **declared entry**: the node list's first element
  and the narrative's first clause. A gate asserting *the edges form one closed cycle covering
  every node* passes green on a perfectly valid ring — so a reviewer reads "validated" — yet it
  never checks *which* node is declared the start, so an anchor set to the last node (or an
  arbitrary "most interesting" one) sails through and **every consumer renders the ring rotated
  to the wrong step** — a wrong-start, not a broken graph. Detection compares the anchor to the
  declared entry (`anchor == nodes[0]`, and the narrative's first clause), **never** "is the
  anchor a valid node id" — validity of the topology is the wrong question. Fix **by
  construction**: derive the anchor *from* the declared entry, or gate the two authored fields
  into equality so they cannot drift (§2, *make a dishonest value unrepresentable*). Because
  such a diagram is usually emitted by a **template / porting script / author habit**, one wrong
  anchor is a strong prior that its **siblings from the same authoring pass carry the same
  disagreement** — run the outward instance-set sweep across every sibling, not just the file in
  hand (`method.md` Phase 4). **Discriminators:** the named-quantity rule above flags a
  *quantity* that drifted **stale** across copies (repetition is not corroboration); here a
  *start-designation* is authored **wrong from origin** and a green **topology** gate supplies
  the false assurance. The partition / ring validity gate in `language-stack-redflags.md` is a
  partitioning *routine's* off-by-one that **falsely rejects** a valid decomposition; this is
  authored *data* whose gate **falsely accepts** by omitting a whole dimension. And §1's
  stated-precedence rule is authority **direction** — one source *outranks* another and must
  reach the decision field; here the anchor and the declared entry are **co-equal** fields that
  must simply be **equal**, and no gate compares them.
- **Freshness is computed from the subject's own newest activity**, never your
  crawl/fetch timestamp (re-crawling otherwise makes dormant records look
  permanently fresh). Treat "undated" as a flagged third state, never silently
  fresh or stale.
- Derived trend/velocity metrics have a **cold start** — don't emit a value
  until enough snapshots exist; handle the warm-up window explicitly.
- **Validate what lands in a field:** reject your own pipeline labels leaking in
  as a subject's name; reject shape mismatches (an email in a name field is both
  a quality defect and an unintended PII exposure).
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
  consumers** (in-repo — but see the externally-consumed carve-out below) is dead pipe (honest comment or wire it); a consumer that reads a
  sibling path skipping the stated guard/filter is the bypass-census miss from
  Phase 2. When testing degraded/empty output, confirm consumers treat
  present-empty as empty — not as valid data (cross-ref
  `reliability-error-handling.md` soft-no-op persistence). **Carve-out for an externally-consumed
  event / metric:** an analytics or telemetry `track()` / `emit()` whose real consumer is
  out-of-tree — a vendor dashboard, a warehouse / BI model, a funnel or retention definition —
  has **no in-repo reader by design**, so "zero in-repo consumers" is *not* dead pipe here, and
  renaming or removing a published event or property is a **breaking change** on par with a public
  API (`api-contracts.md`), silently breaking a downstream surface the diff can't see — not a safe
  cleanup. Verify against a schema / event registry, a tracking plan, or a named owner, not in-repo
  call sites.
- **A write/erosion guard must intercept every mutation primitive the storage
  layer offers** (update AND clear AND append AND delete), not just the common
  one — a cleanup pass that blanks populated cells via an unguarded `clear`/
  `batchClear` bypasses a guard that only wraps `update`/`batchUpdate`, and its
  only remaining protection is a volume ceiling, not the erosion check. Enumerate
  the primitives and check each. The test that proves guard coverage must
  **discover** write-sites (grep/AST), never hardcode a list that goes stale as
  new sites are added.
- **A shared accessor over polymorphic shapes silently no-ops for the shape whose
  key it doesn't reach — the read-side sibling of the erosion-guard rule above.** A
  generic exact-key filter serving several record shapes from one path often matches
  against a **hardcoded OR-list of top-level field names**
  (`[row.fooId, row.barKey, …].filter(Boolean).includes(key)`, or an equivalent `??`
  chain). It works for every shape whose id is a plain top-level property and
  **silently returns empty — no error** — for any shape whose id is **nested** under a
  sub-object (`metadata` / `frontmatter` / `attributes` / `config`): none of the
  top-level candidates is ever truthy, so the list is empty and `[].includes(key)` is
  always `false`, and that collection reads as "nothing ever matches" instead of
  failing loudly. It survives review because each shape works alone and a **per-shape**
  search/scope accessor (built correctly, reaching into the nested field) usually masks
  it, so a smoke test on the common shapes passes. Catch it: enumerate **every** shape
  the filter serves and check each one's real field nesting **at its schema/type, not
  by assumption**; if a sibling accessor already reaches the nested key correctly while
  the shared filter does not, that inconsistency confirms a genuine gap, not a
  limitation; and if the endpoint documents the parameter as working uniformly across
  shapes, the silent per-shape gap is a broken promise (a contract breach on par with a public-API change, `api-contracts.md`). Fix: a per-shape accessor
  registry (`shape → (row) => key | null`), mirroring the per-shape accessors the code
  already has for other concerns — not another ad-hoc entry bolted onto the top-level list. Unlike the erosion-guard’s open-ended write-site surface above, the shape set is closed and type-checkable, so the registry can be exhaustiveness-checked rather than discovered. Regression-test one fetch-by-real-key per shape, not just the first-tested one.
- **An accessor returning an empty collection to signal "not applicable" is indistinguishable,
  to a generic membership filter, from "applies but matches nothing."** One generic list/search
  path often serves several row shapes and narrows by a `scope`/dimension filter through a
  per-type accessor — `SCHEMAS[type].keys(row) → string[]`, matched via
  `keys(row).includes(requested)`. Some types are legitimately never scoped by that dimension, so
  their accessor is a constant `() => []` — the author's way of saying "N/A here," sometimes with
  a comment saying so. The generic filter can't see the comment: `[].includes(requested)` is
  `false` whether the type is inapplicable or genuinely scoped-and-empty, so the whole type
  silently drops out of results whenever any caller passes that filter — no error, just fewer
  rows. This is the *design-intent* sibling of the nested-key accessor gap above: there the
  accessor is empty **by mistake** (unreachable nesting); here it is empty **on purpose**, and
  the generic predicate still can't tell the two apart. Represent inapplicability explicitly
  instead of overloading empty — a whole-type bypass from that filter's domain, a sentinel
  (`null`) the filter special-cases before calling `.includes()`/`.some()`, or excluding the type
  from the filter's domain entirely — never a bare empty collection a generic predicate reads as
  exclusion. (Same "generic code can't see a per-type intent" shape as `product-ux-quality.md`'s
  empty-state coverage rule — an empty render that can't tell "not queried" from "genuinely
  zero," there at the UI layer.) Most dangerous when the endpoint's own contract documents the
  filter as *narrowing* results rather than *excluding whole types*: supplying it then does the
  exact opposite of what the docs promise, silently (cross-ref `api-contracts.md` — behavior that
  diverges from the documented contract). Regression-test: a scoped search call, run against a
  fixture that includes an N/A-by-design type, must still return that type's rows.

## 6. Idempotency, ownership & lifecycle

- Idempotent, safe to run twice; last-write-wins **only** by a stable key and
  **only** when it does not violate §1.
- **A diff/index key must be unique across every *kind* the input mixes — a bare `id` over a
  multi-kind list silently merges two entities.** When a comparison indexes a list that folds more
  than one entity kind into one array (a discriminated union — `kind` + `id`) with
  `new Map(list.map(x => [x.id, x]))` or `new Set(list.map(x => x.id))`, two different kinds
  sharing an id **collide**: `Map`/`Set` keep last-write-wins, so one entity vanishes from the diff
  with **zero signal** — not flagged added, removed, or ambiguous, just gone (the comparison
  iterates surviving keys and emits one delta instead of two). Key on the **compound `(kind, id)`**.
  The tell is cross-referential, not local: each function reads fine alone, but a **sibling** in the
  same module often already takes a `(kind, id)` key (sometimes with a comment saying why), so the
  bare-id diff is a **regression against a contract the codebase set for itself**. Report it even
  when today's data has no collision and the diff has no live caller yet (a latent silent
  false-merge in shared code), but state plainly whether it is currently reachable. A silent merge
  is the false-merge §3 warns against — bias to false-exclude (surface both, flag ambiguous) over
  collapsing two entities into one.
- **A dedup/idempotency key must hash the *full* content, not a truncated display slug.** A
  human-readable id built as `slug(source, key, text.slice(0, N))` — any id whose uniqueness
  component is computed **after** truncation — collides for any two payloads that share the
  first N characters (a common prefix, a boilerplate lead-in, a shared title stem). If that id
  also gates dedup or an idempotency upsert, the second payload is silently dropped or
  overwrites the first. Keep the readable slug and the **collision-resistant key separate**:
  hash the full, untruncated content (or a natural unique key) for identity, and let the
  truncated part be display-only. Test two inputs that differ only *past* the truncation point
  and confirm both survive.
- **Batch membership is an explicit batch id, never a shared timestamp.**
  Selecting "the latest batch/generation" via `WHERE col = max(col)` (or
  `ORDER BY col DESC LIMIT`-as-batch) is silently repointed by *any* single-row
  write to `col` — collapsing the view to one row. Stamp an explicit
  generation/batch id and select on it (cross-ref A in `SKILL.md`).
- **Machine-computed fields are owned by the pipeline** — never hand-edited.
  Reject any change or proposal that mutates them.
- **A dual-registered entity has one write target *per field* — the store the read path treats
  as authoritative.** When the same entity lives in two stores (a legacy CSV/table row and a
  newer per-entity file/record), an edit tool must write each field to whichever store the
  read/compile path actually reads for **that** field — not "whichever is easier" or "both."
  Writing the legacy row for a field the reader now takes from the new file makes the edit a
  **silent no-op** (the change never shows); writing both without a defined precedence lets them
  **drift** into two disagreeing values. Map read-authority per field first, point the write
  there, and test that an edit is observable through the read path. (This is the field-granularity
  case of §5's artifact→consumer census — the target store *has* readers, just not for **this**
  field — and the steady-state sibling of the dual-write family in `reliability-error-handling.md`
  (cross-system) and `performance-db-cost.md` (same-table migration); distinct from §1's
  write-authority arbitration over one field's *value*, and §12's train/serve data contract —
  this is *which store* to write.)
- **Never mass-close, expire, or delete records on a failed or partial upstream
  fetch.** Mutate status only when the refresh provably ran. Prefer insert-only
  / least-mutation with an explicit, documented edit allow-list; fail-fast on
  schema drift at boot.
- Deletes are soft status changes; support subject erasure-on-request; a
  rejected record re-enters the active set only on a material, tracked quality
  improvement, never silently.
- **Soft-delete correctness — a `deleted_at` demands discipline everywhere it is read.** Once a
  table has a soft-delete marker, **every** read must exclude deleted rows (a query, a JOIN, a
  COUNT, an aggregate, a uniqueness check) — via a **default-scoped accessor** (a base query /
  repository scope filtering `deleted_at IS NULL`), not per-call-site filters that drift (one
  site forgets and silently re-admits deleted rows into results, counts, exports). Flag raw
  reads that bypass the scope.
- **A `UNIQUE` constraint must carve out soft-deleted rows.** `UNIQUE(email)` on a soft-delete
  table blocks re-creating a value whose row was soft-deleted (the tombstone still holds the
  constraint) — the user cannot re-sign-up. Make it a **partial index**
  (`UNIQUE … WHERE deleted_at IS NULL`); on an engine without partial indexes, fold a **non-null**
  delete marker into the key (a fixed epoch / `0` / generated column) — never a bare nullable
  `deleted_at` in a composite `UNIQUE`, since `NULL ≠ NULL` lets duplicate **live** rows through
  (Postgres / MySQL / SQLite).
- **Delete semantics are deliberate across relationships.** `ON DELETE CASCADE` can
  **over-delete** (deleting a user nukes shared or audit rows the delete never intended); a hard
  delete with no cascade **under-deletes** — leaving **dangling foreign keys** / orphaned children
  where the FK is **unenforced** (an app-level / cross-service / warehouse relation, a disabled
  constraint) or `ON DELETE SET NULL`; an *enforced* FK with the default `RESTRICT` / `NO ACTION`
  instead **blocks** the delete. Confirm each FK's on-delete policy is chosen on purpose, and a soft-delete cascades
  to its children (or deliberately does not); a parent soft-deleted while children stay
  live-and-reachable is a leak. (The privacy **erasure** obligation is separate —
  `privacy-compliance.md`; this is delete *correctness*.)

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
- **An acknowledgment or readiness flag that nothing *reads* is not a control — it must be active,
  not merely emitted.** A "drop acknowledged" field, a `data_ready` / `is_complete` flag, a coverage
  note — if no gate consumes it and nothing renders it, it is a **write-only** value that changes no
  behavior: the drop still ships silently, the not-ready data is still served. Require a **reader** —
  the acknowledgment gates the merge/publish (or a review surfaces it); the readiness flag is checked
  before the consumer reads. The review test is a **grep for a reader**: a flag written at one site
  and read at none is the finding (§5's **artifact → consumer census** — a written artifact with
  zero readers is dead pipe — is the persisted-store cousin of the same defect).
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
  false-precision rule in `ux-dataviz.md`.)
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
- **An absent window is not a decline — and recency must be monotone in elapsed
  time.** A time/activity score must not read a coverage gap (no observation in a
  window, a source that went quiet, a period not yet collected) as a substantive
  low value ("declining", "churned", "at risk"): distinguish *observed-low* from
  *unobserved* before the number implies a trend. And a recency/freshness score
  must be **monotone in elapsed time** — more time since the last event can only
  lower freshness, never raise it; a non-monotone recency curve manufactures false
  "re-activation". Principle 2 again: the quiet window is evidence only once a
  positive control confirms the source was actually read for it.
- **A failed *read* is not a negative *verdict* — carry a distinct
  `unknown`/`degraded` state, never fold it into the accusing bucket.** A
  per-subject verdict (compliant/delinquent, posted/missing, present/absent)
  joined from several store reads often wraps each read to degrade to an empty
  result on error (`catch → []` / `new Map()`) so one flaky store never 500s the
  page — an often-correct resilience choice. But when that empty-on-failure
  fallback feeds a computation whose *absence* reads as a specific **negative**
  claim, the resilience silently converts an infrastructure fault into a false,
  actionable accusation against a **named subject**: "couldn't read your posting
  history" renders as the same red "never posted" badge (and inflated "still
  owed" count) a genuine miss earns, with nothing in the response telling the two
  apart. This is the read-*failure* sibling of "an absent window is not a
  decline" above — there a coverage gap must not read as a substantive-low
  *score*; here a read that *errored* must not read as a substantive-negative
  *verdict* about an identified subject — and it is worse, because the output is a
  specific accusation, not a neutral "no data yet." Make it reviewable on two
  axes: **(a) polarity** — trace each catch-to-empty forward and ask which bucket
  the empty lands in; into the *positive/compliant* bucket it is an honest floor
  (safe), into the *negative* bucket it fabricates the accusation; **(b) the bit
  must live in the response *shape*** — a `degraded` flag, a `dataIssues:
  string[]`, or a per-row `unknown`/`unverifiable` state the caller can render —
  because a server-side log the reader never sees is not a distinguishing signal.
  Keep the don't-500 resilience; just stop discarding the one bit (did every
  source actually respond?) that says whether the negative is real. Best enforced
  by construction: give the verdict type a third state so "delinquent" has **no
  constructor** from an unread store (§2, *make a dishonest value
  unrepresentable*). Same failure mode as the gate discipline in
  `reliability-error-handling.md` (a can't-check needs a distinct exit + message
  from a found-problem) and the metric version in `observability.md` (a 429 /
  timeout is not "no match" / "score 0"), but on a **different surface**: here the
  distinguishing bit must ride a **per-row response field** the UI can render,
  which a process exit code and an aggregate metric label structurally cannot
  carry.
- **A background-refreshed cache serves the last-good value with no *as-of*
  surface — so a dead refresher renders byte-identical to live.** A hot read path
  that can't query its store synchronously (a sync render function, an async-only
  client) keeps a module-level *last-good snapshot* and kicks off refresh in the
  background, serving the old snapshot on refresh failure rather than throwing —
  a defensible resilience choice, like the don't-500 fallback above. The honesty
  defect is on the **read surface**: the snapshot usually already carries a
  `generated_at` / `refreshed_at` the consumer *could* render, but no caller reads
  it (the accessor's only reference is its own declaration — the same **dead-pipe**
  tell as §5's *artifact → consumer census*: produced, consumed nowhere), and the
  refresh failure is logged **server-side only**. So through an outage of any
  length every consumer renders identically to a fully live read. This is the
  **successful-read twin** of the read-*failure* bullet above — there a read that
  *errored* must not render as a verdict; here a read served from a cache whose
  refresher *silently died* must not render as live — and a server log the reader
  never sees is again not a distinguishing signal. **Do not conflate this with §4
  freshness:** §4 scores the *subject's* own newest activity (never a fetch/refresh
  timestamp); this is the *pipe's* liveness — can the cache still refresh from
  source — a different question, which a subject-level "this record is N days old
  vs its cadence" signal never answers yet is routinely mistaken for in review
  because both use the vocabulary "fresh"/"stale". Fix: **wire the `generated_at`
  into a visible surface** (a "data as of HH:MM" cue, or a banner once cache age
  exceeds N expected refresh intervals) **or assert a read-time freshness bound**;
  pair it with the operator-side alarm on an overdue refresh (`observability.md` —
  freshness = time since last successful run; page when none in 2× the interval),
  which alone still leaves the *reader* blind. If the reader-side signal is
  deliberately deferred, **downgrade the unwired accessor from a shipped API to a
  tracked follow-up** so a later reviewer doesn't read its mere existence as wired
  coverage. Distinct from the cache **stampede** / **negative-cache** /
  invalidation bugs in `performance-db-cost.md` (correctness and cost of the cache
  *mechanism*) — this is a cache that never *visibly* expires because a background
  job owns refresh and its death is unobservable at the point of read.
- **Observability is a per-entity-*class* property, not only a per-window one.**
  The rule above corrects a *temporal* coverage gap; a distinct, cross-sectional
  one is that whole **classes** of entity are structurally less observable on
  public signal — people who work in public (engineers, researchers, OSS
  contributors) over-represent, and those whose work is private or gated
  (operators, investors) under-represent — independent of any time window.
  Uncorrected, an empty profile reads as **inactive** when it means **not publicly
  observable**. Label each entity's **public-footprint class** (high vs low
  observability) and carry it into every consumer: an empty / low profile in a
  low-observability class renders as *not observed*, never *inactive*, and a
  ranking must not read *unobserved* as *low-activity* — that systematically
  penalizes the very members the public surface can't see. Empty-beats-fabricated
  at the coverage layer. (Distinct from §7's per-row coverage flag, which is
  *post-hoc* — which inputs a given run populated; a public-footprint class is
  *a priori*, a structural property of the class known before any fetch runs.)
- **A freshness *window* is observable; a freshness *decay curve* is fabricated.** A **binary
  in-window gate** — `now − retrieved_at ≤ window_for_type` — is honest: elapsed time is an
  observable input, and a per-signal-type window that gates routing ("act on this only within N
  days") is deterministic and clickable. A **continuous decay-strength curve** — `strength =
  0.5^(days / half_life)` — is a **banned fabricated constant** (Principle 2): the half-life
  is invented, not observed — the same family as a predicted buying-stage score. Take the window,
  reject the curve; and treat a vendor / marketing **half-life figure** as **unverified** unless it traces to a
  primary source — use it only to illustrate window *ordering*, never as a number.

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
- **A connector/transform *pivot graph* multiplies both risks per hop — gate every
  hop, not just the chain end.** A pivot engine (identifier → transform → new
  entities → next transform; the Maltego / SpiderFoot pattern) is powerful for
  coverage but compounds two hazards a single-source lane does not have. (1)
  **Attribution risk multiplies:** a wrong entity at hop 2 poisons every entity
  derived at hops 3+, so each transform's *output* entities must re-pass the
  identity / fanout gate (§1 fanout arm, §3 false-merge) **before** attribution —
  not once at the end of the chain. (2) **Identity-disclosure risk multiplies:**
  each hop contacts a new host directly, so a pivot toward a gated host routes
  through a contracted broker under a declared collection-identity policy
  (anonymous / identified / brokered) — never spoof (above) — and a pivot must not become a
  rate-limit-evasion fan-out. A pivot graph without per-hop guards is both a
  fanout amplifier and an identity-exposure amplifier.
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
- **A vector index is a derived dataset whose *embedding model + version* is part of its
  contract.** Embeddings from two different models (or two versions of one) live in
  **different latent spaces**, so a similarity search across them is meaningless — and if
  both produce the **same dimension** there is **no error**, just silently wrong
  nearest-neighbours (a *different* dimension is the loud, easy case: a dimension-typed
  `vector(n)` column rejects it). Two failure modes a shape-check misses: **(a)
  mixed-version index** — a model upgrade that re-embeds only *new* rows (or backfills
  incrementally) leaves the store comparing vectors from two spaces; upgrading requires
  **re-embedding the whole corpus** and an **atomic index swap**, with the query path pinned
  to the **same** model+version the index was built with (tag each vector with its embedding
  model+version; refuse cross-version compares). **(b) stale index** — source documents
  changed or were re-chunked but not re-embedded, so retrieval returns outdated content with
  no error; needs a re-embed-on-source-change pipeline and a freshness/version gate. **(c)
  metric / normalization mismatch** — the contract is not just the model but the **distance
  metric** (cosine vs dot-product vs Euclidean) and its normalization assumption: **cosine
  and dot-product agree on ranking only for unit-normalized vectors**, so an unnormalized
  corpus queried under dot-product conflates vector **magnitude** with relevance. An index built or tuned for one metric but
  queried under another throws no error and no dimension mismatch — just silently
  **reordered nearest-neighbours**, the same "no error, just wrong" shape as the model-version
  case (keep this generic; the exact operator-class behavior varies by vector store). This is
  the *correctness* face of a vector store — distinct from the **security** face (RAG
  access-control / embedding-inversion, `security-ai-agents.md` LLM09) and the **cost** face
  (don't re-embed unchanged inputs, §11). (`pgvector` enforces one dimensionality per typed
  `vector(n)` column, so a different-dimension mix errors loudly; a same-dimension
  cross-model mix does not — it performs no model-provenance check.)

---

**🚩 red flags**: unconditional `UPDATE`/upsert that ignores existing
confidence; `merge` on a single fuzzy field; dedup on non-normalized keys; a dedup/idempotency
key hashed over a truncated display slug;
"latest wins" clobbering verified data; a metric scored `0` where it doesn't
apply; failure types excluded from the denominator; absent/empty/false/list
collapsed in completeness or CAS; freshness derived from `fetched_at`; a model
call that returns a score or a boolean gate; weights inlined in code with no
snapshot; a consumer/export that re-queries raw instead of the filtered set;
written artifact with no reader; an edit written to a store the read path does not
read for that field; mass status-change on an upstream error; a read / JOIN / COUNT on a soft-delete table with no `deleted_at IS NULL`
filter (deleted rows leak into results); a `UNIQUE` column on a soft-delete table with no
partial-index carve-out (cannot re-create a soft-deleted value); a hard delete leaving dangling
foreign keys on an unenforced/`SET NULL` FK, or an `ON DELETE CASCADE` that over-deletes
shared/audit rows; live
counts hard-coded into docs; a coverage threshold lowered in the same diff that
would otherwise fail it; a composite score that **sums** heterogeneous
constructs; a ranker validated with **MAE** instead of concordance, or a "±N"
band wider than the decision range; a config/enum map never tested against a
`SELECT DISTINCT` of real source values; a fanout/uniqueness gate that
blanket-blocks a newly-shared standing value; new enrichment scoped before
existing-source coverage was measured; a per-row score with no coverage/provenance
flag or no recoverable derivation; a time/activity score that reads an unobserved
window as a decline; an entity's structurally-low-observability class read as
inactive rather than not-observed; a non-monotone recency curve; a boolean parser that recognises
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
primitive type, not element shape — weaker than its own builder; a corroboration / fusion step that raises a fused confidence past its **entity-attribution** component on agreement that only evidences occurrence; a hand-rolled composite / score / tiering where a citable external standard exists and wasn't used, or per-metric spec URLs over a **tool-chosen metric set** (the invented index one level up); a non-empty value-A→value-B overwrite with no source-grade arbitration; a join / corroboration key not weighted by value-commonness (a value shared by dozens treated as a confirming match); a corroboration count that collapses same-domain duplicates but not derivation; a per-dimension volume-floor drop acked or blocked with no fold investigation after an identity/roster/entity-resolution change (a correction and a regression are identical from the count); an identity cluster built from raw connected components with no bridge / centrality check (transitive over-merge); a fabricated freshness decay curve (`0.5^(days/half_life)`) or an adopted vendor half-life in place of an observable in-window gate; a diff / index keyed on a **bare `id`** over a list mixing multiple entity **kinds** (a `(kind, id)` collision that silently merges two entities into one delta); a vector index mixing embeddings from two model versions, queried with a different model than it was built with, not re-embedded after its source docs changed, or built for one distance metric / normalization and queried under another; a per-group ratio whose numerator fans a shared/ownerless entity out to every group while its denominator credits it to a single owner (inflated, or undefined, for every group that shares it); a percent-unit guard with a lower bound only, so a value above 1 (legitimate over-100% semantics, or a double conversion) renders wrong with no error; a `scopeKeys`/`tags`/`labels`-style per-type accessor with a constant `[]` return (or a `// not scoped by X` comment) feeding a shared `.includes()`/`.some()` filter with no whole-type bypass, silently dropping that type from every scoped result; a stated precedence (`A` outranks `B`) whose override writes an adjacent `notes`/`read` column while the `status` / decision field is computed only from `B` and never consults it (worse if that caveat-bearing field is then truncated to a length that cuts the disqualifying clause); a dataset join by unguarded substring containment (`a in b or b in a`) that inherits an unrelated entity's confidential row, or a bare exact-match overlay that silently drops rows differing only by a legal suffix / case / punctuation; a graph / diagram authored as data whose closure / topology validity gate stays green while a separate `anchor` / `startNode` field disagrees with the declared entry (the node-list first element / the narrative's first clause), rendering the cycle rotated to the wrong start — and batch-inherited across every sibling from the same authoring pass.
