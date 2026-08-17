# APIs, contracts & integrations

Read this when reviewing public HTTP/GraphQL/RPC surfaces, webhooks, message/
queue payloads, SDK boundaries, or any serialized state that must evolve without
breaking live consumers. Expands section I of `SKILL.md`. For authz/injection/
SSRF on those surfaces, load `security-appsec.md` (OWASP API Security Top 10
overlay lives there); this file is **contract correctness and evolution**.

Standards (URLs + dates in `docs/standards-index.md`): OWASP API Security Top 10
(2023), Semantic Versioning.

---

## Detection procedure

1. **Inventory public operations** — routes, RPC methods, CLI commands that
   cross a trust boundary, event types published/consumed.
2. **For each: find the contract** — OpenAPI/JSON Schema/proto/zod/typebox/
   README table. Missing contract on a public surface is a finding.
3. **Trace one request** — validate at boundary → authorize → handler →
   response shape. Note silent coercion, extra fields stripped/kept, error
   envelope consistency.
4. **Find producers/consumers of persisted or queued messages** — version field?
   required-field additions? migration story?

---

## Public interface hygiene

- Minimal surface; hard to misuse (required auth, explicit content-types,
  bounded payloads). Breaking changes: SemVer **MAJOR** (or a versioned path/
  header) and a documented migration — silent response-shape changes are
  breakages even when status stays 200.
- Inputs validated at the boundary (schema); outputs match the documented
  schema. **Typed errors** with stable machine codes; do not leak upstream
  bodies (cross-ref B secrets/logging).
- Pagination/filter/sort parameters are bounded; "return everything" defaults
  are a reliability and cost finding (cross-ref E).

---

## Webhooks & inbound integrations

- **Verify the signature** with the configured secret; reject on mismatch.
  Timing-safe compare.
- **Replay protection** — timestamp skew window + nonce/idempotency store, or
  provider delivery id stored uniquely.
- Tolerate **duplicates and out-of-order** delivery; handlers must be
  idempotent on the business key.
- Never trust identity claims inside the body (`user_id`, `account_id`) without
  binding them to the verified signature context / server-side session.

**Grep leads:** `webhook` / `stripe` / `github` handlers without `crypto`
verify; `JSON.parse` of raw body after a verifier that needed the raw bytes
(body already consumed); no timestamp check.

---

## Message / queue / serialized-state evolution

Treat persisted and in-flight payloads like DB schemas:

- **Adding a required field** breaks old producers and in-flight messages —
  evolve with optional + default, or bump a `version` / schema id and keep a
  reader for N-1.
- Removing or renaming a field: deprecate, dual-read, then drop on a MAJOR.
- **Poison messages** — bad payload must dead-letter or skip with loud metric,
  not block the partition forever.
- Exactly-once is rare; design for **at-least-once + idempotent consumer**.

---

## Contract tests

- Consumer-driven or schema fixtures: a golden request/response (or message)
  set that fails CI when the handler drifts.
- Webhook: unit-test invalid signature, expired timestamp, duplicate delivery
  id.
- OpenAPI/proto generated types: assert the implementation still matches (or
  generate the handlers) — hand-written types beside a stale spec are a
  coherence finding (cross-ref H lockstep surfaces).

---

**🚩 red flags**: unverified webhook; unvalidated body; silent contract change;
required field added to a live message schema; inconsistent error shapes;
identity taken from webhook body alone; unbounded list endpoints; no version/
compatibility story for queued payloads.
