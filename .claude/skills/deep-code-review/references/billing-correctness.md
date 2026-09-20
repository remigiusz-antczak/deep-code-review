# Billing & monetization correctness

**Read this when** the target meters usage, runs subscriptions, charges cards,
handles invoices or tax, or processes refunds/chargebacks — anywhere a bug
silently loses money or creates tax/legal exposure. This is a mechanics lens on
domain E (cost/money), with cross-refs to F (reliability), G (concurrency), and I
(API/integration). It reviews the *logic*; it is not new machinery.

## Boundary (review the logic; the fiscal/pricing calls are not the reviewer's)

- **In scope:** the correctness of metering, proration, dunning, tax *computation
  and application in code*, refunds/chargebacks, webhook idempotency, the
  money races, multi-currency handling, and ledger balance integrity.
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
  not accidental). Name the mode — half-up, half-even (banker's), or truncate
  — and apply it uniformly: `sum(round(x)) ≠ round(sum(x))` in general, so
  rounding each invoice line then summing and summing then rounding once are
  two different, valid results that must not be mixed within one invoice.
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

## Multi-currency correctness

- **Amount and currency are one value.** An amount stored, passed, or returned
  without its currency is incomplete data — currency travels with the amount
  (Martin Fowler's **Money value-object pattern**), never a bare number with
  the unit assumed from context.
- **Cross-currency arithmetic is a type error, not a rounding nuance.**
  Summing, comparing, or `sum(usd, eur)`-ing amounts in *differing* currencies
  must be structurally impossible (the type rejects mixed-currency ops) or go
  through an explicit, logged conversion — never an implicit numeric add.
- **FX conversions pin source and timestamp.** An unpinned "current rate"
  makes the converted amount unreproducible and unauditable the moment the
  market rate moves.

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
- **A verified signature proves authenticity, not correctness.** The handler
  must also cross-check the webhook's amount/currency against the
  internally-expected value (the order, invoice, or subscription it
  references) before applying it — catching a PSP partial capture, a currency
  mismatch, or a stale order amount that a valid signature alone can't.
  Signature/replay/no-trust-body are already covered (cross-ref I,
  `api-contracts.md`); this is the amount-vs-expected gap it doesn't cover.

## The money races (concurrency)

- **Double-charge race:** two concurrent checkout/renewal paths for the same
  subscription must not both charge — a single-flight lock or idempotency key on
  the charge, keyed on (customer, period), not on the request (cross-ref G,
  `concurrency-shared-state.md`).
- Concurrent webhook + user action (cancel while a renewal charges) resolves to
  one consistent state, not a partial one.

## Ledger integrity

- **Double-entry bookkeeping:** every transaction's debits sum to its credits
  and net to zero, whether the system is a ledger, wallet, or account balance.
- **Derived balance, not mutable:** the balance is `SUM(credits) −
  SUM(debits)` over an immutable, append-only entry log — never a running-total
  column that can drift out of agreement with the entries underneath it. The
  concurrent-mutation guard on that log is compare-and-set (cross-ref G,
  `concurrency-shared-state.md`); the periodic entries-vs-balance
  reconciliation job is `reliability-error-handling.md` (cross-ref F).

## Verification

- A **double-charge race** (two concurrent renewals for one subscription) is
  flagged, and the fix is a single-flight / idempotency key on the charge.
- A **non-idempotent webhook** handler (grants entitlement or counts revenue on
  re-delivery) is flagged.
- No tax rate, threshold, or fee is invented; the registration/filing and
  revenue-recognition calls are routed to an accountant, and pricing to the owner.
- **Cross-currency arithmetic** — summing or comparing amounts in different
  currencies without a provenanced conversion — is flagged as a type error, not a
  rounding nuance; amount and currency are one inseparable value.
- A **mutable running-balance column** — updated in place rather than derived as
  `SUM(credits) − SUM(debits)` over the append-only entry log — is flagged.

## 🚩 red flags

Meter incremented on a retryable path with no dedup; proration that isn't
symmetric; unbounded dunning retries or an immediate cut-off; an amount field
with no adjacent currency, or two money values summed/compared without a
same-currency check; a tax rate hard-coded with no jurisdiction signal; refund
with no idempotency; webhook handler with no signature check, no event-id
dedup, or no amount/currency cross-check against the expected value;
entitlement granted before `payment_succeeded` is confirmed; a charge keyed on
the request instead of the (customer, period) pair; a mutable `balance`
column updated in place instead of derived from the entry log.
