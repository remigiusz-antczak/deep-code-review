# Security — API overlay

Read this when the target serves its own HTTP, GraphQL, gRPC, or WebSocket API (always for `api / service`);
A01–A10, Secrets, and "above" pointers to sections not here name `security-appsec.md`.

## API-specific overlay (OWASP API Security Top 10, 2023)

For HTTP/GraphQL/gRPC APIs, walk the 2023 list; API2/API7/API8 reduce to A07/A01 (SSRF)/A02 above. The categories that
need API-specific procedure:

**API1 + API5 — BOLA (object level) and BFLA (function level).** Run the **two-principal matrix** from A01 above; it's
the procedure for both. BOLA: replay A's object-bearing request with B's id/token/tenant per object route. BFLA:
replay a **privileged verb/route** with an ordinary user's token — enumerate by verb (`GET` allowed, `DELETE`
forgotten), by admin path (`/admin/*`, `/internal/*`), and by nested route (`/orgs/{id}/members/{id}/role`). Expected:
`own → 200`, `other → 403/404`, `under-privileged → 403`. Route-level middleware doesn't prove object-level checks;
grep for handlers that load by id *before* authorizing.

**API3 — mass assignment / over-exposure.** Two directions, both required. Inbound: does the handler bind the request
body wholesale (`Object.assign`, `**body`, `Model(**request.json)`, `update_attributes`, spread into an ORM `update`)?
Require an explicit **allow-list** of bindable fields per endpoint; deny unknown keys rather than ignoring them, and
never let `role`, `owner_id`, `tenant_id`, `balance`, `verified`, or `created_at` be client-settable. Outbound:
serialize through an explicit DTO/field allow-list — returning the whole model (or `SELECT *`) leaks internal columns
and future ones added later. Test by adding a privileged field to a legitimate request and re-reading the object.

**API4 — unrestricted resource consumption, the *spend* axis.** The GraphQL batching/depth limits below and the
container memory/CPU caps (`infra-iac-containers.md`) cover *compute* exhaustion; API4 also names a distinct failure
mode neither catches: an individually-legitimate request — authenticated, or a valid pre-auth flow such as password
reset — that triggers a **metered, paid downstream call** — an SMS/OTP send, an LLM completion, cloud egress, a
per-lookup data-provider API — with **no cap on how many times, or how fast, a caller can trigger it**. Availability
isn't the damage here; the **bill** is (OWASP's own scenario: a forgot-password SMS flow scripted to fire tens of
thousands of times, running up thousands of dollars in minutes). Per paid third-party integration reachable from a
request, ask: is there a **spend ceiling at the provider**, or failing that a **billing alert**? — "Configure spending
limits for all service providers/API integrations. When setting spending limits is not possible, billing alerts should
be configured instead" (OWASP API4:2023). A per-**operation** throttle (OTP sends, password-recovery specifically) is
the application-side complement; a generic per-IP/per-account limiter does not bound a **low-and-slow** spend spread
across many legitimate accounts (CWE-770, Allocation of Resources Without Limits or Throttling). Prefer a
**graduated** response — alert plus the per-operation throttle before a hard cutoff — since a hard provider spend-cap
trips legitimate OTP/reset sends too, converting a cost problem into an availability outage. (In-code spend-governance
bugs — a fail-open ledger, a non-atomic reservation — are in `performance-db-cost.md`.) 🚩 any server-initiated call to
a metered external API / SMS / LLM provider with no per-caller operation throttle and no spend ceiling or billing
alert configured.

**API4 — unrestricted resource consumption, the *auth-exempt outbound-amplification* axis.** The *spend* axis above
bills a **metered** downstream call and names the *bill*, not availability, as the damage; this sibling is the case
where the downstream call need not be billed per use and the damage **is** availability. A
deliberately-**unauthenticated** endpoint that makes a server-side outbound call per request — the canonical case is
an "exchange an identity-provider token for a local session" handler that must run
**before any session cookie exists** — is, by that necessity, on the list of paths the auth middleware is configured
to **skip** (`appsec-edge.md` § Identity Arrival Map, the no-cookie request class). That skip-list entry is the trap: an
*authenticated* endpoint carries an **implicit throttle**, because a caller must first hold a session — itself a
scarce, rate-limited-to-mint credential (A06 § Rate-limit key, burst, and failure mode) — so exempting the endpoint
from the auth gate **removes that implicit throttle along with the auth**, leaving the outbound leg reachable by
anyone at any rate. The individual call is often **correctly** hardened — a per-call timeout, a token-size cap (API10
below) — which is exactly why it survives review: each call looks bounded, yet nothing bounds the
**number or concurrency** of calls, so unbounded inbound requests fan out to unbounded provider calls, exhausting the
app's own outbound worker/connection pool (a self-DoS that starves every other caller) and the provider's
**per-tenant quota** (the provider throttles *you* back, breaking login for everyone) — neither of which a spend
ceiling or billing alert addresses. Why it's missed: the skip-list entry reads as **correct** to an access-control
reviewer — it *must* be reachable pre-session — so the A01 pass signs it off, and the same pass conceals that the
exemption stripped the throttle; the resource-consumption surface is **created by** an access-control decision, and
neither review looks at the other. **Fix:** treat any unauthenticated endpoint that triggers a downstream call as a
resource-consumption surface in its own right — rate-limit it
**specifically and independently of the auth gate it's exempt from** (per-IP, plus per-token-**subject** for honest
callers, backed by a **global** per-endpoint ceiling, since both an IP and an *unverified* token subject are
attacker-mintable — A06 § Rate-limit key) — and **cap the concurrency of the outbound leg** (a bounded pool /
semaphore) so one burst cannot saturate it. Distinct from the *spend* axis (metered call; damage = the bill; fix =
spend ceiling / billing alert), from **A06 § Rate-limit key** (which asks what an *existing* limiter is keyed on and
whether it fails open — here there is **no** limiter, because the auth exemption silently removed the implicit one),
and from **API10** below (which bounds a *single* upstream call's timeout / size / schema — present here — not the
*rate* at which an unauthenticated surface triggers it). 🚩 an endpoint on the auth middleware's skip/allow-list (a
pre-session token-exchange, an unauthenticated "start"/callback, a public webhook that fans out to a downstream call)
making a server-side outbound call, hardened with a per-call timeout / size cap but with **no** per-endpoint rate
limit and no outbound-concurrency cap of its own (CWE-770; OWASP API4:2023).

**API4 — unrestricted resource consumption, the *memory* axis.** Distinct from the spend axis above: the damage here
is exhausted server memory, not a runaway bill, and the trigger is the request's own body, not a downstream call it
makes. OWASP's own vulnerability checklist names "Maximum allocable memory" and "Maximum upload file size" among the
limits an API needs, and its prevention list requires you to "Define and enforce a maximum size of data on all
incoming parameters and payloads, such as maximum length for strings, maximum number of elements in arrays, and
maximum upload file size (regardless of whether it is stored locally or in cloud storage)" (OWASP API4:2023) — but a
cap that exists isn't the same as a cap **enforced in time**. A raw (non-JSON) upload route commonly checks its
byte-size cap only *after* the framework has already fully buffered the whole body into memory: the real check runs
deep inside the storage call, downstream of an unconditional `request.arrayBuffer()`/`.blob()`/`.text()` (or any
framework's equivalent "read the whole body" convenience call) that has no bound of its own. By the time the cap
rejects the request, the allocation it exists to prevent has already happened — a handful of concurrent oversized
uploads exhausts the process for every tenant sharing it, not just the caller who sent them. Two gaps compound: a
pre-check against the declared `Content-Length` is a no-op for a chunked or omitted header (a
`Number(header ?? '')`-style coercion of a missing header commonly evaluates to a value that passes the check
regardless of the real body size), and the framework's whole-body read has no ceiling of its own even when the
declared length was honest. Bound the **read**, not the result of the read: reject immediately on a declared
`Content-Length` already over the cap, *and* enforce a hard ceiling via a streaming read — sum bytes chunk by chunk,
cancel/abort the instant the running total crosses the cap — so worst-case memory use is bounded regardless of what
the client declares or omits. 🚩 grep raw-body reads (`.arrayBuffer()`, `.blob()`, `.formData()` where it buffers, a
no-`limit` `body-parser`) in any handler and trace whether the app's size check runs before that call (safe) or only
after (vulnerable — the memory is already committed). Test with a chunked, `Content-Length`-omitting oversized body
and assert both the rejection and that the handler never buffers past the cap. Distinct from the upload
allow-list/magic-bytes checks (`appsec-files.md`) — those gate *type*, not the order size is enforced
relative to buffering — and from `language-stack-redflags.md`'s CWE-789 "declared/untrusted size value" fold: CWE-789
is a size/count/dimension field read *from inside* an already-received payload driving a derived allocation (a
declared width×height, a record count); this fold is about the raw body's *own byte count* and whether the cap runs
before or after the framework buffers it. Coverage by a shared helper is not coverage of the whole app: a codebase
whose JSON routes sit behind a bounded-read middleware can still ship this bug on the one raw-body route that bypasses
it — precisely because it isn't a JSON route.

**API4 — unrestricted resource consumption, the *response-size* axis.** A third named limit, distinct from the spend
and memory axes above and from the GraphQL batching/depth limits below: **how many rows a single request returns**.
When that count is set by a client parameter (`limit`, `per_page`, `pageSize`, `top`, a GraphQL `first`) and the
server enforces no maximum of its own, one request can be made to return the whole table, and the amplification is on
the **response** side — the memory to materialize and serialize the rows, plus CPU, DB work and egress, all scale with
an attacker-chosen number and multiply by however many such requests a caller fires. This is *not* the memory axis
above (that's the inbound request **body**/upload being buffered; this is the **outbound** result set sized by a
client count), and "the endpoint paginates" is not the control. The bound-the-work cap and keyset-vs-`OFFSET`
mechanics already live in `performance-db-cost.md` (the over-fetch bullet under `## Database`, and the "bound the
work" cap under `## Algorithmic`); the **security** finding is that the size is *client-settable and unbounded*, so a
missing maximum — or one "**set inappropriately (e.g. too low/high)**" (OWASP API4:2023, which names "Number of
records per page to return in a single request-response" among its required limits) — is a DoS vector, not just a
latency cost. A sensible default page size is not a cap: the server must **clamp** the requested size to a hard
maximum regardless of what the client asks for. 🚩 a list/search/export handler that reads a page-size/`limit`/`first`
param and passes it to the query (or ORM `take`/`.limit()`) without clamping it to a server-side maximum.

**API4 — unrestricted resource consumption, the *execution-time* axis.** The fourth named limit: a server-side
wall-clock ceiling on **how long a single inbound request may run** before the server aborts it and frees the handler.
Without one, a heavy endpoint — a wide-date-range report, an unindexed search, a large export, any synchronous long
aggregation — lets a handful of the slowest requests each occupy a request handler/connection for as long as the work
takes, and a few concurrent ones starve the shared, finite pool so every other caller (including cheap requests) is
denied service (CWE-770; OWASP API4:2023 names "Execution timeouts" among its required limits). Correctness of the
result and rarity of the slow path aren't defenses: a caller can send the expensive request deliberately and
repeatedly. This is distinct from **two** timeouts already in scope and must not be conflated with either: the
**session** idle/absolute timeout (`Session termination & timeout`, above) bounds a *user session's* lifetime, not a
request's runtime; and the **outbound** deadline the reliability and SSRF guidance sets — the upstream-call timeout in
API10 below, and `reliability-error-handling.md`'s "propagate the deadline" rule — bounds calls the server *makes* and
in fact *presupposes* an inbound budget exists to derive from. This fold is that inbound budget, enforced by the
server on itself as an anti-DoS control. 🚩 a report/export/search endpoint (or any long synchronous aggregation) with
no server-side per-request time limit that aborts the work; offloading the heavy job to a background queue is
complementary but is not itself the ceiling.

**API6 — unrestricted access to a *sensitive business flow*.** Distinct from the rate-limit key/burst check in A06
above: a flow can be
**correctly authorized, individually within the rate limit, and still harm the business at volume** — scalping limited
inventory across many accounts/IPs, hold-then-cancel to force a price drop, farming a referral/coupon credit. A
generic per-IP / per-principal limiter doesn't catch it because each request, alone, is legitimate; the signal is
**automation, not volume**. First ask the business question the limiter does not — OWASP's framing: "identify the
business flows that might harm the business if they are excessively used" (checkout, referral credit, review/vote,
waitlist, price-affecting cancel). Then check for automation-specific controls the limiter can't provide: device /
headless-browser fingerprinting, human detection (CAPTCHA or behavioral biometrics), and non-human-timing detection —
OWASP's own example is to "analyze the user flow to detect non-human patterns (e.g. the user accessed the 'add to
cart' and 'complete purchase' functions in less than one second)," and ASVS v5.0.0-2.4.2 (L3) requires "business logic
flows require realistic human timing." Machine-consumed (B2B / partner) APIs are the common blind spot. 🚩 a sensitive
flow protected by the **same** generic per-IP limiter as the rest of the API, with no automation / timing signal at
all.

**API9 — inventory (zombie / legacy / `v1`).** Enumerate the *deployed* surface, not the documented one: route tables,
framework route dumps, gateway/CDN and load-balancer configs, access logs, OpenAPI vs reality, old hostnames and
`staging.`/`api-old.` records. Flag every route that is live but unversioned, superseded (`/v1` beside `/v2`),
undocumented, or serving a decommissioned client — old versions usually predate the current authz and rate-limit
layers. Each finding needs an owner and a sunset date or a block at the gateway.

**API10 — unsafe consumption of upstream APIs.** Treat a third-party or internal upstream response as untrusted input:
validate against a schema, bound size and recursion, enforce a timeout and a circuit breaker, and never follow
redirects into internal ranges (A01 SSRF rules apply to the upstream client too). Don't render upstream HTML
unescaped, pass upstream strings to a shell/SQL sink, or trust upstream-supplied ids, prices, or authorization
decisions.

**GraphQL.** Enforce a **depth limit** and a query-cost/complexity budget (recursive fragments are an unauthenticated
DoS); cap **batching** (array of operations) and aliased-field repetition, which multiply cost past a per-request
limit; disable **introspection** and the playground/GraphiQL in production; authorize at the **resolver/field level**
— a single gate on the top-level query lets a nested field walk to data the caller cannot read. Check that errors
don't leak schema internals and that persisted queries, if used, are the only accepted form.

**gRPC.** Auth travels in **metadata**, not a cookie: verify every service method validates the credential in an
interceptor applied server-wide (a per-method check is missed on the next method added), that TLS is required, and
that reflection is off in production. Streaming RPCs need per-message authorization and size/time bounds.

**WebSocket.** Authenticate at the **upgrade** request and re-check on privileged messages; validate `Origin` on the
handshake (browsers do not apply CORS to WebSockets — this is CSWSH) and bind the socket to the authenticated
principal server-side. Never trust a client-supplied user/room id on subsequent frames, and apply per-connection rate
and message-size limits.
