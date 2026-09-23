#!/usr/bin/env python3
"""Lane-start isolation guard: refuse unless this lane really is isolated.

Run as the FIRST step of every write-lane, from the lane's working directory:

    python3 .claude/skills/agentic-delivery/scripts/lane_guard.py --expect-branch NAME

Exit 0 (one `LANE_GUARD OK:` line) only when ALL hold:
  1. --expect-branch was given. Without it the guard could only prove "some
     linked worktree on some non-default branch", not "this lane's worktree",
     so it refuses. --allow-any-branch waives this for a non-lane probe and
     then makes only that weaker claim; a lane brief never uses it.
  2. git answers a plain read in the cwd (a PATH shim or sandbox that blocks
     git fails it). A tool-call hook never sees this subprocess, so chain the
     lane's own direct read first: `git rev-parse HEAD && python3 lane_guard.py`.
  3. The cwd is a LINKED worktree: `git rev-parse --git-dir` differs from
     `--git-common-dir`. Equal means the main checkout (a shared tree), which
     is exactly the escape this guard exists to catch.
  4. HEAD is on a named branch (not detached) that is not a default branch.
  5. HEAD's branch equals --expect-branch exactly.

Otherwise exit 1 with exactly one `LANE_GUARD REFUSE: <reason>` line on stdout,
written to be quoted verbatim in the lane's handback. The lane stops at that
point; it never retries the refused step through another path.

DEFAULT BRANCHES. A union, never a single guess: `main` and `master`, the
remote HEAD's target (`git symbolic-ref refs/remotes/origin/HEAD`) when set,
the main checkout's current branch (first entry of `git worktree list
--porcelain`) when it is on one, and --default-branch when given (it adds to
the set, never replaces it). A stale origin/HEAD therefore cannot make `main`
pass. Fails closed: when the worktree list cannot be read, or when neither
origin/HEAD, the main checkout's branch, nor --default-branch names a branch
(so the repository's real default is unknown), the guard refuses.

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
_ALWAYS_DEFAULTS = ("main", "master")


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


def _main_checkout_branch(cwd, git):
    """Return (readable, branch) for the main checkout.

    The main checkout is the first entry of `git worktree list --porcelain`.
    `readable` is False when that list cannot be read or parsed; `branch` is
    None when the main checkout is detached or bare (no branch to add).
    """
    code, out = _git(["worktree", "list", "--porcelain"], cwd, git)
    if code != 0 or not out.startswith("worktree "):
        return False, None
    prefix = "branch refs/heads/"
    for line in out.split("\n\n", 1)[0].splitlines():
        if line.startswith(prefix) and len(line) > len(prefix):
            return True, line[len(prefix):]
    return True, None


def _default_branches(cwd, explicit, git):
    """Return (set of default branch names, refusal reason or None).

    See the module docstring: the union of main/master, origin/HEAD's target,
    the main checkout's branch, and `explicit`. The reason is set (fail
    closed) when the worktree list is unreadable or no source names a branch.
    """
    defaults = set(_ALWAYS_DEFAULTS)
    named = False
    if explicit:
        defaults.add(explicit)
        named = True
    code, ref = _git(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], cwd, git)
    prefix = "refs/remotes/origin/"
    if code == 0 and ref.startswith(prefix) and len(ref) > len(prefix):
        defaults.add(ref[len(prefix):])
        named = True
    readable, main_branch = _main_checkout_branch(cwd, git)
    if not readable:
        return defaults, "cannot read the worktree list to find the main checkout's branch"
    if main_branch:
        defaults.add(main_branch)
        named = True
    if not named:
        return defaults, (
            "default branch unknown (no origin/HEAD, main checkout not on a branch); "
            "pass --default-branch"
        )
    return defaults, None


def check(cwd, expect_branch=None, default_branch=None, git="git", allow_any_branch=False):
    """Evaluate the lane at `cwd`; return (exit_code, one-line message).

    Refuses when `expect_branch` is None unless `allow_any_branch` is True
    (then the OK line proves only a non-default linked worktree, not which
    lane). Side-effect free: runs read-only git commands only.
    """
    if expect_branch is None and not allow_any_branch:
        return REFUSED, (
            "LANE_GUARD REFUSE: no --expect-branch given; a write-lane must name its own "
            "branch (--allow-any-branch is for non-lane probes only)"
        )
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
    defaults, unknown = _default_branches(top, default_branch, git)
    if unknown:
        return REFUSED, f"LANE_GUARD REFUSE: {unknown} in {top}"
    if branch in defaults:
        return REFUSED, f"LANE_GUARD REFUSE: HEAD is on default branch '{branch}' in {top}"
    if expect_branch is not None and branch != expect_branch:
        return REFUSED, f"LANE_GUARD REFUSE: HEAD is on '{branch}', expected '{expect_branch}' in {top}"
    return OK, f"LANE_GUARD OK: linked worktree {top} on branch '{branch}'"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--expect-branch", help="required: refuse unless HEAD is on exactly this branch")
    parser.add_argument("--allow-any-branch", action="store_true",
                        help="waive --expect-branch (non-lane probes only; proves less)")
    parser.add_argument("--default-branch",
                        help="add a default branch name (joins main, master, origin/HEAD, main checkout)")
    parser.add_argument("--selftest", action="store_true", help="prove every refusal fires")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    code, line = check(os.getcwd(), args.expect_branch, args.default_branch,
                       allow_any_branch=args.allow_any_branch)
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

        lane = "lane-a"
        # --expect-branch is required; only --allow-any-branch waives it.
        expect("no-expect-branch-refused", check(wt_lane), REFUSED, "no --expect-branch")
        expect("allow-any-branch-ok", check(wt_lane, allow_any_branch=True), OK, "LANE_GUARD OK")
        expect("main-checkout-refused", check(repo, expect_branch="main"),
               REFUSED, "not a linked worktree")
        expect("linked-lane-ok", check(wt_lane, expect_branch=lane), OK, "LANE_GUARD OK")
        expect("subdir-of-lane-ok", check(_mkdir(wt_lane, "sub"), expect_branch=lane),
               OK, "LANE_GUARD OK")
        expect("detached-refused", check(wt_detached, expect_branch=lane), REFUSED, "detached")
        expect("expect-branch-mismatch-refused", check(wt_lane, expect_branch="lane-b"),
               REFUSED, "expected 'lane-b'")
        expect("explicit-default-refused",
               check(wt_lane, expect_branch=lane, default_branch=lane),
               REFUSED, "default branch 'lane-a'")
        expect("not-a-repo-refused", check(plain, expect_branch=lane), REFUSED, "git read failed")
        expect("git-refused-refused",
               check(wt_lane, expect_branch=lane, git=os.path.join(tmp, "no-such-git")),
               REFUSED, "git read failed")
        # A git that answers everything except the worktree list: fail closed.
        real_git = shutil.which("git")
        shim = os.path.join(tmp, "git-no-worktree-list")
        with open(shim, "w", encoding="utf-8") as handle:
            handle.write(f'#!/bin/sh\n[ "$1" = worktree ] && exit 1\nexec "{real_git}" "$@"\n')
        os.chmod(shim, 0o755)
        expect("worktree-list-unreadable-refused", check(wt_lane, expect_branch=lane, git=shim),
               REFUSED, "cannot read the worktree list")

        # An inherited GIT_DIR must not redirect the check to another repo.
        saved = os.environ.get("GIT_DIR")
        os.environ["GIT_DIR"] = os.path.join(repo, ".git")
        try:
            expect("inherited-git-dir-ignored", check(wt_lane, expect_branch=lane),
                   OK, "LANE_GUARD OK")
        finally:
            if saved is None:
                os.environ.pop("GIT_DIR", None)
            else:
                os.environ["GIT_DIR"] = saved

        # No origin/HEAD, main checkout moved to trunk: main stays default via
        # the always-default names, and a lane force-added onto the main
        # checkout's own branch is refused.
        _git(["checkout", "-q", "trunk"], repo)
        wt_main = os.path.join(tmp, "wt-main")
        wt_trunk = os.path.join(tmp, "wt-trunk")
        _git(["worktree", "add", "-q", wt_main, "main"], repo)
        _git(["worktree", "add", "-q", "--force", wt_trunk, "trunk"], repo)
        expect("always-default-main-refused", check(wt_main, expect_branch="main"),
               REFUSED, "default branch 'main'")
        expect("main-checkout-branch-refused", check(wt_trunk, expect_branch="trunk"),
               REFUSED, "default branch 'trunk'")
        # --default-branch adds to the set; it never un-defaults main.
        expect("explicit-default-adds-not-replaces",
               check(wt_main, expect_branch="main", default_branch="trunk"),
               REFUSED, "default branch 'main'")
        # origin/HEAD's target is default; a stale origin/HEAD (naming trunk)
        # does not make main pass.
        _git(["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/lane-a"], repo)
        expect("origin-head-target-refused", check(wt_lane, expect_branch=lane),
               REFUSED, "default branch 'lane-a'")
        _git(["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk"], repo)
        expect("stale-origin-head-main-refused", check(wt_main, expect_branch="main"),
               REFUSED, "default branch 'main'")
        expect("origin-head-other-lane-ok", check(wt_lane, expect_branch=lane),
               OK, "LANE_GUARD OK")
        # No origin/HEAD and a detached main checkout: the real default is
        # unknown, so refuse unless --default-branch names it.
        _git(["symbolic-ref", "--delete", "refs/remotes/origin/HEAD"], repo)
        _git(["checkout", "-q", "--detach"], repo)
        expect("default-unknown-refused", check(wt_lane, expect_branch=lane),
               REFUSED, "default branch unknown")
        expect("default-unknown-explicit-ok",
               check(wt_lane, expect_branch=lane, default_branch="trunk"),
               OK, "LANE_GUARD OK")
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
