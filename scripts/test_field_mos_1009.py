#!/usr/bin/env python3
"""Field bugs (#1380): project-dir hook paths, forced-haiku subagent warning, lane staging hygiene."""
import json, os, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".claude/skills/agentic-delivery/scripts"))
import perun_doctor  # noqa: E402
import operating_selfcheck  # noqa: E402

os.environ["DCR_NO_PROBE"] = "1"
TPL = ROOT / ".claude/skills/agentic-delivery/templates/operating-layer.settings.json"
OLD = "python3 .claude/skills/agentic-delivery/scripts/handback_cap.py"
HAS_JQ = shutil.which("jq") is not None


def cmds(data):
    return [h["command"] for es in data["hooks"].values() for e in es for h in e["hooks"]]


class TemplateTests(unittest.TestCase):
    def test_no_relative_hook_paths(self):
        for c in cmds(json.loads(TPL.read_text())):
            self.assertNotRegex(c, r"python3 \.claude", c)
            self.assertNotRegex(c, r"(?:^|[\s=])\.claude/", c)
            self.assertIn('"$CLAUDE_PROJECT_DIR/.claude/', c)

    def test_template_pins_sonnet_not_haiku(self):
        self.assertEqual(json.loads(TPL.read_text())["env"]["CLAUDE_CODE_SUBAGENT_MODEL"], "sonnet")

    def test_docs_and_preamble(self):
        he = (ROOT / ".claude/skills/agentic-delivery/references/host-enforcement.md").read_text()
        self.assertNotIn('"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"', he)
        self.assertNotRegex(he, r'"command": "[^"\n]*python3 \.claude')
        lp = (ROOT / ".claude/skills/agentic-delivery/templates/lane-preamble.md").read_text()
        self.assertIn("never `git add -A`", lp)
        self.assertIn("hand back its path", lp)


@unittest.skipUnless(HAS_JQ, "jq needed")
class ApplyTests(unittest.TestCase):
    def test_reapply_upgrades_old_relative_entries_without_duplicates(self):
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, True)
        (repo / ".claude").mkdir()
        old = {"hooks": {"SubagentStop": [{"hooks": [{"type": "command", "command": OLD}]}]}}
        (repo / ".claude/settings.local.json").write_text(json.dumps(old))
        for _ in range(2):  # second run proves idempotency
            p = subprocess.run(["bash", str(ROOT / "install.sh"), "--with-delivery", str(repo)], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads((repo / ".claude/settings.local.json").read_text())
        cs = cmds(data)
        self.assertEqual(sum("handback_cap.py" in c and "HANDBACK_MAX" not in c for c in cs), 1, cs)
        self.assertFalse([c for c in cs if re.search(r"python3 \.claude", c)], cs)
        for ev, es in data["hooks"].items():  # perun_auto_update legitimately sits in two events
            ec = [h["command"] for e in es for h in e["hooks"]]
            self.assertEqual(len(ec), len(set(ec)), (ev, ec))
        self.assertIn("after a restart", p.stdout)


class WarnTests(unittest.TestCase):
    def repo(self, settings):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        (d / ".claude").mkdir()
        (d / ".claude/settings.local.json").write_text(json.dumps(settings))
        return d

    def rows(self, d):
        return {c: (s, t) for s, c, t in perun_doctor.check(d, d / "home")}

    def test_doctor_flags_relative_hook(self):
        r = self.rows(self.repo({"hooks": {"SubagentStop": [{"hooks": [{"type": "command", "command": OLD}]}]}}))
        self.assertEqual(r["hook paths"][0], "WARN")

    def test_doctor_ok_on_project_dir_hook(self):
        c = 'python3 "$CLAUDE_PROJECT_DIR/.claude/skills/agentic-delivery/scripts/handback_cap.py"'
        r = self.rows(self.repo({"hooks": {"SubagentStop": [{"hooks": [{"type": "command", "command": c}]}]}}))
        self.assertNotIn("hook paths", r)

    def test_doctor_warns_forced_haiku(self):
        r = self.rows(self.repo({"env": {"CLAUDE_CODE_SUBAGENT_MODEL": "haiku", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"}}))
        self.assertEqual(r["subagent model"][0], "WARN")
        self.assertIn("pin to sonnet or unset FORCE", r["subagent model"][1])

    def test_doctor_quiet_on_sonnet_or_unforced(self):
        for env in ({"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"},
                    {"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"}):
            self.assertNotIn("subagent model", self.rows(self.repo({"env": env})))

    def test_selfcheck_warns_forced_haiku(self):
        d = self.repo({"env": {"CLAUDE_CODE_SUBAGENT_MODEL": "claude-haiku-4", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"}})
        st = operating_selfcheck.check_settings(str(d / ".claude/settings.local.json"))["subagent-model-pin"]
        self.assertTrue(st.startswith("WARN") and "pin to sonnet or unset FORCE" in st, st)
        ok = self.repo({"env": {"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"}})
        self.assertEqual(operating_selfcheck.check_settings(str(ok / ".claude/settings.local.json"))["subagent-model-pin"], "PRESENT")


if __name__ == "__main__":
    unittest.main()
