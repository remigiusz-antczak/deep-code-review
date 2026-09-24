#!/usr/bin/env python3
"""Escaped-defect ledger: count regressions per window and tie them to cost cuts.

An escaped defect is a bug found after merge. Its fix commit carries a
`Regression-Of: <sha>` trailer naming the commit that introduced it, plus an
optional `Severity: <Blocker|Critical|High|Medium|Low>` trailer. A cost cut is
a commit carrying a `Cost-Cut: <what was cut>` trailer. Doctrine:
agentic-delivery/references/cost-quality-guardrails.md.

  escaped_defects.py --since DATE [--until DATE] [--baseline-start DATE] [--gh]

Reports, for fix commits dated inside the window: how many carry
Regression-Of, how many of those point at a cost-cut commit, and how many
cost cuts landed in the window. Rules it enforces (exit 1):
  - an escaped Blocker whose Regression-Of sha is a cost-cut commit prints
    `REVERT <cut sha>` — that cut is reverted, no trend analysis;
  - more than one cost cut in the window is ambiguous attribution;
  - with --baseline-start, a cost cut dated within 28 days of it lands
    inside the baseline window.
A Regression-Of sha that does not resolve to a commit is reported
UNRESOLVED and never tied to anything (skip rather than guess). --gh also
counts issues labelled `escaped` created in the window via the GitHub CLI
when it is installed; otherwise it prints that the count was skipped.

Exit codes: 0 clean, 1 a rule fired, 2 usage or git error (fail closed).
Side effects: none (reads git; --gh runs a read-only `gh issue list`).
"""
import argparse
import datetime
import shutil
import subprocess
import sys

BASELINE_DAYS = 28


class LedgerError(Exception):
    """A git failure or bad argument (exit 2)."""


def _git(repo, *args):
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise LedgerError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def _commits(repo, since, until, key):
    """[(sha, iso_date, [trailer values], severity)] for commits in the window carrying `key`."""
    fmt = f"%H%x00%cI%x00%(trailers:key={key},valueonly,separator=%x01)%x00%(trailers:key=Severity,valueonly)%x1e"
    args = ["log", f"--format={fmt}", f"--since={since}"]
    if until:
        args.append(f"--until={until}")
    out = []
    for rec in _git(repo, *args).split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, date, vals, sev = rec.split("\x00")
        vals = [v.strip() for v in vals.split("\x01") if v.strip()]
        if vals:
            out.append((sha, date, vals, sev.strip().split("\n")[0].strip()))
    return out


def _cut_of(repo, ref):
    """(full sha, Cost-Cut text or '') for a commit ref, or (None, '') if it does not resolve."""
    proc = subprocess.run(["git", "-C", repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None, ""
    sha = proc.stdout.strip()
    cut = _git(repo, "log", "-1", "--format=%(trailers:key=Cost-Cut,valueonly)", sha).strip()
    return sha, cut.split("\n")[0].strip()


def ledger(repo, since, until=None, baseline_start=None):
    """Return (report lines, rule_fired) for the window."""
    lines, fired = [], False
    fixes = _commits(repo, since, until, "Regression-Of")
    cuts = _commits(repo, since, until, "Cost-Cut")
    tied = 0
    for fix, _date, targets, sev in fixes:
        for target in targets:
            sha, cut = _cut_of(repo, target)
            if sha is None:
                lines.append(f"UNRESOLVED {fix[:12]} Regression-Of: {target} (not a commit here; not attributed)")
                continue
            if not cut:
                continue
            tied += 1
            if sev.lower() == "blocker":
                fired = True
                lines.append(f'REVERT {sha[:12]} "{cut}": escaped Blocker fixed by {fix[:12]}')
    summary = [
        f"window: {since}..{until or 'now'}",
        f"fix commits with Regression-Of: {len(fixes)}",
        f"regressions traced to a cost cut: {tied}",
        f"cost cuts in window: {len(cuts)}",
    ]
    if len(cuts) > 1:
        fired = True
        lines.append(f"AMBIGUOUS {len(cuts)} cost cuts in one window; ship one cut per measurement window")
    if baseline_start:
        try:
            end = datetime.date.fromisoformat(baseline_start) + datetime.timedelta(days=BASELINE_DAYS)
        except ValueError:
            raise LedgerError(f"--baseline-start must be YYYY-MM-DD, got {baseline_start!r}")
        for sha, date, vals, _sev in cuts:
            if datetime.date.fromisoformat(date[:10]) < end:
                fired = True
                lines.append(f'BASELINE {sha[:12]} "{vals[0]}" landed before the {BASELINE_DAYS}-day baseline ended ({end})')
    return summary + lines, fired


def gh_escaped(since, until):
    """Count issues labelled `escaped` created in the window, or None when gh is unavailable."""
    if not shutil.which("gh"):
        return None
    created = f"created:{since}..{until}" if until else f"created:>={since}"
    proc = subprocess.run(["gh", "issue", "list", "--label", "escaped", "--state", "all", "--limit", "1000",
                           "--search", created, "--json", "number", "--jq", "length"],
                          capture_output=True, text=True)
    return int(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip().isdigit() else None


def main(argv):
    ap = argparse.ArgumentParser(description="Escaped-defect ledger per measurement window.")
    ap.add_argument("--since", required=True, help="window start (YYYY-MM-DD)")
    ap.add_argument("--until", help="window end (YYYY-MM-DD); default now")
    ap.add_argument("--baseline-start", help="date the 4-week baseline began (YYYY-MM-DD)")
    ap.add_argument("--gh", action="store_true", help="also count issues labelled escaped via the GitHub CLI")
    ap.add_argument("--repo", default=".", help="repository path (default: current directory)")
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        return 2
    try:
        lines, fired = ledger(a.repo, a.since, a.until, a.baseline_start)
    except LedgerError as exc:
        print(f"escaped_defects: {exc} (fail closed)", file=sys.stderr)
        return 2
    if a.gh:
        n = gh_escaped(a.since, a.until)
        lines.insert(4, f"issues labelled escaped: {n}" if n is not None else "issues labelled escaped: skipped (gh unavailable)")
    print("\n".join(lines))
    return 1 if fired else 0


# ---------------------------------------------------------------------------
# --selftest — builds a throwaway repo with dated commits and proves each
# rule fires (and stays quiet when it should).
# ---------------------------------------------------------------------------
def _selftest():
    import os
    import tempfile

    passed = failed = 0

    def case(name, ok):
        nonlocal passed, failed
        passed += bool(ok)
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}")

    tmp = tempfile.mkdtemp(prefix="escaped-defects-selftest-")
    try:
        def git(*a, date=None):
            env = dict(os.environ)
            if date:
                env.update(GIT_AUTHOR_DATE=f"{date}T12:00:00Z", GIT_COMMITTER_DATE=f"{date}T12:00:00Z")
            subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True, env=env)

        def commit(msg, date):
            git("commit", "-q", "--allow-empty", "-m", msg, date=date)
            return _git(tmp, "rev-parse", "HEAD").strip()

        git("init", "-q")
        git("config", "user.name", "Jane Smith")
        git("config", "user.email", "jane@example.com")
        feat = commit("feat: add cart", "2026-01-05")
        cut = commit("perf: trim review load\n\nCost-Cut: dropped must-load ref from floor", "2026-02-10")
        commit(f"fix: cart total\n\nRegression-Of: {feat}\nSeverity: High", "2026-02-12")
        commit(f"fix: missed injection\n\nRegression-Of: {cut[:10]}\nSeverity: Blocker", "2026-02-14")
        commit("fix: ghost\n\nRegression-Of: deadbeefdeadbeef\nSeverity: Blocker", "2026-02-15")

        lines, fired = ledger(tmp, "2026-02-01", "2026-02-28")
        text = "\n".join(lines)
        case("counts-fix-commits-with-regression-of", "fix commits with Regression-Of: 3" in text)
        case("ties-regression-to-cost-cut", "regressions traced to a cost cut: 1" in text)
        case("escaped-blocker-on-cut-prints-revert", f"REVERT {cut[:12]}" in text and fired)
        case("unresolved-sha-reported-not-attributed", "UNRESOLVED" in text and text.count("REVERT") == 1)

        lines, fired = ledger(tmp, "2026-02-12", "2026-02-13")
        case("non-cut-regression-does-not-fire", not fired and "traced to a cost cut: 0" in "\n".join(lines))

        commit("perf: cache\n\nCost-Cut: halved CI matrix", "2026-02-20")
        lines, fired = ledger(tmp, "2026-02-16", "2026-02-28")
        case("single-cut-window-clean", not fired)
        lines, fired = ledger(tmp, "2026-02-01", "2026-02-28")
        case("two-cuts-in-window-ambiguous", fired and any(l.startswith("AMBIGUOUS") for l in lines))

        lines, fired = ledger(tmp, "2026-02-16", "2026-02-28", baseline_start="2026-02-01")
        case("cut-inside-baseline-fires", fired and any(l.startswith("BASELINE") for l in lines))
        lines, fired = ledger(tmp, "2026-02-16", "2026-02-28", baseline_start="2026-01-01")
        case("cut-after-baseline-clean", not fired)

        case("bad-baseline-date-exit-2", main(["--repo", tmp, "--since", "2026-02-16", "--baseline-start", "Feb"]) == 2)
        case("not-a-repo-exit-2", main(["--repo", os.path.join(tmp, "nope"), "--since", "2026-01-01"]) == 2)
        case("missing-since-exit-2", main(["--repo", tmp]) == 2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nselftest: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main(sys.argv[1:]))
