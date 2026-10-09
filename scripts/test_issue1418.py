#!/usr/bin/env python3
"""Issue 1418: prose-only not-applicable coverage rows are downgraded; repeatability metric reports known numbers."""
import sys
import unittest
from pathlib import Path

DCR = Path(__file__).resolve().parent.parent / ".claude/skills/deep-code-review/scripts"
sys.path.insert(0, str(DCR))
import merge_findings as mf  # noqa: E402
import score_review as sr  # noqa: E402


class NaProbe(unittest.TestCase):
    def test_prose_only_na_downgraded(self):
        cov, flagged = mf.na_gate({"L": {"status": "not-applicable", "note": "no IaC"}})
        self.assertEqual((cov["L"]["status"], flagged), ("not-scanned", ["L"]))

    def test_half_probe_downgraded(self):
        _, flagged = mf.na_gate({"L": {"status": "not-applicable", "probe": "grep x", "fact": " "}})
        self.assertEqual(flagged, ["L"])

    def test_probed_na_kept(self):
        row = {"status": "not-applicable", "probe": "grep x", "fact": "0 hits"}
        self.assertEqual(mf.na_gate({"L": row}), ({"L": row}, []))


class Repeat(unittest.TestCase):
    def test_selftest_numbers(self):
        self.assertTrue(sr._repeat_selftest())

    def test_two_identical_one_divergent(self):
        a = [{"file": "f.py", "line": 10, "severity": "High"}]
        r = sr.repeatability([a, a, [{"file": "f.py", "line": 13, "severity": "Low"}]])
        f = r["findings"][0]
        self.assertEqual((f["presence"], f["severity_agreement"], f["direction"]), (1.0, 0.6667, "down"))


if __name__ == "__main__":
    unittest.main()
