#!/usr/bin/env python3
"""Flag a completion status that carries a caveat — "a ✅ that needs an asterisk is a ✗".

A heuristic lint for a review's status table / status lines (deep-code-review
Phase 5; see report-format.md). It surfaces CANDIDATE lines where a positive
completion status (✅ / done / exact / matches / verified / complete) co-occurs
with a hedge (if / only / once / after / unless / requires / except / assuming /
caveat / mostly / but see …) and no downgrade marker (⚠️ / ❌ / ✗ / partial /
blocked / unverified) — i.e. a claim that is only true after a non-default action,
reported green.

It is an aid to human judgement, not a proof. It can over-flag a prose line that
merely contains both a status word and a conditional; a flagged line is a lead to
re-check — downgrade to partial/blocked with the condition as the headline, or
split into a scoped two-status verdict — never an automatic defect. Run it on the
status table, not the whole report, for the least noise.

It also UNDER-flags — a clean exit is never proof the claims are true, only that
no listed pattern matched. Known false negatives:
  * it scans one physical line at a time, so a status and its hedge on different
    (wrapped) lines are missed — keep each status row on a single line;
  * the downgrade suppressor is line-global, so a downgrade word used in prose
    ("no partial coverage") can silence a genuine hedged-green on that line;
  * the token lists are fixed — a completion or hedge word not listed slips past.

Exit 0 = no hedged-green lines, 1 = candidate(s) found, 2 = usage/unreadable.
Stdlib only. Reports line numbers + the tokens matched, not full line content.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NoReturn

# A positive completion status: the claim side of "a ✅ that needs an asterisk".
POSITIVE = (
    "✅",
    "done", "exact", "exactly", "matches", "matched", "match", "verified",
    "complete", "completed",
)
# A hedge: the asterisk. A completion claim true only after one of these is a ✗.
HEDGES = (
    "caveat", "asterisk", "footnote", "mostly", "but see", "unless",
    "assuming", "provided", "as long as", "so long as", "requires",
    "once you", "after you", "after selecting", "except", "only", "if",
)
# An honest downgrade already present → the line is not the failure this catches.
# Both ⚠ code points: bare U+26A0 and U+26A0+U+FE0F (with variation selector).
DOWNGRADE = (
    "⚠️", "⚠", "❌", "✗", "partial", "blocked", "changes-requested", "unverified",
)


def die(code: int, msg: str) -> NoReturn:
    print(f"validate_status_claims: {msg}", file=sys.stderr)
    raise SystemExit(code)


def find(tokens: tuple[str, ...], line_lower: str, line_raw: str) -> list[str]:
    """Return which tokens appear on the line. Emoji/phrases: substring;
    single ASCII words: word-boundary (so 'verified' does not match
    'unverified', and 'complete' does not match 'incomplete')."""
    hits: list[str] = []
    for t in tokens:
        if not t.isascii():  # emoji
            if t in line_raw:
                hits.append(t)
        elif " " in t:  # phrase (incl. the trailing-space "if ")
            if t in line_lower:
                hits.append(t.strip())
        else:  # single word
            if re.search(r"\b" + re.escape(t) + r"\b", line_lower):
                hits.append(t)
    return hits


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("--file", "-f"):
        die(2, "usage: validate_status_claims.py --file <report-or-status-table.md>")
    path = Path(argv[2])
    if not path.is_file():
        die(2, f"not a file: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        die(2, "unreadable input")

    flagged: list[tuple[int, list[str], list[str]]] = []
    for n, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        pos = find(POSITIVE, low, line)
        if not pos:
            continue
        if find(DOWNGRADE, low, line):  # already honestly downgraded
            continue
        hedge = find(HEDGES, low, line)
        if hedge:
            flagged.append((n, pos, hedge))

    if flagged:
        for n, pos, hedge in flagged:
            print(
                f"L{n}: green status {pos} carries a hedge {hedge} — "
                "downgrade (partial/blocked, condition as the headline) or split "
                "into a two-status verdict. A ✅ that needs an asterisk is a ✗."
            )
        print(f"validate_status_claims: {len(flagged)} hedged-green line(s) to re-check")
        return 1
    print("validate_status_claims: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
