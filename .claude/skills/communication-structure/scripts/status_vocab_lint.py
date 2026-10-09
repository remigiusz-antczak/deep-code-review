#!/usr/bin/env python3
"""status_vocab_lint.py --file F — flag unverified "live"/"done" claims in a human-facing update.

Status vocabulary: merged, deployed and verified-on-<page> are distinct states. "live", "live now",
"shipped to users" and "done" claim the last one, so each needs a `verified-on-<page>` / `verified on <page>`
or a `journey:` reference on the same or an adjacent line. Otherwise say what is true: "merged", "deployed,
unverified". Prints `L<n>: <phrase> ...` per hit; exit 1 on any hit, 0 clean, 2 usage/unreadable.
Fenced and inline code is ignored. Limits: line-based keyword heuristic (a "go live" plan or "done" meaning something else is a false hit; a
lead to reword, not a defect); a clean run proves only that no listed phrase appeared.
"""
import re
import sys

CLAIM = re.compile(r"\b(live now|live|shipped to users|done)\b", re.I)
CODE = re.compile(r"`[^`]*`")
EVIDENCE = re.compile(r"verified[- ]on[- ]\S+|\bjourney:", re.I)


def lint(text):
    """Return [(line_no, phrase)] for claims with no evidence on the line or its neighbours."""
    lines, fence = [], False
    for line in text.splitlines():  # blank out fenced and inline code: quoted code is not a status claim
        if line.lstrip().startswith("```"):
            fence = not fence
            line = ""
        lines.append("" if fence else CODE.sub("", line))
    hits = []
    for i, line in enumerate(lines):
        m = CLAIM.search(line)
        if m and not any(EVIDENCE.search(x) for x in lines[max(0, i - 1):i + 2]):
            hits.append((i + 1, m.group(1).lower()))
    return hits


def main(argv):
    if len(argv) != 3 or argv[1] != "--file":
        print("usage: status_vocab_lint.py --file <update.md>", file=sys.stderr)
        return 2
    try:
        text = open(argv[2], encoding="utf-8").read()
    except (OSError, UnicodeError):
        print("status_vocab_lint: unreadable input", file=sys.stderr)
        return 2
    hits = lint(text)
    for n, p in hits:
        print(f"L{n}: '{p}' with no verified-on-<page> or journey: reference; say merged / deployed, or cite the check")
    print(f"status_vocab_lint: {'%d hit(s)' % len(hits) if hits else 'ok'}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
