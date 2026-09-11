# Privacy & compliance by design — pre-code product artifacts

**Read this when** the product will face a privacy-regulated user (EU/UK,
California, children, and the like) or an enterprise buyer and needs the
privacy/compliance *artifacts that sit above the code* — a processing
register, a DPIA scaffold, a consent-UX spec, a subprocessor list, or
data-residency options. This is the product-artifact lens over domain Q. The
*engineering* obligations at the code layer — data inventory by grep,
minimization, retention/DSAR/erasure jobs, consent recording, analytics
allow-lists, licenses — live in `privacy-compliance.md`; **read that for the
code, this for the pre-code scaffolds.** Do not restate its detection procedure
here.

Frameworks are named **by name only** (GDPR, UK GDPR, CCPA/CPRA, and the rest as
in `privacy-compliance.md`). **No article numbers** for ROPA, DPIA, or lawful
bases until fetched and logged in `docs/standards-index.md` (repo) or
`references/standards-index.md` (post-install) — describe the artifact, not an
unverified clause. A review/scaffold aid, not legal advice.

## Boundary (scaffold and gap-detect; the legal calls are the owner's + counsel)

- **In scope:** produce the *scaffolds* and detect *gaps* — an empty register row
  with no owner, a new PII field with no purpose, a subprocessor with no
  data-flow note, a consent flow that cannot record withdrawal.
- **Out of scope — route to counsel:**
  - the **privacy-policy / ToS text** itself;
  - **whether a DPIA is legally required** for this processing;
  - **which lawful basis** applies (consent vs legitimate interest vs contract).
- **No fabrication:** no invented article number, no asserted legal deadline, no
  claim that the product "is GDPR-compliant." Empty-and-routed beats
  confident-and-wrong.

## The artifacts

### 1. Processing register (ROPA-style)

A living table an enterprise buyer or regulator can be shown: *what personal
data, for what purpose, on what basis (labeled, owner-confirmed), where stored,
how long, who it is shared with, where it leaves the region.* The code-level
field inventory in `privacy-compliance.md` *feeds* this register; this is the
business-readable roll-up, not a second grep. A processing activity with no named
owner or no stated purpose is the gap to surface.

### 2. DPIA scaffold + risk questions

A template with the risk questions to answer — nature, scope, and context of the
processing; necessity and proportionality; risks to individuals; mitigations —
**not** a determination that a DPIA is required or complete. High-risk signals to
raise for counsel: large-scale sensitive data, systematic monitoring, automated
decisions with legal or similarly significant effect, children's data. Fill the
scaffold; route the "is it required / is it sufficient" call to counsel.

### 3. Consent-UX spec

The product specification of the consent experience — granular per purpose, a
withdrawal control as prominent as the consent control, no pre-ticked boxes, no
dark patterns, a clear notice version surfaced to the user. This is the *design*
spec; the *recording and enforcement* of consent as code (per-purpose record,
load order before tags fire, withdrawal taking effect on the next read) is the
code layer in `privacy-compliance.md`. Cross-ref `product-ux-quality.md` for the
dark-pattern lens.

### 4. Subprocessor list + data-flow notes

The **maintained, customer-facing register** — one row per third party, each with
a named internal owner and a current processing-agreement status, kept
procurement-ready. The *detection* that produces the raw list — enumerating every
SDK/vendor as a data export, noting what leaves, and flagging a missing agreement
or data-flow note — is the code layer in `privacy-compliance.md`; what is new here
is turning that list into the buyer-ready register an enterprise procurement
review asks to see. A register row with no owner is the gap.

### 5. Data-residency options

Where personal data is stored and processed geographically, as an explicit
product decision: the default region, whether region pinning is offered, and
where cross-border transfers occur (a transfer is a decision to record, and the
transfer *mechanism* is a counsel question — name it, do not assert it).
Enterprise and EU buyers ask this first; "we're on the cloud" is not an answer.

## Verification

- Introducing a **new PII field** (a new column or event property carrying
  personal data) prompts the register / DPIA question — it cannot be added
  silently.
- Each artifact exists as a scaffold with owners named and gaps flagged, not
  prose claiming compliance.
- No article number, legal deadline, or "compliant" assertion appears; the
  policy-text, DPIA-required, and lawful-basis calls are routed to counsel.
