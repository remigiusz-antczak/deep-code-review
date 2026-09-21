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
- **An element made interactive with `tabIndex={0}` + `onKeyDown`/`onClick` on a
  non-semantic tag (`<div>`/`<span>`), but given no `role` and no accessible name, has a
  control's *behaviour* without a control's *identity*.** It is focusable and
  keyboard-activatable, so a keyboard-only pass "works" and a reviewer signs off — yet with
  no `role` the element keeps its implicit ARIA **`generic`** mapping ("A nameless container
  element that has no semantic meaning on its own", WAI-ARIA 1.2), so assistive tech is told
  no role; and with no `aria-label`/`aria-labelledby`/own text it has no accessible name. An
  AT user can focus it and press it but is never told what it is — the textbook **WCAG 4.1.2
  Name, Role, Value** gap (name *and* role must be programmatically determinable). The
  classic shape is a shared **roving-tabindex** hook (Gmail/Linear-style `j`/`k` list
  navigation) that spreads `tabIndex`/`onFocus`/`onKeyDown` onto each list item's wrapper
  `<div>`, with Enter activating it, and never sets a role or name. Distinct from three
  neighbours: (1) the `<div onClick>` **with no keyboard handling and no `role`/`tabindex`**
  in the 🚩 grep below is a *lockout* — not operable at all; this one *is* operable and
  degrades gracefully (the wrapped content's own links/buttons stay tab-reachable), which is
  exactly why it slips past a keyboard smoke test. (2) The non-labelable-host bullet below is
  an element that *has* a role and lacks only a name; here **both** are absent, and the
  `tabIndex`/`onKeyDown` is what makes the JSX look finished. (3) The custom-combobox
  required-state (Forms) and loading-skeleton bullets are about whether a *state* or a
  *transition* reaches the tree; this is whether role and name exist at all. Fix in that
  order — **role first, then name**: prefer the native semantic element (`<button>`/`<a>` —
  the first rule of ARIA above); or set the `role` the behaviour implies
  (`button`/`option`/`tab`/`link`) **and then** a computed accessible name — an `aria-label`
  bolted onto a still-`generic` `<div>` is not a half-fix but *no* fix, because there is no
  role for the name to attach to (the `generic`-role aside under the colour-alone chip bullet
  below). For a roving **composite** widget the role goes on **both** the container and its
  items — the container role (`listbox`/`menu`/`grid`/`tablist`) is what makes the item roles
  valid (the APG keyboard bullet under Keyboard & focus); where a single activate-role
  misrepresents rich row content, use `role="group"` + `aria-roledescription` + a computed
  name. Detection/test: the wrapper's **computed role is not `generic`** and it has a
  **non-empty accessible name distinct from its verbatim concatenated contents**, read from
  the accessibility tree (devtools/axe), not the DOM — a keyboard-only pass proves
  operability, never identity.
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
- **A dismissible chip/tag button whose accessible name is only the *value* it represents states no
  *action* — a screen-reader user hears the current filter, never that the control removes it.** The
  common filter/token chip renders as `<button>{label} ×</button>` (a visible label plus a trailing
  `×` multiplication-sign glyph), and its accessible name computes from that visible content to the
  **value** — `"Category: Books ×"` — so assistive tech announces the filter that is *set*, with no
  hint the button's *purpose* is to clear it; the trailing `×` is a decorative glyph with **no
  reliable spoken equivalent** (announced as "times", as its Unicode name, or skipped, depending on AT
  and verbosity). That fails **WCAG 2.4.6 Headings and Labels** (AA — a label must describe the
  control's *purpose*, and "Category: Books" describes the value, not "remove this filter") and leans
  on **4.1.2 Name, Role, Value**. It ships because a name *does* exist and even reads as descriptive,
  so a presence check (`if (!accessibleName)`), a first-read screen-reader pass, and a sighted
  click-through (the `×` reads as "remove" to the eye) all approve. Fix: give the button an
  `aria-label` stating the **action and its target** — `aria-label="Remove filter: Category Books"` —
  and mark the `×` `aria-hidden="true"` so it is not announced. **Distinct** from the Label-in-Name
  (2.5.3) bullet above, whose polarity is opposite — there a rewritten `aria-label` wrongly *drops* the
  visible text; here the visible text *is* the whole name and is insufficient because it names the
  value, not the action — and the two combine: the action label you add must still **contain the
  visible target text** (lead with the action, keep "Category: Books" in the string) so the fix does
  not itself break 2.5.3. Distinct too from the roving-tabindex and non-labelable-host bullets above,
  where a name is **absent or unsourced**; here a name is present with a **valid role**, and only the
  *action semantics* are missing. Detection (source-only): an interactive dismiss/remove/clear control
  whose only accessible name is its subject label plus a bare glyph (`×`/`✕`/`⨯`), with no `aria-label`
  naming the action; test that the computed name contains the action verb, not only the subject.
- **A Tooltip/description helper that wires `aria-describedby` onto the one child
  it is handed assumes that child *is* the focusable control; a call site that
  wraps the real control breaks the association silently.** The common React
  idiom clones the single child and merges the description link (`aria-describedby`
  pointing at the tip's id) plus the hover/focus handlers onto it — correct for a
  bare `<Tooltip><button/></Tooltip>`, where the link lands on the button and a
  screen reader reads the tip on focus. But nothing constrains the child to be the
  control: a caller who wraps it for layout or positioning
  (`<Tooltip><span><button/></span></Tooltip>`), interposes a non-focusable
  wrapper as the disabled-control workaround (a native `disabled` control fires no
  hover/focus events, so the reveal handlers have to sit on the wrapper), or passes
  a `forwardRef`/styled wrapper, lands the description on the wrapper; a **fragment**
  child, or a child component that doesn't forward the prop, drops it entirely. In
  the layout and `forwardRef` cases the inner `<button>` still receives focus but
  now carries no accessible description, so a screen-reader user focusing it hears
  no tip. The disabled-control case is worse: a native `disabled` `<button>` is not
  focusable and not in the tab order at all, so the description is unreachable
  wherever it sits — surfacing the "why is this inert" explanation the tooltip
  exists to give means making the control `aria-disabled` (which keeps it
  focusable) *and* routing the description onto that focusable control, not the
  wrapper. The tip still renders and still appears on hover and keyboard focus (the
  handlers sit on the wrapper and focus events bubble to it), so a sighted
  click-through and any pixel/visual-regression snapshot pass — only the
  accessibility tree shows the focused control's description is empty. This is the
  failure mode of the Label-in-Name bullet's own advice above — move extra context
  into a `title`/tooltip — when that tooltip is a clone-onto-child one, and it
  *extends* the name-sourcing bullets above (there a **name** is unsourced or drops
  its visible text; here a **description** reaches the wrong node). Distinct from
  four neighbours: the roving-tabindex bullet above spreads props onto a wrapper
  that leaves *role and name* absent (here role and name are fine, only the
  description is misrouted); the required-state combobox bullet (Forms) below is a
  *state* that never reaches the control; the loading-skeleton bullet below is a
  *transition* that is never announced; and the dismissible-overlay focus-restore
  bullet below (Keyboard & focus) is about *restoring focus on dismiss*, not wiring
  the description at all. Fix — target the control, not the element passed in:
  document and **dev-time-assert** that the child is the single host element that
  takes focus (`React.Children.only` catches multi-child input, plus a check that
  the child is a focusable host node, not a fragment or a component that swallows
  the prop); or expose the generated id through a ref / render-prop / anchor API so
  the wrapper can keep the handlers while the description is placed on the focusable
  descendant (an anchor-ref API that resolves the actual control is the robust
  shape). Detection/test: assert the **computed accessible description of the
  focused control** from the accessibility tree (devtools/axe), not the presence of
  the `role="tooltip"` node in the DOM or a screenshot — the same computed-property
  harvest the name bullets above rely on.
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
  this is only the announcement half. And see the inverse below — a call site
  that hand-rolls a skeleton while a *correct* shared loader already exists,
  where the fix is reuse (so the announcement propagates), not patching the
  copy.
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
- **A loading placeholder hand-rolled at a call site while a *correct* shared
  loader already exists is one defect wearing two hats — needless duplication
  *and* an accessibility regression the shared fix can't reach.** The
  loading-announce bullet above is a defect *inside* the shared component (it
  has `aria-busy`/a label but no live-region role); this is the inverse. The
  shared `<Loader/>`/`<Spinner/>` is *correct* — its busy-region semantics
  already announce — and one screen reimplements the same shimmer inline
  (`<div className="skeleton">` block grids, `animate-pulse`) with **no**
  `aria-busy`, `role="status"`, or `aria-live` at all, so through its whole
  loading window an assistive-tech user hears nothing (no "content pending", no
  update when it arrives) while the sighted reviewer sees a polished shimmer
  that *matches the rest of the app* and approves. The two faults are coupled,
  not coincidental: because the copy never renders *through* the shared
  component, the accessibility baked into that component — and its next a11y
  fix — never reaches this surface (`product-ux-quality.md`'s "adoption is
  total" and "a fix to a shared concept lands in the shared component"
  bullets). Detection inverts the loading-announce sweep: don't audit the
  shared loader's ARIA — find the correct shared loader, list its importers,
  and diff that set against components that render loading placeholders (grep
  bespoke skeleton scaffolding — a `className` containing
  `skeleton`/`shimmer`/`pulse`, or repeated placeholder block `<div>`s — in
  files importing no shared loader); each such hit is a call site that
  hand-rolled instead of reused. Fix in order: **reuse the shared loader** —
  that, not patching the copy, is what makes every future announcement fix
  propagate; bolting `role="status"` onto the hand-rolled grid cures today's
  silence but keeps the duplication and the next drift. Only if a bespoke
  skeleton is genuinely unavoidable, wrap it in the announced busy region per
  the loading-announce bullet above. Regression-test the reused path: assert
  the placeholder renders through the shared loader (its `getByRole('status')`
  resolves), not a raw div grid. **Distinct** from the dead-`<Suspense>`
  bullet under Reliability & performance (a fallback that never *renders*) —
  this loader renders fine and is merely silent.

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
- **A non-modal popup — a combobox listbox, select menu, autocomplete, or dropdown —
  must also close when focus *leaves* it, a dismiss path separate from Escape and
  outside-click and the one a roving-tabindex / `aria-activedescendant` design most
  often omits.** Such a widget has *three* independent dismiss code paths, wired in
  three different places: **Escape** (a `keydown` handler), **outside pointer** (a
  document `pointerdown`/`click` listener that closes when the target is outside the
  trigger + popup), and **focus leaving the widget** (a `focusout`/`blur` handler, or
  `Tab` intercepted in the `keydown`). The first two are the ones every implementation
  reaches for, so a keyboard-Escape check and a click-away check both pass and a
  reviewer signs off "dismissal handled" — yet moving focus out of the widget with the
  keyboard fires **no** pointer event (the outside-click listener never runs) and is
  **not** the Escape key (that handler never runs), so a popup wired only for those two
  is left **open and orphaned**: it floats over the page while focus sits on some later
  control, a WCAG **2.4.3 Focus Order** break in which the reader's focus and the one
  visible interactive overlay are in different places. The **roving-tabindex /
  `aria-activedescendant`** design is what guarantees the exposure: the WAI-ARIA APG
  *Combobox Pattern* keeps the combobox a **single** tab stop and states that "the
  popup, and the popup descendants are excluded from the page `Tab` sequence" (verified
  this session; the pattern's only listed popup-dismiss key is Escape), so a
  `Tab`/`Shift+Tab` out of the widget necessarily lands focus on the next page control
  with nothing inside the popup to catch it — the stuck-open popup is structural, not
  incidental. A keyboard-only smoke test that opens, arrows, and Escapes never presses
  `Tab` **while the popup is open**, so it never sees it. Fix: add the focus-exit
  dismiss — a `focusout` on the widget container that closes when `relatedTarget` falls
  outside the trigger + popup subtree (or handle `Tab`/`Shift+Tab` in the `keydown`
  before focus moves) — then let focus land naturally on the next control (a non-modal
  popup must **not** trap; see the inverse below). Detection: a listbox/menu/combobox
  with an Escape `keydown` and a document outside-click listener but **no**
  `onBlur`/`focusout` on the container and no `Tab` branch in the `keydown`; confirm
  live by opening the popup and tabbing out — it must close. **Distinct** from three
  neighbours: the dismissible-overlay focus-restore bullet above is the *restore* half
  (return focus to the trigger *once dismissed*, and it lists the dismiss triggers as
  Escape/outside-click/selection) — this is a dismiss trigger that list omits, and it
  must fire *before* any restore can; the combobox APG-pattern bullet above prescribes
  the whole keyboard map (Arrow/Enter/Escape) — this isolates the one dismiss path a
  widget with a correct Escape still routinely lacks, the way the
  disclosure-`aria-expanded` bullet isolates that bullet's most-omitted state; and the
  hand-rolled-`aria-modal` bullet below is a **modal** that must *trap* focus so `Tab`
  wraps **inside** — a non-modal popup is the inverse (Tab moves **out** and closes it),
  so trapping one is as wrong as failing to dismiss the other. Regression test: render
  the widget open, move focus to a control outside it, and assert the popup is gone
  (`queryByRole('listbox')` is null), not only that Escape closes it.
- **Hidden interactive content leaves the tab order — no "phantom focus."** A closed
  off-canvas menu, collapsed accordion, inactive tab panel, or CSS-hidden dropdown must
  remove its focusable descendants from the tab sequence (`inert`, conditional unmount,
  or `tabindex="-1"` on each). And `aria-hidden="true"` must **never** sit on a container
  with a focusable child (the **4th rule of ARIA**: don't put `aria-hidden` or
  `role="presentation"` on a focusable element) — otherwise a keyboard user tabs into an
  element a screen reader can't announce, the mirror of the open-dialog focus-trap above.
  Detector: tab through every collapsed / closed region and confirm focus never lands in it.
- **A hand-rolled full-screen overlay that copies a dialog's ARIA (`role="dialog"`/`"alertdialog"` +
  `aria-modal="true"`) but skips the app's shared modal / focus-trap / background-`inert` helper
  asserts a modality it never delivers.** `aria-modal="true"` is not a label AT reads back — it is an
  *instruction* AT acts on: it tells a screen reader to stop exposing everything outside the dialog
  and confine the user to its subtree. The ARIA APG modal-dialog pattern is explicit that you may set
  it *only* when the code actually prevents interaction with the background **and** the styling
  obscures it, because on some AT it removes the rest of the page from perception. So an interstitial,
  error gate, or "you must do X first" blocker rendered as a raw sibling of the app tree with the
  right role and attribute but **none** of the behavior — focus never moves into it on open, `Tab`
  from its last control escapes to the page behind it, the background is never `inert`/`aria-hidden`,
  focus is never restored on close — is *worse* than one carrying no `aria-modal` at all: a
  keyboard/AT user is sent into background the attribute swore was gone, so it actively misdirects
  rather than merely under-serving. It ships because it looks right — it covers the viewport and
  carries the correct role, so a visual pass and an "is it mounted?" render test both approve — and
  because it is usually the newest surface, landing after the hardening pass that fixed every other
  overlay. **Root cause and fix are the #838 bypass fault (the hand-rolled-skeleton-vs-shared-loader
  bullet above), with a modal-specific payload:** reuse, don't patch — render the surface through the
  ONE shared overlay primitive, or native `<dialog>` opened with `.showModal()` so the modal
  behavior comes from the platform rather than hand-rolled app code; either way the containment
  reaches this surface for the reason that bullet gives. Only if a bespoke overlay is
  genuinely unavoidable, have it call the same focus-move-in, focus-trap, background-`inert`, and
  restore-on-close helpers — bolting the attribute on without them is not the fix. Detection
  **inverts** that sweep: grep every `aria-modal="true"` / `role="dialog"` / `role="alertdialog"` and
  diff the set against the importers of the shared modal/focus-trap helper — each hit that neither
  renders *through* the primitive nor calls the helpers is a Focus Order defect (2.4.3). **Distinct**
  from three neighbours: the dismissible-overlay focus-restore bullet above is only the *close* half
  (return focus to the trigger) and presupposes the open dialog was already trapped — this is the
  *open + while-open* half it assumes; the phantom-focus bullet above marks *hidden* subtrees `inert`
  to keep focus out, where here `inert` belongs on the *visible background under an open dialog* (its
  inverse); and the "modal open/close (trap + restore)" line above states the rule, where this is the
  failure mode in which the rule is skipped but the attribute is asserted anyway. Regression-test the
  behavior, not the mount: on open `document.activeElement` is inside the dialog; `Tab` from the last
  focusable wraps within it and never reaches a background control; the background is
  `inert`/`aria-hidden`; `Escape`/close returns focus to the opener — an "is it mounted?" assertion
  catches none of it.
- **A scroll container made keyboard-scrollable with a static `tabIndex={0}` stays a focus
  stop on the screens where its content fits and nothing scrolls — gate the focusability on a
  live overflow measurement, not a constant prop.** A region that scrolls only by wheel/touch
  has no keyboard equivalent, so making its wrapper focusable (`tabIndex={0}`, often with
  `role="region"`/`"group"`) is the correct, expected fix: it lets arrow/`PageDown`/`Home`/`End`
  scroll it, and an automated scan flags a scrollable region that cannot take focus (axe's
  `scrollable-region-focusable` — the WCAG 2.1.1 Keyboard concern). The bug is applying it
  **unconditionally**. At the widths where the content sits inside the box with room to spare —
  often the common case — the wrapper is still in the tab order with nothing to scroll: a focus
  target that moves nothing and, if named, announces itself for no reason. Repeat it once per
  list row/card and it compounds into many dead stops that stretch keyboard traversal (2.4.3
  Focus Order) on exactly the views built to scan fastest, while a keyboard-only smoke test
  still "passes" — focus lands and the ring shows; only the *purpose* is missing, which a
  shape/keyboard pass never checks. Fix: derive `tabIndex` (and any `role` added *solely* to
  explain that focusability) from a live `ResizeObserver` comparing `scrollWidth > clientWidth`
  (or `scrollHeight > clientHeight`) — the same comparison the clip/truncation check asserts
  (`testing-and-evals.md`) — so the wrapper is a tab stop only while it can actually scroll;
  and recompute on mount/resize, **not while the element holds focus**, since stripping
  `tabIndex` from the focused element bounces focus to `<body>`, a worse Focus Order break than
  the dead stop. When it *is* focusable it still needs a role and an accessible name so AT can
  say why it is a stop (the *role first, then name* bullet above); a genuinely-named landmark
  region keeps its role regardless — the target is the no-op stop, not focusability itself.
  Detector: `tabIndex={0}`/`tabindex="0"` on an `overflow-auto`/`overflow-x-auto`/
  `overflow-scroll` wrapper with **no `onKeyDown`/`onKeyPress`** in the component and no
  condition tying the prop to a measured overflow; a strong secondary tell is the same file
  already gating a *different* attribute on an overflow/clip measure (a title tooltip shown only
  when the text is actually clipped) — the technique is known, just not applied here. Distinct
  from two neighbours: the phantom-focus bullet above removes focus from *hidden* content (here
  the region is visible, just not overflowing), and the roving-tabindex bullet's wrapper is
  *operable* but roleless/nameless (here the wrapper is not operable at all — nothing to
  operate).
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
- **A direction/movement badge whose only non-colour cue is a bare Unicode arrow *glyph* (`▲`/`▼`,
  `↑`/`↓`) clears the colour-blind test but still owes a *spoken* equivalent.** A delta or trend chip
  rendered as a plain `<span>` — an arrow character plus a magnitude, coloured by sentiment — reads
  correctly in greyscale (a *shape* is present, so *Never colour alone* in `product-ux-quality.md`
  looks satisfied) and serves a sighted colour-blind user. But that shape channel is **visual only**:
  a bare Unicode symbol character has **no reliable spoken form** — assistive tech announces `▲` as
  "black up-pointing triangle", as "up arrow", or skips it, depending on AT and verbosity — so to a
  screen-reader user the direction rides on the glyph + colour and neither is dependable (**WCAG 1.1.1
  Non-text Content**: the glyph is not a dependable text alternative; **1.4.1 Use of Color**: colour is
  unspoken). The trap is that a Unicode arrow *looks like text* — it is a character — so it is assumed
  accessible and no alternative is added, unlike an obvious `<img>`/icon. Fix: put the direction in a
  **word** the accessibility tree exposes — visually-hidden (`sr-only`) text inside the chip
  (`<span class="sr-only">up </span>`), which joins the computed name, or an `aria-label` on a
  labelable host (`"up 3 percent versus last month"`) — and mark the decorative glyph
  `aria-hidden="true"`; the arrow reinforces, the word carries. **Distinct** from the two-state
  colour-only chip bullet above, where the branches differ by **colour alone with no shape at all**
  (fix: add any non-colour channel) — here a shape *is* present and the point is that a **glyph is not
  a spoken equivalent**; from *Never colour alone* (`product-ux-quality.md`), which lists `▲▼` as a
  valid **visual** shape cue — this adds that clearing the greyscale axis does **not** clear the
  **screen-reader** axis; and from the icon-button name bullets above, which concern an **icon font /
  SVG** that plainly needs a name — the wrinkle here is a **Unicode character** deceptively treated as
  accessible text. Detection (source-only): a status/delta/trend node whose direction is a literal
  arrow character (`▲▼↑↓▴▾`) in its text with no sibling `sr-only` word and no `aria-label`, the glyph
  not `aria-hidden`. Test: assert the **computed accessible name** (accessibility tree, not
  `textContent`) contains the direction **word**, not only the glyph.
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
- **When a shared `Field`/`FormField` wrapper's required-asterisk is `aria-hidden`,
  "required" MUST still reach assistive tech through some other channel — verify a
  composed custom control actually provides one.** Marking the glyph itself
  `aria-hidden="true"` (`<span aria-hidden="true">*</span>`) is correct on its own — a
  screen reader shouldn't spell out "asterisk" — but that only removes the *wrong*
  channel; it doesn't establish a *right* one. A native `<input required>` / `<select required>` / `<textarea required>` gets the right
  channel for free: per **HTML-AAM** (W3C Working Draft, 2026-08-29) §3.6.116, the HTML
  `required` attribute on those three elements maps automatically to `aria-required` in
  the accessibility tree. A **custom composite control** — a `role="combobox"` `<button>`
  opening a portaled `role="listbox"` (a hand-rolled Select/MultiSelect/Combobox) — is not
  that native element, so it gets no such mapping; if its prop type carries no
  `required`/`aria-required` and nothing spreads onto its trigger, then `<Field required><CustomSelect /></Field>` exposes
  "required" through **no channel at all** — the asterisk is hidden from AT and the
  trigger never sets `aria-required`. Distinct from the accessible-name and Label-in-Name
  bullets above (whether a *name* exists, or still contains the visible text): this is
  whether the required *state* reaches the accessibility tree at all. **WCAG 3.3.2 Labels or
  Instructions** (Level A) is the SC that requires the requirement be communicated at all — its
  Understanding page names **ARIA2: Identifying a required field with the `aria-required`
  property** as an *advisory* technique — and **WAI-ARIA 1.2** makes the visual/programmatic split
  explicit: "The fact that the element is required is often presented visually (such as a
  sign or symbol after the widget). Using the `aria-required` attribute allows the author
  to explicitly convey to assistive technologies that an element is required" (confirmed
  valid on the `combobox`, `listbox`, and `textbox` roles, among others). A default value
  that happens to be valid doesn't close the gap — 3.3.2's instruction duty and
  `aria-required`'s programmatic state are both about whether the requirement is
  *communicated*, independent of whether the current value would *pass* it. (**WCAG 4.1.2
  Name, Role, Value** supplies only the general principle that a component "generated by
  scripts" carries none of a native element's free semantics — not a mandate for
  `aria-required` on an author-set property.) Detection: grep the field wrapper for its
  required indicator and confirm it's visual-only (`aria-hidden`); find every custom
  (non-native-`<select>`) dropdown/combobox and check its prop type and trigger element
  for `required`/`aria-required`; then check real call sites for `<Field required><CustomWidget /></Field>` and read the
  **accessibility tree** (devtools/axe), not the DOM. Fix: add `required` →
  `aria-required` on the custom widget's trigger, or, better, thread it through the
  wrapper's a11y context so every child control derives it automatically. Regression-test
  the **composition**: render `<Field required><CustomSelect /></Field>` and assert `aria-required="true"` on the
  `role="combobox"` node — a test of `Field` or `CustomSelect` in isolation passes either
  way and misses exactly this gap.

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
- **A singleton-read hook that fetches per instance fans out to one identical request per
  mounted consumer — a page with N callers makes N copies of the same call.** A
  `useUser()`/`useSession()`/`useCurrentUser()`-style hook — or any hook many components call to
  read the *same* shared singleton — implemented as its own fetch-on-mount (`useState` + a
  `useEffect` that `fetch`es `/me` and `setState`s, or a fetch on first render) with no shared
  cache or dedup fires an **independent** network request from **every** component that calls it,
  so a page mounting a dozen consumers issues a dozen identical `/me` requests on one load. It
  reads clean at the hook (small, correct, returns the right `{ user, loading }`) and clean at
  each call site (which just calls the hook); the redundancy exists only across the *set* of call
  sites and surfaces only as the network tab's N copies of one request — a per-file review never
  sees it. Worst when the callers sit in the **global shell** (nav bar, command palette, global
  FABs, an auth guard): those mount on **every** route, so the multiplier is paid per navigation,
  and each consumer runs its **own** retry/backoff on failure and gates its own region's render on
  its own copy of `loading`, compounding perceived slowness beyond the raw N× server/network
  load. Detect by grepping the hook's call sites and asking whether the fetch lives behind a
  single shared **Provider/Context** (or a keyed dedup cache) or a **per-instance** effect; count
  the consumers the global shell mounts — each is a per-route multiplier. Strong tell: the
  codebase already documents this cost at **one** call site specially re-engineered to avoid it (a
  hoisted fetch, a threaded-down prop) while other global sites still pay it — name that
  precedent, it makes the fix trivially arguable. Fix: mount **one** Provider/Context (or back the
  hook with a request-deduping cache — SWR / React-Query keyed on the resource, or a module-level
  in-flight singleton promise) once near the root that does the single fetch/retry the hook
  already implements, and switch every call site to a context read; **keep the hook's public
  return shape** so no consumer changes. Acceptance = exactly one identity fetch per page load
  regardless of consumer count. Distinct from the **waterfall** bullet above by *shape*: that is
  chain **depth** (dependent requests each awaiting the previous; fix = parallelize or collapse),
  this is identical **breadth** (independent requests for the *same* value; fix = coalesce to
  one) — same load cost, opposite geometry. Distinct from **N+1** in `performance-db-cost.md`
  (Database): that is N *different* queries, one per **row** of a result; this is N *identical*
  requests for one **singleton**, one per **component instance**. The coalescing itself is the
  **de-dupe / single-flight** mechanism from `performance-db-cost.md` (External calls, and the
  cache-expiry stampede) applied one layer out — at the client component tree rather than a server
  cache.
- **A fetch already collapsed to one request behind a shared hook/Provider is still issued again by
  an always-mounted consumer that kept its own raw fetch of the same URL.** Once the identity /
  notification / settings endpoint is lifted behind the single Provider/Context or request-deduping
  cache from the bullet above, the call sites that read through it collapse to one request as
  intended — but a consumer that was never folded in (typically a nav badge, shell chrome, or a
  telemetry hook that mounts on **every** route) keeps its **own** `fetch`/`useEffect` against the
  same resource, so one load still issues that request **twice** — once for the folded set, once for
  the outlier — not once (more, if several were left out). This is not the absent-coalesce case
  above: the coalescing boundary **exists and works**; the defect is **partial adoption** — one
  always-on consumer left outside it. That difference is load-bearing for **detection**: the bullet
  above says to grep the *hook's* call sites, but the outlier **does not call the hook** — it holds a
  raw fetch — so a hook-name grep **structurally cannot see it**. Grep the **resource URL/endpoint**,
  not the hook or context name, and reconcile every hit against the shared instance's importers; the
  leftover hit is the outlier. A comment at the shared instance ("lifted this to avoid a double
  fetch") is a cue to **audit for a third consumer**, not proof the dedup is complete. It is the
  exact inverse of the *Strong tell* in the bullet above — there **one** site is specially
  re-engineered while the rest fan out; here the rest are folded in while **one** site is left out —
  same partial-adoption geometry, opposite majority. Two consequences the folded set never exhibits:
  (1) the outlier usually runs its **own polling timer**, so its derived view (an unread-count badge)
  drifts **out of sync** with the shared store until each refreshes on its own schedule — a visible
  **consistency** bug, not just wasted bytes; (2) a test scoped to the shared hook alone asserts a
  single fetch and **passes** while the outlier still double-fetches — the regression test must
  **mount every known consumer together** (nav + shell + a page consumer) and assert one request.
  Fix: migrate the outlier onto the same shared instance — delete its raw fetch and its private poll,
  read the context/cache — so a single fetch and a single refresh loop feed every consumer. Distinct
  from the identity fan-out bullet above by *state*: that **builds** the coalescing boundary and
  switches every call site; this is that boundary already built, with one always-mounted consumer
  never moved onto it.
- **A `<Suspense>` boundary whose subtree never *suspends* has a dead fallback — the
  "loading state" it looks like it adds renders nothing.** A Suspense fallback paints only
  while a descendant actually suspends — throws a promise the boundary catches — which is what
  a `lazy()`/`React.lazy` component (before its chunk arrives), a `use(promise)`/`use(Context)`
  on a still-pending value, a suspense-enabled data library, or an `async` Server Component the
  boundary streams do. **The discriminator is *where the awaiting happens*, not whether the
  child holds data:** the fallback is live when an **unresolved** promise (or the async child
  itself) crosses the boundary and something under it does the waiting; it is dead when the
  slow `await` already ran **above** the boundary, so the value handed in is fully resolved and
  nothing under it can throw. Two common shapes look like they added a loading state and
  didn't: (a) a client component that fetches in a `useEffect` and `setState`s — it mounts and
  renders **synchronously** with its data still `null` (typically a blank or empty-state
  branch), then re-renders when the effect resolves, so the wrapping
  `<Suspense fallback={<Spinner/>}>` shows the child's `null`-data render for the whole wait,
  not the spinner; (b) a child handed only already-resolved plain props because the slow
  `await` ran earlier in the same or a parent async function, before this JSX was built —
  contrast the *live* case, where a parent threads an **unawaited** promise down for the child
  to `use()` and the boundary suspends correctly; the fault is awaiting above the boundary, not
  passing data through it. In neither dead shape is the fallback ever reachable. It hides
  because the JSX visibly contains a fallback and a fast local connection makes the missing
  feedback imperceptible; on a real network the surface is a frozen/blank wait or a false
  empty flash — a frequent, invisible contributor to "the app feels heavy/slow." Fix by
  intent: if the fallback is genuinely wanted, move the data-loading into a mechanism that
  suspends — a `use(promise)` on a promise created **above** the boundary and passed through
  it, a suspense-enabled query hook, or a nested `async` child the boundary streams — and/or
  add the framework's route-level loading convention (a Next.js `loading.tsx` wraps the route
  in a real boundary) when the whole route is the wait; if the fetch legitimately stays
  effect-based, **remove the dead `<Suspense>`** (it is a false sense of a loading state) and
  render an explicit loading branch from the component's own state
  (`if (loading) return <Skeleton/>`), separating not-yet-loaded from genuinely-empty. This is
  the precondition behind curing a blank-screen route by wrapping it in `<Suspense>`: the wrap
  works only once the slow work moves **inside** the boundary — leaving the `await` at the top
  of the render, or resolving the props before the JSX, leaves the fallback dead. Detection:
  for each `<Suspense>`, trace its subtree for a real suspension source (`lazy()`, `use()` on a
  pending value, a suspense-enabled hook, an awaited `async` child) and for any unresolved
  promise crossing the boundary; finding none, flag the fallback as dead, and sweep the broader
  shape — an effect-fetching or resolved-before-render page with a Suspense fallback (or no
  adjacent route-level loading file) that shows no feedback on navigation. **Distinct** from the
  `role="status"`/`aria-busy` loading bullet under Accessibility above (whether a loader that
  *does* render announces itself) — this is whether it renders at all; and from a real,
  explicit `if (loading) return <Skeleton/>` state, which is not this bug. Regression-test on a
  throttled network, or assert the fallback actually mounts — not a fast local load.
- **A cleanup arm shared by two async operations clears a loading flag it doesn't own — a
  sibling or superseded invocation's settle flips off the flag the *current* operation still
  needs.** One loader serves two entry points — `load()` for initial/refresh and `load(cursor)`
  for pagination, each with its own in-flight flag (`loading` vs `loadingMore`) — and the shared
  `.finally(() => { setLoading(false); setLoadingMore(false); })` (or a shared `setBusy(false)`)
  resets **both** unconditionally, so when the pagination call settles it also clears the refresh
  flag while that refresh is still in flight: cross-*path* clobber. The single-flag variant is the
  same defect across *generations* — a search/typeahead path re-issues its request as the query
  changes, both attempts share one `finally` that flips one `loading`, and the **superseded** first
  attempt, resolving last, clears `loading` while the current attempt is still pending:
  cross-*generation* clobber. The unifying rule is that **a cleanup may only clear a flag the
  current, owning invocation set** — (a) violates ownership across paths, (b) across generations,
  and both fix by establishing operation identity before the settle is allowed to clear. **The
  failure is not a cosmetic flip.** The control gated by the wrongly-cleared flag reads "done"
  mid-request — the spinner vanishes over still-loading or stale data, and a re-enabled "load more"
  button (or a refresh listener) fires the path again with a now-shifted cursor; when the original,
  superseded response finally resolves, an append-style reducer (`setItems(cur => [...cur,
  ...page])`) appends rows overlapping what the re-fire already added → **duplicated items**. It
  reproduces **only under overlap** (a refresh landing during pagination, or a query change
  mid-request) **plus out-of-order resolution**, so every single-path test passes. **Detect** by
  finding any loader reachable from two entry points and reading its cleanup: does one
  `.finally`/`setBusy(false)` reset a flag it does not own, or can a stale invocation's settle clear
  a flag a newer one still needs? A single shared cleanup that calls more than one
  `setLoading*(false)`, or a `setLoading(false)` on a path that can run concurrently with itself, is
  the tell. **Fix** in two parts: scope each path's cleanup to the flag it owns (`if (isPagination)
  setLoadingMore(false); else setLoading(false);`), or give each operation its own flag; **and**
  establish **operation identity before the settle** — stamp each request with a monotonic id (or an
  `AbortController`), let only the current id's `finally` clear the flag, and **drop** (never append)
  a response whose id is no longer current. **Regression-test the overlap explicitly**: fire both
  paths, resolve them **out of order**, and assert both the flags *and* the resulting list — a
  single-path test asserts neither the cross-path flag clobber nor the stale append. Distinct from
  the two loading-state bullets nearby: the `role="status"`/`aria-busy` bullet under Accessibility is
  whether a loader that *renders* announces itself, and the dead-`<Suspense>` bullet just above is
  whether the loader *renders at all* — here the loader renders fine and is *cleared by an operation
  that does not own it*. The `AbortController` mechanism, and the discipline that a cancel of a
  superseded request is a **user-cancel, not a swallowed timeout**, live in
  `reliability-error-handling.md` (Timeouts, aborts, retries); the "an older result must not clobber
  current state — gate on a version/id" shape is `billing-correctness.md`'s out-of-order rule
  (compare the provider's version/timestamp) applied one layer out, at a client reducer. Distinct too
  from the fetch-dedup bullets above, which govern *how many* requests fire, not *which* operation's
  flag a shared cleanup clears.
- **A debounced write to the URL/shared state closes over the values it read when the
  timer was *scheduled* — a change made for another reason while the timer is pending is
  reverted when the stale timer fires.** A control that writes the URL/query on a delay (a
  search box that `setTimeout`s a `router.replace`/`push` a few hundred ms after the last
  keystroke, an autosave, a slider that debounces its commit) builds the write's payload
  from the params/state it captured at *schedule* time and holds it in the pending closure.
  Before the timer fires, the same URL/state moves on for an unrelated reason — the user
  clicks a filter chip, a nav writes a param, another control commits — via its own
  *immediate* write. The pending timer then fires with its captured-stale set and re-writes
  the URL from it, silently dropping the concurrent newer write (the filter "un-clicks
  itself," the just-set param vanishes ~300 ms later). It reproduces **only under overlap**
  — a second write landing between a debounced write's schedule and its fire — so every
  single-control test passes; a **per-component copy** of the debounce makes it worse, since
  two controls each keep their own stale snapshot and clobber each other. **Fix — read
  current state at fire time, never replay a captured one:** move the debounce into an effect
  keyed on the changed value whose cleanup cancels the still-pending timer on every re-run
  and on unmount (so the write re-schedules whenever the value changes and no superseded
  timer survives), and build the payload **inside** the timer from the live URL/router state
  (or a functional/merge update — `params => ({ ...currentParams, q })` read at fire time),
  never from a set closed over at schedule time; route every debounced writer through **one
  shared debounced-write hook** so they all funnel through the same current-state read
  instead of each holding a private snapshot. Detection: a `setTimeout`/debounced callback
  that spreads captured params/state into a `router.replace`/`push`/`setState` with **no**
  cleanup clearing the pending timer when its keyed value changes, or a per-component
  debounce copy of a URL write. Regression-test the overlap: schedule the debounced write,
  issue a *different* param's write before it fires, let it fire, and assert the concurrent
  change survives — a single-control test asserts neither write's outcome under overlap.
  Distinct from three neighbours: the shared-`.finally` loading-flag clobber above clears a
  loading **flag** a concurrent operation doesn't own (this reverts a **state/URL value**,
  not a flag); the fetch-dedup bullets above govern **how many** requests fire (this governs
  **which write wins**); and the URL-backed-state bullet above ("Drawer / filter / detail
  state should be URL-backed") is about state that **never reaches the URL** (held only in
  `useState`) — here it *does* reach the URL and a stale timer reverts it. The general concurrent-writer form (two writers racing on one value,
  needing a lock/CAS/version) is `concurrency-shared-state.md`'s read-modify-write rule
  applied at a client debounce.
- **An optimistic write that reverts to a value it captured before the call has no idea a *newer* write
  already committed a different value — on failure it reverts to the stale one and clobbers the newer.**
  An optimistic-update handler (drag-to-reorder, an inline edit, a toggle) writes the new value into
  keyed client state — `state[id] = next`, a map keyed by item id, a single field — **before** the
  persist request resolves; the success path leaves it, the failure path reverts by deleting or resetting
  that key to the value it captured at write time. Correct for a **single** in-flight write, it becomes a
  clobber the moment the same key is written a **second** time before the first settles — a second drag,
  a fast double-click, a keyboard repeat, all ordinary interactions when the trigger has no
  disable-while-pending guard. Sequence: write 1 sets `state[id] = A` and fires a slow request, capturing
  `prev`; before it resolves, write 2 reads the current (already-optimistic) value, sets `state[id] = B`,
  and fires a fast request that **succeeds**, correctly leaving `B`; write 1 then **fails** (or simply
  resolves out of order) and its revert **unconditionally** resets `state[id]` to its captured `prev` (or
  deletes it), clobbering the confirmed `B` and snapping the UI back to a stale or pre-write-1 value —
  usually with a misleading "your change was reverted" attached to a request the user has already
  forgotten. Neither branch checks whether the value it is about to overwrite is still the one **this**
  call wrote. It survives review because each handler reads correctly alone (write, then undo on failure)
  and a single-call unit test — call once, resolve/reject the mock, assert state — always passes; the bug
  lives only in the **interaction** of two calls on one key. **Detection:** for any optimistic handler,
  (1) confirm the trigger can fire a second time on the same key before the first request settles (no
  `disabled`-while-pending, no debounce that would prevent it), and (2) check whether the revert (and,
  for symmetry, the success write) mutates by **bare key** or first checks "is the current value/token
  still the one I wrote" — a captured-value compare, or a monotonic per-key request token where only the
  latest token's continuation may mutate state. Bare key plus a plausible double-trigger is the bug;
  **verify before filing** by tracing the exact two-call mutation sequence and showing the clobber, not
  just "seems racy." **Fix — a per-call identity guard (a client-side compare-and-set):** capture the
  value or a request token when the optimistic write happens, and only mutate in the async continuation
  if the current value/token still matches what this call expects; regression-test two overlapping calls
  on one key with the first failing after the second succeeds, asserting the final state reflects the
  second (successful) call. Distinct from the debounced-write bullet directly above: there the stale
  value is a **schedule-time snapshot** a debounce timer replays on its own (successful) late fire, fixed
  by reading current state at fire time; here it is a **pre-write value** reset on an out-of-order
  mutation's **failure** path, fixed by a per-call token — both are a stale write clobbering a concurrent
  newer one, different trigger and fix. Distinct too from `product-ux-quality.md`'s reverted-optimistic-
  write bullet, which governs which **mapper** the revert's error *message* passes through (a user-facing
  string leak) — this governs whether the revert's **state write** still owns the key (a data-correctness
  race); same handler, orthogonal defects. The general concurrent-writer form (a lock/CAS/version on one
  shared value) is `concurrency-shared-state.md`'s read-modify-write rule, here applied to keyed
  **client** state on the optimistic-revert path.
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
- **A lazily-mounted container can't reach backwards into its props — an eagerly-evaluated
  expensive prop runs for every panel, including the ones never shown.** A container that mounts
  its children conditionally — a `Tabs` that renders only the active panel, a `{isOpen &&
  <Panel/>}`, a virtualized/windowed region — skips the *render* of the branches it doesn't show,
  but **not the evaluation of the props it was handed**: a prop expression is an ordinary function
  argument, so the parent computes it **before** the element tree ever reaches the container that
  decides what to mount. Hand such a container an array of pre-built panels —
  `<Tabs panels={[{label, content: renderHeavyChart(a)}, {content: renderHeavyChart(b)}, …]} />`,
  `<Modal body={buildBigTree(data)} />`, `<Panel rows={expensiveTransform(rows)} />` — and every
  chart/tree/transform is computed up front even though only one panel is ever opened; the
  container's mount-only-the-active-child discipline saves nothing. **The discriminator that
  separates the bug from a false positive is call-vs-descriptor:** a bare JSX *element* in prop
  position (`content: <HeavyChart data={raw}/>`) is a cheap `createElement` descriptor — nothing
  heavy runs until the container mounts it, so it is **not** this bug; the bug is a **function
  call** evaluated in prop position (`content: renderHeavyChart(raw)`) or an element whose **inner
  prop is computed on the spot** (`<HeavyChart rows={buildSeries(raw)} />` — the element is cheap
  but `buildSeries` runs now). Flag the call/allocation, not every element passed as a prop, and
  gate on real dataset scale and a real, frequent trigger — over-flagging a correct-looking shape
  at small *n* erodes trust in the finding. **Memoization does not fix this, and reaching for it
  is the tell that the axis was misread:** `useMemo(() => renderHeavyChart(raw), [raw])` still
  executes for **all** N panels on the first render — a memo caches a value across *re-renders*,
  it never skips the *never-opened* branch. The lever is *when* the work is invoked, not *how
  often* it recomputes. Fix: move the work to the point of mount so the container runs it only for
  the panel it actually shows — pass a thunk / render-prop / `children` / a component reference the
  container invokes on mount (`content: () => renderHeavyChart(raw)` rendered as
  `tabs[active].content()`), or hand the panel its raw inputs and let the mounted component do its
  own derivation. Detect: an expensive call or allocation (or an array of them) written as a prop
  value to a component that conditionally/lazily renders that prop; confirm by counting the
  expensive work's invocations while opening panels — acceptance is that the count equals the
  panels actually **opened** (a never-opened tab = zero, a first-time tab switch = exactly one),
  not the number defined. Distinct from the three memoization bullets above by *axis*: those are
  re-render cost — the work reruns because a child lacks `React.memo`, a view-model is unmemoized,
  or an inline literal is referentially unstable, and memoization is the cure; here the
  container's laziness is real and the prop may be perfectly stable, yet the work still runs for
  branches that never mount, so only relocating the invocation helps. And distinct from the
  heavy-optional-library-import bullet below: that is a **bytes** leak — a statically imported lib
  shipped to routes that never open the gate — cured by deferring the **import**; this is a **CPU
  / allocation** cost executed at render for unseen branches, cured by relocating the
  **invocation**.
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
- **A barrel re-export, or a pure export co-located with a heavy import, ships that heavy
  code even when the imported symbol never touches it.** Kin to the dataset-leak bullet
  above, but the tree-shaking failure comes from the **file/module boundary itself**, not
  from the helper depending on the data. Two shapes: (a) a *barrel* — an `index.ts`
  re-exporting many sibling modules — where `import { x } from '../shared'` drags the
  top-level side-effecting imports of *every* re-exported sibling (a chart lib, a compiled
  JSON, an analytics client) into the chunk, because the bundler resolves the barrel as one
  module; (b) a single module that side-effect-imports a large blob (`import DATA from
  './compiled.json'`) at its top level *and also* exports genuinely pure, blob-independent
  values — a static label map, a bare string constant, a pure formatter — where importing one
  of those pure symbols still pulls the whole file, blob included. The reason is **module-level
  granularity**: a bundler drops unused *modules*, not unused *properties of a module it must
  keep*, so any live (value, not `import type`) binding taken from the module keeps the entire
  file — and keeps it *conservatively* unless the first-party package/module is marked
  `"sideEffects": false`, the flag that lets the bundler prove the unused parts are safe to
  drop. This is exactly where the "bundle split and tree-shaken" checklist item above reads
  green but is silently false. **Partial credit does not exist here.** Once the one symbol that
  genuinely reads the blob is moved server-side and its resolved value prop-threaded (the
  dataset-leak bullet's fix), it is tempting to call the file clear — but if the same client
  component, or any sibling in the route's client graph, still imports even one pure constant
  from that blob-backed module (or via the same barrel), the module is still reachable and
  still pulled in whole, so the saving is zero: either *every* runtime import into the client
  graph is gone or the full blob ships. Detect by walking each client entry point's
  **transitive** runtime import graph (strip `import type` first — a component can ship the
  blob by rendering a child that imports it, without naming it itself) for any edge into the
  blob-backed module or the barrel; for each edge, read the *actual definition* of the imported
  symbol in that module's source — a pure literal, or a value that reads the parsed blob? —
  never infer it from a comment or the import line. Confirm in the bundler's analyzer: does the
  produced chunk carry a byte-size outlier or a string fragment that could only be there if the
  blob is embedded? A "this file imports only pure things" review is not proof until the built
  artifact is checked. Fix: import the **specific submodule path** (`../shared/labels`) instead
  of the barrel; **split** the blob-backed module so the pure exports live in a sibling that
  imports the blob *nowhere* in its own file or its transitive imports, and have the blob-backed
  module re-export them from that free sibling (single source of truth kept for its legitimate
  server callers) while every client importer points at the free module; mark a genuinely
  side-effect-free package `"sideEffects": false`; and keep large static data out of any module
  that also exports hot small utilities. Guard it with a **source-level reachability check** — a
  small import-graph walk (not a runtime bundle-size assertion, which may be unavailable where
  tests run) that fails when any client-side module reaches the blob-backed module — run as a
  *shrink-only allowlist* so new offenders fail loudly while known ones stay visible debt. That
  check is necessary but **not sufficient alone**: its module/symbol list goes stale, so
  acceptance pairs it with the built-artifact check above. Distinct from the dataset-leak bullet
  above by **whether the imported symbol depends on the blob**: there the helper closes over a
  singleton derived from the whole dataset, so the data is a genuine dependency and the fix is
  architectural (structural-parameter form); here the imported symbol is genuinely independent
  and only the file boundary or barrel edge binds them, so a mechanical split / submodule-path
  import / `sideEffects` flag severs it outright. Distinct from the heavy-optional-library
  bullet above too: that library is needed only behind an interaction gate and deferring the
  *import* fixes it; here the pure symbol is typically needed unconditionally (first paint), so
  deferral alone leaves the blob riding in beside it — the blob must be severed from the pure
  export, not lazy-loaded with it.

## Security & compatibility

- Output encoding for anything user-influenced (XSS — see `security-appsec.md`
  A05); a strict Content-Security-Policy (directive-level form below).
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
- **A "strict" CSP is a specific, enforceable `script-src` — not just a header being present.**
  OWASP's Strict CSP form is `script-src 'nonce-{RANDOM}' 'strict-dynamic'` (or
  `'sha256-{HASHED_INLINE_SCRIPT}' 'strict-dynamic'` when nonces aren't feasible), plus
  `object-src 'none'` and `base-uri 'none'` — never a bare `'unsafe-inline'`, which lets any
  inline script run (including an attacker's) and defeats the whole point: a strict policy exists
  to "protect against classical stored, reflected, and some of the DOM XSS attacks" (OWASP
  *Content Security Policy Cheat Sheet*). The nonce must be fresh and unguessable **per HTTP
  response**, wired through an actual templating layer — a hardcoded or reused nonce is
  equivalent to publishing it, and a middleware that mechanically stamps `nonce="…"` onto every
  `<script>` tag it finds in already-assembled HTML hands the same nonce to an attacker-injected
  `<script>` too (the cheat sheet's own warning: "attacker-injected scripts will then get the
  nonces as well"). Backstops CWE-79 — Cross-site Scripting, rank #1 in the CWE Top 25
  (`security-appsec.md` already cites it).
- **Trusted Types as a DOM-XSS backstop on top of output encoding, not instead of it.** The
  `require-trusted-types-for 'script'` CSP directive forces DOM injection sinks (`innerHTML`,
  `eval`, `script.src`) to take policy-created typed values, turning a raw-string sink into a
  `TypeError` — a browser-enforced backstop (MDN *Trusted Types API*: Baseline 2026; a tinyfill keeps older browsers from throwing
  but enforces nothing there), layered on the output-encoding rule above.
- **DOM Clobbering: HTML-injection-only, no script execution needed — the neighbor to Trusted
  Types above.** Named `id`/`name` attributes on ordinary elements (`<form id="config">`, `<a
  name="url">`) are auto-exposed as properties on `window`/`document`; a sanitizer that only
  strips script-based XSS lets that markup through untouched, so an attacker's element can shadow
  whatever global the app relies on (OWASP *DOM Clobbering Prevention Cheat Sheet*, worked
  example: injecting `<a id=config><a id=config name=url href='malicious.js'>` against code
  reading `window.config.url`, "to load additional JavaScript code, and obtain arbitrary
  client-side code execution"). DOMPurify's default config only guards built-ins — app-defined
  names need `SANITIZE_NAMED_PROPS: true` (namespaces `id`/`name` with a `user-content-` prefix);
  on the Sanitizer API, set `blockAttributes` on `id`/`name` (its default does not stop this). CSP
  doesn't close the gap either — it can stop a clobbered *script source* from loading new
  attacker JS, but not clobbering used inside code already present (e.g., an `eval()` argument).
  Fix both ends: sanitize named props, and type-check (`instanceof`) any bare
  `window.*`/`document.getElementById(...)` read before trusting it as configuration or a
  callback — a clobbered global is a real `Element`, not the object the code expects. Distinct
  from this skill's other "clobber" hits (concurrent writers racing on shared state, e.g.
  `concurrency-shared-state.md`) — this is a same-origin HTML-injection attack, no race involved.
  Applies wherever user HTML is sanitized and rendered: CMS body text, markdown renderers,
  comment systems.
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
`role`/`tabindex`; a `<div>`/`<span>` **with** `tabIndex={0}`/`tabindex="0"` +
`onKeyDown` but no `role` and no `aria-label`/`aria-labelledby` (focusable and
key-operable yet roleless and nameless — the operable mirror of the previous
tell); `role="button"` on a non-focusable element; images with no
`alt`; `<input>` with no associated `<label>`; `outline: none` with no
replacement focus style; hardcoded `#hex` text colors to spot-check contrast;
`localStorage.setItem('token'`; API keys in `NEXT_PUBLIC_`/`VITE_`/`REACT_APP_`
env names; `addEventListener('message'` with no `event.origin` check; a `<script>`/`<link>` to a
third-party origin with no `integrity=`; a weakened `Referrer-Policy` (`unsafe-url`); no
`frame-ancestors`/`X-Frame-Options` on a page with authenticated or state-changing actions; a
small lookup helper imported from a shared module that also builds a derived singleton over
an entire large dataset (walk the client import graph, stripping type-only imports, for an
edge into that module); a loading/skeleton component with `aria-busy` and/or a label prop but
no `role="status"`/`role="alert"`/`aria-live` on it or an ancestor; bespoke skeleton/shimmer
markup (a `className` containing `skeleton`/`shimmer`/`animate-pulse`, or repeated placeholder block
`<div>`s) in a component that imports **no** shared loader although an accessible one exists elsewhere
(a hand-rolled copy that both duplicates and stays silent — list the shared loader's importers and
diff); a `<Suspense fallback={…}>`
whose subtree loads data only via `useEffect`+`setState` or receives already-resolved props, with
no `lazy()`/`use()`/suspense-enabled hook and no unresolved promise crossing it (the fallback is
dead); an identity/singleton-read hook (`useUser`/`useSession`/`useCurrentUser`) that `fetch`es in
a `useEffect`/on first render with no shared Provider/Context or dedup cache, called from many
components (each mount fires its own request — grep the call sites, count global-shell consumers) —
or, when that shared Provider/cache **already exists**, one always-mounted consumer (nav/badge/shell)
still fetching the same endpoint **directly** via a raw `fetch` of the resource URL rather than the
hook, so one load fetches it twice and the outlier's own poll drifts its derived badge out of sync
(grep the **URL**, not the hook name — the outlier never calls the hook);
a static `aria-label` that
doesn't contain the element's own visible text (WCAG 2.5.3); an icon/label swap keyed off an
`open`/`expanded` boolean with no matching `aria-expanded` on the same control; a
`Content-Security-Policy` header/meta containing `unsafe-inline` with no `nonce`/hash, or missing
`object-src`/`base-uri`; a sanitizer call (`DOMPurify.sanitize`/`new Sanitizer(`) with no
`SANITIZE_NAMED_PROPS`/`blockAttributes` configured, rendering user HTML, alongside a bare
`window.*` global or a `getElementById`/`getElementsByName` result trusted with no type check; a
`setTimeout`/debounced callback that spreads params/state captured at *schedule* time into a
`router.replace`/`push`/`setState` with no cleanup clearing the pending timer when its keyed value
changes (a concurrent newer write is reverted when the stale timer fires), or a per-component copy
of a debounced URL write.
