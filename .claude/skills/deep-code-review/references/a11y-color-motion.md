# Accessibility depth — colour, non-colour cues, motion, and timing

Read this when the target or diff encodes a state or direction by colour, a chip/pill, or a Unicode arrow glyph; pins a sub-AA "decorative" colour token; animates anything (a JS-driven animation, smooth scrolling, `Element.animate()`, a carousel or marquee); or enforces a session time limit or auto-updating content (WCAG 1.1.1, 1.4.1, 1.4.3, 2.2.1, 2.2.2, 2.3.3). Split from `frontend-a11y.md`, whose base WCAG 2.2 AA checklist applies to every UI review.

## Perceivable — depth

- **A two-state chip/pill that differs only by a colour token — with the state word in neither the visible
  label nor the accessible name — fails colour-blind *and* screen-reader users at once.** A badge whose two
  branches share an identical icon and text template and differ only in a colour-utility class (colour is
  invisible to a screen reader, and to anyone in greyscale or forced-colours mode, whatever the hue pair) puts
  the differentiating word only in a `title` (hover-only, not reliably surfaced to a screen reader in browse
  mode) and leaves it out of the computed accessible name too. This is the
  *don't-convey-meaning-by-colour-alone* rule in `frontend-a11y.md` taken to the **accessible-name** channel: the state must
  appear in at least one non-colour channel that's actually announced — put the state word in visually-hidden
  (`sr-only`) text inside the chip (which joins the computed accessible name whatever the element's role) or,
  if the chip carries an interactive/labelable role, in its `aria-label` (`— at capacity`) — and ideally a
  distinct glyph, never a `title` alone (a `title` is a mouse-hover convenience, not an accessibility
  mechanism; `aria-label` is ignored on a bare `generic`-role element). Detect (source-only): find a chip
  whose className branches on a state enum; if the two branches' icon + text are byte-identical and only
  colour classes differ, check whether the state word is in the computed accessible name for **both** branches
  — absent, or present only in `title`, is the finding. Test: assert the two states' **computed
  accessible-name strings differ**, not just their class lists.
- **A direction/movement badge whose only non-colour cue is a bare Unicode arrow *glyph* (`▲`/`▼`, `↑`/`↓`)
  clears the colour-blind test but still owes a *spoken* equivalent.** A delta or trend chip rendered as a
  plain `<span>` — an arrow character plus a magnitude, coloured by sentiment — reads correctly in greyscale
  (a *shape* is present, so *Never colour alone* in `product-ux-quality.md` looks satisfied) and serves a
  sighted colour-blind user. But that shape channel is **visual only**: a bare Unicode symbol character has
  **no reliable spoken form** — assistive tech announces `▲` as "black up-pointing triangle", as "up arrow",
  or skips it, depending on AT and verbosity — so to a screen-reader user the direction rides on the glyph +
  colour and neither is dependable (**WCAG 1.1.1 Non-text Content**: the glyph is not a dependable text
  alternative; **1.4.1 Use of Color**: colour is unspoken). The trap: a Unicode arrow *looks like text* — it's
  a character — so it's assumed accessible and no alternative is added, unlike an obvious `<img>`/icon. Fix:
  put the direction in a **word** the accessibility tree exposes — visually-hidden (`sr-only`) text inside the
  chip (`<span class="sr-only">up </span>`), which joins the computed name, or an `aria-label` on a labelable
  host (`"up 3 percent versus last month"`) — and mark the decorative glyph `aria-hidden="true"`; the arrow
  reinforces, the word carries. **Distinct** from the two-state colour-only chip bullet above, where the
  branches differ by **colour alone with no shape at all** (fix: add any non-colour channel) — here a shape
  *is* present and the point is a **glyph is not a spoken equivalent**; from *Never colour alone*
  (`product-ux-quality.md`), which lists `▲▼` as a valid **visual** shape cue — this adds that clearing the
  greyscale axis does **not** clear the **screen-reader** axis; and from the icon-button name bullets in `a11y-aria.md`,
  which concern an **icon font / SVG** that plainly needs a name — the wrinkle here is a **Unicode character**
  deceptively treated as accessible text. Detection (source-only): a status/delta/trend node whose direction
  is a literal arrow character (`▲▼↑↓▴▾`) in its text with no sibling `sr-only` word and no `aria-label`, the
  glyph not `aria-hidden`. Test: assert the **computed accessible name** (accessibility tree, not
  `textContent`) contains the direction **word**, not only the glyph.
- **Guard a deliberately-decorative / sub-AA token at its point of *use*, not its value.** A token pinned
  below the text-contrast threshold and documented "decorative only" is only decorative if *no component
  paints **real, informational text** with it* — WCAG 1.4.3 holds informational text to 4.5:1 (large text
  3:1), so a `className`/style colouring a **visible label, status word, or helper line** with it fails the
  audit on every route sharing that chrome, while a value-only test asserting the token stays sub-AA stays
  green. Add a lint/test that **fails when the token colours a real text node** — fail-closed, but **with an
  escape**: admit a pinned `a11y-exempt` marker for text 1.4.3 genuinely exempts (an `aria-hidden` or
  purely-decorative glyph, a logotype, large text already meeting 3:1), so the gate is *narrowed to the
  standard, not stricter than it* — the same gate-vs-standard discipline as the disabled-control exemption
  note in `frontend-a11y.md`. Allow the token freely on non-text (borders, backgrounds, icon fills with an accessible-name
  sibling), and have the self-test plant **both** a real-text use (guard fires) and a pinned-exempt use (guard
  stays silent). This closes the runtime-binding gap the encoding self-test only *warns* about
  (`ux-gates.md`, the Phase-6 gate). General form: when a test encodes an intent ("stays
  decorative", "stays internal", "never renders"), assert the **property**, not the value it's derived from —
  the gap between them is where a green suite ships a regression.
- **Audit reduced-motion by the *symptom* (motion-producing APIs), not only the *mechanism* the codebase
  already gates.** A thorough CSS-duration belt + a per-library `motion-reduce` variant can still leave an
  **imperative native** motion path ungated — most commonly `Element.scrollIntoView({behavior: 'smooth'})` /
  `scrollTo` / `scrollBy` with a `behavior` option, CSS `scroll-behavior: smooth`, `Element.animate()`, and
  autoplay / carousel / marquee logic — because a search scoped to the gated mechanism (`transition-`, the
  animation library's import) never sees them. Grep the **symptom set** and gate each on the repo's
  **existing** reduced-motion hook (cited as the patch), not a new pattern — the audit-by-symptom delta, not a
  re-statement of the CSS-doesn't-reach-JS rule in `frontend-a11y.md`.

### Timing & motion (WCAG 2.2.1, 2.2.2 — both Level A)
- **A time limit that logs out or discards unsaved input needs a warn-and-extend path.** A silent idle-logout
  or silent data loss fails **2.2.1 Timing Adjustable**: warn before expiry and let the user extend with one
  simple action (≥ 20 s to react), or let them turn the limit off / lengthen it. Exceptions: real-time events,
  a limit whose extension invalidates the activity, limits > 20 h. Note the **security ↔ a11y tension** — a
  short idle timeout is a security ask, but it still needs the warn+extend affordance before it fires
  (cross-ref `security-appsec.md` A07 session lifetime).
- **Auto-starting motion / auto-updating content needs a user control (2.2.2, Level A).** **Moving / blinking
  / scrolling** content that starts automatically, lasts **> 5 s**, and runs alongside other content needs a
  visible **pause / stop / hide** (an auto-advancing carousel is the classic case) — unless the motion is
  essential. **Auto-updating** content (an auto-refreshing feed / dashboard) needs the same pause/stop/hide
  **or** a control over its update **frequency**, unless the updating itself is essential — and it gets **no**
  5 s grace period. Distinct from the 3×/sec flash limit in `frontend-a11y.md` (seizure risk; this is attention /
  distraction).
