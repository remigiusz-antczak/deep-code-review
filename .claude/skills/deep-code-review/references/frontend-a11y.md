# Frontend, UI/UX & accessibility review

Read this when the target renders UI (web, mobile web, component library, or a server-rendered view). Expands
section P of `SKILL.md` — the **a11y-correctness half**; `product-ux-quality.md` is the companion **design
half** (whether the UI feels *at-home*: data states, encoding, the metric delta, self-evidence). Target **WCAG
2.2 level AA** (W3C Recommendation, 2024-12-12); note AAA items where a flow is high-stakes.

---

## Respect the existing design (read first)

Accessibility and usability findings improve the product — they must not silently redesign it. Two rules:

1. **Separate defects from redesigns.** A contrast failure, a missing label, a keyboard trap, or an unlabeled
   icon button is a **defect** — fix it in place, minimally, preserving the existing look. A change that
   alters layout, spacing system, component structure, typography scale, or brand is a **redesign** — that is
   an owner decision, not a review fix.
2. **Prompt before heavy design change.** If the smallest correct accessibility/usability fix would visibly
   and substantially change the existing design, do **not** impose it. Surface it under "Decisions needed
   (owner)" and ask: is there a design system / style guide the fix should conform to, or is the current UI a
   prototype that can be freely improved? Proceed only on the answer. Offer the minimal-visual-impact option
   first.

This keeps the review net-positive on every axis — it raises accessibility without regressing a deliberate
design.

---

## Accessibility — WCAG 2.2 AA, how to check

Every UI review walks the base checklist under each heading below — that is the floor. Each family's depth lives in a routed sub-file; load one only when its trigger matches the target or the diff:

| Load | When the target or diff … |
|---|---|
| `a11y-aria.md` | builds a control on a `<div>`/`<span>`; sets or computes `role`, `aria-label`, `aria-labelledby`, or `aria-describedby`; wraps a control in a tooltip helper; renders a dismissible chip or a multi-select trigger; or ships landmarks, a skip link, or a tree/nav hierarchy (SC 1.3.1, 2.4.1, 2.4.6, 2.5.3, 4.1.2) |
| `a11y-live.md` | renders a loading / skeleton / spinner region, shared or hand-rolled, or an async success / error message that replaces the control that triggered it (SC 4.1.3) |
| `a11y-focus.md` | builds a custom widget (dialog, tablist, combobox, listbox, menu, disclosure, slider, tree), a popover / dropdown / modal overlay, a control that disables itself while pending, a keyboard-scrollable container, a styled focus ring, or a global focus / scroll-correction handler (SC 2.1.1, 2.4.3, 2.4.7, 2.4.11, 2.4.13, 1.4.11) |
| `a11y-color-motion.md` | encodes a state or direction by colour, a chip, or an arrow glyph; pins a sub-AA "decorative" colour token; animates anything (JS animation, smooth scroll, carousel); or enforces a session time limit or auto-updating content (SC 1.1.1, 1.4.1, 1.4.3, 2.2.1, 2.2.2, 2.3.3) |
| `a11y-forms.md` | renders form fields through a shared `Field` wrapper, or a custom (non-native) select or combobox that can be required (SC 3.3.2, 4.1.2) |

### Structure & semantics
- Native semantic elements (`<button>`, `<a href>`, `<nav>`, `<main>`, `<h1..h6>` in order, `<label>`,
  `<table>` with headers) before ARIA. ARIA only to fill gaps; a wrong `role` is worse than none. First rule
  of ARIA: use a native element if one exists.
- One `<h1>` per page/view; headings describe structure, not styling.
- Landmarks present; a skip-to-content link for keyboard users.

### Keyboard & focus (WCAG 2.1.1, 2.4.3, 2.4.7, and 2.2's 2.4.11)
- Everything actionable is reachable and operable by keyboard alone; logical tab order; no keyboard trap.
- Visible focus indicator; focus is **not obscured** by sticky headers/toolbars (2.2 new: Focus Not Obscured).
- Focus is managed on route change, modal open/close (trap + restore), and async content insertion.

### New in WCAG 2.2 — verify explicitly
- **Target Size (Minimum) 24×24 CSS px** for pointer targets (SC 2.5.8, AA) — but **five exceptions**, so
  don't over-flag: **Spacing** (a 24 CSS px diameter circle centred on each undersized target intersects
  neither another target nor another undersized target's circle — so two adjacent small icons still fail when
  their *circles* overlap), **Equivalent** (another control does the same function at full size), **Inline**
  (a target within a sentence, or sized by the line-height of non-target text), **user-agent-controlled**, and
  **essential**. An undersized target that meets an exception isn't a finding.
- **Dragging Movements**: any drag action has a single-pointer alternative.
- **Consistent Help**: repeated help mechanisms (contact details, a contact mechanism, self-help, an
  automated/chatbot channel) appear in the same **relative order** in the content across pages (SC 3.2.6,
  Level A) — the criterion is *order in the content sequence*, not pixel location.
- **Redundant Entry**: don't force re-entering info already provided in a flow.
- **Accessible Authentication** (SC 3.3.8, AA): an auth step must not require a **cognitive-function test**
  (recall a password, solve a puzzle, transcribe a code) unless it offers an **alternative** method or a
  **mechanism** to complete it — chiefly **password-manager support**: allow **paste** into password/OTP
  fields, set the right `autocomplete` tokens (`current-password` / `new-password` / `one-time-code`), and
  don't intercept clipboard events (the other two allowed exceptions are object-recognition and user-provided
  personal-content tests). **SC 3.3.9 (Enhanced, AAA)** drops the object-recognition and personal-content
  exceptions — so an image CAPTCHA passes 3.3.8 but **fails 3.3.9**; hold high-stakes auth (banking, health)
  to it.

### Perceivable
- Contrast: text ≥ 4.5:1 (large text ≥ 3:1); UI components & graphical objects ≥ 3:1 (1.4.11). Don't convey
  meaning by color alone.
- All non-text content has a text alternative; decorative images `alt=""`.
- Content reflows to 320 CSS px wide without loss (1.4.10); works at 200% zoom.
- Respect `prefers-reduced-motion`; no content flashes > 3×/sec. A CSS `@media (prefers-reduced-motion:
  reduce)` override does **not** reach a JS-driven animation (a `requestAnimationFrame` loop, an autoplaying
  motion library, a scroll/parallax handler) — the JS path must itself consult
  `matchMedia('(prefers-reduced-motion: reduce)')`. Vestibular-safety best practice; for the
  **interaction-triggered** subset (scroll/parallax, hover/click transitions) this is WCAG **2.3.3 Animation
  from Interactions** (AAA — SC 2.2.2 governs the *automatically* started case instead).

### Forms
- Every input has a programmatic label; errors are announced (not color-only), identified, and described;
  instructions are not placeholder-only.
- Autocomplete tokens on personal-data fields (1.3.5).

**Verify with tools + manual**: automated scanners (axe, Lighthouse, pa11y) detect some classes of WCAG
failures, not all; assert no percentage without a cited source. Always add a manual keyboard-only pass and a
screen-reader smoke test (VoiceOver/NVDA). Report the method used; don't claim conformance from an automated
score alone.

---

## Usability & functional suitability

- The intended user's primary task completes with minimal friction; no dead ends. Empty, loading, error, and
  offline states exist and are helpful.
- Destructive actions are confirmable/undoable; nothing irreversible on a single mis-click.
- Copy is clear; errors say what happened and how to fix it.
- **One control, one role.** A visual control that must behave two ways — a navigation link (`aria-current`
  marks the current location) versus a local-state toggle (`aria-pressed`/expanded marks state) — cannot be
  **one component with two mutually-exclusive prop modes**: the mode that isn't wired emits the wrong role,
  focus, and keyboard semantics. Share the **styling** in one primitive and wrap it in two thin behavior
  components (the unification pattern: `migration-parity.md`).

## Cross-view consistency (multi-route apps)

Per-route auditing cannot see inconsistency **between** routes — every page passes on its own. On a
multi-route UI, collect once and diff:

1. **Harvest** the platform-computed accessible name + role of every interactive element (accessibility
   snapshot / `getByRole(...)`, **never** an `innerText` proxy — see principle 2), plus headings and
   empty-state sentences, per route.
2. **Same action, two labels** — group by destination (`href`/handler/resulting route); more than one distinct
   name in a group is a defect, not a nit: WCAG 2.2 **3.2.4 Consistent Identification** (Level AA). Consistent
   Help (3.2.6) is the sibling for help/contact placement.
3. **Malformed names** — flag a name visually two lines but one token (missing separator, `"<name><Kind>"`), a
   bare icon glyph, an ellipsis truncation, or a name duplicating its own text. **Presence checks (`if
   (!name)`) catch none of these**; the usual root cause is one shared component concatenating sibling text
   nodes — fix it once in the design system.
4. **Empty-state phrasing** — one voice and one next action per class of emptiness; N different "nothing here
   yet" sentences is a design-system drift finding.

Report as **one systemic finding** naming the shared component, instances listed (principle 6) — not one per
route. Severity by consequence: a same-action-two-labels group on a primary flow is Medium–High; phrasing
drift is Low.

> **Read the name from the platform, not the DOM text.** A gate that computes
> accessible names from `innerText`/`textContent` (collapsing or inserting
> whitespace) reports a *different* string than the browser's accessibility tree —
> a permanently-green gate (principle 2). Contrast has the mirror trap the other
> way: WCAG 2.2 SC 1.4.3 **exempts** inactive/disabled controls ("a disabled
> control in HTML"), so a gate flagging them is stricter than the standard —
> narrow it, don't weaken the real check (SKILL.md Phase 1, gate-vs-standard).

## Drawer / filter / detail state should be URL-backed

Whatever a drawer, filter, or detail view represents should be bound to the URL
(`searchParams`/`router.query`/equivalent), not held only in component memory (`useState`). State living only
in memory silently resets on refresh, Back, or a shared link — the user reopens the exact page and lands on
the bare list, because the open item's id was never anywhere but memory. This is distinct from *whether* a
detail view should overlay vs. navigate (a product-intent call for `product-ux-quality.md`'s drawers-overlay
rule); this is about the state **surviving** navigation once the surface exists, and it's mechanically
checkable: does the component holding the open/selected/filter state also read and write the URL, and does the
state actually survive a reload.

**🚩 grep**: a drawer/detail/filter component whose expanded or selected id lives only in `useState`/component
memory, with no corresponding `useSearchParams`/`router.query` read or write nearby. Confirm live: open the
state, reload the page, verify it survives.

## Server/client boundary — a plain value proxied across it

In a framework with a server/client split (React Server Components / the Next.js App Router being the common
case), a module marked client-only (`"use client"`) can still export **plain, non-component values** — a
string of utility classes, a config object, a lookup table. When a **Server Component** imports one of those,
the framework doesn't hand it the value: it substitutes a **client-reference proxy** (a stub for a client
export). Used as data on the server — concatenated into a `className`, spread into props — the proxy does
**not** reliably throw; it yields a **broken-but-not-crashing** result (an unstyled element, an empty string,
a control with no padding) reading as a *styling* bug, not a boundary bug.

**Every static gate misses it.** The export's type is correct → **typecheck passes**. No lint rule → **lint
passes**. Unit tests import the module in a plain (non-RSC) context where the value *is* the real value →
**unit tests pass**, often asserting the exact string proxied away at render. It's visible only by rendering
the real route through a real server/client split (a browser against a production-like server).

- **Static check (cheap, mechanical, lint-rule-shaped):** enumerate client-boundary modules, list their
  **plain non-component / non-hook exports**, and flag any imported by a module **lacking** the client
  directive. The fix is always the same: move shared plain values into a **boundary-neutral** module (no
  directive) both sides import — a client module should export only components/hooks across the boundary,
  never plain data.
- **Debugging heuristic:** an element present and correctly structured but **unstyled** (missing
  padding/gap/color the source clearly specifies) on a server-rendered route, with the styling defined in or
  re-exported from a client module — suspect the **boundary** before the CSS. The proxy's stringified form in
  the DOM (a function body / thrown-error text where a class string belongs) is the tell.
- **Completion bar:** "types + unit green" is **not** evidence a shared surface renders across the boundary —
  the rendered output must be exercised in the real split before "done" (the framework-boundary proxy in
  `report-format.md`, "Beware the proxy").

## Reliability & performance (Core Web Vitals)

- **LCP** (loading) ≤ 2.5 s, **INP** (interactivity — replaced FID in 2024) ≤ 200 ms, **CLS** (visual
  stability) ≤ 0.1 at the 75th percentile. That **p75 is a field measurement** (CrUX / RUM / PageSpeed field
  data) — a green Lighthouse or a single CI lab run is a lab snapshot, not the field p75, so "Lighthouse
  passed" is **not** "meets Core Web Vitals" (the same lab-vs-field caveat this file already applies to
  automated a11y scanners; state which was measured).
- No layout shift on the critical render path (reserve space for images/embeds — and for late-injected chrome
  like a consent banner or promo bar); no long tasks blocking input (a synchronous third-party script — tag
  manager, chat/ads widget — is the usual cause); images sized/lazy-loaded; fonts with `font-display: swap`;
  bundle split and tree-shaken; ship less JS — and hold JS / image / font byte-weight to a **committed budget
  a CI check fails on** when it regresses, the same size-ratchet discipline as `skill-authoring-and-size.md`
  (never a silently-raised ceiling).
- Degrades under slow/failed network; no infinite spinners.

Depth, loaded on trigger: `web-fetch.md` when a view fetches data (request waterfalls, a shared hook fetched once per consumer, a partly adopted shared fetch, `<Suspense>` boundaries, shared loading flags, debounced URL writes, optimistic reverts); `web-render.md` when the diff touches list rendering, `React.memo` / `useMemo` / `useCallback`, a lazily mounted container, a heavy optional library, a shared static-data module, or a barrel re-export (re-render cost and client-bundle weight).

## Security & compatibility

- Output encoding for anything user-influenced (XSS — see `security-appsec.md` A05); a strict
  Content-Security-Policy (directive-level form below).
- **No secrets/API keys/tokens in the client bundle or source maps** — anything shipped to the browser is
  public.
- No sensitive data in `localStorage`/`sessionStorage`; tokens in httpOnly+Secure+SameSite cookies where
  possible.
- **A `message` listener validates `event.origin` (and the message shape) before trusting `event.data`.** Any
  origin can `postMessage` to a window, so a handler reading `event.data` with no allow-list check on
  `event.origin` is an origin-validation flaw (CWE-346); a trusted sender can still relay a malformed payload,
  so validate the message syntax too (MDN *Window.postMessage*: "always verify the sender's identity using the
  `origin` and possibly `source` properties").
- **Third-party / CDN `<script>` and `<link>` carry Subresource Integrity.** An `integrity="sha384-…"` hash
  plus `crossorigin` lets the browser refuse a resource a compromised CDN has altered — without it, one CDN
  compromise rewrites what every user's browser executes (MDN *Subresource Integrity*).
- **A "strict" CSP is a specific, enforceable `script-src` — not just a header being present.** OWASP's Strict
  CSP form: `script-src 'nonce-{RANDOM}' 'strict-dynamic'` (or `'sha256-{HASHED_INLINE_SCRIPT}'
  'strict-dynamic'` when nonces aren't feasible), plus `object-src 'none'` and `base-uri 'none'` — never a
  bare `'unsafe-inline'`, which lets any inline script run (including an attacker's), defeating the point: a
  strict policy exists to "protect against classical stored, reflected, and some of the DOM XSS attacks"
  (OWASP *Content Security Policy Cheat Sheet*). The nonce must be fresh and unguessable **per HTTP
  response**, wired through an actual templating layer — a hardcoded or reused nonce is equivalent to
  publishing it, and a middleware that mechanically stamps `nonce="…"` onto every `<script>` tag in
  already-assembled HTML hands the same nonce to an attacker-injected `<script>` too (the cheat sheet's own
  warning: "attacker-injected scripts will then get the nonces as well"). Backstops CWE-79 — Cross-site
  Scripting, rank #1 in the CWE Top 25 (`security-appsec.md` already cites it).
- **Trusted Types as a DOM-XSS backstop on top of output encoding, not instead of it.** The
  `require-trusted-types-for 'script'` CSP directive forces DOM injection sinks (`innerHTML`, `eval`,
  `script.src`) to take policy-created typed values, turning a raw-string sink into a `TypeError` — a
  browser-enforced backstop (MDN *Trusted Types API*: Baseline 2026; a tinyfill keeps older browsers from
  throwing but enforces nothing there), layered on the output-encoding rule above.
- **DOM Clobbering: HTML-injection-only, no script execution needed — the neighbor to Trusted Types above.**
  Named `id`/`name` attributes on ordinary elements (`<form id="config">`, `<a name="url">`) auto-expose as
  properties on `window`/`document`; a sanitizer stripping only script-based XSS lets that markup through, so
  an attacker's element can shadow whatever global the app relies on (OWASP *DOM Clobbering Prevention Cheat
  Sheet*, worked example: injecting `<a id=config><a id=config name=url href='malicious.js'>` against code
  reading `window.config.url`, "to load additional JavaScript code, and obtain arbitrary client-side code
  execution"). DOMPurify's default config only guards built-ins — app-defined names need
  `SANITIZE_NAMED_PROPS: true` (namespaces `id`/`name` with a `user-content-` prefix); on the Sanitizer API,
  set `blockAttributes` on `id`/`name` (its default doesn't stop this). CSP doesn't close the gap either — it
  can stop a clobbered *script source* from loading new attacker JS, but not clobbering used inside code
  already present (e.g., an `eval()` argument). Fix both ends: sanitize named props, and type-check
  (`instanceof`) any bare `window.*`/`document.getElementById(...)` read before trusting it as configuration
  or a callback — a clobbered global is a real `Element`, not the object the code expects. Distinct from this
  skill's other "clobber" hits (concurrent writers racing on shared state, e.g. `concurrency-shared-state.md`)
  — this is a same-origin HTML-injection attack, no race involved. Applies wherever user HTML is sanitized and
  rendered: CMS body text, markdown renderers, comment systems.
- **`Referrer-Policy` does not leak a token-bearing URL cross-origin.** The `Referer` header sends the full
  URL (path + query) to other origins; the modern default is already `strict-origin-when-cross-origin` (MDN
  *Referrer-Policy*), so the finding is a **weakened** policy (`unsafe-url`, `no-referrer-when-downgrade`) —
  or secrets/ids placed in a URL at all, which then ride the `Referer` to a third party (prefer keeping them
  out of the URL).
- **Clickjacking is a named threat, not just a header in a list.** Every page rendering an authenticated or
  state-changing action confirms `frame-ancestors` (CSP) — or legacy `X-Frame-Options` — restricts who may
  frame it; an unset framing policy lets an attacker overlay it in a transparent iframe (`security-appsec.md`
  A02 lists the header among misconfig; this is the threat and the per-page verification).
- Works across the project's target browsers/devices; responsive at real breakpoints;
  internationalization-ready (no hardcoded user-facing strings, correct locale-aware formatting — see section
  i18n in `SKILL.md`).

**🚩 grep**: `<div onClick`/`<span onClick` without keyboard handling & `role`/`tabindex`; a `<div>`/`<span>`
**with** `tabIndex={0}`/`tabindex="0"` + `onKeyDown` but no `role` and no `aria-label`/`aria-labelledby`
(focusable and key-operable yet roleless and nameless — the operable mirror of the previous tell);
`role="button"` on a non-focusable element; images with no `alt`; `<input>` with no associated `<label>`;
`outline: none` with no replacement focus style; hardcoded `#hex` text colors to spot-check contrast;
`localStorage.setItem('token'`; API keys in `NEXT_PUBLIC_`/`VITE_`/`REACT_APP_` env names;
`addEventListener('message'` with no `event.origin` check; a `<script>`/`<link>` to a third-party origin with
no `integrity=`; a weakened `Referrer-Policy` (`unsafe-url`); no `frame-ancestors`/`X-Frame-Options` on a page
with authenticated or state-changing actions; a small lookup helper imported from a shared module that also
builds a derived singleton over a large dataset (walk the client import graph, stripping type-only imports,
for an edge into that module); a loading/skeleton component with `aria-busy` and/or a label prop but no
`role="status"`/`role="alert"`/`aria-live` on it or an ancestor; bespoke skeleton/shimmer markup (a
`className` containing `skeleton`/`shimmer`/`animate-pulse`, or repeated placeholder block `<div>`s) in a
component that imports **no** shared loader though an accessible one exists elsewhere (a hand-rolled copy that
both duplicates and stays silent — list the shared loader's importers and diff); a `<Suspense fallback={…}>`
whose subtree loads data only via `useEffect`+`setState` or receives already-resolved props, with no
`lazy()`/`use()`/suspense-enabled hook and no unresolved promise crossing it (the fallback is dead); an
identity/singleton-read hook (`useUser`/`useSession`/`useCurrentUser`) that `fetch`es in a `useEffect`/on
first render with no shared Provider/Context or dedup cache, called from many components (each mount fires its
own request — grep the call sites, count global-shell consumers) — or, when that shared Provider/cache
**already exists**, one always-mounted consumer (nav/badge/shell) still fetching the same endpoint
**directly** via a raw `fetch` of the resource URL rather than the hook, so one load fetches it twice and the
outlier's own poll drifts its derived badge out of sync (grep the **URL**, not the hook name — the outlier
never calls the hook); a static `aria-label` that doesn't contain the element's own visible text (WCAG 2.5.3);
an icon/label swap keyed off an `open`/`expanded` boolean with no matching `aria-expanded` on the same
control; a `Content-Security-Policy` header/meta containing `unsafe-inline` with no `nonce`/hash, or missing
`object-src`/`base-uri`; a sanitizer call (`DOMPurify.sanitize`/`new Sanitizer(`) with no
`SANITIZE_NAMED_PROPS`/`blockAttributes` configured, rendering user HTML, alongside a bare `window.*` global
or a `getElementById`/`getElementsByName` result trusted with no type check; a `setTimeout`/debounced callback
that spreads params/state captured at *schedule* time into a `router.replace`/`push`/`setState` with no
cleanup clearing the pending timer when its keyed value changes (a concurrent newer write is reverted when the
stale timer fires), or a per-component copy of a debounced URL write.
