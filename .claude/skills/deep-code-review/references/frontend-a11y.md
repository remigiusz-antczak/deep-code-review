# Frontend, UI/UX & accessibility review

Read this when the target renders UI (web, mobile web, component library, or a
server-rendered view). Expands section P of `SKILL.md`. Target **WCAG 2.2
level AA** (W3C Recommendation, 2024-12-12); note AAA items where a flow is
high-stakes.

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
- One `<h1>` per page/view; headings describe structure, not styling.
- Landmarks present; a skip-to-content link for keyboard users.

**Keyboard & focus** (WCAG 2.1.1, 2.4.3, 2.4.7, and 2.2's 2.4.11)
- Everything actionable is reachable and operable by keyboard alone; logical tab
  order; no keyboard trap.
- Visible focus indicator; focus is **not obscured** by sticky headers/toolbars
  (2.2 new: Focus Not Obscured).
- Focus is managed on route change, modal open/close (trap + restore), and
  async content insertion.

**New in WCAG 2.2 — verify explicitly**
- **Target Size (Minimum) 24×24 CSS px** for pointer targets (or adequate
  spacing).
- **Dragging Movements**: any drag action has a single-pointer alternative.
- **Consistent Help**: help/contact is in a consistent location across pages.
- **Redundant Entry**: don't force re-entering info already provided in a flow.
- **Accessible Authentication**: no cognitive-function test (e.g. solving a
  puzzle, transcribing) with no alternative; allow paste into password/OTP.

**Perceivable**
- Contrast: text ≥ 4.5:1 (large text ≥ 3:1); UI components & graphical objects
  ≥ 3:1 (1.4.11). Don't convey meaning by color alone.
- All non-text content has a text alternative; decorative images `alt=""`.
- Content reflows to 320 CSS px wide without loss (1.4.10); works at 200% zoom.
- Respect `prefers-reduced-motion`; no content flashes > 3×/sec.

**Forms**
- Every input has a programmatic label; errors are announced (not color-only),
  identified, and described; instructions are not placeholder-only.
- Autocomplete tokens on personal-data fields (1.3.5).

**Verify with tools + manual**: automated scanners (axe, Lighthouse, pa11y)
catch ~30–40% — always add a manual keyboard-only pass and a screen-reader
smoke test (VoiceOver/NVDA). Report the method used; don't claim conformance
from an automated score alone.

---

## Usability & functional suitability

- The intended user's primary task completes with minimal friction; no dead
  ends. Empty, loading, error, and offline states exist and are helpful.
- Destructive actions are confirmable/undoable; nothing irreversible on a single
  mis-click.
- Copy is clear; errors say what happened and how to fix it.

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

## Reliability & performance (Core Web Vitals)

- **LCP** (loading) ≤ 2.5 s, **INP** (interactivity — replaced FID in 2024)
  ≤ 200 ms, **CLS** (visual stability) ≤ 0.1 at the 75th percentile.
- No layout shift on the critical render path (reserve space for images/embeds);
  no long tasks blocking input; images sized/lazy-loaded; fonts with
  `font-display: swap`; bundle split and tree-shaken; ship less JS.
- Degrades under slow/failed network; no infinite spinners.

## Security & compatibility

- Output encoding for anything user-influenced (XSS — see `security-appsec.md`
  A05); a strict Content-Security-Policy.
- **No secrets/API keys/tokens in the client bundle or source maps** — anything
  shipped to the browser is public.
- No sensitive data in `localStorage`/`sessionStorage`; tokens in
  httpOnly+Secure+SameSite cookies where possible.
- Works across the project's target browsers/devices; responsive at real
  breakpoints; internationalization-ready (no hardcoded user-facing strings,
  correct locale-aware formatting — see section i18n in `SKILL.md`).

**🚩 grep**: `<div onClick`/`<span onClick` without keyboard handling &
`role`/`tabindex`; `role="button"` on a non-focusable element; images with no
`alt`; `<input>` with no associated `<label>`; `outline: none` with no
replacement focus style; hardcoded `#hex` text colors to spot-check contrast;
`localStorage.setItem('token'`; API keys in `NEXT_PUBLIC_`/`VITE_`/`REACT_APP_`
env names.
