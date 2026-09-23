# Frontend reliability & performance — re-render cost and client-bundle weight

Read this when the target or diff renders a list or grid of rows / tiles, adds or removes `React.memo` / `useMemo` / `useCallback`, passes props to a lazily mounted container (tabs, a conditional panel, a virtualized region), imports a heavy optional library (editor, chart, PDF, highlighter), imports a helper from a module holding a large static dataset, or imports through a barrel / `index` re-export. Split from `frontend-a11y.md`, whose Core Web Vitals thresholds and base performance checklist apply to every UI review.

## Reliability & performance — re-render cost and bundle weight

- **A memoized callback needs a memoized recipient — stable props alone don't stop re-renders.** In a
  list/queue rendering N rows via `.map()`, if the parent holds shared per-row state (a selection set, per-row
  drafts, a filter) that changes on ordinary actions, React re-invokes and reconciles **every mounted row** on
  each parent state change — even rows whose own props are unchanged — unless the row is wrapped in
  `React.memo`. `useCallback`/`useMemo` keeping props referentially stable is **necessary but not
  sufficient**: a stable callback passed to a *non-memoized* child still triggers a full re-render (React
  calls the child to get its new element tree regardless). Windowing/pagination bounds how many rows *mount*,
  not the re-render cost of the mounted ones. The tell is subtle — the stable-callback code looks "already
  optimized" (often with comments about avoiding prop churn), so a reviewer stops one level too low. Fix: wrap
  the row in `React.memo` (low-risk/high-payoff precisely *because* the props are already stable — say so, it
  defeats the "will memo even help?" objection); acceptance = a render-count check: one row's action
  re-renders that row only, not the visible set.
- **An unmemoized view-model still recomputes on a sibling's keystrokes — debouncing the fetch doesn't gate
  the recompute.** A tab/view's per-row or per-tile view-model (joining sources, mapping/filtering a
  time-series per row, deriving flags) built directly in the render body instead of behind `useMemo`/a
  selector returns a brand-new array/object on **every** re-render of its parent, not only when its own inputs
  change — so even a row/tile already wrapped in `React.memo` (the bullet above) can't bail out against it:
  memo compares the incoming reference, and this one is never stable. The usual trigger: an always-mounted
  search/filter input sets synchronous "echo" state in the shared parent on every keystroke (a good pattern by
  itself — it's what makes typing feel instant) while only the **debounced** value later reaches the actual
  fetch/filter. That harmless-looking synchronous `setState` still re-renders the shared parent and rebuilds
  the view-model from scratch — the debounce gated the **network call**, not the **work** — so every row/tile,
  and any real chart it owns, redoes its render work on every keystroke instead of only when the debounced
  value actually changes. It hides in plain sight: a tab panel that unmounts while inactive confines the cost
  to whichever tab happens to be open (trace what *else* changes state while that tab is mounted), and a
  neighboring derived value in the same component is often correctly memoized already — keep scanning past the
  first `useMemo` you find; a component can memoize one derived value and skip a costlier one two lines below.
  Detect: confirm the view-model has no memoization keyed on its real upstream inputs (not on the un-debounced
  echo state); gate the finding on real cost (tens-to-low-hundreds of rows/tiles doing non-trivial per-row
  work — a real chart, not a static text cell). Fix: memoize the view-model on its real upstream inputs, then
  apply the row-level `React.memo` from the bullet above so the now-stable reference actually pays off — and
  reject a debounce-only patch: "add a debounce to the search input" doesn't fix this when a debounce already
  gates the fetch and the recompute still fires underneath it; the missing piece is the memo boundary, not
  more delay. Same render-count acceptance as above, run on a keystroke in the *unrelated* input: zero
  re-renders in the view while typing. Distinct from the byte-weight CWV budget in `frontend-a11y.md` (payload size, not
  recompute cost); from the memoized-callback bullet above, which owns the row-level `React.memo` boundary
  triggered by *per-row* shared state such as a selection set, while this owns the derivation going
  unmemoized, the debounce-echo trigger from a *totally unrelated* sibling, and the realistic-cost gate; and
  from the dataset-leak bullet below (a client-bundle **size** leak, not render churn).
- **A correct child memo is silently defeated by an inline collection literal at the call site.** Kin to the
  unmemoized-view-model bullet above, but nothing here flags it: the child *is* memoized correctly — its
  expensive derivation (build a tree, join lists) sits behind `useMemo`/`React.memo` keyed on exactly the
  right prop — but the parent passes that prop as a literal built **inline in JSX**, e.g. `<Child
  matchIds={new Set(items.map(x => x.id))} />` (also a spread `[...]`, `new Map(`, or an object literal
  `{…}`). The literal gets a **brand-new identity on every parent render**, including renders driven by
  something unrelated to its contents (a sibling input's un-debounced keystroke echo, a hover toggle, a
  re-render cascade); memo compares deps by reference, so a same-contents-new-identity value looks like a real
  change — the child's memo invalidates and the expensive work reruns every render. Each file reads clean
  alone: textbook child memo, unremarkable parent one-liner. Detect: grep call sites for a prop whose value is
  an inline `new Set(`/`new Map(`/`[...`/`{…}` **not** itself from a `useMemo`/stable state, confirm the
  receiving component keys a memo/effect dependency on it, then verify by counting the child's recompute while
  triggering an *unrelated* parent state change. Fix: hoist the literal into the parent's `useMemo` keyed on
  its true upstream (`const ids = useMemo(() => new Set(items.map(x => x.id)), [items])`) and pass the stable
  reference down. Distinct from the two bullets above by *what is unstable and whether anything flags it*: the
  memoized-callback bullet has **no `React.memo` on the child at all**; the unmemoized-view-model bullet has
  an unstable **named derivation** a reviewer can see and memoize; here the child's memo is **already correct
  and correctly keyed** and the unstable value is a **bare inline literal** with no named derivation to notice
  — the only fix is stabilizing the literal's identity, never adding memoization the child already has.
- **A lazily-mounted container can't reach backwards into its props — an eagerly-evaluated expensive prop runs
  for every panel, including the ones never shown.** A container that mounts children conditionally — a `Tabs`
  rendering only the active panel, a `{isOpen && <Panel/>}`, a virtualized/windowed region — skips the
  *render* of branches it doesn't show, but **not the evaluation of the props it was handed**: a prop
  expression is an ordinary function argument, so the parent computes it **before** the element tree reaches
  the container deciding what to mount. Hand such a container an array of pre-built panels — `<Tabs
  panels={[{label, content: renderHeavyChart(a)}, {content: renderHeavyChart(b)}, …]} />`, `<Modal
  body={buildBigTree(data)} />`, `<Panel rows={expensiveTransform(rows)} />` — and every chart/tree/transform
  computes up front even though only one panel is ever opened; mount-only-the-active-child saves nothing.
  **The discriminator is call-vs-descriptor:** a bare JSX *element* in prop position (`content: <HeavyChart
  data={raw}/>`) is a cheap `createElement` descriptor — nothing heavy runs until the container mounts it,
  **not** this bug; the bug is a **function call** evaluated in prop position (`content:
  renderHeavyChart(raw)`) or an element whose **inner prop is computed on the spot** (`<HeavyChart
  rows={buildSeries(raw)} />` — the element is cheap but `buildSeries` runs now). Flag the call/allocation,
  not every element passed as a prop, and gate on real dataset scale and a real, frequent trigger —
  over-flagging a correct-looking shape at small *n* erodes trust in the finding. **Memoization does not fix
  this — reaching for it is the tell the axis was misread:** `useMemo(() => renderHeavyChart(raw), [raw])`
  still executes for **all** N panels on first render — a memo caches a value across *re-renders*, never skips
  the *never-opened* branch. The lever is *when* the work is invoked, not *how often* it recomputes. Fix: move
  the work to the point of mount so the container runs it only for the panel it actually shows — pass a thunk
  / render-prop / `children` / a component reference the container invokes on mount (`content: () =>
  renderHeavyChart(raw)` rendered as `tabs[active].content()`), or hand the panel its raw inputs and let the
  mounted component derive its own. Detect: an expensive call or allocation written as a prop value to a
  component that conditionally/lazily renders that prop; confirm by counting the expensive work's invocations
  while opening panels — acceptance is the count equalling panels actually **opened** (a never-opened tab =
  zero, a first-time switch = exactly one), not the number defined. Distinct from the three memoization
  bullets above by *axis*: those are re-render cost — a child lacks `React.memo`, a view-model is unmemoized,
  or an inline literal is referentially unstable, all cured by memoization; here the container's laziness is
  real and the prop may be perfectly stable, yet the work still runs for branches that never mount, so only
  relocating the invocation helps. Distinct too from the heavy-optional-library bullet below: that's a
  **bytes** leak — a statically imported lib shipped to routes that never open the gate, cured by deferring
  the **import**; this is a **CPU/allocation** cost executed at render for unseen branches, cured by
  relocating the **invocation**.
- **A heavy optional-feature library must be gated at the *import*, not just the render.** A rich-text editor,
  chart/diagram lib, PDF/export, or syntax highlighter rendering only behind an interaction gate
  (`open`/`editing`/`expanded`) but **statically imported at module scope** by an always-mounted list/row/card
  component ships in the bundle of **every route** transitively importing that component — so most visitors
  who never trigger the gate still download/parse/compile it (illustratively ~130 KB gzip on the
  highest-traffic routes). It *looks* optimized since the heavy child renders conditionally — but the gate
  that matters for bundle weight is the **import**, not the render. Detect: grep each heavy/optional
  dependency's importers; flag any imported statically from a component mounted on a list/index route where
  the heavy part renders only behind interaction. Fix: defer it (`next/dynamic` / `React.lazy` / an inline
  `import()`) behind the same gate the render already uses. Strong tell: the codebase already defers a
  *different* heavy dep correctly — name that precedent to make the fix trivially arguable.
- **A shared data-access module can leak an entire static dataset into a client bundle through one "harmless"
  helper import.** A module holding a frontend's full compiled/static dataset (a large JSON import) alongside
  small lookup helpers (`getThing(id)`, `labelFor(key)`) ships the **whole dataset** to any client component
  importing even one helper, whenever the module builds its exports by processing the entire dataset at load
  time (spreading it into a derived singleton the helpers close over) — a bundler can't tree-shake around a
  singleton built from the whole input, so importing one small function drags the rest along. It looks safe:
  the helper's signature gives no hint of size, and `import type { Thing } from './data'` really is erased at
  compile time — training a reviewer to assume any import from that module is free, when a *value* import of a
  sibling helper is not. Nothing fails — no test, typecheck, or lint rule catches it; it shows up only as a
  bigger bundle-analyzer entry or a "this page feels slow" report, rarely traced to the import line. Detect by
  walking each client entry point's **runtime** import graph (stripping type-only imports first) for an edge
  into the big-dataset module, then confirming a suspect route's bundle size before/after removing the import.
  Fix by resolving the lookup server-side and passing only the small resolved value down as a prop, or
  refactoring the helper to a structural-parameter form (`getX(id, allThings)`) living in a dataset-free
  module, so a caller supplies its own narrow slice; add a standing import-graph test so a **new** client
  component reaching the dataset fails CI instead of shipping silently. Distinct from the
  heavy-optional-library bullet above — that library is needed only behind an interaction gate and the fix is
  deferring the *import*; a data-lookup helper is typically needed unconditionally at its call site (e.g.
  rendered on first paint), so deferral alone doesn't remove the cost and the fix is architectural instead.
  Also distinct from the Server/client boundary proxy in `frontend-a11y.md`: that's a **Server** Component reading a
  **client**-marked export and getting an inert stub (a functional bug); this is a **Client** Component
  reaching a large payload through an unmarked shared module (a bundle-size bug) — boundary direction and
  failure mode both reversed.
- **A barrel re-export, or a pure export co-located with a heavy import, ships that heavy code even when the
  imported symbol never touches it.** Kin to the dataset-leak bullet above, but the tree-shaking failure comes
  from the **file/module boundary itself**, not the helper depending on the data. Two shapes: (a) a *barrel* —
  an `index.ts` re-exporting many sibling modules — where `import { x } from '../shared'` drags the top-level
  side-effecting imports of *every* re-exported sibling (a chart lib, a compiled JSON, an analytics client)
  into the chunk, since the bundler resolves the barrel as one module; (b) a single module that
  side-effect-imports a large blob (`import DATA from './compiled.json'`) at its top level *and* exports
  genuinely pure, blob-independent values — a static label map, a bare string constant, a pure formatter —
  where importing one of those pure symbols still pulls the whole file, blob included. The reason is
  **module-level granularity**: a bundler drops unused *modules*, not unused *properties of a module it must
  keep*, so any live (value, not `import type`) binding taken from the module keeps the entire file —
  *conservatively* unless the first-party package/module is marked `"sideEffects": false`, the flag letting
  the bundler prove the unused parts are safe to drop. This is exactly where the "bundle split and
  tree-shaken" checklist item in `frontend-a11y.md` reads green but is silently false. **Partial credit does not exist here.**
  Once the symbol that reads the blob is moved server-side and its resolved value prop-threaded (the
  dataset-leak bullet's fix), it's tempting to call the file clear — but if the same client component, or any
  sibling in the route's client graph, still imports even one pure constant from that blob-backed module (or
  via the same barrel), the module is still reachable and pulled in whole, so the saving is zero: either
  *every* runtime import into the client graph is gone or the full blob ships. Detect by walking each client
  entry point's **transitive** runtime import graph (strip `import type` first — a component can ship the blob
  by rendering a child that imports it, without naming it itself) for any edge into the blob-backed module or
  the barrel; for each edge, read the *actual definition* of the imported symbol in that module's source — a
  pure literal, or a value reading the parsed blob? — never infer it from a comment or the import line.
  Confirm in the bundler's analyzer: does the produced chunk carry a byte-size outlier or a string fragment
  that could only be there if the blob is embedded? A "this file imports only pure things" review is not proof
  until the built artifact is checked. Fix: import the **specific submodule path** (`../shared/labels`)
  instead of the barrel; **split** the blob-backed module so the pure exports live in a sibling importing the
  blob *nowhere* in its own file or its transitive imports, and have the blob-backed module re-export them
  from that free sibling (single source of truth kept for its legitimate server callers) while every client
  importer points at the free module; mark a genuinely side-effect-free package `"sideEffects": false`; and
  keep large static data out of any module that also exports hot small utilities. Guard it with a
  **source-level reachability check** — a small import-graph walk (not a runtime bundle-size assertion, which
  may be unavailable where tests run) that fails when any client-side module reaches the blob-backed module —
  run as a *shrink-only allowlist* so new offenders fail loudly while known ones stay visible debt. That check
  is necessary but **not sufficient alone**: its module/symbol list goes stale, so acceptance pairs it with
  the built-artifact check above. Distinct from the dataset-leak bullet above by **whether the imported symbol
  depends on the blob**: there the helper closes over a singleton derived from the whole dataset, so the data
  is a genuine dependency and the fix is architectural (structural-parameter form); here the imported symbol
  is genuinely independent and only the file boundary or barrel edge binds them, so a mechanical split /
  submodule-path import / `sideEffects` flag severs it outright. Distinct from the heavy-optional-library
  bullet above too: that library is needed only behind an interaction gate and deferring the *import* fixes
  it; here the pure symbol is typically needed unconditionally (first paint), so deferral alone leaves the
  blob riding in beside it — the blob must be severed from the pure export, not lazy-loaded with it.
