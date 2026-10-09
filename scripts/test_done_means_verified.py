#!/usr/bin/env python3
"""Offline tests: journey/postdeploy receipt refusal in lane_guard handback, and status_vocab_lint."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(ROOT, ".claude/skills/agentic-delivery/scripts/lane_guard.py")
LINT = os.path.join(ROOT, ".claude/skills/communication-structure/scripts/status_vocab_lint.py")
EVALS = os.path.join(ROOT, ".claude/skills/communication-structure/evals/evals.json")


def run(args, cwd=None):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


class Receipt(unittest.TestCase):
    def repo(self, changed):
        d = tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))
        g = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *a],
                                      cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        g("init", "-q", "-b", "main")
        open(os.path.join(d, "a.txt"), "w").write("x")
        g("add", "."), g("commit", "-qm", "base")
        g("checkout", "-qb", "lane")
        open(os.path.join(d, changed), "w").write("y")
        g("add", "."), g("commit", "-qm", "change")
        self.d, self.sha = d, g("rev-parse", "HEAD")
        return d

    def handback(self, receipt_text=None, *extra):
        args = [sys.executable, GUARD, "handback", "--sha", self.sha, "--base", "main", "--branch", "lane", *extra]
        if receipt_text is not None:
            r = os.path.join(self.d, "receipt.txt")
            open(r, "w").write(receipt_text)
            args += ["--receipt", r]
        return run(args, self.d)

    def test_ui_change_without_receipt_refused(self):
        self.repo("page.tsx")
        code, out = self.handback()
        self.assertEqual(code, 1, out)
        self.assertIn("--receipt", out)

    def test_ui_change_without_journey_line_refused(self):
        self.repo("style.css")
        code, out = self.handback("tests: green\njourney: /home click FAIL\n")
        self.assertEqual(code, 1, out)
        self.assertIn("journey", out)

    def test_ui_change_with_journey_passes(self):
        self.repo("page.tsx")
        code, out = self.handback("journey: /settings click-save,reload,assert-saved PASS\n")
        self.assertEqual(code, 0, out)

    def test_non_ui_change_needs_no_receipt(self):
        self.repo("lib.py")
        self.assertEqual(self.handback()[0], 0)

    def test_deployed_without_postdeploy_line_is_unverified(self):
        self.repo("lib.py")
        code, out = self.handback("tests: green\n", "--deployed")
        self.assertEqual(code, 1, out)
        self.assertIn("deployed, unverified", out)

    def test_deployed_with_errors_refused_clean_passes(self):
        self.repo("lib.py")
        code, out = self.handback("postdeploy-logs: 12x 4xx from billing\n", "--deployed")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.handback("postdeploy-logs: clean\n", "--deployed")[0], 0)


class StatusLint(unittest.TestCase):
    def lint(self, text):
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, dir=os.environ.get("TMPDIR"))
        f.write(text), f.close()
        return run([sys.executable, LINT, "--file", f.name])

    def test_flags_unverified_claims(self):
        for t in ("The export is live now.", "Shipped to users today.", "All 12 features are done.", "Live!"):
            self.assertEqual(self.lint(t)[0], 1, t)

    def test_evidence_nearby_or_honest_words_pass(self):
        for t in ("Export is live; verified-on-/reports.", "Done.\njourney: /reports click,reload PASS",
                  "Merged. Deployed, unverified."):
            self.assertEqual(self.lint(t)[0], 0, t)

    def test_unreadable_is_usage_error(self):
        self.assertEqual(run([sys.executable, LINT, "--file", "/nonexistent"])[0], 2)

    def test_eval_case_present(self):
        ids = {e["id"] for e in json.load(open(EVALS))["evals"]}
        self.assertIn("status-vocabulary-merged-deployed-verified", ids)


if __name__ == "__main__":
    unittest.main()
