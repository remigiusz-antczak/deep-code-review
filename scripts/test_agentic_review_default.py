"""Pins the repo-access review default: /review, the PR workflow template and SKILL.md all say it."""
import pathlib
import re
import sys

R = pathlib.Path(__file__).resolve().parent.parent
S = R / ".claude/skills/deep-code-review"
rule = "Report only issues you can point to in the code (file:line) with why it breaks."
wf = (S / "templates/perun-review.yml").read_text()
checks = [
    ("review.md: repo-access instruction", "never on a pasted diff alone" in (R / "commands/review.md").read_text()
     and "Read, Grep and Glob" in (R / "commands/review.md").read_text()),
    ("workflow: checks out PR head", "ref: ${{ github.event.pull_request.head.sha }}" in wf),
    ("workflow: grants Read,Grep,Glob", '--allowedTools "Read,Grep,Glob"' in wf),
    ("workflow: minimal prompt", rule in wf),
    ("SKILL.md: repo-access line with measured numbers",
     bool(re.search(r"Run with repo access.*\+28 pts recall.*\+21 pts precision.*did not help.*bench90-results\.md", (S / "SKILL.md").read_text()))),
]
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + n)
sys.exit(1 if bad else 0)
