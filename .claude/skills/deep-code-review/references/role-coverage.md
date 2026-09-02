# Role & security-team review overlay

Read this when you drive the review through a **delivery role** (architect,
product & requirements, UX/UI, frontend, backend API & database, data & AI,
platform/DevOps/SRE, QA/performance/accessibility, release & docs) or a
**security-team colour** (Red / Blue / Purple / Yellow / Green / Orange / White /
Black), when you **split a fan-out by role or colour**, or when you need the
checklists `SKILL.md` routes here but does not itself hold: **architecture
quality**, **lightweight product planning**, **SLI/SLO error-budget & burn-rate**,
and **release owner sign-off**. Expands the compact overlay in `SKILL.md`.

**The overlay never changes *what* is reviewed — only who leads and in what
order.** Every role and colour is a lens over the same A–S domains and the same
evidence rules (principle 1: `file:line` or it didn't happen; principle 3: no
fabrication). A role that "owns" a domain does **not** get to skip the others — it
gets first read and the deepest checklist there, and the coverage ledger still
reconciles every applicable domain (Phase 5). Use the overlay to (a) frame a
review for a specific reader, (b) assign fan-out units without leaving a domain
orphaned, or (c) make several role-reviewers add up to one whole-target audit.

---

## Role → domain map (who leads on what)

| Role | Leads on (domains A–S) | Deep refs | Extra lens (below) |
|---|---|---|---|
| **Architect** | A E G H I | — (structure is cross-cutting) | **Architecture quality** |
| **Product & requirements** | A O J | `docs-and-dx.md` | **Lightweight product planning** |
| **UX & UI** | P R | `frontend-a11y.md` | — |
| **Frontend** | P · A (client logic) · B (client-side authz/XSS) · N (no secrets in bundle) | `frontend-a11y.md`, `security-appsec.md` | — |
| **Backend (API & DB)** | B I E A G | `security-appsec.md`, `api-contracts.md`, `performance-db-cost.md` | — |
| **Data & AI** | D C E J Q | `data-quality.md`, `security-ai-agents.md`, `privacy-compliance.md` | — |
| **Platform / DevOps / SRE** | L K M N F | `infra-iac-containers.md`, `observability.md`, `reliability-error-handling.md` | **SLI/SLO, error budget & burn-rate** |
| **QA / performance / a11y** | J E P | `testing-and-evals.md`, `performance-db-cost.md`, `frontend-a11y.md` | — |
| **Release & docs** | S O K | `branch-and-merge-hygiene.md`, `docs-and-dx.md` | **Release owner sign-off** |

Roles overlap on purpose — B is read by frontend, backend, and data; E by
architect, backend, data, SRE, and QA. Overlap is not duplication of *work*: the
owning role writes the finding, the others cross-reference it. When roles review in
parallel, the lead reconciles overlaps so a compound (Phase 4) that spans two
roles — a frontend gap that disables a backend gate — is seen by someone who holds
both returns.

---

## Per-role lenses (the depth `SKILL.md` doesn't hold)

Domains already have their own references; this section adds only what the A–S
checklists do **not** cover. For UX/UI, frontend, backend, data & AI, and
QA/perf/a11y the lens **is** the linked domain refs above — no new checklist, just
first-read ownership.

### Architect — architecture quality

Beyond the per-function correctness of A and the local perf of E, judge the
**shape** of the system. These are design questions; separate architecture
*defects* (fix in place) from *redesigns* (owner decision — principle 5).

- **Boundaries & seams.** Are module/service boundaries drawn along change axes
  (things that change together live together)? Is there a business-logic layer
  distinct from transport/controllers/views, or is logic smeared into handlers?
- **Dependency direction.** Dependencies point toward stable abstractions; no
  import cycles between modules; volatile details (DB, framework, vendor SDK) sit
  at the edges, not the core. A cycle or an inward-pointing vendor dependency is a
  maintainability finding (cross-ref H).
- **State ownership.** One writer / single source of truth per datum (cross-ref D
  and G); no two components authoritatively owning the same field. Name the owner
  of each shared datum.
- **Scaling posture & SPOFs.** What breaks at 10× load or 10× data? Which
  component is a single point of failure or a serialization bottleneck? Is state
  externalized so instances scale horizontally, or is there hidden per-instance
  state (cross-ref G lifetime bugs)?
- **Failure-domain isolation.** A failure in one component is bounded by
  timeouts, bulkheads, and circuit breakers (cross-ref F), not propagated as a
  cascading outage. Control-plane paths (kill-switch, approval) route **above** the
  rate limiter (F).
- **Consistency model stated & matched.** Strong vs eventual consistency is a
  deliberate choice tied to the need, not an accident of the datastore default.
- **Evolvability over speculative generality.** Extension points exist where the
  next likely change lands; premature abstraction and one-caller "frameworks" are
  their own cost (cross-ref H — three similar lines beat a wrong abstraction).
- **Drift from the stated architecture is the finding.** Reconcile the code
  against the documented architecture (C4 / ADRs — domain O). A diagram that no
  longer matches the code is a docs defect *and* a signal the design eroded;
  neither the diagram nor a free redesign is automatically correct — surface the
  gap and let the owner rule.

### Product & requirements — lightweight product planning

Judge whether the code serves the actual **need**, not a plausible adjacent thing
(principle "does what the user needs" — domain A). This is planning discipline at
review time, not a PRD.

- **Problem → acceptance.** Is the problem statement explicit, and does each
  acceptance criterion map to a test or eval (domain J)? An acceptance criterion
  with no test is `unverified`, not "done."
- **Smallest slice that delivers the outcome.** Flag over-build as cost
  (cross-ref E useless-work): code, config, or a dependency added for a need no
  one has stated yet.
- **Non-goals stated.** Explicit out-of-scope prevents a *deliberately* absent
  feature from being mis-filed as a defect — and prevents scope creep from being
  waved through as "while we're here."
- **Success metric defined and measurable.** "How will we know it worked?" ties
  to D (data quality) / J (evals). A feature with no observable success signal
  can't be judged to have shipped value.
- **Prioritization mirrors severity discipline.** Must-have vs nice-to-have maps
  onto the severity rubric; a nice-to-have gap is a Low/Nit, never a Blocker.
- **Product ideas are owner decisions.** Redesign/scope proposals go under
  **Decisions needed (owner)** and never carry Blocker/Critical gate language
  (Phase 5) — unless a product choice *creates* a real defect, in which case the
  defect (not the choice) is rated on consequence.

### Platform / DevOps / SRE — SLI/SLO, error budget & burn-rate

Domains L/K/N/M/F own the artefacts; this lens owns the **reliability contract**.
An SLO with no SLI you actually measure is aspirational — hold it to principle 2
(enforcement artefact, not the doc).

- **SLI — a signal of user-facing health**, measured at the user boundary, not an
  internal proxy: availability, latency at a percentile (P95/P99), error rate,
  freshness, or — for a data/AI pipeline — a **quality** dimension (D's six),
  since "up" isn't "correct." Name where each SLI is actually computed
  (cross-ref M); an SLI defined only in a doc is `unverified`.
- **SLO — a target over a rolling window** (e.g. 99.9% over 30 days) that reflects
  a real user need, not a round number. State the window; a target with no window
  is unmeasurable.
- **Error budget = 1 − SLO** — the allowed unreliability for the window. It is
  *spent* by incidents and risky changes; when it is exhausted, risky change
  **freezes** until it recovers. An error budget nobody consults is decoration.
- **Burn-rate alerting beats a static threshold.** Prefer **multi-window,
  multi-burn-rate** alerts — a fast burn (large budget fraction in a short window)
  **pages**; a slow burn (smaller fraction over a long window) **tickets** — so a
  single static line doesn't both miss slow erosion and page on noise. Alerts on
  the control path route above the limiter (F).
- **Toil & rollback.** A documented, *tested* rollback path (cross-ref E
  migrations, F) and a clean no-op degrade without each credential (N) are part of
  the reliability contract, not extras.

### Release & docs — release owner sign-off

A release is a decision with a **named human owner**, not an automatic
consequence of a green pipeline. The agent **prepares and advises; it does not
self-approve, merge, or push to a protected branch** (principle 7).

- **Sign-off checklist** (all must hold, each cited): aggregate gate green with
  exit code confirmed (Phase 1); **zero Blocker/Critical**, every High either
  fixed or explicitly owner-accepted; rollback path tested (E/F); branch & open-
  work triage done (domain S); docs/CHANGELOG updated (O/K); privacy/name gate
  clean over anything committed (Phase 5).
- **Security rides its own PR.** A change to an auth/permission/authz boundary is
  split onto a separate PR for a decorrelated reviewer (Phase 5) — its sign-off is
  independent of the routine release, never buried under nit commits.
- **Record the sign-off** — who accepted, at what ref, what risk was accepted —
  so the decision is auditable (cross-ref A09) and reconstructable later (O — ADR
  / release notes). "It passed CI" is not a sign-off; a named owner accepting a
  named risk is.

---

## Security-team colours (a lens over the same evidence)

The colours re-package the same A–S work by adversarial stance. They add **no new
findings rules** — Red still needs `file:line`, Blue still fails closed, every
claim is still snippet-or-drop at `START_SHA`.

| Colour | Stance | Drives (in this method) |
|---|---|---|
| **Red** | Attack | Phase 3 adversarial pass — anon-GET sweep, two-principal swap, injection/SSRF/traversal, ASI01–ASI10, exhaustion, races. |
| **Blue** | Defend | Detection & fail-closed posture — M (observability, alerting), F (fail-closed error paths), A09 (logging/alerting), runtime-proven gates (B). |
| **Purple** | Red ⇄ Blue | Turns every red finding into a blue gate or detection; Phase 4 **compounds** and the **Invariants-verified-to-hold** ledger are the purple deliverable. |
| **Yellow** | Build | Constructive quality — A (correctness), H (maintainability), I (contracts), plus **architecture quality** above. |
| **Green** | Yellow + Blue | Defensive lessons become **build-time gates** — K (CI gates, SHA-pinned actions), self-proving gates, Phase 6 standards imprint. |
| **Orange** | Yellow + Red | Attacker lessons become **design constraints** — A06 insecure-design abuse rows, Phase 0 banned-remedies/revert-invariants, secure-by-default. |
| **White** | Govern | Scope, ROE, authorization, confidentiality, owner decisions, and **release sign-off** — the referee that sets the rules and reconciles coverage (this is the lead's synthesis role, not a compute unit). |

### Black Team — the agent boundary is **absolute**

Black is the **physical / human-operations** lens: physical intrusion,
impersonation, social engineering, surveillance, badge or lock bypass, device
placement, covert access, and tests directed at real people or real sites.

> **An agent may only *plan*, *tabletop*, and *analyse evidence the owner
> supplies*. It must never *perform* or *operationally direct* any of those
> actions, and never test a real person or a real site.** Real physical and social
> assessments are **human-led, under written owner authorization and legal rules
> of engagement (ROE)**.

Concretely, in scope for an agent: threat-modelling a physical/social vector on
paper; a tabletop walkthrough; reviewing photos, logs, floor plans, or reports the
owner provides; drafting an ROE or an assessment plan **for humans to execute**;
and reviewing code/config that a physical or social attack would target (badge
systems, door controllers, MFA-reset flows, help-desk scripts) as ordinary
appsec. Out of scope, no exceptions: doing, simulating against live targets,
instructing anyone to do, or providing operational how-to for any of the actions
above. If a request crosses this line, refuse the operational part, keep the
planning/analysis part, and say which is which.

---

## Role-keyed fan-out

When the target is large enough to fan out (Phase 2; `references/parallel-audit.md`
governs the mechanics), the **role or colour map is a natural way to cut the
units** — one unit per role-cluster (the role's "leads on" domains) or per colour
(a Red adversarial unit, a Blue detection unit). Keying by role is a labelling of
the units, not a new contract:

- **Every unit inherits the parallel-audit contract** — read-only toolset, pinned
  `START_SHA`, identifier masking on returns, and lead re-verify at source before
  a finding enters the report. A role label never relaxes it.
- **The coverage ledger records the unit by role/colour plus finder id and
  lead-read `Y/N`** (Phase 0/5). A role unit whose finder didn't complete is
  `unverified`, never absorbed into an implied all-clear — the same no-silent-caps
  rule as any fan-out.
- **The lead still reads the top-N highest-blast-radius files independently**
  (Phase 2), across role lines, so role silos can't hide a cross-role compound and
  a hardened, zero-survivor fan-out still has a non-empty confidence basis.
- **White is not a compute unit** — it is the lead's own synthesis, scope, and
  ROE role. **Black is planning-only** — a "Black unit" produces a tabletop or an
  assessment plan from owner-supplied evidence, never an executed or live-simulated
  test (boundary above).
- **Refused delegation falls back to the audit, not a skip** (Phase 2): if a
  specialized subagent rejects a role prompt, retry once general-purpose or run it
  in-process under the same contract, and note the substitution.

---

Cross-references: fan-out mechanics and the anti-fabrication contract in
`references/parallel-audit.md`; architecture-of-record (C4/ADR) and release/docs
hygiene in `references/docs-and-dx.md`; the SLI signals themselves in
`references/observability.md`; the adversarial procedures Red drives in
`references/security-appsec.md` and `references/security-ai-agents.md`; the
severity, gate, and report format that all roles share in `SKILL.md`.
