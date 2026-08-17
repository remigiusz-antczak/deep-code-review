# Observability, audit trails & recoverability

Read this when reviewing logging, metrics, traces, dashboards, alerting, audit
trails, or "could we tell this broke, reconstruct who did it, and restore what
was lost." Expands section M of `SKILL.md`; the security-event slice is A09 in
`security-appsec.md` (log the right events, tamper-resistant, alerted), and the
failure paths that *produce* these signals are section F /
`reliability-error-handling.md`.

---

## Detection procedure

1. **Pick the two or three flows that matter** (the paid pipeline, the login
   path, the checkout/write path). For each: if it broke silently at 3am, what
   fires? Trace the answer to a real alert rule, not a dashboard nobody opens.
2. **Read the log lines on the failure path**, not the happy path — that's where
   raw request/response objects get dumped.
3. **Enumerate metric emitters**; read label/tag arguments for unbounded values.
4. **Find the audit trail** for destructive and privilege-changing operations,
   and check who can edit or delete it.
5. **Find the backup config, then the restore evidence** — a backup with no
   documented, dated restore drill is untested.

---

## Golden signals & alerting

- Cover **latency, traffic, errors, saturation** per critical service or job —
  plus, for batch/pipeline work, *freshness* (time since last successful run) and
  *volume* (records processed vs. expected). Average latency hides the outage;
  use percentiles (p50/p95/p99).
- **Alert on the symptom, not only the cause.** "CPU > 80%" without "checkout
  error rate > 1%" or "no successful run in 2× the schedule interval" means a
  frozen job or dependency outage pages nobody. Cause alerts are for diagnosis;
  symptom alerts are the contract with the user. Each alert names an owner and a
  next action — constantly-firing alerts train the team to ignore the page.
- **Distinguish transport/quota failure from a substantive negative result.** A
  429/402/timeout recorded as "no match" or "score 0" silently corrupts metrics
  and downstream data (`data-quality.md`). Health/readiness endpoints must check
  real dependencies, not `return 200`.

---

## Logs & traces: secrets, PII, injection

- **Redact by default**: an allow-list of loggable fields beats a deny-list of
  forbidden ones — over-logging is itself a vulnerability (A09). Left-behind
  `print` debugging is its own finding.
- Common leaks: whole request/response objects, `Authorization`/`Cookie` headers,
  bodies on 4xx/5xx, DSN-style connection strings in errors, LLM prompts with
  user data, stack traces with locals, query params carrying tokens or emails,
  error-tracker breadcrumbs.
- **Spans carry the same risk**: span attributes, DB statements with inlined
  literals, HTTP instrumentation recording full URLs and headers. Sampling does
  not make a leak safe — a 1%-sampled secret is still leaked, into a third-party
  store. Log/trace retention counts as personal-data retention
  (`privacy-compliance.md`).
- **Log injection**: user-controlled strings must be emitted as structured
  fields, never concatenated into a line — embedded `\n`/`\r` lets an attacker
  forge entries and break the parser (CRLF/log-forging, CWE-117 — name only,
  verify before citing). Key-value logging avoids this by construction.
- Correlation/request id propagated across services and present on every line so
  an incident can be reassembled; log levels used meaningfully.

**Grep leads (tune to language):** `log`/`logger`/`console.log`/`print` followed
by `req`, `request`, `body`, `headers`, `user`, `token`, `password`, `secret`,
`apiKey`, `authorization`; `JSON.stringify(` inside a log call; `%+v`/`repr()`
of a request or config struct; `setTag`/`setAttribute` with a raw payload.

---

## Metric cardinality bombs

- Never use unbounded values as label/tag values: user id, email, request id,
  UUID, full URL path with ids, raw error message, SQL text. Each combination is
  a new time series — this is how a metrics bill or the backend falls over.
- Bound the label space: templated route (`/users/:id`), error *class* not error
  text, tenant tier not tenant id. Per-entity detail belongs in a log or trace.

**Grep leads:** metric/counter calls whose tag map includes `id`, `uuid`, `path`,
`url`, `email`, `err.message`, or a string-interpolated name
(`counter("job." + name)`).

---

## Audit trail & repudiation

- Destructive, financial, permission, and configuration changes need an audit
  record answering **who, what, when, from where, old value → new value** — an
  UPDATE overwriting a row with no history can't answer "who changed this."
- **Append-only**: no UPDATE/DELETE grants for the application role on the audit
  table, or ship to a write-once/external sink. A trail the acting user (or the
  app's own service account) can rewrite gives no non-repudiation.
- Record the **acting principal, not just the affected subject**; capture
  impersonation/admin-on-behalf-of explicitly. A failed audit write must fail the
  operation or raise loudly, never a silent `catch` (cross-ref
  `reliability-error-handling.md`).

---

## Backup & restore

- A backup that has never been restored is a hypothesis. Look for what is backed
  up (DB, object storage, secrets/config, IaC state), schedule, encryption,
  **off-instance/off-account copy**, retention, and a **dated restore drill**
  with a measured restore time.
- Stated RPO/RTO must reconcile with the backup interval and the drill's measured
  time; a mismatch is a finding. Restore is tested into a scratch environment,
  with a runbook followable by someone who didn't write it (`docs-and-dx.md`).
- Restoring an old snapshot can resurrect erased personal data — the erasure path
  must be re-applicable after a restore (cross-ref `privacy-compliance.md`).

---

**🚩 red flags**: no alert on the critical path; alerts only on causes; averages
only; health check that always returns 200; quota/transport failure counted as a
result; raw request/response/headers logged; secrets or PII in spans; user input
concatenated into log lines; unbounded metric labels; destructive action with no
audit record; audit table the app can UPDATE/DELETE; stateful store with no
backup, no off-site copy, or no dated restore drill.
