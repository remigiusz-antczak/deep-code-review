# Application security depth — gates, proxy chains, caches, and isolation headers

Read this when the target or diff recommends an auth gate, middleware, or edge rule; sits behind a reverse proxy, CDN, or WAF; keys a rate limit, allow/deny list, geo rule, or audit identity on `X-Forwarded-For` / `Forwarded` / `X-Real-IP`; caches a response derived from identity or reflects a header into a cacheable response; is embedded cross-origin or uses camera, microphone, geolocation, or payment APIs; a load test's traffic identity is unverified; or an unauthenticated surface filters resource types by name (allow vs deny list). Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A01:2025 — Broken Access Control (depth: gate proposals, proxy chains, caches)

**Identity Arrival Map (required before proposing any gate).** Before recommending middleware, a document-level
redirect, or an edge gate — especially for an app embedded in an iframe, portal host, or third-party shell — fill this
table from evidence:

| Request class | What identity arrives? | What a gate can see | Can a client forge it? |
|---|---|---|---|
| Document / RSC / SSR (navigation) | ? | ? | ? |
| Same-origin XHR / `fetch` (Bearer, custom headers) | ? | ? | ? |
| Cross-site / bare `curl` (no cookies, no Bearer) | ? | ? | ? |

**Forgeability / bypass row-set (required with the map):** (1) Is the **origin reachable directly**, bypassing the
edge/WAF that enforces auth? (2) Does the app **strip inbound copies** of trusted proxy/identity headers
(`X-Forwarded-*`, `X-User`, host-injected claims)? (3) Does the gate matcher cover `/path`, `/path/`, case variants,
encoded traversal (`%2e%2e`), and **non-GET** verbs? (4) Path normalization before match?
**(5) Do the edge/proxy and origin agree on where one HTTP message ends and the next begins** — `Transfer-Encoding` vs
`Content-Length` precedence, consistent by HTTP version — or can a crafted request desync them, so the edge inspects
one message while the origin executes a different, smuggled one (HTTP request smuggling, CWE-444)? A gate whose input
a client can set is not a gate.

**Known anti-pattern:** "add middleware on the document request" when identity only arrives on same-origin XHR via a
client-attached Bearer (or a host-injected header the document never carries). Propose a gate only on a request class
that actually carries the principal. Cross-ref Phase 0 platform-vs-app-vs-preflight.

**Smuggling defeats a correct gate without forging anything.** Every header check above can be correct and the gate
still bypassed if the edge/WAF and the origin disagree on request boundaries: a `Transfer-Encoding` header alongside a
`Content-Length`, parsed inconsistently by the two hops (CL.TE / TE.CL / TE.TE), lets one connection smuggle a second,
uninspected request past the WAF into the origin — or poison the connection so the *next* user's request arrives
prefixed with attacker bytes it can capture — a confidentiality break, not just an authz bypass. The anonymous-GET
sweep proves nothing here — it shows only that the edge's *own* parser rejects requests it recognizes as
unauthenticated, not that the edge and origin agree on what a request *is*. In HTTP/1.x a present `Transfer-Encoding`
means `Content-Length` must be ignored (ASVS v5.0.0-4.2.1, L2); reject or normalize a message carrying both. 🚩 a
reverse proxy and origin of different vendors/versions in front of an auth gate with no desync-specific test — plain
`curl` won't surface it; it needs a raw-socket / desync tool.

**Bidirectional gate proof (required before recommending a gate).** Every proposed gate ships an expected-status table
**per request class**, before and after: anonymous → 401/redirect **and** legitimate member → 200 on the **same**
class; plus a test that **fails with the gate removed**. A proposal missing the member→200 row is incomplete — don't
recommend it (this is how outage-causing middleware ships).

**A load test against an "authed" endpoint that never actually authenticated reports the
wrong system.** A load-test harness pointed at a route behind an auth gate can **fail open
at the harness**, not the app: a missing/expired token, a login step that silently
no-ops, or a session cookie the runner never picked up all make the harness fall through to
whatever the route serves an anonymous caller — often a cheap 401/redirect or a cached
public response — while the run still reports clean throughput and 0% errors, because
nothing about that shape looks like a failure. The gate then clears the **wrong** code path;
the real, identity-bearing path (per-request user object, session lookups, wider response
payload) never ran once (one observed run: "60 users, 0% errors" turned out to be byte-identical
anonymous and authenticated responses; the real authenticated path, once actually exercised,
OOM'd in 100-200s). **Assert identity resolution before measuring anything else**: confirm the
response body/size differs between an anonymous and an authenticated call to the same URL
before trusting any throughput/error/latency number from the run. The harness itself must
**fail closed** on an auth failure — abort the run rather than silently falling through to the
anonymous path. **Check:** `bytes(authed
response) != bytes(anonymous response)` for the same request, else the load-test run FAILs
before it reports any perf number.

**A denylist of excluded types on an unauthenticated surface is permissive by default for
every type added later — this is not a fail-open bug, it's the list working as written.**
"Fail open" names what a check does when it *can't run* (errors, times out); this check
runs fine and still ships every unnamed type, because excluding by name means anything
unnamed passes. A response filter that hides certain record/resource **types** from an
anonymous caller by naming the ones to *exclude* (a denylist) is silently permissive for
any type that didn't exist, or wasn't named, when the filter was written — a new type
ships visible-by-default to every unauthenticated caller until someone remembers to add
it to the denylist, and nothing fails or warns in the meantime (caught only at review in
one observed case). The unauthenticated surface is exactly the wrong place for a
permissive-by-default list: invert it. **Name the types an anonymous caller may see (an allowlist)**
and exclude everything else by default, so a new type is invisible until someone
deliberately grants it. **Check:** a test asserts the returned type set equals the
allowlist **exactly** (not "contains no denylisted type") — new-type coverage is
structural, not remembered.

**A security decision keyed on a client IP parsed from a multi-hop proxy header trusts the wrong end unless it counts the proxies in front of the app (CWE-348, *Use of Less Trusted Source*).**
A rate-limit key, IP allow/deny, geo/geoblock, or audit-"who did this" identity derived from `X-Forwarded-For` /
`Forwarded` / `X-Real-IP` reads a **chain**, not a value: each proxy *appends* the peer it saw on the **right**, so
the **rightmost** entries are what your own last-mile infrastructure observed and the **leftmost** entry is whatever
the original client sent — as forgeable as any other client-supplied header. Taking a fixed index-0-from-the-left
(`xff.split(',')[0]`) trusts the attacker's value as "the client IP". The trap:
**verifying the parse is correct is not the property under review** — a split-on-comma, trim, validate-each-IP parser
can be flawless and still trust the wrong element, and every happy-path test passes because for an *honest* client
index 0 *is* the real address — only a crafted request that prepends a spoofed `X-Forwarded-For:` reveals the
inversion, letting an attacker mint a fresh "IP" per request to skip a rate limit, land on an allow-list, spoof a geo,
or poison an audit trail (a form of CWE-807, reliance on an untrusted input in a security decision). **Fix:** pin the
exact number **N** of trusted proxies between the app and the internet (or a trusted-CIDR set), then trust the
**(N+1)th entry from the *right*** — the address your outermost trusted proxy observed and appended — and discard everything to its left as client-supplied; use the platform's proven primitive (Express `app.set('trust proxy', <n | CIDRs>)` then `req.ip` — the `security-appsec.md` A02 `trust proxy` misconfig 🚩 is this defect's Express face; WSGI `ProxyFix(x_for=N)`; nginx `set_real_ip_from` + `real_ip_recursive`), never a hand-rolled left index. If the origin is reachable **directly** (not strictly behind the proxy), the header is unusable for a security decision — bind the limit / audit to an **authenticated principal** instead (cross-ref `security-appsec.md` A06 § rate-limit key: a scarce verified identity beats any IP). Distinct from the strip-inbound-copies item in the forgeability row-set above — that *removes* a client-forged header when you trust **zero** proxies; this *selects*
the verified segment when a real N-hop chain exists. **🚩** a forwarded header (`X-Forwarded-For` / `Forwarded` /
`X-Real-IP`) feeding a rate-limit / allow-deny / geo / audit decision via a fixed left index (`split(',')[0]`,
`.shift()`), or with the framework's trusted-proxy count unset or set to blanket-trust (`trust proxy: true`, no
`ProxyFix` hop count, no `set_real_ip_from`).

**Cache / CDN is an authorization surface.** Responses derived from identity must be `Cache-Control: private` /
`no-store` (or keyed by principal). Check framework static vs dynamic decisions for pages reading cookies/headers;
require `Vary` on every identity input (`Cookie`, `Authorization`, custom auth headers). Sweep
**through the CDN as well as origin**; compare anonymous vs member body for the same URL. Origin-only anon GET can
look clean while the edge serves a cached member page.

**Cache poisoning — an unkeyed input that shapes the cached body.** The mirror of the leak above. If an
attacker-controllable request component **influences the response body but isn't part of the cache key** — a reflected
header (`X-Forwarded-Host`, `X-Forwarded-Scheme`) or a routing-override header (`X-Original-URL`, which makes the
server serve a different page's body under the requested URL), a param the app echoes, or any header the response
varies on without a matching `Vary` — the attacker's value is cached under the normal URL and served to **every**
subsequent visitor, turning a *reflected* XSS / open-redirect / malicious-script-src into a
**stored, mass-distributed** one. Census the **cache key** (what the CDN/edge actually keys on) against
**every input that can change the response** (headers the app reads, not only the path+query); anything that varies
the body must be **stripped/normalized at the edge, or keyed on** (keying on an attacker-settable header risks
cache-key cardinality blowup — prefer strip/normalize), and never reflect an unkeyed header into a cacheable response.
(Distinct from the identity leak above — that serves one real user's private body to another; this serves an
*attacker's* injected body to everyone — and from connection-level request smuggling in A01.)

## A02:2025 — Security Misconfiguration (depth: isolation headers)

**`Permissions-Policy` and the cross-origin isolation trio extend the same header census, not a separate concern.**
`Permissions-Policy` denies powerful browser features (camera, microphone, geolocation, payment) by default; the OWASP
HTTP Headers Cheat Sheet frames the goal as letting a site "never allow the camera or microphone to be activated" even
when an injection (XSS) runs. `Cross-Origin-Opener-Policy` (COOP) and `Cross-Origin-Resource-Policy` (CORP) close two
distinct leaks the OWASP XS-Leaks Cheat Sheet documents (with `Cross-Origin-Embedder-Policy` (COEP) the third leg of
the cross-origin-isolation trio, per the HTTP Headers sheet): COOP puts a page in its own browsing context group, so a
cross-origin page that **opens it** (a popup, a lured new-tab click) gets back an inert handle instead of a live
`window` reference — closing the frame-counting family, where the sheet's own example is an attacker opening the
target and reading `win.frames.length` off the handle it gets back. CORP stops another origin from loading the
response at all, closing the `onload`/`onerror` resource-probing family and doubling, per the **HTTP Headers** cheat
sheet, as "a robust defense against attacks like Spectre." XS-Leaks' own Quick Recommendations list COOP+CORP
alongside SameSite cookies and framing protection to "strengthen the isolation of your application between other
origins" — `security-appsec.md` already covers SameSite (A07 § Session cookie flags) and frame-ancestors/clickjacking
(`frontend-a11y.md`); COOP/COEP/CORP is the missing header from that set, not a claim these four close every XS-Leak
(the sheet separately names Fetch Metadata/`Sec-Fetch-Site` and per-resource unpredictable tokens, out of scope here).

**🚩** a cross-origin-embedding-or-embedded surface, or one handling sensitive device-capability APIs
(camera/mic/geolocation/payment), with no `Permissions-Policy` and no COOP/CORP set.
