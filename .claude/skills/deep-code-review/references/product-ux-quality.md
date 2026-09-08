# Product UX quality — the "at-home" bar (domain P, design half)

Read this alongside `frontend-a11y.md` when the target renders a **product UI a
human operates** — a dashboard, table, form, chart, legend, or metric display.
Expands section P of `SKILL.md` (the design half). `frontend-a11y.md` owns a11y
**correctness** (WCAG 2.2 AA, keyboard/focus, contrast, Core Web Vitals, the
cross-view accessible-name pass); this owns whether the UI feels **at-home** —
conventional, self-evident, correct in every data state, and cleanly encoded.
Same spine as the rest of the method: respect the existing design, separate a
defect from a redesign, verify live, and ground every claim in a named standard —
never "looks nicer."

Ground the design half in the tiers the skill already tracks: **WCAG 2.2**
(colour, contrast — via `frontend-a11y.md`), **Nielsen's usability heuristics**
(named, not URL-cited — see the by-name list in `README.md`), and the public
precedent of top products (Linear, Stripe, Notion, Vercel, Figma, Datadog,
Google/Material, Robinhood) — named the same way this skill already names Cursor,
Copilot, and OWASP, and added no differently: no new URL, version, or date the
reviewer did not fetch (principle: no fabrication).

---

## Matching a convention is an observation, not a licence to redesign (read first)

This mirrors `frontend-a11y.md`'s "Respect the existing design," and it is the
rule that keeps this reference net-positive on every axis. A product-UX finding
**improves** the product; it must never silently restyle it.

1. **Separate the defect from the redesign.** A blank screen on a reachable
   state, a delta coloured the wrong way, a legend that is a wall of prose, a
   dead control — these are **defects**, fixed in place, minimally, preserving
   the existing look. A change that alters layout, spacing system, type scale,
   component set, or brand *to match a convention* is a **redesign** — an owner
   decision, not a review fix.
2. **Surface the convention gap under "Decisions needed (owner)."** When a design
   deviates from a named top-product pattern (legend, delta, empty state, date
   picker, table), record it with the precedent cited and the
   **minimal-visual-impact** fix offered first — exactly as `frontend-a11y.md`
   handles a layout/brand change. Import the requirement to *notice* the gap;
   keep the discipline that the owner decides. "Looks nicer" is not a reason —
   and neither is "the convention says so."

---

## Every data state — rule on each, not just the happy path

Every view is intentional and honest in **all five** states, each ruled on
(finding, clean, or `unverified`):
- **empty** — say what will appear and how to get it (never a bare void);
- **loading** — skeleton/spinner, no layout flash;
- **error** — what failed and how to recover, **never a raw stack or blank**;
- **partial** — some data present, some missing/degraded, shown honestly;
- **overflow** — too many rows → scroll/paginate/virtualize **inside the
  component's own container**, never breaking the page layout.

A blank screen or a raw error on a **reachable** state is a P0 "not-at-home"
defect, not a nit — severity by reachability, like any other defect. (Nielsen:
visibility of system status; help users recover from errors.) `frontend-a11y.md`
owns the *phrasing/consistency* of empty states across routes; this owns whether
each state **exists and is honest**.

## Encoding hygiene — one visual channel per dimension

Never make **one channel carry two meanings**. The classic bug: colour encoding
two independent variables at once (green = both "instrumented" *and* "trending
up") — ambiguous, and invisible to an a11y-only pass. Split dimensions across
channels — **shape/fill** for one, **colour** for another, **position/size** for
a third. Run out of channels ⇒ you have too many encodings; cut some. Fewest
encodings wins.

## Never colour alone — colourblind-safe as a method

`frontend-a11y.md` owns the WCAG rule (1.4.1 Use of Color; and the 1.4.3
disabled-control exemption that a gate must not over-flag). This owns the
**testable method**: pair every hue with **shape, icon, or text** (▲▼ ↑↓ ✓ ✗ or a
word) plus an `aria-label`. Colour reinforces; shape carries the meaning. The
one-line test: **it must read correctly in greyscale.** Works in greyscale =
works for the ~8% of men with deuteranopia, and for everyone.

## The metric / KPI delta standard

A near-universal pattern with a right answer (Stripe, Google Analytics, Mixpanel,
Amplitude, Robinhood, Linear, Material) — inventing a novel one here is a cost:
- caret **▲▼** (or arrow ↑↓) **+ the magnitude** (`▲ 3`, `+2.1%`) — direction
  alone never says *how much*;
- colour by **sentiment, not direction** — "up" is not always good; a drop in
  churn / cost / latency / error-rate is **green**. Key the colour to the
  metric's polarity (direction-of-good), not to up/down. Backwards polarity
  actively misleads — a correctness defect, not a taste one;
- muted **`—`** when flat; anchor the delta to its period ("vs last month") in
  the tooltip/`aria`.

## Self-evident over explained — progressive disclosure

Layout + labels + standard components make meaning obvious **without** inline
prose. **If a screen needs a paragraph to be understood, the design failed — fix
the design, not the paragraph.** Demote explanation to a "?" tooltip, a hover, a
collapsible "How this works", or a dismissible first-run hint — available, not
shown by default. Legends/reference blocks: **collapsed by default**; when open, a
**grid showing the actual glyph** beside its meaning, never a paragraph
describing marks in words. Teach on the artifact itself via hover/focus; the
legend is the fallback teacher, not the primary one. (Nielsen:
aesthetic-and-minimalist design; recognition over recall.)

## Drawers, hierarchy, density

- Detail drawers **overlay** the current view — never navigate the background
  away; the user keeps their place and can inspect several items in a row.
- Correct collapse **scope**: a child collapses within its parent's subtree, not
  siblings two levels up.
- Declutter dense rows — few visible chips, secondary actions behind a menu,
  detail on hover. **No dead controls** — a toggle that does nothing is worse
  than none; it is a trust defect, not a cosmetic one.

## Match a named standard; visual & number-format consistency

Before designing an element, recall how the best products solve it and **name the
standard applied**; reinventing a solved problem (legend, delta, table, date
picker, empty state) is a cost, not a feature. Then keep it consistent: one type
scale, one spacing rhythm, one component set, and consistent **number
formatting** — locale/thousands separators and **tabular figures in columns** so
digits align. The same mark/legend renders identically wherever it appears.
`frontend-a11y.md` owns **accessible-name** consistency across routes; this owns
**visual / number-format** consistency — the drift a per-route pass and a
name-only diff both miss. (Nielsen: consistency and standards.)

---

**🚩 grep**: a data-fetch / `useQuery` / `await` render path with no
`isLoading`/`isError`/empty branch, a `.map(` over a list with no length-0 case, a
table/grid with no `overflow`/pagination, a `catch` rendering `err.message`/stack
into the DOM (states) · a colour scale keyed on a field that also drives an
icon/shape, or `>1` semantic use of one `--color-*` token (encoding) · a
status/delta rendered by `color`/`background` with no sibling icon/text node, or a
colour-coded status dot with no `aria-label` (colour-alone) · a delta coloured
green-for-up / red-for-down unconditionally, an arrow/percentage with no
magnitude, or a "change" number with no period anchor (delta) · a paragraph of
instructional copy rendered inline on every load, or a legend built from text
descriptions of marks rather than the marks (self-evident) · a "drawer"/"detail"
that pushes a route change or unmounts the list, or an `onClick` that is a
no-op / `// TODO` (drawers / dead controls) · `>1` font-size/spacing value for one
role, or column numbers interpolated without `toLocaleString`/tabular figures
(consistency).

## Pre-ship checklist (mirror SKILL.md's report discipline)
- [ ] Does it need explaining? If yes, redesign until it doesn't (or demote the text to progressive disclosure).
- [ ] All five data states handled and honest — empty / loading / error / partial / overflow?
- [ ] One channel per dimension; nothing colour-only; reads correctly in greyscale?
- [ ] Deltas are caret + magnitude, coloured by sentiment; flat is a muted `—` with a period anchor?
- [ ] Matches a **named** top-product pattern; convention gaps surfaced to the owner, not silently redesigned?
- [ ] Consistent type scale / spacing / components / number format with sibling views (tabular figures in columns)?
- [ ] Drawers overlay (don't navigate away); collapse scope correct; no dead controls?
- [ ] Verified live in the running product, in more than the happy-path state?

## Enforcing gate (Phase 6 imprint)

A standard with no gate is advisory (SKILL.md Phase 6: *pair each imprinted
standard with the gate that enforces it*). When imprinting into a project that
ships a UI, pair this reference with a UX-evidence gate — held to the skill's own
gate discipline: **a gate must tell "could not check" from "found a problem,"
fail *open* on the former, and never be stricter than the standard**
(`frontend-a11y.md`, the `innerText` and disabled-contrast traps; SKILL.md
Phase 1, gate-vs-standard). Three gates, in descending confidence of what they
can prove:

1. **Screens-changed evidence (proves a look happened).** On any diff that can
   change a rendered page, require a screenshot of each affected route at a narrow
   and a wide width (e.g. 390 / 1440), or an explicit `No UX change: <reason>`
   line. This proves a human/agent *looked*; it does **not** prove the states are
   correct.
2. **State-coverage in tests (proves the branches exist).** A component test that
   renders a data view asserts the **empty and error** branches, not only the
   populated one — extends `testing-and-evals.md`'s "test the failure, not just
   the feature" to UI states.
3. **Encoding self-test (heuristic — scopes its own claim).** Where a design
   system exists, a lint/unit check that no single colour token is bound to two
   semantic names, and that every status/delta element carries a non-colour
   channel (icon/text + `aria-label`). Both are **heuristic**: a static
   "one token, one meaning" check cannot see runtime binding, and "has a
   non-colour sibling" false-positives on decorative nodes — so it **warns and
   lists**, never fails closed, and reports what it could not resolve as
   `unverified`, not as clean. Model: a renderer-tolerant ratchet — a pinned
   exception is *allowed*, never *required* to exhibit.

Ship all three **idempotent and additive**, per Phase 6 — detect-and-stop if
present, add only what is missing, defer to an existing style guide.
