# Product UX depth — interaction completeness and consistency

Read this when the target or diff adds or changes an interactive control: an input and its read-back, a success / completion message, a rich-text field, a filter / facet option, an in-page anchor to another view, a disabled or hydration-gated control, a disclosure default computed from fetched data, an edit that needs change history, or hover / active / focus behaviour shared by a class of controls. Split from `product-ux-quality.md`, whose stance, data-state rules, encoding rules, 🚩 grep, and pre-ship checklist apply to every UI review.

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
  (`concurrency-shared-state.md`'s read-modify-write; the reverted-optimistic-write mapper in
  `ux-writes.md`): those are an optimistic-UI *race* (a newer write clobbered, or a raw error string leaked) —
  this is a **process/pipeline mismatch**, the copy asserting completion the read plane can't back, no
  race involved.
- **WYSIWYG, never raw markup shown to users.** Store markup; **display it formatted**. A rich-text
  field showing `**bold**`, `<u>`, or `*` tokens while the user types has leaked its storage format into
  the UI — render what the text will look like once posted.
- **A click-anywhere-to-edit wrapper's interactive-skip-list must cover every element the field can render
  *while being edited*, not only its read-state elements.** The common pattern wraps a read-only view in a
  click-to-edit handler with an explicit skip-list (links, buttons, inputs) so clicking those doesn't also
  re-trigger the outer edit. That skip-list is usually written before the field grows a richer nested
  editor — a contenteditable rich-text region, or an inline editor panel the field renders once opened —
  which don't match the original list's element types. A click, or even a keystroke (Space/Enter), inside
  the open editor then bubbles up and re-triggers the outer handler, closing the very panel the user is
  mid-edit in. When reviewing this pattern, name every element type the field can render while open —
  contenteditable/rich-text regions and any nested editor panel included — and confirm the skip-list covers
  all of them, not just its read-state set.
- **No dead controls, and disabled must look disabled.** A button/toggle/arrow rendered enabled whose
  handler is a no-op is a trust defect; an unavailable control must *look* unavailable, not merely be
  inert. Unit-logic tests passing is **not** a working UI — exercise the real control in the running app
  (cross-ref the live-verification rule in `product-ux-quality.md`'s pre-ship checklist).
- **A control-inventory / presence gate (which controls render, keyed by name or role) proves presence, not
  that the control works — it needs a separate functional/interaction pass, not a substitute for one.** A
  fast pre-merge gate that lists rendered controls catches accidental removal, and is structurally blind to a
  control that renders, reports itself enabled, and still does the wrong thing (or nothing) when activated —
  "renders but doesn't work" is a different bug class from "was removed," and a green inventory gate is not
  evidence a batch of behaviour changes is safe. Two observed shapes: an edit-confirmation control vanished
  from the real user flow while the inventory gate stayed green (the name it checked for was still present
  elsewhere); a picker rendered and reported present but opened nothing when clicked — the gate proved
  presence, not that the click did anything. A third, related false-positive: the same inventory style, keyed
  by accessible name, flagged an intentional label change on the same control as a "removal." For any
  interactive (not display-only) surface, require both: the inventory/presence check *and* a pass that
  actually invokes each changed control and asserts on its effect.
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
  gate the cross-link too. **Distinct** from the section-chrome-gated-on-content rule in `product-ux-quality.md` (a
  header/count/affordance emitted *outside* a filtered row's presence conditional in the *same*
  component): that is a same-component chrome/empty defect; this is a *cross-component* anchor contract
  broken by a conditionally-omitted `id`, whose blast radius is a dead link on *another* surface.
- **A disabled action explains its cause and its recovery path — not a dead end.** Looking disabled
  (`ux-gates.md` gate 1's *disabled-looks-disabled*) and disabling the same way at every instance (the
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
  five-states rule in `product-ux-quality.md`) and must *look* loading — a skeleton or spinner affordance — not a bare disabled
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
  component, it survives the *one component per concept* grep (`ux-components.md`; that catches duplicate markup; this
  catches divergent state styling on the same component). **Every hover affordance has a non-hover
  path** — anything revealed only on hover is also reachable by keyboard focus and present (or behind an
  explicit control) on touch; a hover-only action is a defect, not a power feature. A **tooltip carries
  new information** (a value, a date anchor, a definition), never a repeat of the visible label. And a
  disabled instance looks disabled the **same way** everywhere — the across-instances form of
  *disabled-looks-disabled* above. (`frontend-a11y.md` owns that a focus ring *exists*; this owns
  **parity** of the reaction across the class.)
