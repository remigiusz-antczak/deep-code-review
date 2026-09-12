# Domain audit checklists (A–W)

Read this when walking a domain in Phase 2 (or a DIFF quick-path that touches that domain). Each section expands the one-line map in `SKILL.md`. Load the linked per-domain `references/*.md` for detection procedures.

## Domain audit checklists (A–W)

> Each item folds in the *why*. A "🚩" line lists patterns to grep/scan for.
> Load the linked reference for per-item detection procedures. To turn any red
> flag into a grep for the target's language, see
> `references/language-stack-redflags.md`.

### A. Correctness & logic
- Does it do what the spec/issue/user actually needs — not a plausible adjacent
  thing? Edge cases: empty, null, zero, negative, max/overflow, unicode,
  duplicate, out-of-order, huge, single-element, off-by-one boundaries.
- **Money & numeric precision**: currency uses integer-minor-units or `Decimal`,
  **never** binary `float`; rounding mode is explicit and consistent;
  accumulation error bounded. (Float-for-money is a textbook Critical.)
- **Time & dates**: store and compute in **UTC**, tz-aware; use a **monotonic
  clock** for durations (not wall-clock, which jumps); handle DST, leap
  day/second, and clock skew across services; never derive freshness from a
  local `now()` where the subject's own timestamp is meant.
- A **scope/subset flag must REPLACE the working set, not union into it** — an
  accidental union silently balloons scope and cost; test the two selectors are
  disjoint.
- A query that selects "the latest batch/generation" via `WHERE col = max(col)`
  (or `ORDER BY col DESC LIMIT`-as-batch) is silently broken by **any**
  single-row write to `col` — it can collapse a whole view to one row. Batch
  membership must be an explicit batch id, not a shared timestamp individual
  writes can move (cross-ref D).
- Error paths are correct, not just happy paths; idempotent where retried;
  deterministic where relied upon.
- **UI chrome is a claim** — a tab/heading/count asserts data beneath it; render
  it only when backing data exists ("empty beats fabricated" for layout too).
- 🚩 `==`/truthiness bugs, `float` for money, naive datetimes, mutation of
  shared/default args, silent coercion, unhandled enum case, subset flag that
  unions, "latest batch" keyed on a shared timestamp a single write can move.

### B. Security — application (OWASP Top 10:2025) → `references/security-appsec.md`
**If the target has a network surface or accepts untrusted input, load
`references/security-appsec.md` before Phase 3** — the probe procedures, payloads,
and the blocked-range list live there. **AppSec is not marked "done" (or clean, or
N/A) on a networked target without that load**; an unloaded reference is an
unwalked domain.

- **A01 Broken Access Control** (incl. SSRF): server-side authorization on every
  sensitive action; no IDOR; deny-by-default. SSRF guards on any URL from input —
  allowlist, resolve-validate-**pin** the IP, `redirect: manual` and re-validate
  each hop; the **blocked-range list** (loopback, private, CGNAT, link-local /
  cloud-metadata, IPv4-mapped, dotless labels) is maintained in the reference, in
  one place, so a copy here can't drift out of date. Complete the **Identity
  Arrival Map** (document / XHR / bare curl) before proposing any gate —
  especially for iframe / portal embeds. **Dual surface:** for every sensitive
  loader, check API handler **and** every RSC/SSR page that calls it; API redacts
  while page does not = Critical when world-reachable. Open with the **anonymous
  GET sweep**.
- **A02 Misconfiguration** — detect: compare deployed config to the docs; probe
  debug/verbose error and header/CORS posture. 🚩 debug on in a prod path,
  default credentials, wildcard CORS, stack traces to the client.
- **A03 Software Supply Chain** — detect: audit the **committed lockfile** and the
  pinning of actions/base images. 🚩 action on `@main`/mutable tag, floating
  `:latest` base, install-time scripts, unreviewed new dependency.
- **A04 Crypto** — detect: grep primitives, key sources, randomness. 🚩 MD5/SHA-1
  for auth, ECB or static IV, hand-rolled crypto, `Math.random()` for tokens,
  keys in source.
- **A05 Injection** — detect: trace every untrusted value to each interpreter
  sink. 🚩 string-built SQL/shell/template/LDAP, `innerHTML`, unparameterized
  query.
- **A06 Insecure Design** — detect: walk Phase 0's abuse row for the money /
  write / secret rows and name the missing control. 🚩 no rate limit on a paid or
  mutating action, business rule enforced only client-side, no approval on an
  irreversible step.
- **A07 Auth** — detect: walk the session lifecycle (issue → refresh → privilege
  change → logout). 🚩 no lockout or MFA path, token in `localStorage`, session
  not rotated on privilege change, unbounded token lifetime.
- **A08 Integrity failures** — detect: find every place code/data is trusted
  without verification. 🚩 unsafe deserialization (`pickle.loads`), unverified
  webhook (cross-ref I), update/artifact with no signature or provenance.
- **A09 Logging & alerting** — detect: ask whether an authorization denial or a
  brute-force burst is observable at all. 🚩 refused request logged nowhere, no
  alert on an auth-failure spike, secrets in logs (cross-ref M).
- **A10 Mishandling of Exceptional Conditions** — detect: read what each error
  path *returns*, not what it logs. 🚩 a gate that fails **open** on error, a
  `catch` that returns success/empty-200, an exception message carrying upstream
  internals (cross-ref F).
- **Gates fail closed; prefer allow-lists to deny-lists** (asymmetric failure: a
  forgotten deny entry ships the leak silently; a forgotten allow entry blocks
  loudly). When a gate's own config input is absent **or empty/whitespace-only**,
  **refuse rather than pass** — a non-empty result is not proof the layer ran.
  Enforce an **egress allow-list that a test scans the source against**, so the
  security doc can't drift from the code.
- **Prove the gate runs; don't assume it from a present code path.** For each
  security-critical gate, is it **measured at runtime** — a boot self-proof or
  health check that exercises the gate against real hostile input and **refuses to
  enable when any check reads OPEN** — or is it merely present in the source? When
  the proof is unavailable or the environment is misconfigured, the feature must
  **fail closed (disabled)**, not silently proceed on the assumption the gate is
  wired. An unproven gate that *reads* as safe is itself the finding — this is what
  separates defense-in-depth theatre from a real fail-closed posture, and it
  extends principle 2 ("what a project enforces is verified against the enforcement
  artifact, not the doc") to runtime. Cross-ref C (tool-authz proven live) and F
  (subsystem proven to execute).
- **Before rating a "sensitive/gated data exposed" finding, establish the actual
  exposure boundary** — is the data-carrying artifact tracked in version control,
  served on an unauthenticated route, or in a client bundle? Pin severity to that
  boundary **and** the confidentiality tier (S0–S3 below) (`git check-ignore`,
  `git ls-files --error-unmatch`, route enumeration + anonymous GET sweep), not
  to the rendering code. And an `Origin`/`Referer`/`Sec-Fetch-Site` check is
  **CSRF defense, not authentication** — bypassable by any non-browser client and
  absent on many GET navigations; if it is the only gate on a sensitive/paid/
  mutating action, that action is effectively unauthenticated.
- **Secrets**: nothing sensitive in source, history, comments, logs, error
  strings, or fixtures; env/secret-manager only. A gate that finds a secret
  reports `file:line` — it **never echoes the secret**. User-facing errors expose
  an error-*class*, never upstream response bodies.
- 🚩 raw SQL concat, `eval`/`exec`/`system`/`pickle.loads`/`yaml.load`,
  `innerHTML`/`dangerouslySetInnerHTML`, `verify=False`, wildcard CORS with
  credentials, committed `.env`, tokens/keys in the diff, a security gate assumed
  from a present code path but never proven live, a feature that enables itself
  when its gate's self-proof is unavailable.

### C. Security — AI / LLM / agents → `references/security-ai-agents.md`
Apply if the code calls an LLM, embeds/retrieves, or runs an agent. Maps to
OWASP Top 10 for LLM Applications **2026** (LLM01–LLM10:2026) and the OWASP
Top 10 for Agentic Applications 2026. When the target **is or installs a
skill**, also walk AST01–AST10 in `references/security-agent-skills.md`.
- **Untrusted-in / untrusted-out**: everything the model reads that isn't your
  trusted prompt is data that may contain instructions; everything it emits is
  untrusted input to the next stage. Fence/delimit untrusted content; **strip
  control chars and zero-width/bidi Unicode** (invisible-instruction smuggling)
  and cap length; **schema-validate every output before any use**; never feed
  raw output into SQL/shell/HTML/`eval`/a path/a fetch. Watch the **multimodal
  blind spot** — text inside images/PDFs bypasses text-layer sanitization.
- **Authorize in the infrastructure, not the prompt** — default-deny tool /
  command allow-lists; re-check authorization **fail-closed inside** tool
  execution, not only at the tool-offer layer. **Least-privilege tools**;
  human-in-the-loop on irreversible/high-impact actions; scope every
  approval/consent token to the specific action **and stage** it authorizes.
  **Prove the re-check fires at runtime** — a self-proof / health check that
  exercises it — not merely that the code path exists; an unproven tool-authz gate
  must fail closed, or it is a finding (the runtime-proven-gate lens, domain B).
- **Deterministic-first**: the model never authors a number, score, status, or
  gate — deterministic code does; the model only phrases/adjudicates behind hard
  gates, with a deterministic fallback and a counter for how often it fires. Use
  **temperature 0** for judges/verifiers. Ground claims to the input;
  **log a redacted fingerprint** of output, never the raw text.
- **Bound consumption** (LLM06:2026, was LLM10:2025): token/cost/rate caps enforced *before* each
  billable call; loop caps; breakers on 402/429; a **no-model fast path** for
  rejected/unauthenticated input so a flood can't burn budget.
- **A safety param set at a call site is a claim, not a guarantee** — confirm the
  layer below actually applies it. A `temperature`, `verify=`, `timeout`, `signal`,
  dry-run flag, allowlist, or `readOnly` can be silently dropped/overridden by a
  lower layer, or delegated to an unverifiable platform guarantee; a comment
  asserting a safety property is the highest-value thing to falsify (the class
  and its two sub-cases are in `references/security-ai-agents.md`).
- 🚩 f-string/format prompts from raw input, output → `execute`/`render`
  unchecked, no `max_tokens`/`timeout`/retry cap, broad-scope tools with no
  confirmation, secrets/authz in the system prompt, a safety param asserted at
  the call site but dropped downstream, a same-owner ask written to a
  many-audience board/mesh, inter-agent messages keyed on a display name
  instead of a tenant/uid, an approval prompt that does not name the audience.

### D. Data integrity & data quality → `references/data-quality.md`
Apply to any pipeline, ETL, enrichment, scraping, or dataset producer. Judge the
**output**, not just the code.
- **Monotonic quality (hard invariant)**: a write/merge may **never** replace a
  populated, higher-confidence value with an empty, lower, or duplicate one.
  Upserts **field-merge with preserve-if-absent** — never wholesale-replace.
  Require a regression test that fails on this exact mode. Non-regression gate:
  a within-dataset uniqueness check **plus** a populated→worse check against an
  **explicitly pinned** baseline (never the live artifact).
- A **degraded/empty/fallback result surfaced by a "latest/max" read is the same
  monotonic breach** even when no overwrite occurred — tag it (`degraded: true`)
  and have latest/best queries skip it. A write/erosion guard must intercept
  **every** mutation primitive (update AND clear AND append AND delete), not just
  the common one, and the test proving its coverage must **discover** write-sites
  (grep/AST), never hardcode a list that rots (see `references/data-quality.md`).
- **No fabrication in the data**: skip a field rather than guess; corroboration =
  **two+ independent sources**; `inferred` ≠ `sourced`; omit the unverifiable.
- **Entity resolution biases false-exclude over false-merge**: stable-id/proof
  match, never name-only; ambiguous → flag, never auto-merge.
- Measure the six dimensions separately; mark an inapplicable metric **`N/A`, not
  `0`**; freshness from the subject's own activity; a named quantity carries one
  value everywhere (repetition ≠ corroboration); every consumer/export calls the
  **same shared filter**; machine-computed fields are pipeline-owned (never
  hand-edited); **never lower a baseline just to pass a build**.
- 🚩 unconditional upsert ignoring confidence, fuzzy single-field merge, dedup on
  non-normalized keys, "latest wins" clobbering verified data, a metric scored
  `0` where N/A, freshness from `fetched_at`, a model call returning a score/gate,
  a guard that watches one write API but not its siblings, a fallback/empty record
  a "latest" read surfaces over a good one.

### E. Performance, efficiency & cost → `references/performance-db-cost.md`
- **Algorithmic**: no accidental O(n²)+ on hot paths; right data structure;
  compute-once.
- **Database**: no N+1; needed indexes exist and are used (check the query plan);
  no `SELECT *`; results bounded/paginated; work pushed to the DB; pooled
  connections; tight transactions (no lock held across a network/LLM call).
- **Schema & data migrations**: expand → migrate → contract (backward-compatible
  with old + new code mid rolling-deploy); non-blocking index/column ops
  (`CONCURRENTLY`); `NOT NULL` only after backfill+default; backfill in bounded
  batches **outside** the DDL transaction; a tested rollback path; **snapshot
  before the mutation, not after**; a data-transforming migration must not
  violate D.
- **External / API / LLM calls — cost-and-value lens**: is each call *necessary*
  now? cache with a correct key + invalidation; batch; single-flight duplicates;
  events over polling; don't re-fetch/re-embed unchanged inputs. Enforce spend
  caps **before** the call — per-run **and** a global/monthly cap (from an
  append-only ledger); a **dry-run must cost nothing** (gate the call, not just
  the write); calibrate a big paid run on a small zero-write sample first. For
  model calls, cache the longest stable prompt prefix, bill each token class at
  its real rate, and don't wrap an auto-retrying SDK in a second retry loop. Spend
  caps have subtle holes — a per-run cap whose default is `0`/unlimited is not a
  cap, a ledger loader that resets to empty on a read fault fails **open**, and a
  `SELECT sum()` then check-then-act (or an in-process singleton shared across
  multiple processes) is not concurrency-safe: the spend-safety checklist is in
  `references/performance-db-cost.md`.
- 🚩 queries in a loop, `SELECT *`, missing `LIMIT`, identical repeated
  HTTP/LLM calls, an external call in a `no-store`/dynamic render body, a fresh
  SDK/HTTP client per call, a prompt-cache marker on per-call-varying content, no
  timeout, `CREATE INDEX` without `CONCURRENTLY`, `ADD COLUMN
  … NOT NULL` w/o default, unbounded caches, per-run cap but no global cap, a
  per-run cap defaulting to 0/unlimited, a spend ledger that fails open on a read
  error, a `SELECT sum()`-then-act spend check, no dry-run/apply switch at all.

### F. Reliability & error handling → `references/reliability-error-handling.md`
- Every external call handles failure explicitly: **check status before reading
  the body**; API clients return null/empty and let the caller escalate; batch
  loops catch **per-item** errors, log, and continue so one bad item can't halt
  the run. Every call carries a **timeout and an independent abort signal**
  (one without the other leaves a hang path). Circuit-break on 402/429 or
  consecutive errors.
- No silent swallow (`catch {}` / `except: pass` / `rescue nil`); fail **closed**
  on security-relevant errors, degrade cleanly elsewhere; partial failure never
  corrupts persisted state. **Echo-verify** a write (compare the response
  field-by-field to what was sent). **"Blocked" ≠ "declined"** — when a
  policy/permission gate stops a write/paid op, surface the exact blocked
  operation and how to run it; never route around it.
- Long jobs are SIGINT-clean, cursor-resumable, idempotent, with append-only
  progress so a crash loses no work; a **two-key confirmation** guards the
  highest-consequence irreversible actions; every credentialed integration
  degrades to a **clean no-op** without its key — unsafe if the CLI still
  **persists an empty/zero artifact** that downstream merge/read treats as data
  (procedure: `references/reliability-error-handling.md`). A **load-order/registration bug
  can silently no-op an entire subsystem** — assert each optional/paid subsystem
  actually executes in the deployed environment, not just locally, and that each
  security-critical gate is **proven live (a self-proof / health check) and fails
  closed when the proof is absent**, never assumed from a present code path (the
  runtime-proven-gate lens, domain B). Route control-plane traffic (kill-switch,
  approval) **above** the rate limiter.
- 🚩 swallowed exceptions, retry-forever, no timeout, non-idempotent retry, work
  lost on crash, status not checked before body read, an emergency stop behind
  the limiter.

### G. Concurrency & shared state → `references/concurrency-shared-state.md`
- No data races on shared mutable state; correct locking/atomicity; no deadlock
  ordering; no check-then-act (TOCTOU). Async: awaited promises, no
  fire-and-forget that drops errors, cancellation handled.
- **Whole-file/load-once state stores**: a single writer per file (or per-key
  files) and reload-before-access, or concurrent writers clobber and long-lived
  readers never re-read; a corrupt/torn read of a critical record fails closed.
  Concurrent agents/workers **claim a lane** (the file set, with expiring claims)
  before editing and commit explicit paths — never stage-all.
- **Lifetime, not only synchronization.** A field on a long-lived singleton
  (framework `@Injectable`/`@Component`, a module global) holding per-request/run
  data leaks across calls **even with perfect synchronization** — match each
  stateful field's lifetime to its data's; thread a per-run value.
- 🚩 shared mutable globals, a singleton field whose lifetime outlives its data,
  missing `await`, non-atomic read-modify-write, lock
  held across I/O, two workers writing the same file, **tests or jobs that write
  a real shared/tracked data path** (cross-ref J;
  `references/testing-and-evals.md`).

### H. Tech debt, dead code & maintainability
- **Dead code & deps** removed (unreferenced code is maintenance + attack
  surface). **Duplication** unified judiciously — but three similar lines beat a
  wrong abstraction, and a one-caller "helper" is premature; where logic *must*
  be mirrored, link the source of truth in a comment **and** add a coherence test
  running one fixture through both paths. **Copies that must stay byte-for-byte in
  lockstep** — vendored modules, per-runtime-plane duplicates, generated-vs-source
  pairs — need a **parity test or a single generated source**, or they silently
  drift; flag the *missing guard*, not the duplication itself (a drifting second
  copy of a crypto/auth module would encrypt/decrypt or authorize differently on
  each plane — a security hazard, cross-ref B).
- **Complexity**: one thing per function; shallow nesting; named constants/enums
  over magic values in one place. **Naming & structure** navigable by human and
  AI. **Dependencies current and safely upgraded** — see K and
  `references/dependency-currency-and-upgrades.md` (currency + safe-bump
  discipline; A03 for supply-chain integrity). Consistency with the surrounding
  code.
- **Feature-flag lifecycle**: each flag has an owner, a kill-switch, a test for
  both states, and a staleness/removal policy; dead flags are removed.
- **Lockstep surfaces** enumerated — the file sets that must change together
  (schema ↔ validator ↔ type ↔ prompt ↔ docs ↔ test).
- 🚩 commented-out blocks, `v2`/`_old`/`copy` files, duplicate helpers, dead
  flags, unused imports/deps, god-functions, byte-identical duplicated modules
  (per-plane, vendored) with no parity guard.

### I. API, interface, contracts & integration → `references/api-contracts.md`
- Public interfaces minimal, consistent, hard to misuse; breaking changes
  versioned (SemVer) and documented; inputs validated at the boundary; outputs
  match the documented schema; errors typed and documented.
- **Serialized-state & message/queue schema evolution**: adding a required field
  breaks in-flight messages and persisted data written by old code — evolve
  compatibly (optional-with-default, versioned payloads), exactly like a DB
  migration.
- **Webhooks / inbound integrations**: **verify the signature**; enforce
  **replay protection** (timestamp + nonce) and **idempotency keys**; tolerate
  **out-of-order and duplicate** delivery. Never trust a webhook body's identity
  claims without verification.
- For HTTP/GraphQL APIs, overlay the OWASP API Security Top 10 (2023) — see the
  appsec reference (`security-appsec.md`); contract evolution and webhook
  procedures live in `api-contracts.md`.
- 🚩 unverified webhook handler, unvalidated request body, silent contract change,
  required-field added to a live message schema, inconsistent error shapes.

### J. Testing & evaluation → `references/testing-and-evals.md`
Match coverage to what the project does; skip inapplicable types rather than
writing theater.
- **Unit / integration / e2e / regression / security / property-fuzz /
  snapshot-weight-pin / AI-evals / non-functional** — apply what fits.
- **Test the failure, not just the feature** (every guard/refusal path);
  **red-first** (watch it fail before it passes); **adversarially test the
  checker itself** and self-test gates against a planted defect so a check can't
  rot into a no-op; **skip loudly** over absent input (never green over unread
  input); **verify the served response, not the repo**; keep tests **hermetic**;
  **probe the real fixture before pinning an expected value**.
- **AI evals** for model-dependent output: a labeled golden set with an accuracy
  threshold that **gates prompt/model-version changes**; the harness's own
  scoring is pure + unit-tested; self-consistency ≠ precision.
- 🚩 tests that assert nothing, trivial mocks, no test for the reported bug,
  hidden `skip`/`xfail`, coverage gamed, an AI feature with only mocked tests,
  **a test that writes a real tracked/shared data path instead of a temp dir —
  especially when cleanup lives only in `finally`/`try` that `process.exit` /
  SIGINT / overlapping runs can skip** (depth: `references/testing-and-evals.md`).

### K. Build, CI/CD, supply chain & release → `references/release-engineering.md`
Two halves: build/supply-chain (below) and the **release** half — feature-flag
lifecycle, canary/blue-green claims vs actual config, DORA-or-`UNMEASURED` —
`references/release-engineering.md`.
- One-command reproducible build; lockfiles committed and honored; CI gates
  merge on lint + format + type + tests + security/dependency scan.
- Third-party CI actions **pinned to a commit SHA** (not `@main`/`@v3`), bumped
  by a bot that passes the same gates; secrets from the CI store, never echoed
  (`set -x` leaks). **Package-signature verification is blocking**; transitive-CVE
  audit is advisory. SBOM + build provenance (SLSA) for releases; rollbacks
  possible; **verify identifier ownership before deploy** (a slug/app-id another
  service owns gets silently clobbered).
- **Dependency currency & safe upgrades** → `references/dependency-currency-and-upgrades.md`.
  Are third-party deps, runtimes, and base images on a supported **latest-stable**
  version, with no known-vulnerable or EOL/unmaintained/deprecated components
  (audit the **committed lockfile**, transitive deps included)? And is upgrading
  *disciplined*: one dep/group at a time, changelog/migration read, risk sized by
  the **semver delta** (a MAJOR is a breaking change by definition), lockfile
  regenerated, the new release checked it isn't itself malicious (cross-ref A03),
  and the project's **own aggregate gate proven green on the bumped tree** before
  merge? Staleness is an A03 security risk; a blind jump to "latest" is how a
  breaking or hijacked version lands — the review closes the *risky* gap through
  the gate, it does not bump everything. Rank by exploitable consequence: a
  known-exploited CVE on a reachable path is Critical/High; merely-behind-latest
  with no vuln is Low/`Nit:` currency debt (batch it, recommend an update bot),
  never outranking a real defect.
- The **privacy/PII gate fails closed when its banned-terms input is missing**,
  scans the lines a branch adds (fork PRs included), and never echoes a match.
- 🚩 green CI that skips tests, secrets in CI logs, actions on a mutable tag, no
  dependency scan, non-reproducible build, deploy without ownership check, a
  known-vulnerable or **EOL** dependency/runtime/base image shipping, a single
  "update all dependencies" commit with no per-dep test evidence, no update-bot
  config (`dependabot.yml`/`renovate.json`) beside a long tail of outdated deps.

### L. Infrastructure as code, containers & cloud → `references/infra-iac-containers.md`
Apply if the target ships Dockerfiles, K8s/Helm, Terraform/Pulumi/CloudFormation,
or cloud config. (OWASP A02/A03; benchmark against CIS.)
- Containers: non-root, pinned-by-digest minimal base, **no secrets in image
  layers/env/build-args**, resource limits, dropped capabilities. K8s: pod
  security context, RBAC least-privilege (no wildcard verbs), default-deny
  NetworkPolicy, secrets via a manager. Terraform: least-privilege IAM (no `*`
  actions/principals), no `0.0.0.0/0` to sensitive ports, no public buckets,
  encryption at rest+in transit, **no secrets in state or `.tf`** (state is
  secret material). Scan IaC in CI.
- 🚩 `FROM …:latest`, no `USER`, `privileged: true`, `hostPath`, `verbs:["*"]`,
  `0.0.0.0/0`, `"Action":"*"`, public-read ACL, secrets in `.tf`/state.

### M. Observability → `references/observability.md`
Load the reference when the target runs unattended (a service, a scheduled job, a
pipeline) or when a finding turns on whether a failure would be **noticed** —
log-level/redaction procedures, correlation-ID plumbing, and the failure-class vs
outcome distinction live there.
- Structured logs at the right level with correlation IDs and **no secret/PII
  leakage** (redact by default; over-logging is itself a vuln). A **transport/
  quota failure is logged in a distinct class** — never recorded as a substantive
  negative outcome, or a rate-limit storm silently corrupts your metrics. Key
  metrics + actionable alerts on the failures that matter; no alert noise.
- 🚩 `print`-debugging left in, logging full request bodies with tokens/PII, no
  way to trace a failure, no metric on the critical path, failures miscounted as
  results.

### N. Configuration, secrets & environments
- All config via env/secret-manager with a committed, secret-free `.env.example`;
  missing config fails **loudly** at startup. Sensible safe defaults; dev/staging/
  prod separation. Files that *functionally* need real values (allowlists, seeds)
  are gitignored and loaded at runtime; a missing file degrades to a clean no-op,
  never a crash or a fabricated result.
- 🚩 committed secrets, hard-coded config paths, prod behavior depending on an
  undocumented value, a silent default that masks misconfiguration.

### O. Documentation & developer experience → `references/docs-and-dx.md`
- **README (human-facing)**: BLUF (what it is, the problem, how it's solved —
  sources → processing → output) in plain language for a non-technical reader;
  an architecture + data-flow diagram (Mermaid / C4); cross-linked docs;
  one-command setup + `.env.example`. Never bake live metrics into prose — cite
  the command. **AI-facing doc** (`AGENTS.md` canonical; `CLAUDE.md` / peers as
  pointers): standards,
  conventions, definition of done, hard rules. Structure docs by **Diátaxis**;
  record significant decisions as **ADRs**.
- **DX**: a `doctor`/preflight that names each missing piece with a fix, prints
  no secrets, and fails only on a genuine blocker; a documented
  missing-prerequisite → symptom map; a **single source of truth** for
  cross-referenced facts enforced by a doc↔code sync check — reconcile each
  load-bearing *optional/required/always/never/all/every* claim against the code
  that enforces it (a mismatch on a deploy-contract claim is at least High);
  document what is deliberately **not** tested/N/A and why.
- **Repository hygiene & cross-agent standards**: community-health files matched
  to the repo's exposure (LICENSE, SECURITY.md, CONTRIBUTING, CODEOWNERS **plus
  the rule that enforces it**, CHANGELOG) and a protected default/release branch
  (PR + review + passing checks, no force-push) — rated Info/Low on a private
  repo, escalating when public/distributed/reaching prod. Agent-instruction files
  (`AGENTS.md` canonical; `CLAUDE.md`/peers as pointers) must not diverge — one
  canonical, the rest point
  to it. **A standards doc with no enforcing gate is advisory** and won't survive
  the next session. (Depth + per-item severities in `references/docs-and-dx.md`.)
- 🚩 aspirational README, stale setup, undocumented env vars, no diagram, "see
  the code," live counts hard-coded in prose, conflicting agent-instruction
  files,  a public repo with no LICENSE/SECURITY.md, a default branch mergeable with no
  review, a standards doc no gate enforces.

### P. Frontend / UI / UX / accessibility → `references/frontend-a11y.md` + `references/product-ux-quality.md`
Apply if the code produces UI. Target **WCAG 2.2 AA**. Two halves: `frontend-a11y.md`
owns a11y **correctness**; `product-ux-quality.md` owns the **design half** (read
it when the target renders a product UI a human operates).
- **Respect the existing design** (principle 5): fix accessibility/usability
  **defects** in place (contrast, labels, keyboard traps, focus, target size);
  treat a change that alters layout/typography/brand as an **owner decision** and
  prompt before imposing it (style guide? or a prototype that can be freely
  changed?). Offer the minimal-visual-impact fix first.
- Semantic HTML before ARIA; keyboard-operable with visible, unobscured focus;
  contrast ≥ 4.5:1 (3:1 large/UI); labels + announced errors; WCAG 2.2 additions
  (target size 24px, dragging alternative, accessible authentication, redundant
  entry). Core Web Vitals (LCP/INP/CLS). **No secrets/keys in the client bundle.**
- 🚩 `<div onClick>` with no keyboard handler, missing labels, contrast failures,
  no loading/error state, secrets in the bundle, `localStorage` for tokens, an
  a11y/UX gate that computes accessible names from `innerText`/`textContent`
  instead of the accessibility tree, a name check that tests presence
  (`if (!name)`) but never shape.

### Q. Privacy, compliance & licensing → `references/privacy-compliance.md`
Load the reference when the target stores, exports, or logs personal data, or when
a licence/regulatory obligation is in scope — retention/erasure procedures,
export-boundary suppression, and licence-compatibility detail live there.
- Only necessary personal data collected; retention/deletion honored; PII
  minimized in logs/analytics/traces; **suppression/erasure enforced once at the
  export/publish boundary** so all downstream inherits it. Dependency licenses
  compatible; attributions where required. Regulatory obligations (consent,
  data-subject rights) met where in scope.
- 🚩 PII in analytics events, GPL code in a permissive project, no retention
  story, tracking without consent, erasure reimplemented per-consumer, a
  committable artifact (PR body, doc, fixture, commit) carrying a real name,
  agent-instance name, or personal workflow when the repo's privacy gate
  forbids it.

### R. Internationalization, encoding & localization
- No hardcoded user-facing strings; locale-aware formatting, sort/collation, and
  pluralization; **Unicode normalization (NFC)** at boundaries — a NFC/NFD or
  casing difference silently splits or merges dedup/join keys (cross-ref D);
  encoding declared and consistent (UTF-8); timezone display vs. UTC storage
  (cross-ref A).
- 🚩 concatenated translated fragments, `.sort()` on localized text without a
  collator, unnormalized text as a key, `latin-1`/mojibake at an I/O boundary.

### S. Branches, merges & open-work triage → `references/branch-and-merge-hygiene.md`
Apply on a **FULL / repo-level review**, or whenever the request names branches,
cleanup, or open work. **N/A by scope on a narrow `DIFF`/`FILE`** — a PR/branch
reviewed against a base stays a compact packet (don't fetch and triage every
branch to review a ten-line change) unless branch cleanup was explicitly asked.
The deliverable is a **triage of all open work**: for every branch, one
recommendation and the exact command. Distinct from section O, which owns whether
branch *protection* is configured — this owns *what open work exists and what to
do with it*; the one seam ("must this merge go through a PR?") reads O's posture.
- **Ground the branch set before judging it** — `git fetch --all --prune` first;
  an un-refreshed/shallow clone hides open branches and a "nothing to clean up" is
  then a false all-clear (principle 2). **Open-PR / merged-PR state is forge state,
  not git state** (`gh pr list`); if forge auth is absent, mark that column
  `unverified`, never infer "no PR."
- **Detect the branching model → it sets each branch's target.** The user's "merge
  to develop **or** main" is answered by the model in use: **git-flow** (a
  `develop` branch exists) merges features to `develop` and `release/*`/`hotfix/*`
  to `main`; **trunk-based / GitHub flow / GitLab flow** integrate to the default
  branch (`main`). State the detected model before recommending targets.
- **Classify by content, not just tip.** `git branch --merged` misses squash- and
  rebase-merged branches; `git cherry` recovers single-commit squashes and
  rebases but **a multi-commit squash defeats patch-id matching** — so the forge's
  merged-PR list is the authoritative "already merged" corroborator. Recommending
  a merge/PR for already-merged work is a fabricated, conflict-generating finding.
- **One recommendation per branch**, target resolved from the model: merge /
  open a PR / rebase-or-refresh / **delete-if-merged** / **split** (security part
  onto its own PR — Phase 5) / **cherry-pick the one good commit** / **close-as-
  superseded** / **convert-to-draft** / **tag-then-delete** (reversible) /
  **escalate to owner** (stale WIP). Carrying any of these out is
  destructive/shared-state — **advise + give the command, execute only on
  approval** (principle 7); **never delete unique unmerged work** (data loss —
  push or tag it first), never rewrite shared history (`--force-with-lease`, never
  `--force`).
- **A leaked secret is not remediated by deleting the branch** — the objects stay
  reachable on the remote until GC/forge cleanup and clones already have them;
  the fix is **credential rotation** (cross-ref B), not `git push --delete`.
- **Default depth on `FULL`: escalate the consequence branches, count the rest.**
  Name and rule on the branches whose consequence is real — an **unmerged security
  or bug fix**, a branch that is the **only copy** of work, a **badly diverged
  long-lived** `develop`/`release/*` — and give the remainder a **one-line count**
  ("11 merged-but-undeleted, 3 stale WIP; cleanup commands on request"). Produce
  the **full per-branch table only when the user asked for cleanup or branch
  triage**; an unrequested 40-row table is what pushes the Criticals off-screen.
- **Severity discipline** (mirrors K/dependency currency): batch routine cleanup
  as **one** Low/Info finding carrying the triage table; escalate individually only
  on consequence — an **unmerged security/bug fix on a stale branch** (written but
  never shipped) is **High**, a **branch that is the only copy** of real work is a
  **High** data-loss risk, a long-lived `develop`/`release/*` badly diverged is
  Medium merge-debt. Don't let branch-cleanup volume outrank a real defect.
- 🚩 a `develop` unmerged to `main` for months; dozens of merged-but-undeleted
  branches with no auto-delete-on-merge; a long-lived branch many commits behind
  its target; an unmerged security fix; a branch with no upstream (only copy); a
  "merge this" recommendation for a branch the forge already squash-merged;
  `git push --force` near a shared branch; "just delete the branch" offered as the
  fix for a committed secret.

### T. Multi-tenancy & isolation
Apply when one deployment serves multiple tenants (customers, orgs, workspaces)
from shared infrastructure. **N/A by scope** on a single-tenant app or a personal
CLI. Distinct from **B/A01**, which owns whether *this request* is authorized for
*this object* (IDOR, missing authz), and from **G**, which owns races on shared
mutable state — **T owns whether the tenant boundary holds across shared
infrastructure**. Its distinctive leaks occur *even when the request-level authz
gate passes and no race exists* — a cache or index keyed without the tenant,
context bleeding between requests — because a shared component, not the request
handler, forgot the tenant. A missing tenant *predicate* on a query shares the
defect class with **B/A01** (data-level access control); what T owns there is the
**systemic** fix — scoping enforced in one place, not re-typed per caller.
- **Every tenant-scoped query carries the tenant predicate — enforced in one
  place, not remembered per caller.** A `WHERE tenant_id = ?` re-typed at each call
  site is one forgotten clause away from a full-table cross-tenant read; push it
  into row-level security, a session variable the DB enforces, or a scoped
  repository/query builder that **fails closed when the scope is absent**. The
  classic breach is a missing tenant filter on a **background job, admin, export,
  or report path** — the routes nobody views by hand (cross-ref B/A01, W jobs).
- **Cache, index and derived-store keys include the tenant.** A cache key, memo,
  search index, vector namespace, materialized view, or rate-limit bucket keyed
  *without* the tenant id serves one tenant's data to another **on a hit** — and
  the authz layer never runs, so B's checks never see the request. This is the
  leak that survives a perfect access-control review.
- **Per-request tenant context does not outlive its request** (cross-ref G,
  lifetime): a tenant id cached on a singleton, thread-local, module global, or a
  connection handed back to a cross-tenant pool bleeds into the next tenant's
  request **even with perfect locking**. Reset or thread the tenant per unit of
  work; never derive it from anything but the authenticated principal.
- **The isolation model is explicit and matches the data's sensitivity**:
  shared-row (RLS), shared-schema, or database/silo-per-tenant — each trades blast
  radius against cost; name which one is in use and why. Where a tenant is promised
  its own encryption key or data residency, a shared-pool default silently
  violates it (cross-ref Q privacy, L infra).
- **Noisy-neighbour fairness**: one tenant's request rate, query cost, or job
  volume must not starve the rest — per-tenant quotas/limits and bounded work per
  tenant (cross-ref E cost, W jobs).
- **Cross-tenant lifecycle is complete**: tenant export and deletion cover *every*
  store — primary, cache, search index, blobs, logs, backups; a half-deleted
  tenant is both a privacy breach (Q) and a future cross-tenant leak.
- 🚩 a tenant-scoped table queried with no tenant predicate on any path (job,
  admin, export, report); a cache/index/rate-limit key missing the tenant id;
  tenant context on a singleton/thread-local/pooled connection; an admin "see
  everything" query reachable by a tenant principal; per-tenant deletion that
  skips the cache/index/backups.

### W. Workflows, jobs & scheduling
Apply when the target runs scheduled jobs (cron), background queues/workers, or
multi-step/long-running workflows. **N/A by scope** on a purely synchronous
request/response app with no async work. Distinct from **F**, which owns whether
*one* call handles its own failure (timeout, retry, idempotent, circuit-break),
and from **G**, which owns races on shared state — **W owns the orchestration**:
whether scheduled, queued, and multi-step work runs correctly *as a system*.
(One-time schema/data migrations are **E**; deploy/rollout is **K** — not here.)
- **Never-runs**: a scheduled job that silently stops is invisible. Assert
  **liveness** — a heartbeat, a last-success timestamp, a dead-man alert — not just
  that the scheduler is "configured". A cron that never fired and a job that ran
  and did nothing are indistinguishable without it (cross-ref M observability).
- **Runs-twice / exactly-once**: overlapping runs (a slow job re-triggered before
  it finishes), at-least-once queue redelivery, and retries all fire the effect
  more than once. "Exactly-once *delivery*" is a myth — design for exactly-once
  **effect** on at-least-once delivery: make the effect **idempotent** (dedup key,
  upsert, processed-set) or guard it with a single-runner lock that has an expiry
  (cross-ref F idempotent retry, I webhook idempotency).
- **Failure escalates from the item (F) to the batch as a whole**: beyond F's
  per-item try/continue and cursor-resumability (cross-ref F), the job needs a
  **dead-letter / parking** path for items that keep failing and a **retry cap**
  so a poison message doesn't retry forever instead of quietly wedging the queue.
- **Schedule time is handled correctly**: cron runs in an **explicit timezone** —
  a local-time schedule shifts under DST, and a job "at 02:30" can run twice or
  zero times on a DST boundary; the **catch-up policy** on a missed window is
  deliberate (run-once vs backfill-each-miss), not accidental. (The clock
  primitives themselves — monotonic durations, UTC storage — are domain A.)
- **Ordering and dependencies are explicit** where relied on: a queue is not FIFO
  under retry, and a downstream job that assumes an upstream finished needs a real
  dependency/trigger, not a `sleep`. Fan-out/fan-in joins wait for actual
  completion, not an elapsed timer.
- **Long-running workflow state is durable and recoverable**: a multi-step saga
  persists each step's outcome and defines **compensation** for a step that fails
  *after* earlier steps committed; a process crash **resumes** the workflow — it
  does not double-apply a committed step or strand the workflow half-done
  (cross-ref F, G).
- **Backpressure and bounds**: queue depth is monitored and bounded; a producer
  faster than its consumer degrades deliberately (shed load, buffer-with-cap),
  never unbounded memory or spend growth (cross-ref E cost, M).
- 🚩 a cron with no liveness/heartbeat alert; a non-idempotent effect on an
  at-least-once queue or an overlapping schedule; no dead-letter path or retry cap
  (poison retries forever); cron in an implicit/local timezone; a downstream step
  that `sleep`s to wait for an upstream; a multi-step workflow with no persisted
  state or compensation; an unbounded queue or producer.

---

