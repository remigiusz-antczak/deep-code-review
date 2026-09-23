# Application security depth — tokens: OAuth / OIDC, JWT, refresh, one-shot bearer

Read this when the target or diff issues or verifies JWTs, implements OAuth or OIDC, rotates refresh tokens, or mints a signed bearer token for an approved one-shot action. Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A07:2025 — Authentication Failures (depth: tokens)

**OAuth / OIDC.** `redirect_uri` matched against an **exact allow-list** (no prefix/wildcard/open-redirect chaining —
this is how tokens get exfiltrated); **PKCE** (S256, not `plain`) on every public client and, per current guidance, on
confidential clients too; `state` bound to the user's session and verified on callback (CSRF on the authorization
flow); `nonce` present in the request and checked inside the returned ID token. Validate the ID token's `iss`, `aud`,
`exp`, and signature against the provider's JWKS — never accept an unverified token or one fetched from an
issuer-supplied URL without pinning. Implicit flow and tokens in URL fragments/query strings are findings.

**JWT algorithm confusion (asymmetric token verified as symmetric).** `alg: none` (`security-appsec.md` A07) is the degenerate case; the
live-key variant is worse. A verifier that accepts **both** a symmetric (HS256) and an asymmetric (RS256/ES256)
algorithm **and reads the algorithm from the token's own `alg` header** is forgeable: an attacker sets `alg: HS256`
and signs with the RSA/EC **public** key — published, not secret — as the HMAC key; a naive `verify(token, key)` then
uses that public key as the HMAC secret and accepts the forgery. "The signature verifies" is not enough when the
attacker chooses the algorithm — a public key is not a secret and must never serve as a MAC key. Fix: pin an
**algorithm allow-list per verification context** and never derive the algorithm from the token. ASVS requires that
"only algorithms on an allowlist can be used to create and verify self-contained tokens, for a given context" and that
the allow-list "must not include the 'None' algorithm"; where it must support "both symmetric and asymmetric"
algorithms, "additional controls will be needed to prevent key confusion" (OWASP ASVS v5.0.0-9.1.2, L1). The OWASP JWT
Cheat Sheet is blunter: "…hardcode the accepted algorithms and do not mix public-key digital signatures algorithms and
MAC algorithms."

**Refresh tokens.** Rotate on every use, invalidate the predecessor, and implement **reuse detection**: presentation
of an already-rotated token means the chain is compromised → revoke the whole family/session and force
re-authentication. Confirm rotation is server-enforced (a stored family/lineage id), that refresh tokens are
single-audience and revocable at logout and on password/MFA change, and that they aren't readable by client JS.

**Short-lived approval/action bearer tokens need single-use enforcement, not just signature + expiry (CWE-294 Authentication Bypass by Capture-replay).**
A token minted after a human approval step and handed to a machine caller for one narrow write
(`Authorization: Bearer <token>`, HMAC-signed, carrying an owner id and `exp`) is commonly verified by checking the
signature and `exp` only — that proves the token **authentic** and **fresh**, not **single-use**. Inside its own
validity window it stays replayable: if it leaks while still valid (an access/error log, an APM/tracing breadcrumb
that records request headers, a shared debugging session, a logging proxy), nothing stops it being resubmitted to
re-trigger the same approved write, attributed to the original approving human, with no signal it fired more than
once. A short expiry is a **mitigation, not a fix** — it narrows the window a leaked token is dangerous in; it doesn't
close it. OWASP's JWT Cheat Sheet (Replay Protection) lists several mitigations without ranking them — short
expiration among them, alongside a denylist that "can typically be implemented based on the jti and iss claims",
"Freshness and replay protection…by using a nonce bound to the session in the JWT claims" (the approach OpenID Connect
uses), and a sender-constrained / proof-of-possession token (DPoP or a TLS-bound JWT). Of those, the latter three
*close* the window rather than only narrowing it: a denylist or a session-bound nonce makes a captured token
single-use, and sender-binding ties it to its caller so a copy replayed from elsewhere is rejected. **Fix**: mint
every one-shot approval token with a unique `jti`; record consumed ids in a store keyed by that id with a TTL at least
as long as the token's own max lifetime, and reject a token whose id is already recorded. The record-and-reject must
be a **single atomic** step — a unique-constraint insert or a conditional/compare-and-set write — because a
read-then-insert is itself a TOCTOU: two concurrent replays of the same token both pass a naive "not yet recorded"
check before either writes (`concurrency-shared-state.md` § DB / store TOCTOU). Fail closed if that store is
unreachable rather than silently allowing an unverifiable reuse. Regression test: mint one token, consume it once
successfully against the real endpoint, replay the identical still-unexpired token and assert the second call is
refused — and fire two replays *concurrently* to confirm the store rejects the loser rather than admitting both.
Distinct from four adjacent controls: an **idempotency key** (`concurrency-shared-state.md` § DB / store TOCTOU;
`api-contracts.md`), which dedups a *legitimate* retry from the same caller so it isn't applied twice, not a captured
token replayed by someone else; **inbound-webhook replay protection** (`api-contracts.md` § Webhooks — consuming
(inbound)), which authenticates a *provider's* redelivery of an already-signed message, not a self-minted credential
replayed by whoever captured it; **refresh-token reuse detection** (the rotated-refresh-token bullet above), which
detects the second use of a long-lived *rotating session credential* and revokes the whole token family, where this is
a one-shot action token with no chain, refused call-by-call (same "record an id, reject its reuse" primitive,
different lifecycle and blast radius); and **CSRF** (`security-appsec.md` A07), which forges a request from a victim's ambient session
with no token in hand at all — here the token is real and correctly issued, it just outlives its intended single use.

**🚩** a bearer-token verifier that checks signature and `exp`/`aud` only — no `jti`/consumed-id lookup, no
session-bound nonce, no sender-binding — on a route that performs a state-changing or privileged action; especially
telling where a *sibling* token format in the same codebase (a rotated refresh token's reuse detection, above, or
another higher-privilege bearer credential) already carries a `jti`/token-id for exactly this purpose and this one
doesn't.
