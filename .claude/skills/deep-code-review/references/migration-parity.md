# Migration & prototype-reference parity

Read this when the reference you are matching is a **prototype / mockup / design
export** (a static page, a design-tool frame, a clickable prototype — typically
built on a handful of seed rows), or the task is a **port / migration to a
reference design**. Expands section P of `SKILL.md`, alongside `frontend-a11y.md`
(a11y correctness) and `product-ux-quality.md` (the design half). The failures this
file prevents: porting a migration screen-by-screen with **no unified chrome** (an
unbounded defect stream), over-claiming parity from the wrong evidence, recommending
the **deletion of real features** to match a sparse reference, and shipping a UI that
matches structurally yet feels poor to use.

---

## Unify the chrome/shell before porting screens — one level above component unification

The unification precondition (`product-ux-quality.md`, one component per concept)
has a level **above** individual components: the **chrome/shell** — per-page header,
tab/section strip, stat-tile frame, sub-nav, and the rule that decides which tabs a
surface shows. Porting the *outer* frame (sidebar, top bar) to a shared component
does **not** unify the *inner* chrome: it can still split into independently-authored
families — one composing the shared header + nav-link tabs, a sibling bypassing it
with a bespoke inline header (a raw font-size, not the token) + a hand-rolled
local-state pill strip. When it does, every downstream "why is this styled
differently / this has fewer sections / the strip won't stick" complaint is one
divergence per surface, "fixed" per-surface without converging. **A per-surface
migration with no unified chrome is an unbounded defect stream** — the tell that the
divergence is structural, not per-screen.

- **Enumerate the chrome primitives first, and confirm every surface renders through
  the shared ones *before* porting individual screens.** A surface that reimplements
  a chrome primitive is a **structural defect**, not a nit.
- **Align the outlier family *to* the consistent majority**, not the reverse — if two
  surfaces diverge and thirteen agree, fix the two; don't rebuild all fifteen.
- **Render the same sub-view *superset* across structurally-similar surfaces**
  (per-entity dashboards) with honest-empty states — not a hand-picked per-entity
  subset — so absence reads as "nothing here yet," not "this entity is different."
  **The one exception is load-bearing:** if a view would render a **misleading
  aggregate** at that scope (a rate/total that is wrong or meaningless for this
  entity), keep it **hidden** — **computed-not-fabricated (principle 4) beats
  tab-count symmetry**. Symmetry is the default; a hidden view is justified only by
  "the number it would show is wrong here," stated in the finding.
- **Unify a control that exists in two *behaviors* by its styling, not by one
  dual-mode component.** A navigation link and a local-state toggle can look
  identical yet carry **different semantics** — `aria-current` for the nav location
  vs `aria-pressed`/expanded for the toggle. Extract the **styling** into one shared
  primitive and wrap it in two thin behavior wrappers; do **not** collapse them into
  a single component with two mutually-exclusive prop modes, which breaks a11y (the
  unwired mode emits the wrong role, focus, and keyboard order — `frontend-a11y.md`).
  This is the **complement** of the feature-flag rule, not a contradiction of it: a
  feature that is *present-or-absent with the same semantics* belongs **inside** the
  component (`product-ux-quality.md`, one component per concept, #123); two
  *different behaviors* stay **separate wrappers over one shared style**.

## Verify parity surface-by-surface, on real data — never from a structural or seed-data audit

A structural component audit, a green test suite, and a section-by-section
screenshot comparison **over-report** parity. They miss exactly the divergences
that appear only on real data and real use: which view a route **defaults** to,
whether a composer carries every field the reference has, whether shared components
are actually unified or quietly reimplemented per page, whether a sub-view was
dropped, whether live data is even populated. Parity is verified
**surface-by-surface, interactively, on real data**: for each surface, drive the
real control and diff against the reference's **actual rendered behaviour** —
default state, every field, every sub-view/mode, data population — not its static
screenshot. Treat every "matches well" as **unverified** until the real surface is
exercised against the real reference. (The structural / green-suite / seed-screenshot
stand-ins are the "Beware the proxy" completion trap — `report-format.md`.)

## Anchor findings on treatment, not data-volume — a sparse mockup is not a feature spec

When the reference is a prototype on seed data, a section-by-section comparison
flags the production surface as "too dense / too tall / a wall of cards" because it
renders **real** data (dozens–hundreds of rows) while the mockup shows three to
five. Much of that "gap" is a **data-volume artifact**, not a design difference —
the mockup's calm emptiness is partly just emptiness. Anchor findings on
**treatment** (layout structure, spacing scale, component choice, hierarchy,
chrome/nav, default view, empty/overflow handling), **not** absolute list length,
page height, or item count.

Separate three kinds of "gap" explicitly — they have **opposite** fixes:
- **(a) genuine treatment difference** — restyle to match.
- **(b) data-volume artifact** — the surface is larger because it holds real data;
  the fix is **progressive disclosure / capping / pagination**, *never* deletion.
- **(c) a real extra feature** the production surface has and the mockup lacks —
  **preserve it**; a design mockup is a look reference, not a feature spec.

**"Drop / replace / remove X to match the reference" is a review smell** for any
surface that renders real data: it is a path to deleting working features and
violates do-no-harm (principle 4) and the never-remove-a-working-feature-without-
confirmation bar. Rewrite the recommendation as "adopt the reference's layout and
default; move the extra content behind progressive disclosure." A page-height or
item-count delta versus a seed-data mockup is a **notice, not a defect** — say so
in the finding, so a downstream implementer does not read it as a cut order. Before
recommending any structural change to a real surface from a mockup, confirm the
difference is **treatment** (reproducible on **equal** data), not volume.

## Flow-cost — navigation cost, scroll burden, and cognitive load are first-class

Structural and pixel parity are necessary but not sufficient: a UI can match the
reference element-for-element and still feel poor, because the failures live in the
**interaction flow**, invisible to a per-screen diff. Run a **flow-cost pass**,
distinct from structural correctness, for each primary task:
- **Navigation cost** — count clicks + scroll distance to complete the task **and
  to reverse / switch**. Flag "must scroll back up to a top nav to change section"
  (→ sticky nav or tabbed sections), "N clicks for a common toggle," and "content
  pushed below a tall element."
- **Cognitive load** — the number of simultaneous choices offered, instructional
  sentences that could be a tooltip or removed, competing primary actions. (N
  interchangeable variants of one thing is the **variant-bloat** smell — cut to one
  default: `product-ux-quality.md`.)
- **Completion bar** — "the components match" or a green suite is not "done" for UI
  work; the bar is the subjective-quality completion bar defined under "Beware the
  proxy" (`report-format.md`).

## Ground the craft bar in cited heuristics, not ad-hoc taste

"Looks about right" is not a standard, and a redesign that references no established
heuristics is guessing — which produces the weak hierarchy, inconsistent spacing,
low-contrast grey-on-tint, and wall-of-text that draw repeated rejection. Apply a
**cited** per-screen checklist and **name the principle** each item comes from: a
review cites the principle, it does not assert "this looks off / fine."

Grounded in **Nielsen Norman Group's 10 Usability Heuristics** (Nielsen, 1994; last
reviewed 2024 — verbatim names in `docs/standards-index.md`), **Refactoring UI**
(cited by name), and the **target's own design system** where it publishes
principles. The heuristic names below are NN/g's own:

- **Visibility of system status** (NN/g #1) — loading / empty / error / offline
  states exist and are honest; the current view and selection are always legible.
- **Match between the system and the real world** (NN/g #2) — labels in the user's
  language, not the schema's.
- **User control and freedom** (NN/g #3) — a clear exit and undo from every state;
  nothing irreversible on one mis-click.
- **Consistency and standards** (NN/g #4) — one component per concept, one spacing
  scale, one type scale, platform conventions (depth: `product-ux-quality.md`, one
  component per concept; scales from Refactoring UI).
- **Error prevention** (NN/g #5) — constrain inputs; confirm the consequential.
- **Recognition rather than recall** (NN/g #6) — keep options visible; don't force
  the user to carry state across screens.
- **Flexibility and efficiency of use** (NN/g #7) — one strong default path plus an
  accelerator for the expert; keep power **behind progressive disclosure**, off the
  default surface.
- **Aesthetic and minimalist design** (NN/g #8) — hierarchy and **de-emphasis**
  (Refactoring UI); every added element competes with the primary action; cut
  self-evident instructional prose.
- **Help users recognize, diagnose, and recover from errors** (NN/g #9) — errors
  say what happened and how to fix it, in plain language.
- **Help and documentation** (NN/g #10) — reachable when needed, never a substitute
  for a self-evident UI.
- From Refactoring UI (by name): **one spacing scale and one type scale**,
  **semantic colour** (not decorative), intentional **empty states**, and
  **motion** with specific durations / easings that honour `prefers-reduced-motion`.

A **"does this feel premium?"** pass closes it — but as a prompt to locate the
specific heuristic a screen violates, never as a substitute for naming it.
(Benchmarking the redesign *direction* against two or three comparable products is
a separate move: `product-ux-quality.md`, *Match a named standard*.)

---

## 🚩 grep / signals

- A parity claim ("matches the reference") backed only by a structural audit, a
  green suite, or seed-data screenshots — with no surface-by-surface real-data pass.
- A recommendation to **drop / remove / replace** a surface or its content to match
  a **prototype / mockup** reference (real data → progressive disclosure, not
  deletion).
- A comparison treating **page height / row count** versus a seed-data mockup as a
  defect rather than a notice.
- "Match the reference and use judgment" with **no cited heuristic** named behind a
  redesign recommendation.
- A primary task that needs a **scroll back to the top nav** to switch sections, or
  N clicks for a common toggle.
