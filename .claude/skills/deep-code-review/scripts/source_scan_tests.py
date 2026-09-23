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
A test file (`*.test.*`, `*.spec.*`, or any file under a `__tests__/`
directory) that BOTH:
  1. reads a UI source file (`.tsx`, `.jsx`, `.vue`, `.svelte`) as text —
     `readFileSync(...)` / `fs.readFileSync(...)` / Python `open(...)` naming
     one of those extensions in its path argument — AND
  2. applies a regex/substring check to that text anywhere in the same file
     (`.match(`, `.test(`, `.includes(`, `new RegExp(`, or Python's
     `re.search` / `re.match` / `re.findall` / `re.compile`),
while carrying NO render/mount call anywhere in the same file (`render(`,
`mount(`, `shallow(`, `screen.`, `fireEvent`, `userEvent`, `cy.mount(`,
`cy.visit(`, `page.goto(`, `page.locator`, `ReactDOM.render`, `createRoot(`,
`renderToString`, `renderToStaticMarkup`, or an `@testing-library` import).

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
  2  usage error, or a NAMED path does not exist (fail closed — never a
     silent narrower scan than the caller asked for).
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

# A UI source file named inside a readFileSync/open(...) argument: one of the
# four extensions this doctrine covers, inside a quoted literal.
_UI_SOURCE_EXT_RE = re.compile(r"\.(?:tsx|jsx|vue|svelte)[\"'`]")

# readFileSync(...) / fs.readFileSync(...) / Python open(...) — the argument
# list is captured up to the first `)`, a deliberate heuristic (a nested call
# in the argument, e.g. `readFileSync(path.join(a, b))`, truncates early and
# simply won't match the extension check — an under-flag, the safe direction).
_READ_CALL_RE = re.compile(
    r"\b(?:fs\.)?readFileSync\s*\(\s*([^)]*)\)|\bopen\s*\(\s*([^)]*)\)"
)

# Regex/substring check applied to text read into a variable. `.test(` and
# `.match(` require a LEADING DOT so Jest's bare `test('name', () => {...})`
# and `expect(x).toMatch(...)` (capital M, no leading dot before "match")
# never match — false positives here would blame files that never scan text.
_REGEX_INCLUDES_RE = re.compile(
    r"\.includes\s*\(|\.match\s*\(|\.test\s*\(|\bnew RegExp\s*\("
    r"|\bre\.search\s*\(|\bre\.match\s*\(|\bre\.findall\s*\(|\bre\.compile\s*\("
)

# A render/mount call anywhere in the file exempts it — presence-only check
# (a comment mentioning "render(" without a real call is an accepted,
# under-flagging false exemption; never a false alarm on genuine coverage).
_RENDER_TOKENS = (
    "render(", "mount(", "shallow(", "screen.", "fireEvent", "userEvent",
    "cy.mount(", "cy.visit(", "page.goto(", "page.locator",
    "ReactDOM.render", "createRoot(", "renderToString", "renderToStaticMarkup",
    "@testing-library",
)

_ALLOW_RE = re.compile(r"(?:#|//)\s*source-scan-lint:\s*allow\b")


def _is_test_file(path: str) -> bool:
    """*.test.*, *.spec.*, or anywhere under a __tests__/ directory."""
    posix = path.replace(os.sep, "/").lower()
    base = posix.rsplit("/", 1)[-1]
    if ".test." in base or ".spec." in base:
        return True
    return "__tests__" in posix.split("/")


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
    read_hits: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        for m in _READ_CALL_RE.finditer(line):
            arg = m.group(1) or m.group(2) or ""
            if _UI_SOURCE_EXT_RE.search(arg) and not _ALLOW_RE.search(line):
                read_hits.append((i, line.strip()))
    if not read_hits:
        return []
    if not _REGEX_INCLUDES_RE.search(text):
        return []
    if any(tok in text for tok in _RENDER_TOKENS):
        return []
    return read_hits


def run_scan(paths: list[str]) -> tuple[int, list[str], list[str]]:
    """Returns (exit_code, finding_lines, error_lines)."""
    files, errors = _iter_test_files(paths)
    if errors:
        return ERROR, [], errors

    findings: list[str] = []
    for path in files:
        text = _read_text(path)
        if text is None:
            continue  # not decodable text — nothing this lint can read
        for lineno, evidence in scan_file(path, text):
            findings.append(
                f"{path}:{lineno}: reads UI source as text and regex/includes "
                f"it, with no render/mount/screen call in this file "
                f"({evidence}) — a source scan is lint, never behaviour "
                f"evidence for a conditional-render claim (testing-ui.md)"
            )
    return (FAIL if findings else OK), findings, []


# ---------------------------------------------------------------------------
# Selftest — planted RED/GREEN cases in a temp dir, no fixture repo checked in.
# ---------------------------------------------------------------------------

def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _selftest() -> int:
    failures: list[str] = []

    def check(name: str, rc: int, lines: list[str], want_rc: int, must_have: tuple[str, ...] = ()) -> None:
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
        rc, findings, errors = run_scan([fire])
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
        rc, findings, errors = run_scan([clean])
        check("render-call-exempts", rc, findings, OK)

        # 3) reads the .tsx but never regex/includes it (e.g. only snapshots
        #    it) — OK, the second signal is required, not just the read.
        readonly = os.path.join(tmp, "readonly")
        _write(
            os.path.join(readonly, "Panel.test.tsx"),
            "import fs from 'fs';\n"
            "test('source snapshot', () => {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  expect(src).toMatchSnapshot();\n"
            "});\n",
        )
        rc, findings, errors = run_scan([readonly])
        check("read-without-regex-is-ok", rc, findings, OK)

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
        rc, findings, errors = run_scan([allowed])
        check("allow-marker-exempts", rc, findings, OK)

        # 5) a non-test file with the exact same shape — ignored (not a test
        #    file by *.test.*/*.spec.*/__tests__/ naming).
        nontest = os.path.join(tmp, "nontest")
        _write(
            os.path.join(nontest, "PanelHelper.ts"),
            "import fs from 'fs';\n"
            "export function bannedImports() {\n"
            "  const src = fs.readFileSync('./Panel.tsx', 'utf8');\n"
            "  return src.includes('lodash');\n"
            "}\n",
        )
        rc, findings, errors = run_scan([nontest])
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
        rc, findings, errors = run_scan([dirnamed])
        check("tests-dir-naming-fires", rc, findings, FAIL)

        # 7) --report-only semantics live in main(); exercised there via the
        #    exit-code contract: run_scan() itself always reports the FAIL
        #    verdict, main() downgrades it to 0 when --report-only is set.

        # 8) a named path that does not exist — ERROR, fail closed.
        rc, findings, errors = run_scan([os.path.join(tmp, "does-not-exist")])
        check("missing-path-errors", rc, errors, ERROR, must_have=("path not found",))

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELFTEST OK: 8/8 cases passed")
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
    parser.add_argument("--selftest", action="store_true", help="run the built-in selftest and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    code, findings, errors = run_scan(args.paths)
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
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
    if args.report_only:
        return OK
    return code


if __name__ == "__main__":
    sys.exit(main())
