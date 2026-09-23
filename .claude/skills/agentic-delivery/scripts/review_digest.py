#!/usr/bin/env python3
"""review_digest.py — a returning reviewer's change digest, not a full re-read.

WHY THIS EXISTS (the failure it closes, #1080)
-----------------------------------------------
The same reviewer — human or agent — returning to a surface a second time
defaults to re-examining the whole tree from scratch, re-deriving what
changed by comparing current state against memory of the last pass. That is
slow and error-prone: a real change can be missed among unchanged
surroundings (a false negative), or something already reviewed and unchanged
gets re-flagged (a false positive). This script renders the digest from git's
own diff between the reviewer's last-seen sha and the current head, so the
reviewer's attention goes to what moved — anything not listed is implicitly
unchanged since it was last approved.

THE RULE
--------
Given `--since SHA` (the reviewer's last-recorded pass) and `--head REF`
(default `HEAD`), print, in order:
  1. the diff stat summary (files/insertions/deletions) for `since..head`;
  2. every commit in `since..head`, subject only, oldest first;
  3. files changed, grouped by directory, each with +/-line counts;
  4. a FLAGGED section naming any changed path that matches a test, CI, or
     config pattern — the paths most likely to change reviewer-relevant
     behavior invisibly (a test loosened, a workflow permission widened, a
     dependency bumped).
`--paths` scopes the whole digest (steps 1, 3, 4) to the given pathspecs,
same as `git diff -- <paths>`; commits (step 2) are not path-filtered, since
"what commits landed" is itself part of the digest.

`--max-lines N` caps the body (commits + directory rows + flagged rows) at N
lines total; the header and diff-stat line are never truncated, since the
diff-stat needs no scoping and is the single most load-bearing number here.
When the cap trims content, the final line names how much was cut and how to
see the rest (a narrower `--paths`, or a wider `--max-lines`).

HONESTY
-------
This digest reports WHAT changed, in git's own terms (file paths, line
counts, commit subjects); it does not judge WHETHER any change is
correct, safe, or already covered — that is the reviewer's job on the
flagged hunks, not this script's. A path that is not test/CI/config-shaped
but still carries a behavior change is not flagged; the directory rows list
every changed file so nothing is silently hidden, only de-prioritized.

EXIT CODES (fail closed)
-------------------------
  0  digest printed
  1  `--max-lines` was too small to hold even the header (unusable request)
  2  `--since` or `--head` does not resolve to a commit (fails closed rather
     than printing a partial or empty digest that could be read as "nothing
     changed")

USAGE
-----
  review_digest.py --since SHA [--head REF] [--paths PATH ...] [--max-lines N]
  review_digest.py --selftest
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

OK, USAGE_ERROR, UNRESOLVABLE = 0, 1, 2

# Path patterns whose change is flagged regardless of directory grouping:
# test surfaces, CI/workflow config, and dependency/build config — the
# classes most likely to change behavior a diff-stat alone would hide.
_FLAG_PATTERNS = [
    re.compile(r"(^|/)tests?/"),
    re.compile(r"(^|/)test_[^/]+\.py$"),
    re.compile(r"[^/]+_test\.py$"),
    re.compile(r"\.(test|spec)\.[jt]sx?$"),
    re.compile(r"^\.github/workflows/"),
    re.compile(r"(^|/)\.gitlab-ci\.ya?ml$"),
    re.compile(r"(^|/)Jenkinsfile$"),
    re.compile(r"(^|/)(package(-lock)?\.json|pyproject\.toml|requirements[^/]*\.txt|"
               r"Cargo\.(toml|lock)|go\.(mod|sum)|Dockerfile[^/]*|"
               r"setup\.(py|cfg)|Makefile|tsconfig[^/]*\.json|"
               r"\.pre-commit-config\.ya?ml)$"),
]


class DigestError(RuntimeError):
    """Raised for a condition that must exit 2 (unresolvable ref)."""


def _run_git(args, cwd=None):
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
    return proc.returncode, proc.stdout, proc.stderr


def _resolve(ref: str, cwd=None) -> str:
    code, out, _err = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"], cwd)
    if code != 0 or not out.strip():
        raise DigestError(f"cannot resolve {ref!r} to a commit")
    return out.strip()


def _is_flagged(path: str) -> bool:
    return any(p.search(path) for p in _FLAG_PATTERNS)


def _commits(since: str, head: str, cwd=None):
    code, out, err = _run_git(["log", "--format=%h%x09%s", "--reverse", f"{since}..{head}", "--"], cwd)
    if code != 0:
        raise DigestError(f"git log {since}..{head} failed: {err.strip()}")
    commits = []
    for line in out.splitlines():
        if not line:
            continue
        sha, _sep, subject = line.partition("\t")
        commits.append((sha, subject))
    return commits


def _numstat(since: str, head: str, paths, cwd=None):
    args = ["diff", "--numstat", f"{since}..{head}"]
    if paths:
        args += ["--", *paths]
    code, out, err = _run_git(args, cwd)
    if code != 0:
        raise DigestError(f"git diff --numstat {since}..{head} failed: {err.strip()}")
    rows = []
    for line in out.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_s, deleted_s, path = parts
        added = None if added_s == "-" else int(added_s)
        deleted = None if deleted_s == "-" else int(deleted_s)
        rows.append((added, deleted, path))
    return rows


def _shortstat(since: str, head: str, paths, cwd=None) -> str:
    args = ["diff", "--shortstat", f"{since}..{head}"]
    if paths:
        args += ["--", *paths]
    code, out, err = _run_git(args, cwd)
    if code != 0:
        raise DigestError(f"git diff --shortstat {since}..{head} failed: {err.strip()}")
    text = out.strip()
    return text if text else "0 files changed"


def _group_by_directory(rows):
    """rows: (added, deleted, path) -> {directory: (added_total, deleted_total, file_count)}, insertion order."""
    groups = {}
    order = []
    for added, deleted, path in rows:
        directory = os.path.dirname(path) or "."
        if directory not in groups:
            groups[directory] = [0, 0, 0, False]  # added, deleted, files, has_binary
            order.append(directory)
        entry = groups[directory]
        if added is None or deleted is None:
            entry[3] = True
        else:
            entry[0] += added
            entry[1] += deleted
        entry[2] += 1
    return [(d, *groups[d]) for d in order]


def build_digest(since: str, head: str = "HEAD", paths=None, max_lines=None, cwd=None) -> str:
    """Return the rendered digest text; raises DigestError on an unresolvable ref."""
    since_sha = _resolve(since, cwd)
    head_sha = _resolve(head, cwd)

    header = f"REVIEW DIGEST since {since_sha[:12]} (head {head_sha[:12]})"
    stat_line = f"Diff stat: {_shortstat(since_sha, head_sha, paths, cwd)}"

    commits = _commits(since_sha, head_sha, cwd)
    rows = _numstat(since_sha, head_sha, paths, cwd)
    flagged = [path for _a, _d, path in rows if _is_flagged(path)]
    grouped = _group_by_directory(rows)

    body = [f"Commits ({len(commits)}):"]
    for sha, subject in commits:
        body.append(f"  {sha} {subject}")

    body.append(f"Changed by directory ({len(grouped)}):")
    for directory, added, deleted, files, has_binary in grouped:
        suffix = " (includes binary)" if has_binary else ""
        plural = "file" if files == 1 else "files"
        body.append(f"  {directory}  +{added}/-{deleted} ({files} {plural}){suffix}")

    body.append(f"Flagged tests/CI/config ({len(flagged)}):")
    for path in flagged:
        body.append(f"  {path}")

    if max_lines is not None:
        fixed_lines = 2  # header + stat_line
        budget = max_lines - fixed_lines
        if budget < 1:
            raise ValueError("max_lines too small to hold the header and diff stat")
        if len(body) > budget:
            cut = len(body) - budget
            body = body[:budget] + [
                f"... {cut} more line(s) truncated (--max-lines {max_lines}); "
                "narrow --paths or raise --max-lines to see the rest"
            ]

    return "\n".join([header, stat_line, *body])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", help="the reviewer's last-seen sha or ref")
    parser.add_argument("--head", default="HEAD", help="current head ref (default HEAD)")
    parser.add_argument("--paths", nargs="*", default=None, help="scope the digest to these pathspecs")
    parser.add_argument("--max-lines", type=int, default=None, help="cap the digest body at N lines total")
    parser.add_argument("--cwd", default=None, help="run git in this directory (default: current directory)")
    parser.add_argument("--selftest", action="store_true", help="build a throwaway repo and prove the digest, offline")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.since:
        parser.error("--since is required (or use --selftest)")

    try:
        digest = build_digest(args.since, args.head, args.paths, args.max_lines, args.cwd)
    except DigestError as exc:
        print(f"REVIEW_DIGEST ERROR: {exc}", file=sys.stderr)
        return UNRESOLVABLE
    except ValueError as exc:
        print(f"REVIEW_DIGEST ERROR: {exc}", file=sys.stderr)
        return USAGE_ERROR

    print(digest)
    return OK


def _selftest() -> int:
    import shutil
    import tempfile

    failures = []
    total = [0]

    def expect(label, cond, detail=""):
        total[0] += 1
        if not cond:
            failures.append(f"{label}: {detail}")

    tmp = tempfile.mkdtemp(prefix="review_digest_selftest_")
    try:
        repo = os.path.join(tmp, "repo")
        os.makedirs(repo)
        commit_args = ["-c", "user.name=Test", "-c", "user.email=test@example.com",
                       "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull]

        def git(args):
            code, out, err = _run_git(args, repo)
            if code != 0:
                raise RuntimeError(f"setup git {args} failed: {err}")
            return out

        git(["init", "-q"])
        git(["symbolic-ref", "HEAD", "refs/heads/main"])
        os.makedirs(os.path.join(repo, "src"))
        with open(os.path.join(repo, "src", "a.py"), "w") as fh:
            fh.write("x = 1\n")
        git(["add", "."])
        git([*commit_args, "commit", "-q", "-m", "base"])
        since_sha = git(["rev-parse", "HEAD"]).strip()

        # A normal source change.
        with open(os.path.join(repo, "src", "a.py"), "a") as fh:
            fh.write("y = 2\n")
        git(["add", "."])
        git([*commit_args, "commit", "-q", "-m", "add y"])

        # A test-surface change and a CI-surface change, each their own commit.
        os.makedirs(os.path.join(repo, "tests"))
        with open(os.path.join(repo, "tests", "test_a.py"), "w") as fh:
            fh.write("def test_x(): assert True\n")
        git(["add", "."])
        git([*commit_args, "commit", "-q", "-m", "add test"])

        os.makedirs(os.path.join(repo, ".github", "workflows"))
        with open(os.path.join(repo, ".github", "workflows", "ci.yml"), "w") as fh:
            fh.write("name: ci\n")
        git(["add", "."])
        git([*commit_args, "commit", "-q", "-m", "add ci workflow"])
        head_sha = git(["rev-parse", "HEAD"]).strip()

        digest = build_digest(since_sha, head_sha, cwd=repo)
        expect("header-names-both-shas", since_sha[:12] in digest and head_sha[:12] in digest, digest)
        expect("three-commits-listed", digest.count("add y") == 1 and digest.count("add test") == 1
               and digest.count("add ci workflow") == 1, digest)
        expect("src-dir-grouped", "src  +1/-0 (1 file)" in digest, digest)
        expect("tests-flagged", "tests/test_a.py" in digest.split("Flagged")[1], digest)
        expect("ci-flagged", ".github/workflows/ci.yml" in digest.split("Flagged")[1], digest)
        expect("diff-stat-present", "Diff stat:" in digest, digest)

        # --paths scopes numstat/flagged/stat but not the commit list.
        scoped = build_digest(since_sha, head_sha, paths=["src"], cwd=repo)
        expect("paths-scopes-out-tests", "tests/test_a.py" not in scoped, scoped)
        expect("paths-still-lists-all-commits", scoped.count("add test") == 1, scoped)

        # --max-lines truncates the body and says so, but keeps header + stat.
        capped = build_digest(since_sha, head_sha, max_lines=4, cwd=repo)
        expect("max-lines-keeps-header", capped.splitlines()[0].startswith("REVIEW DIGEST"), capped)
        expect("max-lines-keeps-stat", capped.splitlines()[1].startswith("Diff stat:"), capped)
        expect("max-lines-notes-truncation", "truncated" in capped, capped)

        # Unresolvable since/head both fail closed with exit 2.
        try:
            build_digest("0" * 40, head_sha, cwd=repo)
            failures.append("unresolvable-since-did-not-raise")
        except DigestError:
            pass
        total[0] += 1
        try:
            build_digest(since_sha, "no-such-ref", cwd=repo)
            failures.append("unresolvable-head-did-not-raise")
        except DigestError:
            pass
        total[0] += 1

        # No commits at all (since == head) still renders a valid, empty digest.
        empty = build_digest(head_sha, head_sha, cwd=repo)
        expect("no-op-range-zero-commits", "Commits (0):" in empty, empty)

        # main() exit codes end to end.
        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--since", "0" * 40, "--head", head_sha, "--cwd", repo],
            capture_output=True, text=True,
        )
        expect("main-exit-2-on-unresolvable", proc.returncode == UNRESOLVABLE, proc.stderr)

        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--since", since_sha, "--head", head_sha,
             "--max-lines", "1", "--cwd", repo],
            capture_output=True, text=True,
        )
        expect("main-exit-1-on-too-small-max-lines", proc.returncode == USAGE_ERROR, proc.stderr)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = total[0] - len(failures)
    if failures:
        print(f"SELFTEST FAILED ({passed}/{total[0]}):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"SELFTEST OK: {passed}/{total[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
