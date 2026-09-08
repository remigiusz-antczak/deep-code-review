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
    "hats_run",
    "assumptions",
    "better_ways",
    "kill_criteria",
    "questions_parent_must_resolve",
    "user_question",
    "dissent_ledger",
    "remaining_risk",
)
VERDICTS = {"HOLD", "REVISE", "PASS_TO_USER"}
INDEPENDENCE = {"inline", "independent"}
ORIGINS = {"owner-request", "agent-originated"}


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
    print("validate_verdict: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
