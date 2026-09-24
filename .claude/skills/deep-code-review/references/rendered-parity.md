# Rendered parity — "matches / looks the same" claims (domain P)

Read this when a task or claim is a port, restyle, or design-parity match to a reference. Split from
`product-ux-quality.md`, which keeps the checklist and every rule an "above" pointer here names; the
enforcing gate is in `ux-gates.md`.

## Parity claims: the default state is the canonical surface

A "matches / exact / parity with `<reference>`" claim is only as good as the **surface** it was checked
against. The canonical surface is the **default state a user lands on** — signed-out / no-role /
no-persona / default route / local default — because it's the state a user is served **by default**,
before any role or persona is chosen: the entry state every user passes through. A mock, or a
hand-selected persona/role view, is a **secondary** surface: a parity claim resting only on it verifies
the wrong state (a first-time user never sees it). "More than the happy-path state" (checklist above) is
necessary but not sufficient — the **default state must be among the states checked**, and a claim
resting on a non-default surface must **name that surface** and say the default wasn't verified.

The general rule that a status is **downgraded the moment it carries a caveat** (and names the surface
its evidence came from) is defined once in `report-format.md` and applies to a parity claim unchanged —
the UI-specific case is that a parity ✅ resting on a **non-default surface** is not green.

## "Looks the same" is about rendered appearance — four axes, and a structural check is not a visual one

"Make X look like reference Y" is a task that frequently earns a false ✅. These rules sit **on top of**
the default-state rule above (never restating it); each is a distinct fidelity rule, or names an evasion
that passes a default-state check yet still ships a UI that doesn't look like Y.

**Read the reference at its highest available fidelity — this is the *reference* side, not your
output's.** The reference exists in three forms; prefer the highest present: a **running build** you
launch and diff against > the design **source** (HTML/CSS, stating the column model, tokens, and spacing
exactly) read property-by-property > a **screenshot** (a lossy picture — last-resort sanity check only).
Never reverse-engineer the source when a running build already exists in the repo, and never eyeball a
picture when the source or build states the spec precisely. **A stale source *comment* ranks below even
the screenshot** — a code comment claiming an element "moved" in some past design revision is not the
current design; when a comment and the live rendered reference disagree, the **current render wins** —
verify against it. This governs how you read **Y**; it doesn't soften the rule below that *your
implementation's* evidence must be the **render**, not the DOM — opposite sides of the comparison.

**Four axes — name which one a claim covers; never conflate them.** A UI compares on four independent
axes:

- **structure** — which sections / components / chrome / affordances are **present** (vs absent), in
  what order, grouping, nesting / DOM;
- **styling** — the rendered *look* of what is present: font size / weight, colour, spacing, radius,
  shadow; each affordance's **glyph** (a star, a caret, a control);
- **content** — the words / copy;
- **data** — the numbers / rows / entities.

A "looks the same" task is almost always **structure + styling**, with content and data allowed to
differ. "Same sections in the same order" is a **structure** claim — **not** evidence of styling parity,
never reported as "matches" / "looks the same." Don't "fix" the **data** (swap a persona, seed rows) to
answer a **styling** complaint: that changes an axis the user didn't raise and leaves the one they did.

**Classify every diff structural vs cosmetic — and get structural parity first.** Structural = different
components, a different grouping / column / tab model, a different page composition — the **structure**
axis above; cosmetic = colour, radius, spacing, glyph — the **styling** axis. Establish structural
parity first (same components, same grouping, same composition), then pursue cosmetic. **Never
characterise a structural divergence as "close", "mostly there", or "1:1"** 🚩: a board whose columns are
`[Unclassified, Manual, Planned, In progress]` when the design's are
`[Up next, In progress, In review, Live]`, or a flat filtered list where the design groups by team, is
not "nearly there" — it's a **different screen**, a rebuild, and calling it close is a category error
that destroys stakeholder trust. If the structure differs, say so plainly and size it as a rebuild, not
a tweak.

**A structural / proxy check is not visual evidence.** A section-presence check, an "element-by-element"
DOM / heading diff, a passing test, or loaded data are all **proxies** for rendered appearance, not the
appearance itself (`report-format.md`, the proxy trap). To claim rendered parity, diff the **rendered
appearance of the default state** against Y: a screenshot and/or **computed styles** — the styling-axis
properties above, side by side. Anything less names its proxy and says the render wasn't checked. Beware
the dodge **"I diffed the *rendered* structure"**: "rendered structure" is still the **structure** axis
— it proves the sections rendered, in order, not that they *look* like Y; only a styling diff shows that.

**Do not move the goalpost you measure against.** If the work changed the configuration that *defines*
the default surface — the env default, a seed, a feature flag, the demo persona, a local default — that
change is itself part of the artifact under review. Disclose it, and check parity against the
**pre-existing** default, not the one you just authored. "Verified on the default state" *after*
reconfiguring what "default" means is a claim about a surface you wrote, not the one the user is served
(general form: `report-format.md`, a self-reconfigured surface is a proxy).

**Enumerate every diff in one pass before fixing any.** Finding diffs one at a time — fix, re-declare
"done," the user finds the next — is the loop that burns trust and manufactures the repeated false ✅.
Run one foundation-first gate, `scripts/parity_differ.py --workflow` (capture: `templates/parity-capture.md`):
tokens, then primitives (a FOUNDATION/PRIMITIVE style row — a property or type role off in 2+ sections
— blocks every section: fix it once), then per-section inventory (completeness is judged **only**
there) + styles; progress = `sections passed k/n`; `--report` is the visual pass before "ready".
The orchestrator spot-checks a harness's pair count before trusting its verdict (`--min-pairs N`, your
floor, on either differ; `--style-min-pairs N` for style): too few pairs = an empty or wrong page, never a pass. Size, height, width, or bounding boxes are never
completeness or "aligned" evidence; geometry proves only layout defects (overlap, clipping, viewport fit
— `testing-ui.md`). Then do a **full side-by-side of the whole surface**, list every styling / placement
delta at once, and fix against that list; the claim is made only when every row is closed or owner-accepted
(accept file: owner-authored only).

**Told "not the same" → disambiguate the axis before acting.** One question — "the layout / structure,
the styling (fonts / spacing / colour / chrome), the copy, or the data?" — costs one turn; guessing
wrong costs many. After **one** wrong guess, **ask, don't guess again** (the multi-hour chase is: guess
the data is sparse → guess a contrast number → guess the persona → the user finally says "styling").

**The reference is the source of truth for styling, not your memory of it.** Re-open Y and compare the
**specific element, at the specific breakpoint, in the specific theme** — styling differs by all three;
a remembered impression of Y is not a comparison.

**A self-inconsistent reference is reconciled to one canonical interpretation before you build — you do
not copy the inconsistency.** The reference is the styling source of truth (above), but a real design
reference often **contradicts itself**: the same component drawn two ways on two screens, a spacing
token whose value disagrees with its own usage, a flow whose steps don't match its own summary. Copying
that verbatim ports the contradiction into the product — now an *implementation* bug (harder to spot and
fix) rather than a design one, and "match the reference" can't adjudicate a reference that disagrees
with itself. When the reference conflicts with itself, **surface the specific conflict and reconcile to
one interpretation first** — pick the reading the rest of the design implies, or raise it as an owner
decision (an A/B of the two) — and keep the **reconciliation separate from the build**, so the chosen
interpretation is explicit and reviewable, not silently resolved by whichever screen you happened to
copy last.

**Match by measured device-pixels, not user-space units — equal user-units ≠ equal pixels.** When two
renderers apply different transforms or zoom (a thumbnail beside a full view; an SVG drawn at ~1.4×
device scale beside one that fills its container at ~9.6×), identical user-space values — stroke widths,
font sizes, gaps — render at wildly different pixel sizes, so tuning one to match at a single zoom
breaks it at another. Express a parity target as **measured device-pixels at the actual render scale**,
compute the **scale ratio** between the two renderers, and derive the second implementation's values
from the first × that ratio (or unify to one component). Persistent **oscillation of one property on the
same axis** — too thick → too thin → too thick, each "fix" trading one mismatch for another — is the
tell that the same visual concept is implemented **twice at different scales**, not that the parameter
is wrong: stop tuning and measure (the stop-tuning discipline is *Repeated owner rejection* above).
Validate the **measurement target itself** — measure the visible ink, not a transparent overlay or
focus-indicator path a DOM query happens to return first.
