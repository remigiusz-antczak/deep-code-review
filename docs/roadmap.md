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
is by **lenses over ~8 skills**, not a sprawl of new ones. Build the spine and the
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

## Architecture — lenses over ~8 skills (not 70)
A naive `STAGE × AREA` grid invites one skill per cell and detonates the repo's
anti-duplication thesis. Instead, following the pattern `deep-code-review` already
runs (fixed domains + an `archetype → load map` + a role overlay that "never adds
or drops a domain"):

- **Keep ~8 skills.** `STAGE` and `AREA` are **lenses** that select and order
  existing content. The orchestrator routes `(stage, area) → (skill, lens)`.
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
| `agentic-ceo` (orchestrator) | Exists (global) — **extend, don't clone** | Routes to the right skill; stays strategic; sizes its own effort to stage |
| `infra-evolution-by-stage` (ref) | Proposed — research done | When to add CI/staging/observability/k8s — extends the going-forward roadmap |
| `docs-evolution-by-stage` (ref) | Proposed — research done | Which docs at which stage; docs acquire normative force as the product matures |
| discovery / validation | Proposed — research done | Design + interpret real user research; never fabricate findings |
| prioritization / focus | Proposed — research done | Riskiest-assumption gate; what to build now vs. defer |
| product-strategy / PMF | Proposed — research done | JTBD, PMF signals, what *not* to build |
| growth / analytics | Proposed — research done | Retention-first; North Star; what to instrument per stage |
| positioning / branding | Proposed — research done | VPC → positioning → messaging; highest fabrication-risk → thin guide, built last |
| business / ops | Proposed — research done | Pricing/unit-economics (apply) vs. legal/tax/securities (route); built last |
| CEO-under-pressure | Under research | Handle a flooding, high-stakes user: capture → triage → focus, support by action |
| further gaps | Under research | Gap-analysis agent hunting missing areas/edges |

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

## Decisions for the owner (open)
1. **Rename / umbrella.** Defensible now that scope has widened (candidate: a
   Slavic-mythology theme, e.g. a "Perun" orchestrator, as a *thin* identity layer
   over functional skill names). Keep the `deep-code-review` skill name. Execute
   only after the spine is proven; owner picks the name; a migration checklist ships
   with it. GitHub auto-redirects the old repo URL, so the blast is mostly README /
   marketplace slug / `plugin.json` name.
2. **`agentic-ceo`:** vendor it into this repo, or keep it global and reference it?
3. **Business-advisory skills:** full "advisor" skills, or thin "framework + the
   questions you must answer yourself" guides? (Recommendation: thin guides — lowest
   fabrication surface.)
4. **Greenlight + order** of the new skills beyond the ready references.

## Status ledger (2026-09-11)
- **Merged to main:** contribution overlay (1.31.0) · agent-readiness lens (1.32.0)
  · stage-aware review + going-forward roadmap (1.33.0). Global install refreshed.
- **Open for owner review:** PR #26 — contribution hardening (1.34.0), left open on
  purpose (self-improvement changes deserve human review).
- **Proposed / not built:** everything in *Build order* beyond the ✅ items; tracked
  as GitHub issues using the *Where / Done-when / Verify / Why* contract.
- **Under research:** CEO-under-pressure, and a gap-analysis of remaining areas.

*This document is provisional and will change as skills are built and decisions are
made. It executes none of the open decisions above.*
