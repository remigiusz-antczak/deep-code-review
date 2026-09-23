# Testing rendered UI and browser specs

Read this when the target renders a UI or ships browser / E2E specs. Split from `testing-and-evals.md`; the general test taxonomy and smells there apply to every review.

## Prove a rendered-layout claim with geometry, not class names

A UI test that asserts **the class that is supposed to produce a layout** —
`expect(pill).toHaveClass(…)`, `toBeVisible()`, a markup snapshot — proves only that
the author wrote the class they typed; it passes while the two elements render **on
top of each other**. Overlap, collision, and clipping are **geometric** properties,
provable cheaply and deterministically, and a class assertion can never catch them.

For any pair of adjacent elements whose collision is user-visible (a label + its
status pill / badge, a row's text + its action cluster, a header + an overflow
control), the test that counts is a **rendered bounding-box assertion**, run at
**each width the project already screenshots** (an overlap is width-dependent and
usually shows only at the narrow one):

```js
// Playwright: adjacent elements must not intersect at the target width.
// boundingBox() returns null for a non-rendered element — assert presence first.
const a = await label.boundingBox();
const b = await pill.boundingBox();
expect(a && b).toBeTruthy();             // both rendered (not null)
const intersects = (r1, r2) =>
  r1.x < r2.x + r2.width && r2.x < r1.x + r1.width &&
  r1.y < r2.y + r2.height && r2.y < r1.y + r1.height;
expect(intersects(a, b)).toBe(false);    // non-intersection
expect(a.width).toBeGreaterThan(0);      // and neither collapsed to zero
```

Equivalent primitives elsewhere: `getBoundingClientRect()` pairs in a browser-backed
unit runner, or `elementHandle.boundingBox()` per locator. Two companion assertions
share the mechanism:
- **Clip / truncation:** `scrollWidth > clientWidth` on an element that must not
  ellipsise.
- **Disabled-looks-disabled:** assert the **computed** affordance (`opacity`,
  `cursor`, or painted colour) of a disabled control, not the `disabled` attribute or
  the class — an attribute that blocks the click while the control still *styles* as
  live is a dead control that looks clickable.

**Scope discipline — invariants, not pixels.** These assertions are for
**non-intersection and non-clipping**, which hold on every renderer. They are **not**
for absolute positions or exact widths, which are renderer- and font-metric-dependent
and produce the cross-OS flake the bar warns against (the renderer-tolerance / pinned-
exception discipline, `ux-gates.md` gate 3). The assertion is "these two do
not overlap," never "this is 132px wide." Show it **red before / green after** the
fix, like any regression test. This is the mechanical proof behind the
screenshot-inspection checklist's **overlap** and **clip** items
(`ux-gates.md` gate 1).

## Capturing the pre-hydration render — the disabled-until-hydrated write control

The geometry assertions above run against the *hydrated* DOM, and one gate-1 defect is
invisible there: a write control gated on client-only state (`useSession` / `useAuth`) is
server-rendered `disabled` and enables only once the client bundle hydrates, so for the
SSR → hydration window it looks like a permanent dead control (`ux-gates.md` gate 1,
*not-dead-before-hydration*). Catching it needs a snapshot taken **before the client bundle
runs** — three captures, cheapest first:

- **Server HTML** — fetch the route's server-rendered markup with no JS executed (the raw
  SSR/SSG response, the same bytes the user first receives) and parse it.
- **JS-disabled render** — load the route with scripting off (Playwright:
  `browser.newContext({ javaScriptEnabled: false })`), which freezes the pre-hydration paint.
- **Throttled capture** — screenshot within the hydration window under slow-CPU emulation;
  least reliable (a race), used only when the two above cannot reach the route.

The assertion is the same across all three: a control that **will** become interactive must
not present as a bare `disabled` (or `aria-disabled="true"`) with **no loading sibling in its
container** in that pre-hydration snapshot — it carries a skeleton/spinner affordance, or is
optimistically enabled (its click captured for replay, never a no-op).

```js
// Playwright: the pre-hydration paint must not show a dead write control.
const ctx = await browser.newContext({ javaScriptEnabled: false });
const page = await ctx.newPage();
await page.goto(url);                               // server HTML, no hydration
// scope to the control's own wrapper so the affordance is a sibling, not page-global
// (a page-wide match would pass on any unrelated spinner; a broken scope that matches
// nothing would fail every disabled control — stricter than the standard, gate 1 forbids):
const box = page.locator('[data-testid="composer"]'); // the write control's container
const btn = box.getByRole('button', { name: /add|submit|post/i });
const disabled = (await btn.getAttribute('disabled')) !== null
  || (await btn.getAttribute('aria-disabled')) === 'true';
const affordance = await box
  .locator('[aria-busy="true"], [data-loading], .skeleton, [role="status"]').count() > 0;
expect(disabled && !affordance).toBe(false);        // dead-until-hydrated is the defect
```

This is the **positive control** for the *not-dead-before-hydration* detector — the instrument
that converts the static `disabled={!session}` *lead* into a finding (principle 2: *an absence
is evidence only after a positive control fires*). Where the harness cannot produce any of the
three captures for a route, the item is **could-not-check** and fails **open**; a missing
snapshot is not a clean pass (`ux-gates.md` gate 1). It complements
`domain-p.md`'s SSR/static-HTML inspection, which catches hydration-*nesting* faults
in the same server-rendered output.

## A rewritten browser spec names its retired coverage and pins the wiring it can no longer reach

The geometry assertions above prove a rendered claim you can still reach. This is the
opposite case: a redesign makes a spec's target surface **structurally unreachable in the
test environment** — a surface that now renders only user-submitted content while the
test store is intentionally empty, so there is nothing to drive the interaction — and the
spec is correctly rewritten against a different surface. The trap is that the rewrite
**silently drops** what the old spec covered: surface A and surface B both exercised an
overlay; B is redesigned to nothing-to-click; the spec moves A-only; a later change
removes B's wiring (the feed's import of the shared overlay-link component) and **no test
goes red**, because the only spec that covered B is gone.

When a spec is rewritten because its surface became unreachable, three things are owed —
and their absence is a finding:

1. **Name the retired coverage as a gap.** What did the old spec assert that the new one
   does not? A dropped assertion is an *absence*, and an unrecorded absence reads as
   coverage (principle 2: *an absence is evidence only after a positive control fires*).
   Record it where coverage gaps are already tracked (the *honest coverage taxonomy*
   in `testing-and-evals.md`), not in a commit message the next reader never sees.
2. **State whether the wiring is now unverifiable via a browser test** without seeding
   the store (or standing up a costly fixture), and why — so the gap is a decision, not
   an accident.
3. **Add a source-level structural gate that pins the wiring** the browser spec can no
   longer reach: a unit/source assertion that the feed component still imports and uses
   the shared overlay-link component (the pattern the codebase's other overlay-wiring
   tests already use). This guarantee is **weaker** than the browser scenario it replaces
   — it proves the component is *referenced*, not that the interaction *works* — so it is
   a **named fallback for a retired check, never a substitute** that lets a team trade
   rendered coverage for import checks and call the surface covered.

## A state-dependent spec must assert its precondition, not lean on a default

A browser / E2E spec that depends on an **implicit UI default** passes only by
coincidence, and the coincidence breaks silently:
- **A flipped default breaks specs that leaned on the old one — at the browser tier,
  not on commit.** A spec that asserts on content visible only while a card is
  *expanded*, or that clicks a bulk "Expand all" a redesign already removed
  (`if (await btn.count()) await btn.click()` — a no-op when the count is `0`), is
  green *only because the default happened to match what it needed*. Flip the default
  and it fails on the slow gate. Make each such spec **drive the state it needs
  explicitly** (open/collapse the specific control by its own affordance), and prefer
  an explicit state assertion over a best-effort "click if present" — a control the
  redesign has since removed silently leaves the precondition unmet.
- **Pin the equivalence between a "should-render / should-expand" predicate and the
  set it gates.** When one boolean decides whether to show or expand something and a
  *separate* path builds what renders inside, independent computation lets them drift —
  the predicate says "expand" but the body is empty, or it collapses a group that has
  content. Derive both from the same source where possible, and pin
  `predicate(x) === (renderSet(x).length > 0)` **in both directions and non-vacuously**
  (at least one input exercising each branch), so a later edit to either side cannot
  silently make them disagree — the class of bug where a "smart default" hides real
  content or expands an empty container.
