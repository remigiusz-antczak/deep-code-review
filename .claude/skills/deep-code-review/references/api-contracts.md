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
- **A number crossing the wire can lose a guarantee its type never enforced.** An integer wider
  than the receiver's exact-integer range is silently **rounded, not rejected**: JSON numbers
  interoperate as IEEE 754 double, exact only for integers in `[-(2^53)+1, (2^53)-1]`
  (RFC 8259 §6 — "implementations will agree exactly" only inside that range), so a 64-bit id, a
  large minor-unit amount, or a snowflake sent as a JSON **number** can arrive **changed** while
  every schema and type check still passes (`integer` says nothing about magnitude). Send such
  values as **strings** (or pin a documented smaller-range contract), and check, per numeric
  field crossing a serialization / storage / language boundary, its exact-representable range at
  each hop — the same class as the cents-vs-dollars unit breach in `data-quality.md`, at the
  representation layer.

---

## Contract tests

- **Assert the contract, not a giant golden dump.** For a cross-boundary payload (an API
  response, a queued message), assert the specific fields, types, and constraints a **consumer**
  depends on, so the check **passes** a backward-compatible additive change (a new optional
  field) and **fails** only a real incompatibility — the signal you want at a boundary. A
  whole-response **golden snapshot** is a poor default here: it fails on **every** change,
  breaking or cosmetic alike, so its failure can't distinguish a real break from a reordered
  field or a new optional key, and it trains an `--update-snapshots` **re-record reflex** that
  rubber-stamps the next genuine break. Reserve a golden fixture for a small, stable,
  whole-value **identity** (`testing-and-evals.md` snapshot / identity-pinning), not a large
  evolving payload.
- Webhook: unit-test invalid signature, expired timestamp, duplicate delivery
  id.
- OpenAPI/proto generated types: assert the implementation still matches (or
  generate the handlers) — hand-written types beside a stale spec are a
  coherence finding (cross-ref H lockstep surfaces).

---

**🚩 red flags**: unverified webhook; unvalidated body; silent contract change;
required field added to a live message schema; inconsistent error shapes;
identity taken from webhook body alone; unbounded list endpoints; no version/
compatibility story for queued payloads; a whole-payload golden snapshot as the
only contract test for an evolving cross-boundary payload (fails on cosmetic churn,
and a `--update-snapshots` re-record reflex rubber-stamps a real break).
