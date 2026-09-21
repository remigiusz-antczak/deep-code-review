# Language & stack red flags — grep-able footguns

Read this to turn the abstract checks in `SKILL.md` into concrete patterns you
can grep for in the target's language(s). These are **signals, not verdicts**:
each hit needs the surrounding context read before it becomes a finding. Tune
paths to the repo; exclude vendored/`node_modules`/generated code.

A fast first pass across any repo:

```bash
# secrets in tree or history (install gitleaks/trufflehog if available)
gitleaks detect --no-banner 2>/dev/null || grep -rInE \
  'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' .
# leftover debug + markers
grep -rInE 'TODO|FIXME|HACK|XXX|@ts-ignore|eslint-disable|type: ignore|nolint' .
grep -rInE 'console\.log|print\(|dbg!|System\.out\.print|fmt\.Print' .
```

---

## Python

- `eval(`, `exec(`, `compile(` on any input → code injection.
- `pickle.loads`, `yaml.load(` (without `SafeLoader`), `marshal`,
  `jsonpickle` on untrusted data → deserialization RCE.
- `subprocess.*(… shell=True)`, `os.system(`, `os.popen(` with a built string →
  command injection. Use an argument list and `shell=False`.
- `requests.*(… verify=False)`, `ssl._create_unverified_context` → TLS bypass.
- String-built SQL: `cursor.execute("… %s" % x)`, f-strings in queries. Use
  bound params (`execute(sql, (x,))`).
- `assert` for validation → stripped under `python -O`; use explicit checks.
- Mutable default args (`def f(x, acc=[])`) → shared state across calls.
- `except:` / `except Exception: pass` → swallowed errors.
- `random.random()`/`random.choice` for tokens → not a CSPRNG; use `secrets`.
- `tempfile.mktemp`, predictable temp paths → TOCTOU.
- `datetime.now()`/`utcnow()` without tz → naive datetimes; use tz-aware UTC.
- `float` for money → use `decimal.Decimal`.
- `a or b or default` over decoded JSON/config → a legitimately-present **falsy** value
  (`0`, `False`, `""`, `[]`, `{}`) is skipped for the next fallback. Resolve by presence, not
  truthiness (`x if x is not None else default`; `d[k] if k in d else default`), and test with
  `0`/`False`/`""`/`[]` present.

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
  from the attacker-chosen-key comparator DoS below — that is worst-case *complexity*; this is a
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

## Go

- Ignored errors: `_ =` on a call that returns `error`, or no `if err != nil`.
- String-built SQL vs `db.Query(q, args...)`; `fmt.Sprintf` into a query.
- `exec.Command("sh", "-c", built)` → command injection.
- Goroutine leaks: a goroutine with no cancellation/`context`; `defer` inside a
  loop accumulating until function return.
- `math/rand` for security (use `crypto/rand`); missing `rows.Close()`;
  data races (run with `-race`; a flag/state shared across goroutines needs
  `sync/atomic` or a channel, not a plain field read); `panic` used for normal
  control flow.
- **Loop-variable capture in a closure/goroutine (pre-Go-1.22 semantics).** `for _, x := range xs { go func(){ use(x) }() }` shares **one** `x` across all iterations before Go 1.22, so the goroutines mostly see the last value. Go 1.22 gives each iteration a fresh variable — but the change follows the **module's declared `go` version in `go.mod`**, not the installed toolchain, so a vendored/legacy `go 1.20` module keeps the bug even built by a 1.22+ compiler. Check the `go.mod` directive, not `go version`; or capture explicitly (`x := x` / a param), which is correct under every version.
- **Channel-close discipline.** Sending on or closing a **closed** channel, and closing a **nil** channel, are **run-time panics**, not no-ops — two fan-in producers each `defer close(ch)` panics the second close. One owner closes; use `sync.Once` or a done-channel when ownership is shared.
- **Concurrent map access is a fatal crash, not a stale read.** An unsynchronized map write concurrent with any other access **can** be runtime-detected and abort the process (`fatal error: concurrent map writes`) even without `-race` — but the check is **best-effort** (the Go FAQ says it *can* crash), so a clean run is **not** proof of no concurrent access; an access the detector misses can still silently corrupt (the torn-value case in `concurrency-shared-state.md`). Guard with a mutex or use `sync.Map`.

## Java / Kotlin

- `ObjectInputStream.readObject` on untrusted bytes → deserialization RCE.
- XXE: `DocumentBuilderFactory`/`SAXParser` without disabling external entities.
- `Runtime.exec`/`ProcessBuilder` with a concatenated string.
- String-built JPQL/SQL vs `PreparedStatement`/bound params.
- `Random` for tokens (use `SecureRandom`); swallowed `catch (Exception e) {}`;
  `printStackTrace()` to the response; broad `@SuppressWarnings`; a field shared across
  threads read without `volatile` / `synchronized` / an `AtomicX` (double-checked
  locking with a non-`volatile` instance field is broken).
- **A mutable field used in `equals()`/`hashCode()` corrupts hash-key lookups.** Mutating a field that participates in `hashCode()` **after** the object is put in a `HashMap`/`HashSet` leaves it physically in the *old* bucket; a later `get`/`contains` computes the *new* hash, looks in a different bucket, and returns **not-found** with no exception (iteration/`remove` corrupt likewise). A hash-key must be effectively immutable over its `hashCode` fields while in the collection; and every field used in `hashCode()` must also be in `equals()` — a `hashCode()` that includes a field `equals()` ignores breaks the contract directly (two equal objects then hash differently); excluding an `equals()`-only field from `hashCode()` merely costs bucket distribution (Bloch). Classic trigger: a JPA `@Entity` or Lombok `@EqualsAndHashCode` over a mutable id/status.

## Ruby

- `eval`, `instance_eval`, `send`/`public_send` with user input, `constantize`.
- `YAML.load` (use `safe_load`), `Marshal.load` on untrusted data.
- String-built SQL vs parameterized (`where("x = ?", v)`); `system`/backticks
  with input; mass assignment without strong params.

## PHP

- `eval`, `assert` on input, `include`/`require` from a request var (LFI/RFI),
  `unserialize` on untrusted data, `extract($_REQUEST)`, `==` vs `===`,
  `$wpdb->query` with a built string, `shell_exec`/`system`/backticks.

## C / C++

- `strcpy`, `strcat`, `sprintf`, `gets`, `scanf("%s")` → buffer overflow; use
  bounded variants. Integer overflow before `malloc`; use-after-free / double
  free; `memcpy` with an unchecked length; format-string bugs (`printf(user)`).
- Run with ASan/UBSan (these map to top CWEs 787/416/125 — plus the classic/stack/heap
  buffer-overflow family, 120/121/122) — and **ThreadSanitizer**
  (`-fsanitize=thread`) for data races, which ASan/UBSan do **not** catch; state shared
  across threads needs `std::atomic` / an explicit `std::memory_order`, not a plain access.

## Rust

- **`unsafe` is a proof obligation, not an escape hatch — review each block for the invariant it asserts.** `std::mem::transmute` reinterprets bytes at a new type with **no validation**: transmuting to an enum value that isn't a declared discriminant, or to a `bool`/`char` outside its valid bit-patterns, is **immediate undefined behaviour**, not a wrong-but-defined value (the std docs flag transmute as a last resort). Prefer a checked conversion (`TryFrom`, `match`, `from_bits`).
- **`unsafe impl Send`/`Sync` silences the compiler's thread-safety check; it does not prove the property.** Wrapping a raw pointer / FFI handle to cross threads (`unsafe impl Send for Handle {}`) asserts a guarantee the compiler can no longer verify — if the pointee isn't actually safe to move/share (thread-affinity, interior aliasing), it is **silent UB with no backstop**, and "it compiles + tests pass" is not evidence (a normal run doesn't exercise UB). The Rustonomicon marks `Send`/`Sync` unsafe to implement for exactly this reason. Require a written safety argument per `unsafe impl` and confirm it holds.
- **Other `unsafe` tells:** a raw-pointer deref with unproven provenance/lifetime; `get_unchecked` / `unwrap_unchecked` without a checked invariant; `slice::from_raw_parts` with an unvalidated length; `MaybeUninit::assume_init` before full initialization. **Verify with `cargo miri`** (and ASan/TSan on the C/C++ side of any FFI boundary), or mark the block `unverified` (`method.md`) — the normal test suite does not exercise UB.

## Switch/case control flow & unreachable code

A linter or compiler catches every pattern in this section on its first run — ESLint,
`go vet`, a C/C++ `-Wswitch`/`-Wimplicit-fallthrough` build flag, a Rust
`#[deny(unreachable_code)]` — which is exactly why a general review skips it. It survives
in an **AI-authored diff** (a model pattern-matches "add a `break`" without checking which
language it's in — see below), a **lint-exempted line** (`eslint-disable`, a suppressed
compiler warning), or **a language/toolchain the target's CI doesn't lint at all** (a
secondary service off the main gate). A hit in any of those three contexts is
higher-confidence, not lower.

- **Switch/case fallthrough is a cross-language reversal, not a universal rule — "add a
  `break`" is right in one family, a compiler error to even need in another, a no-op in a
  third, and meaningless in a fourth.** C, C++, and JavaScript/TypeScript — plus Java's
  classic colon-`case X:` form — fall through by default: omitting `break`/`return`/
  `throw` silently runs execution into the next case. ESLint's `no-fallthrough`
  ("Disallow fallthrough of case statements") flags any such case; the sanctioned
  intentional-fallthrough marker there is a comment matching `/falls?\s?through/i`
  (provided it isn't itself an ESLint directive comment), and C++17 gives the language
  itself a marker via the `[[fallthrough]];` statement attribute ("May only be applied to
  a null statement to create a fallthrough statement," cppreference) — don't assume
  either marker is recognized outside the tool/standard that defines it. **Go** is the
  reverse default: every case implicitly stops, and falling through requires the explicit
  `fallthrough` keyword as the case's last statement — the Go spec: "the last non-empty
  statement may be a … `fallthrough` statement to indicate that control should flow from
  the end of this clause to the first statement of the next clause. Otherwise control
  flows to the end of the `switch` statement." **Swift** shares Go's no-fallthrough
  default — "In Swift, `switch` statements don't fall through the bottom of each case and
  into the next one" — and, unrelated as the two languages are, spells its opt-in keyword
  identically: "you can opt in to this behavior on a case-by-case basis with the
  `fallthrough` keyword" (Apple's Swift Programming Language guide). **C# looks like the
  C family** — colon-`case`, braces, a trailing `break` — but the compiler rejects
  implicit fallthrough outright: "Within a switch statement, control can't fall through
  from one switch section to the next," and "Every switch section must end with a break,
  goto, or return. Falling through from one switch section to the next generates a
  compiler error" (Microsoft's C# reference). A missing `break` in C# cannot ship;
  deliberately reusing another section's logic takes an explicit `goto case` to a
  constant case label ("you can also use the goto statement in the switch statement to
  transfer control to a switch section with a constant case label," Microsoft's C#
  jump-statements reference) — C#'s differently-spelled answer to `fallthrough`. **Rust's
  `match`** has no fallthrough mechanism to opt into at all: "The first arm with a
  matching pattern is chosen as the branch target of the match … and control enters the
  block" (The Rust Reference) — exactly one arm ever runs. Even inside Java, the modern
  arrow form (`case L ->`, Java 14+) switched sides: Oracle's docs confirm arrow labels
  "eliminate the need for break statements to prevent fall through" — only the classic
  colon form keeps Java's C-style default. Confirm both the language **and** the switch
  syntax before treating a missing terminator as a bug, or its presence as a no-op. (This
  is switch/case control flow, not the `||`-falsy-skip "fall through" in this file's
  JavaScript section above — that's operand short-circuiting, unrelated to case labels.)
- **Code after an unconditional `return`/`throw`/`break`/`continue` is unreachable** —
  almost always a logic error, not harmless dead code: a guard clause that stopped
  guarding after a refactor, or a merge artifact that pasted a stale block past the exit
  meant to precede it. ESLint's `no-unreachable` ("Disallow unreachable code after
  `return`, `throw`, `continue`, and `break` statements") and CodeQL's
  `js/unreachable-statement` (CWE-561) both flag it; CodeQL's rationale: "An unreachable
  statement almost always indicates missing code or a latent bug and should be examined
  carefully." Distinct from the unreferenced-code item in `domain-checklists.md` §H —
  that's a live, reachable function/import nobody calls; this is a dead *branch* inside a
  function that **is** called, where one path through it never runs.
- **A `let`/`const`/`class`/`function` declared inside one `case` without a block is
  visible to every sibling case, not scoped to the case that declares it** — it's
  hoisted (`function`) or sits in the temporal dead zone (`let`/`const`) for every other
  branch of the same `switch`, so a sibling case can read an uninitialized binding or
  collide with it. ESLint's `no-case-declarations` ("Disallow lexical declarations in
  case clauses") is the detector; the fix is to wrap each case body that declares one in
  its own `{ }` block.
- **A duplicate `case` label is a dead second branch, and a plain statement label sitting
  inside a `switch` body reads like a case label but isn't one.** CodeQL's
  `js/duplicate-switch-case` (CWE-561): "if two cases in a switch statement have the same
  label, the second case will never be executed. This most likely indicates a copy-paste
  error" (ESLint's equivalent: `no-duplicate-case`, "Disallow duplicate case labels").
  CodeQL's `js/label-in-switch`: a non-case label mixed into a switch body is "most
  likely the result of a typo" for `case N:`.

Grep lead: a `case` in a C-family file (`.c`/`.cc`/`.cpp`/`.java`/`.js`/`.ts`) with no
`break`/`return`/`throw`/`continue` before the next `case`/`default`/closing `}`; a
non-comment line immediately following a `return`/`throw` at the same indent level. Both
are leads, not verdicts — read the surrounding control flow before recording either as a
finding.

## Hand-rolled parsing & delimiter scanning

- **A "find the terminator" scanner that stops at the *first* line/token equal to the
  delimiter mis-parses when that delimiter can also occur *legitimately as content* before
  the real terminator.** Hand-rolled splitting of a structured header from a body — the
  closing `---` of a YAML/TOML frontmatter fence, an end-of-headers blank line, a `--boundary`
  in a multipart body, a here-doc terminator, a section separator — commonly scans for "the
  first line/token that equals `X`" and treats it as the end. It silently misparses the moment
  `X` can appear *inside* the content it scans over: a `---` on its own line within frontmatter
  (a horizontal rule, a `---` list item, a value that contains it), a blank line inside a
  folded block, a chosen multipart boundary that also occurs in a part's bytes. The scanner
  stops early, splits at the wrong point, and hands both halves downstream **without raising** —
  a truncated header parsed as "complete", body content swallowed into the header (or the
  reverse) — so the corruption surfaces far from the parse. It survives review because the
  happy-path fixture (no `X` in the content) passes; the bug needs content that *contains* the
  delimiter, which fixtures rarely include. Fixes, most robust first: **use a real parser** for
  the format (a YAML / MIME / multipart library) instead of a line scan; if hand-rolling,
  require the **open+close structure** (a frontmatter block must both open *and* close with the
  fence — a lone opening fence is an error, not an empty body), **count** paired fences rather
  than matching the first, pick a multipart boundary **proven absent** from the payload, and
  **raise on the ambiguous/malformed case** rather than returning a best-effort split. Grep
  lead: a `split`/`indexOf`/`find`/`readline` loop comparing a line against a literal delimiter
  (`=== '---'`, `== "---"`, `.startswith('---')`, `line == boundary`) with no bound, no fence
  count, and no error branch. (Distinct from the switch/case "missing terminator" above — that
  is a `break`/`fallthrough` control-flow default; this is a *data*-delimiter scan that ends the
  wrong span.)

## Composed numeric bounds — a floor and a later clamp

- **A min-size floor is silently undone by a *later* boundary clamp that re-bounds the same
  value against room computed from a dependent dimension.** One line enforces a floor —
  `size = Math.max(size, MIN)` ("keep a zero-length item visible", a minimum column width, a
  minimum touch-target) — and a later, independently-correct line bounds the same variable to
  the space that is left — `size = Math.min(size, TRACK_END - position)` (don't overflow the
  track / container / page). Each line is right on its own, but **composed** they violate the
  floor's own invariant: whenever `position` sits within `MIN` of the far edge,
  `TRACK_END - position < MIN`, the `Math.min` wins, and the result drops **below** `MIN`
  (often to `0` or negative) — exactly the state the floor existed to prevent, reachable only
  near a boundary the happy-path test rarely exercises. The two lines are usually far apart (the
  floor in a sizing helper, the clamp in a layout/paint pass), so neither reads as wrong in
  isolation and the item simply "disappears" or collapses near an edge. Fix: **re-assert the
  floor after the clamp** (`size = Math.max(Math.min(size, room), MIN)` — then decide explicitly
  whether the item overflows or the container grows, because you can no longer satisfy both), or
  **clamp `position` first** so `room >= MIN` holds by construction. Grep lead: the same variable
  passed through a `Math.max(…, K)` / `max(…, K)` **and** a later `Math.min(…, expr)` /
  `min(…, expr)` (or `clamp()` calls) where `expr` derives from a position/offset — read whether
  any later bound can fall under the earlier floor. Distinct from a single size-cap clamp
  (`security-appsec.md` clamps a requested size to a hard maximum — one bound, no floor for it to
  undo); the defect here is the **composition** of two individually-correct bounds, not either
  bound alone.

## Partition / segmentation validity gates — the minimal terminal segment

- **A validity gate that checks a partition/segmentation accepts every interior piece but
  rejects a *valid* decomposition whose **last** piece is the minimum allowed size — an
  off-by-one at the terminal (or wraparound) boundary.** A routine that carves a sequence
  or a **ring** (a directed cycle of `N` nodes indexed `0..N-1`, split into sub-cycles by
  "backward chord" edges) into contiguous pieces derives each interior piece's size the
  same way, but the **terminal** piece is computed from *what remains* — a remainder, or a
  wraparound index that must close back onto the start — so its size is a *different*
  expression from the interior ones. A check written and tested against interior pieces
  (`len > MIN`, `end - start > MIN`, `next = i + 1` with no `% N`) then mishandles the
  terminal piece at its smallest legal size: the strict `>` rejects a piece that is
  *exactly* `MIN` (it needed `>=`), or the un-wrapped `i + 1` runs off the end instead of
  returning to `0`. The result is a **false rejection** — a decomposition that is genuinely
  valid is reported invalid (or the routine throws / returns an out-of-range index), the
  mirror of the usual off-by-one that *admits one too many*. It survives because happy-path
  fixtures use uneven pieces where the last one sits comfortably above `MIN`; the boundary
  only bites when the terminal piece lands *at* the floor. **Fix:** make the terminal
  comparison inclusive (`>=` / `<=`, matching the interior pieces' true contract), compute
  every ring index modulo `N`, and assert the **partition invariant** — the piece sizes sum
  to `N` and each piece (the last included) is `>= MIN`. **Test** the degenerate boundaries
  explicitly: `N` and `N - 1`; the **all-minimal** decomposition (every piece exactly `MIN`,
  so the terminal piece is minimal too); and a decomposition whose *only* minimal piece is
  the terminal one. Distinct from the composed-floor-and-clamp defect above — that is two
  individually-correct numeric bounds whose *composition* violates a floor; this is a
  **single** boundary comparator one step too strict at the *terminal / wraparound*
  position, wrongly rejecting a valid input rather than admitting an invalid one.

## SQL / migrations

- String interpolation into SQL (see per-language above).
- `SELECT *` in app code; missing `LIMIT`/pagination; query inside a loop (N+1).
- Migrations: `ALTER`/`CREATE INDEX` without `CONCURRENTLY` on a large table
  (locks writes; Postgres syntax — use the engine's online-DDL equivalent
  elsewhere); adding a `NOT NULL` column with no default; backfill in the same
  transaction as DDL; no rollback path. See `performance-db-cost.md`.

## Denial of service / resource amplification

- **ReDoS** — catastrophic backtracking from nested/overlapping quantifiers
  (`(a+)+`, `(.*)*`, `(\d+)*$`) on untrusted input, or an untrusted string
  compiled into a pattern (`new RegExp(userInput)`, `re.compile(userInput)`).
  Bound input length, prefer a linear-time engine (RE2), or apply a match timeout.
- **Null/nil dereference on a reachable path (CWE-476)** — a value from an external call, an
  optional/nullable lookup, or an unchecked cast that can be `null`/`nil`/`None`/`undefined` is
  dereferenced, called, or indexed **before a null check**, on an attacker- or upstream-reachable
  path: a **crash / DoS**, not merely a wrong-answer bug. Per language: a Go `nil` pointer/interface
  panic, a Java/Kotlin NPE (a `!!` on a nullable), a Python `AttributeError` on `None`, a JS/TS deref
  of `undefined` (a `!` non-null assertion papering over it), a C/C++ deref of a failed
  allocation/lookup return. Guard the unhappy path before the deref; cross-ref
  `reliability-error-handling.md` for the fail-closed + resource-release angle on the same crash.
- **Decompression / entity-expansion bombs** — an archive (`zip`/`gzip`/`tar`)
  extracted with no size or ratio cap, or XML parsed with entity expansion enabled
  (billion-laughs): a small input that inflates to gigabytes. Cap the decompressed
  size and disable external/DTD entity resolution.
- **Algorithmic-complexity / hash-flooding on attacker-chosen keys (CWE-407)** — a
  keyed structure (`dict`/`Map`/`HashMap`/`HashSet`) fed attacker-*chosen* keys, or
  a user-suppliable sort/dedup/group-by comparator (`sorted(data, key=...)`,
  `.sort((a, b) => …)`, a custom `Comparator`/`Comparable` driven by request data),
  degrades from amortized O(1) to O(n) per operation — O(n²) total — when the keys
  are crafted to collide into the same bucket, **even under a normal-looking
  item-count cap**: the count is fine, the *keys* are the attack (CWE-407's own
  observed examples, verbatim: "CPU consumption via inputs that cause many hash
  table collisions."). `performance-db-cost.md`'s count/iteration cap does not
  defend against this. Distinct from the GraphQL query-cost/batching/aliasing item
  in `security-appsec.md` — that's request-*multiplication* (more fields/operations
  than a per-request budget allows); this is worst-case complexity from
  attacker-*chosen values* inside one, already count-bounded request. Verify the
  target's hash-map implementation before prescribing a fix: a randomized hash
  seed/SipHash or a treeified-bucket fallback are known mitigation shapes for this
  class in general, but are **not** stated on the CWE-407 page and may already be
  the runtime's default — don't assert either way without checking.
- **Uncontrolled recursion on nested untrusted input (CWE-674, alternate term
  "Stack Exhaustion")** — a recursive-descent parser (hand-rolled, or a
  JSON/YAML/XML/protobuf library whose depth handling you haven't confirmed)
  walking attacker-supplied nesting (`[[[[[…]]]]]`, deeply nested objects) exhausts
  the call stack on a payload of a few KB (CWE-674's own observed example,
  verbatim: "Deeply nested arrays trigger stack exhaustion."). Distinct from the
  decompression bomb above — that's *byte-size* amplification, caught by an
  output-size cap; this is *call-stack depth*, which a tiny, low-byte payload sails
  through that same cap to reach. Distinct too from `security-appsec.md`'s API10
  "bound size and recursion" clause — that's the app **consuming an upstream
  response** (outbound/client direction); this bullet is the **inbound** direction,
  a public endpoint parsing an attacker-supplied request body. Distinct, too, from
  the generic "max depth" cost-cap in `performance-db-cost.md` (an efficiency bound,
  not a stack-crash defense) and from `security-appsec.md`'s GraphQL query-depth
  limit (which bounds resolver depth over a parsed query AST at the application
  layer, not a raw deserializer's call-stack depth at the syntax layer). Grep the inbound
  parse call itself (`json.loads(`, `JSON.parse(`, `yaml.safe_load(`, an XML
  tree-builder call, `Unmarshal(`, a protobuf `parseFrom`/`ParseFrom`) and check
  whether a max-depth/recursion-limit option is set **on that specific call** —
  don't assume a library's default nesting-depth behavior is either safe or unsafe
  without reading its docs for the version in use. Fix: set or confirm the
  library's max-depth option, or add an explicit fail-closed recursion counter, on
  the inbound-parsing path specifically.
- **Unbounded allocation from a declared/untrusted size value (CWE-789)** — code
  reads a size, count, or dimension *from inside the payload itself* (a JSON
  `"count"` field, an image's declared width×height, a multipart part-count) and
  pre-allocates a buffer/array to that size **before** validating the real bytes
  received, so a tiny request can claim a multi-gigabyte allocation (CWE-789's own
  observed examples: "a large value for number of records to return, leading to
  allocation of a large array"; "memory consumption and daemon exit by specifying a
  large value in a length field"). Grep an allocation call fed straight from a
  parsed field — `malloc(declared_size)`, `new byte[declared_size]`,
  `Buffer.alloc(declared_size)`, `make([]T, declared_len)` — and read backward to
  confirm whether that size traces to an unclamped value inside the payload.
  Distinct from the wire-level upload-size cap and the API10 "bound size" clause in
  `security-appsec.md` — both bound bytes actually *transferred*/received, not a
  size *claimed inside* a payload before those bytes arrive. Distinct too from the
  C/C++ section's "integer overflow before `malloc`" above — that's an *undersized*
  allocation from an overflowed calculation, leading to a buffer overflow (memory
  corruption); this is an *oversized* allocation from a value trusted as-is,
  leading to memory exhaustion (availability) — different consequence, different
  fix. Clamp the declared size to a sane ceiling before allocating, or allocate
  incrementally as bytes actually arrive.

## Shell / Bash

- Unquoted expansions (`rm -rf $DIR`), `eval`, `curl … | bash`, parsing `ls`,
  missing `set -euo pipefail`, secrets in `set -x` traces, world-writable temp.
- `for x in $LIST` as a membership/exclusion check on an **unquoted** variable —
  bash word-splits it, zsh (default) does not, so a safety-critical skip/exclusion
  list silently stops excluding under the wrong shell. Use `case` or a line-based
  `grep -qxF`; full mechanism + the merge-guard instance:
  `branch-and-merge-hygiene.md` §6.
- **`set -u` + `"${arr[@]}"` on an *empty* array is a fatal `unbound variable`
  under bash 3.2 — still macOS's default `/bin/bash` (verified `3.2.57`).** A
  script that conditionally builds an array (flags, a discovered file list,
  cleanup targets) and expands it under `set -u` aborts the instant the array is
  empty; this most often sits in **trap / cleanup / reporting** code on the error
  path, where it **masks the real failure** it was meant to report. Guard the
  expansion (`${arr[@]+"${arr[@]}"}`) or seed the array — and run the script
  against the **actual `/bin/bash` on the target**, since a dev box's
  newer/homebrew bash can behave differently and hide it.
- **A bracket *range* used to VALIDATE a character class — `case $x in *[!0-9a-f]*)`,
  `[[ $x =~ ^[0-9a-f]+$ ]]`, `grep '[0-9a-f]'` — is resolved against the locale's
  collating sequence, not codepoint order, so the *same* script returns a *different*
  verdict under a different `LC_COLLATE`.** POSIX defines a range expression as "the set
  of collating elements that fall between two elements in the collation sequence,
  inclusive" and warns that "in other locales" (than POSIX/C) "a range expression has
  unspecified behavior" (The Open Group Base Specifications, RE Bracket Expression). On
  an implementation that collates in dictionary order under a UTF-8 locale (GNU/glibc:
  `a A b B … z Z`), the uppercase letters sort *inside* `[a-f]`/`[a-z]`, so a guard meant
  to *reject* anything that is not lowercase hex (`*[!0-9a-f]*`) silently *accepts* an
  uppercase digest; under `LC_ALL=C` (byte order) the same guard is strict and rejects
  it. The leniency is a property of the **locale + collation data, not the OS** — a
  C/POSIX locale, or any libc that collates these ASCII ranges by codepoint, is strict,
  so do not key the risk to a platform ("macOS is lenient"); verify the target's
  `LC_ALL`/`LANG`. Consequence: a pre-commit hook that blocks every local commit on one
  developer's box while CI stays green, or the reverse — a lenient local pass a strict CI
  rejects — from a **byte-identical** script run in two locales. **Fix:** pin `LC_ALL=C`
  for the comparison, or drop the range for an explicit enumerated set
  (`*[!0123456789abcdef]*`); a POSIX named class (`[[:xdigit:]]`, `[[:lower:]]`) reads the
  intent but is itself locale-scoped, so a security/gate comparison should still pin
  `LC_ALL=C`. **Grep lead:** a bracket *range* (`[a-f]`, `[0-9a-f]`, `[A-Z]`, `[a-z]`)
  inside a `case` / `[[ =~ ]]` / `grep` used as a validity check with no `LC_ALL=C` in
  scope — read whether the compared value can carry the boundary case (uppercase where
  lowercase is meant). **Discriminator vs the gate-divergence family:** the *drifted local
  gate copy* false-green (`branch-and-merge-hygiene.md` § "Self-reported evidence is not a
  trusted control") is two scripts that **differ** — a stale vendored paste behind the CI
  definition — fixed by *single-sourcing* the logic; here the script is single-sourced and
  **byte-identical**, and single-sourcing does **not** fix it: only pinning `LC_ALL=C` (or
  an explicit set) stops one file being read two ways. Distinct too from the
  changed-files / fetch-by-ref detective control and the extension-allow-list
  under-coverage gate in `reliability-error-handling.md` (which turn on *which* input the
  gate sees, not on how one input is interpreted), and from the application-text collation
  rules in `i18n-l10n.md` (sorting / case-folding *user data* for display — this is
  collation inside a *gate's control flow*).

### The reviewer's own verification shell (measuring, not reviewing)

The rule above hunts `pipefail` in *reviewed* code; these hazards apply to the
commands **you** run to establish ground truth, where an empty or wrong exit is
read as a pass (SKILL.md Phase 1). All measured, not asserted:

- **A pipe hands you the last stage's status.** `gate | tail`/`| head`/`| grep`/
  `| less` report the *reader's* exit, so a failing gate reads `0`. Preference
  order: (1) **capture then echo** — `./gate >/tmp/g.log 2>&1; echo "exit=$?";
  tail -20 /tmp/g.log` (no shell-dialect difference); (2) `set -o pipefail` before
  the pipeline; (3) read the array **on the very next command** — bash
  `${PIPESTATUS[0]}`, zsh `${pipestatus[1]}` (1-indexed, different name) — **any**
  intervening command, including a bare `:` no-op, resets it.
- **SIGPIPE reads as `141`, not the gate's code.** Under `pipefail`, a reader that
  exits early (`… | head -1`) makes the pipeline `141` — looks like a real failure
  and is not the gate's.
- **`grep -q` inverts success.** `grep` exits `0` when it *finds* the string —
  which may be the failure message, so `cmd | grep -q ERROR` "passes" on error.
- **Never `2>/dev/null` in a fact-establishing step.** It converts "the thing does
  not exist" into "the measurement came back clean." A classic trap:
  `git show <ref>:missing.sh >/tmp/x.sh 2>/dev/null; bash /tmp/x.sh; echo $?` —
  `git show` fails (path untracked), the capture is 0 bytes, `bash` on an empty
  file exits `0`, and the absent gate reads as a passing one. Assert non-empty
  output (or a known sentinel) before trusting any exit code.

## Infrastructure as code

Terraform / Kubernetes / Docker / cloud config have their own catalog — see
`infra-iac-containers.md`.

---

**Reminder**: a grep hit is a lead. Read the context, confirm the data flow from
an untrusted source to the dangerous sink, and only then record a finding with
`file:line`, impact, and fix. No fabricated line numbers.
