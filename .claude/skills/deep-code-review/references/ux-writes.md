# Product UX depth — writes from the UI (optimistic reverts, load-to-edit forms, reversible actions)

Read this when the target or diff writes from the UI: an optimistic mutation whose failure path rolls back, a load-to-edit form seeded from a fetch and saved as a full-object replace, or a resolve / archive / dismiss action that removes a record from view. Split from `product-ux-quality.md`, whose stance, data-state rules, encoding rules, 🚩 grep, and pre-ship checklist apply to every UI review.

## A reverted optimistic write is the one error path that skips the app's shared safe-message mapper

The five-states *error* rule (`product-ux-quality.md`) bars a raw stack on any failure; this is its consistency twin,
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
region, **read aloud** to a screen-reader user (`a11y-live.md` owns the announced-surface phrasing).
The defect is not "a raw error is rendered" — the states-block grep in `product-ux-quality.md` already owns that — it is the
**asymmetry**: a shared mapper exists and is called at sibling call sites, and this one path bypasses
it, so the app speaks two different error languages depending on which write failed.

**Fix — one mapping boundary.** Every user-facing failure string, a reverted optimistic write's
included, goes through the same shared mapper the normal path uses; the revert handler passes the caught
value to the mapper rather than reading `.message`. Acceptance: a test that makes `fetch` reject with a
raw `TypeError` asserts the rendered (and, if announced, the `aria-live`) text equals the mapper's fixed
fallback, not the raw message — a test mocking only a curated 5xx won't catch it. Same all-consumers
discipline as the least-careful-consumer rule in `product-ux-quality.md`, a different **stakes** class: there a sibling
ignoring a shared *readiness signal* renders a wrong confident value (data-honesty); here a path
bypassing the shared *message mapper* leaks a raw internal string (a user-facing leak — cross-ref
`security-appsec.md` A02 verbose-errors / A10 leaked-internals and `domain-b.md`'s
error-class-not-upstream-response-bodies rule). `reliability-error-handling.md` owns the *server* error
contract; this owns which client path renders it.

**🚩**: a shared error-message mapper (`toSafeMessage` / `toUserMessage` / a toast helper) called at
ordinary request call sites, together with an optimistic mutation's `onError` / `catch` / rollback
handler that reads `(err).message` or renders the error object **directly** instead of calling that
mapper — narrower than the generic *`catch` rendering `err.message`/stack* grep in `product-ux-quality.md`'s states
block, which flags the raw render but not the bypassed-shared-mapper asymmetry.

## A read-failure that seeds an editable form turns a misleading display into a destructive write

The read-failure-honesty family (`product-ux-quality.md`) governs what a failed read may **render**; this is its sharper twin
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
— read-first opener, `product-ux-quality.md`). A **soft-delete** (`deleted_at`) is out of scope: "reads as a
delete" is its *intended* behaviour; its concern is recoverability / trash-visibility, not this.
Like the actionability rule (`ux-lists.md`), this is **fail-open**: a heuristic can't tell a hidden-reversible
action from a deliberate convention, so a human adjudicates every hit — surface options, never
silently restyle.

The self-evident fix — how mature issue-trackers and code-review tools render a resolved thread
— keeps the record **in place, visually muted** (opacity or strikethrough) with a **status
label** ("Resolved"), or offers a clearly labelled, discoverable "resolved / archived" view.
Cross-checks: the affordance must **not rely on colour alone** (pair opacity with a label or
icon + accessible name, per *Never colour alone* in `product-ux-quality.md`); a "show resolved / archived" path must
be **discoverable**, not a buried default-off filter with no cue; verify on the **running app's
default surface**, not only a unit test. Distinct from the honest-empty rule in `product-ux-quality.md` (a *retained*
record hidden by a *reversible* action, not an empty state).
