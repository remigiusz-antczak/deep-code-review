# Support & feedback operations — the compounding solo time-drain

**Read this when** the product has users who file tickets, bug reports, or
feature requests, and you need a support system that scales without eating the
operator alive: an intake + triage taxonomy, an SLA, canned-response quality, and
the support→backlog loop. Narrow scope — this is *reactive support ops*, **not**
onboarding/activation (that is growth / product-ux) and **not** the help-center's
content model (that is Diátaxis in `deep-code-review`'s `docs-and-dx.md`).

## Boundary (draft and scaffold; never speak for the business without approval)

- **In scope:** draft the triage taxonomy, the SLA template, canned-response
  drafts, and the ticket→work-item conversion.
- **HARD safety gate — never auto-send an external reply, and never make a
  promise, commitment, refund, or compensation** on the operator's behalf. Every
  outward reply and every money/policy commitment is **owner-approved before it
  leaves.** A support reply is an external action — the same
  human-approval-on-external-action gate this skill applies to push/deploy.
- **No fabrication:** no invented SLA number, no made-up ticket volume, no
  promised fix date the owner has not agreed to.

## Intake & triage taxonomy

- **One intake, classified on arrival.** Every ticket gets a type (bug / how-to /
  feature-request / billing / outage) and a severity, on entry.
- **Severity mirrors the incident scale** when a ticket signals an outage
  (cross-ref `references/incident-response.md`) — a "site is down" ticket is an
  incident, not a support email.
- **Deduplicate to signal — on a reproducible match, not resemblance.** Many
  tickets describing one defect are one backlog item with a count. But before
  closing any as duplicate, confirm a reproducible match and migrate any unique
  context to the canonical item **first**; resemblance alone is `UNVERIFIED`
  (SKILL.md principle 9 — closing shared state needs evidence, not presumption).
- **Billing tickets split by kind.** A billing *defect* (wrong charge,
  double-charge, bad proration) is a bug → `deep-code-review`'s
  `billing-correctness.md`; a refund or pricing *policy* question → the
  `business-ops` overlay if installed, and the refund action itself stays
  owner-gated (above).

## SLA (template — owner sets the numbers)

A first-response and a resolution target **per severity**, set by the owner (not
a fabricated figure), plus a way to see whether it is being met. An SLA with no
measurement is aspiration, not a control — instrument it and watch the signals
(cross-ref `deep-code-review`'s `observability.md` for the measure-your-SLOs
discipline).

## Canned-response quality

- Clear, honest, and specific — no slop, no false cheer, no commitment the owner
  has not approved. The output-quality rule lives in `communication-structure`;
  apply it, do not restate it.
- A canned response is a *starting draft a human sends*, not an auto-reply. It
  follows the same honesty-over-polish structure as incident comms — read
  `references/incident-response.md`'s Comms templates and apply it, don't restate
  it here.

## The support→backlog loop (the part that compounds)

A ticket that reveals real work becomes a **well-formed work item** using the
delivery **work-item contract** — Where / Done-when / Verify / Why (see the
Output-contract section of `SKILL.md`) — prioritized into the backlog. This is the
loop that turns reactive support into product improvement instead of a bottomless
inbox: the ticket carries the *symptom*; the work item carries the *Done-when*
that closes it. A ticket closed without either a fix or a logged, prioritized
work item is a **dropped signal**.

## Help-center (route, don't restate)

Deflect repeat tickets with a help-center structured on **Diátaxis** (Tutorials /
How-to / Reference / Explanation) — the content model lives in `deep-code-review`'s
`docs-and-dx.md`; read that for the structure. A recurring how-to ticket is a
missing how-to guide, not just another reply.

## Verification

- A ticket describing real work becomes a **well-formed backlog item** (Where /
  Done-when / Verify / Why), not just a closed reply.
- **No external reply, promise, refund, or commitment is auto-sent** — each is
  owner-approved before it leaves.
- SLA numbers are the owner's, not fabricated; a recurring how-to ticket routes
  to a help-center gap.
