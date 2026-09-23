# Product UX quality — the "at-home" bar (domain P, design half)

Read alongside `frontend-a11y.md` when the target renders a **product UI a human operates** —
dashboard, table, form, chart, legend, metric display. Expands section P of `SKILL.md` (design
half). `frontend-a11y.md` owns a11y **correctness** (WCAG 2.2 AA, keyboard/focus, contrast, Core
Web Vitals, cross-view accessible-name pass); this owns whether the UI feels **at-home** —
conventional, self-evident, correct in every data state, cleanly encoded. Same spine as the rest
of the method: respect the existing design, separate a defect from a redesign, verify live,
ground every claim in a named standard — never "looks nicer."

Ground the design half in the tiers the skill already tracks: **WCAG 2.2** (colour, contrast —
via `frontend-a11y.md`), **Nielsen's usability heuristics** (named, not URL-cited — by-name list
in `README.md`), and the public precedent of top products (Linear, Stripe, Notion, Vercel,
Figma, Datadog, Google/Material, Robinhood) — named the way this skill already names Cursor,
Copilot, and OWASP: no new URL, version, or date the reviewer did not fetch (principle: no
fabrication).

---

## Matching a convention is an observation, not a licence to redesign (read first)

Mirrors `frontend-a11y.md`'s "Respect the existing design" — the rule keeping this reference
net-positive on every axis. A product-UX finding **improves** the product; it must never
silently restyle it.

1. **Separate the defect from the redesign.** A blank screen on a reachable state, a delta
   coloured the wrong way, a legend that is a wall of prose, a dead control — these are
   **defects**, fixed in place, minimally, preserving the existing look. A change that alters
   layout, spacing system, type scale, component set, or brand *to match a convention* is a
   **redesign** — an owner decision, not a review fix.
2. **Surface the convention gap under "Decisions needed (owner)."** When a design deviates from
   a named top-product pattern (legend, delta, empty state, date picker, table), record it with
   the precedent cited and the **minimal-visual-impact** fix offered first — as
   `frontend-a11y.md` handles a layout/brand change. Notice the gap; let the owner decide.
   "Looks nicer" is not a reason — nor is "the convention says so."

---

## Repeated owner rejection is a redesign trigger — surface options, don't tune (or impose)

The section above bars a redesign driven by *your* taste; this is its complement: a redesign
driven by the **owner's own repeated rejection** of the same element is warranted — but as
options the owner chooses, never a change you tune your way into or impose. Both obey principle
5 (*respect the existing design; separate a defect from a redesign; surface it, don't impose
it*).

- **Trigger: the owner rejects the same element two or more times** ("bulky / confusing / too
  heavy / looks wrong"). That repetition — not a reviewer's aesthetic read — is evidence the
  approach is **structurally** wrong, not under-tuned. A first rejection is feedback to apply;
  the *same* rejection twice says the structure, not the parameters, is the defect.
- **Stop tuning.** Nudging padding, arrows, spacing, or counts can't remove a structural defect
  (three overlapping rings don't stop overlapping because the arrows moved). Re-tuning after a
  second identical rejection is the failure this rule names — the design-half form of principle
  9 (*root-cause, not symptom*): after the same failure twice, change the approach, don't repeat
  the fix.
- **The same move for a *verification* claim: repeated correction means your method is broken,
  not their patience.** A stakeholder repeatedly correcting your "it matches / it's the same" is
  evidence your **verification method** is wrong, not a cue to ask for more examples. Build the
  comparator (the **parity differ**, Phase-6 *Enforcing gate* below), show its diff, and report
  only what you actually inspected ("the nav now reads A · B · C, I looked at it") — never a
  blanket "it matches"; an honest "not yet verified" beats a false positive (principle 9: after
  the second false "matches", change the instrument, don't re-assert).
- **Name the structural flaw in one line**, then research how **two or three comparable
  products** (named, per *Match a named standard* below) solve the same problem — the muscle
  memory the new direction should borrow.
- **Hand the owner concrete options to choose — show, don't tell.** A side-by-side of two or
  three real directions is a decision the owner makes in seconds; a paragraph describing them is
  not. Product/redesign choices are owner decisions, never carrying Blocker/Critical gate
  language (SKILL.md Phase 5).
- **Variant/option bloat is the supply-side of the same smell.** N interchangeable ways to view
  or style one thing — seven style-toggle tabs on one diagram, eight overlapping list modes —
  reads as unfinished, not powerful: the *choice* is the defect, so **cut to one strong
  default**, not tune the set. Test: would a first-time user know why to pick one over another?
  If not, it's bloat, not flexibility. Distinguish redundant variants (overlapping modes,
  decorative toggles) from genuinely different tools (a diagram vs a table serve different tasks
  — keep both); keep the power path reachable behind **progressive disclosure**, off the default
  surface.

---

## Every data state — rule on each, not just the happy path

Every view is intentional and honest in **all five** states, each ruled on (finding, clean, or
`unverified`):
- **empty** — say what will appear and how to get it (never a bare void);
- **loading** — skeleton/spinner, no layout flash;
- **error** — what failed and how to recover, **never a raw stack or blank**;
- **partial** — some data present, some missing/degraded, shown honestly;
- **overflow** — too many rows → scroll/paginate/virtualize **inside the component's own
  container**, never breaking the page layout; a capped or sliced list also needs an explicit
  **remainder indicator** whenever more rows exist than are shown (below).

A blank screen or a raw error on a **reachable** state is a P0 "not-at-home" defect, not a nit —
severity by reachability, like any other defect. (Nielsen: visibility of system status; help
users recover from errors.) `frontend-a11y.md` owns the *phrasing/consistency* of empty states
across routes; this owns whether each state **exists and is honest**.

**A capped or sliced list needs an explicit remainder indicator whenever more rows exist than
are shown.** A `.slice(0, N)`, SQL `LIMIT N`, or `take(N)` rendering fewer rows than the
underlying `total` is truncating, not paginating, unless the cut is visible: a correct top-line
summary count ("142 issues") doesn't prove the itemized list beneath is complete — count and
rendered rows are independent reads of the same data, and nothing forces them to agree, so a
silent truncation reads as the whole set. Whenever `total > shown`, render an explicit remainder
— "+12 more," a page control, "Show all N" — never a list that just stops (Nielsen: visibility
of system status). **🚩**: a `.slice(0, N)` / `LIMIT` / `take(N)` render path whose length can be
less than a known `total`/count, with no adjacent remainder text or pagination control.

**A partial-apply operation's success counters must reconcile to the operation's own total —
when they can't, and nothing says why, the *partial* state above has quietly gone dishonest.** A
"paste/import N rows, apply what matches" endpoint typically buckets results (`applied`,
`skipped_duplicate`, `unresolved`) and also computes real per-row failure detail —
`error_count`, `errors[]` — from the same operation. The failure detail goes missing not from a
bad render branch but one layer earlier: the client's response type declares only the success
fields, so `error_count`/`errors` are dropped before any render branch could exist for them —
visible badges can sum to less than the request's own `parsed`/`total` with no indication
anything failed, an honest-looking partial render that quietly undercounts. Distinct from the
remainder-indicator rule above: there a list is truncated **in render** below a total the client
already holds; here nothing is sliced on purpose — the client's own declared type is narrower
than what the endpoint returns, invisible to anyone reading only render code. Detect by diffing
the route handler's actual response shape against the client-side type that parses it: any
server field absent from the client type — especially a count or array of failure reasons — is a
candidate silent drop; confirm by checking whether success counters can sum to less than the
total. **The remedy is both halves — the client type declares the failure fields *and* the
render surfaces them** (a count, or the first/aggregate reason); widening the type with no
render branch just relocates the silence a layer down. **🚩**: a hand-maintained client response
type narrower than what the endpoint actually returns, especially one dropping an
`errors`/`error_count`/`rejected` field; visible counts that can't be reconciled to the input
total with no "N failed" surface.

**An empty state must not imply a conclusion it hasn't earned.** "No rows shown" isn't "nothing
happened": an empty activity feed, an all-green board with no data behind it, or a zero-count
that's really an *uncollected* count all read as "all clear / no risk / no activity" when the
source may never have been queried. The empty state must distinguish *no data collected or
covered* from *collected, and genuinely none* — SKILL.md principle 2 (*an absence is evidence
only after a positive control fires*) at the UI layer. Name the coverage, not only the remedy: a
bare "Nothing here" over an unprobed source is a false all-clear, not an honest empty.
(`data-quality.md` §8: same rule where the number is *scored* rather than *shown*.)

**A hardcoded empty-state message that asserts a cause is a fabricated cause the moment more
than one path reaches it.** "No results — try changing filters" names one cause (an over-narrow
filter) and one remedy; honest only if a filtered-to-zero query is the *only* way `count === 0`
renders. Once a fetch error, a permission denial, and a genuine empty all fall through to the
same zero-rows branch, that copy is a guess dressed as diagnosis: a permission-denied user is
told to change filters that were never the problem, a fetch failure reads as "no matches"
(Nielsen: help users recognize, diagnose, and recover from errors). Before trusting the copy,
enumerate every path that reaches the empty branch and confirm each matches the case the message
describes; where paths diverge, branch the copy per cause or fall back to a cause-neutral empty
rather than let one hardcoded string speak for all. Extends, not restates, the coverage rule
above: that asks whether the *source was queried at all*; this asks whether the empty state's
*named cause* holds on every path that reaches it.

**A value's *stakes* decide whether degrading a fetch failure into "empty" is acceptable at all
— a third axis, independent of coverage and cause.** The coverage rule above asks whether the
copy *names* whether the source was probed; the cause rule asks whether a *stated cause* holds
on every path that reaches it, and allows falling back to a **cause-neutral empty** when paths
diverge — this rule narrows that fallback: cause-neutral wording isn't enough on a
**definitive-record surface**. A low-stakes, **supplementary** value — a related-items rail, an
optional recommendation widget — may reasonably let a fetch failure fall through to its ordinary
empty/blank render; the cost of a wrong read is small. A value the user reads as a **definitive
statement about history or state** — an audit log ("this never happened"), a security-events
list, a balance or count a decision rests on — carries no such exemption: it **must surface a
distinct, retryable error state**, never the same branch as a genuine zero, because here "empty"
*reads* as "confirmed none," and a swallowed fetch error becomes a false all-clear no copy can
fix — the defect is architectural, not lexical. Distinct from `data-quality.md` §8's
observed-low-vs-unobserved rule (a *scored* value, measured wrong) and from the silent-swallow 🚩
in `domain-f.md` / `reliability-error-handling.md` (an error *discarded* at the code
layer, with no log or signal): here the fetch error is caught correctly, and the defect is which
**rendered** state a correctly-handled failure is allowed to collapse into.

**An empty list must disclose *why* it is empty — a filter or search removed everything, versus
nothing exists yet — and any header, count, or banner above it must be gated on content, never
implying rows a filter has hidden.** These are two halves of one defect: the render never
separates *filtered-to-none* from *genuinely-none*. On the **copy** side, a single
`items.length === 0` branch reuses one reassuring, success-styled line ("You're all caught up")
for both — honest onboarding when the account is truly empty, but a **false completeness claim**
when a search matched nothing while N real rows sit hidden, so the user reads the task as done
and abandons it. Unlike the cause rule above — where the copy *names* a cause and the fix is
lexical — here the copy names nothing; it asserts a *state*, and the signal that falsifies it is
**already in the component's props and merely unread**: an unfiltered `totalCount` beside the
filtered `items.length`, or a `searchActive`/`filterActive` flag a sibling list already threads.
That single cause-neutral fallback is **not enough here**, because the two truths need different
*next actions* — reserve the positive/"nothing exists yet" copy for a zero **unfiltered** total,
and when the total is non-zero but the view is empty render a neutral "no matches" state
carrying a **clear-/adjust-filter affordance** (narrowing the fallback the same way the stakes
rule above narrows it for definitive records). On the **chrome** side, a section's header,
count, "N done" badge, or a "see all / show breakdown" affordance emitted **outside** the
content-presence conditional — a title rendered unconditionally above a row built by
`list.filter(...)` that can come back empty, with no sibling empty branch — leaves a heading
over a blank strip and an affordance pointing at nothing (a dead control, *No dead controls*
below); gate the chrome on content-presence, or pair it with an explicit empty/no-match fallback
under the same conditional. **Detect** by grepping the empty-state string and enumerating every
path that renders it — one success-styled line reachable from both a filtered and an unfiltered
branch is the copy defect — and by finding a `.filter(...)`/search-fed list whose header, count,
or affordance is emitted before it with **no** adjacent `length === 0` branch. Distinct from the
coverage rule above (whether the source was *probed* at all) and from the *dead filter option*
below (an option matching zero rows in **any** data, versus a valid filter matching zero
**now**); `frontend-a11y.md` assumes the classes of emptiness already exist and enforces one
voice and one next action per class — this owns whether the filtered-vs-genuine distinction is
drawn at all.

## A correct loading/failed signal is only as good as its least careful consumer

The stakes rule above governs what a **correctly-handled** fetch failure may render as; this asks a
narrower, later question — **given** a hook/context whose contract already separates loading/failed from
a confirmed value honestly, does **every** consuming surface actually read that signal? A shared hook
reused across sibling UI surfaces (a provider/context, so two renders share one fetch instead of
duplicating it) can expose its readiness/error field correctly and still ship the exact failure it was
built to prevent, one layer up: one consumer branches on the field and renders honestly; a second, off
the **same shared instance**, destructures only the value and renders it raw. The same transient failure
surface A discloses, surface B renders as a confident wrong zero — indistinguishable from a genuine
"none" — with the only textual disclosure sitting elsewhere on the page, in a component the reader may
never reach.

**A correct contract does not imply a correct consumer, and one correct consumer does not imply the rest
are.** A reviewer who audits the hook plus the one call site that clearly does it right, and concludes
"this is handled," has verified the contract, not its adoption — the same gap the shared-component
adoption-is-total and divergent-props rules name for a shared **component** (Unified across modules,
below), but a different **stakes** class: divergent props there is a visual-consistency defect (a
feature chip present at one mount site, absent at another); a sibling ignoring a readiness signal is a
**data-honesty** defect (a wrong value rendered as settled fact) — hence its place in this data-state
neighborhood, not the component-consistency one.

**Detect** by grepping the hook/context **name** itself, not just its file, to enumerate every consumer
of the shared instance — a component-scoped search misses a sibling elsewhere on the page; check each
independently for a readiness/error branch, never inferring from one correct consumer that others do
too. Verify by forcing the shared fetch to reject and loading the page at **every** consuming surface,
not only the one already known to handle it correctly.

Same all-consumers/all-call-sites sweep discipline as a write-guard covering every mutation primitive or
a soft-delete scope covering every read (`data-quality.md` §5, §6), and a normalization fix required at
every query call site (`i18n-l10n.md`) — a shared correctness property holds only where every consumer
actually exercises it, not wherever the built-once thing merely exists.

**🚩**: two or more components consuming one shared hook/context instance where only some destructure and
branch on its readiness/error field; a consumer destructuring only the value field, with no
readiness/error check anywhere in that render path, while a sibling consumer of the same instance does
check it.

## A reverted optimistic write is the one error path that skips the app's shared safe-message mapper

The five-states *error* rule above bars a raw stack on any failure; this is its consistency twin,
targeting the one seam that survives it. A mature client centralises user-facing failure copy in a
shared mapper — `toSafeMessage(err)` / `toUserMessage(err)` — turning any thrown value into one honest,
non-leaking sentence, and the normal request path calls it everywhere. But an **optimistic mutation**
(apply the change locally at once, fire the write in the background, roll back on failure) often grows
its `onError`/rollback handler by hand, and that handler renders `(err as Error).message` **directly** —
the single call site that skips the mapper the rest of the app trusts.

It survives review because a **non-2xx response is usually safe**: the fetch wrapper throws a *curated*
error whose `.message` is already a clean sentence, so a test mocking a 500 shows correct copy and the
direct `.message` read looks fine. The leak is on the **transport** path — offline, DNS failure, CORS,
an unreachable server — where `fetch()` itself rejects with a browser-native `TypeError` whose text is
UA-specific ("Failed to fetch" / "Load failed" / "NetworkError when attempting to fetch resource"),
shown verbatim where the rest of the app would show its fixed fallback — an internal, inconsistent,
sometimes sensitive detail surfaced to the user and, if the revert writes its status into an `aria-live`
region, **read aloud** to a screen-reader user (`frontend-a11y.md` owns the announced-surface phrasing).
The defect is not "a raw error is rendered" — the states-block grep below already owns that — it is the
**asymmetry**: a shared mapper exists and is called at sibling call sites, and this one path bypasses
it, so the app speaks two different error languages depending on which write failed.

**Fix — one mapping boundary.** Every user-facing failure string, a reverted optimistic write's
included, goes through the same shared mapper the normal path uses; the revert handler passes the caught
value to the mapper rather than reading `.message`. Acceptance: a test that makes `fetch` reject with a
raw `TypeError` asserts the rendered (and, if announced, the `aria-live`) text equals the mapper's fixed
fallback, not the raw message — a test mocking only a curated 5xx won't catch it. Same all-consumers
discipline as the least-careful-consumer rule above, a different **stakes** class: there a sibling
ignoring a shared *readiness signal* renders a wrong confident value (data-honesty); here a path
bypassing the shared *message mapper* leaks a raw internal string (a user-facing leak — cross-ref
`security-appsec.md` A02 verbose-errors / A10 leaked-internals and `domain-b.md`'s
error-class-not-upstream-response-bodies rule). `reliability-error-handling.md` owns the *server* error
contract; this owns which client path renders it.

**🚩**: a shared error-message mapper (`toSafeMessage` / `toUserMessage` / a toast helper) called at
ordinary request call sites, together with an optimistic mutation's `onError` / `catch` / rollback
handler that reads `(err).message` or renders the error object **directly** instead of calling that
mapper — narrower than the generic *`catch` rendering `err.message`/stack* grep in this file's states
block, which flags the raw render but not the bypassed-shared-mapper asymmetry.

## A read-failure that seeds an editable form turns a misleading display into a destructive write

The read-failure-honesty family above governs what a failed read may **render**; this is its sharper twin
— what a failed read may **write**. When the same conflated failure seeds an **editable form** whose
save is a **full-object replace** (a `PUT`/upsert, not a partial patch), the failed read stops being a
misleading display and becomes a silent **data-wipe**. A client fetches "the current value of X" to seed
a create-or-edit form; the loader's `catch` sets an error message and leaves the value at the same falsy
sentinel (`null`/`{}`) it uses for "nothing exists yet," so the form's `initial`/`defaultValue` falls
through to blanks on **both** a genuine new record and a transient blip (a 5xx, a timeout, an auth
hiccup, a rotated token). The user, shown a blank "create/claim" form, fills it in and saves — and
because the write is a replace, it discards whatever real value existed before the read failed. The
prior value survives only in a separate audit/history log if one exists; the current-state pointer the
dashboards and cards read is now wrong until a human notices.

It is worse than an ordinary missing-data bug because an unconfirmed **read** becomes an affirmative,
unreviewed **write** — the cost compounds from "misleading display" to "corrupted state" — and it passes
review because each half is normal in isolation: the `catch` sets an error message (fine), a `PUT` that
replaces a row is ordinary (fine); only their **composition** is the defect, and it lives in no single
file. Showing the error banner does not close it — that handles the display while the destructive write
stays wide open.

**Fix — model "do we know the current value" as an explicit three-state**, `loading | error | resolved`,
where `resolved` covers both *found* and *confirmed-empty* and is never the same nullable used for
"confirmed absent." Then **gate the write on that state**: disable or hide Save while the read is
`error` (or require an explicit "replace with blank values" confirm); or make the save a **partial/merge
patch** so an untouched field is never blanked. Never let an unresolved read's absence flow into a
replace-style write's default seed.

**Detect it** by grepping `catch` blocks that set an error-message state **without** flipping a distinct
"unresolved" flag consumed by the *same* render path that feeds a form's `initial`/`defaultValue`; for
each, read the write handler to confirm replace/upsert vs patch. If both hold, a transient read error
yields a false "nothing here" form whose save clobbers real state. Verify live: force the seed fetch to
reject, open the form, save, and confirm the record is **not** blanked — the logic test alone will not
show it.

This needs **no concurrent writer** — it is not a lost update, and a version-column/CAS guard does not
catch it: there *was* a valid prior version, and the write simply replaces it with blanks, so the
compare-and-set passes. (`concurrency-shared-state.md` owns the persistence-layer twin — a
corrupt/unreadable store must not `catch → write []/{}` and clobber last-good bytes, and absent-file
empty-init is a different branch — the same wipe with no human and no form, plus the lost-update/CAS
bullets this is distinct from.)

**🚩**: a load-to-edit form whose `initial`/`defaultValue` is seeded from a fetch whose error path
collapses to the same empty/nullable as confirmed-absent, combined with a full-object replace/upsert on
save and no disabled/gated Save while the read is unresolved.

## A reversible action reads as a delete when nothing shows the record persists

When an action **presented as non-destructive** — resolve / archive / dismiss, backed by a
retained column (`resolved_at`, `archived_at`) — removes the record from view while giving **no
cue that it persists, is reversible, or where it went**, the user cannot tell it from a hard
delete. Two failures:
- **Product-safety.** The action *reads* as destructive: a first-time user clicks "Resolve,"
  watches the row vanish with no "Resolved" state, no undo, no reachable resolved view, and
  reasonably concludes they deleted it — suppressing a reversible, low-stakes action and eroding
  trust in it.
- **Audit / history visibility.** When the retained trail is *meant to be reviewable*, a surface
  with no way to reach it makes that history effectively invisible — the data layer keeps a
  record the UI never surfaces. (The data is intact; the defect is visibility, not integrity.)

**The defect is the hidden reversibility, not default-hiding as such.** Hiding a completed item
is often the *correct* convention — an `is:open` list, an active-only board, an inbox that
archives out of view all hide a retained record on purpose, behind a well-known filter; those
are conventions, not defects (matching a convention is an observation, not a licence to redesign
— read-first opener above). A **soft-delete** (`deleted_at`) is out of scope: "reads as a
delete" is its *intended* behaviour; its concern is recoverability / trash-visibility, not this.
Like the actionability rule, this is **fail-open**: a heuristic can't tell a hidden-reversible
action from a deliberate convention, so a human adjudicates every hit — surface options, never
silently restyle.

The self-evident fix — how mature issue-trackers and code-review tools render a resolved thread
— keeps the record **in place, visually muted** (opacity or strikethrough) with a **status
label** ("Resolved"), or offers a clearly labelled, discoverable "resolved / archived" view.
Cross-checks: the affordance must **not rely on colour alone** (pair opacity with a label or
icon + accessible name, per *Never colour alone* below); a "show resolved / archived" path must
be **discoverable**, not a buried default-off filter with no cue; verify on the **running app's
default surface**, not only a unit test. Distinct from the honest-empty rule above (a *retained*
record hidden by a *reversible* action, not an empty state).

## Encoding hygiene — one visual channel per dimension

Never make **one channel carry two meanings**. The classic bug: colour encoding two independent
variables at once (green = both "instrumented" *and* "trending up") — ambiguous, and invisible
to an a11y-only pass. Split dimensions across channels — **shape/fill** for one, **colour** for
another, **position/size** for a third. Run out of channels ⇒ you have too many encodings; cut
some. Fewest encodings wins.

## Never colour alone — colourblind-safe as a method

`frontend-a11y.md` owns the WCAG rule (1.4.1 Use of Color; and the 1.4.3 disabled-control
exemption that a gate must not over-flag). This owns the **testable method**: pair every hue
with **shape, icon, or text** (▲▼ ↑↓ ✓ ✗ or a word) plus an `aria-label`. Colour reinforces;
shape carries the meaning. The one-line test: **it must read correctly in greyscale.** Works in
greyscale = works for the ~8% of men with deuteranopia, and for everyone.

## The metric / KPI delta standard

A near-universal pattern with a right answer (Stripe, Google Analytics, Mixpanel, Amplitude,
Robinhood, Linear, Material) — inventing a novel one here is a cost:
- caret **▲▼** (or arrow ↑↓) **+ the magnitude** (`▲ 3`, `+2.1%`) — direction alone never says
  *how much*;
- colour by **sentiment, not direction** — "up" is not always good; a drop in churn / cost /
  latency / error-rate is **green**. Key the colour to the metric's polarity
  (direction-of-good), not to up/down. Backwards polarity actively misleads — a correctness
  defect, not a taste one;
- muted **`—`** when flat; anchor the delta to its period ("vs last month") in the
  tooltip/`aria`.

## Data visualization — a chart must answer a question, legibly

The delta standard above governs a single up/down number; a **plotted series** is its own surface, and a
chart can pass every other rule here — no overlap, no colour-only status — while still answering no
question ("what is this on that date?" has no on-screen answer) or overstating what is known. Rule each
chart:
- **Scale is legible.** A value axis with tick labels **or** direct labels; a bare shape with no scale
  is decorative, acceptable **only** when explicitly marked decorative (`aria-hidden`) **and** the exact
  number it illustrates is printed beside it.
- **A value + its anchor on demand.** Any non-trivial chart returns, on hover/focus, the **value and its
  date/category**, reachable by keyboard, not mouse-only (`frontend-a11y.md` owns the *a11y* of that
  interaction; this owns that a readout *exists and returns a value*).
- **Don't imply the unmeasured.** Mark real samples (a dot per reading) and never smooth or fill a
  **line across sparse points** — nothing between measured points is implied. Two or three readings
  drawn as a continuous trend (a **sparkline** on a handful of readings is exactly this) is a fabricated
  trajectory, the visual form of principle 3 (empty beats fabricated).
- **A grid / heat-map / calendar cell needs a third state — event, collected-zero, not-collected.** A
  per-cell colour scale painting an **uncollected** cell the same as a genuine **zero-activity** cell
  fabricates data: the viewer reads "quiet" where the truth is "unknown / not yet observed." Give the
  not-collected cell a distinct, non-scale encoding (hatch / blank / explicit "no data"), never the low
  end of the activity ramp — the grid form of *Every data state*'s honest-empty rule above and of
  *observed-low vs unobserved* (`data-quality.md` §8).
- **Non-visual access to the numbers.** The chart is *additive* to a table or an `aria` summary, never
  the only path to the data; series are distinguished by pattern/label, not colour alone (*Never colour
  alone*).

## Confidence shown as a bare number is false precision — flag it

A confidence, priority, or match score surfaced as a **raw number** ("87%", "score: 0.92") claims a
calibration the pipeline usually doesn't have, and invites over-trust. It belongs on a **small set of
labeled tiers** — text plus a colourblind-safe cue (see *Never colour alone*) — not a percentage or an
opaque point score. **🚩**: a `confidence` / `score` / `priority` value rendered directly as `{n}%` or a
raw float with no defined tier label beside it; a model-authored number published as precision. (How to
*define* the tiers, and why source reliability and claim corroboration stay independent axes, is a
data-product-output rule — `product-output-safety`'s — not restated here.)

**Measure the field's distribution before building the display at all.** Even a *tier* is false
precision if the underlying signal is **near-constant** — measure it first, on real data. A
`corroborationCount` that is `1` on 16,008 of 16,012 rows makes a "confirmed by N sources" badge fire on
~0.02% of rows and read "1 source" everywhere else; a match-confidence that is `0.9` on ~70% of rows and
`0.8` on the rest is effectively binary, so "90% / 80% confidence" manufactures precision the pipeline
lacks. If the field barely varies, **showing it is false precision, not transparency** — drop it, or
reframe to something that actually varies (e.g. *how* an entity was matched, not a number). A misleading
signal is worse than an honest blank — empty beats fabricated (`data-quality.md`).

## A rendered tier / score / aggregate encoding must invert to its source rows

A confidence tier, match label, or **aggregate visual encoding** — a sparkline tick, heat-map cell,
count badge, rolled-up score — asserts something about **specific underlying rows**, so it must
**invert**: the viewer can resolve it back to the exact source it summarizes. Compute the continuous
intermediate if you like, but **publish only the tier** (the confidence-tier rule above); the acceptance
test is separate — **can the rendered mark be drilled through to the N artifacts that produced it?** A
tier or cell mapping to nothing checkable is decoration wearing a data costume: a real 5-event cell is
indistinguishable from an off-by-one, and no one can audit the roll-up. Applies to **aggregate**
encodings, not only per-row chips — a `count: 12` badge, a sparkline's last tick, a calendar heat cell
each owe a path to their 12 / reading / day's events. Orthogonal to the *decorative-chart* exemption
above (`aria-hidden` with its exact number printed beside it is fine for **legibility**): invertibility
then applies to that printed number/tier itself — not a second drill-path on the decorative shape.
**🚩**: a score / tier / sparkline / heat cell / count with no drill-through to the exact rows it
aggregates (un-invertible — can't be verified or corrected).

## A progress/attainment display with no honest reading is a fabricated "done" — show coverage, not a grade

When a product visualizes **progress toward goals**, constant pressure pushes an **attainment %** or
**grade** even when honest inputs don't exist — no current reading, no ratified rule for *which* metric
counts, an undefined lower-is-better direction. **Distinct from the confidence-tier rule above**: there
a reading *exists* but is shown with false precision; here **no honest reading exists at all**, so any
attainment number fabricates a "done." Review lens: "what's the denominator/rule, and is the current
value **measured** or **inferred**?" The honest alternative is **coverage/readiness** — "**N of M** key
results are measurable/instrumented" — computable without inventing a reading (given an enumerable M and
a defined "measurable"); where a reading is genuinely absent, render **"awaiting reading / not yet
measurable"** (an honest empty state, per *Every data state* above), never a manufactured value.
- **Enforce it structurally, not by convention.** A write-broker/observation gate that **refuses** (e.g.
  `422`) any claim asserting attainment or on-track status the system can't substantiate, so no path —
  human or agent — sneaks a fabricated grade in; and a **contract/doc stating "attainment is out of
  scope"** so a later "add progress bars" ask is triaged as *ratify a rule first*, not a quick UI edit.
- A display that would honestly render **"awaiting reading" on nearly every row is worse than no
  feature** — hold it (a legitimate BLOCKED-ON-OWNER: ratify the rule and instrument the inputs first)
  rather than ship a fabricated grade to fill it.
- **A ratio/coverage tile guarded by `total > 0 ? round(done / total * 100) : 0` renders a fabricated 0%
  for an *empty population* — "nothing to do" is drawn as "none done."** Mirror of the no-honest-reading
  rule above: there no current value exists, so *any* percent fabricates a "done"; here `done` and
  `total` are both real and measured, but the population is **empty** (`total === 0`), so the ternary's
  `: 0` sentinel paints a hard **0%** — the same alarming treatment a genuinely-behind row gets — when
  the honest reading is **not-applicable**: nothing to complete, not work left undone. The guard *looks*
  correct — it prevents a `NaN`/`Infinity` divide-by-zero, clears review, type-checks, never throws —
  the defect is its fallback **value** reads as an attainment, and seed/demo data usually has a non-zero
  `total`, so the empty branch rarely renders in dev. Fix: branch the *empty* denominator to a
  **non-numeric** state — `N/A`, a muted `—`, "nothing to do" — and reserve `0%` for
  `total > 0 && done === 0`, the real "has items, none done" a user can act on; a `100%`-for-empty
  fallback is the same fabrication, opposite sign. **Distinct** from the no-honest-reading rule above
  (reading *absent* — show coverage) and the honest-empty *list* rules under *Every data state*
  (filtered vs genuinely-none over **rows**) — this is a **scalar ratio tile** whose zero denominator,
  not a hidden row, is the trap. **🚩**: a percentage/progress/ratio render whose denominator can be
  zero, guarded by `total > 0 ? … : 0` (or `|| 0` / `?? 0`), whose fallback renders as a real percentage
  rather than not-applicable.
- **🚩** a `%-complete` / grade / progress bar with no measured current value (a fabricated "done"); an
  attainment number the pipeline can't substantiate rendered instead of an "awaiting reading" state or a
  coverage ("N of M measurable") metric.

## Actionability — a unit answers "why does this matter," not just "what happened"

The other domain-P rules prove a component **renders** correctly; this asks whether it **helps the user
decide or act**. A feed, dashboard, or brief can pass every render check and still be a **wall of
verified facts** — each unit a *fact + its source* with no *so-what / now-what*, a real UX defect
invisible to the rendering rules.
- **Every primary information unit carries a why-it-matters signal — derived, never fabricated.** A unit
  a decision depends on states *why it matters* through a **structural / derived** signal: a count ("3rd
  of its kind this quarter"), a recency-delta ("first activity in 60 days"), a graph-degree ("connects
  to N entities you follow"). **Hard rule (anti-fabrication):** the signal is computed from real data —
  **never a model-authored "importance score" or an LLM judgement of salience**, the content-layer
  cousin of the false precision the confidence-tier rule above forbids. A derived signal that barely
  varies is not a signal — measure its distribution first, exactly as for a confidence tier.
- **Where an action is possible, name the concrete next step** on the unit (follow, open, assign,
  dismiss), not a bare record the user must decide what to do with. A signal-led feed maps each event to
  a follow or next step; a relationship surface offers a next-best-action, not just a row (a pattern,
  not a product endorsement).
- **Most-actionable-first, and stable.** The highest-decision-value surface is in the **first paint and
  stable** — not deferred to a post-hydration `aria-hidden` island, nor pushed below fixed
  non-interactive summary chrome (cross-ref layout-shift / CLS in `frontend-a11y.md` and the
  density/footprint rule below). Which order serves the user's job is ruled on in the ranking section
  below.
- **Lead with what's new *and* why it matters** — a reader's first two questions are "what is it?" and
  "is it relevant to me?"; a unit answering only the first is half-built (the **Smart Brevity** pattern;
  `docs/standards-index.md`).
- **Defect vs redesign; the gate is fail-open.** Missing actionability on a decision surface is a
  **defect to surface**, not a licence to redesign a deliberately-terse product — separate the two,
  never carrying Blocker/Critical gate language on a product choice (SKILL.md Phase 5). The heuristic
  gate **warns and lists, never blocks** (unlike the fail-closed `ci-gates.sh` check-#6/#7): it flags a
  primary list/card whose unit is *fact + source* with no derived why-it-matters signal and no action
  affordance, and a top-value surface that is an `aria-hidden`-until-hydration island — but it **cannot
  tell "should be actionable" from "deliberately terse,"** so a human adjudicates every hit.

## Ranking & sort-mode legibility — the order is a product decision, not a default

The variant/option-bloat rule above targets view/style toggles; this extends it to the **ordering of a
feed/list itself** — the confidence-tier rule targets a *displayed* score, not the *ordering key*. The
gap between them: is the **default order** the one serving the user's job, and is each exposed sort mode
**self-explaining and measurably distinct**?
- **The default order serves the user's primary job** (signal / importance / soonest-to-act), not
  implementation-convenient reverse-chronological. Recency is a *mode*, rarely the right *default* for a
  decision surface. (Canonical home of the default-ordering rule the actionability section refers to.)
- **Every exposed sort/rank mode is self-explaining and distinct.** Each mode carries an on-demand
  one-line *"orders by …"* (tooltip / helptext), and the variant-bloat test applies: **would a
  first-time user know why to pick "Top" vs "Momentum"?** If not, it's bloat — cut to one strong
  default, the rest behind progressive disclosure, each self-labeled. Two modes producing
  **near-identical orders** are variant-bloat → collapse (measure the overlap, don't assume it).
- **The sort key needs a measured distribution — anti-fabrication (hard rule).** A key derived from
  real, varying signal is legitimate ranking; a sort by an **opaque or near-constant score is the
  ordering-layer form of false precision** — measure the key's distribution before shipping it as
  "ranking" (reuse the confidence-tier "measure the distribution first" rule above; a key that barely
  varies orders nothing). An order the user can't explain and the data can't justify is noise dressed as
  intelligence.
- **Multiple ordering regimes across surfaces** (a curated home *plus* a multi-mode feed over the same
  data) are a lot of ways to slice one dataset — consolidate, or cross-explain on-surface which regime
  serves which task. Warn-and-list, never block (a human tells a rich-but-legible set from bloat).

## Self-evident over explained — progressive disclosure

Layout + labels + standard components make meaning obvious **without** inline prose. **If a screen needs
a paragraph to be understood, the design failed — fix the design, not the paragraph.** Demote
explanation to a "?" tooltip, a hover, a collapsible "How this works", or a dismissible first-run hint —
available, not shown by default. Legends/reference blocks: **collapsed by default**; when open, a **grid
showing the actual glyph** beside its meaning, never a paragraph describing marks in words. Teach on the
artifact itself via hover/focus; the legend is the fallback teacher, not the primary one. (Nielsen:
aesthetic-and-minimalist design; recognition over recall.)

## Drawers, hierarchy, density

- Detail drawers **overlay** the current view — never navigate the background away; the user
  keeps their place and can inspect several items in a row.
- Correct collapse **scope**: a child collapses within its parent's subtree, not siblings two
  levels up.
- Declutter dense rows — few visible chips, secondary actions behind a menu, detail on hover.
  **No dead controls** — a toggle that does nothing is worse than none; it's a trust defect, not
  a cosmetic one.
- **Footprint tracks information — the opposite failure from a dense row.** The declutter rule
  above fixes an *over*-dense row; the converse defect is wasted space — an
  empty/undefined/placeholder record rendered at a **populated record's footprint** (a full card
  reading "No data source / No owner / —"), a grid stranding half a wide viewport, or a toolbar
  row holding one control across the full width. Collapse or group placeholders (a compact row,
  not a full card), give a grid/list a **density target at the wide viewport** (name the
  top-product precedent — a metrics grid, a list view — not a taste call), and fold stranded
  single-control chrome. The test is **information-per-screen, not pixels-per-item**: a screen
  that could show N× more at a glance without crowding is a density defect, ruled like any other
  — the *space-appropriateness* complement of *Every data state*'s honest-empty rule: a
  full-card empty state is honest and still wastes the footprint.

## Unified across modules — one component per concept

The consistency rule below has a structural cause and a structural fix. **Inconsistency across views is
almost always the same concept built more than once and drifting** — a row, card, field, empty-state,
status chip, or editor reimplemented per page, so a fix to one misses the others and the app feels like
a different product on each screen. This is a maintainability defect (cross-ref domain H) with a UX
consequence, so it is ruled on here too.

- **One shared component per concept.** Before building a UI element, grep for an existing component or
  pattern that already does it and **reuse or extend it** — never reimplement per page. A duplicated UI
  string or markup block across files is the red flag (cross-ref H's duplicate-source-drift:
  byte-identical lockstep copies need a single source or a parity test). **Cross-file duplication is
  invisible to a diff-scoped review** — you see the file you changed, not its twin — so on any "unify"
  or "fix this component" task, grep the **duplicated visible literal string or section heading** across
  the whole tree as the search key that surfaces the twin, before claiming the concept unified.
- **A shared component existing is not proof the concept is unified — check the adoption is total.** A
  shared component often exists *because* a drift was already fixed: built and rolled out to N callers
  (often via its own closed PR/issue) to kill exactly this duplication. But 1–2 new or missed sites
  reintroduce the drift by hand afterward — sometimes copy-pasting the component's own default-string
  constant instead of importing it. A component being *created* reads as the concept being *solved*, so
  reviewers stop once they confirm it's "adopted" without verifying adoption is **total**. When the
  shared component's doc-comment names the exact call sites (or the exact prior drift) it fixed, **diff
  that named set against a fresh whole-tree grep** for the same string/concept; any hit outside the
  named set is a **candidate** straggler — confirm it renders before treating it as reintroduced drift
  (grep finds candidates; the render trace confirms). Higher-confidence than a cold duplicate search —
  the comment describes the "before" state, so you match a known defect instead of guessing.
- **The unassembled molecule — duplication with no shared literal string.** The twin-search above keys
  on a duplicated *string*, which misses call sites that each correctly use the **same underlying
  primitives** (say an icon plus a tooltip/popover) where no one has composed them into the one compound
  widget the recurring concept deserves. The **assembly** carries the real decisions — which a11y
  attributes, native `title` vs the shared tooltip, sizing — so the ad-hoc assemblies silently diverge
  on exactly those, and one site's hard-won fix (e.g. a documented conflict with a
  screenshot/visual-test tool) never propagates because it lives only in that file. The visible label
  differs per site, so grep for a repeated **scaffolding** pattern instead — the same small
  a11y-attribute cluster, or a one-character glyph inside a small rounded element — recurring across
  files that import no common component for it. If the design system already ships the primitives, the
  fix is to build the one shared atom, not just reconcile the wording (the wording was never the only
  thing diverging).
- **Sibling view-variants of one concept each re-declare the shared lookup or primitive the others
  import.** When one entity shows through alternate *layouts* — a compact vs expanded card, a horizontal
  vs vertical diagram, a table vs list a parent switches between — each variant tends to carry its *own*
  copy of a mapping or sub-element rather than resolving the shared source. Distinct from the two
  bullets above: not a whole component missed at a call site (*adoption-is-total*), nor a primitive no
  one has composed (*unassembled molecule*) — here the shared atom **exists** and this variant's file
  **already imports it** for a neighbouring member, so the gap hides behind a present
  `import { … } from './primitives'` that reads as finished. Two shapes: **(a)** an
  enum→label/colour/tone **lookup map** (`Record<Status, …>`) where the union *type* is centralized and
  imported but the map over it is inlined — *type centralized, map not* is the tell; **(b)** a
  sub-element's **derivation-plus-render pair** (a centre readout, an axis block, a legend) left inline
  in one renderer while siblings pull it from the shared module. The hazard spans present and future:
  the inline copy may *already* be a member behind (diff it against the shared map key-by-key), and any
  enum member or sub-element fix added later reaches only the shared source, so that one variant
  silently renders a blank/wrong label, off-brand colour, or stale block, while each variant reviewed
  alone looks correct. Detect by enumerating **every** renderer of the enum or diagram (grep the union
  type, or the parent's layout-toggle option list) and confirming they resolve **one** lookup/primitive;
  a variant with its own inline map or sub-element when a shared one exists is the finding. Same
  sibling-variant family as the row-affordance / view-switch / search bullets below, but the divergence
  is a duplicated *source*, not divergent *handling* of a shared one. Fix: the variant imports the
  shared module and it becomes the single place a new member is added; the one legitimate per-variant
  difference (a size class) becomes a prop, not a second copy.
- **A centralized *value resolver* makes the DRY gut-check pass while the *render* around it is still
  hand-rolled per call site — value unified, markup not.** A team factors the shared *logic* of a
  recurring element into one function — `resolveCategoryColor(key)`, `getStatusVariant(s)`, a
  `Record<Enum, className>` lookup — imported at every surface, so a **DRY pass sees no duplicated magic
  values and signs the concept off as "unified."** But the resolver only centralizes *what value to
  use*; the **wrapper markup that consumes it** — the element (`<span>` vs `<div>` vs a pill), class
  scaffolding, a11y attributes, an optional icon/dot, sizing — is re-written independently at each call
  site, so the *render* drifts exactly where the resolver can't reach: one site paints a dot + text,
  another a filled pill, another adds an icon, all calling the same `resolveCategoryColor`. The tell is
  **duplicate render blocks (often in the same file) wrapping the same resolver call**, not a duplicated
  value — why the twin-search and a DRY check on the resolver both miss it. Fix: consolidate the
  **render**, not just the value — build one component (`<CategoryBadge category={key}/>`) owning *both*
  the resolver call and the markup, its one legitimate per-site difference a prop (size/variant);
  centralizing the value is necessary but not sufficient. **Distinct** from the
  sibling-variant-re-declares-lookup bullet above (there the **lookup map itself is inlined** per
  variant; here the map/resolver *is* shared — *value centralized, render not*, the next rung down);
  from *the unassembled molecule* (there **no** shared composition exists; here a shared resolver *does*
  exist and is precisely what masks the render duplication); and from *One component, divergent props*
  below (there **one render component** exists and a feature-prop defaults off; here there is **no**
  shared render component, only a shared value). Refines the concept-fragmentation root (*"Feels like a
  prototype"* below) — a concept can look consolidated because its value is centralized while still
  re-implemented N ways at the render layer, so audit the **wrapper markup per call site**, never
  conclude "unified" from an imported resolver alone. Detection: grep the resolver's **name** for
  callers, then diff the **markup around each call**; divergent wrappers over one shared resolver is the
  finding.
- **A raw value hardcoded equal to a design token's *current* value is design-system drift that renders
  identically today and breaks the moment the token moves.** This section's *one source per concept*
  thesis covers **design tokens** — a spacing step, colour, radius, z-index — as much as components: the
  token is the single source, and a component writing the literal (`padding: 16px`, `color: '#2563eb'`,
  `borderRadius: 8`) instead of referencing it (`var(--space-4)`, `tokens.color.primary`,
  `theme.radii.md`) has forked that value. Invisible to every check comparing the *rendered* result,
  because the literal was chosen to equal the token's value **now**: the hardcoded copy and its
  token-referencing siblings paint the same pixels, so a screenshot diff, visual-regression snapshot,
  and eyeball pass all agree "consistent." The drift is **latent** — when the token changes (a rebrand,
  a density pass, a dark-theme remap, a 4px→8px grid migration) every referencing sibling moves and the
  hardcoded one silently stays, so the surface that looked most conformant becomes the lone off-brand
  element, caught only by the next screenshot after the change. Detection can't grep the token *name*
  (the literal never names it); use the **siblings as the oracle** — if most components of a class
  reference a token and one writes a literal equal to a defined token's current value, that literal is
  almost certainly a bypass, not a deliberate one-off (same minority-outlier diff as the
  disclosure-`aria-expanded` sweep in `frontend-a11y.md`). Mirror shape: the **same literal with no
  token at all, repeated across N siblings** (`16px` inlined everywhere) — that repetition signals a
  token *should be extracted*, H's duplicate-source-drift at the value level. Fix: reference the token —
  or, for the no-token case, define one and point every sibling at it. **Distinct** from the
  sibling-variant-re-declares-lookup bullet (that inlines a *lookup map or sub-element*; this hardcodes
  a *scalar style value*) and from the duplicated-string twin-search (that duplicates a *literal
  string/markup block*; this duplicates a **token's value**, a finding *precisely because* it renders
  identical, not visibly duplicate). A genuine one-off that must **not** track the token is the
  fail-open exception: mark it (a named constant or comment) so it reads as chosen, not drifted.
- **A shared-recipe / design-token *migration* is audited for completeness by enumerating the control
  TYPE, not the shared component's importers.** When a team migrates a recurring control — a segmented
  control, pill/tab group, filter-chip row — onto one shared recipe or token set, the natural
  completeness check lists the shared component's **call sites (importers)** and confirms each looks
  right. That check is structurally blind to two ways a control stays on the old recipe, since both
  import the shared thing **nowhere**: (a) a control built **later or in a parallel branch**, never
  migrated, still carrying the *old* recipe's markup/class signature; and (b) a control that **cannot**
  use the shared component at all — a state-toggle that isn't a real navigation link, an item needing a
  different role (the *one control, one role* split in `frontend-a11y.md`) — hand-rolling a copy
  instead. Both render correctly today, so a per-screen pass and visual snapshot approve; the drift is
  **latent**, exactly like the hardcoded-token bullet above — when the shared recipe or token moves,
  every migrated instance follows and these lag into off-recipe stragglers. **Enumerate by the control
  CLASS**: grep the *old recipe's* signature (class names, markup shape, inlined literals) and any newer
  variant of the same visual control, take that population, and diff it against the migrated/importer
  set — every member not resolving to the shared recipe is a candidate straggler (confirm it renders,
  per *Fix the surface that renders* below). **Distinct** from the adoption-is-total bullet above (which
  diffs a named-fixed set against a grep for the shared *concept/string*, assuming a straggler *should*
  have imported it — here the search key is the **control type/old-recipe signature** precisely because
  a non-adopting control carries **no** shared marker) and from the hardcoded-value-equals-token bullet
  (a *value-level* check **within** one control — this is the *population* question of **which**
  controls to check at all).
- **A "we'll migrate the rest later" claim is only as good as the ticket behind it — and the leftover
  sites it defers are the ones that *structurally* can't adopt the shared component.** The
  audit-migration-by-control-TYPE bullet above owns the **population** question and the two ways a
  leftover carries no shared marker: (a) never migrated, (b) *can't* use the shared component. This
  bullet owns two ways that leftover stays **hidden even from that sweep**. **(1) The migration is
  "tracked" only in a code comment, not a real ticket.** An extraction that *admits* the leftover —
  `// migrating the server-rendered empty state onto SharedEmptyState is a tracked follow-up` — reads as
  diligence, so a reviewer trusts the claim and moves on; but the follow-up was never filed, so nothing
  forces consolidation and the shared component and un-migrated copy drift apart (an a11y fix, a prop, a
  copy tweak lands on one and not the other — the latent-drift consequence the audit-migration and
  hardcoded-token bullets already name). **Verify the claim against the tracker; don't take the
  comment's word:** grep comments and commit messages for promise phrasing (`tracked follow-up`,
  `migrate … later`, `should become a thin call of`, `consolidation deferred`), and confirm a real open
  issue names the specific two components. A structurally-confirmed duplicate with no tracking issue
  means the claim is false — file the follow-up. Distinct from `frontend-a11y.md`'s "grep for *we
  avoided the shared component because…*" (mines a comment stating a **reason not to use** a primitive,
  a pre-verified bug already worked around) — this mines a comment **promising to finish** a migration,
  and the action is to *verify the promise was kept*, not treat the deviation as the bug. **(2) The one
  relevant leftover is buried in a multi-branch empty-state conditional, masked by legitimately-distinct
  siblings.** A search-like view chains several empty states — *no query yet* / *query too short* / *no
  text matches* / *matches exist but a filter removed them all* / *results* — and only the last is the
  shared "filtered-to-zero" concept; the others are genuinely different and must **not** be forced into
  it. A concept-grep (`No .* match` / `.* match .* filters`) over-matches the legitimately-distinct
  branches, so a reviewer sees "several empty states for good reasons" and stops without classifying
  **which** branch is the shared concept in disguise. Tell: that branch's copy reads as a **prose
  instruction** ("clear a filter to widen the results") rather than an actual control, because the
  working clear button lives elsewhere, wired to a different, often hand-rolled affordance. **Fix the
  framework-boundary survivor at the component, not the call site:** a server-rendered site hand-rolls
  an *action-less* empty state because the shared component takes a client `onClear: () => void` it
  can't pass (blind spot (b)'s server/client-boundary case — a framework boundary, not a wrong role) —
  extend the shared component to accept an **action-descriptor** (an href/action form) alongside the
  bare callback, and when closing an "extract shared component X" ticket **enumerate the call sites
  excluded and why**, rather than closing on "every match of the old pattern is gone." Distinct from the
  **adoption-is-total** bullet above — here the survivor either **couldn't** adopt it (framework
  boundary) or hides behind a *false* "tracked" claim, so it never appeared in a named set to diff
  against.
- **A fix to a shared concept lands in the shared component**, not in one caller — otherwise the same
  defect survives in every other caller, and whoever checked only the screen they were shown signs off a
  still-broken app.
- **Fix the surface that renders, not the first grep hit.** A string can live in a file the target route
  never renders; trace route → component and confirm the component is actually shown before editing it.
  Grep finds candidates; the render trace confirms (cross-ref `parallel-audit.md` §5).
- **Zero mount paths from any entry is the dead-render candidate — the proactive form of the same
  check.** The rule above disambiguates *which* of several candidate surfaces a grep hit renders; this
  is the case where the trace turns up **none**. A component can be cleanly exported and carry its own
  passing unit test — `render(<Widget />)` mounts it directly, keeping the suite green — while having
  **zero mount paths from any router entry, page, or parent component**: nothing on a real route ever
  imports it into a reachable tree. The file reads as alive (exported, tested, maybe lint-clean) and is
  shown to no one. **Different discriminator from domain H's dead-code-removal rule**
  (`domain-h.md`): H's unreferenced-code check is blind to this case, since the component
  *does* have a reference — its own test import — so a plain reference-count linter passes it clean; the
  defect here is *render*-reachability, not *reference*-count. H treats truly unreferenced code as
  maintenance/attack-surface and defaults to **delete**; this is a **product** defect — something built
  to be seen isn't — so the default remedy flips to **wire it up**, retirement the owner's call.
  Detection: walk the router/page tree inward from every entry; a component reachable from **no** entry
  — only its own test file or other already-dead code — is a **candidate**, not confirmed, exactly like
  the straggler check above. A static import trace is blind to `React.lazy()` / dynamic `import()`, a
  string-keyed registry, a CMS-driven map, or a runtime route config — check those too; where they can't
  be checked, the zero-entry result is `unverified`, not found-nothing (could-not-check discipline,
  Enforcing gate below). Flag a confirmed case to **wire it up or retire it**; retirement is an owner
  call under *Decisions needed (owner)*, never a unilateral delete.
- **One component, divergent props, is the other half of inconsistency.** Even a correctly-unified
  shared component reads as inconsistent when a **feature-bearing optional prop defaults off** and some
  mount sites omit it — one listing passes `votes` (the chip shows), another embedding doesn't (no
  chip). Each render is individually correct; together they look cheap, and the twin-search above won't
  catch it since it *is* one component. For any shared component with a feature-bearing optional prop,
  **enumerate every mount site and diff the props**; a feature that should be universal belongs
  **inside** the component, not behind an opt-in a caller can forget. Review question: "does this
  concept render identically at *all* its mount sites?" — don't stop at "it's one component."
- **In a port or migration, unification is a precondition, not a cleanup pass.** Enumerate the shared
  concepts and adopt exactly one component per concept **before** porting screens — a duplicated concept
  is a defect a reviewer *will* find, and retrofitting unification while the owner watches is far slower
  and noisier than building it once up front.
- **Row-click-affordance inconsistency — a detection gap, not a remedy gap.** An entity-row (same
  fields, same detail target) is whole-row-clickable — mouse and keyboard — on one page, and only a
  single inner `<a>`/`<Link>` cell is interactive on a sibling page importing a *different* row
  component. It clears WCAG (named, reachable, focus-ringed) and has no shared component to check
  adoption on, so a11y tooling, a per-page review, and the twin-search above all pass it clean —
  distinct from the *interaction-consistency* bullet below (its row-class parity is *style*-reaction
  parity across *one* shared component's instances; this is affordance *existence* across *separate*
  components). Detect by enumerating every renderer of the row type (grep the shared fields/link target,
  not a literal string) and diffing row-level interactivity against a lone anchor. Fix: one shared row
  component/hook where feasible; else extend the affordance without a **second tab stop** — the inner
  `<a>`/`<Link>` stays the single named, focusable control (a `event.target.closest('a,button')`-guarded
  row `onClick` adds a mouse convenience over it; or a stretched-link `::after` overlay extends the
  anchor's own hit area, preserving native middle-click / open-in-new-tab / copy-link). Don't add
  `tabIndex`/`role` to the row while an inner link already reaches the detail: a second focusable with
  no role or accessible name reads worse to a screen reader than the lone anchor it duplicates
  (`frontend-a11y.md`'s `role`/`tabindex`-pair grep and keyboard floor). The row needs its own
  `tabIndex={0}` + Enter/Space **and** an explicit `role`/accessible name only when it has no inner
  focusable path to the detail — noting a `role` on a `<tr>` overrides its native row semantics, and a
  stretched link changes text selection over the row. Name every renderer of the row type in a "make row
  X clickable" ticket's acceptance criteria, not just the page that prompted it.
- **A view/tab-switch link built from a narrow param allow-list silently drops the active filter.**
  Sibling *view* tabs (list / table / chart / map) over one dataset, addressed by a shared `?view=`
  param, plus a cross-cutting search/filter (`?q=`, facet params) meant to apply to every view. The tab
  strip's href-builder encodes only the base route + `?view=` and does **not** read and forward the
  *current* query string — so clicking a sibling tab while a filter is active navigates to a URL that
  dropped it: the destination renders unfiltered and the search box comes up empty, reading as
  "switching views clears my search." Same family as the row-affordance bullet above — the inconsistency
  lives in one renderer's own link-building, invisible from the shared control. Detect: find the
  tab/view href-builder and classify whether it composes the destination from the **full current param
  set** (overriding only `view`) or a fixed allow-list; a builder naming only `view` drops everything
  else. Fix: build the target href by merging over current params (change `view`, preserve
  `q`/facets/sort), and test that switching view with a filter active preserves it. Decide per param
  whether it's view-scoped (may reset) or cross-cutting (must persist) — never drop cross-cutting state
  by omission.
- **A shared search *filters* on one renderer but only *highlights* on a sibling — and the highlight can
  land behind a fold.** One dataset rendered through two layouts (a tree/list and a diagram/grid)
  sharing one search input. The first-hardened renderer, on a match, **filters** non-matches out **and
  force-expands** the match's collapsed ancestors so it's guaranteed visible; a later,
  structurally-different renderer wires the same value only to a **cosmetic highlight**
  (ring/background) — never filtering, and a match nested inside an independent, user-collapsed fold is
  neither force-opened nor annotated, so a term that worked on the first layout appears to do
  **nothing** on the second (its one visible effect sits behind a fold the user can't see). Same family
  as the two bullets above: the divergence is in each renderer's own handling of the shared value,
  invisible from the shared input, and a caption near it may already claim "search narrows every view"
  without distinguishing *filters* from *merely highlights*. Detect: per renderer, classify the search
  value's use as **filter** (participates in an include/exclude decision) vs **highlight-only** (only a
  className/style); for a highlight-only renderer, check whether any collapse/fold boolean references
  the search/match state — if a fold is computed with zero reference to it, a match inside renders with
  a class the user can't see. Fix: decide per renderer whether search filters or only highlights, and
  make the UI copy match (a caption claiming "narrow" over a highlight-only control is itself a defect);
  where highlight-only sits behind independent fold state, key that state off the active search — force
  the section open or show a "N matches inside" count on the collapsed ancestor. Test the combined
  state: a match nested inside a manually-collapsed ancestor must be visible or explicitly signposted,
  not merely present in the DOM with an invisible class.

## One component at two scopes — single-entity vs aggregate needs scope-aware copy

A shared component reused at **two scopes** — a single entity vs an all-entities
**aggregate/rollup** — but with labels and empty-states **hardcoding the single-entity
phrasing** ("the items *this* owner has", "nothing here for this owner yet") reads wrong or
misleading at the aggregate scope. Related forms: the aggregate view **drops** a section the
single-entity view shows, or lists an unbounded union of rows with **no attribution** of which
entity each row belongs to — so the rollup is unreadable and the two scopes feel inconsistent.

- **Make copy and empty-states scope-aware** — interpolate the scope (the entity name at single
  scope, "all …" at aggregate), don't hardcode one.
- **At aggregate scope, label each row with its owning entity** and **cap/paginate** the union
  (the overflow state).
- **Keep the section set consistent across scopes** unless a per-scope variant is deliberate and
  stated — and at aggregate scope specifically, **hide a view whose number would be a
  *misleading aggregate*** (a rate or total meaningless across heterogeneous entities):
  computed-not-fabricated (principle 3) beats symmetry, exactly as in `migration-parity.md`'s
  misleading-aggregate exception.

A **different axis** from the neighbours: not the *prop* axis (#123 above — one component, a
feature prop present at one mount site and absent at another) and not the *section-set superset*
across **sibling per-entity** surfaces (`migration-parity.md`), but the **single-vs-aggregate
scope** of one component's copy and attribution.

## Interaction-completeness — the loop must close

A control is a defect until its whole loop works in the running product, not just until it renders:

- **No write-only inputs.** Any surface where a user adds or edits data must let them **see, reach, and
  edit** what they added, in the same view (read-back). An input posting to a store but never showing
  the value back is a defect, not a slice — the user can't tell it worked, correct it, or undo it.
- **A completion claim must not outrun the publish pipeline that makes it visible — "Applied" copy on a
  write that still lands in an intermediate store, read back from a different plane, silently disagrees
  with itself.** The read-back rule above asks that a written value appear *somewhere* in the same view;
  this is the sharper failure where a read-back surface *exists* but sits on a **different data plane**
  than the write, with an async or manual step between them, and the success copy was strengthened to
  hide it. A flow changes from "submit → a human reviews → it goes live" to "submit → applies
  immediately," and the success UI matches ("Applied", "X is updated", "no review step needed") — but
  the publish path is **not** actually collapsed: the write still lands in a durable audit log, an
  auto-opened pull request, a moderation queue, or an outbox, reaching the read surface only after a
  *separate* merge / cache invalidation / rebuild / batch job / second approval. The read surface is
  often a **static build, a CDN-cached response, a replica, or a materialized view** the write doesn't
  touch until that step runs — not "eventually consistent in a few seconds," but *not connected*. The
  user sees the old value with **no diff, no "publishing" state, no pending indicator** under a message
  asserting the change is live, making a successful write indistinguishable from a dropped one (they may
  re-submit → duplicate writes, or stop trusting the edit affordance). It ships because the copy change
  and the pipeline are audited separately: the "waiting for a human" affordance is removed from the
  *submission* surface without checking the *display* surface still depends on that step — and the same
  change often **removes a "pending" badge/banner** keyed off the old status enum, deleting the one
  honest signal at the moment it deletes the caveat it implied. **Detect** by finding a write whose
  success UI carries an unqualified completion verb ("Applied/Saved/Updated/Live/Published"), especially
  one recently strengthened from a weaker claim ("Submitted/Sent for review/Queued"); trace where the
  write lands vs. where the read surface reads from; if different planes with an async/manual step
  between, reproduce it — perform the write, re-render the *exact same view* without the manual step,
  and if the old value stands with zero in-flight indication, that's the bug. **Giveaway:** a slower
  flow in the same product (e.g. a reviewer-facing acceptance screen) often still states the real caveat
  honestly — the regression is the faster-feeling flow dropped that language. **Fix, either closes it:**
  (A) make the read surface reflect the write — patch/refetch/revalidate the exact value in the same
  session, keep a "not yet live" indicator until the async step completes (don't delete it because the
  status enum changed); or (B) make the copy match reality — say what happened ("recorded; a change
  request was opened automatically — live once it's reviewed and published"), not borrowed "Applied"
  language from a faster path. **Distinct** from the optimistic-write bullets
  (`concurrency-shared-state.md`'s read-modify-write; the reverted-optimistic-write mapper in this
  file): those are an optimistic-UI *race* (a newer write clobbered, or a raw error string leaked) —
  this is a **process/pipeline mismatch**, the copy asserting completion the read plane can't back, no
  race involved.
- **WYSIWYG, never raw markup shown to users.** Store markup; **display it formatted**. A rich-text
  field showing `**bold**`, `<u>`, or `*` tokens while the user types has leaked its storage format into
  the UI — render what the text will look like once posted.
- **No dead controls, and disabled must look disabled.** A button/toggle/arrow rendered enabled whose
  handler is a no-op is a trust defect; an unavailable control must *look* unavailable, not merely be
  inert. Unit-logic tests passing is **not** a working UI — exercise the real control in the running app
  (cross-ref the live-verification rule below).
- **A filter/facet option that matches zero rows in real data is a dead control too.** The no-op-handler
  case above is *structural*; this is *data*: a filter/facet/sort option whose handler works fine but
  that **no real row can ever satisfy** (a category with no items, a status nothing is ever in) still
  does nothing when clicked. Validate the option set against the **actual data distribution** — render
  only options with a non-zero count (or show the count) rather than hardcoding a menu from an enum that
  outruns the data — so a user never picks a filter that silently returns nothing.
- **A cross-view in-page anchor is a dead control when the section it targets omits its `id` in the
  empty state.** A different flavour of dead control from the two above (a no-op handler; an option no
  row satisfies): here the control — a link `<a href="/detail/{id}#section">` (or a `router.push` to a
  fragment) in a list/table view — is wired correctly, but the element it scrolls to is a detail-page
  section rendered `{data ? <section id="section">…</section> : null}`, so under the empty condition the
  whole wrapper *and its `id`* vanish and the fragment resolves to nothing: clicking scrolls nowhere,
  silent and indistinguishable from a broken button. The cross-link is typically built
  **unconditionally** off the same `0/0`-style counts driving the empty condition, so the exact records
  whose section is absent are the ones whose link renders (often styled as a "problem"/danger state). It
  survives review because each component reads fine alone — the detail page's conditional looks like
  ordinary "don't render a diagram with no data," the list's link like ordinary "click through to
  detail" — the defect exists only in the *combination*, invisible to a diff-scoped or per-component
  pass; an end-to-end test on the anchor is usually written against a record that *has* data, never the
  empty one where the target disappears. It hides especially well when sibling views (a card, a preview
  drawer, a relationships table) render the same empty condition *honestly*, so the one `null` reads as
  consistent with well-handled neighbours. **Detect** by taking any element conditionally rendered on a
  data-presence check that carries a DOM `id` and grepping every `href`/router-push that builds a
  fragment matching that `id`; if the link is unconditional (or gated on a derived count that can
  legitimately be `0`) while the section is gated on the same data, the empty-record case is a
  guaranteed dead anchor. **Fix — keep the wrapper and its `id` always mounted and put an honest inline
  empty-state message inside it**: closes both halves at once — the region is never a blank void, and
  the anchor always resolves to a real in-viewport element; or, if the section genuinely must not exist,
  gate the cross-link too. **Distinct** from the section-chrome-gated-on-content rule above (a
  header/count/affordance emitted *outside* a filtered row's presence conditional in the *same*
  component): that is a same-component chrome/empty defect; this is a *cross-component* anchor contract
  broken by a conditionally-omitted `id`, whose blast radius is a dead link on *another* surface.
- **A disabled action explains its cause and its recovery path — not a dead end.** Looking disabled
  (gate 1's *disabled-looks-disabled*) and disabling the same way at every instance (the
  *interaction-consistency* bullet below) prove the control's appearance and cross-instance parity;
  neither tells the user **why** it's unavailable or **what** unblocks it. A *contextually* unavailable
  action names the **unmet prerequisite and a concrete next step** — and since a native `disabled`
  element may receive **no hover or focus events**, that explanation can't live in the control's own
  tooltip; put it in **nearby text or a focusable wrapper/popover** the user can actually reach. An
  action *permanently* unavailable to the current role is **hidden or replaced with an attainable
  alternative**, not left visibly dead — unless discoverability is explicitly wanted (`frontend-a11y.md`
  owns the disabled-control *contrast* exemption; this owns the *recoverability*).
- **A control disabled only until client state resolves is *loading*, not disabled — render it as
  loading, never dead.** A write control (add, submit, compose) gated on client-only state — `useAuth` /
  `useSession`, a hydration flag — is server-rendered in its `disabled` default, then enabled once the
  client bundle resolves. For the seconds of that SSR → hydration window it looks like a permanent dead
  control (the *no-dead-controls* class above), but it's really in the **loading** data state (the
  five-states rule) and must *look* loading — a skeleton or spinner affordance — not a bare disabled
  button with no reason. Distinct from the *contextually-unavailable* case above: that control **stays**
  disabled and owes an explanation; this one **will** enable itself and owes a loading affordance.
  Optimistic-enabled (render it enabled, act on the click) is allowed **only** when the click is
  captured and replayed after hydration, so the handler is never a no-op — an enabled control whose
  pre-hydration click is dropped is the *dead control / no-op handler* trust defect above, not a fix.
  The static tell — `disabled={!session}` on a write action with no loading sibling — is an
  **`unverified` lead, not a finding**: only a **pre-hydration render** (`testing-ui.md`)
  confirms it, so where the harness can't capture one the gate reports *could-not-check* and fails
  **open**.
- **A disclosure default derived from async-fetched data silently never fires (mount-capture).** An
  open/collapsed default read once at mount — `useState(open)` seeded from a prop or derived value the
  hook does **not** re-sync on later change — locks in whatever was available at first paint. When one
  input to that default is fetched **asynchronously** and lands *after* mount (a count, a flag, a
  permission), the default silently never applies: the pure decision function's unit test is green, the
  running UI never opens/collapses as intended. Drive the mount default from data available
  **synchronously** at first paint (when the deciding signal is async-only, default to the
  collapsed/closed state at mount); surface a late-arriving signal through a **non-reflowing**
  affordance (a badge on the collapsed header), never by force-opening after the fetch (which reflows
  under the reader); keep the async signal in the decision function's *contract* so it's honoured when
  present at mount (a warm cache) and stays tested. Confirm it **live in the running product**, not only
  the logic test — same client-state-timing family as the disabled-until-hydrated rule above.
- **Reviewable change history, and no silent AI edits.** Any surface where an edit is itself a decision
  of record (a value, a target, an assignment, an owner) needs a visible who/what/when history behind
  the current value, not a silent overwrite — the same defect class as a write-only input, one level up.
  A value an agent or model proposed or wrote on a person's behalf is stamped in that history as
  AI-recommended, with its source, **at write time** — never merged in indistinguishably from a human
  edit. An unstamped AI edit is a defect a reviewer can't see, not a shortcut.
- **Interaction *consistency*, not just completeness — the same class reacts the same everywhere.**
  Completeness (above) asks "does this control work?"; consistency asks "do all instances of this class
  react the same, and is every affordance reachable?" For each interactive class (button, row, card,
  chip, tab), its **hover / active / focus-visible reaction is identical at every instance** — divergent
  reactions is a finding, and since the cause is usually per-instance style overrides on a *shared*
  component, it survives the *one component per concept* grep (that catches duplicate markup; this
  catches divergent state styling on the same component). **Every hover affordance has a non-hover
  path** — anything revealed only on hover is also reachable by keyboard focus and present (or behind an
  explicit control) on touch; a hover-only action is a defect, not a power feature. A **tooltip carries
  new information** (a value, a date anchor, a definition), never a repeat of the visible label. And a
  disabled instance looks disabled the **same way** everywhere — the across-instances form of
  *disabled-looks-disabled* above. (`frontend-a11y.md` owns that a focus ring *exists*; this owns
  **parity** of the reaction across the class.)

## Match a named standard; visual & number-format consistency

Before designing an element, recall how the best products solve it and **name the standard
applied**; reinventing a solved problem (legend, delta, table, date picker, empty state) is a
cost, not a feature. Then keep it consistent: one type scale, one spacing rhythm, one component
set, consistent **number formatting** — locale/thousands separators and **tabular figures in
columns** so digits align. The same mark/legend renders identically wherever it appears.
`frontend-a11y.md` owns **accessible-name** consistency across routes; this owns **visual /
number-format** consistency — the drift a per-route pass and a name-only diff both miss.
(Nielsen: consistency and standards.)

- **Fixed-width trailing chips laid out after a `flex-grow` cell align *within* each row but not
  *across* rows — a per-row flex container has no shared column, so the cluster starts at a
  different x on every row.** A repeated list/table row built as a flexbox — a primary cell with
  `flex: 1` (or `flex-grow`) that expands to fill, followed by fixed-width status chips, counts,
  or action buttons — packs its own children correctly, so any **single** row looks perfectly
  aligned and a one-row component test or screenshot passes. But each row is its **own** flex
  container: the `flex: 1` cell consumes whatever width that row's primary content leaves, which
  differs per row, so the trailing cluster begins at a **different horizontal position on every
  row** and the chips read as ragged down the page, sharing no common edge. It hides because the
  raggedness is a **relational** property visible only when rows stack and you scan the trailing
  edge — exactly the composition judgment the *clean-checklist-is-a-floor* rule below names ("a
  column of badges that don't share a right edge") as invisible to a per-element checklist — and
  seed data with near-equal primary-cell lengths lines the chips up by accident. Fix: hoist the
  columns to the **container** with a shared track structure — CSS Grid on the list with one
  `grid-template-columns` (e.g. `1fr max-content max-content`), each row a grid row (or
  `display: contents` / `subgrid` for a nested row component) so every row's chip column shares
  the **same track boundaries**; flexbox aligns children within one container, Grid with a shared
  template aligns a column across many (the data-grid / property-row precedent — Linear, Notion, a
  spreadsheet). Right-aligning the chips within each row does **not** fix it — it only moves the
  ragged edge. **Distinct** from the tabular-figures rule above (glyph-level: digits lining up
  inside one column via `font-variant-numeric`) — this is **column-boundary** alignment across
  rows, a layout-structure defect, not a font-feature one. Detection: a repeated row component
  whose layout is `flex`/`inline-flex` with a `flex-grow`/`flex:1` cell and fixed-width trailing
  elements, with **no** shared grid track tying the cluster's start across rows; verify by
  stacking rows with **unequal** primary-cell lengths and scanning the trailing edge, never a
  single row.

---

**🚩 grep**: a data-fetch / `useQuery` / `await` render path with no `isLoading`/`isError`/empty
branch, a `.map(` over a list with no length-0 case, a table/grid with no `overflow`/pagination,
a `catch` rendering `err.message`/stack into the DOM, or a `.slice(0, N)`/`LIMIT`/`take(N)`
render whose length can be less than a known `total`/count with no adjacent remainder/pagination
text, or a client response type that omits a server-computed `error_count`/`errors`/`rejected`
field so its success counters can't reconcile to the total (states) · a colour scale keyed on a
field that also drives an icon/shape, or `>1` semantic use of one `--color-*` token (encoding) ·
a status/delta rendered by `color`/`background` with no sibling icon/text node, or a
colour-coded status dot with no `aria-label` (colour-alone) · a delta coloured green-for-up /
red-for-down unconditionally, an arrow/percentage with no magnitude, or a "change" number with
no period anchor (delta) · a paragraph of instructional copy rendered inline on every load, or a
legend built from text descriptions of marks rather than the marks (self-evident) · a
"drawer"/"detail" that pushes a route change or unmounts the list, or an `onClick` that is a
no-op / `// TODO` (drawers / dead controls) · `>1` font-size/spacing value for one role, or
column numbers interpolated without `toLocaleString`/tabular figures (consistency) · the same UI
string, section heading, or markup block duplicated across ≥2 component files, or a second
hand-rolled copy of a row/card/field a shared component already renders (one concept built more
than once) · a text input that persists markup while rendering its raw `**`/`*`/`<u>` tokens
back to the user (not WYSIWYG) · an add/create/edit handler that writes to a store with no path
that reads the value back into the same view (write-only input) · an editable record's write
path with no history/log table behind it, or an agent/model-authored value merged in with no
field distinguishing it from a human edit (change-history / silent AI edit) · a
`confidence`/`score`/`priority` rendered as a raw `{n}%` or float with no defined tier label
beside it, or a model confidence number published as precision (confidence tier) · an
`<svg>`/chart with no `<text>`/axis node and no hover/focus readout target, or a line/area drawn
across `<3` data points (data-viz) · a `position: sticky`/`fixed` element whose scroll container
has no padding (gutter), or an action revealed by `onMouseEnter`/`:hover` with no focus/keyboard
sibling (hover-only) · two or more components consuming one shared hook/context instance where
only some destructure and branch on its readiness/error field alongside the value
(sibling-consumer signal) — the footprint, reflow, and per-class-parity defects are
**render-only**, caught by the route sweep below, not a grep.

## Rendered route sweep — apply domain P across every surface (FULL reviews)

The rules above are individually correct and still miss a whole class of defect, because on a
`FULL` (or broad-`DIFF`) review of a product UI **no step renders the assembled product
route-by-route**. The enforcing gate's screenshot is per-change (the route a diff touched), so a
defect spanning many routes is found the way an owner finds it — scrolling the running app one
screenshot at a time, after a green gate and a clean code read. The sweep is the domain-P
analogue of Phase 3's anonymous-GET sweep (`method.md`): a cheap, systematic, whole-surface pass
turning "we have the rules" into "we applied them everywhere."

1. **Enumerate every route** — from the router tree **and** the nav manifest (a route in one but
   not the other is itself a finding), including detail overlays and tabbed sub-views — **and
   every export path** (download / print / copy-as-image): each is a second render surface,
   ruled as its own surface (below), not across this route matrix.
2. **Render each across the matrix** — the matrix the layout-invariant checks (Enforcing gate,
   below) refer to: **{~390px, ~1440px} × {light, dark} × {top, mid-scroll}**, plus any **state
   transition** a route has (loading→loaded, empty→populated, collapsed→expanded). Render the
   **running build at the intended base ref** — verify the checkout first; a stale tree renders
   the wrong product (render from a clean tree at the right ref — the receipt rule below).
3. **Rule the domain-P checklist on each route** — states, encoding, delta, **data-viz**,
   **density/footprint**, interaction **completeness and consistency**, and the **layout
   invariants** (this step *applies* those rules, not restate them) — and record a per-route
   line: `route · viewport · theme · state · what a user sees · severity`.
4. **Report coverage as a ledger, not a verdict.** A route not rendered is `unverified`, never
   clean (the `COVERAGE_LEDGER` discipline, `method.md`); a clean finding generalises **only**
   to the routes actually rendered, never past them (`migration-parity.md`, *Scope a parity
   claim to the correspondence table*). Group findings by root cause: a class spanning many
   routes is **one** systemic finding, not forty.

## A full-page stitched screenshot fabricates fixed/sticky defects — verify against the live DOM before filing

An automated UX audit capturing **full-page** screenshots (`page.screenshot({ fullPage: true })` in
Playwright/Puppeteer, and equivalents) doesn't photograph the page in one shot — it **scrolls the
viewport and stitches** segments into one tall image. A `position: fixed` or `position: sticky` element
is painted **in every segment**, so the stitched result shows it **duplicated down the page** (a header
repeated at each scroll step) or **displaced** from where it actually renders — a **capture artifact of
the stitching, not a defect in the page**; the live product shows the element exactly once, correctly
pinned. It burns a fix cycle because the stitched image looks authoritative: a "duplicated header",
"overlapping toolbar", or "footer floating mid-page" reads as a real layout bug, gets filed, and a
builder chases a problem no real viewport has. **Before filing any suspected fixed/sticky defect sourced
from a full-page capture, reproduce it against the live DOM** — open the running page and scroll it, or
take **per-viewport** captures at specific scroll offsets (the `{top, mid-scroll}` shots the *Rendered
route sweep* above already uses, which don't stitch) — and file only what survives. **Distinct** from
the *sticky-chrome collision* invariant in the Enforcing gate below, a **real** defect (content painting
**under** sticky/fixed chrome, seen mid-scroll) — this is its inverse, a **false** defect the capture
*invents* for a correctly-pinned element; and a UX instance of `method-situational.md`'s *reproduce a finding
against the right surface* family (dev-vs-prod build, the gate's own detector) — here the wrong
instrument is the **full-page stitch capture mode**, the right one the live render or a non-stitched
per-viewport shot.

## A clean checklist is a floor, not a ceiling — read the render and critique composition

The gates below (the enforcing gate's named pixel checklist, the rendered-route sweep, the
full-page-stitch caution above) prove a screenshot was *taken* and scanned for enumerable, per-element
defects — overlap, clip, contrast, a missing empty/loading state, a focus ring. They do **not** prove
the surface *looks acceptable*, and treating "every checklist item passed" as "this is fine" is a
category error a binary list structurally invites. **Composition quality — spacing rhythm, alignment
consistency (a column of badges that don't share a right edge), visual density, information hierarchy,
chrome/nav consistency, element overlap — is a *relational* judgment across everything on screen at
once, not a yes/no property of any one component**, so no fixed line item expresses it, and a
checklist-shaped audit returns a confident "no defects found" on a page a human flags for cramped,
ragged, or unscannable layout in seconds. The clean report is not evidence of quality; it's the
**default output of a shallow pass**, rewarded because a short "no defects" costs less than prose that
must justify each finding (clean-pass bias). A second bias compounds it: a checklist audit that *does*
surface something visually wrong is disproportionately likely to **wave it away as a "screenshot
artifact"** rather than file it — the legitimate full-page-stitch caution above inverted into a blanket
excuse. **The requirement is not a longer checklist:** a UX audit must *read the rendered screenshots*
and produce a **written per-surface composition critique against a named best-in-class bar** — the
operative question is "would a senior designer at a top product org ship this?", answered in a few
sentences about spacing, alignment, density, hierarchy, chrome consistency, and overlap — and a bare "no
defects found" with no such critique is **`unverified`, not a pass** (a status with an unstated
inspection — the enforcing gate's own rule). Capture **multiple real-viewport screenshots at the scroll
positions a user actually lands on**, never a single full-page stitch: the stitch both hides composition
problems (nothing is framed as a user sees it) and fabricates others (a `fixed`/`sticky` element pasted
at its first-frame position). **Distinct** from the full-page-stitch caution above (a capture artifact
producing a false *positive* on fixed/sticky chrome — verify against the live DOM before *filing*): this
is the opposite direction, a checklist producing a false *negative* on real composition defects, and it
warns that reasoning must not be inverted into an excuse to *discard* a real finding unverified.
Distinct too from the enforcing gate's pixel checklist (necessary, and it catches the enumerable defects
— but not sufficient for composition) and from requiring only that a screenshot be *inspected* against
that checklist or that review cite heuristics rather than taste: this reports the failure that survives
all three — the checklist exists, is consulted, and still rubber-stamps.

## A cross-surface difference is a defect only when it carries no meaning — classify before filing

The Unified-across-modules audits above (and the composition critique just above) hunt for one concept
**rendered differently across surfaces** and call it drift. The failure mode of that hunt is the **false
positive**: not every cross-surface difference is accidental drift — some are **intentional and
distinct-semantic**, a concept deliberately drawn two ways because the two instances *mean* different
things, and filing those as drift (then "unifying" them) **destroys a real signal** — a net-negative
"fix" violating do-no-harm and the read-first *separate a defect from a redesign* spine. Before filing
any "renders differently on A vs B" finding, run a **three-question classifier**:

1. **Same concept?** Are both instances the same underlying concept (same entity, same component role) —
   or two different things that merely look alike? Different concepts are not a consistency finding at
   all.
2. **Same intended meaning?** Do the two instances mean the same thing in their contexts? If the
   difference tracks a genuine semantic distinction — a status badge *filled* on the active board but
   *outline* on the archived view (outline **signals** archived), a primary action a solid button on the
   create form but subdued/absent on a read-only detail page (the action **isn't available** there) —
   it's intentional-distinct-semantic, not drift.
3. **Does the difference carry meaning?** Is the visual difference **doing work** — communicating that
   semantic distinction — or noise with no semantic correlate?

**File as drift only when all three say "same concept, same intended meaning, and the difference carries
no meaning."** Otherwise it's intentional-distinct-semantic: leave it, or — if the distinction itself
seems wrong — surface it under *Decisions needed (owner)*, never a Blocker/Critical, never a silent
"unify" (the product-choice gate discipline, SKILL.md Phase 5). **Distinct** from the
composition-critique rule above, which fights the opposite error — a checklist **false negative** that
rubber-stamps a real defect; this fights the **false positive** where the same audit flags a meaningful
distinction as a defect, two symmetric guards on one "is this consistent across surfaces?" question.
**Distinct** too from the shared-value-resolver bullet under *Unified across modules* above: that's a
false **negative** (a shared resolver makes a concept *look* unified while its render drifts — a real
defect hidden); this is the false **positive** (a concept renders differently and *looks* like drift
while the difference is intentional) — the exact inverse error, why the
*render-identically-at-all-mount-sites* question there must pass this classifier first, so the drive to
unify never collapses a distinction the product intends.

## "Feels like a prototype" is usually one or two shared-primitive roots — fix the root, not each surface

When users call a web app "a mediocre prototype" — hover states that behave oddly, motion that isn't
smooth, pages that seem to take seconds to appear — the cause is rarely scattered per-page bugs; it's
usually **one or two shared-primitive roots**, each producing the symptom on *every* surface that
touches it, so one base fix repairs all of them and a symptom-by-symptom patch pass never converges.
This is the diagnostic form of root-cause-not-symptom (SKILL.md principle 9): don't file N per-page
tickets, find the shared root. Two roots recur often enough to check for by default:

- **Root 1 — bespoke interactive elements bypass the design-system primitive and so lack the base
  affordances it bakes in.** A design system puts `cursor: pointer` and a hover/focus `transition` on
  its `Button`/`Link` primitive; any element written as a raw `<button>`/`<a>` (a one-off, a third-party
  wrapper, a "just this once") inherits neither, so it reads as inert (default arrow cursor over a
  clickable thing) or janky (colour/background snapping with no ease). The fix belongs at the
  **base/global layer**, not per component: a global `button:not([disabled]) { cursor: pointer; }` and
  one shared `transition` on `a, button, [role="button"], [role="tab"]`. Two mechanics are load-bearing:
  use the **attribute selector `:not([disabled])`, not the pseudo-class `:not(:disabled)`** — the
  pseudo-class's lower specificity lets a per-instance utility (`cursor-help`) get silently
  out-specified back to the base rule (a real, previously-hit regression, worth a test); and **exclude
  `box-shadow` from the transitioned properties** (never `transition: all`), because keyboard focus
  rings are commonly a `box-shadow` and easing one in over ~150 ms reads as laggy, unresponsive keyboard
  navigation — a genuine a11y regression traded for a cosmetic one. Pair the transition with a
  `prefers-reduced-motion: reduce` zero-out (`frontend-a11y.md` owns the reduced-motion rule, including
  the JS-driven case; this only adds that the base transition needs the same guard).
- **Root 2 — an SSR page ships above-the-fold content at `opacity: 0`, waiting on client JS to reveal
  it.** An entrance-animation pattern renders an above-the-fold element with `opacity: 0` (or a
  `translateY` offset) in the server markup and a client effect flips it visible on hydration. But the
  server already sent the real content — it's merely *invisible* until the bundle loads, parses, and
  hydrates, so a page that rendered correctly and fast **reads as an empty/blank multi-second load**;
  the animation library manufactured the delay. Fix: never gate already-rendered SSR content above the
  fold behind a JS reveal — play the same effect as a **pure CSS `@keyframes` starting at first paint**
  (`animation: fadeIn 300ms ease-out`), or drop the `opacity: 0` initial state above the fold and
  reserve reveal-on-scroll/-mount for content starting below the fold (where the delay is invisible
  anyway).

**Don't over-fix:** in most design systems the `Button`/`Link` primitive and focus ring are already
correct — the gap is specifically the code that *bypasses* them, so audit for **bypass sites** (raw
`<button>`/`<a>` outside the primitive), don't rewrite components that already work. **Verify, don't
assume:** for Root 1, read `getComputedStyle(el).cursor` and `.transitionProperty` on the actual bespoke
element before/after, not by eye; for Root 2, `curl` the route with no JS running and confirm the real
content — not a shell/skeleton — is in the raw HTML with its visible styling already applied, not
shipped `opacity: 0`. **Distinct** from four neighbours: the *interaction-consistency* bullet above (a
*shared* component whose hover/active/focus reaction diverges *across instances* from per-instance
overrides) — Root 1 is an element that never went through the primitive at all, lacking the base
affordance rather than diverging on it; the *not-dead-before-hydration* / dead-`<Suspense>` bullets (an
*interactive control* disabled or blank pre-hydration) — Root 2 hides *already-rendered non-interactive
content* whose data was ready, gating only its *visibility* on hydration; the composition-critique rule
above, how you *notice* the app feels off — this is how you *diagnose it to the shared root* once
noticed; and the concept-fragmentation root (*Unified across modules — one component per concept* above)
— the **opposite topology**, a third prototype-feel root worth checking for by default. Both roots above
share a *single* base-layer / shared-primitive cause whose **one fix propagates to every surface**; the
concept-fragmentation root is the inverse — there is **no** shared component to fix, the concept is
re-implemented N independent ways (a stat tile built four ways, a status pill five, each drifting so a
fix landing in one twin leaves its copies broken), so the remedy is to **consolidate to one
parameterized component**, not repair a base layer. Both share only the tell that a **symptom-by-symptom
patch pass never converges**.

## Export / print / share is a second render surface

A **download / print / copy-as-image** feature emits the view through a *different* code path than the
screen — canvas/`toDataURL`, SVG serialisation, a `@media print` stylesheet — so a green on-screen
render says nothing about the artifact the user actually walks away with. It silently **clips** content
past the viewport, **drops** axis/legend/labels that lived only in interactive chrome, ignores the
current **theme**, or exports an empty/partial view as a blank image. Treat each export path as a review
surface in domain P (the sweep above already enumerates them):

- **Find the export paths** — grep `toDataURL`/canvas capture, SVG serialisation, `@media print`, and
  `download`/`export`/`copy image` handlers.
- **Produce the artifact and inspect it like a route** — no clip of content extending past the viewport;
  **axis / scale / legend / labels baked in** (an interactive-only readout — the hover value+date the
  *Data visualization* rule above requires — needs a *static* equivalent in the export); **theme**
  honored or explicitly normalised; enough **title / as-of / context** that the artifact is
  self-describing out of its app.
- **Every data state exports honestly** — an empty or partial view exports with its honest label, never
  a blank canvas (*Every data state*, applied to the export).
- **Mechanise where you can** — snapshot the exported artifact's dimensions and the presence of its key
  elements (axis text, legend), held to the same could-not-check-vs-found-nothing discipline as the
  enforcing gate's heuristics.

A *different* axis from reproducing an audit finding against the production build (`method-situational.md` verifies
*which build the reviewer reads*; this inspects an artifact the *product emits*), and where the data-viz
checklist above is most often lost — the on-screen chart carries axes and a readout the serialiser
drops.

## Pre-ship checklist (mirror SKILL.md's report discipline)
- [ ] Does it need explaining? If yes, redesign until it doesn't (or demote the text to progressive disclosure).
- [ ] All five data states handled and honest — empty / loading / error / partial / overflow — an empty state names its **coverage** (no-data-collected vs collected-and-genuinely-none), never implying a false all-clear, and any **named cause** in its copy holds on every path that reaches it, not only the one it describes; it distinguishes **filter/search-removed** from **genuinely-none** — the positive/onboarding copy is reserved for a zero **unfiltered** total, while a non-empty total with an empty view gets a neutral no-match state carrying a **clear-filter** action — and any **section chrome** (header, count, "all done" banner, see-all affordance) is **gated on content-presence** or paired with an explicit empty/no-match fallback, never captioning rows a filter has hidden; a **definitive-record surface** (audit log, security events, a decision-bearing balance/count) shows a **distinct, retryable error state** on fetch failure rather than degrading to empty — a low-stakes/supplementary value may acceptably degrade, a definitive one may not; and a capped/sliced overflow list carries an explicit **remainder indicator** whenever `total > shown`; and a partial-apply operation's visible success counters reconcile to the input total — a client response type narrower than the endpoint's actual return (a dropped `error_count`/`errors` field) is a silent undercount, not a clean partial state; and a **load-to-edit** form does not let an **unresolved** read (a failed/timed-out fetch, not a confirmed-empty one) seed its `initial`/`defaultValue` into a **full-object replace** on save — the save is gated (disabled, patched, or confirmed) until the value resolves, since here a failed read degrades into a **destructive write**, not merely a misleading display?
- [ ] Every shared hook/context's readiness/error signal is read the **same way at every consuming surface** — checked independently per consumer, not inferred from the one call site that clearly gets it right; no sibling consumer destructures only the value field while another sibling of the same instance branches on the readiness/error field?
- [ ] One channel per dimension; nothing colour-only; reads correctly in greyscale?
- [ ] Deltas are caret + magnitude, coloured by sentiment; flat is a muted `—` with a period anchor?
- [ ] Confidence / score / priority shown as a **defined labeled tier** (text + a colourblind-safe cue), not a raw `%` or point score, and no model-authored number published as precision?
- [ ] A progress / attainment display shows **coverage / readiness** ("N of M measurable / instrumented"), never a fabricated `%-complete` / grade with no measured reading; an unmeasured item renders **"awaiting reading"**, not a manufactured number; a display "awaiting reading" on nearly every row is **held, not shipped**?
- [ ] Does each primary information unit answer **why it matters** (a derived / structural signal — count, recency-delta, graph-degree — **never a fabricated importance score**), not just what happened; where an action is possible, is a concrete **next step** named; and is the **most decision-ready surface in the first paint and stable** (not a post-hydration `aria-hidden` island, not below fixed non-interactive chrome)?
- [ ] Does the **default ordering serve the user's job** (not reverse-chron by default on a decision surface), and is **each exposed sort/rank mode self-explaining ("orders by …") and measurably distinct** (near-identical modes collapsed; an opaque / near-constant sort key is false precision — measure its distribution first)?
- [ ] Matches a **named** top-product pattern; convention gaps surfaced to the owner, not silently redesigned?
- [ ] If the owner has rejected this element **twice**, stopped tuning — structural flaw named, two or three comparables researched, concrete options surfaced for the owner to choose?
- [ ] Consistent type scale / spacing / components / number format with sibling views (tabular figures in columns)?
- [ ] One shared component per concept — reused/extended, not reimplemented per page; a fix landed in the shared component, not one caller; **sibling view-variants import one shared lookup/primitive (an enum→label/colour map, a sub-element's derivation+render) rather than each re-declaring it**; **searched the tree for a duplicate twin (a duplicated visible string/heading) a diff-scoped review would miss**; and every component built for this surface has at least one **mount path** from a router/page entry, static or dynamic/lazy/registry-based (zero paths = a dead-render candidate — wire up or retire, owner's call)?
- [ ] Interaction loops close — read-back on every input (no write-only), WYSIWYG not raw markup, no dead controls — checked on the route that actually renders?
- [ ] Any action **labelled non-destructive** (resolve / archive / dismiss) that removes the record still shows it **persists** — a persisted-state label, an undo, or a discoverable resolved/archived view — so it doesn't read as a hard delete? (Default-hiding behind a *known* filter is a convention, not this; soft-delete is out of scope; **fail-open** — a human adjudicates.)
- [ ] Every **disabled action explains its cause and a recovery path** — the unmet prerequisite + a concrete next step, in **reachable** text (nearby or a focusable wrapper/popover, not a tooltip on the disabled element, which may get no hover/focus); an action permanently unavailable to the current role is hidden or replaced, not a dead end?
- [ ] **No write control renders as a dead/disabled default during the SSR → hydration window** — a control gated on client-only state (auth/session) shows a loading affordance (skeleton/spinner) or is optimistically enabled with its click **replayed** after hydration (never a dropped no-op), not a bare disabled button; confirmed on a **pre-hydration** snapshot, and *could-not-check* (no pre-hydration capture) fails **open**, not a silent pass?
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
- [ ] UI change: headed-browser receipt on the exact route after the action (screenshot or equivalent) — and the receipt is a **valid non-empty image**, not a proxy/504-wiped stub that passes a bare existence check (existence is not content — `SKILL.md` principle 2), captured from a **clean or separate tree** (a shots script that stashes uncommitted changes discards the very diff under review), and the image **shows the target feature**, not an error / login / empty-state wall (a login page is itself a valid non-empty image — confirm the feature is present, and capture in a dev/identity-bypass mode not a route-auth-walling production build, `testing-and-evals.md`); and where the receipt is embedded in a PR body, it **renders for a cold reviewer** — an uploaded attachment or an in-repo image file, never a bare link to a private raw-content host that shows broken outside an authenticated session? Unit tests alone are not this box.
- [ ] **Layout invariants hold across the sweep's matrix** — no content under sticky chrome, gutters present, optional slots reserve space, no reflow on a state change, tabular numerals in columns — checked **mid-scroll and on state transitions**, both themes, not only at the top of a fresh desktop render; and **footprint tracks information** (no empty record at a populated card's size; grid dense enough at the wide viewport)?
- [ ] **Charts are legible** — a value axis or direct labels, a **keyboard-reachable** hover/focus readout of value + its date/category, real samples marked and no trend implied across sparse points — and **interaction states are consistent per component class** (hover/active/focus parity across instances; every hover affordance also reachable by keyboard and touch; tooltips add information, not a repeat of the label)?
- [ ] **Every export / print / share path inspected as its own surface** — the downloaded artifact doesn't clip off-viewport content, bakes in the axis/legend/labels that live only in interactive chrome, honors or normalizes the theme, is self-describing (title / as-of), and exports each data state honestly (never a blank canvas)?

Parity claims (the default-state canonical surface) and "Looks the same" (the four rendered-appearance axes) live
in `rendered-parity.md`.

## Enforcing gate (Phase 6 imprint)

**A UX-bearing change does not auto-merge on code-gate green alone.** Lint, unit tests, type-check, and
a build passing prove the *code*, not the *rendered result* — auto-merging a UI change on those plus
**presence-only** evidence (a screenshot exists but is unread) ships the exact layout regressions this
reference catches. Gate a UI-change class on the UX-evidence gate below **with its inspection cited**,
not on the code gates alone; treat a **disabled or crashed** UX-quality gate as a **P0 repair that
blocks merges of that change-class** until restored — a silently-off quality gate is worse than none, it
reads green over unexamined UI (cf. `merge-operations.md`, self-reported ≠ trusted control; and
the auto-merge-on-bot-PRs flag in `dependency-currency-and-upgrades.md`). **🚩**: auto-merge on a
UI-bearing change with only code/build/lint gates + a presence-only screenshot; a UX-quality gate
disabled "temporarily" with merges still flowing.

A standard with no gate is advisory (SKILL.md Phase 6: *pair each imprinted standard with the gate that
enforces it*). When imprinting into a project that ships a UI, pair this reference with a UX-evidence
gate — held to the skill's own gate discipline: **a gate must tell "could not check" from "found a
problem," fail *open* on the former, and never be stricter than the standard** (`frontend-a11y.md`, the
`innerText` and disabled-contrast traps; SKILL.md Phase 1, gate-vs-standard). Three gates for any UI
change, in descending confidence of what they can prove — plus a fourth that fires only on a parity
task:

1. **Screens-changed evidence — the artifact, plus the inspection it demands.** On any diff that can
   change a rendered page, require a screenshot of each affected route — the **whole affected surface**,
   not a clip of only the diff's own region (a regression on an adjacent part of the surface is never in
   a cropped shot) — at a narrow and a wide width (e.g. 390 / 1440), or an explicit
   `No UX change: <reason>` line. A screenshot proves a human/agent *looked*; it does **not** prove the
   render is correct — and "screenshot attached" **with no cited inspection** is `unverified`, not
   `verified` (the treatment a parity claim with no named surface gets). The defects that survive every
   other gate are the ones only a look at the image catches, so a UI status **names what it inspected**
   from this checklist (defined once here; a status cites the items):
   - **overlap** — no two text / interactive elements intersect (mechanical proof: the bounding-box
     non-intersection assertion, `testing-ui.md`);
   - **clip / truncation** — no unintended ellipsis or cut glyph at the narrow width
     (`scrollWidth > clientWidth`, same file);
   - **contrast** — text meets AA against its *painted* background (`frontend-a11y.md`);
   - **disabled-looks-disabled** — a functionally disabled control is *visibly* disabled (cursor /
     opacity / painted colour, not only the attribute; the *no-dead-controls* interaction-completeness
     rule above, seen in the render);
   - **not-dead-before-hydration** — a write control gated on client-only state shows a loading
     affordance (or is optimistic-enabled with a **replayed** click), not a bare disabled default, in
     the **pre-hydration** render; the static `disabled={!session}` tell is an `unverified` lead until
     that snapshot confirms it (principle 2), so a harness that cannot capture pre-hydration reports
     *could-not-check*, never a pass;
   - **state named** — which data state the shot is of (empty / loading / error / populated), so an
     absence reads honestly (gate 2's state coverage; the empty≠all-clear rule above);
   - **sticky-chrome collision** — nothing content-bearing paints under a sticky/fixed header or bar;
     visible only mid-scroll, so it is checked at scroll offsets, not only at the top of a fresh render;
   - **gutters present** — every scroll container and sticky bar has padding, so content is not flush to
     the edge or to the chrome;
   - **optional slots reserve space** — a row's rail and baseline hold whether or not an optional
     element (avatar, badge, trend) renders; check the absent-slot variant, so a row doesn't go ragged
     when a slot collapses;
   - **no reflow on a state change** — a control keeps its box across loading→loaded and
     collapsed→expanded (a before/after box compare — the same geometry primitive as *overlap* above),
     checked on the transition, not only at rest;
   - **tabular numerals** wherever numbers stack in a column, so values don't jitter the alignment as
     they update (the tabular-figures rule of *Match a named standard* above, here as a mid-update
     stability invariant).

   Of these, **sticky-chrome collision reads only mid-scroll**, and **reflow (and numeral jitter) only
   across a state change / value update** — a single top-of-page shot can't see them, so on a `FULL`
   review they're ruled across the **rendered route sweep**'s matrix (above). **Gutters and
   optional-slot reservation read at rest** (the latter in the absent-slot data variant) — check them on
   the per-change shot too, and re-confirm in the sweep rather than defer to it. And
   **not-dead-before-hydration reads only before the client bundle runs** — a fourth timing class
   neither the at-rest shot nor the mid-scroll sweep can see, because both capture the *post-hydration*
   render; it needs a snapshot taken inside the SSR → hydration window (a pre-hydration or CPU-throttled
   capture, `testing-ui.md`), and where the harness can't take one the item is *could-not-check*,
   not clean.

   **A PR-body image embed is not evidence unless it renders for the reviewer, not just the author.** A
   `![...](<url>)` pointing at a private raw-content host — a raw-file URL requiring an auth header or
   an authenticated session a markdown renderer's plain `<img>` fetch can't supply — **may render only
   for a viewer already authenticated to that host** (and can break even for the author, under
   cross-origin cookie scoping), showing a broken-image icon for everyone else viewing the PR; on a
   private repo, that's every reviewer reading the PR body cold. The markdown tag *exists* in the diff;
   the evidence does not (existence is not content — SKILL.md principle 2, the same gap the pre-ship
   receipt check above closes for a captured-but-blank image; this closes it for a
   captured-but-invisible one). Gate on **visibility, not presence**: an **uploaded attachment** (the
   review platform's own image upload, served through its own proxy) or an **in-repo, diff-able image
   file** committed with the change both satisfy the bar; a link to a private raw-content host does not,
   even when the file behind it is a real, correct screenshot. **🚩**: a PR-body `![...]` whose URL is a
   raw-content-host link — not an uploaded attachment or proxied URL — on a private repo, with no
   in-repo image file backing it.

   A screenshot with an unstated inspection is an artifact read as the verification it is not.
2. **State-coverage in tests (proves the branches exist).** A component test that renders a data view
   asserts the **empty and error** branches, not only the populated one — extends
   `testing-and-evals.md`'s "test the failure, not just the feature" to UI states.
3. **Encoding self-test (heuristic — scopes its own claim).** Where a design system exists, a lint/unit
   check that no single colour token is bound to two semantic names, and that every status/delta element
   carries a non-colour channel (icon/text + `aria-label`). Both are **heuristic**: a static "one token,
   one meaning" check can't see runtime binding, and "has a non-colour sibling" false-positives on
   decorative nodes — so it **warns and lists**, never fails closed, reporting what it couldn't resolve
   as `unverified`, not clean. Model: a renderer-tolerant ratchet — a pinned exception is *allowed*,
   never *required* to exhibit. Same gate, same discipline, for **chart anatomy** (data-viz above): a
   heuristic assertion that an `<svg>`/canvas chart exposes **axis tick text or a hover/focus readout
   target** and that a series isn't colour-only — it **warns and lists**, never fails closed, because it
   false-positives on a legitimately decorative chart (the `aria-hidden` + printed-number exemption
   above), and whether the readout returns the *right* value stays a human inspection.

4. **Parity differ (parity tasks only — proves *equivalence*, not just that a human looked).** For a
   "make X match reference Y" task, build a mechanical differ **before** any pixel-matching and gate
   every "matches" claim on it. The differ drives both the reference and the target for each screen and
   emits (a) a side-by-side + pixel-diff **image** and (b) a **structured** mismatch list — which nav /
   tab labels are present or absent on each side, the header strings, and bounding-box geometry deltas
   for key elements. **The artifact shown to a reviewer is the diff image, never a sentence.** **Render
   both sides at the same viewport width** and diff the corresponding region — a cropped or scaled
   screenshot of **one** side is a **hypothesis, not evidence**; never infer a present/absent delta from
   one side alone. Before recording an element as app-only or design-only, **confirm its state on the
   other side**: present-but-collapsed, present-but-**disabled-by-data** (a stepper bound to one item
   has nothing to step to), or present-in-a-menu — "absent in this crop" is not "absent in the design".
   This is the evidence feeding the classification (`migration-parity.md`,
   *restyle-an-app-only-feature*): a delta that doesn't exist has no bucket, and every wrong inference
   here is one destructive edit — a removed control, a duplicated element — away. **🚩** a "missing" /
   "extra" parity call whose only evidence is a one-sided crop, or made with the other side's state
   unchecked. Load a no-routing prototype **once and click-navigate** its in-page tabs (it has no
   per-screen URL to fetch), and diff against an existing **running build** of the design if one is in
   the repo rather than reverse-engineering its source (reference-fidelity order,
   `rendered-parity.md`). It diffs **chrome / structure / styling, not text values** — diffing the numbers would flag
   real data as a mismatch and tempt the fix that fabricates (`migration-parity.md`). What it **cannot**
   prove: an intentional improvement from a regression, and its pixel threshold is **agreed, not
   derived** — a human still owns the ship call. **Parity is *set equality*, not containment — run the
   present-or-absent list above in *both* directions.** Produce it per screen as **design → app** (what
   the design has that the app lacks) *and* **app → design** (what the app renders that the design does
   not); an element on exactly one side is a finding **regardless of which side**, and the app→design
   half is the one that gets skipped. The **operative test** for an app-only element — *does removing it
   lose a user capability?* If **no**, it's pure **decoration** (an extra header, a "Showing N of N"
   line, a duplicated label): default **remove-to-match**, and "intentional extra" is the
   rationalisation that ships the mismatch. If **yes** (a per-card upvote, a filter bar, a view tab, a
   deep-link button — removing it removes upvoting, filtering, navigating), it's a **feature**: the
   default is **not** escalate-and-wait but **restyle it into the target's design language**. Deleting
   it to match the mock is a **High** do-no-harm finding, never self-certified. `migration-parity.md`'s
   *restyle-an-app-only-feature* rule governs the classification (and the
   re-express-in-the-target's-own-primitives mechanics), its severity, and the exception ledger;
   escalation to the owner is the **fallback** when no target primitive fits, not the whole answer.
   Scope all of this to **chrome / features**; **data** (values, counts, series) legitimately differs
   (`migration-parity.md`). *Done* on a parity task = the design→app list is empty; the app→design list
   is empty **or every entry is resolved** — restyled into the target's design language, decoration
   removed, or an owner-adjudicated keep/removal (a bare app→design list is not an automatic differ fail
   — the differ can't tell an intentional improvement from a regression, so that half routes to
   classification and, where needed, human adjudication); and the pixel delta is under the agreed
   threshold for every screen in the correspondence table, with those diff images attached — never an
   assertion.

Ship these **idempotent and additive**, per Phase 6 — detect-and-stop if present, add only what is
missing, defer to an existing style guide (the parity differ only when the task is a parity task).
