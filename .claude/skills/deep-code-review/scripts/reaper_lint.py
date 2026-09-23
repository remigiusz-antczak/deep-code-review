#!/usr/bin/env python3
"""reaper_lint.py — a heuristic, opt-in lint that flags a bulk/fleet-wide
process-reaper pattern in a cleanup script before it ships, instead of after it
takes down every parallel agent lane sharing the host.

WHAT THIS IS (AND IS NOT)
--------------------------
A heuristic lint over text, not a proof. It is not a shell, Makefile, YAML, or
JSON parser: it approximates shell quoting and word splitting to find a small
set of known-dangerous shapes. False negatives are possible (a command built
from variables, `eval`, a helper function in another file, a language other
than shell); false positives are possible and are silenced per line with the
allow marker below. A clean run means "none of the shapes below was found",
never "this script only kills what it owns".

WHY THIS EXISTS
----------------
`references/concurrency-shared-state.md`'s "Terminating work you own" section
documents the doctrine: a reaper may only kill processes it can prove are its
own or orphaned (parent PID 1, a cwd inside the caller's own worktree, or a
PID file the caller wrote) and must select the LISTENER only
(`lsof -t -iTCP:PORT -sTCP:LISTEN`), never a bare port or name/command-line
match. That is prose an agent may or may not follow. This script is a
mechanism for the concrete shapes of that bug class (issue #1101).

WHAT IT SCANS
--------------
Each argument may be a file (scanned regardless of its name or extension; the
caller explicitly chose it) or a directory, walked recursively (`.git` and
`node_modules` are skipped) and restricted to:
  * `*.sh`, `*.bash`, `*.zsh`, `*.mk`, `*.yml`, `*.yaml`;
  * files named `Makefile`, `makefile`, `GNUmakefile`, `justfile`,
    `.justfile` (any case), or `package.json`;
  * extensionless files whose first line is a `#!` shebang naming a shell
    (`sh`, `bash`, `zsh`, `dash`, `ksh`, `ash`) or `make`.

Before matching, each file is preprocessed: in a `*.json` file, a
`"key": "value"` line is replaced by its decoded string value (a
`package.json` script is shell text); an unquoted `#` comment is stripped;
and a line ending in `\\`, `|`, `&&`, or `||` is joined with the next line
(a YAML block-scalar header such as `run: |` is not joined). Findings are
reported at the first physical line of the joined logical line.

RULES (fail on any match not carrying the allow marker)
--------------------------------------------------------
  LSOF_NO_LISTEN  an `lsof` call with a terse flag (`t` anywhere in a short
                  flag cluster: `-t`, `-ti`, `-nti`, `-Pti`, `-tiTCP:3000`)
                  and any `-i` selector, in either order, whose state filter
                  is not exactly `-sTCP:LISTEN` (or `-s TCP:LISTEN`), when
                  its output reaches a `kill`: on the same logical line,
                  within the next 2 logical lines, or through a variable
                  (`pids=$(lsof ...)`, `for pid in $(lsof ...)`,
                  `lsof ... | while read pid`) that a later line of the same
                  file passes to `kill`. Matches a connected client, not
                  only the listener.
  RANGE_KILL      a port range feeding a `kill` on the same logical line or
                  within the next 5: `seq [-w] A B` / `seq A STEP B`, a brace
                  range `{A..B}`, or `for ((v=A; v<=B; ...))`, where both
                  bounds are port-like (1024-65535). Small counters such as
                  `seq 1 3` are ignored.
  BROAD_PKILL     `pkill` (with or without `-f`), `killall`, or a `pgrep`
                  whose output reaches a `kill`, whose PATTERN argument (not
                  its flags, not a trailing comment) contains, as a whole
                  word, a browser/server/runtime name (chrome, chromium,
                  firefox, webkit, safari, edge, headless, browser, electron,
                  playwright, puppeteer, node, server, http, python, java,
                  deno, uvicorn, gunicorn, next, vite, webpack). A pattern
                  containing a `$` expansion is treated as caller-scoped
                  (for example `"$LANE_ID/.../vite"`) and not flagged.
  PS_GREP_KILL    a `ps ... | grep <PATTERN>` pipeline whose PATTERN matches
                  the same word list, when its output reaches a `kill` (same
                  line, next 2 lines, or a tracked variable).
  FUSER_KILL      `fuser` with `-k` and a `<port>/tcp` or `<port>/udp`
                  operand: kills every process using the port, clients
                  included.
  KILL_PORT       the `kill-port` command (bare, or via `npx`, `pnpm dlx`,
                  `yarn dlx`, `bunx`): kills whatever holds the port.
  HARDCODED_PORTS a protect/exclude/reserved/except/skip/allow/keep/
                  whitelist/allowlist/ignore/safe-named variable assigned
                  (`NAME=`, `NAME:=`, `NAME+=`, `NAME?=`, optionally after
                  `export`/`local`/`readonly`/`declare`) a value holding 2+
                  port-like numbers (1024-65535), including a multi-line
                  `NAME=(` ... `)` array, in a file that also kills. An
                  operator-owned exclusion list living as a script literal
                  goes stale the moment a new backend is added.

ALLOW MARKER
-------------
A finding is suppressed only when a physical line of the SAME logical line
carries the exact token `# reaper-lint: allow` followed by a non-empty reason
(`kill "$(cat lane.pid)"  # reaper-lint: allow lane-owned PID file`). A
marker on the line above, a marker without a reason, or a near-miss spelling
(`allowance`, `allow:`) suppresses nothing. The reason's content is not
validated; review judges whether it holds.

EXIT CODES (fail-closed)
-------------------------
  0  no unsuppressed finding in any scanned file (including "nothing matched
     the scan filters").
  1  at least one unsuppressed finding (each printed as `path:line: [RULE]
     message`), and no error.
  2  the scan could not be completed: a named path does not exist or is
     neither a file nor a directory, a directory could not be listed during
     the walk, a file could not be read, or a file is not decodable as UTF-8
     text (invalid bytes, or NUL bytes such as UTF-16). Findings from files
     that were scanned are still printed; the exit code is 2, never a silent
     pass.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import tempfile

OK = 0
FAIL = 1
ERROR = 2

# ---------------------------------------------------------------------------
# Scan filters.
# ---------------------------------------------------------------------------
_SCAN_EXTS = (".sh", ".bash", ".zsh", ".mk", ".yml", ".yaml")
_SCAN_NAMES = ("makefile", "gnumakefile", "justfile", ".justfile", "package.json")
_SKIP_DIRS = {".git", "node_modules"}
_SHEBANG_RE = re.compile(
    r"^#!\s*\S*?(?:/|\benv\s+(?:-\S+\s+)*)(?:(?:ba|z|da|k|a)?sh|make)\b"
)

# ---------------------------------------------------------------------------
# Shared patterns.
# ---------------------------------------------------------------------------
_ALLOW_RE = re.compile(r"#\s*reaper-lint: allow[ \t]+\S")
_KILL_WORD_RE = re.compile(r"\bkill\b")
_FILE_KILLS_RE = re.compile(r"\b(?:kill|pkill|killall)\b|\bfuser\b[^\n]*\s-\w*k|\bkill-port\b")
_BROAD_WORD_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:chrome|chromium|firefox|webkit|safari|edge|headless|"
    r"browser|electron|playwright|puppeteer|node|server|http|python|java|deno|"
    r"uvicorn|gunicorn|next|vite|webpack)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_YAML_BLOCK_HEADER_RE = re.compile(r":\s*[|>][-+0-9]*\s*$")
_JSON_PAIR_RE = re.compile(r'^\s*"(?:[^"\\]|\\.)*"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$')

# Variable capture from a selector line.
_ASSIGN_VAR_RE = re.compile(
    r"(?:^|[\s;&(])(?:(?:local|export|readonly)\s+|(?:declare|typeset)\s+(?:-\w+\s+)*)?"
    r"([A-Za-z_]\w*)=[\"']?(?:\$\(|`)"
)
_FOR_VAR_RE = re.compile(r"\bfor\s+([A-Za-z_]\w*)\s+in\b")
_WHILE_READ_RE = re.compile(r"\bwhile\s+(?:IFS=\S*\s+)?read\s+(?:-\w+\s+)*([A-Za-z_]\w*(?:\s+[A-Za-z_]\w*)*)")

# Port ranges (rule RANGE_KILL).
_SEQ_RE = re.compile(r"\bseq(?:\s+-[A-Za-z]+)*\s+(\d+)\s+(\d+)(?:\s+(\d+))?\b")
_BRACE_RE = re.compile(r"\{(\d+)\.\.(\d+)(?:\.\.\d+)?\}")
_CFOR_RE = re.compile(r"\(\(\s*[A-Za-z_]\w*\s*=\s*(\d+)\s*;\s*[A-Za-z_]\w*\s*[<>]=?\s*(\d+)")

# Hard-coded protected-port list (rule HARDCODED_PORTS).
_PROTECT_ASSIGN_RE = re.compile(
    r"^\s*(?:(?:local|export|readonly)\s+|(?:declare|typeset)\s+(?:-\w+\s+)*)?"
    r"([A-Za-z_]\w*)\s*(?:::|[:+?])?=\s*(.*)$"
)
_PROTECT_NAME_RE = re.compile(
    r"(?:protect|exclude|reserved|except|skip|allow|keep|whitelist|allowlist|ignore|safe)",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"(?<![\w.])(\d{4,5})(?![\w.])")

# lsof short options that take a required / optional argument (the rest of the
# cluster, or for a required one the next token when the cluster ends there).
_LSOF_REQ_ARG = set("AcdDekmpu")
_LSOF_OPT_ARG = set("FgorSTxz")

# pkill / killall / pgrep options that consume the next token as an argument.
_PKILL_ARG_OPTS = set("PgGuUtsFJ")
# A signal given as an option (`-TERM`, `-SIGKILL`); single uppercase letters
# such as `-P` / `-U` / `-F` are options, not signals.
_SIGNAL_NAME_RE = re.compile(r"(?:SIG)?[A-Z]{2,}[0-9]*")
_KILLALL_ARG_OPTS = set("utcyon")
_LONG_ARG_OPTS = {"signal", "pidfile", "parent", "group", "euid", "uid", "terminal", "session"}

_MSG = {
    "LSOF_NO_LISTEN": (
        "lsof -t with an -i selector feeds a kill without -sTCP:LISTEN -- "
        "matches a connected client, not only the listener (use "
        "`lsof -t -iTCP:PORT -sTCP:LISTEN`)"
    ),
    "RANGE_KILL": (
        "port-range loop feeds a kill -- reaps every parallel lane's own port "
        "inside the range, not one owned port"
    ),
    "BROAD_PKILL": (
        "pkill/killall/pgrep pattern names a browser/server/runtime -- reaps a "
        "sibling lane's identically named process, not only an orphan"
    ),
    "PS_GREP_KILL": (
        "ps | grep name match feeds a kill -- reaps a sibling lane's "
        "identically named process, not only an orphan"
    ),
    "FUSER_KILL": (
        "fuser -k on a port kills every process using it, connected clients "
        "included -- select the owned listener PID instead"
    ),
    "KILL_PORT": (
        "kill-port kills whatever holds the port, including another lane's "
        "server -- kill a PID you can prove you own instead"
    ),
    "HARDCODED_PORTS": (
        "hard-coded protected-port list in a kill script -- goes stale the "
        "moment an operator adds a real serving port; source exclusions from "
        "operator config instead"
    ),
}


# ---------------------------------------------------------------------------
# File discovery.
# ---------------------------------------------------------------------------

def _has_shell_shebang(path: str) -> bool:
    """True when an extensionless file starts with a shell/make shebang.

    An unreadable file returns True so the read step reports it (fail closed)
    instead of the walk silently dropping it.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(256)
    except OSError:
        return True
    first = head.split(b"\n", 1)[0].decode("utf-8", errors="replace")
    return bool(_SHEBANG_RE.search(first))


def _matches_scan_filter(dirpath: str, name: str) -> bool:
    """True when a file found by a directory walk should be scanned."""
    lower = name.lower()
    if lower.endswith(_SCAN_EXTS) or lower in _SCAN_NAMES:
        return True
    if "." not in name:
        return _has_shell_shebang(os.path.join(dirpath, name))
    return False


def _iter_targets(paths: list[str]) -> tuple[list[str], list[str]]:
    """Resolve CLI paths to a flat file list. Returns (files, errors).

    A named path that is missing, or a directory the walk cannot list, is an
    error (the caller exits 2), never a silent skip.
    """
    files: list[str] = []
    errors: list[str] = []

    def on_walk_error(exc: OSError) -> None:
        errors.append(
            f"reaper_lint: cannot list {getattr(exc, 'filename', '?')} "
            f"(fail closed): {exc.strerror or exc}"
        )

    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p, onerror=on_walk_error):
                dirnames[:] = sorted(d for d in dirnames if d not in _SKIP_DIRS)
                for fn in sorted(filenames):
                    if _matches_scan_filter(dirpath, fn):
                        files.append(os.path.join(dirpath, fn))
        else:
            errors.append(f"reaper_lint: path not found: {p} (fail closed)")
    return files, errors


def _read_text(path: str) -> str:
    """Read `path` as UTF-8 text; raise ValueError when it is not text."""
    with open(path, "rb") as fh:
        data = fh.read()
    if b"\x00" in data:
        raise ValueError("contains NUL bytes (UTF-16 or binary?); cannot scan as UTF-8 text")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"not valid UTF-8 ({exc.reason} at byte {exc.start})") from None


# ---------------------------------------------------------------------------
# Preprocessing: comments, continuations, logical lines.
# ---------------------------------------------------------------------------

def _strip_comment(line: str) -> str:
    """Drop an unquoted shell-style `#` comment (a `#` at a word start)."""
    in_sq = in_dq = False
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if in_sq:
            if ch == "'":
                in_sq = False
        elif ch == "\\":
            i += 2
            continue
        elif in_dq:
            if ch == '"':
                in_dq = False
        elif ch == "'":
            in_sq = True
        elif ch == '"':
            in_dq = True
        elif ch == "#" and (i == 0 or line[i - 1] in " \t;&|()"):
            return line[:i]
        i += 1
    return line


def _logical_lines(raw: list[str], is_json: bool) -> list[tuple[int, int, str]]:
    """Return [(first_idx, last_idx, code_text)] — comment-free, joined lines."""
    code: list[str] = []
    for line in raw:
        text = line
        if is_json:
            m = _JSON_PAIR_RE.match(line)
            if m:
                try:
                    text = json.loads('"' + m.group(1) + '"')
                except ValueError:
                    text = m.group(1)
        code.append(_strip_comment(text).rstrip())

    out: list[tuple[int, int, str]] = []
    i = 0
    while i < len(code):
        start, parts = i, []
        while True:
            part = code[i]
            if part.endswith("\\") and not part.endswith("\\\\"):
                parts.append(part[:-1])
                cont = True
            elif part.endswith(("|", "&&")) and not _YAML_BLOCK_HEADER_RE.search(part):
                parts.append(part)
                cont = True
            else:
                parts.append(part)
                cont = False
            if cont and i + 1 < len(code):
                i += 1
                continue
            break
        out.append((start, i, " ".join(p.strip() for p in parts)))
        i += 1
    return out


def _segments(text: str) -> list[str]:
    """Split a logical line into command segments at unquoted `| ; & ( )`,
    backticks, and `$(` (also inside double quotes). Quotes stay in the text.
    """
    segs: list[str] = []
    buf: list[str] = []
    stack: list[str] = []  # 'sq' | 'dq' | 'sub'

    def cut() -> None:
        segs.append("".join(buf))
        buf.clear()

    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        top = stack[-1] if stack else ""
        if top == "sq":
            buf.append(ch)
            if ch == "'":
                stack.pop()
        elif ch == "\\" and i + 1 < n:
            buf.append(text[i:i + 2])
            i += 2
            continue
        elif ch == "$" and i + 1 < n and text[i + 1] == "(" and text[i + 2:i + 3] != "(":
            stack.append("sub")
            cut()
            i += 2
            continue
        elif ch == "`":
            cut()
        elif top == "dq":
            buf.append(ch)
            if ch == '"':
                stack.pop()
        elif ch == "'":
            stack.append("sq")
            buf.append(ch)
        elif ch == '"':
            stack.append("dq")
            buf.append(ch)
        elif ch == ")" and top == "sub":
            stack.pop()
            cut()
        elif ch in "|;&()":
            cut()
        else:
            buf.append(ch)
        i += 1
    cut()
    return [s for s in segs if s.strip()]


def _tokens(segment: str) -> list[str]:
    """Shell-like word split; falls back to whitespace split on bad quoting."""
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return [t.strip("\"'") for t in segment.split()]


def _command_at(tokens: list[str], names: tuple[str, ...]) -> int:
    """Index of the first token whose basename is one of `names`, else -1."""
    for idx, tok in enumerate(tokens):
        if tok.rsplit("/", 1)[-1] in names:
            return idx
    return -1


# ---------------------------------------------------------------------------
# Per-command classifiers.
# ---------------------------------------------------------------------------

def _lsof_unsafe(args: list[str]) -> bool:
    """True for `lsof` args with a terse flag and an -i selector but no
    listener-only state filter (`-sTCP:LISTEN`)."""
    has_t = has_i = listen_only = False
    j = 0
    while j < len(args):
        tok = args[j]
        j += 1
        if not tok.startswith("-") or tok.startswith("--") or tok == "-":
            continue
        body = tok[1:]
        for k, ch in enumerate(body):
            rest = body[k + 1:]
            if ch == "i":
                has_i = True
                break
            if ch == "s":
                spec = rest
                if not spec and j < len(args) and ":" in args[j] and not args[j].startswith("-"):
                    spec = args[j]
                    j += 1
                if spec:
                    proto, _, states = spec.partition(":")
                    names = {s.strip().upper() for s in states.split(",") if s.strip()}
                    if proto.upper() == "TCP" and names == {"LISTEN"}:
                        listen_only = True
                break
            if ch == "t":
                has_t = True
                continue
            if ch in _LSOF_REQ_ARG:
                if not rest:
                    j += 1
                break
            if ch in _LSOF_OPT_ARG:
                break
    return has_t and has_i and not listen_only


def _pattern_args(args: list[str], arg_opts: set[str]) -> list[str]:
    """Non-option operands of pkill/killall/pgrep, skipping option arguments."""
    out: list[str] = []
    j = 0
    while j < len(args):
        tok = args[j]
        j += 1
        if tok == "--":
            out.extend(args[j:])
            break
        if tok.startswith("--"):
            if "=" not in tok and tok[2:] in _LONG_ARG_OPTS:
                j += 1
            continue
        if tok.startswith("-") and len(tok) > 1:
            body = tok[1:]
            if body.isdigit() or _SIGNAL_NAME_RE.fullmatch(body):
                continue  # a signal: -9, -TERM, -SIGHUP, -USR1
            for k, ch in enumerate(body):
                if ch in arg_opts:
                    if k == len(body) - 1:
                        j += 1
                    break
            continue
        out.append(tok)
    return out


def _broad(patterns: list[str]) -> bool:
    """True when a pattern names a broad browser/server word and is not
    scoped by a `$` expansion."""
    # `[c]hrome` (the grep-avoids-itself idiom) still names chrome.
    unbracketed = (re.sub(r"\[(\w)\]", r"\1", p) for p in patterns)
    return any("$" not in p and _BROAD_WORD_RE.search(p) for p in unbracketed)


def _grep_patterns(args: list[str]) -> list[str]:
    """The PATTERN operand(s) of a grep invocation; empty for `grep -v`."""
    pats: list[str] = []
    j = 0
    positional_done = False
    while j < len(args):
        tok = args[j]
        j += 1
        if tok.startswith("-") and len(tok) > 1:
            if "v" in tok[1:] and not tok.startswith("--"):
                return []
            if tok in ("-e", "--regexp") and j < len(args):
                pats.append(args[j])
                j += 1
                positional_done = True
            elif tok in ("-f", "-m", "-A", "-B", "-C"):
                j += 1
            continue
        if not positional_done:
            pats.append(tok)
            positional_done = True
    return pats


def _classify(text: str) -> tuple[list[str], list[str]]:
    """Classify one logical line. Returns (direct_rules, selector_rules):
    direct rules are kills in themselves; selector rules pick PIDs and are a
    finding only when their output reaches a kill."""
    direct: list[str] = []
    selectors: list[str] = []
    saw_ps = False
    for seg in _segments(text):
        toks = _tokens(seg)
        if not toks:
            continue
        idx = _command_at(toks, ("lsof",))
        if idx >= 0 and _lsof_unsafe(toks[idx + 1:]):
            selectors.append("LSOF_NO_LISTEN")
        idx = _command_at(toks, ("pkill", "killall"))
        if idx >= 0:
            name = toks[idx].rsplit("/", 1)[-1]
            args = toks[idx + 1:]
            if name == "pkill":
                pats = _pattern_args(args, _PKILL_ARG_OPTS)[:1]
            else:
                pats = _pattern_args(args, _KILLALL_ARG_OPTS)
            if _broad(pats):
                direct.append("BROAD_PKILL")
        idx = _command_at(toks, ("pgrep",))
        if idx >= 0 and _broad(_pattern_args(toks[idx + 1:], _PKILL_ARG_OPTS)[:1]):
            selectors.append("BROAD_PKILL")
        if _command_at(toks, ("ps",)) >= 0:
            saw_ps = True
        idx = _command_at(toks, ("grep", "egrep", "fgrep"))
        if saw_ps and idx >= 0 and _broad(_grep_patterns(toks[idx + 1:])):
            selectors.append("PS_GREP_KILL")
        idx = _command_at(toks, ("fuser",))
        if idx >= 0:
            args = toks[idx + 1:]
            has_k = any(a.startswith("-") and not a.startswith("--") and "k" in a for a in args)
            has_port = any(re.search(r"/(?:tcp|udp)$", a) for a in args) or any(
                args[k] == "-n" and args[k + 1] in ("tcp", "udp") for k in range(len(args) - 1)
            )
            if has_k and has_port:
                direct.append("FUSER_KILL")
        idx = _command_at(toks, ("kill-port",))
        if idx >= 0:
            before = {t.rsplit("/", 1)[-1] for t in toks[:idx]}
            installing = bool(before & {"npm", "yarn", "pnpm", "bun"}) and bool(
                before & {"install", "i", "add", "remove", "uninstall", "rm"}
            )
            if not installing:
                direct.append("KILL_PORT")
    return direct, selectors


def _captured_vars(text: str) -> list[str]:
    """Variable names a selector line's output lands in."""
    names: list[str] = []
    m = _ASSIGN_VAR_RE.search(text)
    if m:
        names.append(m.group(1))
    m = _FOR_VAR_RE.search(text)
    if m:
        names.append(m.group(1))
    m = _WHILE_READ_RE.search(text)
    if m:
        names.extend(m.group(1).split())
    return names


def _range_is_portlike(text: str) -> bool:
    """True when the line carries a seq/brace/C-style range whose bounds are
    both port-like (1024-65535)."""
    bounds: list[tuple[int, int]] = []
    for m in _SEQ_RE.finditer(text):
        nums = [int(g) for g in m.groups() if g is not None]
        bounds.append((nums[0], nums[-1]))
    for m in _BRACE_RE.finditer(text):
        bounds.append((int(m.group(1)), int(m.group(2))))
    for m in _CFOR_RE.finditer(text):
        bounds.append((int(m.group(1)), int(m.group(2))))
    return any(1024 <= lo <= 65535 and 1024 <= hi <= 65535 for lo, hi in bounds)


def _portlike_count(value: str) -> int:
    return sum(1 for m in _NUMBER_RE.finditer(value) if 1024 <= int(m.group(1)) <= 65535)


# ---------------------------------------------------------------------------
# Scan.
# ---------------------------------------------------------------------------

def _scan_text(raw: list[str], is_json: bool = False) -> list[tuple[int, str, str]]:
    """Return [(1-based line, RULE, message), ...] for one file's lines,
    excluding findings whose logical line carries the allow marker."""
    logical = _logical_lines(raw, is_json)
    texts = [t for _, _, t in logical]
    file_kills = any(_FILE_KILLS_RE.search(t) for t in texts)
    hits: dict[tuple[int, str], None] = {}

    def add(li: int, rule: str) -> None:
        start, end, _ = logical[li]
        if any(_ALLOW_RE.search(raw[k]) for k in range(start, end + 1)):
            return
        hits.setdefault((li, rule), None)

    for li, text in enumerate(texts):
        if not text.strip():
            continue
        direct, selectors = _classify(text)
        for rule in direct:
            add(li, rule)
        if selectors:
            reaches_kill = any(_KILL_WORD_RE.search(t) for t in texts[li:li + 3])
            if not reaches_kill:
                for var in _captured_vars(text):
                    use = re.compile(r"\$\{?" + re.escape(var) + r"\b")
                    if any(_KILL_WORD_RE.search(t) and use.search(t) for t in texts[li + 1:]):
                        reaches_kill = True
                        break
            if reaches_kill:
                for rule in selectors:
                    add(li, rule)

        if _range_is_portlike(text) and any(_KILL_WORD_RE.search(t) for t in texts[li:li + 6]):
            add(li, "RANGE_KILL")

        if file_kills:
            m = _PROTECT_ASSIGN_RE.match(text)
            if m and _PROTECT_NAME_RE.search(m.group(1)):
                value = m.group(2)
                if value.lstrip().startswith("(") and ")" not in value:
                    for nxt in texts[li + 1:]:
                        value += " " + nxt
                        if ")" in nxt:
                            break
                if _portlike_count(value) >= 2:
                    add(li, "HARDCODED_PORTS")

    return [(logical[li][0] + 1, rule, _MSG[rule]) for li, rule in hits]


def run_gate(paths: list[str]) -> tuple[int, list[str]]:
    """Scan `paths` (files and/or directories); return (exit_code, lines).

    Exit code: OK (0) when nothing was found, FAIL (1) on any unsuppressed
    finding, ERROR (2) when any path, directory, or file could not be scanned
    (findings from scanned files are still included in the output lines).
    """
    files, errors = _iter_targets(paths)
    all_findings: list[tuple[str, int, str, str]] = []
    for f in files:
        try:
            text = _read_text(f)
        except OSError as exc:
            errors.append(f"reaper_lint: cannot read {f} (fail closed): {exc}")
            continue
        except ValueError as exc:
            errors.append(f"reaper_lint: cannot decode {f} (fail closed): {exc}")
            continue
        is_json = f.lower().endswith(".json")
        for lineno, rule, message in _scan_text(text.splitlines(), is_json):
            all_findings.append((f, lineno, rule, message))

    out = [f"{f}:{lineno}: [{rule}] {message}" for f, lineno, rule, message in all_findings]
    if errors:
        return ERROR, out + errors
    if all_findings:
        out.append(f"reaper_lint: {len(all_findings)} finding(s) (see above)")
        return FAIL, out
    return OK, [f"reaper_lint: ok ({len(files)} file(s) scanned)"]


# ---------------------------------------------------------------------------
# Selftest — planted RED/GREEN cases, no network, no fixture repo checked in.
# ---------------------------------------------------------------------------

def _write(path: str, content: str | bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = content if isinstance(content, bytes) else content.encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(data)


# (name, file name, content, expected exit code, rule that must appear or "")
_SH = "#!/usr/bin/env bash\n"
_CASES: tuple[tuple[str, str, str, int, str], ...] = (
    ("clean-script-ok", "clean.sh", _SH + "echo hello\n", OK, ""),
    # LSOF_NO_LISTEN: every flag order and cluster fires.
    ("lsof-ti-fires", "a.sh", _SH + "kill -9 $(lsof -ti :$port)\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-t-iTCP-fires", "a.sh", "lsof -t -iTCP:3000 | xargs kill\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-tiTCP-fires", "a.sh", "lsof -tiTCP:3000 | xargs kill\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-nti-fires", "a.sh", "lsof -nti :3000 | xargs kill\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-Pti-fires", "a.sh", "lsof -Pti :3000 | xargs kill\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-i-then-t-fires", "a.sh", "lsof -i :3000 -t | xargs kill\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-t-i-attached-fires", "a.sh", "lsof -t -i:3000 | xargs kill\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-established-fires", "a.sh", "lsof -ti :3000 -sTCP:ESTABLISHED | xargs kill\n",
     FAIL, "LSOF_NO_LISTEN"),
    ("lsof-listen-in-comment-fires", "a.sh",
     "lsof -ti :3000 | xargs -r kill -9  # -sTCP:LISTEN would be nice\n", FAIL, "LSOF_NO_LISTEN"),
    ("lsof-continuation-fires", "a.sh", "lsof -ti :3000 \\\n  | xargs \\\n  -r \\\n  kill -9\n",
     FAIL, "LSOF_NO_LISTEN"),
    ("lsof-var-tracked-fires", "a.sh", "pids=$(lsof -ti :3000)\n\n\n\nkill $pids\n",
     FAIL, "LSOF_NO_LISTEN"),
    ("lsof-for-var-fires", "a.sh",
     "for pid in $(lsof -ti :3000); do\n  echo stopping\n  echo \"$pid\"\n  kill \"$pid\"\ndone\n",
     FAIL, "LSOF_NO_LISTEN"),
    ("lsof-var-without-kill-ok", "a.sh",
     "pids=$(lsof -ti :3000)\necho \"$pids\"\necho\necho\nkill \"$(cat my.pid)\"\n", OK, ""),
    ("lsof-listen-after-i-ok", "a.sh",
     _SH + "kill -9 $(lsof -t -iTCP:$port -sTCP:LISTEN)\n", OK, ""),
    ("lsof-listen-before-i-ok", "a.sh", "kill $(lsof -t -sTCP:LISTEN -iTCP:$P)\n", OK, ""),
    ("lsof-listen-before-cluster-ok", "a.sh", "kill $(lsof -sTCP:LISTEN -ti :$P)\n", OK, ""),
    ("lsof-listen-spaced-ok", "a.sh", "kill \"$(lsof -tiTCP:$P -s TCP:LISTEN)\"\n", OK, ""),
    # RANGE_KILL: seq, seq -w, brace, C-style for; small counters do not fire.
    ("range-seq-fires", "a.sh",
     _SH + "for port in $(seq 3110 3200); do\n  kill -9 $(lsof -t -iTCP:$port -sTCP:LISTEN)\ndone\n",
     FAIL, "RANGE_KILL"),
    ("range-seq-w-fires", "a.sh", "for p in $(seq -w 3000 3010); do kill $p; done\n",
     FAIL, "RANGE_KILL"),
    ("range-brace-fires", "a.sh",
     "for p in {3000..3010}; do kill $(lsof -t -iTCP:$p -sTCP:LISTEN); done\n", FAIL, "RANGE_KILL"),
    ("range-cfor-fires", "a.sh",
     "for ((p=3000;p<=3010;p++)); do kill $(lsof -t -iTCP:$p -sTCP:LISTEN); done\n",
     FAIL, "RANGE_KILL"),
    ("range-small-counter-ok", "a.sh",
     "for i in $(seq 1 3); do echo retry; done\nkill \"$(cat my.pid)\"\n", OK, ""),
    # BROAD_PKILL: pattern argument only, whole words.
    ("pkill-browser-fires", "a.sh", _SH + "pkill -f 'chromium.*headless'\n", FAIL, "BROAD_PKILL"),
    ("pkill-no-f-fires", "a.sh", "pkill chromium\n", FAIL, "BROAD_PKILL"),
    ("pkill-signal-quoted-fires", "a.sh", "pkill -9 -f \"next dev\"\n", FAIL, "BROAD_PKILL"),
    ("killall-escaped-space-fires", "a.sh", "killall -9 Google\\ Chrome\n", FAIL, "BROAD_PKILL"),
    ("pkill-substring-ok", "a.sh", "pkill -f ledger-sync\n", OK, ""),
    ("pkill-parent-comment-ok", "a.sh", "pkill -P $$  # stop child server\n", OK, ""),
    ("pkill-scoped-var-ok", "a.sh", "pkill -f \"$LANE_ID/node_modules/.bin/vite\"\n", OK, ""),
    ("killall-own-name-ok", "a.sh", "killall mydaemon\n", OK, ""),
    # New shapes.
    ("ps-grep-kill-fires", "a.sh", "ps aux | grep chrome | awk '{print $2}' | xargs kill -9\n",
     FAIL, "PS_GREP_KILL"),
    ("ps-grep-bracket-var-fires", "a.sh",
     "local pids; pids=$(ps aux | grep [c]hrome | awk '{print $2}')\necho\necho\necho\nkill $pids\n",
     FAIL, "PS_GREP_KILL"),
    ("ps-grep-own-name-ok", "a.sh", "ps aux | grep my-lane-worker | awk '{print $2}' | xargs kill\n",
     OK, ""),
    ("pgrep-kill-fires", "a.sh", "pgrep -f webpack | xargs kill\n", FAIL, "BROAD_PKILL"),
    ("pkill-parent-then-pattern-fires", "a.sh", "pkill -P 1234 node\n", FAIL, "BROAD_PKILL"),
    ("fuser-k-fires", "a.sh", "fuser -k 3000/tcp\n", FAIL, "FUSER_KILL"),
    ("fuser-no-k-ok", "a.sh", "fuser 3000/tcp\n", OK, ""),
    ("npx-kill-port-fires", "a.sh", "npx kill-port 3000 3001\n", FAIL, "KILL_PORT"),
    ("bare-kill-port-fires", "a.sh", "kill-port 3000\n", FAIL, "KILL_PORT"),
    # HARDCODED_PORTS: NAME= assignment of 2+ port-like numbers.
    ("hardcoded-array-fires", "a.sh",
     _SH + "PROTECTED_PORTS=(3000 8080 5432)\nkill -9 $(lsof -t -iTCP:$port -sTCP:LISTEN)\n",
     FAIL, "HARDCODED_PORTS"),
    ("hardcoded-quoted-fires", "a.sh",
     "PROTECTED_PORTS=\"3000,8080\"; for p in $X; do kill $p; done\n", FAIL, "HARDCODED_PORTS"),
    ("hardcoded-multiline-fires", "a.sh", "PROTECTED=(\n  3000\n  8080\n)\nkill 1\n",
     FAIL, "HARDCODED_PORTS"),
    ("hardcoded-comment-ok", "a.sh", "# keep ports 3000 8080 in sync with docs\nkill $PID\n", OK, ""),
    ("hardcoded-small-numbers-ok", "a.sh", "SKIP_TESTS=\"unit 10 20\"\nkill $PID\n", OK, ""),
    # Allow marker: exact token, non-empty reason, same line only.
    ("allow-same-line-suppresses", "a.sh",
     "kill -9 $(lsof -ti :$port)  # reaper-lint: allow lane-owned port, verified by caller\n", OK, ""),
    ("allow-line-above-does-not-suppress", "a.sh",
     "# reaper-lint: allow lane-owned port, verified by caller\nkill -9 $(lsof -ti :$port)\n",
     FAIL, "LSOF_NO_LISTEN"),
    ("allow-without-reason-does-not-suppress", "a.sh",
     "lsof -ti :3000 | xargs kill  # reaper-lint: allow\n", FAIL, "LSOF_NO_LISTEN"),
    ("allow-near-miss-does-not-suppress", "a.sh",
     "lsof -ti :3000 | xargs kill; # reaper-lint: allowance\n", FAIL, "LSOF_NO_LISTEN"),
    # Embedded shell: package.json script values and YAML `run: |` blocks.
    ("package-json-scripts-fires", "package.json",
     '{\n  "scripts": {\n    "reap": "for p in $(seq 3110 3200); do kill -9 $p; done"\n  }\n}\n',
     FAIL, "RANGE_KILL"),
    ("package-json-dependency-ok", "package.json",
     ('{\n  "scripts": {\n    "stop": "kill $(cat .pid)"\n  },\n'
      '  "devDependencies": {\n    "kill-port": "^2.0.0"\n  }\n}\n'), OK, ""),
    ("yaml-run-block-fires", "ci.yml",
     ("jobs:\n  e2e:\n    steps:\n      - name: free port\n        run: |\n"
      "          echo freeing\n          lsof -ti :3000 | xargs kill -9\n"), FAIL, "LSOF_NO_LISTEN"),
)


def _selftest() -> int:
    failures: list[str] = []
    passed = 0

    def check(name: str, rc: int, lines: list[str], want_rc: int,
              must_have: tuple[str, ...] = (), must_not_have: tuple[str, ...] = ()) -> None:
        nonlocal passed
        joined = "\n".join(lines)
        ok = (rc == want_rc
              and all(needle in joined for needle in must_have)
              and all(needle not in joined for needle in must_not_have))
        if ok:
            passed += 1
        else:
            failures.append(f"{name}: rc={rc} (want {want_rc}); output={joined!r}")

    skipped: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for idx, (name, fname, content, want_rc, rule) in enumerate(_CASES):
            path = os.path.join(tmp, f"case{idx:02d}", fname)
            _write(path, content)
            rc, lines = run_gate([path])
            check(name, rc, lines, want_rc, must_have=(rule,) if rule else ())

        # Directory walk: scans shell/Makefile-family/YAML/package.json and
        # shebang-sniffed extensionless files; skips everything else.
        scandir = os.path.join(tmp, "scandir")
        bad = "pkill -f chromium\n"
        _write(os.path.join(scandir, "reap.sh"), "kill -9 $(lsof -ti :$port)\n")
        _write(os.path.join(scandir, "notes.txt"), bad)
        _write(os.path.join(scandir, "reap.mk"), "reap:\n\t" + bad)
        _write(os.path.join(scandir, "GNUmakefile"), "reap:\n\t" + bad)
        _write(os.path.join(scandir, "justfile"), "reap:\n    " + bad)
        _write(os.path.join(scandir, "bin", "cleanup"), "#!/bin/bash\n" + bad)
        _write(os.path.join(scandir, "bin", "envcleanup"), "#!/usr/bin/env bash\n" + bad)
        _write(os.path.join(scandir, "bin", "README"), bad)
        rc, lines = run_gate([scandir])
        check(
            "dir-scan-filters-and-sniffs", rc, lines, FAIL,
            must_have=("reap.sh", "LSOF_NO_LISTEN", "reap.mk", "GNUmakefile", "justfile",
                       os.path.join("bin", "cleanup"), os.path.join("bin", "envcleanup")),
            must_not_have=("notes.txt", "README"),
        )

        # A named path that does not exist -> ERROR (fail closed).
        rc, lines = run_gate([os.path.join(tmp, "does-not-exist.sh")])
        check("missing-path-errors", rc, lines, ERROR)

        # Undecodable text -> ERROR, not a silent pass over mojibake.
        u16 = os.path.join(tmp, "u16", "reap.sh")
        _write(u16, "pkill -f chrome\n".encode("utf-16-le"))
        rc, lines = run_gate([u16])
        check("utf16-errors", rc, lines, ERROR, must_have=("cannot decode",))
        latin = os.path.join(tmp, "latin", "reap.sh")
        _write(latin, b"# caf\xe9\npkill -f chrome\n")
        rc, lines = run_gate([latin])
        check("invalid-utf8-errors", rc, lines, ERROR, must_have=("cannot decode",))

        # An unlistable directory during the walk -> ERROR (fail closed).
        locked_root = os.path.join(tmp, "lockroot")
        locked = os.path.join(locked_root, "locked")
        _write(os.path.join(locked, "x.sh"), bad)
        os.chmod(locked, 0)
        try:
            if os.access(locked, os.R_OK):
                skipped.append("unlistable-dir-errors (running with read access to a mode-000 "
                               "directory, e.g. as root; cannot plant the case)")
            else:
                rc, lines = run_gate([locked_root])
                check("unlistable-dir-errors", rc, lines, ERROR, must_have=("cannot list",))
        finally:
            os.chmod(locked, 0o700)

    total = passed + len(failures)
    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    for s in skipped:
        print(f"SELFTEST SKIPPED: {s}")
    print(f"SELFTEST OK: {passed}/{total} cases passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Heuristic lint: flag bulk/fleet-wide process-reaper patterns "
                    "in shell/Makefile/justfile/package.json-script/CI-YAML text."
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
