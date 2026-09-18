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

## Resilience is exercised — chaos engineering

Reliability claims are verified the way rollback is (above): a **chaos-engineering** exercise
states a **steady-state hypothesis** ("checkout success stays above 99% if a cache node dies"),
injects the fault in a **blast-radius-limited** scope (one instance, one AZ, a dependency timeout —
in a controlled window, staging before prod), and confirms the hypothesis held. A DR / failover /
autoscaling / rollback path with **no exercise** — no game-day, no injected-failure drill, no past
incident that ran it — is `unverified`, not proven: a documented runbook is a hypothesis until run.
Scope every experiment so a failed hypothesis cannot itself cause the outage it was testing for.

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

## Measure the flow before adopting a platform or a second methodology

The DORA metrics above say whether the pipeline is healthy; a second, cheaper set says where the
**iteration loop** hurts day to day — **time-to-green** (push → all checks pass), **queue / runner
wait**, and **rerun / flake rate**. These are **not** DORA metrics; apply the same p50/p95
discipline to them (an average hides the tail). Before adopting a build/merge platform (a merge
queue, a remote-cache or CI vendor) or a **second delivery methodology**, **measure the current
flow** on both sets, **attribute the p95 to a stage** (which job, which wait), and take the
**cheap fix first** — cache a step, shard a slow suite, cancel superseded runs, fix the top flaky
test. A tool bought before the bottleneck is measured usually moves a number you were not blocked
on.

- **The adoption bar is a question, not a vibe:** *"which measured metric does this platform move,
  and by how much?"* No number, no adoption — route the spend to the owner **with** the
  measurement (`agentic-delivery`'s Release gate when that overlay runs; the spend decision itself
  is the owner's, like the DORA *measure-it-or-say-so* rule above).
- **One delivery methodology per repo.** A second parallel process — a rival branching model or
  release ritual added "to go faster" — is coordination overhead priced as progress; a measured
  bottleneck justifies **switching** to a better one, never **running both**. Adopting a
  methodology is itself subject to the bar above.

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
- `branch-and-merge-hygiene.md` §5 — **merge trains** and the **red-base
  discharge** recipe: when the target is red and a green-base-required preflight
  blocks the fixes that would green it, the discharge is a merge train, not an
  `--admin` override. The merge mechanism lives there; this file never restates it.
- `agentic-delivery`'s `references/roles.md` **Release** section (if that
  overlay is installed) — the authoring-time counterpart: tag a flag's category
  and set its removal date **when it is added**, not only when a later review
  finds it stale.
- `role-coverage.md` **Platform / DevOps / SRE** lens — SLI/SLO/error-budget/
  burn-rate, the reliability contract a release ships into.
- `docs/standards-index.md` — DORA, feature-toggle, canary, and blue-green
  citations with fetch dates.
