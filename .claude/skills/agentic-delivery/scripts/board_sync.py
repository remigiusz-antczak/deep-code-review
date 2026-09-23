#!/usr/bin/env python3
"""board_sync.py — read a coordination issue from a per-agent cursor, never the tail.

WHY THIS EXISTS (the failure it closes)
---------------------------------------
Agent sessions coordinating on one GitHub issue tend to read it with
`gh issue view <n>`. On a terminal that prints the issue body plus only the
NEWEST comment ("Not showing N comments"); off a terminal it prints the body
alone. So an agent following that command reads a one-comment window and
misses every claim, correction, and collision flag posted in between — and the
only full alternative (`--comments`) re-reads the whole thread every loop,
which on a long-running board costs hundreds of thousands of tokens. This
script reads exactly what this agent has not yet seen, prints it as a compact
digest, and only then records that it was read.

WHAT IT DOES
------------
1. Loads this agent's cursor: `{agent_id, last_comment_id, updated_at, seen}`
   where `updated_at` is the newest comment `updated_at` already read and
   `seen` maps recently-read comment ids to the `updated_at` they had.
2. Fetches `repos/{o}/{r}/issues/{n}/comments?since=<updated_at - overlap>`
   with `gh api --paginate` (every page, not the first 30). GitHub's `since`
   filters on LAST-UPDATED time, so an old comment that was edited comes back
   again; the overlap re-reads a short window so a comment the API had not yet
   indexed at the previous read is not skipped.
3. Classifies each fetched comment by id: unseen and newer than the cursor ->
   new; seen with a different `updated_at` (or older than the cursor, not in
   the recent window, and edited) -> edited; otherwise already read. Duplicate
   rows are collapsed by id.
4. Prints the digest: total comment count, "N unread", then one line per
   unread comment (id, UTC time, author, TYPE, refs, first body line). BLOCKER,
   DECISION, and posts handed `to:` this agent are pinned first; typed chatter
   (STATUS/ACK/READY/LANDED) is collapsed to a list of ids — accounted for,
   not expanded. Untyped comments are always shown in full: unknown content
   is never hidden.
5. Only after the digest is fully written and flushed, atomically replaces the
   cursor file. That advance IS the read receipt. A failed fetch, a truncated
   first read, or a failed write of the digest leaves the cursor untouched, so
   the next run shows the same comments again (at-least-once, never skipped).

FAIL-CLOSED RULES
-----------------
- `gh` error or undecodable output -> exit 2, cursor unchanged.
- First read (no cursor) that returns fewer comments than the issue's own
  comment count -> exit 2 (pagination was truncated), cursor unchanged.
- Corrupt cursor file, or one written for a different agent id -> exit 2; the
  message says to delete it, which forces a full first read.

The cursor lives outside the repository (default `$BOARD_CURSOR_DIR`, else
`~/.cache/board-sync`), one file per repo+issue+agent, so it is never
committed and never shared between agents.

USAGE
-----
  board_sync.py --repo OWNER/NAME --issue N --agent ID [--cursor-dir DIR] [--no-advance]
  board_sync.py --selftest

Exit codes: 0 digest printed (cursor advanced unless --no-advance); 2 error.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_common as bc  # noqa: E402  (sibling module, path set above)

OK = 0
ERROR = 2

# Re-read window before the cursor's high-water mark. Covers a comment that the
# API had not indexed when the previous read ran (eventual consistency) and the
# `since` boundary's inclusive/exclusive ambiguity; re-read rows are deduped by
# id, so the overlap costs a few repeated rows, never a repeated report.
OVERLAP_SECONDS = 600
PRIORITY_TYPES = ("BLOCKER", "DECISION")


class CursorError(Exception):
    """The cursor file exists but cannot be trusted."""


def default_cursor_dir() -> str:
    """Cursor directory: $BOARD_CURSOR_DIR, else ~/.cache/board-sync. Pure."""
    return os.environ.get("BOARD_CURSOR_DIR") or os.path.join(os.path.expanduser("~"), ".cache", "board-sync")


def cursor_file(cursor_dir: str, repo: str, issue: int, agent: str) -> str:
    """Path of one agent's cursor for one board. Pure."""
    return os.path.join(cursor_dir, f"{repo.replace('/', '__')}__{issue}__{agent}.json")


def load_cursor(path: str, agent: str):
    """Return the cursor dict, None when absent, or raise CursorError.

    Side-effects: reads `path`. A file that is not a JSON object with the
    expected fields, or that belongs to another agent id, raises: silently
    starting over would re-flood the reader, silently trusting it could skip.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            cur = json.load(fh)
        ok = (
            isinstance(cur, dict)
            and cur.get("agent_id") == agent
            and isinstance(cur.get("last_comment_id"), int)
            and isinstance(cur.get("seen"), dict)
        )
        if ok and cur.get("updated_at"):
            bc.parse_ts(cur["updated_at"])
    except (OSError, ValueError) as exc:
        raise CursorError(f"unreadable cursor {path}: {exc}; delete it to force a full first read") from exc
    if not ok:
        raise CursorError(f"cursor {path} is malformed or belongs to another agent; delete it to force a full first read")
    return cur


def save_cursor(path: str, cursor: dict) -> None:
    """Atomically write the cursor (temp file + os.replace). Side-effects: disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".cursor-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(cursor, fh, sort_keys=True)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def since_param(cursor) -> str:
    """The `since=` value for a cursor: its high-water minus the overlap, or ''. Pure."""
    if not cursor or not cursor.get("updated_at"):
        return ""
    return bc.format_ts(bc.parse_ts(cursor["updated_at"]) - timedelta(seconds=OVERLAP_SECONDS))


def classify(fetched: list, cursor) -> tuple:
    """Split fetched comments into (new, edited), each sorted by id. Pure.

    Rows are first collapsed by id (keeping the newest updated_at), so a
    comment repeated across overlapping pages is reported once. With no cursor
    every comment is new.
    """
    by_id = {}
    for c in fetched:
        prev = by_id.get(c["id"])
        if prev is None or c["updated_at"] > prev["updated_at"]:
            by_id[c["id"]] = c
    if not cursor:
        return sorted(by_id.values(), key=lambda c: c["id"]), []
    last, seen = cursor["last_comment_id"], cursor["seen"]
    new, edited = [], []
    for cid in sorted(by_id):
        c = by_id[cid]
        known = seen.get(str(cid))
        if known is not None:
            if known != c["updated_at"]:
                edited.append(c)
        elif cid > last:
            new.append(c)
        elif c["updated_at"] != c["created_at"]:
            edited.append(c)  # read long ago (pruned from the window) and edited since
        else:
            new.append(c)  # a straggler the previous read never received
    return new, edited


def next_cursor(agent: str, fetched: list, cursor) -> dict:
    """The cursor to store after this read. Pure.

    `last_comment_id`/`updated_at` only ever move forward. `seen` keeps every
    comment whose updated_at falls inside the overlap window before the new
    high-water mark — exactly the rows the next read can return without their
    having changed — so it stays small no matter how long the board grows.
    """
    last = cursor["last_comment_id"] if cursor else 0
    high = cursor.get("updated_at", "") if cursor else ""
    seen = dict(cursor["seen"]) if cursor else {}
    for c in fetched:
        last = max(last, c["id"])
        high = max(high, c["updated_at"])
        seen[str(c["id"])] = max(seen.get(str(c["id"]), ""), c["updated_at"])
    floor = bc.format_ts(bc.parse_ts(high) - timedelta(seconds=OVERLAP_SECONDS)) if high else ""
    seen = {k: v for k, v in seen.items() if v >= floor}
    return {"agent_id": agent, "last_comment_id": last, "updated_at": high, "seen": seen}


def digest_line(c: dict, edited: bool) -> str:
    """One compact digest line for a comment. Pure."""
    post = bc.parse_header(bc.first_line(c["body"]))
    if post is None:
        who, what, refs, text = f"@{c['user']['login']}", "untyped", "", bc.snippet(c["body"], False)
    else:
        who = f"agent:{post['agent']}"
        what = post["type"] + ("(malformed)" if post["errors"] else "")
        refs = f" refs:{post['refs']}" if post["refs"] else ""
        text = bc.snippet(c["body"], True)
    return f"  {c['id']} {c['created_at']} {who} {what}{refs}{' [edited]' if edited else ''} | {text}"


def render_digest(repo: str, issue: int, agent: str, total: int, new: list, edited: list, cursor) -> str:
    """The digest text for one read. Pure."""
    edited_ids = {c["id"] for c in edited}
    unread = sorted(new + edited, key=lambda c: c["id"])
    priority, normal, chatter = [], [], []
    for c in unread:
        post = bc.parse_header(bc.first_line(c["body"]))
        if post and post["type"] in bc.CHATTER_TYPES:
            chatter.append(str(c["id"]))
        elif post and not post["errors"] and (post["type"] in PRIORITY_TYPES or post["fields"].get("to") == agent):
            priority.append(c)
        else:
            normal.append(c)
    since = cursor["last_comment_id"] if cursor else "none (first read: full range)"
    out = [
        f"board {repo}#{issue}: {total} comments total; {len(unread)} unread "
        f"({len(new)} new, {len(edited)} edited) since cursor {since}"
    ]
    if priority:
        out.append("PRIORITY:")
        out += [digest_line(c, c["id"] in edited_ids) for c in priority]
    if normal:
        out.append("UNREAD:")
        out += [digest_line(c, c["id"] in edited_ids) for c in normal]
    if chatter:
        out.append(f"CHATTER ({len(chatter)}, forge-derivable, not expanded): ids {','.join(chatter)}")
    return "\n".join(out) + "\n"


def sync(repo: str, issue: int, agent: str, cursor_dir: str, runner, out, advance: bool = True) -> int:
    """Fetch, print the digest to `out`, then advance the cursor. Returns an exit code.

    Side-effects: `gh` calls through `runner`, writes to `out`, and (only after
    `out` was written and flushed without error, and only when `advance`)
    replaces the cursor file.
    """
    path = cursor_file(cursor_dir, repo, issue, agent)
    try:
        cursor = load_cursor(path, agent)
        total = bc.gh_object(runner, f"repos/{repo}/issues/{issue}").get("comments")
        if not isinstance(total, int):
            raise bc.ForgeError("issue JSON has no integer comments count")
        fetched = bc.gh_list(runner, bc.comments_path(repo, issue, since_param(cursor)))
        for c in fetched:
            if not (isinstance(c, dict) and isinstance(c.get("id"), int) and c.get("updated_at") and c.get("created_at")):
                raise bc.ForgeError("a comment row lacks id/created_at/updated_at")
    except (CursorError, bc.ForgeError) as exc:
        print(f"board_sync: {exc}; cursor NOT advanced", file=sys.stderr)
        return ERROR
    if cursor is None and len({c["id"] for c in fetched}) < total:
        print(
            f"board_sync: first read returned {len({c['id'] for c in fetched})} of {total} comments "
            "(truncated pagination); cursor NOT advanced",
            file=sys.stderr,
        )
        return ERROR
    new, edited = classify(fetched, cursor)
    try:
        out.write(render_digest(repo, issue, agent, total, new, edited, cursor))
        out.flush()
    except (OSError, ValueError) as exc:
        print(f"board_sync: digest not delivered ({exc}); cursor NOT advanced", file=sys.stderr)
        return ERROR
    if not advance:
        return OK
    try:
        save_cursor(path, next_cursor(agent, fetched, cursor))
    except OSError as exc:
        print(f"board_sync: digest printed but cursor not saved ({exc}); next read repeats it", file=sys.stderr)
        return ERROR
    return OK


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

T0 = "2026-01-05T10:00:00Z"


def _ts(minutes: int) -> str:
    return bc.format_ts(bc.parse_ts(T0) + timedelta(minutes=minutes))


def _board(n: int = 130):
    """A fixture board: n comments across two pages, a mix of typed, chatter, untyped."""
    bodies = [
        "[agent:alpha] CLAIM refs:#{i} ttl:60\ntaking item {i}",
        "[agent:beta] STATUS refs:-\nstill working",
        "plain untyped note {i}",
        "[agent:beta] BLOCKER refs:#{i} topic:ratchet\nmain is red on the ratchet check",
    ]
    return bc.FakeGh([bc.make_comment(1000 + i, bodies[i % 4].format(i=i), _ts(i)) for i in range(n)])


class _BrokenOut(io.StringIO):
    def write(self, s):
        raise OSError("broken pipe")


def _selftest() -> int:
    tmp = tempfile.mkdtemp(prefix="board-sync-selftest-")
    state = {}

    def run(gh, advance=True, out=None, agent="gamma"):
        buf = out if out is not None else io.StringIO()
        rc = sync("acme/board", 7, agent, tmp, gh, buf, advance)
        return rc, buf.getvalue() if not isinstance(buf, _BrokenOut) else ""

    cpath = cursor_file(tmp, "acme/board", 7, "gamma")

    def first_read():
        gh = _board()
        state["gh"] = gh
        rc, text = run(gh)
        cur = load_cursor(cpath, "gamma")
        pages = [c for c in gh.calls if c[:3] == ["gh", "api", "--paginate"]]
        ok = (
            rc == OK and "130 unread (130 new, 0 edited)" in text and cur["last_comment_id"] == 1129
            and "since=" not in pages[0][3] and "per_page=100" in pages[0][3]
            and "CHATTER (33" in text and "1129" in text and "1000" in text
        )
        return ok, text[:300]

    def priority_pinned():
        rc, text = run(_board(8), advance=False, agent="delta")
        head = text.split("UNREAD:")[0]
        return rc == OK and "PRIORITY:" in head and "BLOCKER" in head and "CLAIM" not in head, text

    def second_read_empty():
        rc, text = run(state["gh"])
        pages = [c for c in state["gh"].calls if c[:3] == ["gh", "api", "--paginate"]]
        return rc == OK and "0 unread" in text and "since=" in pages[-1][3], text

    def new_and_edited():
        gh = state["gh"]
        gh.comments.append(bc.make_comment(1130, "[agent:alpha] RELEASE refs:#0\ndone with it", _ts(200)))
        old = next(c for c in gh.comments if c["id"] == 1001)
        old["body"], old["updated_at"] = "[agent:beta] STATUS refs:-\nedited text", _ts(201)
        rc, text = run(gh)
        ok = rc == OK and "2 unread (1 new, 1 edited)" in text and "1130" in text and "CHATTER (1" in text
        return ok, text

    def edited_old_outside_window():
        gh = state["gh"]
        old = next(c for c in gh.comments if c["id"] == 1002)
        old["body"], old["updated_at"] = "untyped but edited long after", _ts(500)
        rc, text = run(gh)
        return rc == OK and "1 unread (0 new, 1 edited)" in text and "[edited]" in text, text

    def reread_after_advance_empty():
        rc, text = run(state["gh"])
        return rc == OK and "0 unread" in text, text

    def straggler_surfaces():
        gh = state["gh"]
        gh.comments.append(bc.make_comment(1140, "newest", _ts(505)))
        rc1, _ = run(gh)
        gh.comments.append(bc.make_comment(1135, "late-indexed note", _ts(504)))  # id below the cursor
        rc, text = run(gh)
        cur = load_cursor(cpath, "gamma")
        ok = rc1 == rc == OK and "1 unread (1 new, 0 edited)" in text and "1135" in text and cur["last_comment_id"] == 1140
        return ok, text

    def no_advance_flag():
        gh = state["gh"]
        before = open(cpath).read()
        gh.comments.append(bc.make_comment(1141, "peek me", _ts(600)))
        rc, text = run(gh, advance=False)
        rc2, text2 = run(gh, advance=False)
        return rc == OK and open(cpath).read() == before and "1141" in text and "1141" in text2, text2

    def fetch_failure_keeps_cursor():
        gh = state["gh"]
        before = open(cpath).read()
        gh.fail = True
        rc, _ = run(gh)
        gh.fail = False
        return rc == ERROR and open(cpath).read() == before, "cursor moved on failure"

    def broken_output_keeps_cursor():
        gh = state["gh"]
        before = open(cpath).read()
        rc, _ = run(gh, out=_BrokenOut())
        rc2, text = run(gh)
        return rc == ERROR and before != open(cpath).read() and "1141" in text and rc2 == OK, text

    def truncated_first_read_refused():
        gh = _board(130)
        real = gh.__call__

        def one_page(args, cwd=None):
            rc, out, err = real(args, cwd)
            if args[:3] == ["gh", "api", "--paginate"]:
                out = out.split("][")[0] + "]"
            return rc, out, err

        rc = sync("acme/board", 8, "gamma", tmp, one_page, io.StringIO())
        return rc == ERROR and not os.path.exists(cursor_file(tmp, "acme/board", 8, "gamma")), f"rc={rc}"

    def foreign_cursor_refused():
        path = cursor_file(tmp, "acme/board", 9, "gamma")
        save_cursor(path, {"agent_id": "someone-else", "last_comment_id": 1, "updated_at": T0, "seen": {}})
        rc = sync("acme/board", 9, "gamma", tmp, _board(3), io.StringIO())
        return rc == ERROR, f"rc={rc}"

    def terminal_escape_stripped():
        gh = bc.FakeGh([bc.make_comment(1, "hi \x1b[2J\x07there", T0)])
        buf = io.StringIO()
        sync("acme/board", 10, "gamma", tmp, gh, buf)
        return "\x1b" not in buf.getvalue() and "hi [2Jthere" in buf.getvalue(), repr(buf.getvalue())

    cases = [
        ("first-read-full-range-130-across-pages", first_read),
        ("priority-types-pinned-first", priority_pinned),
        ("second-read-uses-since-and-is-empty", second_read_empty),
        ("new-and-edited-reported-once", new_and_edited),
        ("edit-outside-window-still-reported", edited_old_outside_window),
        ("cursor-advance-is-read-receipt", reread_after_advance_empty),
        ("straggler-below-high-water-surfaces", straggler_surfaces),
        ("no-advance-peeks-without-receipt", no_advance_flag),
        ("fetch-failure-keeps-cursor", fetch_failure_keeps_cursor),
        ("undelivered-digest-keeps-cursor", broken_output_keeps_cursor),
        ("truncated-first-read-refused", truncated_first_read_refused),
        ("foreign-cursor-refused", foreign_cursor_refused),
        ("terminal-escapes-stripped", terminal_escape_stripped),
    ]
    saved, sys.stderr = sys.stderr, io.StringIO()  # expected fail-closed messages stay out of the log
    try:
        return bc.run_checks("board_sync", cases)
    finally:
        sys.stderr = saved


def main(argv=None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--repo")
    parser.add_argument("--issue", type=int)
    parser.add_argument("--agent")
    parser.add_argument("--cursor-dir", default=None)
    parser.add_argument("--no-advance", action="store_true", help="print the digest without recording a read receipt")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not (args.repo and bc.validate_repo(args.repo) and args.issue and args.issue > 0 and bc.validate_agent(args.agent or "")):
        parser.print_usage(sys.stderr)
        print("board_sync: --repo OWNER/NAME, --issue N (>0) and a valid --agent are required", file=sys.stderr)
        return ERROR
    return sync(args.repo, args.issue, args.agent, args.cursor_dir or default_cursor_dir(), bc.default_runner,
                sys.stdout, advance=not args.no_advance)


if __name__ == "__main__":
    sys.exit(main())
