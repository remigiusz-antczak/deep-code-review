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
  (locks writes); adding a `NOT NULL` column with no default; backfill in the
  same transaction as DDL; no rollback path. See `performance-db-cost.md`.

## Shell / Bash

- Unquoted expansions (`rm -rf $DIR`), `eval`, `curl … | bash`, parsing `ls`,
  missing `set -euo pipefail`, secrets in `set -x` traces, world-writable temp.

## Infrastructure as code

Terraform / Kubernetes / Docker / cloud config have their own catalog — see
`infra-iac-containers.md`.

---

**Reminder**: a grep hit is a lead. Read the context, confirm the data flow from
an untrusted source to the dangerous sink, and only then record a finding with
`file:line`, impact, and fix. No fabricated line numbers.
