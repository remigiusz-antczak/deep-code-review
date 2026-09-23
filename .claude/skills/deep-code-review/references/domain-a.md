# Domain A checklist

Read this when domain A (Correctness & logic) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### A. Correctness & logic
- Does it do what the spec/issue/user actually needs — not a plausible adjacent
  thing? Edge cases: empty, null, zero, negative, max/overflow, unicode,
  duplicate, out-of-order, huge, single-element, off-by-one boundaries.
- **Placement is a correctness question too: right logic, wrong home.** Before
  judging what the code does, ask where it should live — does this belong in
  *this* codebase/layer, or in a shared library, a separate service, or a
  caller's own concern? A change that is correct and fully tested but lands
  one layer too low still costs: it couples that layer to a decision it
  shouldn't own, pre-commits an abstraction on a single data point, or
  puts a capability in a consumer when it belongs upstream (an *ownership*
  question — distinct from H's DRY/duplication axis). That's a design defect even
  when nothing is functionally wrong — though the remedy may be a redesign the
  owner rules on (principle 5), not one the reviewer imposes unilaterally.
  Timing is the same question from a different angle: is *now* the right
  time, or is the caller getting ahead of itself (cross-ref H — a one-caller
  "helper" is premature)? This puts placement on the **default** Domain A path,
  not only the Architect role overlay; `references/role-coverage.md`'s Architect lens (boundaries &
  seams, dependency direction) is the deeper system-shape treatment for when
  architecture leads the review.
- **AI-authored code: a call into a *real* dependency must actually exist on the *pinned* version
  — not just the package.** Beyond package-name hallucination (a whole invented dependency —
  `appsec-supply.md`, `dependency-currency-and-upgrades.md`), an LLM invents a **nonexistent
  method/function/parameter on a real, already-installed dependency**, or misuses a real one with
  plausible-but-wrong arguments ("API hallucination, including invoking non-existent APIs and misusing
  existing ones," `docs/standards-index.md`). The exposure concentrates exactly where a type-checker
  **cannot** catch it: dynamically-typed call sites, reflection/dynamic dispatch (`getattr`,
  `obj[name]`), and stringly-typed integration points (an endpoint path or CLI flag built by
  interpolation). Check: for a new dependency call in an AI-attributed diff, confirm the exact
  symbol exists on the **lockfile-pinned** version — a type-checker where one runs, else
  introspection / a stub-diff / a smoke test. Name the **version-drift** case explicitly: a call
  valid for a plausible *other* version (what the model's training reflects) but not the pinned one
  reads as a bare type error, so it is "fixed" without anyone naming the hallucination pattern.
  Elevate scrutiny (don't routine-pass) on a rarely-used method of a well-known library, newly
  added by an AI-attributed commit, with no test exercising that exact call path. Reviewing
  AI-authored code is a core use of this suite, so this is a first-class correctness check,
  not an edge case.
- **Money & numeric precision**: currency uses integer-minor-units or `Decimal`,
  **never** binary `float`; rounding mode is explicit and consistent;
  accumulation error bounded. (Float-for-money is a textbook Critical.) Amount and
  currency travel together — never sum or compare amounts in different currencies
  without a provenanced conversion. Depth: `billing-correctness.md`.
- **Non-finite results (`NaN`, `±Infinity`) don't fail loud on the float path — and encoders
  disagree on them.** In **unguarded IEEE 754 float** arithmetic (JS numbers, C/Java/Rust
  `float`/`double`, NumPy) a `0.0/0.0` or an overflow yields `NaN`/`±Infinity` that **keeps
  flowing instead of raising**, and by IEEE 754 `NaN` compares **false** to everything including
  itself — so it silently poisons `min`/`max`/`sort`, dedup, and aggregates (order-dependent).
  This is **not** a universal divide-by-zero rule: many languages **guard** division — Python's
  `/` raises `ZeroDivisionError`, integer division traps in Java/Rust/C — so it is a *float-path*
  hazard. Serialization then **diverges**: `JSON.stringify` emits `null`, Python's default
  `json.dumps` emits a non-standard `NaN`/`Infinity` token, Go's `encoding/json` **errors** — so
  a non-finite value becomes a blank cell, a broken parse, or a failed encode depending on stack.
  Detect it (guard the divisor / `isfinite` → reject / clamp / explicit sentinel) at the point it
  can arise, not downstream once it has spread.
- **Time & dates**: store an **instant** (a past/point event) in **UTC**, tz-aware —
  but a **wall-clock-anchored recurrence** (a daily 9am, a monthly invoice date) stores
  **local time + tz-id** and re-resolves per occurrence, or it drifts by the DST offset;
  use a **monotonic clock** for durations (not wall-clock, which jumps); handle DST
  fold/gap, leap day/second, clock skew, and stale tzdata; never derive freshness from a
  local `now()` where the subject's own timestamp is meant. Depth:
  `time-date-correctness.md`.
- A **scope/subset flag must REPLACE the working set, not union into it** — an
  accidental union silently balloons scope and cost; test the two selectors are
  disjoint.
- A query that selects "the latest batch/generation" via `WHERE col = max(col)`
  (or `ORDER BY col DESC LIMIT`-as-batch) is silently broken by **any**
  single-row write to `col` — it can collapse a whole view to one row. Batch
  membership must be an explicit batch id, not a shared timestamp individual
  writes can move (cross-ref D).
- The same non-unique-timestamp trap bites an **incremental-sync cursor**: a batch-stamped
  timestamp used as a strict `WHERE ts > :cursor` (or a naive `>=` high-water mark) **drops or
  double-reads rows at a page boundary** when many rows share the cursor's timestamp — the page
  cuts mid-timestamp and the next query skips (or repeats) the rest. Page on a **unique, monotonic
  tiebreak** (a `(ts, id)` composite cursor) or an explicit sequence, never a shared timestamp alone.
- Error paths are correct, not just happy paths; idempotent where retried;
  deterministic where relied upon.
- **UI chrome is a claim** — a tab/heading/count asserts data beneath it; render
  it only when backing data exists ("empty beats fabricated" for layout too).
- 🚩 `==`/truthiness bugs, `float` for money, naive datetimes, mutation of
  shared/default args, silent coercion, unhandled enum case, subset flag that
  unions, "latest batch" keyed on a shared timestamp a single write can move, an integer id/amount sent as a
  JSON number past 2^53, an unchecked NaN/Infinity on a float path reaching an aggregate or a JSON
  encoder (null / non-standard token / encode error, by stack).
