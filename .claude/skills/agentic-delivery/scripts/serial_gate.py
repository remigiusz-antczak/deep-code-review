#!/usr/bin/env python3
"""serial_gate.py — fail-closed test selection + a cross-lane serial run lock.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
N parallel agent lanes share one repo. If each lane runs the FULL test suite
on every push, the lanes self-DoS the host (CPU/RAM contention, flaky timeouts
that look like real failures). The fix — path-scoped test selection ("only
run the tests near what changed") — introduces a worse failure if it is
wrong: a bad glob silently SKIPS the tests that would have caught a
regression, and the change ships untested with a green check mark. So the
selector itself must be fail-closed (any input it cannot classify with
confidence runs the FULL suite, never "nothing to run, pass") and it must be
testable (`--selftest` pins every fail-closed branch with a real assertion).

Serializing the shared-state parts of a multi-lane push (a migration, a
generated file, the integration branch) needs a real cross-process lock. This
uses `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on a lock file — a KERNEL advisory
lock, not a hand-rolled one: the `flock(2)` syscall exists on both macOS and
Linux (the common "macOS has no flock" claim is about the `flock(1)` CLI
binary used to wrap a shell command, which macOS indeed lacks — the Python
`fcntl.flock()` syscall binding is unaffected and has always worked on both).
A kernel lock has one property no user-space "stale lock" scheme can fully
replicate: the kernel releases it the instant the holding process's last file
descriptor closes, for ANY reason the process ends — clean exit, uncaught
exception, or `SIGKILL`. There is nothing to reclaim and nothing to age out.

TWO SUBCOMMANDS
----------------
select --map <map.tsv> [--base REF --head REF | --changed-file PATH ...]
    Print selected test targets, one per line, OR the single line `FULL`
    meaning "run the whole suite." Exit 0 on a resolved selection (mapped
    or FULL). Exit 2 — plus a reason on stderr — when the input itself could
    not be resolved (a bad ref, a malformed or missing map): FULL is still
    printed to stdout (a caller that only checks stdout still runs the full
    suite), but the caller's script SHOULD treat exit 2 as "investigate,"
    not silently continue.

    MAP FILE FORMAT (tab-separated; one row per line):
      <glob>\t<test target>       — changed path matching <glob> selects <test target>
      !full\t<glob>                — changed path matching <glob> forces FULL
      # comment or blank line      — ignored
    The map file's OWN path is always FULL-forcing, whether or not it also
    appears as a `!full` row — a change to the routing table itself is by
    definition a change no fixed row can vouch for. "Own path" is compared
    both as given and relative to the repository top level (`git rev-parse
    --show-toplevel`, run in --repo or the cwd), so an absolute or
    cwd-relative --map still matches the repo-relative path git reports.

    The diff is read with `git diff --name-only --no-renames`: a rename is
    reported as its deleted OLD path plus its added NEW path, so moving a
    file out of a `!full` or mapped area can never hide the old path.

    GLOB SEMANTICS (exactly what is implemented, not "glob-like"): each
    changed path is normalized to a repo-root-relative POSIX path (backslashes
    turned to `/`, no leading `./`), then matched against each pattern with
    `fnmatch.fnmatchcase`. `fnmatch` has no path-separator concept: a bare
    `*` already matches across `/` the same way `**` conventionally does, `?`
    matches exactly one character, and `[seq]`/`[!seq]` match a character
    class — literally, per Python's `fnmatch` module. `**` is accepted and
    behaves identically to a single `*` (both translate through the same
    "match anything" rule); there is no directory-scoped single-`*`.

    FAIL-CLOSED RULES, in order:
      (a) map missing / unreadable / malformed (bad row shape)   -> FULL, exit 2
      (b) unresolvable ref / git error resolving the diff        -> FULL, exit 2
      (c) empty diff (nothing changed)                           -> FULL, exit 0
      (d) any changed path matches NO row                        -> FULL, exit 0
      (e) any changed path matches a `!full` glob, or IS the map -> FULL, exit 0
      (f) otherwise: union of every matched row's target(s), deduped, sorted

run --lock-dir DIR [--timeout SECONDS] -- <cmd...>
    Serialize <cmd...> across lanes with a kernel advisory lock:
    `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on the file `DIR/lock` (DIR is
    created if missing). A waiter polls with bounded exponential backoff
    (capped, jittered) until it acquires the lock or --timeout elapses
    (default 120s) — on timeout, exits 124 and NEVER runs <cmd...> unlocked.
    Once acquired, the SAME fd is truncated and rewritten with an
    informational owner record (pid, host, UTC acquire time) for a human
    inspecting the lock file; this record is never read back by the tool and
    never consulted for correctness — only the flock decides who holds the
    lock. The lock is released (and the fd closed) in `finally` and on
    SIGTERM/SIGINT; the OS additionally guarantees release on any other
    process death, including SIGKILL, because a dead process cannot hold an
    open file descriptor. The child's own exit code is propagated. There is
    no staleness window, no age-based reclaim, and no lock file to "clean up
    by hand": a lock that looks held IS held, for as long as its holder's
    process is alive, however long that is.

    PLATFORM SCOPE: POSIX advisory locks (`flock`) apply per open-file-table
    entry on a single host's local filesystem. This is not a distributed
    lock: it does not work over NFS or other network filesystems, and it says
    nothing about processes on a different host. Use it only for lanes on one
    shared host talking to one shared local disk. `fcntl` does not exist on
    Windows; `run` on a platform without it fails closed (exit 2, <cmd...>
    never runs) rather than silently running unlocked.

USAGE
-----
  serial_gate.py select --map map.tsv --base origin/main --head HEAD
  serial_gate.py select --map map.tsv --changed-file src/foo.py
  serial_gate.py run --lock-dir /tmp/x.lock -- pytest -k foo
  serial_gate.py --selftest
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import posixpath
import random
import signal
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

try:
    import fcntl  # POSIX only — absent on Windows.
except ImportError:  # pragma: no cover — exercised only on non-POSIX hosts
    fcntl = None  # type: ignore[assignment]

OK = 0
USAGE_ERROR = 2
LOCK_TIMEOUT = 124
LOCK_ERROR = 1

FULL = "FULL"

DEFAULT_LOCK_TIMEOUT = 120.0
_POLL_START = 0.05
_POLL_CAP = 1.0
_POLL_BACKOFF = 1.6


# --------------------------------------------------------------------------
# select
# --------------------------------------------------------------------------


class MapError(Exception):
    """Map file missing, unreadable, or malformed. Always forces FULL."""


def _normalize_path(path: str) -> str:
    """Repo-root-relative POSIX form used for every glob comparison.

    Backslashes become `/`, a leading `./` is stripped, and the result is
    NOT resolved against the filesystem (a changed path from `git diff` may
    no longer exist at HEAD, e.g. a deletion — this must still match).
    """
    p = path.replace("\\", "/")
    p = posixpath.normpath(p)
    if p.startswith("./"):
        p = p[2:]
    return p


def parse_map(map_path: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Parse the TSV map. Returns (rows, full_globs).

    `rows` is `[(glob, target), ...]` in file order. `full_globs` is every
    glob from a `!full` row. Raises `MapError` — never returns a partial or
    best-effort result — on: missing file, unreadable file, or any
    non-comment/non-blank line that is not exactly two tab-separated,
    non-empty fields. A malformed map is a routing-table failure, and a
    routing-table failure must be loud, not silently partially applied.
    """
    if not map_path or not os.path.isfile(map_path):
        raise MapError(f"map file not found: {map_path!r}")
    try:
        with open(map_path, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError as exc:
        raise MapError(f"map file unreadable: {map_path!r} ({exc})") from exc

    rows: list[tuple[str, str]] = []
    full_globs: list[str] = []
    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n").rstrip("\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 2 or not fields[0].strip() or not fields[1].strip():
            raise MapError(
                f"malformed map row at {map_path}:{lineno}: expected "
                f"'<glob>\\t<target>', got {line!r}"
            )
        left, right = fields[0].strip(), fields[1].strip()
        if left == "!full":
            full_globs.append(right)
        else:
            rows.append((left, right))
    return rows, full_globs


def _git_diff_paths(base: str, head: str, repo_dir: str | None) -> list[str]:
    """Return changed paths between two refs. Raises `MapError` on any git
    failure (bad ref, not a repo, etc.) so the caller forces FULL + exit 2.
    """
    cmd = ["git"]
    if repo_dir:
        cmd += ["-C", repo_dir]
    # --no-renames: a rename must surface BOTH its old and new path. With
    # rename detection on (git's porcelain default), only the new path is
    # printed, so moving a file out of a `!full`/mapped area would silently
    # drop the old path from selection — a fail-open.
    cmd += ["diff", "--name-only", "--no-renames", base, head]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        raise MapError(f"git invocation failed: {exc}") from exc
    if proc.returncode != 0:
        raise MapError(
            f"git diff --name-only --no-renames {base} {head} failed (exit "
            f"{proc.returncode}): {proc.stderr.strip()}"
        )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _map_self_paths(map_path: str, repo_dir: str | None) -> set[str]:
    """Every normalized form under which the map file itself may appear in
    the changed-path list.

    Always includes the --map argument as given. Additionally includes the
    map's path relative to the repository top level (resolved via
    `git rev-parse --show-toplevel` in `repo_dir`, or the cwd), because git
    and `--changed-file` report repo-relative paths while --map may be
    absolute or relative to a different cwd. Both sides are `realpath`-ed so
    symlinked temp dirs (e.g. macOS /var -> /private/var) compare equal. If
    the top level cannot be resolved, or the map lies outside it, only the
    as-given form is used (no guess).
    """
    selves = {_normalize_path(map_path)}
    cmd = ["git"]
    if repo_dir:
        cmd += ["-C", repo_dir]
    cmd += ["rev-parse", "--show-toplevel"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError:
        return selves
    top = proc.stdout.strip()
    if proc.returncode != 0 or not top:
        return selves
    try:
        rel = os.path.relpath(os.path.realpath(map_path), os.path.realpath(top))
    except ValueError:  # e.g. different drives on Windows: not inside the repo
        return selves
    rel = _normalize_path(rel)
    if rel != ".." and not rel.startswith("../"):
        selves.add(rel)
    return selves


def select_targets(
    map_path: str,
    changed_files: list[str] | None = None,
    base: str | None = None,
    head: str | None = None,
    repo_dir: str | None = None,
) -> tuple[int, list[str]]:
    """Resolve one selection. Returns `(exit_code, lines_to_print)`.

    `lines_to_print` is either `["FULL"]` or the sorted, deduped target
    list. Every fail-closed rule in the module docstring is implemented
    here, in the documented order, so a caller reading this function top to
    bottom sees the exact precedence.
    """
    try:
        rows, full_globs = parse_map(map_path)
    except MapError as exc:
        print(f"serial_gate: {exc}", file=sys.stderr)
        return USAGE_ERROR, [FULL]

    if changed_files is not None:
        changed = [_normalize_path(p) for p in changed_files]
    else:
        if not base or not head:
            print(
                "serial_gate: select requires --changed-file or both --base and --head",
                file=sys.stderr,
            )
            return USAGE_ERROR, [FULL]
        try:
            changed = [_normalize_path(p) for p in _git_diff_paths(base, head, repo_dir)]
        except MapError as exc:
            print(f"serial_gate: {exc}", file=sys.stderr)
            return USAGE_ERROR, [FULL]

    if not changed:
        return OK, [FULL]

    map_selves = _map_self_paths(map_path, repo_dir)
    force_full_globs = list(full_globs)

    for path in changed:
        if path in map_selves:
            return OK, [FULL]
        if any(fnmatch.fnmatchcase(path, g) for g in force_full_globs):
            return OK, [FULL]

    targets: set[str] = set()
    for path in changed:
        matched_any = False
        for glob, target in rows:
            if fnmatch.fnmatchcase(path, glob):
                matched_any = True
                targets.add(target)
        if not matched_any:
            return OK, [FULL]

    return OK, sorted(targets)


# --------------------------------------------------------------------------
# run — cross-lane serial lock (kernel advisory lock via flock)
# --------------------------------------------------------------------------


class LockTimeout(Exception):
    """Raised internally when acquisition exceeds --timeout."""


def _lock_file_path(lock_dir: str) -> str:
    return os.path.join(lock_dir, "lock")


def acquire_lock(lock_dir: str, timeout: float) -> int:
    """Block until this process holds an exclusive kernel advisory lock.

    Opens (creating if needed) `<lock_dir>/lock` and polls
    `fcntl.flock(fd, LOCK_EX | LOCK_NB)` with bounded, jittered exponential
    backoff until it succeeds or `timeout` elapses. Returns the open file
    descriptor: that fd IS the lock. The caller must keep it open for
    exactly as long as it wants to hold the lock, and release it (see
    `release_lock`) to let a waiter through — or simply let the process die,
    which the kernel treats identically.

    Raises `LockTimeout` once `timeout` elapses without acquiring, closing
    the fd first; the caller must not run its command in that case. Raises
    `OSError` on any other failure opening or locking the file (e.g. a
    permissions error) — a fatal condition distinct from "someone else holds
    it," which callers should treat as an error, not a normal contention
    path.
    """
    assert fcntl is not None, "acquire_lock requires fcntl (POSIX only)"
    os.makedirs(lock_dir, exist_ok=True)
    fd = os.open(_lock_file_path(lock_dir), os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + timeout
    delay = _POLL_START
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            pass  # held by another process right now — keep polling
        except OSError:
            os.close(fd)
            raise

        if time.monotonic() >= deadline:
            os.close(fd)
            raise LockTimeout(f"timed out after {timeout}s waiting for lock: {lock_dir}")

        time.sleep(min(delay, _POLL_CAP) + random.uniform(0, delay * 0.1))
        delay = min(delay * _POLL_BACKOFF, _POLL_CAP)


def _write_owner_info(fd: int) -> None:
    """Best-effort, human-readable record of who holds the lock right now.

    Truncates and rewrites the SAME fd that holds the flock with this
    process's pid, host, and UTC acquire time, so a human looking at the
    lock file mid-run can see who has it. Never read back by this tool and
    never consulted for correctness — only the flock itself decides who
    holds the lock. A failure to write is swallowed: it cannot affect
    whether the lock is held.
    """
    owner = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "acquired_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, json.dumps(owner).encode("utf-8"))
    except OSError:
        pass


def release_lock(fd: int) -> None:
    """Release the flock on `fd` and close it. Never raises."""
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass


def run_locked(lock_dir: str, timeout: float, cmd: list[str]) -> int:
    """Acquire the lock, run `cmd`, release, and return `cmd`'s exit code.

    Fails closed with `LOCK_ERROR`/2-family behavior and never runs `cmd` if
    `fcntl` is unavailable (Windows has no `fcntl` module — this lock is
    POSIX-only) or if the lock file itself cannot be opened/locked for a
    reason other than contention. A SIGTERM/SIGINT while waiting or while
    the child runs still releases the lock: the handler raises `SystemExit`,
    which unwinds through the `finally` below exactly like any other
    exception. Any OTHER process death (including SIGKILL) releases the
    lock without any handler running at all, because the kernel closes the
    dead process's file descriptors.
    """
    if fcntl is None:
        print(
            "serial_gate: fcntl is unavailable on this platform (e.g. "
            "Windows) — this lock is POSIX-only; refusing to run unlocked",
            file=sys.stderr,
        )
        return USAGE_ERROR

    held: dict[str, int | None] = {"fd": None}

    def _on_signal(signum, _frame):
        raise SystemExit(128 + signum)

    old_term = signal.signal(signal.SIGTERM, _on_signal)
    old_int = signal.signal(signal.SIGINT, _on_signal)
    try:
        try:
            held["fd"] = acquire_lock(lock_dir, timeout)
        except LockTimeout as exc:
            print(f"serial_gate: {exc}", file=sys.stderr)
            return LOCK_TIMEOUT
        except OSError as exc:
            print(f"serial_gate: lock acquisition failed: {exc}", file=sys.stderr)
            return LOCK_ERROR
        _write_owner_info(held["fd"])
        proc = subprocess.run(cmd)
        return proc.returncode
    finally:
        if held["fd"] is not None:
            release_lock(held["fd"])
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _cmd_select(args: argparse.Namespace) -> int:
    code, lines = select_targets(
        map_path=args.map,
        changed_files=args.changed_file or None,
        base=args.base,
        head=args.head,
        repo_dir=args.repo,
    )
    for line in lines:
        print(line)
    return code


def _cmd_run(args: argparse.Namespace, cmd: list[str]) -> int:
    if not cmd:
        print("serial_gate: run requires a command after '--'", file=sys.stderr)
        return USAGE_ERROR
    return run_locked(args.lock_dir, args.timeout, cmd)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: `select`, `run -- <cmd>`, or `--selftest`."""
    argv = sys.argv[1:] if argv is None else argv

    if argv and argv[0] == "--selftest":
        return _selftest()

    parser = argparse.ArgumentParser(
        description="Fail-closed path-scoped test selection + a cross-lane serial run lock."
    )
    parser.add_argument("--selftest", action="store_true", help="run the built-in self-test suite")
    sub = parser.add_subparsers(dest="subcommand")

    p_select = sub.add_parser("select", help="pick test targets for a diff, or FULL")
    p_select.add_argument("--map", required=True, help="path to the <glob>\\t<target> TSV map")
    p_select.add_argument("--base", help="base git ref")
    p_select.add_argument("--head", help="head git ref")
    p_select.add_argument("--repo", help="run git in this directory (default: cwd); also locates the repo top level for the map self-check")
    p_select.add_argument(
        "--changed-file", action="append", default=[],
        help="a changed path (repeatable); bypasses git entirely",
    )

    p_run = sub.add_parser("run", help="serialize a command across lanes with a flock-based lock")
    p_run.add_argument("--lock-dir", required=True, help="lock directory path (holds a file named 'lock')")
    p_run.add_argument("--timeout", type=float, default=DEFAULT_LOCK_TIMEOUT,
                        help=f"seconds to wait for the lock before giving up (default {DEFAULT_LOCK_TIMEOUT})")

    cmd: list[str] = []
    if "run" in argv:
        run_idx = argv.index("run")
        if "--" in argv[run_idx:]:
            sep = argv.index("--", run_idx)
            cmd = argv[sep + 1:]
            argv = argv[:sep]

    if not argv:
        parser.error("a subcommand is required (select, run) or --selftest")
        return USAGE_ERROR  # pragma: no cover — parser.error() already exits(2)

    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if args.subcommand == "select":
        return _cmd_select(args)
    if args.subcommand == "run":
        return _cmd_run(args, cmd)
    parser.error("a subcommand is required (select, run) or --selftest")
    return USAGE_ERROR  # pragma: no cover


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------


def _selftest() -> int:
    """Run every planted case and assert it behaves. Any failure prints a
    labeled reason and the function returns non-zero — this is the tool's
    own proof that fail-closed selection and the flock lock actually fire on
    real input, not just that they parse.
    """
    import shutil

    failures: list[str] = []
    total = {"n": 0}

    def check(label: str, cond: bool, detail: str = "") -> None:
        total["n"] += 1
        if not cond:
            failures.append(f"{label}: {detail}" if detail else label)

    tmp = tempfile.mkdtemp(prefix="serial_gate_selftest_")
    try:
        _selftest_select(tmp, check)
        _selftest_lock(tmp, check)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    passed = total["n"] - len(failures)
    if failures:
        print(f"SELFTEST FAILED ({passed}/{total['n']}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"SELFTEST OK: {passed}/{total['n']}")
    return 0


def _write_map(path: str, rows: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")


def _selftest_select(tmp: str, check) -> None:
    map_path = os.path.join(tmp, "map.tsv")
    _write_map(map_path, [
        "# comment line, ignored",
        "",
        "src/alpha/**\ttest_alpha",
        "src/beta/**\ttest_beta",
        "!full\tconfig/critical.*",
    ])

    # 1) mapped path -> exactly its target, and NOT FULL.
    code, lines = select_targets(map_path, changed_files=["src/alpha/x.py"])
    check("mapped-path", code == OK and lines == ["test_alpha"], f"got {code} {lines}")

    # 2) two mapped paths -> union deduped, sorted.
    code, lines = select_targets(
        map_path, changed_files=["src/alpha/x.py", "src/alpha/y.py", "src/beta/z.py"]
    )
    check("two-mapped-union", code == OK and lines == ["test_alpha", "test_beta"], f"got {code} {lines}")

    # 3) unmapped path -> FULL.
    code, lines = select_targets(map_path, changed_files=["docs/readme.md"])
    check("unmapped-full", code == OK and lines == [FULL], f"got {code} {lines}")

    # 4) !full path -> FULL.
    code, lines = select_targets(map_path, changed_files=["config/critical.yaml"])
    check("bang-full", code == OK and lines == [FULL], f"got {code} {lines}")

    # 5) map-file change -> FULL (even though map.tsv matches no listed row).
    code, lines = select_targets(map_path, changed_files=[_normalize_path(map_path)])
    check("map-file-forces-full", code == OK and lines == [FULL], f"got {code} {lines}")

    # 6) empty diff -> FULL.
    code, lines = select_targets(map_path, changed_files=[])
    check("empty-diff-full", code == OK and lines == [FULL], f"got {code} {lines}")

    # 7) malformed map -> rc 2 (+ FULL printed).
    bad_map = os.path.join(tmp, "bad_map.tsv")
    _write_map(bad_map, ["only-one-field-no-tab"])
    code, lines = select_targets(bad_map, changed_files=["src/alpha/x.py"])
    check("malformed-map-rc2", code == USAGE_ERROR and lines == [FULL], f"got {code} {lines}")

    # 8) missing map -> rc 2 (+ FULL printed) — same fail-closed family as malformed.
    code, lines = select_targets(os.path.join(tmp, "does-not-exist.tsv"), changed_files=["x"])
    check("missing-map-rc2", code == USAGE_ERROR and lines == [FULL], f"got {code} {lines}")

    # 9 & 10) real git repo: unresolvable ref -> FULL + rc2; empty diff -> FULL + rc0;
    # plus one real mapped-diff exercise of the --base/--head code path.
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    _git(repo, ["init", "-q"])
    _git(repo, ["config", "user.email", "jane@example.com"])
    _git(repo, ["config", "user.name", "Jane Smith"])
    os.makedirs(os.path.join(repo, "src", "alpha"))
    with open(os.path.join(repo, "src", "alpha", "x.py"), "w") as fh:
        fh.write("1\n")
    _git(repo, ["add", "."])
    _git(repo, ["commit", "-q", "-m", "base"])
    base_sha = _git(repo, ["rev-parse", "HEAD"]).strip()

    with open(os.path.join(repo, "src", "alpha", "x.py"), "w") as fh:
        fh.write("2\n")
    _git(repo, ["commit", "-q", "-am", "change alpha"])
    head_sha = _git(repo, ["rev-parse", "HEAD"]).strip()

    repo_map = os.path.join(repo, "map.tsv")
    _write_map(repo_map, ["src/alpha/**\ttest_alpha"])

    code, lines = select_targets(repo_map, base=base_sha, head=head_sha, repo_dir=repo)
    check("git-diff-mapped", code == OK and lines == ["test_alpha"], f"got {code} {lines}")

    code, lines = select_targets(repo_map, base=head_sha, head=head_sha, repo_dir=repo)
    check("git-empty-diff-full", code == OK and lines == [FULL], f"got {code} {lines}")

    code, lines = select_targets(repo_map, base="does-not-exist-ref", head=head_sha, repo_dir=repo)
    check("git-unresolvable-rc2", code == USAGE_ERROR and lines == [FULL], f"got {code} {lines}")

    # Rename out of a !full area into a mapped one. With git's default rename
    # detection only the NEW (mapped) path is reported and selection would be
    # just `test_alpha` — a fail-open. --no-renames surfaces the old !full
    # path too, so the result must be FULL. Content is long enough for git to
    # detect the rename with detection on (the pre-fix behaviour).
    os.makedirs(os.path.join(repo, "config"))
    with open(os.path.join(repo, "config", "critical.yaml"), "w") as fh:
        fh.write("".join(f"line {i}\n" for i in range(20)))
    _git(repo, ["add", "."])
    _git(repo, ["commit", "-q", "-m", "add critical config"])
    pre_mv = _git(repo, ["rev-parse", "HEAD"]).strip()
    _git(repo, ["mv", "config/critical.yaml", "src/alpha/moved.yaml"])
    _git(repo, ["commit", "-q", "-m", "move critical config"])
    post_mv = _git(repo, ["rev-parse", "HEAD"]).strip()
    renamed_seen = _git(repo, ["diff", "-M", "--name-only", pre_mv, post_mv]).split()
    check("rename-precondition-git-detects-rename", renamed_seen == ["src/alpha/moved.yaml"],
          f"git default diff reported {renamed_seen} — test no longer exercises rename detection")
    rename_map = os.path.join(repo, "rename_map.tsv")
    _write_map(rename_map, ["src/alpha/**\ttest_alpha", "!full\tconfig/critical.*"])
    code, lines = select_targets(rename_map, base=pre_mv, head=post_mv, repo_dir=repo)
    check("rename-old-path-not-dropped", code == OK and lines == [FULL], f"got {code} {lines}")

    # Map self-check against the repo top level: the map lives at ci/map.tsv
    # and a row maps ci/** to a target, so without the top-level comparison
    # an absolute --map would select `test_ci` instead of forcing FULL.
    os.makedirs(os.path.join(repo, "ci"))
    ci_map = os.path.join(repo, "ci", "map.tsv")
    _write_map(ci_map, ["ci/**\ttest_ci", "src/**\ttest_src"])
    code, lines = select_targets(os.path.abspath(ci_map), changed_files=["ci/map.tsv"], repo_dir=repo)
    check("abs-map-vs-repo-relative-changed-file", code == OK and lines == [FULL], f"got {code} {lines}")
    code, lines = select_targets(os.path.abspath(ci_map), changed_files=["ci/other.txt"], repo_dir=repo)
    check("abs-map-sibling-still-mapped", code == OK and lines == ["test_ci"], f"got {code} {lines}")
    _git(repo, ["add", "ci/map.tsv"])
    _git(repo, ["commit", "-q", "-m", "add ci map"])
    pre_ci = _git(repo, ["rev-parse", "HEAD"]).strip()
    with open(ci_map, "a") as fh:
        fh.write("docs/**\ttest_docs\n")
    _git(repo, ["commit", "-q", "-am", "edit ci map"])
    post_ci = _git(repo, ["rev-parse", "HEAD"]).strip()
    code, lines = select_targets(os.path.abspath(ci_map), base=pre_ci, head=post_ci, repo_dir=repo)
    check("abs-map-git-diff-forces-full", code == OK and lines == [FULL], f"got {code} {lines}")


def _git(cwd: str, args: list[str]) -> str:
    proc = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0 and args and args[0] not in ("rev-parse",):
        raise RuntimeError(f"git {args} failed: {proc.stderr}")
    return proc.stdout


def _wait_for(path: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path):
            return True
        time.sleep(0.02)
    return os.path.exists(path)


def _lock_free(lock_dir: str, timeout: float = 2.0) -> bool:
    """True iff `lock_dir`'s lock can be acquired (and is immediately
    released again) within `timeout` — proof that nothing else holds it.
    """
    try:
        fd = acquire_lock(lock_dir, timeout)
    except LockTimeout:
        return False
    release_lock(fd)
    return True


def _selftest_lock(tmp: str, check) -> None:
    """Cross-lane flock lock: exclusivity, promptness on SIGKILL, timeout,
    exit-code propagation, no age-based release, release on normal exit, and
    the fail-closed path when `fcntl` is unavailable.
    """
    script_path = os.path.abspath(__file__)

    _selftest_lock_many_racers(tmp, check, script_path)
    _selftest_lock_release_on_exit(tmp, check, script_path)
    _selftest_lock_sigkill(tmp, check, script_path)
    _selftest_lock_timeout(tmp, check, script_path)
    _selftest_lock_exit_code(tmp, check, script_path)
    _selftest_lock_no_age_reclaim(tmp, check, script_path)
    _selftest_lock_no_fcntl(tmp, check)


def _selftest_lock_many_racers(tmp: str, check, script_path: str) -> None:
    """>= 4 concurrent `run`s, repeated over several rounds: at most one
    child is ever inside the lock.

    Each child appends `enter <id>` then `exit <id>` to one O_APPEND log and
    also keeps a per-holder marker in an `active/` dir while inside; entering
    with any other marker present is written as `overlap`. Exclusivity holds
    iff the log is a strict enter/exit alternation with matching ids, no
    `overlap` line, and one enter per racer. After every racer exits, the
    lock must be immediately acquirable again (release-on-exit, not just
    exclusivity).
    """
    racers = 5
    for rnd in range(3):
        base = os.path.join(tmp, f"race_{rnd}")
        os.makedirs(base)
        lock_dir = os.path.join(base, "lock")
        log = os.path.join(base, "log")
        active = os.path.join(base, "active")
        os.mkdir(active)
        child_tmpl = (
            "import os,sys,time\n"
            "rid=sys.argv[1]; log={log!r}; active={active!r}\n"
            "def w(s):\n"
            "    fd=os.open(log, os.O_WRONLY|os.O_APPEND|os.O_CREAT, 0o644); os.write(fd, s.encode()); os.close(fd)\n"
            "if os.listdir(active): w('overlap '+rid+'\\n')\n"
            "open(os.path.join(active, rid), 'w').close()\n"
            "w('enter '+rid+'\\n')\n"
            "time.sleep(0.1)\n"
            "w('exit '+rid+'\\n')\n"
            "os.remove(os.path.join(active, rid))\n"
        )
        child = child_tmpl.format(log=log, active=active)
        procs = [
            subprocess.Popen([
                sys.executable, script_path, "run", "--lock-dir", lock_dir,
                "--timeout", "60",
                "--", sys.executable, "-c", child, str(i),
            ])
            for i in range(racers)
        ]
        rcs = [p.wait(timeout=90) for p in procs]
        try:
            with open(log, encoding="utf-8") as fh:
                events = [ln.split() for ln in fh.read().splitlines() if ln.strip()]
        except OSError:
            events = []
        ok = all(len(e) == 2 for e in events) and len(events) == 2 * racers
        if ok:
            for i in range(0, len(events), 2):
                if events[i][0] != "enter" or events[i + 1] != ["exit", events[i][1]]:
                    ok = False
                    break
        entered = sorted(e[1] for e in events if e and e[0] == "enter")
        check(f"racers-{rnd}-exclusive",
              ok and not any(e and e[0] == "overlap" for e in events),
              f"log={events}")
        check(f"racers-{rnd}-all-ran",
              rcs == [0] * racers and entered == sorted(str(i) for i in range(racers)),
              f"rcs={rcs} entered={entered}")
        check(f"racers-{rnd}-lock-released-after", _lock_free(lock_dir))


def _selftest_lock_release_on_exit(tmp: str, check, script_path: str) -> None:
    """A holder that exits normally releases the lock immediately."""
    lock_dir = os.path.join(tmp, "lock_release")
    rc = subprocess.run([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "10", "--", sys.executable, "-c", "pass",
    ]).returncode
    check("release-normal-exit-rc0", rc == 0, f"got {rc}")
    check("release-normal-exit-unlocked", _lock_free(lock_dir))


def _selftest_lock_sigkill(tmp: str, check, script_path: str) -> None:
    """SIGKILLing the holder releases the lock immediately (kernel-owned):
    a waiter acquires promptly, with no stale-wait window to cross — because
    none exists.
    """
    lock_dir = os.path.join(tmp, "lock_sigkill")
    started = os.path.join(tmp, "sigkill_started")
    # Short-lived so the orphaned child (SIGKILL only hits the `run` parent,
    # not this grandchild) does not linger past the test.
    holder_child = f"import pathlib,time; pathlib.Path({started!r}).touch(); time.sleep(5)"
    holder = subprocess.Popen([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "30", "--", sys.executable, "-c", holder_child,
    ])
    started_ok = _wait_for(started, timeout=10)
    check("sigkill-holder-started", started_ok)

    holder.kill()  # SIGKILL the process holding the fd/flock
    holder.wait(timeout=10)

    t0 = time.monotonic()
    waiter_rc = subprocess.run([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "10", "--", sys.executable, "-c", "pass",
    ]).returncode
    elapsed = time.monotonic() - t0
    check("sigkill-waiter-acquired", waiter_rc == 0, f"rc={waiter_rc}")
    check("sigkill-waiter-prompt", elapsed < 3.0, f"elapsed={elapsed:.2f}s")


def _selftest_lock_timeout(tmp: str, check, script_path: str) -> None:
    """A held lock that never releases within --timeout -> 124, and the
    command is NEVER executed.
    """
    lock_dir = os.path.join(tmp, "lock_timeout")
    started = os.path.join(tmp, "timeout_started")
    release = os.path.join(tmp, "timeout_release")
    holder_child = (
        f"import pathlib,time; pathlib.Path({started!r}).touch(); "
        f"r=pathlib.Path({release!r})\n"
        f"while not r.exists(): time.sleep(0.02)\n"
    )
    holder = subprocess.Popen([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "30", "--", sys.executable, "-c", holder_child,
    ])
    try:
        check("timeout-holder-started", _wait_for(started, timeout=10))
        marker = os.path.join(tmp, "timeout_marker_should_not_exist")
        rc = subprocess.run([
            sys.executable, script_path, "run", "--lock-dir", lock_dir,
            "--timeout", "1",
            "--", sys.executable, "-c", f"open({marker!r}, 'w').close()",
        ]).returncode
        check("timeout-rc-124", rc == LOCK_TIMEOUT, f"got {rc}")
        check("timeout-command-not-run", not os.path.exists(marker),
              "command ran despite the lock never being acquired")
    finally:
        open(release, "w").close()
        holder.wait(timeout=15)


def _selftest_lock_exit_code(tmp: str, check, script_path: str) -> None:
    """The child's own exit code is propagated through `run`."""
    lock_dir = os.path.join(tmp, "lock_exit")
    rc = subprocess.run([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "10", "--", sys.executable, "-c", "import sys; sys.exit(7)",
    ]).returncode
    check("child-exit-propagated", rc == 7, f"got {rc}")


def _selftest_lock_no_age_reclaim(tmp: str, check, script_path: str) -> None:
    """A held lock survives past any age: there is no --stale-after and no
    reclaim logic left to trip. Back-dating the lock file's mtime far past
    any historical staleness window must have no effect.
    """
    lock_dir = os.path.join(tmp, "lock_no_age")
    started = os.path.join(tmp, "no_age_started")
    release = os.path.join(tmp, "no_age_release")
    holder_child = (
        f"import pathlib,time; pathlib.Path({started!r}).touch(); "
        f"r=pathlib.Path({release!r})\n"
        f"while not r.exists(): time.sleep(0.02)\n"
    )
    holder = subprocess.Popen([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "60", "--", sys.executable, "-c", holder_child,
    ])
    try:
        check("no-age-holder-started", _wait_for(started, timeout=10))
        past = time.time() - 10_000
        os.utime(_lock_file_path(lock_dir), (past, past))
        marker = os.path.join(tmp, "no_age_intruder_ran")
        rc = subprocess.run([
            sys.executable, script_path, "run", "--lock-dir", lock_dir,
            "--timeout", "1",
            "--", sys.executable, "-c", f"open({marker!r}, 'w').close()",
        ]).returncode
        check("no-age-intruder-times-out", rc == LOCK_TIMEOUT, f"rc={rc}")
        check("no-age-intruder-never-ran", not os.path.exists(marker))
    finally:
        open(release, "w").close()
        holder.wait(timeout=15)


def _selftest_lock_no_fcntl(tmp: str, check) -> None:
    """`fcntl` unavailable (e.g. Windows) -> exit 2, fail closed, command
    never runs. Exercised in-process by monkeypatching the module-level
    `fcntl` name rather than by faking a whole platform.
    """
    marker = os.path.join(tmp, "no_fcntl_marker")
    saved = globals()["fcntl"]
    globals()["fcntl"] = None
    try:
        rc = run_locked(
            os.path.join(tmp, "lock_no_fcntl"), 5.0,
            [sys.executable, "-c", f"open({marker!r}, 'w').close()"],
        )
    finally:
        globals()["fcntl"] = saved
    check("no-fcntl-exit-2", rc == USAGE_ERROR, f"rc={rc}")
    check("no-fcntl-command-not-run", not os.path.exists(marker))


if __name__ == "__main__":
    sys.exit(main())
