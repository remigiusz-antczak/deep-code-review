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

## Shell / Bash

- Unquoted expansions (`rm -rf $DIR`), `eval`, `curl … | bash`, parsing `ls`,
  missing `set -euo pipefail`, secrets in `set -x` traces, world-writable temp.
- `for x in $LIST` as a membership/exclusion check on an unquoted variable —
  bash word-splits it (works), zsh by default does not (`x` binds to the whole
  string, the loop body runs once, and a per-item match never fires). A
  safety-critical exclusion (a held/blocked-id skip list feeding a merge or
  delete) built this way silently stops excluding anything the moment it runs
  under a non-word-splitting shell. Use `case "$x" in id1|id2) … ;; esac` or a
  line-based `grep -qxF` instead — depth: `branch-and-merge-hygiene.md` §6.
- **`set -u` + `"${arr[@]}"` on an *empty* array is a fatal `unbound variable`
  under bash 3.2 — still macOS's default `/bin/bash` (verified `3.2.57`).** A
  script that conditionally builds an array (flags, a discovered file list,
  cleanup targets) and expands it under `set -u` aborts the instant the array is
  empty; this most often sits in **trap / cleanup / reporting** code on the error
  path, where it **masks the real failure** it was meant to report. Guard the
  expansion (`${arr[@]+"${arr[@]}"}`) or seed the array — and run the script
  against the **actual `/bin/bash` on the target**, since a dev box's
  newer/homebrew bash can behave differently and hide it.

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
