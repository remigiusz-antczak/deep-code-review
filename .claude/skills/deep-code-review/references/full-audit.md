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

Load an optional domain or reference only when a grep probe shows its surface exists, and record the probe and its
hit count as the evidence for either outcome (a zero-hit probe is the citation that makes the N/A row valid):

| Surface | Probe (examples) | Reference |
|---|---|---|
| Crypto | `createCipher\|crypto\.\|bcrypt\|jwt\|hmac` | `appsec-crypto.md` |
| Templates (SSTI) | template engines, `render_template_string`, `eval(` | `appsec-ssti.md` |
| File handling | upload, `multipart`, `fs.write`, `path.join` on input | `appsec-files.md` |
| Supply chain | lockfiles, `postinstall`, CI workflow `uses:` | `appsec-supply.md` |
| Accessibility | JSX/HTML/templates present | `frontend-a11y.md` |
| ML / models | model files, `torch\|sklearn\|embeddings` | `data-ml.md` |
| Billing | `stripe\|subscription\|invoice\|meter` | `billing-correctness.md` |

No hit: record the probe and mark N/A; do not load the reference.
