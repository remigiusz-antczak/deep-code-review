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
  abandoned (no metrics wired, no end date). **And the assignment code itself is reviewable, not
  just the readout:** bucketing must be a **deterministic hash of a stable randomization unit + an
  experiment salt** (`hash(unit + experimentKey) % 100`), never `Math.random()` / session-scoped /
  re-rolled per request, and the unit stays constant across a logged-out→logged-in transition; the
  **exposure event fires at the point the variant actually changes rendered behavior**, not at
  assignment or page load (logging exposure for units that never reach the branched code dilutes
  the effect); and a **sample-ratio-mismatch (SRM) guard** — observed group sizes vs the intended
  split — is wired. SRM is a **high-sensitivity signal that something in the assignment/exposure
  pipeline is broken** — a symptom with several causes (telemetry filtering, trigger/exposure
  misconfiguration, or the bucketing itself), not a pointer to one, and it in most cases
  invalidates the results outright (Fabijan et al., KDD 2019; Kohavi et al., *Trustworthy Online
  Controlled Experiments* — by name). **Concurrent experiments on the same surface must be
  isolated:** two experiments that both mutate the same UI or flow with no layering and no mutual
  exclusion **confound** each other's readouts (a unit lands in both), and per-experiment bucketing
  + SRM — which only check one experiment's own assignment — won't catch it. The assignment infra
  must put overlapping experiments in **orthogonal layers** (Google's overlapping-experiment
  infrastructure uses "orthogonal diversion criteria for experiments in different 'layers' so that
  each event ... can be assigned to multiple experiments") or **mutually exclude** experiments that
  touch the same surface; an ad-hoc second experiment bolted on with neither is a code-side finding.
  Read-side validity (peeking, always-valid bounds) stays in `growth-analytics`; interpreting the
  effect over time (**novelty/primacy**) and correcting across many metrics (**multiple-comparison /
  false-discovery**) are read-side statistical analysis too — not the code side covered here.
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

**Flag evaluation (runtime), not just lifecycle:**
- **Pin the evaluated value once per logical request / transaction.** Re-evaluating the same flag
  mid-request — across async continuations, retries, or separate service calls in one operation —
  can render a **composite of both code paths** in a single response. This is a config-read
  *consistency* bug, not a data race (nothing is mutated — distinct from the check-then-act TOCTOU
  in `domain-checklists.md` / `concurrency-shared-state.md`). It is the **complement, not a
  contradiction,** of caching the flag *fetch* with a TTL (`performance-db-cost.md`): cache the
  fetch, but **pin the evaluated value** for the life of the request and pass it down rather than
  re-reading — the same shape as the lifetime-mismatch rule in `concurrency-shared-state.md`
  (thread a per-run value as a parameter).
- **Set the provider-unreachable default per flag category, and disambiguate "closed."** When the
  flag service is unreachable the code takes a default, and **fail-open is the bug for a risky or
  incomplete feature** exactly as a fail-open rate-limiter store is (`security-appsec.md` — the
  store-unreachable-defaults-open case). For a flag, "closed" is ambiguous: a **release toggle**
  closed = the *old code path* (safe), but an **ops kill-switch**'s safe default is *engaged*
  (feature degraded), not disengaged. Name the safe default **per category**, so an outage
  neither silently enables a half-built feature nor disables a safety lever.

## Canary / blue-green — claims need config, not prose

A PR description or runbook claiming "canary rollout" or "blue-green deploy" is
a claim like any other (principle 1) — it needs a citable mechanism, not a
label:

- **Canary**: traffic actually split to a small subset first (random sample,
  internal users, or a named demographic), with a **named halt metric** and an
  automatic-rollback path on regression of that metric — not only an error-rate
  check; a real "immune system" watches a business metric too, since a broken
  feature can be 200-OK and still wrong. The halt metric must be **partitioned by
  the canary cohort** (`service.version` or an equivalent tag) — an unpartitioned
  metric blends canary and baseline traffic and can never regress-check
  (`observability.md`, telemetry resource identity).
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
autoscaling path with **no exercise** — no game-day, no injected-failure drill, no past incident
that ran it — is `unverified`, not proven, exactly as the Rollback section above holds: a
documented runbook is a hypothesis until run.
Scope every experiment so a failed hypothesis cannot itself cause the outage it was testing for.
A game-day / drill also loses evidentiary value as the code drifts from what it validated: **date it**
like the backup-restore drill (`observability.md`), and flag one with **no re-run since a material
change to the exercised path** as **stale, not proof** — extending the Rollback section's exercise
bar to a recency bar, the same "a green run is a sample, not a proof" discipline `testing-and-evals.md`
applies. Exercising the infra path is also not a substitute for a repo-owned regression test on the
fallback branch's output (`testing-and-evals.md`).

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

Beyond delivery throughput, **developer productivity and experience are multi-dimensional** — the
**SPACE** and **DevEx** frames span satisfaction/well-being, performance, activity, communication,
and efficiency/flow, precisely because any single proxy (lines of code, commit or PR count, story
points) is gameable and misleads. A review that reduces "productivity" or "velocity" to one number
is the finding — the same false-precision bar as a composite score that sums heterogeneous
constructs (`data-quality.md`). Name what a metric can and cannot support, and **route a
people-performance judgement to the owner** — never assert it from repo activity.

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

## Signed releases — a consumer-verifiable signature, not just build provenance

Distinct from build provenance / attestation (SLSA), which `infra-iac-containers.md` covers as a **deploy-side**
gate the team verifies on its *own* pipeline: does the release process also **produce a signature a downstream
consumer can check**? A GitHub Release, package publish, or image push should ship a signature next to the
artifact — cosign / keyless Sigstore (`*.sigstore` / `*.sigstore.json`), `npm publish --provenance`, PyPI attestations (PEP 740, produced under Trusted Publishing), a GPG-signed tag or `*.asc` / `*.sig`, or a SLSA provenance file (`*.intoto.jsonl`) attached
as a release asset. OpenSSF Scorecard's Signed-Releases check is **"Risk: `High` (possibility of installing
malicious releases)"** and "tries to determine if the project cryptographically signs release artifacts"
("Signed releases attest to the provenance of the artifact"). A project can have SLSA build provenance
internally yet attach **no** consumer-verifiable signature to what it ships — that gap is the finding. (`security-appsec.md` A03 poses the same producer-side question in one line — *is a released artifact signed, or only checksummed over the same channel it ships on?* — this section is its depth.)

- **Find the signature artifact next to the release**, and confirm the publish job actually runs the signing
  step — a documented "we sign our releases" with no signing step in the actual `release` / `publish` workflow
  is not signing. And presence is not validity — a signature a consumer cannot chain to a trusted key is
  the producer-side echo of "generated provenance is not verified provenance" (Scorecard's own check "does
  not verify the signatures").

- **A valid signature proves who signed, not where the build ran.** A GPG-signed tag or a cosign/Sigstore
  signature satisfies the check above even when the actual build, tag, and publish steps all ran on a
  maintainer's own laptop rather than a hosted build platform — the check observes the identity that signed,
  never the machine the artifact was built on. A stolen publish credential or a compromised workstation
  produces an artifact that still tags, signs, and verifies cleanly, because the compromise sits upstream of
  the cryptography the check re-derives. This is the producer-side half of the question `security-appsec.md`
  poses on the verify side — its L1/L2/L3 build-provenance ladder (depth there, not restated here)
  presupposes an answer to *where the build ran*, which a bare signature check never asks. Before crediting a
  release with any level above the trivial-to-forge provenance-exists floor, confirm the publish/release job
  actually ran on hosted CI, or a recognized hosted-builder integration — GitHub Actions OIDC `npm publish
  --provenance`, PyPI Trusted Publishing — not a local `npm publish` / `twine upload` / manual `git tag` +
  upload, by reading the workflow run, not the signature.

**🚩**: a Release/publish with no signature, attestation, or provenance asset; a signing step present in docs
but absent from the workflow that ships the artifact; a signature present but not validatable against a
trusted key; a release credited with a build-provenance level despite no publish/release job in
`.github/workflows/` (or equivalent CI config) — just `RELEASING.md` / `CONTRIBUTING.md` or a `Makefile`
target a human runs by hand (`npm publish`, `twine upload`, `git tag -s` + manual asset upload).

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
