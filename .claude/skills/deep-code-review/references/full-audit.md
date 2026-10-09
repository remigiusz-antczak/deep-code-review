# FULL-scope audit: entry-point table and surface-gated domains

Read this when the scope is `FULL` (never for `DIFF` or `FILE`). Two steps that make a whole-repo audit both cheaper
and sharper.

## 1. Entry-point table

Before reading domain checklists, enumerate every externally triggerable entry point: server actions, HTTP routes,
background jobs and crons, queue consumers, and inbound webhooks (grep the framework's route and handler
conventions). One row each:

| Entry point | Auth | Rate limit | External calls | Timeout budget | Idempotency |
|---|---|---|---|---|---|

Fill each cell from code, not memory; an empty cell is a finding candidate ("none found" is a valid, cited value).
Rows without auth on a mutating path, without a rate limit on a costly or credential-checking path, with external
calls but no timeout, or retried without an idempotency key are the leads to verify first. The timeout column feeds
the latency-budget probe in `reliability-error-handling.md`.

## 2. Gate domains on a surface probe

Load an optional domain or reference only when a case-insensitive `grep -E` probe shows its surface exists, and record the probe and its
hit count as the evidence for either outcome (a zero-hit probe is the citation that makes the N/A row valid):

| Surface | Probe (examples) | Reference |
|---|---|---|
| Crypto | `crypto\.\|crypto/\|hashlib\|cryptography\|Fernet\|AES\|bcrypt\|argon2\|scrypt\|nacl\|jose\|jwt\|hmac` | `appsec-crypto.md` |
| Templates (SSTI) | `render_template_string\|Template\(\|jinja\|handlebars\|ejs\|pug\|mustache\|eval\(` | `appsec-ssti.md` |
| File handling | `multipart\|upload\|FormData\|writeFile\|fs\.write\|send_file\|path\.join\|open\(.*[\"']w` | `appsec-files.md` |
| Supply chain | `postinstall\|package-lock\|yarn\.lock\|poetry\.lock\|go\.sum\|Cargo\.lock\|requirements.*\.txt\|uses:` | `appsec-supply.md` |
| Accessibility | `<(img\|button\|input\|a\|div)\b\|aria-\|\.tsx\|\.jsx` | `frontend-a11y.md` |
| ML / models | `torch\|tensorflow\|sklearn\|scikit\|onnx\|safetensors\|transformers\|xgboost\|embedding` | `data-ml.md` |
| Billing | `stripe\|paddle\|braintree\|checkout\|lemonsqueezy\|chargebee\|subscription\|invoice\|meter` | `billing-correctness.md` |

No hit: record the probe and mark N/A; do not load the reference.
