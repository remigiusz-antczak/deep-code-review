"""Field-audit additions: FULL-only refs routed from SKILL.md, probes present, DIFF path untouched."""
import pathlib, subprocess, unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SK = ROOT / ".claude/skills/deep-code-review"
REF = SK / "references"
PROBES = {
    "reliability-error-handling.md": ["Latency budget per handler", "0.7", "Partial-success pipelines"],
    "observability.md": ["Alert and notification paths", "mark-before-send", "Audit coverage"],
    "concurrency-shared-state.md": ["fixed-name QA database or port"],
    "appsec-design.md": ["Config hygiene and kill switches", "fail closed"],
    "appsec-login.md": ["Delegated-session revocation"],
    "full-audit.md": ["Entry-point table", "Idempotency", "Gate domains on a surface probe"],
    "nextjs-app-router.md": ["use server", "cookies().set", "cache()", "redirect()", "Suspense"],
}


class FullAuditField(unittest.TestCase):
    def test_probes_present(self):
        for f, needles in PROBES.items():
            text = (REF / f).read_text()
            for n in needles:
                self.assertIn(n, text, f"{f} lacks {n!r}")

    def test_new_refs_routed_with_trigger(self):
        skill = (SK / "SKILL.md").read_text()
        self.assertIn("`nextjs-app-router.md` when `next` is a dependency", skill)
        self.assertIn("for `FULL`, `full-audit.md`", skill)

    def test_diff_path_unchanged(self):
        for p in ("commands/review.md", ".claude/skills/deep-code-review/references/method.md"):
            r = subprocess.run(["git", "diff", "--quiet", "origin/main", "--", p], cwd=ROOT)
            self.assertEqual(r.returncode, 0, f"{p} must not change")


if __name__ == "__main__":
    unittest.main()
