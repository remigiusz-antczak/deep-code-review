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

## Repeated owner rejection is a redesign trigger — surface options, don't tune (or impose)

The section above bars a redesign driven by *your* taste. This is its complement,
resolving the same tension from the other side: a redesign driven by the **owner's
own repeated rejection** of the same element is warranted — but as options the
owner chooses, never a change you tune your way into or impose. Both obey
principle 5 (*respect the existing design; separate a defect from a redesign;
surface it, don't impose it*).

- **Trigger: the owner rejects the same element two or more times** ("bulky /
  confusing / too heavy / looks wrong"). That repetition — not a reviewer's
  aesthetic read — is the evidence the approach is **structurally** wrong, not
  under-tuned. A first rejection is feedback to apply; the *same* rejection twice
  says the structure, not the parameters, is the defect.
- **Stop tuning.** Nudging padding, arrows, spacing, or counts cannot remove a
  structural defect (three overlapping rings do not stop overlapping because the
  arrows moved). Re-tuning after a second identical rejection is the failure this
  rule names — the design-half form of principle 9 (*root-cause, not symptom*):
  after the same failure twice, change the approach, do not repeat the fix.
- **The same move for a *verification* claim: repeated correction means your
  method is broken, not their patience.** If a stakeholder repeatedly corrects your
  "it matches / it's the same," that is evidence your **verification method** is
  wrong — not a cue to ask them for more examples. Change the method: build the
  comparator (the **parity differ**, Phase-6 *Enforcing gate* below) and show its
  diff, rather than outsourcing your verification back to the person reviewing you.
  Report only what you actually inspected on the target ("the nav now reads A · B ·
  C, I looked at it"), never a blanket "it matches"; an honest "not yet verified"
  beats a false positive (principle 9 again — after the second false "matches",
  change the instrument, do not re-assert).
- **Name the structural flaw in one line**, then research how **two or three
  comparable products** (named, per *Match a named standard* below) solve the same
  problem — the muscle memory the new direction should borrow.
- **Hand the owner concrete options to choose — show, don't tell.** A side-by-side
  of two or three real directions is a decision the owner makes in seconds; a
  paragraph describing them is not. Product/redesign choices are owner decisions
  and never carry Blocker/Critical gate language (SKILL.md Phase 5).
- **Variant/option bloat is the supply-side of the same smell.** N interchangeable
  ways to view or style one thing — seven style-toggle tabs on one diagram, eight
  overlapping list modes — reads as unfinished, not powerful: the *choice* is the
  defect, so the fix is **cut to one strong default**, not tune the set. Test:
  would a first-time user know why to pick one over another? If not it is bloat,
  not flexibility. Distinguish redundant variants (overlapping modes, decorative
  toggles) from genuinely different tools (a diagram vs a table serve different
  tasks — keep both), and keep the power path reachable behind **progressive
  disclosure**, off the default surface.

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

**An empty state must not imply a conclusion it hasn't earned.** "No rows shown"
is not "nothing happened": an empty activity feed, an all-green board with no
data behind it, or a zero-count that is really an *uncollected* count all read to
the user as "all clear / no risk / no activity" when the truth may be that the
source was never queried. The empty state must distinguish *no data collected or
covered* from *collected, and genuinely none* — SKILL.md principle 2 (*an absence
is evidence only after a positive control fires*) at the UI layer. Name the
coverage, not only the remedy: a bare "Nothing here" over an unprobed source is a
false all-clear, not an honest empty. (`data-quality.md` §8 owns the same rule
where the number is *scored* rather than *shown*.)

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

## Confidence shown as a bare number is false precision — flag it

A confidence, priority, or match score surfaced as a **raw number** ("87%",
"score: 0.92") claims a calibration the pipeline usually does not have, and invites
over-trust. It belongs on a **small set of labeled tiers** — text plus a
colourblind-safe cue (see *Never colour alone*) — not a percentage or an opaque
point score. **🚩**: a `confidence` / `score` / `priority` value rendered directly
as `{n}%` or a raw float in the UI with no defined tier label beside it; a
model-authored number published as precision. (How to *define* the tiers, and why
source reliability and claim corroboration stay independent axes, is a
data-product-output rule — `product-output-safety`'s — not restated here.)

**Measure the field's distribution before building the display at all.** Even a
*tier* is false precision if the underlying signal is **near-constant** — so measure
it first, on real data. A `corroborationCount` that is `1` on 16,008 of 16,012 rows
makes a "confirmed by N sources" badge fire on ~0.02% of rows and read "1 source"
everywhere else; a match-confidence that is `0.9` on ~70% of rows and `0.8` on the
rest is effectively binary, so "90% / 80% confidence" manufactures precision the
pipeline lacks. If the field barely varies, **showing it is false precision, not
transparency** — drop it, or reframe to something that actually varies (e.g. *how*
an entity was matched, not a number). A misleading signal is worse than an honest
blank — empty beats fabricated (`data-quality.md`).

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

## Unified across modules — one component per concept

The consistency rule below has a structural cause and a structural fix.
**Inconsistency across views is almost always the same concept built more than
once and drifting** — a row, card, field, empty-state, status chip, or editor
reimplemented per page, so a fix to one misses the others and the app feels like
a different product on each screen. This is a maintainability defect (cross-ref
domain H) with a UX consequence, so it is ruled on here too.

- **One shared component per concept.** Before building a UI element, grep for an
  existing component or pattern that already does it and **reuse or extend it** —
  never reimplement per page. A duplicated UI string or markup block across files
  is the red flag (cross-ref H's duplicate-source-drift: byte-identical lockstep
  copies need a single source or a parity test). **Cross-file duplication is
  invisible to a diff-scoped review** — you see the file you changed, not its twin —
  so on any "unify" or "fix this component" task, grep the **duplicated visible
  literal string or section heading** across the whole tree as the search key that
  surfaces the twin, before claiming the concept unified.
- **A fix to a shared concept lands in the shared component**, not in one caller —
  otherwise the same defect survives in every other caller, and whoever checked
  only the screen they were shown signs off a still-broken app.
- **Fix the surface that renders, not the first grep hit.** A string can live in a
  file the target route never renders; trace route → component and confirm the
  component is actually shown on that screen before editing it. Grep finds
  candidates; the render trace confirms (cross-ref `parallel-audit.md` §5).
- **One component, divergent props, is the other half of inconsistency.** Even a
  correctly-unified shared component reads as inconsistent when a **feature-bearing
  optional prop defaults off** and some mount sites omit it — one listing passes
  `votes` (the chip shows), a second embedding doesn't (no chip). Each render is
  individually correct; together they look cheap, and the twin-search above won't
  catch it because it *is* one component. For any shared component with a
  feature-bearing optional prop, **enumerate every mount site and diff the props**;
  a feature that should be universal belongs **inside** the component (on wherever
  its data exists), not behind an opt-in a caller can forget. Review question:
  "does this concept render identically at *all* its mount sites?" — don't stop at
  "it's one component."
- **In a port or migration, unification is a precondition, not a cleanup pass.**
  Enumerate the shared concepts and adopt exactly one component per concept
  **before** porting screens — a duplicated concept is a defect a reviewer *will*
  find, and retrofitting unification while the owner watches is far slower and
  noisier than building it once up front.

## One component at two scopes — single-entity vs aggregate needs scope-aware copy

A shared component reused at **two scopes** — a single entity vs an all-entities
**aggregate/rollup** — but with labels and empty-states that **hardcode the
single-entity phrasing** ("the items *this* owner has", "nothing here for this owner
yet") reads wrong or misleading at the aggregate scope. Related forms: the aggregate
view **drops** a section the single-entity view shows, or lists an unbounded union of
rows with **no attribution** of which entity each row belongs to — so the rollup is
unreadable and the two scopes feel inconsistent.

- **Make copy and empty-states scope-aware** — interpolate the scope (the entity name
  at single scope, "all …" at aggregate), don't hardcode one.
- **At aggregate scope, label each row with its owning entity** and **cap/paginate**
  the union (the overflow state).
- **Keep the section set consistent across scopes** unless a per-scope variant is
  deliberate and stated — and at aggregate scope specifically, **hide a view whose
  number would be a *misleading aggregate*** (a rate or total that is meaningless
  across heterogeneous entities): computed-not-fabricated (principle 4) beats
  symmetry, exactly as in `migration-parity.md`'s misleading-aggregate exception.

A **different axis** from the neighbours: not the *prop* axis (#123 above — one
component, a feature prop present at one mount site and absent at another) and not the
*section-set superset* across **sibling per-entity** surfaces (`migration-parity.md`),
but the **single-vs-aggregate scope** of one component's copy and attribution.

## Interaction-completeness — the loop must close

A control is a defect until its whole loop works in the running product, not just
until it renders:

- **No write-only inputs.** Any surface where a user adds or edits data must let
  them **see, reach, and edit** what they added, in that same view (read-back). An
  input that posts to a store but never shows the value back is a defect, not a
  slice — the user cannot tell it worked, correct it, or undo it.
- **WYSIWYG, never raw markup shown to users.** Store markup; **display it
  formatted**. A rich-text field that shows `**bold**`, `<u>`, or `*` tokens while
  the user types has leaked its storage format into the UI — render what the text
  will look like once posted.
- **No dead controls, and disabled must look disabled.** A button/toggle/arrow
  rendered enabled whose handler is a no-op is a trust defect; a control that is
  unavailable must *look* unavailable, not merely be inert. Unit-logic tests
  passing is **not** a working UI — exercise the real control in the running app
  (cross-ref the live-verification rule below).
- **Reviewable change history, and no silent AI edits.** Any surface where an
  edit is itself a decision of record (a value, a target, an assignment, an
  owner) needs a visible who/what/when history behind the current value, not a
  silent overwrite — the same defect class as a write-only input, one level up.
  A value an agent or model proposed or wrote on a person's behalf is stamped
  in that history as AI-recommended, with its source, **at write time** —
  never merged into the record indistinguishably from a human edit. An
  unstamped AI edit is a defect a reviewer cannot see, not a shortcut.

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
(consistency) · the same UI string, section heading, or markup block
duplicated across ≥2 component files, or a second hand-rolled copy of a
row/card/field a shared component already renders (one concept built more than
once) · a text input that
persists markup while rendering its raw `**`/`*`/`<u>` tokens back to the user
(not WYSIWYG) · an add/create/edit handler that writes to a store with no path
that reads the value back into the same view (write-only input) · an editable
record's write path with no history/log table behind it, or an
agent/model-authored value merged in with no field distinguishing it from a
human edit (change-history / silent AI edit) · a `confidence`/`score`/`priority`
rendered as a raw `{n}%` or float with no defined tier label beside it, or a model
confidence number published as precision (confidence tier).

## Pre-ship checklist (mirror SKILL.md's report discipline)
- [ ] Does it need explaining? If yes, redesign until it doesn't (or demote the text to progressive disclosure).
- [ ] All five data states handled and honest — empty / loading / error / partial / overflow — and an empty state names its **coverage** (no-data-collected vs collected-and-genuinely-none), never implying a false all-clear?
- [ ] One channel per dimension; nothing colour-only; reads correctly in greyscale?
- [ ] Deltas are caret + magnitude, coloured by sentiment; flat is a muted `—` with a period anchor?
- [ ] Confidence / score / priority shown as a **defined labeled tier** (text + a colourblind-safe cue), not a raw `%` or point score, and no model-authored number published as precision?
- [ ] Matches a **named** top-product pattern; convention gaps surfaced to the owner, not silently redesigned?
- [ ] If the owner has rejected this element **twice**, stopped tuning — structural flaw named, two or three comparables researched, concrete options surfaced for the owner to choose?
- [ ] Consistent type scale / spacing / components / number format with sibling views (tabular figures in columns)?
- [ ] One shared component per concept — reused/extended, not reimplemented per page; a fix landed in the shared component, not one caller; **searched the tree for a duplicate twin (a duplicated visible string/heading) a diff-scoped review would miss**?
- [ ] Interaction loops close — read-back on every input (no write-only), WYSIWYG not raw markup, no dead controls — checked on the route that actually renders?
- [ ] Drawers overlay (don't navigate away); collapse scope correct; no dead controls?
- [ ] Verified live in the running product, in more than the happy-path state — **including the default state a user lands on** (signed-out / no-role / default route / local default), not only a mock or a hand-picked persona view?
- [ ] Any "matches / exact / parity" claim checked against the **default served state of the tree under review** as the canonical surface (not whichever tree happens to hold the port — name url · branch · sha, `report-format.md`) — and if it rests on a non-default surface, does it **name** that surface and say the default was not checked?
- [ ] "Looks the same" backed by a **rendered-appearance** diff of the default state vs the reference (screenshot / computed styles), **not** section-presence, DOM order, a passing test, or loaded data — and stating **which axis** (structure / styling / content / data) the evidence covers, without "fixing" data to answer a styling complaint?
- [ ] Parity task: differences classified **structural vs cosmetic** (structural parity first; a structural divergence **never** called "close / 1:1"); every "matches" claim gated on a **mechanical differ** (diff image + structured mismatch list attached, not an assertion); reference read at its **highest fidelity** (running build > source > screenshot); **no mock sample value copied** into the product; and the differ run **both ways** (design→app and app→design), both lists **resolved** (design→app empty; each app→design entry restyled into the target language, decoration removed, or owner-adjudicated — an app-only element is a finding to resolve, never a silent bonus)?
- [ ] Parity **delta** established by rendering **both sides at the same viewport width** (a one-sided crop is a hypothesis, never the evidence), and each app-only / design-only element's **state confirmed on the other side** (present-but-collapsed / disabled-by-data / in-a-menu) before it is called a delta?
- [ ] Did **not reconfigure the default** (persona / seed / flag / env) and then claim "verified on the default" — checked the pre-existing default and disclosed any change to it?
- [ ] Every styling / placement delta enumerated in **one** side-by-side pass and fixed against that inventory — not piecemeal-fix-then-redeclare-done?
- [ ] Told "not the same" → **asked which axis** before acting (after one wrong guess, asked not guessed), and compared the **reference itself** at the element × breakpoint × theme, not from memory?
- [ ] Parity target expressed in **measured device-pixels at the actual render scale** (not user-space units — equal user-units ≠ equal pixels), and same-axis oscillation treated as a **duplicate-implementation-at-different-scale** signal (measure the ratio, don't tune)?
- [ ] No status is green-with-a-caveat — a status the author can immediately qualify is **downgraded**, not asserted beside a hedge (`report-format.md`)?
- [ ] UI change: headed-browser receipt on the exact route after the action (screenshot or equivalent) — and the receipt is a **valid non-empty image**, not a proxy/504-wiped stub that passes a bare existence check (existence is not content — `SKILL.md` principle 2), captured from a **clean or separate tree** (a shots script that stashes uncommitted changes discards the very diff under review)? Unit tests alone are not this box.

## Parity claims: the default state is the canonical surface

A "matches / exact / parity with `<reference>`" claim is only as good as the
**surface** it was checked against. The canonical surface is the **default state
a user lands on** — signed-out / no-role / no-persona / default route / local
default — because it is the state a user is served **by default**, before any role
or persona is chosen: the entry state every user passes through. A mock, or a
hand-selected persona/role view, is a **secondary** surface: a parity claim
resting only on it verifies the wrong state (a first-time user never sees it). "More than the
happy-path state" (checklist above) is necessary but not sufficient — the
**default state must be among the states checked**, and a claim that rests on a
non-default surface must **name that surface** and say the default was not
verified.

The general rule that a status is **downgraded the moment it carries a caveat**
(and names the surface its evidence came from) is defined once in
`report-format.md` and applies to a parity claim unchanged — the UI-specific case
is that a parity ✅ resting on a **non-default surface** is not green.

## "Looks the same" is about rendered appearance — four axes, and a structural check is not a visual one

"Make X look like reference Y" is a task that frequently earns a false ✅. These
rules sit **on top of** the default-state rule above (never restating it); each is
a distinct fidelity rule, or names an evasion that passes a default-state check yet
still ships a UI that does not look like Y.

**Read the reference at its highest available fidelity — this is the *reference*
side, not your output's.** The reference exists in three forms; prefer the highest
present: a **running build** you launch and diff against > the design **source**
(HTML/CSS, which states the column model, tokens, and spacing exactly) you read
property-by-property > a **screenshot** (a lossy picture — last-resort sanity check
only). Never reverse-engineer the source when a running build of the design
already exists in the repo, and never eyeball a picture when the source or build
states the spec precisely. **A stale source *comment* ranks below even the
screenshot** — a code comment claiming an element "moved" in some past design
revision is not the current design; when a comment and the live rendered reference
disagree, the **current render wins** — verify against it, not the comment. This
governs how you read **Y**; it does not soften the
rule below that *your implementation's* evidence must be the **render**, not the
DOM — opposite sides of the comparison.

**Four axes — name which one a claim covers; never conflate them.** A UI compares
on four independent axes:
- **structure** — which sections / components / chrome / affordances are
  **present** (vs absent), in what order, grouping, nesting / DOM;
- **styling** — the rendered *look* of what is present: font size / weight,
  colour, spacing, radius, shadow; each affordance's **glyph** (a star, a caret, a
  control); overall layout dimensions;
- **content** — the words / copy;
- **data** — the numbers / rows / entities.

A "looks the same" task is almost always **structure + styling**, with content and
data allowed to differ. "Same sections in the same order" is a **structure** claim —
it is **not** evidence of styling parity and must never be reported as "matches" /
"looks the same." And do not "fix" the **data** (swap a persona, seed rows) to
answer a **styling** complaint: that changes an axis the user did not raise and
leaves the one they did.

**Classify every diff structural vs cosmetic — and get structural parity first.**
Structural = different components, a different grouping / column / tab model, a
different page composition — the **structure** axis above (presence, grouping,
composition); cosmetic = colour, radius, spacing, glyph — the **styling** axis.
(Same two axes, renamed for the parity decision: presence/composition is
structural; the rendered look of what is present is cosmetic.) Establish
structural parity first (same components, same grouping, same composition), then
pursue cosmetic. **Never characterise a structural divergence as "close", "mostly
there", or "1:1"** 🚩: a board whose columns are `[Unclassified, Manual, Planned,
In progress]` when the design's are `[Up next, In progress, In review, Live]`, or a
flat filtered list where the design groups by team, is not "nearly there" — it is a
**different screen**, a rebuild, and calling it close is a category error that
destroys stakeholder trust. If the structure differs, say so plainly and size it as
a rebuild, not a tweak.

**A structural / proxy check is not visual evidence.** A section-presence check, an
"element-by-element" DOM / heading diff, a passing test, or loaded data are all
**proxies** for rendered appearance, not the appearance itself (`report-format.md`,
the proxy trap — *structure / DOM order / section-presence* is its UI instance). To
claim rendered parity, diff the **rendered appearance of the default state** against
Y: a screenshot and/or **computed styles** — the styling-axis properties above,
side by side. Anything less names its proxy and says the render was not checked.
Beware the specific dodge **"I diffed the *rendered* structure"**: "rendered
structure" is still the **structure** axis — it proves the sections rendered, in
order, not that they *look* like Y. Opening the page confirms structure rendered;
rendered **appearance** is the styling properties, and only a styling diff shows it.

**Do not move the goalpost you measure against.** If the work changed the
configuration that *defines* the default surface — the env default, a seed, a
feature flag, the demo persona, a local default — that change is itself part of the
artifact under review. Disclose it, and check parity against the **pre-existing**
default, not the one you just authored. "Verified on the default state" *after*
reconfiguring what "default" means is a claim about a surface you wrote, not the one
the user is served (general form: `report-format.md`, a self-reconfigured surface is
a proxy).

**Enumerate every diff in one pass before fixing any.** Finding diffs one at a time —
fix, re-declare "done," the user finds the next — is the loop that burns trust and
manufactures the repeated false ✅. Start with the single fastest discriminator: a
**gross-dimension diff** — the total height / width of the compared surface. A large
delta (one surface markedly taller or wider than Y) is by itself evidence styling
parity does **not** hold, before any element-level work. Then do a **full
side-by-side of the whole surface**, list every styling / placement delta at once,
and fix against that inventory; the parity claim is made only when every row is
closed or owner-accepted.

**Told "not the same" → disambiguate the axis before acting.** One question — "the
layout / structure, the styling (fonts / spacing / colour / chrome), the copy, or the
data?" — costs one turn; guessing wrong costs many. After **one** wrong guess, **ask,
do not guess again** (the multi-hour chase is: guess the data is sparse → guess a
contrast number → guess the persona → the user finally says "styling").

**The reference is the source of truth for styling, not your memory of it.** Re-open
Y and compare the **specific element, at the specific breakpoint, in the specific
theme** — styling differs by all three; a remembered impression of Y is not a
comparison.

**Match by measured device-pixels, not user-space units — equal user-units ≠ equal
pixels.** When two renderers apply different transforms or zoom (a thumbnail beside a
full view; an SVG drawn at ~1.4× device scale beside one that fills its container at
~9.6×), identical user-space values — stroke widths, font sizes, gaps — render at
wildly different pixel sizes, so tuning one to match at a single zoom breaks it at
another. Express a parity target as **measured device-pixels at the actual render
scale**, compute the **scale ratio** between the two renderers, and derive the second
implementation's values from the first × that ratio (or unify to one component).
Persistent **oscillation of one property on the same axis** — too thick → too thin →
too thick, each "fix" trading one mismatch for another — is the tell that the same
visual concept is implemented **twice at different scales**, not that the parameter is
wrong: stop tuning and measure (the stop-tuning discipline is *Repeated owner
rejection* above). And validate the **measurement target itself** — measure the
visible ink, not a transparent overlay or focus-indicator path a DOM query happens to
return first.

## Enforcing gate (Phase 6 imprint)

A standard with no gate is advisory (SKILL.md Phase 6: *pair each imprinted
standard with the gate that enforces it*). When imprinting into a project that
ships a UI, pair this reference with a UX-evidence gate — held to the skill's own
gate discipline: **a gate must tell "could not check" from "found a problem,"
fail *open* on the former, and never be stricter than the standard**
(`frontend-a11y.md`, the `innerText` and disabled-contrast traps; SKILL.md
Phase 1, gate-vs-standard). Three gates for any UI change, in descending
confidence of what they can prove — plus a fourth that fires only on a parity
task:

1. **Screens-changed evidence — the artifact, plus the inspection it demands.** On
   any diff that can change a rendered page, require a screenshot of each affected
   route at a narrow and a wide width (e.g. 390 / 1440), or an explicit `No UX
   change: <reason>` line. A screenshot proves a human/agent *looked*; it does
   **not** prove the render is correct — and "screenshot attached" **with no cited
   inspection** is `unverified`, not `verified` (the treatment a parity claim with no
   named surface gets, #192). The defects that survive every other gate are the ones
   only a look at the image catches, so a UI status **names what it inspected** from
   this checklist (defined once here; a status cites the items):
   - **overlap** — no two text / interactive elements intersect (mechanical proof:
     the bounding-box non-intersection assertion, `testing-and-evals.md`);
   - **clip / truncation** — no unintended ellipsis or cut glyph at the narrow width
     (`scrollWidth > clientWidth`, same file);
   - **contrast** — text meets AA against its *painted* background
     (`frontend-a11y.md`);
   - **disabled-looks-disabled** — a functionally disabled control is *visibly*
     disabled (cursor / opacity / painted colour, not only the attribute; the
     *no-dead-controls* interaction-completeness rule above, seen in the render);
   - **state named** — which data state the shot is of (empty / loading / error /
     populated), so an absence reads honestly (gate 2's state coverage; the
     empty≠all-clear rule above).

   A screenshot with an unstated inspection is an artifact read as the verification
   it is not.
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

4. **Parity differ (parity tasks only — proves *equivalence*, not just that a human
   looked).** For a "make X match reference Y" task, build a mechanical differ
   **before** any pixel-matching and gate every "matches" claim on it. The differ
   drives both the reference and the target for each screen and emits (a) a
   side-by-side + pixel-diff **image** and (b) a **structured** mismatch list — which
   nav / tab labels are present or absent on each side, the header strings, and
   bounding-box geometry deltas for key elements. **The artifact shown to a reviewer
   is the diff image, never a sentence.** **Render both sides at the same viewport
   width** and diff the corresponding region — a cropped or scaled screenshot of
   **one** side is a **hypothesis, not evidence**; never infer a present/absent delta
   from one side alone. Before recording an element as app-only or design-only,
   **confirm its state on the other side**: present-but-collapsed,
   present-but-**disabled-by-data** (a stepper bound to one item has nothing to step
   to), or present-in-a-menu — "absent in this crop" is not "absent in the design".
   This is the evidence that feeds the classification (`migration-parity.md`,
   *restyle-an-app-only-feature*): a delta that does not exist has no bucket, and every
   wrong inference here is one destructive edit — a removed control, a duplicated
   element — away. **🚩** a "missing" / "extra" parity call whose only evidence is a
   one-sided crop, or made with the other side's state unchecked. Load a no-routing
   prototype **once and
   click-navigate** its in-page tabs (it has no per-screen URL to fetch), and diff
   against an existing **running build** of the design if one is in the repo rather
   than reverse-engineering its source (reference-fidelity order, "Looks the same"
   above). It diffs **chrome / structure / styling, not text values** — diffing the
   numbers would flag real data as a mismatch and tempt the fix that fabricates
   (`migration-parity.md`). What it **cannot** prove: an intentional improvement from
   a regression, and its pixel threshold is **agreed, not derived** — a human still
   owns the ship call. **Parity is *set equality*, not containment — run the
   present-or-absent list above in *both* directions.** Produce it per screen as
   **design → app** (what the design has that the app lacks) *and* **app → design**
   (what the app renders that the design does not); an element on exactly one side is
   a finding **regardless of which side**, and the app→design half is the one that
   gets skipped. The **operative test** for an app-only element — *does removing it
   lose a user capability?* If **no**, it is pure **decoration** (an extra header, a
   "Showing N of N" line, a duplicated label): default **remove-to-match**, and
   "intentional extra" is the rationalisation that ships the mismatch. If **yes** (a
   per-card upvote, a filter bar, a view tab, a deep-link button — removing it removes
   upvoting, filtering, navigating), it is a **feature**: the default is **not**
   escalate-and-wait but **restyle it into the target's design language**. Deleting it
   to match the mock is a **High** do-no-harm finding, never self-certified.
   `migration-parity.md`'s *restyle-an-app-only-feature* rule governs the
   classification (and the re-express-in-the-target's-own-primitives mechanics), its
   severity, and the exception ledger; escalation to the owner is the **fallback** when
   no target primitive fits, not the whole answer.
   Scope all of this to **chrome / features**; **data** (values, counts, series)
   legitimately differs (`migration-parity.md`). *Done* on a parity task = the
   design→app list is empty; the app→design list is empty **or every entry is
   resolved** — restyled into the target's design language, decoration removed, or an
   owner-adjudicated keep/removal (a bare app→design list is not an automatic differ
   fail — the differ can't tell an intentional improvement from a regression, so that
   half routes to classification and, where needed, human adjudication); and the
   pixel delta is under the agreed threshold for every screen in the correspondence
   table, with those diff images attached — never an assertion.

Ship these **idempotent and additive**, per Phase 6 — detect-and-stop if
present, add only what is missing, defer to an existing style guide (the parity
differ only when the task is a parity task).
