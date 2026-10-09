#!/usr/bin/env python3
"""Offline tests for bench_corpus.py run isolation: a run dir is fresh, immutable-named and single-owner; readers take one complete run."""
import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_corpus as bc  # noqa: E402
from test_bench_corpus import OK, corpus_with, proc  # noqa: E402


class RunIsolation(unittest.TestCase):
    def test_concurrent_drivers_cannot_share_a_dir(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(time, "strftime", return_value="T"):
            wins, losses, gate = [], [], threading.Barrier(8)

            def drive():
                gate.wait()
                try:
                    wins.append(bc.start_run(Path(t) / "runs", "perun", 1))
                except FileExistsError:
                    losses.append(1)
            ts = [threading.Thread(target=drive) for _ in range(8)]
            [x.start() for x in ts]; [x.join() for x in ts]
            self.assertEqual((len(wins), len(losses)), (1, 7))

    def test_manifest_and_name(self):
        with tempfile.TemporaryDirectory() as t:
            sk = Path(t) / "skill"; sk.mkdir(); (sk / "SKILL.md").write_text("x")
            d = bc.start_run(Path(t) / "runs", "plain", 2, sk)
            m = json.loads((d / "manifest.json").read_text())
            self.assertRegex(d.name, r"^plain-2-\d{8}T\d{6}Z$")
            self.assertEqual((m["model"], m["arm"], m["rep"], len(m["skill_sha256"])), (bc.MODEL, "plain", 2, 64))
            self.assertIn("--allowedTools", m["claude_args"])
            self.assertIsNone(json.loads((bc.start_run(Path(t) / "runs", "plain", 3) / "manifest.json").read_text())["skill_sha256"])

    def test_cli_run_marks_complete_and_refuses_reuse_and_partial_reads(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(bc.subprocess, "run", return_value=proc(OK)):
            t = Path(t); c = corpus_with(t / "corp")
            (c / "manifest.json").write_text(json.dumps([{"id": "c1", "split": "test"}]))
            argv = ["run", "--corpus", str(c), "--arm", "plain", "--runs", str(t / "runs")]
            with mock.patch.object(time, "strftime", return_value="T"):
                self.assertEqual(bc.main(argv), 0)
                with self.assertRaises(SystemExit) as e:
                    bc.main(argv)
                self.assertIn("refusing to start", str(e.exception))
            run = next((t / "runs").iterdir())
            self.assertTrue((run / "COMPLETE").is_file() and (run / "plain/c1.json").is_file())
            self.assertEqual(bc.main(["report", "--corpus", str(c), "--out", str(run)]), 0)
            (run / "COMPLETE").unlink()
            for cmd in ("report", "verify"):
                with self.assertRaises(SystemExit):
                    bc.main([cmd, "--corpus", str(c), "--out", str(run), "--arm", "plain"])

    def test_perun_gap_needs_complete_base_and_leaves_it_untouched(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t); c = corpus_with(t / "corp")
            (c / "manifest.json").write_text(json.dumps([{"id": "c1", "split": "test"}]))
            base = bc.start_run(t / "runs", "perun", 1); (base / "perun").mkdir()
            (base / "perun/c1.json").write_text(json.dumps(dict(id="c1", findings=[], cost=0, seconds=0, turns=0, raw="", error="")))
            argv = ["run", "--corpus", str(c), "--arm", "perun-gap", "--runs", str(t / "runs"), "--base", str(base)]
            with self.assertRaises(SystemExit):
                bc.main(argv)  # base not COMPLETE
            (base / "COMPLETE").write_text("1 cases\n")
            before = (base / "perun/c1.json").read_bytes()
            with mock.patch.object(bc.subprocess, "run", return_value=proc(OK)), mock.patch.object(time, "strftime", return_value="G"):
                self.assertEqual(bc.main(argv), 0)
            self.assertEqual((base / "perun/c1.json").read_bytes(), before)
            self.assertTrue((t / "runs/perun-gap-1-G/perun/c1.json").is_file())


if __name__ == "__main__":
    unittest.main()
