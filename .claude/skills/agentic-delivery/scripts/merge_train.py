#!/usr/bin/env python3
"""merge_train.py — land several green PRs as ONE verified union (a merge train).

WHY THIS EXISTS (the failure it closes)
----------------------------------------
deep-code-review's `references/merge-operations.md` (*Merge trains*) states
the rules for landing several independently-green PRs without a platform
merge queue: verify the combination once, isolate a culprit by holding the
others out for the suspect's whole verification cycle (issue #1119), attribute
a numeric-cap overshoot to the member that owns it (issue #1106), retry the
union immediately after parking a member instead of sleeping a cycle per
conflict (issue #1134), and never merge onto a base that moved or was
rewritten after the union was proved (issue #1137). Prose alone let every one
of those rules be skipped under pressure; this script is the mechanism.

SUBCOMMANDS
-----------
  plan    List open PRs targeting --base that are non-draft, same-repo (fork
          heads skipped unless --allow-forks), MERGEABLE, not parked, and
          green: the LATEST check run per name is completed with conclusion
          success/neutral/skipped, and at least --min-checks (K, >= 1) of those
          latest runs are `success`. Commit statuses (the legacy status API)
          are not read. Read-only.
  verify  Re-plan, fetch the base and every member head, then build ONE union
          in a throwaway worktree (members merged in PR-number order onto the
          fresh base) and run --verify-cmd once in it (plus --count-cmd vs --cap
          when given). On a merge conflict the member is parked with its files
          and the union is rebuilt at once, so N conflicts cost one run, not N
          cycles (#1134). On a deterministic failure:
            - numeric cap failed (--count-cmd output > --cap): print one line
              per member, `#N +D marker=present|none`, where D is the count at
              the member's head minus the count at its own merge-base with the
              base, and marker is whether the member's own commit range carries
              a `<--marker-key>: ...` line (#1106); every member with D > 0 and
              marker=none is parked;
            - otherwise (or when attribution names no one): prefix bisection.
              The base alone must pass (else HALT); the smallest failing prefix
              names the culprit — the member whose inclusion breaks the gate.
              Members outside a prefix are held out for that prefix's entire
              verification run, never re-admitted mid-search (#1119).
          A parked member stays excluded from every later plan/verify until its
          head changes. The surviving union is rebuilt immediately. When a
          union is green the base SHA and member heads are recorded in --state.
  merge   Dry-run by default: prints what would merge. With --apply (and
          --grant) it merges the recorded members back-to-back with
          `gh pr merge --merge --match-head-commit`, preserving each member's
          own commits and closing keywords (never a squash of the union). It
          refuses (HALT) unless the base head equals the SHA the union was
          proved on: a fast-forward move means re-plan; a non-fast-forward move
          means a possible history rewrite and needs a human (#1137). It never
          re-verifies on its own. Before each merge the PR must still be OPEN,
          at the recorded head, and MERGEABLE (UNKNOWN is polled with bounded
          backoff); after each merge the new base head must be exactly the merge
          of the previous head and that member, else another writer moved the
          base mid-train (HALT). A member that fails deterministically is parked
          with its reason and the rest HALT, because the remaining combination
          was never verified.

FLAKY VS DETERMINISTIC
----------------------
A failing --verify-cmd is re-run up to --retries times on the same tree with
exponential backoff (--backoff seconds, doubling, capped at 300 s). A re-run
that passes is reported `FLAKY` and counts as a pass; failing every attempt is
deterministic. A failed `gh pr merge` is retried on the same bounded schedule.
Parking a member never sleeps.

AUTHORITY AND SAFETY
--------------------
Merging needs the integration owner or a standing grant the owner recorded.
`--apply` requires `--grant <ref>` naming that decision (a link or record id);
this script only checks that it is present and echoes it on every MERGED line.
It cannot verify the grant. The script never pushes: any `git push` it is
asked to run raises HALT, so it cannot force-push a shared branch. --verify-cmd
runs PR code on this machine, which is why fork PRs are skipped by default.

OUTPUT AND EXIT CODES
---------------------
One line per action (ELIGIBLE, SKIP, PLAN, FAIL, FLAKY, PARK, GREEN, RED,
WOULD-MERGE, MERGED, NOOP, HALT, ERROR). Untrusted text (check names, file
names, forge errors) is stripped of control characters and truncated.
  0  plan listed; union green; dry-run printed; members merged; nothing to do
  1  verify found no green union (every member parked)
  2  usage or forge/git error (fail closed; nothing is guessed)
  3  HALT: base moved or rewritten, base red, another writer mid-train, a
     member failed at merge time, or a refused push

USAGE
-----
  merge_train.py plan   --base main [--repo OWNER/NAME] [--min-checks K]
  merge_train.py verify --base main --verify-cmd 'make test'
                        [--count-cmd CMD --cap N --marker-key size-budget-raise]
                        [--retries 2] [--backoff 30] [--timeout 3600]
  merge_train.py merge  --base main [--apply --grant REF]
  merge_train.py --selftest
Common: --remote origin, --state PATH (default <git-common-dir>/merge-train.json).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager

sys.dont_write_bytecode = True  # never litter __pycache__ into a checksummed skill tree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_common as bc  # noqa: E402  (validate_repo, run_checks)

OK, RED, ERROR, HALT = 0, 1, 2, 3
GREEN_CONCLUSIONS = {"success", "neutral", "skipped"}
PR_LIMIT = 200
MAX_BACKOFF = 300
GIT_ID = ["-c", "user.name=merge-train", "-c", "user.email=merge-train@example.invalid"]


class Halt(Exception):
    """Stop all automation; a human or a fresh plan must decide what happens next."""


class ForgeError(Exception):
    """A forge or git call failed or returned something unusable; fail closed."""


class Conflict(Exception):
    """A member did not merge cleanly into the union."""

    def __init__(self, member, files):
        super().__init__(member["number"])
        self.member, self.files = member, files


def default_runner(args, cwd=None, timeout=3600):
    """Run a command without a shell; return (returncode, stdout, stderr).

    Side-effects: spawns a subprocess. A missing binary is rc 127 and a timeout
    rc 124, returned rather than raised so callers fail closed uniformly.
    """
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s: {args[0]}"
    return proc.returncode, proc.stdout, proc.stderr


def clean(text, limit=80) -> str:
    """Strip control characters and truncate untrusted text before printing it. Pure."""
    return re.sub(r"[\x00-\x1f\x7f]", "?", str(text))[:limit]


def names(members) -> str:
    """`#1,#2` for a member list (empty string for none). Pure."""
    return ",".join(f"#{m['number']}" for m in members)


class Train:
    """One merge-train invocation: forge/git I/O goes through `runner`, waits through `sleep`."""

    def __init__(self, args, runner, out, sleep):
        self.a, self.runner, self.out, self.sleep = args, runner, out, sleep
        self.repo_flag = ["--repo", args.repo] if args.repo else []
        self.base_sha = ""
        self.state_path = args.state or self._default_state()
        self.state = self._load()

    # ---- plumbing -------------------------------------------------------
    def say(self, line):
        """Print one action line to the output stream."""
        print(line, file=self.out)

    def run(self, argv, cwd=None, ok=True, timeout=None):
        """Run argv through the runner; raise ForgeError on a non-zero rc when ok=True.

        Refuses every `git push` with HALT before the runner sees it: this tool
        never pushes, so it can never force-push a shared branch.
        """
        if argv[:1] == ["git"] and "push" in argv[1:]:
            raise Halt("refusing git push: merge_train never pushes (merges go through the forge API only)")
        rc, out, err = self.runner(argv, cwd=cwd, **({"timeout": timeout} if timeout else {}))
        if ok and rc != 0:
            raise ForgeError(f"{clean(' '.join(argv[:4]))} rc={rc}: {clean(err.strip(), 160)}")
        return rc, out, err

    def _default_state(self):
        """<git-common-dir>/merge-train.json, shared by every worktree of the repository."""
        _, out, _ = self.run(["git", "rev-parse", "--git-common-dir"])
        return os.path.join(os.path.abspath(out.strip()), "merge-train.json")

    def _load(self):
        """Read the state file; a missing file is empty state, an unreadable one fails closed."""
        try:
            with open(self.state_path, encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as exc:
            raise ForgeError(f"unreadable state {self.state_path}: {exc}") from exc

    def save(self):
        """Write the state file atomically (temp file + rename)."""
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.state, fh, indent=1, sort_keys=True)
        os.replace(tmp, self.state_path)

    def rev(self, ref):
        """Resolve a git ref to its SHA."""
        return self.run(["git", "rev-parse", ref])[1].strip()

    def fetch(self, *refs):
        """Fetch the base (plus `refs`) from the remote; return the fresh base SHA."""
        self.run(["git", "fetch", "--quiet", self.a.remote, self.a.base, *refs])
        return self.rev(f"refs/remotes/{self.a.remote}/{self.a.base}")

    def delay(self, attempt):
        """Backoff before retry `attempt` (1-based): --backoff doubling, capped at MAX_BACKOFF."""
        return min(self.a.backoff * 2 ** (attempt - 1), MAX_BACKOFF)

    def park(self, member, reason):
        """Exclude `member` at its current head from every later plan, persist it, print PARK."""
        self.state.setdefault("parked", {})[str(member["number"])] = {"head": member["head"], "reason": reason}
        self.save()
        self.say(f"PARK #{member['number']} {reason}")

    # ---- plan -----------------------------------------------------------
    def plan(self):
        """The `plan` subcommand: print eligibility, change nothing."""
        self.eligible()
        return OK

    def eligible(self):
        """Return eligible members [{number, head}] in PR-number order; one line per PR."""
        _, out, _ = self.run(["gh", "pr", "list", *self.repo_flag, "--base", self.a.base, "--state", "open",
                              "--limit", str(PR_LIMIT), "--json", "number,headRefOid,isDraft,mergeable,isCrossRepository"])
        prs = json.loads(out or "[]")
        if len(prs) >= PR_LIMIT:
            raise ForgeError(f"pr list hit the {PR_LIMIT} limit; refusing a truncated plan")
        heads = {str(p["number"]): p["headRefOid"] for p in prs}
        parked = {n: p for n, p in self.state.get("parked", {}).items() if heads.get(n) == p["head"]}
        self.state["parked"] = parked  # a new head is new information: it un-parks
        members = []
        for pr in sorted(prs, key=lambda p: p["number"]):
            why = self._ineligible(pr, parked)
            if why:
                self.say(f"SKIP #{pr['number']} {why}")
            else:
                members.append({"number": pr["number"], "head": pr["headRefOid"]})
                self.say(f"ELIGIBLE #{pr['number']} {pr['headRefOid'][:7]}")
        self.say(f"PLAN base={self.a.base} members={names(members) or 'none'}")
        return members

    def _ineligible(self, pr, parked):
        """'' when `pr` may join the train, else the reason it is skipped."""
        if pr.get("isDraft"):
            return "draft"
        if pr.get("isCrossRepository") and not self.a.allow_forks:
            return "fork (verify would run its code here; --allow-forks)"
        if str(pr["number"]) in parked:
            return f"parked ({parked[str(pr['number'])]['reason']})"
        if pr.get("mergeable") != "MERGEABLE":
            return f"mergeable={clean(pr.get('mergeable'))}"
        passed, bad = self._checks(pr["headRefOid"])
        if bad:
            return f"check {bad}"
        return f"checks {passed}<{self.a.min_checks}" if passed < self.a.min_checks else ""

    def _checks(self, sha):
        """(latest-per-name success count, first non-green 'name=state' or '')."""
        repo = self.a.repo or "{owner}/{repo}"
        _, out, _ = self.run(["gh", "api", f"repos/{repo}/commits/{sha}/check-runs?per_page=100"])
        data = json.loads(out)
        runs = data.get("check_runs") or []
        if data.get("total_count", len(runs)) > len(runs):
            raise ForgeError(f"{sha[:7]} has more than {len(runs)} check runs; not verified")
        latest = {}
        for r in runs:
            key = (r.get("started_at") or "", r.get("id") or 0)
            if r["name"] not in latest or key > latest[r["name"]][0]:
                latest[r["name"]] = (key, r)
        passed = 0
        for name in sorted(latest):
            r = latest[name][1]
            if r.get("status") != "completed" or r.get("conclusion") not in GREEN_CONCLUSIONS:
                return passed, clean(f"{name}={r.get('conclusion') or r.get('status')}")
            passed += r.get("conclusion") == "success"
        return passed, ""

    # ---- verify ---------------------------------------------------------
    @contextmanager
    def tree(self, start, merges):
        """Throwaway detached worktree at `start` with `merges` merged in order."""
        tmp = tempfile.mkdtemp(prefix="merge-train-")
        wt = os.path.join(tmp, "wt")
        try:
            self.run(["git", "worktree", "add", "--quiet", "--detach", wt, start])
            for m in merges:
                rc, _, err = self.run(["git", *GIT_ID, "merge", "--no-ff", "--no-edit", "-m",
                                       f"merge-train: #{m['number']}", m["head"]], cwd=wt, ok=False)
                if rc:
                    files = self.run(["git", "diff", "--name-only", "--diff-filter=U"], cwd=wt, ok=False)[1].split()
                    self.run(["git", "merge", "--abort"], cwd=wt, ok=False)
                    if not files:
                        raise ForgeError(f"merge of #{m['number']} failed without conflicts: {clean(err.strip(), 160)}")
                    raise Conflict(m, files)
            yield wt
        finally:
            self.run(["git", "worktree", "remove", "--force", wt], ok=False)
            shutil.rmtree(tmp, ignore_errors=True)

    def fails(self, members, label):
        """'' when base+members passes the gate, else 'verify' or 'cap C>N'."""
        with self.tree(self.base_sha, members) as wt:
            attempts = self.a.retries + 1
            for i in range(attempts):
                if i:
                    self.sleep(self.delay(i))
                if self.run(["sh", "-c", self.a.verify_cmd], cwd=wt, ok=False, timeout=self.a.timeout)[0] == 0:
                    if i:
                        self.say(f"FLAKY {label} passed on attempt {i + 1}/{attempts}")
                    break
            else:
                self.say(f"FAIL {label} deterministic ({attempts}/{attempts} attempts)")
                return "verify"
            if self.a.count_cmd:
                count = self.count(wt)
                if count > self.a.cap:
                    self.say(f"FAIL {label} cap {count}>{self.a.cap}")
                    return f"cap {count}>{self.a.cap}"
        return ""

    def count(self, wt):
        """Run --count-cmd in `wt`; it must print exactly one integer (else fail closed)."""
        out = self.run(["sh", "-c", self.a.count_cmd], cwd=wt, timeout=self.a.timeout)[1].strip()
        if not re.fullmatch(r"-?\d+", out):
            raise ForgeError(f"--count-cmd must print one integer, got {clean(out)!r}")
        return int(out)

    def attribute(self, members):
        """#1106: `#N +D marker=...` per member; return [(member, reason)] with D > 0 and no marker."""
        guilty = []
        key = re.compile(rf"^{re.escape(self.a.marker_key)}:[ \t]*\S", re.M)
        for m in members:
            mb = self.run(["git", "merge-base", m["head"], self.base_sha])[1].strip()
            counts = []
            for sha in (m["head"], mb):
                with self.tree(sha, []) as wt:
                    counts.append(self.count(wt))
            delta = counts[0] - counts[1]
            marked = bool(key.search(self.run(["git", "log", "--format=%B", f"{mb}..{m['head']}"])[1]))
            self.say(f"#{m['number']} {delta:+d} marker={'present' if marked else 'none'}")
            if delta > 0 and not marked:
                guilty.append((m, f"ratchet {delta:+d} marker=none"))
        return guilty

    def bisect(self, members):
        """#1119 prefix bisection: the member whose inclusion first breaks the gate."""
        if self.fails([], "base"):
            raise Halt(f"base {self.base_sha[:7]} fails the gate on its own; no member is isolable (discharge a red base first)")
        lo, hi = 0, len(members)  # invariant: prefix lo passes, prefix hi fails
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.fails(members[:mid], f"prefix {names(members[:mid])}"):
                hi = mid
            else:
                lo = mid
        return members[hi - 1], f"breaks gate after {names(members[:hi - 1]) or 'base'}"

    def verify(self):
        """The `verify` subcommand: find the largest green union, parking culprits; record it."""
        members = self.eligible()
        self.base_sha = self.fetch(*[f"refs/pull/{m['number']}/head" for m in members])
        parked_any = False
        while members:
            try:
                why = self.fails(members, f"union {names(members)}")
            except Conflict as c:
                self.park(c.member, "conflict " + ",".join(clean(f, 60) for f in c.files[:5]))
                members, parked_any = [m for m in members if m is not c.member], True
                continue  # #1134: rebuild at once, never a sleep per conflict
            if not why:
                self.state.update(base=self.a.base, base_sha=self.base_sha, members=members)
                self.save()
                self.say(f"GREEN base={self.base_sha[:7]} members={names(members)}")
                return OK
            guilty = self.attribute(members) if why.startswith("cap") else []
            for m, reason in guilty or [self.bisect(members)]:
                self.park(m, reason)
                members, parked_any = [x for x in members if x is not m], True
        self.state.update(base=self.a.base, base_sha=self.base_sha, members=[])
        self.save()
        self.say("RED no green union: every member parked" if parked_any else "NOOP no eligible members")
        return RED if parked_any else OK

    # ---- merge ----------------------------------------------------------
    def same_base(self, proved, current):
        """HALT unless `current` is the base SHA the union was proved on (#1137)."""
        if current == proved:
            return
        rc = self.run(["git", "merge-base", "--is-ancestor", proved, current], ok=False)[0]
        if rc == 0:
            raise Halt(f"base {self.a.base} moved {proved[:7]}->{current[:7]} since verify; re-plan "
                       "(never re-verify silently on a changed base)")
        if rc == 1:
            raise Halt(f"base {self.a.base} rewritten: {proved[:7]} is not an ancestor of {current[:7]} "
                       "(non-fast-forward, possible history rewrite); a human must clear this")
        raise ForgeError(f"cannot compare {proved[:7]} with {current[:7]} (rc={rc})")

    def still_ready(self, m):
        """'' when the PR is OPEN, at the recorded head, and MERGEABLE (UNKNOWN polled), else why not."""
        attempts = self.a.retries + 1
        for i in range(attempts):
            if i:
                self.sleep(self.delay(i))
            pr = json.loads(self.run(["gh", "pr", "view", str(m["number"]), *self.repo_flag,
                                      "--json", "state,headRefOid,mergeable"])[1])
            if pr.get("state") != "OPEN":
                return f"state={clean(pr.get('state'))}"
            if pr.get("headRefOid") != m["head"]:
                return f"head moved to {clean(pr.get('headRefOid'))[:7]}"
            if pr.get("mergeable") == "MERGEABLE":
                return ""
            if pr.get("mergeable") != "UNKNOWN":
                return f"mergeable={clean(pr.get('mergeable'))}"
        return f"mergeable=UNKNOWN after {attempts} polls"

    def merge_one(self, m):
        """Merge one member at its recorded head with bounded retries; '' on success, else why not."""
        attempts, err = self.a.retries + 1, ""
        for i in range(attempts):
            if i:
                self.sleep(self.delay(i))
            rc, _, err = self.run(["gh", "pr", "merge", str(m["number"]), *self.repo_flag, "--merge",
                                   "--match-head-commit", m["head"]], ok=False)
            if rc == 0:
                if i:
                    self.say(f"FLAKY merge #{m['number']} landed on attempt {i + 1}/{attempts}")
                return ""
        return f"merge failed {attempts}x: {clean(err.strip().splitlines()[-1] if err.strip() else 'no stderr')}"

    def merge(self):
        """The `merge` subcommand: dry-run by default; with --apply land members back-to-back."""
        members = self.state.get("members") or []
        if self.state.get("base") != self.a.base or not self.state.get("base_sha"):
            raise ForgeError(f"no verified union for base {self.a.base} in {self.state_path}; run verify")
        if not members:
            self.say("NOOP nothing verified to merge")
            return OK
        prev = self.fetch()
        self.same_base(self.state["base_sha"], prev)
        if not self.a.apply:
            for m in members:
                self.say(f"WOULD-MERGE #{m['number']} {m['head'][:7]} onto {self.a.base}@{prev[:7]}")
            self.say("DRY-RUN nothing merged; --apply --grant REF merges (integration owner or recorded standing grant)")
            return OK
        for i, m in enumerate(members):
            why = self.still_ready(m) or self.merge_one(m)
            if why:
                self.park(m, why)
                self.state["members"] = []
                self.save()
                raise Halt(f"#{m['number']} not merged ({why}); {names(members[i + 1:]) or 'no members'} "
                           "left unmerged: re-plan and re-verify")
            new = self.fetch()
            parents = self.run(["git", "rev-list", "--parents", "-n", "1", new])[1].split()[1:]
            if parents != [prev, m["head"]]:
                self.state["members"] = []
                self.save()
                raise Halt(f"base moved by another writer while merging #{m['number']} ({new[:7]} is not "
                           f"{prev[:7]}+#{m['number']}); {names(members[i + 1:]) or 'no members'} left unmerged")
            self.state.update(base_sha=new, members=members[i + 1:])
            self.save()
            self.say(f"MERGED #{m['number']} {m['head'][:7]} -> {self.a.base}@{new[:7]} grant={clean(self.a.grant)}")
            prev = new
        return OK


def build_parser():
    """Argument parser: plan / verify / merge subcommands plus --selftest."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base", required=True, help="target branch the PRs merge into")
    common.add_argument("--repo", default="", help="OWNER/NAME (default: gh infers from the checkout)")
    common.add_argument("--remote", default="origin")
    common.add_argument("--state", default="", help="state file (default <git-common-dir>/merge-train.json)")
    common.add_argument("--min-checks", type=int, default=1, help="K: latest successful check runs required")
    common.add_argument("--allow-forks", action="store_true", help="admit fork PRs (their code runs locally)")
    common.add_argument("--retries", type=int, default=2, help="bounded re-runs for a flaky step")
    common.add_argument("--backoff", type=float, default=30.0, help="first retry delay in seconds (doubles, max 300)")
    p = argparse.ArgumentParser(description="Verify several green PRs as one union, then land them back-to-back.")
    p.add_argument("--selftest", action="store_true", help="run offline self-tests against a fake forge")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("plan", parents=[common])
    v = sub.add_parser("verify", parents=[common])
    v.add_argument("--verify-cmd", required=True, help="gate command run once in the union tree (sh -c)")
    v.add_argument("--count-cmd", default="", help="prints one integer: a numeric ratchet count")
    v.add_argument("--cap", type=int, default=None, help="maximum allowed --count-cmd value")
    v.add_argument("--marker-key", default="size-budget-raise", help="trailer key recording a deliberate raise")
    v.add_argument("--timeout", type=int, default=3600, help="seconds per gate command")
    m = sub.add_parser("merge", parents=[common])
    m.add_argument("--apply", action="store_true", help="actually merge (default is a dry run)")
    m.add_argument("--grant", default="", help="the owner's decision or recorded standing grant authorising this merge")
    return p


def run(argv, runner=default_runner, out=sys.stdout, sleep=time.sleep) -> int:
    """Parse argv and execute one subcommand. Returns the exit code; never raises."""
    parser = build_parser()
    a = parser.parse_args(argv)
    if a.cmd is None:
        parser.print_usage(out)
        return ERROR
    problems = []
    if a.repo and not bc.validate_repo(a.repo):
        problems.append("--repo must be OWNER/NAME")
    if a.min_checks < 1:
        problems.append("--min-checks must be >= 1 (zero checks is never green)")
    if a.retries < 0 or a.backoff < 0:
        problems.append("--retries/--backoff must be >= 0")
    if a.cmd == "verify" and bool(a.count_cmd) != (a.cap is not None):
        problems.append("--count-cmd and --cap go together")
    if a.cmd == "merge" and a.apply and not a.grant.strip():
        problems.append("--apply needs --grant naming the integration owner's decision or a recorded standing grant")
    if problems:
        print("ERROR " + "; ".join(problems), file=out)
        return ERROR
    try:
        train = Train(a, runner, out, sleep)
        return getattr(train, a.cmd)()
    except Halt as exc:
        print(f"HALT {exc}", file=out)
        return HALT
    except (ForgeError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR {clean(exc, 240)} (not verified)", file=out)
        return ERROR


# ---- selftest: a fake forge + git, no network, no real repository ----------
class FakeForge:
    """Simulates the gh + git calls merge_train makes; records every call and sleep."""

    def __init__(self, n=4):
        self.hist = ["B0"]  # linear base history, tip last
        self.prs = {i: {"head": f"h{i}", "isDraft": False, "mergeable": "MERGEABLE", "isCrossRepository": False,
                        "state": "OPEN", "runs": [_run("ci", "success"), _run("lint", "success")]}
                    for i in range(1, n + 1)}
        self.bad = set()  # a union containing any of these fails verify
        self.flaky_left = 0  # the next N verify runs fail, then pass
        self.conflicts = set()  # these conflict when merged after any other member
        self.delta, self.marked = {}, set()
        self.view_override, self.merge_fail, self.intruder = {}, set(), False
        self.trees, self.calls, self.sleeps, self.gates = {}, [], [], []
        self.fail_prefix, self.parents = None, {}

    def base(self):
        return self.hist[-1]

    def __call__(self, args, cwd=None, timeout=None):
        self.calls.append(args)
        if self.fail_prefix and args[:len(self.fail_prefix)] == self.fail_prefix:
            return 1, "", "simulated outage"
        a = [args[0], *args[5:]] if args[1:5] == GIT_ID else args
        if a[:3] == ["gh", "pr", "list"]:
            rows = [{"number": n, "headRefOid": p["head"], **{k: p[k] for k in ("isDraft", "mergeable", "isCrossRepository")}}
                    for n, p in self.prs.items() if p["state"] == "OPEN"]
            return 0, json.dumps(rows), ""
        if a[:2] == ["gh", "api"]:
            sha = a[2].split("/commits/")[1].split("/")[0]
            runs = next(p["runs"] for p in self.prs.values() if p["head"] == sha)
            return 0, json.dumps({"total_count": len(runs), "check_runs": runs}), ""
        if a[:3] == ["gh", "pr", "view"]:
            p = self.prs[int(a[3])]
            row = {"state": p["state"], "headRefOid": p["head"], "mergeable": p["mergeable"]}
            row.update(self.view_override.get(int(a[3]), {}))
            return 0, json.dumps(row), ""
        if a[:3] == ["gh", "pr", "merge"]:
            n = int(a[3])
            if n in self.merge_fail:
                return 1, "", "GraphQL: Pull request is not mergeable"
            if self.intruder:
                self.hist.append("X9")
            self.hist.append(f"M{n}")
            self.parents[f"M{n}"] = [self.hist[-2], self.prs[n]["head"]]
            self.prs[n]["state"] = "MERGED"
            return 0, "", ""
        if a[:2] == ["git", "fetch"] or a[:3] in (["git", "worktree", "remove"], ["git", "merge", "--abort"]):
            return 0, "", ""
        if a[:2] == ["git", "rev-parse"]:
            return 0, self.base() + "\n", ""
        if a[:3] == ["git", "worktree", "add"]:
            self.trees[a[5]] = {"start": a[6], "merged": []}
            return 0, "", ""
        if a[:2] == ["git", "merge"] and cwd:
            n = int(a[-1][1:])
            if n in self.conflicts and self.trees[cwd]["merged"]:
                self.trees[cwd]["conflict"] = True
                return 1, "", "CONFLICT"
            self.trees[cwd]["merged"].append(n)
            return 0, "", ""
        if a[:2] == ["git", "diff"]:
            return 0, "src/shared.py\n" if self.trees[cwd].pop("conflict", False) else "", ""
        if a[:3] == ["git", "merge-base", "--is-ancestor"]:
            return (0 if a[3] in self.hist else 1), "", ""
        if a[:2] == ["git", "merge-base"]:
            return 0, f"mb{a[2][1:]}\n", ""
        if a[:2] == ["git", "log"]:
            n = int(a[3].split("..h")[1])
            return 0, ("feat: x\n\nsize-budget-raise: a.md 1->2 reason\n" if n in self.marked else "feat: x\n"), ""
        if a[:2] == ["git", "rev-list"]:
            return 0, " ".join([a[-1], *self.parents.get(a[-1], ["?"])]), ""
        if a[:2] == ["sh", "-c"]:
            t = self.trees[cwd]
            if a[2] == "count":
                start = t["start"]
                own = self.delta.get(int(start[1:]), 0) if start.startswith("h") else 0
                return 0, str(10 + own + sum(self.delta.get(m, 0) for m in t["merged"])) + "\n", ""
            self.gates.append(tuple(t["merged"]))
            if self.flaky_left:
                self.flaky_left -= 1
                return 1, "", ""
            return (1 if self.bad & set(t["merged"]) else 0), "", ""
        return 99, "", f"fake: unexpected {args}"


def _run(name, conclusion, started="2026-01-01T00:00:00Z", rid=1, status="completed"):
    return {"name": name, "status": status, "conclusion": conclusion, "started_at": started, "id": rid}


def _selftest() -> int:
    import io

    tmp = tempfile.mkdtemp(prefix="merge-train-selftest-")

    def go(forge, *argv, state="s.json"):
        buf = io.StringIO()
        rc = run([*argv, "--base", "main", "--state", os.path.join(tmp, state), "--backoff", "5"],
                 runner=forge, out=buf, sleep=forge.sleeps.append)
        return rc, buf.getvalue()

    def fresh(state):
        p = os.path.join(tmp, state)
        if os.path.exists(p):
            os.remove(p)
        return state

    def verified(forge, state):
        rc, out = go(forge, "verify", "--verify-cmd", "t", state=fresh(state))
        assert rc == OK, out
        return state

    def plan_filters():
        f = FakeForge(7)
        f.prs[2]["isDraft"] = True
        f.prs[3]["runs"] = [_run("ci", "success", rid=1), _run("ci", "failure", "2026-01-02T00:00:00Z", 2), _run("lint", "success")]
        f.prs[4]["runs"] = [_run("ci", "failure", rid=1), _run("ci", "success", "2026-01-02T00:00:00Z", 2), _run("lint", "success")]
        f.prs[5]["mergeable"] = "CONFLICTING"
        f.prs[6]["runs"] = [_run("ci", "success")]
        f.prs[7]["isCrossRepository"] = True
        rc, out = go(f, "plan", "--min-checks", "2", state=fresh("plan.json"))
        want = ["ELIGIBLE #1 h1", "SKIP #2 draft", "SKIP #3 check ci=failure", "ELIGIBLE #4 h4",
                "SKIP #5 mergeable=CONFLICTING", "SKIP #6 checks 1<2", "SKIP #7 fork", "PLAN base=main members=#1,#4"]
        return rc == OK and all(w in out for w in want), out

    def culprit_among_four_is_isolated_and_stays_parked():
        f = FakeForge(4)
        f.bad = {3}
        rc, out = go(f, "verify", "--verify-cmd", "t", state=fresh("c.json"))
        # union fails; base passes; prefix #1,#2 passes; prefix #1,#2,#3 fails with #4 held out; rebuilt union passes
        runs = list(f.gates)
        want_runs = [(1, 2, 3, 4)] * 3 + [()] + [(1, 2)] + [(1, 2, 3)] * 3 + [(1, 2, 4)]
        ok1 = (rc == OK and "PARK #3 breaks gate after #1,#2" in out and "GREEN base=B0 members=#1,#2,#4" in out
               and runs == want_runs)
        rc2, out2 = go(f, "verify", "--verify-cmd", "t", state="c.json")
        ok2 = rc2 == OK and "SKIP #3 parked (breaks gate after #1,#2)" in out2 and f.gates[-1] == (1, 2, 4)
        f.prs[3]["head"] = "h3b"  # a new push is new information: it un-parks
        rc3, out3 = go(f, "plan", state="c.json")
        return ok1 and ok2 and rc3 == OK and "ELIGIBLE #3 h3b" in out3, (out, runs, out2, out3)

    def conflicts_all_parked_in_one_cycle_without_sleeping():
        f = FakeForge(4)
        f.conflicts = {2, 3, 4}
        rc, out = go(f, "verify", "--verify-cmd", "t", state=fresh("k.json"))
        ok = (rc == OK and all(f"PARK #{n} conflict src/shared.py" in out for n in (2, 3, 4))
              and "GREEN base=B0 members=#1" in out and f.sleeps == [] and f.gates == [(1,)])
        return ok, (out, f.sleeps, f.gates)

    def flaky_passes_on_retry_with_bounded_backoff():
        f = FakeForge(2)
        f.flaky_left = 2
        rc, out = go(f, "verify", "--verify-cmd", "t", state=fresh("f.json"))
        return (rc == OK and "FLAKY union #1,#2 passed on attempt 3/3" in out and "PARK" not in out
                and f.sleeps == [5, 10]), (out, f.sleeps)

    def deterministic_failure_parks_member():
        f = FakeForge(2)
        f.bad = {2}
        rc, out = go(f, "verify", "--verify-cmd", "t", state=fresh("d.json"))
        return (rc == OK and "FAIL union #1,#2 deterministic (3/3 attempts)" in out
                and "PARK #2 breaks gate after #1" in out and "GREEN base=B0 members=#1" in out), out

    def all_members_bad_is_red():
        f = FakeForge(2)
        f.bad = {1, 2}
        rc, out = go(f, "verify", "--verify-cmd", "t", "--retries", "0", state=fresh("r.json"))
        return rc == RED and "RED no green union" in out, out

    def red_base_halts():
        f = FakeForge(2)
        f.flaky_left = 99
        rc, out = go(f, "verify", "--verify-cmd", "t", "--retries", "0", state=fresh("rb.json"))
        return rc == HALT and "fails the gate on its own" in out, out

    def ratchet_overshoot_attributed_per_member():
        f = FakeForge(3)
        f.delta, f.marked = {1: 0, 2: 3, 3: 1}, {3}
        rc, out = go(f, "verify", "--verify-cmd", "t", "--count-cmd", "count", "--cap", "12", state=fresh("a.json"))
        want = ["FAIL union #1,#2,#3 cap 14>12", "#1 +0 marker=none", "#2 +3 marker=none", "#3 +1 marker=present",
                "PARK #2 ratchet +3 marker=none", "GREEN base=B0 members=#1,#3"]
        return rc == OK and all(w in out for w in want), out

    def dry_run_is_default():
        f = FakeForge(2)
        st = verified(f, "dr.json")
        rc, out = go(f, "merge", state=st)
        merged = [c for c in f.calls if c[:3] == ["gh", "pr", "merge"]]
        return rc == OK and "WOULD-MERGE #1 h1" in out and "DRY-RUN" in out and not merged, out

    def apply_needs_grant():
        rc, out = go(FakeForge(1), "merge", "--apply", state="dr.json")
        return rc == ERROR and "--grant" in out, out

    def apply_merges_back_to_back():
        f = FakeForge(2)
        st = verified(f, "ap.json")
        rc, out = go(f, "merge", "--apply", "--grant", "owner-grant-1", state=st)
        merged = [c[3] for c in f.calls if c[:3] == ["gh", "pr", "merge"]]
        again_rc, again = go(f, "merge", "--apply", "--grant", "owner-grant-1", state=st)
        return (rc == OK and merged == ["1", "2"] and "MERGED #2 h2 -> main@M2 grant=owner-grant-1" in out
                and all("--merge" in c for c in f.calls if c[:3] == ["gh", "pr", "merge"])
                and again_rc == OK and "NOOP" in again), (out, merged, again)

    def base_moved_halts_without_reverify():
        f = FakeForge(2)
        st = verified(f, "bm.json")
        f.hist.append("B1")  # someone else landed a commit (fast-forward)
        before = len(f.gates)
        rc, out = go(f, "merge", "--apply", "--grant", "g", state=st)
        merged = [c for c in f.calls if c[:3] == ["gh", "pr", "merge"]]
        return (rc == HALT and "moved B0->B1" in out and "re-plan" in out and not merged
                and len(f.gates) == before), out

    def base_rewritten_halts():
        f = FakeForge(2)
        st = verified(f, "rw.json")
        f.hist = ["Z0"]  # force-pushed: B0 is no longer in history
        rc, out = go(f, "merge", "--apply", "--grant", "g", state=st)
        merged = [c for c in f.calls if c[:3] == ["gh", "pr", "merge"]]
        return rc == HALT and "rewritten" in out and "non-fast-forward" in out and not merged, out

    def intruder_mid_train_halts():
        f = FakeForge(2)
        st = verified(f, "in.json")
        f.intruder = True
        rc, out = go(f, "merge", "--apply", "--grant", "g", state=st)
        merged = [c[3] for c in f.calls if c[:3] == ["gh", "pr", "merge"]]
        return rc == HALT and "another writer" in out and merged == ["1"], out

    def merge_time_conflict_parks_and_halts():
        f = FakeForge(3)
        st = verified(f, "mc.json")
        f.view_override = {2: {"mergeable": "CONFLICTING"}}
        rc, out = go(f, "merge", "--apply", "--grant", "g", state=st)
        merged = [c[3] for c in f.calls if c[:3] == ["gh", "pr", "merge"]]
        return (rc == HALT and "PARK #2 mergeable=CONFLICTING" in out and "#3 left unmerged" in out
                and merged == ["1"]), out

    def unknown_mergeable_polls_then_parks():
        f = FakeForge(1)
        st = verified(f, "uk.json")
        f.view_override = {1: {"mergeable": "UNKNOWN"}}
        rc, out = go(f, "merge", "--apply", "--grant", "g", state=st)
        return rc == HALT and "mergeable=UNKNOWN after 3 polls" in out and f.sleeps == [5, 10], (out, f.sleeps)

    def push_is_refused_before_the_runner():
        f = FakeForge(1)
        a = build_parser().parse_args(["plan", "--base", "main", "--state", os.path.join(tmp, "p.json")])
        t = Train(a, f, io.StringIO(), f.sleeps.append)
        try:
            t.run(["git", "push", "--force", "origin", "main"])
            return False, "no HALT"
        except Halt:
            return not any("push" in c for c in f.calls), f.calls

    def forge_outage_fails_closed():
        f = FakeForge(1)
        f.fail_prefix = ["gh", "pr", "list"]
        rc, out = go(f, "verify", "--verify-cmd", "t", state=fresh("o.json"))
        return rc == ERROR and "not verified" in out and not f.gates, out

    def untrusted_text_is_sanitised():
        return clean("a\x1b[31mb\nc") == "a?[31mb?c", clean("a\x1b[31mb\nc")

    cases = [
        ("plan-filters-latest-check-per-name-and-K", plan_filters),
        ("culprit-among-four-isolated-and-stays-parked", culprit_among_four_is_isolated_and_stays_parked),
        ("conflicts-all-parked-in-one-cycle-no-sleep", conflicts_all_parked_in_one_cycle_without_sleeping),
        ("flaky-passes-on-retry-bounded-backoff", flaky_passes_on_retry_with_bounded_backoff),
        ("deterministic-failure-parks-member", deterministic_failure_parks_member),
        ("all-members-bad-is-red", all_members_bad_is_red),
        ("red-base-halts", red_base_halts),
        ("ratchet-overshoot-attributed-per-member", ratchet_overshoot_attributed_per_member),
        ("dry-run-is-default", dry_run_is_default),
        ("apply-needs-grant", apply_needs_grant),
        ("apply-merges-back-to-back", apply_merges_back_to_back),
        ("base-moved-halts-without-reverify", base_moved_halts_without_reverify),
        ("base-rewritten-halts", base_rewritten_halts),
        ("intruder-mid-train-halts", intruder_mid_train_halts),
        ("merge-time-conflict-parks-and-halts", merge_time_conflict_parks_and_halts),
        ("unknown-mergeable-polls-then-parks", unknown_mergeable_polls_then_parks),
        ("push-refused-before-runner", push_is_refused_before_the_runner),
        ("forge-outage-fails-closed", forge_outage_fails_closed),
        ("untrusted-text-sanitised", untrusted_text_is_sanitised),
    ]
    try:
        return bc.run_checks("merge_train", cases)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None) -> int:
    """CLI entry point. Returns the process exit code."""
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return _selftest()
    return run(argv)


if __name__ == "__main__":
    sys.exit(main())
