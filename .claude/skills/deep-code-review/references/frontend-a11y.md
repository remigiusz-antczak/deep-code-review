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
- One `<h1>` per page/view; headings describe structure, not styling.
- Landmarks present; a skip-to-content link for keyboard users.

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
- **Accessible Authentication**: no cognitive-function test (e.g. solving a
  puzzle, transcribing) with no alternative; allow paste into password/OTP.

**Perceivable**
- Contrast: text ≥ 4.5:1 (large text ≥ 3:1); UI components & graphical objects
  ≥ 3:1 (1.4.11). Don't convey meaning by color alone.
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
  budget. (Chrome Lighthouse, *critical request chains*.)
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
`frame-ancestors`/`X-Frame-Options` on a page with authenticated or state-changing actions.
