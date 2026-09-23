# Product UX depth — one component per concept, across modules and scopes

Read this when the target or diff renders one concept in more than one place: a shared component or design token, a design-system / shared-recipe migration, sibling view variants of one entity, a row type or view-switch or shared search across layouts, a component with no visible mount path, or one component reused at single-entity and aggregate scope. Split from `product-ux-quality.md`, whose stance, data-state rules, encoding rules, 🚩 grep, and pre-ship checklist apply to every UI review.

## Unified across modules — one component per concept

The consistency rule (`product-ux-quality.md`, *Match a named standard*) has a structural cause and a structural fix. **Inconsistency across views is
almost always the same concept built more than once and drifting** — a row, card, field, empty-state,
status chip, or editor reimplemented per page, so a fix to one misses the others and the app feels like
a different product on each screen. This is a maintainability defect (cross-ref domain H) with a UX
consequence, so it is ruled on here too.

- **One shared component per concept.** Before building a UI element, grep for an existing component or
  pattern that already does it and **reuse or extend it** — never reimplement per page. A duplicated UI
  string or markup block across files is the red flag (cross-ref H's duplicate-source-drift:
  byte-identical lockstep copies need a single source or a parity test). **Cross-file duplication is
  invisible to a diff-scoped review** — you see the file you changed, not its twin — so on any "unify"
  or "fix this component" task, grep the **duplicated visible literal string or section heading** across
  the whole tree as the search key that surfaces the twin, before claiming the concept unified.
- **A shared component existing is not proof the concept is unified — check the adoption is total.** A
  shared component often exists *because* a drift was already fixed: built and rolled out to N callers
  (often via its own closed PR/issue) to kill exactly this duplication. But 1–2 new or missed sites
  reintroduce the drift by hand afterward — sometimes copy-pasting the component's own default-string
  constant instead of importing it. A component being *created* reads as the concept being *solved*, so
  reviewers stop once they confirm it's "adopted" without verifying adoption is **total**. When the
  shared component's doc-comment names the exact call sites (or the exact prior drift) it fixed, **diff
  that named set against a fresh whole-tree grep** for the same string/concept; any hit outside the
  named set is a **candidate** straggler — confirm it renders before treating it as reintroduced drift
  (grep finds candidates; the render trace confirms). Higher-confidence than a cold duplicate search —
  the comment describes the "before" state, so you match a known defect instead of guessing.
- **The unassembled molecule — duplication with no shared literal string.** The twin-search above keys
  on a duplicated *string*, which misses call sites that each correctly use the **same underlying
  primitives** (say an icon plus a tooltip/popover) where no one has composed them into the one compound
  widget the recurring concept deserves. The **assembly** carries the real decisions — which a11y
  attributes, native `title` vs the shared tooltip, sizing — so the ad-hoc assemblies silently diverge
  on exactly those, and one site's hard-won fix (e.g. a documented conflict with a
  screenshot/visual-test tool) never propagates because it lives only in that file. The visible label
  differs per site, so grep for a repeated **scaffolding** pattern instead — the same small
  a11y-attribute cluster, or a one-character glyph inside a small rounded element — recurring across
  files that import no common component for it. If the design system already ships the primitives, the
  fix is to build the one shared atom, not just reconcile the wording (the wording was never the only
  thing diverging).
- **Sibling view-variants of one concept each re-declare the shared lookup or primitive the others
  import.** When one entity shows through alternate *layouts* — a compact vs expanded card, a horizontal
  vs vertical diagram, a table vs list a parent switches between — each variant tends to carry its *own*
  copy of a mapping or sub-element rather than resolving the shared source. Distinct from the two
  bullets above: not a whole component missed at a call site (*adoption-is-total*), nor a primitive no
  one has composed (*unassembled molecule*) — here the shared atom **exists** and this variant's file
  **already imports it** for a neighbouring member, so the gap hides behind a present
  `import { … } from './primitives'` that reads as finished. Two shapes: **(a)** an
  enum→label/colour/tone **lookup map** (`Record<Status, …>`) where the union *type* is centralized and
  imported but the map over it is inlined — *type centralized, map not* is the tell; **(b)** a
  sub-element's **derivation-plus-render pair** (a centre readout, an axis block, a legend) left inline
  in one renderer while siblings pull it from the shared module. The hazard spans present and future:
  the inline copy may *already* be a member behind (diff it against the shared map key-by-key), and any
  enum member or sub-element fix added later reaches only the shared source, so that one variant
  silently renders a blank/wrong label, off-brand colour, or stale block, while each variant reviewed
  alone looks correct. Detect by enumerating **every** renderer of the enum or diagram (grep the union
  type, or the parent's layout-toggle option list) and confirming they resolve **one** lookup/primitive;
  a variant with its own inline map or sub-element when a shared one exists is the finding. Same
  sibling-variant family as the row-affordance / view-switch / search bullets below, but the divergence
  is a duplicated *source*, not divergent *handling* of a shared one. Fix: the variant imports the
  shared module and it becomes the single place a new member is added; the one legitimate per-variant
  difference (a size class) becomes a prop, not a second copy.
- **A centralized *value resolver* makes the DRY gut-check pass while the *render* around it is still
  hand-rolled per call site — value unified, markup not.** A team factors the shared *logic* of a
  recurring element into one function — `resolveCategoryColor(key)`, `getStatusVariant(s)`, a
  `Record<Enum, className>` lookup — imported at every surface, so a **DRY pass sees no duplicated magic
  values and signs the concept off as "unified."** But the resolver only centralizes *what value to
  use*; the **wrapper markup that consumes it** — the element (`<span>` vs `<div>` vs a pill), class
  scaffolding, a11y attributes, an optional icon/dot, sizing — is re-written independently at each call
  site, so the *render* drifts exactly where the resolver can't reach: one site paints a dot + text,
  another a filled pill, another adds an icon, all calling the same `resolveCategoryColor`. The tell is
  **duplicate render blocks (often in the same file) wrapping the same resolver call**, not a duplicated
  value — why the twin-search and a DRY check on the resolver both miss it. Fix: consolidate the
  **render**, not just the value — build one component (`<CategoryBadge category={key}/>`) owning *both*
  the resolver call and the markup, its one legitimate per-site difference a prop (size/variant);
  centralizing the value is necessary but not sufficient. **Distinct** from the
  sibling-variant-re-declares-lookup bullet above (there the **lookup map itself is inlined** per
  variant; here the map/resolver *is* shared — *value centralized, render not*, the next rung down);
  from *the unassembled molecule* (there **no** shared composition exists; here a shared resolver *does*
  exist and is precisely what masks the render duplication); and from *One component, divergent props*
  below (there **one render component** exists and a feature-prop defaults off; here there is **no**
  shared render component, only a shared value). Refines the concept-fragmentation root (*"Feels like a
  prototype"*, `ux-sweep.md`) — a concept can look consolidated because its value is centralized while still
  re-implemented N ways at the render layer, so audit the **wrapper markup per call site**, never
  conclude "unified" from an imported resolver alone. Detection: grep the resolver's **name** for
  callers, then diff the **markup around each call**; divergent wrappers over one shared resolver is the
  finding.
- **A raw value hardcoded equal to a design token's *current* value is design-system drift that renders
  identically today and breaks the moment the token moves.** This section's *one source per concept*
  thesis covers **design tokens** — a spacing step, colour, radius, z-index — as much as components: the
  token is the single source, and a component writing the literal (`padding: 16px`, `color: '#2563eb'`,
  `borderRadius: 8`) instead of referencing it (`var(--space-4)`, `tokens.color.primary`,
  `theme.radii.md`) has forked that value. Invisible to every check comparing the *rendered* result,
  because the literal was chosen to equal the token's value **now**: the hardcoded copy and its
  token-referencing siblings paint the same pixels, so a screenshot diff, visual-regression snapshot,
  and eyeball pass all agree "consistent." The drift is **latent** — when the token changes (a rebrand,
  a density pass, a dark-theme remap, a 4px→8px grid migration) every referencing sibling moves and the
  hardcoded one silently stays, so the surface that looked most conformant becomes the lone off-brand
  element, caught only by the next screenshot after the change. Detection can't grep the token *name*
  (the literal never names it); use the **siblings as the oracle** — if most components of a class
  reference a token and one writes a literal equal to a defined token's current value, that literal is
  almost certainly a bypass, not a deliberate one-off (same minority-outlier diff as the
  disclosure-`aria-expanded` sweep in `a11y-focus.md`). Mirror shape: the **same literal with no
  token at all, repeated across N siblings** (`16px` inlined everywhere) — that repetition signals a
  token *should be extracted*, H's duplicate-source-drift at the value level. Fix: reference the token —
  or, for the no-token case, define one and point every sibling at it. **Distinct** from the
  sibling-variant-re-declares-lookup bullet (that inlines a *lookup map or sub-element*; this hardcodes
  a *scalar style value*) and from the duplicated-string twin-search (that duplicates a *literal
  string/markup block*; this duplicates a **token's value**, a finding *precisely because* it renders
  identical, not visibly duplicate). A genuine one-off that must **not** track the token is the
  fail-open exception: mark it (a named constant or comment) so it reads as chosen, not drifted.
- **A shared-recipe / design-token *migration* is audited for completeness by enumerating the control
  TYPE, not the shared component's importers.** When a team migrates a recurring control — a segmented
  control, pill/tab group, filter-chip row — onto one shared recipe or token set, the natural
  completeness check lists the shared component's **call sites (importers)** and confirms each looks
  right. That check is structurally blind to two ways a control stays on the old recipe, since both
  import the shared thing **nowhere**: (a) a control built **later or in a parallel branch**, never
  migrated, still carrying the *old* recipe's markup/class signature; and (b) a control that **cannot**
  use the shared component at all — a state-toggle that isn't a real navigation link, an item needing a
  different role (the *one control, one role* split in `frontend-a11y.md`) — hand-rolling a copy
  instead. Both render correctly today, so a per-screen pass and visual snapshot approve; the drift is
  **latent**, exactly like the hardcoded-token bullet above — when the shared recipe or token moves,
  every migrated instance follows and these lag into off-recipe stragglers. **Enumerate by the control
  CLASS**: grep the *old recipe's* signature (class names, markup shape, inlined literals) and any newer
  variant of the same visual control, take that population, and diff it against the migrated/importer
  set — every member not resolving to the shared recipe is a candidate straggler (confirm it renders,
  per *Fix the surface that renders* below). **Distinct** from the adoption-is-total bullet above (which
  diffs a named-fixed set against a grep for the shared *concept/string*, assuming a straggler *should*
  have imported it — here the search key is the **control type/old-recipe signature** precisely because
  a non-adopting control carries **no** shared marker) and from the hardcoded-value-equals-token bullet
  (a *value-level* check **within** one control — this is the *population* question of **which**
  controls to check at all).
- **A "we'll migrate the rest later" claim is only as good as the ticket behind it — and the leftover
  sites it defers are the ones that *structurally* can't adopt the shared component.** The
  audit-migration-by-control-TYPE bullet above owns the **population** question and the two ways a
  leftover carries no shared marker: (a) never migrated, (b) *can't* use the shared component. This
  bullet owns two ways that leftover stays **hidden even from that sweep**. **(1) The migration is
  "tracked" only in a code comment, not a real ticket.** An extraction that *admits* the leftover —
  `// migrating the server-rendered empty state onto SharedEmptyState is a tracked follow-up` — reads as
  diligence, so a reviewer trusts the claim and moves on; but the follow-up was never filed, so nothing
  forces consolidation and the shared component and un-migrated copy drift apart (an a11y fix, a prop, a
  copy tweak lands on one and not the other — the latent-drift consequence the audit-migration and
  hardcoded-token bullets already name). **Verify the claim against the tracker; don't take the
  comment's word:** grep comments and commit messages for promise phrasing (`tracked follow-up`,
  `migrate … later`, `should become a thin call of`, `consolidation deferred`), and confirm a real open
  issue names the specific two components. A structurally-confirmed duplicate with no tracking issue
  means the claim is false — file the follow-up. Distinct from mining an *avoidance* comment ("we
  avoided the shared component because…" — a stated reason not to use a primitive, a bug already
  worked around) — this mines a comment **promising to finish** a migration,
  and the action is to *verify the promise was kept*, not treat the deviation as the bug. **(2) The one
  relevant leftover is buried in a multi-branch empty-state conditional, masked by legitimately-distinct
  siblings.** A search-like view chains several empty states — *no query yet* / *query too short* / *no
  text matches* / *matches exist but a filter removed them all* / *results* — and only the last is the
  shared "filtered-to-zero" concept; the others are genuinely different and must **not** be forced into
  it. A concept-grep (`No .* match` / `.* match .* filters`) over-matches the legitimately-distinct
  branches, so a reviewer sees "several empty states for good reasons" and stops without classifying
  **which** branch is the shared concept in disguise. Tell: that branch's copy reads as a **prose
  instruction** ("clear a filter to widen the results") rather than an actual control, because the
  working clear button lives elsewhere, wired to a different, often hand-rolled affordance. **Fix the
  framework-boundary survivor at the component, not the call site:** a server-rendered site hand-rolls
  an *action-less* empty state because the shared component takes a client `onClear: () => void` it
  can't pass (blind spot (b)'s server/client-boundary case — a framework boundary, not a wrong role) —
  extend the shared component to accept an **action-descriptor** (an href/action form) alongside the
  bare callback, and when closing an "extract shared component X" ticket **enumerate the call sites
  excluded and why**, rather than closing on "every match of the old pattern is gone." Distinct from the
  **adoption-is-total** bullet above — here the survivor either **couldn't** adopt it (framework
  boundary) or hides behind a *false* "tracked" claim, so it never appeared in a named set to diff
  against.
- **A fix to a shared concept lands in the shared component**, not in one caller — otherwise the same
  defect survives in every other caller, and whoever checked only the screen they were shown signs off a
  still-broken app.
- **Fix the surface that renders, not the first grep hit.** A string can live in a file the target route
  never renders; trace route → component and confirm the component is actually shown before editing it.
  Grep finds candidates; the render trace confirms (cross-ref `parallel-audit.md` §5).
- **Zero mount paths from any entry is the dead-render candidate — the proactive form of the same
  check.** The rule above disambiguates *which* of several candidate surfaces a grep hit renders; this
  is the case where the trace turns up **none**. A component can be cleanly exported and carry its own
  passing unit test — `render(<Widget />)` mounts it directly, keeping the suite green — while having
  **zero mount paths from any router entry, page, or parent component**: nothing on a real route ever
  imports it into a reachable tree. The file reads as alive (exported, tested, maybe lint-clean) and is
  shown to no one. **Different discriminator from domain H's dead-code-removal rule**
  (`domain-h.md`): H's unreferenced-code check is blind to this case, since the component
  *does* have a reference — its own test import — so a plain reference-count linter passes it clean; the
  defect here is *render*-reachability, not *reference*-count. H treats truly unreferenced code as
  maintenance/attack-surface and defaults to **delete**; this is a **product** defect — something built
  to be seen isn't — so the default remedy flips to **wire it up**, retirement the owner's call.
  Detection: walk the router/page tree inward from every entry; a component reachable from **no** entry
  — only its own test file or other already-dead code — is a **candidate**, not confirmed, exactly like
  the straggler check above. A static import trace is blind to `React.lazy()` / dynamic `import()`, a
  string-keyed registry, a CMS-driven map, or a runtime route config — check those too; where they can't
  be checked, the zero-entry result is `unverified`, not found-nothing (could-not-check discipline,
  Enforcing gate in `ux-gates.md`). Flag a confirmed case to **wire it up or retire it**; retirement is an owner
  call under *Decisions needed (owner)*, never a unilateral delete.
- **One component, divergent props, is the other half of inconsistency.** Even a correctly-unified
  shared component reads as inconsistent when a **feature-bearing optional prop defaults off** and some
  mount sites omit it — one listing passes `votes` (the chip shows), another embedding doesn't (no
  chip). Each render is individually correct; together they look cheap, and the twin-search above won't
  catch it since it *is* one component. For any shared component with a feature-bearing optional prop,
  **enumerate every mount site and diff the props**; a feature that should be universal belongs
  **inside** the component, not behind an opt-in a caller can forget. Review question: "does this
  concept render identically at *all* its mount sites?" — don't stop at "it's one component."
- **In a port or migration, unification is a precondition, not a cleanup pass.** Enumerate the shared
  concepts and adopt exactly one component per concept **before** porting screens — a duplicated concept
  is a defect a reviewer *will* find, and retrofitting unification while the owner watches is far slower
  and noisier than building it once up front.
- **Row-click-affordance inconsistency — a detection gap, not a remedy gap.** An entity-row (same
  fields, same detail target) is whole-row-clickable — mouse and keyboard — on one page, and only a
  single inner `<a>`/`<Link>` cell is interactive on a sibling page importing a *different* row
  component. It clears WCAG (named, reachable, focus-ringed) and has no shared component to check
  adoption on, so a11y tooling, a per-page review, and the twin-search above all pass it clean —
  distinct from the *interaction-consistency* bullet in `ux-interaction.md` (its row-class parity is *style*-reaction
  parity across *one* shared component's instances; this is affordance *existence* across *separate*
  components). Detect by enumerating every renderer of the row type (grep the shared fields/link target,
  not a literal string) and diffing row-level interactivity against a lone anchor. Fix: one shared row
  component/hook where feasible; else extend the affordance without a **second tab stop** — the inner
  `<a>`/`<Link>` stays the single named, focusable control (a `event.target.closest('a,button')`-guarded
  row `onClick` adds a mouse convenience over it; or a stretched-link `::after` overlay extends the
  anchor's own hit area, preserving native middle-click / open-in-new-tab / copy-link). Don't add
  `tabIndex`/`role` to the row while an inner link already reaches the detail: a second focusable with
  no role or accessible name reads worse to a screen reader than the lone anchor it duplicates
  (`frontend-a11y.md`'s `role`/`tabindex`-pair grep and keyboard floor). The row needs its own
  `tabIndex={0}` + Enter/Space **and** an explicit `role`/accessible name only when it has no inner
  focusable path to the detail — noting a `role` on a `<tr>` overrides its native row semantics, and a
  stretched link changes text selection over the row. Name every renderer of the row type in a "make row
  X clickable" ticket's acceptance criteria, not just the page that prompted it.
- **A view/tab-switch link built from a narrow param allow-list silently drops the active filter.**
  Sibling *view* tabs (list / table / chart / map) over one dataset, addressed by a shared `?view=`
  param, plus a cross-cutting search/filter (`?q=`, facet params) meant to apply to every view. The tab
  strip's href-builder encodes only the base route + `?view=` and does **not** read and forward the
  *current* query string — so clicking a sibling tab while a filter is active navigates to a URL that
  dropped it: the destination renders unfiltered and the search box comes up empty, reading as
  "switching views clears my search." Same family as the row-affordance bullet above — the inconsistency
  lives in one renderer's own link-building, invisible from the shared control. Detect: find the
  tab/view href-builder and classify whether it composes the destination from the **full current param
  set** (overriding only `view`) or a fixed allow-list; a builder naming only `view` drops everything
  else. Fix: build the target href by merging over current params (change `view`, preserve
  `q`/facets/sort), and test that switching view with a filter active preserves it. Decide per param
  whether it's view-scoped (may reset) or cross-cutting (must persist) — never drop cross-cutting state
  by omission.
- **A shared search *filters* on one renderer but only *highlights* on a sibling — and the highlight can
  land behind a fold.** One dataset rendered through two layouts (a tree/list and a diagram/grid)
  sharing one search input. The first-hardened renderer, on a match, **filters** non-matches out **and
  force-expands** the match's collapsed ancestors so it's guaranteed visible; a later,
  structurally-different renderer wires the same value only to a **cosmetic highlight**
  (ring/background) — never filtering, and a match nested inside an independent, user-collapsed fold is
  neither force-opened nor annotated, so a term that worked on the first layout appears to do
  **nothing** on the second (its one visible effect sits behind a fold the user can't see). Same family
  as the two bullets above: the divergence is in each renderer's own handling of the shared value,
  invisible from the shared input, and a caption near it may already claim "search narrows every view"
  without distinguishing *filters* from *merely highlights*. Detect: per renderer, classify the search
  value's use as **filter** (participates in an include/exclude decision) vs **highlight-only** (only a
  className/style); for a highlight-only renderer, check whether any collapse/fold boolean references
  the search/match state — if a fold is computed with zero reference to it, a match inside renders with
  a class the user can't see. Fix: decide per renderer whether search filters or only highlights, and
  make the UI copy match (a caption claiming "narrow" over a highlight-only control is itself a defect);
  where highlight-only sits behind independent fold state, key that state off the active search — force
  the section open or show a "N matches inside" count on the collapsed ancestor. Test the combined
  state: a match nested inside a manually-collapsed ancestor must be visible or explicitly signposted,
  not merely present in the DOM with an invisible class.

## One component at two scopes — single-entity vs aggregate needs scope-aware copy

A shared component reused at **two scopes** — a single entity vs an all-entities
**aggregate/rollup** — but with labels and empty-states **hardcoding the single-entity
phrasing** ("the items *this* owner has", "nothing here for this owner yet") reads wrong or
misleading at the aggregate scope. Related forms: the aggregate view **drops** a section the
single-entity view shows, or lists an unbounded union of rows with **no attribution** of which
entity each row belongs to — so the rollup is unreadable and the two scopes feel inconsistent.

- **Make copy and empty-states scope-aware** — interpolate the scope (the entity name at single
  scope, "all …" at aggregate), don't hardcode one.
- **At aggregate scope, label each row with its owning entity** and **cap/paginate** the union
  (the overflow state).
- **Keep the section set consistent across scopes** unless a per-scope variant is deliberate and
  stated — and at aggregate scope specifically, **hide a view whose number would be a
  *misleading aggregate*** (a rate or total meaningless across heterogeneous entities):
  computed-not-fabricated (principle 3) beats symmetry, exactly as in `migration-parity.md`'s
  misleading-aggregate exception.

A **different axis** from the neighbours: not the *prop* axis (#123 above — one component, a
feature prop present at one mount site and absent at another) and not the *section-set superset*
across **sibling per-entity** surfaces (`migration-parity.md`), but the **single-vs-aggregate
scope** of one component's copy and attribution.
