# Python red flags

Read this when the target contains Python. Split from `language-stack-redflags.md`; its fast first pass and cross-language sections apply to every review, and each hit here is a signal, not a verdict.

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
