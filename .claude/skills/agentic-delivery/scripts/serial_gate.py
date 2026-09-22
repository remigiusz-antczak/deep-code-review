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

run --lock-dir DIR [--stale-after SECONDS] [--timeout SECONDS] -- <cmd...>
    Serialize <cmd...> across lanes using an atomic `os.mkdir` lock at DIR
    (never `flock` — no portable directory-flock on macOS). A process HOLDS
    the lock only after both its `os.mkdir(DIR)` succeeded AND it created
    `DIR/owner.json` exclusively (`O_CREAT|O_EXCL`) holding its pid, host,
    UTC start (ISO-8601), and a random per-acquisition token. A waiter polls
    with bounded exponential backoff (capped, jittered) until it acquires the
    lock or --timeout elapses (default 120s) — on timeout, exits 124 and
    NEVER runs <cmd...> unlocked. The child's own exit code is propagated.

    STALENESS — exactly when a held lock may be reclaimed:
      * owner on THIS host: stale only if its pid is provably dead
        (`os.kill(pid, 0)` raises ProcessLookupError). A live same-host owner
        is NEVER stale, however long it runs — --stale-after does not apply.
      * owner on ANOTHER host (a shared filesystem; its pid cannot be probed
        from here): stale when the lock directory's mtime is older than
        --stale-after (default 900s). A foreign owner that legitimately runs
        longer than --stale-after WILL be reclaimed, and the age is measured
        against this host's clock, so set --stale-after well above both the
        longest run and any clock skew.
      * lock dir with no readable `owner.json`: an acquirer between its mkdir
        and its owner write. Live for a 30s grace measured from the dir
        mtime; only after that is it treated as an abandoned acquisition.

    RECLAIM — a waiter that sees a stale lock takes a short reclaim mutex
    (atomic `os.mkdir` of `DIR.reclaim`; a mutex older than 10s is treated
    as left by a dead reclaimer and removed). Under it, it re-reads
    `owner.json` and proceeds only if the SAME token is still there and still
    stale. The commit point is an atomic `os.rename` of `owner.json` to a
    unique aside name followed by a re-check of the moved file's token: two
    reclaimers can never both claim one owner file, and a claim that turns
    out to hold a different token (a new owner raced in) is put back with
    `os.link` (which never overwrites) and nothing is removed. An owner-less
    stale dir is removed with `os.rmdir` only, which fails harmlessly if an
    acquirer has since written its owner file (side files a dead reclaimer
    left behind are restored if they still name a live owner, else deleted).

    RELEASE — in `finally` and on SIGTERM/SIGINT, the holder removes DIR only
    if `owner.json` still carries its own pid AND token; a process whose lock
    was reclaimed never deletes its successor's lock.

    WHAT THIS DOES NOT GUARANTEE (residual assumptions, stated plainly):
      * an acquirer must not stall longer than the 30s grace between its
        mkdir and its owner write — a stall that long lets its dir be
        reclaimed as abandoned;
      * pid reuse: if a dead owner's pid is reused by an unrelated live
        process, the lock looks live and waiters time out (exit 124, fail
        closed — never a second holder); remove DIR by hand after checking;
      * the foreign-host age rule above.

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
import secrets
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
# An owner-less lock dir (acquirer between mkdir and its owner write) is live
# for this long, by dir mtime; only then is it an abandoned acquisition.
_OWNERLESS_GRACE = 30.0
# A reclaim mutex older than this was left by a reclaimer that died.
_RECLAIM_MUTEX_STALE = 10.0


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


def _reclaim_mutex_path(lock_dir: str) -> str:
    return lock_dir.rstrip("/\\") + ".reclaim"


def _write_owner(lock_dir: str) -> str:
    """Create `owner.json` EXCLUSIVELY and return this acquisition's token.

    `O_CREAT|O_EXCL` means the write can never clobber another process's
    owner file: if one already exists (an acquirer that raced into the same
    directory incarnation), this raises FileExistsError and the caller does
    not hold the lock. Raises OSError (e.g. FileNotFoundError) if `lock_dir`
    vanished between the caller's mkdir and this write.
    """
    token = secrets.token_hex(16)
    owner = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "start_utc": datetime.now(timezone.utc).isoformat(),
        "token": token,
    }
    fd = os.open(_owner_path(lock_dir), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(owner, fh)
    return token


def _read_owner(path_dir_or_file: str) -> dict | None:
    """Parse an owner file (given its lock dir, or the file path itself).

    Returns None when the file is missing, unreadable, not valid JSON, or not
    a JSON object — every one of which the staleness verdict treats as an
    acquirer that has not finished writing yet (grace), never as proof of a
    dead owner.
    """
    path = path_dir_or_file
    if os.path.isdir(path):
        path = _owner_path(path)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _pid_alive(pid: int) -> bool:
    """True unless `pid` is provably dead on this host.

    `PermissionError` means the process exists but belongs to another user —
    alive. Only `ProcessLookupError` proves death.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return True  # unknown error: fail closed (treat as alive)
    return True


def _stale_verdict(owner: dict | None, dir_mtime: float, stale_after: float,
                   now: float | None = None) -> bool:
    """Pure staleness rule (see the module docstring, STALENESS).

    * no parsable owner (or no integer pid): stale only after
      `_OWNERLESS_GRACE` seconds of directory age — an acquirer mid-write is
      live;
    * same-host owner: stale iff its pid is provably dead — age is never
      consulted, so a long-running live owner is never reclaimed;
    * foreign-host owner: stale iff directory age exceeds `stale_after`.
    """
    now = time.time() if now is None else now
    age = now - dir_mtime
    if owner is None or not isinstance(owner.get("pid"), int):
        return age > _OWNERLESS_GRACE
    if owner.get("host") == socket.gethostname():
        return not _pid_alive(owner["pid"])
    return age > stale_after


def _snapshot(lock_dir: str) -> tuple[float, dict | None] | None:
    """`(dir_mtime, owner)` for `lock_dir`, or None if it does not exist."""
    try:
        mtime = os.stat(lock_dir).st_mtime
    except OSError:
        return None
    return mtime, _read_owner(lock_dir)


def _is_stale(lock_dir: str, stale_after: float) -> bool:
    """Staleness verdict for the lock dir as it is right now (False if absent)."""
    snap = _snapshot(lock_dir)
    if snap is None:
        return False
    return _stale_verdict(snap[1], snap[0], stale_after)


def _take_reclaim_mutex(lock_dir: str) -> bool:
    """Try once to take the short reclaim mutex; True iff taken.

    The mutex is an empty directory created with atomic `os.mkdir`. One left
    behind by a reclaimer that died mid-reclaim (older than
    `_RECLAIM_MUTEX_STALE` seconds) is removed with `os.rmdir` and the take is
    retried once. The mutex only narrows contention; correctness does not
    depend on it being exclusive, because `_reclaim`'s commit point is the
    atomic owner-file rename (see there).
    """
    mutex = _reclaim_mutex_path(lock_dir)
    for _ in range(2):
        try:
            os.mkdir(mutex)
            return True
        except FileExistsError:
            try:
                age = time.time() - os.stat(mutex).st_mtime
            except OSError:
                continue  # vanished between mkdir and stat: retry the mkdir
            if age <= _RECLAIM_MUTEX_STALE:
                return False
            try:
                os.rmdir(mutex)
            except OSError:
                return False
        except OSError:
            return False
    return False


def _drop_reclaim_mutex(lock_dir: str) -> None:
    try:
        os.rmdir(_reclaim_mutex_path(lock_dir))
    except OSError:
        pass


def _restore_or_clear_leftovers(lock_dir: str, stale_after: float) -> bool:
    """Deal with `owner.json.*` side files in an owner-less lock dir.

    Called only under the reclaim mutex, so any such file was left by a
    reclaimer (or a pre-token release of this tool) that died mid-operation.
    If one still names a LIVE owner, it is put back as `owner.json` (with
    `os.link`, which never overwrites) and True is returned: the lock is
    live and must not be removed. Every other side file is deleted so the
    following `os.rmdir` can succeed. Returns False when nothing was
    restored.
    """
    try:
        names = os.listdir(lock_dir)
    except OSError:
        return False
    now = time.time()
    for name in names:
        if not name.startswith("owner.json."):
            continue
        path = os.path.join(lock_dir, name)
        leftover = _read_owner(path)
        try:
            leftover_mtime = os.stat(path).st_mtime
        except OSError:
            continue
        if (leftover is not None and isinstance(leftover.get("pid"), int)
                and not _stale_verdict(leftover, leftover_mtime, stale_after, now)):
            try:
                os.link(path, _owner_path(lock_dir))
            except OSError:
                pass
            try:
                os.remove(path)
            except OSError:
                pass
            return True
        try:
            os.remove(path)
        except OSError:
            pass
    return False


def _reclaim(lock_dir: str, stale_after: float) -> bool:
    """Remove `lock_dir` iff it is stale; True iff this call removed it.

    Under the reclaim mutex:
      1. Re-snapshot. Not stale any more (or gone) -> do nothing.
      2. Owner-less stale dir (abandoned acquisition): `os.rmdir` only. If an
         acquirer wrote its owner file meanwhile, rmdir fails ENOTEMPTY and
         the live lock is left alone.
      3. Owned stale dir: atomically `os.rename` `owner.json` to a unique
         aside name. Only one caller can move a given file; the rest get
         FileNotFoundError. Then re-read the MOVED file: if its token is not
         the token judged stale in step 1 (a new owner raced in), put it
         back with `os.link` (never overwrites) and stop. Otherwise delete
         the aside file and `os.rmdir` the now-empty lock dir.
    """
    if not _take_reclaim_mutex(lock_dir):
        _dbg("reclaim: mutex busy")
        return False
    try:
        snap = _snapshot(lock_dir)
        if snap is None:
            return False
        mtime, owner = snap
        if not _stale_verdict(owner, mtime, stale_after):
            _dbg(f"reclaim: re-check LIVE owner={owner}")
            return False

        if owner is None or not isinstance(owner.get("pid"), int):
            if _restore_or_clear_leftovers(lock_dir, stale_after):
                return False
            try:
                os.rmdir(lock_dir)
            except OSError as exc:
                _dbg(f"reclaim: owner-less rmdir refused {exc}")
                return False
            _dbg("reclaim: removed abandoned owner-less dir")
            return True

        stale_token = owner.get("token")
        aside = os.path.join(lock_dir, f"owner.json.reclaim-{uuid.uuid4().hex}")
        try:
            os.rename(_owner_path(lock_dir), aside)
        except OSError as exc:
            _dbg(f"reclaim: claim rename lost {exc}")
            return False
        moved = _read_owner(aside)
        if moved is None or moved.get("token") != stale_token:
            _dbg(f"reclaim: claimed a DIFFERENT owner {moved} — restoring")
            try:
                os.link(aside, _owner_path(lock_dir))
            except OSError as exc:
                _dbg(f"reclaim: restore refused {exc}")
            try:
                os.remove(aside)
            except OSError:
                pass
            return False
        try:
            os.remove(aside)
        except OSError:
            pass
        try:
            os.rmdir(lock_dir)
        except OSError as exc:
            _dbg(f"reclaim: rmdir after claim refused {exc}")
            return False
        _dbg(f"reclaim: removed stale owner={owner}")
        return True
    finally:
        _drop_reclaim_mutex(lock_dir)


def acquire_lock(lock_dir: str, stale_after: float, timeout: float) -> str:
    """Block until this process holds `lock_dir`; return its owner token.

    Raises `LockTimeout` once `timeout` elapses. Never returns while unlocked:
    a return means this process's `os.mkdir(lock_dir)` succeeded AND its
    exclusive `owner.json` write succeeded.
    """
    deadline = time.monotonic() + timeout
    delay = _POLL_START
    while True:
        try:
            os.mkdir(lock_dir)
        except FileExistsError:
            _dbg("acquire: mkdir FileExistsError")
        else:
            try:
                token = _write_owner(lock_dir)
                _dbg("acquire: HOLD")
                return token
            except OSError as exc:
                # Another acquirer already owns this directory incarnation,
                # or it was removed under us: we do NOT hold it. Never delete
                # anything here — just retry.
                _dbg(f"acquire: owner write refused {exc}")

        if time.monotonic() >= deadline:
            raise LockTimeout(f"timed out after {timeout}s waiting for lock: {lock_dir}")

        if _is_stale(lock_dir, stale_after) and _reclaim(lock_dir, stale_after):
            continue  # removed a stale lock: retry mkdir immediately

        time.sleep(min(delay, _POLL_CAP) + random.uniform(0, delay * 0.1))
        delay = min(delay * _POLL_BACKOFF, _POLL_CAP)


def release_lock(lock_dir: str, token: str) -> bool:
    """Release `lock_dir` iff this process still owns it; True iff removed.

    Removes the lock only when `owner.json` carries BOTH this process's pid
    and `token`. A process whose lock was reclaimed (and possibly re-acquired
    by a successor) leaves the successor's lock untouched. Never raises.
    """
    owner = _read_owner(lock_dir)
    if owner is None or owner.get("pid") != os.getpid() or owner.get("token") != token:
        _dbg(f"release: not ours (owner={owner}) — leaving it")
        return False
    try:
        os.remove(_owner_path(lock_dir))
    except OSError:
        return False
    try:
        os.rmdir(lock_dir)
    except OSError:
        pass  # an acquirer already wrote into the dir: it is theirs now
    return True


def run_locked(lock_dir: str, stale_after: float, timeout: float, cmd: list[str]) -> int:
    """Acquire the lock, run `cmd`, release, and return `cmd`'s exit code.

    A SIGTERM/SIGINT while waiting or while the child runs still releases
    the lock: the handler raises `SystemExit`, which unwinds through the
    `finally` below exactly like any other exception.
    """
    held: dict[str, str | None] = {"token": None}

    def _on_signal(signum, _frame):
        raise SystemExit(128 + signum)

    old_term = signal.signal(signal.SIGTERM, _on_signal)
    old_int = signal.signal(signal.SIGINT, _on_signal)
    try:
        try:
            held["token"] = acquire_lock(lock_dir, stale_after, timeout)
        except LockTimeout as exc:
            print(f"serial_gate: {exc}", file=sys.stderr)
            return LOCK_TIMEOUT
        proc = subprocess.run(cmd)
        return proc.returncode
    finally:
        if held["token"] is not None:
            release_lock(lock_dir, held["token"])
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
    p_select.add_argument("--repo", help="run git in this directory (default: cwd); also locates the repo top level for the map self-check")
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

    # stale-after is deliberately tiny: the dead-pid owner is reclaimable
    # regardless of age, and the WINNER's own live same-host lock must stay
    # un-reclaimable even though it is instantly "older" than stale-after
    # (same-host owners are never age-stale).
    proc = {}
    for key in ("c", "d"):
        proc[key] = subprocess.Popen([
            sys.executable, script_path, "run", "--lock-dir", lock_dir3,
            "--stale-after", "0.01", "--timeout", "30",
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
    os.mkdir(lock_dir5)  # held by this (live) selftest process for the whole case
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

    _selftest_lock_verdicts(tmp, check)
    _selftest_lock_release(tmp, check)
    _selftest_lock_live_owner_not_aged_out(tmp, check, script_path)
    _selftest_lock_many_racers(tmp, check, script_path)


def _dead_pid() -> int:
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()
    return proc.pid


def _plant_owner(lock_dir: str, owner: dict, age: float = 0.0) -> None:
    """Create `lock_dir` with an owner file, then back-date the dir mtime."""
    os.mkdir(lock_dir)
    with open(_owner_path(lock_dir), "w", encoding="utf-8") as fh:
        json.dump(owner, fh)
    if age:
        past = time.time() - age
        os.utime(lock_dir, (past, past))


def _selftest_lock_verdicts(tmp: str, check) -> None:
    """Pure staleness rules plus the reclaim branches that need no racing."""
    host = socket.gethostname()
    ancient = 0.0  # epoch: older than any stale-after
    live_here = {"pid": os.getpid(), "host": host, "token": "t-live"}
    check("verdict-live-same-host-never-age-stale",
          _stale_verdict(live_here, ancient, stale_after=1.0) is False)
    check("verdict-dead-same-host-stale",
          _stale_verdict({"pid": _dead_pid(), "host": host, "token": "t"}, time.time(), 1e9) is True)
    foreign = {"pid": 1, "host": "other-host.example", "token": "t-f"}
    check("verdict-foreign-fresh-live", _stale_verdict(foreign, time.time(), 60.0) is False)
    check("verdict-foreign-aged-stale", _stale_verdict(foreign, time.time() - 120, 60.0) is True)
    check("verdict-ownerless-in-grace-live",
          _stale_verdict(None, time.time() - (_OWNERLESS_GRACE - 5), 0.0) is False)
    check("verdict-ownerless-past-grace-stale",
          _stale_verdict(None, time.time() - (_OWNERLESS_GRACE + 5), 1e9) is True)

    # Owner-less dir inside the grace window: an acquirer mid-write. Never
    # reclaimed, even with stale-after 0.
    d = os.path.join(tmp, "v_ownerless_fresh")
    os.mkdir(d)
    check("reclaim-ownerless-in-grace-refused", _reclaim(d, 0.0) is False and os.path.isdir(d))
    past = time.time() - (_OWNERLESS_GRACE + 5)
    os.utime(d, (past, past))
    check("reclaim-ownerless-past-grace-removed", _reclaim(d, 0.0) is True and not os.path.exists(d))

    # Live same-host owner with an ancient dir: never reclaimed.
    d = os.path.join(tmp, "v_live_ancient")
    _plant_owner(d, live_here, age=10_000)
    check("reclaim-live-same-host-ancient-refused",
          _reclaim(d, 1.0) is False and _read_owner(d) == live_here)

    # Foreign-host owner: fresh is kept, aged is reclaimed.
    d = os.path.join(tmp, "v_foreign")
    _plant_owner(d, foreign)
    check("reclaim-foreign-fresh-refused", _reclaim(d, 60.0) is False and os.path.isdir(d))
    past = time.time() - 120
    os.utime(d, (past, past))
    check("reclaim-foreign-aged-removed", _reclaim(d, 60.0) is True and not os.path.exists(d))

    # A fresh reclaim mutex (another reclaimer at work) blocks; an old one
    # (a reclaimer that died) is broken and the reclaim proceeds.
    d = os.path.join(tmp, "v_mutex")
    _plant_owner(d, {"pid": _dead_pid(), "host": host, "token": "t-dead"})
    os.mkdir(_reclaim_mutex_path(d))
    check("reclaim-fresh-mutex-blocks", _reclaim(d, 1e9) is False and os.path.isdir(d))
    past = time.time() - (_RECLAIM_MUTEX_STALE + 5)
    os.utime(_reclaim_mutex_path(d), (past, past))
    check("reclaim-dead-mutex-broken", _reclaim(d, 1e9) is True and not os.path.exists(d)
          and not os.path.exists(_reclaim_mutex_path(d)))

    # A reclaimer that died after moving a LIVE owner's file aside leaves an
    # owner-less dir; the next reclaim must restore that owner, not delete it.
    d = os.path.join(tmp, "v_leftover_live")
    os.mkdir(d)
    with open(os.path.join(d, "owner.json.reclaim-deadbeef"), "w", encoding="utf-8") as fh:
        json.dump(live_here, fh)
    past = time.time() - (_OWNERLESS_GRACE + 5)
    os.utime(d, (past, past))
    check("reclaim-leftover-live-owner-restored",
          _reclaim(d, 1.0) is False and _read_owner(d) == live_here)


def _selftest_lock_release(tmp: str, check) -> None:
    """Release deletes only this process's own lock (pid AND token)."""
    d = os.path.join(tmp, "rel_own")
    token = acquire_lock(d, stale_after=1e9, timeout=5)
    check("release-wrong-token-refused", release_lock(d, "not-" + token) is False and os.path.isdir(d))
    check("release-own-lock-removed", release_lock(d, token) is True and not os.path.exists(d))

    # Same token but a different pid in the file: not ours, keep it.
    d = os.path.join(tmp, "rel_pid")
    _plant_owner(d, {"pid": os.getppid(), "host": socket.gethostname(), "token": "shared"})
    check("release-wrong-pid-refused", release_lock(d, "shared") is False and os.path.isdir(d))

    # A holder whose lock was reclaimed and re-acquired by a successor must
    # not delete the successor's lock on its own (late) release.
    d = os.path.join(tmp, "rel_successor")
    old_token = acquire_lock(d, stale_after=1e9, timeout=5)
    os.remove(_owner_path(d))
    os.rmdir(d)  # simulate the reclaim of the old holder's lock
    successor = {"pid": os.getppid(), "host": socket.gethostname(), "token": "successor"}
    _plant_owner(d, successor)
    check("release-late-holder-keeps-successor",
          release_lock(d, old_token) is False and _read_owner(d) == successor)


def _selftest_lock_live_owner_not_aged_out(tmp: str, check, script_path: str) -> None:
    """A live same-host owner running far past --stale-after keeps the lock."""
    lock = os.path.join(tmp, "live_long")
    started = os.path.join(tmp, "live_long_started")
    release = os.path.join(tmp, "live_long_release")
    marker = os.path.join(tmp, "live_long_intruder_ran")
    holder_child = (
        f"import pathlib,time; pathlib.Path({started!r}).touch(); "
        f"r=pathlib.Path({release!r})\n"
        f"while not r.exists(): time.sleep(0.02)\n"
    )
    holder = subprocess.Popen([
        sys.executable, script_path, "run", "--lock-dir", lock,
        "--stale-after", "0.1", "--timeout", "30", "--", sys.executable, "-c", holder_child,
    ])
    try:
        check("live-long-holder-started", _wait_for(started, timeout=10))
        owner_before = _read_owner(lock)
        time.sleep(0.3)  # the holder is now well past --stale-after
        rc = subprocess.run([
            sys.executable, script_path, "run", "--lock-dir", lock,
            "--stale-after", "0.1", "--timeout", "1.5",
            "--", sys.executable, "-c", f"open({marker!r}, 'w').close()",
        ], stderr=subprocess.DEVNULL).returncode
        check("live-long-intruder-timed-out", rc == LOCK_TIMEOUT, f"rc={rc}")
        check("live-long-intruder-never-ran", not os.path.exists(marker))
        check("live-long-owner-unchanged",
              owner_before is not None and _read_owner(lock) == owner_before,
              f"before={owner_before} after={_read_owner(lock)}")
    finally:
        open(release, "w").close()
        holder.wait(timeout=15)
    check("live-long-holder-released", holder.returncode == 0 and not os.path.exists(lock),
          f"rc={holder.returncode}")


def _selftest_lock_many_racers(tmp: str, check, script_path: str) -> None:
    """>= 4 concurrent `run`s, repeated, over clean / dead-pid / owner-less /
    aged-foreign starting states: at most one child is ever inside the lock.

    Each child appends `enter <id>` then `exit <id>` to one O_APPEND log and
    also keeps a per-holder marker in an `active/` dir while inside; entering
    with any other marker present is written as `overlap`. Exclusivity holds
    iff the log is a strict enter/exit alternation with matching ids, no
    `overlap` line, and one enter per racer. stale-after is tiny so any
    regression to age-based reclaim of a live same-host owner shows up here.
    """
    racers = 5
    host = socket.gethostname()
    seeds = ["clean", "dead-pid", "ownerless-aged", "foreign-aged", "clean", "dead-pid"]
    for rnd, seed in enumerate(seeds):
        base = os.path.join(tmp, f"race_{rnd}")
        os.makedirs(base)
        lock = os.path.join(base, "lock")
        log = os.path.join(base, "log")
        active = os.path.join(base, "active")
        os.mkdir(active)
        if seed == "dead-pid":
            _plant_owner(lock, {"pid": _dead_pid(), "host": host, "token": "t-dead"})
        elif seed == "ownerless-aged":
            os.mkdir(lock)
            past = time.time() - (_OWNERLESS_GRACE + 5)
            os.utime(lock, (past, past))
        elif seed == "foreign-aged":
            _plant_owner(lock, {"pid": 1, "host": "other-host.example", "token": "t-f"}, age=10_000)
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
                sys.executable, script_path, "run", "--lock-dir", lock,
                "--stale-after", "0.01", "--timeout", "60",
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
        check(f"racers-{seed}-{rnd}-exclusive",
              ok and not any(e and e[0] == "overlap" for e in events),
              f"log={events}")
        check(f"racers-{seed}-{rnd}-all-ran",
              rcs == [0] * racers and entered == sorted(str(i) for i in range(racers)),
              f"rcs={rcs} entered={entered}")
        check(f"racers-{seed}-{rnd}-lock-released", not os.path.exists(lock))


def _wait_for(path: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(path):
            return True
        time.sleep(0.02)
    return os.path.exists(path)


if __name__ == "__main__":
    sys.exit(main())
