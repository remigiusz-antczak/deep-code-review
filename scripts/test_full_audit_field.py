"""Field-audit additions: FULL-only refs routed from SKILL.md, probes present, DIFF path untouched."""
import hashlib, pathlib, re, subprocess, unittest

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
        for ref in ("nextjs-app-router.md", "full-audit.md"):
            self.assertIn(ref, skill)
        self.assertRegex(skill, r"`nextjs-app-router\.md` when `next`")
        self.assertRegex(skill, r"`FULL` scope: `full-audit\.md`")

    def test_diff_path_unchanged(self):
        self.assertTrue((ROOT / "commands/review.md").is_file())
        def git(*a):
            return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
        mb = git("merge-base", "HEAD", "origin/main")
        base = mb.stdout.strip() if mb.returncode == 0 else git("rev-list", "--max-parents=0", "HEAD").stdout.split()[-1]
        for p in ("commands/review.md", "method.md"):
            path = p if p.startswith("commands") else f".claude/skills/deep-code-review/references/{p}"
            old = git("show", f"{base}:{path}")
            if old.returncode != 0:
                continue  # absent at fallback base
            h = lambda b: hashlib.sha256(b.encode()).hexdigest()
            self.assertEqual(h(old.stdout), h((ROOT / path).read_text()), f"{path} must not change")

    def test_probes_hit_multilang_fixtures(self):
        table = (REF / "full-audit.md").read_text()
        probes = {}
        for m in re.finditer(r"^\| ([^|]+?) \| `(.+)` \| `[a-z0-9-]+\.md` \|$", table, re.M):
            probes[m.group(1)] = re.compile(m.group(2).replace("\\|", "|"), re.I)
        hits = {
            "Crypto": ["import hashlib", "from cryptography.fernet import Fernet", "AES.new(k)", "argon2.hash(p)",
                       "import \"crypto/sha256\"", "nacl.secret", "jose.jwt.sign(x)", "crypto.createHash('md5')"],
            "Templates (SSTI)": ["render_template_string(s)", "new Handlebars.compile(s)", "Template(user)", "eval(x)"],
            "File handling": ["fs.writeFile(p)", "request.files multipart", "send_file(p)", "open(p, 'w')"],
            "Supply chain": ["\"postinstall\": \"x\"", "uses: actions/checkout@v4", "go.sum", "poetry.lock"],
            "Accessibility": ["<button onClick>", "<img src=x>", "aria-label", "App.tsx"],
            "ML / models": ["import torch", "from sklearn import svm", "model.safetensors", "OpenAIEmbeddings"],
            "Billing": ["stripe.Customer", "paddle.js", "braintree.gateway", "lemonsqueezy", "chargebee.Subscription", "checkout.session"],
        }
        self.assertEqual(set(probes), set(hits))
        for k, snippets in hits.items():
            for sn in snippets:
                self.assertRegex(sn, probes[k], f"{k} probe misses {sn!r}")


if __name__ == "__main__":
    unittest.main()
