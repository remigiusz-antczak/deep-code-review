#!/usr/bin/env python3
"""fix_class_gate.py — every fix commit must touch a pinned test, or say why not.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
A bug gets "fixed" one reported case at a time — four, five, six commits in a
row, same shape, no regression test ever pinned — so the bug class keeps
resurfacing under a new input each time. This tool enforces one narrow,
mechanical precondition on every `fix:`-labeled commit in a range: it must add
or modify at least one path on a documented test surface, or it must carry a
`No-Test-Reason:` trailer explaining why it doesn't. Nothing more.

HONESTY (read this before wiring it into CI or citing it in a report)
-----------------------------------------------------------------------
This gate verifies ONLY that a fix commit touched a test-surface path or
declared why not. It does NOT and CANNOT verify that the test actually pins
the whole bug class rather than the one reported case — that a fix scoped to
an enumerated list is judged against that list, and a green test proves
non-regression of the named cases, not completeness against the rest of the
tree, stays the reviewer's job (see `references/method.md`, class-discipline
passage). Any claim that this tool "enforces whole-class fixes" is a
fabrication. The accurate claim is: it enforces a pinned test per fix.

MERGE COMMITS ARE NOT CHECKED (known bypass). The range is walked with
`git rev-list --no-merges`, so every merge commit is skipped — even one whose
subject is `fix:`. A so-called evil merge (a merge commit that carries its own
code change beyond resolving the two parents) can therefore introduce an
untested fix and this gate will not see it. If that matters for a repo,
forbid code changes in merge commits by policy/review, or squash/rebase
instead of merging; this tool does not detect it.

WHAT COUNTS AS A "FIX" COMMIT
------------------------------
The commit subject matches, case-sensitively on the literal `fix`:
    ^fix(\\([^)]*\\))?!?:
i.e. `fix:`, `fix(scope):`, `fix!:`, `fix(scope)!:`. This is Conventional
Commits' `fix` type, including its optional scope and breaking-change `!`.
It deliberately does NOT match `fixture:`, `fixes:`, or any subject where
`fix` is not immediately followed by `(`, `!`, or `:` — those are not the
Conventional Commits `fix` type and are silently ignored (not a failure).

WHAT COUNTS AS "TOUCHING A TEST SURFACE"
------------------------------------------
The commit's diff (`git diff-tree --name-status`) has at least one path that
is ADDED, MODIFIED, RENAMED, or COPIED (never a DELETE-only path — deleting a
test file is not adding coverage) whose new/current path matches one of the
`--test-glob` patterns. Glob syntax: `*` matches within one path segment,
`**` matches across segments (including zero), `?` matches one character.
Default globs (used only when `--test-glob` is never passed; passing any
`--test-glob` REPLACES the defaults, it does not add to them):
    tests/**  test/**  **/*_test.*  **/*.test.*  **/*.spec.*
    **/test_*.py  spec/**  **/evals/*.json

THE `No-Test-Reason` ESCAPE HATCH
------------------------------------
A fix commit with no test-surface touch still PASSES if its trailer block
carries `No-Test-Reason: <non-empty text>` (read via
`git log --format=%(trailers:key=No-Test-Reason,valueonly)`, so folded/
multi-line trailer values are honored the same way `git interpret-trailers`
would resolve them). A present-but-empty trailer (`No-Test-Reason:` with
nothing after it, or only whitespace) does NOT exempt the commit — the point
is a stated reason, not a magic keyword.

EXIT CODES (fail-closed; every branch below is load-bearing)
---------------------------------------------------------------
  0  every fix commit in range passed (touched a test surface or was
     exempted by a non-empty `No-Test-Reason` trailer), including the
     legitimately-empty case of zero commits in range. Merge commits are
     never counted (see HONESTY), so a range whose only fix is a merge
     commit also exits 0.
  1  at least one fix commit failed; each is printed as its own FAIL line.
  2  FAIL CLOSED — the range could not be evaluated at all, never a silent
     pass: not a git repository; `--base`/`--head` unresolvable; `--base` is
     the all-zeros SHA (the value CI hands a brand-new branch push — pass the
     PR base ref or a computed merge-base instead); or the range itself
     could not be walked (a real git error, e.g. an unrelated/unreachable
     history). An empty-but-resolvable range (base and head are the same
     commit) is distinct from all of this and exits 0 with an explicit
     `0 commits in range` line.

USAGE
-----
  fix_class_gate.py --base <ref> --head <ref> [--test-glob GLOB ...]
  fix_class_gate.py --selftest
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

OK = 0
FAIL = 1
ERROR = 2

ZERO_SHA = "0" * 40

# Conventional Commits `fix` type only: `fix`, `fix(scope)`, `fix!`,
# `fix(scope)!`, each followed by `:`. Case-sensitive on the literal `fix` so
# `Fix:`/`FIX:` (not Conventional Commits) are deliberately not matched.
FIX_SUBJECT_RE = re.compile(r"^fix(\([^)]*\))?!?:")

DEFAULT_TEST_GLOBS = (
    "tests/**",
    "test/**",
    "**/*_test.*",
    "**/*.test.*",
    "**/*.spec.*",
    "**/test_*.py",
    "spec/**",
    "**/evals/*.json",
)


def _glob_to_regex(pattern: str) -> re.Pattern:
    """Translate one glob pattern into a compiled full-match regex.

    `**/` matches zero or more leading path segments (so `**/*_test.*`
    matches both `bar_test.py` and `foo/bar_test.py`); a bare trailing `**`
    matches the rest of the path including `/` (so `tests/**` matches every
    path under `tests/`); a lone `*` matches within one segment; `?` matches
    one non-`/` character. Everything else is a literal, regex-escaped.
    """
    out = ["^"]
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*" and pattern[i:i + 2] == "**":
            if pattern[i:i + 3] == "**/":
                out.append("(?:.*/)?")
                i += 3
            else:
                out.append(".*")
                i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    out.append("$")
    return re.compile("".join(out))


def _compile_globs(globs: tuple[str, ...]) -> list[re.Pattern]:
    """Compile a glob tuple once per run; called with either defaults or CLI globs."""
    return [_glob_to_regex(g) for g in globs]


def _matches_any(path: str, compiled_globs: list[re.Pattern]) -> bool:
    """True iff `path` (a git-relative, `/`-separated path) matches any compiled glob."""
    return any(rx.match(path) for rx in compiled_globs)


class GitError(RuntimeError):
    """A git invocation failed in a way the caller must fail closed on."""


def _run_git(repo: str, args: list[str]) -> str:
    """Run `git <args>` in `repo`; return stdout, or raise GitError with stderr on failure."""
    proc = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise GitError(proc.stderr.strip() or f"git {' '.join(args)} failed (rc={proc.returncode})")
    return proc.stdout


def _is_git_repo(repo: str) -> bool:
    """True iff `repo` is inside a git work tree (never raises)."""
    proc = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _resolve_commit(repo: str, ref: str) -> str | None:
    """Resolve `ref` to a full commit SHA, or None if it does not resolve to a commit."""
    proc = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _list_range_shas(repo: str, base: str, head: str) -> list[str]:
    """Non-merge commit SHAs in `base..head`, oldest first. Raises GitError on a real git failure."""
    out = _run_git(repo, ["rev-list", "--no-merges", "--reverse", f"{base}..{head}"])
    return [line for line in out.splitlines() if line.strip()]


def _subject(repo: str, sha: str) -> str:
    """First line (subject) of `sha`'s commit message."""
    return _run_git(repo, ["log", "-1", "--format=%s", sha]).strip()


def _short_sha(repo: str, sha: str) -> str:
    """Git's own abbreviated form of `sha` (report-friendly, unique in this repo)."""
    return _run_git(repo, ["rev-parse", "--short", sha]).strip()


def _no_test_reason(repo: str, sha: str) -> str:
    """Value of `sha`'s `No-Test-Reason` trailer, or `''` if absent/empty.

    `%(trailers:...,valueonly)` resolves folded (multi-line) trailer values the
    same way `git interpret-trailers` would, and yields `''` for both "trailer
    absent" and "trailer present with no value" — both are treated as
    not-exempting by the caller, which is the point: a bare keyword doesn't
    count as a stated reason.
    """
    out = _run_git(
        repo,
        ["log", "-1", "--format=%(trailers:key=No-Test-Reason,valueonly)", sha],
    )
    return out.strip()


def _changed_paths(repo: str, sha: str) -> list[tuple[str, bool]]:
    """`[(path, counts_as_add_or_modify), ...]` touched by one non-merge commit `sha`.

    Uses NUL-terminated `--name-status -z` output so paths with spaces or tabs
    never desync the parser. A rename/copy (`R`/`C`) counts its NEW path as
    modified (the old path is not separately reported — its removal alone
    would never satisfy "touches a test surface"). A delete-only path (`D`)
    is reported with `counts_as_add_or_modify=False`: removing a test file is
    never sufficient to pass this gate.
    """
    out = _run_git(
        repo,
        ["diff-tree", "-r", "--no-commit-id", "--name-status", "-z", sha],
    )
    tokens = out.split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    results: list[tuple[str, bool]] = []
    i = 0
    while i < len(tokens):
        status = tokens[i]
        i += 1
        code = status[0] if status else ""
        if code in ("R", "C"):
            i += 1  # old path, not reported on its own
            new_path = tokens[i]
            i += 1
            results.append((new_path, True))
        elif code == "D":
            path = tokens[i]
            i += 1
            results.append((path, False))
        else:
            path = tokens[i]
            i += 1
            results.append((path, True))
    return results


def run_gate(repo: str, base: str, head: str, test_globs: tuple[str, ...]) -> tuple[int, list[str]]:
    """Evaluate `base..head` in `repo`; return (exit_code, printable lines).

    Fail-closed ordering: repo-ness, then the all-zeros sentinel, then ref
    resolution, then the range walk, are each checked before any commit is
    inspected — so an unresolvable input can never fall through to a 0/1
    verdict on a partial or wrong commit set.
    """
    lines: list[str] = []

    if not _is_git_repo(repo):
        return ERROR, [f"error: {repo!r} is not a git repository"]

    if base == ZERO_SHA:
        return ERROR, [
            "error: --base is the all-zeros SHA (git's placeholder for a new-branch "
            "push). This is not a usable diff base. Pass the pull request's declared "
            "base ref, or a computed `git merge-base` between the branches, instead."
        ]

    base_sha = _resolve_commit(repo, base)
    if base_sha is None:
        return ERROR, [f"error: --base {base!r} does not resolve to a commit"]
    head_sha = _resolve_commit(repo, head)
    if head_sha is None:
        return ERROR, [f"error: --head {head!r} does not resolve to a commit"]

    try:
        shas = _list_range_shas(repo, base_sha, head_sha)
    except GitError as exc:
        return ERROR, [f"error: could not walk range {base}..{head}: {exc}"]

    if not shas:
        return OK, ["0 commits in range"]

    compiled_globs = _compile_globs(test_globs)
    fails: list[str] = []
    total_fix = 0
    exempted = 0

    for sha in shas:
        subject = _subject(repo, sha)
        if not FIX_SUBJECT_RE.match(subject):
            continue
        total_fix += 1
        changed = _changed_paths(repo, sha)
        touched_test = any(
            counts and _matches_any(path, compiled_globs) for path, counts in changed
        )
        if touched_test:
            continue
        reason = _no_test_reason(repo, sha)
        if reason:
            exempted += 1
            continue
        short = _short_sha(repo, sha)
        fails.append(
            f"FAIL {short} {subject} — no test surface touched and no No-Test-Reason trailer"
        )

    lines.extend(fails)
    if fails:
        lines.append(
            f"fix_class_gate: FAILED ({total_fix} fix commit(s) checked, "
            f"{len(fails)} failing, {exempted} exempted by trailer)"
        )
        return FAIL, lines

    lines.append(f"fix_class_gate: ok ({total_fix} fix commit(s) checked, {exempted} exempted by trailer)")
    return OK, lines


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

_GIT_ENV_NAME = "Jane Smith"
_GIT_ENV_EMAIL = "jane@example.com"


def _sh(repo: Path, *args: str) -> str:
    """Run one git command in the selftest's throwaway repo; raise on failure."""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


def _init_repo(repo: Path) -> None:
    """Create a throwaway git repo with placeholder identity and no gpg signing."""
    repo.mkdir(parents=True, exist_ok=True)
    _sh(repo, "init", "-q")
    _sh(repo, "config", "user.name", _GIT_ENV_NAME)
    _sh(repo, "config", "user.email", _GIT_ENV_EMAIL)
    _sh(repo, "config", "commit.gpgsign", "false")
    _sh(repo, "config", "tag.gpgsign", "false")


def _commit(repo: Path, message: str, files: dict[str, str], delete: list[str] | None = None) -> str:
    """Write/update `files`, delete `delete`, commit `message`; return the new commit's full SHA."""
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        _sh(repo, "add", rel)
    for rel in delete or []:
        _sh(repo, "rm", "-q", rel)
    _sh(repo, "commit", "-q", "-m", message)
    return _sh(repo, "rev-parse", "HEAD")


def _run_tool(repo: Path, base: str, head: str, globs: list[str] | None = None) -> tuple[int, str]:
    """Invoke this module's own CLI in-process-equivalent via subprocess against `repo`."""
    args = [sys.executable, __file__, "--base", base, "--head", head]
    for g in globs or []:
        args.extend(["--test-glob", g])
    proc = subprocess.run(args, cwd=str(repo), capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr)


def _selftest() -> int:
    """Build throwaway git repos and assert every mandatory case's exact (rc, evidence).

    Each case below is a real assertion against a real repo and a real
    subprocess invocation of this tool — not a unit test of an internal
    helper — so a future edit that quietly turns a fail-closed branch into a
    pass breaks this function loudly, printing which case broke and why.
    """
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

    with tempfile.TemporaryDirectory(prefix="fix_class_gate_selftest_") as tmp:
        tmp_path = Path(tmp)

        # 1) fix without touching a test surface -> FAIL, names the commit.
        repo = tmp_path / "case_fix_no_test"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        head = _commit(repo, "fix: off-by-one in parser", {"src/a.py": "x = 2\n"})
        rc, out = _run_tool(repo, base, head)
        check("fix-no-test", rc, out, FAIL, must_have=("FAIL", head[:7]))

        # 2) fix touching a test file -> pass.
        repo = tmp_path / "case_fix_with_test"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        head = _commit(
            repo, "fix: off-by-one in parser",
            {"src/a.py": "x = 2\n", "tests/test_a.py": "def test_a(): assert True\n"},
        )
        rc, out = _run_tool(repo, base, head)
        check("fix-with-test", rc, out, OK, must_not=("FAIL",))

        # 3) fix with a non-empty No-Test-Reason trailer -> pass, counted exempted.
        repo = tmp_path / "case_fix_trailer_nonempty"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        _sh(repo, "add", ".")
        Path(repo / "src/a.py").write_text("x = 2\n")
        _sh(repo, "add", "src/a.py")
        _sh(repo, "commit", "-q", "-m",
            "fix: cannot repro locally\n\nNo-Test-Reason: requires prod-only race, tracked in ticket")
        head = _sh(repo, "rev-parse", "HEAD")
        rc, out = _run_tool(repo, base, head)
        check("fix-trailer-nonempty", rc, out, OK, must_have=("1 exempted",), must_not=("FAIL",))

        # 4) fix with an EMPTY No-Test-Reason trailer -> FAIL (bare keyword doesn't exempt).
        repo = tmp_path / "case_fix_trailer_empty"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        Path(repo / "src/a.py").write_text("x = 2\n")
        _sh(repo, "add", "src/a.py")
        _sh(repo, "commit", "-q", "-m", "fix: cannot repro locally\n\nNo-Test-Reason:")
        head = _sh(repo, "rev-parse", "HEAD")
        rc, out = _run_tool(repo, base, head)
        check("fix-trailer-empty", rc, out, FAIL, must_have=("FAIL",))

        # 5) feat: without a test -> pass (not a fix commit at all).
        repo = tmp_path / "case_feat_no_test"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        head = _commit(repo, "feat: add new widget", {"src/b.py": "y = 1\n"})
        rc, out = _run_tool(repo, base, head)
        check("feat-no-test", rc, out, OK, must_not=("FAIL",))

        # 6) fix(scope)!: recognized as a fix (fails without a test, proving recognition).
        repo = tmp_path / "case_fix_scope_bang"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        head = _commit(repo, "fix(api)!: break compatibility to correct types", {"src/a.py": "x = 2\n"})
        rc, out = _run_tool(repo, base, head)
        check("fix-scope-bang", rc, out, FAIL, must_have=("FAIL", head[:7]))

        # 7) fixture:/fixes subjects are NOT the fix type -> pass even without a test.
        repo = tmp_path / "case_not_fix_type"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        _commit(repo, "fixture: update golden fixtures", {"src/a.py": "x = 2\n"})
        head = _commit(repo, "fixes bug in parser prose", {"src/a.py": "x = 3\n"})
        rc, out = _run_tool(repo, base, head)
        check("not-fix-type", rc, out, OK, must_not=("FAIL",))

        # 8) fix that only DELETES a test file -> FAIL (deletion isn't coverage).
        repo = tmp_path / "case_fix_deletes_test"
        _init_repo(repo)
        base = _commit(
            repo, "chore: init",
            {"src/a.py": "x = 1\n", "tests/test_a.py": "def test_a(): assert True\n"},
        )
        head = _commit(repo, "fix: remove flaky test", {}, delete=["tests/test_a.py"])
        rc, out = _run_tool(repo, base, head)
        check("fix-deletes-test", rc, out, FAIL, must_have=("FAIL",))

        # 9) merge commit skipped even if fix-labeled; only non-merge fix commits count.
        repo = tmp_path / "case_merge_skipped"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        _sh(repo, "checkout", "-q", "-b", "feature")
        _commit(repo, "chore: unrelated feature work", {"src/feature.py": "z = 1\n"})
        _sh(repo, "checkout", "-q", "-")
        _sh(repo, "merge", "--no-ff", "-m", "fix: integrate feature branch", "feature")
        head = _sh(repo, "rev-parse", "HEAD")
        rc, out = _run_tool(repo, base, head)
        check("merge-skipped", rc, out, OK, must_have=("0 fix commit(s) checked",), must_not=("FAIL",))

        # 10) mixed range: one good fix + one bad fix -> FAIL naming only the bad one.
        repo = tmp_path / "case_mixed_range"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        good = _commit(
            repo, "fix: guard null input",
            {"src/a.py": "x = 2\n", "tests/test_a.py": "def test_a(): assert True\n"},
        )
        bad = _commit(repo, "fix: guard empty input", {"src/a.py": "x = 3\n"})
        rc, out = _run_tool(repo, base, bad)
        check("mixed-range", rc, out, FAIL, must_have=(bad[:7],), must_not=(good[:7],))

        # 11) unresolvable base -> ERROR (fail closed, never a silent pass).
        repo = tmp_path / "case_bad_base"
        _init_repo(repo)
        head = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        rc, out = _run_tool(repo, "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef", head)
        check("bad-base", rc, out, ERROR)

        # 12) all-zeros base -> ERROR, tells the caller to use the PR base/merge-base.
        repo = tmp_path / "case_zero_base"
        _init_repo(repo)
        head = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        rc, out = _run_tool(repo, ZERO_SHA, head)
        check("zero-base", rc, out, ERROR, must_have=("merge-base",))

        # 13) empty range (base == head) -> OK, explicit "0 commits in range".
        repo = tmp_path / "case_empty_range"
        _init_repo(repo)
        only = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        rc, out = _run_tool(repo, only, only)
        check("empty-range", rc, out, OK, must_have=("0 commits in range",))

        # 14) custom --test-glob overrides (not adds to) the defaults.
        repo = tmp_path / "case_custom_glob"
        _init_repo(repo)
        base = _commit(repo, "chore: init", {"src/a.py": "x = 1\n"})
        head = _commit(
            repo, "fix: off-by-one in parser",
            {"src/a.py": "x = 2\n", "mytests/check.py": "def check(): assert True\n"},
        )
        rc_default, out_default = _run_tool(repo, base, head)
        check("custom-glob-default-fails", rc_default, out_default, FAIL, must_have=("FAIL",))
        rc_custom, out_custom = _run_tool(repo, base, head, globs=["mytests/**"])
        check("custom-glob-overrides", rc_custom, out_custom, OK, must_not=("FAIL",))

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELFTEST OK: 14/14 cases passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: `--selftest`, or `--base <ref> --head <ref> [--test-glob ...]`."""
    parser = argparse.ArgumentParser(
        description=(
            "Enforce a pinned test per fix: every Conventional-Commits `fix:` commit in "
            "base..head must touch a test-surface path or declare a No-Test-Reason trailer."
        )
    )
    parser.add_argument("--base", help="range base ref (exclusive)")
    parser.add_argument("--head", help="range head ref (inclusive)")
    parser.add_argument(
        "--test-glob", action="append", dest="test_globs", metavar="GLOB",
        help="glob a test-surface path must match; repeatable; REPLACES the defaults when given",
    )
    parser.add_argument("--selftest", action="store_true", help="run the built-in selftest and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.base or not args.head:
        parser.error("--base and --head are both required")
        return ERROR  # pragma: no cover — parser.error() already exits(2)

    globs = tuple(args.test_globs) if args.test_globs else DEFAULT_TEST_GLOBS
    code, lines = run_gate(".", args.base, args.head, globs)
    for line in lines:
        print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
