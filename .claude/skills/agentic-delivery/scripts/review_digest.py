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
  2. a FLAGGED section naming every changed path that matches a test, CI,
     dependency/lockfile, build, ownership, or budget pattern — the paths most
     likely to change reviewer-relevant behavior invisibly (a test loosened, a
     workflow permission widened, a dependency bumped, a budget raised);
  3. files changed, grouped by directory, each with +/-line counts;
  4. every commit in `since..head`, subject only, oldest first.
Diffs run with `--no-renames`, so a renamed file is listed under BOTH its old
and its new path and either one can trip the flag (a test moved out of
`tests/` is still flagged by its old path).
`--paths` scopes the whole digest (steps 1-3) to the given pathspecs, same as
`git diff -- <paths>`; commits (step 4) are not path-filtered, since "what
commits landed" is itself part of the digest.

`--since` must be an ancestor of `--head`. If it is not (a rebase or force-push
rewrote the history the reviewer saw), `since..head` would silently mix in
changes the reviewer never approved or drop ones they did, so the script exits
2 and names the merge-base to re-run from. `--allow-diverged` prints the
digest anyway, with a WARN line as the very first line of output.

`--max-lines N` caps the TOTAL output at N lines, the truncation notice
included. The header, the diff-stat line, any WARN line, and the whole FLAGGED
section are never truncated; commit rows are cut first, then directory rows,
and the final line says how many of each were hidden. A cap too small to hold
the never-truncated lines (plus the notice, when anything must be cut) exits 1
and names the minimum.

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
  1  usage error: a bad or missing flag, or a `--max-lines` too small to hold
     the never-truncated lines (unusable request)
  2  `--since` or `--head` does not resolve to a commit, or `--since` is not an
     ancestor of `--head` without `--allow-diverged` (fails closed rather than
     printing a digest that could be read as "nothing changed")

USAGE
-----
  review_digest.py --since SHA [--head REF] [--paths PATH ...] [--max-lines N]
                   [--allow-diverged]
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
# test surfaces, CI/workflow config, dependency manifests and lockfiles,
# build config, ownership rules, and budgets — the classes most likely to
# change behavior a diff-stat alone would hide.
_FLAG_PATTERNS = [
    # Test surfaces.
    re.compile(r"(^|/)(tests?|__tests__|spec)/"),
    re.compile(r"(^|/)test_[^/]+\.py$"),
    re.compile(r"[^/]+_test\.(py|go)$"),
    re.compile(r"\.(test|spec)\.[jt]sx?$"),
    re.compile(r"(^|/)(conftest\.py|pytest\.ini|tox\.ini)$"),
    re.compile(r"(^|/)(jest|vitest)\.config[^/]*$"),
    re.compile(r"(^|/)scripts/test-[^/]+$"),
    # CI and workflow config.
    re.compile(r"^\.github/(workflows|actions)/"),
    re.compile(r"(^|/)action\.ya?ml$"),
    re.compile(r"^\.circleci/"),
    re.compile(r"(^|/)azure-pipelines[^/]*$"),
    re.compile(r"(^|/)\.travis\.yml$"),
    re.compile(r"(^|/)\.gitlab-ci\.ya?ml$"),
    re.compile(r"(^|/)Jenkinsfile$"),
    re.compile(r"(^|/)CODEOWNERS$"),
    # Dependency manifests, lockfiles, and build config.
    re.compile(r"(^|/)(package(-lock)?\.json|yarn\.lock|pnpm-lock\.ya?ml|"
               r"pyproject\.toml|requirements[^/]*\.txt|poetry\.lock|uv\.lock|"
               r"Gemfile(\.lock)?|Cargo\.(toml|lock)|go\.(mod|sum)|Dockerfile[^/]*|"
               r"setup\.(py|cfg)|Makefile|tsconfig[^/]*\.json|"
               r"\.pre-commit-config\.ya?ml)$"),
    # Budgets (size, token, spend, ...): any file whose name mentions one.
    re.compile(r"(^|/)[^/]*budget[^/]*$", re.IGNORECASE),
]


class DigestError(RuntimeError):
    """Raised for a condition that must exit 2 (unresolvable ref, or a diverged --since)."""


def _run_git(args, cwd=None):
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
    return proc.returncode, proc.stdout, proc.stderr


def _resolve(ref: str, cwd=None) -> str:
    code, out, _err = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"], cwd)
    if code != 0 or not out.strip():
        raise DigestError(f"cannot resolve {ref!r} to a commit")
    return out.strip()


def _is_flagged(path: str) -> bool:
    """True iff `path` matches a test/CI/dependency/build/ownership/budget pattern."""
    return any(p.search(path) for p in _FLAG_PATTERNS)


def _ancestry(since: str, head: str, cwd=None):
    """Return None if `since` is an ancestor of `head`, else the merge-base sha (or "none")."""
    code, _out, err = _run_git(["merge-base", "--is-ancestor", since, head], cwd)
    if code == 0:
        return None
    if code != 1:
        raise DigestError(f"git merge-base --is-ancestor failed: {err.strip()}")
    code, out, _err = _run_git(["merge-base", since, head], cwd)
    return out.strip() if code == 0 and out.strip() else "none"


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
    # -z: raw, unquoted paths, so a non-ASCII name cannot dodge a flag pattern.
    args = ["diff", "--numstat", "--no-renames", "-z", f"{since}..{head}"]
    if paths:
        args += ["--", *paths]
    code, out, err = _run_git(args, cwd)
    if code != 0:
        raise DigestError(f"git diff --numstat {since}..{head} failed: {err.strip()}")
    rows = []
    for line in out.split("\0"):
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
    args = ["diff", "--shortstat", "--no-renames", f"{since}..{head}"]
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


def build_digest(since: str, head: str = "HEAD", paths=None, max_lines=None, cwd=None,
                 allow_diverged: bool = False) -> str:
    """Return the rendered digest text.

    Raises DigestError on an unresolvable ref or a `since` that is not an
    ancestor of `head` (unless `allow_diverged`, which prepends a WARN line),
    and ValueError when `max_lines` cannot hold the never-truncated lines.
    """
    since_sha = _resolve(since, cwd)
    head_sha = _resolve(head, cwd)

    fixed = []
    merge_base = _ancestry(since_sha, head_sha, cwd)
    if merge_base is not None:
        detail = (f"--since {since_sha[:12]} is not an ancestor of head {head_sha[:12]} "
                  f"(merge-base {merge_base[:12]}); history was rewritten since the last pass")
        if not allow_diverged:
            raise DigestError(f"{detail}; re-run with --since {merge_base[:12]}, "
                              "or pass --allow-diverged to diff the endpoints anyway")
        fixed.append(f"WARN: {detail}; this digest diffs the two endpoints and may include "
                     "changes the reviewer never saw or omit ones they did")

    fixed.append(f"REVIEW DIGEST since {since_sha[:12]} (head {head_sha[:12]})")
    fixed.append(f"Diff stat: {_shortstat(since_sha, head_sha, paths, cwd)}")

    commits = _commits(since_sha, head_sha, cwd)
    rows = _numstat(since_sha, head_sha, paths, cwd)
    flagged = [path for _a, _d, path in rows if _is_flagged(path)]
    grouped = _group_by_directory(rows)

    fixed.append(f"Flagged tests/CI/config ({len(flagged)}):")
    fixed.extend(f"  {path}" for path in flagged)

    dir_block = [f"Changed by directory ({len(grouped)}):"]
    for directory, added, deleted, files, has_binary in grouped:
        suffix = " (includes binary)" if has_binary else ""
        plural = "file" if files == 1 else "files"
        dir_block.append(f"  {directory}  +{added}/-{deleted} ({files} {plural}){suffix}")
    commit_block = [f"Commits ({len(commits)}):"]
    commit_block.extend(f"  {sha} {subject}" for sha, subject in commits)

    if max_lines is None or len(fixed) + len(dir_block) + len(commit_block) <= max_lines:
        return "\n".join([*fixed, *dir_block, *commit_block])

    # Something must be cut: the notice line itself counts toward the cap.
    avail = max_lines - len(fixed) - 1
    if avail < 0:
        raise ValueError(f"--max-lines {max_lines} cannot hold the header, diff stat, and "
                         f"{len(flagged)} flagged path(s) plus a truncation notice; "
                         f"need at least {len(fixed) + 1}")
    shown_dirs = dir_block[:avail]
    shown_commits = commit_block[:max(avail - len(shown_dirs), 0)]
    hidden_dir_rows = len(grouped) - max(len(shown_dirs) - 1, 0)
    hidden_commit_rows = len(commits) - max(len(shown_commits) - 1, 0)
    notice = (f"... truncated to --max-lines {max_lines}: {hidden_commit_rows} of {len(commits)} "
              f"commit(s) and {hidden_dir_rows} of {len(grouped)} directory row(s) hidden; "
              "raise --max-lines to see them (--paths narrows directory rows, not commits)")
    return "\n".join([*fixed, *shown_dirs, *shown_commits, notice])


class _Parser(argparse.ArgumentParser):
    """ArgumentParser whose usage errors exit USAGE_ERROR (1), never the fail-closed 2."""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"REVIEW_DIGEST ERROR: {message}", file=sys.stderr)
        sys.exit(USAGE_ERROR)


def main(argv=None) -> int:
    parser = _Parser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", help="the reviewer's last-seen sha or ref")
    parser.add_argument("--head", default="HEAD", help="current head ref (default HEAD)")
    parser.add_argument("--paths", nargs="*", default=None, help="scope the digest to these pathspecs")
    parser.add_argument("--max-lines", type=int, default=None,
                        help="cap the whole digest at N lines; flagged paths are never cut")
    parser.add_argument("--allow-diverged", action="store_true",
                        help="digest even if --since is not an ancestor of --head (prints a WARN first)")
    parser.add_argument("--cwd", default=None, help="run git in this directory (default: current directory)")
    parser.add_argument("--selftest", action="store_true", help="build a throwaway repo and prove the digest, offline")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.since:
        parser.error("--since is required (or use --selftest)")

    try:
        digest = build_digest(args.since, args.head, args.paths, args.max_lines, args.cwd,
                              allow_diverged=args.allow_diverged)
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

        # Renames: --no-renames lists both paths, so either one can trip the flag.
        os.makedirs(os.path.join(repo, "lib"))
        with open(os.path.join(repo, "tests", "fixture_data.py"), "w") as fh:
            fh.write("DATA = 1\n" * 5)
        with open(os.path.join(repo, "src", "helper.py"), "w") as fh:
            fh.write("def helper():\n    return 1\n" * 3)
        git(["add", "."])
        git([*commit_args, "commit", "-q", "-m", "pre-rename"])
        rename_base = git(["rev-parse", "HEAD"]).strip()
        git(["mv", "tests/fixture_data.py", "lib/fixture_data.py"])
        git(["mv", "src/helper.py", "tests/helper.py"])
        non_ascii = "tests/münchen_case.py"  # git quotes this path without -z
        with open(os.path.join(repo, non_ascii), "w") as fh:
            fh.write("x = 1\n")
        git(["add", "."])
        git([*commit_args, "commit", "-q", "-m", "renames"])
        rename_head = git(["rev-parse", "HEAD"]).strip()
        renamed = build_digest(rename_base, rename_head, cwd=repo)
        flagged_lines = renamed.split("Flagged")[1].split("Changed by directory")[0].splitlines()
        expect("rename-out-of-tests-flags-old-path", "  tests/fixture_data.py" in flagged_lines, renamed)
        expect("rename-into-tests-flags-new-path", "  tests/helper.py" in flagged_lines, renamed)
        expect("no-rename-arrows", "=>" not in renamed, renamed)
        expect("non-ascii-path-flagged-unquoted", f"  {non_ascii}" in flagged_lines, renamed)

        # --max-lines: flagged first and never cut, commits cut first, and the
        # notice line counts toward the cap.
        trunc_base = rename_head
        for i in range(6):
            os.makedirs(os.path.join(repo, f"d{i}"))
            with open(os.path.join(repo, f"d{i}", "f.txt"), "w") as fh:
                fh.write(f"{i}\n")
            if i == 5:
                with open(os.path.join(repo, "tests", "test_bulk.py"), "w") as fh:
                    fh.write("def test_bulk(): assert True\n")
                with open(os.path.join(repo, ".github", "workflows", "bulk.yml"), "w") as fh:
                    fh.write("name: bulk\n")
            git(["add", "."])
            git([*commit_args, "commit", "-q", "-m", f"bulk {i}"])
        trunc_head = git(["rev-parse", "HEAD"]).strip()
        full_lines = build_digest(trunc_base, trunc_head, cwd=repo).splitlines()
        expect("flagged-section-right-after-stat", full_lines[2].startswith("Flagged"), full_lines)
        cap = len(full_lines) - 3
        capped = build_digest(trunc_base, trunc_head, max_lines=cap, cwd=repo)
        lines = capped.splitlines()
        expect("max-lines-total-includes-notice", len(lines) <= cap, f"{len(lines)} > {cap}: {capped}")
        expect("max-lines-keeps-header", lines[0].startswith("REVIEW DIGEST"), capped)
        expect("max-lines-keeps-stat", lines[1].startswith("Diff stat:"), capped)
        expect("max-lines-keeps-all-flagged", "  tests/test_bulk.py" in lines
               and "  .github/workflows/bulk.yml" in lines, capped)
        expect("max-lines-cuts-commits-first", "  d5  +1/-0 (1 file)" in lines and "bulk 5" not in capped, capped)
        expect("max-lines-notice-counts", lines[-1].startswith("... truncated")
               and "4 of 6 commit(s)" in lines[-1] and "0 of 8 directory row(s)" in lines[-1], capped)
        try:
            build_digest(trunc_base, trunc_head, max_lines=5, cwd=repo)
            failures.append("max-lines-below-flagged-did-not-raise")
        except ValueError as exc:
            if "need at least 6" not in str(exc):
                failures.append(f"max-lines-below-flagged-names-minimum: {exc}")
        total[0] += 1

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

        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--since", since_sha, "--no-such-flag"],
            capture_output=True, text=True,
        )
        expect("main-usage-error-exit-1-not-2", proc.returncode == USAGE_ERROR, proc.stderr)

        # A --since that is not an ancestor of head fails closed, naming the merge-base.
        git(["checkout", "-q", "-b", "side", since_sha])
        with open(os.path.join(repo, "side.txt"), "w") as fh:
            fh.write("rewritten history\n")
        git(["add", "."])
        git([*commit_args, "commit", "-q", "-m", "side commit"])
        side_sha = git(["rev-parse", "HEAD"]).strip()
        git(["checkout", "-q", "main"])
        try:
            build_digest(side_sha, head_sha, cwd=repo)
            failures.append("diverged-since-did-not-raise")
        except DigestError as exc:
            if since_sha[:12] not in str(exc) or "merge-base" not in str(exc):
                failures.append(f"diverged-error-names-merge-base: {exc}")
        total[0] += 1
        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--since", side_sha, "--head", head_sha, "--cwd", repo],
            capture_output=True, text=True,
        )
        expect("main-exit-2-on-diverged", proc.returncode == UNRESOLVABLE and since_sha[:12] in proc.stderr,
               f"{proc.returncode} {proc.stderr}")
        warned = build_digest(side_sha, head_sha, cwd=repo, allow_diverged=True)
        expect("allow-diverged-warns-first", warned.splitlines()[0].startswith("WARN:")
               and since_sha[:12] in warned.splitlines()[0], warned)

        # Every widened flag pattern fires; near-miss paths do not.
        must_flag = [
            ".github/actions/setup/action.yml", "tools/action.yaml", ".circleci/config.yml",
            "azure-pipelines.yml", ".travis.yml", "web/__tests__/app.js", "spec/models/user_spec.rb",
            "pkg/server_test.go", "lib/util_test.py", "test_util.py", "conftest.py", "pytest.ini",
            "tox.ini", "jest.config.js", "vitest.config.ts", "package-lock.json", "yarn.lock",
            "pnpm-lock.yaml", "poetry.lock", "uv.lock", "Gemfile.lock", "Cargo.lock", "go.sum",
            "CODEOWNERS", ".github/CODEOWNERS", "Makefile", "Dockerfile", "docker/Dockerfile.dev",
            "scripts/test-ci-gates.sh", "scripts/size-budgets.tsv", "config/token_budget.json",
            "tests/fixtures/data.json", ".github/workflows/ci.yml",
        ]
        missed = [path for path in must_flag if not _is_flagged(path)]
        expect("widened-patterns-flag", not missed, f"not flagged: {missed}")
        must_not_flag = ["src/app.py", "docs/readme.md", "src/contest.py", "spectrum/color.py",
                         "latest.py", "src/attestation.go", "scripts/deploy.sh", "github/workflows.md"]
        wrong = [path for path in must_not_flag if _is_flagged(path)]
        expect("near-misses-not-flagged", not wrong, f"wrongly flagged: {wrong}")
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
