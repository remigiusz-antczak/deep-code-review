#!/usr/bin/env python3
"""board_state.py — render a coordination issue's current state into its body.

WHY THIS EXISTS (the failure it closes)
---------------------------------------
A coordination issue whose body is never updated holds no state, only a
stream: "who holds what", "what is broken", and "what waits on the owner" can
only be recovered by replaying every comment, so a session joining mid-run
either pays for a full read or acts on a stale body. This script folds the
typed posts (see board_common.py for the grammar; board_post.py writes them)
into one deterministic state record and writes it into the issue body between
two markers, so the body IS the current state and the stream is its log.

WHAT THE RECORD HOLDS
---------------------
- Claims with TTL. A CLAIM holds each ref for `ttl:` minutes (default
  DEFAULT_TTL_MINUTES); the holder re-posting CLAIM renews it (a heartbeat)
  and keeps its first claim's id and time, which tie-break verdicts cite.
  A CLAIM on a ref another agent holds unexpired does not take it: the first
  valid claim holds and the later one is listed as contested. An expired
  claim is marked EXPIRED and reclaimable by the next CLAIM. RELEASE by the
  holder frees the ref (with or without `rule:`); HANDOFF by the holder moves
  it to `to:`. A RELEASE by an agent that contested the ref is its stand-down
  and clears its contested row; any other RELEASE or HANDOFF from a
  non-holder changes nothing and is listed as ignored.
- Known issues, keyed by `topic:` (else the refs). BLOCKER opens an entry;
  FIX-CLAIM marks it fix-claimed with its sha/test; a BLOCKER after a
  FIX-CLAIM on the same key reopens it and counts a recurrence, so "fixed for
  good, then red again" is visible in the record, not buried in the stream.
- Owner-gated items: QUESTION or BLOCKER carrying `gate:owner`, open until a
  DECISION or ANSWER cites it with `of:<comment id>`. Plus open (ungated)
  questions and the last RECENT_DECISIONS decisions.
- Audit verdicts: an AUDIT post records one peer's measured `verdict:`
  (gap / done / na) per ref at `sha:`; the latest posted AUDIT on a ref wins
  (comment order, not commit age), so a fresh post supersedes an older one.

THE BACKLOG VIEW (--backlog --head SHA)
---------------------------------------
One agent measures, every agent consumes: before spawning a worker, print the
audited refs as a dispatch list instead of re-measuring them. Each ref is
exactly one of DISPATCH (gap, measured at --head, unclaimed or claim
expired), REVERIFY (any verdict measured at another sha: spot-check that it
still holds at head before acting; do not re-measure from scratch), CLAIMED
(gap under a live claim), or SKIP (done / na measured at head: nothing to
build; a live claim on it is flagged as a likely duplicate dispatch). --head
is required and must be a lowercase hex sha of 7-40 chars, since an audit row
is only as current as the commit it measured. Sha comparison is
by prefix, so REVERIFY means "not measured at this exact head", never a
judgement of how far behind. A ref no AUDIT names is not listed: the view is
the audited backlog, not every open item.

PROPERTIES
----------
- Deterministic: comments are processed in id order, every list is sorted,
  and the record carries no render timestamp — the same comments and the same
  clock minute give byte-identical output. The only clock input is claim
  expiry.
- Guarded, not atomic, write: the forge offers no compare-and-swap on an
  issue body, so a writer that folded fewer comments could overwrite a newer
  record. --write therefore re-reads the issue right before the PATCH and,
  if the body or the comment count changed since the fold, sends nothing and
  exits 3 (conflict: rerun). A narrow window between that re-read and the
  PATCH remains; rerun after any new post rather than trusting convergence.
- Idempotent write: text outside the markers is preserved byte-for-byte; if
  the spliced body equals the current body, no PATCH is sent.
- Fail closed: a `gh` error, a comment list shorter than the issue's own
  count (truncated pagination), or malformed markers (one without the other,
  duplicates, end before start) exits 2 and writes nothing.
- Peer text is data: only grammar-validated fields (ids, refs, topics, shas)
  and sanitised one-line snippets reach the record, so a comment cannot close
  the markers or inject markup.

LIMITS: the forge account is shared, so a DECISION is attributed by its
`[agent:]` tag, not verified as the owner's; and a FIX-CLAIM that bypassed
board_post.py was never git-verified — the record says "fix-claimed", not
"fixed".

USAGE
-----
  board_state.py --repo OWNER/NAME --issue N [--now 2026-01-05T10:00:00Z]          # print record
  board_state.py --repo OWNER/NAME --issue N --write                                # splice into body
  board_state.py --repo OWNER/NAME --issue N --backlog --head <mainline sha>        # dispatch list
  board_state.py --selftest

Exit codes: 0 rendered (and written, or unchanged); 2 error; 3 the issue
changed between the read and the write (nothing written; rerun).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_common as bc  # noqa: E402  (sibling module, path set above)

OK = 0
ERROR = 2
CONFLICT = 3

START = "<!-- board-state:start -->"
END = "<!-- board-state:end -->"
RECENT_DECISIONS = 5


class MarkerError(Exception):
    """The issue body's state markers are malformed; refuse to guess a splice."""


def fold(comments: list, now: datetime) -> dict:
    """Fold comments into the state dict. Pure: no I/O.

    Comments are sorted by id first, so input order never changes the result.
    Only posts whose header parses with zero grammar errors change state.
    """
    st = {"max_id": 0, "counts": {"typed": 0, "chatter": 0, "untyped": 0, "malformed": 0},
          "claims": {}, "contested": [], "ignored": [], "issues": {}, "questions": {}, "decisions": [], "audits": {}}
    for c in sorted(comments, key=lambda c: c["id"]):
        st["max_id"] = max(st["max_id"], c["id"])
        post = bc.parse_header(bc.first_line(c["body"]))
        if post is None:
            st["counts"]["untyped"] += 1
            continue
        if post["type"] in bc.CHATTER_TYPES:
            st["counts"]["chatter"] += 1
            continue
        if post["errors"]:
            st["counts"]["malformed"] += 1
            continue
        st["counts"]["typed"] += 1
        _apply(st, c, post)
    for claim in st["claims"].values():
        claim["expired"] = claim["expires"] <= now
    return st


def _apply(st: dict, c: dict, post: dict) -> None:
    """Apply one valid typed post to the state dict (mutates `st`). Pure otherwise."""
    at, cid, agent, ptype, fields = bc.parse_ts(c["created_at"]), c["id"], post["agent"], post["type"], post["fields"]
    refs = [r for r in post["refs"].split(",") if r != "-"]
    ttl = timedelta(minutes=int(fields.get("ttl", bc.DEFAULT_TTL_MINUTES)))
    if ptype == "CLAIM":
        for ref in refs:
            cur = st["claims"].get(ref)
            live = bool(cur) and cur["expires"] > at
            if live and cur["agent"] != agent:
                st["contested"].append((ref, agent, cid, cur["agent"]))
            else:
                # A live holder's re-claim is a renewal: `since`/`id` move to it,
                # but the tenure's first claim (the one a crossed claim lost to)
                # is kept, so a tie-break verdict never cites the renewal.
                first = (cur["first_id"], cur["first_since"]) if live else (cid, at)
                st["claims"][ref] = {"agent": agent, "since": at, "expires": at + ttl, "id": cid,
                                     "first_id": first[0], "first_since": first[1]}
    elif ptype in ("RELEASE", "HANDOFF"):
        for ref in refs:
            cur = st["claims"].get(ref)
            if not cur or cur["agent"] != agent:
                # A RELEASE by an agent that contested the ref is its
                # stand-down: drop its contested rows so the cross is settled.
                mine = [row for row in st["contested"] if row[0] == ref and row[1] == agent]
                if ptype == "RELEASE" and mine:
                    st["contested"] = [row for row in st["contested"] if row not in mine]
                else:
                    st["ignored"].append(cid)
            elif ptype == "RELEASE":
                del st["claims"][ref]
            else:
                st["claims"][ref] = {"agent": fields["to"], "since": at, "expires": at + ttl, "id": cid,
                                     "first_id": cid, "first_since": at}
    elif ptype in ("BLOCKER", "FIX-CLAIM"):
        key = fields.get("topic") or post["refs"]
        entry = st["issues"].setdefault(key, {"status": "", "blocker": 0, "fixes": 0, "recurrences": 0, "fix": None})
        if ptype == "BLOCKER":
            if entry["status"] == "fix-claimed":
                entry["recurrences"] += 1
            entry["status"], entry["blocker"] = "open", cid
        else:
            entry["status"], entry["fixes"] = "fix-claimed", entry["fixes"] + 1
            entry["fix"] = (fields["sha"], fields["test"], cid)
    elif ptype == "AUDIT":
        for ref in refs:
            st["audits"][ref] = {"verdict": fields["verdict"], "sha": fields["sha"], "agent": agent, "id": cid}
    if ptype == "QUESTION" or (ptype == "BLOCKER" and fields.get("gate") == "owner"):
        st["questions"][cid] = {"agent": agent, "type": ptype, "refs": post["refs"], "gated": fields.get("gate") == "owner",
                                "text": bc.snippet(c["body"], True), "answered_by": 0}
    if ptype in ("ANSWER", "DECISION") and "of" in fields and int(fields["of"]) in st["questions"]:
        q = st["questions"][int(fields["of"])]
        q["answered_by"] = q["answered_by"] or cid
    if ptype == "DECISION":
        st["decisions"].append((cid, agent, post["refs"], fields.get("of", ""), bc.snippet(c["body"], True)))


def live_contests(st: dict, ref: str) -> list:
    """The folded contested rows on `ref` that still bind its current holder. Pure.

    A row `(ref, contester, comment_id, holder)` is live only while `holder`
    still holds `ref` in the same tenure: the same agent, and a contesting
    comment later than that tenure's first claim (`first_id`, which a
    renewal keeps). A row recorded against a holder who since released,
    handed off, or let the claim expire and re-claimed is history, not a
    live cross. Returns [] when nobody holds `ref`. Shared by claim_probe.py
    (KEEP/YIELD) and board_post.py (when a RELEASE must name its rule).
    """
    cl = st["claims"].get(ref)
    if not cl:
        return []
    return [row for row in st["contested"] if row[0] == ref and row[3] == cl["agent"] and row[2] > cl["first_id"]]


def release_rule_needed(st: dict, agent: str, refs) -> list:
    """Why a RELEASE by `agent` on `refs` must name its `rule:`; [] = it need not. Pure.

    A rule is required when a ref carries a live crossed claim (see
    `live_contests`): either `agent` contested it (its stand-down must cite
    the tie-break, e.g. `earliest-claim`) or someone else contests it
    (releasing settles that contest, so say why, e.g. `handoff`). A plain
    release of an uncontested ref returns [] and board_post.py defaults it
    to `rule:done`. One reason per live row, in fold order.
    """
    reasons = []
    for ref in refs:
        for _, contester, cid, holder in live_contests(st, ref):
            if contester == agent:
                reasons.append(f"you contested `{ref}` (comment {cid}) while agent:{holder} held it: "
                               "name the tie-break you stand down under (e.g. rule:earliest-claim)")
            else:
                reasons.append(f"agent:{contester} contests `{ref}` (comment {cid}): releasing it settles "
                               "that contest, so name why (e.g. rule:handoff or rule:superseded)")
    return reasons


def render(st: dict) -> str:
    """Render the state dict to the marker-wrapped markdown record. Pure."""
    n = st["counts"]
    out = [
        START,
        "## Board state",
        "",
        f"Rendered by `board_state.py` from typed posts; do not hand-edit (the next render overwrites it). "
        f"Source: comments through id {st['max_id']}: {n['typed']} typed, {n['chatter']} chatter, "
        f"{n['untyped']} untyped, {n['malformed']} malformed (ignored).",
        "",
        "### Claims",
    ]
    for ref in sorted(st["claims"]):
        cl = st["claims"][ref]
        when = f"EXPIRED {bc.format_ts(cl['expires'])}, reclaimable" if cl["expired"] else f"expires {bc.format_ts(cl['expires'])}"
        out.append(f"- `{ref}` - agent:{cl['agent']} since {bc.format_ts(cl['since'])}, {when} (comment {cl['id']})")
    if not st["claims"]:
        out.append("- none")
    for ref, agent, cid, holder in sorted(st["contested"]):
        out.append(f"- contested: `{ref}` also claimed by agent:{agent} (comment {cid}) while agent:{holder} held it")
    if st["ignored"]:
        out.append(f"- ignored release/handoff from a non-holder: comments {', '.join(map(str, sorted(set(st['ignored']))))}")
    out += ["", "### Audit (latest verdict per ref; `--backlog` for the dispatch list)"]
    out += [f"- `{ref}` - {a['verdict']} at `{a['sha']}` by agent:{a['agent']} (comment {a['id']})"
            for ref, a in sorted(st["audits"].items())] or ["- none"]
    out += ["", "### Known issues"]
    for key in sorted(st["issues"]):
        e = st["issues"][key]
        line = f"- `{key}` - {e['status']}"
        if e["blocker"]:
            line += f" (last BLOCKER comment {e['blocker']})"
        if e["fix"]:
            sha, test, fid = e["fix"]
            line += f"; fix-claimed {e['fixes']}x, last `{sha}` with test `{test}` (comment {fid})"
        line += f"; recurred {e['recurrences']}x after a fix claim"
        out.append(line)
    if not st["issues"]:
        out.append("- none")
    gated = [(i, q) for i, q in sorted(st["questions"].items()) if q["gated"] and not q["answered_by"]]
    open_q = [(i, q) for i, q in sorted(st["questions"].items()) if not q["gated"] and not q["answered_by"]]
    for title, rows in (("Owner-gated (open)", gated), ("Open questions", open_q)):
        out += ["", f"### {title}"]
        out += [f"- comment {i} - agent:{q['agent']} {q['type']} refs:{q['refs']}: {q['text']}" for i, q in rows] or ["- none"]
    out += ["", f"### Recent decisions (last {RECENT_DECISIONS})"]
    recent = st["decisions"][-RECENT_DECISIONS:]
    out += [f"- comment {cid} - agent:{agent} refs:{refs}{f' of:{of}' if of else ''}: {text}"
            for cid, agent, refs, of, text in recent] or ["- none"]
    out.append(END)
    return "\n".join(out)


def _same_sha(a: str, b: str) -> bool:
    """True iff the shorter of two hex shas prefixes the longer. Pure."""
    n = min(len(a), len(b))
    return a[:n].lower() == b[:n].lower()


BACKLOG_ORDER = (("DISPATCH", "dispatch"), ("REVERIFY", "re-verify"), ("CLAIMED", "claimed"), ("SKIP", "skip"))


def backlog(st: dict, head: str) -> list:
    """The dispatch view of the folded audits at mainline `head` (see THE BACKLOG VIEW). Pure.

    Returns a summary line then one line per audited ref, ordered DISPATCH,
    REVERIFY, CLAIMED, SKIP and by ref within each. A claim counts only while
    unexpired, exactly as the Claims section reads it. Raises ValueError when
    `head` (or a folded audit sha) is not a lowercase hex sha of 7-40 chars:
    an empty or garbage head would otherwise prefix-match every audit.
    """
    if not bc.FIELD_RULES["sha"].match(head or ""):
        raise ValueError(f"--head {head!r} is not a lowercase hex sha of 7-40 chars")
    rows = {kind: [] for kind, _ in BACKLOG_ORDER}
    for ref, a in sorted(st["audits"].items()):
        cl = st["claims"].get(ref)
        held = cl if cl and not cl["expired"] else None
        src = f"(agent:{a['agent']}, comment {a['id']})"
        if not bc.FIELD_RULES["sha"].match(a["sha"]):
            raise ValueError(f"audit of {ref} carries a malformed sha {a['sha']!r}")
        if a["verdict"] != "gap":
            note = (f"; claimed by agent:{held['agent']}: an audited-{a['verdict']} item under a live claim is "
                    "likely a duplicate dispatch" if held else "")
            if _same_sha(a["sha"], head):
                rows["SKIP"].append(f"SKIP `{ref}` {a['verdict']} at {a['sha']} {src}: nothing to build{note}")
            else:
                # A done/na verdict dates to the commit it measured: a later
                # merge can revert or reopen it, so it is not a SKIP at head.
                rows["REVERIFY"].append(f"REVERIFY `{ref}` {a['verdict']} measured at {a['sha']}, not head {head} "
                                        f"{src}: spot-check it still holds at head; post a fresh AUDIT if not{note}")
        elif held:
            rows["CLAIMED"].append(f"CLAIMED `{ref}` gap, held by agent:{held['agent']} until "
                                   f"{bc.format_ts(held['expires'])} {src}")
        elif _same_sha(a["sha"], head):
            rows["DISPATCH"].append(f"DISPATCH `{ref}` gap measured at head {src}")
        else:
            rows["REVERIFY"].append(f"REVERIFY `{ref}` gap measured at {a['sha']}, not head {head} {src}: "
                                    "spot-check it is still open at head, then dispatch; do not re-measure from scratch")
    counts = ", ".join(f"{len(rows[kind])} {label}" for kind, label in BACKLOG_ORDER)
    summary = f"Backlog: {len(st['audits'])} audited refs at head {head}: {counts}"
    return [summary] + [line for kind, _ in BACKLOG_ORDER for line in rows[kind]]


def splice(body: str, block: str) -> str:
    """Put `block` between the markers in `body` (append when absent). Pure.

    Raises MarkerError for a start without an end (or vice versa), more than
    one of either, or an end before the start — any of which means a human or
    another tool edited the markers, and a guessed splice could delete text.
    """
    body = body or ""
    ns, ne = body.count(START), body.count(END)
    if ns == 0 and ne == 0:
        return f"{body.rstrip()}\n\n{block}\n" if body.strip() else f"{block}\n"
    if ns != 1 or ne != 1 or body.index(END) < body.index(START):
        raise MarkerError(f"issue body has {ns} start and {ne} end markers (or end before start); fix by hand")
    head, rest = body.split(START, 1)
    tail = rest.split(END, 1)[1]
    return f"{head}{block}{tail}"


def read_board(repo: str, issue: int, runner):
    """Read a board issue and every comment; return `(issue_obj, comments)`.

    Side-effects: two `gh api` reads through `runner`. Raises bc.ForgeError on
    a failed call, undecodable output, or a comment list shorter than the
    issue's own `comments` count (truncated pagination), so no caller ever
    folds a partial stream as if it were complete. Shared with claim_probe.py.
    """
    issue_obj = bc.gh_object(runner, f"repos/{repo}/issues/{issue}")
    comments = bc.gh_list(runner, bc.comments_path(repo, issue))
    total = issue_obj.get("comments")
    if not isinstance(total, int) or len({c.get("id") for c in comments}) < total:
        raise bc.ForgeError(f"read {len(comments)} comments, issue reports {total}: truncated, refusing to fold")
    return issue_obj, comments


def run_backlog(repo: str, issue: int, now: datetime, head: str, runner, out) -> int:
    """Fetch and fold the board, then print the backlog view. Returns an exit code.

    Side-effects: `gh` reads through `runner` only; never writes. Fails closed
    (exit 2, nothing on stdout) on any read error or truncated comment stream.
    """
    try:
        _, comments = read_board(repo, issue, runner)
        lines = backlog(fold(comments, now), head)
    except (bc.ForgeError, KeyError, TypeError, ValueError) as exc:
        print(f"board_state: {exc}; no backlog", file=sys.stderr)
        return ERROR
    out.write("\n".join(lines) + "\n")
    return OK


def run(repo: str, issue: int, now: datetime, write: bool, runner, out) -> int:
    """Fetch, fold, render; print the record or write it into the body. Returns an exit code.

    Side-effects: `gh` reads through `runner`; with `write`, one re-read of
    the issue and at most one `gh api -X PATCH` (skipped when the body is
    already current, or when the re-read shows a changed body or comment
    count — then CONFLICT) via a temp JSON file, so no body text passes
    through a shell or argv.
    """
    try:
        issue_obj, comments = read_board(repo, issue, runner)
        total = issue_obj["comments"]
        block = render(fold(comments, now))
        if not write:
            out.write(block + "\n")
            return OK
        body = issue_obj.get("body") or ""
        new_body = splice(body, block)
    except (bc.ForgeError, MarkerError, KeyError, TypeError, ValueError) as exc:
        print(f"board_state: {exc}; nothing written", file=sys.stderr)
        return ERROR
    if new_body == body:
        out.write("board_state: body already current; no write\n")
        return OK
    try:
        fresh = bc.gh_object(runner, f"repos/{repo}/issues/{issue}")
    except bc.ForgeError as exc:
        print(f"board_state: re-read before write failed ({exc}); nothing written", file=sys.stderr)
        return ERROR
    if (fresh.get("body") or "") != body or fresh.get("comments") != total:
        print(f"board_state: CONFLICT — the issue changed since it was read (comments {total} -> "
              f"{fresh.get('comments')}, body {'changed' if (fresh.get('body') or '') != body else 'unchanged'}); "
              "nothing written, rerun", file=sys.stderr)
        return CONFLICT
    fd, tmp = tempfile.mkstemp(prefix="board-state-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"body": new_body}, fh)
        rc, _, err = runner(["gh", "api", "-X", "PATCH", f"repos/{repo}/issues/{issue}", "--input", tmp])
    finally:
        os.unlink(tmp)
    if rc != 0:
        print(f"board_state: PATCH failed (rc {rc}): {err.strip()[:300]}", file=sys.stderr)
        return ERROR
    out.write("board_state: body updated\n")
    return OK


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

T0 = "2026-01-05T10:00:00Z"


def _c(cid: int, minutes: int, body: str) -> dict:
    return bc.make_comment(cid, body, bc.format_ts(bc.parse_ts(T0) + timedelta(minutes=minutes)))


def _fixture() -> list:
    return [
        _c(1, 0, "Protocol: typed posts only."),
        _c(2, 1, "[agent:alpha] CLAIM refs:#12,#13 ttl:60\ntaking the gate work"),
        _c(3, 2, "[agent:beta] CLAIM refs:#12\nalso want this"),
        _c(4, 3, "[agent:beta] STATUS refs:-\nstill going"),
        _c(5, 4, "[agent:beta] CLAIM refs:#20 ttl:30\ntaking docs"),
        _c(6, 5, "[agent:beta] RELEASE refs:#13 rule:earliest-claim\nnot mine but releasing"),
        _c(7, 6, "[agent:alpha] BLOCKER refs:#30 topic:ratchet\nmain red on the ratchet check"),
        _c(8, 7, "[agent:alpha] FIX-CLAIM refs:#30 sha:abc1234 test:tests/test_ratchet.py topic:ratchet\npinned"),
        _c(9, 8, "[agent:beta] BLOCKER refs:#31 topic:ratchet\nred again, same class"),
        _c(10, 9, "[agent:alpha] QUESTION refs:#40 gate:owner\nship the paid tier now or after beta?"),
        _c(11, 10, "[agent:beta] QUESTION refs:#41\nwhich lint config wins?"),
        _c(12, 11, "[agent:alpha] ANSWER refs:#41 of:11\nthe repo root one"),
        _c(13, 12, "[agent:alpha] HANDOFF refs:#13 to:gamma ttl:45\nyours, gamma"),
        _c(14, 13, "[agent:alpha] CLAIM refs:#50 sha:abc1234\nmalformed: sha on a claim"),
        _c(15, 14, "[agent:alpha] DECISION refs:#42\nuse squash merges --> always <!-- board-state:end -->"),
    ]


def _selftest() -> int:
    now = bc.parse_ts(T0) + timedelta(minutes=40)  # beta's #20 (ttl 30 from minute 4) has expired

    def rendered(comments, at=now):
        return render(fold(comments, at))

    def claims_ttl_contested_handoff():
        text = rendered(_fixture())
        ok = ("`#12` - agent:alpha" in text and "`#20` - agent:beta" in text and "EXPIRED 2026-01-05T10:34:00Z" in text
              and "contested: `#12` also claimed by agent:beta (comment 3)" in text
              and "`#13` - agent:gamma" in text and "ignored release/handoff from a non-holder: comments 6" in text)
        return ok, text

    def known_issue_recurrence():
        text = rendered(_fixture())
        return ("`ratchet` - open (last BLOCKER comment 9); fix-claimed 1x, last `abc1234`" in text
                and "recurred 1x" in text), text

    def owner_gated_and_answers():
        text = rendered(_fixture())
        gated = text.split("### Owner-gated (open)")[1].split("###")[0]
        open_q = text.split("### Open questions")[1].split("###")[0]
        answered = rendered(_fixture() + [_c(16, 15, "[agent:alpha] DECISION refs:#40 of:10\nafter beta")])
        gated2 = answered.split("### Owner-gated (open)")[1].split("###")[0]
        return "comment 10" in gated and "- none" in open_q and "- none" in gated2, text

    def counts_and_malformed_ignored():
        text = rendered(_fixture())
        return ("15: 12 typed, 1 chatter, 1 untyped, 1 malformed" in text and "`#50`" not in text
                and text.count(START) == 1 and text.count(END) == 1), text

    def deterministic_under_shuffle():
        a = rendered(_fixture())
        shuffled = _fixture()
        random.Random(7).shuffle(shuffled)
        return a == rendered(shuffled), "order changed output"

    def renew_by_holder():
        text = rendered([_c(1, 0, "[agent:beta] CLAIM refs:#20 ttl:30\nx"), _c(2, 25, "[agent:beta] CLAIM refs:#20 ttl:30\nstill mine")])
        return "`#20` - agent:beta since 2026-01-05T10:25:00Z, expires 2026-01-05T10:55:00Z" in text, text

    def expired_claim_reclaimable():
        text = rendered([_c(1, 0, "[agent:beta] CLAIM refs:#20 ttl:5\nx"), _c(2, 10, "[agent:alpha] CLAIM refs:#20\nmine now")])
        return "`#20` - agent:alpha" in text and "contested" not in text, text

    def release_with_rule_frees_ref():
        text = rendered([_c(1, 0, "[agent:alpha] CLAIM refs:#9 ttl:30\nx"),
                         _c(2, 1, "[agent:alpha] RELEASE refs:#9 rule:earliest-claim\nyielding")])
        claims_block = text.split("### Claims")[1].split("###")[0]
        return "#9" not in claims_block and "- none" in claims_block, text

    def legacy_release_without_rule_frees_ref():
        # A RELEASE posted before `rule:` existed stays valid on read: `rule`
        # is required only when composing a post, never when folding one.
        text = rendered([_c(1, 0, "[agent:alpha] CLAIM refs:#9 ttl:30\nx"),
                         _c(2, 1, "[agent:alpha] RELEASE refs:#9\ndone with it")])
        claims_block = text.split("### Claims")[1].split("###")[0]
        return "#9" not in claims_block and "0 malformed" in text, text

    def loser_release_clears_contest():
        # beta crossed alpha's claim, then stood down: its RELEASE removes its
        # contested row instead of being ignored as a non-holder's no-op.
        st = fold([_c(1, 0, "[agent:alpha] CLAIM refs:#55 ttl:60\nx"), _c(2, 1, "[agent:beta] CLAIM refs:#55 ttl:60\nx"),
                   _c(3, 2, "[agent:beta] RELEASE refs:#55 rule:earliest-claim\nalpha claimed first")], now)
        text = render(st)
        return (st["contested"] == [] and st["ignored"] == [] and st["claims"]["#55"]["agent"] == "alpha"
                and "- contested:" not in text and "- ignored release" not in text), text

    def renewal_keeps_first_claim():
        st = fold([_c(1, 0, "[agent:alpha] CLAIM refs:#55 ttl:60\nx"), _c(2, 1, "[agent:beta] CLAIM refs:#55 ttl:60\nx"),
                   _c(3, 5, "[agent:alpha] CLAIM refs:#55 ttl:60\nheartbeat")], now)
        cl = st["claims"]["#55"]
        return (cl["id"] == 3 and cl.get("first_id") == 1 and cl.get("first_since") == bc.parse_ts(T0)
                and live_contests(st, "#55") == [("#55", "beta", 2, "alpha")]), cl

    def contests_die_with_the_tenure():
        # Released then re-claimed (by anyone), expired then re-claimed, or
        # handed off: a row recorded against the old tenure is history.
        base = [_c(1, 0, "[agent:alpha] CLAIM refs:#55 ttl:10\nx"), _c(2, 1, "[agent:beta] CLAIM refs:#55\nx")]
        worlds = {
            "release-then-gamma": base + [_c(3, 2, "[agent:alpha] RELEASE refs:#55 rule:done\nx"),
                                          _c(4, 3, "[agent:gamma] CLAIM refs:#55\nx")],
            "release-then-alpha": base + [_c(3, 2, "[agent:alpha] RELEASE refs:#55 rule:done\nx"),
                                          _c(4, 3, "[agent:alpha] CLAIM refs:#55\nx")],
            "expired-then-alpha": base + [_c(3, 20, "[agent:alpha] CLAIM refs:#55\nx")],
            "handoff-to-gamma": base + [_c(3, 2, "[agent:alpha] HANDOFF refs:#55 to:gamma\nx")],
        }
        live = {k: live_contests(fold(v, now), "#55") for k, v in worlds.items()}
        return all(v == [] for v in live.values()), live

    def release_rule_needed_cases():
        crossed = fold([_c(1, 0, "[agent:alpha] CLAIM refs:#55 ttl:60\nx"), _c(2, 1, "[agent:beta] CLAIM refs:#55\nx"),
                        _c(3, 2, "[agent:alpha] CLAIM refs:#56 ttl:60\nx")], now)
        loser, holder = release_rule_needed(crossed, "beta", ["#55"]), release_rule_needed(crossed, "alpha", ["#55"])
        plain = release_rule_needed(crossed, "alpha", ["#56"])
        ok = (len(loser) == 1 and "earliest-claim" in loser[0] and len(holder) == 1 and "agent:beta" in holder[0]
              and plain == [])
        return ok, (loser, holder, plain)

    def write_appends_then_idempotent():
        gh = bc.FakeGh(_fixture(), body="Protocol text the owner wrote.\n")
        r1 = run("acme/board", 7, now, True, gh, _Sink())
        body1 = gh.body
        patches = sum(1 for c in gh.calls if "PATCH" in c)
        r2 = run("acme/board", 7, now, True, gh, _Sink())
        patches2 = sum(1 for c in gh.calls if "PATCH" in c)
        ok = (r1 == r2 == OK and body1.startswith("Protocol text the owner wrote.\n\n" + START)
              and gh.body == body1 and patches == 1 and patches2 == 1)
        return ok, f"patches {patches}->{patches2}"

    def write_replaces_between_markers_only():
        old = f"Header\n{START}\nstale\n{END}\nFooter kept\n"
        gh = bc.FakeGh(_fixture(), body=old)
        rc = run("acme/board", 7, now, True, gh, _Sink())
        return rc == OK and gh.body.startswith("Header\n" + START) and gh.body.endswith(END + "\nFooter kept\n") and "stale" not in gh.body, gh.body

    def malformed_markers_refused():
        results = []
        for body in (f"x {START} no end", f"{END} {START}", f"{START}{END}{START}{END}"):
            gh = bc.FakeGh(_fixture(), body=body)
            results.append(run("acme/board", 7, now, True, gh, _Sink()) == ERROR and gh.body == body)
        return all(results), str(results)

    def snippet_cannot_break_markers():
        text = rendered(_fixture())
        return text.count(END) == 1 and "-->" not in text.split("### Recent decisions")[1].split(END)[0], text

    def truncated_read_refused():
        gh = bc.FakeGh(_fixture())
        real = gh.__call__

        def short(args, cwd=None):
            rc, out, err = real(args, cwd)
            if args[:3] == ["gh", "api", "--paginate"]:
                out = json.dumps(json.loads(out)[:5])
            return rc, out, err

        return run("acme/board", 7, now, False, short, _Sink()) == ERROR, "rendered a partial stream"

    def many_comments_across_pages():
        comments = [_c(i, i, f"[agent:a{i % 3}] CLAIM refs:#{i}\nx") for i in range(1, 131)]
        sink = _Sink()
        rc = run("acme/board", 7, bc.parse_ts(T0), False, bc.FakeGh(comments), sink)
        return rc == OK and "through id 130: 130 typed" in sink.text and "`#130`" in sink.text, sink.text[:200]

    def raced(mutate):
        """Run --write where `mutate(gh)` fires on the pre-PATCH re-read of the issue."""
        gh = bc.FakeGh(_fixture(), body="Owner text.\n")
        real, reads = gh.__call__, []

        def runner(args, cwd=None):
            if args[:2] == ["gh", "api"] and len(args) == 3:
                reads.append(1)
                if len(reads) == 2:
                    mutate(gh)
            return real(args, cwd)

        rc = run("acme/board", 7, now, True, runner, _Sink())
        return rc, gh, sum(1 for c in gh.calls if "PATCH" in c)

    def body_changed_before_patch_not_overwritten():
        def edit(gh):
            gh.body = "Owner text.\nA peer's newer record.\n"
        rc, gh, patches = raced(edit)
        return rc == CONFLICT and patches == 0 and "newer record" in gh.body, f"rc={rc} patches={patches}"

    def comment_added_before_patch_not_overwritten():
        rc, gh, patches = raced(lambda gh: gh.comments.append(_c(99, 30, "[agent:beta] CLAIM refs:#77\nnew")))
        return rc == CONFLICT and patches == 0 and gh.body == "Owner text.\n", f"rc={rc} patches={patches}"

    head, old = "1111111aaaa", "2222222bbbb"

    def audit_fixture():
        return [
            _c(1, 0, f"[agent:alpha] AUDIT refs:#1,web/cart sha:{head} verdict:gap\nmeasured at mainline"),
            _c(2, 1, f"[agent:alpha] AUDIT refs:#2 sha:{old} verdict:gap\nmeasured three merges ago"),
            _c(3, 2, f"[agent:alpha] AUDIT refs:#3 sha:{head} verdict:done\nalready shipped"),
            _c(4, 3, f"[agent:alpha] AUDIT refs:#4 sha:{head} verdict:na\nno counterpart"),
            _c(5, 4, f"[agent:alpha] AUDIT refs:#5 sha:{head} verdict:gap\nreal gap"),
            _c(6, 5, "[agent:beta] CLAIM refs:#5 ttl:60\ntaking it"),
            _c(7, 6, "[agent:beta] CLAIM refs:#3 ttl:60\nspawned before reading the audit"),
            _c(8, 7, f"[agent:alpha] AUDIT refs:#6 sha:{head} verdict:gap\nfirst pass"),
            _c(9, 8, f"[agent:gamma] AUDIT refs:#6 sha:{head} verdict:done\nre-measured: merged since"),
            _c(10, 9, "[agent:beta] CLAIM refs:#7 ttl:5\nabandoned"),
            _c(11, 10, f"[agent:alpha] AUDIT refs:#7 sha:{head} verdict:gap\nreal gap"),
        ]

    def audit_rendered_latest_wins():
        text = rendered(audit_fixture())
        section = text.split("### Audit")[1].split("###")[0] if "### Audit" in text else ""
        ok = ("`#6` - done at `1111111aaaa` by agent:gamma (comment 9)" in section
              and "`web/cart` - gap" in section and "`#4` - na" in section)
        return ok, section or text

    def backlog_view():
        st = fold(audit_fixture(), now)
        lines = backlog(st, head)
        text = "\n".join(lines)
        kinds = [ln.split()[0] for ln in lines[1:]]
        ok = (lines[0].startswith("Backlog: 8 audited refs at head 1111111aaaa: 3 dispatch, 1 re-verify, 1 claimed, 3 skip")
              and kinds == ["DISPATCH"] * 3 + ["REVERIFY", "CLAIMED"] + ["SKIP"] * 3
              and "DISPATCH `#7`" in text and "DISPATCH `web/cart`" in text
              and "REVERIFY `#2` gap measured at 2222222bbbb" in text
              and "CLAIMED `#5` gap, held by agent:beta" in text
              and "SKIP `#3` done" in text and "claimed by agent:beta: an audited-done item under a live claim is likely a duplicate dispatch" in text
              and "SKIP `#6` done" in text and "SKIP `#4` na" in text)
        return ok, text

    def backlog_needs_head():
        saved, sys.stderr = sys.stderr, _Sink()
        try:
            rc1 = main(["--repo", "acme/board", "--issue", "7", "--backlog"])
            rc2 = main(["--repo", "acme/board", "--issue", "7", "--backlog", "--head", "zz-not-hex"])
            rc3 = main(["--repo", "acme/board", "--issue", "7", "--backlog", "--head", head, "--write"])
        finally:
            sys.stderr = saved
        return rc1 == rc2 == rc3 == ERROR, f"rc={rc1},{rc2},{rc3}"

    def stale_done_or_na_reverify():
        comments = [
            _c(1, 0, f"[agent:alpha] AUDIT refs:#8 sha:{old} verdict:done\nshipped three merges ago"),
            _c(2, 1, f"[agent:alpha] AUDIT refs:#9 sha:{old} verdict:na\nno counterpart then"),
            _c(3, 2, f"[agent:alpha] AUDIT refs:#10 sha:{head} verdict:done\nshipped at head"),
        ]
        lines = backlog(fold(comments, now), head)
        text = "\n".join(lines)
        ok = ("REVERIFY `#8` done measured at 2222222bbbb" in text and "REVERIFY `#9` na measured at 2222222bbbb" in text
              and "SKIP `#10` done at 1111111aaaa" in text and "SKIP `#8`" not in text and "SKIP `#9`" not in text
              and lines[0].endswith("0 dispatch, 2 re-verify, 0 claimed, 1 skip"))
        return ok, text

    def backlog_rejects_bad_head():
        st = fold(audit_fixture(), now)
        refused = []
        for bad in ("", "abc", "ZZZZZZZ1", "1111111AAAA", "1111111aaaa;rm"):
            try:
                backlog(st, bad)
                refused.append(False)
            except ValueError:
                refused.append(True)
        rc = run_backlog("acme/board", 7, now, "", bc.FakeGh(audit_fixture()), _Sink())
        return all(refused) and rc == ERROR, f"refused={refused} rc={rc}"

    def backlog_run_reads_forge():
        sink = _Sink()
        rc = run_backlog("acme/board", 7, now, head, bc.FakeGh(audit_fixture()), sink)
        return rc == OK and "DISPATCH `#1`" in sink.text and "REVERIFY `#2`" in sink.text, sink.text

    cases = [
        ("audit-rendered-latest-wins", audit_rendered_latest_wins),
        ("backlog-dispatch-reverify-claimed-skip", backlog_view),
        ("backlog-requires-hex-head-and-no-write", backlog_needs_head),
        ("backlog-reads-forge", backlog_run_reads_forge),
        ("backlog-stale-done-or-na-reverify", stale_done_or_na_reverify),
        ("backlog-rejects-bad-head", backlog_rejects_bad_head),
        ("claims-ttl-contested-handoff-ignored", claims_ttl_contested_handoff),
        ("changed-body-before-patch-conflicts", body_changed_before_patch_not_overwritten),
        ("new-comment-before-patch-conflicts", comment_added_before_patch_not_overwritten),
        ("known-issue-recurrence-counted", known_issue_recurrence),
        ("owner-gated-open-until-cited", owner_gated_and_answers),
        ("counts-and-malformed-ignored", counts_and_malformed_ignored),
        ("deterministic-under-shuffle", deterministic_under_shuffle),
        ("holder-reclaim-renews", renew_by_holder),
        ("expired-claim-reclaimable", expired_claim_reclaimable),
        ("release-with-rule-frees-ref", release_with_rule_frees_ref),
        ("legacy-release-without-rule-frees-ref", legacy_release_without_rule_frees_ref),
        ("loser-release-clears-contest", loser_release_clears_contest),
        ("renewal-keeps-first-claim", renewal_keeps_first_claim),
        ("contests-die-with-the-tenure", contests_die_with_the_tenure),
        ("release-rule-needed-cases", release_rule_needed_cases),
        ("write-appends-then-idempotent", write_appends_then_idempotent),
        ("write-replaces-between-markers-only", write_replaces_between_markers_only),
        ("malformed-markers-refused", malformed_markers_refused),
        ("snippet-cannot-break-markers", snippet_cannot_break_markers),
        ("truncated-read-refused", truncated_read_refused),
        ("130-comments-across-pages", many_comments_across_pages),
    ]
    saved, sys.stderr = sys.stderr, _Sink()
    try:
        return bc.run_checks("board_state", cases)
    finally:
        sys.stderr = saved


class _Sink:
    """Minimal writable used by the selftest to capture output."""

    def __init__(self):
        self.text = ""

    def write(self, s):
        self.text += s

    def flush(self):
        pass


def main(argv=None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--repo")
    parser.add_argument("--issue", type=int)
    parser.add_argument("--now", help="evaluate claim expiry at this UTC time (YYYY-MM-DDTHH:MM:SSZ); default: now")
    parser.add_argument("--write", action="store_true", help="splice the record into the issue body (an external write)")
    parser.add_argument("--backlog", action="store_true", help="print the audit dispatch list (read-only); needs --head")
    parser.add_argument("--head", help="mainline commit sha the audits are compared against (hex, 7-40 chars)")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not (args.repo and bc.validate_repo(args.repo) and args.issue and args.issue > 0):
        print("board_state: --repo OWNER/NAME and --issue N (>0) are required", file=sys.stderr)
        return ERROR
    try:
        now = bc.parse_ts(args.now) if args.now else datetime.now(timezone.utc).replace(second=0, microsecond=0)
    except ValueError:
        print("board_state: --now must be YYYY-MM-DDTHH:MM:SSZ", file=sys.stderr)
        return ERROR
    if args.backlog:
        if args.write or not bc.FIELD_RULES["sha"].match(args.head or ""):
            print("board_state: --backlog needs --head <hex sha, 7-40 chars> and cannot be combined with --write",
                  file=sys.stderr)
            return ERROR
        return run_backlog(args.repo, args.issue, now, args.head, bc.default_runner, sys.stdout)
    return run(args.repo, args.issue, now, args.write, bc.default_runner, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
