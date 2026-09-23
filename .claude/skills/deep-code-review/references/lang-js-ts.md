# JavaScript / TypeScript red flags

Read this when the target contains JavaScript or TypeScript. Split from `language-stack-redflags.md`; its fast first pass and cross-language sections apply to every review, and each hit here is a signal, not a verdict.

## JavaScript / TypeScript

- `eval(`, `new Function(`, `setTimeout("string")` → code injection.
- `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`,
  `dangerouslySetInnerHTML`, Vue `v-html` → DOM XSS. Use text nodes / framework
  binding / sanitizer (DOMPurify).
- `child_process.exec(` / `execSync(` with a built string → command injection;
  use `execFile`/`spawn` with an arg array.
- `==`/`!=` (coercion) vs `===`; `JSON.parse` on untrusted input without a
  schema; prototype pollution via `Object.assign`/merge of untrusted keys
  (`__proto__`, `constructor`, `prototype`).
- `a || b || default` over decoded JSON/config → the same **falsy**-skip footgun (`0`, `false`,
  `""`, `NaN` fall through). Use `??` (nullish coalescing) so only `null`/`undefined` fall back,
  and test with `0`/`false`/`""` present.
- A shared sort comparator that can return `NaN`: an `isMissing`/`isBlank` guard covering
  `null`/`undefined`/`''` but not `NaN` lets a `NaN` (failed `parseFloat`/`Number()`, `0/0`, an
  unresolved average — all `typeof 'number'`) slip the type dispatch into `a - b`, so the comparator
  returns `NaN`. `Array.prototype.sort` never throws on this and the order is silently corrupt — one
  `NaN` can scramble the order of *other* valid values, not only misplace itself. Fold
  `Number.isNaN(v)` into the *same* "missing" predicate every caller shares (missing sorts last, both
  directions); regression-test one `NaN` among several distinct numbers and assert **global
  monotonicity** of the sorted result in both directions, not just where the `NaN` landed. Distinct
  from the attacker-chosen-key comparator DoS (`language-stack-redflags.md`) — that is worst-case *complexity*; this is a
  wrong *return value*.
- A sort comparator that **hand-places one sentinel but not its siblings.** A placeholder forced to
  a fixed end by naming it — `if (a.status === 'TBD') return 1`, or a `null`-goes-first branch — pins
  *that one* value and lets everything else fall through to the natural-key compare. Introduce a
  **second** placeholder later (an `'N/A'` beside the `'TBD'`, a new enum member) and, because the
  change touches the domain and not this function, it misses the branch, sorts by its **raw key**, and
  lands in an arbitrary-but-consistent slot (a label `localeCompare`s wherever its letters fall).
  Distinct from the `NaN` bullet above — that returns a *malformed* value and breaks the total-order
  contract, so the monotonicity assertion catches it; this returns a **valid** order and only
  *mis-places* the value, so that same assertion stays green and the bug reads as surface-specific.
  Fix by keying on a **positive** predicate — *"is this a real value?"* — so the `else` forces
  **every** placeholder, present or future, to the end by construction, with no list to keep complete.
  If you must enumerate them, enumerate the **whole** set from the one enum/type that defines it and
  add a test that fails when a member is added with no rule — a pinned handled-subset proves
  non-regression, not completeness (`method.md`). A one-sided special-case (`return 1` with no
  mirrored `return -1`) also breaks antisymmetry. The cross-version sibling of the same completeness
  question — a consumer's exhaustive-`switch` outgrown by a **producer's** newly-added enum member —
  is the added-enum-member breaking-change note in `api-contracts.md`.
- `new Date('2026-03-14')` / `Date.parse` on a **date-only** string → **UTC** midnight, while a
  `'…T00:00:00'` (time, no offset) → **local** midnight (MDN) → a viewer behind UTC renders a bare
  day a **day early**; non-ISO/slash forms are unportable. Mechanism + fix in
  `time-date-correctness.md`.
- `Math.random()` for tokens/ids → use `crypto.randomBytes`/`randomUUID`.
- `any`, `as any`, `@ts-ignore`, `!` non-null assertions → type holes; `TS` set
  to non-`strict`.
- Floating promises (missing `await`), `.catch` absent, `async` in `forEach`
  (does not await) → dropped errors / races.
- `addEventListener` / `.on(` / `.subscribe(` / `setInterval` / `setTimeout` with no matching
  `removeEventListener` / `.off(` / `unsubscribe` / `clearInterval` / `clearTimeout` on
  unmount / request-end / disposal → listener + timer leaks (a `useEffect` with no cleanup return
  is the React form; see the subscription-lifetime rule in `concurrency-shared-state.md`).
- `process.env.X` read at module load without validation → silent misconfig.
- Secrets or API keys referenced in client/bundle code → shipped to the browser.
- **A component/module with *no* `"use client"` directive does not thereby "render
  once per request on the server" — render *location* (and so render *frequency*)
  follows **who imports it**, not the file's own contents.** In a server/client-split
  framework (React Server Components / the Next.js App Router), a directive-less module
  is *shared*: imported by a Server Component it runs on the server (once per request);
  imported and rendered by a **Client Component** it is pulled into the **client
  bundle**, runs in the browser, and re-executes on **every** client render. A "runs
  exactly once on the server" assumption baked into it then breaks silently the instant a
  client caller imports it — a module-load singleton now re-initializes in each client
  that loads the bundle (its value exposed client-side, no longer one-per-request); a
  one-time side effect in the render path fires on every client render; an id / nonce /
  timestamp "generated once" varies per client; a **server-only secret / env var** read
  at module scope ships to the browser. It passes typecheck, lint, and unit tests (which
  import the module in a plain Node context where it *does* run once), so only a real
  client-side render exposes it. **Fix:** never infer render-frequency from file
  content — enforce the boundary. Add a build-time `server-only` import to any module
  that must never reach the client (it **fails the build** if a client module pulls it
  in), keep once-per-request state in a request-scoped server construct rather than
  module scope, and verify the real import graph, not the directive. Distinct from the
  plain-value-**proxied**-across-the-boundary defect (`frontend-a11y.md` § "Server/client
  boundary — a plain value proxied across it") — that is a **client** value turned into a
  client-reference **proxy** when a **server** component imports it; this is the opposite
  direction, a **directive-less** module pulled **into the client** and re-run, breaking a
  render-once / server-only assumption.
- **A client "tab shell" handed already-built Server-Component section bodies as props gates
  only *display*, not *execution* — every section has already run its server-side reads and
  shipped, whichever tab is active.** A common App-Router shape: a **Server Component** parent
  builds N sections — each itself a Server Component doing real data reads/joins — and passes
  them to a **Client Component** tab switcher as an array of `{ id, node }`, where `node` is
  the **already-rendered** `ReactNode`. The client's `activeTab` state then chooses which
  `node` to show (conditional render, or CSS `hidden`). But by the time that state exists,
  **all N section bodies have already executed on the server** — every read, every join, for
  every tab — and their output (plus any data serialized into the RSC payload) has already
  been sent to the client. The active-tab state only reveals a pre-computed node; it cannot
  un-run the work. Consequences: **wasted server work** (N sections fetched to show one),
  repeated **over-fetch / cost** on every request, and a **leak** — data for tabs the user
  never opens (an admin-only panel, another user's detail, a not-yet-entitled section) is
  computed and **serialized into the payload the browser receives**, readable in the network
  response regardless of the CSS that hides it. It passes typecheck and unit tests (each
  section renders correctly in isolation) and looks right in the browser (only the active tab
  shows), so only reading the RSC payload or the server query log exposes it. **Fix — gate
  the *work*, not the *display*:** make an inactive section's body **not run** until it is
  chosen. Give each tab its **own route/segment** (`/dashboard/overview`, `/dashboard/billing`)
  so navigation, not a client boolean, triggers the read; or defer the body behind a boundary
  that only renders on activation (a lazily-loaded segment that fetches on mount, a route
  handler the tab calls when selected). Pass the **inputs** a tab needs (an id, a query key)
  to something that fetches on demand — never the pre-built node of an unopened tab. Verify by
  reading the RSC/network payload of a freshly-loaded page and confirming an unopened tab's
  data is **absent**, and that the server query log shows only the active tab's reads.
  **Discriminator vs the directive-less-module bullet above:** that one is about *where and
  how often a single module runs* — a directive-less module pulled into a **client** import
  re-executes in the browser every render and can leak a module-scope secret; this one is
  about **eagerly-built server children that ran correctly, once, on the server, but cannot be
  un-run by a client display gate**. There the fix enforces the boundary so the module never
  reaches the client; here the boundary is fine (the sections are legitimately server-side) and
  the fix is to **defer execution** so an inactive tab's reads never fire. Passing an
  already-executed server node to a client switcher is exactly what makes "which tab is active"
  unable to prevent the other tabs' work.
