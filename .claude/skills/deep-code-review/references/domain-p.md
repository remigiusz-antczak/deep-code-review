# Domain P checklist

Read this when domain P (Frontend / UI / UX / accessibility) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### P. Frontend / UI / UX / accessibility → `references/frontend-a11y.md` + `references/product-ux-quality.md` + `references/rendered-parity.md` + `references/migration-parity.md`
Apply if the code produces UI. Target **WCAG 2.2 AA**. Four references:
`frontend-a11y.md` owns a11y **correctness**; `product-ux-quality.md` owns the
**design half** (read it when the target renders a product UI a human operates);
`rendered-parity.md` owns a **"matches / looks the same" claim** (read it
on a port / restyle / design-parity task);
`migration-parity.md` owns the **port / prototype-reference half** (read it when the
reference is a prototype/mockup or the task is a migration to a reference design).
- **Respect the existing design** (principle 5): fix accessibility/usability
  **defects** in place (contrast, labels, keyboard traps, focus, target size);
  treat a change that alters layout/typography/brand as an **owner decision** and
  prompt before imposing it (style guide? or a prototype that can be freely
  changed?). Offer the minimal-visual-impact fix first.
- Semantic HTML before ARIA; keyboard-operable with visible, unobscured focus;
  contrast ≥ 4.5:1 (3:1 large/UI); labels + announced errors; WCAG 2.2 additions
  (target size 24px, dragging alternative, accessible authentication, redundant
  entry). Core Web Vitals (LCP/INP/CLS). **No secrets/keys in the client bundle.**
- **SSR / hydration nesting** (server-rendered or static frameworks): a
  restricted-content-model element placed where its parent forbids it — a
  block-level element or a `<p>` inside a `<p>`, nested `<button>`/`<a>`, or
  misplaced table elements — logs a hydration mismatch, but **the browser silently
  auto-corrects it, so it is absent from the hydrated DOM** and may render in only
  one auth/data state. Check each call site's wrapper against the component's root
  element, and reproduce against the **SSR/static HTML in the specific state** (e.g.
  signed-out), not the convenient live DOM.
- **SSR / hydration mismatch from *nondeterministic render output*** (distinct from the
  nesting case above): a component renders **different output server-side vs. the first
  client render** because it reads `Date.now()`, `Math.random()`, `typeof window !==
  'undefined'`, or a browser-only API (`matchMedia`, `localStorage`) **during render**. The
  framework logs it, but two forms defeat that net — **(a) state-dependent** mismatches
  (only a signed-in user, a non-UTC timezone, a specific random branch) never fire on the
  author's machine/data; **(b) `suppressHydrationWarning`** applied to a subtree to silence
  a *real* mismatch rather than a deliberately-expected one (a live timestamp), which one
  grep finds. The consequence is worse than a corrected DOM: the framework **doesn't
  reliably** patch a mismatch and can leave **event handlers attached to the wrong
  elements** (a control that does nothing on first click). Fix: gate nondeterministic /
  browser-only reads to a post-hydration effect (render a stable server placeholder), use a
  stable id API (`useId`) not `Math.random()`, and reserve `suppressHydrationWarning` for
  genuinely-expected diffs. (react.dev, hydration.)
- **Server/client boundary** (RSC / App Router and similar): a **plain
  non-component value** exported from a `"use client"` module and imported by a
  server component is silently replaced with a **client-reference proxy** — an
  unstyled/empty render that passes typecheck, lint, and unit tests, caught only by
  rendering the real split. Depth + the lint-shaped static check:
  `frontend-a11y.md`.
- 🚩 `<div onClick>` with no keyboard handler, missing labels, contrast failures,
  no loading/error state, secrets in the bundle, `localStorage` for tokens, an
  a11y/UX gate that computes accessible names from `innerText`/`textContent`
  instead of the accessibility tree, a name check that tests presence
  (`if (!name)`) but never shape, a `<p>`-rooted or block-level component mounted
  inside a `<p>` wrapper (or nested `<button>`/`<a>`) — a hydration error checked
  in SSR/static output, not the auto-corrected live DOM; a plain value
  (class-string / config / lookup) exported from a `"use client"` module and
  imported by a server component (proven by rendering the real split, not by types).
