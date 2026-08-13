# Application security — OWASP Top 10:2025 review playbook

Read this when the target exposes any network surface (web app, API, service,
CLI that touches untrusted input), handles authentication/authorization, or
processes data from users, files, or third parties. It expands section B of
`SKILL.md` with per-category **detection procedures**, red-flag greps, a
minimal safe verification, and the fix. Map every finding to the category and,
where useful, the CWE.

Standards this file tracks (see `docs/standards-index.md` for verified URLs and
verification dates): OWASP Top 10:2025, OWASP API Security Top 10 (2023), OWASP
ASVS 5.0, OWASP WSTG, and the 2025 CWE Top 25.

> Verification etiquette: prove exploitability **locally and non-destructively**
> only. Never attack a system you do not own or lack written authorization to
> test; never run an exploit against production, shared, or third-party
> infrastructure. A plausible-but-unproven issue is reported as `unverified`
> with the reason — it is still a finding.

---

## A01:2025 — Broken Access Control (includes SSRF)

The most exploited class. Every sensitive read/write must prove the caller is
authorized **server-side**, on every request.

**How to detect in review**
- Enumerate every route/handler/mutation. For each, find where authorization is
  checked. A route with no server-side check is the finding — do not assume a
  middleware covers it; trace it.
- Look for object references taken from the request (`/orders/:id`, `userId` in
  a body) that are used to fetch/modify data **without** confirming the object
  belongs to the caller → IDOR (CWE-639 / CWE-862 Missing Authorization, #4 on
  the 2025 CWE Top 25).
- Authorization decided in the client (hidden buttons, front-end route guards)
  with no server enforcement = no authorization.
- Default posture: is it deny-by-default (allowlist of who may act) or
  allow-by-default (blocklist)? The latter fails open on every new route.
- **SSRF** (now folded into A01): any URL/host/IP taken from input and fetched
  server-side. Confirm an allowlist and that internal ranges
  (`127.0.0.0/8`, `169.254.169.254` cloud metadata, `10/172.16/192.168`,
  `::1`, `.internal`) are blocked **after** DNS resolution (guard against
  DNS-rebinding and decimal/octal IP encodings).

**🚩 grep**: `req.params`/`req.body` id flowing straight into a query; routes
without an auth decorator/guard; `fetch(userSuppliedUrl)`, `requests.get(url)`,
`axios.get(url)` where `url` derives from input; `role === 'admin'` checked only
in UI code.

**Fix**: centralized, deny-by-default authorization checked at the data layer
(row-level / object-level), keyed on the authenticated principal — not on IDs
from the request. For SSRF: allowlist hosts, resolve-then-validate the IP,
disable redirects to new hosts, and fetch through an egress proxy where possible.

## A02:2025 — Security Misconfiguration

**How to detect**: debug/verbose errors in prod; stack traces returned to
clients; default or sample credentials; overly permissive CORS
(`Access-Control-Allow-Origin: *` **with** credentials); directory listing;
admin/actuator/`/debug` endpoints reachable; missing security headers
(HSTS, `Content-Security-Policy`, `X-Content-Type-Options`, frame-ancestors);
cloud storage/buckets world-readable; unnecessary services/features enabled.

**🚩 grep**: `DEBUG = True`, `NODE_ENV` not enforced to `production`,
`Access-Control-Allow-Origin: *`, `cors({ origin: true, credentials: true })`,
`app.use(errorhandler())` in prod, `.enable('trust proxy')` misused.

**Fix**: harden by default; ship prod config that disables debug, sets headers,
scopes CORS to known origins, and removes sample/default accounts. Track against
CIS Benchmarks for the runtime/platform.

## A03:2025 — Software Supply Chain Failures

Elevated in 2025. Covers dependencies, build, and CI/CD provenance.

**How to detect**: lockfile present and honored (`package-lock.json`,
`poetry.lock`, `go.sum`, `Cargo.lock`)? Dependencies pinned (no floating
`^`/`latest` for security-critical libs)? Any unmaintained/abandoned or
typosquatted package (name a character off from a popular one)? Install-time
scripts (`postinstall`) from untrusted packages? CI actions pinned to a **commit
SHA**, not a mutable tag (`@main`, `@v3`)? Is the build reproducible/hermetic?
Is there dependency + image scanning and an SBOM?

**🚩 grep**: `"postinstall"` in `package.json`, `uses: actions/*@main`,
unpinned base images (`FROM node:latest`), `curl … | bash` in build steps,
dependencies added in a diff without a lockfile update.

**Fix**: pin by hash, commit lockfiles, scan dependencies and images in CI,
generate an SBOM (CycloneDX/SPDX), and adopt provenance (SLSA) for released
artifacts. See `infra-iac-containers.md` and section K of `SKILL.md`.

## A04:2025 — Cryptographic Failures

**How to detect**: TLS enforced end-to-end (no plaintext transport of secrets);
no weak/legacy primitives (MD5, SHA-1, DES, RC4, ECB mode); passwords hashed
with a memory-hard KDF (argon2id / bcrypt / scrypt), never fast hashes or
encryption; secrets not hard-coded; IVs/nonces unique per message; randomness
from a CSPRNG (`secrets`, `crypto.randomBytes`), never `Math.random`/`rand()`
for security; keys rotated and stored in a KMS/secret manager.

**🚩 grep**: `md5(`, `sha1(`, `DES`, `AES/ECB`, `Math.random()` near token/id
generation, `random.random()` for secrets, hard-coded keys/IVs, `password` +
`sha256` without a salt/KDF.

**Fix**: TLS everywhere; argon2id for passwords; AEAD ciphers (AES-GCM,
ChaCha20-Poly1305) with unique nonces; CSPRNG for all security-relevant
randomness; keys in a managed store.

## A05:2025 — Injection

SQL/NoSQL/OS-command/LDAP/XPath/template/header injection and XSS. Corresponds
to several top-of-list 2025 CWEs (XSS #1, SQLi #2, OS Command Injection #9,
Code Injection #10).

**How to detect**: any query/command/markup **built by string concatenation or
interpolation** from input. Confirm parameterized queries / prepared statements
/ bound ORM params for SQL; safe templating with contextual auto-escaping for
HTML (no raw sinks); argument arrays (not a shell string) for subprocess calls;
no `eval`/`exec`/dynamic code from input; safe deserialization only.

**🚩 grep**:
- SQL: `"SELECT … " +`, f-strings/`format`/template literals inside a query,
  `.query(\`… ${x} …\`)`, `execute("… %s" % x)`.
- XSS: `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `|safe`,
  `render_template_string`, `document.write`.
- Command: `os.system`, `subprocess.*(shell=True)`, `child_process.exec(`,
  `Runtime.exec(` with a concatenated string, backticks.
- Code: `eval(`, `exec(`, `Function(`, `pickle.loads`, `yaml.load` (unsafe).

**Fix**: parameterize; use the ORM's bound parameters; contextual output
encoding + a strict CSP; argument-vector subprocess calls; never deserialize
untrusted data with an unsafe loader. See `language-stack-redflags.md` for
per-language sinks.

## A06:2025 — Insecure Design

A missing control, not a buggy one. **How to detect**: is there a threat model
for the sensitive flows (auth, payment, data export, admin)? Are abuse cases
considered (what if the user is hostile / the upstream is compromised)? Are
rate limits, quotas, and business-logic limits **designed in** (e.g. can a user
request 10,000 password resets, redeem a coupon twice, or race a balance check)?
Secure defaults, or must the operator remember to turn safety on?

**Fix**: threat-model the flow, add server-side business-logic limits, make the
safe path the default. Cross-reference OWASP API Security Top 10 (2023) API4
(Unrestricted Resource Consumption) and API6 (Unrestricted Access to Sensitive
Business Flows) for API work.

## A07:2025 — Authentication Failures

**How to detect**: credential-stuffing exposure (no rate limit / lockout / bot
defense on login); weak password policy; session fixation (session id not
rotated on login); tokens that don't expire or are reusable after logout;
missing MFA on high-value accounts; JWTs with `alg: none`, weak secrets, or no
expiry/audience check; password reset tokens that are guessable or long-lived.

**🚩 grep**: `jwt.decode(… verify=False)`, `algorithms=['none']`, no `exp`
claim, session id reused across privilege change, `password == input` (plaintext
compare), reset tokens from a non-CSPRNG.

**Fix**: rate-limit and lock out; rotate session on auth state change; short
token lifetimes + server-side revocation; verify JWT signature/alg/exp/aud; MFA
where warranted.

## A08:2025 — Software or Data Integrity Failures

**How to detect**: unsigned updates/artifacts; auto-deserialization of untrusted
data into objects (insecure deserialization, CWE-502); CI/CD that can be
tampered (unprotected branches, unsigned commits on release paths); critical
data written without an integrity check; client-supplied data trusted for
security decisions after a round-trip.

**Fix**: sign and verify artifacts and critical data; never auto-deserialize
untrusted input; protect and attest the release pipeline (ties to A03/SLSA).

## A09:2025 — Security Logging and Alerting Failures

**How to detect**: are authn/authz events, high-value actions, and security
errors logged? Are the logs **free of secrets/PII/tokens** (over-logging is its
own vuln — see `L` observability)? Are logs tamper-resistant and actually
alerted on? Can you reconstruct an incident from them?

**🚩 grep**: logging full request bodies / headers (`Authorization`, cookies),
`console.log(user)`, `logger.info(token)`, no audit log on delete/role-change.

**Fix**: log security events with correlation IDs and without secrets; ship to a
tamper-resistant store; alert on the failures that matter; redact by default.

## A10:2025 — Mishandling of Exceptional Conditions

New in 2025. **How to detect**: errors handled inconsistently or swallowed;
fail-**open** on an error in a security check (exception → access granted);
stack traces/internals leaked to the caller; resources (files, locks, sockets,
DB handles) not released on the error path; partial failure corrupts persisted
state; a `catch` that logs and continues as if nothing happened.

**🚩 grep**: `except: pass`, `catch (e) {}`, `catch { return true }` on an auth
path, `rescue nil`, missing `finally`/`defer`/context-manager around a resource.

**Fix**: handle errors explicitly and fail **closed** on security-relevant
paths; release resources on every path; never leak internals; keep state
consistent under partial failure. See section F of `SKILL.md`.

---

## Secrets (cross-cutting)

Nothing sensitive in source, git history, comments, logs, error strings, or
fixtures. Secrets via env/secret manager only. Scan the **diff and the history**
(`git log -p`, `gitleaks`, `trufflehog`). A secret that was ever committed is
compromised — rotate it, don't just delete it.

## API-specific overlay (OWASP API Security Top 10, 2023)

For HTTP/GraphQL/gRPC APIs, also walk: API1 Broken Object Level Authorization
(the #1 API risk — same root as IDOR), API2 Broken Authentication, API3 Broken
Object Property Level Authorization (mass-assignment / over-exposure of fields),
API4 Unrestricted Resource Consumption, API5 Broken Function Level
Authorization, API6 Unrestricted Access to Sensitive Business Flows, API7
Server Side Request Forgery, API8 Security Misconfiguration, API9 Improper
Inventory Management (undocumented/legacy/`v1` endpoints still live), API10
Unsafe Consumption of APIs (trusting a third-party API's response blindly).

## Going deeper

- **ASVS 5.0** — use as the verification checklist when you need depth beyond
  the Top 10; pick L1/L2/L3 to match the app's risk.
- **WSTG** — the how-to-test companion for each risk above.
- **CWE Top 25 (2025)** — weakness-level detail; the current top entries are
  XSS (CWE-79), SQL Injection (CWE-89), CSRF (CWE-352), Missing Authorization
  (CWE-862), Out-of-bounds Write (CWE-787), Path Traversal (CWE-22),
  Use-After-Free (CWE-416), Out-of-bounds Read (CWE-125), OS Command Injection
  (CWE-78), and Code Injection (CWE-94).
