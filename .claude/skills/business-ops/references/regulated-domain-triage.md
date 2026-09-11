# Regulated-domain obligation triage — the design-time front door

**Read this when** a product is being designed or is about to enter a new
market, and you need to know *which regimes might apply before the architecture
hardens* — the most expensive rework class is discovering a regime binds after
building. This is the operational decision tree for **Lane R**: it runs the
triage at design time and **names + routes**; it does not restate Lane R's
asymmetric boundary (see `SKILL.md`) and it never concludes that a regime binds.

## Boundary (name and route — never determine that a regime binds)

- **In scope:** ask the trigger questions, **name** the likely regime(s), and
  list the engineering obligations each one *typically* implies **as leads to
  verify**, not as settled facts. Re-prompt when the product enters a new
  market or starts handling a new data type.
- **Out of scope — route to a licensed professional:** whether a regime
  **actually binds** this business, its thresholds, its deadlines, and what
  compliance requires. That is a legal determination (Lane R → counsel), never
  concluded here.
- **No fabrication.** Regimes are named **by name only**; no article numbers, no
  dollar/record thresholds, no deadlines, no "this applies to you" — those stay
  `UNVERIFIED` until fetched, logged, and confirmed with counsel.

## How to run

Ask each trigger below. On any *yes* (or *maybe*), name the regime, surface the
engineering-obligation leads, and route the binding question to counsel. Several
can fire at once — a product can be in multiple regimes.

## The tree (trigger → regime named → engineering leads)

- **Health / medical data?** (diagnoses, treatment, health status, fitness data
  used clinically) → likely **HIPAA** (US) and other health-privacy regimes →
  leads: access controls, audit logging, encryption, business-associate
  relationships, breach handling. Route the "are we a covered entity / business
  associate" question to counsel.
- **Payments / card data?** (you touch card numbers or handle cardholder data) →
  **PCI DSS** (a card-industry standard, not a statute) → leads: minimize card
  data in scope, prefer a compliant processor/tokenization so raw card data never
  hits your servers, network segmentation. Route scope/attestation level to a
  QSA/processor.
- **Minors / children likely in the audience?** → **COPPA** (US) and
  age-appropriate-design regimes → leads: an age signal, server-enforced gating
  of collection and personalization, parental-consent flows. Route the
  "does it apply / verifiable-consent method" call to counsel.
- **EU or UK personal data?** → **GDPR / UK GDPR** → leads: the pre-code
  artifacts in `deep-code-review`'s `privacy-by-design.md` (processing register,
  DPIA scaffold, consent-UX, subprocessors, residency) and the code-layer
  obligations in its `privacy-compliance.md`. Route lawful-basis and
  DPIA-required to counsel.
- **US state privacy** (California residents, and other US state regimes)? →
  **CCPA / CPRA** and peer state laws → leads: data inventory, opt-out of
  sale/share, deletion/access request handling (same engineering refs as above).
  Route applicability/thresholds to counsel.
- **Biometrics?** (face, fingerprint, voiceprint, retina) → biometric-privacy
  regimes (several US states have specific statutes) → leads: explicit consent,
  strict retention limits, a deletion path. Route which statute(s) apply to
  counsel.
- **Consequential or automated decisions?** (credit, employment, housing,
  insurance, or other decisions with legal/similar effect on a person) →
  emerging automated-decision / anti-discrimination regimes → leads: human
  oversight, contestability, bias testing — cross-ref `product-output-safety`
  for the output-harm method. Route legal applicability to counsel.
- **Money movement beyond your own product's sale?** (holding, transmitting, or
  moving other parties' funds) → money-transmission / financial-services
  regulation → leads: this is rarely a build-first domain. Route to counsel
  early; cross-ref Lane R (fundraising/securities is a separate Lane-R crossing).
- **Selling to enterprises / security posture demanded?** → buyer-driven
  frameworks like **SOC 2** or **ISO 27001** (not law, but contractual
  obligations that shape architecture) → leads: access control, logging, change
  management, vendor management, an evidence trail from day one. Route the
  audit/scope decision to the owner + an auditor.

## Re-prompt triggers (the tree is not one-and-done)

Re-run the triage when the product: enters a new country/state, adds a new
category of personal or sensitive data, starts serving a new audience (e.g.
minors, healthcare), begins moving money, or takes on an enterprise buyer with a
security questionnaire. A regime that did not apply at launch can apply after a
market move.

## Verification

- A **health / payments / minors** input yields a **"route to counsel + named
  regime"** with engineering leads — never a compliance conclusion and never a
  "this applies / does not apply to you" verdict.
- Regimes are named by name only; no article number, threshold, or deadline is
  asserted.
- The privacy branches point to `privacy-by-design.md` and `privacy-compliance.md`
  for the downstream engineering rather than restating them.
