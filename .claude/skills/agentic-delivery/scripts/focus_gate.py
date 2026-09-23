#!/usr/bin/env python3
"""focus_gate.py — no work outside the owner's open priority until that priority is done or blocked.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
Agent fleets repeatedly stopped working on the owner's main priority before it
was finished and drifted to cheaper, more visible items. The prose rule ("an
open owner priority outranks every other item") existed and did not fire: every
drifting lane had a locally plausible reason to move on. This gate turns the
rule into a blocking fact. The owner writes the priority down once; the
priority is DONE only when its acceptance command exits 0, never when a lane
judges it "close enough".

THE RULE
--------
  status  OPEN     the record is trusted, its acceptance command did not exit 0,
                   and no valid blocker row exists — or the record is missing,
                   unreadable, malformed, or not owner-authored (fail closed:
                   never DONE, and an untrusted scope puts nothing in scope).
          DONE     the acceptance command was run and exited 0 (evidence: its
                   exit code, duration, HEAD commit, and the output tail).
          BLOCKED  not DONE, and at least one blocker row names another party
                   AND an http(s) evidence link. A row without both is
                   reported as rejected and the priority stays OPEN.
  check   GO       the priority is DONE or BLOCKED (work elsewhere is allowed),
                   or the item/paths are inside the priority scope.
          NO-GO    the priority is OPEN and the item/paths are outside scope.
  In scope means: (the item is a scope ref, or every changed path matches a
  scope glob) AND, when the record names any glob, no changed path falls
  outside the globs — tagging a change with the priority's issue number does
  not carry unrelated paths in with it.
  Oracle guard: when the priority is DONE on this tree but the change itself
  touches a path named in the acceptance command that is outside scope (the
  reference design, the differ script), the DONE is unproven for that change
  and the verdict is NO-GO — land oracle changes separately, owner-reviewed.

RECORD GRAMMAR (default path `.claude/PRIORITY.md`; read from the committed
blob at `--rev`, never from the working tree, so an uncommitted edit is inert)
------------------------------------------------------------------------------
Only lines of the form `key: value` (optionally led by `- ` or `* `) with the
keys below are parsed; every other line (headings, prose) is ignored.
  priority: <id>                         exactly one; required
  scope: <token> [<token> ...]           repeatable; tokens split on space/comma.
                                         `#123` (any `#`-led token) is an item
                                         ref; anything else is a path glob
                                         (`**`, `*`, `?`; fix_class_gate grammar)
  acceptance: <shell command>            exactly one; one pair of surrounding
                                         backticks is stripped. Missing or
                                         duplicated -> OPEN, never DONE
  blocker: <party> | <evidence-url> | <note>
                                         repeatable; owner-accepted blocker
  owner-quote: <YYYY-MM-DD> | <where said> | <verbatim text>
                                         repeatable; the quote route (below)
Example:
  priority: design-alignment
  scope: app/screens/** #123 #124
  acceptance: python3 tools/parity_differ.py design.html app.html
  blocker: design vendor | https://example.com/tickets/42 | final spec pending

TRUST (same authorship rule as the standing grant in agentic-delivery SKILL.md)
-------------------------------------------------------------------------------
The record counts only as an owner-authored artifact. Route 1, owner commit:
the last commit touching the record AND every commit that authored a surviving
line (`git blame`) must have an author email in the owner set, carry no
`Co-authored-by:` trailer (an agent-assisted commit is not the owner's own),
and, with `--require-signed`, a good signature (`%G?` = G). Route 2, owner
quote: when route 1 fails and `--commit-only` is not set, a record carrying at
least one well-formed `owner-quote:` row is trusted only if every scope token,
the acceptance command, and every valid blocker's party and evidence appear
literally inside the quoted text — the record cannot claim anything the quote
does not say. An agent therefore cannot create, widen, or close the record on
its own authority. Owner set, first non-empty of: `--owner-email` (repeatable),
env `DCR_OWNER_EMAIL` (comma/space separated), `git config --get-all dcr.owner`.
None configured -> untrusted -> OPEN. The acceptance command of an untrusted
record is NEVER executed (it would be arbitrary code from an unverified author).

HONESTY (what this cannot prove)
--------------------------------
A commit author email is unauthenticated metadata: anyone can commit under
any identity, and an agent on the owner's own machine may commit under the
owner's configured identity. The co-author-trailer rule catches an agent that
follows its own attribution convention; `--require-signed` plus a signing key
the agent cannot use is the only hard guarantee. The owner-email setting is
the trust root: in CI, set `DCR_OWNER_EMAIL` from protected configuration, not
from a file the change under review can edit. The quote route cannot
authenticate a quote; it only prevents the record from exceeding it, and a
quote-routed acceptance command was transcribed by whoever wrote the record —
pass `--commit-only` wherever that execution matters. The
oracle guard covers paths named literally in the acceptance command, not
their transitive imports. DONE proves the owner's own acceptance command
passed on this tree; it cannot judge whether that command is the right test.

EXIT CODES
----------
  check:  0 GO      1 NO-GO (including every fail-closed OPEN)   2 usage/range error
  status: 0 DONE    1 OPEN                                       3 BLOCKED   2 usage error

USAGE
-----
  focus_gate.py status [common options] [--evidence FILE]
  focus_gate.py check  [common options] [--item REF] [--paths P ...] [--base REF --head REF]
  focus_gate.py --selftest
common options: --record PATH (.claude/PRIORITY.md)  --rev REV (HEAD; --head when given)
                --owner-email E ...  --commit-only  --require-signed  --timeout SECONDS (900)
                --repo DIR (.)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

sys.dont_write_bytecode = True
from refix_gate import load_fix_class_gate  # noqa: E402  (sibling script; one loader)

GO, NO_GO, ERROR = 0, 1, 2
S_DONE, S_OPEN, S_BLOCKED = "DONE", "OPEN", "BLOCKED"
STATUS_EXIT = {S_DONE: 0, S_OPEN: 1, S_BLOCKED: 3}
DEFAULT_RECORD = ".claude/PRIORITY.md"
DEFAULT_TIMEOUT = 900.0
ZERO_SHA = "0" * 40
MAX_STATUS_LINES = 10

GitRunner = Callable[[list], str]
# (command, cwd, timeout_seconds) -> (exit_code, combined stdout+stderr). Raises on
# timeout / spawn failure; the caller turns any exception into OPEN.
CmdRunner = Callable[[str, str, float], tuple]

_KEY_RE = re.compile(r"^\s*(?:[-*]\s+)?(priority|scope|acceptance|blocker|owner-quote)\s*:\s*(.*?)\s*$",
                     re.IGNORECASE)
_URL_RE = re.compile(r"^https?://\S+$")
_SELF_PARTIES = {"self", "me", "us", "we", "agent", "the agent", "this agent", "lane", "this lane", "myself"}
_BLAME_HEADER_RE = re.compile(r"^([0-9a-f]{40}) \d+ \d+(?: \d+)?$")


class GitError(RuntimeError):
    """A git invocation failed; the caller must fail closed."""


def real_git(repo: str = ".") -> GitRunner:
    """Return a runner executing `git -C repo <args>`; raises GitError on a non-zero exit."""
    def run(args: list) -> str:
        proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
        if proc.returncode != 0:
            raise GitError(proc.stderr.strip() or f"git {' '.join(args)} failed (rc={proc.returncode})")
        return proc.stdout
    return run


def real_cmd(command: str, cwd: str, timeout: float) -> tuple:
    """Run the owner's acceptance command through the shell; return (exit_code, combined output).

    Side effect: executes an arbitrary shell command — callers only reach this for a
    TRUSTED record. Raises subprocess.TimeoutExpired / OSError, which the caller maps
    to OPEN (a command that could not finish never proves DONE).
    """
    proc = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


@dataclass
class Record:
    """The parsed priority record. `fatal` non-empty means the scope cannot be trusted."""
    priority: str = ""
    globs: list = field(default_factory=list)
    refs: list = field(default_factory=list)
    raw_scope: list = field(default_factory=list)
    acceptance: str | None = None
    acceptance_note: str = ""
    blockers: list = field(default_factory=list)          # [(party, evidence, note)]
    rejected_blockers: list = field(default_factory=list)  # [(raw, reason)]
    quotes: list = field(default_factory=list)            # [(date, where, text)]
    fatal: list = field(default_factory=list)


def _norm_ref(token: str) -> str:
    """`#123`, `123`, `#ENG-7` -> case-folded id without the leading `#`."""
    return token.strip().lstrip("#").casefold()


def _norm_path(path: str) -> str:
    """Repo-relative, `/`-separated, no leading `./`."""
    path = path.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def _strip_ticks(value: str) -> str:
    """Remove one pair of surrounding backticks (markdown inline code)."""
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        return value[1:-1].strip()
    return value


def parse_record(text: str) -> Record:
    """Parse the record grammar (module docstring). Pure; never raises.

    Edge cases: zero or several `priority:` lines -> fatal (scope untrusted); zero
    or several `acceptance:` lines -> acceptance None with a note (OPEN, never
    DONE); a blocker without another party or an http(s) evidence link, and a
    malformed owner-quote row, are kept aside as rejected rather than honoured.
    """
    rec = Record()
    priorities, acceptances = [], []
    for line in text.splitlines():
        m = _KEY_RE.match(line)
        if not m:
            continue
        key, value = m.group(1).lower(), m.group(2)
        if key == "priority":
            priorities.append(value)
        elif key == "scope":
            for tok in re.split(r"[\s,]+", value):
                tok = _strip_ticks(tok.strip())
                if not tok:
                    continue
                rec.raw_scope.append(tok)
                if tok.startswith("#"):
                    if _norm_ref(tok):
                        rec.refs.append(_norm_ref(tok))
                else:
                    rec.globs.append(_norm_path(tok))
        elif key == "acceptance":
            acceptances.append(_strip_ticks(value))
        elif key == "blocker":
            parts = [p.strip() for p in value.split("|")]
            party = parts[0] if parts else ""
            evidence = parts[1] if len(parts) > 1 else ""
            note = " | ".join(parts[2:]) if len(parts) > 2 else ""
            if not party or party.casefold() in _SELF_PARTIES:
                rec.rejected_blockers.append((value, "names no other party"))
            elif not _URL_RE.match(evidence):
                rec.rejected_blockers.append((value, "no http(s) evidence link"))
            else:
                rec.blockers.append((party, evidence, note))
        elif key == "owner-quote":
            parts = [p.strip() for p in value.split("|", 2)]
            if len(parts) == 3 and all(parts):
                try:
                    date.fromisoformat(parts[0])
                except ValueError:
                    continue
                quote = parts[2]
                if len(quote) >= 2 and quote[0] == quote[-1] and quote[0] in "\"'":
                    quote = quote[1:-1]
                if quote:
                    rec.quotes.append((parts[0], parts[1], quote))
    if len(priorities) != 1 or not priorities[0]:
        rec.fatal.append(f"expected exactly one non-empty `priority:` line, found {len(priorities)}")
    else:
        rec.priority = priorities[0]
    if not acceptances or not acceptances[0]:
        rec.acceptance_note = "acceptance command missing"
    elif len(acceptances) > 1:
        rec.acceptance_note = f"ambiguous: {len(acceptances)} `acceptance:` lines"
    else:
        rec.acceptance = acceptances[0]
    return rec


def resolve_owners(explicit: list | None, git: GitRunner) -> list:
    """Owner emails, case-folded: --owner-email, else DCR_OWNER_EMAIL, else `git config dcr.owner`."""
    if explicit:
        vals = explicit
    elif os.environ.get("DCR_OWNER_EMAIL", "").strip():
        vals = re.split(r"[,\s]+", os.environ["DCR_OWNER_EMAIL"])
    else:
        try:
            vals = git(["config", "--get-all", "dcr.owner"]).split()
        except GitError:
            vals = []
    return sorted({v.strip().strip("<>").casefold() for v in vals if v.strip()})


def _commit_meta(git: GitRunner, sha: str) -> tuple:
    """(author_email_casefolded, signature_status, has_coauthor_trailer) for one commit."""
    out = git(["show", "-s", "--format=%ae%x1f%G?%x1f%(trailers:key=Co-authored-by,valueonly)", sha])
    parts = out.split("\x1f")
    if len(parts) != 3:
        raise GitError(f"unparseable commit metadata for {sha[:12]}")
    return parts[0].strip().casefold(), parts[1].strip(), bool(parts[2].strip())


def load_record(git: GitRunner, path: str, rev: str, owners: list,
                commit_only: bool = False, require_signed: bool = False) -> tuple:
    """Read and authenticate the record at `rev:path`.

    Returns (record | None, trusted: bool, source: str, reasons: list[str]).
    Never raises: a git failure is an untrusted/absent record (fail closed).
    """
    try:
        text = git(["show", f"{rev}:{path}"])
    except GitError:
        try:
            last = git(["log", "-1", "--format=%h %ae", rev, "--", path]).strip()
        except GitError:
            last = ""
        why = f"record deleted at {last}" if last else "no record"
        return None, False, "none", [f"{why} at {rev}:{path} (fail closed: OPEN)"]
    rec = parse_record(text)
    if not owners:
        return rec, False, "untrusted", [
            "no owner email configured (--owner-email, DCR_OWNER_EMAIL, or git config dcr.owner)"]
    reasons: list = []
    try:
        last_line = git(["log", "-1", "--format=%H", rev, "--", path]).strip()
        blame = git(["blame", "--porcelain", rev, "--", path])
        shas = {m.group(1) for m in map(_BLAME_HEADER_RE.match, blame.splitlines()) if m}
        content_lines = sum(1 for ln in blame.splitlines() if ln.startswith("\t"))
        if last_line:
            shas.add(last_line)
        if not shas or not content_lines:
            reasons.append("record has no committed lines")
        for sha in sorted(shas):
            email, sig, coauthor = _commit_meta(git, sha)
            role = "last touch" if sha == last_line else "line author"
            if email not in owners:
                reasons.append(f"{role} {sha[:7]} by {email or '?'} is not the owner")
            elif coauthor:
                reasons.append(f"{role} {sha[:7]} carries a Co-authored-by trailer (agent-assisted)")
            elif require_signed and sig != "G":
                reasons.append(f"{role} {sha[:7]} has no good signature (%G?={sig or '?'})")
    except GitError as exc:
        reasons.append(f"authorship unverifiable: {exc}")
    if not reasons:
        return rec, True, f"owner-commit {last_line[:7]}", []
    if commit_only or not rec.quotes:
        return rec, False, "untrusted", reasons
    corpus = "\n".join(q[2] for q in rec.quotes)
    claims = list(rec.raw_scope) + ([rec.acceptance] if rec.acceptance else [])
    for party, evidence, _ in rec.blockers:
        claims += [party, evidence]
    missing = [c for c in claims if c not in corpus]
    if missing:
        return rec, False, "untrusted", reasons + [
            "owner-quote does not contain: " + ", ".join(repr(c) for c in missing[:4])]
    d, where, _ = rec.quotes[0]
    return rec, True, f"owner-quote {d} ({where})", []


@dataclass
class Status:
    """Computed priority state plus the evidence lines that justify it."""
    state: str
    trusted: bool
    record: Record | None
    source: str
    reasons: list
    acceptance_rc: int | None = None
    acceptance_secs: float | None = None
    tail: list = field(default_factory=list)
    head: str = ""


def _tail(output: str, n: int = 3) -> list:
    """Last `n` non-empty output lines, each capped at 160 chars."""
    lines = [ln.rstrip() for ln in output.splitlines() if ln.strip()]
    return [ln[:160] for ln in lines[-n:]]


def evaluate(git: GitRunner, run_cmd: CmdRunner, record_path: str, rev: str, owners: list,
             cwd: str, timeout: float, commit_only: bool = False, require_signed: bool = False) -> Status:
    """Compute OPEN / DONE / BLOCKED. Runs the acceptance command only for a trusted record.

    Fail-closed order: record present -> authorship trusted -> grammar sound ->
    acceptance present -> acceptance exits 0. Any step failing leaves OPEN.
    """
    rec, trusted, source, reasons = load_record(git, record_path, rev, owners, commit_only, require_signed)
    try:
        head = git(["rev-parse", "--verify", "-q", f"{rev}^{{commit}}"]).strip()
    except GitError:
        head = ""
    st = Status(S_OPEN, trusted, rec, source, list(reasons), head=head)
    if rec is None or not trusted:
        return st
    if rec.fatal:
        st.trusted = False
        st.reasons += rec.fatal
        return st
    if rec.acceptance is None:
        st.reasons.append(f"{rec.acceptance_note} -> OPEN, never DONE")
    else:
        started = time.monotonic()
        try:
            rc, out = run_cmd(rec.acceptance, cwd, timeout)
            st.acceptance_rc, st.tail = rc, _tail(out)
        except Exception as exc:  # timeout, spawn failure: never proof of DONE
            st.reasons.append(f"acceptance did not complete: {type(exc).__name__}")
        st.acceptance_secs = round(time.monotonic() - started, 2)
        if st.acceptance_rc == 0:
            st.state = S_DONE
            return st
    if rec.blockers:
        st.state = S_BLOCKED
    return st


def status_lines(st: Status) -> list:
    """At most MAX_STATUS_LINES human-readable lines stating the verdict and its evidence."""
    rec = st.record
    pid = rec.priority if rec and rec.priority else "?"
    lines = [f"focus_gate: {st.state} priority={pid} source={st.source}"
             + (f" head={st.head[:12]}" if st.head else "")]
    if rec and st.trusted:
        lines.append(f"scope: {len(rec.globs)} glob(s), {len(rec.refs)} ref(s): "
                     + " ".join(rec.raw_scope)[:140])
    if rec and st.trusted and rec.acceptance:
        rc = "not run" if st.acceptance_rc is None else f"exit {st.acceptance_rc}"
        lines.append(f"acceptance: {rc} in {st.acceptance_secs}s: {rec.acceptance[:120]}")
        lines += [f"  | {t}" for t in st.tail]
    if rec and st.trusted:
        for party, ev, _ in rec.blockers[:2]:
            lines.append(f"blocker: {party} evidence={ev[:100]}")
        if rec.rejected_blockers:
            lines.append(f"rejected blocker row(s): {len(rec.rejected_blockers)} "
                         f"({rec.rejected_blockers[0][1]})")
    for r in st.reasons:
        lines.append(f"reason: {r}")
    return lines[:MAX_STATUS_LINES]


def _range_paths(git: GitRunner, base: str, head: str) -> list:
    """Changed paths of merge-base(base, head)..head (NUL-safe, renames split). Raises GitError."""
    if base == ZERO_SHA:
        raise GitError("--base is the all-zeros SHA; pass the PR base ref")
    mb = git(["merge-base", base, head]).strip()
    if not mb:
        raise GitError(f"no merge base between {base} and {head}")
    out = git(["diff", "-z", "--name-only", "--no-renames", mb, head])
    return [p for p in out.split("\0") if p]


def _oracle_paths(command: str) -> set:
    """Repo-relative path tokens named literally in the acceptance command."""
    try:
        toks = shlex.split(command)
    except ValueError:
        toks = command.split()
    return {_norm_path(t) for t in toks if t and not t.startswith("-") and not t.startswith("/")}


def check(st: Status, item: str | None, paths: list, fcg) -> tuple:
    """GO / NO-GO for one item and/or change set against the computed status. Pure."""
    rec = st.record
    pid = rec.priority if rec and rec.priority else "?"
    label = item or f"{len(paths)} path(s)"
    paths = [_norm_path(p) for p in paths]
    compiled = fcg._compile_globs(tuple(rec.globs)) if rec else []
    outside = [p for p in paths if not fcg._matches_any(p, compiled)] if compiled else list(paths)
    if st.state == S_DONE:
        tampered = sorted(set(paths) & _oracle_paths(rec.acceptance or "") & set(outside))
        if tampered:
            return NO_GO, [f"focus_gate: NO-GO {label} — change touches the acceptance oracle outside "
                           f"scope ({', '.join(tampered[:3])}); DONE on this tree is unproven for it"]
        return GO, [f"focus_gate: GO {label} — priority {pid} is DONE (acceptance exit 0)"]
    if st.state == S_BLOCKED:
        party = rec.blockers[0][0]
        return GO, [f"focus_gate: GO {label} — priority {pid} is BLOCKED on {party} (evidence recorded)"]
    finish = f"; finish the priority first (acceptance: {rec.acceptance})" if rec and rec.acceptance else ""
    if not st.trusted:
        why = st.reasons[0] if st.reasons else "record untrusted"
        return NO_GO, [f"focus_gate: NO-GO {label} — priority is OPEN and its record is untrusted, "
                       f"so nothing is in scope ({why})"]
    ref_ok = bool(item) and _norm_ref(item) in rec.refs
    paths_ok = bool(paths) and bool(compiled) and not outside
    if (ref_ok or paths_ok) and not (compiled and paths and outside):
        return GO, [f"focus_gate: GO {label} — inside the scope of open priority {pid}"]
    if ref_ok and outside:
        detail = "in-scope ref but path(s) outside scope: " + ", ".join(outside[:3])
    elif outside:
        detail = "outside scope: " + ", ".join(outside[:3])
    else:
        detail = f"item {item} is not a scope ref"
    return NO_GO, [f"focus_gate: NO-GO {label} — priority {pid} is OPEN; {detail}{finish}"]


def write_evidence(path: str, st: Status) -> None:
    """Write the status evidence as JSON to `path` (side effect: creates/overwrites the file)."""
    rec = st.record
    doc = {"state": st.state, "priority": rec.priority if rec else None, "source": st.source,
           "trusted": st.trusted, "head": st.head, "reasons": st.reasons,
           "acceptance": {"command": rec.acceptance if rec else None, "exit": st.acceptance_rc,
                          "seconds": st.acceptance_secs, "tail": st.tail},
           "blockers": [{"party": p, "evidence": e, "note": n} for p, e, n in (rec.blockers if rec else [])],
           "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    Path(path).write_text(json.dumps(doc, indent=2) + "\n")


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------
OWNER, AGENT = "owner@example.com", "lane-bot@example.com"
GOOD = ("# Owner priority\n\npriority: design-alignment\nscope: app/screens/** #12\n"
        "acceptance: `python3 tools/parity_differ.py design.html app/screens/home.html`\n")


def _fake_git(text: str | None, commits: dict, blame_shas: list, last: str | None = None,
              deleted: str = "", diff: list | None = None) -> GitRunner:
    """Offline git double: `commits` maps sha -> (email, sig, coauthor_value)."""
    last = last if last is not None else (blame_shas[-1] if blame_shas else "")

    def run(args: list) -> str:
        cmd = args[0]
        if cmd == "show" and args[1].startswith("-s"):
            email, sig, co = commits[args[-1]]
            return f"{email}\x1f{sig}\x1f{co}\n"
        if cmd == "show":
            if text is None:
                raise GitError("fatal: path does not exist")
            return text
        if cmd == "log" and args[2] == "--format=%h %ae":
            return deleted
        if cmd == "log":
            return last + "\n"
        if cmd == "blame":
            lines = (text or "").splitlines()
            out = []
            for i, ln in enumerate(lines):
                out.append(f"{blame_shas[i % len(blame_shas)]} {i + 1} {i + 1} 1")
                out.append(f"\t{ln}")
            return "\n".join(out) + "\n"
        if cmd == "rev-parse":
            return "f" * 40 + "\n"
        if cmd == "merge-base":
            return "b" * 40 + "\n"
        if cmd == "diff":
            return "\0".join(diff or []) + ("\0" if diff else "")
        if cmd == "config":
            raise GitError("unset")
        raise GitError(f"unexpected git {args}")
    return run


def _fake_cmd(rc: int | None, calls: list, out: str = "MISMATCH home: 3 elements\n") -> CmdRunner:
    """Offline acceptance double; rc None simulates a timeout. Records each call."""
    def run(command: str, cwd: str, timeout: float) -> tuple:
        calls.append(command)
        if rc is None:
            raise subprocess.TimeoutExpired(command, timeout)
        return rc, out
    return run


def _selftest() -> int:
    """Assert every verdict branch on offline fixtures, then end to end on a real throwaway repo."""
    fcg = load_fix_class_gate()
    if fcg is None:
        print("SELFTEST FAILED: sibling deep-code-review/scripts/fix_class_gate.py not found")
        return 1
    failures: list = []
    ran = [0]
    O1, O2, A1 = "1" * 40, "2" * 40, "a" * 40
    owner_c = {O1: (OWNER, "N", ""), O2: (OWNER.upper(), "G", "")}

    def status_of(git, rc=1, owners=(OWNER,), calls=None, **kw):
        calls = [] if calls is None else calls
        return evaluate(git, _fake_cmd(rc, calls), DEFAULT_RECORD, "HEAD", list(owners), ".", 5.0, **kw)

    def case(label, st, want_state=None, item=None, paths=(), want_rc=None, must=()):
        ran[0] += 1
        out = "\n".join(status_lines(st))
        if want_state and st.state != want_state:
            failures.append(f"{label}: state={st.state} want {want_state}: {out}")
        if len(status_lines(st)) > MAX_STATUS_LINES:
            failures.append(f"{label}: status exceeds {MAX_STATUS_LINES} lines")
        if want_rc is not None:
            rc, lines = check(st, item, list(paths), fcg)
            out = "\n".join(lines) + "\n" + out
            if rc != want_rc:
                failures.append(f"{label}: check rc={rc} want {want_rc}: {out}")
        failures.extend(f"{label}: missing {m!r}: {out}" for m in must if m not in out)

    owner_git = _fake_git(GOOD, owner_c, [O1, O2])
    st_open = status_of(owner_git, rc=1)
    case("open-in-scope-ref-go", st_open, S_OPEN, item="#12", want_rc=GO, must=("exit 1", "MISMATCH home"))
    case("open-in-scope-paths-go", st_open, S_OPEN, paths=["app/screens/home.html"], want_rc=GO)
    # Planted drift: a cosmetic item outside the open priority FIRES.
    case("outside-scope-no-go", st_open, S_OPEN, item="#99", paths=["web/theme.css"], want_rc=NO_GO,
         must=("NO-GO #99", "outside scope: web/theme.css", "finish the priority first"))
    case("item-not-ref-no-go", st_open, S_OPEN, item="#99", want_rc=NO_GO, must=("not a scope ref",))
    case("ref-does-not-carry-paths", st_open, S_OPEN, item="#12",
         paths=["app/screens/home.html", "web/theme.css"], want_rc=NO_GO, must=("in-scope ref but path",))
    case("ref-normalized", st_open, S_OPEN, item="12", want_rc=GO)
    # Agent-authored record: rejected, acceptance never executed, nothing in scope.
    calls: list = []
    st = status_of(_fake_git(GOOD, {A1: (AGENT, "N", "")}, [A1]), rc=0, calls=calls)
    case("agent-record-rejected", st, S_OPEN, item="#12", want_rc=NO_GO, must=("is not the owner",))
    if calls:
        failures.append(f"agent-record-rejected: acceptance of an untrusted record was executed: {calls}")
    case("agent-widened-line-rejected",
         status_of(_fake_git(GOOD, {**owner_c, A1: (AGENT, "N", "")}, [O1, A1, O1], last=O1)),
         S_OPEN, item="#12", want_rc=NO_GO, must=("line author aaaaaaa",))
    case("coauthored-commit-rejected",
         status_of(_fake_git(GOOD, {O1: (OWNER, "N", "Assistant <bot@example.com>")}, [O1])),
         S_OPEN, item="#12", want_rc=NO_GO, must=("Co-authored-by",))
    case("unsigned-rejected-when-required", status_of(owner_git, require_signed=True), S_OPEN,
         item="#12", want_rc=NO_GO, must=("no good signature",))
    case("no-owner-configured", status_of(owner_git, owners=()), S_OPEN, item="#12", want_rc=NO_GO,
         must=("no owner email configured",))
    case("record-deleted", status_of(_fake_git(None, owner_c, [O1], deleted="abc1234 " + AGENT)), S_OPEN,
         item="#12", want_rc=NO_GO, must=("record deleted at abc1234",))
    case("malformed-no-priority", status_of(_fake_git("scope: app/**\n", owner_c, [O1])), S_OPEN,
         item="#12", want_rc=NO_GO, must=("exactly one non-empty `priority:`",))
    case("malformed-two-priorities", status_of(_fake_git(GOOD + "priority: other\n", owner_c, [O1]), rc=0),
         S_OPEN, item="#12", want_rc=NO_GO, must=("found 2",))
    # Acceptance exit 0 -> DONE -> GO for everything; the oracle guard still fires.
    st_done = status_of(owner_git, rc=0)
    case("done-go-everything", st_done, S_DONE, item="#99", paths=["web/theme.css"], want_rc=GO,
         must=("is DONE",))
    case("done-oracle-tamper-no-go", st_done, S_DONE, paths=["tools/parity_differ.py"], want_rc=NO_GO,
         must=("acceptance oracle",))
    case("done-in-scope-oracle-ok", st_done, S_DONE, paths=["app/screens/home.html"], want_rc=GO)
    calls = []
    case("acceptance-missing-open", status_of(_fake_git(GOOD.replace("acceptance", "accept"), owner_c, [O1]),
                                              rc=0, calls=calls), S_OPEN, must=("acceptance command missing",))
    if calls:
        failures.append("acceptance-missing-open: a command ran with no acceptance line")
    case("acceptance-ambiguous-open",
         status_of(_fake_git(GOOD + "acceptance: true\n", owner_c, [O1]), rc=0), S_OPEN, must=("ambiguous",))
    case("acceptance-timeout-open", status_of(owner_git, rc=None), S_OPEN, item="#99", want_rc=NO_GO,
         must=("TimeoutExpired",))
    # Blockers: another party + evidence -> BLOCKED -> GO for others; without evidence -> still OPEN.
    blocked = GOOD + "blocker: design vendor | https://example.com/t/42 | spec pending\n"
    case("blocked-with-evidence-go", status_of(_fake_git(blocked, owner_c, [O1])), S_BLOCKED,
         item="#99", paths=["web/theme.css"], want_rc=GO, must=("BLOCKED on design vendor",))
    case("blocked-without-evidence-open",
         status_of(_fake_git(GOOD + "blocker: design vendor | waiting on them\n", owner_c, [O1])), S_OPEN,
         item="#99", want_rc=NO_GO, must=("no http(s) evidence link",))
    case("blocked-on-self-open",
         status_of(_fake_git(GOOD + "blocker: agent | https://example.com/x\n", owner_c, [O1])), S_OPEN,
         item="#99", want_rc=NO_GO, must=("names no other party",))
    case("done-beats-blocked", status_of(_fake_git(blocked, owner_c, [O1]), rc=0), S_DONE)
    # Quote route: every claim must appear inside the verbatim owner quote.
    quote = ('owner-quote: 2026-09-20 | planning call | "finish design-alignment: app/screens/** and #12, '
             'done when python3 tools/parity_differ.py design.html app/screens/home.html passes"\n')
    q_git = _fake_git(GOOD + quote, {A1: (AGENT, "N", "")}, [A1])
    case("quote-route-trusted", status_of(q_git), S_OPEN, item="#12", want_rc=GO, must=("owner-quote 2026-09-20",))
    case("quote-route-commit-only", status_of(q_git, commit_only=True), S_OPEN, item="#12", want_rc=NO_GO)
    case("quote-route-widened-rejected",
         status_of(_fake_git(GOOD.replace("#12", "#12 web/**") + quote, {A1: (AGENT, "N", "")}, [A1])),
         S_OPEN, item="#99", paths=["web/theme.css"], want_rc=NO_GO, must=("does not contain: 'web/**'",))
    ran[0] += 1
    try:
        got = _range_paths(_fake_git(GOOD, owner_c, [O1], diff=["a b.txt", "c.txt"]), "base", "head")
        if got != ["a b.txt", "c.txt"]:
            failures.append(f"range-paths: {got}")
        _range_paths(owner_git, ZERO_SHA, "head")
        failures.append("zero-base: no error")
    except GitError:
        pass

    # End to end through the CLI on a real throwaway repo (local git only; no network).
    with tempfile.TemporaryDirectory(prefix="focus_gate_selftest_") as tmp:
        repo = Path(tmp)
        git = real_git(tmp)
        git(["init", "-q"])
        git(["config", "commit.gpgsign", "false"])

        def commit(email: str, rel: str, body: str, msg: str = "chore: record") -> str:
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(body)
            git(["add", rel])
            git(["-c", f"user.email={email}", "-c", "user.name=Jane Smith", "commit", "-q", "-m", msg])
            return git(["rev-parse", "HEAD"]).strip()

        flag = repo / "flag.txt"
        flag.write_text("1")
        acceptance = f"{shlex.quote(sys.executable)} -c \"import sys; sys.exit(int(open('flag.txt').read()))\""
        base = commit(OWNER, "src/a.txt", "a\n", "chore: init")
        commit(OWNER, DEFAULT_RECORD, f"priority: p1\nscope: app/**\nacceptance: {acceptance}\n")

        def cli(*args: str) -> subprocess.CompletedProcess:
            ran[0] += 1
            return subprocess.run([sys.executable, __file__, *args, "--owner-email", OWNER],
                                  cwd=tmp, capture_output=True, text=True)

        p = cli("check", "--item", "#5", "--paths", "web/x.css")
        if p.returncode != NO_GO or "is OPEN" not in p.stdout:
            failures.append(f"e2e-open-fires: rc={p.returncode} {p.stdout}{p.stderr}")
        p = cli("status")
        if p.returncode != STATUS_EXIT[S_OPEN] or "source=owner-commit" not in p.stdout:
            failures.append(f"e2e-status-open: rc={p.returncode} {p.stdout}{p.stderr}")
        flag.write_text("0")
        ev = repo / "evidence.json"
        p = cli("status", "--evidence", str(ev))
        if p.returncode != STATUS_EXIT[S_DONE] or not ev.is_file() or json.loads(ev.read_text())["state"] != S_DONE:
            failures.append(f"e2e-done: rc={p.returncode} {p.stdout}{p.stderr}")
        head = commit(OWNER, "web/x.css", "x\n", "style: tweak")
        p = cli("check", "--base", base, "--head", head)
        if p.returncode != GO:
            failures.append(f"e2e-done-range-go: rc={p.returncode} {p.stdout}{p.stderr}")
        flag.write_text("1")
        commit(AGENT, DEFAULT_RECORD, f"priority: p1\nscope: app/** web/**\nacceptance: {acceptance}\n",
               "chore: widen scope")
        p = cli("check", "--paths", "web/x.css")
        if p.returncode != NO_GO or "untrusted" not in p.stdout:
            failures.append(f"e2e-agent-widen-fires: rc={p.returncode} {p.stdout}{p.stderr}")

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"focus_gate selftest: OK ({ran[0]} cases)")
    return 0


def main(argv: list | None = None) -> int:
    """CLI entry point: `status`, `check`, or `--selftest` (see module docstring)."""
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["--selftest"]:
        return _selftest()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--record", default=DEFAULT_RECORD, help="record path (default .claude/PRIORITY.md)")
    common.add_argument("--rev", help="revision to read the record at (default HEAD, or --head when given)")
    common.add_argument("--owner-email", action="append", help="owner author email; repeatable")
    common.add_argument("--commit-only", action="store_true", help="disable the owner-quote route")
    common.add_argument("--require-signed", action="store_true", help="record commits need a good signature")
    common.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="acceptance timeout seconds")
    common.add_argument("--repo", default=".", help="repository directory (default .)")
    parser = argparse.ArgumentParser(description="Block work outside an OPEN owner priority.")
    parser.add_argument("--selftest", action="store_true", help="run the built-in selftest and exit")
    sub = parser.add_subparsers(dest="cmd")
    p_status = sub.add_parser("status", parents=[common], help="print OPEN/DONE/BLOCKED with evidence")
    p_status.add_argument("--evidence", help="also write the evidence as JSON to this file")
    p_check = sub.add_parser("check", parents=[common], help="GO/NO-GO for an item and/or changed paths")
    p_check.add_argument("--item", help="item ref, e.g. #123")
    p_check.add_argument("--paths", nargs="*", default=[], help="changed repo-relative paths")
    p_check.add_argument("--base", help="range base (changed paths = merge-base..head)")
    p_check.add_argument("--head", help="range head")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.cmd is None:
        parser.error("a subcommand is required: status or check")
    git = real_git(args.repo)
    try:
        cwd = git(["rev-parse", "--show-toplevel"]).strip()
    except GitError as exc:
        print(f"focus_gate: error: not a git repository: {exc}", file=sys.stderr)
        return ERROR
    paths = list(getattr(args, "paths", []) or [])
    if args.cmd == "check":
        if bool(args.base) != bool(args.head):
            parser.error("--base and --head go together")
        if args.base:
            try:
                paths += _range_paths(git, args.base, args.head)
            except GitError as exc:
                print(f"focus_gate: error: {exc}", file=sys.stderr)
                return ERROR
        if not args.item and not paths and not args.base:
            parser.error("check needs --item, --paths, or --base/--head")
        if args.base and not paths and not args.item:
            print("focus_gate: GO — 0 paths changed in range")
            return GO
    rev = args.rev or getattr(args, "head", None) or "HEAD"
    owners = resolve_owners(args.owner_email, git)
    st = evaluate(git, real_cmd, args.record, rev, owners, cwd, args.timeout,
                  args.commit_only, args.require_signed)
    if args.cmd == "status":
        for line in status_lines(st):
            print(line)
        if args.evidence:
            write_evidence(args.evidence, st)
        return STATUS_EXIT[st.state]
    code, lines = check(st, args.item, paths, load_fix_class_gate())
    for line in lines + [f"  {ln}" for ln in status_lines(st)[1:4]]:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
