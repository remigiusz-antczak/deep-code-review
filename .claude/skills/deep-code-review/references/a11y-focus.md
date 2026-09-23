# Accessibility depth — keyboard & focus (custom widgets, overlays, focus management)

Read this when the target or diff builds a custom interactive widget (dialog, tablist, combobox, listbox, menu, disclosure, slider, tree), a popover / dropdown / flyout / hand-rolled modal overlay, a control that disables itself while an action is pending, a keyboard-scrollable container, a styled focus indicator, a document-level focus / scroll-into-view correction handler, or an off-canvas, collapsed, or visually hidden region that holds focusable content (WCAG 2.1.1, 2.4.3, 2.4.7, 2.4.11, 2.4.13, 1.4.11). Split from `frontend-a11y.md`, whose base WCAG 2.2 AA checklist applies to every UI review.

## Keyboard & focus — depth

- **A custom interactive widget is built to its ARIA Authoring Practices (APG) pattern.** Each widget class
  (dialog, tablist, combobox, listbox, menu, disclosure, slider, tree) has a prescribed role +
  states/properties + a **full keyboard map** — e.g. dialog: `Esc` + focus trap; tablist: `Arrow` / `Home` /
  `End`, with only the active tab in the tab order (roving tabindex); combobox: `Arrow` + `Enter` + `Esc`.
  "Tab reaches it" is not "operable": the finding is a **custom widget missing its pattern's keys or states**
  (a `role="tablist"` with no arrow-key navigation, a `role="dialog"` with no `Esc`, a control with no
  `aria-expanded`/`aria-selected` reflecting its state). Prefer a native element first (rule in `frontend-a11y.md`); reach for
  the APG only when you build the widget yourself.
- **A disclosure toggle that swaps its `aria-label` text or icon between "Expand"/"Collapse" still needs
  `aria-expanded` on the same control — the label communicates what will happen, not the current state.** The
  APG-conformance point above already names a missing `aria-expanded`/`aria-selected` as an example of a
  widget shipped without its pattern's states; this is the single most common concrete shape it takes. A
  hand-rolled expand/collapse row (tree row, accordion header, filter section) commonly swaps its icon
  (`name={open ? 'chevron-down' : 'chevron-right'}`) and its `aria-label` text (`(open ? 'Collapse' :
  'Expand') + title`) on click and stops there — a screen reader landing fresh on the button hears a sensible
  "Expand" or "Collapse," so a first-read smoke test and a sighted click-through both look correct. But that
  swapped text is the accessible NAME, not the `aria-expanded` STATE the ARIA disclosure pattern requires on
  the same control: assistive tech reporting state changes rather than re-announcing the full name on every
  interaction never gets one, and neither does any tooling asserting on state directly (axe, Testing Library's
  `getByRole(..., {expanded})`), which won't recognize the row as a disclosure widget at all. Per MDN,
  `aria-expanded` "is applied to th[e] focusable, interactive control that toggles the visibility of the
  object," normally paired with `aria-controls` naming which element it toggles — both belong on the same
  button whose label/icon already swap. Detection: grep the icon/label-swap tell above, then check whether the
  same button also carries `aria-expanded={open}`; on a codebase with several tree/list/accordion rows, diff
  them against each other — most carrying `aria-expanded` and one not is strong evidence of an overlooked
  component, not deliberate omission, worth flagging as a reuse smell alongside the correctness bug (a single
  shared `<DisclosureButton>` primitive makes the gap structurally impossible to reintroduce). Regression
  test: assert `aria-expanded` flips per click via `getByRole('button', {expanded: false|true})`, not only
  that the content becomes visible in the DOM.
- **A focus indicator must clear the contrast floor, not merely *change*.** "Visible" is a numeric bar: the
  indicator's colour must reach **>=3:1** against what it sits on — WCAG **1.4.11 Non-text Contrast** (AA)
  requires 3:1 for "visual information required to identify user interface components and states," and
  **2.4.13 Focus Appearance** (AAA) requires **both** the indicator's **area** be at least that of a **2 CSS
  px thick perimeter** of the **unfocused** component (or sub-component) **and** a **>=3:1** contrast "between
  the same pixels in the focused and unfocused states" — a thin 1px ring clearing the contrast floor still
  fails the area prong. An automated focus check capturing computed style, calling `.focus()`, and flagging
  only when *nothing changed* validates the **wrong property** — a change from transparent to a
  real-but-too-faint colour is a passing diff and a failing product. Resolve the **actual rendered colours**
  on both sides and compute the ratio (the way a text-contrast check does) — except an **unmodified
  user-agent-default** focus style, which 1.4.11 **exempts** from the floor (2.4.7 still requires it
  *visible*); scope the detector to **author-styled** indicators. Beware a **narrow-purpose token** (e.g. a
  ring meant for a dark filled button) reused as a component's focus colour on a light surface — its
  doc-comment's intended context is unenforced, so grep its **call sites**, not its comment; the fix is
  usually just removing the override so the correct global `:focus-visible` default wins.
- **Restore-focus-to-the-trigger is not modal-only — it applies to every dismissible overlay.** A popover,
  dropdown/select menu, combobox listbox, flyout, or click-triggered tooltip the user can dismiss (Escape,
  outside click, selection) must return focus to the element that opened it, same as a modal's close does;
  skip it and focus falls to `<body>` on dismiss, dumping a keyboard user back at the top of the page with no
  sense of where they were. The tell: a bare boolean open/close state plus an Escape/outside-click handler
  with no captured trigger ref and no `.focus()` call back onto it. Contrast: a design-system overlay
  primitive that captures the trigger ref on open and calls `.focus()` on it in its close path has the correct
  shape.
- **A control that self-disables *while it holds focus* drops the keyboard user to `<body>` — the
  `disabled={pending}` / `disabled={isSubmitting}` submit recipe is the common shape.** The native HTML
  `disabled` attribute removes an element from the focus and tab order, so applying it to the element that
  **currently holds focus** — a submit/action button the user activated with `Enter`/`Space`, which then sets
  `disabled` for the in-flight request — moves focus to `<body>` (the document default), with nothing
  restoring it: the keyboard user is dumped to the top of the page mid-task, no announcement, no way back to
  where they were. It ships: a sighted mouse user sees only the button grey out while the request runs (their
  focus was never tracked there), the JSX is the textbook "disable to prevent double-submit" pattern, and a
  keyboard smoke test that `Tab`s to the button and presses `Enter` rarely checks *where focus lands after*; a
  render test asserts the button is `disabled`, not `document.activeElement`. This is a **WCAG 2.4.3 Focus
  Order** (Level A) break — the same "focus silently falls to `<body>`" failure the async-outcome bullet
  (`a11y-live.md`) and the scroll-container bullet below name, reached by a third trigger. Fix:
  at or **before** the disable, move focus to a sensible target — a `role="status"` result/toast region (which
  also *announces* the outcome), the next logical control, or a results region — so focus is placed, not
  dropped; **or** keep the element focusable by driving the busy state with `aria-disabled="true"` plus a
  **guarded handler** (an early-`return` in `onClick`/`onKeyDown` while pending) instead of the native
  `disabled` attribute, so focus stays put and the tab order is unbroken (`aria-disabled` doesn't block
  activation on its own — the handler must). **Distinct** from three neighbours: the async-outcome bullet
  fires when the control is **removed from the DOM** and replaced by a message, recommending "keep it mounted,
  disabled and relabelled" as the *safe* alternative — this bullet is the correction that even that in-place
  disable drops focus when the control holds it, so the disable must itself be paired with a focus move, and
  it fires **mid-request** (`pending`), not at the resolved outcome; the scroll-container bullet below shares
  the exact mechanism — stripping focusability from the focused element bounces focus to `<body>` — but by a
  different trigger (a `tabIndex` recompute vs a submit); and the dismissible-overlay restore bullet above
  *restores* focus to a trigger on **dismiss**, whereas here nothing is dismissed — the control disables
  itself in place. Regression test: drive the pending state and assert `document.activeElement !==
  document.body` immediately after the control disables (and, for the `aria-disabled` variant, that the
  guarded handler is a no-op while pending).
- **A non-modal popup — a combobox listbox, select menu, autocomplete, or dropdown — must also close when
  focus *leaves* it, a dismiss path separate from Escape and outside-click and the one a roving-tabindex /
  `aria-activedescendant` design most often omits.** Such a widget has *three* independent dismiss code paths,
  wired in three different places: **Escape** (a `keydown` handler), **outside pointer** (a document
  `pointerdown`/`click` listener that closes when the target is outside the trigger + popup), and **focus
  leaving the widget** (a `focusout`/`blur` handler, or `Tab` intercepted in the `keydown`). The first two are
  the ones every implementation reaches for, so a keyboard-Escape check and a click-away check both pass and a
  reviewer signs off "dismissal handled" — yet moving focus out of the widget with the keyboard fires **no**
  pointer event (the outside-click listener never runs) and is **not** the Escape key (that handler never
  runs), so a popup wired only for those two is left **open and orphaned**: it floats over the page while
  focus sits on some later control, a WCAG **2.4.3 Focus Order** break in which the reader's focus and the one
  visible interactive overlay are in different places. The **roving-tabindex / `aria-activedescendant`**
  design guarantees the exposure: the WAI-ARIA APG *Combobox Pattern* keeps the combobox a **single** tab stop
  and states that "the popup, and the popup descendants are excluded from the page `Tab` sequence" (verified
  this session; the pattern's only listed popup-dismiss key is Escape), so a `Tab`/`Shift+Tab` out of the
  widget necessarily lands focus on the next page control with nothing inside the popup to catch it — the
  stuck-open popup is structural, not incidental. A keyboard-only smoke test that opens, arrows, and Escapes
  never presses `Tab` **while the popup is open**, so it never sees it. Fix: add the focus-exit dismiss — a
  `focusout` on the widget container that closes when `relatedTarget` falls outside the trigger + popup
  subtree (or handle `Tab`/`Shift+Tab` in the `keydown` before focus moves) — then let focus land naturally on
  the next control (a non-modal popup must **not** trap; see the inverse below). Detection: a
  listbox/menu/combobox with an Escape `keydown` and a document outside-click listener but **no**
  `onBlur`/`focusout` on the container and no `Tab` branch in the `keydown`; confirm live by opening the popup
  and tabbing out — it must close. **Distinct** from three neighbours: the dismissible-overlay focus-restore
  bullet above is the *restore* half (return focus to the trigger *once dismissed*, listing the dismiss
  triggers as Escape/outside-click/selection) — this is a dismiss trigger that list omits, and it must fire
  *before* any restore can; the combobox APG-pattern bullet above prescribes the whole keyboard map
  (Arrow/Enter/Escape) — this isolates the one dismiss path a widget with a correct Escape still routinely
  lacks, the way the disclosure-`aria-expanded` bullet isolates that bullet's most-omitted state; and the
  hand-rolled-`aria-modal` bullet below is a **modal** that must *trap* focus so `Tab` wraps **inside** — a
  non-modal popup is the inverse (Tab moves **out** and closes it), so trapping one is as wrong as failing to
  dismiss the other. Regression test: render the widget open, move focus to a control outside it, and assert
  the popup is gone (`queryByRole('listbox')` is null), not only that Escape closes it.
- **Hidden interactive content leaves the tab order — no "phantom focus."** A closed off-canvas menu,
  collapsed accordion, inactive tab panel, or CSS-hidden dropdown must remove its focusable descendants from
  the tab sequence (`inert`, conditional unmount, or `tabindex="-1"` on each). And `aria-hidden="true"` must
  **never** sit on a container with a focusable child (the **4th rule of ARIA**: don't put `aria-hidden` or
  `role="presentation"` on a focusable element) — otherwise a keyboard user tabs into an element a screen
  reader can't announce, the mirror of the open-dialog focus-trap rule in `frontend-a11y.md`. Detector: tab through every collapsed
  / closed region and confirm focus never lands in it.
- **A hand-rolled full-screen overlay that copies a dialog's ARIA (`role="dialog"`/`"alertdialog"` +
  `aria-modal="true"`) but skips the app's shared modal / focus-trap / background-`inert` helper asserts a
  modality it never delivers.** `aria-modal="true"` is not a label AT reads back — it's an *instruction* AT
  acts on: it tells a screen reader to stop exposing everything outside the dialog and confine the user to its
  subtree. The ARIA APG modal-dialog pattern is explicit that you may set it *only* when the code actually
  prevents interaction with the background **and** the styling obscures it, because on some AT it removes the
  rest of the page from perception. So an interstitial, error gate, or "you must do X first" blocker rendered
  as a raw sibling of the app tree with the right role and attribute but **none** of the behavior — focus
  never moves into it on open, `Tab` from its last control escapes to the page behind it, the background is
  never `inert`/`aria-hidden`, focus is never restored on close — is *worse* than one carrying no `aria-modal`
  at all: a keyboard/AT user is sent into background the attribute swore was gone, so it actively misdirects
  rather than merely under-serving. It ships: it looks right — covers the viewport and carries the correct
  role, so a visual pass and an "is it mounted?" render test both approve — and it's usually the newest
  surface, landing after the hardening pass that fixed every other overlay. **Root cause and fix are the #838
  bypass fault (the hand-rolled-skeleton-vs-shared-loader bullet, `a11y-live.md`), with a modal-specific payload:**
  reuse, don't patch — render the surface through the ONE shared overlay primitive, or native `<dialog>`
  opened with `.showModal()` so the modal behavior comes from the platform rather than hand-rolled app code;
  either way the containment reaches this surface for the reason that bullet gives. Only if a bespoke overlay
  is genuinely unavoidable, have it call the same focus-move-in, focus-trap, background-`inert`, and
  restore-on-close helpers — bolting the attribute on without them isn't the fix. Detection **inverts** that
  sweep: grep every `aria-modal="true"` / `role="dialog"` / `role="alertdialog"` and diff the set against the
  importers of the shared modal/focus-trap helper — each hit that neither renders *through* the primitive nor
  calls the helpers is a Focus Order defect (2.4.3). **Distinct** from three neighbours: the
  dismissible-overlay focus-restore bullet above is only the *close* half (return focus to the trigger) and
  presupposes the open dialog was already trapped — this is the *open + while-open* half it assumes; the
  phantom-focus bullet above marks *hidden* subtrees `inert` to keep focus out, where here `inert` belongs on
  the *visible background under an open dialog* (its inverse); and the "modal open/close (trap + restore)"
  line in `frontend-a11y.md` states the rule, where this is the failure mode where the rule is skipped but the attribute is
  asserted anyway. Regression-test the behavior, not the mount: on open `document.activeElement` is inside the
  dialog; `Tab` from the last focusable wraps within it and never reaches a background control; the background
  is `inert`/`aria-hidden`; `Escape`/close returns focus to the opener — an "is it mounted?" assertion catches
  none of it.
- **A scroll container made keyboard-scrollable with a static `tabIndex={0}` stays a focus stop on the screens
  where its content fits and nothing scrolls — gate the focusability on a live overflow measurement, not a
  constant prop.** A region that scrolls only by wheel/touch has no keyboard equivalent, so making its wrapper
  focusable (`tabIndex={0}`, often with `role="region"`/`"group"`) is the correct, expected fix: it lets
  arrow/`PageDown`/`Home`/`End` scroll it, and an automated scan flags a scrollable region that can't take
  focus (axe's `scrollable-region-focusable` — the WCAG 2.1.1 Keyboard concern). The bug is applying it
  **unconditionally**. At widths where the content sits inside the box with room to spare — often the common
  case — the wrapper is still in the tab order with nothing to scroll: a focus target that moves nothing and,
  if named, announces itself for no reason. Repeat it once per list row/card and it compounds into many dead
  stops that stretch keyboard traversal (2.4.3 Focus Order) on exactly the views built to scan fastest, while
  a keyboard-only smoke test still "passes" — focus lands and the ring shows; only the *purpose* is missing,
  which a shape/keyboard pass never checks. Fix: derive `tabIndex` (and any `role` added *solely* to explain
  that focusability) from a live `ResizeObserver` comparing `scrollWidth > clientWidth` (or `scrollHeight >
  clientHeight`) — the same comparison the clip/truncation check asserts (`testing-ui.md`) — so the
  wrapper is a tab stop only while it can actually scroll; recompute on mount/resize, **not while the element
  holds focus**, since stripping `tabIndex` from the focused element bounces focus to `<body>`, a worse Focus
  Order break than the dead stop. When it *is* focusable it still needs a role and an accessible name so AT
  can say why it's a stop (the *role first, then name* bullet, `a11y-aria.md`); a genuinely-named landmark region keeps
  its role regardless — the target is the no-op stop, not focusability itself. Detector:
  `tabIndex={0}`/`tabindex="0"` on an `overflow-auto`/`overflow-x-auto`/`overflow-scroll` wrapper with **no
  `onKeyDown`/`onKeyPress`** in the component and no condition tying the prop to a measured overflow; a strong
  secondary tell is the same file already gating a *different* attribute on an overflow/clip measure (a title
  tooltip shown only when the text is actually clipped) — the technique is known, just not applied here.
  Distinct from two neighbours: the phantom-focus bullet above removes focus from *hidden* content (here the
  region is visible, just not overflowing), and the roving-tabindex bullet's (`a11y-aria.md`) wrapper is *operable* but
  roleless/nameless (here the wrapper is not operable at all — nothing to operate).
- A **global focus/scroll-into-view correction** handler (the *Focus Not Obscured* remedy) must yield to an
  open overlay and scope to the focused element's own scroll container — detector below.

### Global focus-correction vs. an open overlay

A **document-level focus/scroll-into-view correction** handler — the common remedy for *Focus Not Obscured*
(nudge the scroll so a focused control clears sticky chrome) — must **bail while an overlay is open** (gate on
the open-dialog state, the `:modal` element / `aria-modal`, or a focus-trap boundary) and **scope its scroll
to the focused element's own scroll container**, never a page-level one. A global handler missing both guards
fires for a control *inside* an open modal/drawer, measures it against the **background** chrome, and scrolls
the background out from under the overlay — the a11y remedy for one rule silently breaks
`product-ux-quality.md`'s rule that a detail drawer overlays so "the user keeps their place", never moving the
background. Container scoping is the more general fix (it also covers any nested scroll region).

**🚩 grep**: a `document`/`window`-level `focusin`/`focus` listener or a `scrollIntoView`/`scrollTo`/`scrollBy`
correction with no open-overlay guard and no scroll-container scoping; exercise it — focus a field inside an
open overlay and confirm the background does not move.
