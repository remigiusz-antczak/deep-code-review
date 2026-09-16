#!/usr/bin/env python3
"""Flag a completion status that carries a caveat — "a ✅ that needs an asterisk is a ✗".

A heuristic lint for a review's status table / status lines (deep-code-review
Phase 5; see report-format.md). It surfaces CANDIDATE lines where a positive
completion status (✅ / done / exact / matches / verified / complete) co-occurs
with a hedge (if / only / once / after / unless / requires / except / assuming /
caveat / mostly / but see …) and no downgrade marker (⚠️ / ❌ / ✗ / partial /
blocked / unverified) — i.e. a claim that is only true after a non-default action,
reported green.

A second detector (issue #192) flags a positive status whose row also carries
parity vocabulary (parity / renders / restyled / screen / "matches the design" …)
yet names NO verification surface — no URL / port and no rendered sha. When more
than one tree can serve the app, a parity claim that names no surface is INVALID
(there is nothing to downgrade): it may be true about the author's tree yet false
on every surface a human opens, so this detector fires even on a ⚠️-downgraded row.
The sha test requires >= 7 hex chars with both a hex letter and a digit (so neither
a hex-looking word nor a plain number passes as a commit).

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

Exit 0 = no candidate lines (neither detector fired), 1 = candidate(s) found,
2 = usage/unreadable.
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
# UI / parity vocabulary: marks a status line as a design / parity claim, which
# must name a verification surface. A positive parity status naming no surface is
# the failure the second detector catches (issue #192 — "which tree served it?",
# ambiguous the moment more than one tree can serve the app). A broad single word
# ("screen" …) can over-flag a non-parity row ("screen-reader"); a flag is a lead.
SURFACE_VOCAB = (
    "parity", "renders", "rendered", "restyled", "restyle",
    "matches the design", "matches the reference", "looks the same", "screen",
)
# The detector flags a parity row that names NEITHER a URL / port NOR a rendered
# sha (either one present = a surface is named → no flag; issue #192's "no URL and
# no sha"). The sha needs >= 7 hex chars with BOTH a hex letter and a digit, so a
# hex-looking prose word ("defaced") and a plain number ("1234567") are neither
# mistaken for a commit; the URL needs a real host, so a time ("12:30") is not a port.
_URL_RE = re.compile(r"https?://|\blocalhost\b|\b\d{1,3}(?:\.\d{1,3}){3}\b", re.IGNORECASE)
_SHA_RE = re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*[0-9])[0-9a-f]{7,40}\b", re.IGNORECASE)


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

    flagged: list[tuple[int, list[str], list[str]]] = []       # hedged-green
    surfaceless: list[tuple[int, list[str], list[str]]] = []   # UI/parity, no surface
    for n, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        pos = find(POSITIVE, low, line)
        if not pos:
            continue
        # Surfaceless-parity detector runs FIRST and regardless of a downgrade
        # marker: a parity claim that names no surface is INVALID, not merely
        # downgraded — a ⚠️ does not rescue it (report-format.md), so the downgrade
        # marker must not suppress this half.
        surf = find(SURFACE_VOCAB, low, line)
        if surf and not _URL_RE.search(line) and not _SHA_RE.search(line):
            surfaceless.append((n, pos, surf))
        # Hedged-green detector: an honest downgrade already surfaces the caveat, so
        # a downgraded line is not the failure THIS half catches.
        if find(DOWNGRADE, low, line):
            continue
        hedge = find(HEDGES, low, line)
        if hedge:
            flagged.append((n, pos, hedge))

    if flagged or surfaceless:
        for n, pos, hedge in flagged:
            print(
                f"L{n}: green status {pos} carries a hedge {hedge} — "
                "downgrade (partial/blocked, condition as the headline) or split "
                "into a two-status verdict. A ✅ that needs an asterisk is a ✗."
            )
        for n, pos, surf in surfaceless:
            print(
                f"L{n}: green UI/parity status {pos} names no verification surface "
                f"(vocab {surf}) — a parity claim with no URL and no rendered sha is "
                "INVALID, not downgraded; name url · tree/worktree · branch · sha, or "
                "make no claim (#192)."
            )
        total = len(flagged) + len(surfaceless)
        print(
            f"validate_status_claims: {total} line(s) to re-check "
            f"({len(flagged)} hedged-green, {len(surfaceless)} surfaceless parity)"
        )
        return 1
    print("validate_status_claims: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
