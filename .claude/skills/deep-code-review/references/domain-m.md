# Domain M checklist

Read this when domain M (Observability: logs, metrics, traces) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### M. Observability → `references/observability.md`
Load the reference when the target runs unattended (a service, a scheduled job, a
pipeline) or when a finding turns on whether a failure would be **noticed** —
log-level/redaction procedures, correlation-ID plumbing, and the failure-class vs
outcome distinction live there.
- Structured logs at the right level with correlation IDs and **no secret/PII
  leakage** (redact by default; over-logging is itself a vuln). A **transport/
  quota failure is logged in a distinct class** — never recorded as a substantive
  negative outcome, or a rate-limit storm silently corrupts your metrics. Key
  metrics + actionable alerts on the failures that matter; no alert noise.
- 🚩 `print`-debugging left in, logging full request bodies with tokens/PII, no
  way to trace a failure, no metric on the critical path, failures miscounted as
  results.
