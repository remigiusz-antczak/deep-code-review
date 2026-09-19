# Application security — OWASP Top 10:2025 review playbook

Read this when the target exposes any network surface (web app, API, service,
CLI that touches untrusted input), handles authentication/authorization, or
processes data from users, files, or third parties. It expands section B of
`SKILL.md` with per-category **detection procedures**, red-flag greps, a
minimal safe verification, and the fix. Map every finding to the category and,
where useful, the CWE.

Standards this file tracks (see `references/standards-index.md` when installed
with the skill, else `docs/standards-index.md` in the skill repository): OWASP Top
10:2025, OWASP API Security Top 10 (2023), OWASP ASVS 5.0, OWASP WSTG, and the
2025 CWE Top 25.

> Verification etiquette: prove exploitability **locally and non-destructively**
> only. Never attack a system you do not own or lack written authorization to
> test; never run an exploit against production, shared, or third-party
> infrastructure. A plausible-but-unproven issue is reported as `unverified`
> with the reason — it is still a finding.

---

## A01:2025 — Broken Access Control (includes SSRF)

The most exploited class. Every sensitive read/write must prove the caller is
authorized **server-side**, on every request. Prefer **safe probes** (missing
header, id swap, status/body compare) over exploit kits.

**Identity Arrival Map (required before proposing any gate).** Before
recommending middleware, a document-level redirect, or an edge gate — especially
for apps embedded in an iframe, portal host, or third-party shell — fill this
table from evidence:

| Request class | What identity arrives? | What a gate can see | Can a client forge it? |
|---|---|---|---|
| Document / RSC / SSR (navigation) | ? | ? | ? |
| Same-origin XHR / `fetch` (Bearer, custom headers) | ? | ? | ? |
| Cross-site / bare `curl` (no cookies, no Bearer) | ? | ? | ? |

**Forgeability / bypass row-set (required with the map):** (1) Is the **origin
reachable directly**, bypassing the edge/WAF that enforces auth? (2) Does the
app **strip inbound copies** of trusted proxy/identity headers (`X-Forwarded-*`,
`X-User`, host-injected claims)? (3) Does the gate matcher cover `/path`,
`/path/`, case variants, encoded traversal (`%2e%2e`), and **non-GET** verbs?
(4) Path normalization before match? **(5) Do the edge/proxy and the origin
agree on where one HTTP message ends and the next begins** — `Transfer-Encoding`
vs `Content-Length` precedence, consistently by HTTP version — or can a crafted
request desync them so the edge inspects one message while the origin executes a
different, smuggled one (HTTP request smuggling, CWE-444)? A gate whose input a
client can set is not a gate.

**Known anti-pattern:** "add middleware on the document request" when identity
only arrives on same-origin XHR via a client-attached Bearer (or host-injected
header the document never carries). Propose a gate only on a request class that
actually carries the principal. Cross-ref Phase 0 platform-vs-app-vs-preflight.

**Smuggling defeats a correct gate without forging anything.** Every header check
above can be correct and the gate still bypassed if the edge/WAF and the origin
disagree on request boundaries: a `Transfer-Encoding` header alongside a
`Content-Length`, parsed inconsistently by the two hops (CL.TE / TE.CL / TE.TE),
lets one connection smuggle a second, uninspected request past the WAF into the
origin — or poison the connection so the *next* user's request arrives prefixed with attacker bytes it can capture — a confidentiality break, not just an authz bypass. The anonymous-GET sweep proves nothing here — it shows only that the
edge's *own* parser rejects requests it recognizes as unauthenticated, not that the
edge and origin agree on what a request *is*. In HTTP/1.x a present `Transfer-Encoding`
means `Content-Length` must be ignored (ASVS v5.0.0-4.2.1, L2); reject or normalize a
message carrying both. 🚩 a reverse proxy and origin of different vendors/versions in
front of an auth gate with no desync-specific test — plain `curl` will not surface it;
it needs a raw-socket / desync tool.

**Bidirectional gate proof (required before recommending a gate).** Every
proposed gate ships an expected-status table **per request class**, before and
after: anonymous → 401/redirect **and** legitimate member → 200 on the **same**
class; plus a test that **fails with the gate removed**. A proposal missing the
member→200 row is incomplete — do not recommend it (this is how outage-causing
middleware ships).

**How to detect in review**
- Enumerate every route/handler/mutation **and** non-route entry points: server
  actions, RPC/tRPC, GraphQL resolvers, cron/webhooks, websocket handlers. For
  each, find where authorization is checked. Do not assume middleware covers it.
- **Dual surface (API redaction ≠ page protection).** For every sensitive loader,
  inventory **every** caller: JSON/API handler, RSC/SSR/`page.tsx`, serialized
  props / streaming flight payload (not only rendered DOM), framework-generated
  data siblings, BFFs, mobile clients. Divergence — one surface redacts/401s
  while another returns the full object — is **Critical** when world-reachable.
- **An export/download is a *sharper* leak surface than an on-screen view.** A file
  leaves with the user, redistributable **beyond** the auth boundary, so a leak
  there outlives the session and the gate. Put every export/download route in the
  dual-surface census above and hold it **no weaker than, and preferably stricter
  than,** the dashboard — public-tier rows only, or at least the **same token *and*
  scope** as the guarded API, never an unauthenticated or unscoped dump. Corollary for SSR: confidential, per-viewer
  data belongs behind an **authenticated, server-scoped API** the client calls, not
  baked into a server-rendered page whose only identity is client-side (the SSR row
  of the Identity Arrival Map above cannot scope what it never receives).
- **Tenant / row scoping.** Confirm tenant/owner predicates are applied in a
  **shared accessor**, not ad-hoc per call site. Flag request-path use of an
  admin/service credential that bypasses row policy as Critical. "DB policy
  enabled" is unproven until a test shows the app path cannot skip it. Never trust
  `tenant_id` / `org_id` from the body alone — bind to the authenticated principal.
- Authorization decided only in the client = no authorization. Default:
  deny-by-default.
- **SSRF**: URL/host/IP from input fetched server-side → allowlist +
  resolve-validate-**pin** the IP; block loopback, RFC-1918, CGNAT, link-local
  metadata (`169.254/16`), IPv4-mapped/6to4, `.internal`, dotless labels;
  `redirect: manual` and re-validate each hop. (Full range list stays here — do
  not restate a divergent copy in `SKILL.md`.)
- **Untrusted-egress caller census (after a guard lands):** inventory every
  call site that fetches an untrusted or attacker-influenced URL (HTTP clients,
  redirect-following options, robots/calendar/sidecar scripts — language-
  neutral, not a single API name). Confirm each uses the guarded transport and
  hop-revalidates; a breaker or allowlist on **one** client while siblings still
  follow redirects bare is the same class of miss. A guard nothing calls is a
  no-op.

**Two-principal matrix (mandatory beside the anonymous sweep).** Seed two
accounts (different tenant/role when multi-tenant). For every object-bearing
route: replay A's request with B's id / B's token / B's tenant. Expected:
`own → 200`, `other → 403/404`, `none → 401`. Missing a second account →
`Decisions needed`, not a skip. Most production authz bugs are
authenticated-but-unauthorized; reading code for IDOR is not enough.

**Segregation of duties — a consequential action needs a distinct *second*
principal, and this is not the two-principal matrix above.** The matrix tests
that principal A cannot reach principal B's *object* (cross-principal access,
IDOR). Segregation of duties is the orthogonal axis: the **same** principal must
not be able to both **initiate and approve** a high-consequence action — issue
and approve a payout, create and activate a credential, request and grant
elevated access, submit and merge to a protected surface. Check that
**`approver != requester` is enforced server-side on a stable principal id** (not
a client field, not a display name), that a user cannot **self-grant** the
approver role to satisfy it, that it is scoped to genuinely consequential actions
(gating every write is friction, not control), and that the maker-checker
decision is **audit-trailed** — who requested, who approved, when (cross-ref
`observability.md` § Audit trail & repudiation; don't restate). Absent, one
compromised or malicious account completes the whole chain alone. (SOX, PCI DSS,
and NIST 800-53 AC-5 mandate this control; whether a given target is legally
required to enforce it routes to `business-ops` / counsel, not this gate.)
- **🚩** a consequential action (payout, credential issue, privilege grant,
  protected-surface merge) whose initiate and approve steps accept the **same**
  principal id; an `approver` / `approved_by` read from a client field or equal
  to the requester; an approver role a user can grant themselves.

**Cache / CDN is an authorization surface.** Responses derived from identity must
be `Cache-Control: private` / `no-store` (or keyed by principal). Check
framework static vs dynamic decisions for pages that read cookies/headers;
require `Vary` on every identity input (`Cookie`, `Authorization`, custom
auth headers). Sweep **through the CDN as well as origin**; compare anonymous
body vs member body for the same URL. Origin-only anon GET can look clean while
the edge serves a cached member page.

**Presigned / signed URLs & uploads.** Presigned URLs: one object, short TTL,
re-issued per request; must die on permission revocation. User uploads: authorize
per object; never rely on unguessable paths; size/type/magic-bytes checks;
no executables in public dirs; SVG/HTML as stored XSS; archive extract =
zip-slip risk (see A05 files block).

**🚩 grep**: `req.params`/`req.body` id → query; ungated routes; `fetch(userUrl)`;
`role === 'admin'` in UI only; shared loaders across API + page with asymmetric
redaction; `Cache-Control: public` on auth'd handlers; `tenant_id` from body;
trusted headers read without strip; `getSignedUrl` / long-lived signed links.

**Fix**: deny-by-default authz at the data layer on **every** entry point; strip
forgeable identity headers; private/no-store (or keyed) caches; bidirectional
tests. Never recommend document-middleware without a completed Identity Arrival
Map + bidirectional proof.

**Anonymous GET sweep (mandatory opener — local/dev by default).** Hit every
documented GET with **no cookies and no Authorization**. Default target =
local/dev/staging you own; production/shared host requires **explicit owner
authorization** — else record `unverified` + needed artifact (staging URL /
route table). Record status + size; **also** follow redirects separately, grep
bodies for sentinel/canary fields from private data, and **diff anon vs
authenticated body** for the same URL (subset-equality = pass — size alone
misses small leaks and login-shell 200s).

```bash
# Tune BASE + paths from the route inventory; no auth headers. Local/dev first.
for path in / /api/meta /api/... ; do
  curl -s -o /tmp/body -w "%{http_code} %{size_download} $path\n" "$BASE$path"
done
```

World-reachable sensitive catalog → Critical under S0–S3 in `SKILL.md`.

**Exposure-boundary discriminator.** Pin severity to boundary × confidentiality
tier: VCS-tracked? unauthenticated route (anon sweep)? client bundle? CDN cache?
Not to how scary the React looks.

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
typosquatted package (name a character off from a popular one)? Any **slopsquat**
risk — a *newly-added* dependency whose name an LLM may have **hallucinated** (a
plausible name that never existed until an attacker pre-registered it, which
name-proximity does **not** catch)? Verify a new dependency resolves to an
**established** package (registry age, download history, a real source repo /
provenance), not merely that it isn't a typo of a popular one — LLM-hallucinated
package names are a **predictable** pre-registration target (a material share of
AI-recommended packages don't exist, and the *same* hallucinations recur across
runs — package-hallucination study logged in `docs/standards-index.md`). Cross-ref
`dependency-currency-and-upgrades.md` (the release-age cooldown extends to
never-existed-until-now). Install-time scripts (`postinstall`) from untrusted
packages? CI actions pinned to a **commit
SHA**, not a mutable tag (`@main`, `@v3`)? Is the build reproducible/hermetic?
Is there dependency + image scanning and an SBOM — and, if an SBOM ships, is it
paired with a **VEX** whose `not_affected` entries each carry a justification (see
Fix)? **CI/CD trigger & token
hygiene** — does a `pull_request_target` (or `workflow_run`) workflow check out
untrusted PR head code? GitHub's hardening guide: these triggers "expose the
repository to security compromises" and "must not explicitly check out untrusted
code." Is untrusted `${{ github.event.* }}` interpolated straight into a `run:`
step (script injection — route it through an intermediate `env:` var)? Is
`GITHUB_TOKEN` / `permissions` read-only by default and escalated per job?
**Verification vs authenticity** — is a released artifact **signed**
(SLSA / sigstore), or only checksummed over the **same channel** it ships on? (Producer-side signing depth — cosign/Sigstore, npm/PyPI provenance, GPG — is in `release-engineering.md`.) A
same-origin checksum defends against corruption and a CDN mishap, **not** a
compromised origin, so it does not neutralize the trust-on-first-use risk of a
`curl | sh` install from that origin.

**Provenance is only as strong as its verification.** SLSA's own Build track
separates *provenance exists* (**L1** — trivial to forge, may be unsigned) from
*signed provenance from a hosted builder* (**L2**) and a *hardened, tamper-resistant
build* (**L3**), so a bare "adopts SLSA" with **no level named** is unverified
strength, not the strong guarantee. The failure that reads as done but isn't: an
artifact **generates** provenance / an SBOM, but the **deploy or promotion step
never checks it**. It must **verify the attestation before promoting** — the
attestation's **subject digest matches the artifact** being promoted (the spec's
first check, or a validly-signed attestation for a *different* artifact passes), its
signature is valid, the **signer / builder identity is one you trust**, and the
recorded **canonical source repository** (and, where the builder records it, the
commit) matches what you expect — and **fail closed** on a missing or mismatched
attestation, not merely emit a file nothing downstream re-reads. This is the runtime-proven-gate
lens (domain B) applied to the supply chain, and the **same blocking-gate bar**
already required for inbound package signatures (`infra-iac-containers.md`): the
outbound attestation of the thing you actually ship deserves the same enforcement.

**🚩 grep**: `"postinstall"` in `package.json`, `uses: actions/*@main`,
unpinned base images (`FROM node:latest`), `curl … | bash` in build steps,
dependencies added in a diff without a lockfile update, `pull_request_target`
paired with a checkout of the PR head, `${{ github.event.` inside a `run:`
block, a workflow with no `permissions:` block or `permissions: write-all`, an
install path whose only integrity check is a checksum served from the same host
as the artifact.

**Fix**: pin by hash, commit lockfiles, scan dependencies and images in CI,
generate an SBOM (CycloneDX/SPDX), and adopt provenance (SLSA) for released
artifacts. Pair the SBOM with a **VEX** (Vulnerability Exploitability eXchange) —
a producer-issued, per-CVE exploitability assertion (`not_affected` **with a
justification**, `affected`, `fixed`, `under_investigation`) so a consumer can tell
a real exposure from a component that merely *ships* the vulnerable code on an
unreachable path; it complements, never replaces, the SBOM (CISA VEX). For
workflows: never check out untrusted PR code under
`pull_request_target`; set `permissions` to least privilege (read by default,
escalate per job); pass untrusted context through an `env:` var, never inline
`${{ }}` in `run:`; sign released artifacts (a checksum is integrity, not
authenticity). **Severity keys on reachability** — a weak install verification on
the *sole documented install path for every user* outranks the same weakness on
an optional side channel. See `infra-iac-containers.md` and section K of `SKILL.md`.

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

**TLS enforced is not TLS validated.** "TLS everywhere" above is about the wire; it
says nothing about whether the *client* checks who it is talking to. A client with
certificate validation disabled — `verify=False` (Python `requests`),
`rejectUnauthorized: false` / `NODE_TLS_REJECT_UNAUTHORIZED=0` (Node),
`InsecureSkipVerify: true` (Go), an all-accepting `TrustManager` / `HostnameVerifier`
(Java), `curl -k` / `--insecure` — still shows `https://` in every URL and satisfies
"TLS everywhere" by the letter while trusting **any** certificate from **any** host, so
a MITM terminates and re-originates the connection for free (CWE-295, "Improper
Certificate Validation"; the hostname-mismatch sub-case is CWE-297). It is commonly a debugging shortcut against a
self-signed internal cert that shipped un-reverted. Internal / service-to-service TLS
is **not** exempt — pin the specific internal CA or self-signed cert, do not disable
validation to reach it (ASVS v5.0.0-12.3.2 requires TLS clients validate certificates;
-12.3.4 requires internal services trust only specific internal CAs / self-signed
certs). **🚩 grep**: `verify\s*=\s*False` near `requests.` / `urllib3`,
`rejectUnauthorized:\s*false`, `NODE_TLS_REJECT_UNAUTHORIZED`, `InsecureSkipVerify:\s*true`,
an empty or always-true `TrustManager` / `HostnameVerifier`, `ssl._create_unverified_context` (Python), `curl .*(-k|--insecure)`.
(Distinct from the JWT `verify=False` in A07 — that is signature verification, not TLS.)

**Crypto-agility & post-quantum readiness.** Beyond using strong *current*
primitives, check the code can **change** them: algorithm choices named in
config / metadata (a versioned suite id), not hard-coded at each call site, so a
primitive can be rotated without a rewrite — and a ciphertext / signature envelope
carries an algorithm identifier so old and new can coexist during a migration.
For **long-lived** confidentiality (data or secrets that must stay secret for
years), weigh **harvest-now-decrypt-later**: an adversary can record
classical-encrypted traffic today and decrypt it once a cryptographically-relevant
quantum computer exists — so long-lived secrets warrant a migration path to the
NIST post-quantum standards: **FIPS 203 ML-KEM** (key encapsulation), **FIPS 204
ML-DSA** and **FIPS 205 SLH-DSA** (signatures), published 2024. Not every system
needs PQC now; the finding is a **hard-coded, un-versioned primitive with no swap
path on a long-lived-data surface** — not "you must ship ML-KEM today" (that would
be stricter than the standard).

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

**Files, archives & parsers.** Uploads: enforce a size cap **and** an allow-list
of types validated by **magic bytes**, not the client-supplied `Content-Type` or
extension. Store outside any directory the server will execute or serve as code;
no executables in public dirs. Treat SVG and HTML as **stored XSS** — serve from
a separate origin, or `Content-Disposition: attachment` +
`X-Content-Type-Options: nosniff`, never inline on the app origin. Archive
extraction: reject entries whose resolved path escapes the target dir
(**zip-slip**, CWE-22), plus symlinks, absolute paths, and decompression bombs
(cap entry count and uncompressed size). XML parsers: **disable external
entities and DTDs** (XXE, CWE-611) — `defusedxml` in Python,
`setFeature(FEATURE_SECURE_PROCESSING, true)` / disallow-doctype-decl in Java,
`noent: False` for lxml. Same posture for any format with an include/reference
mechanism (XSLT, SVG `<use>`, YAML anchors, spreadsheet formulas).

## A06:2025 — Insecure Design

A missing control, not a buggy one. **How to detect**: is there a threat model
for the sensitive flows (auth, payment, data export, admin)? Are abuse cases
considered (what if the user is hostile / the upstream is compromised)? Are
rate limits, quotas, and business-logic limits **designed in** (e.g. can a user
request 10,000 password resets, redeem a coupon twice, or race a balance check)?
Secure defaults, or must the operator remember to turn safety on?

**Which threat-model method — name the one that fits, don't hand-wave "a threat model."**
**STRIDE** (per element: Spoofing / Tampering / Repudiation / Info-disclosure / DoS /
Elevation) for a component or data flow; **PASTA** when the model must tie threats to
business impact; **attack trees** to decompose one attacker goal; **LINDDUN** for *privacy*
threats (STRIDE's privacy counterpart — its **Linkability** / **Identifiability**
threats have a concrete lens in `privacy-compliance.md` § Linkability &
re-identification, its **Detectability** threat in A07 account-enumeration below);
**MAESTRO** for an *agentic-AI* system — the agentic
threat-modeling method, complementary to the OWASP ASI / MITRE ATLAS catalogs in
`security-ai-agents.md`. The review lens is **coverage, not ceremony**: a change that
introduces a new trust boundary, principal, or state transition the existing model never
considered is a finding — the model went **stale relative to the diff** — and an agentic
surface with no agent-specific (MAESTRO-shaped) model is the common miss. (Maturity frames —
NIST SSDF, OWASP SAMM, BSIMM — measure the org's *program*, not this diff; name, don't score.)

- **A producer crossing a publish / trust boundary invalidates guards scoped to the old side —
  re-audit them.** A guard's *sufficiency* is often conditioned on a precondition — "internal
  only," "never published," "not user-facing," "dry-run," "behind auth." When a change wires that
  producer **across** the boundary (to a published / trusted / user-facing / external consumer),
  every guard justified by the old precondition must be **re-audited under the new one** — a
  weaker guard that was fine "because it never publishes" now ships its excused defect to the
  public surface (a false attribution, say). Two things hide it: the comment defending the weaker
  guard is now **out of date** (its precondition changed) yet reads authoritative, and the guard and the
  boundary-crossing edit usually live in **different files**, so a diff-scoped review sees one but
  not the other (the DIFF blast-radius rule, `SKILL.md`).
- **🚩 at the crossing:** a guard whose rationale cites "internal only / never published / dry-run /
  no rows" on a producer the same change wires to a published or external surface.
- **A rendered *trust signal* must resist *visual* spoofing, not only injection — STRIDE
  Spoofing at the display layer.** When user-controlled text is shown as an identity a human
  or system trusts and acts on, HTML-escaping and input-sanitizing do **not** stop **Unicode
  confusables / mixed-script homographs** — visual identity ≠ string identity, so the trust
  decision is made on a lie. The spoofable surfaces, a worked example, and the detection
  mechanism (Unicode skeleton / mixed-script restriction, UTS #39) live in `i18n-l10n.md` —
  threat-model such a signal for spoofing and check it there. Distinct from dependency
  typosquatting (`dependency-currency-and-upgrades.md`) and the bidi / Trojan-Source class
  (`i18n-l10n.md`).
- **🚩** a domain / sender-name / package-name / username rendered from user-controlled text as
  a trust cue with only HTML-escaping — no confusable or mixed-script check.

**Detect steps, in order**
- **Inventory the money/state machines.** List every flow that moves value or
  advances state: checkout, refund, credit/balance, coupon, invite, quota,
  approval, tier change. For each, write the legal state transitions; anything
  not listed must be rejected server-side, not merely un-rendered.
- **Client-trust fields.** Diff request bodies against what the server
  recomputes. `price`, `amount`, `currency`, `qty`, `discount`, `tier`, `step`,
  `status`, `isAdmin` arriving from the client and persisted without
  re-derivation from server state is a finding. Wizards: confirm the server
  validates the *whole* invariant on the final step, not just `step`
  monotonicity — a client can post the final step first.
- **TOCTOU on redeem/balance.** Any check-then-act (coupon redeem, balance
  debit, seat claim, one-time token) needs a single atomic mutation:
  conditional/compare-and-set update, `SELECT … FOR UPDATE`, or a unique
  constraint on the redemption key. Read-then-write in separate statements
  without a transaction/lock → race. Verify by firing N concurrent identical
  requests locally and asserting exactly one succeeds.
- **Rate-limit key, burst, and failure mode.** Ask what the limiter is keyed on
  (IP alone is bypassable; key on principal **and** target resource), whether
  burst is bounded (fixed windows allow 2× at the boundary), and what happens
  when the counter store is unreachable — **fail-open on limiter error is the
  bug**, and it is common. Confirm limits are enforced server-side for every
  entry point into the flow, not just the primary route.

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

**Account enumeration is a detectability leak (CWE-203 Observable Discrepancy).**
On signup, login, and password-reset, diff the response — status code, body / error
text, redirect target, **and response time** — between *subject exists* and *subject
does not exist*. A distinguishable response on any of those axes lets an
unauthenticated outsider enumerate valid accounts (LINDDUN's *Detectability*
threat): a different string for "invalid username" vs "invalid password"; a
`409`/`422` on signup revealing "email taken"; a reset endpoint that emails-or-not
based on existence. Fix: one **generic response** for the exists/not-exists pair and
a **constant-time** path so existence is not observable — not the removal of
per-field validation.

**Session cookie flags (server-side checklist — read the `Set-Cookie` bytes, not
the config object).** Every session/auth cookie: `Secure` (never sent over
plaintext), `HttpOnly` (no JS read — blunts XSS token theft), `SameSite=Lax` or
`Strict` for session cookies; `SameSite=None` **requires** `Secure` and a real
cross-site reason, so treat it as a finding until justified. Also check
`Path=/`-vs-scoped, host-only vs `Domain=` (a `Domain` cookie leaks to every
subdomain — including one an attacker controls via subdomain takeover),
`__Host-` prefix where applicable, and a bounded `Max-Age`/`Expires`. Verify with
`curl -si` on the login response; a framework default can be silently overridden
by a proxy or a custom cookie writer.

**OAuth / OIDC.** `redirect_uri` matched against an **exact allow-list** (no
prefix/wildcard/open-redirect chaining — this is how tokens get exfiltrated);
**PKCE** (S256, not `plain`) on every public client and, per current guidance, on
confidential clients too; `state` bound to the user's session and verified on
callback (CSRF on the authorization flow); `nonce` present in the request and
checked inside the returned ID token. Validate the ID token's `iss`, `aud`,
`exp`, and signature against the provider's JWKS — never accept an unverified
token or one fetched from an issuer-supplied URL without pinning. Implicit flow
and tokens in URL fragments/query strings are findings.

**JWT algorithm confusion (asymmetric token verified as symmetric).** `alg: none`
(above) is the degenerate case; the live-key variant is worse. A verifier that
accepts **both** a symmetric (HS256) and an asymmetric (RS256/ES256) algorithm **and
reads the algorithm from the token's own `alg` header** is forgeable: an attacker
sets `alg: HS256` and signs with the RSA/EC **public** key — published, not secret —
as the HMAC key; a naive `verify(token, key)` then uses that public key as the HMAC
secret and accepts the forgery. "The signature verifies" is not enough when the
attacker chooses the algorithm — a public key is not a secret and must never serve as
a MAC key. Fix: pin an **algorithm allow-list per verification context** and never derive the algorithm from the token. ASVS requires that "only algorithms on an allowlist can be used to create and verify self-contained tokens, for a given context" and that the allow-list "must not include the 'None' algorithm"; where it must support "both symmetric and asymmetric" algorithms, "additional controls will be needed to prevent key confusion" (OWASP ASVS v5.0.0-9.1.2, L1). The OWASP JWT Cheat Sheet is blunter: "…hardcode the accepted algorithms and do not mix public-key digital signatures algorithms and MAC algorithms."

**Refresh tokens.** Rotate on every use, invalidate the predecessor, and
implement **reuse detection**: presentation of an already-rotated token means the
chain is compromised → revoke the whole family/session and force
re-authentication. Confirm rotation is server-enforced (a stored family/lineage
id), that refresh tokens are single-audience and revocable at logout and on
password/MFA change, and that they are not readable by client JS.

**Session termination & timeout are server-side controls, not a cookie `Max-Age`.**
Require two distinct, both-enforced controls — an **inactivity (idle) timeout** and an
**absolute maximum session lifetime** — both server-side and driven by documented risk
decisions (ASVS v5.0.0-7.3.1 / -7.3.2, L2), not a client-trusted cookie `Max-Age`/`Expires`
(which the client can ignore). Typical ranges (OWASP Session Management Cheat Sheet): idle
"2-5 minutes for high-value applications and 15-30 minutes for low risk applications"; an
absolute cap "between 4 and 8 hours" for a full workday. **Logout must actually terminate the
session server-side** — a stateless self-contained JWT cannot be "deleted" (clearing the client
cookie is not revocation), so ASVS v5.0.0-7.4.1 (L1) requires "a solution such as maintaining a
list of terminated tokens, disallowing tokens produced before a per-user date and time or
rotating a per-user signing key." A token still accepted after logout, or a session with no
absolute cap, is the finding. (Accessibility: a short idle timeout still needs the warn-and-extend
affordance in `frontend-a11y.md` before it fires.)

**Fix**: rate-limit and lock out; rotate session on auth state change; short
token lifetimes + server-side revocation; verify JWT signature/alg/exp/aud; MFA
where warranted.

**🚩 CSRF guard mistaken for authentication.** An `Origin` / `Referer` /
`Sec-Fetch-Site` check is CSRF defense only — (1) any non-browser client sets
those headers freely, and (2) browsers omit `Origin` on many same-site **GET**
navigations, so the check is simultaneously bypassable and leaky. If it is the
*only* gate on a sensitive/paid/mutating action, that action is effectively
unauthenticated: CWE-352 (CSRF) is not a substitute for CWE-306 (Missing
Authentication) / CWE-862 (Missing Authorization). Confirm a real identity check
exists.

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
own vuln — see domain M / `observability.md`)? Are logs tamper-resistant and actually
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

## Deterministic corroboration (cross-cutting) — an LLM claim rides on a proof it cannot generate

Running the project's wired scanners is already Phase 1 (`method.md`), and re-verifying a
finding against source and tests is already the fan-out discipline (`parallel-audit.md` §4–5).
This adds the security-specific rule: for a class of finding a **deterministic engine can
*prove***, corroborate the LLM's claim against that proof or mark it `unverified` — the review
layers judgment on a proof no LLM reliably produces, it does not assert the proof.

- **Code-level SAST / quality engines** to run and read (tool-agnostic — the project's own
  wired one): **Semgrep** / OpenGrep (pattern + data-flow, autofix), **CodeQL** / GitHub code
  scanning (a query engine returning the source→sink path), **SonarQube** (quality gate +
  security *hotspots* — a hotspot is a triage signal, not a confirmed defect), **Snyk** (Code +
  Open Source), plus the ecosystem linters (`bandit`, `ruff`, `mypy`, `hadolint`).
- **The proof ↔ claim map** (corroborate, don't assert):
  - *"user input reaches this sink"* ↔ a **CodeQL taint / data-flow path** (source→sink); a
    claim with no path is `unverified`, not a finding.
  - *"this secret is real"* ↔ **TruffleHog** logging into the provider (Verified / Unverified /
    Unknown) — Unverified is not "clean" (the `Secrets` rule above still holds: a committed
    secret is compromised).
  - *"this dependency version is vulnerable"* ↔ an **exact version↔CVE match** against
    machine-readable ranges (`osv-scanner` / Trivy / Grype — `dependency-currency-and-upgrades.md`),
    replacing the LLM's error-prone recall of affected ranges.
  - *"you're exposed because you depend on X"* ↔ **reachability** (Semgrep Supply Chain): a dep
    vuln matters only when code matches the vulnerable pattern — importing ≠ executing.
- **Ingestion:** pull deterministic findings through the standard interchange formats —
  **SARIF 2.1.0** (any scanner → code-scanning alerts) and **OSV JSON** (advisory data) — so the
  review reasons over a machine-readable proof, not a screen-scrape.

## API-specific overlay (OWASP API Security Top 10, 2023)

For HTTP/GraphQL/gRPC APIs, walk the 2023 list; API2/API7/API8 reduce to A07/A01
(SSRF)/A02 above. The categories that need API-specific procedure:

**API1 + API5 — BOLA (object level) and BFLA (function level).** Run the
**two-principal matrix** from A01 above; it is the procedure for both. BOLA:
replay A's object-bearing request with B's id/token/tenant per object route.
BFLA: replay a **privileged verb/route** with an ordinary user's token — enumerate
by verb (`GET` allowed, `DELETE` forgotten), by admin path (`/admin/*`,
`/internal/*`), and by nested route (`/orgs/{id}/members/{id}/role`). Expected:
`own → 200`, `other → 403/404`, `under-privileged → 403`. Route-level middleware
does not prove object-level checks; grep for handlers that load by id *before*
authorizing.

**API3 — mass assignment / over-exposure.** Two directions, both required.
Inbound: does the handler bind the request body wholesale (`Object.assign`,
`**body`, `Model(**request.json)`, `update_attributes`, spread into an ORM
`update`)? Require an explicit **allow-list** of bindable fields per endpoint;
deny unknown keys rather than ignoring them, and never let `role`, `owner_id`,
`tenant_id`, `balance`, `verified`, or `created_at` be client-settable. Outbound:
serialize through an explicit DTO/field allow-list — returning the whole model
(or `SELECT *`) leaks internal columns and future ones added later. Test by
adding a privileged field to a legitimate request and re-reading the object.

**API6 — unrestricted access to a *sensitive business flow*.** Distinct from the
rate-limit key/burst check in A06 above: a flow can be **correctly authorized,
individually within the rate limit, and still harm the business at volume** —
scalping limited inventory across many accounts/IPs, hold-then-cancel to force a
price drop, farming a referral/coupon credit. A generic per-IP / per-principal
limiter does not catch it because each request, alone, is legitimate; the signal is
**automation, not volume**. First ask the business question the limiter does not —
OWASP's framing: "identify the business flows that might harm the business if they
are excessively used" (checkout, referral credit, review/vote, waitlist,
price-affecting cancel). Then check for automation-specific controls the limiter
can't provide: device / headless-browser fingerprinting, human detection (CAPTCHA or
behavioral biometrics), and non-human-timing detection — OWASP's own example is to
"analyze the user flow to detect non-human patterns (e.g. the user accessed the 'add
to cart' and 'complete purchase' functions in less than one second)," and ASVS
v5.0.0-2.4.2 (L3) requires "business logic flows require realistic human timing."
Machine-consumed (B2B / partner) APIs are the common blind spot. 🚩 a sensitive flow
protected by the **same** generic per-IP limiter as the rest of the API, with no
automation / timing signal at all.

**API9 — inventory (zombie / legacy / `v1`).** Enumerate the *deployed* surface,
not the documented one: route tables, framework route dumps, gateway/CDN and
load-balancer configs, access logs, OpenAPI vs reality, old hostnames and
`staging.`/`api-old.` records. Flag every route that is live but unversioned,
superseded (`/v1` beside `/v2`), undocumented, or serving a decommissioned
client — old versions usually predate the current authz and rate-limit layers.
Each finding needs an owner and a sunset date or a block at the gateway.

**API10 — unsafe consumption of upstream APIs.** Treat a third-party or internal
upstream response as untrusted input: validate against a schema, bound size and
recursion, enforce a timeout and a circuit breaker, and never follow redirects
into internal ranges (A01 SSRF rules apply to the upstream client too). Do not
render upstream HTML unescaped, pass upstream strings to a shell/SQL sink, or
trust upstream-supplied ids, prices, or authorization decisions.

**GraphQL.** Enforce a **depth limit** and a query-cost/complexity budget
(recursive fragments are an unauthenticated DoS); cap **batching** (array of
operations) and aliased-field repetition, which multiply cost past a per-request
limit; disable **introspection** and the playground/GraphiQL in production;
authorize at the **resolver/field level** — a single gate on the top-level query
lets a nested field walk to data the caller cannot read. Check that errors do not
leak schema internals and that persisted queries, if used, are the only accepted
form.

**gRPC.** Auth travels in **metadata**, not a cookie: verify every service method
validates the credential in an interceptor applied server-wide (a per-method
check is missed on the next method added), that TLS is required, and that
reflection is off in production. Streaming RPCs need per-message authorization
and size/time bounds.

**WebSocket.** Authenticate at the **upgrade** request and re-check on
privileged messages; validate `Origin` on the handshake (browsers do not apply
CORS to WebSockets — this is CSWSH) and bind the socket to the authenticated
principal server-side. Never trust a client-supplied user/room id on subsequent
frames, and apply per-connection rate and message-size limits.

## Going deeper

- **ASVS 5.0.0** — the version recorded as latest stable in the standards index
  (the OWASP project page confirms 5.0.0); use it as the L1/L2/L3 verification
  checklist when you need depth beyond the Top 10, and pick the level that
  matches the app's risk. Citing ASVS as a *reference* is not the same as having
  walked it: only claim ASVS coverage in the report if the review actually
  verified the requirements, and say which level and which chapters.
- **WSTG** — the how-to-test companion for each risk above.
- **CWE Top 25 (2025)** — weakness-level detail; the current top entries are
  XSS (CWE-79), SQL Injection (CWE-89), CSRF (CWE-352), Missing Authorization
  (CWE-862), Out-of-bounds Write (CWE-787), Path Traversal (CWE-22),
  Use-After-Free (CWE-416), Out-of-bounds Read (CWE-125), OS Command Injection
  (CWE-78), and Code Injection (CWE-94).
