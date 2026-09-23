#!/usr/bin/env python3
"""task_ledger.py — the ONE durable todo list for a project, so the conductor
never loses an owner's ask under a flood or a compaction.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
Under real pressure an owner fires many asks at once. Without a durable store,
the conductor keeps the list in its own context: a compaction, a context-loss,
or simply "losing its place" then makes it recreate a SECOND todo list instead
of resuming the first — asks silently fork, collide, or vanish, and the owner
never finds out which happened. This script is the single external memory:
one markdown file the owner can also read, one row per ask, atomic writes so
a crash mid-write cannot corrupt it, and an `fcntl` file lock so two agents
racing on the same project never interleave a read-modify-write and drop a
row. The doctrine that points here lives in `../SKILL.md`; this is the
mechanism that makes it actually fire instead of staying prose.

THE RULE
--------
The ledger file (default `.claude/TASKS.md`) is the ONLY todo list for a
project. Every owner ask goes in verbatim, one ask per row, before work
starts. Nothing here re-splits an ask into subtasks — the caller decides what
counts as one ask and calls `add` once per ask. A near-duplicate ask (matched
by normalized-text similarity, not just an exact string) is refused and the
existing row's id is returned instead of silently forking a second row for
the same ask. Marking a row `done` requires evidence (a sha, a PR link, a
test name, or any link) — an unverified "done" is worse than an honest "open".
Marking a row `blocked` requires naming the other party (`"<party>: <reason>"`)
so a stall is never anonymous. `status` is the only source of truth for a
progress report — never memory, never a paraphrase.

DATA MODEL — one markdown table, one row per ask
-------------------------------------------------
    | id | status | created | updated | ask | evidence | source |
id       T-### (T-001, T-002, ... never reused, never renumbered)
status   open | doing | blocked | done | dropped-by-owner
created  ISO-8601 UTC, set once at `add`
updated  ISO-8601 UTC, set on every transition
ask      the owner's words verbatim, sanitized to one table line (newlines
         collapsed to spaces; `|` and `\\` escaped so a row can never smuggle
         a second row or break the table)
evidence "-" until `done`/`blocked` sets it (sha|PR|test|link, or "<party>:
         <reason>" for a block)
source   caller-supplied provenance (e.g. a message timestamp/id), "-" if
         omitted

The file always opens with a fixed title line, then the exact header and
separator rows above; a file that does not parse to this shape (hand-edited
into an inconsistent state, truncated, or from a different tool) is treated
as MALFORMED and every command fails closed (exit 2) rather than guessing
at a repair.

LOCKING + ATOMICITY (concurrency-safe by construction)
-------------------------------------------------------
Every command takes an advisory lock on `<file>.lock` via `fcntl.flock`
(exclusive for a write command, shared for a read-only one) around the full
read-modify-write, so two `add`/`start`/`done`/`block` invocations racing on
the same ledger from different processes can never interleave. Every write
goes to a temp file in the same directory (so `os.replace` is an atomic
rename on the same filesystem) — a crash mid-write leaves the previous
version intact, never a half-written file. `fcntl` is POSIX-only by design:
this suite runs on macOS/Linux hosts, not Windows.

EXIT CODES (fail closed)
-------------------------
  0  the command's normal-success verdict — but see `status`/`reconcile`,
     which use exit 1 for their own "not fully done" / "found a gap" signal,
     not an error
  1  a business-rule refusal that is not a bug: a near-duplicate `add`, a
     `done`/`block` missing its required evidence, `status` finding an
     unresolved (non-done, non-dropped) row, or `reconcile` finding an owner
     ask missing from the ledger
  2  a hard error: an unreadable/malformed ledger file, an unknown `--id`,
     malformed `--transcript-asks` input, or bad CLI usage

USAGE
-----
  task_ledger.py [--file PATH] add --ask "<owner words verbatim>" [--source S]
  task_ledger.py [--file PATH] start --id T-###
  task_ledger.py [--file PATH] done  --id T-### --evidence "<sha|PR|test|link>"
  task_ledger.py [--file PATH] block --id T-### --evidence "<party>: <reason>"
  task_ledger.py [--file PATH] next
  task_ledger.py [--file PATH] status
  task_ledger.py [--file PATH] reconcile --transcript-asks FILE
  task_ledger.py --selftest

`--file` defaults to `.claude/TASKS.md` (relative to the current directory).
`next` additionally reads `.claude/PRIORITY.md` (same directory as the
ledger) READ-ONLY, if present: one priority per line (an id or free text),
first line wins by id match then by normalized-text similarity; falls back
to the oldest open row when the file is absent or nothing matches.
`reconcile` reads `--transcript-asks` as JSON Lines, one `{"ask": "..."}`
object per line (extra keys ignored).
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
import fcntl
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

OK, WARN, ERROR = 0, 1, 2

HEADER_CELLS = ("id", "status", "created", "updated", "ask", "evidence", "source")
HEADER_LINE = "| " + " | ".join(HEADER_CELLS) + " |"
SEP_LINE = "|" + "|".join(["---"] * len(HEADER_CELLS)) + "|"
TITLE_LINE = "# Task Ledger"

STATUSES = ("open", "doing", "blocked", "done", "dropped-by-owner")
RESOLVED_STATUSES = {"done", "dropped-by-owner"}

ID_RE = re.compile(r"^T-(\d{3,})$")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_PARTY_RE = re.compile(r"^\s*(?P<party>[^:]+):\s*(?P<reason>.*)$", re.S)

NEAR_DUP_THRESHOLD = 0.82  # add-time / reconcile "is this the same ask" bar
PRIORITY_MATCH_THRESHOLD = 0.55  # next-time "does this priority line mean this row" bar
STATUS_MAX_ROWS = 13  # + the counts line + a "N more" line stays within the 15-line cap


class LedgerError(ValueError):
    """The ledger file does not parse to the fixed shape; caller exits 2."""


# ---------------------------------------------------------------------------
# Pure logic: no I/O below this line touches a filesystem. Every rule is a
# function over an in-memory row list, so the selftest exercises the RULES,
# not a temp-file dance, for every branch except the concurrency/CLI ones.
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Lowercase, punctuation-stripped, whitespace-collapsed form for similarity. Pure."""
    text = _PUNCT_RE.sub(" ", (text or "").lower())
    return " ".join(text.split())


def _similarity(a: str, b: str) -> float:
    """difflib ratio over normalized text. Pure, stdlib-only."""
    return difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def _names_other_party(evidence: str) -> bool:
    """True iff `evidence` is shaped "<party>: <reason>" with a non-empty party. Pure."""
    m = _PARTY_RE.match(evidence or "")
    if not m:
        return False
    party = m.group("party").strip()
    return bool(party) and any(ch.isalnum() for ch in party)


def _sanitize_cell(text) -> str:
    """One markdown-table-safe line: whitespace-collapsed, printable-only, `\\`/`|` escaped. Pure.

    Whitespace (including newlines/tabs) is collapsed to single spaces FIRST:
    `str.isprintable()` treats `\\n`/`\\t` as non-printable, so stripping
    non-printable chars before collapsing whitespace would delete a newline
    outright and fuse the words on either side of it.
    """
    text = "" if text is None else str(text)
    text = " ".join(text.split())
    text = "".join(ch for ch in text if ch.isprintable())
    text = text.replace("\\", "\\\\").replace("|", "\\|")
    return text or "-"


def _split_row(line: str) -> list:
    """Split one `| a | b\\|c | ... |` table line into its raw (unescaped) cells. Pure."""
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")) or len(s) < 2:
        raise LedgerError(f"row is not pipe-delimited: {line!r}")
    inner = s[1:-1]
    cells, buf, i = [], [], 0
    while i < len(inner):
        ch = inner[i]
        if ch == "\\" and i + 1 < len(inner) and inner[i + 1] in "\\|":
            buf.append(inner[i + 1])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def parse_ledger_text(text: str) -> list:
    """Parse the ledger file's exact shape into a row-dict list, or raise LedgerError.

    An empty/whitespace-only file is a valid EMPTY ledger (no rows yet) — the
    first `add` creates the title/header/separator. Anything else must match
    the fixed title line, the exact header row, the exact separator row, then
    zero or more data rows each with exactly len(HEADER_CELLS) cells, a
    well-formed T-### id (unique), and a known status. Fail closed on any
    deviation: this is the sole writer's format, so a mismatch means the file
    was hand-edited, truncated, or came from something else.
    """
    if text is None or text.strip() == "":
        return []
    lines = text.splitlines()
    if lines[0].strip() != TITLE_LINE:
        raise LedgerError(f"missing {TITLE_LINE!r} title line (malformed ledger file)")
    try:
        hidx = lines.index(HEADER_LINE)
    except ValueError:
        raise LedgerError("missing or altered table header row (malformed ledger file)") from None
    if hidx + 1 >= len(lines) or lines[hidx + 1].strip() != SEP_LINE:
        raise LedgerError("missing or altered table separator row (malformed ledger file)")
    rows, seen_ids = [], set()
    for line in lines[hidx + 2 :]:
        if not line.strip():
            continue
        cells = _split_row(line)
        if len(cells) != len(HEADER_CELLS):
            raise LedgerError(f"row has {len(cells)} cells, expected {len(HEADER_CELLS)}: {line!r}")
        row = dict(zip(HEADER_CELLS, cells))
        if not ID_RE.match(row["id"]):
            raise LedgerError(f"row id {row['id']!r} does not match T-### (malformed ledger file)")
        if row["id"] in seen_ids:
            raise LedgerError(f"duplicate id {row['id']!r} (malformed ledger file)")
        if row["status"] not in STATUSES:
            raise LedgerError(f"row {row['id']} has unknown status {row['status']!r} (malformed ledger file)")
        seen_ids.add(row["id"])
        rows.append(row)
    return rows


def render_ledger_text(rows: list) -> str:
    """Render rows back to the fixed ledger shape. Pure; inverse of parse_ledger_text on valid input."""
    lines = [
        TITLE_LINE,
        "",
        "Durable single source of truth for owner asks. Read at session start and "
        "after any compaction. This is the ONLY todo list -- never create a second one.",
        "",
        HEADER_LINE,
        SEP_LINE,
    ]
    for r in rows:
        lines.append("| " + " | ".join(_sanitize_cell(r[c]) for c in HEADER_CELLS) + " |")
    return "\n".join(lines) + "\n"


def next_id(rows: list) -> str:
    """The next unused T-### id: max existing number + 1, zero-padded to 3 digits. Pure."""
    nums = [int(m.group(1)) for r in rows for m in [ID_RE.match(r["id"])] if m]
    return f"T-{max(nums, default=0) + 1:03d}"


def find_duplicate(rows: list, ask: str):
    """The best-matching existing row for `ask` if it clears NEAR_DUP_THRESHOLD, else None. Pure."""
    best, best_ratio = None, 0.0
    for r in rows:
        ratio = _similarity(ask, r["ask"])
        if ratio > best_ratio:
            best, best_ratio = r, ratio
    return best if best is not None and best_ratio >= NEAR_DUP_THRESHOLD else None


def _now_iso(now: datetime = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def do_add(rows: list, ask: str, source: str = None, now: datetime = None):
    """Append one row for `ask`, refusing a near-duplicate. Pure; returns (code, message, new_rows).

    One ask = one row: this never splits `ask` itself — the caller decides
    what one ask is and calls this once per ask.
    """
    ask = (ask or "").strip()
    if not ask:
        return ERROR, "error: --ask must be non-empty", rows
    dup = find_duplicate(rows, ask)
    if dup is not None:
        return WARN, f"REFUSED: near-duplicate of {dup['id']} (ask not added) -- use that id: {dup['id']}", rows
    ts = _now_iso(now)
    row = {
        "id": next_id(rows),
        "status": "open",
        "created": ts,
        "updated": ts,
        "ask": ask,
        "evidence": "-",
        "source": (source or "-").strip() or "-",
    }
    return OK, f"ADDED {row['id']}: {ask}", rows + [row]


def do_transition(rows: list, task_id: str, new_status: str, evidence: str = None, now: datetime = None):
    """Move `task_id` to `new_status`, enforcing evidence rules. Pure; returns (code, message, new_rows).

    `done` refuses without non-empty evidence; `blocked` refuses without
    evidence naming the other party (`"<party>: <reason>"`); `doing` (start)
    requires nothing.
    """
    idx = next((i for i, r in enumerate(rows) if r["id"] == task_id), None)
    if idx is None:
        return ERROR, f"error: no such id {task_id}", rows
    evidence = (evidence or "").strip()
    if new_status == "done" and not evidence:
        return WARN, f"REFUSED: done requires --evidence (a sha|PR|test|link) for {task_id}", rows
    if new_status == "blocked" and not _names_other_party(evidence):
        return WARN, (
            f'REFUSED: block requires --evidence naming the other party, '
            f'e.g. "owner: waiting on pricing decision", for {task_id}'
        ), rows
    row = dict(rows[idx])
    row["status"] = new_status
    row["updated"] = _now_iso(now)
    if evidence:
        row["evidence"] = evidence
    new_rows = list(rows)
    new_rows[idx] = row
    return OK, f"{new_status.upper()} {task_id}", new_rows


def pick_next(rows: list, priority_lines: list):
    """The single next OPEN row, or None. Pure.

    Priority order: the first `priority_lines` entry that matches an open
    row's id exactly, or (failing that on every line) the open row whose ask
    best matches a priority line at or above PRIORITY_MATCH_THRESHOLD; else
    the oldest open row by `created` (ties broken by id).
    """
    open_rows = [r for r in rows if r["status"] == "open"]
    if not open_rows:
        return None
    for raw in priority_lines:
        line = raw.strip().lstrip("-*").strip()
        if not line:
            continue
        for r in open_rows:
            if r["id"].lower() == line.lower():
                return r
        best, best_ratio = None, 0.0
        for r in open_rows:
            ratio = _similarity(line, r["ask"])
            if ratio > best_ratio:
                best, best_ratio = r, ratio
        if best is not None and best_ratio >= PRIORITY_MATCH_THRESHOLD:
            return best
    return min(open_rows, key=lambda r: (r["created"], r["id"]))


def status_summary(rows: list):
    """Counts line + up to STATUS_MAX_ROWS unresolved rows. Pure; returns (exit_code, lines).

    exit_code is OK only when every row is `done` or `dropped-by-owner`
    (spec: "exit 1 if any owner ask is not done").
    """
    counts = {s: 0 for s in STATUSES}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    unresolved = sorted((r for r in rows if r["status"] not in RESOLVED_STATUSES), key=lambda r: (r["created"], r["id"]))
    lines = [
        f"status: open={counts['open']} doing={counts['doing']} blocked={counts['blocked']} "
        f"done={counts['done']} dropped={counts['dropped-by-owner']}"
    ]
    shown = unresolved[:STATUS_MAX_ROWS]
    lines += [f"{r['id']} [{r['status']}] {r['ask']}" for r in shown]
    if len(unresolved) > len(shown):
        lines.append(f"... {len(unresolved) - len(shown)} more")
    return (OK if not unresolved else WARN), lines


def reconcile_missing(rows: list, asks: list) -> list:
    """Owner asks with no near-duplicate row in the ledger (any status). Pure."""
    return [ask for ask in asks if find_duplicate(rows, ask) is None]


# ---------------------------------------------------------------------------
# I/O: locking, atomic writes, file reads. Everything above this line is pure.
# ---------------------------------------------------------------------------


def _lock_path(path: str) -> str:
    return f"{path}.lock"


@contextlib.contextmanager
def _locked(path: str, exclusive: bool):
    """Hold an advisory fcntl lock on `<path>.lock` for the duration of the block.

    Side-effect: creates the ledger's parent directory and the lock file if
    absent. Exclusive for a write command, shared for a read-only one, so
    concurrent `add`/`start`/`done`/`block` calls from different processes
    never interleave a read-modify-write.
    """
    lock_path = _lock_path(path)
    parent = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(parent, exist_ok=True)
    with open(lock_path, "a+") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        try:
            yield
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: str, content: str) -> None:
    """Write `content` to `path` via temp-file-then-rename in the same directory (atomic on POSIX)."""
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".task_ledger.tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


def _read_rows(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return parse_ledger_text(fh.read())


def _read_priority_lines(path: str) -> list:
    """Non-empty lines of `.claude/PRIORITY.md` (sibling of the ledger), READ-ONLY. Never absent -> []."""
    pfile = os.path.join(os.path.dirname(os.path.abspath(path)), "PRIORITY.md")
    if not os.path.isfile(pfile):
        return []
    with open(pfile, encoding="utf-8") as fh:
        return [ln for ln in fh.read().splitlines() if ln.strip()]


def _read_transcript_asks(file: str) -> list:
    """Parse `--transcript-asks` JSON Lines (`{"ask": "..."}` per line). Raises ValueError on malformed input."""
    asks = []
    with open(file, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{file}:{i}: not valid JSON: {exc}") from None
            if not isinstance(obj, dict) or not isinstance(obj.get("ask"), str) or not obj["ask"].strip():
                raise ValueError(f"{file}:{i}: expected an object with a non-empty 'ask' string")
            asks.append(obj["ask"].strip())
    return asks


def main(argv: list = None) -> int:
    """CLI entry point; see the module docstring for commands, options, and exit codes."""
    ap = argparse.ArgumentParser(prog="task_ledger.py", description="The one durable per-project todo ledger.")
    ap.add_argument("--file", default=os.path.join(".claude", "TASKS.md"), help="ledger file (default .claude/TASKS.md)")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add", help="append one row for an owner ask, verbatim")
    p_add.add_argument("--ask", required=True)
    p_add.add_argument("--source", default=None)

    for name, help_text in (
        ("start", "mark a row 'doing'"),
        ("done", "mark a row 'done' (requires --evidence)"),
        ("block", "mark a row 'blocked' (requires --evidence naming the other party)"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--id", required=True)
        p.add_argument("--evidence", default=None)

    sub.add_parser("next", help="print the single next open row")
    sub.add_parser("status", help="print counts + unresolved rows")

    p_rec = sub.add_parser("reconcile", help="find owner asks missing from the ledger")
    p_rec.add_argument("--transcript-asks", required=True, metavar="FILE")

    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.cmd:
        ap.print_usage()
        return ERROR

    path = args.file
    try:
        if args.cmd == "add":
            with _locked(path, exclusive=True):
                rows = _read_rows(path)
                code, msg, new_rows = do_add(rows, args.ask, args.source)
                if code == OK:
                    _atomic_write(path, render_ledger_text(new_rows))
            print(msg)
            return code

        if args.cmd in ("start", "done", "block"):
            new_status = {"start": "doing", "done": "done", "block": "blocked"}[args.cmd]
            with _locked(path, exclusive=True):
                rows = _read_rows(path)
                code, msg, new_rows = do_transition(rows, args.id, new_status, args.evidence)
                if code == OK:
                    _atomic_write(path, render_ledger_text(new_rows))
            print(msg)
            return code

        if args.cmd == "next":
            with _locked(path, exclusive=False):
                rows = _read_rows(path)
                priority_lines = _read_priority_lines(path)
            row = pick_next(rows, priority_lines)
            if row is None:
                print("next: none (no open asks)")
            else:
                print(f"next: {row['id']} [{row['status']}] {row['ask']}")
                print(f"created: {row['created']} source: {row['source']}")
            return OK

        if args.cmd == "status":
            with _locked(path, exclusive=False):
                rows = _read_rows(path)
            code, lines = status_summary(rows)
            for line in lines:
                print(line)
            return code

        if args.cmd == "reconcile":
            try:
                asks = _read_transcript_asks(args.transcript_asks)
            except (OSError, ValueError) as exc:
                print(f"error: {exc}")
                return ERROR
            with _locked(path, exclusive=False):
                rows = _read_rows(path)
            missing = reconcile_missing(rows, asks)
            for ask in missing:
                print(f"MISSING: {ask}")
            print(f"reconcile: {len(missing)} missing of {len(asks)} asks")
            return OK if not missing else WARN
    except LedgerError as exc:
        print(f"error: malformed ledger file {path}: {exc}")
        return ERROR

    ap.print_usage()
    return ERROR


# ---------------------------------------------------------------------------
# Selftest: pure-logic cases first (every rule branch), then two I/O cases
# (malformed-file exit code, concurrent `add` safety) against real temp
# files. Fully offline: no network, no model, no external process.
# ---------------------------------------------------------------------------


def _selftest() -> int:
    import io
    import threading

    failures: list = []
    ran = [0]

    def check(label: str, cond: bool, detail: str = "") -> None:
        ran[0] += 1
        if not cond:
            failures.append(f"{label}: {detail}")

    # -- add / duplicate refusal -------------------------------------------------
    code1, msg1, rows1 = do_add([], "Build the CSV export feature")
    check("add-ok", code1 == OK and rows1[0]["id"] == "T-001", f"{code1} {msg1}")
    code2, msg2, rows2 = do_add(rows1, "build csv export feature!!")
    check("duplicate-refused", code2 == WARN, f"{code2} {msg2}")
    check("duplicate-refused-names-existing-id", "T-001" in msg2, msg2)
    check("duplicate-refused-no-new-row", len(rows2) == 1, str(rows2))
    code3, _, rows3 = do_add(rows1, "Write onboarding docs")
    check("distinct-ask-gets-new-id", code3 == OK and rows3[-1]["id"] == "T-002", str(rows3))
    code_empty, _, _ = do_add([], "   ")
    check("empty-ask-errors", code_empty == ERROR, str(code_empty))

    # -- start / done / block evidence rules -------------------------------------
    tid = rows1[0]["id"]
    code_start, _, rows_start = do_transition(rows1, tid, "doing")
    check("start-needs-no-evidence", code_start == OK and rows_start[0]["status"] == "doing", str(code_start))
    code_done_bare, _, _ = do_transition(rows1, tid, "done", "")
    check("done-without-evidence-refused", code_done_bare == WARN, str(code_done_bare))
    code_done_ok, _, rows_done = do_transition(rows1, tid, "done", "PR#42")
    check("done-with-evidence-ok", code_done_ok == OK and rows_done[0]["evidence"] == "PR#42", str(rows_done))
    code_block_anon, _, _ = do_transition(rows1, tid, "blocked", "waiting on stuff")
    check("block-without-party-refused", code_block_anon == WARN, str(code_block_anon))
    code_block_ok, _, rows_blocked = do_transition(rows1, tid, "blocked", "owner: pricing decision pending")
    check("block-with-party-ok", code_block_ok == OK and rows_blocked[0]["status"] == "blocked", str(rows_blocked))
    code_unknown, _, _ = do_transition(rows1, "T-999", "done", "x")
    check("unknown-id-errors", code_unknown == ERROR, str(code_unknown))

    # -- next ordering ------------------------------------------------------------
    ordered_rows = [
        {"id": "T-001", "status": "open", "created": "2026-01-02T00:00:00Z", "updated": "2026-01-02T00:00:00Z",
         "ask": "Write onboarding docs", "evidence": "-", "source": "-"},
        {"id": "T-002", "status": "open", "created": "2026-01-01T00:00:00Z", "updated": "2026-01-01T00:00:00Z",
         "ask": "Fix the CSV export bug", "evidence": "-", "source": "-"},
    ]
    check("next-oldest-first-no-priority", pick_next(ordered_rows, [])["id"] == "T-002")
    check("next-priority-file-overrides-by-id", pick_next(ordered_rows, ["T-001"])["id"] == "T-001")
    check("next-priority-fuzzy-text-match", pick_next(ordered_rows, ["no such thing", "fix the csv export bug!"])["id"] == "T-002")
    check("next-no-open-returns-none", pick_next([dict(r, status="done") for r in ordered_rows], []) is None)

    # -- status ---------------------------------------------------------------
    mixed = ordered_rows + [dict(ordered_rows[0], id="T-003", status="done", ask="Ship the release")]
    code_status, lines_status = status_summary(mixed)
    check("status-unresolved-exits-warn", code_status == WARN, str(lines_status))
    check("status-line-count-bounded", len(lines_status) <= 15, str(len(lines_status)))
    all_done = [dict(r, status="done") for r in ordered_rows]
    code_status_done, _ = status_summary(all_done)
    check("status-all-resolved-exits-ok", code_status_done == OK)
    all_dropped = [dict(r, status="dropped-by-owner") for r in ordered_rows]
    check("status-dropped-counts-as-resolved", status_summary(all_dropped)[0] == OK)

    # -- reconcile ------------------------------------------------------------
    known = [dict(r) for r in ordered_rows]
    missing = reconcile_missing(known, ["Write onboarding docs", "fix csv export bug", "Migrate the billing DB"])
    check("reconcile-finds-dropped-ask", missing == ["Migrate the billing DB"], str(missing))
    check("reconcile-no-false-positive", reconcile_missing(known, ["write the onboarding docs"]) == [])

    # -- ledger text parse/render round-trip + malformed detection -----------
    check("empty-text-parses-to-no-rows", parse_ledger_text("") == [])
    check("empty-text-parses-to-no-rows-whitespace", parse_ledger_text("   \n  ") == [])
    rendered = render_ledger_text(mixed)
    check("round-trip-preserves-rows", parse_ledger_text(rendered) == mixed, rendered)
    pipe_row = [{"id": "T-001", "status": "open", "created": "2026-01-01T00:00:00Z", "updated": "2026-01-01T00:00:00Z",
                 "ask": "A | B\nand a \\ backslash", "evidence": "-", "source": "-"}]
    rt = parse_ledger_text(render_ledger_text(pipe_row))
    check("pipe-and-backslash-escaped-round-trip", rt[0]["ask"] == "A | B and a \\ backslash", rt)
    for bad, why in (
        ("not a ledger at all", "missing title"),
        (TITLE_LINE + "\nno header here", "missing header"),
        (TITLE_LINE + "\n" + HEADER_LINE + "\nnot the separator", "missing separator"),
        (TITLE_LINE + "\n" + HEADER_LINE + "\n" + SEP_LINE + "\n| only | four | cells | -|", "short row"),
        (TITLE_LINE + "\n" + HEADER_LINE + "\n" + SEP_LINE + "\n| X-001 | open | t | t | ask | - | - |", "bad id"),
        (TITLE_LINE + "\n" + HEADER_LINE + "\n" + SEP_LINE + "\n| T-001 | weird | t | t | ask | - | - |", "bad status"),
    ):
        try:
            parse_ledger_text(bad)
            failures.append(f"malformed-detected[{why}]: no LedgerError raised")
        except LedgerError:
            pass
        ran[0] += 1
    dup_id_text = (
        TITLE_LINE + "\n" + HEADER_LINE + "\n" + SEP_LINE
        + "\n| T-001 | open | t | t | a | - | - |"
        + "\n| T-001 | open | t | t | b | - | - |"
    )
    try:
        parse_ledger_text(dup_id_text)
        failures.append("malformed-detected[duplicate id]: no LedgerError raised")
    except LedgerError:
        pass
    ran[0] += 1

    # -- names-other-party edge cases ------------------------------------------
    check("party-needs-alnum", not _names_other_party(": just punctuation :::"))
    check("party-colon-required", not _names_other_party("no colon here"))
    check("party-ok", _names_other_party("QA: waiting on the fixture"))

    # -- I/O: malformed file on disk -> CLI exits 2 ----------------------------
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="task_ledger_selftest_")
    try:
        bad_path = os.path.join(tmpdir, "TASKS.md")
        with open(bad_path, "w", encoding="utf-8") as fh:
            fh.write("this is not a ledger file\njust some text\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["--file", bad_path, "status"])
        check("malformed-file-cli-exits-2", rc == ERROR, f"rc={rc} out={buf.getvalue()!r}")

        # -- I/O: concurrent `add` from multiple threads is safe (real fcntl lock,
        #    real atomic write) -- distinct asks must all land, once each, with
        #    unique ids, and the resulting file must still parse.
        conc_path = os.path.join(tmpdir, "CONC.md")
        # Deliberately dissimilar asks: near-identical phrasing (e.g. differing
        # only by a trailing number) would legitimately trip near-dup refusal
        # and the test would be checking the wrong thing.
        conc_asks = [
            "Migrate the billing database",
            "Write the onboarding guide",
            "Fix the CSV export bug",
            "Update the pricing page copy",
            "Rotate the signing keys",
            "Draft the investor update",
            "Patch the auth middleware",
            "Refresh the onboarding screenshots",
        ]
        n = len(conc_asks)
        rcs = [None] * n

        def worker(i: int) -> None:
            # No per-thread redirect_stdout: it swaps the process-global
            # sys.stdout, so two threads racing it would stomp on each
            # other's redirection. One outer redirect (below) covers all of
            # them; each `add`'s own print is harmless either way.
            rcs[i] = main(["--file", conc_path, "add", "--ask", conc_asks[i]])

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        conc_buf = io.StringIO()
        with contextlib.redirect_stdout(conc_buf):
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        check("concurrent-add-all-ok", all(rc == OK for rc in rcs), str(rcs))
        with open(conc_path, encoding="utf-8") as fh:
            final_rows = parse_ledger_text(fh.read())
        check("concurrent-add-no-lost-rows", len(final_rows) == n, str(len(final_rows)))
        check("concurrent-add-unique-ids", len({r["id"] for r in final_rows}) == n, str([r["id"] for r in final_rows]))
        ran[0] += 3
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"SELFTEST OK: task_ledger {ran[0]}/{ran[0]} cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
