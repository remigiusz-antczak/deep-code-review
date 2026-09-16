#!/usr/bin/env python3
"""Split-rubric eval runner — the execution layer over every skill's evals.json.

`docs/roadmap.md` Loop 2 wants two graders: a deterministic predicate on the
*hard* axes (fabrication / boundary — where a fluent wrong answer fools an LLM
judge) and a decorrelated LLM judge on the *soft* axes. `scripts/eval_predicates.py`
already built the hard half (deterministic predicates + a golden good/red
discrimination gate). This script is the runner that ties both halves together and
reports coverage.

What is BUILT here and safe to run with no key, no network, no spend:
  --dry-run (the DEFAULT)  enumerate every eval in every skill, classify each as
                           HARD (a deterministic predicate is bound for it in
                           eval_predicates.BINDINGS) or SOFT (needs the live judge),
                           re-run the hard-axis discrimination, and print a coverage
                           report as JSON on stdout. Never calls a model.
  --selftest               prove this runner's own guards offline: dry-run works,
                           the decorrelation guard aborts on equal/missing model
                           ids, the spend-cap guard aborts on a missing/non-positive
                           cap, and the live path reaches only the un-built stub.

What is DEFERRED to the owner (a live model call spends money and needs a secret
that lives only on the scheduled/dispatch run against main, never on a PR):
  --live                   validate the subject/judge model configuration, enforce
                           decorrelation and a positive spend cap, then hand off to
                           the model-call site — which is an explicit, un-filled
                           stub (`_live_judge_stub`). This runner ships NO
                           model-calling code, so --live cannot spend by accident;
                           it aborts at the stub after its guards. Wiring a real
                           client there, the scheduled dispatch workflow, and the
                           committed results-freshness gate are the owner-gated
                           remainder of issue #61.

The hard/soft split is derived from eval_predicates.BINDINGS, so no evals.json is
tagged and no skill version is bumped (the same reversibility eval_predicates.py
relies on).

Exit codes:
  --dry-run   0 = every binding resolves and every hard predicate discriminates its
                  golden pair; 1 = a binding is broken or a hard predicate failed to
                  discriminate (fail closed); 2 = usage / an unreadable evals.json /
                  an unwritable --out path.
  --selftest  0 = every offline guard behaved; 1 = a guard is wrong; 2 = usage.
  --live      always non-zero here: 2 when the model configuration is missing or
                  fails decorrelation or the spend cap is missing/non-positive;
                  3 at the owner stub when configuration is valid (the model client
                  is intentionally not built).

Stdlib only. No default model id, ever — a live subject/judge must be named
explicitly in the environment, or the run aborts.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import eval_predicates as ep  # noqa: E402  (sibling script; reuse its predicates + bindings)


def _skills_with_evals(repo: Path) -> "list[str]":
    """Every skill directory that ships an evals/evals.json, sorted."""
    root = repo / ".claude" / "skills"
    return sorted(p.parent.parent.name for p in root.glob("*/evals/evals.json"))


def _hard_index() -> "dict[tuple[str, str], str]":
    """(skill, eval_id) -> predicate name, from the deterministic bindings."""
    return {(b["skill"], b["eval_id"]): b["predicate"] for b in ep.BINDINGS}


def build_coverage(repo: Path) -> "dict":
    """Classify every eval as hard (predicate-bound) or soft (needs live judge).

    Pure enumeration + classification. Makes no model call and reads only the
    committed evals.json files and the in-code bindings. The report carries no
    timestamp, so the same tree produces the same report (a committed
    results-freshness gate can diff it without spurious churn).
    """
    hard = _hard_index()
    skills = []
    total = hard_total = soft_total = 0
    for skill in _skills_with_evals(repo):
        ids = ep._eval_ids(repo, skill)
        if ids is None:
            skills.append({"skill": skill, "error": "unreadable evals.json"})
            continue
        hard_ids = sorted(i for i in ids if (skill, i) in hard)
        soft_ids = sorted(i for i in ids if (skill, i) not in hard)
        total += len(ids)
        hard_total += len(hard_ids)
        soft_total += len(soft_ids)
        skills.append(
            {
                "skill": skill,
                "total": len(ids),
                "hard": hard_ids,          # graded offline by a deterministic predicate
                "soft_pending": soft_ids,  # need the live judge (deferred to owner dispatch)
            }
        )
    return {
        "mode": "dry-run",
        "totals": {"evals": total, "hard": hard_total, "soft_pending": soft_total},
        "skills": skills,
    }


def _validate_bindings(repo: Path) -> "list[str]":
    """Every binding must name an existing predicate and an eval id that exists.

    Returns a list of problems (empty = clean). This is the fail-closed check: a
    binding that points at a renamed/removed eval, or a missing predicate, is a
    defect, not a skip.
    """
    problems = []
    for b in ep.BINDINGS:
        if b["predicate"] not in ep.PREDICATES:
            problems.append(f"{b['skill']}/{b['eval_id']}: unknown predicate {b['predicate']!r}")
            continue
        ids = ep._eval_ids(repo, b["skill"])
        if ids is None:
            problems.append(f"{b['skill']}: evals.json unreadable")
        elif b["eval_id"] not in ids:
            problems.append(f"{b['skill']}: bound eval id {b['eval_id']!r} not present")
    return problems


def decorrelation_error(subject: "str | None", judge: "str | None") -> "str | None":
    """Return why the judge/subject pairing is invalid, or None when it is sound.

    A missing value is an abort, never a vacuous pass (issue #61: "aborts when
    judge==subject model id" — an unset id is not a decorrelated id). Compared by
    identifier only; no vendor/model name is hardcoded here.
    """
    if not subject or not subject.strip():
        return "subject model id is unset (no default is assumed)"
    if not judge or not judge.strip():
        return "judge model id is unset (no default is assumed)"
    if subject.strip() == judge.strip():
        return f"judge and subject are the same model id ({subject.strip()!r}) — not decorrelated"
    return None


def spend_cap_error(raw: "str | None") -> "str | None":
    """Return why the spend cap is invalid, or None when it is a positive number.

    Presence alone is not enough — a `0`, a negative, or a non-numeric cap does not
    bound spend (issue #61: "a per-run spend cap is enforced before each call").
    """
    if raw is None or not raw.strip():
        return "EVAL_SPEND_CAP_USD is unset (bound spend before any paid call)"
    try:
        value = float(raw)
    except ValueError:
        return f"EVAL_SPEND_CAP_USD is not a number ({raw!r})"
    if value <= 0:
        return f"EVAL_SPEND_CAP_USD must be positive (got {value})"
    return None


def _live_judge_stub(*_args, **_kwargs):
    """The single model-call site — intentionally not implemented.

    A real implementation calls the configured judge model, accounts spend against
    the cap before each call, and returns a PASS/FAIL per soft expectation. It is
    left un-built on purpose so this runner ships no code that can spend money; the
    owner wires a client here and runs it from the scheduled/dispatch job where the
    key lives. See issue #61.
    """
    raise NotImplementedError(
        "live judge is owner-operated: implement the model client + per-call spend "
        "accounting here and invoke from the scheduled dispatch (issue #61)"
    )


def run_live(repo: Path) -> int:
    """Guard the live path, then hand off to the (un-built) model-call site.

    Never spends: after the guards it reaches `_live_judge_stub`, which raises. The
    guards exist so that when the owner fills the stub, an unconfigured, correlated,
    or unbounded run still fails closed.
    """
    err = decorrelation_error(os.environ.get("EVAL_SUBJECT_MODEL"), os.environ.get("EVAL_JUDGE_MODEL"))
    if err:
        print(f"run-evals --live: refusing to run — {err}", file=sys.stderr)
        return 2
    err = spend_cap_error(os.environ.get("EVAL_SPEND_CAP_USD"))
    if err:
        print(f"run-evals --live: refusing to run — {err}", file=sys.stderr)
        return 2
    try:
        _live_judge_stub(repo=repo)
    except NotImplementedError as e:
        print(f"run-evals --live: configuration valid, but {e}", file=sys.stderr)
        return 3
    return 0  # unreachable until the stub is implemented


def run_dry_run(repo: Path, out: "Path | None") -> int:
    coverage = build_coverage(repo)
    skill_errors = [s["skill"] for s in coverage["skills"] if "error" in s]
    problems = _validate_bindings(repo)
    # Re-run the hard-axis discrimination gate (the golden good/red pairs), with its
    # stdout redirected to stderr so this command's stdout stays valid JSON. A hard
    # eval whose predicate can no longer tell a refusal from a fabrication is a
    # broken gate, reported here as a failure of the dry run.
    fixtures = SCRIPT_DIR / "eval-fixtures"
    if fixtures.is_dir():
        with contextlib.redirect_stdout(sys.stderr):
            hard_ok = ep.run_selftest(fixtures, repo) == 0
    else:
        hard_ok = None
    report = dict(coverage)
    report["binding_problems"] = problems
    report["skill_errors"] = skill_errors
    report["hard_discrimination"] = (
        "ok" if hard_ok else ("FAILED" if hard_ok is False else "skipped (no fixtures dir)")
    )
    text = json.dumps(report, indent=2)
    if out is not None:
        try:
            out.write_text(text + "\n", encoding="utf-8")
        except OSError as e:
            print(f"run-evals: cannot write --out {out}: {e}", file=sys.stderr)
            return 2
    print(text)  # the only thing on stdout: a valid JSON report
    if skill_errors:
        print(f"\nrun-evals: unreadable evals.json in {skill_errors} — fail closed", file=sys.stderr)
        return 2
    if problems:
        print(f"\nrun-evals: {len(problems)} binding problem(s) — fail closed", file=sys.stderr)
        return 1
    if hard_ok is False:
        print("\nrun-evals: hard-axis predicates failed discrimination — fail closed", file=sys.stderr)
        return 1
    return 0


def run_selftest(repo: Path) -> int:
    """Prove this runner's guards offline. No network, no model, no artifact."""
    checks: "list[tuple[str, bool]]" = []

    cov = build_coverage(repo)
    checks.append(("dry-run enumerates evals", cov["totals"]["evals"] > 0))
    checks.append(("at least one hard eval is bound", cov["totals"]["hard"] > 0))
    checks.append(("some evals are soft (need the live judge)", cov["totals"]["soft_pending"] > 0))

    # Decorrelation guard: equal ids, either unset/blank -> error; distinct ids -> ok.
    checks.append(("equal model ids rejected", decorrelation_error("m", "m") is not None))
    checks.append(("unset subject rejected", decorrelation_error(None, "j") is not None))
    checks.append(("blank judge rejected", decorrelation_error("s", "  ") is not None))
    checks.append(("distinct model ids accepted", decorrelation_error("subject-x", "judge-y") is None))

    # Spend-cap guard: missing / non-positive / non-numeric -> error; positive -> ok.
    checks.append(("missing spend cap rejected", spend_cap_error(None) is not None))
    checks.append(("zero spend cap rejected", spend_cap_error("0") is not None))
    checks.append(("negative spend cap rejected", spend_cap_error("-5") is not None))
    checks.append(("non-numeric spend cap rejected", spend_cap_error("abc") is not None))
    checks.append(("positive spend cap accepted", spend_cap_error("5") is None))

    # The live path must fail closed at each guard and never reach a real call.
    # Drive run_live through all three stages with the env under our control, then
    # restore it. This pins the spend-cap guard (not just the decorrelation guard)
    # and confirms a fully-configured run still only reaches the un-built stub.
    saved = {k: os.environ.pop(k, None) for k in ("EVAL_SUBJECT_MODEL", "EVAL_JUDGE_MODEL", "EVAL_SPEND_CAP_USD")}
    try:
        checks.append(("live refuses with no config", run_live(repo) == 2))
        os.environ["EVAL_SUBJECT_MODEL"] = "subject-x"
        os.environ["EVAL_JUDGE_MODEL"] = "judge-y"
        checks.append(("live refuses without a spend cap", run_live(repo) == 2))
        os.environ["EVAL_JUDGE_MODEL"] = "subject-x"  # now equal -> decorrelation refusal
        os.environ["EVAL_SPEND_CAP_USD"] = "5"
        checks.append(("live refuses correlated models even with a cap", run_live(repo) == 2))
        os.environ["EVAL_JUDGE_MODEL"] = "judge-y"     # distinct + cap set -> reaches the stub
        checks.append(("live with full config reaches the un-built stub (no call)", run_live(repo) == 3))
    finally:
        for k in ("EVAL_SUBJECT_MODEL", "EVAL_JUDGE_MODEL", "EVAL_SPEND_CAP_USD"):
            os.environ.pop(k, None)
            if saved.get(k) is not None:
                os.environ[k] = saved[k]

    # The model-call site is genuinely un-built (cannot spend by accident).
    stub_raises = False
    try:
        _live_judge_stub()
    except NotImplementedError:
        stub_raises = True
    checks.append(("model-call site is an un-built stub", stub_raises))

    ok = True
    for name, passed in checks:
        print(f"{'ok  ' if passed else 'FAIL'} {name}")
        ok = ok and passed
    print("run-evals selftest: ok" if ok else "run-evals selftest: FAILED")
    return 0 if ok else 1


def main(argv: "list[str]") -> int:
    parser = argparse.ArgumentParser(add_help=True, description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="enumerate + classify + check hard predicates, no model (default)")
    mode.add_argument("--selftest", action="store_true", help="prove this runner's guards offline")
    mode.add_argument("--live", action="store_true", help="owner-operated: guarded, then hands off to the un-built model-call site")
    parser.add_argument("--repo", type=Path, default=SCRIPT_DIR.parent)
    parser.add_argument("--out", type=Path, default=None, help="dry-run: also write the coverage report here (gitignored path recommended)")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest(args.repo)
    if args.live:
        return run_live(args.repo)
    return run_dry_run(args.repo, args.out)  # default: dry-run


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
