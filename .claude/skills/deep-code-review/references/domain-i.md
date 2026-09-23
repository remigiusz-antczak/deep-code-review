# Domain I checklist

Read this when domain I (API, interface, contracts & integration) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### I. API, interface, contracts & integration → `references/api-contracts.md`
- Public interfaces minimal, consistent, hard to misuse; breaking changes
  versioned (SemVer) and documented; inputs validated at the boundary; outputs
  match the documented schema; errors typed and documented.
- **Serialized-state & message/queue schema evolution**: adding a required field
  breaks in-flight messages and persisted data written by old code — evolve
  compatibly (optional-with-default, versioned payloads), exactly like a DB
  migration.
- **Webhooks / inbound integrations**: **verify the signature**; enforce
  **replay protection** (timestamp + nonce) and **idempotency keys**; tolerate
  **out-of-order and duplicate** delivery. Never trust a webhook body's identity
  claims without verification.
- For HTTP/GraphQL APIs, overlay the OWASP API Security Top 10 (2023) — see the
  appsec overlay (`security-api.md`); contract evolution and webhook
  procedures live in `api-contracts.md`.
- 🚩 unverified webhook handler, unvalidated request body, silent contract change,
  required-field added to a live message schema, inconsistent error shapes.
