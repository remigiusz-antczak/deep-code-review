#!/usr/bin/env python3
"""restore_ledger.py — classify every branch after a VCS history-rewrite incident. Never pushes.

WHY THIS EXISTS (#1136): after a forced-update on a protected branch, a human
restorer facing ~20 lane branches cannot safely guess, per branch, whether its
head still needs restoring or already moved on legitimately. Guessing wrong
either re-applies a rewrite that was already fixed, or skips a branch that is
still sitting on the bad history. This script replaces the guess with one
classification per ref, backed by a pre-incident mirror and the current
remote state, plus the exact command to run — the human (or the restore step
in `references/incident-response.md`) still runs that command; this script
never does.

INPUTS
------
  --mirror DIR              a `git clone --mirror` (or any repo with full
                             history) taken BEFORE the incident — the trusted,
                             frozen baseline. Only its refs/heads/* are read.
  --current-file FILE       `git ls-remote` output (or `sha<TAB>ref` lines)
                             describing the CURRENT remote state, read
                             offline — no network.
  --current-remote SRC      a remote URL or local path; this script runs
                             `git ls-remote --heads SRC` itself (the one
                             network read this script performs) AND, only for
                             a ref whose tip differs from the mirror, fetches
                             that one object into the mirror under a scratch
                             ref (`refs/dcr-restore-check/*`, deleted again
                             after) to test ancestry. Still never a push.
Exactly one of --current-file / --current-remote is required.

CLASSIFICATION (per ref, comparing mirror tip to current tip)
---------------------------------------------------------------
  UNCHANGED_ORIGINAL  same sha in both — nothing to do.
  NEW_SINCE           ref exists only in the current state — created after
                       the backup; not evaluated against the mirror.
  DELETED             ref exists only in the mirror — missing on the remote
                       now (the rewrite, or an unrelated deletion).
  CHANGED_SINCE       different sha, and the mirror's tip IS an ancestor of
                       the current tip — legitimate forward progress since
                       the backup; nothing to restore.
  STILL_REWRITTEN     different sha, and the mirror's tip is NOT an ancestor
                       of the current tip (a real divergence) — OR ancestry
                       could not be verified at all (no remote/object access,
                       e.g. --current-file with no fetchable source). Fails
                       CLOSED to this state: an unverifiable divergence is
                       treated as still needing restore-review, never silently
                       waved through as CHANGED_SINCE.

Each row's suggested command is printed, never run.

EXIT CODES: 0 nothing needs restoring (every row UNCHANGED_ORIGINAL /
CHANGED_SINCE); 1 at least one STILL_REWRITTEN, DELETED, or NEW_SINCE row
(action needed); 2 usage or I/O error (bad --mirror, unreadable --current-file,
an unresolvable --current-remote).
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile

UNCHANGED, NEW_SINCE, DELETED, CHANGED_SINCE, STILL_REWRITTEN = (
    "UNCHANGED_ORIGINAL", "NEW_SINCE", "DELETED", "CHANGED_SINCE", "STILL_REWRITTEN",
)
NEEDS_ACTION = {DELETED, STILL_REWRITTEN, NEW_SINCE}
HEX_RE = re.compile(r"^[0-9a-f]{7,64}$")
SCRATCH_PREFIX = "refs/dcr-restore-check/"
GIT_TIMEOUT = 60.0


class LedgerError(Exception):
    """A condition that makes the ledger un-buildable (always exit 2)."""


def _git(args, cwd=None, timeout=GIT_TIMEOUT, check_ok=True):
    """Run one git command non-interactively; a hang past `timeout`s raises LedgerError."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True,
                               timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise LedgerError(f"git {' '.join(args)} timed out after {timeout:g}s")
    except OSError as exc:
        raise LedgerError(f"git could not be started: {exc}")
    if check_ok and proc.returncode != 0:
        raise LedgerError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return proc


def _refname(name):
    """Full refs/heads/<name> if `name` isn't already a full ref. Pure."""
    return name if name.startswith("refs/") else f"refs/heads/{name}"


def _short(name):
    """Display name: refs/heads/<x> -> <x>, else unchanged. Pure."""
    return name[len("refs/heads/"):] if name.startswith("refs/heads/") else name


def read_mirror_refs(mirror):
    """{full-refname: sha} for every refs/heads/* in the mirror repo."""
    if not os.path.isdir(mirror):
        raise LedgerError(f"--mirror {mirror!r} is not a directory")
    _git(["-C", mirror, "rev-parse", "--git-dir"])  # raises LedgerError if not a repo
    out = _git(["-C", mirror, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads/"]).stdout
    refs = {}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        sha, _, ref = line.partition(" ")
        if HEX_RE.match(sha) and ref:
            refs[ref] = sha.lower()
    remotes = _git(["-C", mirror, "for-each-ref", "--format=%(refname)", "refs/remotes/"]).stdout.split()
    if len(remotes) > len(refs):
        raise LedgerError(f"--mirror {mirror!r} looks like a plain clone ({len(refs)} local heads, "
                          f"{len(remotes)} remote-tracking refs): use `git clone --mirror`, or every remote "
                          "branch would read as NEW_SINCE")
    return refs


def parse_current_refs(text):
    """{full-refname: sha} from ls-remote-shaped text: `sha<TAB or space>ref` lines.

    Peeled tag lines (ref ending in ^{}) and anything outside refs/heads/ are
    dropped; HEAD and refs/heads/HEAD are not branches.
    """
    refs = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        sha, ref = parts[0].strip().lower(), parts[1].strip()
        if not HEX_RE.match(sha) or ref.endswith("^{}"):
            continue
        ref = _refname(ref) if not ref.startswith("refs/") else ref
        if ref.startswith("refs/heads/"):
            refs[ref] = sha
    return refs


def fetch_current_refs(remote, timeout=GIT_TIMEOUT):
    """{full-refname: sha} read live via `git ls-remote --heads <remote>` (read-only)."""
    if not remote or remote.startswith("-"):
        raise LedgerError(f"bad --current-remote {remote!r}")
    out = _git(["ls-remote", "--heads", remote], timeout=timeout).stdout
    return parse_current_refs(out)


def _try_ancestor(mirror, remote, mirror_sha, current_sha, timeout=GIT_TIMEOUT):
    """True/False if ancestry of mirror_sha in current_sha's history is decided, else None (unverifiable).

    Fetches current_sha into the mirror under a throwaway scratch ref (deleted
    again after) ONLY when `remote` is given — a read, never a push. With no
    remote (offline --current-file use) this returns None without touching
    the mirror.
    """
    have = _git(["-C", mirror, "cat-file", "-e", current_sha + "^{commit}"], check_ok=False)
    fetched_scratch = None
    if have.returncode != 0:
        if not remote:
            return None
        scratch = SCRATCH_PREFIX + current_sha
        try:
            res = _git(["-C", mirror, "fetch", "--no-tags", "--", remote, f"{current_sha}:{scratch}"],
                       timeout=timeout, check_ok=False)
        except LedgerError:
            return None
        if res.returncode != 0:
            return None
        fetched_scratch = scratch
    try:
        res = _git(["-C", mirror, "merge-base", "--is-ancestor", mirror_sha, current_sha], check_ok=False)
        if res.returncode not in (0, 1):
            return None
        return res.returncode == 0
    finally:
        if fetched_scratch:
            _git(["-C", mirror, "update-ref", "-d", fetched_scratch], check_ok=False)


def build_ledger(mirror, current, remote=None, timeout=GIT_TIMEOUT):
    """Return a list of row dicts (ref, state, mirror_sha, current_sha, command), sorted by display name."""
    mirror_refs = read_mirror_refs(mirror)
    rows = []
    for ref in sorted(set(mirror_refs) | set(current), key=_short):
        m_sha, c_sha = mirror_refs.get(ref), current.get(ref)
        name = _short(ref)
        if m_sha is not None and c_sha is None:
            state = DELETED
            cmd = f"git push {remote or '<remote>'} {m_sha}:{ref}  # restore the deleted branch from the mirror"
        elif m_sha is None and c_sha is not None:
            state = NEW_SINCE
            cmd = "VERIFY: created after the backup; confirm it does not fork from a rewritten commit (rebase --onto the restored base if it does)"
        elif m_sha == c_sha:
            state = UNCHANGED
            cmd = "none (ref matches the pre-incident backup)"
        else:
            anc = _try_ancestor(mirror, remote, m_sha, c_sha, timeout)
            if anc is True:
                state = CHANGED_SINCE
                cmd = "none (already builds on the pre-incident commit; spot-check, do not restore)"
            else:
                state = STILL_REWRITTEN
                note = "" if anc is False else " (ancestry UNVERIFIED offline -- confirm manually before restoring)"
                cmd = (f"git push --force-with-lease={ref}:{c_sha} {remote or '<remote>'} {m_sha}:{ref}"
                       f"  # or: git rebase --onto {m_sha} <rewritten-base> {name}{note}")
        rows.append({"ref": name, "state": state, "mirror_sha": m_sha, "current_sha": c_sha, "command": cmd})
    return rows


def format_ledger(rows):
    lines = [f"{'REF':<30} {'STATE':<18} {'MIRROR':<10} {'CURRENT':<10} COMMAND"]
    for r in rows:
        lines.append(f"{r['ref']:<30} {r['state']:<18} {(r['mirror_sha'] or '-')[:9]:<10} "
                     f"{(r['current_sha'] or '-')[:9]:<10} {r['command']}")
    return "\n".join(lines)


def _parser():
    p = argparse.ArgumentParser(prog="restore_ledger.py",
                                description="Classify every branch after a VCS history-rewrite incident. Never pushes.")
    p.add_argument("--mirror", help="path to a pre-incident `git clone --mirror` (or any full-history repo)")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--current-file", help="file holding `git ls-remote`-shaped current-state lines")
    src.add_argument("--current-remote", help="remote URL/path; ls-remote'd live (read-only)")
    p.add_argument("--timeout", type=float, default=GIT_TIMEOUT, help="seconds per git call")
    p.add_argument("--json", action="store_true", help="print the ledger as a JSON array instead of a table")
    p.add_argument("--selftest", action="store_true", help="run offline self-tests")
    return p


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.mirror:
        _parser().print_usage(sys.stderr)
        print("restore_ledger.py: --mirror is required", file=sys.stderr)
        return 2
    if not args.current_file and not args.current_remote:
        print("restore_ledger.py: one of --current-file / --current-remote is required", file=sys.stderr)
        return 2
    try:
        if args.current_file:
            with open(args.current_file, encoding="utf-8") as fh:
                current = parse_current_refs(fh.read())
            remote = None
        else:
            current = fetch_current_refs(args.current_remote, args.timeout)
            remote = args.current_remote
        rows = build_ledger(args.mirror, current, remote, args.timeout)
    except LedgerError as exc:
        print(f"restore_ledger: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"restore_ledger: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(rows, sort_keys=True))
    else:
        print(format_ledger(rows))
    return 1 if any(r["state"] in NEEDS_ACTION for r in rows) else 0


# ---------------------------------------------------------------------------
# --selftest — offline: throwaway bare "remote"/"mirror" git repos in a temp
# dir, no network. Every classification is exercised at least once.
# ---------------------------------------------------------------------------
def _selftest():
    import contextlib
    import shutil

    passed = failed = 0

    def check(name, cond, detail=""):
        nonlocal passed, failed
        passed += bool(cond)
        failed += not cond
        print(f"{'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"\n      {detail}"))

    tmp = tempfile.mkdtemp(prefix="restore-ledger-selftest-")
    env_keys = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM", "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL")
    saved = {k: os.environ.get(k) for k in env_keys}
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                      GIT_AUTHOR_NAME="Jane Smith", GIT_AUTHOR_EMAIL="jane@example.com",
                      GIT_COMMITTER_NAME="Jane Smith", GIT_COMMITTER_EMAIL="jane@example.com")
    try:
        remote = os.path.join(tmp, "remote.git")
        work = os.path.join(tmp, "work")
        g = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, check=True).stdout.strip()
        g("init", "--quiet", "--bare", remote)
        g("init", "--quiet", work)
        g("-C", work, "commit", "--quiet", "--allow-empty", "-m", "base")
        base = g("-C", work, "rev-parse", "HEAD")
        for branch in ("main", "pre", "gone", "rewritten", "tail"):
            g("-C", work, "branch", "--quiet", "-f", branch, "HEAD")
        g("-C", work, "push", "--quiet", remote, "main", "pre", "gone", "rewritten", "tail")

        # mirror = pre-incident backup: exact snapshot of the remote right now.
        mirror = os.path.join(tmp, "mirror.git")
        g("clone", "--quiet", "--mirror", remote, mirror)
        # A second, never-fetched-into copy of the pristine mirror: the live
        # --current-remote run below fetches missing objects into `mirror` to
        # test ancestry, which would otherwise make a *later* offline run see
        # those objects as already present (they survive ref deletion) and
        # falsely "verify" ancestry it never actually had a fetch source for.
        pristine_mirror = os.path.join(tmp, "pristine-mirror.git")
        g("clone", "--quiet", "--mirror", mirror, pristine_mirror)

        # "main": untouched -> UNCHANGED_ORIGINAL.
        # "pre": moved FORWARD on the remote after the backup (normal work) -> CHANGED_SINCE.
        g("-C", work, "checkout", "--quiet", "pre")
        g("-C", work, "commit", "--quiet", "--allow-empty", "-m", "pre moved on")
        g("-C", work, "push", "--quiet", remote, "pre")
        # "gone": deleted on the remote -> DELETED.
        g("-C", work, "push", "--quiet", remote, "--delete", "gone")
        # "rewritten": remote history REPLACED by an unrelated commit (not a descendant) -> STILL_REWRITTEN.
        g("-C", work, "checkout", "--quiet", "--orphan", "rewritten-tmp")
        g("-C", work, "commit", "--quiet", "--allow-empty", "-m", "rewritten history")
        g("-C", work, "push", "--quiet", "--force", remote, "rewritten-tmp:rewritten")
        # "new-branch": exists only on the remote, not in the mirror -> NEW_SINCE.
        g("-C", work, "checkout", "--quiet", base)
        g("-C", work, "branch", "--quiet", "new-branch")
        g("-C", work, "push", "--quiet", remote, "new-branch")
        # "tail" is left untouched too (a second UNCHANGED_ORIGINAL row, sanity).

        def run(argv):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(argv)
            return rc, buf.getvalue()

        # --current-remote: live ls-remote against the local bare "remote" (offline: file path, no network).
        rc, out = run(["--mirror", mirror, "--current-remote", remote, "--json"])
        rows = {r["ref"]: r for r in json.loads(out)}
        check("main unchanged -> UNCHANGED_ORIGINAL", rows.get("main", {}).get("state") == UNCHANGED, out)
        check("pre moved forward -> CHANGED_SINCE", rows.get("pre", {}).get("state") == CHANGED_SINCE, out)
        check("gone deleted on remote -> DELETED", rows.get("gone", {}).get("state") == DELETED, out)
        check("rewritten diverged -> STILL_REWRITTEN", rows.get("rewritten", {}).get("state") == STILL_REWRITTEN, out)
        check("new-branch only on remote -> NEW_SINCE", rows.get("new-branch", {}).get("state") == NEW_SINCE, out)
        check("DELETED suggests a restoring push, never runs one",
              "git push" in rows["gone"]["command"] and "force" not in rows["gone"]["command"], out)
        check("STILL_REWRITTEN suggests --force-with-lease, never bare --force",
              "--force-with-lease" in rows["rewritten"]["command"] and " --force " not in
              (" " + rows["rewritten"]["command"] + " "), out)
        check("exit 1 when action-needed rows exist (DELETED/STILL_REWRITTEN present)", rc == 1, str(rc))

        # Offline --current-file path: same remote state, read from a saved ls-remote-shaped file, no network.
        current_text = "\n".join(f"{r['current_sha']}\t{'refs/heads/' + r['ref']}"
                                 for r in rows.values() if r["current_sha"])
        cur_file = os.path.join(tmp, "current.txt")
        with open(cur_file, "w") as fh:
            fh.write(current_text + "\n")
        rc2, out2 = run(["--mirror", pristine_mirror, "--current-file", cur_file, "--json"])
        rows2 = {r["ref"]: r for r in json.loads(out2)}
        check("current-file: main still UNCHANGED_ORIGINAL", rows2.get("main", {}).get("state") == UNCHANGED, out2)
        check("current-file: no fetchable source -> divergence fails closed to STILL_REWRITTEN, not silently green",
              rows2.get("rewritten", {}).get("state") == STILL_REWRITTEN, out2)
        check("current-file: ancestry-unverifiable note present when offline",
              "UNVERIFIED" in rows2["rewritten"]["command"], out2)
        check("current-file mode is fully offline: no scratch ref left behind in the mirror",
              g("-C", pristine_mirror, "for-each-ref", SCRATCH_PREFIX) == "", "leftover scratch ref")
        check("--current-remote mode cleans up its scratch ref too (never left behind)",
              g("-C", mirror, "for-each-ref", SCRATCH_PREFIX) == "", "leftover scratch ref after live run")

        # Table (non-JSON) output stays one row per ref, human-readable.
        rc3, out3 = run(["--mirror", mirror, "--current-remote", remote])
        check("table output has a header plus one row per ref", out3.count("\n") >= 6, out3)

        # Clean world (no DELETED/STILL_REWRITTEN) exits 0.
        clean_mirror = os.path.join(tmp, "clean-mirror.git")
        clean_remote = os.path.join(tmp, "clean-remote.git")
        g("init", "--quiet", "--bare", clean_remote)
        clean_work = os.path.join(tmp, "clean-work")
        g("init", "--quiet", clean_work)
        g("-C", clean_work, "commit", "--quiet", "--allow-empty", "-m", "c")
        g("-C", clean_work, "push", "--quiet", clean_remote, "HEAD:refs/heads/main")
        g("clone", "--quiet", "--mirror", clean_remote, clean_mirror)
        rc4, out4 = run(["--mirror", clean_mirror, "--current-remote", clean_remote])
        check("nothing to restore -> exit 0", rc4 == 0, out4)

        # NEW_SINCE needs action (exit 1): a post-incident branch may fork from rewritten history.
        g("-C", clean_work, "push", "--quiet", clean_remote, "HEAD:refs/heads/late-branch")
        rc8, out8 = run(["--mirror", clean_mirror, "--current-remote", clean_remote])
        check("NEW_SINCE row -> exit 1 (verify its fork point)", rc8 == 1 and "late-branch" in out8, out8)

        # A plain (non-mirror) clone is refused: its remote branches would all read NEW_SINCE.
        plain = os.path.join(tmp, "plain-clone")
        g("clone", "--quiet", clean_remote, plain)
        g("-C", clean_work, "push", "--quiet", clean_remote, "HEAD:refs/heads/extra-1")
        g("-C", plain, "fetch", "--quiet")
        rc9, _ = run(["--mirror", plain, "--current-remote", clean_remote])
        check("plain clone as --mirror refused (exit 2)", rc9 == 2, str(rc9))

        # Usage errors are refused (exit 2), never a silent empty ledger.
        rc5, _ = run(["--mirror", mirror])
        check("missing --current-* refused (exit 2)", rc5 == 2)
        rc6, _ = run(["--current-remote", remote])
        check("missing --mirror refused (exit 2)", rc6 == 2)
        rc7, _ = run(["--mirror", os.path.join(tmp, "nope"), "--current-remote", remote])
        check("nonexistent --mirror refused (exit 2)", rc7 == 2)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nselftest: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
