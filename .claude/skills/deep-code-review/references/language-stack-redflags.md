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

## Per-language red flags — load only the languages present

Each language family has its own file. Load the file for every language the target contains (Phase 0 detects them) and skip the rest:

| Language(s) present | Load |
|---|---|
| Python | `lang-python.md` |
| JavaScript / TypeScript | `lang-js-ts.md` |
| Go | `lang-go.md` |
| Java / Kotlin | `lang-jvm.md` |
| Ruby, PHP | `lang-ruby-php.md` |
| C / C++, Rust | `lang-c-cpp-rust.md` |
| Shell — any shell run by CI (`run:`), hooks, Dockerfile `RUN`, Makefile recipes, or scripts | `lang-shell.md` |
| SQL — any SQL string, ORM query, or migration | `lang-sql.md` |

The cross-language sections below (switch/case, delimiter scanning, composed numeric bounds, partition gates, denial of service, the reviewer's own verification shell) apply to every review.

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
  is switch/case control flow, not the `||`-falsy-skip "fall through" in `lang-js-ts.md`'s
  JavaScript section — that's operand short-circuiting, unrelated to case labels.)
- **Code after an unconditional `return`/`throw`/`break`/`continue` is unreachable** —
  almost always a logic error, not harmless dead code: a guard clause that stopped
  guarding after a refactor, or a merge artifact that pasted a stale block past the exit
  meant to precede it. ESLint's `no-unreachable` ("Disallow unreachable code after
  `return`, `throw`, `continue`, and `break` statements") and CodeQL's
  `js/unreachable-statement` (CWE-561) both flag it; CodeQL's rationale: "An unreachable
  statement almost always indicates missing code or a latent bug and should be examined
  carefully." Distinct from the unreferenced-code item in `domain-h.md` —
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
  (`security-api.md` clamps a requested size to a hard maximum — one bound, no floor for it to
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
  in `security-api.md` — that's request-*multiplication* (more fields/operations
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
  through that same cap to reach. Distinct too from `security-api.md`'s API10
  "bound size and recursion" clause — that's the app **consuming an upstream
  response** (outbound/client direction); this bullet is the **inbound** direction,
  a public endpoint parsing an attacker-supplied request body. Distinct, too, from
  the generic "max depth" cost-cap in `performance-db-cost.md` (an efficiency bound,
  not a stack-crash defense) and from `security-api.md`'s GraphQL query-depth
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
  `security-api.md` — both bound bytes actually *transferred*/received, not a
  size *claimed inside* a payload before those bytes arrive. Distinct too from the
  C/C++ "integer overflow before `malloc`" bullet in `lang-c-cpp-rust.md` — that's an *undersized*
  allocation from an overflowed calculation, leading to a buffer overflow (memory
  corruption); this is an *oversized* allocation from a value trusted as-is,
  leading to memory exhaustion (availability) — different consequence, different
  fix. Clamp the declared size to a sane ceiling before allocating, or allocate
  incrementally as bytes actually arrive.

## Shell / Bash

Reviewed-code shell footguns (unquoted expansions, `set -u` on empty arrays, locale-dependent bracket ranges) live in `lang-shell.md` — load it per the Shell row of the table above.

### The reviewer's own verification shell (measuring, not reviewing)

`lang-shell.md` hunts `pipefail` in *reviewed* code; these hazards apply to the
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
