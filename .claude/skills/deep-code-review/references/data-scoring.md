# Data quality depth — scoring, corroboration, and fusion

Read this when the target or diff computes a score, rank, tier, leaderboard, or confidence; fuses or corroborates several sources into one value; or sets a decision field (`status`, `verdict`, `recommendation`) under a stated source precedence. Split from `data-quality.md`, whose core checks (monotonic writes, provenance, units, nulls, joins and keys, dedupe, freshness, idempotent writes) apply to every data review.

## Stated precedence over a decision field (depth of `data-quality.md` §1)

- **A stated precedence must be enforced in the branch that sets the DECISION field — writing the
  higher-authority value into an adjacent column a reader never consults is precedence in name only.**
  When a doc / contract says one source **outranks** another (a human read > a model estimate, a
  manual correction > an automated guess), grep the field that actually **encodes the acted-on
  decision** (`status`, `verdict`, `recommendation`) and confirm the senior source is consulted
  **first in the branch that computes THAT field** — not merely written *somewhere* on the row. The
  breach: the override lands in a side `notes` / `read` / `urgency` column while the decision field is
  computed **purely from the junior (model) branch and never reads the override**, so a row shows
  `status="keep"` beside a human note that says "do NOT do this." This is the authority-**direction**
  complement to grade-monotonic write-authority in `data-quality.md` §1 — that refuses a *junior* value from overwriting
  a senior one; this makes a *senior* value actually **reach** the decision — and a field-granularity
  case of the write-only-value defect (`data-quality.md` §7, an acknowledgment nobody reads). Distinct from `data-quality.md` §6's
  dual-registered write-target (which *store* holds a field) and from a compare-and-swap that guards
  the wrong column (`concurrency-shared-state.md`): here one store, one record — the write reaches the
  row, but the decision branch ignores it. Compounding tell: **truncating** the caveat-bearing field
  to a length that can cut the disqualifying clause (a read of "strong, but do NOT proceed —
  regulated" clipped to "strong") — never truncate a field whose job is to carry the reason; clip
  low-information display fields instead. Test the **conflict case**: a row where override and base
  disagree must render the **override's** verdict in the acted-on cell.

## Scores, corroboration, and liveness (depth of `data-quality.md` §7)

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
  nothing (`data-quality.md` §2). The tell: a confidence computed as `min(identity_match, occurrence, role)`
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
  guess" (`data-quality.md` §2).
- **Any ranking, scoring, or leaderboard gates on an *observed* liveness signal;
  a missing liveness field is a blocker, not a nice-to-have.** Ranking an entity
  set with no liveness gate puts dead or discontinued entities on a live shortlist
  — the same failure the exclusion gate in `data-quality.md` §7 catches at parse time, here as an
  affirmative *input requirement*. Liveness comes from the subject's **own recent
  activity** (cf. `data-quality.md` §4 freshness — from the subject's own newest activity, never your
  fetch timestamp), not from the record merely existing; if the source emits no
  liveness signal, that is fail-closed — exclude or flag `unknown`, never rank as
  live. (A covered-but-dead entity is distinct from an uncovered one — `data-freshness.md`
  observed-low vs unobserved on the data side, and the honest-empty rule in
  `product-ux-quality.md` on the UI side.)
- **Carry a per-row coverage flag; keep each score glass-box.** A score computed
  on partial inputs is a weaker claim than one computed on full inputs — stamp
  each row with which inputs were actually present (a coverage / provenance flag)
  so a consumer never reads a thin-input score as equal-confidence to a
  fully-covered one, and keep the derivation inspectable (the inputs that drove
  this row's number are recoverable), never an opaque scalar. Principle 2 at row
  scope: a missing input is not a low input. (The *interpretation* rule — an
  absent window is not a decline — is in `data-freshness.md`; this owns the per-row mechanism.)

**🚩 red flags** (this file):
a composite score that **sums** heterogeneous constructs;
a per-row score with no coverage/provenance flag or no recoverable derivation;
a derived field named for a conclusion it did not measure (a co-occurrence count called a "strength"/"relationship" score);
a ranking/leaderboard with no observed-liveness gate (a missing liveness field ranked as live);
a corroboration / fusion step that raises a fused confidence past its **entity-attribution** component on agreement that only evidences occurrence;
a hand-rolled composite / score / tiering where a citable external standard exists and wasn't used, or per-metric spec URLs over a **tool-chosen metric set** (the invented index one level up);
a stated precedence (`A` outranks `B`) whose override writes an adjacent `notes`/`read` column while the `status` / decision field is computed only from `B` and never consults it (worse if that caveat-bearing field is then truncated to a length that cuts the disqualifying clause);
