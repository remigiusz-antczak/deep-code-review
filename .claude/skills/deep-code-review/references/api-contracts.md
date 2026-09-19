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
  schema. **Typed errors** with stable machine codes, in **one consistent,
  machine-readable envelope across the whole surface** — a registered structure
  (RFC 9457 `application/problem+json`: `type` / `status` / `title` / `detail` /
  `instance` plus extension members; obsoletes RFC 7807) rather than an ad-hoc
  shape per endpoint, so a consumer writes a single error-parsing path; do not
  leak upstream bodies (cross-ref B secrets/logging). The **stable machine code is
  itself part of the versioned contract** — changing or repurposing a code is a
  breaking change (below), so freeze it post-release and treat it as an extensible
  enum a consumer may not yet know.
- Pagination/filter/sort parameters are bounded; "return everything" defaults
  are a reliability and cost finding (cross-ref E).

---

## Long-running operations — an async job is its own contract

An endpoint that can't finish its work inside the request's synchronous budget must
not fake synchrony (block the caller, or return a fake `200` before the work is
done). It returns **202 Accepted** plus a second, independently-versioned
**operation / job resource**: a **stable id**; an explicit **status enum with real
terminal states** (`succeeded` / `failed` / `canceled`, never a bare boolean that
conflates "not done" with "failed" — the make-impossible-states-unrepresentable rule,
`reliability-error-handling.md`); an **error payload only on the failed state** and a
**result only on succeeded**; and a documented way to discover and poll it (a
`Location` header — or a vendor `Operation-Location`-style header — or a documented
poll URL, with `Retry-After`). A polling client must **distinguish poll-transport failure from
operation failure** — the poll `GET` returning `500` is not the same as it returning
`200` with `status: failed` (the async cousin of "check status before reading the
body", cross-ref `reliability-error-handling.md`).

- **The start call needs provider-side idempotency.** If the client retries the
  start request because the `202` was lost in transit, an **idempotency key on the
  start call** (enforced server-side; reject a reused key carrying a **differing
  body** with a `4xx` + the RFC 9457 envelope above) must fold an identical retry
  into the **same** operation — without it, a lost `202`
  silently spawns a **second** operation and the work runs twice. This is the
  provider half of the caller-side idempotency rule in
  `reliability-error-handling.md`; the job's own internal durability / compensation
  is domain W (`domain-checklists.md`).

---

## Breaking-change discipline for public APIs & SDK exports

The **SemVer MAJOR for a breaking change** rule above needs a *recognition taxonomy* and a
*mechanical* check — most breaks are not a removed field — and it applies to a **library / SDK's
exported symbols** exactly as to an HTTP response: a public exported function, class, type, or CLI
flag is a contract, which is the SDK-boundary scope this file's header claims.

- **Recognize the non-obvious breaking changes.** Beyond remove/rename, each of these breaks an
  existing consumer although nothing was deleted: **stricter validation** on an existing field/param
  (input previously accepted is now rejected); a **changed default** for an existing optional
  param/field (callers that relied on the old default silently get new behavior); a **new required** param on a direct
  call (not only a queued-message field); a **widened output** (a field goes non-null → nullable, or
  a returned union grows a case the consumer's exhaustive handling does not cover); and an **added
  enum / union member** a strict or exhaustive-`switch` consumer must now handle; and — for a
  resource with **full-replacement update** (`PUT`, or `PATCH` with an `update_mask` of `*`) —
  **adding a new mutable field**, because an old client that round-trips (reads the object, changes one
  field, writes the whole object back) never learned to send the new field and silently clears it
  (AIP-134). The mirror is a
  **forward-compatibility** guarantee to state and test — a consumer tolerates an unknown field or a
  new enum value rather than crashing (the flip side of the extra-fields-tolerated note above).
- **Add a mechanical surface-diff gate, distinct from hand-written contract tests.** The contract
  tests below catch only what someone thought to assert; complement them with an **automated
  differ** that compares the current declared surface against the last released version and fails CI
  on an incompatible delta, independent of whether a test covers that field. Name the instrument per
  ecosystem (OpenAPI: `oasdiff`; protobuf/gRPC: `buf breaking`; a typed/compiled SDK: a
  semver-checking differ such as `cargo-semver-checks`). **🚩** no automated surface-diff in CI — a
  signature change then rides in only on a human reviewer or a hand-written test noticing it.
- **Removal needs a stated window and a usage precondition, not just the deprecate → dual-read →
  drop sequence below.** Publish a **sunset date** and a machine-readable deprecation signal on the
  surface itself — the HTTP **`Sunset`** response header (RFC 8594: a single HTTP-date hint that the
  URI is likely to become unresponsive at that time; a separate `Deprecation` header exists, cited
  by name only) — so consumers are warned in-band. And you **cannot know the window has safely
  expired unless something measures calls to the deprecated path**: removal with no call-volume
  evidence is a guess, not a verified drop (the skip-rather-than-guess bar). Distinct from
  `security-appsec.md`'s zombie/legacy-route sunset, which retires an already-orphaned surface rather
  than planning the deprecation of a live one.

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
