# Agent suite roadmap (proposed / living)

> **Status:** a design captured so nothing is lost — **proposed**, pending the
> owner decisions flagged in *Decisions for the owner*. Nothing here is built
> except items marked ✅. The `deep-code-review` **skill name stays stable**
> regardless of any repository/umbrella rename. Dated 2026-09-11.

## BLUF
This repository is evolving from a **portable code-review bar** into a
**stage-aware agentic product-building suite**: a "CEO" orchestrator plus opt-in
specialist skills that support a solo or small builder across a product's whole
life — code, infrastructure, docs, product/PMF, prioritization, discovery,
growth, positioning, and business/ops — while **preventing over-engineering** and
**never fabricating**. One epistemic spine holds every skill together. Navigation
is by **lenses over ~10 skills**, not a sprawl of new ones. Build the spine and the
lowest-risk skills first; add the advisory skills, on the tightest leash, last.

## The epistemic spine (non-negotiable in every skill) — and the differentiator
1. **Frameworks + the user's own inputs + observable evidence.** Apply named
   industry frameworks to the builder's actual context; never invent
   market/financial/competitor facts.
2. **Route the unknowable.** When correctness depends on context the repo/agent
   does not hold (a market number, a legal/tax/securities question), hand it to
   real research or a licensed professional — never conclude on it.
3. **Stage-aware.** Calibrate what to do *and what not to do* to lifecycle stage;
   the floor (security, secrets, auth, data-loss/backups) never relaxes.
4. **Surface uncertainty; skip rather than guess.** Empty beats fabricated.

The market has converged on "AI cofounder / agent team" persona products;
research found their **limits language is near-empty**. So the differentiator is
not more personas — it is **honesty, verification, and stage-awareness**. That is
the white space, and it is exactly this repo's existing thesis.

## Architecture — lenses over ~10 skills (not 70)
A naive `STAGE × AREA` grid invites one skill per cell and detonates the repo's
anti-duplication thesis. Instead, following the pattern `deep-code-review` already
runs (fixed domains + an `archetype → load map` + a role overlay that "never adds
or drops a domain"):

- **Keep ~10 skills; admit a new one only by the admission rule.** A new *skill* is
  justified only when it **cannot** be a lens or reference over an existing skill,
  **or** when a safety boundary requires its own home (the reason the suite is 10, not
  8 — `business-ops` keeps Lane A arithmetic separate from Lane R professional-routing).
  Lenses and references are **not** skill rows; do not count them as such. `STAGE` and
  `AREA` are **lenses** that select and order existing content. The orchestrator routes
  `(stage, area) → (skill, lens)`.
- **Navigation, two layers.** *Passive:* each skill's frontmatter `description` is
  the routing key — disjoint "use when…", one home per skill, no duplication
  (Level-1 metadata is ~100 tokens/skill, so the orchestrator can hold the whole
  map and still route precisely). *Active:* the CEO reads `(stage + need +
  artifact)` and dispatches.
- **The suite map is a registry, not a bundle.** It *describes how to reach* each
  skill; it never holds copies. One index serves agents and humans alike.
- **Topology by work type.** Fan out (3–5 subagents, clear boundaries) only for
  read-mostly, decomposable work (research, audit, review); keep **writing
  single-writer**. Size effort to the project — a small/early project is one agent
  wearing several skill-hats, not a swarm burning tokens.

## Stage model (shared) — ✅ shipped
`prototype → mvp → growth → mature`, calibrating *demands* (urgency), never a
defect's intrinsic severity, and never the floor. Lives in `deep-code-review`
(the first-response `STAGE` field + the *Project stage* section + the going-forward
roadmap). Every advisory skill keys to it.

## The suite (skills and lenses)
| Skill | Status | Role |
|---|---|---|
| `deep-code-review` | ✅ (stage-aware) | The review bar; archetype/role/stage lenses; parallel-audit fan-out |
| `agentic-delivery` | ✅ | Gated G0–G10 build; roles as hats; one writer per worktree |
| `idea-critic` | ✅ | Pre-owner adversarial attack (the critic half of "critic + verifier") |
| `communication-structure` | ✅ | BLUF, one-ask human-facing messages |
| `contribution` | ✅ (hardened — PR #26) | Human-gated, privacy-safe upstream self-improvement |
| agent-readiness lens | ✅ | Is the repo agent-ready? (a `role-coverage.md` lens) |
| `agentic-ceo` (orchestrator) | ✅ vendored (1.37.0) | Suite registry + (stage, area) → (skill, lens) routing + effort-sizing + chaos playbook; defers general delivery/critique to `agentic-delivery` / `idea-critic` |
| `infra-evolution-by-stage` (ref) | Proposed — research done | When to add CI/staging/observability/k8s — extends the going-forward roadmap |
| `docs-evolution-by-stage` (ref) | Proposed — research done | Which docs at which stage; docs acquire normative force as the product matures |
| discovery / validation | ✅ shipped in `product-discovery` (1.36.0) | Design + interpret real user research; never fabricate findings |
| prioritization / focus | ✅ shipped in `product-discovery` (1.36.0) | Riskiest-assumption gate; what to build now vs. defer |
| product-strategy / PMF | ✅ folded into `product-discovery` (1.39.0) — PMF read + Non-goals lens; standalone skill dropped per carve | JTBD, PMF signals, what *not* to build |
| growth / analytics | ✅ shipped in `growth-analytics` (1.38.0) | Retention-first; North Star; what to instrument per stage |
| positioning / branding | ✅ shipped in `positioning` (1.41.0) | VPC → positioning → message house, as a hypothesis; thin guide; never fabricates TAM/competitor/quotes/clearance |
| business / ops | ✅ shipped in `business-ops` (1.42.0) | Lane A pricing/unit-economics (apply) vs. Lane R legal/tax/securities (route); thin guide |
| CEO-under-pressure | Researched → `agentic-ceo` (#36) | Capture losslessly → reflect back → triage → one next action → tracked backlog → support by action (never "calm down") |
| responsible-AI / output safety | Researched → **build first among gaps** (NEW skill) | Govern the harm the product's own outputs do to end-users (NIST AI RMF lens) |
| further areas (gap-analysis) | Researched → *Further areas* + issues | regulated-triage, support-ops, op-readiness, privacy-by-design, decision-hygiene, billing — mostly lenses |

## Build order (research-backed)
1. **Critic + verifier** — ✅ have (`idea-critic`, `deep-code-review`); *assemble*, don't rebuild.
2. **Discovery + PMF-gate** — the top risk-reducer: a coding agent now builds the *wrong thing* faster, so the seat it does not fill (is this worth building?) is the highest leverage. New.
3. **Product-strategy / "what NOT to build"** — governs the coding agent's backlog; prevents gold-plating.
4. **Analytics scoreboard + one primary metric** — tells the builder whether the fast-built thing works; anchors every skill to one axis.
5. **Stage-aware CEO spine** — extend `agentic-ceo` with stage/size-aware routing + the suite registry.
- **Ready now, low-risk:** the `infra-evolution-by-stage` and `docs-evolution-by-stage` references (extend the going-forward roadmap).
- **Defer / lightest touch:** engineering advisor (already covered by the coding agent), design/UX (partly covered + `product-ux-quality`), legal/ops (one-time checklists + a tripwire), fundraising/hiring (stage-gated), positioning/branding + business/ops (highest fabrication-risk → thin "framework + the questions you must answer" guides, built last).

**Sequencing rationale (and the pushback that produced it):** do **not** big-bang a
dozen skills — that is the exact over-engineering the suite exists to prevent, and
it front-loads the riskiest (business/branding) skills before the pattern is
proven. Build the spine + the lowest-fabrication-risk skills first, prove
navigation end-to-end, then add the advisory skills with the tightest leash.

## Per-area boundaries (frameworks by name; the hard line for each)
- **Discovery/validation:** Mom Test, JTBD switch interviews, Teresa Torres
  continuous discovery, assumption/riskiest-assumption mapping, fake-door/concierge
  tests. *Boundary:* design and interpret research the **user runs**; never
  fabricate quotes, personas, market size, or a "validated" verdict; refuse to emit
  an "example finding" (it becomes fake evidence).
- **Product/PMF/prioritization:** riskiest-assumption gate (name it, run the
  cheapest test *before* building — it produces a refusal); PMF read via the
  "very-disappointed" survey + a flattening retention cohort; ICE over RICE for a
  solo builder. *Boundary:* the skill owns the question, structure, and arithmetic;
  it **routes for every input** and never emits a scoring table with invented
  numbers.
- **Growth/analytics:** retention-first (AARRR read bottom-up), a customer-value
  North Star (not vanity metrics), instrument only what answers a named question.
  *Boundary:* no fabricated benchmarks; route real figures to the user's analytics.
  Note: the product-analytics identifier rule *inverts* the ops-observability one
  (a stable per-user id is required for cohorts) — a seam to state, not restate.
- **Positioning/branding:** Value Proposition Canvas → positioning → a message
  house → validation with real buyers; a "minimum viable brand" pre-PMF. *Boundary:*
  frameworks yield a **hypothesis**; the evidence comes from outside the model.
  Never fabricate TAM, competitor claims, quotes, outcomes, or trademark/domain
  clearance. Premature branding/scaling is a documented failure mode.
- **Infra-evolution-by-stage:** infrastructure is *earned*, not provisioned — start
  with one boring, well-modularized deployable; add each layer (CI, staging, IaC,
  observability, containers, orchestration, service extraction) only on a concrete
  observable trigger. *Boundary:* the floor never relaxes; route the six
  business/ops unknowables (real SLA, regulatory class, revenue exposure, funding
  runway, team trajectory, customer concentration) to the owner. Complements
  `infra-iac-containers.md` (how-to-secure) with a when-to-add lens.
- **Docs-evolution-by-stage:** docs acquire **normative force** as the product
  matures — one-pager (persuade) → design-doc/RFC (decide) → spec (contract,
  CI-enforced); trigger, not calendar. Agent-legibility = a small always-loaded
  router + depth routed with "read this when…". Complements `docs-and-dx.md`.
- **Business/ops (asymmetric boundary):** *Lane A — arithmetic* (pricing, unit
  economics): **apply** to the builder's own numbers with the formula and every
  assumption shown, flag thin data — but never turn arithmetic into a directive.
  *Lane R — regulation-dependent* (legal, tax, securities, employment
  classification, privacy compliance): **route to a licensed professional, never
  conclude**; fundraising (selling equity/SAFEs is a securities offering) *is* the
  boundary crossing. Standing disclaimer: educational information, not advice.

## The product ↔ user ↔ agent loop ("growing together")
Two nested build-measure-learn loops. **Loop 1** (the builder's product): the agent
structures feedback and proposes experiments; the human decides. **Loop 2** (the
suite's own improvement): capture each interaction → evaluate with a *split* rubric
(**deterministic gates** for the hard axes — boundary-compliance and
non-fabrication, because a fluent wrong answer fools an LLM judge; **LLM-judge, and
a decorrelated one, for the soft axes** only) → ratchet only through the
human-gated, generalization-checked `contribution` flow. Quality **only ratchets
up**: a regression gate stops backsliding, generalized eval cases raise the floor,
and a human authorizes every landing. The fuel is verified eval cases and
citations — not hoarded user data.

## Additive principles (generalized from field practice and research)
- **Registry, not a bundle** — describe how to reach things; never duplicate them.
- **Store the query, not the answer; audit memory automatically** — a stored status
  rots silently; store how to re-derive it, and flag memories that stopped being true.
- **Issue contract: Where / Done-when / Verify / Why** — "Verify" is load-bearing;
  without it "done" is an opinion. Used for this repo's own backlog issues.
- **Unreadable must never look like empty** (= the repo's `UNVERIFIED`); **enforce
  rules in code, not prose** (= `contribution`'s `kernel-paths.txt` gate); **deny by
  default**. These validated recent work rather than changing it.

## CEO under pressure (chaos playbook) — folds into `agentic-ceo` (#36)
When the owner floods the orchestrator with many rapid, conflicting asks under real
pressure, the failure is to freelance (obey the last thing, drop the rest, act on
colliding orders) or to patronize ("calm down"). Support is **by action, not
affect** — six moves in order:
1. **Capture losslessly** — every request/aside becomes a numbered logged item
   before any judgement; tag request vs. context; nothing filtered or merged.
2. **Reflect the full list back** — the played-back numbered list *is* the
   acknowledgement; name any collision between items as its own finding.
3. **Triage to the vital few** — a sequential first-hit-wins chain: blocks-others or
   irreversible → Now; failing on the live surface → Now; time-critical but
   reversible → Next; else → Held (visible, not dropped).
4. **One highest-leverage next action** — the lead domino + a one-line why, offered
   as the existing A/B decision so the owner keeps final say.
5. **Hold the rest as a tracked backlog** — each item has a visible state (in-flight
   / next / held / dropped-with-reason); WIP-limit to one primary action.
6. **Support by action** — acknowledge the stakes as legitimate, show the list, name
   the move. **Forbidden:** "calm down"/"relax" (reactance + invalidation), toxic
   positivity, minimizing, narrating their feelings, "on it!" with nothing captured,
   silently absorbing conflicting orders.

Boundary: the agent is an **organizer, not a therapist** — the calm comes from the
system being visibly under control. Capture-mode is **not** yes-mode: it still
surfaces real disagreement (conflicts, quality-bar breaches, spread-thin mediocrity)
in one line with the standard cited, then the owner decides. Frameworks (by name):
GTD capture/clarify, incident command (single commander, unity-of-command, activity
log), emergency-severity triage, WIP limits, "the ONE thing," psychological
reactance, motivational-interviewing reflective listening.

## Further areas (from gap-analysis)
The suite is strong on builder + product + code; the gap is the **end-user runtime
axis** (what the product does to people once live) plus **operational readiness for
the bad day**. Mostly **lenses** over existing skills, not new skills. Ranked:
- **G1 · Responsible-AI / product-output safety** — NEW skill; govern harm from the
  product's own outputs (bias, hallucination-as-fact, missing AI-disclosure,
  deceptive patterns, unsafe automation). NIST AI RMF (GOVERN/MAP/MEASURE/MANAGE)
  lens; measure via the eval harness (domain J); human-in-the-loop on high-stakes
  outputs. **The defining hole for an agentic-*product* suite — build first.**
- **G2 · Regulated-domain obligation triage** — small lens; a design-time decision
  tree (health? payments? minors? EU data? biometrics? consequential decisions?)
  that names the regime and routes **before** architecture hardens; re-runs on
  entering a new market. Cheapest build, earliest bite; unblocks G4/G5.
- **G3 · Support & feedback operations** — lens; intake/triage/SLA + support→backlog.
- **G4 · Operational readiness** — lens over `agentic-delivery` postmortem + M/Q:
  incident-response runbook, severity + comms + status page, break-glass access,
  credential/renewal inventory with dead-man reminders, solo-founder succession.
- **G5 · Privacy/compliance by design (product artifacts)** — lens over Q: data
  inventory/ROPA, DPIA scaffold, consent-UX spec, subprocessor list; coupled to G2.
- **G6 · Decision hygiene for the builder's own calls** — a routed reference
  **extending `idea-critic`** (one-/two-way doors, base rates, kill criteria set up
  front) — not a new skill.
- **G7 · Billing / monetization system correctness** — a routed `deep-code-review`
  reference (metering, proration, dunning, tax, webhook idempotency, double-charge
  races) — mechanics of E/F/G/I applied to revenue.
- **Conditional:** G8 trust & safety / abuse (multi-user products), G9 vendor
  business-risk, G10 accessibility-as-design (mostly redundant with domain P).
- **Do NOT build (redundant):** cost / i18n / a11y-code-gate / supply-chain /
  data-integrity — already covered. **Owned by planned skills (name in their
  charters):** scope-defense → prioritization; data-as-moat → product-strategy;
  event-taxonomy → growth; pricing-strategy → business-ops; cloud right-sizing →
  infra-by-stage.
- **Boundary (all gaps):** inventory / scaffold / checklist / red-team / cite-only-
  what-was-fetched; **never** fabricate a statute, deadline, CWE, or metric; route
  every legal/regime determination to a licensed professional. Legal specifics stay
  **by-name / UNVERIFIED** until fetched (as `privacy-compliance.md` already does).
  The NIST AI RMF core function names (Govern/Map/Measure/Manage) are confirmed
  (`docs/standards-index.md`); its AI RMF 1.0 / Generative AI Profile control
  specifics and GDPR/DPIA/COPPA/PCI/breach-clock specifics were not — fetch before
  citing.
- **Build first among gaps:** G1, then G2 (unblocks G4/G5), then G3.

## Decisions for the owner (open)
1. **Rename / umbrella.** Defensible now that scope has widened (candidate: a
   Slavic-mythology theme, e.g. a "Perun" orchestrator, as a *thin* identity layer
   over functional skill names). Keep the `deep-code-review` skill name. Execute
   only after the spine is proven; owner picks the name; a migration checklist ships
   with it. GitHub auto-redirects the old repo URL, so the blast is mostly README /
   marketplace slug / `plugin.json` name.
2. **`agentic-ceo`:** ✅ **resolved — vendored into this repo** (1.37.0, the suite
   conductor). Chosen over reference-global so the suite stays portable; coexists
   with any global skill of that name via project-scoping.
3. **Business-advisory skills:** full "advisor" skills, or thin "framework + the
   questions you must answer yourself" guides? (Recommendation: thin guides — lowest
   fabrication surface.)
4. **Suite scale (#66):** ✅ **resolved — keep ~10 under a written admission rule**
   (Architecture §). A new *skill* must fail the "can this be a lens/reference over an
   existing skill?" test **or** be a safety boundary; otherwise it lands as a lens/ref,
   and lenses/refs are not counted as skill rows. Applying it to the gap backlog:
   **#43–#49 are lenses/references** over existing skills; only **#42
   (product-output-safety / responsible-AI)** is admitted as standalone **skill #11** —
   output-harm governance is a distinct method from code-security and is a safety
   boundary. Residual risk: if #42 drafts thin, fold it as a `deep-code-review` lens
   rather than ship a standalone skill.

## Status ledger (2026-09-11)
- **Suite complete + hardening — main @ 1.47.0, 10 skills.** Shipped: contribution overlay
  (1.31.0) · agent-readiness lens (1.32.0) · stage-aware review + going-forward roadmap
  (1.33.0) · contribution hardening (1.34.0; contribution 1.1.0) · infra/docs
  stage-evolution refs (1.35.0) · `product-discovery` (1.36.0, +Non-goals 1.39.0 →
  1.1.0) · `agentic-ceo` conductor (1.37.0, +full registry 1.43.0 → 1.1.0) ·
  `growth-analytics` (1.38.0) · `positioning` (1.41.0) · `business-ops` (1.42.0) ·
  no-slop output contract (`communication-structure` → 1.2.0, at 1.40.0). Each new
  skill passed an independent reviewer pass before merge.
- **Post-build hardening (1.44–1.47):** suite-enumeration gate (1.44.0, #62) · DCR
  fabrication-refusal eval (1.45.0, #65) · `--recommend` surfaces advisory overlays
  (1.46.0, #68) · README "which skill when" quickstart (#67) · offline eval-predicate
  discrimination gate (1.47.0, #61 slice 1). Global install content-current (no skill
  content changed since 1.43.0).
- **Owner decisions:** #39 (agentic-ceo) **resolved — vendored**; #40 (business-advisory
  shape) **resolved — thin guides**; #38 (rename) **deferred** until the suite is proven.
- **Post-build backlog (filed):** #61 live eval harness · #62 suite-enumeration gate ·
  #63 routing eval coverage · #64 eval-id anti-drift gate · #65 DCR fabrication eval ·
  #66 [decision] suite scale — ✅ resolved (~10 + admission rule) · #67 README quickstart · #68 `--recommend` surfaces
  advisory skills · #69 dogfood the contribution loop. Gap-analysis skills: #42–#49.
- **Research complete:** all 12 areas + CEO-under-pressure + gap-analysis. CEO-under-
  pressure shipped in `agentic-ceo`'s chaos playbook.

*This document is provisional and updated as skills ship. Decisions #39 (vendor),
#40 (thin guides), and #66 (suite scale) are resolved and executed; #38 (rename)
remains deferred. The suite is 10 skills under a written admission rule (Architecture
§); #42 (product-output-safety) is the one admitted standalone candidate — skill #11.*
