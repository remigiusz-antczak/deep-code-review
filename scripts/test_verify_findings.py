#!/usr/bin/env python3
"""Offline tests for verify_findings.py: batching, fail-closed merge, tolerant verdict parsing, CLI."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import verify_findings as vf  # noqa: E402

FS = [{"id": f"F{i}", "file": f"f{i}.sh", "text": f"bug {i}"} for i in range(1, 8)]


def v(i, verdict, ev="x.sh:1", basis="tool"):
    return {"id": i, "verdict": verdict, "evidence": ev, "basis": basis}


class VerifyFindings(unittest.TestCase):
    def test_selftest(self):
        self.assertTrue(vf.selftest())

    def test_batching_bounds_verifier_count(self):
        ps = vf.prompts(FS, 3, "abc123")
        self.assertEqual([len(p["ids"]) for p in ps], [3, 3, 1])
        self.assertIn("at abc123", ps[0]["prompt"])
        self.assertNotIn("F4", ps[0]["prompt"])  # a verifier sees only its batch

    def test_confirmed_needs_evidence_and_missing_is_unverified(self):
        r = vf.merge(FS, [v("F1", "confirmed"), v("F2", "confirmed", ""), v("F3", "refuted"), v("F4", "bogus")])
        self.assertEqual([f["id"] for f in r["confirmed"]], ["F1"])
        self.assertEqual([f["id"] for f in r["unverified"]], ["F2", "F4", "F5", "F6", "F7"])
        self.assertEqual(r["counts"], {"candidates": 7, "confirmed": 1, "unverified": 5, "refuted": 1})

    def test_model_only_or_missing_basis_never_settles(self):
        r = vf.merge(FS[:3], [v("F1", "confirmed", basis="model-only"), v("F2", "refuted", basis=""), {"id": "F3", "verdict": "confirmed", "evidence": "a:1"}])
        self.assertEqual((len(r["confirmed"]), r["refuted_count"], len(r["unverified"])), (0, 0, 3))

    def test_refuted_without_evidence_is_not_dropped(self):
        r = vf.merge(FS[:1], [v("F1", "refuted", "")])
        self.assertEqual((r["refuted_count"], len(r["unverified"])), (0, 1))

    def test_conflicting_verdicts_settle_nothing(self):
        r = vf.merge(FS[:1], [v("F1", "confirmed"), v("F1", "refuted")])
        self.assertEqual((len(r["confirmed"]), r["refuted_count"], len(r["unverified"])), (0, 0, 1))

    def test_unknown_ids_and_prose_tolerated(self):
        ans = vf.parse_verdicts('Here you go:\n{"id": "F1", "verdict": "confirmed", "basis": "tool", "evidence": "a:1"}\nnot json {oops}\n{"id": "ZZ", "verdict": "refuted", "basis": "tool", "evidence": "b:2"}')
        r = vf.merge(FS[:1], ans)
        self.assertEqual((len(r["confirmed"]), r["unknown_ids"]), (1, ["ZZ"]))

    def test_braces_inside_evidence_do_not_drop_a_verdict(self):
        a = vf.parse_verdicts('```\n{"id": "F1", "verdict": "confirmed", "basis": "tool", "evidence": "uses ${VAR} and {}"}\n```')
        self.assertEqual([x["id"] for x in a], ["F1"])

    def test_cli_roundtrip_and_bad_input(self):
        d = Path(tempfile.mkdtemp())
        (d / "f.json").write_text(json.dumps([{"file": "a.sh", "text": "t"}]))
        (d / "v.txt").write_text('{"id": "F1", "verdict": "confirmed", "basis": "tool", "evidence": "a.sh:1"}')
        run = lambda *a: subprocess.run([sys.executable, str(SCRIPTS / "verify_findings.py"), *a], capture_output=True, text=True)
        self.assertEqual(json.loads(run("merge", str(d / "f.json"), str(d / "v.txt")).stdout)["counts"]["confirmed"], 1)
        self.assertEqual(run("prompts", str(d / "nope.json")).returncode, 2)
        (d / "dup.json").write_text(json.dumps([{"id": "A", "text": "t"}, {"id": "A", "text": "u"}]))
        self.assertEqual(run("prompts", str(d / "dup.json")).returncode, 2)


if __name__ == "__main__":
    unittest.main()
