#!/usr/bin/env python3
"""Lane-start isolation guard: refuse unless this lane really is isolated.

Run as the FIRST step of every write-lane, from the lane's working directory:

    python3 .claude/skills/agentic-delivery/scripts/lane_guard.py [--expect-branch NAME]

Exit 0 (one `LANE_GUARD OK:` line) only when ALL hold:
  1. git answers a plain read in the cwd (a PATH shim or sandbox that blocks
     git fails it). A tool-call hook never sees this subprocess, so chain the
     lane's own direct read first: `git rev-parse HEAD && python3 lane_guard.py`.
  2. The cwd is a LINKED worktree: `git rev-parse --git-dir` differs from
     `--git-common-dir`. Equal means the main checkout (a shared tree), which
     is exactly the escape this guard exists to catch.
  3. HEAD is on a named branch (not detached) that is not the default branch.
  4. With --expect-branch, HEAD's branch equals it exactly.

Otherwise exit 1 with exactly one `LANE_GUARD REFUSE: <reason>` line on stdout,
written to be quoted verbatim in the lane's handback. The lane stops at that
point; it never retries the refused step through another path.

DEFAULT BRANCH. Taken from --default-branch when given; else from the remote
HEAD (`git symbolic-ref refs/remotes/origin/HEAD`); else, when neither is
known, BOTH `main` and `master` count as default (fail closed rather than
guess which one this repo uses).

ENVIRONMENT. GIT_DIR, GIT_WORK_TREE, GIT_COMMON_DIR and GIT_INDEX_FILE are
removed from every git call's environment, so an inherited variable (for
example from a git hook) cannot point the check at a different repository than
the cwd. Read-only: the guard never writes to the repository.

    lane_guard.py --selftest    builds throwaway repos and proves every
                                refusal fires (and that the OK case passes).
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

OK = 0
REFUSED = 1
_STRIPPED_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")
_FALLBACK_DEFAULTS = ("main", "master")


def _git(args, cwd, git="git"):
    """Run one read-only git command; return (returncode, stripped stdout).

    A missing binary or an OS-level refusal returns code 127 instead of raising,
    so the caller turns it into a refusal line rather than a traceback.
    """
    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    try:
        proc = subprocess.run(
            [git, *args], cwd=cwd, env=env, capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return 127, ""
    return proc.returncode, proc.stdout.strip()


def _default_branches(cwd, explicit, git):
    """Return the set of branch names treated as default (see module docstring)."""
    if explicit:
        return {explicit}
    code, ref = _git(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd, git)
    prefix = "refs/remotes/origin/"
    if code == 0 and ref.startswith(prefix) and len(ref) > len(prefix):
        return {ref[len(prefix):]}
    return set(_FALLBACK_DEFAULTS)


def check(cwd, expect_branch=None, default_branch=None, git="git"):
    """Evaluate the lane at `cwd`; return (exit_code, one-line message).

    Side-effect free: runs read-only git commands only.
    """
    code, top = _git(["rev-parse", "--show-toplevel"], cwd, git)
    if code != 0 or not top:
        return REFUSED, (
            f"LANE_GUARD REFUSE: git read failed in {cwd} (exit {code}); "
            "stop and hand back, do not retry git another way"
        )
    code_d, git_dir = _git(["rev-parse", "--git-dir"], top, git)
    code_c, common_dir = _git(["rev-parse", "--git-common-dir"], top, git)
    if code_d != 0 or code_c != 0 or not git_dir or not common_dir:
        return REFUSED, f"LANE_GUARD REFUSE: cannot resolve git dirs in {top}"
    real_git_dir = os.path.realpath(os.path.join(top, git_dir))
    real_common = os.path.realpath(os.path.join(top, common_dir))
    if real_git_dir == real_common:
        return REFUSED, (
            f"LANE_GUARD REFUSE: {top} is the main checkout, not a linked worktree "
            "(git-dir == git-common-dir)"
        )
    code, branch = _git(["symbolic-ref", "--quiet", "--short", "HEAD"], top, git)
    if code != 0 or not branch:
        return REFUSED, f"LANE_GUARD REFUSE: HEAD is detached in {top}; a write-lane needs its own branch"
    defaults = _default_branches(top, default_branch, git)
    if branch in defaults:
        return REFUSED, f"LANE_GUARD REFUSE: HEAD is on default branch '{branch}' in {top}"
    if expect_branch is not None and branch != expect_branch:
        return REFUSED, f"LANE_GUARD REFUSE: HEAD is on '{branch}', expected '{expect_branch}' in {top}"
    return OK, f"LANE_GUARD OK: linked worktree {top} on branch '{branch}'"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--expect-branch", help="refuse unless HEAD is on exactly this branch")
    parser.add_argument("--default-branch", help="default branch name (else origin/HEAD, else main+master)")
    parser.add_argument("--selftest", action="store_true", help="prove every refusal fires")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    code, line = check(os.getcwd(), args.expect_branch, args.default_branch)
    print(line)
    return code


def _selftest():
    """Build throwaway repos and assert each planted case refuses (or passes)."""
    failures = []
    total = [0]

    def expect(label, result, want_code, want_text):
        total[0] += 1
        code, line = result
        if code != want_code or want_text not in line or "\n" in line:
            failures.append(f"{label}: got ({code}) {line!r}")

    tmp = os.path.realpath(tempfile.mkdtemp(prefix="lane_guard_selftest_"))
    # Stop repository discovery at tmp, so "not a repo" holds even when the
    # temp dir itself sits inside some checkout.
    saved_ceiling = os.environ.get("GIT_CEILING_DIRECTORIES")
    os.environ["GIT_CEILING_DIRECTORIES"] = tmp
    try:
        repo = os.path.join(tmp, "repo")
        os.makedirs(repo)
        for args in (
            ["init", "-q"],
            ["symbolic-ref", "HEAD", "refs/heads/main"],
            ["-c", "user.name=Test", "-c", "user.email=test@example.com",
             "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
             "commit", "-q", "--allow-empty", "-m", "seed"],
            ["branch", "lane-a"],
            ["branch", "trunk"],
            ["worktree", "add", "-q", os.path.join(tmp, "wt-lane"), "lane-a"],
            ["worktree", "add", "-q", "--detach", os.path.join(tmp, "wt-detached"), "main"],
        ):
            code, _ = _git(args, repo)
            if code != 0:
                print(f"SELFTEST FAILED: setup git {' '.join(args)} exited {code}")
                return 1
        wt_lane = os.path.join(tmp, "wt-lane")
        wt_detached = os.path.join(tmp, "wt-detached")
        plain = os.path.join(tmp, "not-a-repo")
        os.makedirs(plain)

        expect("main-checkout-refused", check(repo), REFUSED, "not a linked worktree")
        expect("linked-lane-ok", check(wt_lane), OK, "LANE_GUARD OK")
        expect("subdir-of-lane-ok", check(_mkdir(wt_lane, "sub")), OK, "LANE_GUARD OK")
        expect("detached-refused", check(wt_detached), REFUSED, "detached")
        expect("expect-branch-match-ok", check(wt_lane, expect_branch="lane-a"), OK, "LANE_GUARD OK")
        expect("expect-branch-mismatch-refused", check(wt_lane, expect_branch="lane-b"),
               REFUSED, "expected 'lane-b'")
        expect("explicit-default-refused", check(wt_lane, default_branch="lane-a"),
               REFUSED, "default branch 'lane-a'")
        expect("not-a-repo-refused", check(plain), REFUSED, "git read failed")
        expect("git-refused-refused", check(wt_lane, git=os.path.join(tmp, "no-such-git")),
               REFUSED, "git read failed")

        # Default-branch detection: fallback treats main as default, and a
        # linked worktree on main (main checkout moved to trunk) is refused.
        _git(["checkout", "-q", "trunk"], repo)
        wt_main = os.path.join(tmp, "wt-main")
        _git(["worktree", "add", "-q", wt_main, "main"], repo)
        expect("fallback-default-main-refused", check(wt_main), REFUSED, "default branch 'main'")
        # origin/HEAD wins over the fallback: with it naming trunk, main is an
        # ordinary lane branch and passes.
        _git(["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk"], repo)
        expect("origin-head-main-ok", check(wt_main), OK, "LANE_GUARD OK")

        # An inherited GIT_DIR must not redirect the check to another repo.
        saved = os.environ.get("GIT_DIR")
        os.environ["GIT_DIR"] = os.path.join(repo, ".git")
        try:
            expect("inherited-git-dir-ignored", check(wt_lane), OK, "LANE_GUARD OK")
        finally:
            if saved is None:
                os.environ.pop("GIT_DIR", None)
            else:
                os.environ["GIT_DIR"] = saved
    finally:
        if saved_ceiling is None:
            os.environ.pop("GIT_CEILING_DIRECTORIES", None)
        else:
            os.environ["GIT_CEILING_DIRECTORIES"] = saved_ceiling
        shutil.rmtree(tmp, ignore_errors=True)

    passed = total[0] - len(failures)
    if failures:
        print(f"SELFTEST FAILED ({passed}/{total[0]}):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"SELFTEST OK: {passed}/{total[0]}")
    return 0


def _mkdir(parent, name):
    path = os.path.join(parent, name)
    os.makedirs(path, exist_ok=True)
    return path


if __name__ == "__main__":
    sys.exit(main())
