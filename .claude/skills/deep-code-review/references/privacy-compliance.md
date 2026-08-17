# Privacy, compliance & licensing

Read this when the target touches personal data (names, emails, device/user ids,
location, biometrics, free text that can carry any of those), retention or
deletion, consent, data-subject export/erasure, analytics/telemetry, or ships
third-party code to users. Expands section Q of `SKILL.md`.

Regulatory frameworks are referenced **by name only** (GDPR, UK GDPR, CCPA/CPRA,
HIPAA, COPPA, PIPEDA, LGPD, ePrivacy/cookie rules) — no URLs or article numbers
until verified and logged in `docs/standards-index.md` (skill repo) or
`references/standards-index.md` (post-install); describe the
*engineering* obligation instead of citing an unfetched clause. A review aid, not
legal advice — jurisdiction and scope are owner decisions.

---

## Detection procedure

1. **Inventory personal data, don't assume it.** Grep schemas, migrations, event
   payloads, fixtures, and log statements; build a table of *field → collected
   where → stored where → leaves the system where* (analytics, vendor SDK,
   export file, LLM prompt, error tracker, backup).
2. **For each field ask "why?"** — name the purpose and the code that consumes
   it. A field nothing reads is a **minimization** finding, not just dead code.
3. **Follow one user end to end**: signup → storage → derived tables/caches →
   exports/reports → deletion request. Any hop keeping a copy the deletion path
   doesn't reach is a finding.
4. **Prove the jobs run.** Retention/erasure existing only as a function is not a
   control — find the schedule, its last successful run, its alert.

---

## Minimization & purpose limitation

- Collect and persist the minimum: prefer derived values (age band, region) to
  raw ones (birthdate, coordinates), opaque ids to raw identifiers.
- **Purpose limitation as code**: the allowed purpose is a flag or column on the
  record (or on the consent) and every read path checks it. "We only use it for
  X" backed by a doc paragraph alone is advisory (cross-ref `docs-and-dx.md`).
- Secondary uses (model training, enrichment, marketing exports) are their own
  purpose — reuse of data collected for a different one is a design finding until
  the owner confirms scope. Free text and uploads are personal data too.

---

## Retention, DSAR & erasure

- Every personal-data store has a **stated retention period**, a job enforcing
  it, and a way to see the job ran (last-run metric/alert — cross-ref
  `observability.md`). Retention "by policy doc" with no deleting code is a
  finding.
- **Access/export (DSAR) and erasure requests have a clock.** Look for the intake
  path, a request record with `received_at` / `completed_at`, and a bounded SLA
  something actually tracks. No timestamps → no proof of compliance.
- **Erasure must reach every copy**: replicas, search indexes, caches, warehouse
  tables, object storage, queues/dead-letters, logs, error-tracker events, vendor
  systems, backups. Where a backup can't be surgically edited, the control is a
  bounded backup-retention window plus re-erase on restore — say that explicitly
  rather than claiming full deletion.
- The erasure path must be idempotent and re-runnable; prefer soft-delete +
  suppression + a hard-delete job over an immediate delete that orphans rows.
  **Suppression is enforced once, at the export/publish boundary** — the single
  place every consumer passes through. Per-consumer re-implementation is both a
  compliance and a duplication finding (cross-ref `data-quality.md`).

**Grep leads:** `deleted_at` with no job acting on it; `suppress`/`optout`/
`do_not_contact` used in one exporter but not another; a `retention` constant
referenced nowhere; no scheduled task issuing a delete at all.

---

## Consent & lawful basis

- Consent (or the alternative basis, e.g. legitimate interest) is **recorded per
  purpose** with a timestamp, notice version, and subject id — a single boolean
  `consented` cannot answer "to what, and when?" Withdrawal is as easy as
  granting and takes effect on the **next** read (check caches/materialized
  audiences that keep serving a withdrawn user).
- Non-essential analytics/marketing tags must not fire before consent where the
  regime requires it — verify *load order* in the actual page/bundle, not intent
  in a config file.
- **Children / age gates**, if the product plausibly reaches minors: is there an
  age signal, does it gate collection and personalization, and is it
  server-enforced rather than a dismissible client dialog?

---

## Analytics, telemetry & third-party SDKs

- **Allow-list, not deny-list**: events carry only explicitly permitted
  properties; a generic `track(event, {...props})` forwarding arbitrary objects
  will eventually ship PII. Redact at the emitter, not the dashboard. No
  identifiers or free text in URLs/referrers/screen names sent to vendors; no
  session-replay of forms with personal data unless masked.
- Every third-party SDK, pixel, error tracker, and LLM/vendor API is a data
  export — list them, note what leaves, and flag the ones with no documented
  processing agreement (the decision is the owner's). PII in logs/traces:
  `observability.md` and A09 of `security-appsec.md`.

---

## Dependency licenses & attribution

- Copyleft bites differently for **distributed** code (binaries/bundles, public
  packages, client-side JS) than for a server-only service — state the
  distribution assumption in the finding.
- Check for a license inventory (`license-checker`, `pip-licenses`, `cargo-deny`,
  SBOM) and an allowed-license policy enforced in CI; flag strong-copyleft
  (GPL/AGPL) or unlicensed dependencies in a permissive project, and missing
  NOTICE/attribution where required. The project's own LICENSE must not
  contradict its dependencies (cross-ref `docs-and-dx.md`).

---

**🚩 red flags**: fields collected with no reader; retention policy with no job;
erasure that misses indexes/caches/warehouse/vendors; DSAR with no timestamps or
SLA; suppression re-implemented per consumer; boolean consent with no purpose or
version; tags firing pre-consent; `track(event, props)` passthrough; PII in
analytics ids or URLs; vendor SDK with no data-flow note; GPL/AGPL or unlicensed
dependency in a distributed permissive project; a compliance claim no code
enforces.
