# Frontend reliability & performance — data fetching and async state

Read this when the target or diff fetches data for a view: dependent requests on the render-critical path, a shared read hook (`useUser` / `useSession` style) that many components call, a `<Suspense>` boundary, a loader reachable from two entry points (refresh and pagination, or a re-issued search), a debounced URL or shared-state write, or an optimistic update with a rollback. Split from `frontend-a11y.md`, whose Core Web Vitals thresholds and base performance checklist apply to every UI review.

## Reliability & performance — data fetching and async state

- **No sequential data-fetch waterfall on the critical path.** Dependent requests that each start only after
  the previous resolves (a **critical request chain**) push out LCP/TTI even when every individual request is
  fast and the bundle/image/font budgets are all green — a green byte-budget is not a green load; chain
  *depth*, not payload size, is the cost. Flag chained `await`s / dependent fetches on the render-critical
  path; parallelize independent ones (`Promise.all`), collapse the chain server-side (a BFF/single endpoint
  returning what the view needs in one round trip), and prefetch/colocate data with the route so it fires on
  navigation. Measure the request-waterfall, not only the bundle budget (Chrome Lighthouse, *critical request
  chains*). The same accidental-serialization shape inside a server handler's own loader — no browser round
  trip involved, hurting TTFB rather than LCP — is `performance-db-cost.md`'s Concurrency section.
- **A singleton-read hook that fetches per instance fans out to one identical request per mounted consumer — a
  page with N callers makes N copies of the same call.** A `useUser()`/`useSession()`/`useCurrentUser()`-style
  hook — or any hook many components call to read the *same* shared singleton — implemented as its own
  fetch-on-mount (`useState` + a `useEffect` that `fetch`es `/me` and `setState`s, or a fetch on first render)
  with no shared cache or dedup fires an **independent** network request from **every** component calling it,
  so a page mounting a dozen consumers issues a dozen identical `/me` requests on one load. It reads clean at
  the hook (small, correct, returns the right `{ user, loading }`) and clean at each call site (which just
  calls the hook); the redundancy exists only across the *set* of call sites, surfacing only as the network
  tab's N copies of one request — a per-file review never sees it. Worst when the callers sit in the **global
  shell** (nav bar, command palette, global FABs, an auth guard): those mount on **every** route, so the
  multiplier is paid per navigation, and each consumer runs its **own** retry/backoff on failure and gates its
  own region's render on its own copy of `loading`, compounding perceived slowness beyond the raw N×
  server/network load. Detect by grepping the hook's call sites and asking whether the fetch lives behind a
  single shared **Provider/Context** (or a keyed dedup cache) or a **per-instance** effect; count the
  consumers the global shell mounts — each is a per-route multiplier. Strong tell: the codebase already
  documents this cost at **one** call site specially re-engineered to avoid it (a hoisted fetch, a
  threaded-down prop) while other global sites still pay it — name that precedent to make the fix trivially
  arguable. Fix: mount **one** Provider/Context (or back the hook with a request-deduping cache — SWR /
  React-Query keyed on the resource, or a module-level in-flight singleton promise) once near the root, doing
  the single fetch/retry the hook already implements, and switch every call site to a context read; **keep the
  hook's public return shape** so no consumer changes. Acceptance = exactly one identity fetch per page load
  regardless of consumer count. Distinct from the **waterfall** bullet above by *shape*: that's chain
  **depth** (dependent requests each awaiting the previous; fix = parallelize or collapse), this is identical
  **breadth** (independent requests for the *same* value; fix = coalesce to one) — same load cost, opposite
  geometry. Distinct from **N+1** in `performance-db-cost.md` (Database): that's N *different* queries, one
  per **row** of a result; this is N *identical* requests for one **singleton**, one per **component
  instance**. The coalescing itself is the **de-dupe / single-flight** mechanism from `performance-db-cost.md`
  (External calls, and the cache-expiry stampede) applied one layer out — at the client component tree rather
  than a server cache.
- **A reusable component that owns its per-item data fetch is fine mounted once and an N+1 when a caller
  mounts it per row.** Check **every call site** of a shared component with a private fetch hook: can it mount
  many times on one page, and does the request count scale with that? One observed run: 47 separate requests
  to one per-item endpoint from a single page (counted by decoding each request's parameters, since a raw count
  can double under a dev-mode double render). **Fix — shared-instance prop with private-fetch fallback:** an
  optional shared-data prop fed by one batched fetch, with the private fetch kept as the default, so
  single-mount callers are unchanged. Distinct from the
  singleton-read-hook bullet above, where every mount wants the *same* value (fix: dedup/cache).
- **A fetch already collapsed to one request behind a shared hook/Provider is still issued again by an
  always-mounted consumer that kept its own raw fetch of the same URL.** Once the identity / notification /
  settings endpoint is lifted behind the single Provider/Context or request-deduping cache from the bullet
  above, call sites reading through it collapse to one request as intended — but a consumer never folded in
  (typically a nav badge, shell chrome, or a telemetry hook mounting on **every** route) keeps its **own**
  `fetch`/`useEffect` against the same resource, so one load still issues that request **twice** — once for
  the folded set, once for the outlier — not once (more, if several were left out). This is not the
  absent-coalesce case above: the coalescing boundary **exists and works**; the defect is **partial adoption**
  — one always-on consumer left outside it. That difference is load-bearing for **detection**: the bullet
  above says to grep the *hook's* call sites, but the outlier **does not call the hook** — it holds a raw
  fetch — so a hook-name grep **structurally cannot see it**. Grep the **resource URL/endpoint**, not the hook
  or context name, and reconcile every hit against the shared instance's importers; the leftover hit is the
  outlier. A comment at the shared instance ("lifted this to avoid a double fetch") is a cue to **audit for a
  third consumer**, not proof the dedup is complete. It's the exact inverse of the *Strong tell* in the bullet
  above — there **one** site is specially re-engineered while the rest fan out; here the rest are folded in
  while **one** site is left out — same partial-adoption geometry, opposite majority. Two consequences the
  folded set never exhibits: (1) the outlier usually runs its **own polling timer**, so its derived view (an
  unread-count badge) drifts **out of sync** with the shared store until each refreshes on its own schedule —
  a visible **consistency** bug, not just wasted bytes; (2) a test scoped to the shared hook alone asserts a
  single fetch and **passes** while the outlier still double-fetches — the regression test must **mount every
  known consumer together** (nav + shell + a page consumer) and assert one request. Fix: migrate the outlier
  onto the same shared instance — delete its raw fetch and its private poll, read the context/cache — so a
  single fetch and a single refresh loop feed every consumer. Distinct from the identity fan-out bullet above
  by *state*: that **builds** the coalescing boundary and switches every call site; this is that boundary
  already built, with one always-mounted consumer never moved onto it.
- **A `<Suspense>` boundary whose subtree never *suspends* has a dead fallback — the "loading state" it looks
  like it adds renders nothing.** A Suspense fallback paints only while a descendant actually suspends —
  throws a promise the boundary catches — which is what a `lazy()`/`React.lazy` component (before its chunk
  arrives), a `use(promise)`/`use(Context)` on a still-pending value, a suspense-enabled data library, or an
  `async` Server Component the boundary streams do. **The discriminator is *where the awaiting happens*, not
  whether the child holds data:** the fallback is live when an **unresolved** promise (or the async child
  itself) crosses the boundary and something under it does the waiting; it's dead when the slow `await`
  already ran **above** the boundary, so the value handed in is fully resolved and nothing under it can throw.
  Two common shapes look like they added a loading state and didn't: (a) a client component that fetches in a
  `useEffect` and `setState`s — it mounts and renders **synchronously** with its data still `null` (typically
  a blank or empty-state branch), then re-renders when the effect resolves, so the wrapping `<Suspense
  fallback={<Spinner/>}>` shows the child's `null`-data render for the whole wait, not the spinner; (b) a
  child handed only already-resolved plain props because the slow `await` ran earlier in the same or a parent
  async function, before this JSX was built — contrast the *live* case, where a parent threads an
  **unawaited** promise down for the child to `use()` and the boundary suspends correctly; the fault is
  awaiting above the boundary, not passing data through it. In neither dead shape is the fallback ever
  reachable. It hides: the JSX visibly contains a fallback, a fast local connection makes the missing feedback
  imperceptible; on a real network the surface is a frozen/blank wait or a false empty flash — a frequent,
  invisible contributor to "the app feels heavy/slow." Fix by intent: if the fallback is genuinely wanted,
  move the data-loading into a mechanism that suspends — a `use(promise)` on a promise created **above** the
  boundary and passed through it, a suspense-enabled query hook, or a nested `async` child the boundary
  streams — and/or add the framework's route-level loading convention (a Next.js `loading.tsx` wraps the route
  in a real boundary) when the whole route is the wait; if the fetch legitimately stays effect-based, **remove
  the dead `<Suspense>`** (it's a false sense of a loading state) and render an explicit loading branch from
  the component's own state (`if (loading) return <Skeleton/>`), separating not-yet-loaded from
  genuinely-empty. This is the precondition behind curing a blank-screen route by wrapping it in `<Suspense>`:
  the wrap works only once the slow work moves **inside** the boundary — leaving the `await` at the top of the
  render, or resolving the props before the JSX, leaves the fallback dead. Detection: for each `<Suspense>`,
  trace its subtree for a real suspension source (`lazy()`, `use()` on a pending value, a suspense-enabled
  hook, an awaited `async` child) and for any unresolved promise crossing the boundary; finding none, flag the
  fallback as dead, and sweep the broader shape — an effect-fetching or resolved-before-render page with a
  Suspense fallback (or no adjacent route-level loading file) showing no feedback on navigation. **Distinct**
  from the `role="status"`/`aria-busy` loading bullet in `a11y-live.md` (whether a loader that *does*
  render announces itself) — this is whether it renders at all; and from a real, explicit `if (loading) return
  <Skeleton/>` state, which isn't this bug. Regression-test on a throttled network, or assert the fallback
  actually mounts — not a fast local load.
- **A cleanup arm shared by two async operations clears a loading flag it doesn't own — a sibling or
  superseded invocation's settle flips off the flag the *current* operation still needs.** One loader serves
  two entry points — `load()` for initial/refresh and `load(cursor)` for pagination, each with its own
  in-flight flag (`loading` vs `loadingMore`) — and the shared `.finally(() => { setLoading(false);
  setLoadingMore(false); })` (or a shared `setBusy(false)`) resets **both** unconditionally, so when the
  pagination call settles it also clears the refresh flag while that refresh is still in flight: cross-*path*
  clobber. The single-flag variant is the same defect across *generations* — a search/typeahead path re-issues
  its request as the query changes, both attempts share one `finally` flipping one `loading`, and the
  **superseded** first attempt, resolving last, clears `loading` while the current attempt is still pending:
  cross-*generation* clobber. The unifying rule: **a cleanup may only clear a flag the current, owning
  invocation set** — (a) violates ownership across paths, (b) across generations, both fixed by establishing
  operation identity before the settle may clear. **The failure is not a cosmetic flip.** The control gated by
  the wrongly-cleared flag reads "done" mid-request — the spinner vanishes over still-loading or stale data,
  and a re-enabled "load more" button (or a refresh listener) fires the path again with a now-shifted cursor;
  when the original, superseded response resolves, an append-style reducer (`setItems(cur => [...cur,
  ...page])`) appends rows overlapping what the re-fire already added → **duplicated items**. It reproduces
  **only under overlap** (a refresh landing during pagination, or a query change mid-request) **plus
  out-of-order resolution**, so every single-path test passes. **Detect** by finding any loader reachable from
  two entry points and reading its cleanup: does one `.finally`/`setBusy(false)` reset a flag it doesn't own,
  or can a stale invocation's settle clear a flag a newer one still needs? A single shared cleanup calling
  more than one `setLoading*(false)`, or a `setLoading(false)` on a path that can run concurrently with
  itself, is the tell. **Fix** in two parts: scope each path's cleanup to the flag it owns (`if (isPagination)
  setLoadingMore(false); else setLoading(false);`), or give each operation its own flag; **and** establish
  **operation identity before the settle** — stamp each request with a monotonic id (or an `AbortController`),
  let only the current id's `finally` clear the flag, and **drop** (never append) a response whose id is no
  longer current. **Regression-test the overlap explicitly**: fire both paths, resolve them **out of order**,
  and assert both the flags *and* the resulting list — a single-path test asserts neither the cross-path flag
  clobber nor the stale append. Distinct from two loading-state bullets nearby: the
  `role="status"`/`aria-busy` bullet in `a11y-live.md` is whether a loader that *renders* announces itself,
  and the dead-`<Suspense>` bullet above is whether the loader *renders at all* — here it renders fine and is
  *cleared by an operation that doesn't own it*. The `AbortController` mechanism, and the discipline that
  cancelling a superseded request is a **user-cancel, not a swallowed timeout**, live in
  `reliability-error-handling.md` (Timeouts, aborts, retries); the "an older result must not clobber current
  state — gate on a version/id" shape is `billing-correctness.md`'s out-of-order rule (compare the provider's
  version/timestamp) applied one layer out, at a client reducer. Distinct too from the fetch-dedup bullets
  above, which govern *how many* requests fire, not *which* operation's flag a shared cleanup clears.
- **A debounced write to the URL/shared state closes over the values it read when the timer was *scheduled* —
  a change made for another reason while the timer is pending is reverted when the stale timer fires.** A
  control that writes the URL/query on a delay (a search box that `setTimeout`s a `router.replace`/`push` a
  few hundred ms after the last keystroke, an autosave, a slider that debounces its commit) builds the write's
  payload from the params/state captured at *schedule* time and holds it in the pending closure. Before the
  timer fires, the same URL/state moves on for an unrelated reason — the user clicks a filter chip, a nav
  writes a param, another control commits — via its own *immediate* write. The pending timer then fires with
  its captured-stale set and re-writes the URL from it, silently dropping the concurrent newer write (the
  filter "un-clicks itself," the just-set param vanishes ~300 ms later). It reproduces **only under overlap**
  — a second write landing between a debounced write's schedule and its fire — so every single-control test
  passes; a **per-component copy** of the debounce makes it worse, since two controls each keep their own
  stale snapshot and clobber each other. **Fix — read current state at fire time, never replay a captured
  one:** move the debounce into an effect keyed on the changed value whose cleanup cancels the still-pending
  timer on every re-run and on unmount (so the write re-schedules whenever the value changes and no superseded
  timer survives), and build the payload **inside** the timer from the live URL/router state (or a
  functional/merge update — `params => ({ ...currentParams, q })` read at fire time), never from a set closed
  over at schedule time; route every debounced writer through **one shared debounced-write hook** so they all
  funnel through the same current-state read instead of each holding a private snapshot. Detection: a
  `setTimeout`/debounced callback spreading captured params/state into a `router.replace`/`push`/`setState`
  with **no** cleanup clearing the pending timer when its keyed value changes, or a per-component debounce
  copy of a URL write. Regression-test the overlap: schedule the debounced write, issue a *different* param's
  write before it fires, let it fire, and assert the concurrent change survives — a single-control test
  asserts neither write's outcome under overlap. Distinct from three neighbours: the shared-`.finally`
  loading-flag clobber above clears a loading **flag** a concurrent operation doesn't own (this reverts a
  **state/URL value**, not a flag); the fetch-dedup bullets above govern **how many** requests fire (this
  governs **which write wins**); and the URL-backed-state bullet in `frontend-a11y.md` ("Drawer / filter / detail state should
  be URL-backed") is about state that **never reaches the URL** (held only in `useState`) — here it *does*
  reach the URL and a stale timer reverts it. The general concurrent-writer form (two writers racing on one
  value, needing a lock/CAS/version) is `concurrency-shared-state.md`'s read-modify-write rule applied at a
  client debounce.
- **An optimistic write that reverts to a value it captured before the call has no idea a *newer* write
  already committed a different value — on failure it reverts to the stale one and clobbers the newer.** An
  optimistic-update handler (drag-to-reorder, an inline edit, a toggle) writes the new value into keyed client
  state — `state[id] = next`, a map keyed by item id, a single field — **before** the persist request
  resolves; the success path leaves it, the failure path reverts by deleting or resetting that key to the
  value captured at write time. Correct for a **single** in-flight write, it becomes a clobber the moment the
  same key is written a **second** time before the first settles — a second drag, a fast double-click, a
  keyboard repeat, all ordinary interactions when the trigger has no disable-while-pending guard. Sequence:
  write 1 sets `state[id] = A` and fires a slow request, capturing `prev`; before it resolves, write 2 reads
  the current (already-optimistic) value, sets `state[id] = B`, and fires a fast request that **succeeds**,
  correctly leaving `B`; write 1 then **fails** (or simply resolves out of order) and its revert
  **unconditionally** resets `state[id]` to its captured `prev` (or deletes it), clobbering the confirmed `B`
  and snapping the UI back to a stale or pre-write-1 value — usually with a misleading "your change was
  reverted" attached to a request the user has already forgotten. Neither branch checks whether the value it's
  about to overwrite is still the one **this** call wrote. It survives review because each handler reads
  correctly alone (write, then undo on failure) and a single-call unit test — call once, resolve/reject the
  mock, assert state — always passes; the bug lives only in the **interaction** of two calls on one key.
  **Detection:** for any optimistic handler, (1) confirm the trigger can fire a second time on the same key
  before the first request settles (no `disabled`-while-pending, no debounce that would prevent it), and (2)
  check whether the revert (and, for symmetry, the success write) mutates by **bare key** or first checks "is
  the current value/token still the one I wrote" — a captured-value compare, or a monotonic per-key request
  token where only the latest token's continuation may mutate state. Bare key plus a plausible double-trigger
  is the bug; **verify before filing** by tracing the exact two-call mutation sequence and showing the
  clobber, not just "seems racy." **Fix — a per-call identity guard (a client-side compare-and-set):** capture
  the value or a request token when the optimistic write happens, and only mutate in the async continuation if
  the current value/token still matches what this call expects; regression-test two overlapping calls on one
  key with the first failing after the second succeeds, asserting the final state reflects the second
  (successful) call. Distinct from the debounced-write bullet directly above: there the stale value is a
  **schedule-time snapshot** a debounce timer replays on its own (successful) late fire, fixed by reading
  current state at fire time; here it's a **pre-write value** reset on an out-of-order mutation's **failure**
  path, fixed by a per-call token — both a stale write clobbering a concurrent newer one, different trigger
  and fix. Distinct too from `ux-writes.md`'s reverted-optimistic-write bullet, which governs which
  **mapper** the revert's error *message* passes through (a user-facing string leak) — this governs whether
  the revert's **state write** still owns the key (a data-correctness race); same handler, orthogonal defects.
  The general concurrent-writer form (a lock/CAS/version on one shared value) is
  `concurrency-shared-state.md`'s read-modify-write rule, here applied to keyed **client** state on the
  optimistic-revert path.
