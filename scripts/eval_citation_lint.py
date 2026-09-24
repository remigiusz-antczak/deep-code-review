#!/usr/bin/env python3
"""eval_citation_lint.py — flag a routed references/*.md file with zero evals
citing it by name.

WHY THIS EXISTS: a rule moved out of a SKILL.md must-load body and into a
references/*.md file is only as trustworthy as the proof its trigger still
fires. `docs/standards-index.md`/CLAUDE.md already require every
references/*.md to be ROUTED from SKILL.md (a "read this when..." pointer);
this script checks the companion claim — that at least one row in the same
skill's evals/evals.json actually exercises that file (cites its basename in
the eval's id/prompt/expected_output/expectations), so "the doctrine is
tested" is a checked fact, not an assumption. A file with zero citing evals
is not proven to fire; it may be dead prose.

WHAT COUNTS AS "ROUTED" / "CITED"
----------------------------------
Routed: <skill>/SKILL.md's raw text contains the reference file's basename
(the same substring check CLAUDE.md's own pre-commit routing check uses —
see this repo's root CLAUDE.md). Cited: the JSON-serialized text of at least
one entry in <skill>/evals/evals.json contains that basename as a substring.
Both checks are deliberately loose (substring, not a parsed link) — the
routing convention already relies on this same substring shape, and a false
negative (a file cited in prose that doesn't literally contain the filename)
is the fail-closed direction: this script under-credits, it does not
over-credit an uncited file as covered.

SCOPE: a skill with no `references/` directory or no `evals/evals.json` is
skipped (nothing to check), never a failure — plenty of skills are prose-only
or have no evals yet; this lint only judges skills that HAVE both.

USAGE
  eval_citation_lint.py <skill-dir> [<skill-dir> ...]   report coverage
  eval_citation_lint.py --gate <skill-dir> [...]        exit 1 on any
                                                          routed-but-uncited file
  eval_citation_lint.py --selftest                      run built-in selftest

Exit codes: 0 clean (or advisory-only findings without --gate); 1 under
--gate with at least one routed-but-uncited reference file; 2 a named
<skill-dir> does not exist (fail closed, never a silent skip of a typo'd path).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

OK = 0
GATE_FAIL = 1
ERROR = 2


def find_uncited(skill_dir: Path) -> list[str]:
    """Return the basenames of every references/*.md file in `skill_dir`
    that IS routed from SKILL.md but is cited by NO eval in evals/evals.json.
    Returns [] when the skill has no references/ dir or no evals.json (both
    are legitimate "nothing to check" states, not findings)."""
    refs_dir = skill_dir / "references"
    evals_path = skill_dir / "evals" / "evals.json"
    if not refs_dir.is_dir() or not evals_path.is_file():
        return []

    skill_md = skill_dir / "SKILL.md"
    skill_text = skill_md.read_text(encoding="utf-8", errors="replace") if skill_md.is_file() else ""
    evals_text = evals_path.read_text(encoding="utf-8", errors="replace")
    try:
        # Re-serialize so a citation split oddly across raw JSON formatting
        # (unlikely, but this is cheap insurance) still matches; falls back
        # to the raw text if the file doesn't parse as JSON.
        evals_text = json.dumps(json.loads(evals_text))
    except (json.JSONDecodeError, ValueError):
        pass

    uncited = []
    for ref in sorted(refs_dir.glob("*.md")):
        name = ref.name
        if name not in skill_text:
            continue  # not routed -- CLAUDE.md's own routing check owns this, not this lint
        if name not in evals_text:
            uncited.append(name)
    return uncited


def _selftest() -> int:
    import tempfile

    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = Path(tmp) / "sample-skill"
        (skill_dir / "references").mkdir(parents=True)
        (skill_dir / "evals").mkdir()
        (skill_dir / "SKILL.md").write_text(
            "read a.md when doing A. read b.md when doing B.\n", encoding="utf-8"
        )
        (skill_dir / "references" / "a.md").write_text("# A\n", encoding="utf-8")
        (skill_dir / "references" / "b.md").write_text("# B\n", encoding="utf-8")
        (skill_dir / "evals" / "evals.json").write_text(
            json.dumps({"skill_name": "sample-skill", "evals": [
                {"id": "cites-a", "prompt": "about a.md", "expected_output": "x", "expectations": []},
            ]}),
            encoding="utf-8",
        )

        uncited = find_uncited(skill_dir)
        if uncited != ["b.md"]:
            failures.append(f"expected ['b.md'] uncited, got {uncited}")

        # An unrouted file (not named in SKILL.md) must never be reported --
        # that gap belongs to the routing check, not this one.
        (skill_dir / "references" / "c-unrouted.md").write_text("# C\n", encoding="utf-8")
        uncited2 = find_uncited(skill_dir)
        if "c-unrouted.md" in uncited2:
            failures.append(f"unrouted file must not be reported, got {uncited2}")

        # A skill with no evals/evals.json is skipped entirely, not flagged.
        no_evals_skill = Path(tmp) / "no-evals-skill"
        (no_evals_skill / "references").mkdir(parents=True)
        (no_evals_skill / "SKILL.md").write_text("read x.md when doing X.\n", encoding="utf-8")
        (no_evals_skill / "references" / "x.md").write_text("# X\n", encoding="utf-8")
        if find_uncited(no_evals_skill) != []:
            failures.append("skill with no evals.json must return [] (nothing to check)")

        # main() --gate exit code wiring.
        import contextlib
        import io

        with contextlib.redirect_stdout(io.StringIO()):
            rc = main([str(skill_dir)])
        if rc != OK:
            failures.append(f"non-gate mode: exit {rc}, want {OK}")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main(["--gate", str(skill_dir)])
        if rc != GATE_FAIL:
            failures.append(f"--gate mode with an uncited file: exit {rc}, want {GATE_FAIL}")

        missing = Path(tmp) / "does-not-exist"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = main([str(missing)])
        if rc != ERROR:
            failures.append(f"nonexistent skill-dir: exit {rc}, want {ERROR}")

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("SELFTEST OK: 5/5 cases passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill_dirs", nargs="*", metavar="SKILL_DIR")
    parser.add_argument("--gate", action="store_true", help="exit 1 on any routed-but-uncited file")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.skill_dirs:
        parser.error("at least one SKILL_DIR is required")
        return ERROR  # pragma: no cover — parser.error() already exits(2)

    any_uncited = False
    for raw in args.skill_dirs:
        skill_dir = Path(raw)
        if not skill_dir.is_dir():
            print(f"eval_citation_lint: skill dir not found: {skill_dir}", file=sys.stderr)
            return ERROR
        uncited = find_uncited(skill_dir)
        if not uncited:
            print(f"eval_citation_lint: {skill_dir.name}: ok (no routed-but-uncited references)")
            continue
        any_uncited = True
        for name in uncited:
            print(f"UNCITED: {skill_dir.name}/references/{name} is routed from SKILL.md"
                  " but no eval cites it by name")

    if args.gate and any_uncited:
        return GATE_FAIL
    return OK


if __name__ == "__main__":
    sys.exit(main())
