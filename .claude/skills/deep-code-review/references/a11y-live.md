# Accessibility depth — live regions, loading states, and async outcomes

Read this when the target or diff renders a loading / skeleton / spinner region (a shared loader or a hand-rolled placeholder), or an async action whose success or error message replaces the control that triggered it (WCAG 4.1.3 Status Messages; focus continuity under 2.4.3). Split from `frontend-a11y.md`, whose base WCAG 2.2 AA checklist applies to every UI review.

## Structure & semantics — live regions and loading states

- **A loading/skeleton region that visually swaps state needs a live region announcing the transition, not
  only `aria-busy`.** `aria-busy="true"` marks an element as *being updated* — a state property assistive tech
  can query, not an announcement it makes unprompted — and a plain `aria-label` on that same element is only
  exposed as its accessible NAME (spoken if the element is focused, or is itself an auto-announced role),
  never spoken proactively on mount. A shared loading/spinner component that sets `aria-busy` and
  `aria-label="Loading things…"`, with no `role="status"`, `role="alert"`, or `aria-live` anywhere on it or an
  ancestor, looks finished — the JSX carries a sensible-sounding label — but leaves the entire loading window,
  and the swap to the loaded result, completely silent for screen-reader users. This is squarely what WCAG
  defines as a **status message** — content providing information on "the waiting state of an application" or
  "the progress of a process" — and SC **4.1.3 Status Messages** (AA) requires that "status messages can be
  programmatically determined through role or properties such that they can be presented to the user by
  assistive technologies without receiving focus," which neither `aria-busy` nor a plain `aria-label`
  satisfies. Fix: add `role="status"` to the region — it carries an implicit `aria-live="polite"` and
  `aria-atomic="true"` (MDN), so no separate `aria-live` attribute is needed — so the label is announced on
  mount and again when the wrapped content changes; keep `aria-busy` alongside it to suppress reads of
  partially-updated content, never as a replacement for the role. Detection is source-only: find shared
  loading/spinner/skeleton components and confirm whether `aria-busy`/a label prop is paired with
  `role="status"`/`role="alert"`/`aria-live` on the same or an ancestor element — and check the codebase's own
  error-state sibling, if one exists, which often correctly reaches for `role="alert"` right next to a loading
  state that doesn't; that asymmetry is itself the tell. Regression test: render the component and assert
  `getByRole('status')` (or the role used) resolves and contains the expected text, not only a DOM snapshot.
  Cross-ref `product-ux-quality.md` for whether the skeleton/spinner *design* is right — this is only the
  announcement half. And see the inverse below — a call site that hand-rolls a skeleton while a *correct*
  shared loader already exists, where the fix is reuse (so the announcement propagates), not patching the
  copy.
- **An async action's *outcome* that unmounts the focused control needs a live region AND explicit focus
  continuity — two failures, not one.** Distinct from the loading-announce bullet above (an *ongoing wait*):
  here the action has *resolved*, and the success/error message replaces the very control that was clicked and
  still holds focus — rendered as a plain text node with no `role="status"`/`role="alert"`/`aria-live`. Two
  compounding defects: the outcome is never announced (a plain element is not a live region), **and** because
  the focused element was removed from the DOM rather than disabled/relabelled, keyboard focus silently falls
  back to `<body>` (focus must be managed on async content insertion — the Keyboard & focus rules in `frontend-a11y.md` — not
  left to fall to `<body>`), so a keyboard user loses their place with no signal the action finished. A
  sighted mouse user sees the message appear, so it ships. Fix: give the success message `role="status"`
  (polite) and the error `role="alert"` (assertive); **prefer keeping the original control mounted** —
  disabled and relabelled with the outcome — over replacing it; if it must be replaced, move focus explicitly
  to the replacement (`ref.current?.focus()`). Test both halves: `getByRole('status'|'alert')` resolves with
  the outcome text, **and** `document.activeElement !== document.body` afterward.
- **A loading placeholder hand-rolled at a call site while a *correct* shared loader already exists is one
  defect wearing two hats — needless duplication *and* an accessibility regression the shared fix can't
  reach.** The loading-announce bullet above is a defect *inside* the shared component (it has `aria-busy`/a
  label but no live-region role); this is the inverse. The shared `<Loader/>`/`<Spinner/>` is *correct* — its
  busy-region semantics already announce — and one screen reimplements the same shimmer inline (`<div
  className="skeleton">` block grids, `animate-pulse`) with **no** `aria-busy`, `role="status"`, or
  `aria-live` at all, so through its whole loading window an assistive-tech user hears nothing (no "content
  pending", no update when it arrives) while the sighted reviewer sees a polished shimmer that *matches the
  rest of the app* and approves. The two faults are coupled, not coincidental: because the copy never renders
  *through* the shared component, the accessibility baked into that component — and its next a11y fix — never
  reaches this surface (`ux-components.md`'s "adoption is total" and "a fix to a shared concept lands in
  the shared component" bullets). Detection inverts the loading-announce sweep: don't audit the shared
  loader's ARIA — find the correct shared loader, list its importers, and diff that set against components
  that render loading placeholders (grep bespoke skeleton scaffolding — a `className` containing
  `skeleton`/`shimmer`/`pulse`, or repeated placeholder block `<div>`s — in files importing no shared loader);
  each such hit is a call site that hand-rolled instead of reused. Fix in order: **reuse the shared loader** —
  that, not patching the copy, is what makes every future announcement fix propagate; bolting `role="status"`
  onto the hand-rolled grid cures today's silence but keeps the duplication and the next drift. Only if a
  bespoke skeleton is genuinely unavoidable, wrap it in the announced busy region per the loading-announce
  bullet above. Regression-test the reused path: assert the placeholder renders through the shared loader (its
  `getByRole('status')` resolves), not a raw div grid. **Distinct** from the dead-`<Suspense>` bullet under
  Reliability & performance (`web-fetch.md`; a fallback that never *renders*) — this loader renders fine and is merely silent.
