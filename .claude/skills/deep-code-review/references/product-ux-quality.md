# Product UX quality — the "at-home" bar (domain P, design half)

Read this alongside `frontend-a11y.md` when the target renders a **product UI a
human operates** — a dashboard, table, form, chart, legend, or metric display.
Expands section P of `SKILL.md` (the design half). `frontend-a11y.md` owns a11y
**correctness** (WCAG 2.2 AA, keyboard/focus, contrast, Core Web Vitals, the
cross-view accessible-name pass); this owns whether the UI feels **at-home** —
conventional, self-evident, correct in every data state, and cleanly encoded.
Same spine as the rest of the method: respect the existing design, separate a
defect from a redesign, verify live, and ground every claim in a named standard —
never "looks nicer."

Ground the design half in the tiers the skill already tracks: **WCAG 2.2**
(colour, contrast — via `frontend-a11y.md`), **Nielsen's usability heuristics**
(named, not URL-cited — see the by-name list in `README.md`), and the public
precedent of top products (Linear, Stripe, Notion, Vercel, Figma, Datadog,
Google/Material, Robinhood) — named the same way this skill already names Cursor,
Copilot, and OWASP, and added no differently: no new URL, version, or date the
reviewer did not fetch (principle: no fabrication).

---

## Matching a convention is an observation, not a licence to redesign (read first)

This mirrors `frontend-a11y.md`'s "Respect the existing design," and it is the
rule that keeps this reference net-positive on every axis. A product-UX finding
**improves** the product; it must never silently restyle it.

1. **Separate the defect from the redesign.** A blank screen on a reachable
   state, a delta coloured the wrong way, a legend that is a wall of prose, a
   dead control — these are **defects**, fixed in place, minimally, preserving
   the existing look. A change that alters layout, spacing system, type scale,
   component set, or brand *to match a convention* is a **redesign** — an owner
   decision, not a review fix.
2. **Surface the convention gap under "Decisions needed (owner)."** When a design
   deviates from a named top-product pattern (legend, delta, empty state, date
   picker, table), record it with the precedent cited and the
   **minimal-visual-impact** fix offered first — exactly as `frontend-a11y.md`
   handles a layout/brand change. Import the requirement to *notice* the gap;
   keep the discipline that the owner decides. "Looks nicer" is not a reason —
   and neither is "the convention says so."

---

## Repeated owner rejection is a redesign trigger — surface options, don't tune (or impose)

The section above bars a redesign driven by *your* taste. This is its complement,
resolving the same tension from the other side: a redesign driven by the **owner's
own repeated rejection** of the same element is warranted — but as options the
owner chooses, never a change you tune your way into or impose. Both obey
principle 5 (*respect the existing design; separate a defect from a redesign;
surface it, don't impose it*).

- **Trigger: the owner rejects the same element two or more times** ("bulky /
  confusing / too heavy / looks wrong"). That repetition — not a reviewer's
  aesthetic read — is the evidence the approach is **structurally** wrong, not
  under-tuned. A first rejection is feedback to apply; the *same* rejection twice
  says the structure, not the parameters, is the defect.
- **Stop tuning.** Nudging padding, arrows, spacing, or counts cannot remove a
  structural defect (three overlapping rings do not stop overlapping because the
  arrows moved). Re-tuning after a second identical rejection is the failure this
  rule names — the design-half form of principle 9 (*root-cause, not symptom*):
  after the same failure twice, change the approach, do not repeat the fix.
- **The same move for a *verification* claim: repeated correction means your
  method is broken, not their patience.** If a stakeholder repeatedly corrects your
  "it matches / it's the same," that is evidence your **verification method** is
  wrong — not a cue to ask them for more examples. Change the method: build the
  comparator (the **parity differ**, Phase-6 *Enforcing gate* below) and show its
  diff, rather than outsourcing your verification back to the person reviewing you.
  Report only what you actually inspected on the target ("the nav now reads A · B ·
  C, I looked at it"), never a blanket "it matches"; an honest "not yet verified"
  beats a false positive (principle 9 again — after the second false "matches",
  change the instrument, do not re-assert).
- **Name the structural flaw in one line**, then research how **two or three
  comparable products** (named, per *Match a named standard* below) solve the same
  problem — the muscle memory the new direction should borrow.
- **Hand the owner concrete options to choose — show, don't tell.** A side-by-side
  of two or three real directions is a decision the owner makes in seconds; a
  paragraph describing them is not. Product/redesign choices are owner decisions
  and never carry Blocker/Critical gate language (SKILL.md Phase 5).
- **Variant/option bloat is the supply-side of the same smell.** N interchangeable
  ways to view or style one thing — seven style-toggle tabs on one diagram, eight
  overlapping list modes — reads as unfinished, not powerful: the *choice* is the
  defect, so the fix is **cut to one strong default**, not tune the set. Test:
  would a first-time user know why to pick one over another? If not it is bloat,
  not flexibility. Distinguish redundant variants (overlapping modes, decorative
  toggles) from genuinely different tools (a diagram vs a table serve different
  tasks — keep both), and keep the power path reachable behind **progressive
  disclosure**, off the default surface.

---

## Every data state — rule on each, not just the happy path

Every view is intentional and honest in **all five** states, each ruled on
(finding, clean, or `unverified`):
- **empty** — say what will appear and how to get it (never a bare void);
- **loading** — skeleton/spinner, no layout flash;
- **error** — what failed and how to recover, **never a raw stack or blank**;
- **partial** — some data present, some missing/degraded, shown honestly;
- **overflow** — too many rows → scroll/paginate/virtualize **inside the
  component's own container**, never breaking the page layout.

A blank screen or a raw error on a **reachable** state is a P0 "not-at-home"
defect, not a nit — severity by reachability, like any other defect. (Nielsen:
visibility of system status; help users recover from errors.) `frontend-a11y.md`
owns the *phrasing/consistency* of empty states across routes; this owns whether
each state **exists and is honest**.

**An empty state must not imply a conclusion it hasn't earned.** "No rows shown"
is not "nothing happened": an empty activity feed, an all-green board with no
data behind it, or a zero-count that is really an *uncollected* count all read to
the user as "all clear / no risk / no activity" when the truth may be that the
source was never queried. The empty state must distinguish *no data collected or
covered* from *collected, and genuinely none* — SKILL.md principle 2 (*an absence
is evidence only after a positive control fires*) at the UI layer. Name the
coverage, not only the remedy: a bare "Nothing here" over an unprobed source is a
false all-clear, not an honest empty. (`data-quality.md` §8 owns the same rule
where the number is *scored* rather than *shown*.)

## A reversible action reads as a delete when nothing shows the record persists

When an action **presented as non-destructive** — resolve / archive / dismiss,
backed by a retained column (`resolved_at`, `archived_at`) — removes the record
from view while giving **no cue that it persists, is reversible, or where it went**,
the user cannot tell it from a hard delete. Two failures:
- **Product-safety.** The action *reads* as destructive: a first-time user clicks
  "Resolve," watches the row vanish with no "Resolved" state, no undo, and no
  reachable resolved view, and reasonably concludes they deleted it — suppressing a
  reversible, low-stakes action and eroding trust in it.
- **Audit / history visibility.** When the retained trail is *meant to be
  reviewable*, a surface with no way to reach it makes that history effectively
  invisible — the data layer keeps a record the UI never surfaces. (The data is
  intact; the defect is visibility, not integrity.)

**The defect is the hidden reversibility, not default-hiding as such.** Hiding a
completed item is often the *correct* convention — an `is:open` list, an active-only
board, an inbox that archives out of view all hide a retained record on purpose,
behind a well-known filter; those are conventions, not defects (matching a
convention is an observation, not a licence to redesign — read-first opener above).
A **soft-delete** (`deleted_at`) is out of scope: "reads as a delete" is its
*intended* behaviour; its concern is recoverability / trash-visibility, not this.
Like the actionability rule, this is **fail-open**: a heuristic cannot tell a
hidden-reversible action from a deliberate convention, so a human adjudicates every
hit — surface options, never silently restyle.

The self-evident fix — how mature issue-trackers and code-review tools render a
resolved thread — keeps the record **in place, visually muted** (opacity or
strikethrough) with a **status label** ("Resolved"), or offers a clearly labelled,
discoverable "resolved / archived" view. Cross-checks: the affordance must **not
rely on colour alone** (pair opacity with a label or icon + accessible name, per
*Never colour alone* below); a "show resolved / archived" path must be
**discoverable**, not a buried default-off filter with no cue; verify on the
**running app's default surface**, not only a unit test. Distinct from the
honest-empty rule above (a *retained* record hidden by a *reversible* action, not an
empty state).

## Encoding hygiene — one visual channel per dimension

Never make **one channel carry two meanings**. The classic bug: colour encoding
two independent variables at once (green = both "instrumented" *and* "trending
up") — ambiguous, and invisible to an a11y-only pass. Split dimensions across
channels — **shape/fill** for one, **colour** for another, **position/size** for
a third. Run out of channels ⇒ you have too many encodings; cut some. Fewest
encodings wins.

## Never colour alone — colourblind-safe as a method

`frontend-a11y.md` owns the WCAG rule (1.4.1 Use of Color; and the 1.4.3
disabled-control exemption that a gate must not over-flag). This owns the
**testable method**: pair every hue with **shape, icon, or text** (▲▼ ↑↓ ✓ ✗ or a
word) plus an `aria-label`. Colour reinforces; shape carries the meaning. The
one-line test: **it must read correctly in greyscale.** Works in greyscale =
works for the ~8% of men with deuteranopia, and for everyone.

## The metric / KPI delta standard

A near-universal pattern with a right answer (Stripe, Google Analytics, Mixpanel,
Amplitude, Robinhood, Linear, Material) — inventing a novel one here is a cost:
- caret **▲▼** (or arrow ↑↓) **+ the magnitude** (`▲ 3`, `+2.1%`) — direction
  alone never says *how much*;
- colour by **sentiment, not direction** — "up" is not always good; a drop in
  churn / cost / latency / error-rate is **green**. Key the colour to the
  metric's polarity (direction-of-good), not to up/down. Backwards polarity
  actively misleads — a correctness defect, not a taste one;
- muted **`—`** when flat; anchor the delta to its period ("vs last month") in
  the tooltip/`aria`.

## Data visualization — a chart must answer a question, legibly

The delta standard above governs a single up/down number; a **plotted series** is
its own surface, and a chart can pass every other rule here — no overlap, no
colour-only status — while still answering no question ("what is this on that
date?" has no on-screen answer) or overstating what is known. Rule each chart:

- **Scale is legible.** A value axis with tick labels **or** direct labels; a bare
  shape with no scale is decorative, and a decorative chart is acceptable **only**
  when it is explicitly marked decorative (`aria-hidden`) **and** the exact number
  it illustrates is printed beside it.
- **A value + its anchor on demand.** Any non-trivial chart returns, on
  hover/focus, the **value and its date/category**, reachable by keyboard, not
  mouse-only (`frontend-a11y.md` owns the *a11y* of that interaction; this owns
  that a readout *exists and returns a value*).
- **Don't imply the unmeasured.** Mark real samples (a dot per reading) and never
  smooth or fill a **line across sparse points** — nothing between measured points
  is implied. Two or three readings drawn as a continuous trend is a fabricated
  trajectory, the visual form of principle 3 (empty beats fabricated).
- **Non-visual access to the numbers.** The chart is *additive* to a table or an
  `aria` summary, never the only path to the data; and series are distinguished by
  pattern/label, not colour alone (*Never colour alone*).

## Confidence shown as a bare number is false precision — flag it

A confidence, priority, or match score surfaced as a **raw number** ("87%",
"score: 0.92") claims a calibration the pipeline usually does not have, and invites
over-trust. It belongs on a **small set of labeled tiers** — text plus a
colourblind-safe cue (see *Never colour alone*) — not a percentage or an opaque
point score. **🚩**: a `confidence` / `score` / `priority` value rendered directly
as `{n}%` or a raw float in the UI with no defined tier label beside it; a
model-authored number published as precision. (How to *define* the tiers, and why
source reliability and claim corroboration stay independent axes, is a
data-product-output rule — `product-output-safety`'s — not restated here.)

**Measure the field's distribution before building the display at all.** Even a
*tier* is false precision if the underlying signal is **near-constant** — so measure
it first, on real data. A `corroborationCount` that is `1` on 16,008 of 16,012 rows
makes a "confirmed by N sources" badge fire on ~0.02% of rows and read "1 source"
everywhere else; a match-confidence that is `0.9` on ~70% of rows and `0.8` on the
rest is effectively binary, so "90% / 80% confidence" manufactures precision the
pipeline lacks. If the field barely varies, **showing it is false precision, not
transparency** — drop it, or reframe to something that actually varies (e.g. *how*
an entity was matched, not a number). A misleading signal is worse than an honest
blank — empty beats fabricated (`data-quality.md`).

## Actionability — a unit answers "why does this matter," not just "what happened"

The other domain-P rules prove a component **renders** correctly; this one asks
whether it **helps the user decide or act**. A feed, dashboard, or brief can pass
every render check and still be a **wall of verified facts** — each unit a *fact +
its source* with no *so-what / now-what*. That is a real UX defect, invisible to the
rendering rules.

- **Every primary information unit carries a why-it-matters signal — derived, never
  fabricated.** A unit a decision depends on states *why it matters* through a
  **structural / derived** signal: a count ("3rd of its kind this quarter"), a
  recency-delta ("first activity in 60 days"), a graph-degree ("connects to N
  entities you follow"). **Hard rule (anti-fabrication):** the signal is computed
  from real data — **never a model-authored "importance score" or an LLM judgement
  of salience**, which is the content-layer cousin of the false precision the
  confidence-tier rule above forbids. A derived signal that barely varies is not a
  signal — measure its distribution first, exactly as for a confidence tier.
- **Where an action is possible, name the concrete next step** on the unit (follow,
  open, assign, dismiss), not a bare record the user must decide what to do with. A
  signal-led feed maps each event to a follow or next step; a relationship surface
  offers a next-best-action, not just a row (a pattern, not a product endorsement).
- **Most-actionable-first, and stable.** The highest-decision-value surface is in the
  **first paint and stable** — not deferred to a post-hydration `aria-hidden` island,
  and not pushed below fixed non-interactive summary chrome (cross-ref layout-shift /
  CLS in `frontend-a11y.md` and the density/footprint rule below). Which order serves
  the user's job is ruled on in the ranking section below.
- **Lead with what's new *and* why it matters** — a reader's first two questions are
  "what is it?" and "is it relevant to me?"; a unit that answers only the first is
  half-built (the **Smart Brevity** pattern; `docs/standards-index.md`).
- **Defect vs redesign; the gate is fail-open.** Missing actionability on a decision
  surface is a **defect to surface**, not a licence to redesign a deliberately-terse
  product — separate the two, and never carry Blocker/Critical gate language on a
  product choice (SKILL.md Phase 5). The heuristic gate **warns and lists, never
  blocks** (unlike the fail-closed `ci-gates.sh` check-#6/#7): it flags a primary
  list/card whose unit is *fact + source* with no derived why-it-matters signal and
  no action affordance, and a top-value surface that is an `aria-hidden`-until-
  hydration island — but it **cannot tell "should be actionable" from "deliberately
  terse,"** so a human adjudicates every hit.

## Ranking & sort-mode legibility — the order is a product decision, not a default

The variant/option-bloat rule above targets view/style toggles; this extends it to
the **ordering of a feed/list itself**, and the confidence-tier rule targets a
*displayed* score, not the *ordering key*. The gap between them: is the **default
order** the one that serves the user's job, and is each exposed sort mode
**self-explaining and measurably distinct**?

- **The default order serves the user's primary job** (signal / importance /
  soonest-to-act), not implementation-convenient reverse-chronological. Recency is a
  *mode*, rarely the right *default* for a decision surface. (This is the canonical
  home of the default-ordering rule the actionability section refers to.)
- **Every exposed sort/rank mode is self-explaining and distinct.** Each mode carries
  an on-demand one-line *"orders by …"* (tooltip / helptext), and the variant-bloat
  test applies: **would a first-time user know why to pick "Top" vs "Momentum"?** If
  not, it is bloat — cut to one strong default, the rest behind progressive
  disclosure, each self-labeled. Two modes that produce **near-identical orders** are
  variant-bloat → collapse (measure the overlap, don't assume it).
- **The sort key needs a measured distribution — anti-fabrication (hard rule).** A key
  derived from real, varying signal is legitimate ranking; a sort by an **opaque or
  near-constant score is the ordering-layer form of false precision** — measure the
  key's distribution before shipping it as "ranking" (reuse the confidence-tier
  "measure the distribution first" rule above; a key that barely varies orders
  nothing). An order the user cannot explain and the data cannot justify is noise
  dressed as intelligence.
- **Multiple ordering regimes across surfaces** (a curated home *plus* a multi-mode
  feed over the same data) are a lot of ways to slice one dataset — consolidate, or
  cross-explain on-surface which regime serves which task. Warn-and-list, never block
  (a human tells a rich-but-legible set from bloat).

## Self-evident over explained — progressive disclosure

Layout + labels + standard components make meaning obvious **without** inline
prose. **If a screen needs a paragraph to be understood, the design failed — fix
the design, not the paragraph.** Demote explanation to a "?" tooltip, a hover, a
collapsible "How this works", or a dismissible first-run hint — available, not
shown by default. Legends/reference blocks: **collapsed by default**; when open, a
**grid showing the actual glyph** beside its meaning, never a paragraph
describing marks in words. Teach on the artifact itself via hover/focus; the
legend is the fallback teacher, not the primary one. (Nielsen:
aesthetic-and-minimalist design; recognition over recall.)

## Drawers, hierarchy, density

- Detail drawers **overlay** the current view — never navigate the background
  away; the user keeps their place and can inspect several items in a row.
- Correct collapse **scope**: a child collapses within its parent's subtree, not
  siblings two levels up.
- Declutter dense rows — few visible chips, secondary actions behind a menu,
  detail on hover. **No dead controls** — a toggle that does nothing is worse
  than none; it is a trust defect, not a cosmetic one.
- **Footprint tracks information — the opposite failure from a dense row.** The
  declutter rule above fixes an *over*-dense row; the converse defect is wasted
  space — an empty/undefined/placeholder record rendered at a **populated record's
  footprint** (a full card reading "No data source / No owner / —"), a grid that
  strands half a wide viewport, or a toolbar row holding one control across the
  full width. Collapse or group placeholders (a compact row, not a full card),
  give a grid/list a **density target at the wide viewport** (name the top-product
  precedent — a metrics grid, a list view — not a taste call), and fold stranded
  single-control chrome. The test is **information-per-screen, not
  pixels-per-item**: a screen that could show N× more at a glance without crowding
  is a density defect, ruled like any other. This is the *space-appropriateness*
  complement of *Every data state*'s honest-empty rule — a full-card empty state is
  honest and still wastes the footprint.

## Unified across modules — one component per concept

The consistency rule below has a structural cause and a structural fix.
**Inconsistency across views is almost always the same concept built more than
once and drifting** — a row, card, field, empty-state, status chip, or editor
reimplemented per page, so a fix to one misses the others and the app feels like
a different product on each screen. This is a maintainability defect (cross-ref
domain H) with a UX consequence, so it is ruled on here too.

- **One shared component per concept.** Before building a UI element, grep for an
  existing component or pattern that already does it and **reuse or extend it** —
  never reimplement per page. A duplicated UI string or markup block across files
  is the red flag (cross-ref H's duplicate-source-drift: byte-identical lockstep
  copies need a single source or a parity test). **Cross-file duplication is
  invisible to a diff-scoped review** — you see the file you changed, not its twin —
  so on any "unify" or "fix this component" task, grep the **duplicated visible
  literal string or section heading** across the whole tree as the search key that
  surfaces the twin, before claiming the concept unified.
- **A fix to a shared concept lands in the shared component**, not in one caller —
  otherwise the same defect survives in every other caller, and whoever checked
  only the screen they were shown signs off a still-broken app.
- **Fix the surface that renders, not the first grep hit.** A string can live in a
  file the target route never renders; trace route → component and confirm the
  component is actually shown on that screen before editing it. Grep finds
  candidates; the render trace confirms (cross-ref `parallel-audit.md` §5).
- **One component, divergent props, is the other half of inconsistency.** Even a
  correctly-unified shared component reads as inconsistent when a **feature-bearing
  optional prop defaults off** and some mount sites omit it — one listing passes
  `votes` (the chip shows), a second embedding doesn't (no chip). Each render is
  individually correct; together they look cheap, and the twin-search above won't
  catch it because it *is* one component. For any shared component with a
  feature-bearing optional prop, **enumerate every mount site and diff the props**;
  a feature that should be universal belongs **inside** the component (on wherever
  its data exists), not behind an opt-in a caller can forget. Review question:
  "does this concept render identically at *all* its mount sites?" — don't stop at
  "it's one component."
- **In a port or migration, unification is a precondition, not a cleanup pass.**
  Enumerate the shared concepts and adopt exactly one component per concept
  **before** porting screens — a duplicated concept is a defect a reviewer *will*
  find, and retrofitting unification while the owner watches is far slower and
  noisier than building it once up front.

## One component at two scopes — single-entity vs aggregate needs scope-aware copy

A shared component reused at **two scopes** — a single entity vs an all-entities
**aggregate/rollup** — but with labels and empty-states that **hardcode the
single-entity phrasing** ("the items *this* owner has", "nothing here for this owner
yet") reads wrong or misleading at the aggregate scope. Related forms: the aggregate
view **drops** a section the single-entity view shows, or lists an unbounded union of
rows with **no attribution** of which entity each row belongs to — so the rollup is
unreadable and the two scopes feel inconsistent.

- **Make copy and empty-states scope-aware** — interpolate the scope (the entity name
  at single scope, "all …" at aggregate), don't hardcode one.
- **At aggregate scope, label each row with its owning entity** and **cap/paginate**
  the union (the overflow state).
- **Keep the section set consistent across scopes** unless a per-scope variant is
  deliberate and stated — and at aggregate scope specifically, **hide a view whose
  number would be a *misleading aggregate*** (a rate or total that is meaningless
  across heterogeneous entities): computed-not-fabricated (principle 3) beats
  symmetry, exactly as in `migration-parity.md`'s misleading-aggregate exception.

A **different axis** from the neighbours: not the *prop* axis (#123 above — one
component, a feature prop present at one mount site and absent at another) and not the
*section-set superset* across **sibling per-entity** surfaces (`migration-parity.md`),
but the **single-vs-aggregate scope** of one component's copy and attribution.

## Interaction-completeness — the loop must close

A control is a defect until its whole loop works in the running product, not just
until it renders:

- **No write-only inputs.** Any surface where a user adds or edits data must let
  them **see, reach, and edit** what they added, in that same view (read-back). An
  input that posts to a store but never shows the value back is a defect, not a
  slice — the user cannot tell it worked, correct it, or undo it.
- **WYSIWYG, never raw markup shown to users.** Store markup; **display it
  formatted**. A rich-text field that shows `**bold**`, `<u>`, or `*` tokens while
  the user types has leaked its storage format into the UI — render what the text
  will look like once posted.
- **No dead controls, and disabled must look disabled.** A button/toggle/arrow
  rendered enabled whose handler is a no-op is a trust defect; a control that is
  unavailable must *look* unavailable, not merely be inert. Unit-logic tests
  passing is **not** a working UI — exercise the real control in the running app
  (cross-ref the live-verification rule below).
- **A disabled action explains its cause and its recovery path — not a dead end.**
  Looking disabled (gate 1's *disabled-looks-disabled*) and disabling the same way at
  every instance (the *interaction-consistency* bullet below) prove the control's
  appearance and its cross-instance parity; neither tells the user **why** it is
  unavailable or **what** unblocks it.
  A *contextually* unavailable action names the **unmet prerequisite and a concrete
  next step** — and because a native `disabled` element may receive **no hover or
  focus events**, that explanation cannot live in the control's own tooltip; put it
  in **nearby text or a focusable wrapper/popover** the user can actually reach. An
  action *permanently* unavailable to the current role is **hidden or replaced with
  an attainable alternative**, not left visibly dead — unless its discoverability is
  explicitly wanted (`frontend-a11y.md` owns the disabled-control *contrast*
  exemption; this owns the *recoverability*).
- **A control disabled only until client state resolves is *loading*, not disabled —
  render it as loading, never dead.** A write control (add, submit, compose) gated on
  client-only state — `useAuth` / `useSession`, a hydration flag — is server-rendered in
  its `disabled` default, then enabled once the client bundle resolves. For the seconds of
  that SSR → hydration window it looks like a permanent dead control (the *no-dead-controls*
  class above), but it is really in the **loading** data state (the five-states rule) and
  must *look* loading — a skeleton or spinner affordance — not a bare disabled button with no
  reason. This is a distinct class from the *contextually-unavailable* case just above: that
  control **stays** disabled and owes an explanation; this one **will** enable itself and owes
  a loading affordance. Optimistic-enabled (render it enabled, act on the click) is allowed
  **only** when the click is captured and replayed after hydration, so the handler is never a
  no-op — an enabled control whose pre-hydration click is dropped is the *dead control / no-op
  handler* trust defect above, not a fix. The static tell — `disabled={!session}` on a write
  action with no loading sibling — is an **`unverified` lead, not a finding**: only a
  **pre-hydration render** (a snapshot taken before the client bundle runs,
  `testing-and-evals.md`) confirms it, so where the harness cannot capture one the gate reports
  *could-not-check* and fails **open**.
- **A disclosure default derived from async-fetched data silently never fires
  (mount-capture).** An open/collapsed default read once at mount — `useState(open)`
  seeded from a prop or derived value the hook does **not** re-sync on later change —
  locks in whatever was available at first paint. When one input to that default is
  fetched **asynchronously** and lands *after* mount (a count, a flag, a permission),
  the default silently never applies: the pure decision function's unit test is green,
  the running UI never opens/collapses as intended. Drive the mount default from data
  available **synchronously** at first paint (when the deciding signal is async-only,
  default to the collapsed/closed state at mount — the badge affordance below assumes
  that polarity); surface a late-arriving signal through a **non-reflowing**
  affordance (a badge on the collapsed header), never by force-opening after the fetch
  (which reflows under the reader); keep the async signal in the decision function's
  *contract* so it is honoured when present at mount (a warm cache) and stays tested.
  Confirm it **live in the running product** (the live-verification rule above), not
  only the logic test — same client-state-timing family as the disabled-until-hydrated
  rule above.
- **Reviewable change history, and no silent AI edits.** Any surface where an
  edit is itself a decision of record (a value, a target, an assignment, an
  owner) needs a visible who/what/when history behind the current value, not a
  silent overwrite — the same defect class as a write-only input, one level up.
  A value an agent or model proposed or wrote on a person's behalf is stamped
  in that history as AI-recommended, with its source, **at write time** —
  never merged into the record indistinguishably from a human edit. An
  unstamped AI edit is a defect a reviewer cannot see, not a shortcut.
- **Interaction *consistency*, not just completeness — the same class reacts the
  same everywhere.** Completeness (above) asks "does this control work?";
  consistency asks "do all instances of this class react the same, and is every
  affordance reachable?" For each interactive class (button, row, card, chip, tab),
  its **hover / active / focus-visible reaction is identical at every instance** —
  divergent reactions for one class is a finding, and because the cause is usually
  per-instance style overrides on a *shared* component, it survives the *one
  component per concept* grep (that catches duplicate markup; this catches divergent
  state styling on the same component). **Every hover affordance has a non-hover
  path** — anything revealed only on hover is also reachable by keyboard focus and
  present (or behind an explicit control) on touch; a hover-only action is a defect,
  not a power feature. A **tooltip carries new information** (a value, a date anchor,
  a definition), never a repeat of the visible label. And a disabled instance looks
  disabled the **same way** everywhere — the across-instances form of
  *disabled-looks-disabled* above. (`frontend-a11y.md` owns that a focus ring
  *exists*; this owns **parity** of the reaction across the class.)

## Match a named standard; visual & number-format consistency

Before designing an element, recall how the best products solve it and **name the
standard applied**; reinventing a solved problem (legend, delta, table, date
picker, empty state) is a cost, not a feature. Then keep it consistent: one type
scale, one spacing rhythm, one component set, and consistent **number
formatting** — locale/thousands separators and **tabular figures in columns** so
digits align. The same mark/legend renders identically wherever it appears.
`frontend-a11y.md` owns **accessible-name** consistency across routes; this owns
**visual / number-format** consistency — the drift a per-route pass and a
name-only diff both miss. (Nielsen: consistency and standards.)

---

**🚩 grep**: a data-fetch / `useQuery` / `await` render path with no
`isLoading`/`isError`/empty branch, a `.map(` over a list with no length-0 case, a
table/grid with no `overflow`/pagination, a `catch` rendering `err.message`/stack
into the DOM (states) · a colour scale keyed on a field that also drives an
icon/shape, or `>1` semantic use of one `--color-*` token (encoding) · a
status/delta rendered by `color`/`background` with no sibling icon/text node, or a
colour-coded status dot with no `aria-label` (colour-alone) · a delta coloured
green-for-up / red-for-down unconditionally, an arrow/percentage with no
magnitude, or a "change" number with no period anchor (delta) · a paragraph of
instructional copy rendered inline on every load, or a legend built from text
descriptions of marks rather than the marks (self-evident) · a "drawer"/"detail"
that pushes a route change or unmounts the list, or an `onClick` that is a
no-op / `// TODO` (drawers / dead controls) · `>1` font-size/spacing value for one
role, or column numbers interpolated without `toLocaleString`/tabular figures
(consistency) · the same UI string, section heading, or markup block
duplicated across ≥2 component files, or a second hand-rolled copy of a
row/card/field a shared component already renders (one concept built more than
once) · a text input that
persists markup while rendering its raw `**`/`*`/`<u>` tokens back to the user
(not WYSIWYG) · an add/create/edit handler that writes to a store with no path
that reads the value back into the same view (write-only input) · an editable
record's write path with no history/log table behind it, or an
agent/model-authored value merged in with no field distinguishing it from a
human edit (change-history / silent AI edit) · a `confidence`/`score`/`priority`
rendered as a raw `{n}%` or float with no defined tier label beside it, or a model
confidence number published as precision (confidence tier) · an `<svg>`/chart with
no `<text>`/axis node and no hover/focus readout target, or a line/area drawn across
`<3` data points (data-viz) · a `position: sticky`/`fixed` element whose scroll
container has no padding (gutter), or an action revealed by `onMouseEnter`/`:hover`
with no focus/keyboard sibling (hover-only) — the footprint, reflow, and
per-class-parity defects are **render-only**, caught by the route sweep below, not a
grep.

## Rendered route sweep — apply domain P across every surface (FULL reviews)

The rules above are individually correct and still miss a whole class of defect,
because on a `FULL` (or broad-`DIFF`) review of a product UI **no step renders the
assembled product route-by-route**. The enforcing gate's screenshot is per-change
(the route a diff touched), so a defect spanning many routes is found the way an
owner finds it — scrolling the running app one screenshot at a time, after a green
gate and a clean code read. The sweep is the domain-P analogue of Phase 3's
anonymous-GET sweep (`method.md`): a cheap, systematic, whole-surface pass that
turns "we have the rules" into "we applied them everywhere."

1. **Enumerate every route** — from the router tree **and** the nav manifest (a
   route in one but not the other is itself a finding), including detail overlays
   and tabbed sub-views — **and every export path** (download / print /
   copy-as-image): each is a second render surface, ruled as its own surface
   (below), not across this route matrix.
2. **Render each across the matrix** — this is the matrix the layout-invariant
   checks (Enforcing gate, below) refer to: **{~390px, ~1440px} × {light, dark} ×
   {top, mid-scroll}**, plus any **state transition** a route has (loading→loaded,
   empty→populated, collapsed→expanded). Render the **running build at the intended
   base ref** — verify the checkout first; a stale tree renders the wrong product
   (render from a clean tree at the right ref — the receipt rule below).
3. **Rule the domain-P checklist on each route** — states, encoding, delta,
   **data-viz**, **density/footprint**, interaction **completeness and
   consistency**, and the **layout invariants** (all defined above / in the
   enforcing gate; this step *applies* those rules, it does not restate them) — and
   record a per-route line: `route · viewport · theme · state · what a user sees ·
   severity`.
4. **Report coverage as a ledger, not a verdict.** A route not rendered is
   `unverified`, never clean (the `COVERAGE_LEDGER` discipline, `method.md`); and a
   clean finding generalises **only** to the routes actually rendered, never past
   them (`migration-parity.md`, *Scope a parity claim to the correspondence table*).
   Group findings by root
   cause: a class spanning many routes is **one** systemic finding, not forty.

## Export / print / share is a second render surface

A **download / print / copy-as-image** feature emits the view through a *different*
code path than the screen — canvas/`toDataURL`, SVG serialisation, a `@media print`
stylesheet — so a green on-screen render says nothing about the artifact the user
actually walks away with. It silently **clips** content past the viewport, **drops**
axis/legend/labels that lived only in interactive chrome, ignores the current
**theme**, or exports an empty/partial view as a blank image. Treat each export path
as a review surface in domain P (the sweep above already enumerates them):

- **Find the export paths** — grep `toDataURL`/canvas capture, SVG
  serialisation, `@media print`, and `download`/`export`/`copy image` handlers.
- **Produce the artifact and inspect it like a route** — no clip of content that
  extended past the viewport; **axis / scale / legend / labels baked in** (an
  interactive-only readout — the hover value+date the *Data visualization* rule
  above requires — needs a *static* equivalent in the export); **theme** honored or
  explicitly normalised; and enough **title / as-of / context** that the artifact is
  self-describing out of its app.
- **Every data state exports honestly** — an empty or partial view exports with its
  honest label, never a blank canvas (*Every data state*, applied to the export).
- **Mechanise where you can** — snapshot the exported artifact's dimensions and the
  presence of its key elements (axis text, legend), held to the same
  could-not-check-vs-found-nothing discipline as the enforcing gate's heuristics.

This is a *different* axis from reproducing an audit finding against the production
build (`method.md` verifies *which build the reviewer reads*; this inspects an
artifact the *product emits*), and it is where the data-viz checklist above is most
often lost — the on-screen chart carries axes and a readout the serialiser drops.

## Pre-ship checklist (mirror SKILL.md's report discipline)
- [ ] Does it need explaining? If yes, redesign until it doesn't (or demote the text to progressive disclosure).
- [ ] All five data states handled and honest — empty / loading / error / partial / overflow — and an empty state names its **coverage** (no-data-collected vs collected-and-genuinely-none), never implying a false all-clear?
- [ ] One channel per dimension; nothing colour-only; reads correctly in greyscale?
- [ ] Deltas are caret + magnitude, coloured by sentiment; flat is a muted `—` with a period anchor?
- [ ] Confidence / score / priority shown as a **defined labeled tier** (text + a colourblind-safe cue), not a raw `%` or point score, and no model-authored number published as precision?
- [ ] Does each primary information unit answer **why it matters** (a derived / structural signal — count, recency-delta, graph-degree — **never a fabricated importance score**), not just what happened; where an action is possible, is a concrete **next step** named; and is the **most decision-ready surface in the first paint and stable** (not a post-hydration `aria-hidden` island, not below fixed non-interactive chrome)?
- [ ] Does the **default ordering serve the user's job** (not reverse-chron by default on a decision surface), and is **each exposed sort/rank mode self-explaining ("orders by …") and measurably distinct** (near-identical modes collapsed; an opaque / near-constant sort key is false precision — measure its distribution first)?
- [ ] Matches a **named** top-product pattern; convention gaps surfaced to the owner, not silently redesigned?
- [ ] If the owner has rejected this element **twice**, stopped tuning — structural flaw named, two or three comparables researched, concrete options surfaced for the owner to choose?
- [ ] Consistent type scale / spacing / components / number format with sibling views (tabular figures in columns)?
- [ ] One shared component per concept — reused/extended, not reimplemented per page; a fix landed in the shared component, not one caller; **searched the tree for a duplicate twin (a duplicated visible string/heading) a diff-scoped review would miss**?
- [ ] Interaction loops close — read-back on every input (no write-only), WYSIWYG not raw markup, no dead controls — checked on the route that actually renders?
- [ ] Any action **labelled non-destructive** (resolve / archive / dismiss) that removes the record still shows it **persists** — a persisted-state label, an undo, or a discoverable resolved/archived view — so it doesn't read as a hard delete? (Default-hiding behind a *known* filter is a convention, not this; soft-delete is out of scope; **fail-open** — a human adjudicates.)
- [ ] Every **disabled action explains its cause and a recovery path** — the unmet prerequisite + a concrete next step, in **reachable** text (nearby or a focusable wrapper/popover, not a tooltip on the disabled element, which may get no hover/focus); an action permanently unavailable to the current role is hidden or replaced, not a dead end?
- [ ] **No write control renders as a dead/disabled default during the SSR → hydration window** — a control gated on client-only state (auth/session) shows a loading affordance (skeleton/spinner) or is optimistically enabled with its click **replayed** after hydration (never a dropped no-op), not a bare disabled button; confirmed on a **pre-hydration** snapshot, and *could-not-check* (no pre-hydration capture) fails **open**, not a silent pass?
- [ ] Drawers overlay (don't navigate away); collapse scope correct; no dead controls?
- [ ] Verified live in the running product, in more than the happy-path state — **including the default state a user lands on** (signed-out / no-role / default route / local default), not only a mock or a hand-picked persona view?
- [ ] Any "matches / exact / parity" claim checked against the **default served state of the tree under review** as the canonical surface (not whichever tree happens to hold the port — name url · branch · sha, `report-format.md`) — and if it rests on a non-default surface, does it **name** that surface and say the default was not checked?
- [ ] "Looks the same" backed by a **rendered-appearance** diff of the default state vs the reference (screenshot / computed styles), **not** section-presence, DOM order, a passing test, or loaded data — and stating **which axis** (structure / styling / content / data) the evidence covers, without "fixing" data to answer a styling complaint?
- [ ] Parity task: differences classified **structural vs cosmetic** (structural parity first; a structural divergence **never** called "close / 1:1"); every "matches" claim gated on a **mechanical differ** (diff image + structured mismatch list attached, not an assertion); reference read at its **highest fidelity** (running build > source > screenshot); **no mock sample value copied** into the product; and the differ run **both ways** (design→app and app→design), both lists **resolved** (design→app empty; each app→design entry restyled into the target language, decoration removed, or owner-adjudicated — an app-only element is a finding to resolve, never a silent bonus)?
- [ ] Parity **delta** established by rendering **both sides at the same viewport width** (a one-sided crop is a hypothesis, never the evidence), and each app-only / design-only element's **state confirmed on the other side** (present-but-collapsed / disabled-by-data / in-a-menu) before it is called a delta?
- [ ] Did **not reconfigure the default** (persona / seed / flag / env) and then claim "verified on the default" — checked the pre-existing default and disclosed any change to it?
- [ ] Every styling / placement delta enumerated in **one** side-by-side pass and fixed against that inventory — not piecemeal-fix-then-redeclare-done?
- [ ] Told "not the same" → **asked which axis** before acting (after one wrong guess, asked not guessed), and compared the **reference itself** at the element × breakpoint × theme, not from memory?
- [ ] Parity target expressed in **measured device-pixels at the actual render scale** (not user-space units — equal user-units ≠ equal pixels), and same-axis oscillation treated as a **duplicate-implementation-at-different-scale** signal (measure the ratio, don't tune)?
- [ ] No status is green-with-a-caveat — a status the author can immediately qualify is **downgraded**, not asserted beside a hedge (`report-format.md`)?
- [ ] UI change: headed-browser receipt on the exact route after the action (screenshot or equivalent) — and the receipt is a **valid non-empty image**, not a proxy/504-wiped stub that passes a bare existence check (existence is not content — `SKILL.md` principle 2), captured from a **clean or separate tree** (a shots script that stashes uncommitted changes discards the very diff under review), and the image **shows the target feature**, not an error / login / empty-state wall (a login page is itself a valid non-empty image — confirm the feature is present, and capture in a dev/identity-bypass mode not a route-auth-walling production build, `testing-and-evals.md`)? Unit tests alone are not this box.
- [ ] **Layout invariants hold across the sweep's matrix** — no content under sticky chrome, gutters present, optional slots reserve space, no reflow on a state change, tabular numerals in columns — checked **mid-scroll and on state transitions**, both themes, not only at the top of a fresh desktop render; and **footprint tracks information** (no empty record at a populated card's size; grid dense enough at the wide viewport)?
- [ ] **Charts are legible** — a value axis or direct labels, a **keyboard-reachable** hover/focus readout of value + its date/category, real samples marked and no trend implied across sparse points — and **interaction states are consistent per component class** (hover/active/focus parity across instances; every hover affordance also reachable by keyboard and touch; tooltips add information, not a repeat of the label)?
- [ ] **Every export / print / share path inspected as its own surface** — the downloaded artifact doesn't clip off-viewport content, bakes in the axis/legend/labels that live only in interactive chrome, honors or normalizes the theme, is self-describing (title / as-of), and exports each data state honestly (never a blank canvas)?

## Parity claims: the default state is the canonical surface

A "matches / exact / parity with `<reference>`" claim is only as good as the
**surface** it was checked against. The canonical surface is the **default state
a user lands on** — signed-out / no-role / no-persona / default route / local
default — because it is the state a user is served **by default**, before any role
or persona is chosen: the entry state every user passes through. A mock, or a
hand-selected persona/role view, is a **secondary** surface: a parity claim
resting only on it verifies the wrong state (a first-time user never sees it). "More than the
happy-path state" (checklist above) is necessary but not sufficient — the
**default state must be among the states checked**, and a claim that rests on a
non-default surface must **name that surface** and say the default was not
verified.

The general rule that a status is **downgraded the moment it carries a caveat**
(and names the surface its evidence came from) is defined once in
`report-format.md` and applies to a parity claim unchanged — the UI-specific case
is that a parity ✅ resting on a **non-default surface** is not green.

## "Looks the same" is about rendered appearance — four axes, and a structural check is not a visual one

"Make X look like reference Y" is a task that frequently earns a false ✅. These
rules sit **on top of** the default-state rule above (never restating it); each is
a distinct fidelity rule, or names an evasion that passes a default-state check yet
still ships a UI that does not look like Y.

**Read the reference at its highest available fidelity — this is the *reference*
side, not your output's.** The reference exists in three forms; prefer the highest
present: a **running build** you launch and diff against > the design **source**
(HTML/CSS, which states the column model, tokens, and spacing exactly) you read
property-by-property > a **screenshot** (a lossy picture — last-resort sanity check
only). Never reverse-engineer the source when a running build of the design
already exists in the repo, and never eyeball a picture when the source or build
states the spec precisely. **A stale source *comment* ranks below even the
screenshot** — a code comment claiming an element "moved" in some past design
revision is not the current design; when a comment and the live rendered reference
disagree, the **current render wins** — verify against it, not the comment. This
governs how you read **Y**; it does not soften the
rule below that *your implementation's* evidence must be the **render**, not the
DOM — opposite sides of the comparison.

**Four axes — name which one a claim covers; never conflate them.** A UI compares
on four independent axes:
- **structure** — which sections / components / chrome / affordances are
  **present** (vs absent), in what order, grouping, nesting / DOM;
- **styling** — the rendered *look* of what is present: font size / weight,
  colour, spacing, radius, shadow; each affordance's **glyph** (a star, a caret, a
  control); overall layout dimensions;
- **content** — the words / copy;
- **data** — the numbers / rows / entities.

A "looks the same" task is almost always **structure + styling**, with content and
data allowed to differ. "Same sections in the same order" is a **structure** claim —
it is **not** evidence of styling parity and must never be reported as "matches" /
"looks the same." And do not "fix" the **data** (swap a persona, seed rows) to
answer a **styling** complaint: that changes an axis the user did not raise and
leaves the one they did.

**Classify every diff structural vs cosmetic — and get structural parity first.**
Structural = different components, a different grouping / column / tab model, a
different page composition — the **structure** axis above (presence, grouping,
composition); cosmetic = colour, radius, spacing, glyph — the **styling** axis.
(Same two axes, renamed for the parity decision: presence/composition is
structural; the rendered look of what is present is cosmetic.) Establish
structural parity first (same components, same grouping, same composition), then
pursue cosmetic. **Never characterise a structural divergence as "close", "mostly
there", or "1:1"** 🚩: a board whose columns are `[Unclassified, Manual, Planned,
In progress]` when the design's are `[Up next, In progress, In review, Live]`, or a
flat filtered list where the design groups by team, is not "nearly there" — it is a
**different screen**, a rebuild, and calling it close is a category error that
destroys stakeholder trust. If the structure differs, say so plainly and size it as
a rebuild, not a tweak.

**A structural / proxy check is not visual evidence.** A section-presence check, an
"element-by-element" DOM / heading diff, a passing test, or loaded data are all
**proxies** for rendered appearance, not the appearance itself (`report-format.md`,
the proxy trap — *structure / DOM order / section-presence* is its UI instance). To
claim rendered parity, diff the **rendered appearance of the default state** against
Y: a screenshot and/or **computed styles** — the styling-axis properties above,
side by side. Anything less names its proxy and says the render was not checked.
Beware the specific dodge **"I diffed the *rendered* structure"**: "rendered
structure" is still the **structure** axis — it proves the sections rendered, in
order, not that they *look* like Y. Opening the page confirms structure rendered;
rendered **appearance** is the styling properties, and only a styling diff shows it.

**Do not move the goalpost you measure against.** If the work changed the
configuration that *defines* the default surface — the env default, a seed, a
feature flag, the demo persona, a local default — that change is itself part of the
artifact under review. Disclose it, and check parity against the **pre-existing**
default, not the one you just authored. "Verified on the default state" *after*
reconfiguring what "default" means is a claim about a surface you wrote, not the one
the user is served (general form: `report-format.md`, a self-reconfigured surface is
a proxy).

**Enumerate every diff in one pass before fixing any.** Finding diffs one at a time —
fix, re-declare "done," the user finds the next — is the loop that burns trust and
manufactures the repeated false ✅. Start with the single fastest discriminator: a
**gross-dimension diff** — the total height / width of the compared surface. A large
delta (one surface markedly taller or wider than Y) is by itself evidence styling
parity does **not** hold, before any element-level work. Then do a **full
side-by-side of the whole surface**, list every styling / placement delta at once,
and fix against that inventory; the parity claim is made only when every row is
closed or owner-accepted.

**Told "not the same" → disambiguate the axis before acting.** One question — "the
layout / structure, the styling (fonts / spacing / colour / chrome), the copy, or the
data?" — costs one turn; guessing wrong costs many. After **one** wrong guess, **ask,
do not guess again** (the multi-hour chase is: guess the data is sparse → guess a
contrast number → guess the persona → the user finally says "styling").

**The reference is the source of truth for styling, not your memory of it.** Re-open
Y and compare the **specific element, at the specific breakpoint, in the specific
theme** — styling differs by all three; a remembered impression of Y is not a
comparison.

**Match by measured device-pixels, not user-space units — equal user-units ≠ equal
pixels.** When two renderers apply different transforms or zoom (a thumbnail beside a
full view; an SVG drawn at ~1.4× device scale beside one that fills its container at
~9.6×), identical user-space values — stroke widths, font sizes, gaps — render at
wildly different pixel sizes, so tuning one to match at a single zoom breaks it at
another. Express a parity target as **measured device-pixels at the actual render
scale**, compute the **scale ratio** between the two renderers, and derive the second
implementation's values from the first × that ratio (or unify to one component).
Persistent **oscillation of one property on the same axis** — too thick → too thin →
too thick, each "fix" trading one mismatch for another — is the tell that the same
visual concept is implemented **twice at different scales**, not that the parameter is
wrong: stop tuning and measure (the stop-tuning discipline is *Repeated owner
rejection* above). And validate the **measurement target itself** — measure the
visible ink, not a transparent overlay or focus-indicator path a DOM query happens to
return first.

## Enforcing gate (Phase 6 imprint)

A standard with no gate is advisory (SKILL.md Phase 6: *pair each imprinted
standard with the gate that enforces it*). When imprinting into a project that
ships a UI, pair this reference with a UX-evidence gate — held to the skill's own
gate discipline: **a gate must tell "could not check" from "found a problem,"
fail *open* on the former, and never be stricter than the standard**
(`frontend-a11y.md`, the `innerText` and disabled-contrast traps; SKILL.md
Phase 1, gate-vs-standard). Three gates for any UI change, in descending
confidence of what they can prove — plus a fourth that fires only on a parity
task:

1. **Screens-changed evidence — the artifact, plus the inspection it demands.** On
   any diff that can change a rendered page, require a screenshot of each affected
   route at a narrow and a wide width (e.g. 390 / 1440), or an explicit `No UX
   change: <reason>` line. A screenshot proves a human/agent *looked*; it does
   **not** prove the render is correct — and "screenshot attached" **with no cited
   inspection** is `unverified`, not `verified` (the treatment a parity claim with no
   named surface gets, #192). The defects that survive every other gate are the ones
   only a look at the image catches, so a UI status **names what it inspected** from
   this checklist (defined once here; a status cites the items):
   - **overlap** — no two text / interactive elements intersect (mechanical proof:
     the bounding-box non-intersection assertion, `testing-and-evals.md`);
   - **clip / truncation** — no unintended ellipsis or cut glyph at the narrow width
     (`scrollWidth > clientWidth`, same file);
   - **contrast** — text meets AA against its *painted* background
     (`frontend-a11y.md`);
   - **disabled-looks-disabled** — a functionally disabled control is *visibly*
     disabled (cursor / opacity / painted colour, not only the attribute; the
     *no-dead-controls* interaction-completeness rule above, seen in the render);
   - **not-dead-before-hydration** — a write control gated on client-only state shows a
     loading affordance (or is optimistic-enabled with a **replayed** click), not a bare
     disabled default, in the **pre-hydration** render; the static `disabled={!session}` tell
     is an `unverified` lead until that snapshot confirms it (principle 2), so a harness that
     cannot capture pre-hydration reports *could-not-check*, never a pass;
   - **state named** — which data state the shot is of (empty / loading / error /
     populated), so an absence reads honestly (gate 2's state coverage; the
     empty≠all-clear rule above);
   - **sticky-chrome collision** — nothing content-bearing paints under a
     sticky/fixed header or bar; visible only mid-scroll, so it is checked at scroll
     offsets, not only at the top of a fresh render;
   - **gutters present** — every scroll container and sticky bar has padding, so
     content is not flush to the edge or to the chrome;
   - **optional slots reserve space** — a row's rail and baseline hold whether or
     not an optional element (avatar, badge, trend) renders; check the absent-slot
     variant, so a row doesn't go ragged when a slot collapses;
   - **no reflow on a state change** — a control keeps its box across
     loading→loaded and collapsed→expanded (a before/after box compare — the same
     geometry primitive as *overlap* above), checked on the transition, not only at
     rest;
   - **tabular numerals** wherever numbers stack in a column, so values don't jitter
     the alignment as they update (the tabular-figures rule of *Match a named
     standard* above, here as a mid-update stability invariant).

   Of these, **sticky-chrome collision reads only mid-scroll**, and **reflow (and
   numeral jitter) only across a state change / value update** — a single top-of-page
   shot cannot see them, so on a `FULL` review they are ruled across the **rendered
   route sweep**'s matrix (above). **Gutters and optional-slot reservation read at
   rest** (the latter in the absent-slot data variant) — check them on the per-change
   shot too, and re-confirm in the sweep rather than defer to it. And
   **not-dead-before-hydration reads only before the client bundle runs** — a fourth timing
   class neither the at-rest shot nor the mid-scroll sweep can see, because both capture the
   *post-hydration* render; it needs a snapshot taken inside the SSR → hydration window (a
   pre-hydration or CPU-throttled capture, `testing-and-evals.md`), and where the harness
   cannot take one the item is *could-not-check*, not clean.

   A screenshot with an unstated inspection is an artifact read as the verification
   it is not.
2. **State-coverage in tests (proves the branches exist).** A component test that
   renders a data view asserts the **empty and error** branches, not only the
   populated one — extends `testing-and-evals.md`'s "test the failure, not just
   the feature" to UI states.
3. **Encoding self-test (heuristic — scopes its own claim).** Where a design
   system exists, a lint/unit check that no single colour token is bound to two
   semantic names, and that every status/delta element carries a non-colour
   channel (icon/text + `aria-label`). Both are **heuristic**: a static
   "one token, one meaning" check cannot see runtime binding, and "has a
   non-colour sibling" false-positives on decorative nodes — so it **warns and
   lists**, never fails closed, and reports what it could not resolve as
   `unverified`, not as clean. Model: a renderer-tolerant ratchet — a pinned
   exception is *allowed*, never *required* to exhibit. Same gate, same discipline,
   for **chart anatomy** (data-viz above): a heuristic assertion that an
   `<svg>`/canvas chart exposes **axis tick text or a hover/focus readout target**
   and that a series is not colour-only — it **warns and lists**, never fails
   closed, because it false-positives on a legitimately decorative chart (the
   `aria-hidden` + printed-number exemption above), and whether the readout returns
   the *right* value stays a human inspection.

4. **Parity differ (parity tasks only — proves *equivalence*, not just that a human
   looked).** For a "make X match reference Y" task, build a mechanical differ
   **before** any pixel-matching and gate every "matches" claim on it. The differ
   drives both the reference and the target for each screen and emits (a) a
   side-by-side + pixel-diff **image** and (b) a **structured** mismatch list — which
   nav / tab labels are present or absent on each side, the header strings, and
   bounding-box geometry deltas for key elements. **The artifact shown to a reviewer
   is the diff image, never a sentence.** **Render both sides at the same viewport
   width** and diff the corresponding region — a cropped or scaled screenshot of
   **one** side is a **hypothesis, not evidence**; never infer a present/absent delta
   from one side alone. Before recording an element as app-only or design-only,
   **confirm its state on the other side**: present-but-collapsed,
   present-but-**disabled-by-data** (a stepper bound to one item has nothing to step
   to), or present-in-a-menu — "absent in this crop" is not "absent in the design".
   This is the evidence that feeds the classification (`migration-parity.md`,
   *restyle-an-app-only-feature*): a delta that does not exist has no bucket, and every
   wrong inference here is one destructive edit — a removed control, a duplicated
   element — away. **🚩** a "missing" / "extra" parity call whose only evidence is a
   one-sided crop, or made with the other side's state unchecked. Load a no-routing
   prototype **once and
   click-navigate** its in-page tabs (it has no per-screen URL to fetch), and diff
   against an existing **running build** of the design if one is in the repo rather
   than reverse-engineering its source (reference-fidelity order, "Looks the same"
   above). It diffs **chrome / structure / styling, not text values** — diffing the
   numbers would flag real data as a mismatch and tempt the fix that fabricates
   (`migration-parity.md`). What it **cannot** prove: an intentional improvement from
   a regression, and its pixel threshold is **agreed, not derived** — a human still
   owns the ship call. **Parity is *set equality*, not containment — run the
   present-or-absent list above in *both* directions.** Produce it per screen as
   **design → app** (what the design has that the app lacks) *and* **app → design**
   (what the app renders that the design does not); an element on exactly one side is
   a finding **regardless of which side**, and the app→design half is the one that
   gets skipped. The **operative test** for an app-only element — *does removing it
   lose a user capability?* If **no**, it is pure **decoration** (an extra header, a
   "Showing N of N" line, a duplicated label): default **remove-to-match**, and
   "intentional extra" is the rationalisation that ships the mismatch. If **yes** (a
   per-card upvote, a filter bar, a view tab, a deep-link button — removing it removes
   upvoting, filtering, navigating), it is a **feature**: the default is **not**
   escalate-and-wait but **restyle it into the target's design language**. Deleting it
   to match the mock is a **High** do-no-harm finding, never self-certified.
   `migration-parity.md`'s *restyle-an-app-only-feature* rule governs the
   classification (and the re-express-in-the-target's-own-primitives mechanics), its
   severity, and the exception ledger; escalation to the owner is the **fallback** when
   no target primitive fits, not the whole answer.
   Scope all of this to **chrome / features**; **data** (values, counts, series)
   legitimately differs (`migration-parity.md`). *Done* on a parity task = the
   design→app list is empty; the app→design list is empty **or every entry is
   resolved** — restyled into the target's design language, decoration removed, or an
   owner-adjudicated keep/removal (a bare app→design list is not an automatic differ
   fail — the differ can't tell an intentional improvement from a regression, so that
   half routes to classification and, where needed, human adjudication); and the
   pixel delta is under the agreed threshold for every screen in the correspondence
   table, with those diff images attached — never an assertion.

Ship these **idempotent and additive**, per Phase 6 — detect-and-stop if
present, add only what is missing, defer to an existing style guide (the parity
differ only when the task is a parity task).
