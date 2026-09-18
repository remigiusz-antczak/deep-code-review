# Production-grade product playbook — build to the bar (G3 Design)

**Read this when** you are shaping a user-facing product surface in G3
Design, so you build to the domain-P quality bar up front instead of
discovering the gaps in review. It is the positive, build-time companion to
`deep-code-review`'s domain P (`product-ux-quality.md`): domain P reviews a
finished surface for defects; this file gives the build-time patterns to build
to, and pairs each with the review axis that verifies it.

## The build→verify direction
A review bar is written to catch what is wrong. Even where domain P states a
positive standard, it is framed for the reviewer as a pass/fail axis, not as a
build spec — and a defect list read as a build spec produces the minimum that
passes review, not a production-grade surface.
So build to the defaults below in G3, then verify each at G6 review — on the
G5 headed-browser evidence — with the paired domain-P axis. When a build
default and a review axis appear to disagree, the review axis is canonical (it
is the enforced gate); nothing here loosens it.

## Do not restate the review axes — build to them
Most of what makes a surface production-grade is already stated once, as an
enforced review axis in `deep-code-review`'s `product-ux-quality.md`. Build to
those; do not copy them here (a second copy is the duplication this suite
exists to condemn). The pairing — build default → the axis that verifies it:

| Build to this default | Verified by (`product-ux-quality.md`) |
|---|---|
| Every primary unit carries a *derived* why-it-matters signal — what changed, why it matters, the next step — never fabricated | *Actionability* |
| The default order serves the user's job; signal over recency; each sort mode is self-evident and measured-distinct | *Ranking & sort-mode legibility* |
| Progressive disclosure — the summary is self-evident, depth is one interaction away | *Self-evident over explained* |
| One component per concept across modules; scope-aware copy for single-vs-aggregate | *Unified across modules*; *One component at two scopes* |
| Every interaction loop closes — loading, empty, error, success, and a focus/keyboard sibling for every action | *Interaction-completeness*; *Every data state* |

If a pattern you need is in that table, build it and move on — its home is
domain P, not this file.

## What this file adds — the build-time patterns domain P does not spell out
Three positive patterns the review axes assume but do not state as a shape,
because a review catches their *absence* case-by-case while a builder needs
the *form* up front.

### 1. Job-first information architecture
The primary surface answers the user's core decision first — not "here is all
the data, arranged neatly." Before laying out a surface, name the one
decision or job the user opened it to make, and make the view that serves it
the default: above the fold, ahead of any secondary data. Two domain-P axes
review this — *most-actionable-first* for first-paint placement, and *Ranking &
sort-mode legibility* for which view and order serve the job — and the build
default is to derive the layout *from* the job, rather than arrange the data
first and hope the job is served.

The job differs by surface shape. Three common shapes — illustrative, not a
taxonomy to complete:
- **A monitoring / metrics surface** leads with the exception: what breached,
  what is off-trend, what needs a decision now — not an even grid of every
  metric at equal weight. The healthy majority is context, not headline.
- **A stream / feed surface** leads with what changed, and why it matters to
  this user since they last looked — not a reverse-chronological dump where
  signal and noise share one font size.
- **An entity-relationship surface** (pattern 2) leads with the connection,
  not the record.

### 2. Lead with the relationship, not the record
When the product's value is in how entities connect — who knows whom, what
depends on what, how a thing reached its current state — the primary surface
makes the *relationship* the object: the path between two entities, the
shared context, the chain of dependence. A flat table of entities with the
connections buried one click deep inverts the value proposition: it fronts
the records a user could get anywhere and hides the graph that is the reason
to use the product at all. Build the relationship as the first-class view;
record detail is the drill-down, not the entry point. Domain P has no
dedicated axis for this — it is a build choice, not a defect class — but a
surface that buries its own core value reads as low actionability in review.

### 3. Density is a build target, not an afterthought
Choose the information-density target for each surface at design time and
build to it. A professional, high-frequency tool earns trust by showing
enough at a glance; it does not spread three fields across a screen of
whitespace. Domain P's *density / footprint* axis reviews this after the fact
(footprint must track information). The build default is to *choose* the
density baseline for the surface's audience up front — an expert, repeat-use
tool is dense; a first-run onboarding surface is not — and lay out to it,
rather than inherit a component library's default spacing and discover the
waste in review. Record the chosen baseline in the G3 ADR beside the NFR
budgets.

## A note on precedent — cite conventions, never vendors
When a pattern above points to "what the best tools do," name a *public,
widely-recognized design convention* (as `product-ux-quality.md` does when it
asks you to name the top-product convention for a density target), never a
private product you have seen internally. Describe the pattern; do not vendor
a name. A named method or framework used as precedent gets a row in
`docs/standards-index.md`, same as any other cited standard.

## Where this sits in the gates
- **G3 Design:** choose the job-first IA, the relationship-vs-record framing,
  and the density baseline; record them in the ADR (`template-adr.md`) beside
  the interface and NFR decisions.
- **G5 Verify:** capture the headed-browser evidence on the exact route after
  the action — the receipt domain P is reviewed against.
- **G6 Review:** `deep-code-review` domain P verifies each choice against the
  axes in the table above, on that evidence.

The build default and the review axis are one standard seen from two ends.
This file is the build end, and defers to the review end on any conflict.
