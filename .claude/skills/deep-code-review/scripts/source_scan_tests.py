#!/usr/bin/env python3
"""source_scan_tests.py — flag a "test" that reads UI source as TEXT instead
of rendering it, the class of test that cannot observe conditional rendering
(issue #1105; doctrine: `references/testing-ui.md`, "A conditional-render
behaviour needs a rendered-DOM assertion, not a source scan").

WHY THIS EXISTS
----------------
A "show more" disclosure that never actually collapsed shipped through
thousands of green unit tests. The tests were source scans: a regular
expression over the component's source TEXT, pinning that certain strings
appear in a certain order. A source scan proves the author typed certain
characters; it cannot observe what the DOM actually contains before and
after an interaction — a list sliced by a live count can sit right next to a
second, unconditionally-mapped list of the same rows, and a string-order
assertion never notices. A single screenshot caught it; this script is the
opt-in, no-cost mechanism that catches the *pattern* before a screenshot is
even taken.

WHAT COUNTS AS THE DEFECT (heuristic — text pattern matching, not a parser)
-----------------------------------------------------------------------------
A test file (`*.test.*`, `*.spec.*`, any file under a `__tests__/` directory,
or a pytest-named file — `test_*.py` / `*_test.py`) that BOTH:
  1. reads a UI source file (`.tsx`, `.jsx`, `.vue`, `.svelte`) as text. This
     covers several read shapes: `readFileSync(...)` / `fs.readFileSync(...)`,
     `fs.promises.readFile(...)` / a bare `readFile(...)` (e.g. imported from
     `fs/promises`), a bundler raw-text import (`import x from './X.tsx?raw'`),
     Python's `open(...)` or `Path(...).read_text()`, and a path held in a
     variable (`const p = path.join(..., 'X.tsx'); readFileSync(p)`) — AND
  2. applies a check tied to the variable the text was read into: a
     regex/substring/Jest-matcher call whose receiver or argument is that
     variable (`.includes(`, `.match(`, `.test(`, `new RegExp(`, `.toMatch(`,
     `.toContain(`, `.toMatchSnapshot(`, Python's `re.search` / `re.match` /
     `re.findall` / `re.compile`). An unrelated call sharing one of these
     names but never applied to the source variable (`[1].includes(1)`) does
     not count — best-effort: when the read's variable can't be identified,
     this falls back to "anywhere in the file", the old, looser behaviour,
While carrying NO render/mount call anywhere in the same file (`render(`,
`mount(`, `shallow(`, `screen.`, `fireEvent`, `userEvent`, `cy.mount(`,
`cy.visit(`, `page.goto(`, `page.locator`, `ReactDOM.render`, `createRoot(`,
`renderToString`, `renderToStaticMarkup`, an `@testing-library` import, or any
call whose name contains "render" or "mount" case-insensitively, e.g. a
project helper named `renderPanel()`).

A file with BOTH signals and a render/mount call is exempt: a test may
legitimately grep source for an unrelated invariant (an import assertion, a
banned-pattern lint) alongside a real render elsewhere in the same spec.
Under-flagging here is the safe direction — the point is to catch a
BEHAVIOUR CLAIM whose ONLY evidence is a source scan, not to ban reading
source text for a lint-shaped check.

THIS IS A LINT, NOT A PROOF. It cannot tell whether the flagged test claims
to verify BEHAVIOUR (the failure mode) or a genuine lint-shaped invariant
mislabeled as a behaviour test (also worth a human look). A clean run means
"no file matched this text shape", never "every conditional-render path has
rendered-DOM coverage" — that is a human judgement this script feeds, not
replaces (`references/testing-ui.md`).

KNOWN GAPS (documented, not fixed — a parser would close these; this stays a
heuristic on purpose)
-----------------------------------------------------------------------------
- A UI component authored in plain `.ts`/`.js` (no `.tsx`/`.jsx`/`.vue`/
  `.svelte` extension — e.g. `React.createElement` without JSX, or a
  `.astro`/other framework extension not in the tracked set) is invisible to
  the extension check: this script only recognizes the four listed
  extensions in a read path.
- A comment or string literal that merely mentions `render(`/`mount(`/a
  render-shaped name (e.g. `// we don't render() here`, or that literal text
  inside a quoted string) exempts the file exactly like a real render call —
  this is presence-only text matching, not a parser that knows about
  comments or string boundaries. Under-flagging is the accepted direction.
- The variable-linkage check (point 2 above) is itself best-effort: it
  recognizes `const/let/var NAME = <read>`, a bare `NAME = <read>` (Python),
  and `import NAME from '...?raw'`, then requires NAME to appear as the
  receiver or an argument of the check call. A read whose result is used
  without ever being bound to a name (chained inline) is not variable-linked
  and falls back to "anywhere in the file" instead of skipping it.

ALLOW MARKER
-------------
A flagged line carrying `source-scan-lint: allow <reason>` (as a `#` or `//`
comment, anywhere on the same physical line as the `readFileSync`/`open`
call) is exempted — a human has recorded why this specific read is not
behaviour evidence in disguise, and the reason lives next to the code, not in
this script.

EXIT CODES
-----------
  0  no test file matched the pattern (or --report-only was passed).
  1  at least one test file matched (each finding on stderr as `path:line:`).
  2  usage error; a NAMED path does not exist; a resolved test file could not
     be read/decoded as text; or zero test files were found under the given
     paths and `--allow-empty` was not passed. All fail closed — never a
     silent narrower scan, and never a silent "nothing to report" that was
     actually "nothing was scanned".
Stdlib only.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile

OK = 0
FAIL = 1
ERROR = 2

_SKIP_DIRS = {".git", "node_modules"}

# A UI source file named inside a read argument or a raw-text import: one of
# the four extensions this doctrine covers, inside a quoted literal, with an
# optional bundler `?raw` suffix (`import x from './X.tsx?raw'`).
_UI_SOURCE_EXT_RE = re.compile(r"\.(?:tsx|jsx|vue|svelte)(?:\?raw)?[\"'`]")

# Read-call shapes that pull a UI source file's bytes into a string, captured
# up to the first unmatched `)` (deliberate heuristic — a nested call in the
# argument, e.g. `readFileSync(path.join(a, b))`, truncates early and simply
# won't match the extension check in the common case; an under-flag, the safe
# direction). `[^)]*` matches across newlines, so a call whose arguments span
# multiple lines is still captured (see `_var_for_read_line`'s note on the
# starting line only). Each alternative funnels its argument text into one of
# these four numbered groups so `_first_present` below can pick whichever
# fired.
_READ_CALL_RE = re.compile(
    r"\b(?:fs\.)?readFileSync\s*\(\s*([^)]*)\)"
    r"|\bopen\s*\(\s*([^)]*)\)"
    r"|\b(?:fs\.promises\.readFile|readFile)\s*\(\s*([^)]*)\)"
    r"|\bPath\s*\(\s*([^)]*)\)\s*\.\s*read_text\s*\(\s*\)"
)

# A bundler raw-text import: `import NAME from './X.tsx?raw'`. This is a read
# by itself — no call, no variable-linkage inference needed, the binding name
# is the import's own local name.
_IMPORT_RAW_RE = re.compile(
    r"""\bimport\s+([A-Za-z_$][\w$]*)\s+from\s*"""
    r"""['"`]([^'"`]+\.(?:tsx|jsx|vue|svelte)\?raw)['"`]"""
)

# A variable assigned a value that itself names a UI source file anywhere in
# the RHS (covers both a bare literal, `const p = './Panel.tsx'`, and a
# wrapped one, `const p = path.join(__dirname, 'Panel.tsx')`) — feeds the
# "path held in a variable, then read(p)" shape.
_VAR_ASSIGN_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*=\s*[^;\n]*\.(?:tsx|jsx|vue|svelte)(?:\?raw)?[\"'`]"
)

# The variable a read call's result was bound to, extracted from the read
# call's OWN starting physical line only (a multi-line call's continuation
# lines are not consulted) — best-effort, matching this script's "heuristic,
# not a parser" contract.
_VAR_DECL_RE = re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=")
_VAR_BARE_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*=")


def _var_for_read_line(line: str) -> str | None:
    m = _VAR_DECL_RE.search(line)
    if m:
        return m.group(1)
    m = _VAR_BARE_ASSIGN_RE.match(line)
    if m:
        return m.group(1)
    return None


# Regex/substring/Jest-matcher check applied to text. `.test(` and `.match(`
# require a LEADING DOT so Jest's bare `test('name', () => {...})` and a bare
# `match(...)` never match — false positives here would blame files that
# never scan text. `.toMatch(`/`.toContain(`/`.toMatchSnapshot(` are Jest
# matchers over a raw string and count as text checks too (the core #1105
# case: `expect(src).toMatch(/x/)` is exactly the failure mode, not a lint
# exemption).
_REGEX_INCLUDES_RE = re.compile(
    r"\.includes\s*\(|\.match\s*\(|\.test\s*\(|\bnew RegExp\s*\("
    r"|\.toMatch\s*\(|\.toContain\s*\(|\.toMatchSnapshot\s*\("
    r"|\bre\.search\s*\(|\bre\.match\s*\(|\bre\.findall\s*\(|\bre\.compile\s*\("
)

# A render/mount call anywhere in the file exempts it — presence-only check
# (a comment or string literal mentioning "render(" without a real call is an
# accepted, under-flagging false exemption; never a false alarm on genuine
# coverage).
_RENDER_TOKENS = (
    "render(", "mount(", "shallow(", "screen.", "fireEvent", "userEvent",
    "cy.mount(", "cy.visit(", "page.goto(", "page.locator",
    "ReactDOM.render", "createRoot(", "renderToString", "renderToStaticMarkup",
    "@testing-library",
)

# A call whose name CONTAINS "render" or "mount" (case-insensitive) also
# exempts — a project helper like `renderPanel()` or `mountComponent()`
# renders just as much as a literal `render(` call; `_RENDER_TOKENS` above
# only covers exact framework spellings.
_RENDER_CALL_RE = re.compile(r"\w*(?:render|mount)\w*\s*\(", re.IGNORECASE)

_ALLOW_RE = re.compile(r"(?:#|//)\s*source-scan-lint:\s*allow\b")


def _is_ui_reference(name_or_arg: str, path_vars: set[str]) -> bool:
    """True when `name_or_arg` (a read call's captured argument text) names a
    UI source file directly, or is a bare identifier bound to one via
    `_VAR_ASSIGN_RE` (the "path held in a variable" shape)."""
    if _UI_SOURCE_EXT_RE.search(name_or_arg):
        return True
    first = name_or_arg.split(",", 1)[0].strip().strip("'\"`")
    return bool(re.fullmatch(r"[A-Za-z_$][\w$]*", first)) and first in path_vars


def _has_var_linked_check(text: str, text_vars: set[str]) -> bool:
    """Best-effort: does a regex/includes/Jest-matcher check reference one of
    `text_vars` as its receiver or an argument? Falls back to "anywhere in
    the file" (the caller decides when to use that) when `text_vars` is
    empty — the read's binding could not be identified."""
    if not text_vars:
        return False
    var_alt = "|".join(re.escape(v) for v in sorted(text_vars))
    patterns = (
        # Direct chain on the variable: `src.includes(`, `src.toMatch(`, ...
        rf"\b(?:{var_alt})\b\s*\.\s*(?:includes|match|test|toMatch|toContain|toMatchSnapshot)\s*\(",
        # Jest's expect(VAR).toMatch(/toContain/toMatchSnapshot(...).
        rf"\bexpect\s*\(\s*(?:{var_alt})\s*\)\s*\.\s*(?:toMatch|toContain|toMatchSnapshot)\s*\(",
        # Argument-style: `pattern.test(src)`, `re.search(p, src)`, etc.
        rf"(?:\.test|\.search|\.match|\.findall)\s*\([^)]*\b(?:{var_alt})\b",
    )
    return any(re.search(p, text) for p in patterns)


def _is_test_file(path: str) -> bool:
    """*.test.*, *.spec.*, anywhere under a __tests__/ directory, or a
    pytest-named file (`test_*.py` / `*_test.py`)."""
    posix = path.replace(os.sep, "/").lower()
    base = posix.rsplit("/", 1)[-1]
    if ".test." in base or ".spec." in base:
        return True
    if "__tests__" in posix.split("/"):
        return True
    if base.endswith(".py") and (base.startswith("test_") or base.endswith("_test.py")):
        return True
    return False


def _iter_test_files(paths: list[str]) -> tuple[list[str], list[str]]:
    """Resolve CLI paths to test files. Returns (files, errors).

    A named path that does not exist is an error (fail closed) — never a
    silently narrower scan than the caller asked for.
    """
    files: list[str] = []
    errors: list[str] = []

    def on_walk_error(exc: OSError) -> None:
        errors.append(
            f"source_scan_tests: cannot list {getattr(exc, 'filename', '?')} "
            f"(fail closed): {exc.strerror or exc}"
        )

    for p in paths:
        if os.path.isfile(p):
            if _is_test_file(p):
                files.append(p)
        elif os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p, onerror=on_walk_error):
                dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
                for fn in sorted(filenames):
                    full = os.path.join(dirpath, fn)
                    if _is_test_file(full):
                        files.append(full)
        else:
            errors.append(f"source_scan_tests: path not found: {p} (fail closed)")
    return files, errors


def _read_text(path: str) -> str | None:
    """Read `path` as UTF-8 text; None when it is not readable text."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def scan_file(path: str, text: str) -> list[tuple[int, str]]:
    """Return [(lineno, evidence line)] when `text` is a source-scan-only test."""
    lines = text.splitlines()
    path_vars = {m.group(1) for m in _VAR_ASSIGN_RE.finditer(text)}

    read_hits: list[tuple[int, str]] = []
    text_vars: set[str] = set()

    for m in _READ_CALL_RE.finditer(text):
        arg = next((g for g in m.groups() if g is not None), "")
        if not _is_ui_reference(arg, path_vars):
            continue
        lineno = text.count("\n", 0, m.start()) + 1
        line = lines[lineno - 1] if 0 <= lineno - 1 < len(lines) else ""
        if _ALLOW_RE.search(line):
            continue
        read_hits.append((lineno, line.strip()))
        var = _var_for_read_line(line)
        if var:
            text_vars.add(var)

    for m in _IMPORT_RAW_RE.finditer(text):
        # _IMPORT_RAW_RE's own capture already requires the extension +
        # `?raw` suffix — no separate extension check needed here.
        var = m.group(1)
        lineno = text.count("\n", 0, m.start()) + 1
        line = lines[lineno - 1] if 0 <= lineno - 1 < len(lines) else ""
        if _ALLOW_RE.search(line):
            continue
        read_hits.append((lineno, line.strip()))
        text_vars.add(var)

    if not read_hits:
        return []

    has_check = _has_var_linked_check(text, text_vars)
    if not has_check and not text_vars:
        # Binding could not be identified for any read hit — best-effort
        # fallback to the old, looser "anywhere in the file" signal.
        has_check = bool(_REGEX_INCLUDES_RE.search(text))
    if not has_check:
        return []
    if any(tok in text for tok in _RENDER_TOKENS) or _RENDER_CALL_RE.search(text):
        return []
    return read_hits


class ScanCounts:
    """Plain counters `run_scan` reports so a caller can tell "scanned
    everything, found nothing" apart from "scanned nothing"."""

    __slots__ = ("scanned", "skipped")

    def __init__(self, scanned: int = 0, skipped: int = 0) -> None:
        self.scanned = scanned
        self.skipped = skipped


def run_scan(
    paths: list[str], allow_empty: bool = False
) -> tuple[int, list[str], list[str], ScanCounts]:
    """Returns (exit_code, finding_lines, error_lines, counts)."""
    files, errors = _iter_test_files(paths)
    if errors:
        return ERROR, [], errors, ScanCounts()

    if not files:
        if allow_empty:
            return OK, [], [], ScanCounts()
        return (
            ERROR,
            [],
            [
                f"source_scan_tests: 0 test file(s) found under "
                f"{', '.join(paths)} (fail closed; pass --allow-empty for an "
                f"intentionally test-free path)"
            ],
            ScanCounts(),
        )

    findings: list[str] = []
    read_errors: list[str] = []
    counts = ScanCounts()
    for path in files:
        text = _read_text(path)
        if text is None:
            counts.skipped += 1
            read_errors.append(
                f"source_scan_tests: cannot read {path} as text (fail closed: "
                f"unreadable or undecodable)"
            )
            continue
        counts.scanned += 1
        for lineno, evidence in scan_file(path, text):
            findings.append(
                f"{path}:{lineno}: reads UI source as text and regex/includes "
                f"it, with no render/mount/screen call in this file "
                f"({evidence}) — a source scan is lint, never behaviour "
                f"evidence for a conditional-render claim (testing-ui.md)"
            )
    if read_errors:
        return ERROR, findings, read_errors, counts
    return (FAIL if findings else OK), findings, [], counts


# ---------------------------------------------------------------------------
# Selftest — planted RED/GREEN cases in a temp dir, no fixture repo checked in.
# ---------------------------------------------------------------------------

def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _selftest() -> int:
    failures: list[str] = []
    total = 0

    def check(
        name: str,
        rc: int,
        lines: list[str],
        want_rc: int,
        must_have: tuple[str, ...] = (),
    ) -> None:
        nonlocal total
        total += 1
        joined = "\n".join(lines)
        ok = rc == want_rc and all(needle in joined for needle in must_have)
        if not ok:
            failures.append(f"{name}: rc={rc} (want {want_rc}); output={joined!r}")

    with tempfile.TemporaryDirectory() as tmp:
        # 1) source-scan-only test on a .tsx — FAIL, names file:line.
        fire = os.path.join(tmp, "fire")
        _write(
            os.path.join(fire, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('collapses on click', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect(src.includes('aria-expanded')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([fire])
        check(
            "source-scan-only-fires", rc, findings, FAIL,
            must_have=("Panel.test.tsx:3:", "source scan is lint"),
        )

        # 2) same shape, but the file ALSO renders and asserts the DOM — OK,
        #    the render call exempts it (a lint-shaped grep alongside real
        #    coverage is not the defect this catches).
        clean = os.path.join(tmp, "clean")
        _write(
            os.path.join(clean, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "import { render, screen, fireEvent } from '@testing-library/react';\n"
            "import { Panel } from './Panel';\n"
            "test('collapses on click', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect(src.includes('aria-expanded')).toBe(true);\n"
            "  render(<Panel />);\n"
            "  fireEvent.click(screen.getByText('Show more'));\n"
            "  expect(screen.queryByText('hidden row')).not.toBeInTheDocument();\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([clean])
        check("render-call-exempts", rc, findings, OK)

        # 3) reads the .tsx but applies no regex/includes/Jest-matcher check
        #    to it at all — OK, the second signal is required, not just the
        #    read (`.toMatchSnapshot()` DOES count now, see case 8 below —
        #    this uses a plain length check to stay a genuine non-match).
        readonly = os.path.join(tmp, "readonly")
        _write(
            os.path.join(readonly, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('has content', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect(src.length).toBeGreaterThan(0);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([readonly])
        check("read-without-any-check-is-ok", rc, findings, OK)

        # 4) planted violation with an inline allow marker — exempted.
        allowed = os.path.join(tmp, "allowed")
        _write(
            os.path.join(allowed, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('banned-import lint', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8'); "
            "// source-scan-lint: allow import-lint, not a behaviour claim\n"
            "  expect(src.includes('lodash')).toBe(false);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([allowed])
        check("allow-marker-exempts", rc, findings, OK)

        # 5) a non-test file with the exact same shape, inside a directory
        #    with no test files at all — the naming check correctly excludes
        #    it; `allow_empty=True` documents that a directory legitimately
        #    carrying no test files is not itself the failure this script
        #    guards (case 19 below covers the opposite, unscoped default).
        nontest = os.path.join(tmp, "nontest")
        _write(
            os.path.join(nontest, "PanelHelper.ts"),
            "import fs from 'fs';\n"
            "export function bannedImports() {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  return src.includes('lodash');\n"
            "}\n",
        )
        rc, findings, errors, _ = run_scan([nontest], allow_empty=True)
        check("non-test-file-ignored", rc, findings, OK)

        # 6) __tests__/ directory naming, not *.test.* — still matched.
        dirnamed = os.path.join(tmp, "dirnamed")
        _write(
            os.path.join(dirnamed, "__tests__", "panel.tsx"),
            "import fs from 'fs';\n"
            "test('collapses', () => {\n"
            "  const src = fs.readFileSync('../Panel.tsx', 'utf8');\n"
            "  expect(src.match(/aria-expanded/)).toBeTruthy();\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([dirnamed])
        check("tests-dir-naming-fires", rc, findings, FAIL)

        # 7) a named path that does not exist — ERROR, fail closed.
        rc, findings, errors, _ = run_scan([os.path.join(tmp, "does-not-exist")])
        check("missing-path-errors", rc, errors, ERROR, must_have=("path not found",))

        # 8) `expect(src).toMatchSnapshot()` alone IS a text check now (the
        #    core #1105 fix: a raw-source snapshot is exactly as blind to
        #    conditional rendering as a `.includes()` check) — FAIL.
        snap = os.path.join(tmp, "snap")
        _write(
            os.path.join(snap, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('source snapshot', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect(src).toMatchSnapshot();\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([snap])
        check("toMatchSnapshot-counts-as-text-check", rc, findings, FAIL)

        # 9) `expect(src).toMatch(...)` / `.toContain(...)` — Jest's actual
        #    idiom for the #1105 bug, previously invisible to the lint
        #    (`.match(` required a leading dot, `.toMatch(` has none before
        #    "match") — FAIL.
        tomatch = os.path.join(tmp, "tomatch")
        _write(
            os.path.join(tomatch, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('x', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect(src).toMatch(/hidden/);\n"
            "  expect(src).toContain('x');\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([tomatch])
        check("toMatch-and-toContain-count-as-text-checks", rc, findings, FAIL)

        # 10) an `.includes(` call that shares the file but is never applied
        #     to the source variable — not itself a text check on the
        #     source; with no other check present this is OK.
        unrelated = os.path.join(tmp, "unrelated")
        _write(
            os.path.join(unrelated, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('x', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect([1].includes(1)).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([unrelated])
        check("unrelated-includes-not-flagged", rc, findings, OK)

        # 11) `fs.promises.readFile` (async read shape) — FAIL.
        async_read = os.path.join(tmp, "async_read")
        _write(
            os.path.join(async_read, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('x', async () => {\n"
            "  const src = await fs.promises.readFile('./Panel.tsx', 'utf8');\n"
            "  expect(src.includes('hidden')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([async_read])
        check("fs-promises-readFile-fires", rc, findings, FAIL)

        # 12) bare `readFile` imported from 'fs/promises' — FAIL.
        bare_read = os.path.join(tmp, "bare_read")
        _write(
            os.path.join(bare_read, "Panel.test.tsx"),
            "import { readFile } from 'fs/promises';\n"
            "test('x', async () => {\n"
            "  const src = await readFile('./Panel.tsx', 'utf8');\n"
            "  expect(src.includes('hidden')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([bare_read])
        check("bare-readFile-from-fs-promises-fires", rc, findings, FAIL)

        # 13) a bundler raw-text import, `import src from './Panel.tsx?raw'`
        #     — no call at all, the import itself is the read — FAIL.
        raw_import = os.path.join(tmp, "raw_import")
        _write(
            os.path.join(raw_import, "Panel.test.tsx"),
            "import src from './Panel.tsx?raw';\n"
            "test('x', () => {\n"
            "  expect(src.includes('hidden')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([raw_import])
        check("raw-text-import-fires", rc, findings, FAIL)

        # 14) Python `Path(...).read_text()`, pytest `test_*.py` naming — FAIL.
        py_prefix = os.path.join(tmp, "py_prefix")
        _write(
            os.path.join(py_prefix, "test_panel.py"),
            "from pathlib import Path\n"
            "import re\n"
            "def test_x():\n"
            "    src = Path('Panel.tsx').read_text()\n"
            "    assert re.search('hidden', src)\n",
        )
        rc, findings, errors, _ = run_scan([py_prefix])
        check("python-read-text-and-pytest-prefix-naming-fires", rc, findings, FAIL)

        # 15) pytest `*_test.py` naming (the suffix form) — FAIL.
        py_suffix = os.path.join(tmp, "py_suffix")
        _write(
            os.path.join(py_suffix, "panel_test.py"),
            "import re\n"
            "def test_x():\n"
            "    src = open('Panel.tsx').read()\n"
            "    assert re.search('hidden', src)\n",
        )
        rc, findings, errors, _ = run_scan([py_suffix])
        check("pytest-suffix-naming-fires", rc, findings, FAIL)

        # 16) a path held in a variable, then read via that variable — FAIL.
        var_path = os.path.join(tmp, "var_path")
        _write(
            os.path.join(var_path, "Panel.test.tsx"),
            "import fs from 'fs'; import path from 'path';\n"
            "test('x', () => {\n"
            "  const p = path.join(__dirname, 'Panel.tsx');\n"
            "  const src = fs.readFileSync(p, 'utf8');\n"
            "  expect(src.includes('hidden')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([var_path])
        check("path-in-variable-fires", rc, findings, FAIL)

        # 17) a read call whose arguments span multiple lines — FAIL, and the
        #     reported line is the call's OWN starting line.
        multiline = os.path.join(tmp, "multiline")
        _write(
            os.path.join(multiline, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('x', () => {\n"
            "  const src = fs.readFileSync(\n"
            "    './Panel.tsx', 'utf8');\n"
            "  expect(src.includes('hidden')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([multiline])
        check("multiline-call-args-fires", rc, findings, FAIL, must_have=("Panel.test.tsx:3:",))

        # 18) a project helper whose NAME contains "render" (not a literal
        #     `render(` token) — exempts, same as a real render call.
        helper = os.path.join(tmp, "helper")
        _write(
            os.path.join(helper, "Panel.test.tsx"),
            "import { renderPanel } from './helpers';\n"
            "import fs from 'fs';\n"
            "test('x', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect(src.includes('lodash')).toBe(false);\n"
            "  renderPanel();\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([helper])
        check("helper-render-name-exempts", rc, findings, OK)

        # 19) zero test files found, no `--allow-empty` — ERROR, fail closed
        #     (an empty scan must never look identical to "clean").
        zero_dir = os.path.join(tmp, "zero")
        os.makedirs(zero_dir)
        rc, findings, errors, counts = run_scan([zero_dir])
        check(
            "zero-test-files-errors-without-allow-empty", rc, errors, ERROR,
            must_have=("0 test file(s) found",),
        )
        if counts.scanned != 0 or counts.skipped != 0:
            failures.append(
                f"zero-test-files-counts-are-zero: scanned={counts.scanned} skipped={counts.skipped}"
            )
        total += 1

        # 20) same empty directory, `--allow-empty` passed — OK.
        rc, findings, errors, _ = run_scan([zero_dir], allow_empty=True)
        check("zero-test-files-ok-with-allow-empty", rc, findings, OK)

        # 21) an undecodable test file — ERROR, fail closed, names the file.
        undecodable = os.path.join(tmp, "undecodable")
        os.makedirs(undecodable, exist_ok=True)
        with open(os.path.join(undecodable, "Panel.test.ts"), "wb") as fh:
            fh.write(b"test('x', () => { fs.readFileSync('./Panel.tsx'); });\n\xff\xfe\x00")
        rc, findings, errors, _ = run_scan([undecodable])
        check(
            "unreadable-file-errors", rc, errors, ERROR,
            must_have=("cannot read", "Panel.test.ts"),
        )

        # 22) scanned/skipped counts are reported and reflect a real mix of
        #     readable and undecodable test files (dynamic — not a hardcoded
        #     count of the WHOLE selftest, just this fixture's own 2 files).
        mixed = os.path.join(tmp, "mixed")
        _write(
            os.path.join(mixed, "Clean.test.tsx"),
            "test('x', () => { expect(1).toBe(1); });\n",
        )
        with open(os.path.join(mixed, "Bad.test.ts"), "wb") as fh:
            fh.write(b"\xff\xfe\x00 not decodable")
        rc, findings, errors, counts = run_scan([mixed])
        total += 1
        if not (rc == ERROR and counts.scanned == 1 and counts.skipped == 1):
            failures.append(
                f"scanned-skipped-counts-reported: rc={rc} scanned={counts.scanned} skipped={counts.skipped}"
            )

        # 23) `--report-only` is actually exercised end-to-end via `main()`,
        #     not just asserted about in a comment: a planted violation still
        #     exits 0 when the flag is passed.
        report_only_rc = main([fire, "--report-only"])
        total += 1
        if report_only_rc != OK:
            failures.append(f"report-only-actually-runs: rc={report_only_rc} (want {OK})")

        # 24) a `.ts` (not `.tsx`) component source is a documented gap, not
        #     a bug — the extension check deliberately does not cover it.
        ts_gap = os.path.join(tmp, "ts_gap")
        _write(
            os.path.join(ts_gap, "Panel.test.ts"),
            "import fs from 'fs';\n"
            "test('x', () => {\n"
            "  const src = fs.readFileSync('./Panel.ts', 'utf8');\n"
            "  expect(src.includes('hidden')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([ts_gap])
        check("dot-ts-extension-is-a-documented-gap-not-flagged", rc, findings, OK)

        # 25) an unsupported framework extension (`.astro`) is likewise a
        #     documented gap.
        astro_gap = os.path.join(tmp, "astro_gap")
        _write(
            os.path.join(astro_gap, "Panel.test.ts"),
            "import fs from 'fs';\n"
            "test('x', () => {\n"
            "  const src = fs.readFileSync('./Panel.astro', 'utf8');\n"
            "  expect(src.includes('hidden')).toBe(true);\n"
            "});\n",
        )
        rc, findings, errors, _ = run_scan([astro_gap])
        check("dot-astro-extension-is-a-documented-gap-not-flagged", rc, findings, OK)

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"SELFTEST OK: {total}/{total} cases passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flag a test that reads UI source as text (readFileSync/open + "
        "regex/includes) with no render/mount/screen call in the same file — "
        "lint, never behaviour evidence for a conditional-render claim."
    )
    parser.add_argument(
        "paths", nargs="*", default=["."],
        help="test files and/or directories to scan (default: current directory)",
    )
    parser.add_argument(
        "--report-only", action="store_true",
        help="print findings but always exit 0 (advisory mode)",
    )
    parser.add_argument(
        "--allow-empty", action="store_true",
        help="exit 0 (instead of 2) when zero test files are found under the given paths",
    )
    parser.add_argument("--selftest", action="store_true", help="run the built-in selftest and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    code, findings, errors, counts = run_scan(args.paths, allow_empty=args.allow_empty)
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        print(
            f"source_scan_tests: scanned {counts.scanned} test file(s), "
            f"skipped {counts.skipped} (unreadable)",
            file=sys.stderr,
        )
        return ERROR
    for line in findings:
        print(line, file=sys.stderr if code == FAIL else sys.stdout)
    if findings:
        print(
            f"source_scan_tests: {len(findings)} source-scan-only test(s) found",
            file=sys.stderr,
        )
    else:
        print("source_scan_tests: ok")
    print(
        f"source_scan_tests: scanned {counts.scanned} test file(s), "
        f"skipped {counts.skipped} (unreadable)"
    )
    if args.report_only:
        return OK
    return code


if __name__ == "__main__":
    sys.exit(main())
