# Application security — OWASP Top 10:2025 review playbook

Read when the target exposes any network surface (web app, API, service, CLI touching untrusted input), handles
authentication/authorization, or processes data from users, files, or third parties. Expands section B of `SKILL.md`:
per-category **detection procedures**, red-flag greps, a minimal safe verification, and the fix. Map every finding to
its category and, where useful, the CWE.

Standards tracked here (see `references/standards-index.md` once installed, else `docs/standards-index.md` in the
skill repo): OWASP Top 10:2025, OWASP API Security Top 10 (2023), OWASP ASVS 5.0, OWASP WSTG, and the 2025 CWE Top 25.

> Verification etiquette: prove exploitability **locally and non-destructively** only. Never attack a system you don't
> own or lack written authorization to test; never run an exploit against production, shared, or third-party
> infrastructure. A plausible-but-unproven issue is still a finding — report it `unverified` with the reason.

## Routed depth — load a sub-file only on its trigger

Every category below keeps the checks each application review needs. Narrower depth lives in these
sub-files; load one when the target or diff matches its trigger.

| Load | When the target or diff … |
|---|---|
| `appsec-edge.md` | recommends an auth gate, middleware, or edge rule (Identity Arrival Map, forgeability row-set, request smuggling, bidirectional gate proof); sits behind a reverse proxy, CDN, or WAF; keys a security decision on `X-Forwarded-For` / `Forwarded` / `X-Real-IP`; caches identity-derived responses or reflects a header into a cacheable one; is embedded cross-origin or uses camera / microphone / geolocation / payment APIs |
| `appsec-scan-tests.md` | ships a regression or inventory test that scans every route, handler, or migration and asserts a security property |
| `appsec-links.md` | reflects a `next` / `returnTo` / `redirect` parameter into a redirect, or turns text into HTML or links (markdown, autolinker, linkify, a hand-built `href`) |
| `appsec-approvals.md` | performs a consequential or high-value action: payout, wire transfer, credential issue, privilege grant, protected-surface merge |
| `appsec-supply.md` | adds or bumps a dependency, touches a lockfile or `postinstall`, edits a CI workflow or a file a privileged pipeline executes, ships a signed / attested / SBOM-bearing artifact, or the target has a dependency manifest, lockfile, or CI workflow (A03) |
| `appsec-crypto.md` | encrypts or decrypts (mode, IV, nonce), compares a signature / token / API key / OTP against caller input, hashes passwords, wraps keys, or holds long-lived confidential data (A04) |
| `appsec-ssti.md` | compiles a server-side template from anything but a static file (`render_template_string`, `env.from_string`, a user-customizable template) |
| `appsec-files.md` | accepts uploads, issues presigned / signed URLs, extracts archives, serves a file by a user-supplied path, parses XML, or exports CSV / spreadsheet files |
| `appsec-tokens.md` | issues or verifies JWTs, implements OAuth / OIDC, rotates refresh tokens, or mints a one-shot approval bearer token (A07) |
| `appsec-login.md` | implements passkeys / WebAuthn, push MFA, OTP, or a password policy (A07) |
| `appsec-design.md` | asks for or relies on a threat model, adds a trust boundary or principal, wires a producer across a publish boundary, or renders user text as a trust cue (A06) |

---

## A01:2025 — Broken Access Control (includes SSRF)

The most exploited class. Every sensitive read/write must prove the caller is authorized **server-side** on every
request. Prefer **safe probes** (missing header, id swap, status/body compare) over exploit kits.

Depth: `appsec-edge.md` (gate proposals, proxy chains, caches), `appsec-scan-tests.md`, `appsec-links.md`
(open redirect), `appsec-approvals.md`, `appsec-files.md` (signed URLs, uploads).

**How to detect in review**
- Enumerate every route/handler/mutation **and** non-route entry points: server actions, RPC/tRPC, GraphQL resolvers,
  cron/webhooks, websocket handlers. For each, find where authorization is checked. Don't assume middleware covers it.
- **Dual surface (API redaction ≠ page protection).** For every sensitive loader, inventory **every** caller: JSON/API
  handler, RSC/SSR/`page.tsx`, serialized props / streaming flight payload (not only rendered DOM),
  framework-generated data siblings, BFFs, mobile clients. Divergence — one surface redacts/401s while another returns
  the full object — is **Critical** when world-reachable.
- **An export/download is a *sharper* leak surface than an on-screen view.** A file leaves with the user,
  redistributable **beyond** the auth boundary, so a leak there outlives the session and the gate. Put every
  export/download route in the dual-surface census above and hold it **no weaker than, and preferably stricter than,**
  the dashboard — public-tier rows only, or at least the **same token *and* scope** as the guarded API, never an
  unauthenticated or unscoped dump. Corollary for SSR: confidential, per-viewer data belongs behind an
  **authenticated, server-scoped API** the client calls, not baked into a server-rendered page whose only identity is
  client-side (the SSR row of the Identity Arrival Map in `appsec-edge.md` can't scope what it never receives).
- **Tenant / row scoping.** Confirm tenant/owner predicates are applied in a **shared accessor**, not ad-hoc per call
  site. Flag request-path use of an admin/service credential that bypasses row policy as Critical. "DB policy enabled"
  is unproven until a test shows the app path cannot skip it. Never trust `tenant_id` / `org_id` from the body alone —
  bind to the authenticated principal.
- Authorization decided only in the client = no authorization. Default: deny-by-default.
- **SSRF**: URL/host/IP from input fetched server-side → allowlist + resolve-validate-**pin** the IP; block loopback,
  RFC-1918, CGNAT, link-local metadata (`169.254/16`), IPv4-mapped/6to4, `.internal`, dotless labels;
  `redirect: manual` and re-validate each hop. (Full range list stays here — don't restate a divergent copy in
  `SKILL.md`.)
- **Untrusted-egress caller census (after a guard lands):** inventory every call site fetching an untrusted or
  attacker-influenced URL (HTTP clients, redirect-following options, robots/calendar/sidecar scripts —
  language-neutral, not a single API name). Confirm each uses the guarded transport and hop-revalidates; a breaker or
  allowlist on **one** client while siblings still follow redirects bare is the same class of miss. A guard nothing
  calls is a no-op.

**Two-principal matrix (mandatory beside the anonymous sweep).** Seed two accounts (different tenant/role when
multi-tenant). For every object-bearing route: replay A's request with B's id / B's token / B's tenant. Expected:
`own → 200`, `other → 403/404`, `none → 401`. Missing a second account → `Decisions needed`, not a skip. Most
production authz bugs are authenticated-but-unauthorized; reading code for IDOR isn't enough.

**🚩 grep**: `req.params`/`req.body` id → query; ungated routes; `fetch(userUrl)`; `role === 'admin'` in UI only;
shared loaders across API + page with asymmetric redaction; `Cache-Control: public` on auth'd handlers; a reflected
`X-Forwarded-Host`/`X-Forwarded-*` in a cacheable response; `tenant_id` from body; trusted headers read without strip;
`getSignedUrl` / long-lived signed links.

**Fix**: deny-by-default authz at the data layer on **every** entry point; strip forgeable identity headers;
private/no-store (or keyed) caches; bidirectional tests. Never recommend document-middleware without a completed
Identity Arrival Map + bidirectional proof (`appsec-edge.md`).

**Anonymous GET sweep (mandatory opener — local/dev by default).** Hit every documented GET with
**no cookies and no Authorization**. Default target = local/dev/staging you own; production/shared host requires
**explicit owner authorization** — else record `unverified` + needed artifact (staging URL / route table). Record
status + size; **also** follow redirects separately, grep bodies for sentinel/canary fields from private data, and
**diff anon vs authenticated body** for the same URL (subset-equality = pass — size alone misses small leaks and
login-shell 200s).

```bash
# Tune BASE + paths from the route inventory; no auth headers. Local/dev first.
for path in / /api/meta /api/... ; do
  curl -s -o /tmp/body -w "%{http_code} %{size_download} $path\n" "$BASE$path"
done
```

World-reachable sensitive catalog → Critical under S0–S3 in `SKILL.md`.

**Exposure-boundary discriminator.** Pin severity to boundary × confidentiality tier: VCS-tracked? unauthenticated
route (anon sweep)? client bundle? CDN cache? Not to how scary the React looks.

## A02:2025 — Security Misconfiguration

**How to detect**: debug/verbose errors in prod; stack traces returned to clients; default or sample credentials;
overly permissive CORS (`Access-Control-Allow-Origin: *` **with** credentials); directory listing;
admin/actuator/`/debug` endpoints reachable; missing security headers (HSTS, `Content-Security-Policy`,
`X-Content-Type-Options`, frame-ancestors, `Permissions-Policy`,
`Cross-Origin-Opener-Policy`/`Cross-Origin-Embedder-Policy`/ `Cross-Origin-Resource-Policy`); cloud storage/buckets
world-readable; unnecessary services/features enabled.

**🚩 grep**: `DEBUG = True`, `NODE_ENV` not enforced to `production`, `Access-Control-Allow-Origin: *`,
`cors({ origin: true, credentials: true })`, `app.use(errorhandler())` in prod, `.enable('trust proxy')` misused.

**Fix**: harden by default; ship prod config that disables debug, sets headers, scopes CORS to known origins, and
removes sample/default accounts. Track against CIS Benchmarks for the runtime/platform.

Depth (`Permissions-Policy`, COOP / COEP / CORP): `appsec-edge.md`.

## A03:2025 — Software Supply Chain Failures

Elevated in 2025. Covers dependencies, build, and CI/CD provenance.
Depth — every detection step, grep, and fix: `appsec-supply.md`.

## A04:2025 — Cryptographic Failures

**How to detect**: TLS enforced end-to-end (no plaintext transport of secrets); no weak/legacy primitives (MD5, SHA-1,
DES, RC4, ECB mode); passwords hashed with a memory-hard KDF (argon2id / bcrypt / scrypt), never fast hashes or
encryption; secrets not hard-coded; IVs/nonces unique per message; randomness from a CSPRNG (`secrets`,
`crypto.randomBytes`), never `Math.random`/`rand()` for security; keys rotated and stored in a KMS/secret manager.

**🚩 grep**: `md5(`, `sha1(`, `DES`, `AES/ECB`, `Math.random()` near token/id generation, `random.random()` for
secrets, hard-coded keys/IVs, `password` + `sha256` without a salt/KDF.

**Fix**: TLS everywhere; argon2id for passwords; AEAD ciphers (AES-GCM, ChaCha20-Poly1305) with unique nonces; CSPRNG
for all security-relevant randomness; keys in a managed store.

**TLS enforced is not TLS validated.** "TLS everywhere" above is about the wire; it says nothing about whether the
*client* checks who it's talking to. A client with certificate validation disabled — `verify=False` (Python
`requests`), `rejectUnauthorized: false` / `NODE_TLS_REJECT_UNAUTHORIZED=0` (Node), `InsecureSkipVerify: true` (Go),
an all-accepting `TrustManager` / `HostnameVerifier` (Java), `curl -k` / `--insecure` — still shows `https://` in
every URL and satisfies "TLS everywhere" by the letter while trusting **any** certificate from **any** host, so a MITM
terminates and re-originates the connection for free (CWE-295, "Improper Certificate Validation"; the
hostname-mismatch sub-case is CWE-297). It's commonly a debugging shortcut against a self-signed internal cert that
shipped un-reverted. Internal / service-to-service TLS is **not** exempt — pin the specific internal CA or self-signed
cert, don't disable validation to reach it (ASVS v5.0.0-12.3.2 requires TLS clients validate certificates; -12.3.4
requires internal services trust only specific internal CAs / self-signed certs). **🚩 grep**: `verify\s*=\s*False`
near `requests.` / `urllib3`, `rejectUnauthorized:\s*false`, `NODE_TLS_REJECT_UNAUTHORIZED`,
`InsecureSkipVerify:\s*true`, an empty or always-true `TrustManager` / `HostnameVerifier`,
`ssl._create_unverified_context` (Python), `curl .*(-k|--insecure)`. (Distinct from the JWT `verify=False` in A07 —
that's signature verification, not TLS.)

Depth (crypto-agility, nonce reuse, constant-time compare, KDF cost, envelope keys): `appsec-crypto.md`.

## A05:2025 — Injection

SQL/NoSQL/OS-command/LDAP/XPath/template/header injection and XSS. Corresponds to several top-of-list 2025 CWEs (XSS
#1, SQLi #2, OS Command Injection #9, Code Injection #10).

**How to detect**: any query/command/markup **built by string concatenation or interpolation** from input. Confirm
parameterized queries / prepared statements / bound ORM params for SQL; safe templating with contextual auto-escaping
for HTML (no raw sinks); argument arrays (not a shell string) for subprocess calls; no `eval`/`exec`/dynamic code from
input; safe deserialization only.

**🚩 grep**:
- SQL: `"SELECT … " +`, f-strings/`format`/template literals inside a query, `.query(\`… ${x} …\`)`,
  `execute("… %s" % x)`.
- XSS: `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `|safe`, `render_template_string`, `document.write`.
- Command: `os.system`, `subprocess.*(shell=True)`, `child_process.exec(`, `Runtime.exec(` with a concatenated string,
  backticks.
- Code: `eval(`, `exec(`, `Function(`, `pickle.loads`, `yaml.load` (unsafe).
- Path traversal (CWE-22) sink: `sendFile`/`send_file`/`send_from_directory`, `open(<dir> + <input>)`,
  `path.join(<root>, <input>)` — depth: `appsec-files.md`.

**Fix**: parameterize; use the ORM's bound parameters; contextual output encoding + a strict CSP; argument-vector
subprocess calls; never deserialize untrusted data with an unsafe loader. Per-language sinks: the `lang-*.md` files.

Depth: `appsec-ssti.md` (template engines), `appsec-links.md` (text-to-markup, href sinks),
`appsec-files.md` (uploads, archives, path serving, XML, CSV export).

## A06:2025 — Insecure Design

A missing control, not a buggy one. **How to detect**: is there a threat model for the sensitive flows (auth, payment,
data export, admin)? Are abuse cases considered (what if the user is hostile / the upstream is compromised)? Are rate
limits, quotas, and business-logic limits **designed in** (e.g. can a user request 10,000 password resets, redeem a
coupon twice, or race a balance check)? Secure defaults, or must the operator remember to turn safety on?

Depth (threat-model method, boundary crossings, trust-signal spoofing): `appsec-design.md`.

**Detect steps, in order**
- **Inventory the money/state machines.** List every flow that moves value or advances state: checkout, refund,
  credit/balance, coupon, invite, quota, approval, tier change. For each, write the legal state transitions; anything
  not listed must be rejected server-side, not merely un-rendered.
- **Client-trust fields.** Diff request bodies against what the server recomputes. `price`, `amount`, `currency`,
  `qty`, `discount`, `tier`, `step`, `status`, `isAdmin` arriving from the client and persisted without re-derivation
  from server state is a finding. Wizards: confirm the server validates the *whole* invariant on the final step, not
  just `step` monotonicity — a client can post the final step first.
- **TOCTOU on redeem/balance.** Any check-then-act (coupon redeem, balance debit, seat claim, one-time token) needs a
  single atomic mutation: conditional/compare-and-set update, `SELECT … FOR UPDATE`, or a unique constraint on the
  redemption key. Read-then-write in separate statements without a transaction/lock → race. Verify by firing N
  concurrent identical requests locally and asserting exactly one succeeds.
- **Rate-limit key, burst, and failure mode.** Ask what the limiter is keyed on (IP alone is bypassable; key on
  principal **and** target resource) — **and how cheaply that key is minted**: a self-service or unauthenticated
  **session token, device id, or API key** an attacker rotates for free is no better than IP, because re-minting
  resets the counter (the *rotating-key-vs-stable-identity* confusion). Key on a **scarce, verified** identity (a
  verified account, a payment instrument, a credential that itself costs / is rate-limited to create), or rate-limit
  the **minting** path itself. Then check whether burst is bounded (fixed windows allow 2× at the boundary), and what
  happens when the counter store is unreachable — **fail-open on limiter error is the bug**, and it's common. Confirm
  limits are enforced server-side for every entry point into the flow, not just the primary route.

**Fix**: threat-model the flow, add server-side business-logic limits, make the safe path the default. Cross-reference
OWASP API Security Top 10 (2023) API4 (Unrestricted Resource Consumption) and API6 (Unrestricted Access to Sensitive
Business Flows) for API work.

## A07:2025 — Authentication Failures

**How to detect**: credential-stuffing exposure (no rate limit / lockout / bot defense on login); weak password
policy; session fixation (session id not rotated on login); tokens that don't expire or are reusable after logout;
missing MFA on high-value accounts; JWTs with `alg: none`, weak secrets, or no expiry/audience check; password reset
tokens that are guessable or long-lived.

**🚩 grep**: `jwt.decode(… verify=False)`, `algorithms=['none']`, no `exp` claim, session id reused across privilege
change, `password == input` (plaintext compare), reset tokens from a non-CSPRNG.

**Account enumeration is a detectability leak (CWE-203 Observable Discrepancy).** On signup, login, and
password-reset, diff the response — status code, body / error text, redirect target, **and response time** — between
*subject exists* and *subject does not exist*. A distinguishable response on any of those axes lets an unauthenticated
outsider enumerate valid accounts (LINDDUN's *Detectability* threat): a different string for "invalid username" vs
"invalid password"; a `409`/`422` on signup revealing "email taken"; a reset endpoint that emails-or-not based on
existence. Fix: one **generic response** for the exists/not-exists pair and a **constant-time** path so existence
isn't observable — not the removal of per-field validation.

**A static secret used as an *admit* gate needs an enforced length/entropy floor at the point of use — a property separate from constant-time compare.**
A shared secret, API key, webhook-signing key, or admin token compared against a caller-supplied value gates
**admission**, so a short or low-entropy secret is **brute-forceable** however the comparison is written —
constant-time compare closes a timing side-channel, it doesn't make a 6-character secret strong. Enforce a minimum
length **and** entropy **where the secret is used** (reject a too-short / low-entropy value at load and fail closed),
not only where it's generated: a strong generator doesn't stop a hand-set `changeme` in one deployment's env.
**Admit-direction weakness outranks exclude-direction** (a weak admit secret grants access; a weak exclude secret only
over-blocks). Detect by grepping for the **floor itself** (a length/entropy check at the compare site), not the
secret's name — the guard was never written, so the secret's name won't lead you to the gap.

**Session cookie flags (server-side checklist — read the `Set-Cookie` bytes, not the config object).** Every
session/auth cookie: `Secure` (never sent over plaintext), `HttpOnly` (no JS read — blunts XSS token theft),
`SameSite=Lax` or `Strict` for session cookies; `SameSite=None` **requires** `Secure` and a real cross-site reason, so
treat it as a finding until justified. Also check `Path=/`-vs-scoped, host-only vs `Domain=` (a `Domain` cookie leaks
to every subdomain — including one an attacker controls via subdomain takeover), `__Host-` prefix where applicable,
and a bounded `Max-Age`/`Expires`. Verify with `curl -si` on the login response; a framework default can be silently
overridden by a proxy or a custom cookie writer.

Depth: `appsec-tokens.md` (OAuth / OIDC, JWT, refresh, one-shot bearer), `appsec-login.md` (passkeys, MFA,
OTP, password policy).

**Session termination & timeout are server-side controls, not a cookie `Max-Age`.** Require two distinct,
both-enforced controls — an **inactivity (idle) timeout** and an **absolute maximum session lifetime** — both
server-side and driven by documented risk decisions (ASVS v5.0.0-7.3.1 / -7.3.2, L2), not a client-trusted cookie
`Max-Age`/`Expires` (which the client can ignore). Typical ranges (OWASP Session Management Cheat Sheet): idle "2-5
minutes for high-value applications and 15-30 minutes for low risk applications"; an absolute cap "between 4 and 8
hours" for a full workday. **Logout must actually terminate the session server-side** — a stateless self-contained JWT
cannot be "deleted" (clearing the client cookie is not revocation), so ASVS v5.0.0-7.4.1 (L1) requires "a solution
such as maintaining a list of terminated tokens, disallowing tokens produced before a per-user date and time or
rotating a per-user signing key." A token still accepted after logout, or a session with no absolute cap, is the
finding. (Accessibility: a short idle timeout still needs `a11y-color-motion.md`'s warn-and-extend affordance before
it fires.)

**Fix**: rate-limit and lock out; rotate session on auth state change; short token lifetimes + server-side revocation;
verify JWT signature/alg/exp/aud; MFA where warranted.

**🚩 CSRF guard mistaken for authentication.** An `Origin` / `Referer` / `Sec-Fetch-Site` check is CSRF defense only —
(1) any non-browser client sets those headers freely, and (2) browsers omit `Origin` on many same-site **GET**
navigations, so the check is simultaneously bypassable and leaky. If it's the *only* gate on a sensitive/paid/mutating
action, that action is effectively unauthenticated: CWE-352 (CSRF) is not a substitute for CWE-306 (Missing
Authentication) / CWE-862 (Missing Authorization). Confirm a real identity check exists.

**🚩 A CSRF guard on one route is not a guard on the class.** When a CSRF token / double-submit / `Origin` check
exists, **grep every cookie-authenticated *mutating* route** (`POST`/`PUT`/`PATCH`/`DELETE`) and confirm the guard is
wired into **all** of them — a guard bolted onto the single route an incident exposed leaves its siblings open, the
same copy-idiom-scoped-to-one-callsite miss the review scopes to its full instance set (Phase 4). Second,
**verify the shared body parser requires `Content-Type: application/json`** (and rejects a mismatched type) *before*
it parses: a parser that also accepts `text/plain` / `application/x-www-form-urlencoded` / `multipart/form-data` is
reachable by the classic **HTML-form-to-JSON CSRF** — a cross-site `<form>` can send those content-types with
**no CORS preflight**, so a "we only accept JSON, so we're safe from forms" assumption is false unless the parser
actually enforces it. Census: every mutating route × {guard present?, parser content-type-gated?}.

## A08:2025 — Software or Data Integrity Failures

**How to detect**: unsigned updates/artifacts; auto-deserialization of untrusted data into objects (insecure
deserialization, CWE-502); CI/CD that can be tampered (unprotected branches, unsigned commits on release paths);
critical data written without an integrity check; client-supplied data trusted for security decisions after a
round-trip.

**Fix**: sign and verify artifacts and critical data; never auto-deserialize untrusted input; protect and attest the
release pipeline (ties to A03/SLSA).

## A09:2025 — Security Logging and Alerting Failures

**How to detect**: are authn/authz events, high-value actions, and security errors logged? Are the logs
**free of secrets/PII/tokens** (over-logging is its own vuln — see domain M / `observability.md`)? Are logs
tamper-resistant and actually alerted on? Can you reconstruct an incident from them?

**🚩 grep**: logging full request bodies / headers (`Authorization`, cookies), `console.log(user)`,
`logger.info(token)`, no audit log on delete/role-change.

**Fix**: log security events with correlation IDs and without secrets; ship to a tamper-resistant store; alert on the
failures that matter; redact by default.

## A10:2025 — Mishandling of Exceptional Conditions

New in 2025. **How to detect**: errors handled inconsistently or swallowed; fail-**open** on an error in a security
check (exception → access granted); stack traces/internals leaked to the caller; resources (files, locks, sockets, DB
handles) not released on the error path; partial failure corrupts persisted state; a `catch` that logs and continues
as if nothing happened.

**🚩 grep**: `except: pass`, `catch (e) {}`, `catch { return true }` on an auth path, `rescue nil`, missing
`finally`/`defer`/context-manager around a resource.

**Fix**: handle errors explicitly and fail **closed** on security-relevant paths; release resources on every path;
never leak internals; keep state consistent under partial failure. See section F of `SKILL.md`.

---

## Secrets (cross-cutting)

Nothing sensitive in source, git history, comments, logs, error strings, or fixtures. Secrets via env/secret manager
only. Scan the **diff and the history** (`git log -p`, `gitleaks`, `trufflehog`). A secret that was ever committed is
compromised — rotate it, don't just delete it.

- **Anything with an expiry needs an inventory, an ahead-of-time alert, and rotation before it lapses — an unmonitored credential is a scheduled outage.**
  TLS certificates, code-/JWT-signing keys, API tokens, OAuth client secrets, DB passwords, cloud access keys, and
  domains all expire; when one lapses in production the failure is total and time-triggered (the classic "the cert
  expired at midnight and took everything down"), precisely because nothing was watching the clock. Distinct from
  rotating a *leaked* secret (above) and from validating a *request* token's `exp` (A07): this is the operational
  **lifecycle**. Check: (1) an **inventory** of every expiring credential/cert with its expiry date and an owner; (2)
  an **alert with lead time** (days/weeks ahead, not on the outage — a synthetic/uptime check catches the cert, an
  expiry-scan the rest); (3) **automated renewal/rotation ahead of expiry** (ACME / cert-manager for TLS; a scheduled
  rotation job for secrets/keys with an **overlap window** so old and new are both valid during cutover), not a manual
  calendar reminder. 🚩 a long-lived cert/secret/token with no renewal automation and no expiry monitor — a silent
  time-bomb. (Reliability consequence → `reliability-error-handling.md`; alert wiring → `observability.md`; the
  owner-facing inventory/reminder template lives in the `agentic-delivery` overlay's `incident-response.md` — here
  it's the review-time check.)

## Deterministic corroboration (cross-cutting) — an LLM claim rides on a proof it cannot generate

Running the project's wired scanners is already Phase 1 (`method.md`), and re-verifying a finding against source and
tests is already the fan-out discipline (`parallel-audit.md` §4–5). This adds the security-specific rule: for a class
of finding a **deterministic engine can *prove***, corroborate the LLM's claim against that proof or mark it
`unverified` — the review layers judgment on a proof no LLM reliably produces, it does not assert the proof.

- **Code-level SAST / quality engines** to run and read (tool-agnostic — the project's own wired one): **Semgrep** /
  OpenGrep (pattern + data-flow, autofix), **CodeQL** / GitHub code scanning (a query engine returning the source→sink
  path), **SonarQube** (quality gate + security *hotspots* — a hotspot is a triage signal, not a confirmed defect),
  **Snyk** (Code + Open Source), plus the ecosystem linters (`bandit`, `ruff`, `mypy`, `hadolint`).
- **The proof ↔ claim map** (corroborate, don't assert):
  - *"user input reaches this sink"* ↔ a **CodeQL taint / data-flow path** (source→sink); a claim with no path is
    `unverified`, not a finding.
  - *"this secret is real"* ↔ **TruffleHog** logging into the provider (Verified / Unverified / Unknown) — Unverified
    is not "clean" (the `Secrets` rule above still holds: a committed secret is compromised).
  - *"this dependency version is vulnerable"* ↔ an **exact version↔CVE match** against machine-readable ranges
    (`osv-scanner` / Trivy / Grype — `dependency-currency-and-upgrades.md`), replacing the LLM's error-prone recall of
    affected ranges.
  - *"you're exposed because you depend on X"* ↔ **reachability** (Semgrep Supply Chain): a dep vuln matters only when
    code matches the vulnerable pattern — importing ≠ executing.
- **Ingestion:** pull deterministic findings through the standard interchange formats — **SARIF 2.1.0** (any scanner →
  code-scanning alerts) and **OSV JSON** (advisory data) — so the review reasons over a machine-readable proof, not a
  screen-scrape.

API-specific overlay (API1–API10): `security-api.md`.

## Going deeper

- **ASVS 5.0.0** — the version recorded as latest stable in the standards index (the OWASP project page confirms
  5.0.0); use it as the L1/L2/L3 verification checklist when you need depth beyond the Top 10, and pick the level that
  matches the app's risk. Citing ASVS as a *reference* is not the same as having walked it: only claim ASVS coverage
  in the report if the review actually verified the requirements, and say which level and which chapters.
- **WSTG** — the how-to-test companion for each risk above.
- **CWE Top 25 (2025)** — weakness-level detail; the current top entries are XSS (CWE-79), SQL Injection (CWE-89),
  CSRF (CWE-352), Missing Authorization (CWE-862), Out-of-bounds Write (CWE-787), Path Traversal (CWE-22),
  Use-After-Free (CWE-416), Out-of-bounds Read (CWE-125), OS Command Injection (CWE-78), and Code Injection (CWE-94).
