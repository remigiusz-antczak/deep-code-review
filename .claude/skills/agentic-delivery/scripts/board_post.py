#!/usr/bin/env python3
"""board_post.py — compose one typed, capped, privacy-linted coordination post.

WHY THIS EXISTS (the failures it closes)
----------------------------------------
Free-text posting to a shared coordination issue fails in four recurring ways:
(1) chatter — status ticks, acks, "ready for you" pings — crowds out the posts
that change what another agent should do, and every one of them relays state
the forge already holds; (2) posts grow into multi-thousand-character state
documents nobody re-reads; (3) a body passed as a shell string gets
interpolated — one unquoted backtick runs a command and pastes its output
(emails, paths) into a shared thread; (4) "root cause found, fixed for good"
is asserted without a proof anyone can check, then recurs. This script is the
only write path: it builds the header itself, reads the body from a FILE, and
refuses a post that breaks a rule, before anything reaches the forge.

RULES (each rejection names the rule; exit 1)
---------------------------------------------
- TYPE must be one of CLAIM RELEASE DECISION HANDOFF BLOCKER FIX-CLAIM
  QUESTION ANSWER. STATUS/ACK/READY/LANDED are rejected as chatter; a body
  that is only an acknowledgement ("ok", "thanks", "+1", ...) is rejected too.
- Header + body <= MAX_POST_CHARS (1000). Longer content belongs in a
  committed file or PR, linked from the post.
- The body comes from --body-file only; there is no --body flag, so nothing a
  shell could interpolate ever becomes post text. The body may not start with
  its own `[agent:` header (the script writes the only header).
- Privacy lint over header + body: email addresses, absolute home-directory
  paths, secret-shaped tokens (the same shapes this repo's committed
  `.banlist.txt` blocks), plus every pattern in a banlist file (`--banlist`,
  else `<git toplevel>/.banlist.txt` and its `.banlist.local.txt` sibling when
  present). A hit reports the line number and rule name, never the match, so
  a secret is not echoed into a log. An unparseable banlist pattern fails
  closed (exit 2).
- FIX-CLAIM requires `--sha` and `--test`, and verifies both with git in
  --repo-dir: the SHA resolves to a commit that is an ancestor of the default
  branch (`--default-branch`, else `origin/HEAD`); the test file exists at
  that SHA; and a `path::name` test id's name occurs in that file there.
  A claim of "fixed" is thus pinned to a commit on the governing branch and a
  regression test that exists in it.

OUTPUT
------
Writes the composed post (header line + body) to --out (default:
`<body-file>.post`) and prints the exact `gh issue comment ... --body-file`
command. With --post it runs that command instead (an external send: the
caller decides). Server time is authoritative, so the post carries no
hand-typed timestamp.

USAGE
-----
  board_post.py --repo O/N --issue N --agent ID --type CLAIM --refs '#12' \\
                --body-file note.md [--ttl 90] [--post]
  board_post.py ... --type FIX-CLAIM --refs '#12' --sha abc1234 \\
                --test tests/test_x.py::test_y [--topic ratchet] --body-file fix.md
  board_post.py --selftest

Exit codes: 0 composed (and posted with --post); 1 rejected by a rule;
2 usage, git, forge, or banlist error.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_common as bc  # noqa: E402  (sibling module, path set above)

OK = 0
REJECTED = 1
ERROR = 2

MAX_POST_CHARS = 1000

# Secret shapes mirror the committed repo `.banlist.txt` so the lint works in a
# target repo that has no banlist; a present banlist ADDS to these.
BUILTIN_RULES = (
    ("email address", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("absolute home path", r"(?:/Users/|/home/|[A-Za-z]:\\Users\\)[^/\\\s]+"),
    ("cloud access key", r"(?:AKIA|ASIA)[0-9A-Z]{16}"),
    ("forge token", r"gh[pousr]_[A-Za-z0-9]{36,}"),
    ("chat token", r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    ("api key", r"sk-[A-Za-z0-9]{20,}"),
    ("private key block", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
)
ACK_ONLY = {"ack", "acked", "ok", "okay", "thanks", "thank you", "ty", "+1", "noted", "roger", "ready", "done", "lgtm"}


class GitError(Exception):
    """A git query could not be answered (not a repo, bad ref, git missing)."""


def load_rules(banlist: str | None, repo_dir: str, runner) -> list:
    """Compile builtin rules plus banlist patterns into (name, regex) pairs.

    Side-effects: reads banlist files; may run `git rev-parse` to find the
    repo top level. Banlist patterns are named by file and ordinal only — a
    local banlist holds private identifiers, so its patterns are never echoed.
    Raises ValueError on an unreadable explicit banlist or a bad pattern.
    """
    rules = [(name, re.compile(rx)) for name, rx in BUILTIN_RULES]
    paths = []
    if banlist:
        if not os.path.isfile(banlist):
            raise ValueError(f"banlist not found: {banlist}")
        paths.append(banlist)
    else:
        rc, top, _ = runner(["git", "-C", repo_dir, "rev-parse", "--show-toplevel"])
        if rc == 0 and os.path.isfile(os.path.join(top.strip(), ".banlist.txt")):
            paths.append(os.path.join(top.strip(), ".banlist.txt"))
    for primary in list(paths):
        root, ext = os.path.splitext(primary)
        if os.path.isfile(f"{root}.local{ext}"):
            paths.append(f"{root}.local{ext}")
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            actionable = [ln.strip() for ln in fh if ln.strip() and not ln.strip().startswith("#")]
        for i, pattern in enumerate(actionable, 1):
            try:
                rules.append((f"{os.path.basename(path)} pattern #{i}", re.compile(pattern)))
            except re.error as exc:
                raise ValueError(f"{os.path.basename(path)} pattern #{i} is not a valid regex ({exc})") from exc
    return rules


def privacy_hits(text: str, rules: list) -> list:
    """Return 'line N: <rule name>' for every rule hit, never the matched text. Pure."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        hits += [f"line {n}: {name}" for name, rx in rules if rx.search(line)]
    return hits


def verify_fix_claim(sha: str, test: str, default_branch: str | None, repo_dir: str, runner) -> list:
    """Return rule violations for a FIX-CLAIM's sha:/test: (empty = verified).

    Side-effects: read-only git queries through `runner`. Raises GitError when
    git cannot answer at all (no repo, no resolvable default branch), which the
    caller turns into exit 2 — an unanswerable proof is not a passing proof.
    """
    def git(*args):
        return runner(["git", "-C", repo_dir, *args])

    ref = default_branch
    if ref and ref.startswith("-"):
        raise GitError(f"default branch {ref!r} looks like an option, not a ref")
    if not ref:
        rc, out, _ = git("symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
        if rc != 0:
            raise GitError("cannot resolve origin/HEAD; pass --default-branch")
        ref = out.strip()
    rc, _, _ = git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if rc != 0:
        raise GitError(f"default branch {ref!r} does not resolve to a commit")
    rc, full, _ = git("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
    if rc != 0:
        return [f"sha:{sha} is not a commit in this repository"]
    full = full.strip()
    rc, _, err = git("merge-base", "--is-ancestor", full, ref)
    if rc == 1:
        return [f"sha:{sha} is not reachable from the default branch {ref} (a fix off the governing branch fixes nothing)"]
    if rc != 0:
        raise GitError(f"merge-base failed: {err.strip()[:200]}")
    path, _, name = test.partition("::")
    rc, _, _ = git("cat-file", "-e", f"{full}:{path}")
    if rc != 0:
        return [f"test:{test} — file {path} does not exist at sha:{sha}"]
    if name:
        rc, _, _ = git("grep", "-q", "-F", "-e", name, full, "--", path)
        if rc != 0:
            return [f"test:{test} — {name!r} does not occur in {path} at sha:{sha}"]
    return []


def compose(args, body: str, rules: list, runner) -> tuple:
    """Validate one post; return (violations, composed_text). Pure except git.

    Side-effects: only the read-only git queries a FIX-CLAIM needs.
    """
    fields = {k: str(v) for k, v in (("sha", args.sha), ("test", args.test), ("topic", args.topic),
                                     ("ttl", args.ttl), ("to", args.to), ("of", args.of), ("gate", args.gate)) if v is not None}
    errors = []
    if not bc.validate_agent(args.agent):
        errors.append("--agent must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}")
    errors += bc.validate_post(args.type, args.refs, fields)
    stripped = body.strip()
    if not stripped:
        errors.append("body is empty: a post with nothing to say is chatter")
    elif stripped.lower().strip(" .!") in ACK_ONLY:
        errors.append("body is only an acknowledgement: your board_sync.py cursor advance is the ack")
    if stripped.startswith("[agent:"):
        errors.append("body starts with its own [agent:] header; the script writes the only header")
    header = bc.format_header(args.agent, args.type, args.refs, fields)
    text = f"{header}\n{body.rstrip()}\n"
    if len(text) > MAX_POST_CHARS:
        errors.append(f"post is {len(text)} chars, over the {MAX_POST_CHARS}-char cap; link a committed file or PR instead")
    errors += [f"privacy: {h}" for h in privacy_hits(text, rules)]
    if args.type == "FIX-CLAIM" and not errors:
        errors += verify_fix_claim(args.sha, args.test, args.default_branch, args.repo_dir, runner)
    return errors, text


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser. There is deliberately no --body option. Pure."""
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0], allow_abbrev=False)
    p.add_argument("--repo")
    p.add_argument("--issue", type=int)
    p.add_argument("--agent", default="")
    p.add_argument("--type", default="")
    p.add_argument("--refs", default="-")
    p.add_argument("--body-file")
    p.add_argument("--sha")
    p.add_argument("--test")
    p.add_argument("--topic")
    p.add_argument("--ttl", type=int)
    p.add_argument("--to")
    p.add_argument("--of")
    p.add_argument("--gate")
    p.add_argument("--default-branch")
    p.add_argument("--repo-dir", default=".")
    p.add_argument("--banlist")
    p.add_argument("--out")
    p.add_argument("--post", action="store_true", help="send it (an external write); default prints the command")
    p.add_argument("--selftest", action="store_true")
    return p


def run(argv, runner, out=sys.stdout) -> int:
    """Parse, validate, write the composed post, then print or send. Returns an exit code.

    Side-effects: reads the body file and banlist, git queries, writes --out,
    and with --post runs `gh issue comment` through `runner`.
    """
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return ERROR if exc.code else OK
    if args.selftest:
        return _selftest()
    if not (args.repo and bc.validate_repo(args.repo) and args.issue and args.issue > 0 and args.body_file):
        print("board_post: --repo OWNER/NAME, --issue N (>0) and --body-file are required", file=sys.stderr)
        return ERROR
    try:
        with open(args.body_file, encoding="utf-8") as fh:
            body = fh.read()
        rules = load_rules(args.banlist, args.repo_dir, runner)
        errors, text = compose(args, body, rules, runner)
    except (OSError, ValueError, GitError) as exc:
        print(f"board_post: {exc}", file=sys.stderr)
        return ERROR
    if errors:
        print("board_post: REJECTED", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return REJECTED
    dest = args.out or f"{args.body_file}.post"
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(text)
    cmd = ["gh", "issue", "comment", str(args.issue), "--repo", args.repo, "--body-file", dest]
    if not args.post:
        out.write(" ".join(shlex.quote(c) for c in cmd) + "\n")
        return OK
    rc, stdout, err = runner(cmd)
    if rc != 0:
        print(f"board_post: gh issue comment failed (rc {rc}): {err.strip()[:300]}", file=sys.stderr)
        return ERROR
    out.write(stdout)
    return OK


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------


def _git_repo(tmp: str) -> dict:
    """A throwaway repo: main has the regression test; side has an unmerged commit."""
    repo = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(repo, "tests"))
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def git(*a):
        return subprocess.run(["git", "-C", repo, *a], check=True, capture_output=True, text=True, env=env).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.email", "jane@example.com")
    git("config", "user.name", "Jane Smith")
    with open(os.path.join(repo, "tests", "test_ratchet.py"), "w") as fh:
        fh.write("def test_allowlist_pin():\n    assert True\n")
    git("add", ".")
    git("commit", "-q", "-m", "fix: pin allowlist")
    on_main = git("rev-parse", "HEAD")
    git("checkout", "-q", "-b", "side")
    git("commit", "-q", "--allow-empty", "-m", "unmerged work")
    off_main = git("rev-parse", "HEAD")
    git("checkout", "-q", "main")
    return {"repo": repo, "on": on_main[:10], "off": off_main[:10]}


def _selftest() -> int:
    tmp = tempfile.mkdtemp(prefix="board-post-selftest-")
    g = _git_repo(tmp)
    banlist = os.path.join(tmp, "banlist.txt")
    with open(banlist, "w") as fh:
        fh.write("# fixture policy\nAcme Capital\n")

    def attempt(body, *extra, post=False):
        path = os.path.join(tmp, f"body-{len(os.listdir(tmp))}.md")
        with open(path, "w") as fh:
            fh.write(body)
        gh = bc.FakeGh()
        runner = lambda a, cwd=None: gh(a, cwd) if a[0] == "gh" else bc.default_runner(a, cwd)  # noqa: E731
        argv = ["--repo", "acme/board", "--issue", "7", "--agent", "alpha", "--body-file", path,
                "--repo-dir", g["repo"], "--default-branch", "main", "--banlist", banlist, *extra]
        if post:
            argv.append("--post")
        result, stderr = _capture_stderr(lambda buf: run(argv, runner, buf))
        return result, stderr, gh, path

    def expect(code_want, body, *extra, needle="", post=False):
        (rc, stdout), stderr, gh, path = attempt(body, *extra, post=post)
        ok = rc == code_want and needle in (stderr + stdout)
        return ok, f"rc={rc} want={code_want} out={stdout!r} err={stderr!r}"

    fix = ["--type", "FIX-CLAIM", "--refs", "#12", "--topic", "ratchet"]
    token = "gh" + "p_" + "A1b2" * 10  # built at runtime so no token-shaped literal is committed

    def valid_claim():
        (rc, stdout), _, gh, path = attempt("Taking the ratchet gate.", "--type", "CLAIM", "--refs", "#12", "--ttl", "90")
        posted = open(path + ".post").read()
        ok = (rc == OK and posted.startswith("[agent:alpha] CLAIM refs:#12 ttl:90\n")
              and "gh issue comment 7 --repo acme/board --body-file" in stdout and gh.calls == [])
        return ok, f"{rc} {stdout!r} {posted!r}"

    def post_sends_via_body_file():
        (rc, _), _, gh, path = attempt("Handing #12 over.", "--type", "HANDOFF", "--refs", "#12", "--to", "beta", post=True)
        call = gh.calls[-1] if gh.calls else []
        return rc == OK and call[:3] == ["gh", "issue", "comment"] and call[-1] == path + ".post", str(gh.calls)

    def no_body_flag():
        argv = ["--repo", "acme/board", "--issue", "7", "--agent", "a", "--type", "CLAIM", "--body", "x"]
        (rc, _), stderr = _capture_stderr(lambda buf: run(argv, bc.FakeGh(), buf))
        return rc == ERROR and "unrecognized arguments: --body" in stderr, f"rc={rc} {stderr!r}"

    def exact_cap_accepted():
        header = "[agent:alpha] QUESTION refs:-\n"
        body = "q" * (1000 - len(header) - 1)  # literal 1000: the cap is pinned, not read back
        return expect(OK, body, "--type", "QUESTION")

    def token_not_echoed():
        (rc, _), stderr, _, _ = attempt(f"use {token}", "--type", "QUESTION")
        return rc == REJECTED and "forge token" in stderr and token not in stderr, stderr

    cases = [
        ("valid-claim-composed-not-sent", valid_claim),
        ("post-sends-via-body-file", post_sends_via_body_file),
        ("status-chatter-rejected", lambda: expect(REJECTED, "still on it", "--type", "STATUS", needle="chatter")),
        ("ack-chatter-rejected", lambda: expect(REJECTED, "x", "--type", "ACK", needle="chatter")),
        ("ready-chatter-rejected", lambda: expect(REJECTED, "x", "--type", "READY", needle="chatter")),
        ("ack-only-body-rejected", lambda: expect(REJECTED, "Thanks!", "--type", "ANSWER", "--of", "123", needle="acknowledgement")),
        ("unknown-type-rejected", lambda: expect(REJECTED, "x", "--type", "PING", needle="unknown TYPE")),
        ("oversize-rejected", lambda: expect(REJECTED, "x" * 1000, "--type", "DECISION", needle="1000-char cap")),
        ("exact-cap-accepted", exact_cap_accepted),
        ("no-body-flag-exists", no_body_flag),
        ("forged-body-header-rejected", lambda: expect(REJECTED, "[agent:beta] DECISION refs:-\nx", "--type", "QUESTION", needle="own [agent:]")),
        ("email-rejected", lambda: expect(REJECTED, "ping jane@example.com", "--type", "QUESTION", needle="email address")),
        ("home-path-rejected", lambda: expect(REJECTED, "see /Users/jsmith/x.log", "--type", "QUESTION", needle="home path")),
        ("token-rejected-not-echoed", token_not_echoed),
        ("banlist-pattern-rejected", lambda: expect(REJECTED, "for Acme Capital", "--type", "QUESTION", needle="banlist.txt pattern #1")),
        ("zero-ttl-rejected", lambda: expect(REJECTED, "taking it", "--type", "CLAIM", "--refs", "#12", "--ttl", "0", needle="ttl must be")),
        ("claim-without-refs-rejected", lambda: expect(REJECTED, "taking it", "--type", "CLAIM", needle="must name the item")),
        ("bad-agent-id-rejected", lambda: expect(REJECTED, "x y", "--type", "QUESTION", "--agent", "a b", needle="--agent")),
        ("fix-claim-without-sha-rejected", lambda: expect(REJECTED, "fixed", *fix, "--test", "tests/test_ratchet.py", needle="requires sha:")),
        ("fix-claim-without-test-rejected", lambda: expect(REJECTED, "fixed", *fix, "--sha", g["on"], needle="requires test:")),
        ("fix-claim-off-default-branch-rejected", lambda: expect(REJECTED, "fixed", *fix, "--sha", g["off"], "--test", "tests/test_ratchet.py", needle="not reachable")),
        ("fix-claim-unknown-sha-rejected", lambda: expect(REJECTED, "fixed", *fix, "--sha", "deadbeef12", "--test", "tests/test_ratchet.py", needle="not a commit")),
        ("fix-claim-missing-test-file-rejected", lambda: expect(REJECTED, "fixed", *fix, "--sha", g["on"], "--test", "tests/test_nope.py", needle="does not exist")),
        ("fix-claim-missing-test-name-rejected", lambda: expect(REJECTED, "fixed", *fix, "--sha", g["on"], "--test", "tests/test_ratchet.py::test_other", needle="does not occur")),
        ("fix-claim-verified-accepted", lambda: expect(OK, "Pinned allowlist; regression test added.", *fix, "--sha", g["on"], "--test", "tests/test_ratchet.py::test_allowlist_pin")),
        ("fix-claim-option-shaped-branch-errors", lambda: expect(ERROR, "fixed", *fix, "--sha", g["on"], "--test", "tests/test_ratchet.py", "--default-branch=--output=x", needle="looks like an option")),
        ("fix-claim-bad-default-branch-errors", lambda: expect(ERROR, "fixed", *fix, "--sha", g["on"], "--test", "tests/test_ratchet.py", "--default-branch", "nope", needle="does not resolve")),
    ]
    return bc.run_checks("board_post", cases)


def _capture_stderr(fn):
    """Run fn(stdout_buffer) with stderr captured; return ((rc, stdout), stderr)."""
    import io

    out, err, saved = io.StringIO(), io.StringIO(), sys.stderr
    sys.stderr = err
    try:
        rc = fn(out)
    finally:
        sys.stderr = saved
    return (rc, out.getvalue()), err.getvalue()


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:], bc.default_runner))
