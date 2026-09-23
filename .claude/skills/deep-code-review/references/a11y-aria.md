# Accessibility depth — structure & semantics (roles, names, landmarks, hierarchy)

Read this when the target or diff builds a control on a non-semantic element (`<div>`/`<span>`), sets or computes `role` / `aria-label` / `aria-labelledby` / `aria-describedby`, wraps a control in a tooltip helper, renders a dismissible chip or a multi-select trigger, or ships landmarks, headings, a skip link, or a tree/nav hierarchy (WCAG 1.3.1, 2.4.1, 2.4.6, 2.5.3, 4.1.2). Split from `frontend-a11y.md`, whose base WCAG 2.2 AA checklist applies to every UI review.

## Structure & semantics — depth

- **An element made interactive with `tabIndex={0}` + `onKeyDown`/`onClick` on a non-semantic tag
  (`<div>`/`<span>`), but given no `role` and no accessible name, has a control's *behaviour* without a
  control's *identity*.** It's focusable and keyboard-activatable — a keyboard-only pass "works" and a
  reviewer signs off — yet with no `role` it keeps its implicit ARIA **`generic`** mapping ("A nameless
  container element that has no semantic meaning on its own", WAI-ARIA 1.2), so assistive tech is told no
  role; with no `aria-label`/`aria-labelledby`/own text it also has no accessible name. An AT user can focus
  and press it but is never told what it is — the textbook **WCAG 4.1.2 Name, Role, Value** gap (name *and*
  role must be programmatically determinable). Classic shape: a shared **roving-tabindex** hook
  (Gmail/Linear-style `j`/`k` list navigation) spreading `tabIndex`/`onFocus`/`onKeyDown` onto each list
  item's wrapper `<div>`, Enter activating it, never setting a role or name. Distinct from three neighbours:
  (1) the `<div onClick>` **with no keyboard handling and no `role`/`tabindex`** in the closing 🚩 grep of `frontend-a11y.md` is a
  *lockout* — not operable at all; this one *is* operable and degrades gracefully (wrapped links/buttons stay
  tab-reachable), why it slips past a keyboard smoke test. (2) the non-labelable-host bullet below *has* a
  role and lacks only a name; here **both** are absent, and `tabIndex`/`onKeyDown` is what makes the JSX look
  finished. (3) the custom-combobox required-state (`a11y-forms.md`) and loading-skeleton (`a11y-live.md`) bullets concern a *state* or
  *transition* reaching the tree; this is whether role and name exist at all. Fix in order — **role first,
  then name**: prefer the native semantic element (`<button>`/`<a>` — first rule of ARIA, `frontend-a11y.md`); or set the
  `role` the behaviour implies (`button`/`option`/`tab`/`link`) **and then** a computed accessible name — an
  `aria-label` bolted onto a still-`generic` `<div>` is *no* fix: no role exists for the name to attach to
  (the `generic`-role aside under the colour-alone chip bullet, `a11y-color-motion.md`). For a roving **composite** widget the
  role goes on **both** container and items — the container role (`listbox`/`menu`/`grid`/`tablist`) makes the
  item roles valid (the APG keyboard bullet under Keyboard & focus, `a11y-focus.md`); where a single activate-role
  misrepresents rich row content, use `role="group"` + `aria-roledescription` + a computed name.
  Detection/test: the wrapper's **computed role is not `generic`** and it has a **non-empty accessible name
  distinct from its verbatim concatenated contents**, read from the accessibility tree (devtools/axe), not the
  DOM — a keyboard-only pass proves operability, never identity.
- **A custom control built on a *non-labelable* element is not named by a wrapping `<label>` — name it
  explicitly and verify the computed name.** HTML `<label>` only names **labelable** elements (`<input>`,
  `<button>`, `<select>`, `<textarea>`, `<meter>`, `<output>`, `<progress>`, and form-associated custom
  elements). A widget built on a **`<div>` or `<span>`** given an ARIA role (`<div role="checkbox">`, `<span
  role="button">`) isn't in that set, so a wrapping (or adjacent) `<label>`'s text isn't taken as its
  accessible name — and if the element has no text of its own (its visible content is an `aria-hidden` glyph),
  it announces with **no name** ("checkbox, not checked" instead of "Accept terms, checkbox, not checked").
  The JSX can look plausibly labeled, so a shape-based review misses it. (Adding a `role` to a *labelable*
  element — `<button role="switch">`, `<input type="checkbox" role="switch">` — doesn't lose the label; the
  WAI-ARIA APG recommends exactly that as the robust switch. The fault is the non-labelable **host element**,
  not the role override.) Fix: name the control explicitly with `aria-labelledby` (referencing the visible
  label's id) or `aria-label`, and **verify the platform-computed accessible name** in the accessibility tree
  (devtools / axe), not the DOM — the same computed-name harvest the cross-view-consistency check in `frontend-a11y.md`
  performs.
- **A wrapper deliberately left roleless to dodge the nested-interactive anti-pattern still needs a name — and
  a bare `<div>`'s implicit `generic` role cannot carry one, so its `aria-label` is silently discarded.** A
  list row made keyboard-operable by hand (`tabIndex={0}` plus `onClick`/`onKeyDown`) sometimes also wraps
  genuinely interactive descendants — a `<details>/<summary>` disclosure, a nested `<a>` — and HTML's content
  model already forbids exactly that nesting for a native control (the `<a>` element's content model: "there
  must be no interactive content descendant, `a` element descendant, or descendant with the `tabindex`
  attribute specified," HTML Standard). An author who knows an ARIA `role="button"`/`role="link"` on the row
  would reproduce the same interactive-in-interactive hazard for assistive tech deliberately withholds the
  role — and, still wanting the row announced, adds an explicit `aria-label` to the now-roleless `<div>`. That
  reads as finished (focusable, key-operable, visibly labeled in the JSX) but per WAI-ARIA 1.2 §5.2.8.6,
  `generic` — the implicit role of a `<div>`/`<span>` carrying no other semantics — is one of the roles with
  **Name Prohibited**: "Authors MUST NOT use the `aria-label` or `aria-labelledby` attributes to name the
  element" (confirmed on MDN's `generic`-role reference: "`aria-labelledby` and `aria-label` attributes are
  prohibited"). The browser's accessible-name computation **discards** the label outright, leaving the row
  with role `generic` and no name — WCAG **4.1.2 Name, Role, Value**. It ships: every surface a reviewer
  actually checks looks right — the JSX carries an `aria-label`, an outerHTML dump shows the attribute
  present, a keyboard smoke test finds the row focusable and its nested link/`<summary>` still works — only
  the accessibility tree (where the attribute never surfaces) shows the gap. **Distinct from the
  roving-tabindex bullet above**, whose premise is that no name was ever attempted (role and name both simply
  forgotten) — here a name is deliberately authored and still lost, for a spec reason, not forgetfulness.
  **Distinct from the non-labelable-host bullet above**, whose failure is an *indirect* path — a wrapping
  `<label>` not transferring to a non-labelable role'd host — fixed by adding a *direct* `aria-label`; here
  the host carries **no role at all**, so the very direct `aria-label` that bullet prescribes is exactly what
  `generic` throws away. Fix: don't resolve nested-interactive by dropping to `generic` plus `aria-label` —
  restructure so the row's primary action is a real, singly-interactive control (a `<button>`/`<a>`) with the
  genuinely-interactive descendants living outside its content model, the native-compliant shape; or, where
  the row's compound content is what makes a single activate-role wrong, reach for the `role="group"` +
  `aria-roledescription` + computed-name technique already named above for a rich composite row (`group` is
  not in the Name Prohibited set, so `aria-label` reaches it) — but a plain `role="group"` carries no
  activation semantics of its own, so this still means the descendants, not the group wrapper, own any
  keyboard activation; or drop `aria-label` entirely and name the row from a visible heading/`aria-labelledby`
  referencing on-screen text. Detection: grep a hand-rolled interactive row (`tabIndex={0}` +
  `onKeyDown`/`onClick` on a `<div>`/`<span>`) that also carries a static or computed `aria-label` and **no**
  `role`, then read the row's **computed accessible name** in the accessibility tree (devtools/axe) — present
  in the DOM, absent from the tree, is the tell; a JSX/DOM read alone always looks fixed. Regression test:
  assert `getByRole` resolves the row under some **non-generic** role with a non-empty accessible name — not
  merely that the `aria-label` prop was passed.
- **An `aria-label` rewritten to add context must still contain the visible text it labels (WCAG 2.5.3 Label
  in Name, Level A).** SC 2.5.3 requires that "for user interface components with labels that include text or
  images of text, the name contains the text that is presented visually" — so a button showing "Export SVG"
  given `aria-label="Export the report as a PDF file (summary only)"` fails the SC the instant the rewrite
  drops the original words, even though the new label is *more* descriptive, not less. The break is invisible
  to a normal screen-reader smoke test (some reasonable name is still announced) and invisible visually (the
  short visible text on screen is unchanged) — it only surfaces for speech-input/voice-control users, who
  match a spoken command ("click Export SVG") against the accessible name and get no match once the visible
  words are gone, exactly the population a manual pass tends to skip. Detection (source-only): for every
  interactive element with both visible text content and a static `aria-label`, check case-insensitively
  whether the visible text appears as a contiguous substring of the `aria-label`; flag any label whose
  *opening* words differ from the visible text, since the usual break is the visible text surviving only as a
  caveat embedded mid-sentence rather than the label's opening words. Fix: default to no `aria-label` when the
  visible text is already a reasonable name, putting extra context in a `title`/tooltip or adjacent sr-only
  text instead; where one is genuinely needed, lead with the visible text verbatim and append the extra
  context after it (`"<visible text> — <extra context>"`) — the SC's own note gives the same best practice,
  that the label's text belongs at the start of the name. Distinct from the accessible-name-*sourcing* bullet
  above (whether a name exists, and from where) and from Consistent Identification in `frontend-a11y.md` (whether the same
  destination gets the same name across routes): this is whether a name that already exists still contains
  what's on screen.
- **A multi-select/dropdown trigger whose visible text and `aria-label` are two independently-computed
  expressions can agree on every "something selected" branch and still drift apart on the one branch nobody
  tests: empty/placeholder.** A multi-select or combobox trigger typically renders its visible summary from
  the current selection (`"Books, Movies"`, `"3 selected"`, or a placeholder such as `"Select categories…"`
  when nothing is chosen) and separately computes an `aria-label` for context (`"Category filter: Books,
  Movies"`). When something is selected, both expressions derive from the same selection array/count, so they
  naturally agree — a reviewer who opens the dropdown, picks an option, and checks the label sees them agree
  and moves on. The empty branch is where they stop sharing a source: the visible placeholder is one
  hand-written literal ("Select categories…") and the `aria-label`'s empty-state text is a second,
  independently hand-written literal ("Category filter" or "No categories selected") — authored at a different
  time, sometimes by a later PR updating only the placeholder copy — so the accessible name for that one
  branch doesn't contain the on-screen placeholder text at all: WCAG **2.5.3 Label in Name** (Level A) fails,
  but only in the branch that's empty by definition and therefore the one QA or a screenshot review is least
  likely to exercise (testers routinely select something first to "see it work," exactly the branch where the
  drift is invisible). **Distinct from the static Label-in-Name bullet above**, whose failure is a *single,
  permanently-wrong* literal — one author rewrote a name and dropped the original words, reproducible on every
  render, caught by a one-shot substring check against "the" visible text; here the visible text and the label
  are each *themselves* branch-dependent, agree on most branches by construction, and only one under-tested
  branch carries the drift — the same *things-that-must-stay-in-sync-and-didn't* shape as the sibling-copy
  guard-parity family (`testing-and-evals.md`), but at the granularity of **branches inside one component's
  two parallel expressions**, not **N separate call sites**. Detection: don't stop at a single substring check
  — enumerate every branch the trigger's state machine defines (empty, one selected, many selected, all
  selected) and, for **each**, check whether that branch's computed accessible name contains that same
  branch's computed visible text; audit the empty/placeholder branch first, not last, since it's the one a
  populated-dropdown-only manual pass never reaches. Fix: stop hand-authoring the label as a second, parallel
  string — derive the accessible name from the same expression that already produces the visible text
  (appending extra context after it, per the fix above), so there's one source of truth per branch instead of
  two texts kept in sync by hand; if the empty state genuinely needs different wording, include the real
  placeholder text verbatim inside it. Regression test: assert, for the **empty** render specifically (not
  only a "something-selected" fixture), that the computed accessible name contains the visible placeholder
  text — the branch most existing test suites never construct.
- **A dismissible chip/tag button whose accessible name is only the *value* it represents states no *action* —
  a screen-reader user hears the current filter, never that the control removes it.** The common filter/token
  chip renders as `<button>{label} ×</button>` (a visible label plus a trailing `×` multiplication-sign
  glyph), and its accessible name computes from that visible content to the **value** — `"Category: Books ×"`
  — so assistive tech announces the filter that's *set*, with no hint the button's *purpose* is to clear it;
  the trailing `×` is a decorative glyph with **no reliable spoken equivalent** (announced as "times", as its
  Unicode name, or skipped, depending on AT and verbosity). That fails **WCAG 2.4.6 Headings and Labels** (AA
  — a label must describe the control's *purpose*, and "Category: Books" describes the value, not "remove this
  filter") and leans on **4.1.2 Name, Role, Value**. It ships: a name *does* exist and even reads as
  descriptive, so a presence check (`if (!accessibleName)`), a first-read screen-reader pass, and a sighted
  click-through (the `×` reads as "remove" to the eye) all approve. Fix: give the button an `aria-label`
  stating the **action and its target** — `aria-label="Remove filter: Category Books"` — and mark the `×`
  `aria-hidden="true"` so it isn't announced. **Distinct** from the Label-in-Name (2.5.3) bullet above, whose
  polarity is opposite — there a rewritten `aria-label` wrongly *drops* the visible text; here the visible
  text *is* the whole name and is insufficient because it names the value, not the action — and the two
  combine: the action label you add must still **contain the visible target text** (lead with the action, keep
  "Category: Books" in the string) so the fix doesn't itself break 2.5.3. Distinct too from the
  roving-tabindex and non-labelable-host bullets above, where a name is **absent or unsourced**; here a name
  is present with a **valid role**, and only the *action semantics* are missing. Detection (source-only): an
  interactive dismiss/remove/clear control whose only accessible name is its subject label plus a bare glyph
  (`×`/`✕`/`⨯`), with no `aria-label` naming the action; test that the computed name contains the action verb,
  not only the subject.
- **A Tooltip/description helper that wires `aria-describedby` onto the one child it is handed assumes that
  child *is* the focusable control; a call site that wraps the real control breaks the association silently.**
  The common React idiom clones the single child and merges the description link (`aria-describedby` pointing
  at the tip's id) plus the hover/focus handlers onto it — correct for a bare `<Tooltip><button/></Tooltip>`,
  where the link lands on the button and a screen reader reads the tip on focus. But nothing constrains the
  child to be the control: a caller who wraps it for layout or positioning
  (`<Tooltip><span><button/></span></Tooltip>`), interposes a non-focusable wrapper as the disabled-control
  workaround (a native `disabled` control fires no hover/focus events, so the reveal handlers have to sit on
  the wrapper), or passes a `forwardRef`/styled wrapper, lands the description on the wrapper; a **fragment**
  child, or a child component that doesn't forward the prop, drops it entirely. In the layout and `forwardRef`
  cases the inner `<button>` still receives focus but now carries no accessible description, so a
  screen-reader user focusing it hears no tip. The disabled-control case is worse: a native `disabled`
  `<button>` is not focusable and not in the tab order at all, so the description is unreachable wherever it
  sits — surfacing the "why is this inert" explanation the tooltip exists to give means making the control
  `aria-disabled` (which keeps it focusable) *and* routing the description onto that focusable control, not
  the wrapper. The tip still renders on hover and keyboard focus (handlers sit on the wrapper, focus events
  bubble to it), so a sighted click-through and any pixel/visual-regression snapshot pass — only the
  accessibility tree shows the focused control's description is empty. This is the failure mode of the
  Label-in-Name bullet's own advice above — move extra context into a `title`/tooltip — when that tooltip is a
  clone-onto-child one, and it *extends* the name-sourcing bullets above (there a **name** is unsourced or
  drops its visible text; here a **description** reaches the wrong node). Distinct from four neighbours: the
  roving-tabindex bullet above spreads props onto a wrapper that leaves *role and name* absent (here role and
  name are fine, only the description is misrouted); the required-state combobox bullet (`a11y-forms.md`) is a
  *state* that never reaches the control; the loading-skeleton bullet (`a11y-live.md`) is a *transition* never announced;
  and the dismissible-overlay focus-restore bullet (`a11y-focus.md`) is about *restoring focus on
  dismiss*, not wiring the description at all. Fix — target the control, not the element passed in: document
  and **dev-time-assert** that the child is the single host element that takes focus (`React.Children.only`
  catches multi-child input, plus a check that the child is a focusable host node, not a fragment or a
  component that swallows the prop); or expose the generated id through a ref / render-prop / anchor API so
  the wrapper can keep the handlers while the description is placed on the focusable descendant (an anchor-ref
  API that resolves the actual control is the robust shape). Detection/test: assert the **computed accessible
  description of the focused control** from the accessibility tree (devtools/axe), not the presence of the
  `role="tooltip"` node in the DOM or a screenshot — the same computed-property harvest the name bullets above
  rely on.
- **Correct ARIA landmarks satisfy the automated *bypass-blocks* check yet leave a sighted keyboard-only user
  with no way past a long repeated nav — that still needs a real skip link.** WCAG **2.4.1 Bypass Blocks**
  (Level A — "a mechanism is available to bypass blocks of content that are repeated on multiple web pages")
  is met by any *one* of its sufficient techniques, independent options: **ARIA11** (landmark regions), **G1**
  (a link at the top to the main content), or **H69** (headings at each section). So a page shipping correct
  `banner`/`nav`/`main` landmarks meets the SC on ARIA11 alone, and the automated rule mapping to it (axe-core
  `bypass`, Lighthouse *bypass blocks* — each accepts a region *or* a skip link *or* a heading) goes green.
  That green check reads as "bypass handled," so the skip link is dropped as redundant — but a landmark is a
  **screen-reader** navigation affordance (rotor / region jump); a user navigating by **keyboard alone with no
  screen reader running** can't perceive or jump to a landmark, so they must `Tab` through every nav item on
  every page to reach content. The tool can't see this because the SC genuinely *is* satisfied; only a manual
  keyboard-only pass (`Tab` from the top, no SR) exposes the traversal. Fix: add a genuine skip link — an
  in-page anchor to the `#main` / main-landmark id, placed as the **first focusable element** in the DOM and
  **visually hidden until it receives focus** (the `sr-only`-until-`:focus` pattern, so it doesn't alter the
  visible design but appears for the keyboard user); point it at a focusable/labelled main region so
  activating it *moves focus*, not just the scroll position. **Distinct** from the terse "Landmarks present; a
  skip-to-content link" checklist line in `frontend-a11y.md` — this is *why* both are listed and not interchangeable: a green
  bypass-blocks check on landmarks alone is a false signal that the skip link is optional. And distinct from
  the unnamed-`<section>` bullet below, where a region is **missing from the landmark tree** (a defect *in*
  the landmarks) — here the landmarks are **correct and complete** and still insufficient for the non-SR
  keyboard user. Detection: never infer 2.4.1 conformance from an automated pass; run a keyboard-only pass and
  confirm the first `Tab` reaches a skip control that moves focus into main.
- **An unnamed `<section>` is not a poorly-labeled landmark — it is not a landmark at all.** By the HTML/ARIA
  host-language mapping, `<section>` exposes to assistive tech as the ARIA `region` landmark only when it
  carries an accessible name (`aria-label`, `aria-labelledby`, or, as a fallback, `title`); with none, it maps
  to no landmark role and is absent from landmark/rotor navigation — a screen-reader user scanning by region
  skips straight past it. The bug hides well: sibling sections built from the same component (one instance
  passed a name prop, another not) render identically, so nothing on screen reveals the gap. Detection: pull
  the page's landmark/rotor list, not the DOM, and confirm every `<section>` you expect as a region actually
  appears in it.
- **A tree/nav whose parent-child depth is drawn only with left-padding and a colour accent shows the
  hierarchy to the eye but hides it from the accessibility tree.** A sidebar, file explorer, or nav tree
  rendered as a **flat `<ul>` of sibling `<li>` rows**, all at the same DOM depth, with the level expressed by
  an incremental `padding-left` step per depth plus a colour-matched accent, carries the hierarchy in
  **presentation only**. Assistive tech reads the accessibility tree, not the pixels: a flat list of siblings
  announces every row at the same level with no parent/child containment, so a screen-reader user hears "list,
  N items" with no sense of depth, which row owns which, or where a subtree begins and ends — indentation has
  no programmatic equivalent, and the colour accent is unspoken (and invisible in greyscale / forced-colours).
  This is **WCAG 1.3.1 Info and Relationships** (Level A) — "information, structure, and relationships
  conveyed through presentation can be programmatically determined or are available in text," whose
  Understanding page gives *indented list items* as the canonical example — with the colour accent
  additionally leaning on **1.4.1 Use of Color** (Level A). It ships: the indentation makes the hierarchy
  unmistakable *visually*, so a sighted review and any screenshot / visual-regression pass approve, and the
  rows may each carry a correct label and correct `aria-expanded` on the collapsible ones — a per-row check
  looks complete when the gap is the **relationship between rows**, which no single-row inspection sees. Fix:
  expose the hierarchy in the tree, not in padding + colour — either **real nested lists** (each child `<ul>`
  inside its parent `<li>`, so containment is structural) or the **ARIA tree pattern** (`role="tree"` on the
  container, `role="treeitem"` on rows, `aria-level` for depth, `aria-setsize`/`aria-posinset` for position,
  `aria-expanded` on parents, and `aria-owns` to wire parent→children when the DOM can't physically nest
  them); keep the indentation and accent as visual reinforcement, never the sole carrier. **Distinct** from
  three neighbours: the disclosure-`aria-expanded` bullet under Keyboard & focus (`a11y-focus.md`) is a per-row **open/close
  *state*** — a tree can carry correct `aria-expanded` on every parent and still leave the **level /
  containment *relationship*** invisible if it's a flat `<ul>` with padding; the APG custom-widget bullet
  there names `tree` as a widget class needing its full pattern — this is the concrete flat-list-plus-padding
  shape of that class's *structural* half, as the disclosure bullet is its `aria-expanded` half; and the
  two-state colour-only chip and direction-badge bullets under Perceivable (`a11y-color-motion.md`) are a **binary state** carried by
  colour or a glyph on one element, where here the missing thing is a **multi-level structural relationship
  across rows** whose primary carrier is indentation (1.3.1), colour only secondary. Detection/test: read the
  accessibility tree (devtools / axe), not the DOM padding — assert rows expose their level/containment
  (`getByRole('treeitem', { level })`, or a genuine nested-list structure); a flat `<ul>` whose only depth
  signal is a `style`/`className` padding step per level, with no `aria-level` / nested `<ul>` /
  `role="tree"`, is the tell.
