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
generated file, the integration branch) needs a real cross-process lock. On
macOS there is no `flock` for arbitrary directories usable portably across
lanes, so this uses `os.mkdir`, which is atomic on every POSIX filesystem:
exactly one caller's `mkdir` of the same path can succeed.

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
    definition a change no fixed row can vouch for.

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

run --lock-dir DIR [--stale-after SECONDS] [--timeout SECONDS] -- <cmd...>
    Serialize <cmd...> across lanes on one host using an atomic `os.mkdir`
    lock at DIR (never `flock` — no portable directory-flock on macOS). The
    lock directory holds `owner.json` (pid, host, UTC start ISO-8601). A
    waiter polls with bounded exponential backoff (capped, jittered) until it
    acquires the lock or --timeout elapses (default 120s) — on timeout, exits
    124 and NEVER runs <cmd...> unlocked. A waiter reclaims a STALE lock
    (owner pid dead on this host, or owner age > --stale-after, default
    900s) by an atomic rename-aside of the lock dir followed by its own
    `os.mkdir` — exactly one of any number of concurrent reclaimers can
    rename-away a given lock dir (the loser's `rename` raises because the
    source is already gone), so exactly one proceeds while the rest fall
    back to the normal poll loop. The lock is always released — in `finally`
    and in a SIGTERM/SIGINT handler — and the child's own exit code is
    propagated as this process's exit code.

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
import uuid
from datetime import datetime, timezone

OK = 0
USAGE_ERROR = 2
LOCK_TIMEOUT = 124

FULL = "FULL"

DEFAULT_STALE_AFTER = 900.0
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
    cmd += ["diff", "--name-only", base, head]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        raise MapError(f"git invocation failed: {exc}") from exc
    if proc.returncode != 0:
        raise MapError(
            f"git diff --name-only {base} {head} failed (exit "
            f"{proc.returncode}): {proc.stderr.strip()}"
        )
    return [line for line in proc.stdout.splitlines() if line.strip()]


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

    map_self = _normalize_path(map_path)
    force_full_globs = list(full_globs)

    for path in changed:
        if path == map_self:
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
# run — cross-lane serial lock
# --------------------------------------------------------------------------


class LockTimeout(Exception):
    """Raised internally when acquisition exceeds --timeout."""


def _dbg(msg: str) -> None:
    log = os.environ.get("SERIAL_GATE_DEBUG_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"{time.time():.6f} pid={os.getpid()} {msg}\n")


def _owner_path(lock_dir: str) -> str:
    return os.path.join(lock_dir, "owner.json")


def _write_owner(lock_dir: str) -> None:
    owner = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "start_utc": datetime.now(timezone.utc).isoformat(),
    }
    tmp = _owner_path(lock_dir) + f".tmp-{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(owner, fh)
    os.replace(tmp, _owner_path(lock_dir))


def _read_owner(lock_dir: str) -> dict | None:
    try:
        with open(_owner_path(lock_dir), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _is_stale(lock_dir: str, stale_after: float) -> bool:
    """A lock is stale iff its owner is provably gone or provably too old.

    Missing/unparsable `owner.json` is treated as "recently created, not yet
    written" rather than automatically stale — a partial write during
    another process's own acquisition must not be reclaimed out from under
    it just because the file briefly did not parse. Age is measured off the
    lock directory's own mtime, which exists the instant `os.mkdir` succeeds
    and survives a missing/corrupt owner file.
    """
    try:
        mtime = os.stat(lock_dir).st_mtime
    except OSError:
        return False  # dir vanished underneath us; treat as "not our problem"
    return _is_stale_info(mtime, _read_owner(lock_dir), stale_after)


def _is_stale_info(mtime: float, owner: dict | None, stale_after: float) -> bool:
    """Pure staleness verdict from an already-captured `(mtime, owner)` pair.

    Split out from `_is_stale` so `_reclaim` can re-run this EXACT check on
    data frozen by a successful `os.rename` (see `_reclaim`), instead of
    re-reading the live, still-mutable path — that split closes the races
    below, not just style.
    """
    age = time.time() - mtime
    if owner is not None and owner.get("host") == socket.gethostname():
        pid = owner.get("pid")
        if isinstance(pid, int):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True  # owner process is provably dead on this host
            except PermissionError:
                pass  # alive, just not ours to signal — fall through to age
    return age > stale_after


def _reclaim(lock_dir: str, stale_after: float) -> bool:
    """Atomically rename the (believed-stale) lock dir aside, and commit to
    removing it ONLY if a frozen re-check of the moved copy still says
    stale. Returns True iff this call actually removed a stale lock (the
    caller may then retry `os.mkdir` immediately).

    Two races this closes, both required for "exactly one reclaimer
    proceeds, and a live lock is never destroyed out from under its owner":

    1. Two waiters both see the same stale lock and both call this. POSIX
       `os.rename` removes the source name atomically, so only the first
       racer's `os.rename` can succeed; every later racer's `os.rename` on
       the now-vanished source raises and returns False immediately —
       never touching anything.
    2. The winner's pre-rename staleness read can be stale ITSELF: by the
       time its `os.rename` lands, a DIFFERENT process may already have
       reclaimed and replaced `lock_dir` with a brand-new, legitimately
       live lock (this is exactly what a second concurrent reclaimer of the
       same original stale dir would otherwise steal). So staleness is
       re-decided here on the data that just got moved into `aside` —
       which cannot change again once moved, because only this call holds
       that path — and if that re-check says "actually live," the moved
       copy is put straight back (own `os.rename`, which only succeeds if
       `lock_dir` is still empty) rather than deleted, so a live owner's
       lock is never destroyed by a loser's late rename.
    """
    aside = f"{lock_dir}.stale-{uuid.uuid4().hex}"
    try:
        os.rename(lock_dir, aside)
    except OSError as exc:
        _dbg(f"reclaim: rename-away FAILED {exc}")
        return False
    _dbg("reclaim: rename-away OK")

    try:
        mtime = os.stat(aside).st_mtime
    except OSError:
        return False  # can't happen (we just renamed it), but never crash
    owner = _read_owner(aside)

    if _is_stale_info(mtime, owner, stale_after):
        _dbg(f"reclaim: post-rename verdict STALE owner={owner}")
        _rmtree_best_effort(aside)
        return True

    # We raced ahead of a legitimate acquirer and stole its brand-new lock
    # by mistake. Put it back if the slot is still free; if a third party
    # has since claimed `lock_dir`, that claim is the linearizable outcome
    # and this stolen copy is simply discarded.
    _dbg(f"reclaim: post-rename verdict LIVE owner={owner} — restoring")
    try:
        os.rename(aside, lock_dir)
        _dbg("reclaim: restore OK")
    except OSError as exc:
        _dbg(f"reclaim: restore FAILED {exc} — discarding stolen live copy")
        _rmtree_best_effort(aside)
    return False


def _rmtree_best_effort(path: str) -> None:
    try:
        for name in os.listdir(path):
            try:
                os.remove(os.path.join(path, name))
            except OSError:
                pass
        os.rmdir(path)
    except OSError:
        pass


def acquire_lock(lock_dir: str, stale_after: float, timeout: float) -> None:
    """Block until this process holds `lock_dir`, or raise `LockTimeout`.

    Never returns while unlocked: every exit from this function other than
    the timeout raise means `os.mkdir(lock_dir)` just succeeded for this
    process.
    """
    deadline = time.monotonic() + timeout
    delay = _POLL_START
    while True:
        try:
            os.mkdir(lock_dir)
        except FileExistsError:
            _dbg("acquire: mkdir FileExistsError")
        else:
            _dbg("acquire: mkdir OK")
            try:
                _write_owner(lock_dir)
                _dbg("acquire: write_owner OK -> HOLD")
                return
            except OSError as exc:
                _dbg(f"acquire: write_owner FAILED {exc} — retry loop")
                # Lost a pathological race: lock_dir was reclaimed out from
                # under us between our mkdir and our own owner-file write.
                # Not a crash — just retry the whole acquire loop.
                pass

        if time.monotonic() >= deadline:
            raise LockTimeout(f"timed out after {timeout}s waiting for lock: {lock_dir}")

        stale = os.path.isdir(lock_dir) and _is_stale(lock_dir, stale_after)
        _dbg(f"acquire: stale-check={stale}")
        if stale:
            _reclaim(lock_dir, stale_after)  # win, lose, or bounce back — loop and retry mkdir
            continue

        time.sleep(min(delay, _POLL_CAP) + random.uniform(0, delay * 0.1))
        delay = min(delay * _POLL_BACKOFF, _POLL_CAP)


def release_lock(lock_dir: str) -> None:
    """Best-effort release. Safe to call even if the lock was never held or
    was already reclaimed by someone else (never raises).
    """
    _rmtree_best_effort(lock_dir)


def run_locked(lock_dir: str, stale_after: float, timeout: float, cmd: list[str]) -> int:
    """Acquire the lock, run `cmd`, release, and return `cmd`'s exit code.

    A SIGTERM/SIGINT while waiting or while the child runs still releases
    the lock: the handler raises `SystemExit`, which unwinds through the
    `finally` below exactly like any other exception.
    """
    acquired = {"value": False}

    def _on_signal(signum, _frame):
        raise SystemExit(128 + signum)

    old_term = signal.signal(signal.SIGTERM, _on_signal)
    old_int = signal.signal(signal.SIGINT, _on_signal)
    try:
        try:
            acquire_lock(lock_dir, stale_after, timeout)
            acquired["value"] = True
        except LockTimeout as exc:
            print(f"serial_gate: {exc}", file=sys.stderr)
            return LOCK_TIMEOUT
        proc = subprocess.run(cmd)
        return proc.returncode
    finally:
        if acquired["value"]:
            release_lock(lock_dir)
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
    return run_locked(args.lock_dir, args.stale_after, args.timeout, cmd)


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
    p_select.add_argument("--repo", help="run git in this directory (default: cwd)")
    p_select.add_argument(
        "--changed-file", action="append", default=[],
        help="a changed path (repeatable); bypasses git entirely",
    )

    p_run = sub.add_parser("run", help="serialize a command across lanes with a mkdir lock")
    p_run.add_argument("--lock-dir", required=True, help="lock directory path")
    p_run.add_argument("--stale-after", type=float, default=DEFAULT_STALE_AFTER,
                        help=f"seconds before an unresponsive owner's lock is reclaimable (default {DEFAULT_STALE_AFTER})")
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
    own proof that fail-closed selection and the mkdir lock actually fire on
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


def _git(cwd: str, args: list[str]) -> str:
    proc = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0 and args and args[0] not in ("rev-parse",):
        raise RuntimeError(f"git {args} failed: {proc.stderr}")
    return proc.stdout


def _selftest_lock(tmp: str, check) -> None:
    script_path = os.path.abspath(__file__)

    # 11) two concurrent `run`s: second waits until the first releases.
    # Ordering is proven with marker files gated on a release signal file,
    # never on a sleep duration.
    lock_dir = os.path.join(tmp, "lock_order")
    started_a = os.path.join(tmp, "a_started")
    release_a = os.path.join(tmp, "release_a")
    started_b = os.path.join(tmp, "b_started")

    waiter_a = (
        f"import pathlib,time; p=pathlib.Path({started_a!r}); p.touch(); "
        f"r=pathlib.Path({release_a!r})\n"
        f"while not r.exists(): time.sleep(0.02)\n"
    )
    waiter_b = f"import pathlib; pathlib.Path({started_b!r}).touch()"

    proc_a = subprocess.Popen([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "30", "--", sys.executable, "-c", waiter_a,
    ])
    _wait_for(started_a, timeout=10)

    proc_b = subprocess.Popen([
        sys.executable, script_path, "run", "--lock-dir", lock_dir,
        "--timeout", "30", "--", sys.executable, "-c", waiter_b,
    ])

    time.sleep(0.3)  # give B every chance to (wrongly) start while A holds the lock
    check("lock-order-b-waits", not os.path.exists(started_b),
          "B's child ran before A released the lock")

    open(release_a, "w").close()
    proc_a.wait(timeout=15)
    ok_b = _wait_for(started_b, timeout=10)
    proc_b.wait(timeout=15)
    check("lock-order-b-ran-after", ok_b, "B never ran after A released")
    check("lock-order-exit-codes", proc_a.returncode == 0 and proc_b.returncode == 0,
          f"a={proc_a.returncode} b={proc_b.returncode}")

    # 12) stale lock with a dead pid -> reclaimed (new owner runs immediately).
    lock_dir2 = os.path.join(tmp, "lock_stale")
    dead_proc = subprocess.Popen([sys.executable, "-c", "pass"])
    dead_pid = dead_proc.pid
    dead_proc.wait()
    os.mkdir(lock_dir2)
    with open(_owner_path(lock_dir2), "w") as fh:
        json.dump({"pid": dead_pid, "host": socket.gethostname(),
                   "start_utc": datetime.now(timezone.utc).isoformat()}, fh)
    marker = os.path.join(tmp, "stale_reclaim_ran")
    rc = subprocess.run([
        sys.executable, script_path, "run", "--lock-dir", lock_dir2,
        "--stale-after", "999999", "--timeout", "10",
        "--", sys.executable, "-c", f"open({marker!r}, 'w').close()",
    ]).returncode
    check("stale-dead-pid-reclaimed", rc == 0 and os.path.exists(marker), f"rc={rc}")

    # 13) two concurrent reclaimers of the SAME stale lock -> exactly one
    # proceeds at a time (ordering proof, not a timing guess).
    lock_dir3 = os.path.join(tmp, "lock_stale_race")
    dead_proc2 = subprocess.Popen([sys.executable, "-c", "pass"])
    dead_pid2 = dead_proc2.pid
    dead_proc2.wait()
    os.mkdir(lock_dir3)
    with open(_owner_path(lock_dir3), "w") as fh:
        json.dump({"pid": dead_pid2, "host": socket.gethostname(),
                   "start_utc": datetime.now(timezone.utc).isoformat()}, fh)

    # Both racers are symmetric: touch a started-file, then block on their
    # OWN release-file. Which of the two wins the post-reclaim `os.mkdir` is
    # a fair race (whichever process's reclaim attempt happens to fail
    # harmlessly and loops back to `os.mkdir` first still wins fairly — see
    # `_reclaim`'s docstring) and is NOT the property under test here. The
    # property under test is exclusivity: the loser's started-file must
    # never appear before the winner's release-file is created.
    started = {"c": os.path.join(tmp, "c_started"), "d": os.path.join(tmp, "d_started")}
    release = {"c": os.path.join(tmp, "release_c"), "d": os.path.join(tmp, "release_d")}
    waiter = {}
    for key in ("c", "d"):
        waiter[key] = (
            f"import pathlib,time; pathlib.Path({started[key]!r}).touch(); "
            f"r=pathlib.Path({release[key]!r})\n"
            f"while not r.exists(): time.sleep(0.02)\n"
        )

    # stale-after is deliberately large: the two waiters' shared contention is
    # over the DEAD-PID owner only (dead-pid staleness is unconditional, not
    # age-gated) — a small/zero stale-after would also make the WINNER's own
    # freshly-written, legitimately-live lock look instantly stale again and
    # spuriously re-trigger reclaim churn between the two racers.
    proc = {}
    for key in ("c", "d"):
        proc[key] = subprocess.Popen([
            sys.executable, script_path, "run", "--lock-dir", lock_dir3,
            "--stale-after", "999999", "--timeout", "30",
            "--", sys.executable, "-c", waiter[key],
        ])

    deadline = time.monotonic() + 10
    winner = None
    while time.monotonic() < deadline and winner is None:
        for key in ("c", "d"):
            if os.path.exists(started[key]):
                winner = key
                break
        if winner is None:
            time.sleep(0.02)
    loser = {"c": "d", "d": "c"}.get(winner)

    check("reclaim-race-someone-won", winner is not None, "neither racer's child ever started")
    time.sleep(0.3)
    check("reclaim-race-mutex", winner is not None and not os.path.exists(started[loser]),
          "both reclaimers' children ran concurrently")

    if winner is not None:
        open(release[winner], "w").close()
        proc[winner].wait(timeout=15)
        got_loser = _wait_for(started[loser], timeout=10)
        check("reclaim-race-second-ran", got_loser, "second reclaimer's child never ran")
        if got_loser:
            open(release[loser], "w").close()
        proc[loser].wait(timeout=15)

    # 14) child exit code propagated.
    lock_dir4 = os.path.join(tmp, "lock_exit")
    rc = subprocess.run([
        sys.executable, script_path, "run", "--lock-dir", lock_dir4,
        "--timeout", "10", "--", sys.executable, "-c", "import sys; sys.exit(7)",
    ]).returncode
    check("child-exit-propagated", rc == 7, f"got {rc}")

    # 15) timeout -> non-zero, and the command is NEVER executed.
    lock_dir5 = os.path.join(tmp, "lock_timeout")
    os.mkdir(lock_dir5)  # held forever (no owner.json => not stale within window)
    _write_owner(lock_dir5)
    marker2 = os.path.join(tmp, "timeout_marker_should_not_exist")
    rc = subprocess.run([
        sys.executable, script_path, "run", "--lock-dir", lock_dir5,
        "--stale-after", "999999", "--timeout", "1",
        "--", sys.executable, "-c", f"open({marker2!r}, 'w').close()",
    ]).returncode
    check("timeout-nonzero", rc != 0, f"got {rc}")
    check("timeout-command-not-run", not os.path.exists(marker2),
          "command ran despite the lock never being acquired")


def _wait_for(path: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path):
            return True
        time.sleep(0.02)
    return os.path.exists(path)


if __name__ == "__main__":
    sys.exit(main())
