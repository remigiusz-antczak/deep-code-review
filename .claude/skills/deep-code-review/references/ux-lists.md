# Product UX depth — feeds, lists, and tables (actionability, ordering, row alignment)

Read this when the target or diff renders a feed, list, table, or dashboard of items: whether each unit says why it matters and what to do next, its default order and exposed sort / rank modes, or repeated rows whose trailing chips or actions must align across rows. Split from `product-ux-quality.md`, whose stance, data-state rules, encoding rules, 🚩 grep, and pre-ship checklist apply to every UI review.

## Actionability — a unit answers "why does this matter," not just "what happened"

The other domain-P rules prove a component **renders** correctly; this asks whether it **helps the user
decide or act**. A feed, dashboard, or brief can pass every render check and still be a **wall of
verified facts** — each unit a *fact + its source* with no *so-what / now-what*, a real UX defect
invisible to the rendering rules.
- **Every primary information unit carries a why-it-matters signal — derived, never fabricated.** A unit
  a decision depends on states *why it matters* through a **structural / derived** signal: a count ("3rd
  of its kind this quarter"), a recency-delta ("first activity in 60 days"), a graph-degree ("connects
  to N entities you follow"). **Hard rule (anti-fabrication):** the signal is computed from real data —
  **never a model-authored "importance score" or an LLM judgement of salience**, the content-layer
  cousin of the false precision the confidence-tier rule in `ux-dataviz.md` forbids. A derived signal that barely
  varies is not a signal — measure its distribution first, exactly as for a confidence tier.
- **Where an action is possible, name the concrete next step** on the unit (follow, open, assign,
  dismiss), not a bare record the user must decide what to do with. A signal-led feed maps each event to
  a follow or next step; a relationship surface offers a next-best-action, not just a row (a pattern,
  not a product endorsement).
- **Most-actionable-first, and stable.** The highest-decision-value surface is in the **first paint and
  stable** — not deferred to a post-hydration `aria-hidden` island, nor pushed below fixed
  non-interactive summary chrome (cross-ref layout-shift / CLS in `frontend-a11y.md` and the
  density/footprint rule in `product-ux-quality.md`). Which order serves the user's job is ruled on in the ranking section
  below.
- **Lead with what's new *and* why it matters** — a reader's first two questions are "what is it?" and
  "is it relevant to me?"; a unit answering only the first is half-built (the **Smart Brevity** pattern;
  `docs/standards-index.md`).
- **Defect vs redesign; the gate is fail-open.** Missing actionability on a decision surface is a
  **defect to surface**, not a licence to redesign a deliberately-terse product — separate the two,
  never carrying Blocker/Critical gate language on a product choice (SKILL.md Phase 5). The heuristic
  gate **warns and lists, never blocks** (unlike the fail-closed `ci-gates.sh` check-#6/#7): it flags a
  primary list/card whose unit is *fact + source* with no derived why-it-matters signal and no action
  affordance, and a top-value surface that is an `aria-hidden`-until-hydration island — but it **cannot
  tell "should be actionable" from "deliberately terse,"** so a human adjudicates every hit.

## Ranking & sort-mode legibility — the order is a product decision, not a default

The variant/option-bloat rule in `product-ux-quality.md` targets view/style toggles; this extends it to the **ordering of a
feed/list itself** — the confidence-tier rule (`ux-dataviz.md`) targets a *displayed* score, not the *ordering key*. The
gap between them: is the **default order** the one serving the user's job, and is each exposed sort mode
**self-explaining and measurably distinct**?
- **The default order serves the user's primary job** (signal / importance / soonest-to-act), not
  implementation-convenient reverse-chronological. Recency is a *mode*, rarely the right *default* for a
  decision surface. (Canonical home of the default-ordering rule the actionability section refers to.)
- **Every exposed sort/rank mode is self-explaining and distinct.** Each mode carries an on-demand
  one-line *"orders by …"* (tooltip / helptext), and the variant-bloat test applies: **would a
  first-time user know why to pick "Top" vs "Momentum"?** If not, it's bloat — cut to one strong
  default, the rest behind progressive disclosure, each self-labeled. Two modes producing
  **near-identical orders** are variant-bloat → collapse (measure the overlap, don't assume it).
- **The sort key needs a measured distribution — anti-fabrication (hard rule).** A key derived from
  real, varying signal is legitimate ranking; a sort by an **opaque or near-constant score is the
  ordering-layer form of false precision** — measure the key's distribution before shipping it as
  "ranking" (reuse the confidence-tier "measure the distribution first" rule, `ux-dataviz.md`; a key that barely
  varies orders nothing). An order the user can't explain and the data can't justify is noise dressed as
  intelligence.
- **Multiple ordering regimes across surfaces** (a curated home *plus* a multi-mode feed over the same
  data) are a lot of ways to slice one dataset — consolidate, or cross-explain on-surface which regime
  serves which task. Warn-and-list, never block (a human tells a rich-but-legible set from bloat).

## Repeated rows — align trailing columns across rows, not only within each row

- **Fixed-width trailing chips laid out after a `flex-grow` cell align *within* each row but not
  *across* rows — a per-row flex container has no shared column, so the cluster starts at a
  different x on every row.** A repeated list/table row built as a flexbox — a primary cell with
  `flex: 1` (or `flex-grow`) that expands to fill, followed by fixed-width status chips, counts,
  or action buttons — packs its own children correctly, so any **single** row looks perfectly
  aligned and a one-row component test or screenshot passes. But each row is its **own** flex
  container: the `flex: 1` cell consumes whatever width that row's primary content leaves, which
  differs per row, so the trailing cluster begins at a **different horizontal position on every
  row** and the chips read as ragged down the page, sharing no common edge. It hides because the
  raggedness is a **relational** property visible only when rows stack and you scan the trailing
  edge — exactly the composition judgment the *clean-checklist-is-a-floor* rule in `ux-sweep.md` names ("a
  column of badges that don't share a right edge") as invisible to a per-element checklist — and
  seed data with near-equal primary-cell lengths lines the chips up by accident. Fix: hoist the
  columns to the **container** with a shared track structure — CSS Grid on the list with one
  `grid-template-columns` (e.g. `1fr max-content max-content`), each row a grid row (or
  `display: contents` / `subgrid` for a nested row component) so every row's chip column shares
  the **same track boundaries**; flexbox aligns children within one container, Grid with a shared
  template aligns a column across many (the data-grid / property-row precedent — Linear, Notion, a
  spreadsheet). Right-aligning the chips within each row does **not** fix it — it only moves the
  ragged edge. **Distinct** from the tabular-figures rule in `product-ux-quality.md` (glyph-level: digits lining up
  inside one column via `font-variant-numeric`) — this is **column-boundary** alignment across
  rows, a layout-structure defect, not a font-feature one. Detection: a repeated row component
  whose layout is `flex`/`inline-flex` with a `flex-grow`/`flex:1` cell and fixed-width trailing
  elements, with **no** shared grid track tying the cluster's start across rows; verify by
  stacking rows with **unequal** primary-cell lengths and scanning the trailing edge, never a
  single row.
