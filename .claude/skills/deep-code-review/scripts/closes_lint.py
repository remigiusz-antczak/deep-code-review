#!/usr/bin/env python3
"""closes_lint.py — a closing keyword may only reference an issue/PR this change owns.

WHY THIS EXISTS (the failure it closes, issue #1121)
------------------------------------------------------
A reviewed, ready pull request was closed without merging, and nobody had
closed it. An unrelated commit — from a DIFFERENT pull request — carried a
stray `Closes #<n>` line in its message (a copy-paste leftover in a squashed
or amended commit). When that commit reached the default branch, the forge's
closing-keyword automation closed the OTHER PR. The close event is
attributed to whoever pushed, so it reads as deliberate and nobody questions
it. This gate scans a commit range for GitHub closing keywords and fails
when a referenced number is not in an explicitly declared allowed set — the
set of issues/PRs THIS change actually owns.

WHAT COUNTS AS A CLOSING KEYWORD (case-insensitive)
------------------------------------------------------
`close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves`,
`resolved` — GitHub's own closing-keyword list — followed by a colon and/or
whitespace, then a reference: `#N`, `owner/repo#N`, or an issue/PR URL
`https://<host>/owner/repo/issues/N` or `.../pull/N` (`Closes #12`,
`Closes: #12`, and `Closes:#12` all count; `Closes#12`, glued with neither
separator, does not). The keyword must not be glued to a preceding letter,
digit, or underscore — `(?<![A-Za-z0-9_])` — so punctuation or markup right
before it still counts (`(fixes #12)`, `**Closes #12**`, `done;closes #12`),
while an ordinary English word that merely contains a keyword does not
(`prefixes #12`: the `fixes` inside it is glued to `pre`).

HONESTY (read this before wiring it into CI or citing it in a report)
-----------------------------------------------------------------------
This is a heuristic LINT, not a re-implementation of GitHub's own closing-
keyword parser (GitHub does not publish one; `unattended-trackers.md`
documents the real behavior as widely observed to match anywhere in a PR
body or commit message, including inside a quote or a code fence). This
tool deliberately uses a bounded, deterministic position rule (the keyword
is not glued to a preceding word character) so its verdict is reproducible.
It can over-report — it has no quote/code-fence awareness, so a keyword
inside a quote or a fence still counts — and it will MISS a pair GitHub
might act on when the keyword is glued to a word character (`xCloses #12`)
or the reference takes a form it does not parse (a URL with no
`/issues/N` or `/pull/N` path). It does not aggregate a comma-separated
reference list (`Closes #12, #34`) beyond the first reference immediately
following the keyword — a second, bare `#34` with no keyword of its own is
not itself a closing reference by this tool's rule (nor reliably by
GitHub's, which is why the honest style is one keyword per issue, per
line). A URL's host is not checked: any host is keyed by its owner/repo
path. Never claim this tool proves a commit message's closing references
are "correct" — it proves only that every one it can see appears in the
declared allowed set.

ALLOWED SET (keyed on repository AND number)
----------------------------------------------
Every reference is keyed as (repository, number). An unqualified `#N` is
the LOCAL repository; `owner/repo#N` and a URL are keyed by that owner/repo
(case-insensitive), so `other/repo#12` never matches an allowed `12`. Pass
`--repo OWNER/REPO` to name the local repository: a qualified reference or
URL to it then keys as local, the same as `#N`. Without `--repo`, a
qualified self-reference must be allowed in qualified form.
Either `--allow SPEC` (comma-separated; each entry `N`, `#N`, or
`owner/repo#N`), or `--pr-body FILE` (a file holding the landing PR's own
body text; the allowed set is every reference THAT file's own closing
keywords make — same regex, same keying). Both may be given together (the
sets union). Neither given is a usage error (exit 2): there is nothing to
check a reference against.

EXIT CODES (fail-closed; every branch below is load-bearing)
---------------------------------------------------------------
  0  every closing-keyword reference found in base..head is in the allowed
     set, including the legitimately-empty case of zero references or zero
     commits in range.
  1  at least one closing-keyword reference names a number outside the
     allowed set; each is printed as its own FAIL line (commit + line).
  2  FAIL CLOSED — usage error (a malformed --allow entry or --repo
     included), an unreadable --pr-body file, an unresolvable --base/--head,
     or the working directory is not a git repository. Never a silent skip.

Stdlib only (subprocess + git; no network, no third-party parser).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NoReturn, Optional, Tuple

OK = 0
FAIL = 1
ERROR = 2

ZERO_SHA = "0" * 40

# GitHub's own closing-keyword set (case-insensitive): close/closes/closed,
# fix/fixes/fixed, resolve/resolves/resolved.
_KEYWORD = r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)"
_REPO = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
# `#N`, `owner/repo#N`, or an issue/PR URL `<scheme>://<host>/owner/repo/(issues|pull)/N`.
_REF = (rf"(?:(?P<repo>{_REPO})?#(?P<num>\d+)"
        rf"|https?://[^\s/]+/(?P<urepo>{_REPO})/(?:issues|pull)/(?P<unum>\d+))")
# A separator between the keyword and the reference: a colon (with zero or
# more following whitespace — `Closes:#12` and `Closes: #12` both count) or,
# with no colon, one or more whitespace characters (`Closes #12`). Either
# form requires at least one of {colon, whitespace} — `Closes#12` (glued,
# neither) does not count.
_SEP = r"(?::\s*|\s+)"
# The keyword must not be glued to a preceding letter, digit, or underscore:
# line start, whitespace, punctuation, and markup all pass (`(fixes #12)`,
# `**Closes #12**`, `done;closes #12`); `prefixes #12` does not.
_CLOSES_RE = re.compile(
    rf"(?<![A-Za-z0-9_]){_KEYWORD}{_SEP}{_REF}",
    re.IGNORECASE,
)
_REPO_RE = re.compile(rf"^{_REPO}$")
_ALLOW_RE = re.compile(rf"^(?:(?P<repo>{_REPO})?#)?(?P<num>\d+)$")

# A reference key: (lower-cased "owner/repo", or None for the local repository; number).
RefKey = Tuple[Optional[str], int]


def die(code: int, msg: str) -> NoReturn:
    print(f"closes_lint: {msg}", file=sys.stderr)
    raise SystemExit(code)


def ref_key(repo: str | None, num: int, local_repo: str | None = None) -> RefKey:
    """Key one reference. Pure. `repo` None (an unqualified `#N`) is the local
    repository; a qualified repo is case-folded, and folds to None when it
    equals `local_repo` (already case-folded or not)."""
    if repo is None:
        return (None, num)
    folded = repo.casefold()
    if local_repo is not None and folded == local_repo.casefold():
        return (None, num)
    return (folded, num)


def show_key(key: RefKey) -> str:
    """Render a key as it reads in a message: `#N` (local) or `owner/repo#N`. Pure."""
    repo, num = key
    return f"#{num}" if repo is None else f"{repo}#{num}"


def find_refs(text: str, local_repo: str | None = None) -> list[tuple[int, str, RefKey]]:
    """Return (1-based line number, matched text, reference key) for every
    closing-keyword reference in `text`, scanned one physical line at a time.
    Pure. Keys follow `ref_key` (unqualified = local; `local_repo` folds a
    qualified self-reference or URL to local)."""
    hits: list[tuple[int, str, RefKey]] = []
    for n, line in enumerate(text.splitlines(), start=1):
        for m in _CLOSES_RE.finditer(line):
            if m.group("num") is not None:
                key = ref_key(m.group("repo"), int(m.group("num")), local_repo)
            else:
                key = ref_key(m.group("urepo"), int(m.group("unum")), local_repo)
            hits.append((n, m.group(0).strip(), key))
    return hits


class GitError(RuntimeError):
    """A git invocation failed in a way the caller must fail closed on."""


def _run_git(repo: str, args: list[str]) -> str:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip() or f"git {' '.join(args)} failed (rc={proc.returncode})")
    return proc.stdout


def _is_git_repo(repo: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _resolve_commit(repo: str, ref: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def run_lint(repo: str, base: str, head: str, allowed: set[RefKey],
             local_repo: str | None = None) -> tuple[int, list[str]]:
    """Evaluate `base..head` in `repo` against `allowed` (a set of `ref_key`
    keys); return (exit_code, lines). Reads git; writes nothing.

    Fail-closed ordering: repo-ness, then the all-zeros sentinel, then ref
    resolution, then the range walk, are each checked before any commit is
    inspected — so an unresolvable input can never fall through to a 0/1
    verdict on a partial or wrong commit set.
    """
    if not _is_git_repo(repo):
        return ERROR, [f"error: {repo!r} is not a git repository"]

    if base == ZERO_SHA or head == ZERO_SHA:
        return ERROR, [
            "error: --base/--head is the all-zeros SHA (git's placeholder for a "
            "new/deleted-branch push). This is not a usable diff endpoint. Pass "
            "the pull request's declared base ref, or a computed `git merge-base` "
            "between the branches, instead."
        ]

    base_sha = _resolve_commit(repo, base)
    if base_sha is None:
        return ERROR, [f"error: --base {base!r} does not resolve to a commit"]
    head_sha = _resolve_commit(repo, head)
    if head_sha is None:
        return ERROR, [f"error: --head {head!r} does not resolve to a commit"]

    try:
        # Merges included: a squash-merge is a normal single-parent commit and
        # a merge commit's own message can carry a hand-edited stray keyword
        # too — never narrow the scan to skip either.
        shas = _run_git(repo, ["rev-list", "--reverse", f"{base_sha}..{head_sha}"]).splitlines()
        shas = [s for s in shas if s.strip()]
    except GitError as exc:
        return ERROR, [f"error: cannot list {base}..{head}: {exc}"]

    lines: list[str] = []
    fail = False
    for sha in shas:
        try:
            body = _run_git(repo, ["log", "-1", "--format=%B", sha])
        except GitError as exc:
            return ERROR, [f"error: cannot read commit message for {sha}: {exc}"]
        for n, matched, key in find_refs(body, local_repo):
            if key in allowed:
                continue
            fail = True
            shown = ", ".join(sorted(show_key(k) for k in allowed))
            lines.append(
                f"FAIL {sha[:7]} L{n}: {matched!r} references {show_key(key)}, not in the "
                f"allowed set [{shown}] — strip it unless this change is "
                "meant to close it (issue #1121: a stray closing keyword from an "
                "unrelated commit auto-closes a ready PR when it reaches the "
                "default branch)"
            )

    if fail:
        return FAIL, lines
    return OK, [f"closes_lint: ok ({len(shas)} commit(s) checked, 0 out-of-set closing reference(s))"]


def _parse_allow(spec: str, local_repo: str | None = None) -> set[RefKey]:
    """Parse `--allow` (entries `N`, `#N`, or `owner/repo#N`) into keys; exit 2 on a malformed entry."""
    out: set[RefKey] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m = _ALLOW_RE.match(part)
        if m is None:
            die(ERROR, f"--allow entry is not N, #N, or owner/repo#N: {part!r}")
        out.add(ref_key(m.group("repo"), int(m.group("num")), local_repo))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail when a closing keyword (close/fix/resolve + #N) in base..head "
            "references a number outside an explicitly declared allowed set."
        )
    )
    parser.add_argument("--base", help="range base ref (exclusive)")
    parser.add_argument("--head", help="range head ref (inclusive)")
    parser.add_argument("--allow", help="comma-separated references this change may close: N, #N, or owner/repo#N")
    parser.add_argument(
        "--pr-body", metavar="FILE",
        help="file holding the landing PR's own body; its own closing keywords define (part of) the allowed set",
    )
    parser.add_argument("--repo", metavar="OWNER/REPO",
                        help="the local repository; a qualified reference or URL to it keys as unqualified #N")
    parser.add_argument("--selftest", action="store_true", help="run the built-in selftest and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.base or not args.head:
        parser.error("--base and --head are both required")
        return ERROR  # pragma: no cover — parser.error() already exits(2)

    local_repo = None
    if args.repo is not None:
        if not _REPO_RE.match(args.repo):
            die(ERROR, f"--repo is not OWNER/REPO: {args.repo!r}")
        local_repo = args.repo.casefold()

    allowed: set[RefKey] = set()
    if args.allow:
        allowed |= _parse_allow(args.allow, local_repo)
    if args.pr_body:
        path = Path(args.pr_body)
        if not path.is_file():
            die(ERROR, f"--pr-body file not found: {path}")
        try:
            body_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            die(ERROR, f"--pr-body file unreadable: {exc}")
        allowed |= {key for _, _, key in find_refs(body_text, local_repo)}
    if not args.allow and not args.pr_body:
        parser.error("one of --allow or --pr-body is required (nothing to check references against)")

    code, lines = run_lint(".", args.base, args.head, allowed, local_repo)
    for line in lines:
        print(line)
    return code


# ---------------------------------------------------------------------------
# Selftest fixtures. Fictional placeholder identity only (jane@example.com);
# no third-party names, no real issue numbers beyond this repo's own #1121
# cited in the FAIL message text above (a doc reference, not fixture data).
# ---------------------------------------------------------------------------
_GIT_ENV_NAME = "Jane Smith"
_GIT_ENV_EMAIL = "jane@example.com"


def _sh(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _sh(repo, "init", "-q")
    _sh(repo, "config", "user.name", _GIT_ENV_NAME)
    _sh(repo, "config", "user.email", _GIT_ENV_EMAIL)
    _sh(repo, "config", "commit.gpgsign", "false")
    _sh(repo, "config", "tag.gpgsign", "false")


def _commit(repo: Path, message: str, files: dict[str, str]) -> str:
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        _sh(repo, "add", rel)
    _sh(repo, "commit", "-q", "-m", message)
    return _sh(repo, "rev-parse", "HEAD")


def _run_tool(repo: Path, base: str, head: str, allow: str | None = None,
              pr_body: Path | None = None, local: str | None = None) -> tuple[int, str]:
    args = [sys.executable, __file__, "--base", base, "--head", head]
    if allow is not None:
        args += ["--allow", allow]
    if pr_body is not None:
        args += ["--pr-body", str(pr_body)]
    if local is not None:
        args += ["--repo", local]
    proc = subprocess.run(args, cwd=str(repo), capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)


def _selftest() -> int:
    """Build throwaway git repos and assert every mandatory case's exact (rc, evidence)."""
    failures: list[str] = []

    def check(label: str, rc: int, out: str, want_rc: int,
              must_have: tuple[str, ...] = (), must_not: tuple[str, ...] = ()) -> None:
        if rc != want_rc:
            failures.append(f"{label}: rc={rc}, want {want_rc} (output: {out!r})")
        for needle in must_have:
            if needle not in out:
                failures.append(f"{label}: output missing {needle!r} (output: {out!r})")
        for needle in must_not:
            if needle in out:
                failures.append(f"{label}: output must not contain {needle!r} (output: {out!r})")

    with tempfile.TemporaryDirectory(prefix="closes_lint_selftest_") as tmp:
        tmp_path = Path(tmp)

        # 1) unit tests of the regex/extractor, no git involved.
        # Keys: (None, N) is the local repository; ("owner/repo", N) is qualified.
        cases = [
            ("Closes #12", [(1, (None, 12))]),
            ("closes #12", [(1, (None, 12))]),
            ("Closed #12", [(1, (None, 12))]),
            ("Fix #12", [(1, (None, 12))]),
            ("Fixes #12", [(1, (None, 12))]),
            ("Fixed #12", [(1, (None, 12))]),
            ("Resolve #12", [(1, (None, 12))]),
            ("Resolves #12", [(1, (None, 12))]),
            ("Resolved #12", [(1, (None, 12))]),
            ("Closes: #12", [(1, (None, 12))]),
            ("Closes:#12", [(1, (None, 12))]),
            ("Closes#12", []),  # glued: neither colon nor whitespace separator
            ("Fixes acme-corp/Widgets#42", [(1, ("acme-corp/widgets", 42))]),
            ("random prose with no keyword", []),
            ("prefixes #12", []),  # the keyword is glued to "pre" — a word character
            ("_fixes #12", []),  # an underscore is a word character too
            ("Body:\nCloses #7\nmore text", [(2, (None, 7))]),
            ("  Closes #9", [(1, (None, 9))]),  # leading whitespace before line-start keyword
            ("some text. Closes #5", [(1, (None, 5))]),  # keyword after whitespace mid-line
            # Punctuation or markup right before the keyword still counts.
            ("see (fixes #12)", [(1, (None, 12))]),
            ("**Closes #12**", [(1, (None, 12))]),
            ("done;closes #12", [(1, (None, 12))]),
            # Issue and pull-request URLs are keyed by their owner/repo path.
            ("Closes https://github.com/o/r/issues/12", [(1, ("o/r", 12))]),
            ("Closes https://github.com/o/r/pull/12", [(1, ("o/r", 12))]),
            ("Closes https://github.com/o/r", []),  # no /issues/N or /pull/N path
        ]
        for text, want in cases:
            got = [(n, key) for n, _, key in find_refs(text)]
            if got != want:
                failures.append(f"find_refs({text!r}): got {got}, want {want}")
        # With the local repository named, a qualified self-reference or URL
        # keys as local; any other repository stays qualified.
        local_cases = [
            ("Closes O/R#4", [(1, (None, 4))]),
            ("Closes https://github.com/o/r/pull/4", [(1, (None, 4))]),
            ("Closes other/r#4", [(1, ("other/r", 4))]),
        ]
        for text, want in local_cases:
            got = [(n, key) for n, _, key in find_refs(text, "o/r")]
            if got != want:
                failures.append(f"find_refs({text!r}, 'o/r'): got {got}, want {want}")

        # 2) clean: commit's Closes # is in the allowed set -> OK.
        repo = tmp_path / "case_clean"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(repo, "feat: add widget\n\nCloses #12", {"a.txt": "2"})
        rc, out = _run_tool(repo, base, head, allow="12")
        check("clean-in-set", rc, out, OK, must_have=("ok",), must_not=("FAIL",))

        # 3) the #1121 case: a stray Closes # in an unrelated commit, not in
        # the allowed set -> FAIL, names the commit + the out-of-set number.
        repo = tmp_path / "case_stray"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(
            repo,
            "fix: retry constant\n\n(explaining the bug this closes)\nCloses #99",
            {"a.txt": "2"},
        )
        rc, out = _run_tool(repo, base, head, allow="12")
        check("stray-out-of-set", rc, out, FAIL, must_have=("FAIL", head[:7], "#99", "[#12]"))

        # 4) multiple commits, only one dirty -> FAIL exit 1, only the
        # offending line reported (the clean commit's own Closes # is silent).
        repo = tmp_path / "case_mixed"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        mid = _commit(repo, "feat: a\n\nCloses #1", {"a.txt": "2"})
        head = _commit(repo, "feat: b\n\nCloses #2", {"a.txt": "3"})
        rc, out = _run_tool(repo, base, head, allow="1")
        check("mixed-one-dirty", rc, out, FAIL, must_have=("FAIL", head[:7], "#2"), must_not=(mid[:7],))

        # 5) no closing keyword at all -> OK, zero references.
        repo = tmp_path / "case_none"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(repo, "docs: typo fix", {"a.txt": "2"})
        rc, out = _run_tool(repo, base, head, allow="1")
        check("no-keyword", rc, out, OK, must_have=("0 out-of-set",))

        # 6) empty range (base == head) -> OK, zero commits.
        repo = tmp_path / "case_empty_range"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        rc, out = _run_tool(repo, base, base, allow="1")
        check("empty-range", rc, out, OK, must_have=("0 commit(s) checked",))

        # 7) --pr-body defines the allowed set from the PR body's own closing
        # keywords, matching the #1121 remediation shape.
        repo = tmp_path / "case_pr_body"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(repo, "feat: land it\n\nCloses #12", {"a.txt": "2"})
        pr_body_path = tmp_path / "pr_body.txt"
        pr_body_path.write_text("This lands the feature.\n\nCloses #12\n")
        rc, out = _run_tool(repo, base, head, pr_body=pr_body_path)
        check("pr-body-allows", rc, out, OK, must_have=("ok",))

        # 8) --pr-body's own set does not cover a stray reference -> FAIL.
        repo = tmp_path / "case_pr_body_stray"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(repo, "fix: unrelated\n\nCloses #77", {"a.txt": "2"})
        pr_body_path2 = tmp_path / "pr_body2.txt"
        pr_body_path2.write_text("Closes #12\n")
        rc, out = _run_tool(repo, base, head, pr_body=pr_body_path2)
        check("pr-body-stray", rc, out, FAIL, must_have=("FAIL", "#77"))

        # 9) --allow and --pr-body union.
        repo = tmp_path / "case_union"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(repo, "feat: two refs\n\nCloses #5\nFixes #9", {"a.txt": "2"})
        pr_body_path3 = tmp_path / "pr_body3.txt"
        pr_body_path3.write_text("Fixes #9\n")
        rc, out = _run_tool(repo, base, head, allow="5", pr_body=pr_body_path3)
        check("union", rc, out, OK, must_have=("ok",))

        # 10) neither --allow nor --pr-body -> usage error, exit 2.
        rc, out = _run_tool(repo, base, head)
        check("no-allowed-set", rc, out, ERROR)

        # 11) ZERO_SHA base -> fail closed, exit 2.
        rc, out = _run_tool(repo, ZERO_SHA, head, allow="5,9")
        check("zero-sha-base", rc, out, ERROR, must_have=("all-zeros",))

        # 12) unresolvable base ref -> fail closed, exit 2.
        rc, out = _run_tool(repo, "not-a-real-ref", head, allow="5,9")
        check("unresolvable-base", rc, out, ERROR, must_have=("does not resolve",))

        # 13) not a git repo at all -> fail closed, exit 2.
        not_repo = tmp_path / "case_not_a_repo"
        not_repo.mkdir()
        rc, out = _run_tool(not_repo, "HEAD", "HEAD", allow="1")
        check("not-a-git-repo", rc, out, ERROR, must_have=("not a git repository",))

        # 14) missing --pr-body file -> fail closed, exit 2.
        rc, out = _run_tool(repo, base, head, pr_body=tmp_path / "does-not-exist.txt")
        check("pr-body-missing", rc, out, ERROR, must_have=("not found",))

        # 15) non-numeric --allow entry -> fail closed, exit 2.
        rc, out = _run_tool(repo, base, head, allow="5,abc")
        check("allow-non-numeric", rc, out, ERROR, must_have=("not N, #N, or owner/repo#N",))
        rc, out = _run_tool(repo, base, head, allow="x#5")
        check("allow-bad-qualifier", rc, out, ERROR, must_have=("not N, #N, or owner/repo#N",))
        rc, out = _run_tool(repo, base, head, allow="5,9", local="not-a-repo")
        check("repo-malformed", rc, out, ERROR, must_have=("--repo is not OWNER/REPO",))

        # 16) merge commit's own hand-edited message is scanned too (a
        # squash/merge is not exempt — the #1121 report describes exactly
        # this shape: "a copy-paste leftover in a squashed or amended
        # message").
        repo = tmp_path / "case_merge_message"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        _sh(repo, "checkout", "-b", "feature")
        _commit(repo, "feat: work", {"b.txt": "1"})
        _sh(repo, "checkout", "-")
        _sh(repo, "merge", "--no-ff", "feature", "-m", "Merge feature\n\nCloses #55")
        head = _sh(repo, "rev-parse", "HEAD")
        rc, out = _run_tool(repo, base, head, allow="1")
        check("merge-commit-scanned", rc, out, FAIL, must_have=("FAIL", "#55"))

        # 17) a keyword right after punctuation/markup is a real reference:
        # `(fixes #99)`, `**Closes #98**`, and `done;closes #97` all FAIL
        # against an allowed set that holds none of them.
        repo = tmp_path / "case_punct"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(repo, "fix: a (fixes #99)\n\n**Closes #98**\ndone;closes #97", {"a.txt": "2"})
        rc, out = _run_tool(repo, base, head, allow="12")
        check("punctuation-before-keyword", rc, out, FAIL, must_have=("#99", "#98", "#97"))

        # 18) the allowed set is keyed on (repo, N): a same-numbered reference
        # in ANOTHER repository — qualified or as an issue/PR URL — FAILs
        # against an unqualified allowed 12, and passes once allowed qualified.
        repo = tmp_path / "case_cross_repo"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"a.txt": "1"})
        head = _commit(
            repo,
            "feat: x\n\nCloses other/lib#12\nFixes https://github.com/other/lib/pull/12",
            {"a.txt": "2"},
        )
        rc, out = _run_tool(repo, base, head, allow="12")
        check("cross-repo-same-number", rc, out, FAIL, must_have=("other/lib#12",))
        rc, out = _run_tool(repo, base, head, allow="#12,Other/Lib#12")
        check("cross-repo-allowed-qualified", rc, out, OK, must_have=("ok",))

        # 19) --repo names the local repository: a qualified self-reference
        # and an issue URL to it key as local, so an unqualified allowed 12
        # covers them; a --pr-body URL reference to it allows `#12` too.
        head = _commit(
            repo,
            "feat: y\n\nCloses acme/app#12\nCloses https://github.com/acme/app/issues/12",
            {"a.txt": "3"},
        )
        rc, out = _run_tool(repo, base, head, allow="12", local="Acme/App")
        check("local-repo-qualified", rc, out, FAIL, must_have=("other/lib#12",), must_not=("acme/app#12",))
        mid = _sh(repo, "rev-parse", "HEAD~1")
        rc, out = _run_tool(repo, mid, head, allow="12", local="acme/app")
        check("local-repo-only", rc, out, OK, must_have=("ok",))
        rc, out = _run_tool(repo, mid, head, allow="12")
        check("local-repo-unnamed", rc, out, FAIL, must_have=("acme/app#12",))
        pr_url = tmp_path / "pr_url.txt"
        pr_url.write_text("Closes https://github.com/acme/app/pull/12\n")
        rc, out = _run_tool(repo, mid, head, pr_body=pr_url, local="acme/app")
        check("pr-body-url-local", rc, out, OK, must_have=("ok",))

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELFTEST OK: 26/26 cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
