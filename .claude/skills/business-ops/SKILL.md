---
name: business-ops
description: >-
  Use for the money and compliance questions a builder hits taking a product
  to market — in two clearly separated lanes. Lane A (arithmetic): pricing,
  unit economics, LTV/CAC, margin, runway, break-even — APPLIES the math to
  YOUR OWN numbers with the formula and every assumption shown, never a
  directive. Lane R (regulation): legal, tax, securities, employment
  classification, privacy compliance, and fundraising (selling equity or SAFEs
  is a securities offering) — names the regime and ROUTES to a licensed
  professional, never concludes. Standing disclaimer: educational information,
  not advice; never fabricates a financial figure, statute, or deadline.
  Opt-in overlay, default off; install with --with-business.
license: MIT
metadata:
  author: deep-code-review contributors
  version: "1.1.0"
---

# Business ops

Two lanes, one hard rule between them. The money-and-compliance questions a
solo/small builder hits split cleanly: arithmetic you can **apply** to the
user's own numbers, and regulation-dependent questions you must **route** to a
licensed professional. Putting a Lane-R question in Lane A — answering a
securities, tax, or employment-law question as if it were math — is the failure
this skill exists to prevent.

**Standing disclaimer (state it once, up front, every engagement):** this is
educational information, not legal, tax, accounting, financial, or investment
advice.

Persisted artifacts stay normal English. Chat may be terse.

---

## The asymmetric boundary (decide the lane first)

Before answering any money/compliance question, classify it:

- **Does the correct answer depend on a law, regulation, or a legal/financial
  determination** (what is owed, what is permitted, what must be disclosed, how
  something must be classified)? → **Lane R: route.**
- **Or is it arithmetic on the user's own numbers**, where the user owns the
  inputs and the decision? → **Lane A: apply, showing the work.**

When unsure, treat it as Lane R. Lane A is reversible structuring; Lane R is
where a confident wrong answer causes real legal or financial harm.

## Lane A — arithmetic (apply, never direct)

Pricing structure (value-based vs cost-plus vs competitor-anchored, on the
user's inputs) and unit economics: LTV, CAC, LTV:CAC, payback period, gross and
contribution margin, burn, runway, break-even.

- **Show the formula and every assumption.** `runway = cash ÷ net monthly burn`,
  then the numbers the user gave and the ones you assumed. The reader can audit
  and change any input.
- **Apply, don't direct.** Present the math and a sensitivity range ("at CAC X
  and churn Y, payback is Z months"); the pricing/spend **decision is the
  user's**. Never "you should charge $49."
- **Never fabricate the inputs.** CAC, churn, conversion, margin, and any
  competitor price are the user's real numbers or flagged unknowns with how to
  obtain them — never invented, and thin data is labelled thin.

## Lane R — regulation-dependent (route, never conclude)

Legal (entity choice, contracts, IP, terms), tax (what is owed, where, when),
**securities** (raising money by selling equity or SAFEs **is a securities
offering**), employment classification (contractor vs employee), and privacy
compliance (GDPR/CCPA and the like).

- **Name the regime, then route.** Identify which body of law/regulation the
  question falls under and hand it to a licensed professional (lawyer, CPA,
  tax adviser). Do **not** state the conclusion, the amount owed, the filing, or
  the "this is legal" verdict.
- **Fundraising is the boundary crossing.** The moment the question is "how do I
  raise a round / issue SAFEs / sell equity," it is a securities matter → counsel.
  Lane A may do **ownership / dilution arithmetic on terms the user supplies**; it
  does **not** interpret an instrument's conversion mechanics (cap, discount,
  pro-rata, MFN), set or assess terms, or opine on what is permitted — those are
  Lane R.
- **Never fabricate** a statute, rate, deadline, threshold, or a jurisdiction's
  rule. An `UNVERIFIED` + "confirm with a professional" beats a plausible wrong
  figure.

**Design-time triage (front door).** Before architecture hardens — and again when
the product enters a new market or handles a new data type — run the
regulated-domain decision tree in `references/regulated-domain-triage.md` —
**read it when** you need to know which regimes might apply early enough to shape
the build (health, payments/card data, minors, EU/UK or US-state personal data,
biometrics, consequential/automated decisions, money movement, enterprise
security). It names the regime and surfaces engineering-obligation leads, then
routes the binding question to counsel; it never concludes that a regime applies.

## Stage-awareness
Keys to the stage model in `deep-code-review`. Early: a simple pricing hypothesis
and a unit-economics skeleton (Lane A) are enough; heavy legal/tax/fundraising
structure is premature — note it and defer. As the product raises money, hires,
or handles regulated data, the Lane-R triggers fire → route then, not before.
For privacy-by-design specifics, see `deep-code-review`'s `privacy-compliance.md`
(domain Q); this skill routes the *obligation* question, that reference covers the
*engineering*.

## Definition of done
- The lane was decided first; Lane-R questions were routed, never concluded.
- Lane-A answers show the formula and every assumption; no input was fabricated;
  the decision was left to the user (no directive).
- Fundraising / securities, tax, employment classification, and legal questions
  went to a licensed professional with the regime named.
- The educational-information-not-advice disclaimer is present.
- No invented figure, statute, rate, or deadline.

## Anti-rationalization (excuse → rebuttal)

| Excuse | Rebuttal |
|---|---|
| "Just tell me what to charge." | Apply the math and show the sensitivity; the price is your decision, not a directive. |
| "Roughly, how much tax will I owe?" | Tax owed is regulation-dependent. Name the regime and route to a CPA; do not estimate the figure. |
| "Walk me through issuing SAFEs to raise a round." | Selling SAFEs is a securities offering → counsel. Dilution arithmetic on terms you supply is Lane A; interpreting the instrument or setting terms is not. |
| "Are my contractors correctly classified?" | Worker classification is a legal determination → employment counsel; never conclude it here. |
| "Estimate our CAC so the model is complete." | An un-instrumented input is UNVERIFIED. Give the formula + how to obtain it; never invent the number. |

## Standards (by name; verify a figure/URL before citing one)
Unit economics (LTV, CAC, LTV:CAC, payback, contribution margin); value-based,
cost-plus, and competitor-anchored pricing; runway / burn / break-even analysis; the securities-offering
boundary (equity/SAFE fundraising); worker-classification tests; the GDPR/CCPA
obligation triage (routed, not concluded). Named leads only — fetch and log a
source before citing a specific figure, rate, or statute (repo convention). Output
structure follows `communication-structure`.

## Verification
- A pricing / unit-economics ask applies the user's own numbers with the formula
  and assumptions shown, as math not a directive (`shows-formula-not-directive`).
- A legal/tax question names the regime and routes to a professional, without
  concluding (`routes-regulation-questions`).
- A fundraising / SAFE / equity question is flagged as a securities matter and
  routed to counsel (`fundraising-is-a-securities-matter`).
- A financial input with no data is not invented; the formula + how-to-obtain is
  returned (`no-fabricated-financials`).
- `evals/evals.json` plants these cases.
