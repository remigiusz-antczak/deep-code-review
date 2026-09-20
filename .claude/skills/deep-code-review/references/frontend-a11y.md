# Frontend, UI/UX & accessibility review

Read this when the target renders UI (web, mobile web, component library, or a
server-rendered view). Expands section P of `SKILL.md` — the **a11y-correctness
half**; `product-ux-quality.md` is the companion **design half** (whether the UI
feels *at-home*: data states, encoding, the metric delta, self-evidence). Target
**WCAG 2.2 level AA** (W3C Recommendation, 2024-12-12); note AAA items where a
flow is high-stakes.

---

## Respect the existing design (read first)

Accessibility and usability findings improve the product — they must not
silently redesign it. Two rules:

1. **Separate defects from redesigns.** A contrast failure, a missing label, a
   keyboard trap, or an unlabeled icon button is a **defect** — fix it in place,
   minimally, preserving the existing look. A change that alters layout,
   spacing system, component structure, typography scale, or brand is a
   **redesign** — that is an owner decision, not a review fix.
2. **Prompt before heavy design change.** If the smallest correct
   accessibility/usability fix would visibly and substantially change the
   existing design, do **not** impose it. Surface it under "Decisions needed
   (owner)" and ask: is there a design system / style guide the fix should
   conform to, or is the current UI a prototype that can be freely improved?
   Proceed only on the answer. Offer the minimal-visual-impact option first.

This keeps the review net-positive on every axis — it raises accessibility
without regressing a deliberate design.

---

## Accessibility — WCAG 2.2 AA, how to check

**Structure & semantics**
- Native semantic elements (`<button>`, `<a href>`, `<nav>`, `<main>`,
  `<h1..h6>` in order, `<label>`, `<table>` with headers) before ARIA. ARIA
  only to fill gaps; a wrong `role` is worse than none. First rule of ARIA: use
  a native element if one exists.
- **A custom control built on a *non-labelable* element is not named by a wrapping
  `<label>` — name it explicitly and verify the computed name.** HTML `<label>` only names
  **labelable** elements (`<input>`, `<button>`, `<select>`, `<textarea>`, `<meter>`,
  `<output>`, `<progress>`, and form-associated custom elements). A widget built on a **`<div>` or `<span>`** given an ARIA role
  (`<div role="checkbox">`, `<span role="button">`) is **not** in that set, so a wrapping (or
  adjacent) `<label>`'s text is **not** taken as its accessible name — and if the element has
  no text of its own (its visible content is an `aria-hidden` glyph), it announces with **no
  name** ("checkbox, not checked" instead of "Accept terms, checkbox, not checked"). The JSX
  can look plausibly labeled, so a shape-based review misses it. (Adding a `role` to a
  *labelable* element — `<button role="switch">`, `<input type="checkbox" role="switch">` — does
  **not** lose the label; the WAI-ARIA APG recommends exactly that as the robust switch. The
  fault is the non-labelable **host element**, not the role override.) Fix: name the control
  explicitly with `aria-labelledby` (referencing the visible label's id) or `aria-label`, and
  **verify the platform-computed accessible name** in the accessibility tree (devtools / axe),
  not the DOM — the same computed-name harvest the cross-view-consistency check below performs.
- **An `aria-label` rewritten to add context must still contain the visible text it
  labels (WCAG 2.5.3 Label in Name, Level A).** SC 2.5.3 requires that "for user
  interface components with labels that include text or images of text, the name
  contains the text that is presented visually" — so a button showing "Export SVG"
  given `aria-label="Export the report as a PDF file (summary only)"` fails the SC
  the instant the rewrite drops the original words, even though the new label is
  *more* descriptive, not less. The break is invisible to a normal screen-reader
  smoke test (some reasonable name is still announced) and invisible visually (the
  short visible text on screen is unchanged) — it only surfaces for speech-input/
  voice-control users, who match a spoken command ("click Export SVG") against the
  accessible name and get no match once the visible words are gone, exactly the
  population a manual pass tends to skip. Detection (source-only): for every
  interactive element with both visible text content and a static `aria-label`,
  check case-insensitively whether the visible text appears as a contiguous
  substring of the `aria-label`; flag any label whose *opening* words differ from
  the visible text, since the usual break is the visible text surviving only as a
  caveat embedded mid-sentence rather than the label's opening words. Fix: default
  to no `aria-label` when the visible text is already a reasonable name, putting
  extra context in a `title`/tooltip or adjacent sr-only text instead; where one is
  genuinely needed, lead with the visible text verbatim and append the extra
  context after it (`"<visible text> — <extra context>"`) — the SC's own note
  gives the same best practice, that the label's text belongs at the start of the
  name. Distinct from the accessible-name-*sourcing* bullet above (whether a name
  exists, and from where) and from Consistent Identification below (whether the
  same destination gets the same name across routes): this is whether a name that
  already exists still contains what is on screen.
- One `<h1>` per page/view; headings describe structure, not styling.
- Landmarks present; a skip-to-content link for keyboard users.
- **An unnamed `<section>` is not a poorly-labeled landmark — it is not a landmark at
  all.** By the HTML/ARIA host-language mapping, `<section>` exposes to assistive tech
  as the ARIA `region` landmark only when it carries an accessible name (`aria-label`,
  `aria-labelledby`, or, as a fallback, `title`); with none, it maps to no landmark role
  and is absent from landmark/rotor navigation — a screen-reader user scanning by region
  skips straight past it. The bug hides well: sibling sections built from the same
  component (one instance passed a name prop, another not) render identically, so
  nothing on screen reveals the gap. Detection: pull the page's landmark/rotor list, not
  the DOM, and confirm every `<section>` you expect as a region actually appears in it.
- **A loading/skeleton region that visually swaps state needs a live region
  announcing the transition, not only `aria-busy`.** `aria-busy="true"` marks an
  element as *being updated* — a state property assistive tech can query, not an
  announcement it makes unprompted — and a plain `aria-label` on that same element
  is only exposed as its accessible NAME (spoken if the element is focused, or is
  itself an auto-announced role), never spoken proactively on mount. A shared
  loading/spinner component that sets `aria-busy` and `aria-label="Loading
  things…"`, with no `role="status"`, `role="alert"`, or `aria-live` anywhere on
  it or an ancestor, looks finished — the JSX carries a sensible-sounding label —
  but leaves the entire loading window, and the swap to the loaded result,
  completely silent for screen-reader users. This is squarely what WCAG defines
  as a **status message** — content providing information on "the waiting
  state of an application" or "the progress of a process" — and SC **4.1.3
  Status Messages** (AA) requires that "status messages can be programmatically
  determined through role or properties such that they can be presented to the
  user by assistive technologies without receiving focus," which neither
  `aria-busy` nor a plain `aria-label` satisfies. Fix: add `role="status"` to
  the region — it
  carries an implicit `aria-live="polite"` and `aria-atomic="true"` (MDN), so no
  separate `aria-live` attribute is needed — so the label is announced on mount
  and again when the wrapped content changes; keep `aria-busy` alongside it to
  suppress reads of partially-updated content, never as a replacement for the
  role. Detection is source-only: find shared loading/spinner/skeleton
  components and confirm whether `aria-busy`/a label prop is paired with
  `role="status"`/`role="alert"`/`aria-live` on the same or an ancestor element —
  and check the codebase's own error-state sibling, if one exists, which often
  correctly reaches for `role="alert"` right next to a loading state that
  doesn't; that asymmetry is itself the tell. Regression test: render the
  component and assert `getByRole('status')` (or the role used) resolves and
  contains the expected text, not only a DOM snapshot. Cross-ref
  `product-ux-quality.md` for whether the skeleton/spinner *design* is right —
  this is only the announcement half.
- **An async action's *outcome* that unmounts the focused control needs a live region AND explicit
  focus continuity — two failures, not one.** Distinct from the loading-announce bullet above (an
  *ongoing wait*): here the action has *resolved*, and the success/error message replaces the very
  control that was clicked and still holds focus — rendered as a plain text node with no
  `role="status"`/`role="alert"`/`aria-live`. Two compounding defects: the outcome is never
  announced (a plain element is not a live region), **and** because the focused element was removed
  from the DOM rather than disabled/relabelled, keyboard focus silently falls back to `<body>`
  (focus must be managed on async content insertion — the Keyboard & focus rules below — not left to
  fall to `<body>`), so a keyboard user loses their
  place with no signal the action finished. A sighted mouse user sees the message appear, so it
  ships. Fix: give the success message `role="status"` (polite) and the error `role="alert"`
  (assertive); and **prefer keeping the original control mounted** — disabled and relabelled with
  the outcome — over replacing it; if it must be replaced, move focus explicitly to the replacement
  (`ref.current?.focus()`). Test both halves: `getByRole('status'|'alert')` resolves with the
  outcome text, **and** `document.activeElement !== document.body` afterward.

**Keyboard & focus** (WCAG 2.1.1, 2.4.3, 2.4.7, and 2.2's 2.4.11)
- Everything actionable is reachable and operable by keyboard alone; logical tab
  order; no keyboard trap.
- **A custom interactive widget is built to its ARIA Authoring Practices (APG) pattern.**
  Each widget class (dialog, tablist, combobox, listbox, menu, disclosure, slider, tree) has
  a prescribed role + states/properties + a **full keyboard map** — e.g. dialog: `Esc` +
  focus trap; tablist: `Arrow` / `Home` / `End`, with only the active tab in the tab order
(roving tabindex); combobox: `Arrow` + `Enter` + `Esc`. "Tab
  reaches it" is not "operable": the finding is a **custom widget missing its pattern's keys
  or states** (a `role="tablist"` with no arrow-key navigation, a `role="dialog"` with no
  `Esc`, a control with no `aria-expanded`/`aria-selected` reflecting its state). Prefer a
  native element first (rule above); reach for the APG only when you build the widget yourself.
- **A disclosure toggle that swaps its `aria-label` text or icon between
  "Expand"/"Collapse" still needs `aria-expanded` on the same control — the label
  communicates what will happen, not the current state.** The APG-conformance
  point above already names a missing `aria-expanded`/`aria-selected` as an
  example of a widget shipped without its pattern's states; this is the single
  most common concrete shape it takes. A hand-rolled expand/collapse row (tree
  row, accordion header, filter section) commonly swaps its icon
  (`name={open ? 'chevron-down' : 'chevron-right'}`) and its `aria-label` text
  (`(open ? 'Collapse' : 'Expand') + title`) on click and stops there — a screen
  reader landing fresh on the button hears a sensible "Expand" or "Collapse," so
  a first-read smoke test and a sighted click-through both look correct. But that
  swapped text is the accessible NAME, not the `aria-expanded` STATE the ARIA
  disclosure pattern requires on the same control: assistive tech that reports
  state changes rather than re-announcing the full name on every interaction
  never gets one, and neither does any tooling that asserts on state directly
  (axe, Testing Library's `getByRole(..., {expanded})`), which will not recognize
  the row as a disclosure widget at all. Per MDN, `aria-expanded` "is applied to
  th[e] focusable, interactive control that toggles the visibility of the
  object," normally paired with `aria-controls` naming which element it toggles —
  both belong on the same button whose label/icon already swap. Detection: grep
  the icon/label-swap tell above, then check whether the same button also
  carries `aria-expanded={open}`; on a codebase with several tree/list/accordion
  rows, diff them against each other — most carrying `aria-expanded` and one not
  is strong evidence of an overlooked component, not a deliberate omission, and
  worth flagging as a reuse smell alongside the correctness bug (a single shared
  `<DisclosureButton>` primitive makes the gap structurally impossible to
  reintroduce). Regression test: assert `aria-expanded` flips per click via
  `getByRole('button', {expanded: false|true})`, not only that the content
  becomes visible in the DOM.
- Visible focus indicator; focus is **not obscured** by sticky headers/toolbars
  (2.2 new: Focus Not Obscured).
- **A focus indicator must clear the contrast floor, not merely *change*.** "Visible" is a
  numeric bar: the indicator's colour must reach **>=3:1** against what it sits on — WCAG **1.4.11
  Non-text Contrast** (AA) requires 3:1 for "visual information required to identify user interface
  components and states," and **2.4.13 Focus Appearance** (AAA) requires **both** that the indicator's **area** be at
  least that of a **2 CSS px thick perimeter** of the **unfocused** component (or sub-component) **and** a **>=3:1** contrast
  "between the same pixels in the focused and unfocused states" — a thin 1px ring that clears
  the contrast floor still fails the area prong. An automated focus check that
  captures computed style, calls `.focus()`, and flags only when *nothing changed* validates the
  **wrong property** — a change from transparent to a real-but-too-faint colour is a passing diff and
  a failing product. Resolve the **actual rendered colours** on both sides and compute the ratio (the
  way a text-contrast check does) — except an **unmodified user-agent-default** focus style, which
  1.4.11 **exempts** from the floor (2.4.7 still requires it *visible*); scope the detector to
  **author-styled** indicators. Beware a **narrow-purpose token** (e.g. a ring meant for a dark
  filled button) reused as a component's focus colour on a light surface — its doc-comment's intended
  context is unenforced, so grep its **call sites**, not its comment; the fix is usually just removing
  the override so the correct global `:focus-visible` default wins.
- Focus is managed on route change, modal open/close (trap + restore), and
  async content insertion.
- **Restore-focus-to-the-trigger is not modal-only — it applies to every dismissible
  overlay.** A popover, dropdown/select menu, combobox listbox, flyout, or click-triggered
  tooltip that the user can dismiss (Escape, outside click, selection) must return focus
  to the element that opened it, same as a modal's close does; skip it and focus falls to
  `<body>` on dismiss, dumping a keyboard user back at the top of the page with no sense
  of where they were. The tell: a bare boolean open/close state plus an Escape/outside-click
  handler with no captured trigger ref and no `.focus()` call back onto it. Contrast: a
  design-system overlay primitive that captures the trigger ref on open and calls
  `.focus()` on it in its close path has the correct shape.
- **Hidden interactive content leaves the tab order — no "phantom focus."** A closed
  off-canvas menu, collapsed accordion, inactive tab panel, or CSS-hidden dropdown must
  remove its focusable descendants from the tab sequence (`inert`, conditional unmount,
  or `tabindex="-1"` on each). And `aria-hidden="true"` must **never** sit on a container
  with a focusable child (the **4th rule of ARIA**: don't put `aria-hidden` or
  `role="presentation"` on a focusable element) — otherwise a keyboard user tabs into an
  element a screen reader can't announce, the mirror of the open-dialog focus-trap above.
  Detector: tab through every collapsed / closed region and confirm focus never lands in it.
- A **global focus/scroll-into-view correction** handler (the *Focus Not
  Obscured* remedy) must yield to an open overlay and scope to the focused
  element's own scroll container — detector below.

**Global focus-correction vs. an open overlay**

A **document-level focus/scroll-into-view correction** handler — the common remedy
for *Focus Not Obscured* (nudge the scroll so a focused control clears sticky
chrome) — must **bail while an overlay is open** (gate on the open-dialog state, the
`:modal` element / `aria-modal`, or a focus-trap boundary) and **scope its scroll to
the focused element's own scroll container**, never a page-level one. A global handler
missing both guards fires for a control *inside* an open modal/drawer, measures it
against the **background** chrome, and scrolls the background out from under the
overlay — the a11y remedy for one rule silently breaks `product-ux-quality.md`'s rule
that a detail drawer overlays so "the user keeps their place", never moving the
background. Container scoping is the more general fix (it also covers any nested scroll
region).

**🚩 grep**: a `document`/`window`-level `focusin`/`focus` listener or a
`scrollIntoView`/`scrollTo`/`scrollBy` correction with no open-overlay guard and no
scroll-container scoping; exercise it — focus a field inside an open overlay and
confirm the background does not move.

**New in WCAG 2.2 — verify explicitly**
- **Target Size (Minimum) 24×24 CSS px** for pointer targets (SC 2.5.8, AA) — but **five
  exceptions**, so don't over-flag: **Spacing** (a 24 CSS px diameter circle centred on each
  undersized target intersects neither another target nor another undersized target's circle —
  so two adjacent small icons still fail when their *circles* overlap), **Equivalent** (another control
  does the same function at full size), **Inline** (a target within a sentence, or sized by the
  line-height of non-target text), **user-agent-controlled**, and **essential**. An undersized
  target that meets an exception is not a finding.
- **Dragging Movements**: any drag action has a single-pointer alternative.
- **Consistent Help**: repeated help mechanisms (contact details, a contact mechanism,
  self-help, an automated/chatbot channel) appear in the same **relative order** in the content
  across pages (SC 3.2.6, Level A) — the criterion is *order in the content sequence*, not pixel
  location.
- **Redundant Entry**: don't force re-entering info already provided in a flow.
- **Accessible Authentication** (SC 3.3.8, AA): an auth step must not require a
  **cognitive-function test** (recall a password, solve a puzzle, transcribe a code) unless it
  offers an **alternative** method or a **mechanism** to complete it — chiefly **password-manager
  support**: allow **paste** into password/OTP fields, set the right `autocomplete` tokens
  (`current-password` / `new-password` / `one-time-code`), and don't intercept clipboard events
  (the other two allowed exceptions are object-recognition and user-provided personal-content
  tests). **SC 3.3.9 (Enhanced, AAA)** drops the object-recognition and personal-content
  exceptions — so an image CAPTCHA passes 3.3.8 but **fails 3.3.9**; hold high-stakes auth
  (banking, health) to it.

**Perceivable**
- Contrast: text ≥ 4.5:1 (large text ≥ 3:1); UI components & graphical objects
  ≥ 3:1 (1.4.11). Don't convey meaning by color alone.
- **A two-state chip/pill that differs only by a colour token — with the state word in neither the
  visible label nor the accessible name — fails colour-blind *and* screen-reader users at once.** A
  badge whose two branches share an identical icon and text template and differ only in a
  colour-utility class (colour is invisible to a screen reader, and to anyone in greyscale or
  forced-colours mode, whatever the hue pair) puts the differentiating word only in a `title`
  (hover-only, not reliably surfaced to a screen reader in browse mode) and leaves it out of the
  computed accessible name too. This is the *don't-convey-meaning-by-colour-alone* rule above taken
  to the **accessible-name** channel: the state must appear in at least one non-colour channel that
  is actually announced — put the state word in visually-hidden (`sr-only`) text inside the chip
  (which joins the computed accessible name whatever the element's role) or, if the chip carries an
  interactive/labelable role, in its `aria-label` (`— at capacity`) — and ideally a distinct glyph,
  never a `title` alone (a `title` is a mouse-hover convenience, not an accessibility mechanism; and
  `aria-label` is ignored on a bare `generic`-role element). Detect
  (source-only): find a chip whose className branches on a state enum; if the two branches' icon +
  text are byte-identical and only colour classes differ, check whether the state word is in the
  computed accessible name for **both** branches — absent, or present only in `title`, is the
  finding. Test: assert the two states' **computed accessible-name strings differ**, not just their
  class lists.
- **Guard a deliberately-decorative / sub-AA token at its point of *use*, not its
  value.** A token pinned below the text-contrast threshold and documented
  "decorative only" is only decorative if *no component paints **real, informational
  text** with it* — WCAG 1.4.3 holds informational text to 4.5:1 (large text 3:1), so
  a `className`/style that colours a **visible label, status word, or helper line**
  with it fails the audit on every route sharing that chrome, while a value-only test
  asserting the token stays sub-AA stays green. Add a lint/test that **fails when the
  token colours a real text node** — fail-closed, but **with an escape**: admit a
  pinned `a11y-exempt` marker for the text 1.4.3 genuinely exempts (an `aria-hidden`
  or purely-decorative glyph, a logotype, large text already meeting 3:1), so the gate
  is *narrowed to the standard, not stricter than it* — the same gate-vs-standard
  discipline as the disabled-control exemption note below. Allow the token freely on
  non-text (borders, backgrounds, icon fills with an accessible-name sibling), and have
  the self-test plant **both** a real-text use (guard fires) and a pinned-exempt use
  (guard stays silent). This closes the runtime-binding gap the encoding self-test only
  *warns* about (`product-ux-quality.md`, the Phase-6 gate). General form: when a test
  encodes an intent ("stays decorative", "stays internal", "never renders"), assert the
  **property**, not the value it is derived from — the gap between them is where a
  green suite ships a regression.
- All non-text content has a text alternative; decorative images `alt=""`.
- Content reflows to 320 CSS px wide without loss (1.4.10); works at 200% zoom.
- Respect `prefers-reduced-motion`; no content flashes > 3×/sec. A CSS
  `@media (prefers-reduced-motion: reduce)` override does **not** reach a JS-driven
  animation (a `requestAnimationFrame` loop, an autoplaying motion library, a
  scroll/parallax handler) — the JS path must itself consult
  `matchMedia('(prefers-reduced-motion: reduce)')`. Vestibular-safety best practice; for
  the **interaction-triggered** subset (scroll/parallax, hover/click transitions) this is
  WCAG **2.3.3 Animation from Interactions** (AAA — SC 2.2.2 governs the *automatically*
  started case instead).
- **Audit reduced-motion by the *symptom* (motion-producing APIs), not only the *mechanism* the
  codebase already gates.** A thorough CSS-duration belt + a per-library `motion-reduce` variant can
  still leave an **imperative native** motion path ungated — most commonly
  `Element.scrollIntoView({behavior: 'smooth'})` / `scrollTo` / `scrollBy` with a `behavior` option,
  CSS `scroll-behavior: smooth`, `Element.animate()`, and autoplay / carousel / marquee logic —
  because a search scoped to the gated mechanism (`transition-`, the animation library's import)
  never sees them. Grep the **symptom set** and gate each on the repo's **existing** reduced-motion hook
  (cited as the patch), not a new pattern — the audit-by-symptom delta, not a re-statement of the
  CSS-doesn't-reach-JS rule above.

**Timing & motion** (WCAG 2.2.1, 2.2.2 — both Level A)
- **A time limit that logs out or discards unsaved input needs a warn-and-extend path.**
  A silent idle-logout or silent data loss fails **2.2.1 Timing Adjustable**: warn before
  expiry and let the user extend with one simple action (≥ 20 s to react), or let them
  turn the limit off / lengthen it. Exceptions: real-time events, a limit whose extension
  invalidates the activity, limits > 20 h. Note the **security ↔ a11y tension** — a short
  idle timeout is a security ask, but it still needs the warn+extend affordance before it
  fires (cross-ref `security-appsec.md` A07 session lifetime).
- **Auto-starting motion / auto-updating content needs a user control (2.2.2, Level A).**
  **Moving / blinking / scrolling** content that starts automatically, lasts **> 5 s**, and
  runs alongside other content needs a visible **pause / stop / hide** (an auto-advancing
  carousel is the classic case) — unless the motion is essential. **Auto-updating** content
  (an auto-refreshing feed / dashboard) needs the same pause/stop/hide **or** a control over
  its update **frequency**, unless the updating itself is essential — and it gets **no** 5 s
  grace period. Distinct from the 3×/sec flash limit above (seizure risk; this is
  attention / distraction).

**Forms**
- Every input has a programmatic label; errors are announced (not color-only),
  identified, and described; instructions are not placeholder-only.
- Autocomplete tokens on personal-data fields (1.3.5).

**Verify with tools + manual**: automated scanners (axe, Lighthouse, pa11y)
detect some classes of WCAG failures, not all; assert no percentage without a cited
source. Always add a manual keyboard-only pass and a screen-reader smoke test
(VoiceOver/NVDA). Report the method used; don't claim conformance from an
automated score alone.

---

## Usability & functional suitability

- The intended user's primary task completes with minimal friction; no dead
  ends. Empty, loading, error, and offline states exist and are helpful.
- Destructive actions are confirmable/undoable; nothing irreversible on a single
  mis-click.
- Copy is clear; errors say what happened and how to fix it.
- **One control, one role.** A visual control that must behave two ways — a
  navigation link (`aria-current` marks the current location) versus a local-state
  toggle (`aria-pressed`/expanded marks state) — cannot be **one component with two
  mutually-exclusive prop modes**: the mode that isn't wired emits the wrong role,
  focus, and keyboard semantics. Share the **styling** in one primitive and wrap it
  in two thin behavior components (the unification pattern: `migration-parity.md`).

## Cross-view consistency (multi-route apps)

Per-route auditing cannot see inconsistency **between** routes — every page passes
on its own. On a multi-route UI, collect once and diff:

1. **Harvest** the platform-computed accessible name + role of every interactive
   element (accessibility snapshot / `getByRole(...)`, **never** an `innerText`
   proxy — see principle 2), plus headings and empty-state sentences, per route.
2. **Same action, two labels** — group by destination (`href`/handler/resulting
   route); more than one distinct name in a group is a defect, not a nit: WCAG 2.2
   **3.2.4 Consistent Identification** (Level AA). Consistent Help (3.2.6) is the
   sibling for help/contact placement.
3. **Malformed names** — flag a name that is visually two lines but one token
   (missing separator, `"<name><Kind>"`), a bare icon glyph, an ellipsis
   truncation, or a name duplicating its own text. **Presence checks (`if (!name)`)
   catch none of these**; the usual root cause is one shared component
   concatenating sibling text nodes — fix it once in the design system.
4. **Empty-state phrasing** — one voice and one next action per class of emptiness;
   N different "nothing here yet" sentences is a design-system drift finding.

Report as **one systemic finding** naming the shared component, instances listed
(principle 6) — not one per route. Severity by consequence: a same-action-two-
labels group on a primary flow is Medium–High; phrasing drift is Low.

> **Read the name from the platform, not the DOM text.** A gate that computes
> accessible names from `innerText`/`textContent` (collapsing or inserting
> whitespace) reports a *different* string than the browser's accessibility tree —
> a permanently-green gate (principle 2). Contrast has the mirror trap the other
> way: WCAG 2.2 SC 1.4.3 **exempts** inactive/disabled controls ("a disabled
> control in HTML"), so a gate flagging them is stricter than the standard —
> narrow it, don't weaken the real check (SKILL.md Phase 1, gate-vs-standard).

## Drawer / filter / detail state should be URL-backed

Whatever a drawer, filter, or detail view represents should be bound to the
URL (`searchParams`/`router.query`/equivalent), not held only in component
memory (`useState`). State that lives only in memory silently resets on
refresh, Back, or a shared link — the user reopens the exact page and lands on
the bare list, because the open item's id was never anywhere but memory. This
is distinct from *whether* a detail view should overlay vs. navigate (a
product-intent call for `product-ux-quality.md`'s drawers-overlay rule); this
is about the state **surviving** navigation once the surface exists, and it is
mechanically checkable: does the component that holds the open/selected/filter
state also read and write the URL, and does the state actually survive a
reload.

**🚩 grep**: a drawer/detail/filter component whose expanded or selected id
lives only in `useState`/component memory, with no corresponding
`useSearchParams`/`router.query` read or write nearby. Confirm live: open the
state, reload the page, verify it survives.

## Server/client boundary — a plain value proxied across it

In a framework with a server/client split (React Server Components / the Next.js
App Router being the common case), a module marked client-only (`"use client"`)
can still export **plain, non-component values** — a string of utility classes, a
config object, a lookup table. When a **Server Component** imports one of those,
the framework does not hand it the value: it substitutes a **client-reference
proxy** (a stub for a client export). Used as data on the server — concatenated
into a `className`, spread into props — the proxy does **not** reliably throw; it
yields a **broken-but-not-crashing** result (an unstyled element, an empty string,
a control with no padding) that reads as a *styling* bug, not a boundary bug.

**Every static gate misses it.** The export's type is correct → **typecheck
passes**. No lint rule → **lint passes**. Unit tests import the module in a plain
(non-RSC) context where the value *is* the real value → **unit tests pass**, often
asserting the exact string that is proxied away at render. It is visible only by
rendering the real route through a real server/client split (a browser against a
production-like server).

- **Static check (cheap, mechanical, lint-rule-shaped):** enumerate client-boundary
  modules, list their **plain non-component / non-hook exports**, and flag any
  imported by a module that **lacks** the client directive. The fix is always the
  same: move shared plain values into a **boundary-neutral** module (no directive)
  both sides import — a client module should export only components/hooks across the
  boundary, never plain data.
- **Debugging heuristic:** an element present and correctly structured but
  **unstyled** (missing padding/gap/color the source clearly specifies) on a
  server-rendered route, with the styling defined in or re-exported from a client
  module — suspect the **boundary** before the CSS. The proxy's stringified form in
  the DOM (a function body / thrown-error text where a class string belongs) is the
  tell.
- **Completion bar:** "types + unit green" is **not** evidence a shared surface
  renders across the boundary — the rendered output must be exercised in the real
  split before "done" (the framework-boundary proxy in `report-format.md`, "Beware
  the proxy").

## Reliability & performance (Core Web Vitals)

- **LCP** (loading) ≤ 2.5 s, **INP** (interactivity — replaced FID in 2024)
  ≤ 200 ms, **CLS** (visual stability) ≤ 0.1 at the 75th percentile. That **p75 is a
  field measurement** (CrUX / RUM / PageSpeed field data) — a green Lighthouse or a single
  CI lab run is a lab snapshot, not the field p75, so "Lighthouse passed" is **not** "meets
  Core Web Vitals" (the same lab-vs-field caveat this file already applies to automated a11y
  scanners; state which was measured).
- No layout shift on the critical render path (reserve space for images/embeds — and for
  late-injected chrome like a consent banner or promo bar); no long tasks blocking input
  (a synchronous third-party script — tag manager, chat/ads widget — is the usual cause);
  images sized/lazy-loaded; fonts with `font-display: swap`; bundle split and tree-shaken;
  ship less JS — and hold JS / image / font byte-weight to a **committed budget a CI check
  fails on** when it regresses, the same size-ratchet discipline as
  `skill-authoring-and-size.md` (never a silently-raised ceiling).
- Degrades under slow/failed network; no infinite spinners.
- **No sequential data-fetch waterfall on the critical path.** Dependent requests that each
  start only after the previous resolves (a **critical request chain**) push out LCP/TTI
  even when every individual request is fast and the bundle/image/font budgets are all green
  — a green byte-budget is not a green load; the chain *depth*, not payload size, is the
  cost. Flag chained `await`s / dependent fetches on the render-critical path; parallelize
  independent ones (`Promise.all`), collapse the chain server-side (a BFF/single endpoint
  returning what the view needs in one round trip), and prefetch/colocate data with the
  route so it fires on navigation. Measure the request-waterfall, not only the bundle
  budget. (Chrome Lighthouse, *critical request chains*.) The same accidental-serialization
  shape inside a server handler's own loader — no browser round trip involved, hurting TTFB
  rather than LCP — is `performance-db-cost.md`'s Concurrency section.
- **A memoized callback needs a memoized recipient — stable props alone don't stop
  re-renders.** In a list/queue rendering N rows via `.map()`, if the parent holds shared
  per-row state (a selection set, per-row drafts, a filter) that changes on ordinary
  actions, React re-invokes and reconciles **every mounted row** on each parent state change
  — even rows whose own props are unchanged — unless the row is wrapped in `React.memo`.
  `useCallback`/`useMemo` keeping props referentially stable is **necessary but not
  sufficient**: a stable callback passed to a *non-memoized* child still triggers a full
  re-render (React calls the child to get its new element tree regardless).
  Windowing/pagination bounds how many rows *mount*, not the re-render cost of the mounted
  ones. The tell is subtle — the stable-callback code looks "already optimized" (often with
  comments about avoiding prop churn), so a reviewer stops one level too low. Fix: wrap the
  row in `React.memo` (low-risk/high-payoff precisely *because* the props are already stable
  — say so, it defeats the "will memo even help?" objection); acceptance = a render-count
  check: one row's action re-renders that row only, not the visible set.
- **An unmemoized view-model still recomputes on a sibling's keystrokes — debouncing the
  fetch doesn't gate the recompute.** A tab/view's per-row or per-tile view-model (joining
  sources, mapping/filtering a time-series per row, deriving flags) built directly in the
  render body instead of behind `useMemo`/a selector returns a brand-new array/object on
  **every** re-render of its parent, not only when its own inputs change — so even a row/tile
  already wrapped in `React.memo` (the bullet above) can't bail out against it: memo compares
  the incoming reference, and this one is never stable. The usual trigger: an always-mounted
  search/filter input sets synchronous "echo" state in the shared parent on every keystroke (a good pattern
  by itself — it's what makes typing feel instant) while only the **debounced** value later
  reaches the actual fetch/filter. That harmless-looking synchronous `setState` still
  re-renders the shared parent and rebuilds the view-model from scratch — the debounce gated
  the **network call**, not the **work** — so every row/tile, and any real chart it owns,
  redoes its render work on every keystroke instead of only when the debounced value actually
  changes. It hides in plain sight because a tab panel that unmounts while inactive confines
  the cost to whichever tab happens to be open (trace what *else* changes state while that
  tab is mounted), and because a neighboring derived value in the same component is often
  correctly memoized already — keep scanning past the first `useMemo` you find; a component
  can memoize one derived value and skip a costlier one two lines below. Detect: confirm the
  view-model has no memoization keyed on its real upstream inputs (not on the un-debounced
  echo state); gate the finding on real cost (tens-to-low-hundreds of rows/tiles doing
  non-trivial per-row work — a real chart, not a static text cell). Fix: memoize the
  view-model on its real upstream inputs, then apply the row-level `React.memo` from the
  bullet above so the now-stable reference actually pays off — and reject a debounce-only
  patch: "add a debounce to the search input" does not fix this when a debounce already gates
  the fetch and the recompute still fires underneath it; the missing piece is the memo
  boundary, not more delay. Same render-count acceptance as above, run on a keystroke in the
  *unrelated* input: zero re-renders in the view while typing. Distinct from the byte-weight
  CWV budget above (payload size, not recompute cost); from the memoized-callback bullet
  above, which owns the row-level `React.memo` boundary triggered by *per-row* shared state
  such as a selection set, while this owns the derivation going unmemoized, the debounce-echo
  trigger from a *totally unrelated* sibling, and the realistic-cost gate; and from the
  dataset-leak bullet below (a client-bundle **size** leak, not render churn).
- **A correct child memo is silently defeated by an inline collection literal at the call
  site.** Kin to the unmemoized-view-model bullet above, but with nothing for a reviewer to notice: here the child *is* memoized correctly
  — its expensive derivation (build a tree, join lists) is behind `useMemo`/`React.memo` keyed
  on exactly the right prop — but the parent passes that prop as a literal built **inline in
  JSX**, e.g. `<Child matchIds={new Set(items.map(x => x.id))} />` (also a spread `[...]`, `new
  Map(`, or an object literal `{…}`). The literal takes a **brand-new identity on every parent
  render** — including renders driven by something unrelated to its contents (a sibling input's
  un-debounced keystroke echo, a hover toggle, a re-render cascade) — and memo compares deps by
  reference, so a same-contents-new-identity value is indistinguishable from a real change: the
  child's memo invalidates and the expensive work reruns on every parent render. It reads clean
  in either file alone — the child's memo is textbook, the parent's prop is an unremarkable
  one-liner. Detect: grep call sites for a prop whose value is an inline `new Set(`/`new
  Map(`/`[...`/`{…}` that is **not** itself from a `useMemo`/stable state, then confirm the
  receiving component keys a memo/effect dependency on it; verify by counting the child's
  recompute while triggering an *unrelated* parent state change. Fix: hoist the literal into the
  parent's `useMemo` keyed on its true upstream (`const ids = useMemo(() => new Set(items.map(x
  => x.id)), [items])`) and pass the stable reference down. Distinct from the two bullets above by
  *what is unstable and whether anything flags it*: the memoized-callback bullet has **no
  `React.memo` on the child at all**; the unmemoized-view-model bullet has an unstable **named
  derivation** (a view-model a reviewer can see and memoize); here the child's memo is **already
  correct and correctly keyed** and the unstable value is a **bare inline literal** with no named
  derivation to notice — so the only fix is to stabilize the literal's identity, never to add
  memoization the child already has.
- **A heavy optional-feature library must be gated at the *import*, not just the render.** A
  rich-text editor, chart/diagram lib, PDF/export, or syntax highlighter that renders only
  behind an interaction gate (`open`/`editing`/`expanded`) but is **statically imported at
  module scope** by an always-mounted list/row/card component ships in the bundle of **every
  route** that transitively imports that component — so the majority of visitors who never
  trigger the gate still download/parse/compile it (illustratively ~130 KB gzip on the
  highest-traffic routes). It *looks* optimized because the heavy child renders
  conditionally — but the gate that matters for bundle weight is the **import**, not the
  render. Detect: grep each heavy/optional dependency's importers; flag any imported
  statically from a component mounted on a list/index route where the heavy part only
  renders behind interaction. Fix: defer it (`next/dynamic` / `React.lazy` / an inline
  `import()`) behind the same gate the render already uses. Strong tell: the codebase
  already defers a *different* heavy dep correctly — name that precedent, it makes the fix
  trivially arguable.
- **A shared data-access module can leak an entire static dataset into a client bundle
  through one "harmless" helper import.** A module holding a frontend's full
  compiled/static dataset (a large JSON import) alongside small lookup helpers
  (`getThing(id)`, `labelFor(key)`) ships the **whole dataset** to any client
  component that imports even one helper, whenever the module builds its exports by
  processing the entire dataset at load time (spreading it into a derived singleton
  the helpers close over) — a bundler cannot tree-shake around a singleton built
  from the whole input, so importing one small function drags the rest along. It
  looks safe because the helper's signature gives no hint of size, and because
  `import type { Thing } from './data'` really is erased at compile time — training
  a reviewer to assume any import from that module is free, when a *value* import of
  a sibling helper is not. Nothing fails: no test, typecheck, or lint rule catches
  it; it shows up only as a bigger bundle-analyzer entry or a "this page feels slow"
  report, rarely traced to the import line. Detect by walking each client entry
  point's **runtime** import graph (stripping type-only imports first) for an edge
  into the big-dataset module, then confirming a suspect route's bundle size
  before/after removing the import. Fix by resolving the lookup server-side and
  passing only the small resolved value down as a prop, or by refactoring the helper
  to a structural-parameter form (`getX(id, allThings)`) living in a dataset-free
  module, so a caller supplies its own narrow slice; add a standing import-graph
  test so a **new** client component reaching the dataset fails CI instead of
  shipping silently. Distinct from the heavy-optional-library bullet above — that
  library is needed only behind an interaction gate and the fix is deferring the
  *import*; a data-lookup helper is typically needed unconditionally at its call
  site (e.g. rendered on first paint), so deferral alone doesn't remove the cost and
  the fix is architectural instead. Also distinct from the Server/client boundary
  proxy above: that is a **Server** Component reading a **client**-marked export and
  getting an inert stub (a functional bug); this is a **Client** Component reaching
  a large payload through an unmarked shared module (a bundle-size bug) — the
  boundary direction and the failure mode are both reversed.

## Security & compatibility

- Output encoding for anything user-influenced (XSS — see `security-appsec.md`
  A05); a strict Content-Security-Policy.
- **No secrets/API keys/tokens in the client bundle or source maps** — anything
  shipped to the browser is public.
- No sensitive data in `localStorage`/`sessionStorage`; tokens in
  httpOnly+Secure+SameSite cookies where possible.
- **A `message` listener validates `event.origin` (and the message shape) before trusting
  `event.data`.** Any origin can `postMessage` to a window, so a handler that reads `event.data`
  with no allow-list check on `event.origin` is an origin-validation flaw (CWE-346); and a trusted
  sender can still relay a malformed payload, so validate the message syntax too (MDN
  *Window.postMessage*: "always verify the sender's identity using the `origin` and possibly
  `source` properties").
- **Third-party / CDN `<script>` and `<link>` carry Subresource Integrity.** An
  `integrity="sha384-…"` hash plus `crossorigin` lets the browser refuse a resource a compromised
  CDN has altered — without it, one CDN compromise rewrites what every user's browser executes
  (MDN *Subresource Integrity*).
- **Trusted Types as a DOM-XSS backstop on top of output encoding, not instead of it.** The
  `require-trusted-types-for 'script'` CSP directive forces DOM injection sinks (`innerHTML`,
  `eval`, `script.src`) to take policy-created typed values, turning a raw-string sink into a
  `TypeError` — a browser-enforced backstop (MDN *Trusted Types API*: Baseline 2026; a tinyfill keeps older browsers from throwing
  but enforces nothing there), layered on the output-encoding rule above.
- **`Referrer-Policy` does not leak a token-bearing URL cross-origin.** The `Referer` header sends
  the full URL (path + query) to other origins; the modern default is already
  `strict-origin-when-cross-origin` (MDN *Referrer-Policy*), so the finding is a **weakened** policy
  (`unsafe-url`, `no-referrer-when-downgrade`) — or secrets/ids placed in a URL at all, which then
  ride the `Referer` to a third party (prefer keeping them out of the URL).
- **Clickjacking is a named threat, not just a header in a list.** Every page rendering an
  authenticated or state-changing action confirms `frame-ancestors` (CSP) — or legacy
  `X-Frame-Options` — restricts who may frame it; an unset framing policy lets an attacker overlay
  it in a transparent iframe (`security-appsec.md` A02 lists the header among misconfig; this is the
  threat and the per-page verification).
- Works across the project's target browsers/devices; responsive at real
  breakpoints; internationalization-ready (no hardcoded user-facing strings,
  correct locale-aware formatting — see section i18n in `SKILL.md`).

**🚩 grep**: `<div onClick`/`<span onClick` without keyboard handling &
`role`/`tabindex`; `role="button"` on a non-focusable element; images with no
`alt`; `<input>` with no associated `<label>`; `outline: none` with no
replacement focus style; hardcoded `#hex` text colors to spot-check contrast;
`localStorage.setItem('token'`; API keys in `NEXT_PUBLIC_`/`VITE_`/`REACT_APP_`
env names; `addEventListener('message'` with no `event.origin` check; a `<script>`/`<link>` to a
third-party origin with no `integrity=`; a weakened `Referrer-Policy` (`unsafe-url`); no
`frame-ancestors`/`X-Frame-Options` on a page with authenticated or state-changing actions; a
small lookup helper imported from a shared module that also builds a derived singleton over
an entire large dataset (walk the client import graph, stripping type-only imports, for an
edge into that module); a loading/skeleton component with `aria-busy` and/or a label prop but
no `role="status"`/`role="alert"`/`aria-live` on it or an ancestor; a static `aria-label` that
doesn't contain the element's own visible text (WCAG 2.5.3); an icon/label swap keyed off an
`open`/`expanded` boolean with no matching `aria-expanded` on the same control.
