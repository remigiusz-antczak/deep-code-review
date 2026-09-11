# Billing & monetization correctness

**Read this when** the target meters usage, runs subscriptions, charges cards,
handles invoices or tax, or processes refunds/chargebacks — anywhere a bug
silently loses money or creates tax/legal exposure. This is a mechanics lens on
domain E (cost/money), with cross-refs to F (reliability), G (concurrency), and I
(API/integration). It reviews the *logic*; it is not new machinery.

## Boundary (review the logic; the fiscal/pricing calls are not the reviewer's)

- **In scope:** the correctness of metering, proration, dunning, tax *computation
  and application in code*, refunds/chargebacks, webhook idempotency, and the
  money races.
- **Out of scope — route:**
  - **tax registration, nexus, filing, and remittance** → accountant / tax
    professional (the reviewer flags that a rate is applied by a jurisdiction
    signal, not whether the entity is registered to collect it);
  - **revenue-recognition policy** (when revenue is booked) → accountant;
  - **pricing levels / packaging** → owner (`business-ops`).
- **No fabrication:** never invent a tax rate, a threshold, or a fee. An unknown
  rate is `UNVERIFIED` and owner/accountant-routed, never guessed.

## Metering & usage

- **Every billable event is counted exactly once.** Trace the path from the event
  to the invoice line; a retry, a replay, or an at-least-once queue that
  increments a meter without dedup is a **revenue-leakage or over-charge** bug
  (cross-ref G, concurrency, and I, webhooks). Idempotency key on the billable
  event, not just on the API call.
- **No silent drops.** A metering write that can fail with no reconciliation path
  under-bills; find the reconcile job and its last run (cross-ref
  `observability.md`).
- Clock, time-zone, and month-boundary handling for usage windows — an off-by-one
  at the period edge bills the wrong cycle.

## Proration & plan changes

- Upgrade/downgrade mid-cycle: is the proration credit/charge computed from the
  actual remaining time, and is it symmetric (a downgrade credits what an upgrade
  would charge)? Rounding is defined and consistent (half-cent handling stated,
  not accidental).
- Trial→paid, pause/resume, and cancellation effective dates: the transition
  cannot double-bill the overlap or leave a free gap.

## Dunning & failed-payment recovery

- A failed charge enters a **bounded** retry/dunning schedule (cross-ref F,
  `reliability-error-handling.md`) with a defined terminal state (grace → suspend
  → cancel) — not an
  unbounded retry loop and not an immediate cut-off.
- Access state follows payment state deterministically: a customer who pays on
  retry regains access, and one who never pays loses it on schedule. Involuntary
  churn from an expiring card is caught before the charge fails where possible.

## Tax / VAT

- The correct rate is selected by the correct signal (jurisdiction, product tax
  category, B2B vs B2C, reverse-charge / VAT-ID where relevant) and applied to the
  correct base at the correct time. **The reviewer checks the code applies *a*
  rate consistently and auditably — not whether the rate or the registration is
  legally correct** (that is the accountant's). Inclusive vs exclusive tax display
  matches what the customer agreed to.

## Refunds & chargebacks

- Refunds (full or partial) reverse the right amount, adjust tax, and reconcile
  the meter/entitlement; a refund cannot be issued twice for the same charge
  (idempotent — cross-ref G).
- Chargebacks/disputes update entitlement and are recorded; the webhook that
  reports them is handled (see below), not dropped.

## Webhook idempotency (the money-critical integration)

- Provider webhooks (payment succeeded/failed, dispute, subscription updated) are
  the source of truth and arrive **at least once, out of order, and duplicated.**
  Handlers must be idempotent keyed on the provider event id, tolerate
  re-delivery, and verify the signature. A non-idempotent `payment_succeeded`
  handler that grants entitlement or increments revenue twice is a double-count
  bug (cross-ref I and G).
- Out-of-order handling: a `subscription.updated` older than current state must
  not clobber it — compare the provider's version/timestamp.

## The money races (concurrency)

- **Double-charge race:** two concurrent checkout/renewal paths for the same
  subscription must not both charge — a single-flight lock or idempotency key on
  the charge, keyed on (customer, period), not on the request (cross-ref G,
  `concurrency-shared-state.md`).
- Concurrent webhook + user action (cancel while a renewal charges) resolves to
  one consistent state, not a partial one.

## Verification

- A **double-charge race** (two concurrent renewals for one subscription) is
  flagged, and the fix is a single-flight / idempotency key on the charge.
- A **non-idempotent webhook** handler (grants entitlement or counts revenue on
  re-delivery) is flagged.
- No tax rate, threshold, or fee is invented; the registration/filing and
  revenue-recognition calls are routed to an accountant, and pricing to the owner.

## 🚩 red flags

Meter incremented on a retryable path with no dedup; proration that isn't
symmetric; unbounded dunning retries or an immediate cut-off; a tax rate
hard-coded with no jurisdiction signal; refund with no idempotency; webhook
handler with no signature check or event-id dedup; entitlement granted before
`payment_succeeded` is confirmed; a charge keyed on the request instead of the
(customer, period) pair.
