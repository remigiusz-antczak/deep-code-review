#!/usr/bin/env python3
"""reaper_lint.py — flag a bulk/fleet-wide process-reaper pattern in a cleanup
script before it ships, instead of after it takes down every parallel agent
lane sharing the host.

WHY THIS EXISTS
----------------
`references/concurrency-shared-state.md`'s "Terminating work you own" section
documents the doctrine: a reaper may only kill processes it can prove are its
own or orphaned (parent PID 1, a cwd inside the caller's own worktree, or a
PID file the caller wrote) and must select the LISTENER only
(`lsof -t -iTCP:PORT -sTCP:LISTEN`), never a bare port or name/command-line
match. That is prose an agent may or may not follow. This script is the
mechanism: a static, stdlib-only lint over shell/Makefile/package.json-script/
CI-YAML text that flags the four concrete shapes of the bug class named in
issue #1101 before they land.

WHAT IT SCANS
--------------
Each argument may be a file (scanned regardless of its name/extension — the
caller explicitly chose it) or a directory (walked recursively, restricted to
`*.sh` / `*.bash` / `*.zsh`, a file literally named `Makefile` or `makefile`,
`package.json`, and `*.yml` / `*.yaml` — the shapes named in the routing
issue; `.git` and `node_modules` are skipped). Detection itself is plain-text,
line-based (not a shell/YAML/JSON parser), so a dangerous command embedded as
a YAML `run: |` block or a `package.json` `scripts` string value is caught
the same way a `.sh` file is — the false-positive/negative trade-off of a
lint, not a linter's guarantee.

RULES (fail on any un-escaped match)
--------------------------------------
  a. LSOF_NO_LISTEN   `lsof -ti` / `-it` / `-t -i` (terse + network flags
                       combined, either order) on a line that also mentions
                       `kill` (same line or within the next 2 lines) with no
                       `-sTCP:LISTEN` on that line — matches a connected
                       client, not only the listener.
  b. RANGE_KILL       `seq <N> <M>` feeding a loop that also mentions `kill`
                       within the next 5 lines — a bulk kill across a whole
                       port range, not a single owned port.
  c. BROAD_PKILL      `pkill -f` or `killall` targeting a browser/server-name
                       pattern (chrome/chromium/firefox/webkit/safari/edge/
                       headless/browser/electron/playwright/puppeteer/node/
                       server/http/python/java/deno/uvicorn/gunicorn/next/
                       vite/webpack) — reaps a sibling lane's identically
                       named process, not only an orphan.
  d. HARDCODED_PORTS  a protect/exclude/reserved/skip/allow/keep-named
                       variable assigned a literal list of 2+ port-like
                       numbers, in a file that also mentions `kill` anywhere
                       — an operator-owned exclusion list living as a script
                       literal goes stale the moment a new backend is added.

ESCAPE HATCH
-------------
A finding is suppressed when the literal text `reaper-lint: allow <reason>`
appears on the same line or the line immediately above it (a `#`/`//`
comment in shell/Makefile/YAML, or a plain preceding line where the file
format has no comment syntax, e.g. `package.json`). The reason is never
validated for content — presence is the gate; review judges whether the
stated reason holds.

EXIT CODES (fail-closed)
-------------------------
  0  no un-escaped finding in any scanned file (including "nothing matched
     the scan filters").
  1  at least one un-escaped finding (each printed as `path:line: [RULE]
     message`).
  2  an explicitly named path does not exist, or is neither a file nor a
     directory — the scan could not run at all, never a silent pass.
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

ESCAPE_MARKER = "reaper-lint: allow"

# --- rule (a): terse+network lsof flags combined, in either short-flag order.
_LSOF_TI_RE = re.compile(r"lsof\s+(-ti\b|-it\b|-t\s+-i\b|-i\s+-t\b)", re.IGNORECASE)
_STCP_LISTEN_RE = re.compile(r"-s\s*tcp:listen", re.IGNORECASE)
_KILL_WORD_RE = re.compile(r"\bkill\b", re.IGNORECASE)

# --- rule (b): a numeric seq range.
_SEQ_RANGE_RE = re.compile(r"\bseq\s+\d+\s+\d+\b")

# --- rule (c): pkill/killall on a browser- or server-shaped pattern.
_PKILL_RE = re.compile(r"\b(pkill|killall)\b", re.IGNORECASE)
_BROAD_KEYWORDS = (
    "chrom", "firefox", "webkit", "safari", "edge", "headless", "browser",
    "electron", "playwright", "puppeteer", "node", "server", "http",
    "python", "java", "deno", "uvicorn", "gunicorn", "next", "vite",
    "webpack",
)

# --- rule (d): a protect/exclude-named var assigned a literal port list.
_PROTECT_NAME_RE = re.compile(
    r"\b(protect|exclude|reserved|except|skip|allow|keep|whitelist|allowlist)\w*",
    re.IGNORECASE,
)
_PORT_LIST_RE = re.compile(r"\d{2,5}(?:\s*[, ]\s*\d{2,5}){1,}")

# Files a directory walk restricts to (an explicitly named file is always
# scanned regardless of this list — the caller already chose it).
_SHELL_EXTS = (".sh", ".bash", ".zsh")
_YAML_EXTS = (".yml", ".yaml")
_SKIP_DIRS = {".git", "node_modules"}


def _matches_scan_filter(name: str) -> bool:
    lower = name.lower()
    if lower.endswith(_SHELL_EXTS) or lower.endswith(_YAML_EXTS):
        return True
    if lower in ("makefile", "package.json"):
        return True
    return False


def _iter_targets(paths: list[str]) -> tuple[list[str], list[str]]:
    """Resolve CLI paths to a flat file list. Returns (files, errors)."""
    files: list[str] = []
    errors: list[str] = []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
                for fn in filenames:
                    if _matches_scan_filter(fn):
                        files.append(os.path.join(dirpath, fn))
        else:
            errors.append(f"reaper_lint: path not found: {p} (fail closed)")
    return files, errors


def _is_escaped(lines: list[str], idx: int) -> bool:
    if ESCAPE_MARKER in lines[idx]:
        return True
    if idx > 0 and ESCAPE_MARKER in lines[idx - 1]:
        return True
    return False


def _scan_text(lines: list[str]) -> list[tuple[int, str, str]]:
    """Return [(1-based line, RULE, message), ...] for one file's lines,
    already excluding escaped hits."""
    findings: list[tuple[int, str, str]] = []
    file_has_kill = any(_KILL_WORD_RE.search(line) for line in lines)

    for i, line in enumerate(lines):
        # (a) lsof -ti/-it/-t -i without -sTCP:LISTEN, feeding a nearby kill.
        if _LSOF_TI_RE.search(line) and not _STCP_LISTEN_RE.search(line):
            window = lines[i:i + 3]
            if any(_KILL_WORD_RE.search(w) for w in window):
                if not _is_escaped(lines, i):
                    findings.append((
                        i + 1, "LSOF_NO_LISTEN",
                        "lsof -ti/-it/-t -i feeds a kill without -sTCP:LISTEN "
                        "-- matches a connected client, not only the listener "
                        "(use `lsof -t -iTCP:PORT -sTCP:LISTEN`)",
                    ))

        # (b) a seq range feeding a kill loop within the next few lines.
        if _SEQ_RANGE_RE.search(line):
            window = lines[i:i + 6]
            if any(_KILL_WORD_RE.search(w) for w in window):
                if not _is_escaped(lines, i):
                    findings.append((
                        i + 1, "RANGE_KILL",
                        "seq-driven port-range loop feeds a kill -- reaps every "
                        "parallel lane's own port inside the range, not one "
                        "owned port",
                    ))

        # (c) pkill -f / killall on a browser/server-shaped pattern.
        if _PKILL_RE.search(line):
            lowered = line.lower()
            if any(kw in lowered for kw in _BROAD_KEYWORDS):
                if not _is_escaped(lines, i):
                    findings.append((
                        i + 1, "BROAD_PKILL",
                        "pkill/killall targets a browser- or server-name "
                        "pattern -- reaps a sibling lane's identically named "
                        "process, not only an orphan",
                    ))

        # (d) a protect/exclude-named var holding a literal port list.
        if (file_has_kill and _PROTECT_NAME_RE.search(line)
                and _PORT_LIST_RE.search(line)):
            if not _is_escaped(lines, i):
                findings.append((
                    i + 1, "HARDCODED_PORTS",
                    "hard-coded protected-port list in a kill script -- goes "
                    "stale the moment an operator adds a real serving port; "
                    "source exclusions from operator config instead",
                ))

    return findings


def run_gate(paths: list[str]) -> tuple[int, list[str]]:
    """Scan `paths` (files and/or directories); return (exit_code, lines)."""
    files, errors = _iter_targets(paths)
    if errors:
        return ERROR, errors

    all_findings: list[tuple[str, int, str, str]] = []
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            return ERROR, [f"reaper_lint: cannot read {f} (fail closed): {exc}"]
        lines = text.splitlines()
        for lineno, rule, message in _scan_text(lines):
            all_findings.append((f, lineno, rule, message))

    if all_findings:
        out = [
            f"{f}:{lineno}: [{rule}] {message}"
            for f, lineno, rule, message in all_findings
        ]
        out.append(f"reaper_lint: {len(all_findings)} finding(s) (see above)")
        return FAIL, out

    return OK, [f"reaper_lint: ok ({len(files)} file(s) scanned)"]


# ---------------------------------------------------------------------------
# Selftest — planted RED/GREEN cases, no network, no fixture repo checked in.
# ---------------------------------------------------------------------------

def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _selftest() -> int:
    failures: list[str] = []

    def check(name: str, rc: int, lines: list[str], want_rc: int,
              must_have: tuple[str, ...] = (), must_not_have: tuple[str, ...] = ()) -> None:
        joined = "\n".join(lines)
        ok = (rc == want_rc
              and all(needle in joined for needle in must_have)
              and all(needle not in joined for needle in must_not_have))
        if not ok:
            failures.append(f"{name}: rc={rc} (want {want_rc}); output={joined!r}")

    with tempfile.TemporaryDirectory() as tmp:
        # 1) clean shell script -> OK.
        clean = os.path.join(tmp, "clean.sh")
        _write(clean, "#!/usr/bin/env bash\necho hello\n")
        rc, lines = run_gate([clean])
        check("clean-script-ok", rc, lines, OK)

        # 2) lsof -ti feeding kill with no -sTCP:LISTEN -> FAIL rule (a).
        bad_lsof = os.path.join(tmp, "bad_lsof.sh")
        _write(bad_lsof, "#!/usr/bin/env bash\nkill -9 $(lsof -ti :$port)\n")
        rc, lines = run_gate([bad_lsof])
        check("lsof-no-listen-fires", rc, lines, FAIL, must_have=("LSOF_NO_LISTEN",))

        # 2b) same shape but WITH -sTCP:LISTEN -> OK (paired negative).
        good_lsof = os.path.join(tmp, "good_lsof.sh")
        _write(good_lsof, "#!/usr/bin/env bash\nkill -9 $(lsof -t -iTCP:$port -sTCP:LISTEN)\n")
        rc, lines = run_gate([good_lsof])
        check("lsof-with-listen-ok", rc, lines, OK, must_not_have=("LSOF_NO_LISTEN",))

        # 3) seq range feeding a kill loop -> FAIL rule (b).
        range_kill = os.path.join(tmp, "range_kill.sh")
        _write(
            range_kill,
            "#!/usr/bin/env bash\n"
            "for port in $(seq 3110 3200); do\n"
            "  kill -9 $(lsof -t -iTCP:$port -sTCP:LISTEN)\n"
            "done\n",
        )
        rc, lines = run_gate([range_kill])
        check("range-kill-fires", rc, lines, FAIL, must_have=("RANGE_KILL",))

        # 4) pkill -f on a browser pattern -> FAIL rule (c).
        pkill_browser = os.path.join(tmp, "pkill_browser.sh")
        _write(pkill_browser, "#!/usr/bin/env bash\npkill -f 'chromium.*headless'\n")
        rc, lines = run_gate([pkill_browser])
        check("broad-pkill-fires", rc, lines, FAIL, must_have=("BROAD_PKILL",))

        # 5) hard-coded protected-port list in a file that also kills -> FAIL rule (d).
        hardcoded = os.path.join(tmp, "hardcoded.sh")
        _write(
            hardcoded,
            "#!/usr/bin/env bash\n"
            "PROTECTED_PORTS=(3000 8080 5432)\n"
            "kill -9 $(lsof -t -iTCP:$port -sTCP:LISTEN)\n",
        )
        rc, lines = run_gate([hardcoded])
        check("hardcoded-ports-fires", rc, lines, FAIL, must_have=("HARDCODED_PORTS",))

        # 6) inline escape comment suppresses an otherwise-firing line -> OK.
        escaped = os.path.join(tmp, "escaped.sh")
        _write(
            escaped,
            "#!/usr/bin/env bash\n"
            "# reaper-lint: allow only-lane-owned port, verified by caller\n"
            "kill -9 $(lsof -ti :$port)\n",
        )
        rc, lines = run_gate([escaped])
        check("escape-comment-suppresses", rc, lines, OK)

        # 7) directory scan restricts to shell/Makefile/package.json/YAML;
        #    a decoy .txt with the same dangerous text is skipped in dir
        #    mode but would still fire if named explicitly (case 2 above
        #    already proves the explicit-file path; this proves the filter).
        scandir = os.path.join(tmp, "scandir")
        _write(os.path.join(scandir, "reap.sh"), "#!/usr/bin/env bash\nkill -9 $(lsof -ti :$port)\n")
        _write(os.path.join(scandir, "notes.txt"), "kill -9 $(lsof -ti :$port)\n")
        rc, lines = run_gate([scandir])
        check(
            "dir-scan-filters-extensions", rc, lines, FAIL,
            must_have=("reap.sh", "LSOF_NO_LISTEN"),
            must_not_have=("notes.txt",),
        )

        # 8) package.json scripts value scanned as plain text when named
        #    explicitly -> FAIL rule (b) (embedded shell inside a JSON string).
        pkg = os.path.join(tmp, "package.json")
        _write(
            pkg,
            '{\n  "scripts": {\n'
            '    "reap": "for p in $(seq 3110 3200); do kill -9 $p; done"\n'
            "  }\n}\n",
        )
        rc, lines = run_gate([pkg])
        check("package-json-scripts-fires", rc, lines, FAIL, must_have=("RANGE_KILL",))

        # 9) a named path that does not exist -> ERROR (fail closed).
        missing = os.path.join(tmp, "does-not-exist.sh")
        rc, lines = run_gate([missing])
        check("missing-path-errors", rc, lines, ERROR)

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELFTEST OK: 9/9 cases passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flag bulk/fleet-wide process-reaper patterns in shell/"
                     "Makefile/package.json-script/CI-YAML text."
    )
    parser.add_argument("paths", nargs="*", help="files and/or directories to scan")
    parser.add_argument("--selftest", action="store_true", help="run the built-in selftest and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.paths:
        parser.error("at least one file or directory is required")
        return ERROR  # pragma: no cover — parser.error() already exits(2)

    code, lines = run_gate(args.paths)
    out = sys.stdout if code == OK else sys.stderr
    for line in lines:
        print(line, file=out)
    return code


if __name__ == "__main__":
    sys.exit(main())
