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

**Transaction authorization (WYSIWYS) — an orthogonal, *same*-principal control,
not a restatement of segregation of duties above.** Segregation of duties is about
*who* approves — a distinct second principal. Transaction authorization is about
*what* that principal is shown and confirms, even when it's the same person who
initiated the action. For a high-value transaction (wire transfer, payout-
destination change), the OWASP Transaction Authorization Cheat Sheet's **What You
See Is What You Sign** principle requires the confirmation step show and let the
user acknowledge the transaction's own significant data — the actual target
account and amount — not a generic "confirm?": "An authorization method must
permit a user to identify and acknowledge the data that is significant to a given
transaction." The same cheat sheet also requires each transaction be authorized
with credentials **unique to it**, not a reusable session factor: "If applications
only ask for transaction authorization credentials once … the user could authorize
any transaction during the entire session or reuse the same credentials," which
lets a compromised session or sniffed credential authorize an attacker-substituted
transaction the user never saw. A confirmation that re-uses the login-session MFA
code and shows only a generic prompt fails both halves at once — it isn't
transaction content, and it isn't unique/bound to this transaction. Cross-ref
`billing-correctness.md` for the amount/ledger-correctness side of a
money-movement change; this control is the authorization-credential side, not the
arithmetic.
- **🚩** a high-value transaction confirmation showing a generic prompt instead of
  the actual amount/recipient, or accepting the same MFA/session credential
  already used to authenticate the session.

**Cache / CDN is an authorization surface.** Responses derived from identity must
be `Cache-Control: private` / `no-store` (or keyed by principal). Check
framework static vs dynamic decisions for pages that read cookies/headers;
require `Vary` on every identity input (`Cookie`, `Authorization`, custom
auth headers). Sweep **through the CDN as well as origin**; compare anonymous
body vs member body for the same URL. Origin-only anon GET can look clean while
the edge serves a cached member page.

**Cache poisoning — an unkeyed input that shapes the cached body.** The mirror of the leak
above. If an attacker-controllable request component **influences the response body but is not
part of the cache key** — a reflected header (`X-Forwarded-Host`, `X-Forwarded-Scheme`) or a
routing-override header (`X-Original-URL`, which makes the server serve a different page's body
under the requested URL), a param the app echoes, any header the response varies on without a matching
`Vary` — the attacker's value is cached under the normal URL and served to **every** subsequent
visitor, turning a *reflected* XSS / open-redirect / malicious-script-src into a **stored,
mass-distributed** one. Census the **cache key** (what the CDN/edge actually keys on) against
**every input that can change the response** (headers the app reads, not only the path+query);
anything that varies the body must be **stripped/normalized at the edge, or keyed on** (keying
on an attacker-settable header risks cache-key cardinality blowup — prefer strip/normalize), and
never reflect an unkeyed header into a cacheable response. (Distinct from the identity leak above
— that serves one real user's private body to another; this serves an *attacker's* injected body
to everyone — and from connection-level request smuggling in A01.)

**Presigned / signed URLs & uploads.** Presigned URLs: one object, short TTL,
re-issued per request; must die on permission revocation. User uploads: authorize
per object; never rely on unguessable paths; size/type/magic-bytes checks;
no executables in public dirs; SVG/HTML as stored XSS; archive extract =
zip-slip risk (see A05 files block).

**🚩 grep**: `req.params`/`req.body` id → query; ungated routes; `fetch(userUrl)`;
`role === 'admin'` in UI only; shared loaders across API + page with asymmetric
redaction; `Cache-Control: public` on auth'd handlers; a reflected `X-Forwarded-Host`/`X-Forwarded-*` in a cacheable response; `tenant_id` from body;
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
(HSTS, `Content-Security-Policy`, `X-Content-Type-Options`, frame-ancestors,
`Permissions-Policy`, `Cross-Origin-Opener-Policy`/`Cross-Origin-Embedder-Policy`/
`Cross-Origin-Resource-Policy`); cloud storage/buckets world-readable; unnecessary
services/features enabled.

**🚩 grep**: `DEBUG = True`, `NODE_ENV` not enforced to `production`,
`Access-Control-Allow-Origin: *`, `cors({ origin: true, credentials: true })`,
`app.use(errorhandler())` in prod, `.enable('trust proxy')` misused.

**Fix**: harden by default; ship prod config that disables debug, sets headers,
scopes CORS to known origins, and removes sample/default accounts. Track against
CIS Benchmarks for the runtime/platform.

**`Permissions-Policy` and the cross-origin isolation trio extend the same header
census, not a separate concern.** `Permissions-Policy` denies powerful browser
features (camera, microphone, geolocation, payment) by default; the OWASP HTTP
Headers Cheat Sheet frames the goal as letting a site "never allow the camera or
microphone to be activated" even when an injection (XSS) runs.
`Cross-Origin-Opener-Policy` (COOP) and `Cross-Origin-Resource-Policy` (CORP)
close two distinct leaks the OWASP XS-Leaks Cheat Sheet documents (with
`Cross-Origin-Embedder-Policy` (COEP) the third leg of the cross-origin-isolation
trio, per the HTTP Headers sheet): COOP puts a page in its own browsing context group, so a
cross-origin page that **opens it** (a popup, a lured new-tab click) gets back an
inert handle instead of a live `window` reference — closing the frame-counting
family, where the sheet's own example is an attacker opening the target and
reading `win.frames.length` off the handle it gets back. CORP stops another origin
from loading the response at all, closing the `onload`/`onerror` resource-probing
family and doubling, per the **HTTP Headers** cheat sheet, as "a robust defense against attacks like
Spectre." XS-Leaks' own Quick Recommendations list COOP+CORP alongside SameSite
cookies and framing protection to "strengthen the isolation of your application
between other origins" — this file already covers SameSite (A07 § Session cookie
flags) and frame-ancestors/clickjacking (`frontend-a11y.md`); COOP/COEP/CORP is
the missing header from that set, not a claim that these four close every XS-Leak
(the sheet separately names Fetch Metadata/`Sec-Fetch-Site` and per-resource
unpredictable tokens, out of scope here).

**🚩** a cross-origin-embedding-or-embedded surface, or one handling sensitive
device-capability APIs (camera/mic/geolocation/payment), with no
`Permissions-Policy` and no COOP/CORP set.

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
`GITHUB_TOKEN` / `permissions` read-only by default and escalated per job? **But
`permissions:` scopes the *token*, not a *secret*.** A repo- or org-level secret
(`${{ secrets.PROD_DEPLOY_KEY }}`) has no per-job boundary — *any* job running in
the repository context can reference it, including a lint/test job that never
deploys — so a production deploy credential sits in reach of jobs that do not
need it (OWASP CI/CD **CICD-SEC-05**, Insufficient PBAC: malicious code in a
pipeline node "can access secrets, access the underlying host and connect to any
of the systems the pipeline in question has access to"). Fix per **CICD-SEC-06**
(Insufficient Credential Hygiene): "Ensure secrets that are used in CI/CD systems
are scoped in a manner that allows each pipeline and step to have access to only
the secrets it requires" — bind prod credentials to a protected deployment
`environment:`, whose secrets only a job that declares that environment can read
and whose deploy is gated by an approval / wait / branch restriction, instead of
leaving them readable workflow- or repo-wide. A plain fork `pull_request` job
already runs *without* repo secrets (GitHub withholds them — see
`infra-iac-containers.md`); the trigger that hands a secrets-bearing context to
untrusted PR code is `pull_request_target` (above), so keep prod credentials out
of any job reachable that way. Distinct axes: self-hosted-runner
isolation/ephemerality (`infra-iac-containers.md`) bounds *where* a job runs and
what residue it harvests; the committed-secret / rotation checks under
**Secrets** below are secret-at-rest — this bounds which jobs may *read* a live
secret. **Are
the files a privileged/protected pipeline *executes* under the same enforced review
gate as the workflow file** — a `make` target, `scripts/*.sh`, a `Dockerfile`,
`conftest.py`, `.pre-commit-config.yaml`, a `package.json` script? Protecting only
`.github/workflows/` stops an edit to the pipeline *config*, but the privileged job
still runs whatever those *referenced* files contain, so an attacker edits the
referenced file (not the protected workflow) and the pipeline runs their code with
its privileges (OWASP CI/CD **CICD-SEC-04**, *Indirect* PPE — distinct from the
script-injection and `pull_request_target` checkout above, which poison the config
or its inputs directly). The trust boundary is the transitive closure of what the
pipeline executes, not the workflow YAML alone — and CODEOWNERS on those paths binds
a merge only when branch protection enforces it (`docs-and-dx.md`).
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
**But attestation at promotion doesn't cover the handoffs *inside* the pipeline.**
When a later job consumes an earlier job's `upload-artifact`/`download-artifact`
output, or restores a build **cache**, with no integrity check between stages, a
poisoned cache or a tampered inter-job artifact flows downstream even though the
*final* artifact is attested — the tampering entered *before* the thing that gets
signed was built, so the pipeline faithfully attests poisoned bytes (OWASP CI/CD
**CICD-SEC-09**, distinct from the final-artifact attestation above). Validate
integrity at *each* stage handoff — pin/verify inter-job artifacts and cache keys so
a restored input is checked before a downstream stage consumes it, not only at the
promotion step.

**🚩 grep**: `"postinstall"` in `package.json`, `uses: actions/*@main`,
unpinned base images (`FROM node:latest`), `curl … | bash` in build steps,
dependencies added in a diff without a lockfile update, `pull_request_target`
paired with a checkout of the PR head, `${{ github.event.` inside a `run:`
block, a workflow with no `permissions:` block or `permissions: write-all`, an
install path whose only integrity check is a checksum served from the same host
as the artifact. A privileged workflow whose `run:` invokes `make`,
`bash scripts/…`, `docker build`, `pre-commit`, or a `package.json` script whose
target file is **not** under the same review/CODEOWNERS rule as `.github/workflows/`.
A job that `download-artifact`s a prior job's output or restores `actions/cache` and
consumes it with no digest/attestation check before the next stage. A job that
references `${{ secrets.` with no `environment:` scoping it — especially a
prod/deploy credential, or a `pull_request_target` job that runs with repo/org
secrets available while exposed to untrusted PR code.

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
authenticity); put every file the privileged pipeline *executes* — build scripts,
`Makefile`, `Dockerfile`, hook/linter configs, `package.json` scripts — under the
**same** enforced review/CODEOWNERS gate as the workflow file; and verify the
integrity of inter-job artifacts and restored caches at **each** stage handoff
(pin/attest them, check a digest before a downstream job consumes them), not only
when the final artifact is signed at promotion (OWASP CI/CD **CICD-SEC-04** /
**CICD-SEC-09**). Scope secrets to the job that needs them — bind prod
credentials to a protected deployment `environment:` (its secrets readable only
by a job that declares it, deploy gated by an approval / wait / branch
restriction), not a repo/org-wide secret every job can read, and keep them out of
`pull_request_target` or other jobs exposed to untrusted PR code (OWASP CI/CD
**CICD-SEC-05** / **CICD-SEC-06**). **Severity keys on reachability** — a weak install verification on
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

**Nonce/IV reuse is a forgery bug for AEAD ciphers, not merely a leak —
"unique" and "unpredictable" are different bars.** The "unique per message"
rule above doesn't say what breaks, or how much, when it's violated. For
**AES-GCM** (or any AEAD built on GHASH), NIST's requirement is exact: "The
probability that the authenticated encryption function ever will be invoked
with the same IV and the same key on two (or more) distinct sets of input
data shall be no greater than 2^-32" (NIST SP 800-38D §8). Break it and, per
Appendix A, "it is likely that an adversary will be able to determine the
hash subkey from the resulting ciphertexts. The adversary then could easily
construct a ciphertext forgery... the authentication assurance essentially is
lost. Worse, the loss of authentication means that GCM inherits the
problematic malleability of its Counter mode ciphertext... the adversary
essentially could control the plaintext output of the authenticated
decryption function." That is CWE-323 ("Reusing a Nonce, Key Pair in
Encryption") — pin severity with the exposure-boundary discriminator (A01)
rather than a flat default — and it is current, not historical: CVE-2024-36289
(a social-networking app reusing a nonce/key pair, letting an MITM manipulate
direct messages) and CVE-2024-21530 (a Rust package reusing one on object
clone, resetting the RNG).

CBC/CFB's bar is stricter than "unique": NIST SP 800-38A requires the IVs "be
unpredictable. In particular, for any given plaintext, it must not be
possible to predict the IV that will be associated to the plaintext in
advance of the generation of the IV" — a sequential, attacker-visible counter
IV can be unique and still fail this. CTR/OFB reuse instead compromises the
confidentiality of the two messages wherever they overlap — the keystream
repeats from the first block, so every aligned block position leaks (a
two-time-pad break), not merely an occasional block (SP 800-38A) — on top of
Counter-mode's existing bit-flip malleability.

Detect at the call site, not the algorithm name: is the nonce/IV drawn fresh
from a CSPRNG (or SP 800-38A's own Appendix B/C construction) immediately
before **every** encryption call, or is it a module-level constant, a config
value, a counter with no durable high-water mark across restarts, or a value
that survives an object clone? **🚩 grep**: a hard-coded/all-zero IV
constant; an IV assigned once outside the encrypt call; a counter reset on
process start; `clone`/`copy` on a struct carrying cipher state.

**A hand-rolled equality check on a secret-derived value is a timing side
channel — generalize it across every raw-secret compare, not only the
webhook and admit-gate instances already named.** Comparing an
HMAC/webhook signature, session/CSRF token, API key, or OTP/reset code
against caller input with a short-circuiting equality (`==`, `.equals()`,
`strcmp`, `Arrays.equals`) leaks the position of the first mismatched byte
through response timing — CWE-208, "Observable Timing Discrepancy": "Two
separate operations in a product require different amounts of time to
complete, in a way that is observable to an actor and reveals
security-relevant information about the state of the product, such as
whether a particular operation was successful or not." Not theoretical:
CVE-2019-10071 is a Java framework comparing HMAC signatures with
`String.equals()` instead of a constant-time algorithm. The webhook-signature
check (`api-contracts.md` § Webhooks — consuming) and the admit-gate-entropy
aside in A07 below both name this same primitive — a shared secret, API key,
webhook-signing key, or admin token compared against caller input — so this
generalizes it to any raw secret-byte compare, anywhere. (Distinct from
account-enumeration in A07 below, which equalizes response time across a
*whole* signup/login/reset request path to hide existence — a coarser,
whole-endpoint timing control, not a byte-by-byte secret compare. bcrypt/argon2
`verify()` calls are already constant-time internally — the gap here is a
hand-rolled compare elsewhere: session tokens, CSRF tokens, OTP/2FA, reset
codes, API keys.)

Two vendor gotchas belong in the fix. Node's `crypto.timingSafeEqual`
requires equal-length inputs — "a and b must both be Buffers, TypedArrays, or
DataViews, and they must have the same byte length. An error is thrown if a
and b have different byte lengths" — so calling it on a raw, variable-length,
attacker-controlled candidate either throws, or, if pre-checked with
`a.length === b.length` to dodge the throw, reintroduces a smaller
length-timing leak; compare fixed-length values instead (HMAC-then-compare,
or hash both sides first). Java's safe primitive is the **static**
`MessageDigest.isEqual(byte[], byte[])`, not `.equals()`/`Arrays.equals()`
(CVE-2019-10071's exact mistake) — per the Javadoc's Implementation Note:
"The calculation time depends only on the length of digesta. It does not
depend on the length of digestb or the contents of digesta and digestb."

**🚩 grep**: `==`/`.equals()`/`Arrays.equals`/`strcmp` comparing a
`signature`/`hmac`/`token`/`csrf`/`otp`/`code`/`apiKey`-named variable against
a request-derived value, with no `timingSafeEqual`/`hmac.compare_digest`/
`MessageDigest.isEqual`/`subtle.ConstantTimeCompare` (Go) in the same function.

**The algorithm name is not the control — the cost parameters are, and the
floor is a moving target.** The check above ("hashed with a memory-hard
KDF... never fast hashes") verifies *which function* runs, not *how
expensively*: `argon2.hash(pw, { memoryCost: 512, timeCost: 1 })` and
`bcrypt.hash(pw, 4)` both call a compliant KDF and pass a name-only check
while sitting far below any current floor — commonly a cost turned down "for
fast tests" that ships to prod unnoticed. Read the call-site arguments
(memory/time/parallelism for Argon2id; work factor for bcrypt; N/r/p for
scrypt) against the **current** OWASP Password Storage Cheat Sheet floor —
quoted for today's date only, not as permanent doctrine: "Use Argon2id with a
minimum configuration of 19 MiB of memory, an iteration count of 2, and 1
degree of parallelism. If Argon2id is not available, use scrypt with a
minimum CPU/memory cost parameter of (2^17)... For legacy systems using
bcrypt, use a work factor of 10 or more and with a password limit of 72
bytes" — bcrypt specifically only "for password storage in legacy systems
where Argon2 and scrypt are not available." The floor rises as hardware gets
cheaper — re-check the cheat sheet at review time; do not hard-pin today's
numbers as a permanent gate.

**🚩 grep**: a KDF call whose numeric argument sits below the current floor
cited above (today, that means: a single-digit bcrypt work factor, an Argon2
`memoryCost`/`timeCost` far under the cited figures, a `scrypt` cost under
`2^17`) — or no visible parameter at all, meaning the library default is in
effect and must be checked against the same floor.

**Envelope encryption needs two independent keys, not one key filling both
roles.** An application doing its own field/record-level key wrapping — a
Data Encryption Key (DEK) that encrypts the data, wrapped by a Key Encryption
Key (KEK) — must keep the two separate. OWASP's Cryptographic Storage Cheat
Sheet, § Encrypting Stored Keys: "At least two separate keys are required for
this: The Data Encryption Key (DEK) is used to encrypt the data. The Key
Encryption Key (KEK) is used to encrypt the DEK. For this to be effective, the
KEK must be stored separately from the DEK," and "The KEK should also be at
least as strong as the DEK." Reusing one key
as both collapses the boundary the two-key design exists to provide — a KEK
compromise then directly exposes every DEK it wrapped, not only the data
behind the one key an attacker actually reached. Scope: hand-rolled/manual
key wrapping only — pure-KMS delegation enforces this internally and is out
of scope.

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

**Server-side template injection (SSTI, CWE-1336) — user input reaching the template *engine*, not the template's *data*.** Distinct from XSS: XSS is untrusted **data** rendered into HTML output (fixed by contextual output escaping); SSTI is untrusted input that becomes part of the **template source the engine compiles and evaluates**, so escaping the output does nothing. In a server-side engine (Jinja2, Twig, Freemarker, Velocity, ERB, Handlebars / Nunjucks with helpers) it is usually a path to **RCE**, not just markup injection: the payload traverses the language's object graph to reach a callable (Jinja2 `{{ ''.__class__.__mro__[1].__subclasses__() … }}`, FreeMarker `<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}`), and an engine "sandbox" is a **mitigation, not a boundary** (documented escapes exist). 🚩 the input is passed **as the template** rather than **as context**: `render_template_string(user_input)`, `Template(user_input).render(...)`, `env.from_string(request.…)`, a template string built by concatenation, or any "user-customizable template / email-subject / label" feature. **Fix**: never compile a template from user input — render a **statically-defined** template and pass user values only as **bound context variables** (data cannot introduce template syntax); if user-authored templates are a genuine product feature, use a **logic-less** engine (Mustache) or a locked-down allow-listed sandbox, and treat that path as an **RCE-grade trust boundary**.

**An idempotency "already-formatted, skip it" short-circuit that bypasses the sanitizer, not just the transform (XSS).** A text-to-markup helper — an autolinker that turns bare URLs into `<a>` tags, a markdown renderer, a mention/emoji expander — is frequently made safe to run twice with a guard: *if the input already contains links / looks already-processed, return it unchanged.* The defect is that the **scheme check and escaping live only on the branch that *builds* the markup**, so the "already-formatted" branch returns the pre-existing value **with no revalidation** — the tool's href-safety guarantee holds only where it constructed the href itself. Whoever controls the free text the tool runs on (a title, a generated changelog line, a description pasted in from elsewhere) then controls the value on the skip branch: they pair a token that *looks already-processed* — a stray `<a` tag is enough to trip the guard — with the real payload (a raw `<img onerror=…>` or `<script>`, or an anchor whose own href is a `javascript:`/`data:` scheme), so the whole string passes the guard and reaches the HTML sink unchecked → stored/reflected XSS. It survives review because the skip is **deliberate and unit-tested** ("running twice does not double-wrap"): that test pins the exact branch that is the hole, and a reviewer who reads only the build path sees a correct scheme check and signs off. 🚩 an early-return / fast-path / cache-hit keyed on *"already done"* that returns a value bound for an HTML/URL/`src` sink where the scheme-allowlist or escape step sits **inside the transform it just skipped**. **Fix**: scope the idempotency guard to the *transform only* — the skip branch must **re-validate the pre-existing value** (confirm the href scheme against the allowlist; don't trust it), because sanitizing is a *different operation* from the link-transform and must not be made conditional on it. Independently, the render-time sink needs **its own** scheme allowlist no matter what any producer promises — sanitize-at-the-sink holds for an in-process generator, not only a network upstream — and a codebase with more than one text-to-link path wants **one shared, audited** linker, not a second bespoke one that skipped the audit. Trace every URL/`href`/`src` sink back to *every* producer and ask whether any path — the idempotency/skip branch first — reaches the sink without passing the scheme allowlist.

**Files, archives & parsers.** Uploads: enforce a size cap **and** an allow-list
of types validated by **magic bytes**, not the client-supplied `Content-Type` or
extension. Store outside any directory the server will execute or serve as code;
no executables in public dirs. Treat SVG and HTML as **stored XSS** — serve from
a separate origin, or `Content-Disposition: attachment` +
`X-Content-Type-Options: nosniff`, never inline on the app origin. Archive
extraction: reject entries whose resolved path escapes the target dir
(**zip-slip**, CWE-22), plus symlinks, absolute paths, and decompression bombs
(cap entry count and uncompressed size). **Serving or downloading a file by a user-supplied
path is the same CWE-22 on the read side:** a handler that opens `BASE_DIR + name`,
`send_file(request.args['path'])`, or `res.sendFile(req.query.path)` lets `../` — or an
absolute path or an escaping symlink — walk out of the base and read arbitrary files
(`/etc/passwd`, secrets, another tenant's data). **Resolve to a real, canonical path
(`realpath`, which follows symlinks — a lexical `path.resolve` alone does not) and verify it is a
true subpath of the base** — compare against the base **plus its trailing separator**, or use a
real is-subpath check, since a bare string-prefix on `/base` also matches `/base-evil`;
canonicalize *before* the check, reject absolute overrides, and reject an escaping symlink; a
bare `../` denylist is bypassable
(`%2e%2e`, `....//`). Grep `sendFile`/`send_file`/`send_from_directory`/`open(<dir> + <input>)`
with no post-resolve base-prefix check. XML parsers: **disable external
entities and DTDs** (XXE, CWE-611) — `defusedxml` in Python,
`setFeature(FEATURE_SECURE_PROCESSING, true)` / disallow-doctype-decl in Java,
`noent: False` for lxml. Same posture for any format with an include/reference
mechanism (XSLT, SVG `<use>`, YAML anchors, spreadsheet formulas).

**CSV / spreadsheet formula injection (export direction, CWE-1236).** The upload
checks above guard *inbound* files (the include/reference line even names inbound
spreadsheet formulas, for XXE); a data **export** — CSV, or an XLS/XLSX/ODS generated
from stored rows — is the *outbound* mirror and needs its own check. Any stored,
user-controlled string (a display name, a coupon code, a free-text note) whose value
**starts with** `=`, `+`, `-`, `@`, a tab, or a NUL is parsed as a **formula** by the
spreadsheet app that opens the export, not as text — an exfiltration / RCE-adjacent chain (`=WEBSERVICE(...)`, `=cmd|...`) that runs when a human opens the file — a plain formula evaluates on open; `=WEBSERVICE`/DDE `=cmd|` payloads typically prompt a security warning first — with **no injection into your app** required. HTML-escaping the same field for the web
UI does **nothing** here — a different output context. Fix at **export** time: prefix
a single quote before any such leading character. ASVS v5.0.0-1.2.10 (L3) names them (a non-exhaustive list — the standard says "including") — "special characters (including '=', '+', '-', '@', '\t' (tab), and '\0'
(null character)) must be escaped with a single quote if they appear as the first
character in a field value" — and also requires RFC 4180 escaping for the CSV itself.
🚩 a CSV / XLSX export path (`csv.writer`, `fast-csv`, SheetJS / `xlsx` write, a manual
comma-join) writing a stored field with no leading-character check.

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
  (IP alone is bypassable; key on principal **and** target resource) — **and how
  cheaply that key is minted**: a self-service or unauthenticated **session token,
  device id, or API key** an attacker rotates for free is no better than IP, because
  re-minting resets the counter (the *rotating-key-vs-stable-identity* confusion).
  Key on a **scarce, verified** identity (a verified account, a payment instrument, a
  credential that itself costs / is rate-limited to create), or rate-limit the
  **minting** path itself. Then check whether
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

**A static secret used as an *admit* gate needs an enforced length/entropy floor at
the point of use — a property separate from constant-time compare.** A shared secret,
API key, webhook-signing key, or admin token compared against a caller-supplied value
gates **admission**, so a short or low-entropy secret is **brute-forceable** however
the comparison is written — constant-time compare closes a timing side-channel, it
does not make a 6-character secret strong. Enforce a minimum length **and** entropy
**where the secret is used** (reject a too-short / low-entropy value at load and fail
closed), not only where it is generated: a strong generator does not stop a hand-set
`changeme` in one deployment's env. **Admit-direction weakness outranks
exclude-direction** (a weak admit secret grants access; a weak exclude secret only
over-blocks). Detect by grepping for the **floor itself** (a length/entropy check at
the compare site), not the secret's name — the guard was never written, so the
secret's name won't lead you to the gap.

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

**Short-lived approval/action bearer tokens need single-use enforcement, not
just signature + expiry (CWE-294 Authentication Bypass by Capture-replay).** A
token minted after a human approval step and handed to a machine caller for one
narrow write (`Authorization: Bearer <token>`, HMAC-signed, carrying an owner id
and `exp`) is commonly verified by checking the signature and `exp` only — that
proves the token **authentic** and **fresh**, not **single-use**. Inside its own
validity window it stays replayable: if it leaks while still valid (an
access/error log, an APM/tracing breadcrumb that records request headers, a
shared debugging session, a logging proxy), nothing stops it being resubmitted
to re-trigger the same approved write, attributed to the original approving
human, with no signal it fired more than once. A short expiry is a
**mitigation, not a fix** — it narrows the window a leaked token is dangerous
in; it doesn't close it. OWASP's JWT Cheat Sheet (Replay Protection) lists
several mitigations without ranking them — short expiration among them, alongside
a denylist that "can typically be implemented based on the jti and iss claims",
"Freshness and replay protection…by using a nonce bound to the session in the
JWT claims" (the approach OpenID Connect uses), and a sender-constrained /
proof-of-possession token (DPoP or a TLS-bound JWT). Of those, the latter three
*close* the window rather than only narrowing it: a denylist or a session-bound
nonce makes a captured token single-use, and sender-binding ties it to its
caller so a copy replayed from elsewhere is rejected.
**Fix**: mint every one-shot approval token with a unique `jti`; record
consumed ids in a store keyed by that id with a TTL at least as long as the
token's own max lifetime, and reject a token whose id is already recorded. The
record-and-reject must be a **single atomic** step — a unique-constraint insert
or a conditional/compare-and-set write — because a read-then-insert is itself a
TOCTOU: two concurrent replays of the same token both pass a naive "not yet
recorded" check before either writes (`concurrency-shared-state.md` § DB / store
TOCTOU). Fail closed if that store is unreachable rather than silently allowing
an unverifiable reuse. Regression test: mint one token, consume it once
successfully against the real endpoint, replay the identical still-unexpired
token and assert the second call is refused — and fire two replays
*concurrently* to confirm the store rejects the loser rather than admitting both.
Distinct from four adjacent controls: an **idempotency key**
(`concurrency-shared-state.md` § DB / store TOCTOU; `api-contracts.md`), which
dedups a *legitimate* retry from the same caller so it isn't applied twice, not a
captured token replayed by someone else; **inbound-webhook replay protection**
(`api-contracts.md` § Webhooks — consuming (inbound)), which authenticates a
*provider's* redelivery of an already-signed message, not a self-minted
credential replayed by whoever captured it; **refresh-token reuse detection**
(the rotated-refresh-token bullet above), which detects the second use of a
long-lived *rotating session credential* and revokes the whole token family,
where this is a one-shot action token with no chain, refused call-by-call (same
"record an id, reject its reuse" primitive, different lifecycle and blast
radius); and **CSRF** (below), which forges a request from a victim's ambient
session with no token in hand at all — here the token is real and correctly
issued, it just outlives its intended single use.

**🚩** a bearer-token verifier that checks signature and `exp`/`aud` only — no
`jti`/consumed-id lookup, no session-bound nonce, no sender-binding — on a
route that performs a state-changing or privileged action; especially telling
where a *sibling* token format in the same codebase (a rotated refresh token's
reuse detection, above, or another higher-privilege bearer credential) already
carries a `jti`/token-id for exactly this purpose and this one doesn't.

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

**Passkey / WebAuthn credential-layer checks — the block above is about session *tokens*; this
is the *credential*.** WebAuthn/passkeys are the platform-default sign-in and the credential NIST
treats as phishing-resistant when properly configured (its verifier-name binding is exactly rules
1–2 below), so a project shipping "passkey login" earns a
credential-layer pass, not just a session-token one:
- **RP ID pinned server-side** to the expected origin, never derived from a client-supplied
  `Host`/`Origin` header. A credential is *scoped to* its Relying Party ID — "a valid domain
  string identifying the WebAuthn Relying Party" (W3C WebAuthn L3) — so an attacker-influenced RP
  ID lets a credential validate for the wrong origin; verify `origin` and `rpIdHash` against a
  fixed expected value on every assertion.
- **Signature counter checked for clone detection.** Its "purpose is to aid Relying Parties in
  detecting cloned authenticators" (W3C WebAuthn L3): a new `signCount` **≤** the stored value is
  a possible-clone/replay signal to surface, never silently ignore. (A counter that is always
  `0`/absent is legitimate on some authenticators — flag a *regression*, not its absence.)
- **No silent downgrade to a weaker factor.** A WebAuthn failure that quietly falls back to a
  password or SMS/TOTP defeats the phishing resistance the flow advertises — NIST SP 800-63-4
  requires AAL2 to **offer at least one phishing-resistant option** and AAL3 a phishing-resistant
  authenticator with a **non-exportable** key. The silent fallback path is the finding.
- **Attestation verified only where the threat model needs authenticator provenance**
  (regulated/high-assurance tiers); most consumer flows correctly skip it — don't over-flag its
  absence. Syncable ("multi-device") passkeys have exportable keys, so NIST bars them at AAL3 —
  check the assurance tier before requiring *or* forbidding sync.

**Push-based MFA needs challenge-response, not blind-approve — and OTP is a secret
with its own lifecycle discipline.** A bare accept/deny push, sent repeatedly and
often paired with social engineering, is push-bombing (MFA fatigue): the attacker
relies on the victim eventually tapping approve out of habit or annoyance. The
OWASP Multifactor Authentication Cheat Sheet's mitigations: require
challenge-response push authentication (for example, number matching) so approval
can't be blind, rate-limit or cap push notifications so repeated prompting isn't
possible in the first place, and monitor for multiple pushes in a short window as
an anomaly signal. Where the factor is an OTP (SMS, email, or a TOTP-adjacent
one-time code), the same sheet sets a lifecycle floor the implementation SHOULD
meet: enforce a short TTL, ensure single use, apply strict attempt limits,
invalidate on successful verification — and SHOULD NOT log the OTP value. This is
distinct from the constant-time compare OTP verification already needs (A04,
above) and from the per-operation send-cost throttle on OTP dispatch
(`API-specific overlay` § API4, below): those guard the compare operation and the
send volume; this bounds the code's own lifecycle and exposure. Cross-ref the
one-shot approval-token `jti`/single-use primitive above — same record-and-reject
discipline, applied to a human-facing OTP instead of a machine-bearer token.

**🚩** a push-MFA flow with a plain accept/deny and no rate cap; an OTP written to
an access/debug log, accepted more than once, or carrying no expiry.

**Password policy follows current NIST, not 2017-era habits.** Flagging the *absence* of forced
periodic rotation or character-composition rules is following **outdated** guidance — NIST SP
800-63-4 reverses both: "Verifiers and CSPs SHALL NOT impose other composition rules (e.g.,
requiring mixtures of different character types)" and "SHALL NOT require subscribers to change
passwords periodically" (but "SHALL force a change if there is evidence that the authenticator has
been compromised"). Screen new passwords against a known-breached-credential list and set a length
floor instead; a mandated 90-day rotation or a complexity regex is itself the finding, not its
absence.

**🚩 CSRF guard mistaken for authentication.** An `Origin` / `Referer` /
`Sec-Fetch-Site` check is CSRF defense only — (1) any non-browser client sets
those headers freely, and (2) browsers omit `Origin` on many same-site **GET**
navigations, so the check is simultaneously bypassable and leaky. If it is the
*only* gate on a sensitive/paid/mutating action, that action is effectively
unauthenticated: CWE-352 (CSRF) is not a substitute for CWE-306 (Missing
Authentication) / CWE-862 (Missing Authorization). Confirm a real identity check
exists.

**🚩 A CSRF guard on one route is not a guard on the class.** When a CSRF token /
double-submit / `Origin` check exists, **grep every cookie-authenticated *mutating*
route** (`POST`/`PUT`/`PATCH`/`DELETE`) and confirm the guard is wired into **all**
of them — a guard bolted onto the single route an incident exposed leaves its
siblings open, the same copy-idiom-scoped-to-one-callsite miss the review scopes to
its full instance set (Phase 4). Second, **verify the shared body parser requires
`Content-Type: application/json`** (and rejects a mismatched type) *before* it
parses: a parser that also accepts `text/plain` / `application/x-www-form-urlencoded`
/ `multipart/form-data` is reachable by the classic **HTML-form-to-JSON CSRF** — a
cross-site `<form>` can send those content-types with **no CORS preflight**, so a
"we only accept JSON, so we're safe from forms" assumption is false unless the
parser actually enforces it. Census: every mutating route × {guard present?, parser
content-type-gated?}.

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

- **Anything with an expiry needs an inventory, an ahead-of-time alert, and rotation before
  it lapses — an unmonitored credential is a scheduled outage.** TLS certificates,
  code-/JWT-signing keys, API tokens, OAuth client secrets, DB passwords, cloud access keys,
  and domains all expire; when one lapses in production the failure is total and
  time-triggered (the classic "the cert expired at midnight and took everything down"),
  precisely because nothing was watching the clock. Distinct from rotating a *leaked* secret
  (above) and from validating a *request* token's `exp` (A07): this is the operational
  **lifecycle**. Check: (1) an **inventory** of every expiring credential/cert with its
  expiry date and an owner; (2) an **alert with lead time** (days/weeks ahead, not on the
  outage — a synthetic/uptime check catches the cert, an expiry-scan the rest); (3)
  **automated renewal/rotation ahead of expiry** (ACME / cert-manager for TLS; a scheduled
  rotation job for secrets/keys with an **overlap window** so old and new are both valid
  during cutover), not a manual calendar reminder. 🚩 a long-lived cert/secret/token with no
  renewal automation and no expiry monitor — a silent time-bomb. (Reliability consequence →
  `reliability-error-handling.md`; alert wiring → `observability.md`; the owner-facing
  inventory/reminder template lives in the `agentic-delivery` overlay's
  `incident-response.md` — here it is the review-time check.)

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

**API4 — unrestricted resource consumption, the *spend* axis.** The GraphQL
batching/depth limits below and the container memory/CPU caps
(`infra-iac-containers.md`) cover *compute* exhaustion; API4 also names a distinct failure mode neither catches: an individually-legitimate request — authenticated, or a valid pre-auth flow such as password reset — that triggers a **metered, paid downstream call** — an SMS/OTP send, an LLM completion,
cloud egress, a per-lookup data-provider API — with **no cap on how many times, or
how fast, a caller can trigger it**. Availability is not the damage here; the **bill** is (OWASP’s own scenario: a forgot-password SMS flow scripted to fire tens of thousands of times, running up thousands of dollars in minutes). Per paid third-party integration
reachable from a request, ask: is there a **spend ceiling at the provider**, or
failing that a **billing alert**? — "Configure spending limits for all service
providers/API integrations. When setting spending limits is not possible, billing
alerts should be configured instead" (OWASP API4:2023). A per-**operation** throttle
(OTP sends, password-recovery specifically) is the application-side complement; a
generic per-IP/per-account limiter does not bound a **low-and-slow** spend spread
across many legitimate accounts (CWE-770, Allocation of Resources Without Limits or Throttling). Prefer a **graduated** response — alert plus the per-operation throttle before a hard cutoff — since a hard provider spend-cap trips legitimate OTP/reset sends too, converting a cost problem into an availability outage. (In-code spend-governance bugs — a fail-open ledger, a non-atomic reservation — are in `performance-db-cost.md`.) 🚩 any server-initiated call to a metered external API / SMS / LLM
provider with no per-caller operation throttle and no spend ceiling or billing alert
configured.

**API4 — unrestricted resource consumption, the *memory* axis.** Distinct from
the spend axis above: the damage here is exhausted server memory, not a
runaway bill, and the trigger is the request's own body, not a downstream call
it makes. OWASP's own vulnerability checklist names "Maximum allocable memory"
and "Maximum upload file size" among the limits an API needs, and its
prevention list requires you to "Define and enforce a maximum size of data on
all incoming parameters and payloads, such as maximum length for strings,
maximum number of elements in arrays, and maximum upload file size (regardless
of whether it is stored locally or in cloud storage)" (OWASP API4:2023) — but a
cap that exists is not the same as a cap **enforced in time**. A raw
(non-JSON) upload route commonly checks its byte-size cap only *after* the
framework has already fully buffered the whole body into memory: the real
check runs deep inside the storage call, downstream of an unconditional
`request.arrayBuffer()`/`.blob()`/`.text()` (or any framework's equivalent
"read the whole body" convenience call) that has no bound of its own. By the
time the cap rejects the request, the allocation it exists to prevent has
already happened — a handful of concurrent oversized uploads exhausts the
process for every tenant sharing it, not just the caller who sent them. Two
gaps compound: a pre-check against the declared `Content-Length` is a no-op
for a chunked or omitted header (a `Number(header ?? '')`-style coercion of a
missing header commonly evaluates to a value that passes the check regardless
of the real body size), and the framework's whole-body read has no ceiling of
its own even when the declared length was honest. Bound the **read**, not the
result of the read: reject immediately on a declared `Content-Length` already
over the cap, *and* enforce a hard ceiling via a streaming read — sum bytes
chunk by chunk, cancel/abort the instant the running total crosses the cap —
so worst-case memory use is bounded regardless of what the client declares or
omits. 🚩 grep raw-body reads (`.arrayBuffer()`, `.blob()`, `.formData()` where
it buffers, a no-`limit` `body-parser`) in any handler and trace whether the
app's size check runs before that call (safe) or only after (vulnerable — the
memory is already committed). Test with a chunked, `Content-Length`-omitting
oversized body and assert both the rejection and that the handler never
buffers past the cap. Distinct from the upload allow-list/magic-bytes checks
above (`Files, archives & parsers`) — those gate *type*, not the order size is
enforced relative to buffering — and from `language-stack-redflags.md`'s
CWE-789 "declared/untrusted size value" fold: CWE-789 is a size/count/dimension
field read *from inside* an already-received payload driving a derived
allocation (a declared width×height, a record count); this fold is about the raw body's
*own byte count* and whether the cap runs before or after the framework buffers
it. Coverage by a shared helper is not coverage of the whole app: a codebase
whose JSON routes sit behind a bounded-read middleware can still ship this bug
on the one raw-body route that bypasses it — precisely because it isn't a JSON
route.

**API4 — unrestricted resource consumption, the *response-size* axis.** A third
named limit, distinct from the spend and memory axes above and from the GraphQL
batching/depth limits below: **how many rows a single request returns**. When that
count is set by a client parameter (`limit`, `per_page`, `pageSize`, `top`, a
GraphQL `first`) and the server enforces no maximum of its own, one request can be
made to return the whole table, and the amplification is on the **response** side —
the memory to materialize and serialize the rows, plus CPU, DB work and egress, all
scale with an attacker-chosen number and multiply by however many such requests a
caller fires. This is *not* the memory axis above (that is the inbound request
**body**/upload being buffered; this is the **outbound** result set sized by a client
count), and "the endpoint paginates" is not the control. The bound-the-work cap and
keyset-vs-`OFFSET` mechanics already live in `performance-db-cost.md` (the over-fetch
bullet under `## Database`, and the "bound the work" cap under `## Algorithmic`); the
**security** finding is that the
size is *client-settable and unbounded*, so a missing maximum — or one "**set
inappropriately (e.g. too low/high)**" (OWASP API4:2023, which names "Number of
records per page to return in a single request-response" among its required limits)
— is a DoS vector, not just a latency cost. A sensible default page size is not a
cap: the server must **clamp** the requested size to a hard maximum regardless of
what the client asks for. 🚩 a list/search/export handler that reads a
page-size/`limit`/`first` param and passes it to the query (or ORM `take`/`.limit()`)
without clamping it to a server-side maximum.

**API4 — unrestricted resource consumption, the *execution-time* axis.** The fourth
named limit: a server-side wall-clock ceiling on **how long a single inbound request
may run** before the server aborts it and frees the handler. Without one, a heavy
endpoint — a wide-date-range report, an unindexed search, a large export, any
synchronous long aggregation — lets a handful of the slowest requests each occupy a
request handler/connection for as long as the work takes, and a few concurrent ones
starve the shared, finite pool so every other caller (including cheap requests) is
denied service (CWE-770; OWASP API4:2023 names "Execution timeouts" among its
required limits). Correctness of the result and rarity of the slow path are not
defenses: a caller can send the expensive request deliberately and repeatedly. This
is distinct from **two** timeouts already in scope and must not be conflated with
either: the **session** idle/absolute timeout (`Session termination & timeout`,
above) bounds a *user session's* lifetime, not a request's runtime; and the
**outbound** deadline the reliability and SSRF guidance sets — the upstream-call
timeout in API10 below, and `reliability-error-handling.md`'s "propagate the
deadline" rule — bounds calls the server *makes* and in fact *presupposes* an
inbound budget exists to derive from. This fold is that inbound budget, enforced by
the server on itself as an anti-DoS control. 🚩 a report/export/search endpoint (or
any long synchronous aggregation) with no server-side per-request time limit that
aborts the work; offloading the heavy job to a background queue is complementary but
is not itself the ceiling.

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
