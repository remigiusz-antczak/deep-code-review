# Domain B checklist

Read this when domain B (Security — application (OWASP Top 10:2025)) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### B. Security — application (OWASP Top 10:2025) → `references/security-appsec.md`
**If the target has a network surface or accepts untrusted input, load
`references/security-appsec.md` before Phase 3** — the probe procedures, payloads,
and the blocked-range list live there — **plus any sub-file whose trigger matches**
(its routing table names each one). **AppSec is not marked "done" (or clean, or
N/A) on a networked target without that load**; an unloaded reference is an
unwalked domain.

- **A01 Broken Access Control** (incl. SSRF): server-side authorization on every
  sensitive action; no IDOR; deny-by-default. SSRF guards on any URL from input —
  allowlist, resolve-validate-**pin** the IP, `redirect: manual` and re-validate
  each hop; the full **blocked-range list** is maintained canonically in
  `security-appsec.md` (A01), not re-enumerated here (a second copy drifts). Complete the **Identity
  Arrival Map** (document / XHR / bare curl — procedure: `appsec-edge.md`) before proposing any gate —
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
  boundary **and** the confidentiality tier (S0–S3 in `SKILL.md`) (`git check-ignore`,
  `git ls-files --error-unmatch`, route enumeration + anonymous GET sweep), not
  to the rendering code. And an `Origin`/`Referer`/`Sec-Fetch-Site` check is
  **CSRF defense, not authentication** — if it is the only gate on a sensitive/paid/
  mutating action, that action is effectively unauthenticated (why it is bypassable,
  and the CWE-352-vs-CWE-306 split, are in `security-appsec.md`).
- **Secrets**: nothing sensitive in source, history, comments, logs, error
  strings, or fixtures; env/secret-manager only. A gate that finds a secret
  reports `file:line` — it **never echoes the secret**. User-facing errors expose
  an error-*class*, never upstream response bodies.
- 🚩 raw SQL concat, `eval`/`exec`/`system`/`pickle.loads`/`yaml.load`,
  `innerHTML`/`dangerouslySetInnerHTML`, `verify=False`, wildcard CORS with
  credentials, committed `.env`, tokens/keys in the diff, a security gate assumed
  from a present code path but never proven live, a feature that enables itself
  when its gate's self-proof is unavailable.
