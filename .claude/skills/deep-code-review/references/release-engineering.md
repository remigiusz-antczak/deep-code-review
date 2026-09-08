# Release engineering — feature flags, progressive delivery & DORA (domain K)

Read this when the target ships a feature-flag system, a canary or blue-green
deploy pipeline, or a CI workflow that deploys — the **release** half of domain
K, sitting beside `dependency-currency-and-upgrades.md`'s **build/supply-chain**
half. `agentic-delivery`'s **Release** hat (`references/roles.md`, if that
overlay is installed) is the authoring-time discipline this file audits at
review time; this file stands alone for a plain review-only install with no
delivery overlay.

Before this file existed, a `FULL` review had no reference file behind domain
K's "release" promise at all — a permanently-on `// temporary` feature flag or
an undefined canary rollback produced zero findings, not because the target was
clean but because nothing in the skill looked.

---

## Feature-flag lifecycle

Not every flag is the same risk shape. Tag each by category before judging its
age (Fowler's four):

- **Release toggle** — hides incomplete/untested code on the path to
  production. Short-lived by design: "should generally not stick around much
  longer than a week or two." A release toggle older than that, with no removal
  date or tracking issue, is carrying-cost debt, not a feature.
- **Experiment toggle** — A/B or cohort routing. Lifetime tracks the
  experiment, not a fixed window; flag it only if the experiment itself looks
  abandoned (no metrics wired, no end date).
- **Ops toggle** — an operator kill-switch/degrade lever. Meant to be
  long-lived; the finding here is a *missing* one on a risky rollout, not an
  old one.
- **Permissioning toggle** — feature-by-segment (e.g. paying customers). Also
  long-lived by design; treat like any other authz surface (domain B) if it
  gates access rather than behavior.

**🚩**: a release-category flag with no removal date/issue, committed more than
two weeks ago (grep the flag's own git blame date, not "when I noticed it");
flags treated as inventory nobody counts — "savvy teams view feature toggles in
their codebase as inventory which comes with a carrying cost," and the classic
failure mode of stale toggle debt is a launched-and-forgotten switch nobody
dares remove.

## Canary / blue-green — claims need config, not prose

A PR description or runbook claiming "canary rollout" or "blue-green deploy" is
a claim like any other (principle 1) — it needs a citable mechanism, not a
label:

- **Canary**: traffic actually split to a small subset first (random sample,
  internal users, or a named demographic), with a **named halt metric** and an
  automatic-rollback path on regression of that metric — not only an error-rate
  check; a real "immune system" watches a business metric too, since a broken
  feature can be 200-OK and still wrong.
- **Blue-green**: two environments actually provisioned, the idle one tested,
  and cutover is a **router flip** — find the router/traffic-split config, not
  just the runbook step that says "flip."
- **🚩**: "canary" or "blue-green" in a PR title/description/runbook with no
  matching router, load-balancer, feature-flag-percentage, or traffic-split
  config anywhere in the diff or the referenced infra — this is prose, not a
  mechanism, and it is exactly as verifiable-or-not as any other unproven claim
  this skill already refuses to accept at face value.

## Rollback — tested, not merely asserted

`agentic-delivery` G8 already requires "rollback proven"; the review-side check
is the same evidence bar applied to a target with no delivery overlay: name the
rollback mechanism (router flip back, flag off, previous image/tag redeploy),
and find where it was **exercised** (a runbook drill, a game-day note, a past
incident) — not only documented. A rollback path that has never been run is
`unverified`, the same as an SLI defined only in a doc (`role-coverage.md`).

## DORA — measure it or say so

The DORA framework's own five metrics, in two categories, are the standard
vocabulary for whether the pipeline itself is healthy — **throughput** (change
lead time, deployment frequency, failed-deployment recovery time) and
**instability** (change fail rate, deployment rework rate — the share of
deployments that are unplanned but happen as a result of a production
incident). Do not compute a number from vibes:

- **Computable** — the repo/pipeline has the raw signal (deploy timestamps,
  commit-to-deploy linkage, incident/rollback records): compute it, cite the
  query or log source, `file:line` or command.
- **Not computable** — no CI-timestamp history, no incident log, no
  deploy-frequency record: report `UNMEASURED` (mirroring the skill's own
  `UNPRICED`/`UNVERIFIED` convention), never a fabricated number, and never a
  silent pass that reads as "fine."

---

**🚩 grep**: `feature.?flag`/`FF_`/`toggle` definitions with no adjacent removal
date, ticket reference, or category comment; `canary`/`blue.?green`/`rollout` in
prose (PR body, runbook, `README`) with no matching weight/percentage/router
config in the diff; a rollback section in a runbook with no evidence it was ever
run (no drill note, no incident reference); a CI/CD workflow that deploys with
no deployment-frequency or lead-time signal anywhere (no tagged releases, no
deploy-event log) — DORA is structurally `UNMEASURED` for that pipeline, and
that absence is itself worth naming once, not per-PR.

## Cross-references

- `dependency-currency-and-upgrades.md` — the other half of domain K (build,
  supply chain, safe version bumps); this file never restates it.
- `agentic-delivery`'s `references/roles.md` **Release** section (if that
  overlay is installed) — the authoring-time counterpart: tag a flag's category
  and set its removal date **when it is added**, not only when a later review
  finds it stale.
- `role-coverage.md` **Platform / DevOps / SRE** lens — SLI/SLO/error-budget/
  burn-rate, the reliability contract a release ships into.
- `docs/standards-index.md` — DORA, feature-toggle, canary, and blue-green
  citations with fetch dates.
