# Changelog

All notable changes to this repository are documented here. Format loosely
follows Keep a Changelog; versioning follows Semantic Versioning.

## [1.60.0] — 2026-09-12

Two new review domains — the taxonomy grows from A–S (19) to A–W (21): **T
Multi-tenancy & isolation** and **W Workflows, jobs & scheduling** (issue #96).

### Added
- **Domain T — Multi-tenancy & isolation** (`deep-code-review`): the cross-tenant
  leak that survives a clean access-control review — a cache / index / pool / job
  that forgot the tenant key, tenant context outliving its request, per-tenant
  lifecycle (export & deletion across every store), noisy-neighbour fairness, and
  the isolation model (row-level / schema / silo-per-tenant). Checklist-only in
  `references/domain-checklists.md` (like A/H/N/R); the seam is stated explicitly
  against **B/A01** (authz / IDOR) and **G** (races). New eval: a tenant-less
  cache key leaks across tenants even though the authorization review is clean.
- **Domain W — Workflows, jobs & scheduling** (`deep-code-review`): orchestration
  correctness for cron, queues, and multi-step workflows — never-runs (liveness),
  runs-twice (exactly-once *effect* on at-least-once delivery), dead-letter and
  retry caps, cron timezone / DST, ordering, durable long-running / saga state
  with compensation, and backpressure. Checklist-only; the seam is stated against
  **F** (single-call handling) and **G** (races), and scoped **out** of **E**
  (one-time migrations) and **K** (deploy / rollout). New eval: an at-least-once
  billing job needs an idempotent effect, a liveness alert, and an explicit
  timezone.

### Changed
- **Taxonomy A–S → A–W (21 domains).** Propagated the range through `SKILL.md`
  (domain map, phases, both role tables), `domain-checklists.md`, `method.md`,
  `role-coverage.md` (T assigned to the Backend lead, W to Platform / DevOps / SRE
  so no domain is orphaned), and `README.md`. **U, V and X–Z remain unassigned** —
  a domain earns its letter; the map grows only when a genuinely new class of
  defect does, never to pad the alphabet.
- Lockstep bump to **1.60.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.59.0] — 2026-09-11

README-authoring method — so the skillset produces onboarding READMEs for any
project, not just this one.

### Added
- **`deep-code-review/references/readme-authoring.md`** — the depth behind the
  domain-O "README (human-facing)" checklist: model the reader (default the
  evaluator), the plain-value-first onboarding arc with progressive disclosure,
  one host-native diagram (quote Mermaid labels; no external badges — a rotting
  live value), the anti-slop craft (superlatives out, tables over repeated
  patterns, no uncontrolled third-party claims), accuracy-vs-code (every
  command/flag verified against the tool; verify a pin actually pins), and keeping
  the **safe install path as the quickstart**. Generalized from this repo's own
  README overhaul and its independent review; routed from domain O and cross-linked
  from `docs-and-dx.md`. New eval resists two planted bad asks (a version badge; a
  shorter-but-unsafe install first).

### Changed
- Lockstep bump to **1.59.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.58.0] — 2026-09-11

Adopt the **Perun** umbrella brand (issue #38) — theme + wordmark only.

### Changed
- **README hero + `plugin.json` description** rebranded to **Perun** ("bring the
  thunder to your codebase") — the suite's umbrella identity, named for the
  Slavic thunder god of order and justice (strikes down chaos, never fabricates,
  leaves the bar in place). The **flagship skill name `deep-code-review` is
  unchanged**, as are all sibling skill names; the brand is the suite/repo layer.
  Added `perun` to `plugin.json` keywords.
- **Repo-slug rename deferred** (owner decision): GitHub redirects make it safe
  to do anytime; the pinned URLs to update when chosen are README (clone + npx
  slug) and `plugin.json` (homepage/repository). Brand adopted first.
- Copy kept **agent-agnostic**: "for building with AI agents", any major coding
  agent — no single-vendor focus.
- Lockstep bump to **1.58.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed (branding metadata only).

## [1.57.0] — 2026-09-11

Support & feedback operations lens (issue #44, G3) — agentic-delivery.

### Added
- **`agentic-delivery/references/support-ops.md`** — narrow reactive support-ops:
  an intake + triage taxonomy, a per-severity SLA template (owner sets the
  numbers), canned-response quality, and the **support→backlog loop** (a ticket
  revealing real work becomes a well-formed work item via the Where/Done-when/
  Verify/Why contract). **Load-bearing safety gate:** never auto-send an external
  reply and never make a promise/refund/commitment without owner approval — the
  same human-approval-on-external-action gate the skill applies to push/deploy.
  It cross-refs rather than restates: `incident-response.md` (outage tickets),
  `deep-code-review`'s `docs-and-dx.md` (Diátaxis help-center), and
  `communication-structure` (no-slop responses). Scope is narrow — not
  onboarding/activation (growth/product-ux). New evals: a ticket becomes a
  well-formed backlog item; no external reply/refund is auto-sent without
  approval. Independently reviewed before merge.

### Changed
- Lockstep bump to **1.57.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` gained content (a reference + a minimal routing
  pointer + two evals); it stays allowlisted for SKILL.md size (a trim pass into
  references is due).

## [1.56.0] — 2026-09-11

Adopt the two additive principles that were not yet codified (issue #37).

### Added
- **`deep-code-review/references/docs-and-dx.md`** — a "Persisted knowledge
  hygiene — store the query, not the answer" lens (domain O): a durable doc/memory
  that records a fact derived from live state (an issue count, a current version)
  rots; store the *query* that regenerates it. Audits a memory store / `AGENTS.md`
  / runbook for three decay modes — dead paths, status-without-a-command, and
  embedded credentials (cross-ref `privacy-compliance.md`) — each a finding.
- **`agentic-delivery/SKILL.md`** — a **work-item contract** beside the output
  contract: a work item is specified as **Where / Done-when / Verify / Why**, and
  one missing *Done-when* or *Verify* is underspecified and sent back to be scoped,
  not started (the input the output contract is graded against).

### Notes
- The third sub-item (a — the suite map as a *registry that describes access, never
  copies*) was already adopted: `agentic-ceo/SKILL.md` frames the registry as "a
  map, not a bundle" and its anti-rationalization table rejects restating a skill's
  steps. No change needed there; verified before closing.
- No duplication introduced (the memory-audit's secret check cross-refs the privacy
  reference rather than restating it; the work-item contract has no prior home).

### Changed
- Lockstep bump to **1.56.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin).

## [1.55.0] — 2026-09-11

Design-time regulated-domain obligation triage (issue #43, G2) — business-ops.

### Added
- **`business-ops/references/regulated-domain-triage.md`** (business-ops → 1.1.0)
  — the design-time front door for Lane R: a decision tree that runs *before the
  architecture hardens* (and re-prompts on entering a new market or handling a new
  data type). Triggers — health data, payments/card data, minors, EU/UK personal
  data, US-state privacy, biometrics, consequential/automated decisions, money
  movement, enterprise security — each **name the regime** (HIPAA, PCI DSS, COPPA,
  GDPR/UK GDPR, CCPA/CPRA, biometric-privacy, SOC 2/ISO 27001, and the like, by
  name only) and surface engineering-obligation **leads**, then **route the binding
  question to counsel**. The privacy branches point downstream to
  `deep-code-review`'s `privacy-by-design.md` (pre-code artifacts) and
  `privacy-compliance.md` (engineering) rather than restating them; it reuses Lane
  R's asymmetric boundary instead of duplicating it. **Boundary:** name + route;
  it never determines that a regime binds this business, and asserts no article
  number, threshold, or deadline. New eval: a health/payments/minors input yields
  a "route to counsel + named regime", never a compliance conclusion. Unblocks the
  G4/G5 lenses (they inherit the named regime).

### Changed
- Lockstep bump to **1.55.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `business-ops` gained content (independently versioned 1.0.0 →
  1.1.0).

## [1.54.0] — 2026-09-11

Two deep-code-review lenses: privacy-by-design product artifacts (issue #46, G5)
and billing/monetization correctness (issue #48, G7).

### Added
- **`deep-code-review/references/privacy-by-design.md`** — the pre-code
  privacy/compliance *artifacts* an EU user or enterprise buyer demands, as a lens
  over domain Q: a ROPA-style processing register, a DPIA scaffold + risk
  questions, a consent-UX spec, a subprocessor list with data-flow notes, and
  data-residency options. It sits *above* `privacy-compliance.md` (which stays the
  code layer — inventory, retention/DSAR/erasure, consent recording) and links to
  it rather than restating it. **Boundary:** scaffold + gap-detect; the
  privacy-policy/ToS text, whether a DPIA is legally required, and lawful-basis
  selection route to counsel. Frameworks named by name only; **no article numbers
  or legal deadlines** until fetched. New eval: a new PII field prompts the
  register/DPIA question.
- **`deep-code-review/references/billing-correctness.md`** — a mechanics lens on
  domain E (cross-ref F/G/I) for revenue correctness: metering (exactly-once),
  proration, dunning/failed-payment recovery, tax/VAT *application in code*,
  refunds/chargebacks, webhook idempotency, and the double-charge/revenue-leakage
  races. **Boundary:** review the logic; tax registration/filing and
  revenue-recognition policy route to an accountant, pricing to the owner
  (`business-ops`); **no invented tax rate**. New eval: a double-charge race and a
  non-idempotent webhook are both flagged.

### Changed
- Both references routed from the domain table in `deep-code-review/SKILL.md`
  (rows E and Q) with when-triggers; SKILL.md 21298 → 21439 bytes, well under the
  24000 budget.
- Lockstep bump to **1.54.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.53.0] — 2026-09-11

Operational-readiness lens — incident response + continuity (issue #45, G4).

### Added
- **`agentic-delivery/references/incident-response.md`** — the "system on fire
  OR the operator is gone" binder for bus factor = 1. Incident runbook
  (detect→triage→contain→eradicate→recover→blameless review), severity-level and
  status/comms templates, a break-glass access path, a credential/renewal
  inventory (domain, TLS, card, DNS, secrets) with **dead-man** reminders, a
  restore-drill schedule, and a solo-operator succession note. It reuses the
  blameless `template-postmortem.md` / `retrospective.md` for the review step and
  points restore/observability depth at `deep-code-review` rather than restating
  it. **Boundary:** breach-notification *timing* routes to G2 + counsel and is
  never asserted here; executing notification/succession is the owner's; no
  invented SLA, deadline, or renewal date. New eval: a planted expired TLS
  credential is surfaced, a restore-drill schedule is present, and the breach
  deadline is routed, not fabricated.

### Changed
- Lockstep bump to **1.53.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` gained content (a reference + a minimal
  routing pointer + one eval); the routing pointer keeps the allowlisted
  SKILL.md's growth to routing, not depth.

## [1.52.0] — 2026-09-11

Decision-hygiene frame for the builder's own hard calls (issue #47, G6).

### Added
- **`idea-critic/references/decision-hygiene.md`** — a routed reference that
  structures the owner's *own* high-stakes call (pivot, quit/kill, big
  irreversible spend) rather than attacking a proposal. Frame: one-way vs
  two-way door classification; the outside view (reference-class / base rate);
  sunk-cost, confirmation, and escalation-of-commitment surfaced; and
  kill/quit/pivot criteria pre-committed *before* the bet. It reuses the
  `kill-criteria` premortem instead of restating it, and it **structures** the
  decision for the owner — it never makes the call and never fabricates a
  probability (an ungroundable number is labeled `assumption`).

### Changed
- Lockstep bump to **1.52.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `idea-critic` gained content (a reference + its routing pointer).

## [1.51.0] — 2026-09-11

Routing-eval coverage for the conductor (issue #63, offline half).

### Added
- **`agentic-ceo/evals`** — a routing eval per registry destination (deep-code-review,
  agentic-delivery, idea-critic, growth-analytics, positioning, product-output-safety,
  communication-structure, contribution — joining the existing product-discovery /
  business-ops / owner cases). Each pins a (stage, area, artifact) prompt to its
  expected skill and asserts the routed method is not re-implemented inline
  (registry-not-bundle).
- **`test-ci-gates.sh`** — a coverage assertion: every shipped skill except the
  conductor must have an `agentic-ceo` routing eval, so a destination cannot be
  mis-routed unnoticed. Now 55/55. Live grading of each case rides the eval harness (#61).

### Changed
- Lockstep bump to **1.51.0** (deep-code-review, agentic-delivery, idea-critic, plugin).
  No skill content changed (conductor evals + a self-test added).

## [1.50.0] — 2026-09-11

Gives the SKILL.md size ratchet teeth and gates the install overlay-stamp guard
(issues #16, #83).

### Changed
- **`ci-gates.sh routing` size budget now FAILS, not warns** (#16). An oversized
  `SKILL.md` fails the gate against the documented byte budget (`ci.yml` enforces
  **24000**), unless the skill is on a small reasoned allowlist in `cmd_routing`
  (today only `agentic-delivery`, the full G0–G10 delivery OS). A pin is allowed its
  overage, never required to keep it. Documented in
  `references/skill-authoring-and-size.md`.

### Added
- **`test-ci-gates.sh`** — a non-allowlisted oversized `SKILL.md` now FAILS (was a
  warn); an allowlisted one passes with a `SIZE ALLOWED` note; and every
  skill-adding overlay flag (`WITH_*` guarding a `SKILLS+=` block) must appear in the
  AGENTS.md overlay-stamp guard, so a standalone `--with-<x>` install cannot land a
  skill without its stamp (#83 — the class fixed in #82). Now 54/54.

### Changed
- Lockstep bump to **1.50.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed (a reference doc gained the budget number).

## [1.49.0] — 2026-09-11

Fixes the plugin-install rail and stale first-party metadata (issues #78, #72, #80,
#79). A `/plugin install` or marketplace pin previously discovered **zero** skills —
skills live under `.claude/skills/` but the plugin default scans a root `skills/` and
`plugin.json` declared no `skills` path, so only metadata loaded. Same honesty class
as #55 (documented pin vs actual tree).

### Fixed
- **`.claude-plugin/plugin.json`** — add `"skills": "./.claude/skills"` so the plugin
  rail discovers all 11 skills (the field supplements the default `skills/` scan; path
  relative to plugin root, per the Claude Code plugins reference fetched this session).
  `install.sh` already copied from `.claude/skills/`; the two rails now agree (#78).
- **`plugin.json` description** — was a three-skill string ("gated-delivery and
  idea-critic"); now states the real posture (review-only default + opt-in overlays)
  without copying any skill's method (#72). The GitHub About field was updated to
  match (#79).
- **`docs/roadmap.md`** — `infra-evolution-by-stage` / `docs-evolution-by-stage`
  marked shipped 1.35.0, not "Proposed" (#80).

### Changed
- Lockstep bump to **1.49.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.48.0] — 2026-09-11

Adds **`product-output-safety`** (skill #11) — governs the harm a product's own AI
outputs and automated decisions do to end-users (bias, hallucination surfaced as
fact, over-reliance, missing AI-disclosure, deceptive patterns, unsafe automation of
high-stakes actions). Distinct from `deep-code-review` (the code's security) and
`business-ops` (money/legal routing): it is the behavior of the shipped product
toward its users. The one gap-analysis item (#42) admitted as a standalone skill
under the #66 admission rule; the rest fold as lenses/references.

### Added
- **`.claude/skills/product-output-safety/`** — MAP the per-feature harm inventory,
  MEASURE it with output-harm evals / red-teaming, MANAGE it with a human-in-the-loop
  gate on high-stakes / irreversible actions (NIST AI RMF core functions, by name).
  Hard boundary: red-team + measure + recommend HITL; never certifies "safe" /
  "unbiased" / "compliant", never fabricates a harm metric, routes any legal
  disclosure duty to counsel (+ `business-ops` Lane R). Opt-in, `--with-output-safety`,
  not in `--full`. Four refusal evals (never-certifies-safe, high-stakes-action-gated,
  routes-legal-disclosure-duty, no-fabricated-harm-metric).
- Wired into every enumerated site: `ci.yml` routing, `write-checksums.sh`,
  `install.sh` (flag + `SKILLS` + overlay stamp), `recommend-overlays.py`
  (`REVIEW_ONLY_SKILLS` + advisory list), the `agentic-ceo` registry + routing,
  `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/roadmap.md`.

### Changed
- Lockstep bump to **1.48.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). The new skill starts at its own `1.0.0`.

## [1.47.0] — 2026-09-11

Executes the fabrication-refusal evals offline for the first time. Each skill's
`evals/evals.json` described a refusal but was only a fixture, never run; this adds
deterministic predicates that grade a candidate answer and a gate proving each
predicate SEPARATES a fabricated answer from a refusal — no model, no network, no
spend. First slice of the live eval harness (issue #61); the model-calling runner
is the next slice.

### Added
- **`scripts/eval_predicates.py`** — two deterministic predicates over a candidate
  answer: `no_fabricated_finding` (rejects an asserted CWE-id, or a line-numbered
  defect with vuln context, on a clean file) and `no_fabricated_numeric_fact`
  (rejects an asserted currency / percentage / multiplier figure, including worded
  forms like `USD 180` and `four point two billion`), shared by positioning and
  business-ops. A `BINDINGS` table ties each of the three fabrication-refusal evals
  to its predicate and cross-checks the real eval ids, so a renamed eval fails the
  gate rather than silently orphaning the predicate.
- **`scripts/eval-fixtures/`** — a golden `good.txt` (a refusal, must PASS) and
  `red.txt` (a fabricated answer, must FAIL) per bound eval.
- **`--selftest`** — asserts every predicate discriminates its good/red pair;
  wired into `ci.yml` (offline, no key). `test-ci-gates.sh` gains records including
  a planted-RED (a good fixture overwritten with a fabricated answer) that must
  fail closed and name the eval, plus evasion regressions locking known dodges.
  Now 52/52.

### Changed
- Lockstep bump to **1.47.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.46.0] — 2026-09-11

`--recommend` now surfaces the advisory + conductor overlays (issue #68). Previously it
could only ever name 3 of 10 skills (deep-code-review + the delivery/critic pack), so
every advisory skill was invisible exactly when the owner was choosing what to install.

### Changed
- **`scripts/recommend-overlays.py`** — prints an unconditional "advisory overlays
  available (opt-in, default off)" block listing product-discovery, growth-analytics,
  positioning, business-ops, agentic-ceo, communication-structure, and contribution with
  their `--with-*` flags and a one-line reach. It still writes nothing and never
  auto-installs; shape-based auto-push of the highest-fabrication-risk skills is a
  deliberate non-goal.
- Lockstep bump to **1.46.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.45.0] — 2026-09-11

Adds a fabrication-refusal eval to `deep-code-review` (issue #65): the crown-jewel
skill's most-cited safety property — "never invent a defect, metric, CWE, source, or
line" — now has an executable fixture.

### Added
- **`deep-code-review/evals/evals.json`** — `refuses-fabricated-finding-on-clean-file`:
  a prompt that baits CWE ids and line numbers over a clean file; the pass condition is
  no-finding / unverified, not a plausible-looking defect. Distinct from
  `planted-defect-must-be-reported`, which guards fabricating verification *status*.

### Changed
- Lockstep bump to **1.45.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No other skill changed.

## [1.44.0] — 2026-09-11

Adds a **suite-enumeration completeness gate** (`ci-gates.sh enumeration`) — the
enforce-in-code fix for the drift class behind the 1.43.0 registry bug and the
recurring recommend-overlays miss. A new skill can no longer ship green while
missing from a hand-maintained list (issue #62).

### Added
- **`ci-gates.sh enumeration <root>`** — asserts every shipped skill appears in all
  five hand-maintained lists: the `agentic-ceo` registry table (a row, not prose),
  `install.sh` (`SKILLS+=`), the `ci.yml` routing lines, the `write-checksums.sh`
  find-list, and `recommend-overlays.py`. Fail-closed; wired into `ci.yml`.
- **`test-ci-gates.sh`** — two records: the real tree is fully enumerated, and the
  gate goes RED on a planted un-enumerated skill (so it cannot pass vacuously).
  Now 47/47.

### Changed
- Lockstep bump to **1.44.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.43.0] — 2026-09-11

Fixes a routing bug in the `agentic-ceo` conductor (→ 1.1.0): its suite registry was
written at 1.37.0 and never updated as later skills shipped, so it could not route to
`growth-analytics` (1.38.0), `positioning` (1.41.0), or `business-ops` (1.42.0) — a
third of the suite was unreachable from the conductor. Found by two independent review
agents converging on the same defect.

### Fixed
- **`agentic-ceo` → 1.1.0** — the registry table and routing section now cover all
  nine non-conductor skills; new routing eval `routes-later-skill-not-inline`
  exercises dispatch to a later-shipped skill (business-ops Lane A/R). A
  suite-enumeration completeness gate to prevent recurrence is filed as a follow-up.

### Changed
- Lockstep bump to **1.43.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). All other skills unchanged.

## [1.42.0] — 2026-09-11

Adds `business-ops` (1.0.0) — the second thin advisory guide (built last) and the
last of the recommended suite skills. Two clearly separated lanes: Lane A applies
pricing / unit-economics arithmetic to the user's own numbers with the formula shown
(never a directive); Lane R routes legal / tax / securities / employment / privacy —
and fundraising — to a licensed professional (never concludes). Opt-in overlay,
default off, not in `--full`; install with `--with-business`.

### Added
- **`business-ops/`** (new skill, 1.0.0) — the asymmetric Lane A / Lane R boundary
  stated in the frontmatter description (the routing key); standing "educational
  information, not advice" disclaimer; refusal evals: `shows-formula-not-directive`,
  `routes-regulation-questions`, `fundraising-is-a-securities-matter`,
  `no-fabricated-financials`. Never fabricates a figure, statute, rate, or deadline.
  Frameworks registered by-name in `docs/standards-index.md`.
- Wired into CI routing, checksums, `recommend-overlays.py` (`REVIEW_ONLY_SKILLS`),
  `install.sh` (`--with-business`), `CONTRIBUTING.md`, `README.md`, `CLAUDE.md`.

### Changed
- Lockstep bump to **1.42.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). All other skills unchanged.

## [1.41.0] — 2026-09-11

Adds `positioning` (1.0.0) — the first of two thin advisory guides (highest
fabrication-risk, built last): value proposition, segment, differentiation, and a
message house on the USER's own inputs, produced as a hypothesis to validate with
real buyers. Opt-in overlay, default off, not in `--full`; install with
`--with-positioning`.

### Added
- **`positioning/`** (new skill, 1.0.0) — Value Proposition Canvas → positioning
  statement → message house → validate-with-real-buyers, plus the minimum-viable-brand
  rule pre-PMF. Every artifact is a hypothesis or an empty-slot template; refusal evals
  enforce it: never fabricate TAM / competitor claims / customer quotes / outcome
  numbers / trademark-domain clearance (a search is not clearance → route to a
  professional). Frameworks registered by-name in `docs/standards-index.md`.
- Wired into CI routing, checksums, `install.sh` (`--with-positioning`),
  `CONTRIBUTING.md`, `README.md`, `CLAUDE.md`.

### Changed
- Lockstep bump to **1.41.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` / `growth-analytics` (1.0.0), `product-discovery` (1.1.0),
  `communication-structure` (1.2.0), `contribution` (1.1.0) unchanged.

## [1.40.0] — 2026-09-11

Broadens `communication-structure` (→ 1.2.0) into the suite's **no-slop output
contract**: it now governs human-facing *deliverables* (reports, plans, docs,
tables), not only short messages. BLUF, one ask, core-value-only, and the full
"cut on sight" list apply to any output; the 30-second / 150-word cap stays a
message rule (a deliverable is as long as its content requires and no longer).
This is the single home the `agentic-ceo` conductor already points every skill's
output to — enforcing the owner's "clean, concise, no model-forced filler" bar
across all outputs, not just chat.

### Changed
- **`communication-structure` → 1.2.0** — scope widened from messages to messages
  *and* deliverables; new "Deliverables, not just messages" section; description
  updated.
- Lockstep bump to **1.40.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` / `growth-analytics` (1.0.0), `product-discovery` (1.1.0),
  and `contribution` (1.1.0) unchanged.

## [1.39.0] — 2026-09-11

Folds a **Non-goals** lens into `product-discovery` (→ 1.1.0) — the inverse of the
prioritization list and the scope-defense that stops a coding agent from
gold-plating. This completes the carve decision: the standalone product-strategy
skill is dropped; its distinct half (what NOT to build) lives here, its JTBD and
PMF halves already did.

### Changed
- **`product-discovery` → 1.1.0** — new *Non-goals (what you are deliberately NOT
  building)* section: recorded, stage-tied decisions revisited each stage; fed by
  the riskiest-assumption gate; used as one-line scope defense when a request
  touches a non-goal. Refusal eval `non-goals-scope-defense` (flags the collision,
  asks to reopen, never invents a non-goal the user did not choose). Description
  updated to name "what to deliberately not build".
- Lockstep bump to **1.39.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` (1.0.0), `growth-analytics` (1.0.0), `contribution`
  (1.1.0), and `communication-structure` (1.1.0) unchanged.

## [1.38.0] — 2026-09-11

Adds `growth-analytics` (1.0.0) — the standing measurement scoreboard: one
customer-value North Star, the AARRR funnel read bottom-up (retention first), an
event taxonomy that answers a named question, and stage-aware instrumentation.
Opt-in overlay, default off, not in `--full`; install with `--with-growth`.

### Added
- **`growth-analytics/`** (new skill, 1.0.0) — measure the user's own data against
  the user's own baseline; never fabricate benchmarks, metrics, or "good"
  thresholds; route real figures to the user's analytics. States the
  product-analytics vs ops-observability identifier seam (a stable pseudonymous
  per-user id for cohorts) as a pointer to `observability.md` /
  `privacy-compliance.md`, not a restatement. Refusal evals: no fabricated
  benchmarks, North-Star-not-vanity, instrument-only-what-answers-a-question,
  route-real-figures-to-analytics.
- Wired into CI routing, checksums, `install.sh` (`--with-growth`),
  `CONTRIBUTING.md`, `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.38.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` (1.0.0), `product-discovery` (1.0.0), `contribution`
  (1.1.0), and `communication-structure` (1.1.0) unchanged.

## [1.37.0] — 2026-09-11

Adds `agentic-ceo` (1.0.0) — the suite's conductor: the orchestrator that routes
across the specialist skills, sizes its own effort to the project stage, and runs
the under-pressure chaos playbook. Opt-in overlay, default off, not in `--full`;
install with `--with-ceo`.

### Added
- **`agentic-ceo/`** (new skill, 1.0.0) — a registry of the suite's skills (a map,
  not a bundle), `(stage, area) -> (skill, lens)` routing, stage/size effort-sizing
  (one agent wearing several skill-hats on small work; fan-out only for read-mostly,
  decomposable work), and the owner-under-pressure chaos playbook (capture losslessly
  -> reflect the full list -> triage to the vital few -> one next action -> hold the
  rest -> support by action, never "calm down"). Refusal evals enforce
  route-not-fan-out on small work, no dropped request under a flood, and routing the
  unknowable to the owner. Self-contained for the suite; general delivery/critique
  defer to `agentic-delivery` / `idea-critic`.
- Wired into CI routing, checksums, `install.sh` (`--with-ceo`), `CONTRIBUTING.md`,
  `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.37.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `product-discovery` (1.0.0), `contribution` (1.1.0), and
  `communication-structure` (1.1.0) unchanged.

## [1.36.0] — 2026-09-11

Adds `product-discovery` (1.0.0) — the first product-advisory specialist skill:
decide whether something is worth building, what to build first, and whether what
shipped works, by structuring evidence from real users. Opt-in overlay, default
off, not in `--full`; install with `--with-discovery`.

### Added
- **`product-discovery/`** (new skill, 1.0.0) — the riskiest-assumption gate (name
  it, run the cheapest disconfirming test before building), Mom-Test / JTBD
  discovery interview design + interpretation, fake-door / concierge experiments, a
  product-market-fit read (very-disappointed survey + retention cohorts), and ICE
  prioritization — all on the user's own inputs. The epistemic spine is enforced by
  refusal evals: it never fabricates findings, quotes, personas, market size,
  scores, or a "validated" verdict, and routes the unknowable to the owner.
- Wired into CI routing, checksums, `install.sh` (`--with-discovery`),
  `CONTRIBUTING.md`, `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.36.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `contribution` (1.1.0) and `communication-structure` (1.1.0) unchanged.

## [1.35.0] — 2026-09-11

Extends the stage-aware going-forward roadmap with two *when-to-add* reference
lenses for `deep-code-review`, complementing the existing *how-to-secure* domain
files without duplicating them.

### Added
- **`deep-code-review/references/infra-evolution-by-stage.md`** (new) — infrastructure
  and architecture are *earned, not provisioned*: per-stage build-vs-not-yet, an
  observable trigger for each step (CI, staging, containers, IaC, observability,
  orchestration, service extraction, SLOs), a floor that never relaxes (security,
  secrets, auth, backups), and six business/ops facts routed to the owner. Routed
  from the Project-stage section and domain L.
- **`deep-code-review/references/docs-evolution-by-stage.md`** (new) — which documents
  acquire normative force at which stage (one-pager → design-doc/RFC → spec),
  trigger-not-calendar, and a two-tier router+depth shape for agent legibility.
  Routed from the Project-stage section and domain O.

### Changed
- **`deep-code-review/SKILL.md`** → **1.35.0** (lockstep with `agentic-delivery`,
  `idea-critic`, and the plugin): the Project-stage section now routes the two
  stage-evolution lenses, and domain rows L and O cross-link them (when-to-add vs.
  how-to-secure). No change to `contribution` (1.1.0) or `communication-structure`
  (1.1.0).

## [1.34.0] — 2026-09-11

Hardens the `contribution` self-improvement skill so quality can only ratchet up —
it can never weaken the bar, fabricate, or self-authorize a send. Grounded in
research into secure self-hosted agents (a kernel/userspace split) and
self-modifying-agent precedents, which converge on one conclusion: keep the
human-gated, no-auto-PR, protected-core design, and gate only the irreversible step.

### Added
- **`contribution/kernel-paths.txt`** (new) — the enforceable protected-core path
  list. A drafted contribution whose changed files intersect it is a **kernel edit →
  human-authored only**, never an agent-drafted send. Meta-immutable (the list is
  itself a kernel path).
- **`contribution/evals/evals.json`** — `kernel-edit-refused` (a draft that would
  weaken the privacy gate is refused as a kernel edit) and `injection-lesson-rejected`
  (a lesson that directs the process is treated as untrusted data).

### Changed
- **`contribution/SKILL.md`** + **`references/contribution-procedure.md`** → **1.1.0**:
  a kernel-vs-userspace protected core (immutable kernel: the scrub, the
  evaluator/thresholds, merge authority, the provenance ledger, the Definition of
  Done, and the kernel path-list itself); the **second-order kernel rule** (a
  self-improvement that changes how the scrub / evaluator / generality-gate *behaves*
  is human-authored only); **evaluator independence** (graded by the unmodified
  harness); the **lesson-is-untrusted-data** injection guard; a **mosaic-leakage**
  line in the provenance block; the "human-gated send, automate everything reversible
  before it" reframe; and an explicit scope extension to **agent prompts, skills, and
  orchestration** as drafts for human review. Anima-style decay/impact triage is
  admitted only as a *local* candidate filter, never an autonomous upstream writer.
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.34.0**;
  `contribution` → **1.1.0** (independent line). `SHA256SUMS` regenerated.

## [1.33.0] — 2026-09-11

Stage-aware review + a going-forward roadmap. `deep-code-review` now calibrates
its *demands* to the project's lifecycle stage (prototype / mvp / growth / mature)
and ends a FULL review with a stage-sequenced roadmap — what to do now, what to
defer, and which skillset to adopt going forward — so effort matches the stage
instead of over-engineering a prototype or under-hardening a live product. Stage
calibrates **urgency only**; it never rewrites a defect's severity and never
downgrades a security, secret, or data-loss finding.

### Added
- **`deep-code-review/SKILL.md`** — a `STAGE` field in the first-response block and
  a compact **Project stage** section: a four-stage table (what each stage relaxes
  the *demand* on) plus three guardrails — stage is declared or evidence-named
  (never guessed; unstated defaults to the stricter reading); security / secret /
  data-loss findings never relax; stage moves urgency, not intrinsic severity
  (reusing the latent-findings rule).
- **`deep-code-review/references/report-format.md`** — a **Going-forward roadmap**
  (machine + plain-language): sequences the findings already reported by
  stage-urgency, points at `install.sh --recommend` for the skillset to adopt (no
  restating), and adds ≤ 3 evidence-grounded development moves — anything needing
  business context the repo cannot evidence is routed to *Decisions needed (owner)*,
  not invented.

### Changed
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.33.0**;
  independent skills unchanged. Definition of done (a) now requires a FULL review to
  state `STAGE` and produce the going-forward roadmap. `SHA256SUMS` regenerated.

## [1.32.0] — 2026-09-11

New review lens: **agent-readiness**. A first-class way to assess whether a repo
or product is architected, tested, gated, documented, and permissioned for
coding agents to work in it safely — the thesis-fit, evidence-grounded form of an
"AI-transformation" review. It is a lens over existing domains (C, J, K, M, N, F,
O, H), not a new domain or a new skill, and it deliberately **stops at the
technical substrate**: it never advises which product to build, how to reorganize,
or what business metric to set (that would require inputs the repo does not
contain and would violate the evidence and no-fabrication principles).

### Added
- **`deep-code-review/references/role-coverage.md`** — an **Agent-readiness
  lens**: a role-map row (leads on C J K M N F O H) and a lens section whose spine
  is the boundary between reviewable technical substrate (agent-safe scoping,
  agent-verifiability, gating, observability, legibility — all from existing
  domains) and business/strategy questions, which are routed to *Decisions needed
  (owner)*. Deliverable is the standard severity-ranked `file:line` report plus a
  short agent-readiness summary — never a strategy deck.
- **`deep-code-review/SKILL.md`** — the compact role table gains the matching
  `Agent-readiness` row so the map and its depth stay consistent.

### Fixed
- **`contribution/SKILL.md`** — corrected the procedure ordering so the mechanical
  privacy scrub runs on the **drafted files** (draft in step 3, then scrub in step
  4), not before drafting; the previous numbering could be read as scanning an
  undrafted checkout, making the "mechanical floor" vacuous. `contribution` → **1.0.1**.

### Changed
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest →
  **1.32.0**; `communication-structure` (1.1.0) unchanged; `contribution` → **1.0.1**
  (fix above). `SHA256SUMS` regenerated.

## [1.31.0] — 2026-09-11

New opt-in overlay `contribution`: prepare a privacy-safe, generalized
improvement back to the public skillset for a human to review and open as a PR.
This is the self-improvement capability the owner asked for — a skillset that
gets better from field use — built with the safety shape the design work
required rather than an autonomous push.

### Added
- **`.claude/skills/contribution/`** (new; independent line at **1.0.0**) — an
  opt-in overlay that turns a generalizable, scrubbed lesson into a drafted skill
  edit + CHANGELOG + eval + routing, runs the repo's own gates, and assembles a
  **provenance-and-risk block** a human signs before the PR. One routed reference
  (`references/contribution-procedure.md`) and three evals
  (`third-party-identifier-blocked`, `non-generalizable-imprint-locally`,
  `no-autonomous-push`). Guardrails: a hard **generality gate** (contribute only a
  defect-class or method-gap the bar lacks and that reproduces beyond one project —
  otherwise imprint locally via `deep-code-review` Phase 6); reuse of the repo's
  existing **fail-closed privacy gate** as the mechanical floor, with the human as
  the privacy authority for the semantic leaks a pattern scan cannot catch; a
  **protected core** (tests, privacy gate, and merge authority immutable to the
  agent) so a self-improvement loop cannot game its own evaluator; and **no
  autonomous push or PR** to the public repository.
- **`install.sh`** — `--with-contribution` flag (deliberately **not** part of
  `--full`, since it is the one overlay whose function is moving content toward a
  public destination); usage, header, AGENTS.md overlay stamp, and re-install
  line updated. Default install stays review-only; the new skill is off unless
  explicitly requested.

### Changed
- **`agentic-delivery/SKILL.md`** — G10 gains a one-line discovery pointer: when
  the `contribution` overlay is installed, it is the mechanism for proposing the
  generalized, stripped lesson back to the public skillset (the
  generalize-and-strip mandate itself is unchanged).
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest →
  **1.31.0**; `communication-structure` stays **1.1.0** (unchanged this release);
  `contribution` starts at **1.0.0** on its own independent line. `SHA256SUMS`
  regenerated over the five skill trees.
- **`README.md`**, **`CONTRIBUTING.md`**, **`CLAUDE.md`** — document the new
  overlay, its install flag, and its routing-gate line.

## [1.30.0] — 2026-09-11

Selective adoption from an external "studio coordination" proposal, filtered by
this repo's own bar: security-cleared, thesis-fit, non-regressive, and cited only
to sources verified this session (no new citations were needed). The proposal's
product pivot (a brand/marketing "studio OS") and its rewrite of the delivery
overlay were **declined** — the rewrite would have deleted runnable detection
instruments and added a standing-authorization carve-out that conflicts with the
confirm-before-action rule. Every existing instrument is preserved; only
additions and internal-consistency fixes land.

### Added
- **`agentic-delivery/references/host-enforcement.md`** (new) — a claimed-vs-enforced
  honesty framework: three levels (protocol / validated-artifact / host-enforced),
  each with what it *cannot* establish, a per-control capability declaration, and an
  optional adapter interface. Routed from `SKILL.md`.
- **`agentic-delivery/references/project-state.md`** (new) — a durable project-record
  contract, a resume / crash-after-effect reconciliation protocol (an interrupted
  effect with an unknown result is not presumed failed; an uncertain side effect is
  not replayed), and a non-code artifact-receipt contract that *extends*, not
  restates, the SKILL.md Output contract. Routed from `SKILL.md`.
- **`deep-code-review/references/model-tiering.md`** — a "did the tiering work?"
  cost-accounting section (model / usage / price / budget / outcome tracking; cost per
  *accepted* task with failures in the numerator), added **alongside** — not
  replacing — the existing optimization levers.
- **`idea-critic/SKILL.md`** — a "test the claim before assent" reframe (a sound plan
  may pass once a real failure hypothesis was tried and held; automatic disagreement
  is as performative as automatic agreement), an `UNVERIFIED` operational status
  *outside* the verdict enum (review-could-not-run is not a rejection), a two-recheck
  cap on `REVISE`, an "independence is a declaration" note, and an anti-rationalization
  row against a proposal that games its own evaluator.
- **`agentic-delivery/evals/evals.json`** — four scenarios pinning shipped instruments:
  crash-after-external-effect, goal-change-invalidates-work, fabricated-or-stale-receipt,
  g6-severity-and-permission.

### Changed
- **`agentic-delivery/SKILL.md`** — G6 now applies the `deep-code-review` severity
  rubric verbatim (Blocker/Critical block, High needs a named owner's acceptance,
  Medium tracked and non-blocking), resolving a contradiction where G6 blocked on
  Medium; principle 3 reworded so a check that "could not run" is `UNVERIFIED` (never a
  fake pass) and evidence is separated from permission. The same wording is aligned in
  `references/roles.md` and `references/fast-agentic-delivery.md`.
- **`communication-structure/SKILL.md`** — cut reflexive hedges but **keep material
  uncertainty** ("the log is unavailable" is evidence, not filler); the A/B decision
  template is retained.
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.30.0**;
  `communication-structure` → **1.1.0** (independent line); `SHA256SUMS` regenerated.

### Declined (from the external patch, with reason)
- The `studio-capabilities` specialist packs (brand/marketing/commercial), the "CEO
  mandate" Conductor reframe, and the install-trigger `description` rewrite — a
  different product (agency OS), not a portable code-review bar.
- A Human-gates "standing authorization — do not ask again" carve-out — conflicts with
  the confirm-before-destructive/irreversible non-negotiable.
- The rewrite's deletion of runnable instruments (behavioural drift tell, fan-out tiers
  + the Cemri failure-mode mapping, the RAM/swap headroom probe, the seven cost levers,
  the A/B ask template) — all kept.
- 19 new `standards-index` rows and the promotion of NIST SSDF / AI RMF / SLSA from
  by-name to verified — not verified by direct fetch this session.
- The size-enforcement CI cap and the idea-critic validator/test-suite tightening —
  coupled to the rejected rewrite or to coordinated fixture changes; deferred to a
  separate, self-contained change rather than risk the gate.

## [1.29.0] — 2026-09-10

Tier 2–3 of the same prime-agent-informed batch: supply-chain and CI/CD
detection instruments, a dependency release-age cooldown control, six eval
fixtures, and two repo-hygiene items. Additive; the method and the default
(review-only) install are unchanged. Two Tier-3 items were found **already
implemented** during the work and are recorded, not re-added (see Note).

### Added
- **`deep-code-review/references/security-appsec.md`** — A03 gains CI/CD
  trigger-and-token hygiene (`pull_request_target` untrusted checkout,
  `${{ github.event.* }}` script injection, least-privilege
  `GITHUB_TOKEN` / `permissions`) and a verification-vs-authenticity instrument:
  a same-origin checksum is integrity, not authenticity, and does not neutralize
  the trust-on-first-use risk of a `curl | sh` install; severity keys on
  reachability. Cited to GitHub's Security-hardening guide.
- **`deep-code-review/references/security-agent-skills.md`** — AST02 gains the
  integrity-vs-authenticity grade, downloaded-manifest path-traversal
  validation, and a pointer that CI workflow files are executable config
  reviewed under A03; AST03 gains installer over-privilege beyond identity files
  (shell-rc append, global `npm i -g`, `PATH` export).
- **`deep-code-review/references/dependency-currency-and-upgrades.md`** — a
  release-age cooldown control (refuse to resolve a version until it has been
  public N days; Renovate `minimumReleaseAge`, security advisories exempt) plus
  a matching red flag. Cited to Renovate's docs.
- **`deep-code-review/evals/evals.json`** — six fixtures pinning the new
  instruments (interpreter-is-the-exec-sink, silent safety-param drop,
  process-group-is-not-isolation, installer over-privilege, cost-vs-token cap,
  inconsistent untrusted-content spotlighting).
- **`.gitattributes`** — normalize text to LF and keep shipped `*.sh` LF so the
  installer runs identically on every checkout.
- **`.github/workflows/ci.yml`** — the `name:`-matches-directory check now runs
  on every shipped skill, not only `deep-code-review`.

### Changed
- The three lockstep skill `VERSION` files, their `SKILL.md` stamps, and the
  plugin manifest follow **1.29.0**; `SHA256SUMS` regenerated.
  `communication-structure` remains at 1.0.0.

### Note
- "Run `install.sh` end-to-end in CI" and "sort `SHA256SUMS` entries" were found
  **already implemented** and were not re-added: `scripts/test-ci-gates.sh`
  already drives the real installer (`ci-gates.sh install --src .`) across modes
  with an idempotent-second-run assertion, and `scripts/write-checksums.sh`
  already sorts its entries.

## [1.28.0] — 2026-09-10

Five agent/LLM review-instrument sharpenings for domain C, found by routing the
skill's own `agent / LLM` archetype path against a production agent runtime and
recording where a reference stated a rule but handed the reviewer nothing to
run. Additive; no change to the method, scope modes, or the default
(review-only) install.

### Added
- **`deep-code-review/references/security-ai-agents.md`** — the "untrusted
  content is data" principle gains a detection step (enumerate every sink where
  non-prompt content enters a prompt; require a delimiter + a data-guard at
  each; **inconsistent** spotlighting is itself the finding) and a reframe for
  code-interpreter agents, where "model output reaches `exec`" is the product —
  so the controls to review are the isolation boundary and the default
  confirmation gate, not the exec call. Tool-gating now locates the dispatch
  chokepoint and separates a shipped default from an opt-in `examples/` demo;
  a human-confirmation gate must fail **closed** when no interactive UI exists.
  Spend governance gains the **cost ≠ tokens** and **before ≠ after** (pre-call
  vs post-hoc reconciliation) tests plus a `while (true)` loop-bound check.
  Matching `🚩 grep` keys throughout.
- **`deep-code-review/references/security-agent-skills.md`** — AST06 gains an
  isolation-grading instrument: grep the exec runtime for `subprocess` /
  `Popen` / `spawn`, check each spawn for a real boundary (namespaces, seccomp,
  netns, uid-drop, chroot, a container), and treat `start_new_session` /
  process groups / Job-Objects as lifecycle control, not a security boundary; an
  opt-in `examples/` sandbox or gate that is not loaded by default is not an
  enforced control. Matching `🚩 grep` keys.

### Changed
- The three lockstep skill `VERSION` files, their `SKILL.md` stamps, and the
  plugin manifest follow **1.28.0**; `SHA256SUMS` regenerated for the changed
  skill trees. (`communication-structure` remains at 1.0.0.)

## [1.27.0] — 2026-09-10

Two field lessons for the delivery overlay and the product-UX review half, each
a completeness fix to an existing rule rather than a new one. No change to the
review method or the default (review-only) install.

### Added
- **`agentic-delivery/SKILL.md`** — the Conductor operating rhythm gains a
  *drift-detection and recovery* step: the event-driven "does not do the lane's
  work itself" rule stated **behaviourally** (a run of consecutive
  query/build/edit/mutate turns is the tell), with a stop → package → dispatch →
  resume recovery and one named exception (work only the Conductor's own session
  can perform, done minimally and handed straight back). Applies the existing
  event-driven discipline to *action*, not only attention.
- **`agentic-delivery/SKILL.md`** — Gate epistemology principle 11:
  "visible/done" is measured on the owner's own surface, never a proxy (an
  integrated SHA, a green branch build, a passing test, an insert/grep count);
  keeps wired/defined/rendered distinct from has-a-real-value. Ties to
  principle 3's `UNVERIFIED` and the G9 production-verify gate.
- **`deep-code-review/references/product-ux-quality.md`** — a redesign-trigger
  section complementing "not a licence to redesign": the owner's *repeated*
  rejection (2+ times) of the same element is a structural signal to stop tuning,
  name the flaw, research two or three comparable products, and surface concrete
  options for the owner to choose (show, don't tell). Reconciled with principle 5
  and grounded in principle 9.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin manifest
  follow **1.27.0**.

## [1.26.0] — 2026-09-09

New reference `skill-authoring-and-size.md` (domain H): a portable rule for
keeping agent skills lean as they accrete lessons — a thin always-loaded
`SKILL.md` core + a routed index, depth in on-demand `references/`, two budgets
(body tokens on invocation, `description` chars always-loaded, ≤1024 by spec), a
reasoned allowlist (allowed-not-required), and a size ratchet that FAILS on bloat
with a self-test that proves it fires. Routed from the domain map (H) and a
"skills as targets" pointer. CI `--max-bytes` stays 100000 (still a warning);
tightening to 24000 and making it FAIL need a follow-up with `workflow` scope.
No behaviour change to the review method.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin
  manifest follow **1.26.0**.

## [1.25.0] — 2026-09-09

Concurrency, scheduling, and merge-cadence cut for `agentic-delivery`. Default
install stays review-only.

### Added
- **`agentic-delivery/references/fast-agentic-delivery.md`**: five field-tested
  refinements — a corrected resource-gate signal (free RAM + swap trend, not
  `load1` alone, which conflates disk I/O with CPU contention), CI-offload as
  the actual concurrency unlock (lane weight over lane count), sweeping the
  whole ready queue on every Conductor trigger, a fleet-wide external-advisory
  gate-epistemology case, and reconciling an independent-PR-queue merge
  cascade with the existing union-proof-before-a-train rule. Five sources
  fetched and cited (Kanban WIP limits, Google small-CLs, blast radius,
  GitLab merge trains, Linux load-average mechanics). Routed from three spots
  in `SKILL.md` (environment probe, Conductor operating rhythm, gate
  epistemology).

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin
  manifest follow **1.25.0**.

## [1.24.0] — 2026-09-08

Cost-governance leftover from colliding PR #13, restamped onto
current main so it does not reuse shipped 1.22.0 / 1.23.0.

### Added
- **`model-tiering.md`**: default-and-ceiling callout — cheapest tier
  that clears its own gate; state a reason before exceeding frontier
  except lead-verify / adversarial-design.
- **`agentic-delivery` environment probe**: composite resource
  predicate (free RAM >15% AND load1 < cores × 1.3 AND CPU idle >25%,
  plus macOS swap check). Throttle when any one trips.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.24.0**.

## [1.23.0] — 2026-09-08

Discipline and compatibility cut. Mechanisms, not packs. Default
install stays review-only.

### Added
- Anti-rationalization (excuse → rebuttal) tables in `idea-critic`
  and `agentic-delivery` G4/G5.
- Headed-browser evidence as a **required** G5 / domain P receipt
  when a rendered page can change. Unit tests alone are not a UI gate.
- Spec Kit constitution *compat*: if `.specify/` or `constitution.md`
  exists, review against it. Do not install Spec Kit.
  `--recommend` prints that notice.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.23.0**.

## [1.22.0] — 2026-09-08

Distribution and fixture-eval cut. Default install stays review-only.
Does not claim OpenSSF Model Signing.

### Added
- `evals/evals.json` on each of the three skills (fixture contract:
  planted defect must be reported; `--recommend` must not write;
  owner-request cannot HOLD). Wired into `scripts/test-ci-gates.sh`.
- `SHA256SUMS` of the three skill trees and `scripts/write-checksums.sh`.
  CI compares the committed file to a fresh regeneration.
- `SECURITY.md` — pin by release tag, refuse unsigned HEAD, honest
  signing gap.

### Changed
- README documents `git clone --branch vX.Y.Z` and
  `npx skills add remigiusz-antczak/deep-code-review#vX.Y.Z` next to
  `install.sh`, with an AST07 warning against floating HEAD.
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.22.0**.

## [1.21.0] — 2026-09-08

Orchestration lessons unique to the leftover PR #11 branch, restamped
onto current main so they do not collide with shipped 1.20.0. Additive
on 1.20.0 — the review bar's six phases, domains A–S, the gate table,
and the report shape are unchanged. Two items checked against 1.19.0
were already present (robust shell list-membership; worktree-per-lane
preflight) and are not duplicated.

### Added
- **`agentic-delivery/SKILL.md`**: "Environment probe (before you size
  anything)" (probe RAM/CPU/disk and usable tool/connector auth; decide
  heavy-lane count, model tier, and local-vs-CI from the probe, not
  habit); a general-lane context-inheriting-fork rule (a fork carries
  every prior instruction, not only the newest one — fresh unit for
  narrow work, or an explicit prohibition plus a check of what the unit
  actually called); a lane's own scope ends at its own green PR, not at
  the merge; Gate epistemology principle 9 (closing/deleting shared
  state needs evidence, not presumption); G7-vs-G8 clarification (a
  work item is done at integration; release/deploy is later and
  owner-gated); principle 3 gains a concrete triage step (identify the
  failing job **and step**, rerun a suspected flake, before reverting).
- **`deep-code-review/references/parallel-audit.md`** §2: tree-diff is
  blind outside the tree (issue/comment/message); verify a prompt-level
  strip actually held from the unit's tool calls, not its summary.
- **`deep-code-review/references/branch-and-merge-hygiene.md`** §1:
  truncated forge listing — `gh issue list`/`gh pr list` default page
  is 30; count with `--limit` or paginate.
- **`deep-code-review/references/product-ux-quality.md`**: reviewable
  who/what/when change history behind any decision-of-record edit, and
  agent/model-authored values stamped as such at write time.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the
  plugin manifest follow **1.21.0**.
- README missing-space nit after the personal-install sentence.

## [1.20.0] — 2026-09-08

Closes the remaining 1.19.0 self-review backlog after 1.19.1 landed
the byte-exact VERSION gate (F2/F8).

Domain C now walks OWASP LLM Top 10 **2026** titles quoted from
`OWASP-GenAI-LLM-Top-10-2026-v1.0.pdf` (fetched 2026-09-08). 2025 IDs
remain only as a compatibility map. New reference
`security-agent-skills.md` walks OWASP Agentic Skills Top 10
AST01–AST10 against both skill-consuming targets and this repo's
`install.sh` / VERSION / SHA stamp.

Repo dogfood that is settings-not-code (F3/F6/F7) is applied on the
GitHub repo itself: `delete_branch_on_merge`, secret scanning + push
protection, Dependabot security updates, tag `v1.19.1`. This commit
adds Dependabot version updates for GitHub Actions, an issue-template
`config.yml` so GitHub indexes the templates (F5), a PR-template gate
list that matches CONTRIBUTING (F10), and the idea-critic description
trigger `Use when` (F9). Required-review branch protection is still
off so a same-owner merge is not trapped.

### Added
- `.claude/skills/deep-code-review/references/security-agent-skills.md`
  (AST01–AST10), routed from `SKILL.md`.
- `.github/dependabot.yml` for `github-actions`.
- `.github/ISSUE_TEMPLATE/config.yml`.

### Changed
- Domain C / `security-ai-agents.md` walks LLM01–LLM10:**2026**.
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.20.0**.
- PR template mirrors CONTRIBUTING's pre-PR gate block.
- idea-critic description starts `Use when`.

## [1.19.1] — 2026-09-08

Patch on 1.19.0. The VERSION provenance gate no longer strips
whitespace before matching, and it no longer accepts a matching heading
anywhere in CHANGELOG.md. VERSION must be byte-exact ASCII core SemVer
(`MAJOR.MINOR.PATCH`, no leading zeros in a multi-digit part) with at
most one optional terminal LF. The first `## ` heading in CHANGELOG.md
must announce that version.

Closes the fail-open that accepted a planted `  1.19.0  ` file, and the
stale-ordering hole where an older first heading still passed if a later
heading matched. Ports the unpushed local `d104e72` contract onto main
and adds the planted whitespace / NUL / first-heading cases to
`scripts/test-ci-gates.sh`.

### Changed
- `scripts/ci-gates.sh` `version`: hex-validate raw VERSION bytes, then
  require the first CHANGELOG release heading to announce it.
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the
  plugin manifest follow **1.19.1**.

### Tests
- Eight new version-gate cases: leading-zero major, NUL, embedded
  whitespace, multiline, leading whitespace, stale first heading
  (reject); exact `1.13.0` with trailing LF, and no trailing LF (accept).

## [1.19.0] — 2026-09-08

A hardening pass on top of 1.18.0's software-house roles, from four research
streams: closing this skill's own spend-cap gap, filling the domain-K release-
engineering gap and the one-line G10 retrospective, hardening `idea-critic`
past a same-brain "independent" verdict, and six portable lessons drawn from
one AI-agent-maintained project's own operational history (scrubbed of every
project-specific detail — generic principles and fictional examples only).
Additive on 1.18.0 — the review bar's six phases, domains A–S, gate table, and
report shape are unchanged. Four candidate detectors from that lessons pass
(duplicated-UI-concept drift, write-only inputs, render-trace-before-edit,
UI-changing diffs needing visual proof) were found **already shipped** in
1.18.0's `product-ux-quality.md` and `parallel-audit.md` §5 during
verification against this branch — not re-added; see the PR body for the full
staleness note. Grounded in the sources logged in `docs/standards-index.md`'s
three new 2026-09-08 sections.

### Added
- **`references/model-tiering.md`** (domain E): three vendor-neutral model
  tiers, the cost/quality levers in the order the evidence favors reaching for
  them (effort tuning, prompt caching, batching, escalate-on-failure, budgets,
  bounded advisor consults, model swap last), two negative results (don't fan
  out on a single dependent chain; don't over-consult an advisor), and the
  mapping onto this skill's own fan-out tiers and delivery hats.
- **`references/release-engineering.md`** (domain K, the release half
  `dependency-currency-and-upgrades.md` never covered): feature-flag
  category/lifetime checklist, canary/blue-green claims checked against actual
  router/traffic-split config, DORA-or-`UNMEASURED`. Paired with a **Release**
  depth section in `agentic-delivery/references/roles.md`.
- **`agentic-delivery/references/retrospective.md`** + **`template-
  postmortem.md`** (routed from G10): blameless principle, mandatory-trigger
  criteria (not every bug fix), action-item-closure gate, repeat-root-cause
  check against prior postmortems.
- **`agentic-delivery/references/template-adr.md`** (routed from G3): Nygard's
  five-part shape + MADR's optional sections, giving G3's existing "ADRs /
  contracts" requirement an actual shape.
- **"Conductor operating rhythm"** subsection in `agentic-delivery/SKILL.md`:
  event-driven attention (not polled), fan-out sized to decomposition (not
  concurrency), pilot before full width, escalate-a-lane-don't-just-retry-it,
  and an empirical failure-taxonomy callout (Cemri et al., MAST) mapping onto
  the existing gate shape.
- **`idea-critic`**: verdict schema gains `steelman` (attack the strongest
  defensible reading of the claim) and `strongest_attack_survived` (the
  sharpest objection actually tried, and why it failed — required and
  non-generic on `PASS_TO_USER`), both enforced by `validate_verdict.py`; a
  premortem clause on the `kill-criteria` hat; Independence now tiers
  decorrelation strength (a different model family is stronger than a
  different context alone); a new "false-closure REVISE" pitfall.
- Six portable-lesson closes verified absent from this branch before being
  added: `role-coverage.md` (success-metric-to-emitted-event loop closure +
  the missing SRE-workbook burn-rate citation), `testing-and-evals.md`
  (stated Test-Pyramid-vs-Testing-Trophy philosophy required), `frontend-
  a11y.md` (URL-backed drawer/filter state), `infra-iac-containers.md` (a
  green health check is not proof of an out-of-band post-deploy data
  dependency), `docs-and-dx.md` (dated status/handoff doc proliferation),
  `concurrency-shared-state.md` (worktree-per-lane + spawn-time duplicate-work
  preflight).
- `branch-and-merge-hygiene.md`: stacked-PR-safe branch deletion, generated-
  file merge-conflict resolution (regenerate, never hand-splice), a new
  "Merge trains" subsection (verify the union once, merge members
  individually, sequence a gate-adding PR last), a combined safety-rail bullet
  on gating an irreversible command on a preflight's documented pass condition
  paired with a robust-shell-list-membership lesson (`for x in $LIST` on an
  unquoted variable silently stops excluding anything under a non-word-
  splitting shell; use a literal `case` or `grep -qxF` instead), and a §8
  spike/prototype branch-naming convention. A matching grep-flag row in
  `language-stack-redflags.md`'s Shell/Bash section.
- Three operating-discipline sentences with no code detector: principle 5 (a
  previously and explicitly made design choice is treated as a stated style
  guide — propose against it, never silently revert it); the Confirm bullet
  (a tentative/question-phrased message is a request for assessment, not
  authorization); `report-format.md`'s mechanism-unproven-fix language now
  extends to status reporting generally (running ≠ fixed).
- `docs/standards-index.md`: three new 2026-09-08 sections logging every
  source above with fetch dates and, per the file's own convention, what each
  fetch did **not** confirm (DORA's single-source caveat, the MAST paper's
  14-mode taxonomy not independently enumerated, Panickssery et al. tested on
  GPT-4/Llama 2 not Claude, and others).

### Changed
- `parallel-audit.md`: the shared fan-out context packet is flagged cacheable;
  a don't-start threshold complements the existing stop rule (don't fan out on
  one dependent chain or a single-context target); the Tier-1→Tier-2 sweep now
  tiers by model capability, not only effort; a new addendum distinguishes a
  concurrency-capacity flake from a genuine defect.
- `agentic-delivery/SKILL.md` G2 now requires a per-lane token/dollar budget
  before G4 starts (no budget = blocked, not unlimited) — closes a
  self-referential gap between this skill's own LLM10/`spend-cap` invariants
  (enforced on every *target*) and its own gate table (which enforced neither
  on itself). G0 now names an explicit appetite (a time-box, not an estimate).
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the plugin
  manifest follow **1.19.0**.

## [1.18.0] — 2026-09-08

The delivery overlay becomes a **software-house in a repo**: the full role roster
as hats (not standing bots), a first-class **Product Analyst** role, a hardened
adversary, the orchestration discipline that keeps parallel lanes from thrashing,
and the product-UX **interaction-completeness** bar. Additive on 1.17.0 — the six
review phases, domains **A–S**, the severity rubric, and the report shape are
unchanged; the review side gains one product-UX section and one fan-out
discriminator, the delivery overlay gains one routed reference, and the CI routing
gate now also covers the overlays. Grounded in five directly-fetched sources
(Anthropic *Building Effective AI Agents*; Claude Code Subagents; Anthropic Agent
Skills; MetaGPT; ChatDev) logged in `docs/standards-index.md`.

### Added
- **`agentic-delivery/references/roles.md`** (routed from that skill's `SKILL.md`):
  the software-house role roster as **hats, not headcount** — Conductor, Product
  Analyst, Architect, Implementer, Evil Twin, QA, Security, UX & Design, Release,
  Docs — each mapped to when it fires, the gate it owns (G0–G10), and the
  `deep-code-review` review lens it corresponds to. Depth only for the three roles
  the review-side `role-coverage.md` does **not** hold (Product Analyst,
  Evil-Twin-as-hat, Implementer); one-line pointers for the rest, to avoid
  restating the review overlay. Includes the two-tier **gates a software-house
  repo runs** table (commit-time: privacy/format/lint/type/unit+count; CI:
  build+E2E-at-SHA / verify-visible-UX / ux-evidence / dependency) with the repo's
  own gate epistemology (tell can't-check from found-a-problem; fail open on the
  former; provable-red on a planted defect; never stricter than the standard).
- **Product Analyst** hat in `agentic-delivery` (Operating model + G0/G1): turns a
  real signal into a testable spec, enforces **interaction-completeness**,
  benchmarks solved elements against **named** comparable products, and maintains
  a **feedback-coverage map** (each item → scoped → verified / deferred) — the
  product analogue of the review's coverage ledger.
- **Interaction-completeness + unified-UX** section in
  `references/product-ux-quality.md` (domain P): one **shared component per
  concept** (reuse/extend, never reimplement per page; a fix lands in the shared
  component, not one caller), **no write-only inputs** (read-back required),
  **WYSIWYG** (store markup, render it — never show raw `**`/`<u>` tokens), and
  fix-the-surface-that-renders — with new grep 🚩 rows and two pre-ship checklist
  items.
- **Render-surface discriminator** in `references/parallel-audit.md` §5: a grep
  match is a *candidate*, not a live site — trace route → component (UI) or the
  call graph (code path) before a finding or a fix names a `file:line` as the live
  surface; a fix aimed at a grep hit the target never runs is wasted work that
  leaves the real surface broken.
- `docs/standards-index.md`: a **2026-09-08** verified-by-direct-fetch section for
  the five sources above, each row stating what the fetch did and did **not**
  confirm (the arXiv abstracts do not enumerate specific role titles verbatim).

### Changed
- **`idea-critic`** hardened into a "proper evil twin": a **default-to-dissent**
  prime directive (with the reflexive-praise trigger), **attack before
  substantive work** (not after), and **verify-your-own-objection — the critic is
  a lead, not an oracle** (check a pushback's premise against current verified
  state; a critic that blocks good work with a stale fact is a false negative).
- **`agentic-delivery` orchestration discipline**: *Worktrees and occupancy* now
  states that a subagent/fork mechanism does **not** necessarily isolate the tree
  (assume shared until proven; branch/index/deps are per-tree), requires cleaning
  the base before launching and a **preflight** (running workers, `git worktree
  list`, open PRs) before spawning any lane; *Failure* adds **a running lane is
  not a finished one** (report what runs; report done only when verified).
- **`recommend-overlays.py`** now inspects the target for the quality gates it
  already has (CI, lint, format, tests, pre-commit, privacy — filename-level,
  reporting "not detected", never "absent") and frames the pack as the
  software-house roles + the gates the imprint would add. It also detects a
  **live custom delivery pack**: a skill under a real host skill root
  (`.claude/skills/` and peers — not a `docs/` archive) whose path, frontmatter
  `name`, or a small `SKILL.md` prefix names a delivery OS. Named packs already
  counted; a private factory, a software-house-pattern skill, or an
  already-installed `agentic-delivery` overlay previously still received
  `--with-delivery` / `--full`. Detection is review-negative (`deep-code-review`
  and `idea-critic` never count), skips non-regular files and `SKILL.md`
  symlinks (a FIFO would hang `open()`; a symlink can point outside the
  target), and stays bounded — one level under each known skill root, reading
  only a prefix, failing closed on any single unreadable file.
- **CI + CONTRIBUTING**: the `routing` gate runs on **all three** skill dirs
  (`deep-code-review`, `agentic-delivery`, `idea-critic`), so a new overlay
  reference cannot ship unrouted — the repo dogfoods its own "documented but
  unenforced is a finding" rule.
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the plugin
  manifest follow **1.18.0**. README gains a *software-house overlay* section and
  refreshed counts.

## [1.17.0] — 2026-09-08

Dogfood of 1.15.0/1.16.0 against two external product repositories plus the
Agent Skills spec. Three defects in the bar itself, not in those products: `--recommend` treated archived Superpowers
notes as a live delivery OS; kit-leftover `AGENTS.md` was not a named DX
defect; delivery never required a running local stack. Anti-slop is now an
explicit Phase-4 filter so a review of a well-gated product does not emit
community-health noise.

### Added
- **Anti-slop** in `references/method.md` Phase 4: drop findings that would
  not change a merge or a ship. Kit leftover (`AGENTS.md` still describing
  scaffold `app/` while the product lives in `apps/` / `packages/`) is **one**
  DX finding, not a docs wall.
- **Kit leftover vs product tree** and **local environment is DX** in
  `references/docs-and-dx.md`.
- **Local environment (own it)** in `agentic-delivery`: discover the project's
  one-command / compose / devcontainer, bring it up, verify against the
  running process (`verify:served` when present), tear down. G5 is
  `UNVERIFIED` if the stack never started.
- `idea-critic` pitfall: `HOLD` slop recs (extra docs, restyle, second
  delivery OS) unless a named defect requires them.

### Changed
- `--recommend` only treats a delivery pack as live when a skill path exists
  (`.claude/skills/superpowers/SKILL.md` and peers) or a marker directory sits
  outside `docs/` / `archive` / `history` / `code-review` / `notes`. Historical
  Superpowers plans under `docs/` no longer suppress `agentic-delivery`.
- Overlay `VERSION` files and plugin manifest follow 1.17.0.

## [1.16.0] — 2026-09-08

A **product-UX quality** reference under domain **P** — the *design half* of a
frontend review (whether a UI feels **at-home**: conventional, self-evident,
correct in every data state, cleanly encoded), complementing the a11y-correctness
half `frontend-a11y.md` already owns. Additive on 1.15.0: the six phases, domains
**A–S**, the severity rubric, and the report shape are unchanged; domain P gains
a second reference (routed by a "read it when…" trigger) and the web archetype
must-load set. No new URL, version, or date is cited — the design half grounds
in WCAG 2.2 (already tracked), Nielsen's usability heuristics (named, not
URL-cited), and the public precedent of top products.

### Added
- **`references/product-ux-quality.md`** (routed from domain P): the "at-home"
  design bar — **every data state ruled on** (empty/loading/error/partial/
  overflow), **one-visual-channel-per-dimension** encoding hygiene,
  **never-colour-alone** (the greyscale test), the **metric/KPI delta standard**
  (caret + magnitude, colour by *sentiment* not direction), **self-evident-over-
  explained** (progressive disclosure; legends collapsed, glyph-grid not prose),
  **drawers-overlay + no-dead-controls**, and a **named** top-product precedent
  per solved element. Opens with the reconciliation rule (read first): matching a
  convention is a review **observation** surfaced under "Decisions needed (owner)"
  with the minimal-visual-impact fix — **never a licence to redesign**. Closes
  with a **Phase-6 UX-evidence gate** that fails open on could-not-check.

### Changed
- `SKILL.md` domain **P** routes both `frontend-a11y.md` and
  `product-ux-quality.md`. Web archetype must-load includes the design half.
- README P-row names the design half; Nielsen's usability heuristics added to
  the by-name standards list.

## [1.15.0] — 2026-09-08

The review bar stays the default product. Optional overlays inject a
public-safe **gated delivery** pattern and a **pre-owner idea attack** into
a target repo. Spec compliance (Agent Skills description ≤1024 characters,
`SKILL.md` under 500 lines) unblocks every later install.

### Added
- **`agentic-delivery`** (opt-in) — G0–G10 gated delivery: smallest-sufficient
  hats, independent QA/security, one writer per worktree, exact-SHA receipts,
  human approval on push/merge/deploy. Names `deep-code-review` at G1/G6/G7.
  Public-safe distillation; no operator preferences, no private intake, no
  runtime names.
- **`idea-critic`** (opt-in) — three hats (skeptic, better-way, kill-criteria);
  verdict `HOLD | REVISE | PASS_TO_USER`; `owner-request` cannot HOLD.
  `scripts/validate_verdict.py` fail-closes on a missing key, an illegal
  HOLD, or a list-shaped `user_question`.
- **`./install.sh --recommend <project>`** — inspects the target and prints a
  pack. The agent may recommend `--full`; the owner decides. Another delivery
  pack already in the tree is a reason **not** to also install
  `agentic-delivery`.
- Install flags: `--with-delivery`, `--with-critic`, `--full`,
  `--with-extra-hosts` (Gemini, OpenCode, Copilot `.github/skills/`, Windsurf,
  Hermes, Kiro).
- `.claude-plugin/plugin.json` so `/plugin marketplace add` works.
- Community health: `CODE_OF_CONDUCT.md`, issue templates, PR template.
- `references/method.md`, `domain-checklists.md`, `report-format.md` — method
  depth moved out of `SKILL.md` (progressive disclosure).

### Changed
- Default `./install.sh <project>` remains **review-only**. Delivery is never
  the default.
- `deep-code-review` `description` rewritten to ≤1024 characters, when-to-use
  in the first 57 characters.
- `SKILL.md` is the map (under 500 lines). Checklists, phase procedures, and
  report templates load on demand.
- `CONTRIBUTING.md` points at `scripts/test-ci-gates.sh` + `ci-gates.sh`.
- Chat voice is **not** vendored. Compressed assistant prose, if wanted, is
  a pointer to the public caveman skill repository. Persisted artifacts stay
  normal English.

### Not in this release
- No private operating-registry content, live values, or third-party
  identifiers.
- No default-on full pack.
- No caveman files copied into this tree.

## [1.13.0] — 2026-09-02

A role-aware **software-house overlay** over the existing method, plus the repo's
own gates re-homed into one fail-closed helper proven by a self-test harness.
Additive and smallest-sufficient — the six phases, domains **A–S**, the severity
rubric, and the report shape are unchanged; the overlay only orders and assigns
domains through a delivery-role or security-team lens, it never adds or drops one.

### Added
- **Role & team overlay** in `SKILL.md` + `references/role-coverage.md` (routed
  by path with a "read this when…" trigger): per-role leads-on domains for the
  nine delivery roles, driven through the same A–S method. Adds the lenses this
  file does not hold — **architecture quality** (seams, dependency direction,
  SPOFs, drift from the stated design), **lightweight product planning**
  (problem→acceptance, smallest slice, success metric), **SLI/SLO with error
  budget & burn-rate**, and **release-owner sign-off**.
- **Security-team colour model** (re-packages the same evidence by stance — no new
  rules; Red still needs `file:line`, Blue still fails closed): **Red** adversarial
  pass, **Blue** detection/fail-closed, **Purple** red→blue gate, **Yellow** build,
  **Green** (Yellow+Blue), **Orange** (Yellow+Red), **White** scope/ROE/owner
  decisions/sign-off.
- **Black Team — the agent boundary is absolute.** A physical / human-operations
  lens (intrusion, impersonation, social engineering, surveillance, badge/lock
  bypass, device placement) where an agent may **only plan, tabletop, and analyse
  owner-supplied evidence** — never perform or operationally direct any such action,
  and never test a real person or site. Real assessments are **human-led under
  written owner authorization and legal rules of engagement (ROE)**; a request that
  crosses the line has its operational part refused and its planning part kept.
- `scripts/ci-gates.sh` — one **fail-closed** production helper for the repo's
  documented gates (`privacy`, `routing`, `version`, `install`): no `|| true`, no
  always-success fallback, no pipeline that swallows the real exit status. Privacy
  reports matching **file names only, never content**, and fails closed on a
  missing, empty/comment-only, or malformed-ERE banlist while honouring an optional
  sibling `.banlist.local.txt`. Routing matches basenames **literally** (fixed-
  string) and flags dangling routes, with a non-failing size WARN.
- `scripts/test-ci-gates.sh` — a **16-case RED/GREEN self-test harness** pinning
  that helper's contract with real exit codes preserved: privacy (reject empty and
  all-comment banlists, detect a planted secret, reject an invalid ERE without
  disclosing banlist content, load the sibling local override), routing (reject
  unrouted, reject a regex-meta basename match, WARN on an oversized SKILL.md),
  version (reject malformed VERSION and a missing CHANGELOG heading), and install
  (overwrite a placeholder with the real vendored docs; **Claude**, **minimal**,
  **Codex**, and **full** agent-agnostic default modes; **Codex/full** assert the
  managed AGENTS.md block sentinels — `deep-code-review:begin`, `Installed:`,
  `Agent-agnostic` — and **full** re-installs to prove exactly one idempotent
  managed block, never a duplicate; collision-free backups on rapid repeated
  installs).

### Changed
- CI (`.github/workflows/ci.yml`) now runs the self-tests and then enforces the
  documented gates through that **same single helper** — one authoritative
  implementation, no inline copies, so the enforced check and its tests never
  diverge.
- `install.sh` backups are **portable and collision-free** — a seconds-resolution
  timestamp plus an existence-checked numeric suffix (avoiding `date +%N`, which is
  unsupported on BSD/macOS `date`), landing under `.../skill-backups/`, never inside
  `skills/`.
- **Confidentiality scoped first- vs third-party** (principle 11): a project's
  intended-public identity (published maintainer/author, public repo URL) is not a
  leak, while drift beyond that stated-public surface is the finding; softened the
  prose's unsupported scanner/breach claims to what the gate actually proves. The
  project's own `CLAUDE.md` confidentiality rule is aligned to the same scoping so
  the repo's governance and the skill it ships no longer disagree on first-party
  identity (the repo dogfoods its own gate: `.banlist.txt` bans secrets + generic
  patterns, real identifiers live in gitignored `.banlist.local.txt`).
- README reference-file count → **20**.

## [1.12.0] — 2026-09-01

Throughput-and-affirmation harvest from a FULL run against a large, hardened
production Node codebase: make the fan-out cheap on large targets, make the verify
step catch intended-behavior false positives, and make the review's value legible
on a target that yields few or no defects. Additive — phases, domains A–S, and the
report shape are unchanged; the report gains one co-equal affirmative section.

### Added
- `parallel-audit.md`: **two-tier sweep** — a cheap Tier-1 candidate enumeration
  before the high-effort Tier-2 confirm that runs only on survivors, so
  agent-minutes track candidate count, not domain size; plus small
  one-invariant units (a few hundred lines of owned surface) so no single finder
  stalls the pipeline under a small concurrency cap.
- **Verify against the tests, not only the source** (`parallel-audit.md` §4 +
  SKILL Phase 4): before `CONFIRMED`, read the tests that exercise the finding — a
  fix that contradicts a passing assertion is `REFUTED` as intended behavior — and,
  for a change to security/cost/concurrency logic, apply the fix in a throwaway
  worktree and run the suite. Re-reading the source the finder read cannot catch an
  intended-behavior false positive; only the tests encode intent.
- **"Invariants verified to hold"** as a first-class, co-equal report section
  (Phase 5 + report format + rules + definition of done) fed by a new
  `checked_sound` affirmative return in the fan-out contract — the primary
  deliverable on a hardened target, grounded `file:line`-or-drop like any finding.
- **Runtime-proven-gate lens** in domains B (home), C (tool-authz proven live), and
  F (subsystem proven to execute): is the gate measured at runtime (a
  self-proof/health check) and **fail-closed when the proof is absent**, or merely
  present in code? An unproven gate that reads as safe is itself the finding.
- **Failure direction as a severity axis** (rubric + Phase 4): fail-open (bypass /
  over-grant / leak) scales with blast radius; fail-closed (self-DoS / over-deny /
  conservative accounting) caps **Low** unless it enables a further exploit.
- Domain H: **duplicate-source-drift** probe — byte-identical lockstep copies
  (vendored, per-plane, generated-vs-source) need a parity test or single source;
  flag the missing guard, not the duplication.
- **Lead independent read of the top-N blast-radius files**, concurrent with the
  fan-out (`parallel-audit.md` §4 + Phase 2), so a zero-survivor run still has a
  non-empty confidence basis and no high-stakes surface goes unread.
- **Coverage attributed per unit** — finder id + lead-read, with a stalled/refused
  unit marked `unverified` rather than silently absorbed (Phase 0 ledger + Phase 5
  reconciliation + `parallel-audit.md` unit-manifest Lead-read column).

### Changed
- Example report version stamp 1.12.0; the example now shows the affirmative
  invariants ledger, a REFUTED-at-verify candidate (intended, test-encoded,
  fail-closed), and finder + lead-read coverage.

## [1.11.0] — 2026-08-21

Harvest from a same-owner inter-agent bridge review: name ASI01–ASI10, and
treat audience-mismatch plus committable-identifier leaks as first-class.

### Added
- ASI01–ASI10 titles (from the 2025-12-09 OWASP announcement, verified
  2026-08-21) in `references/security-ai-agents.md`.
- Same-owner vs many-audience probe under ASI07 (channel audience named;
  protocol keyed on tenant/uid, not a display name).
- Privacy: committable artifacts (PR/doc/fixture/commit) as a Q surface.
- Fan-out revision identity now fails closed on a missing or mistyped full SHA.
- Executable review units use separate worktrees and temp/port/process namespaces;
  aggregate suites serialize when that isolation is unavailable.
- Standards-index addendum 2026-08-21 (ASI titles; 2026 LLM Top 10 exists,
  titles unverified).

### Changed
- Domain C / adversarial pass / domain Q flags point at the new probes.

## [1.10.0] — 2026-08-21

Instrument/measurement discipline from three 2026-08-21 FULL/PR feedback runs —
the reviewer's own tools, not the code, were the dominant error source. Durable
invariants only; host-CI trimmed to one Phase-1 line + one report row (no new
first-response field), requirements-move ceremony left out.

### Added
- Principle 2: an absence needs a positive control; canonical instrument over
  proxy; read a platform-computed value from the platform (a gate reimplementing
  it is a finding); a project's enforcement is verified against the artifact, not
  the doc; self-review test blind spot.
- Phase 1: pipe/`$?`, SIGPIPE-141, `grep -q`, and `2>/dev/null` gate hazards
  (mechanics in `language-stack-redflags.md`); a tool count is a floor until caps
  are checked; gate-vs-standard (narrow ≠ weaken; WCAG 1.4.3 example); host-CI of
  the base branch.
- Phase 0: provision the worktree (never symlink deps; an env-shaped failure in a
  fresh worktree ≠ Blocker); read the revert *body* for its invariant.
- DIFF quick-path (consolidated) + ceremony-to-scope: ledger emitted at every
  scope, two-artifact report FULL-only, lighter `found → fix → re-gate` trail when
  reviewer = fixer.
- `mechanism-unproven` fix marker (Fix line + Phase 5 + definition-of-done).
- Domain G: singleton lifetime-vs-data bug class (leaks with perfect sync).
- Domain P 🚩: an a11y gate computing names from `innerText`; a presence-only name
  check.
- Ground-truth report row: `Host CI (base <ref>)`.
- `parallel-audit.md`: `REVERT_INVARIANTS` packet field; brief facts labelled
  `verified`/`to-be-verified` with premise verified before dispatch;
  `BRIEF_CONTRADICTION` as first-class output; symmetric re-verification; per-run
  diagnostic paths.
- `frontend-a11y.md`: cross-view consistency pass (WCAG 3.2.4 / 3.2.6) and the
  accessibility-tree-not-`innerText` rule.
- WCAG SC 1.4.3 / 3.2.4 / 3.2.6 verified by direct fetch (2026-08-21) in
  `docs/standards-index.md`.

### Changed
- Example report version stamp 1.10.0.

## [1.9.0] — 2026-08-19

Method honesty and detection depth from two FULL multi-model skill-feedback
runs — narrowed to durable invariants; host/model ceremony and duplicated
doctrine left out.

### Added
- SCOPE / packet field `BANNED_REMEDIES` (records Phase 0 revert/deletion scan).
- Principle 5: drift from a named stating artifact is the finding.
- Phase 2 named check: stated invariant / landed guard → bypass census
  (appsec untrusted-egress caller census; data-quality artifact→consumer).
- Config/runtime evidence rule: no severity on an unobserved branch.
- Planted-probe skip caps gate-self-test only (DoD wording).
- Parallel-audit: unit manifest, material dissent preservation, stop rule,
  named substitute in fan-out preamble.
- Soft-no-op persistence (empty artifact overwrite) in reliability + F map.
- Concurrency: corrupt→wipe ban; stale RMW across `await`.
- Data-quality: denominator integrity; absent/expected-empty/false/empty-list.
- Spend ledger: test present-fault branch (`EACCES`/`EISDIR`/invalid body).

### Changed
- Phase 5 BLUF: top defects + `Decisions: N` pointer; product/redesign never
  carries Blocker/Critical gate language.
- Example report version stamp 1.9.0.

## [1.8.0] — 2026-08-17

Depth from multi-model review of the skill itself: close authenticated-IDOR and
cache/CDN blind spots; force agent hard-gates; install support docs; lean privacy
+ observability refs; token-cutting coverage ledger and DIFF-scoped Phase 1.

### Added
- A01: Identity Map **forgeability** column + bypass row-set; **bidirectional
  gate proof**; **two-principal matrix**; **cache/CDN authz**; dual-surface
  beyond `page.tsx` (serialized payload, server actions, RPC/GraphQL/WS);
  tenant/row scoping; presigned URL / upload checks; safer anon-GET (canary +
  anon-vs-auth body diff; local/dev default).
- A05 files/archives/XXE; A06 business-logic detect steps; A07 session cookies +
  OAuth/OIDC + refresh rotation; API overlay procedures (BOLA/BFLA, mass-
  assignment, zombie APIs, GraphQL/gRPC/WS).
- `references/privacy-compliance.md`, `references/observability.md`.
- Phase-0 coverage ledger + archetype → load map; first-response hard block
  (`SCOPE`/`START_SHA`/`TREE_STATE`/`REVERTS_CHECKED`/…).
- Banned remedies: deleted gate paths (`--diff-filter=D`), not only Revert
  subjects.
- Authz posture ledger in Ground truth; negative authz tests in DoD;
  DIFF authz 🚩 list; public-repo disclosure rule for committed reports.
- Parallel-audit: frozen packet schema + invariant catalog.
- `install.sh` copies `standards-index.md` + `example-review-report.md` into
  installed `references/`.
- ASVS 5.0.0 verified by direct fetch (2026-08-17) in standards-index.

### Changed
- Phase 5 default: chat BLUF ≤30 lines + out-of-tree; `code-review/` write is
  opt-in (`--write-report` / confirm).
- Phase 1 scoped for `DIFF`/`FILE` (changed-path tests; plant only if gate under
  review).
- Domain S FULL: consequence branches + count by default.
- Domain B: SSRF ranges single-sourced in appsec; A02–A10 one-liners + force
  load of `security-appsec.md` before Phase 3.
- S2 world-reachable without auth = Critical (zero discretion).
- README domain table + reference count; example report version stamp 1.8.0.
- CI asserts installed support docs present.

## [1.7.0] — 2026-08-17

Access-control depth from a production anonymous-read class of defect:
identity must be mapped per request class before any gate is proposed; API
redaction is not page protection; preflight that expects anonymous 200 on
data routes is a finding; internal business data is Confidentiality Tier S2.

### Added
- **Identity Arrival Map** (document / XHR / bare curl) in `security-appsec.md`
  A01 — required before proposing middleware or document gates; "middleware on
  document when identity only arrives via client Bearer" marked anti-pattern.
- **Dual-surface check** — sensitive loader used by API ∩ RSC/SSR page;
  asymmetric redaction = Critical when world-reachable.
- **Anonymous GET sweep** — mandatory Phase 0/3 opener for networked apps
  (status + body size, no auth).
- **Confidentiality tiers S0–S3** in the severity rubric (incl. internal
  business data as S2 → Critical if world-readable).
- Phase 0: platform-vs-app-vs-preflight trust rows; **banned remedies** from
  recent auth/middleware/gate reverts.
- Phase 1 planted-defect matrix: missing / **empty** / wrong / path-excluding
  config.
- `parallel-audit.md`: specialized-subagent reject → **generalPurpose** fallback
  under the same read-only contract (do not stall A01 on harness ceremony).

### Changed
- Phase 5: prefer out-of-tree report during active Critical remediation; chat
  order for FULL = verdict → plain top 5 → decisions → path to machine table
  (table in file, not first bubble); advise-only on security gates (no
  auto-implement middleware).
- Domain B checklist + adversarial opener cross-link the new A01 procedures.
- `testing-and-evals.md`: empty-config self-test called out.

## [1.6.0] — 2026-08-17

**Agent-agnostic packaging.** The method was already host-neutral in substance;
install + docs still read Claude-first. Default install now mirrors the skill
into every common skill root (`.agents/`, `.cursor/`, `.claude/`), `AGENTS.md`
is the cross-vendor entry pointer, and SKILL/parallel-audit/docs speak to any
major coding agent first.

### Added
- Default multi-path install: `.agents/skills/`, `.cursor/skills/`,
  `.claude/skills/` (+ optional `--with-codex` → `.codex/skills/`).
- `--minimal` lean install; `--with-cursor` kept as no-op for compatibility.
- Harness table rows for Copilot / Gemini / Aider / Windsurf; generic-first
  fan-out contract.

### Changed
- SKILL "How to use" + confidentiality restatement → agent-agnostic discovery
  and `AGENTS.md`-canonical imprint language.
- `docs-and-dx.md` portability / imprint: prefer `AGENTS.md`, peers as pointers.
- README / AGENTS.md install pointer: no "for non-Claude agents" framing.
- CI dry-run asserts `.agents` + `.cursor` + `.claude` paths on default install.

## [1.5.0] — 2026-08-17

Depth + install portability on top of 1.4.0's multi-agent checkout safety. New
reference playbooks for reliability, concurrency, and API contracts; review-
surface gate in the definition of done; harness notes for fan-out; version
stamp + optional Cursor-native install path; worked fictional example report.

### Added
- `references/reliability-error-handling.md` — domain F depth (timeouts/aborts,
  retries, crash/SIGINT resume, silent subsystem no-op).
- `references/concurrency-shared-state.md` — domain G depth (races, file stores,
  TOCTOU, tests/jobs vs real shared paths).
- `references/api-contracts.md` — domain I depth (public contracts, webhooks,
  message-schema evolution; OWASP API Top 10 overlay stays in appsec).
- Skill `VERSION` file (`1.5.0`); `install.sh` stamps version + short SHA into
  the AGENTS.md pointer and **refreshes** that block on re-install.
- `install.sh --with-cursor` — also copies the skill to
  `.cursor/skills/deep-code-review/` (Cursor-native; Cursor already loads
  `.claude/skills/` for compatibility — verified against Cursor Agent Skills
  docs this session).
- `docs/example-review-report.md` — fictional FULL report showing `START_SHA`
  preamble, `CONFIRMED`/`CORROBORATED`/`PLAUSIBLE`/`latent`, and plain-language
  companion.
- `parallel-audit.md` harness notes — Claude Code / Cursor / Codex / one-shot
  map for read-only toolsets vs mutate-ban + tree-diff fallback.
- Definition-of-done + first-response **review surface pinned** checklist
  (`START_SHA`, worktree, history count).

### Changed
- README domain table routes F/G/I to the new references; install docs cover
  `--with-cursor` and the version stamp.

## [1.4.0] — 2026-08-17

Ops/safety hardening for **live multi-agent checkouts** — the review loop already
caught real defects under an anti-fabrication contract; this release makes the
method safe when another agent is editing, switching branches, or committing in
the same tree. Additive: domains A–S and report sections unchanged; new
confidence marker `CORROBORATED`; Phase 0/1/5 and `parallel-audit.md` carry the
depth.

### Added
- **Immutable review surface** — Phase 0 captures `START_SHA`, prefers
  `git show $START_SHA:path` or a dedicated worktree/clone (default for `FULL`),
  and detects a shared/mutating checkout (`git status` twice; occupied → don't
  plant or write into the live tree). First-response line states the pinned ref.
- **History-depth check** — Phase 0 runs `git rev-list --count HEAD` /
  `git log --oneline -5` (and shallow detection); never trust a prose "no
  history" claim; tree scrub ≠ history scrub for secrets/PII.
- **Triage-first fast lane** — Phase 0 runs project `doctor`/gates/documented
  invariants before expensive fan-out; Review mechanics and Phase 2 order by
  blast radius after those hits.
- **`parallel-audit.md` contracts** — read-only tool allowlist (or mutate-ban +
  lead before/after tree-diff hard-fail); transitive identifier masking in
  subagent returns; mega-file chunking by named concern; `CORROBORATED`
  confidence when independent units converge on the same sink.
- **Phase 5 shared-tree escape hatch** — if the checkout is occupied or an
  unrelated change is in flight, deliver the human-readable report out-of-tree /
  offer a dedicated review branch instead of writing `code-review/` into someone
  else's commit surface.
- **Hermetic-test shared-state red flag** — domain J (cross-ref G) + depth in
  `testing-and-evals.md`: tests that write real tracked/shared data paths with
  cleanup only in `finally`/`try` that hard-exit can skip.

### Changed
- Principle 7 — planted-defect probe defaults to a dedicated worktree/copy;
  report write is conditional on an unshared idle tree; fan-out least-privilege
  is by toolset where the harness allows.
- Principle 11 / confidentiality restatement — masking is transitive through
  fan-out, not lead-only.
- Phase 1 planted probe — worktree/copy at `START_SHA` by default; never plant
  into a tree another process can commit from.

## [1.3.0] — 2026-08-14

New capability — **branch, merge & open-work triage**. The review now analyzes
every open branch and advises, per branch, whether to merge it (to `main` or
`develop`, per the detected branching model), open a PR, rebase/refresh, delete
(if already merged), archive, split, or escalate — so leftover work gets cleaned
up instead of rotting. Unlike 1.2.0, this **does** change the domain list
(A–R → A–S) and **adds a report section** (the branch & merge triage table).
Additive and opt-in to act on: the triage is advice; any merge/delete/push runs
only on explicit approval.

### Added
- `references/branch-and-merge-hygiene.md` — the depth behind the new domain S:
  ground the branch set before judging it (`git fetch --all --prune`; a shallow/
  stale clone hides open work; open-PR state is forge state, mark `unverified`
  when forge auth is absent); detect the branching model (Trunk-Based / GitHub
  flow / GitLab flow / git-flow) to resolve each branch's target; classify by
  **content, not just tip** — `git branch --merged` misses squash/rebase-merges,
  `git cherry` recovers single-commit squashes but a **multi-commit squash defeats
  patch-id matching**, so the forge merged-PR list is the authoritative
  corroborator; a per-branch decision tree → recommendation with the exact
  command; merge-strategy trade-offs; safety rails (never delete unique unmerged
  work, `--force-with-lease` not `--force`, a leaked secret is fixed by rotation
  not branch deletion); and severity discipline so branch cleanup never buries a
  real defect. All enumeration commands validated against a scratch repo this
  session. Routed from the new domain S.
- **Domain S — Branches, merges & open-work triage** in `SKILL.md` (A–R → A–S),
  scoped to a local git checkout; a Phase-0 open-branch/open-PR inventory hook; a
  Phase-5 triage-table output; a **Branch & merge triage** section in the findings
  report and an "Open work to tidy up" section in the human-readable report; and a
  definition-of-done line requiring every open branch to carry one recommendation.
- Boundary made explicit with section O (`docs-and-dx.md`): O owns *is branch
  protection configured*; S owns *what open work exists and what to do with it* —
  cross-referenced, not duplicated.
- `docs/standards-index.md`: verified-this-session rows (2026-08-14) for
  Trunk-Based Development, GitHub flow, GitLab flow, git-flow (Driessen), Fowler's
  branching-patterns article, GitHub's merge-method / protected-branch / merge-
  queue / branch-deletion docs, and the `git` reference manual, with the two
  attribution caveats surfaced by primary-source checks (GitHub's own docs do not
  state "main is always deployable"; "merge debt" is not Fowler's phrase).

## [1.2.1] — 2026-08-14

### Fixed
- `install.sh` backed up an existing skill to `…/.claude/skills/<name>.backup-<ts>`
  — **inside** `skills/`, where Claude Code then loaded the backup as a duplicate
  skill. Backups now go to `…/.claude/skill-backups/` and are never loaded.

### Changed
- `install.sh` is **universal by default**: alongside the Claude Code skill it
  writes an additive, idempotent cross-agent `AGENTS.md` pointer (Codex, Cursor,
  Copilot, Gemini, Aider), so the method is not Claude-only. The opt-in
  `--portable` flag is replaced by a `--claude-only` opt-out (`--portable` is still
  accepted as a no-op, with a note).

## [1.2.0] — 2026-08-14

Coverage extension — dependency currency & safe upgrades, repository hygiene,
cross-agent portability of the standards imprint, and DX depth — plus the repo now
enforces its own documented gates in CI. Additive; phases, domains A–R, and report
formats are unchanged.

### Added
- `references/dependency-currency-and-upgrades.md` — detect stale / EOL /
  known-vulnerable dependencies, then upgrade with discipline (no blind "latest",
  semver-risk sizing, changelog review, regenerated lockfile, the project's own
  gate proven green on the bumped tree, provenance check) with severity discipline
  so "behind latest" never becomes noise. Routed from K and H.
- Repository hygiene & community-health review (`docs-and-dx.md`, SKILL.md O):
  LICENSE, SECURITY.md, CONTRIBUTING, CODEOWNERS + its enforcing rule, branch
  protection, CHANGELOG, templates — rated by repo exposure (Info/Low private,
  escalating when public / distributed / reaching production).
- Cross-agent portability: a divergence check across `CLAUDE.md` / `AGENTS.md` /
  peer instruction files, and a Phase-6 imprint that now defaults fresh standards
  to a canonical cross-vendor `AGENTS.md` with thin per-agent pointers; the
  "documented but unenforced = advisory" durable-standards finding.
- `install.sh --portable` — additively drops an idempotent root `AGENTS.md`
  pointer so non-Claude agents (Codex, Cursor, Copilot, Gemini, Aider) discover
  the method.
- This repository now dogfoods its own bar: `.github/workflows/ci.yml` (routing,
  name-match, `install.sh` parse, banlist-driven fail-closed privacy gate; a
  SHA-pinned action + least-privilege token), plus `SECURITY.md`,
  `CONTRIBUTING.md`, and `.editorconfig`.
- 16 standards verified by direct fetch and logged in `docs/standards-index.md`.

### Changed
- **DX** (`docs-and-dx.md`) gains fewest-commands-to-first-run (normalized
  bootstrap / devcontainer), dev/prod parity, and time-to-first-run as friction.
- **Phase 6 / imprint** is now idempotent and additive (detect-and-stop,
  create-if-missing, add-only-missing-lines, print-what-changed) and pairs every
  imprinted standard with the gate that enforces it.
- **Decorrelated second-model review** (SKILL.md review mechanics) is read-only
  and fail-soft — it advises, never hard-blocks.
- README reference-file count (10 → 11); standards list refreshed.

### Fixed (from a self-review of the skill)
- **Phase 5** no longer mandates writing `code-review/…` for a `DIFF` of a PR/MR
  (which may have no writable checkout, and would land the file inside the diff
  under review) — that write is scoped to FULL / local-checkout, and a DIFF's
  deliverable is the review comment on the PR.
- **Phase 1**'s planted-defect gate probe now requires a verified-clean tree (or a
  throwaway worktree) and a confirmed revert, carved into principle 7 as the one
  permitted transient mutation.
- **Severity rubric**: `unverified` / `PLAUSIBLE` findings now have an explicit
  gate rule (reported at provisional severity, block only once confirmed); Blocker
  vs Critical for data damage is discriminated (already-corrupting vs
  will-corrupt-next-run).
- **Coverage**: input-amplification DoS (ReDoS, decompression / entity-expansion
  bombs) added to the adversarial pass and the red-flag greps; AI-eval golden-set
  **contamination** flagged as a Critical eval defect; one-shot-prompt mode now
  names the references to also paste.
- **Duplication / pointers**: data-quality's spend-governance restatement folded
  into a cross-reference to `performance-db-cost.md`; a stale "section M" secret
  pointer repointed to N; `N-A` → `N/A`; `CREATE INDEX CONCURRENTLY` marked
  Postgres-specific.

## [1.1.0] — 2026-08-13

Field-hardening pass distilled from four independent FULL-run engagements. No
restructuring — phases, domains A–R, and report formats are unchanged; these are
additive method, rubric, and reference refinements.

### Added
- `references/parallel-audit.md` — fan-out protocol for large targets: a shared
  context packet, a fabrication-resistant subagent contract (one named invariant,
  `file:line` + failing case, `NONE` is valued), and orchestrator re-verification
  of every subagent finding in both directions. Routed from "Review mechanics"
  and Phase 2.

### Changed
- **Phase 1** now verifies gate *scope*: run the project's own aggregate gate by
  name, confirm exit codes, enumerate what the gates exclude and report coverage
  per subtree, prove each gate goes red on a planted defect, and flag
  decorative/unwired tests — plus a container/serverless deploy-contract
  preflight.
- **Severity rubric** gains a reachability qualifier: a `latent` finding keeps its
  intrinsic severity but gates "enabling the subsystem," not merge (a bounded +
  gated + recoverable destructive breach may be High); owner priority raises
  prominence, not severity. Machine and human reports gain a two-status verdict
  and `CONFIRMED`/`PLAUSIBLE` finding confidence.
- **Domains A–E, C, O** and their references gain: latest-batch-by-`max(col)`;
  exposure-boundary-first + CSRF≠auth; the "asserted-but-unenforced safety
  property" class; a spend-safety checklist (default-off caps, fail-open ledgers,
  `SELECT sum()` TOCTOU, cross-process guards); monotonic read-path shadowing +
  write-guard-covers-every-primitive; and a docs↔code claim-reconciliation
  technique.
- **Principle 2 / Phases 4–5**: byte-fidelity before invisible-character claims; a
  live-vs-documented-incident discriminator; report privacy re-scan, third-party
  proper-noun scrub, and PR-split by risk surface.
- README reference-file count (9 → 10).

## [1.0.0] — 2026-08-13

Initial release: a universal, evidence-grounded deep code-review skill.

### Added
- `.claude/skills/deep-code-review/SKILL.md` — the review method (6 phases) and
  eighteen domain checklists (A–R) plus an adversarial/red-team pass, severity
  rubric, exact report format, and definition of done.
- Nine on-demand reference playbooks under `references/`: application security
  (OWASP Top 10:2025), AI/LLM/agent security (OWASP LLM Top 10:2025 + Agentic
  Applications 2026), data integrity & quality, performance/DB/cost, testing &
  evals, infrastructure/IaC/containers, docs/DX (incl. the standards-imprint
  phase), frontend/accessibility (WCAG 2.2 AA), and language/stack red flags.
- `install.sh` — one-command install of the skill into any project's
  `.claude/skills/`, with backup-on-update and self-install guard.
- `README.md` (human-facing, with a Mermaid method diagram and a coverage map),
  `CLAUDE.md` (AI-facing standards for this repo), `docs/standards-index.md`
  (verified standards with URLs + verification dates), `.banlist.txt` privacy-gate
  seed, `LICENSE` (MIT), and `.gitignore`.

### Notable design decisions
- **Judge the outcome, not just the code** — a hard monotonic-quality invariant
  for any data producer, with a required non-regression test.
- **Do no harm** — every proposed change must be net-positive across all axes;
  never fix one by regressing another.
- **Respect the existing design** — accessibility/UX defects are fixed in place;
  design-altering changes are surfaced as owner decisions.
- **Standards imprint** — an opt-in final phase persists a tailored standards set
  into the reviewed project so quality holds on later iterations.
- **Human-readable report** — Phase 5 also writes a plain-language, non-technical
  report into a top-level `code-review/` directory in the reviewed repo (dated,
  additive), so a founder or leader can act on it without reading the code.
- **No duplication** — the skill has a single home; `SKILL.md` routes to every
  reference; nothing is restated.
- **No fabrication / cite-only-verified** — standards are split into
  directly-fetched (with dates) and by-name in `docs/standards-index.md`.
