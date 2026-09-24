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
starts. Nothing here re-splits an ask into subtasks — the caller splits a
multi-ask message and calls `add` once per ask. A harness todo tool (e.g. a
per-session TodoWrite list) may mirror the ledger as a view, never act as a
second source.

Near-duplicates are never auto-refused and never auto-merged. When a new ask
clears the normalized-text similarity bar against an existing row, `add`
prints BOTH texts, adds nothing, and exits 1 until the caller re-runs with
`--same T-###` (the same ask: no row added) or `--new` (a distinct ask).
Two asks are treated as distinct automatically — no question asked — when
their numbers, their negation (not / never / no / don't / *n't), or their
file/format tokens (`report.csv`, `json`, `pdf`, ...) differ, because those
are exactly the edits a similarity ratio cannot see ("export 12 rows" vs
"export 13 rows"). A match against a `done` or `dropped-by-owner` row also
offers `reopen --id`.

Evidence is shape-checked, not trusted blindly: `done` requires a commit sha
(7-40 hex chars with at least one digit), a URL, a `#N` reference, or a test
id (`path::name` or `name[param]`); free prose ("looks good") is refused.
`block` requires an explicit `--party "<name/role>"` AND `--evidence`; the
party is never parsed out of the evidence text (a URL's `https:` is not a
party). `drop` requires the owner's own words (`--quote`). The shape check
proves the evidence has a checkable form, not that it is true.

TRANSITIONS (explicit table; anything else is refused with exit 1)
-------------------------------------------------------------------
  start    open                     -> doing   (repeat on `doing` is a no-op)
  done     open | doing             -> done    (evidence pattern required)
  block    open | doing             -> blocked (--party and --evidence)
  unblock  blocked                  -> open    (clears the block evidence;
                                                refused while a parked question
                                                on the row is unanswered)
  drop     open | doing | blocked   -> dropped-by-owner (--quote required)
  reopen   done | dropped-by-owner  -> open    (clears the old evidence)
So `done -> doing` is refused until `reopen`, and a blocked row must be
`unblock`ed before it is started again.

`status` is the only source of truth for a progress report — never memory,
never a paraphrase. Its exit 1 means "open asks exist" (informational), not
an error.

DATA MODEL — one markdown table, one row per ask
-------------------------------------------------
    | id | status | created | updated | ask | evidence | source |
id       T-### (T-001, T-002, ... never reused, never renumbered)
status   open | doing | blocked | done | dropped-by-owner
created  ISO-8601 UTC, set once at `add`
updated  ISO-8601 UTC, set on every transition
ask      the owner's words verbatim, sanitized to one table line (newlines
         collapsed to spaces; `|` and `\\` escaped on write, unescaped on
         read, so a row can never smuggle a second row or break the table)
evidence "-" until `done`/`block`/`drop` sets it: the done evidence, or
         "<party>: <evidence>" for a block, or `owner: "<quote>"` for a drop;
         `reopen`/`unblock` reset it to "-"
source   caller-supplied provenance (e.g. a message timestamp/id), "-" if
         omitted

The file always opens with a fixed title line, then the exact header and
separator rows above. The parser tolerates one hand-edit shape: a row with
MORE than seven cells (an unescaped `|` typed into a cell by hand) keeps its
first four and last two cells and joins the middle back into the ask with
" | " (so the text is kept, never dropped; a stray pipe typed into the
evidence/source cell lands in the ask instead). Any other deviation (too few
cells, bad id, unknown status, missing header) is MALFORMED and every command
fails closed (exit 2) rather than guessing at a repair.

LOCKING + ATOMICITY (concurrency-safe by construction)
-------------------------------------------------------
Every command takes an advisory lock on `<file>.lock` via `fcntl.flock`
(exclusive for a write command, shared for a read-only one) around the full
read-modify-write, so two write commands racing on the same ledger from
different processes can never interleave. Every write goes to a temp file in
the same directory (so `os.replace` is an atomic rename on the same
filesystem) — a crash mid-write leaves the previous version intact, never a
half-written file. `fcntl` is POSIX-only by design: this suite runs on
macOS/Linux hosts, not Windows.

EXIT CODES (fail closed)
-------------------------
  0  the command's normal-success verdict
  1  a business-rule stop that is not a bug: a near-duplicate `add` awaiting
     `--same`/`--new`, missing or mis-shaped evidence, a transition the table
     refuses, `status` finding open asks (informational), `reconcile`
     finding an owner ask missing from the ledger, `questions` finding
     pending questions (informational), or a question already answered
  2  a hard error: an unreadable/malformed ledger or questions file, an
     unknown `--id`/`--qid`, malformed `--transcript-asks` input, or bad CLI usage

USAGE
-----
  task_ledger.py [--file PATH] add --ask "<owner words>" [--source S] [--same T-### | --new]
  task_ledger.py [--file PATH] start   --id T-###
  task_ledger.py [--file PATH] done    --id T-### --evidence "<sha|URL|#N|path::test|test[param]>"
  task_ledger.py [--file PATH] block   --id T-### --party "<name/role>" --evidence "<why>"
  task_ledger.py [--file PATH] unblock --id T-###
  task_ledger.py [--file PATH] drop    --id T-### --quote "<owner words>"
  task_ledger.py [--file PATH] reopen  --id T-###
  task_ledger.py [--file PATH] next
  task_ledger.py [--file PATH] status
  task_ledger.py [--file PATH] reconcile --transcript-asks FILE
  task_ledger.py [--file PATH] defer   --id T-### --question "<q>" (--default "<choice taken>" | --park)
  task_ledger.py [--file PATH] questions
  task_ledger.py [--file PATH] answer  --qid Q-### --text "<owner answer>"
  task_ledger.py --selftest

`--file` defaults to `.claude/TASKS.md` (relative to the current directory).
`next` returns the oldest `doing` row first (finish what is started); only
when nothing is `doing` does it read `.claude/PRIORITY.md` (same directory as
the ledger) READ-ONLY, if present — one priority per line (an id or free
text), first line wins by id match then by normalized-text similarity —
and otherwise falls back to the oldest open row.
`next` also prints how many deferred owner questions are pending.
`defer` records a question for an absent owner in `QUESTIONS.jsonl` (same
directory as the ledger; one JSON object per line: id, item, question,
default, ts, answer) so the run never stalls on it: `--default` names the
choice the agent took and keeps working under; `--park` (for a destructive or
irreversible choice no standing grant covers) also blocks only that item on
the owner, so `next` skips it. `questions` prints the pending batch for the
owner (exit 1 = questions waiting, informational); `answer` records the
owner's reply and names `unblock` for a parked item. `defer` is refused
on a done/dropped row; `unblock` is refused while a parked question on the
row is unanswered.
`reconcile` reads `--transcript-asks` as JSON Lines, one `{"ask": "..."}`
object per line (extra keys ignored), and uses the same duplicate rule as
`add` (auto-distinct asks count as missing).
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
QID_RE = re.compile(r"^Q-\d{3,}$")
QUESTION_KEYS = ("id", "item", "question", "default", "ts", "answer")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)

# Auto-distinct signals: two asks that differ in any of these are different
# asks even when their similarity ratio is high.
_NUM_RE = re.compile(r"\d+(?:[.,]\d+)*")
_NEG_RE = re.compile(r"\b(?:not|never|no|dont)\b|n['\u2019]t\b", re.IGNORECASE)
_FORMAT_WORDS = frozenset(
    "csv tsv json jsonl yaml yml xml pdf xlsx xls docx pptx md html txt png jpg jpeg svg gif "
    "sql parquet zip".split()
)
_CODE_EXTS = "py js ts tsx jsx mjs cjs sh go rs rb java kt swift c cpp h css scss toml ini lock"
_FILE_TOKEN_RE = re.compile(
    r"(?<![\w/.-])(?:[\w.-]+/)*[\w-]+\.(?:" + "|".join(sorted(_FORMAT_WORDS) + _CODE_EXTS.split()) + r")\b",
    re.IGNORECASE,
)

# Evidence shapes `done` accepts (a checkable form, not proof it is true).
_SHA_RE = re.compile(r"(?<![0-9A-Za-z])(?=[0-9a-fA-F]*\d)[0-9a-fA-F]{7,40}(?![0-9A-Za-z])")
_URL_RE = re.compile(r"\bhttps?://[^\s/?#]+\S*", re.IGNORECASE)
_ISSUE_RE = re.compile(r"#\d+\b")
_TESTID_RE = re.compile(r"\S+::\S+|\b\w+\[[^\]\s][^\]]*\]")

# Explicit transition table: command -> (allowed source statuses, target status).
TRANSITIONS = {
    "start": (frozenset({"open"}), "doing"),
    "done": (frozenset({"open", "doing"}), "done"),
    "block": (frozenset({"open", "doing"}), "blocked"),
    "unblock": (frozenset({"blocked"}), "open"),
    "drop": (frozenset({"open", "doing", "blocked"}), "dropped-by-owner"),
    "reopen": (frozenset({"done", "dropped-by-owner"}), "open"),
}
_CLEARS_EVIDENCE = {"unblock", "reopen"}

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


def _valid_party(party: str) -> bool:
    """True iff `party` names someone: non-empty with at least one alphanumeric char. Pure."""
    party = (party or "").strip()
    return bool(party) and any(ch.isalnum() for ch in party)


def evidence_kind(evidence: str):
    """The first checkable evidence shape found in `evidence`, or None. Pure.

    Returns one of "sha" (7-40 hex chars containing at least one digit, so an
    all-letter English word such as "defaced" is not mistaken for a sha),
    "url" (http/https), "ref" (`#N`, e.g. `PR #42`), or "test"
    (`path::name` or `name[param]`). A shape match is a checkable form, not
    proof: a digits-only token of 7+ chars also passes as a sha.
    """
    text = evidence or ""
    for kind, rx in (("url", _URL_RE), ("sha", _SHA_RE), ("ref", _ISSUE_RE), ("test", _TESTID_RE)):
        if rx.search(text):
            return kind
    return None


def _distinct_signals(text: str):
    """(numbers, negated, file/format tokens) of an ask — the auto-distinct signals. Pure."""
    nums = frozenset(_NUM_RE.findall(text or ""))
    negated = bool(_NEG_RE.search(text or ""))
    files = {m.lower() for m in _FILE_TOKEN_RE.findall(text or "")}
    files |= {w for w in _normalize(text).split() if w in _FORMAT_WORDS}
    return nums, negated, frozenset(files)


def auto_distinct(a: str, b: str) -> bool:
    """True when two asks differ in numbers, negation, or file/format tokens. Pure.

    These are the edits a similarity ratio cannot see ("export 12 rows" vs
    "export 13 rows", "delete the cache" vs "do not delete the cache",
    "export CSV" vs "export JSON"), so such a pair is treated as two asks
    without asking the caller.
    """
    return _distinct_signals(a) != _distinct_signals(b)


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
    well-formed T-### id (unique), and a known status. One tolerated
    hand-edit: a row with MORE cells than the header (an unescaped `|` typed
    into a cell) keeps its first four and last two cells and joins the rest
    into the ask with " | ". Fail closed on any other deviation: this is the
    sole writer's format, so a mismatch means the file was hand-edited,
    truncated, or came from something else.
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
        if len(cells) > len(HEADER_CELLS):
            # A hand-typed unescaped `|`: keep the fixed-position cells and
            # join the middle back into the ask rather than dropping text.
            cells = cells[:4] + [" | ".join(cells[4:-2])] + cells[-2:]
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
    """The best-matching existing row for `ask`, or None. Pure.

    A row is a candidate only when it clears NEAR_DUP_THRESHOLD AND is not
    `auto_distinct` from `ask` (numbers, negation, and file/format tokens all
    agree); any status counts, so a match can be a done row.
    """
    best, best_ratio = None, 0.0
    for r in rows:
        if auto_distinct(ask, r["ask"]):
            continue
        ratio = _similarity(ask, r["ask"])
        if ratio > best_ratio:
            best, best_ratio = r, ratio
    return best if best is not None and best_ratio >= NEAR_DUP_THRESHOLD else None


def _now_iso(now: datetime = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_row(rows: list, task_id: str):
    return next((i for i, r in enumerate(rows) if r["id"] == task_id), None)


def do_add(rows: list, ask: str, source: str = None, now: datetime = None, same: str = None, new: bool = False):
    """Append one row for `ask`, or ask the caller to decide on a near-duplicate. Pure.

    Returns (code, message, new_rows). One ask = one row: this never splits
    `ask` itself — the caller splits a multi-ask message and calls this once
    per ask. A near-duplicate is never refused outright: without `same`/`new`
    the message prints both texts and exit 1 asks for `--same T-###` (no row
    added; OK) or `--new` (added regardless). A match against a done or
    dropped row also names `reopen`. `same` naming an unknown id, or both
    `same` and `new`, is an ERROR.
    """
    ask = (ask or "").strip()
    if not ask:
        return ERROR, "error: --ask must be non-empty", rows
    if same and new:
        return ERROR, "error: --same and --new are mutually exclusive", rows
    if same:
        idx = _find_row(rows, same)
        if idx is None:
            return ERROR, f"error: no such id {same}", rows
        row = rows[idx]
        msg = f"SAME {row['id']} [{row['status']}]: recorded as the existing ask; no row added"
        if row["status"] in RESOLVED_STATUSES:
            msg += f" -- run `reopen --id {row['id']}` to work it again"
        return OK, msg, rows
    if not new:
        dup = find_duplicate(rows, ask)
        if dup is not None:
            lines = [
                f"DECIDE: possible duplicate of {dup['id']} [{dup['status']}] -- nothing added",
                f"  new:      {ask}",
                f"  existing: {dup['ask']}",
                f"re-run with --same {dup['id']} (the same ask) or --new (a distinct ask)",
            ]
            if dup["status"] in RESOLVED_STATUSES:
                lines.append(f"or `reopen --id {dup['id']}` if the {dup['status']} ask must be worked again")
            return WARN, "\n".join(lines), rows
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


def do_transition(rows: list, task_id: str, cmd: str, evidence: str = None, party: str = None,
                  quote: str = None, now: datetime = None):
    """Apply command `cmd` to `task_id` per TRANSITIONS and the evidence rules. Pure.

    Returns (code, message, new_rows). `done` needs `evidence_kind(evidence)`;
    `block` needs a `_valid_party(party)` and non-empty `evidence` (stored as
    "<party>: <evidence>"); `drop` needs a non-empty owner `quote` (stored as
    `owner: "<quote>"`); `unblock`/`reopen` reset evidence to "-". A source
    status the table does not allow is refused (WARN) with the command that
    would unlock it; `start` on a `doing` row is an idempotent no-op (OK).
    """
    if cmd not in TRANSITIONS:
        return ERROR, f"error: unknown command {cmd}", rows
    idx = _find_row(rows, task_id)
    if idx is None:
        return ERROR, f"error: no such id {task_id}", rows
    allowed, target = TRANSITIONS[cmd]
    current = rows[idx]["status"]
    if cmd == "start" and current == "doing":
        return OK, f"DOING {task_id} (already doing; no change)", rows
    if current not in allowed:
        hint = ""
        if current in RESOLVED_STATUSES:
            hint = f"; run `reopen --id {task_id}` first"
        elif current == "blocked":
            hint = f"; run `unblock --id {task_id}` first"
        return WARN, f"REFUSED: cannot {cmd} {task_id} from '{current}'{hint}", rows
    evidence = (evidence or "").strip()
    if cmd == "done" and evidence_kind(evidence) is None:
        return WARN, (
            f"REFUSED: done requires --evidence with a sha (7-40 hex), a URL, a #N reference, "
            f"or a test id (path::name or name[param]) for {task_id}"
        ), rows
    stored = None
    if cmd == "done":
        stored = evidence
    elif cmd == "block":
        if not _valid_party(party) or not evidence:
            return WARN, (
                f'REFUSED: block requires --party "<name/role>" and --evidence "<why>", '
                f'e.g. --party owner --evidence "pricing decision pending", for {task_id}'
            ), rows
        stored = f"{party.strip()}: {evidence}"
    elif cmd == "drop":
        quote = (quote or "").strip()
        if not quote:
            return WARN, f'REFUSED: drop requires --quote "<the owner\'s own words>" for {task_id}', rows
        stored = f'owner: "{quote}"'
    row = dict(rows[idx])
    row["status"] = target
    row["updated"] = _now_iso(now)
    if cmd in _CLEARS_EVIDENCE:
        row["evidence"] = "-"
    elif stored is not None:
        row["evidence"] = stored
    new_rows = list(rows)
    new_rows[idx] = row
    return OK, f"{target.upper()} {task_id}", new_rows


def _oldest(rows: list):
    return min(rows, key=lambda r: (r["created"], r["id"]))


def pick_next(rows: list, priority_lines: list):
    """The single next row to work, or None. Pure.

    Order: (1) the oldest `doing` row — finish what is started; (2) among
    open rows, the first `priority_lines` entry that matches an open row's
    id exactly or, failing that, the open row whose ask best matches that
    line at or above PRIORITY_MATCH_THRESHOLD (lines tried in order); (3) the
    oldest open row by `created` (ties broken by id). Blocked and resolved
    rows are never returned.
    """
    doing = [r for r in rows if r["status"] == "doing"]
    if doing:
        return _oldest(doing)
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
    return _oldest(open_rows)


def status_summary(rows: list):
    """Counts line + up to STATUS_MAX_ROWS unresolved rows. Pure; returns (exit_code, lines).

    exit_code is OK only when every row is `done` or `dropped-by-owner`;
    WARN (exit 1) means "open asks exist" — informational, not an error.
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


def parse_questions_text(text: str) -> list:
    """Parse the questions file (JSON Lines, one question object per line). Pure.

    Raises LedgerError on any line that is not an object carrying exactly the
    QUESTION_KEYS with a Q-### id, so a hand-edit fails closed instead of
    silently dropping a question the owner has not seen.
    """
    questions = []
    for i, line in enumerate((text or "").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerError(f"questions line {i}: not valid JSON: {exc}") from None
        if not isinstance(obj, dict) or set(obj) != set(QUESTION_KEYS) or not QID_RE.match(str(obj["id"])):
            raise LedgerError(f"questions line {i}: expected keys {', '.join(QUESTION_KEYS)} with a Q-### id")
        questions.append(obj)
    return questions


def render_questions_text(questions: list) -> str:
    """Serialize questions to JSON Lines (the inverse of parse_questions_text). Pure."""
    return "".join(json.dumps({k: q[k] for k in QUESTION_KEYS}, ensure_ascii=False) + "\n" for q in questions)


def pending_questions(questions: list) -> list:
    """Questions the owner has not answered yet. Pure."""
    return [q for q in questions if q["answer"] is None]


def do_defer(rows: list, questions: list, task_id: str, question: str, default: str = None, park: bool = False,
             now: datetime = None):
    """Record a question for an absent owner without stalling the run. Pure.

    Returns (exit_code, message, new_rows, new_questions). Exactly one of
    `default` (the choice the agent took and keeps working under) or `park`
    is required. `park` blocks only this item on the owner (the `block`
    transition, so `next` skips it); the rest of the backlog stays workable.
    Refusals return the inputs unchanged: ERROR for bad input or an unknown
    id, WARN when the item is resolved (done/dropped). Parking an already
    blocked row records the question without another transition.
    """
    question = (question or "").strip()
    default = (default or "").strip()
    if not question:
        return ERROR, "error: --question is required", rows, questions
    if bool(default) == bool(park):
        return ERROR, "error: give exactly one of --default \"<choice taken>\" or --park", rows, questions
    idx = _find_row(rows, task_id)
    if idx is None:
        return ERROR, f"error: no such id {task_id}", rows, questions
    status = rows[idx]["status"]
    if status in RESOLVED_STATUSES:
        return WARN, f"REFUSED: {task_id} is {status}; `reopen --id {task_id}` first if it is live again", rows, questions
    qid = f"Q-{max((int(q['id'][2:]) for q in questions), default=0) + 1:03d}"
    new_rows = rows
    if park and status != "blocked":  # an already-blocked row stays as it is; the question is still recorded
        code, msg, new_rows = do_transition(rows, task_id, "block", evidence=f"{qid} parked: {question}", party="owner")
        if code != OK:
            return code, msg, rows, questions
    record = {"id": qid, "item": task_id, "question": question, "default": "parked" if park else default,
              "ts": _now_iso(now), "answer": None}
    tail = f"parked {task_id} (blocked on owner)" if park else f"default taken: {default}"
    return OK, f"deferred {qid} on {task_id}: {tail}; continue with `next`", new_rows, questions + [record]


def parked_question(questions: list, task_id: str):
    """Id of an unanswered parked question on `task_id`, or None. Pure; gates `unblock`."""
    return next((q["id"] for q in pending_questions(questions)
                 if q["item"] == task_id and q["default"] == "parked"), None)


def do_answer(questions: list, qid: str, text: str, rows: list = None):
    """Record the owner's answer to a pending question. Pure; returns (exit_code, message, new_questions).

    A parked question's item stays blocked until the caller runs `unblock`.
    The message names `unblock` only when `rows` shows the row still blocked
    by this question, so answering never silently restarts work and never
    nudges past another party's block.
    """
    text = (text or "").strip()
    if not text:
        return ERROR, "error: --text \"<owner answer>\" is required", questions
    idx = next((i for i, q in enumerate(questions) if q["id"] == qid), None)
    if idx is None:
        return ERROR, f"error: no such question {qid}", questions
    q = questions[idx]
    if q["answer"] is not None:
        return WARN, f"REFUSED: {qid} is already answered", questions
    new_questions = list(questions)
    new_questions[idx] = dict(q, answer=text)
    row = next((r for r in rows or [] if r["id"] == q["item"]), None)
    own_block = row is not None and row["status"] == "blocked" and f"{qid} parked" in row["evidence"]
    hint = f"; then unblock --id {q['item']}" if own_block else ""
    return OK, f"answered {qid} ({q['item']}){hint}", new_questions


def questions_summary(questions: list):
    """The owner's batch: a count line + one line per pending question. Pure; returns (exit_code, lines).

    WARN (exit 1) means "questions are waiting" — informational, like `status`.
    """
    pending = pending_questions(questions)
    lines = [f"questions: {len(pending)} pending"]
    lines += [f"{q['id']} {q['item']} ({q['ts']}) {q['question']} -- default: {q['default']}" for q in pending]
    return (WARN if pending else OK), lines


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


def _questions_path(path: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(path)), "QUESTIONS.jsonl")


def _read_questions(path: str) -> list:
    """Questions stored beside the ledger `path`; absent file -> []. Raises LedgerError when malformed."""
    qfile = _questions_path(path)
    if not os.path.isfile(qfile):
        return []
    with open(qfile, encoding="utf-8") as fh:
        return parse_questions_text(fh.read())


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

    p_add = sub.add_parser("add", help="append one row for one owner ask, verbatim")
    p_add.add_argument("--ask", required=True)
    p_add.add_argument("--source", default=None)
    dup_choice = p_add.add_mutually_exclusive_group()
    dup_choice.add_argument("--same", metavar="T-###", default=None,
                            help="the ask is the same as this existing row: add nothing")
    dup_choice.add_argument("--new", action="store_true", help="the ask is distinct: add it anyway")

    p = sub.add_parser("start", help="mark an open row 'doing'")
    p.add_argument("--id", required=True)
    p = sub.add_parser("done", help="mark a row 'done' (requires a sha|URL|#N|test-id --evidence)")
    p.add_argument("--id", required=True)
    p.add_argument("--evidence", default=None)
    p = sub.add_parser("block", help="mark a row 'blocked' (requires --party and --evidence)")
    p.add_argument("--id", required=True)
    p.add_argument("--party", default=None, help="who the block waits on (name or role)")
    p.add_argument("--evidence", default=None)
    p = sub.add_parser("drop", help="mark a row 'dropped-by-owner' (requires the owner's --quote)")
    p.add_argument("--id", required=True)
    p.add_argument("--quote", default=None)
    for name, help_text in (("reopen", "reopen a done/dropped row (clears evidence)"),
                            ("unblock", "return a blocked row to 'open' (clears evidence)")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--id", required=True)

    sub.add_parser("next", help="print the single next row: doing first, then priority, then oldest open")
    sub.add_parser("status", help="print counts + unresolved rows")
    p = sub.add_parser("defer", help="record a question for an absent owner; keep working (default) or park the item")
    p.add_argument("--id", required=True)
    p.add_argument("--question", required=True)
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument("--default", default=None, help="the choice taken; work continues under it")
    choice.add_argument("--park", action="store_true", help="block only this item on the owner")
    sub.add_parser("questions", help="print the pending owner questions as one batch")
    p = sub.add_parser("answer", help="record the owner's answer to a deferred question")
    p.add_argument("--qid", required=True)
    p.add_argument("--text", required=True)

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
                code, msg, new_rows = do_add(rows, args.ask, args.source, same=args.same, new=args.new)
                if code == OK:
                    _atomic_write(path, render_ledger_text(new_rows))
            print(msg)
            return code

        if args.cmd in TRANSITIONS:
            with _locked(path, exclusive=True):
                gate = parked_question(_read_questions(path), args.id) if args.cmd == "unblock" else None
                if gate:
                    print(f"REFUSED: {args.id} waits on parked question {gate}; "
                          f"record the owner's reply with `answer --qid {gate}` first")
                    return WARN
                rows = _read_rows(path)
                code, msg, new_rows = do_transition(
                    rows, args.id, args.cmd,
                    evidence=getattr(args, "evidence", None),
                    party=getattr(args, "party", None),
                    quote=getattr(args, "quote", None),
                )
                if code == OK and new_rows is not rows:
                    _atomic_write(path, render_ledger_text(new_rows))
            print(msg)
            return code

        if args.cmd == "next":
            with _locked(path, exclusive=False):
                rows = _read_rows(path)
                priority_lines = _read_priority_lines(path)
                pending = pending_questions(_read_questions(path))
            row = pick_next(rows, priority_lines)
            if row is None:
                print("next: none (nothing doing or open)")
            else:
                print(f"next: {row['id']} [{row['status']}] {row['ask']}")
                print(f"created: {row['created']} source: {row['source']}")
            if pending:
                print(f"questions pending: {len(pending)} (batch for the owner: `questions`)")
            return OK

        if args.cmd == "defer":
            with _locked(path, exclusive=True):
                rows = _read_rows(path)
                questions = _read_questions(path)
                code, msg, new_rows, new_questions = do_defer(rows, questions, args.id, args.question,
                                                              default=args.default, park=args.park)
                if code == OK:
                    # Ledger first: a crash between the two writes leaves a blocked
                    # row whose evidence still carries the question text.
                    if new_rows is not rows:
                        _atomic_write(path, render_ledger_text(new_rows))
                    _atomic_write(_questions_path(path), render_questions_text(new_questions))
            print(msg)
            return code

        if args.cmd == "questions":
            with _locked(path, exclusive=False):
                questions = _read_questions(path)
            code, lines = questions_summary(questions)
            for line in lines:
                print(line)
            return code

        if args.cmd == "answer":
            with _locked(path, exclusive=True):
                questions = _read_questions(path)
                code, msg, new_questions = do_answer(questions, args.qid, args.text, _read_rows(path))
                if code == OK:
                    _atomic_write(_questions_path(path), render_questions_text(new_questions))
            print(msg)
            return code

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
        print(f"error: malformed ledger or questions file beside {path}: {exc}")
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

    # -- add / near-duplicate decision (never an auto-refusal) ---------------
    code1, msg1, rows1 = do_add([], "Build the CSV export feature")
    check("add-ok", code1 == OK and rows1[0]["id"] == "T-001", f"{code1} {msg1}")
    code2, msg2, rows2 = do_add(rows1, "build csv export feature!!")
    check("near-dup-asks-for-decision", code2 == WARN and "DECIDE" in msg2 and "REFUSED" not in msg2, msg2)
    check("near-dup-prints-both-texts", "build csv export feature!!" in msg2 and "Build the CSV export feature" in msg2, msg2)
    check("near-dup-names-same-and-new", "--same T-001" in msg2 and "--new" in msg2, msg2)
    check("near-dup-adds-nothing", len(rows2) == 1, str(rows2))
    check("near-dup-open-row-no-reopen-offer", "reopen" not in msg2, msg2)
    code_same, msg_same, rows_same = do_add(rows1, "build csv export feature!!", same="T-001")
    check("same-flag-adds-nothing-ok", code_same == OK and len(rows_same) == 1 and "T-001" in msg_same, msg_same)
    code_same_bad, _, _ = do_add(rows1, "x", same="T-404")
    check("same-flag-unknown-id-errors", code_same_bad == ERROR, str(code_same_bad))
    code_both, _, _ = do_add(rows1, "x", same="T-001", new=True)
    check("same-and-new-errors", code_both == ERROR, str(code_both))
    code_new, _, rows_new = do_add(rows1, "build csv export feature!!", new=True)
    check("new-flag-adds-row", code_new == OK and rows_new[-1]["id"] == "T-002", str(rows_new))
    code3, _, rows3 = do_add(rows1, "Write onboarding docs")
    check("distinct-ask-gets-new-id", code3 == OK and rows3[-1]["id"] == "T-002", str(rows3))
    code_empty, _, _ = do_add([], "   ")
    check("empty-ask-errors", code_empty == ERROR, str(code_empty))
    # Auto-distinct: numbers, negation, file/format tokens differ -> added, no question.
    for label, first, second in (
        ("numbers", "Export 12 rows to the sheet", "Export 13 rows to the sheet"),
        ("negation-not", "Delete the stale cache files", "Do not delete the stale cache files"),
        ("negation-dont", "Retry the failed upload job", "Don't retry the failed upload job"),
        ("negation-never", "Email the weekly summary", "Never email the weekly summary"),
        ("format-word", "Build the CSV export feature", "Build the JSON export feature"),
        ("file-token", "Update config.yaml defaults", "Update config.toml defaults"),
    ):
        _, _, base_rows = do_add([], first)
        code_d, msg_d, rows_d = do_add(base_rows, second)
        check(f"auto-distinct[{label}]", code_d == OK and len(rows_d) == 2, msg_d)
    check("auto-distinct-same-signals-false", not auto_distinct("Export 12 rows", "export 12 rows!"))
    # A match against a done row offers reopen.
    done_rows = [dict(rows1[0], status="done", evidence="abc1234")]
    code_dd, msg_dd, _ = do_add(done_rows, "build csv export feature!!")
    check("near-dup-of-done-offers-reopen", code_dd == WARN and "reopen --id T-001" in msg_dd, msg_dd)
    code_sd, msg_sd, _ = do_add(done_rows, "build csv export feature!!", same="T-001")
    check("same-on-done-offers-reopen", code_sd == OK and "reopen --id T-001" in msg_sd, msg_sd)

    # -- evidence shapes -------------------------------------------------------
    for ev, kind in (("abc1234", "sha"), ("a" * 3 + "1" * 37, "sha"), ("https://example.com/pull/7", "url"),
                     ("PR #42", "ref"), ("tests/test_x.py::test_ok", "test"), ("test_ok[case1]", "test")):
        check(f"evidence-kind[{ev}]", evidence_kind(ev) == kind, str(evidence_kind(ev)))
    for ev in ("", "looks good to me", "defaced", "abc123", "done and dusted", "ship it []"):
        check(f"evidence-rejected[{ev}]", evidence_kind(ev) is None, str(evidence_kind(ev)))

    # -- transitions: explicit table + evidence rules --------------------------
    tid = rows1[0]["id"]
    code_start, _, rows_start = do_transition(rows1, tid, "start")
    check("start-needs-no-evidence", code_start == OK and rows_start[0]["status"] == "doing", str(code_start))
    code_again, _, rows_again = do_transition(rows_start, tid, "start")
    check("start-on-doing-is-noop", code_again == OK and rows_again is rows_start, str(code_again))
    code_done_bare, _, _ = do_transition(rows1, tid, "done", "")
    check("done-without-evidence-refused", code_done_bare == WARN, str(code_done_bare))
    code_done_prose, _, _ = do_transition(rows1, tid, "done", "looks good to me")
    check("done-prose-evidence-refused", code_done_prose == WARN, str(code_done_prose))
    code_done_ok, _, rows_done = do_transition(rows1, tid, "done", "PR #42")
    check("done-with-evidence-ok", code_done_ok == OK and rows_done[0]["evidence"] == "PR #42", str(rows_done))
    code_dd2, msg_dd2, _ = do_transition(rows_done, tid, "start")
    check("done-to-doing-refused-names-reopen", code_dd2 == WARN and "reopen --id" in msg_dd2, msg_dd2)
    code_re, _, rows_re = do_transition(rows_done, tid, "reopen")
    check("reopen-clears-evidence", code_re == OK and rows_re[0]["status"] == "open" and rows_re[0]["evidence"] == "-",
          str(rows_re))
    code_re_open, _, _ = do_transition(rows1, tid, "reopen")
    check("reopen-open-row-refused", code_re_open == WARN, str(code_re_open))
    code_block_noparty, _, _ = do_transition(rows1, tid, "block", "owner: pricing decision pending")
    check("block-without-party-flag-refused", code_block_noparty == WARN, str(code_block_noparty))
    code_block_url, _, _ = do_transition(rows1, tid, "block", "https://example.com/issues/9")
    check("block-url-is-not-a-party", code_block_url == WARN, str(code_block_url))
    code_block_noev, _, _ = do_transition(rows1, tid, "block", "", party="owner")
    check("block-without-evidence-refused", code_block_noev == WARN, str(code_block_noev))
    code_block_punct, _, _ = do_transition(rows1, tid, "block", "why", party=":::")
    check("block-party-needs-alnum", code_block_punct == WARN, str(code_block_punct))
    code_block_ok, _, rows_blocked = do_transition(rows1, tid, "block", "pricing decision pending", party="owner")
    check("block-with-party-ok", code_block_ok == OK and rows_blocked[0]["evidence"] == "owner: pricing decision pending",
          str(rows_blocked))
    code_bs, msg_bs, _ = do_transition(rows_blocked, tid, "start")
    check("blocked-to-doing-refused-names-unblock", code_bs == WARN and "unblock --id" in msg_bs, msg_bs)
    code_ub, _, rows_ub = do_transition(rows_blocked, tid, "unblock")
    check("unblock-clears-evidence", code_ub == OK and rows_ub[0]["status"] == "open" and rows_ub[0]["evidence"] == "-",
          str(rows_ub))
    code_drop_bare, _, _ = do_transition(rows1, tid, "drop")
    check("drop-without-quote-refused", code_drop_bare == WARN, str(code_drop_bare))
    code_drop, _, rows_drop = do_transition(rows_blocked, tid, "drop", quote="skip it, not needed")
    check("drop-with-quote-ok", code_drop == OK and rows_drop[0]["status"] == "dropped-by-owner"
          and rows_drop[0]["evidence"] == 'owner: "skip it, not needed"', str(rows_drop))
    code_drop_re, _, rows_drop_re = do_transition(rows_drop, tid, "reopen")
    check("reopen-dropped-ok", code_drop_re == OK and rows_drop_re[0]["status"] == "open", str(rows_drop_re))
    code_unknown, _, _ = do_transition(rows1, "T-999", "done", "abc1234")
    check("unknown-id-errors", code_unknown == ERROR, str(code_unknown))

    # -- next ordering: doing first, then priority, then oldest open ------------
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
    doing_rows = ordered_rows + [dict(ordered_rows[0], id="T-003", status="doing", created="2026-01-05T00:00:00Z",
                                      ask="Rotate the signing keys")]
    check("next-doing-beats-priority-and-oldest", pick_next(doing_rows, ["T-001"])["id"] == "T-003")
    check("next-skips-blocked", pick_next([dict(ordered_rows[1], status="blocked"), ordered_rows[0]], [])["id"] == "T-001")

    # -- defer / questions / answer: a question for an absent owner never stalls the run
    q_now = datetime(2026, 1, 3, tzinfo=timezone.utc)
    code_qd, msg_qd, rows_qd, qs_qd = do_defer(ordered_rows, [], "T-002", "Which date format?", default="ISO-8601",
                                               now=q_now)
    check("defer-default-records-question", code_qd == OK and len(qs_qd) == 1 and qs_qd[0]["id"] == "Q-001"
          and qs_qd[0]["item"] == "T-002" and qs_qd[0]["default"] == "ISO-8601"
          and qs_qd[0]["ts"] == "2026-01-03T00:00:00Z" and qs_qd[0]["answer"] is None, str(qs_qd))
    check("defer-default-keeps-item-workable", rows_qd is ordered_rows and pick_next(rows_qd, [])["id"] == "T-002",
          str(rows_qd))
    check("defer-default-says-continue-with-next", "ISO-8601" in msg_qd and "next" in msg_qd, msg_qd)
    code_qp, msg_qp, rows_qp, qs_qp = do_defer(ordered_rows, qs_qd, "T-002", "Drop the legacy table?", park=True)
    check("defer-park-blocks-item-on-owner", code_qp == OK and rows_qp[1]["status"] == "blocked"
          and rows_qp[1]["evidence"].startswith("owner: ") and "Q-002" in rows_qp[1]["evidence"], str(rows_qp))
    check("defer-park-records-parked", qs_qp[-1]["id"] == "Q-002" and qs_qp[-1]["default"] == "parked", str(qs_qp))
    _, _, _, qs_gap = do_defer(ordered_rows, [dict(qs_qd[0], id="Q-007")], "T-001", "Q?", default="x")
    check("defer-id-never-reused-after-hand-delete", qs_gap[-1]["id"] == "Q-008", str(qs_gap))
    check("next-skips-parked-item", pick_next(rows_qp, [])["id"] == "T-001", str(pick_next(rows_qp, [])))
    doing_parked = [dict(ordered_rows[1], status="doing"), ordered_rows[0]]
    _, _, rows_dp, _ = do_defer(doing_parked, [], "T-002", "Rename the bucket?", park=True)
    check("next-skips-parked-doing-item", pick_next(rows_dp, [])["id"] == "T-001", str(rows_dp))
    for label, kwargs in (("no-default-no-park", {}), ("both", {"default": "x", "park": True}),
                          ("empty-question", {"default": "x", "question": "  "}),
                          ("unknown-id", {"default": "x", "task_id": "T-404"})):
        args = {"task_id": "T-001", "question": "Q?"} | kwargs
        code_bad, _, rows_bad, qs_bad = do_defer(ordered_rows, [], args.pop("task_id"), args.pop("question"), **args)
        check(f"defer-refused[{label}]", code_bad == ERROR and rows_bad is ordered_rows and qs_bad == [], str(code_bad))
    code_pd, _, rows_pd, qs_pd = do_defer([dict(ordered_rows[0], status="done")], [], "T-001", "Q?", park=True)
    check("defer-park-on-done-refused-records-nothing", code_pd == WARN and qs_pd == [], str(code_pd))
    code_dd3, _, _, qs_dd3 = do_defer([dict(ordered_rows[0], status="done")], [], "T-001", "Q?", default="x")
    check("defer-default-on-resolved-refused", code_dd3 == WARN and qs_dd3 == [], str(code_dd3))
    vendor_blocked = [dict(ordered_rows[0], status="blocked", evidence="vendor: API key pending")]
    code_pb, msg_pb, rows_pb, qs_pb = do_defer(vendor_blocked, [], "T-001", "Delete the cache?", park=True)
    check("defer-park-on-blocked-records-without-transition", code_pb == OK and rows_pb is vendor_blocked
          and qs_pb[0]["default"] == "parked", msg_pb)
    check("answer-on-already-blocked-no-unblock-nudge",
          "unblock" not in do_answer(qs_pb, "Q-001", "yes", vendor_blocked)[1], do_answer(qs_pb, "Q-001", "yes", vendor_blocked)[1])
    check("parked-question-gates-item", parked_question(qs_qp, "T-002") == "Q-002" and parked_question(qs_qp, "T-001") is None)
    code_ql, lines_ql = questions_summary(qs_qp)
    check("questions-pending-exits-warn", code_ql == WARN and lines_ql[0] == "questions: 2 pending", str(lines_ql))
    check("questions-lists-default-and-item", "T-002" in lines_ql[1] and "ISO-8601" in lines_ql[1]
          and "parked" in lines_ql[2], str(lines_ql))
    code_ans, msg_ans, qs_ans = do_answer(qs_qp, "Q-002", "yes, drop it", rows_qp)
    check("answer-resolves-and-names-unblock", code_ans == OK and qs_ans[1]["answer"] == "yes, drop it"
          and "unblock --id T-002" in msg_ans, msg_ans)
    check("questions-after-answer", questions_summary(qs_ans)[1][0] == "questions: 1 pending")
    check("parked-question-cleared-by-answer", parked_question(qs_ans, "T-002") is None)
    check("answer-twice-refused", do_answer(qs_ans, "Q-002", "again")[0] == WARN)
    check("answer-needs-text", do_answer(qs_qp, "Q-001", " ")[0] == ERROR)
    check("answer-unknown-id-errors", do_answer(qs_qp, "Q-404", "x")[0] == ERROR)
    check("questions-none-exits-ok", questions_summary([])[0] == OK)
    check("questions-jsonl-round-trip", parse_questions_text(render_questions_text(qs_ans)) == qs_ans)
    for bad in ("not json", '{"id": "Q-001"}', '[1, 2]'):
        try:
            parse_questions_text(bad)
            failures.append(f"questions-malformed-detected[{bad}]: no LedgerError raised")
        except LedgerError:
            pass
        ran[0] += 1

    # -- status ---------------------------------------------------------------
    mixed =ordered_rows + [dict(ordered_rows[0], id="T-003", status="done", ask="Ship the release")]
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
    raw_pipe = TITLE_LINE + "\n" + HEADER_LINE + "\n" + SEP_LINE + "\n| T-001 | open | t | t | A | B | C | - | src |"
    tolerant = parse_ledger_text(raw_pipe)
    check("parser-tolerates-unescaped-pipe", tolerant[0]["ask"] == "A | B | C" and tolerant[0]["source"] == "src",
          str(tolerant))
    rt2 = parse_ledger_text(render_ledger_text(tolerant))
    check("unescaped-pipe-re-escaped-on-write", rt2 == tolerant, str(rt2))
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

        # -- I/O: defer --park via the CLI writes both files; `next` skips the
        #    parked item and reports the pending count; `questions` exits 1.
        q_path = os.path.join(tmpdir, "Q.md")
        with contextlib.redirect_stdout(io.StringIO()):
            main(["--file", q_path, "add", "--ask", "Migrate the billing database"])
            main(["--file", q_path, "add", "--ask", "Write the onboarding guide"])
            rc_defer = main(["--file", q_path, "defer", "--id", "T-001", "--question", "Drop old table?", "--park"])
        next_buf = io.StringIO()
        with contextlib.redirect_stdout(next_buf):
            main(["--file", q_path, "next"])
            rc_q = main(["--file", q_path, "questions"])
        out = next_buf.getvalue()
        check("cli-defer-park-ok", rc_defer == OK and os.path.isfile(os.path.join(tmpdir, "QUESTIONS.jsonl")), str(rc_defer))
        check("cli-next-skips-parked-and-counts", "next: T-002" in out and "questions pending: 1" in out, out)
        check("cli-questions-exits-warn", rc_q == WARN and "Q-001 T-001" in out, out)
        ub_buf = io.StringIO()
        with contextlib.redirect_stdout(ub_buf):
            rc_ub_early = main(["--file", q_path, "unblock", "--id", "T-001"])
            main(["--file", q_path, "answer", "--qid", "Q-001", "--text", "archive it instead"])
            rc_ub_late = main(["--file", q_path, "unblock", "--id", "T-001"])
        check("cli-unblock-refused-while-parked-question-pending", rc_ub_early == WARN and "answer --qid Q-001"
              in ub_buf.getvalue(), ub_buf.getvalue())
        check("cli-unblock-ok-after-answer", rc_ub_late == OK, ub_buf.getvalue())

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
