#!/usr/bin/env python3
"""Validate an idea-critic verdict JSON file.

Exit 0 = valid, 1 = contract violation, 2 = usage or unreadable input.
Stdlib only. Reports field names, never file contents that might be private.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NoReturn

REQUIRED = (
    "verdict",
    "independence",
    "origin",
    "claim",
    "steelman",
    "hats_run",
    "assumptions",
    "better_ways",
    "kill_criteria",
    "strongest_attack_survived",
    "questions_parent_must_resolve",
    "user_question",
    "dissent_ledger",
    "remaining_risk",
)
VERDICTS = {"HOLD", "REVISE", "PASS_TO_USER"}
INDEPENDENCE = {"inline", "independent"}
ORIGINS = {"owner-request", "agent-originated"}
# Phrases that read as a performative, non-attacking "attack" — a
# strongest_attack_survived that reduces to one of these defeats the point
# of the field (see idea-critic/SKILL.md, verdict schema).
GENERIC_PASS_PHRASES = {
    "none",
    "n/a",
    "na",
    "no issues found",
    "no issues",
    "looks good",
    "nothing",
    "no objections",
    "no attack",
    "not applicable",
}


def die(code: int, msg: str) -> NoReturn:
    print(f"validate_verdict: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("--file", "-f"):
        die(2, "usage: validate_verdict.py --file <verdict.json>")
    path = Path(argv[2])
    if not path.is_file():
        die(2, f"not a file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        die(2, "unreadable or malformed JSON")
    if not isinstance(data, dict):
        die(1, "verdict must be a JSON object")

    missing = [k for k in REQUIRED if k not in data]
    if missing:
        die(1, f"missing key(s): {', '.join(missing)}")

    verdict = data["verdict"]
    origin = data["origin"]
    independence = data["independence"]
    user_q = data["user_question"]
    steelman = data["steelman"]
    strongest_attack = data["strongest_attack_survived"]

    if verdict not in VERDICTS:
        die(1, "verdict must be HOLD | REVISE | PASS_TO_USER")
    if origin not in ORIGINS:
        die(1, "origin must be owner-request | agent-originated")
    if independence not in INDEPENDENCE:
        die(1, "independence must be inline | independent")
    if origin == "owner-request" and verdict == "HOLD":
        die(1, "owner-request + HOLD is illegal")
    if isinstance(user_q, list):
        die(1, "user_question must be one line or NONE, never a list")
    if not isinstance(user_q, str) or not user_q.strip():
        die(1, "user_question must be a non-empty string or NONE")
    if not isinstance(steelman, str) or not steelman.strip():
        die(1, "steelman must be a non-empty string")
    # Only PASS_TO_USER is checked for content: HOLD/REVISE never reach the
    # owner, so a thin strongest_attack_survived there is not yet the defect
    # this field exists to catch (it becomes one the moment the verdict
    # would surface unattacked to the owner).
    if verdict == "PASS_TO_USER":
        if not isinstance(strongest_attack, str) or not strongest_attack.strip():
            die(1, "PASS_TO_USER requires a non-empty strongest_attack_survived")
        if strongest_attack.strip().lower() in GENERIC_PASS_PHRASES:
            die(
                1,
                "strongest_attack_survived reads as generic/performative, not a real attack",
            )
    print("validate_verdict: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
