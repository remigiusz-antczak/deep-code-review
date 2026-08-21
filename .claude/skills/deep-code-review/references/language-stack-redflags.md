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
- `process.env.X` read at module load without validation → silent misconfig.
- Secrets or API keys referenced in client/bundle code → shipped to the browser.

## Go

- Ignored errors: `_ =` on a call that returns `error`, or no `if err != nil`.
- String-built SQL vs `db.Query(q, args...)`; `fmt.Sprintf` into a query.
- `exec.Command("sh", "-c", built)` → command injection.
- Goroutine leaks: a goroutine with no cancellation/`context`; `defer` inside a
  loop accumulating until function return.
- `math/rand` for security (use `crypto/rand`); missing `rows.Close()`;
  data races (run with `-race`); `panic` used for normal control flow.

## Java / Kotlin

- `ObjectInputStream.readObject` on untrusted bytes → deserialization RCE.
- XXE: `DocumentBuilderFactory`/`SAXParser` without disabling external entities.
- `Runtime.exec`/`ProcessBuilder` with a concatenated string.
- String-built JPQL/SQL vs `PreparedStatement`/bound params.
- `Random` for tokens (use `SecureRandom`); swallowed `catch (Exception e) {}`;
  `printStackTrace()` to the response; broad `@SuppressWarnings`.

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
- Run with ASan/UBSan; these map to top CWEs (787/416/125).

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
- **Decompression / entity-expansion bombs** — an archive (`zip`/`gzip`/`tar`)
  extracted with no size or ratio cap, or XML parsed with entity expansion enabled
  (billion-laughs): a small input that inflates to gigabytes. Cap the decompressed
  size and disable external/DTD entity resolution.

## Shell / Bash

- Unquoted expansions (`rm -rf $DIR`), `eval`, `curl … | bash`, parsing `ls`,
  missing `set -euo pipefail`, secrets in `set -x` traces, world-writable temp.

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
