"""Pins the lean /review path: DIFF/FILE must not load the full SKILL.md; FULL and --high-stakes still do."""
import pathlib
import sys

R = pathlib.Path(__file__).resolve().parent.parent
t = (R / "commands/review.md").read_text()
lean, _, full = t.partition("For `FULL` scope")
checks = [
    ("DIFF/FILE: skill not loaded", "do not load the `deep-code-review` skill" in lean),
    ("DIFF/FILE: file:line + why-it-breaks bar", "file:line" in lean and "why it breaks" in lean),
    ("FULL and --high-stakes still load the skill", "load the `deep-code-review`" in full and "--high-stakes" in full),
    ("high-stakes Opus single pass kept", "same single pass on\nOpus" in full and "do not add a second pass" in full),
    ("default scope kept", "DIFF origin/main" in lean),
]
for n, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + n)
sys.exit(1 if [1 for _, ok in checks if not ok] else 0)
