#!/usr/bin/env python3
"""compact-mode reference: routed from SKILL.md, under 2.5KB, bench data present."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / ".claude/skills/deep-code-review"


class CompactMode(unittest.TestCase):
    def test_routed_with_trigger(self):
        line = [l for l in (SK / "SKILL.md").read_text().splitlines() if "references/compact-mode.md" in l]
        self.assertTrue(line and "Non-Claude" in line[0])

    def test_size_and_header(self):
        t = (SK / "references/compact-mode.md").read_text()
        self.assertLess(len(t.encode()), 2500)
        self.assertTrue(t.startswith("Read this when the model running this skill is not Claude"))
        self.assertIn("SKILL.md stays the source of truth", t.splitlines()[1])

    def test_bench_data(self):
        self.assertTrue((ROOT / "docs/bench/xmodel2-summary.md").is_file())
        self.assertIn("bench/xmodel2-summary.md", (ROOT / "docs/host-safety.md").read_text())


if __name__ == "__main__":
    unittest.main()
