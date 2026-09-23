# Data quality depth — time series, freshness, and coverage gaps

Read this when the target or diff scores activity over time (recency, trend, velocity, an activity window), renders a per-subject verdict from store reads that can fail, serves a background-refreshed cache, or probes an external source for a current-state signal. Split from `data-quality.md`, whose core checks (monotonic writes, provenance, units, nulls, joins and keys, dedupe, freshness, idempotent writes) apply to every data review.

## Trend cold start (depth of `data-quality.md` §4)

- Derived trend/velocity metrics have a **cold start** — don't emit a value
  until enough snapshots exist; handle the warm-up window explicitly.

## Coverage gaps, read failures, and freshness windows (depth of `data-quality.md` §8)

- **An absent window is not a decline — and recency must be monotone in elapsed
  time.** A time/activity score must not read a coverage gap (no observation in a
  window, a source that went quiet, a period not yet collected) as a substantive
  low value ("declining", "churned", "at risk"): distinguish *observed-low* from
  *unobserved* before the number implies a trend. And a recency/freshness score
  must be **monotone in elapsed time** — more time since the last event can only
  lower freshness, never raise it; a non-monotone recency curve manufactures false
  "re-activation". Principle 2 again: the quiet window is evidence only once a
  positive control confirms the source was actually read for it.
- **A failed *read* is not a negative *verdict* — carry a distinct
  `unknown`/`degraded` state, never fold it into the accusing bucket.** A
  per-subject verdict (compliant/delinquent, posted/missing, present/absent)
  joined from several store reads often wraps each read to degrade to an empty
  result on error (`catch → []` / `new Map()`) so one flaky store never 500s the
  page — an often-correct resilience choice. But when that empty-on-failure
  fallback feeds a computation whose *absence* reads as a specific **negative**
  claim, the resilience silently converts an infrastructure fault into a false,
  actionable accusation against a **named subject**: "couldn't read your posting
  history" renders as the same red "never posted" badge (and inflated "still
  owed" count) a genuine miss earns, with nothing in the response telling the two
  apart. This is the read-*failure* sibling of "an absent window is not a
  decline" above — there a coverage gap must not read as a substantive-low
  *score*; here a read that *errored* must not read as a substantive-negative
  *verdict* about an identified subject — and it is worse, because the output is a
  specific accusation, not a neutral "no data yet." Make it reviewable on two
  axes: **(a) polarity** — trace each catch-to-empty forward and ask which bucket
  the empty lands in; into the *positive/compliant* bucket it is an honest floor
  (safe), into the *negative* bucket it fabricates the accusation; **(b) the bit
  must live in the response *shape*** — a `degraded` flag, a `dataIssues:
  string[]`, or a per-row `unknown`/`unverifiable` state the caller can render —
  because a server-side log the reader never sees is not a distinguishing signal.
  Keep the don't-500 resilience; just stop discarding the one bit (did every
  source actually respond?) that says whether the negative is real. Best enforced
  by construction: give the verdict type a third state so "delinquent" has **no
  constructor** from an unread store (`data-quality.md` §2, *make a dishonest value
  unrepresentable*). Same failure mode as the gate discipline in
  `reliability-error-handling.md` (a can't-check needs a distinct exit + message
  from a found-problem) and the metric version in `observability.md` (a 429 /
  timeout is not "no match" / "score 0"), but on a **different surface**: here the
  distinguishing bit must ride a **per-row response field** the UI can render,
  which a process exit code and an aggregate metric label structurally cannot
  carry.
- **A background-refreshed cache serves the last-good value with no *as-of*
  surface — so a dead refresher renders byte-identical to live.** A hot read path
  that can't query its store synchronously (a sync render function, an async-only
  client) keeps a module-level *last-good snapshot* and kicks off refresh in the
  background, serving the old snapshot on refresh failure rather than throwing —
  a defensible resilience choice, like the don't-500 fallback above. The honesty
  defect is on the **read surface**: the snapshot usually already carries a
  `generated_at` / `refreshed_at` the consumer *could* render, but no caller reads
  it (the accessor's only reference is its own declaration — the same **dead-pipe**
  tell as `data-quality.md` §5's *artifact → consumer census*: produced, consumed nowhere), and the
  refresh failure is logged **server-side only**. So through an outage of any
  length every consumer renders identically to a fully live read. This is the
  **successful-read twin** of the read-*failure* bullet above — there a read that
  *errored* must not render as a verdict; here a read served from a cache whose
  refresher *silently died* must not render as live — and a server log the reader
  never sees is again not a distinguishing signal. **Do not conflate this with `data-quality.md` §4
  freshness:** §4 scores the *subject's* own newest activity (never a fetch/refresh
  timestamp); this is the *pipe's* liveness — can the cache still refresh from
  source — a different question, which a subject-level "this record is N days old
  vs its cadence" signal never answers yet is routinely mistaken for in review
  because both use the vocabulary "fresh"/"stale". Fix: **wire the `generated_at`
  into a visible surface** (a "data as of HH:MM" cue, or a banner once cache age
  exceeds N expected refresh intervals) **or assert a read-time freshness bound**;
  pair it with the operator-side alarm on an overdue refresh (`observability.md` —
  freshness = time since last successful run; page when none in 2× the interval),
  which alone still leaves the *reader* blind. If the reader-side signal is
  deliberately deferred, **downgrade the unwired accessor from a shipped API to a
  tracked follow-up** so a later reviewer doesn't read its mere existence as wired
  coverage. Distinct from the cache **stampede** / **negative-cache** /
  invalidation bugs in `performance-db-cost.md` (correctness and cost of the cache
  *mechanism*) — this is a cache that never *visibly* expires because a background
  job owns refresh and its death is unobservable at the point of read.
- **Observability is a per-entity-*class* property, not only a per-window one.**
  The rule above corrects a *temporal* coverage gap; a distinct, cross-sectional
  one is that whole **classes** of entity are structurally less observable on
  public signal — people who work in public (engineers, researchers, OSS
  contributors) over-represent, and those whose work is private or gated
  (operators, investors) under-represent — independent of any time window.
  Uncorrected, an empty profile reads as **inactive** when it means **not publicly
  observable**. Label each entity's **public-footprint class** (high vs low
  observability) and carry it into every consumer: an empty / low profile in a
  low-observability class renders as *not observed*, never *inactive*, and a
  ranking must not read *unobserved* as *low-activity* — that systematically
  penalizes the very members the public surface can't see. Empty-beats-fabricated
  at the coverage layer. (Distinct from `data-scoring.md`'s per-row coverage flag, which is
  *post-hoc* — which inputs a given run populated; a public-footprint class is
  *a priori*, a structural property of the class known before any fetch runs.)
- **A freshness *window* is observable; a freshness *decay curve* is fabricated.** A **binary
  in-window gate** — `now − retrieved_at ≤ window_for_type` — is honest: elapsed time is an
  observable input, and a per-signal-type window that gates routing ("act on this only within N
  days") is deterministic and clickable. A **continuous decay-strength curve** — `strength =
  0.5^(days / half_life)` — is a **banned fabricated constant** (Principle 2): the half-life
  is invented, not observed — the same family as a predicted buying-stage score. Take the window,
  reject the curve; and treat a vendor / marketing **half-life figure** as **unverified** unless it traces to a
  primary source — use it only to illustrate window *ordering*, never as a number.

## Freshness of an external source (depth of `data-quality.md` §11)

- **A feasibility probe for a *current-state* signal gates on freshness, not just
  schema and match-rate.** An external source can pass API-works, has-the-fields,
  and adequate identity-match yet still describe *last year's* state. Query the
  **max timestamp per metric** (`... MAX(sample_date) ... GROUP BY metric` —
  per-metric, since columns in one table lag differently) and compare to today
  **before** designing anything on it. Label a derived signal by the recency of the
  metric it is **actually computed from**, not the freshest column in the table
  (overstating freshness in a deliverable is a silent correctness bug; the freshness
  dimension itself is `data-quality.md` §4). Run the **cheapest decisive go/no-go query first** —
  match-rate can look like the kill-question while staleness is the real one — and
  keep the probe **re-runnable**: a finding of *too stale to use* outvalues a
  polished pipeline built on a stale signal.

**🚩 red flags** (this file):
a time/activity score that reads an unobserved window as a decline;
an entity's structurally-low-observability class read as inactive rather than not-observed;
a non-monotone recency curve;
an external-source feasibility sign-off with no max-timestamp freshness check;
a fabricated freshness decay curve (`0.5^(days/half_life)`) or an adopted vendor half-life in place of an observable in-window gate;
