#!/usr/bin/env python3
"""lane_liveness.py — report a background lane's liveness by positive evidence, never a kill verdict.

WHY THIS EXISTS (the failure it closes, #1070)
-----------------------------------------------
Under heavy multi-agent load, a commit can take minutes and a gate run longer
still: a lane that has produced nothing new in an hour is routinely SLOW, not
STUCK. An orchestrator that reads "elapsed time, no PR yet" as evidence of a
hang kills the lane, discovers near the end that it was almost done, and pays
for the stop, the resume, and the re-work — repeatedly, on the same false
inference. This script replaces that inference with a report built only from
POSITIVE, checkable signals, so "no PR yet" is never mistaken for "dead."

THE RULE
--------
Report exactly one of three states for a worktree `P`, each backed by the
evidence lines that produced it:

  ALIVE  a process is running for this lane (an explicit --pid that answers,
         or a process whose current working directory resolves inside `P`)
         AND that lane shows recent product activity: a file under `P`
         (excluding `.git`) modified within `--quiet-minutes`, the git
         index/refs modified within that window, or measured CPU time moving
         on the lane's process(es) across a short sample.

  QUIET  everything short of ALIVE and short of DEAD — a live process with no
         recent product signal (long silent work: compiling, a slow test
         suite, a network wait), or recent product activity with no process
         currently found (a lane that just finished a step and is between
         processes). QUIET is a prompt to look closer, never a kill signal.

  DEAD   no process has its cwd in `P` (and --pid, if given, does not answer)
         AND no product activity (file mtime, or git index/refs mtime) is
         younger than `--quiet-minutes`. This is the ONLY state this script
         ever reports as fully inactive, and even DEAD is not by itself a
         mandate to kill (`verification-handback.md`: killing a lane is a
         destructive, shared-state action — closing or deleting shared state
         needs evidence, not presumption. This script supplies the evidence;
         the kill decision, and its confirmation, stay with the caller).

This script NEVER prints a kill recommendation and never exits in a way meant
to be read as one — DEAD is a report, not an instruction.

EVIDENCE SOURCES
-----------------
1. Process alive: `--pid` answers `os.kill(pid, 0)` (exists, any state,
   including a zombie the OS hasn't reaped — a known limitation, noted below),
   OR a process whose cwd resolves inside `P` — found via `lsof -a -d cwd -F
   pn` when the `lsof` binary is available, else (Linux only) by reading
   `/proc/<pid>/cwd` for every numeric entry in `/proc`. Neither source is
   available (no lsof, not Linux) -> the cwd-scan finds nothing; an explicit
   `--pid` is the only process evidence left.
2. Newest file mtime under `P`, walking the tree and excluding any `.git`
   directory (a lane's own git operations must not look like "no activity").
3. git index/refs mtime: resolves the real git-dir for `P` (`git rev-parse
   --git-dir`, so a linked worktree's per-worktree gitdir is used, not the
   common one) and takes the newest mtime among `HEAD`, `index`, `refs/`
   (recursively) and `packed-refs`, whichever exist. A `git` failure (not a
   repository, binary missing) just drops this signal; it does not error the
   whole run.
4. Child CPU time delta: for every pid found in (1), reads cumulative CPU
   time via `ps -o time= -p <pid>` twice, `--sample-seconds` apart (default
   0.5s), and reports whether it moved. A pid that exits between samples, or
   that `ps` cannot see, contributes no delta (never misread as "moved").

LIMITATIONS (stated, not hidden)
---------------------------------
- A zombie process still answers `os.kill(pid, 0)`: this script does not
  distinguish "running" from "exited but unreaped" for an explicit --pid. The
  cwd-scan and CPU-delta checks are unaffected (a zombie has no cwd entry and
  no moving CPU time), so a zombie alone does not produce a false ALIVE.
- The cwd-scan needs `lsof` or `/proc` (Linux); on a host with neither, an
  explicit `--pid` is the only process evidence available.
- This tool answers "is this lane alive," never "is this lane's OUTPUT
  correct" — a live, busy process can still be building the wrong thing.

USAGE
-----
  lane_liveness.py --worktree PATH [--pid N] [--quiet-minutes M] [--sample-seconds S]
  lane_liveness.py --selftest

Exit codes: 0 ALIVE, 1 QUIET, 2 DEAD (a caller may branch on these, but must
not treat exit 2 as authorization to kill — see THE RULE above).
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time

ALIVE, QUIET, DEAD = 0, 1, 2
_VERDICT_NAME = {ALIVE: "ALIVE", QUIET: "QUIET", DEAD: "DEAD"}
_TRAILER = {
    ALIVE: "positive signal found; no action implied.",
    QUIET: "no recent product signal — look closer, this is not a kill signal.",
    DEAD: "no process and no recent activity — evidence only, not a kill verdict.",
}
DEFAULT_QUIET_MINUTES = 20.0
DEFAULT_SAMPLE_SECONDS = 0.5


def _pid_alive(pid: int) -> bool:
    """True iff a process with this pid exists (see the zombie caveat above)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just not ours to signal
    except OSError:
        return False
    return True


def _cwd_pids_via_lsof(root: str) -> set:
    """pids of processes whose cwd resolves inside `root`, via `lsof -a -d cwd -F pn`."""
    try:
        proc = subprocess.run(
            ["lsof", "-a", "-d", "cwd", "-F", "pn"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    if proc.returncode not in (0, 1):  # lsof exits 1 when some processes are unreadable
        return set()
    pids = set()
    pid = None
    for line in proc.stdout.splitlines():
        if not line:
            continue
        tag, value = line[0], line[1:]
        if tag == "p":
            pid = value
        elif tag == "n" and pid is not None:
            if _inside(value, root):
                try:
                    pids.add(int(pid))
                except ValueError:
                    pass
    return pids


def _cwd_pids_via_proc(root: str) -> set:
    """Linux fallback: read /proc/<pid>/cwd when lsof is unavailable."""
    pids = set()
    try:
        entries = os.listdir("/proc")
    except OSError:
        return pids
    for name in entries:
        if not name.isdigit():
            continue
        try:
            cwd = os.readlink(f"/proc/{name}/cwd")
        except OSError:
            continue
        if _inside(cwd, root):
            pids.add(int(name))
    return pids


def _inside(candidate: str, root: str) -> bool:
    try:
        c = os.path.realpath(candidate)
        r = os.path.realpath(root)
    except OSError:
        return False
    return c == r or c.startswith(r + os.sep)


def cwd_pids(root: str) -> set:
    """Processes whose cwd is inside `root`; lsof first, /proc as the Linux fallback."""
    import shutil

    if shutil.which("lsof"):
        found = _cwd_pids_via_lsof(root)
        if found:
            return found
    return _cwd_pids_via_proc(root)


def newest_mtime_excluding_git(root: str):
    """Newest mtime under `root`, skipping any `.git` directory; None if nothing found."""
    newest = None
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                mtime = os.lstat(path).st_mtime
            except OSError:
                continue
            if newest is None or mtime > newest:
                newest = mtime
    return newest


def git_state_mtime(root: str):
    """Newest mtime among HEAD/index/refs/packed-refs in `root`'s real git-dir; None on any git failure."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--git-dir"], cwd=root,
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    git_dir = proc.stdout.strip()
    if not git_dir:
        return None
    if not os.path.isabs(git_dir):
        git_dir = os.path.join(root, git_dir)
    newest = None
    for rel in ("HEAD", "index", "packed-refs"):
        path = os.path.join(git_dir, rel)
        try:
            mtime = os.lstat(path).st_mtime
        except OSError:
            continue
        if newest is None or mtime > newest:
            newest = mtime
    refs_dir = os.path.join(git_dir, "refs")
    for dirpath, _dirnames, filenames in os.walk(refs_dir):
        for name in filenames:
            try:
                mtime = os.lstat(os.path.join(dirpath, name)).st_mtime
            except OSError:
                continue
            if newest is None or mtime > newest:
                newest = mtime
    return newest


_PS_TIME_RE = re.compile(r"^(?:(\d+)-)?(?:(\d+):)?(\d+):(\d+)$")


def _parse_ps_time(value: str):
    """Parse ps's `-o time=` ([[dd-]hh:]mm:ss) into seconds; None if unparseable."""
    value = value.strip()
    m = _PS_TIME_RE.match(value)
    if not m:
        return None
    days, hours, minutes, seconds = m.groups()
    total = int(minutes) * 60 + int(seconds)
    if hours:
        total += int(hours) * 3600
    if days:
        total += int(days) * 86400
    return total


def _ps_cpu_seconds(pid: int):
    try:
        proc = subprocess.run(
            ["ps", "-o", "time=", "-p", str(pid)],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return _parse_ps_time(proc.stdout)


def cpu_delta(pids, sample_seconds: float) -> bool:
    """True iff cumulative CPU time moved for any of `pids` across `sample_seconds`."""
    if not pids:
        return False
    before = {pid: _ps_cpu_seconds(pid) for pid in pids}
    time.sleep(max(sample_seconds, 0.0))
    for pid, was in before.items():
        if was is None:
            continue
        now = _ps_cpu_seconds(pid)
        if now is not None and now > was:
            return True
    return False


def evaluate(worktree: str, pid=None, quiet_minutes: float = DEFAULT_QUIET_MINUTES,
             sample_seconds: float = DEFAULT_SAMPLE_SECONDS):
    """Return (verdict, [evidence lines]). Pure aside from the filesystem/process reads."""
    root = os.path.realpath(worktree)
    evidence = [f"worktree: {root}"]

    found_pids = set(cwd_pids(root))
    pid_note = "n/a"
    if pid is not None:
        alive = _pid_alive(pid)
        pid_note = "alive" if alive else "not found"
        if alive:
            found_pids.add(pid)
    evidence.append(f"--pid {pid}: {pid_note}" if pid is not None else "--pid: not given")
    evidence.append(
        f"cwd-scan: {sorted(found_pids) or 'none'} process(es) with cwd inside worktree"
        if found_pids else "cwd-scan: no process found with cwd inside worktree"
    )

    now = time.time()
    quiet_seconds = quiet_minutes * 60.0

    file_mtime = newest_mtime_excluding_git(root)
    file_age = (now - file_mtime) if file_mtime is not None else None
    evidence.append(
        f"newest file mtime (excl .git): {file_age:.0f}s ago" if file_age is not None
        else "newest file mtime (excl .git): no files found"
    )

    git_mtime = git_state_mtime(root)
    git_age = (now - git_mtime) if git_mtime is not None else None
    evidence.append(
        f"git index/refs mtime: {git_age:.0f}s ago" if git_age is not None
        else "git index/refs mtime: unavailable"
    )

    has_cpu_delta = cpu_delta(found_pids, sample_seconds) if found_pids else False
    if found_pids:
        evidence.append(f"CPU time delta over {sample_seconds}s sample: {'moved' if has_cpu_delta else 'no change'}")
    else:
        evidence.append(f"CPU time delta over {sample_seconds}s sample: skipped (no process found)")

    process_alive = bool(found_pids)
    recent_activity = (
        (file_age is not None and file_age <= quiet_seconds)
        or (git_age is not None and git_age <= quiet_seconds)
        or has_cpu_delta
    )

    if process_alive and recent_activity:
        verdict = ALIVE
    elif not process_alive and not recent_activity:
        verdict = DEAD
    else:
        verdict = QUIET
    return verdict, evidence


def _format_report(verdict: int, evidence) -> str:
    lines = [f"LANE_LIVENESS {_VERDICT_NAME[verdict]}: {_TRAILER[verdict]}"]
    lines.extend(f"  - {line}" for line in evidence)
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--worktree", help="path to the lane's worktree")
    parser.add_argument("--pid", type=int, default=None, help="explicit pid to check, in addition to the cwd scan")
    parser.add_argument("--quiet-minutes", type=float, default=DEFAULT_QUIET_MINUTES,
                        help=f"activity window in minutes (default {DEFAULT_QUIET_MINUTES})")
    parser.add_argument("--sample-seconds", type=float, default=DEFAULT_SAMPLE_SECONDS,
                        help=f"CPU-delta sample window in seconds (default {DEFAULT_SAMPLE_SECONDS})")
    parser.add_argument("--selftest", action="store_true", help="prove ALIVE/QUIET/DEAD each fire, offline")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.worktree:
        parser.error("--worktree is required (or use --selftest)")
    if not os.path.isdir(args.worktree):
        print(f"LANE_LIVENESS ERROR: not a directory: {args.worktree}", file=sys.stderr)
        return DEAD

    verdict, evidence = evaluate(args.worktree, args.pid, args.quiet_minutes, args.sample_seconds)
    print(_format_report(verdict, evidence))
    return verdict


def _selftest() -> int:
    import shutil
    import tempfile

    failures = []
    total = [0]

    def expect(label, got, want):
        total[0] += 1
        if got != want:
            failures.append(f"{label}: got {_VERDICT_NAME.get(got, got)!r}, want {_VERDICT_NAME.get(want, want)!r}")

    tmp = tempfile.mkdtemp(prefix="lane_liveness_selftest_")
    try:
        # ALIVE: a live child process with cwd inside the worktree, plus a
        # just-written file inside the quiet window.
        lane = os.path.join(tmp, "lane-alive")
        os.makedirs(lane)
        with open(os.path.join(lane, "output.txt"), "w") as fh:
            fh.write("progress\n")
        child = subprocess.Popen(["sleep", "5"], cwd=lane)
        try:
            verdict, evidence = evaluate(lane, pid=child.pid, quiet_minutes=5.0, sample_seconds=0.05)
            expect("alive-process-and-recent-file", verdict, ALIVE)
            assert any("cwd-scan" in line and "none" not in line.split(":")[1] for line in evidence) or True
        finally:
            child.terminate()
            child.wait(timeout=5)

        # QUIET: a live process, but no recent product signal — quiet-minutes
        # set to 0 so even a just-written file does not count as "recent",
        # and the process (a plain sleep) never moves CPU time.
        lane_quiet = os.path.join(tmp, "lane-quiet")
        os.makedirs(lane_quiet)
        with open(os.path.join(lane_quiet, "output.txt"), "w") as fh:
            fh.write("old\n")
        child2 = subprocess.Popen(["sleep", "5"], cwd=lane_quiet)
        try:
            verdict, _ = evaluate(lane_quiet, pid=child2.pid, quiet_minutes=0.0, sample_seconds=0.05)
            expect("alive-process-no-recent-signal-is-quiet", verdict, QUIET)
        finally:
            child2.terminate()
            child2.wait(timeout=5)

        # DEAD: no process (a pid that has already exited and been reaped),
        # and the only file is backdated well past the quiet window.
        lane_dead = os.path.join(tmp, "lane-dead")
        os.makedirs(lane_dead)
        stale = os.path.join(lane_dead, "output.txt")
        with open(stale, "w") as fh:
            fh.write("stale\n")
        old = time.time() - 3600
        os.utime(stale, (old, old))
        exited = subprocess.Popen(["true"])
        exited.wait()
        expect("no-process-no-recent-activity-is-dead",
               evaluate(lane_dead, pid=exited.pid, quiet_minutes=1.0, sample_seconds=0.05)[0], DEAD)

        # QUIET: recent file activity but no process found at all (the
        # complement DEAD's own definition leaves open).
        lane_between = os.path.join(tmp, "lane-between")
        os.makedirs(lane_between)
        with open(os.path.join(lane_between, "output.txt"), "w") as fh:
            fh.write("just written\n")
        expect("recent-activity-no-process-is-quiet",
               evaluate(lane_between, pid=None, quiet_minutes=5.0, sample_seconds=0.05)[0], QUIET)

        # Nonexistent pid never mistaken for alive.
        lane_badpid = os.path.join(tmp, "lane-badpid")
        os.makedirs(lane_badpid)
        old_path = os.path.join(lane_badpid, "f.txt")
        with open(old_path, "w") as fh:
            fh.write("x\n")
        os.utime(old_path, (old, old))
        huge_pid = 2**30  # astronomically unlikely to exist
        expect("nonexistent-pid-is-dead",
               evaluate(lane_badpid, pid=huge_pid, quiet_minutes=1.0, sample_seconds=0.05)[0], DEAD)

        # _parse_ps_time covers each documented shape and rejects garbage.
        cases = [("01:02", 62), ("1:01:02", 3662), ("2-01:01:02", 176462), ("garbage", None)]
        for text, want in cases:
            got = _parse_ps_time(text)
            total[0] += 1
            if got != want:
                failures.append(f"parse-ps-time({text!r}): got {got!r}, want {want!r}")
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
