# Changelog

All notable changes to this repository are documented here. Format loosely
follows Keep a Changelog; versioning follows Semantic Versioning.

## [1.195.0] — 2026-09-19

### deep-code-review — wave 116 web frontend security (browser-native controls, frontend-a11y.md)

From the COMPARATIVE research round (benchmark vs OWASP ASVS 5.0): V3 "Web Frontend Security" was the
one category-level gap — the existing Security section covered XSS/CSP/secrets/localStorage but not the
browser-native control cluster. Five deltas added to `frontend-a11y.md`, each MDN-verified this session
and scoped (not overclaimed):

- **postMessage** — a `message` listener must validate `event.origin` (+ message shape) before trusting
  `event.data` (any origin can post; CWE-346).
- **Subresource Integrity** — `integrity` + `crossorigin` on third-party/CDN `<script>`/`<link>` so a
  CDN compromise can't run arbitrary code in every browser.
- **Trusted Types** — `require-trusted-types-for` as a DOM-XSS backstop on top of output encoding
  (Baseline 2026; tinyfill for older browsers — scoped, not claimed universal).
- **Referrer-Policy** — the modern default is already safe, so the finding is a *weakened* policy or a
  token-bearing URL leaking via `Referer`.
- **Clickjacking** — promoted from a bare header-name in A02 to a named threat + per-page
  `frame-ancestors`/`X-Frame-Options` verification on authenticated/state-changing pages.

Three evals (deep-code-review 210 -> 213). Sources: 4 MDN pages fetched + logged; OWASP ASVS 5.0 V3
by name. Trio -> 1.195.0. `SHA256SUMS` regenerated last.

## [1.194.0] — 2026-09-19

### deep-code-review — wave 115 LLM streaming / completion-delivery review (security-ai-agents.md)

From a round-3 research scout (verified genuine at source; the standard LLM-app items are covered under
LLM01/10 + LLM06 + testing-and-evals RAG + privacy egress — streaming/completion-delivery mode was the
zero-hit gap). Added as ONE bullet in "Defensive patterns to look for" (keeping the OWASP LLM01–LLM10
enumeration a clean 1:1 walk), no new external source (under OWASP LLM Top 10 2026, already logged).

- Check `finish_reason`/`stop_reason` before use (a length/safety-truncated 200 read as complete) — LLM10.
- A complete-string moderation/sanitizer guard must run on the ASSEMBLED stream, not per-chunk — LLM10.
- Chunk-boundary evasion (a payload split across two chunks passes a per-chunk sanitizer) — LLM10.
- A client disconnect must cancel the upstream generation (non-cancelled generation burns billed tokens;
  distinct from pre-dispatch caps) — LLM06; cross-ref the abort-wiring discipline in reliability-error-handling.md.

Three evals (deep-code-review 207 -> 210). Trio -> 1.194.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): FIX-FIRST -> applied. Moved all 4 deltas out of the mid-OWASP-list splice
into "Defensive patterns" (one bullet, LLM10/LLM06 tagged) so the LLM01–LLM10 walk stays 1:1; rewrote
the client-disconnect eval to withhold the mechanism and make the "distinct from pre-call caps"
expectation discriminate; added the reliability-error-handling cross-ref. No fabrication/overclaim found.

## [1.193.0] — 2026-09-19

### deep-code-review — wave 114 resource lifecycle / leak review

From an industry-research scout (verified genuine at source; acquire/release-on-error-path already
covered by A10, unbounded-cache/goroutine-leak already covered — these 3 sub-patterns were zero-hit).
Engineering-judgment deltas, no new external citation.

- **A subscription/listener/observer that outlives its subscriber is the same lifetime mismatch** —
  the live emitter retains the dead subscriber (no GC) and its handler fires on detached state; pair
  register with deregister on teardown. → `concurrency-shared-state.md` (+ 🚩 footer widened).
- **Listener/timer/subscription with no teardown** (`addEventListener`/`.on`/`.subscribe`/
  `setInterval` with no matching removal; a `useEffect` with no cleanup) → `language-stack-redflags.md`.
- **A pool connection not released on the error path starves the pool**; pool exhaustion as its own
  symptom → `performance-db-cost.md` (cross-ref `security-appsec.md` A10 for the general form; 🚩 grep
  extended).

Three evals (deep-code-review 204 -> 207). Trio -> 1.193.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): PASS-WITH-NITS -> applied (widened the concurrency 🚩 footer to match the
extended lifetime class; added the pool-exhaustion pattern to the perf-db-cost 🚩 grep; cross-ref'd
A10 from the pool bullet). No-duplication and correctness verified clean.

## [1.192.0] — 2026-09-19

### deep-code-review — wave 113 API/SDK evolution & deprecation discipline (api-contracts.md)

From an industry-research scout (verified genuine at source; the file's header claims "SDK boundaries"
scope but the body was HTTP-only, and SemVer-MAJOR was stated without a recognition taxonomy or a
mechanical check). New section between "Public interface hygiene" and "Webhooks".

- **Breaking-change recognition taxonomy beyond remove/rename** — stricter validation, changed
  default, new required param, widened/nullable output, added enum member; + the forward-compatibility
  mirror; + a public exported symbol / CLI flag is a contract like an HTTP response (fulfils the SDK
  scope the header claims).
- **Mechanical surface-diff CI gate** distinct from hand-written contract tests (which catch only what
  was asserted) — per ecosystem: `oasdiff` / `buf breaking` / `cargo-semver-checks` (by name).
- **Removal needs a sunset window + usage precondition** — the HTTP `Sunset` header (RFC 8594) as the
  machine-readable signal, and call-volume evidence before dropping (skip rather than guess). Distinct
  from security-appsec's zombie-route sunset.

Three evals (deep-code-review 201 -> 204). Source: RFC 8594 (Informational) fetched + logged this
session. Trio -> 1.192.0. `SHA256SUMS` regenerated last.

## [1.191.0] — 2026-09-19

### deep-code-review — wave 112 feature-flag & experiment correctness (release-engineering.md, domain K)

From an industry-research scout (verified genuine at source; lifecycle / kill-switch / both-states /
PII already covered — these three were the absent slivers, on the code-review side vs growth-analytics'
read side).

- **Experiment assignment is reviewable code** — deterministic hash(unit+salt), not Math.random /
  session-scoped; unit stable across logout→login; exposure fires at variant-render, not page load; an
  SRM guard wired (a high-sensitivity signal the assignment/exposure pipeline is broken — several
  causes, not one). Extends the Experiment-toggle bullet.
- **Pin the evaluated flag value once per request/transaction** — re-eval mid-request renders a
  composite of both paths; a config-read consistency bug, not a data race; complements TTL-caching the
  fetch (cache the fetch, pin the value).
- **Provider-unreachable default per flag category, and disambiguate "closed"** — fail-open is the bug
  for a risky feature; release-toggle-closed = old path, ops-kill-switch safe default = engaged.

Three evals (deep-code-review 198 -> 201). Sources by name (Fabijan KDD-2019 SRM; Kohavi et al.). Trio
-> 1.191.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): PASS-WITH-NITS -> applied. Must-fix: a cross-ref to a non-existent
"migration-parity.md consistency rule" was repointed to the real lifetime-mismatch rule in
`concurrency-shared-state.md` (verify-before-cite). Also: corrected an eval's OWASP section (A06 not
A07), scoped the SRM claim to a multi-cause symptom (not a pointer to the bucketing code), and dropped
an uncued TTL sub-expectation from the pin-once eval.

## [1.190.0] — 2026-09-19

### deep-code-review — wave 111 telemetry / analytics-event correctness (data-quality.md)

From an industry-research scout (verified genuine at source; PII-in-analytics + consent were
already covered in `privacy-compliance.md`, and one-definition-per-metric in `growth-analytics` —
these three were the absent slivers, at the data-quality × api-contracts intersection).

- **An externally-consumed event is not dead-pipe just because no in-repo reader exists** — the
  artifact→consumer census misfires for a `track()`/`emit()` whose consumer is a vendor
  dashboard / warehouse / funnel; rename/removal of a published event is a breaking change, not a
  cleanup. Carve-out added to the census bullet (§5), cross-ref `api-contracts.md`.
- **Test/QA traffic pollutes the metric denominator** the same way an ineligible type does —
  filter at the emitter/ingestion boundary (enforced once), not a per-dashboard `is_test` filter.
  §4 denominator-integrity.
- **Outcome-correlated sampling biases the metric** — sample at a uniform known rate
  (reweightable) or independently of the measured outcome. §8.

Three evals (deep-code-review 195 -> 198). No new external source (engineering-judgment deltas).
Trio -> 1.190.0. `SHA256SUMS` regenerated last.

## [1.189.0] — 2026-09-19

### deep-code-review — wave: numeric correctness at a boundary

From an industry-research scout (verified genuine at source; float-for-money was already covered,
these boundary-crossing numeric mechanics were absent by repo-wide grep).

- **Integer past 2^53 across a JSON boundary is silently rounded, not rejected** — JSON numbers
  interoperate as IEEE 754 double, exact only for integers in [-(2^53)+1, (2^53)-1] (RFC 8259 §6);
  a 64-bit id / large amount sent as a JSON number arrives changed while `type: integer` still
  passes. Send as strings or a documented range contract. → `api-contracts.md`.
- **Non-finite results (NaN/±Infinity) don't fail loud on the float path** — they poison
  min/max/sort/aggregate (NaN compares false to everything). Scoped honestly: many languages guard
  division (Python's `/` raises), and encoders diverge on non-finite output (JS → null, Python →
  non-standard token, Go → error), so the "silent null" outcome is stack-specific, not universal.
  → `domain-checklists.md` domain A.

Two evals (deep-code-review 193 -> 195). Sources logged in `docs/standards-index.md`: RFC 8259
(STD 90) + CWE-1339 (fetched 2026-09-19); IEEE 754 added to the by-name list (paywalled). Trio ->
1.189.0. `SHA256SUMS` regenerated last.

Dogfood reviewer (sonnet): FIX-FIRST -> applied. The non-finite claim was overclaimed as a
universal (empirically false: Python `/` raises, `json.dumps(NaN)` emits a token, Go errors) —
rescoped to the unguarded-float path with per-stack encoder behavior, and the eval pinned to
Node/JS so its expectations stay sharp. IEEE 754 was cited but unindexed — added by-name.

## [1.188.0] — 2026-09-19

### deep-code-review — wave 109 i18n / Unicode-security depth (domain R)

From an industry-research scout (verified genuine at source; all 4 sub-checks were absent by
repo-wide grep). Domain R was already a routed lens (bidi/Trojan-Source, NFC/NFD, collation,
timezone all covered) — these are the missing sub-checks, added as depth, not a new lens.

- **Unicode confusables / mixed-script homograph** — a user-controlled string rendered as a
  *trust signal* (domain, sender name, package name, username) needs confusable / mixed-script
  detection, not just HTML-escaping; visual identity ≠ string identity. Mechanism depth (UTS #39
  skeleton / mixed-script / restriction levels) in `i18n-l10n.md` next to the bidi sibling;
  security framing (STRIDE Spoofing at the display layer) as a bullet in `security-appsec.md` A06.
- **Locale-dependent case-folding** (Turkish ı/İ, German ß→SS) — a case-insensitive compare/key
  must use Unicode case-folding, not an ASCII `lower()/upper()` round-trip. `i18n-l10n.md`.
- **Grapheme-cluster-safe truncation** — slicing on bytes/code-units splits surrogate pairs and
  ZWJ/combining sequences (mojibake); truncate and count on UAX #29 grapheme clusters. `i18n-l10n.md`.
- **Locale-formatted input parsing** — `1.234` is 1234 or 1.234 by locale; a naive parse is a
  silent 1000× data-integrity bug. Parse against the input's locale or require a machine format.
  `i18n-l10n.md` (read-side counterpart to the existing output-formatting rule).

Three evals (deep-code-review 190 -> 193). Sources logged in `docs/standards-index.md`: Unicode
UTS #39 + UAX #29 (both fetched 2026-09-19). Trio -> 1.188.0. `SHA256SUMS` regenerated last.

## [1.187.0] — 2026-09-19

### agentic-delivery — wave 108 autonomous-loop epistemology + auto-close hygiene

- **#423** (SKILL.md gate epistemology, new principle 12): an apparent owner-fork that a
  ratified invariant (no-data-loss, a security/a11y floor, a monotonic-quality rule) already
  decides is not a human gate — applying the invariant is a lane's mechanical job; escalate
  only the genuine forks the invariants leave open.
- **#476** (fast-agentic-delivery.md, sibling to the under-close section): the over-close
  mirror — a close keyword fires the *whole* referenced issue on merge, so an umbrella/epic
  or partly-advancing PR must use a non-keyword link (`Part of #N`); and the parser is purely
  textual, so a keyword only *quoted* while explaining a bug still closes the issue. A split
  clause states which section governs which case; it does not license parking a G7-complete item.
- **#413** (fast-agentic-delivery.md, ownership-map absence-check): `gh`/issue state is blind
  to local-only branches, worktrees, and unpushed commits, so a forge-only occupancy check can
  read "unclaimed" while a lane is in flight; scan local git too, treating a hit as a lead to
  check for liveness (not proof of an active lane), then adopt-and-re-verify or reconcile it.
- **#421** (SKILL.md principle 3, net-new clause): a conclusion that surprises you is the
  signal to re-fetch the specific state at decision time, not to act on a remembered snapshot.
  (The four-instance unification #421 also proposed is already covered by existing re-verify instances (SKILL.md principles 3/9/11, plus the
  mergeable-snapshot and open-tracker sections) in their own homes — restating it was declined per the no-duplication rule; only this trigger
  clause was net-new.)

Three evals (agentic-delivery 40 -> 43, incl. the over-close discriminator paired with the
existing under-close eval). Trio -> 1.187.0. `SHA256SUMS` regenerated last.

## [1.186.0] — 2026-09-19

Wave 107 — **product-ux data-viz honesty batch: invertibility, heat-cell third state, sparkline, UX auto-merge policy** (#459 + #487 + #486 + #485 + #471; dcr; from the 4-agent parallel triage). Five deltas in `product-ux-quality.md`: **(#459+#487)** a new section — a rendered tier/score/**aggregate encoding** (sparkline tick, heat cell, count) must **invert** to the exact source rows it summarizes (drill-through), or it is decoration that can't be verified or corrected; applies to aggregate encodings, not only per-row chips. **(#486)** a grid/heat-map/calendar cell needs a **third state** (event / collected-zero / not-collected) — an uncollected cell painted as low-activity fabricates "quiet" where the truth is "unknown" (grid form of observed-low-vs-unobserved). **(#485)** named the **sparkline** case in the sparse-line rule. **(#471)** a UX-bearing change does not **auto-merge** on code/build/lint + presence-only evidence, and a disabled UX-quality gate is a **P0** blocking that change-class. Inline 🚩 on the invertibility section and the auto-merge policy. Three evals (deep-code-review 187 -> 190). Trio -> 1.186.0. Closes #459, #487, #486, #485, #471.

Dogfood reviewer (sonnet): PASS-WITH-NITS → applied. MED: added a carve-out so the invertibility rule does not collide with the decorative-chart (`aria-hidden` + printed-number) exemption above; delivered #471's third practice — screenshot the **whole affected surface**, not a clip of only the diff's region — so "Closes #471" is honest. LOW: corrected "Inline 🚩 on each" to the two sections that actually got one; backlinked the heat-cell bullet to "Every data state" (link-don't-restate). Nit: de-gifted eval 1's prompt.

## [1.185.0] — 2026-09-19

Wave 106 — **data-quality integrity batch: re-attribution drops, connected-component over-merge, freshness decay-curve fabrication** (#446 + #465 + #463; dcr; from the 4-agent parallel triage). Shared spine: a data-integrity gate/count/curve must reflect OBSERVED reality, not a blind count or an invented model. **(#446, §1)** an identity/roster/ER change re-keys attribution across cached signals, so a volume drop may be a correction (re-attributed / poisoned-as-ambiguous) not a regression — investigate the fold before ack/block (the gate is the trigger, the fold is the adjudication). **(#465, §3)** raw connected-components over-merge (spurious A~B + real B~C); run graph metrics — a single-artifact bridge edge / low centrality flags the false merge a shared-key gate misses. **(#463, §8)** a binary in-window freshness gate is observable and ships; a continuous decay curve (`0.5^(days/half_life)`) is a banned fabricated number (invented half-life), and vendor half-lives are not data. Three 🚩 flags. Three evals (deep-code-review 184 -> 187). Trio -> 1.185.0. Closes #446, #465, #463.

Dogfood reviewer (sonnet): FIX-FIRST → fixed pre-merge. HIGH: a wrong graph-theory claim — a bridge edge has *high* betweenness centrality (Girvan-Newman), so "low centrality = weak link" was inverted; replaced with **low neighborhood overlap / embeddedness** (the actual weak-tie signal), in the section and the eval. MED: scoped #446 against the run-over-run drift guard in the same section ("beyond-attrition drop = regression" is the trigger to investigate, not the verdict). MED: softened an unsourced vendor-half-life provenance claim to "unverified unless it traces to a primary source" (no-fabrication, in-section and eval). LOW: relabeled the decay curve a **fabricated constant** (Principle 2), not "model-authored" (no model in `0.5^(days/hl)`).

## [1.184.0] — 2026-09-19

Wave 105 — **autonomous-terminus honesty batch: verify every work queue + enumerate don't keyword-filter** (#445 + #450; agentic-delivery). Two coherent `fast-agentic-delivery.md` sections — the two halves of "terminus is a claim about ALL work": **(#445)** before declaring done, enumerate EVERY work surface (issue tracker(s), a gaps/todo queue, a debt/critique file, failing/skipped tests, TODO comments, an open-review backlog) and confirm each drained-or-blocked — "I finished my queue" is not "nothing left"; name the queues checked; the delivery-side analog of the review coverage-ledger reconcile (`method.md`). **(#450)** discover work by enumerating the surface, not a keyword/title filter (titles are lossy — a docs/CI/security item may lack the keywords; mind pagination) — a filter orders a known-complete set, never defines it; state the filter when claiming done. Each with a 🚩 tell. Two evals (agentic-delivery 38 -> 40). Trio -> 1.184.0. Closes #445, #450.

Dogfood reviewer (sonnet): PASS-WITH-NITS → 3 polish fixes applied. Cross-linked the terminus section to this file's own termination-conditions bullet (it generalizes "backlog empty" to "every surface"); generalized the pagination note (dropped a GitHub-specific "~30 rows" stated as generic — the eval stays GitHub-specific, correctly); moved the `---` back-matter divider back to before `## Sources` (the insert had stranded it). Verified clean: no-duplication (vs work-loop / go-faster / research-not-delivery + method.md), correctness, eval discrimination, 🚩-tell convention.

## [1.183.0] — 2026-09-19

Wave 104 — **soft-delete & referential-integrity correctness** (#493; dcr, data-lifecycle lens). Extends `data-quality.md` §6 (lifecycle) — which already noted deletes-are-soft + erasure — with the **correctness** angle (distinct from the privacy-erasure obligation): once a table has a `deleted_at`, every read / JOIN / COUNT / uniqueness check must exclude deleted rows via a **default-scoped accessor**, not drift-prone per-call-site filters; a `UNIQUE` column needs a **partial index** (`WHERE deleted_at IS NULL`) or the tombstone blocks re-creating the value; delete semantics across FKs are deliberate — `ON DELETE CASCADE` can over-delete (shared/audit rows), a hard delete under-deletes (dangling FKs / orphans), and a soft-deleted parent with live children is a leak. Three 🚩 flags; cross-refs `privacy-compliance.md` (erasure). Two evals (deep-code-review 182 -> 184). Trio -> 1.183.0. Closes #493.

Dogfood reviewer (sonnet): FIX-FIRST → SQL-correctness fixes applied pre-merge. (HIGH) the UNIQUE "fold the delete marker into the key" fallback was unsafe as written — a bare nullable `deleted_at` in a composite `UNIQUE` lets duplicate **live** rows through (`NULL ≠ NULL` on Postgres/MySQL/SQLite); qualified it to require a **non-null** sentinel. (MED) the dangling-FK claim was unconditional — an *enforced* FK with `RESTRICT`/`NO ACTION` blocks the delete rather than orphaning; scoped it to unenforced / `SET NULL` relations. (MED) both evals' third expectation required disclaiming an *unprompted* erasure topic (correct-by-silence would fail) → reworded to absence-framing. Rewrapped the long 🚩 line. Verified clean: no-duplication, scope gate, eval-2 discriminator (rejects hard-delete).

## [1.182.0] — 2026-09-19

Wave 103 — **state-machine / lifecycle correctness** (#490; dcr, new lens from the architecture-pattern research). A new section in `reliability-error-handling.md`: any entity with a status/lifecycle (order, subscription, document, job, ticket) is an often-implicit state machine — review it as one, distinct from saga compensation and the dual-write atomicity above. Checks: model the valid `from→to` transition set (a bare `UPDATE status=?` with no from-state check permits `refunded→shipped`); guard each transition with **compare-and-set** in the write, not read-then-write (which races two transitions into a double effect — the state-machine face of the concurrency CAS rule); make **impossible states unrepresentable** (one enum, not a boolean soup admitting `isRefunded && !isPaid`); **no stuck/orphan states** (every non-terminal state has a timeout/exit; terminal states stay terminal); transition **side effects fire once** (cross-ref idempotency + dual-write). Scope-gated to entities with a lifecycle. Two evals (deep-code-review 180 -> 182). Trio -> 1.182.0. Closes #490.

Dogfood reviewer (sonnet): FIX-FIRST → blocker fixed pre-merge + nits. The "No stuck/orphan states" bullet listed "a manual path" as an acceptable exit yet named "an approval that never expires" as the hazard — a self-contradiction (an approval IS a manual path), and it contradicted eval 2 (whose reviewer-approval exit the bullet would have waved through). Restated the discriminating rule: an exit must not depend on **one specific actor** always acting (a timeout/escalation, or a reclaim any eligible actor can take). Nits: qualified impossible-states so genuinely orthogonal flags aren't false-flagged; disambiguated "0 rows-affected" in the eval (absent id vs illegal transition); split the 3-in-1 🚩 clause into three flags.

## [1.181.0] — 2026-09-19

Wave 102 — **test-quality batch: type-check ≠ full suite + tautological property test** (#364 + #373; dcr, testing-and-evals). Two smells added to "What good tests do": **(#364)** a passing type-check / compile is a **partial** gate, not the suite — after a conflict resolution on a long-behind branch a type-correct three-way merge can still fail a behaviorally-pinned test (the other side refactored the pinned shape away); run the full behavioral + regression suite before declaring the resolution correct, and treat a broken pinned test as a signal to re-examine the resolution, not a cue to delete it. **(#373)** a property test whose **generator encodes the invariant it checks** is tautological — it never samples the violating case, passes vacuously, guards nothing; the generator must sample the full input space independently of the property (sibling of the mocked-into-a-tautology smell). Both append a clause to the tail 🚩 block. Two evals (deep-code-review 178 -> 180). Trio -> 1.181.0. Closes #364, #373.

Dogfood reviewer (sonnet): PASS-WITH-NITS → two precision fixes applied. (#373) qualified "independently of the property": constraining a generator to a property's *precondition* is legitimate PBT — the smell is specifically encoding the property's *conclusion*, so the overbroad wording could have false-flagged a well-scoped test (a stricter-than-the-standard risk). (#364) dropped "an arity" from the type-invisible examples — arity IS type-checked, contradicting the bullet's own claim; replaced with a default value. Both mirrored in the evals. Verified clean: no duplication, correctness, 🚩-block, eval discrimination.

## [1.180.0] — 2026-09-19

Wave 101 — **systems-correctness batch: caching-correctness gaps + the dual-write problem** (#478 + #482; dcr). **(#478, performance-db-cost.md)** extends the existing Caching & memoization section (correct key / invalidation / TTL / tenant-isolation were already present — the issue's "0 files" was term-based) with the genuine net-new: **stampede / thundering-herd on expiry** (single-flight or soft-TTL, not a bare TTL), **cache-aside write race** (write-then-invalidate ordering / versioned keys, not set-after-write), **negative caching** (short re-checkable TTL for not-found/errors), and the **authoritative-vs-advisory** contract (a cache as source-of-truth = data loss on eviction). **(#482, reliability-error-handling.md)** a new section on the **dual-write problem** — a local write + a remote publish in two non-atomic steps diverge (lost vs phantom event); fix = transactional outbox / CDC (event in the same transaction, commit-before-publish), fallback = idempotent consumer + reconciliation; scope-gated to cross-system operations, distinct from saga compensation. Both append a clause to their file's tail 🚩 block (`🚩 grep` in performance-db-cost, `🚩 red flags` in reliability). Two evals (deep-code-review 176 -> 178). Trio -> 1.180.0. Closes #482.

#478 stays **open**: this wave shipped its genuine net-new (stampede, cache-aside race, negative caching, authoritative-vs-advisory), but #478's own acceptance also names invalidation-depth (derived/related-key completeness), key-isolation (cardinality / PII-in-key), and TTL-discipline (freshness cadence) as distinct checks **and** requires an invalidation eval — none shipped here, so closing it would over-claim. Those remain a scoped follow-up.

## [1.179.0] — 2026-09-19

Wave 100 — **data-integrity evidence-grading trio** (#458 + #460 + #464; dcr, batched — one theme: a signal's weight depends on provenance/distinctiveness, not raw presence). Three method-level deltas in `data-quality.md`: **(#460, §1)** grade-monotonic write-authority — the non-regression gate must arbitrate a non-empty value-A→value-B overwrite by source grade (refuse `new.grade < incumbent.grade`, keep incumbent on ties), additive to the populated→empty + fanout checks, else a lower-grade source silently overwrites a higher-grade value while the field stays populated; **(#458, §3)** grade a shared value by frequency, not all-or-nothing — a value's match/join weight is inversely related to its commonness (rare = stronger, common = demote as a generic key), via a deterministic value-commonness table + corroboration scaled by commonness; **(#464, §2)** corroboration counts independent *origins*, not distinct domains — collapse derivation (an aggregator / repost / re-cite of one origin is one origin), preferring the conservative count where derivation can't be established. All three are deterministic (no invented scores); #460 extends the non-regression gate (§1) and #458 routes a field-emptying demotion through it, while #464 governs a corroboration count, not a write path. Three evals (deep-code-review 173 -> 176). Trio -> 1.179.0. Closes #458, #460, #464.

Dogfood reviewer (sonnet): FIX-FIRST → both blockers fixed pre-merge + nits. (1) The ledger over-claimed "all route through the non-regression gate" — false for #464 (it governs a corroboration count, not a write path); scoped it. (2) The three deltas added no clause to the file's tail "🚩 red flags" block (its dominant convention, 4-commit precedent) — appended three, and removed #460's lone inline "In review:" question so review-surfacing is uniform. Nits: de-gifted the frequency eval (dropped a parenthetical that handed the "generic value" conclusion), comma-form multi-issue Closes, and cross-referenced §2 source-independence to §7 occurrence-not-attribution (the two halves of corroboration discipline). Verified clean: no duplication, correctness, determinism, eval count 173→176.

## [1.178.0] — 2026-09-19

Wave 99 — **a finished check's green can be stale off a prior evaluation — confirm it ran against the current head, and know each gate's trigger model** (#365; dcr). A new section in `branch-and-merge-hygiene.md` (after mergeable-is-a-snapshot): most gates re-evaluate only on a subset of events (typically a new push) and do NOT recompute on a body/metadata edit, a base retarget, a bot amending the description, or a rebuild another process is mid-way through — so a finished green can certify a state that no longer exists. Two shapes: merging while another lane still owns the change (green belongs to the pre-rebuild head → lands an intermediate state), and a gate reading a stale cached artifact/body. Rule: read the SHA/input-digest the passing check ran against vs the merge target (pin-to-SHA, `method.md`), and know each gate's trigger model so a mutation it does not cover is recognized as invalidating. The verdict-staleness sibling of the moving-base cases (mergeability-snapshot / stale-base gate-diff) and distinct from a check that never ran. One eval (deep-code-review 172 -> 173). Trio -> 1.178.0. Closes #365.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + two nits. The do-not-recompute list wrongly included "a rebuild/rebase mid-way," but a rebuild that pushes a new head DOES fire the push/synchronize trigger — and the section's own advice said to "wait for the gate to re-evaluate," contradicting the trigger-coverage label. Restructured into two clearly-labeled causes: **trigger coverage** (body/metadata/retarget/cached-artifact — the check never re-runs) and **timing** (a rebuild fires the trigger but its run is still in flight — the visible green is the pre-rebuild one). Nits: relocated the inline 🚩 to the file's bottom "🚩 Red flags" list (its established convention; the sibling §236 hazard sits there too), and dropped an eval clause about "an actor still mutating" that had no hook in the eval's completed-edits scenario.

## [1.177.0] — 2026-09-19

Wave 98 — **a completion claim in a PR body or handback carries a `Verify:` line, or it is unverified** (#401; agentic-delivery). A new section in `fast-agentic-delivery.md`: a delivery lane's PR body / handback that asserts a verified outcome ("tested and working," "confirmed in the browser") is a self-reported claim, not evidence — it is auditable only if it carries a `Verify:` line naming HOW (the command run, the surface exercised, the evidence link). Without it, treat the claim as `unverified` and ask for the method, not the adjective (a false "done" is trusted, built on, and surfaces late). The constructive form of the over-claim rule applied to the delivery artifact — a **claim-quality** requirement, NOT a trusted control (still self-reported; the SHA-pinned forge run is the control — cross-ref `branch-and-merge-hygiene.md` self-reported-evidence). Pairs with visual evidence (what changed vs how confirmed) and the co-evolve-the-gate-with-its-producers rule (gate on `Verify:` only if the lane template emits it). One eval (agentic-delivery 37 -> 38). Trio -> 1.177.0. Closes #401.

Dogfood reviewer: PASS-WITH-NITS → no blocker; no-duplication verified airtight (the `Verify:`-convention definition is genuinely new — `branch-and-merge-hygiene.md` §378 only names "a `Verify:` line" as one item in a list of body-gate conventions, never defines it; §412's mechanism is cross-reffed, not re-taught), and consistency with §412 (claim-quality not a trusted control) + §378 (co-evolve) confirmed, placement load-bearing, insertion-hazard sweep clean. Applied two nits: labeled the new red flag `🚩 tell:` to match the file convention, and tightened its tail so "unverified until the method is stated" cannot read out of context as "method stated ⇒ verified" (still self-reported after; the forge run is the control).

## [1.176.0] — 2026-09-19

Wave 97 — **ML fairness — detect it in review, never certify it** (#457; dcr, new area from the research cron). A new section in `testing-and-evals.md` (after the ML cluster): a fairness DETECTION lens for a default review, which had none (0 fairness content). **Scope-gated first** — applies only to a consequential decision about people with a group dimension in the data, else say so and stop (avoiding a fabricated "stricter than the standard" finding). Detects: protected-attribute direct use (disparate treatment) vs proxy (disparate impact) — a proxy is **demonstrated** by in-data correlation, never asserted, and absence of the attribute is not fairness (nor is blindly dropping a suspected proxy); requires a **disaggregated** evaluation with a **stated, justified** fairness metric (flagging the absence of a choice, not prescribing one); flags a missing model card (per-subgroup performance, Mitchell et al. 2019). Cross-refs `data-quality.md` §4 (dataset representativeness), `product-output-safety` (the output-harm guardrail — inventory / never-certify / measure — **not restated**), NIST SP 1270 (bias taxonomy), and the coverage-not-grade rule. Three evals (deep-code-review 169 -> 172). Trio -> 1.176.0. Standards logged (NIST SP 1270 read direct, Model Cards — both 2026-09-19). Closes #457.

Dogfood reviewer: FIX-FIRST (close call) → both fixes applied; everything else cleared (no-duplication vs `product-output-safety`, both sources verified to primary, eval-discrimination incl. the drop-the-feature guard, correctness, no metric-impossibility overreach). MAJOR: the scope gate's **inverse** — the fabricated-finding it exists to prevent — was unevalled, while the suite pervasively plants the does-not-apply case as an executable test; added a third eval (an out-of-scope demand-forecast model whose null manufactures a fairness finding → fails all expectations). NIT: legal terms of art ("disparate treatment/impact") appeared in-body with counsel-routing only in provenance; added an in-section clause routing the unlawful-or-not determination to counsel (`business-ops` Lane R), mirroring `product-output-safety` — the code finding is the missing measurement, never a legal verdict.

## [1.175.0] — 2026-09-19

Wave 96 — **MCP (Model Context Protocol) server/client security — the topology's delta** (#453; dcr, new area from the research cron). A new section in `security-ai-agents.md`: when the target is/hosts/connects to an MCP server it inherits a new principal + two surfaces the general agent-security lenses do not cover by default. Three labelled families, each specializing a general lens (not restating it): **(1) authorization in the proxy topology** — OAuth-proxy confused deputy (per-client consent MUST precede the third-party flow), token passthrough forbidden (`aud` must be the MCP server; no upstream-token forwarding — cross-ref A07), least-privilege scopes; **(2) consent-UI fidelity & local-server execution** — a one-click local server runs code with the client's privileges, so the exact untruncated command MUST be shown (approved bytes == executed bytes; cf. ASI09); **(3) tool metadata is untrusted, model-read instruction surface** — tool-description poisoning (hidden docstring directives the user does not see) and rug-pull (definitions mutate post-approval -> pin/hash + re-approve on change; extends ASI04). OWASP MCP Top 10 named as a **beta** regime only (no category IDs walked). Two evals (deep-code-review 167 -> 169). Trio -> 1.175.0. Standards logged (official MCP security spec, OWASP MCP Top 10, Willison/Invariant Labs — all fetched 2026-09-19). Closes #453.

Dogfood reviewer: PASS-WITH-NITS → no blocker. The fabrication pass was clean (the reviewer re-fetched all three sources; every `MUST`/quote/status verbatim-faithful), and duplication + eval-discrimination were verified. Applied the cheap nits, several serving the repo's own thesis: added MCP to the file's read-this-when trigger and the `SKILL.md` agent/LLM domain row (a standalone MCP server with no LLM now routes here); cross-linked the new tool-metadata section to the existing "trust the transport, not the payload" bullet (the third MCP trust leg); fixed the intro's "two surfaces" -> three (parallelism with the three families — the same enumeration discipline W94 corrected); dropped quote-marks on two illustrative glosses (the verbatim quotes live in `docs/standards-index.md`); softened "Official OWASP GenAI project" -> "Official OWASP project" in the ledger (the GenAI umbrella was not confirmable from the project page); "steal the code" -> "steal the MCP authorization code"; `MCP0x` -> `MCPxx`.

## [1.174.0] — 2026-09-19

Wave 95 — **a new PR-body / artifact gate is a contract with its producers — co-evolve them, or every automated PR silently fails it** (#411; dcr, branch-and-merge hygiene). A new section in `branch-and-merge-hygiene.md`: adding a gate that requires a convention in the PR **body** or a committed **artifact** (a `Verify:` line, a changelog fragment, a commit trailer) silently fails every producer that does not yet emit it. §5's "sequence the gate-adding PR last" handles the in-flight batch; this covers **standing** producers — PR templates, Dependabot/Renovate, release bots, agent swarms — which keep emitting the old shape on every future run until their **definition** is updated (automation cannot "just adapt" like a human author). Practices: co-evolve gate + producers in one change; grandfather/ramp (warn-only or apply-after-date); make the failure name the exact fix; inventory the producers first. Review lens + 🚩. Cross-referenced to the merge-train ordering rule (§5) and the message-payload sibling in `api-contracts.md`. One eval (deep-code-review 166 → 167). Trio → 1.174.0. Closes #411.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + a lockstep co-fix + a nit. The eval's expectation 2 (and expected_output) accepted a bare "apply the gate to PRs opened after a date" as a valid ramp — but a **past-dated** cutoff does nothing for a **standing** producer (its next run is always after any past date), the exact failure the section teaches, so a plausible wrong answer could have scored full marks. Qualified the ramp to a bridge (warn-only or a *future* cutover) with co-evolving the producer definitions as the primary fix, and fixed the same imprecision in the section's "Grandfather or ramp" bullet in lockstep. Nit: reworded a self-contradictory "fails it green-but-unmergeable" red flag (a failing check is red) to "refused — green on its real work, red on the new gate". Reviewer verified NO DUPLICATION (extends §230 + `api-contracts.md`, both distinct), cross-refs resolve, and the null-answer discrimination holds.

## [1.173.0] — 2026-09-19

Wave 94 — **a producer crossing a publish/trust boundary invalidates guards scoped to the old side** (#399; dcr, A06 Insecure Design + the DIFF blast-radius rule). A new bullet in `security-appsec.md` A06: a guard's sufficiency is often conditioned on a precondition ("internal only / never published / dry-run / behind auth"); when a change wires the producer **across** that boundary (to a published/external consumer), every guard justified by the old precondition must be **re-audited** — a weaker guard that was fine "because it never publishes" now ships its excused defect to the public surface (a false attribution). Two things hide it: the defending comment is now **stale** yet reads authoritative, and the guard + the boundary-crossing edit live in **different files** (a diff-scoped review sees one, not the other). Added the trigger to `SKILL.md`'s DIFF blast-radius 🚩 list. One eval (deep-code-review 165 → 166). Trio → 1.173.0. Closes #399.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + a nit. The blast-radius list header read "(each obliges Phase 3 anon-GET / two-principal probes)" — a universal the new producer-crossing member **falsifies** (its remedy is a guard re-audit, not a reachability/scoping probe; a reviewer following it literally would run the wrong probe and wrongly clear the case). Reworded to name the obligation per class (anon-GET / two-principal for the access items; a guard re-audit for the producer-crossing one). Nit: relocated the A06 cue to a standalone 🚩 bullet (off the mid-bullet position) and de-duped a "stale" echo.

## [1.172.0] — 2026-09-19

Wave 93 — **a green run is a sample, not a proof, when the trigger is nondeterministic or the run is too costly to repeat** (#414; dcr). A new section in `testing-and-evals.md`: some fixes can't be validated in one session (a ~1-in-N nondeterministic trigger; a ~20-min run where one pass isn't proof), so shipping on a single green run is a false "done" — distinguish **validated** from **happened-to-pass-once**. Ship the part you *can* validate; **name the part you can't as a Known-limitation** in the PR body with a concrete follow-up (a named residual is honest, a silent one ships a false done); don't let "while I'm here" scope-creep bolt an **unproven** refactor onto an otherwise-validated PR; symmetric with refusing a **placebo** fix proven not to work. Trailing 🚩 line added. One eval (deep-code-review 164 → 165). Trio → 1.172.0. Closes #414.

Dogfood reviewer: PASS-WITH-NITS → two applied. Added a closing cross-ref distinguishing this *ran-green-but-once* residual from a *deferred / never-run* gate (`parallel-audit.md`'s "an unrun matrix is `unverified`, not a pass") and `SKILL.md` principle 2 — both resolve the same way (name the residual, never a silent pass), linked not restated (verified parallel-audit:459 carries that spine). And added a placebo hook to the eval prompt so its symmetric-with-placebo expectation tests scenario reasoning, not lesson recall.

## [1.171.0] — 2026-09-19

Wave 92 — **adding a new dependency is a governance decision, not an implementation detail** (#439; dcr). A new §4 in `dependency-currency-and-upgrades.md` (sections 1–3 keep *existing* deps current; this covers *taking on a new one*): a new runtime dependency is a long-term liability the maintainer carries — bundle-size/perf, supply-chain/security surface (the whole transitive tree), license, maintenance — so it is an **owner/maintainer decision**, not one an agent or feature PR can unilaterally own. Report "needs a new dep" as **BLOCKED-ON-OWNER** with the exact dep + tradeoff (never a fait-accompli `npm install`); check for a lighter path first (existing capability / bundled lib / native API); calibrate by weight (tiny/ubiquitous/audited routine, heavy/novel/broad-surface = owner's call). Review lens + 🚩: a PR adding a manifest dependency alongside a feature — necessary, minimal, maintained, approved? The global confirm-before-a-lasting-commitment rule applied to the dependency manifest. One eval (deep-code-review 163 → 164). Trio → 1.171.0. Closes #439.

Dogfood reviewer: FIX-FIRST → the blocker fixed pre-merge + one nit. Two cross-refs — "different severities (see §4)" and "rank it per §4" — are about **severity** but pointed at §4; they were **dangling on origin/main** (no §4 existed) and would have become **active misdirection** the moment this PR added a real §4 (new-dep governance). Re-pointed both to **§3** (Severity discipline) — which also fixes the pre-existing latent bug (do-no-harm: the PR must not regress the accuracy axis of the file it edits). Nit: added a cross-ref from §4 to §2's slopsquat / established-package check (governance = *whether* to add; §2 = the added dep's *integrity* once approved).

## [1.170.0] — 2026-09-19

Wave 91 — **a negative-assertion (assert-absent) test is a ratified constraint — never loosen it to ship a conflicting feature** (#432; dcr). A new section in `testing-and-evals.md`: a test asserting something is **absent** (`assert.doesNotMatch(brief, /ProgressBar/)`, "no attainment %") encodes a deliberate, often-ratified design constraint. When a feature request conflicts, the **wrong** move is to delete/loosen the guardrail to pass (silently reversing a ratified decision — the code-review equivalent of pulling the smoke detector); the **right** move is to read the negative test as intent, ship only the non-violating part, and report the conflict as **BLOCKED-ON-OWNER** (changing a ratified constraint is an explicit owner-visible commit, never a feature-PR side effect). Review lens + 🚩: a diff that loosens/removes an assertion — especially an absence assertion — while adding a feature. Pairs with `product-ux-quality.md`'s *show coverage, not a grade* (the test that pins the omit-attainment contract); distinct from the retired-because-unreachable-spec case (owed a named gap). One eval (deep-code-review 162 → 163). Trio → 1.170.0. Closes #432.

Dogfood reviewer: PASS-WITH-NITS → three applied. Trimmed an eval expectation whose second clause demanded cross-doc navigation a correct "can I delete this test?" answer needn't volunteer (a false-negative risk); rewrapped the appended 🚩 line to the block's width; and reworded "the enforcement half of" → "a test-layer enforcement of" *show coverage, not a grade* (that section already carries its own 422-gate + contract enforcement). The flat imperative title was kept per house style (body hedges "often-ratified").

## [1.169.0] — 2026-09-19

Wave 90 — **a published standard is the constructive escape from an invented score — check both the definition and the *selection* layer** (#396; dcr, domain D / anti-fabrication). A new bullet in `data-quality.md` §7: instead of an "invented composite index" or inferred human-judgment score, adopt an external **published standard** whose definition is the spec, not the tool's judgment (examples named **by name only**: CHAOSS, Fellegi-Sunter, W3C PROV, rel=me / ORCID / schema.org `sameAs`, network-science centrality, ESCO / O*NET). **The subtle trap it closes:** citing each metric's spec while **hand-picking which metrics to include** re-introduces the invented index *one level up* — the selection becomes editorial judgment, hidden because every row still has a spec URL. Two-layer + observability check: each metric a cited **definition**; the metric **selection** itself a cited published **model** (not a tool-chosen set); each metric's **input observable**; deviations recorded per metric with a reason. Corollary: a standard often supplies an honest **skip band** for free (Fellegi-Sunter's possible-match tier). The named standards are added to `docs/standards-index.md`'s **by-name** list (not fetched this session). One eval (deep-code-review 161 → 162). Trio → 1.169.0. Closes #396.

Dogfood reviewer: PASS-WITH-NITS → two precision nits applied; the reviewer confirmed the provenance is clean (all six standards characterized at category level only, no version/figure/URL asserted, in the by-name list) and noted the wave correctly **omitted** #396's one spec-level claim ("CHAOSS metric-models refuse a single roll-up") that would have needed a fetch. Nits: restored "redundant **with a system that already observes it**" (the observability check had dropped the with-what); and re-labelled the standards-index group **network-science structural-position measures** since Burt structural holes is a brokerage/position measure, not strictly a centrality index.

## [1.168.0] — 2026-09-19

Wave 89 — **show coverage/readiness, never a fabricated attainment/grade** (#407; dcr, domain P product-UX honesty). A new section in `product-ux-quality.md`, paired with the confidence-false-precision section: a progress bar / `%-complete` / grade with **no honest current reading is a fabricated "done"** — the honest alternative is **coverage/readiness** ("N of M key results measurable/instrumented"), always computable, and for an unmeasured item render **"awaiting reading"**, never a manufactured number. Enforce structurally, not by convention: a **write-broker/observation gate that 422s** any attainment/on-track claim the system can't substantiate, and a **contract declaring "attainment out of scope"** so a later "add progress bars" ask is triaged as *ratify a rule first*. A display that would honestly be "awaiting reading" on nearly every row is worse than no feature — hold it. Review lens: ask the denominator/rule + measured-vs-inferred. One eval (deep-code-review 160 → 161). Trio → 1.168.0. Closes #407.

Dogfood reviewer: FIX-FIRST (light) → four one-liners applied pre-merge. (1) The new `##` section had added **no pre-ship-checklist line**, breaking the file's strict section→checklist convention (the rule was inert at the checklist layer) — added one. (2) Added an explicit **boundary sentence** vs the paired confidence-tier section (there a reading exists but is rendered false-precise; here no honest reading exists, so any grade fabricates a "done") — the file's adjacent-rules-declare-their-boundary convention. (3) Softened the over-claim "coverage is *always* honestly computable" → "computable without inventing a reading (given an enumerable M and a defined 'measurable')". (4) Split a compound eval expectation (hold-when-mostly-empty vs the review lens) into two.

## [1.167.0] — 2026-09-19

Wave 88 — **corroboration establishes occurrence, not attribution** (#368; dcr, domain D / anti-fabrication). A new bullet in `data-quality.md` §7: an event confidence often fuses three independent propositions — occurrence, role, and **entity-attribution** — and cross-source corroboration (N independent publishers naming the same event) evidences only **occurrence**, never whether entity X was involved. A promotion that lifts the *whole* fused confidence to "fact-grade" on an agreement count silently promotes a **weakly-matched attribution** — the worst axis (a confident false attribution is worse than publishing nothing). The tell: a `min(identity_match, occurrence, role)` confidence **raised** by a corroboration count that only evidences occurrence, overriding the binding minimum that flagged the shaky match. Rule: corroboration may raise only occurrence/role, never past the entity-attribution component — it answers "did it happen," never "whose is it"; safest default, carry the count as unrendered evidence and don't promote a fused confidence at all. One eval (deep-code-review 159 → 160). Trio → 1.167.0. Closes #368.

Dogfood reviewer: PASS-WITH-NITS → three applied pre-merge: the detector moved from a non-conforming inline 🚩 into the file's consolidated 🚩 red-flags index (the file's one-index convention); the descriptive claim aligned to the rule ("evidences occurrence (and role)"); and the "a false attribution is worse than publishing nothing" cross-ref re-pointed from §1 (monotonic-quality) to **§2** (No fabrication — "an empty cell beats a confident-looking wrong one"), its literal home, in both the bullet and the eval (the recurring mis-pointed-cross-ref class).

## [1.166.0] — 2026-09-19

Wave 87 — **the gate's own harness crash is a could-not-check, not a finding** (#372; dcr). Generalizes the canonical cannot-check bullet in `reliability-error-handling.md` from an *external dependency* to the gate's **own harness** (a headless browser, dev/preview server, probe): a crash during harness **setup, before the first measurement**, is a could-not-check — it must not block or be reported as a violation (after bounded transient retries). Adds the specific defect + detector: **a gate that exits the *same* failure code for a setup/harness crash as for a real violation** leaves consumers unable to tell an outage from a finding, so a flaky harness blocks everything and trains blanket-overrides (which then suppress the real findings too) — require **distinct exit semantics + a distinct message**, and flag any gate whose pre-measurement crash is indistinguishable from a finding. The security/authz/integrity fail-closed exception is unchanged. One eval (deep-code-review 158 → 159). Trio → 1.166.0. Closes #372.

Dogfood reviewer: PASS-WITH-NITS → one clarity nit applied. The security/authz/integrity/spend exception now explicitly names **its own harness failing to launch** as a can't-verify that still fails **closed** — foreclosing a literal misread of the newly-broadened fail-open list (the reviewer verified security gates were never actually made to fail open: the exception is a categorical by-gate-class override, and a harness crash is a can't-verify). The novel exit-semantics detector (same code for crash and violation is the defect), the base-vs-overlay layering vs `fast-agentic-delivery.md`, and the eval's strict quality-vs-security boundary expectation were each confirmed clean.

## [1.165.0] — 2026-09-19

Wave 86 — **an auto-merger scopes by a manufactured ownership signal, not by author** (#424; agentic-delivery). An auto-merge/auto-rebase system must act on agent PRs and never on a human's own — but "merge PRs authored by the bot" **fails when agents authenticate as the human** (agent lanes run `gh` under the owner's token, so every PR shows the same author; observed: a human-owned design PR shared the agent author and was distinguished only by a semantic read — had it gone mergeable the drainer would have merged unfinished work). New section in `fast-agentic-delivery.md`, right after the queue-drainer section (that iterates the candidate set; this decides which PRs are in it): give agents a **distinct identity** (bot account / separate `GITHUB_TOKEN`) so authorship discriminates; else key on an **explicit convention** (allowlist / denylist / `agent-mergeable` label / `bot/*` vs `feat/*` prefix) and **default-deny anything not positively marked agent-owned**. General: automation on shared artifacts needs a reliable ownership signal — when identity is shared, manufacture one, don't infer from a field every actor shares. One eval (agentic-delivery 36 → 37). Trio → 1.165.0. Closes #424.

Dogfood reviewer: FIX-FIRST → two corrections applied pre-merge, both verified against primary sources. (1) The 🚩 tell cited `is:author @me` — invalid GitHub syntax (`is:` takes pr/issue/open/closed/…, never author; author filtering is `author:@me` / `gh … --author @me`); corrected, since a fabricated qualifier in a grep-detector line is worse than none (no-fabrication rule). (2) This entry had said the drainer "nearly merged" the human's PR, but #424 is explicit it never became mergeable ("had it become mergeable, the drainer would have"); reworded to the conditional, mirroring the reference file's already-hedged parenthetical.

## [1.164.0] — 2026-09-19

Wave 85 — **safe programmatic git under multi-worktree automation** (#417 + #426; dcr). Two safety rails added to `branch-and-merge-hygiene.md` §6, for agent/automated git where no human eyeballs the diff. **#426:** `git add` stages on-disk content including conflict markers, so `add` exiting 0 is not proof of resolution — and a `[param]`/glob-metachar path (`app/kpis/[key]/page.tsx`) can make `git checkout --theirs` **silently no-op** (glob-expands to a no-match); quote/escape metachar paths (or the shell's glob switch — `setopt noglob` in zsh, `set -f` in bash) and **grep the staged tree for conflict markers, gating on the result** (`git grep --cached -qE '…'` failing on a hit, or `git diff --cached --check`; a bare `git diff -G` prints but exits 0, so it does not gate). **#417:** to update a branch already checked out in another worktree, use a **detached-HEAD fast-forward** (`git worktree add --detach <dir> origin/<branch>` → push `HEAD:<branch>`), never a force-push (which strands that lane's unpushed work on a diverged branch + discards its pushed commits); verify the remote ref is an ancestor first. Two red-flag lines + two evals (deep-code-review 156 → 158). Trio → 1.164.0. Closes #417, #426.

Dogfood reviewer: FIX-FIRST → three empirically-verified corrections applied pre-merge. (1) The marker-grep `git diff --cached -G '…'` **exits 0 even with markers staged** — wired `cmd && commit` it always commits, the exact silent-pass trap it condemned; replaced with `git grep --cached -qE '…'` (exit 0 = found → block) / `git diff --cached --check`. (2) `set -f` disables globbing only in bash/POSIX sh — in **zsh** (the shell the bug lives in) it is NO_RCS and leaves globbing on; corrected to `setopt noglob` / `noglob` for zsh, quoting primary everywhere. (3) A remote force-push does not *clobber* the other lane's unpushed work — it **strands** it on a now-diverged branch (and discards commits already pushed); aligned four sites to the eval's already-correct "strands." All three verified in a scratch repo (bash + zsh, `git grep`/`--check` exit codes).

## [1.163.0] — 2026-09-19

Wave 84 — **a serial queue-drainer must advance past a blocked head, not re-select it** (#400; agentic-delivery). A serial auto-processor (merge-drainer, retry queue, task poller) that picks the first-eligible item each cycle spins forever on one item blocked for a persistent reason — head-of-line **starvation** that looks like *idle*: an auto-merge drainer re-picks the first green+mergeable PR that a stricter final gate (a PR-body lint) keeps refusing, and never reaches the others. New section in `fast-agentic-delivery.md`: the cheap pre-filter (green+mergeable) is **not** the final admission gate; **iterate all candidates and advance past a refusal** (never break + re-select the head); keep a **cooldown / skip-set** with periodic re-eval; **log per-item outcomes** so a spin is visible, not mistaken for idle. Completes the adjacent *sweep the whole ready queue* rule (scan-all ↔ don't-get-stuck-on-the-head). One eval (agentic-delivery 35 → 36). Trio → 1.163.0. Closes #400.

Dogfood reviewer: PASS — clean across all axes, no findings. No-duplication verified distinct from the adjacent *sweep the whole ready queue* (scan-completeness), *mergeable is a snapshot* (stale vs persistently-blocked), *red base* (base-red vs one-item-blocked), and wave 83's *go-faster signal* (agent-side taxonomy vs a concrete stalled instance); both internal cross-ref directions confirmed correct; eval discrimination, the trio version bump, and SHA256SUMS all verified.

## [1.162.0] — 2026-09-19

Wave 83 — **a go-faster signal fires on a clock, not on state; holding is a valid response** (#419; agentic-delivery). The **counterweight** to "an unattended time budget is a work loop" above: that rule says *don't stop while the backlog has work*; this one says *don't fake work once it doesn't*. A recurring pressure signal (a cron, a "why are you stalling?" prompt) fires on a clock, not state, so it keeps arriving when the correct action is to **hold** — async work draining, backlog exhausted or owner-gated (a termination condition), or only risky moves left. New section in `fast-agentic-delivery.md`: distinguish **stalled** (blocked on yourself → move) from **correctly holding** (async progressing / owner-gated → no move); answer the pressure with a **truthful one-line status** (what's running, what's blocked and on whom), never manufactured work; at a genuine terminus prefer non-fan-out moves (drain the queue, close delivered, surface gating decisions), then hold — busywork under observation is still busywork. One eval (agentic-delivery 34 → 35). Trio → 1.162.0. Closes #419.

Dogfood reviewer: PASS-WITH-NITS → two no-duplication cross-ref refinements applied pre-merge: the bullet-2 status triad now cross-refs the adjacent *if the loop is idling, say so loudly* rule it extends (same whole-window status, opposite failure — **silence** there vs **filler** here) rather than the ask-ledger data structure it had pointed at; and the counterweight framing now names the *the owner's message cadence is not the loop's clock* bullet it mirrors (that stops owner-quiet throttling the loop down; this stops a pressure tick driving it up).

## [1.161.0] — 2026-09-19

Wave 82 — **a delegated "verify green" is a lead, not the authoritative gate** (#408; agentic-delivery). In a delegate → review → land pipeline, a subagent's green in an isolated worktree ran a **narrower scope** than the real gate (changed-files / package-local, not repo-wide), so it can sit on failures the full gate catches — an unused-import that root `eslint . --max-warnings 0` flags, formatter diffs on untouched files, coverage / cross-workspace checks the worktree could not run. New section in `fast-agentic-delivery.md`: the **authoritative gate is the full-repo run at integration** (real pre-commit hook / CI, on the integrated tree); **land re-runs the full gate** and that is the verdict of record — a lane's green is `unverified` until then. Framed as the **inverse** of the symlinked-deps / provisioning-gap sections (env too *poor* → false failure; here too *partial* → false pass) and **distinct** from the stale-verdict case (moved head vs partial scope). One eval (agentic-delivery 33 → 34). Trio → 1.161.0. Closes #408.

Dogfood reviewer: PASS-WITH-NITS → three applied pre-merge: a directional cross-ref slip fixed (the provisioning-gap section is *above* this one, not below — the inverse relationship itself was correct); a disambiguating cross-ref added to the neighbouring "CI-offload the heavy gate" section (closest existing prose — kept distinct: that picks *which tier* a lane runs for the RAM budget, this is what a *delegated* verdict entitles you to conclude + the integrated-tree point); and #408's "budget a fix-and-recommit at land" item folded in (a delegated green predicts less rework, never none).

## [1.160.0] — 2026-09-19

Wave 81 — **fix a mis-cited operating principle** (#398; dcr correctness / exemplary-repo hygiene — a reference bar must cite its own principles correctly). The "empty beats fabricated" / "computed-not-fabricated" concept is **No fabrication = `SKILL.md` principle 3**, but six loci labeled it **principle 4** (Do no harm): `product-ux-quality.md` (×2), `migration-parity.md`, and three eval expected-outputs/expectations in `deep-code-review/evals/evals.json`. Corrected all six to principle 3; the genuine principle-4 citations (net-positive-on-every-axis, no-regression, never-delete-a-feature-to-reach-parity) were each verified in context and left untouched. No behavior change — a self-citation accuracy fix. Trio → 1.160.0. Closes #398.

Reviewed independently via advisor (a stronger model with full context): the classification of all fifteen principle citations — the six corrected to principle 3 and the nine genuine do-no-harm principle-4 citations left untouched — was confirmed, and a repo-wide proximity scan (any `fabricat`/`invent`/`empty beats` concept within ±2 lines of a `principle N` citation) verified no seventh mis-cite locus remains.

## [1.159.0] — 2026-09-19

Wave 80 — **ML in production: drift monitoring & safe model rollout** (dcr; completes the ML lifecycle after wave 75). A new `##` section in `testing-and-evals.md`, after "ML pipeline correctness": the *post-deployment* half — W75 verified the model was **trained** honestly and `data-quality.md` §12 verifies train/serve feature parity; this covers a model that **silently decays** in production or a **swap that ships a quietly worse model**, both invisible to the training checks. (1) **Drift monitoring** — a served model degrades with no error as the input distribution drifts; monitor the input-feature + prediction distributions and realized performance against **lagging** ground truth (alert on a proxy — distribution shift / confidence drop — in the meantime); green infra dashboards are not model monitoring. (2) **Safe model rollout** — a new model version is a behavior change, not a deploy; green error-rate / latency do not mean it is as good, so prove it on **prediction quality** via **shadow** or **canary / champion-challenger** with a rollback path and a longer quality-based bake than a code canary (ground truth lags). Specializes the generic `observability.md` monitoring and `release-engineering.md` canary/rollback disciplines to the ML case; explicitly distinct from W75 (training) and data-quality §12 (train/serve skew). A red-flag line added. One eval (deep-code-review 155 → 156). No new external standard → no `docs/standards-index.md` change. Research-derived (no filed issue). Trio → 1.159.0.

Dogfood reviewer: PASS-WITH-NITS (no fix-first — the provenance axis that flagged the prior waves was verified against the primary source here). Three optional prose nits applied: an in-bullet distinction from `data-quality.md` §12's train/serve *parity* check (drift = live inputs vs the training baseline over time, not two computation paths at one instant); reduced a verbatim symptom-phrase overlap with §12; and softened "ground truth lags" → "often lags" (not universal — some labels arrive fast).

## [1.158.0] — 2026-09-19

Wave 79 — **EU NIS2 name-and-route**, a new regulatory area (the last non-gated new-area from the coverage cartography; primary-sourced this session). A new tree entry in `business-ops/regulated-domain-triage.md`: an organization operating its own in-scope services in the EU (medium-sized+ in a covered sector — energy, transport, digital infrastructure, cloud / data centres / DNS, health, water, public administration, …) → name the **EU NIS2 Directive (Directive (EU) 2022/2555)** + engineering-obligation leads (the risk-management measures — risk analysis, incident handling, business continuity, supply-chain security, cyber hygiene; and **incident-reporting readiness** → maps to `deep-code-review` observability + `agentic-delivery`'s `incident-response.md`; the supply-chain half reuses the CRA / A03 leads); route in-scope / essential-vs-important / reporting-authority / timelines / management-accountability to counsel (name-and-route boundary; no rot-prone dates encoded). Distinct from the CRA's product scope (NIS2 = how you *operate*; CRA = the *product* you ship). Verified by direct fetch of EUR-Lex 2022/2555 this session — the verbatim risk-management-measures list and the staged reporting windows were **not** reachable via the fetch (cited by name only; the leads are grounded in the preamble categories the fetch did surface).

Dogfood reviewer: FIX-FIRST → two provenance-precision fixes applied pre-merge. (1) The entry (and its Verification bullet, eval, and this changelog) had cited the risk-management-measures **article by its number** — which `regulated-domain-triage.md`'s own boundary forbids ("regimes are named by name only; no article numbers … until fetched, logged, and confirmed"), and that article's measure list was never reachable in the fetch; dropped the number at every locus, matching the CRA/EAA precedent (the eval no longer requires a boundary-violating answer to pass). (2) The `docs/standards-index.md` row had attributed business-continuity and supply-chain-security to recitals 79/89, which the fetch did not pin there; reworded to cite to the recitals only the categories they surfaced and to mark the full measure set as by-name / not-pinned. One eval + a Verification-list entry (business-ops 8 → 9). Research-derived (no filed issue). **business-ops → 1.5.0; trio → 1.158.0.**

## [1.157.0] — 2026-09-19

Wave 78 — **mergeability is a snapshot against a moving base head**, from issues **#376 + #379** (review-method deltas; dcr). "Green + mergeable" is a snapshot against the current base head, not a durable property: landing one PR can flip an overlapping PR back to CONFLICTING while its checks stay green (they ran against the old base). New `###` subsection in `branch-and-merge-hygiene.md`, after the merge-train section, at two scales — (1) *snapshot-then-batch*: re-check mergeability before **each** merge (not once at the top of the batch), and group the batch by file sets (serial-with-rebase within a group, parallel only across disjoint groups); (2) *sweep-while-resolving*: a merge sweep run concurrently with a resolver lane re-dirties the resolution on every merge, so **freeze the merge step (not the build step)** while a resolver is active — queue greens, land the hardest-to-rebase set first, then drain. Framed as the stale-base failure (below) at the mergeability layer. `fast-agentic-delivery.md`'s existing branch-and-merge cross-ref extended to point here (the #376 fleet-coordinator audience). One eval (deep-code-review 154 → 155). No new external standard → no `docs/standards-index.md` change. Trio → 1.157.0. Closes #376, #379.

Dogfood reviewer: FIX-FIRST → all four addressed pre-merge. (1) A parenthetical had over-claimed that the merge-train union "pre-empts most of this" — but that union branch is **thrown away** (step 4) and the member branches are left unchanged, so it proves the *combination builds* and surfaces the collisions without making a conflicting member mergeable; this also **contradicted #376's own tooling caveat**. Rewrote it: the union "does not make a conflicting member mergeable — sequence the resolver first, then run the train," and the per-merge re-check still applies at step 3. (2) Added the missing 🚩 red-flag line for this failure mode (the file's per-subsection convention). (3) Tightened eval expectation 1 to the unprompted causal claim (green CI ran against the *old* base, so it is not evidence of current mergeability). (4) PR body uses per-issue `Closes` keywords (GitHub's comma-list auto-close fires only on the first).

## [1.156.0] — 2026-09-19

Wave 77 — **per-diff delta gating over absolute-count ratchets under parallel lanes**, from issue **#375** (a review-method delta; agentic-delivery). An absolute-count gate over the whole tree — `--max-warnings N`, a coverage-percent floor, a bundle-size budget — is **contended shared state** under parallel write-lanes: two lanes off the same base each add a harmless delta, and the second to push goes red for consuming a slot the first already took (punished for arriving second; invisible until the second lane's CI runs; scales with fan-out width). New section in `fast-agentic-delivery.md`: **gate on the per-diff delta** ("no new warnings versus the merge base") — order-independent, so no lane consumes another's slot; keep the absolute count as a slow-moving burndown target, never the per-PR gate under fan-out; never raise the ceiling to pass (a ratchet only tightens). Explicitly distinguished from the adjacent phantom-warning `--max-warnings` false-fail (there the count is *wrong*; here it is *right but contended*), and generalized to any absolute-threshold gate on a shared counter (coverage %, bundle-size). One eval (agentic-delivery 32 → 33). No new external standard → no `docs/standards-index.md` change. Trio → 1.156.0. Closes #375.

Dogfood reviewer: FIX-FIRST → all three fixed pre-merge. (1) The cross-reference to the "cap in-flight lanes" section had read "the same **contention** as" — but that section's failure is over-admission (real spend with the integration head unchanged), not one lane's legitimate land red-flagging another; softened to "the same **shape** as" (the shared principle — gate on the quantity you own, not an ambient total — still holds, and the pointer stays useful). (2) The worked example was arithmetically under-specified: from a base of `N-1`, lane B reaches `N+1` only if lane A *also* added a warning — made lane A explicitly add one and take the last slot. (3) "never the per-PR gate" was unqualified, but an absolute ratchet is fine for a single committer (as #375 itself notes) — scoped it to "under fan-out" in the section, the eval, and this entry.

## [1.155.0] — 2026-09-19

Wave 76 — **EU Accessibility Act (EAA) name-and-route**, a new regulatory area (the coverage cartography's EAA candidate, now primary-sourced). A new tree entry in `business-ops/regulated-domain-triage.md`: a consumer product / service on the EU market (e-commerce, banking / payment terminals, transport ticketing & self-service, e-readers, computers / OS) → name the **EU Accessibility Act (Directive (EU) 2019/882)** + the EN 301 549 / WCAG engineering benchmark (routes to `frontend-a11y.md`); route in-scope / micro-enterprise-exemption / timelines to counsel (name-and-route boundary; no rot-prone dates encoded). Verified by direct fetch of EUR-Lex 2019/882 this session (the cartography couldn't reach a primary source; now logged in `docs/standards-index.md`). One eval + a Verification-list entry (business-ops 7 → 8). **business-ops → 1.4.0; trio → 1.155.0.**

Dogfood reviewer: FIX-FIRST → fixed pre-merge. The EAA ledger row had asserted "aligns with EN 301 549 / WCAG" attributed to the EUR-Lex fetch, but that page names neither standard — removed the claim from the ledger (EN 301 549 kept as a by-name engineering lead in the skill body only, WCAG stays grounded by its own row); softened the tree/eval "the benchmark **is** EN 301 549 / WCAG" to a lead-to-verify, per the name-and-route boundary.

## [1.154.0] — 2026-09-19

Wave 75 — **ML-pipeline correctness** (data leakage, training reproducibility, label quality), from research issue **#384** (a new area; dcr-only). Perun's AI coverage was security / output / governance-shaped; this adds the *correctness of a classical ML training/eval pipeline* — where a leaked split makes the reported metric **false** (the anti-fabrication thesis in classical-ML clothing).
- **`testing-and-evals.md` (new subsection):** split train/test before any preprocessing, fit preprocessing on the train subset only (a Pipeline stops CV/tuning leaking), no target/temporal leakage, no duplicate rows across splits — a leaked split *passes too well* (scikit-learn); and training must be reproducible (seed the RNG, pin data/model/code per reported number) so a metric delta is attributable (Breck et al., *The ML Test Score*, 2017).
- **`data-quality.md`:** requiring expert labels sets the bar but doesn't verify it — measure inter-annotator agreement (bounds label noise, caps the achievable metric), spot-audit errors, handle class imbalance honestly; label errors distort the metric *and* re-rank models (Northcutt et al., NeurIPS 2021, ≥3.3% avg errors across the 10 benchmarks studied). The *opposite* lesson from inter-model agreement.

Three sources verified by direct fetch (2026-09-19), in a new `docs/standards-index.md` section. Three evals (deep-code-review 151 → 154). Trio → 1.154.0. Closes #384.

Dogfood reviewer: PASS-WITH-NITS → scoped the Northcutt figure to "across the 10 benchmarks studied" (it had read as a universal property) and dropped a stray "~" in the eval; sources otherwise verified verbatim.

## [1.153.0] — 2026-09-19

Wave 74 — **EU Cyber Resilience Act (name-and-route) + VEX**, from research issue **#358** (cartography survivor — a new regulatory area + a supply-chain artifact).
- **CRA (`business-ops/regulated-domain-triage.md`):** a new tree entry — shipping a product with digital elements to the EU market → name the **EU Cyber Resilience Act (Regulation (EU) 2024/2847)** + its engineering-obligation leads (security-by-design; SBOM + coordinated-vulnerability-disclosure; a support / update period; reporting actively-exploited vulns to the designated authority → maps to dcr A03); route in-scope / conformity-class / reporting-authority / exact-timelines to counsel (name-and-route boundary; no rot-prone dates encoded).
- **VEX (`security-appsec.md` A03):** pair an SBOM with a **VEX** — a producer-issued per-CVE exploitability assertion (`not_affected` *with a justification*, `affected`, `fixed`, `under_investigation`) so a consumer distinguishes a real exposure from a component that merely *ships* the vulnerable code on an unreachable path (CISA VEX; complements, never replaces, the SBOM).

CRA + VEX verified by direct fetch this session (2026-09-19), in a new `docs/standards-index.md` section. Two evals — business-ops (6 → 7, + a Verification-list entry) and deep-code-review (150 → 151). **business-ops → 1.3.0; trio → 1.153.0.** Closes #358.

Dogfood reviewer: PASS-WITH-NITS → both fixed pre-merge. Generalized the CRA reporting recipient to "the designated authority" (the CSIRT-coordinator/ENISA specifics are correct to CRA Art. 14 but were not in the fetched summary — routed to counsel, per verify-before-cite), and added a VEX prompt to A03's *How to detect* so the eval's reviewer check has a home on the detection surface.

## [1.152.0] — 2026-09-19

Wave 73 — **crypto-agility & post-quantum readiness** in `security-appsec.md` A04, from research issue **#359** (cartography survivor — a new technical dimension; A04 reviewed *current* crypto but had nothing on algorithm agility or PQC).
- **Crypto-agility:** algorithm choices named in config / metadata (a versioned suite id), not hard-coded per call site, so a primitive can be rotated without a rewrite; a ciphertext / signature envelope carries an algorithm identifier so old and new coexist during migration.
- **Harvest-now-decrypt-later:** long-lived confidentiality warrants a migration path to the NIST post-quantum standards — **FIPS 203 ML-KEM** (KEM), **FIPS 204 ML-DSA** + **FIPS 205 SLH-DSA** (signatures), published 2024.
- **Bounded (not stricter than the standard):** the finding is a hard-coded, un-versioned primitive with no swap path on a long-lived-data surface — not "ship ML-KEM today." No compliance deadline encoded (rot rule).

- **GPC adjacent (domain Q):** honor the **Global Privacy Control** universal opt-out — the code reads `Sec-GPC: 1` / `navigator.globalPrivacyControl` and acts on it as a do-not-sell/share opt-out (a greppable check); the *legal* binding question routes to counsel / `business-ops` (`privacy-compliance.md`).

FIPS 203/204/205 + W3C GPC verified by direct fetch this session (2026-09-19), in `docs/standards-index.md`. Two evals (deep-code-review 148 → 150). Trio → 1.152.0. Closes #359 (PQC/crypto-agility + the GPC adjacent).

Dogfood reviewer: PASS-WITH-NITS (PQC half) → the one soft item was that #359 also names a "GPC adjacent (Q)" sub-scope; rather than half-close, built the GPC honor-check too so "Closes #359" is accurate. FIPS names + GPC signal verified verbatim by direct fetch; bounded (no PQC mandate / no deadline); provenance filed in a correctly-dated section.

## [1.151.0] — 2026-09-19

Wave 72 — **LLM-application engineering correctness** (RAG retrieval-seam + agent-trajectory eval), from research issue **#391** (cartography survivor — a new area under the existing agent/LLM archetype; section-add to `testing-and-evals.md`, no new archetype). The AI-evals section covered generic model-output quality but not the RAG retrieval seam or agent trajectories:
- **RAG evaluated at the retrieval seam, not only end-to-end** — a faithful answer over the *wrong* retrieved context is still wrong, and a good end-to-end score can hide a retrieval miss the model covered from parametric memory (which fails silently when the knowledge base changes). Evaluate retrieval quality (context precision / recall @k, chunk-boundary loss, reranking) AND generation faithfulness separately.
- **An agent is evaluated on its trajectory** — tool-call selection + arguments + multi-step completion — not only its final answer (a right answer via a lucky / unsafe path is a latent failure).

Framed by concept, not vendor: RAG technique = Lewis et al. 2020 (neutral anchor); metric names operationalized by a tool like RAGAS (a *tool*, not a standard). Both added to `docs/standards-index.md`; one-line cross-ref from `security-ai-agents.md` (the RAG *correctness* half vs its *security* half). One eval (deep-code-review 147 → 148). Trio → 1.151.0. Closes #391.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. Re-filed the two standards-index rows under a proper `2026-09-19` dated section (they had landed inside the 2026-09-08 idea-critic section — a date/scope contradiction) and scoped the RAGAS row to what the cited index page shows (per-metric definitions were read on the sub-pages). Un-conflated **faithfulness** (groundedness) from **answer relevancy** (addresses the question) — two distinct metrics — in the bullet and the eval.

## [1.150.0] — 2026-09-19

Wave 71 — **a deserializer re-enforces its builder's invariants** (`data-quality.md`), from owner-filed **#403** (top triage net-new). In a build → serialize → parse pipeline, a serialized line can be torn / hand-edited / older-schema / written by someone else, so "the builder guarantees X" does not mean a parsed object satisfies X. The parse path must independently **re-derive computed fields** (a count from the validated collection, not read verbatim) and **validate element shape** (not just a primitive type) — a parser weaker than its own builder reintroduces, at the deserialize trust boundary, the exact fabrication the builder prevents, invisible to a builder-only test suite. Proof: property tests `parse(serialize(x))` preserves the invariant + `parse(torn input)` drops/rejects rather than emits a violating object (a tautological generator tests nothing — ties #373). The data-integrity face of untrusted deserialization (CWE-502). One eval + a 🚩 red-flag (deep-code-review 146 → 147). Trio → 1.150.0. Closes #403.

Dogfood reviewer: PASS-WITH-NITS → tightened an over-claim ("tests nothing" → exercises only round-trip fidelity, never the violation path) and logged **CWE-502** in `docs/standards-index.md` (a pre-existing cite-without-log gap this wave also touches).

## [1.149.0] — 2026-09-19

Wave 70 — **slopsquatting**: a dependency existence / provenance check beyond name-proximity, from research issue **#402** (AI-code research). A03's only name discriminator was typosquat (a character off a popular name); a package name an LLM *hallucinated* — that an attacker pre-registers — isn't a typo of anything, so it passed every named check.
- **`security-appsec.md` A03:** verify a *newly-added* dependency resolves to an **established** package (registry age, download history, a real source repo / provenance), not merely that it isn't a typo. LLM-hallucinated names are a *predictable* pre-registration target.
- **`dependency-currency-and-upgrades.md`:** the release-age cooldown also catches a never-existed-until-now name (no history to clear the window); typosquat / slopsquat / maintainer-hijack named together.
- **By-defect, not author-gated** — the rationale mentions the elevated base rate in AI-assisted code, but the check gates on the dependency's provenance, never on who wrote the diff.

Source (USENIX Security 2025, Spracklen et al.) added to `docs/standards-index.md` + the file's own standards list. One eval (deep-code-review 145 → 146). Trio → 1.149.0. Closes #402.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. The reviewer fetched the USENIX PDF and confirmed every figure accurate, but caught two provenance-honesty defects in the standards-index row: a false "corroborated across the authors' GitHub" claim (the GitHub states a 19.7% overall rate, not the per-model figures) and a per-package-vs-per-sample denominator misframe. Corrected the row ("at least 21.7% of *packages recommended by* open-source models …"; GitHub corroborates names/samples/models + a 19.7% overall rate), removed the inline figures from A03 (they live in the ledger), and fixed the eval's denominator.

## [1.148.0] — 2026-09-19

Wave 69 — a new **i18n / l10n depth reference** (domain R), from research issue **#390** (coverage cartography — a genuinely new area, no new archetype). Domain R routed only to an 8-line checklist that omitted bidi/RTL; new `references/i18n-l10n.md` carries the standards-heavy depth a checklist can't hold, routed from the R map row + the checklist header:
- **Encoding & normalization:** UTF-8 declared in-document; normalize before compare / dedup / key — and *after* concatenation, because "None of the Normalization Forms are closed under string concatenation" (UAX #15), so per-fragment NFC can still assemble to un-normalized output.
- **Bidi / RTL:** declare `dir`; wrap opposite-direction phrases; reject/flag Unicode bidi *override* controls (UAX #9 — "avoided … because of security concerns," UTR #36) — the Trojan-Source class.
- **Plurals / formatting / collation:** CLDR plural categories (zero/one/two/few/many/other), never `n == 1`; locale-aware number/date/currency formatting; a locale collator, not `.sort()`; text-expansion room.

Sources verified by fetch this session (2026-09-19): W3C i18n, UAX #15, UAX #9 + UTR #36, Unicode CLDR — all added to `docs/standards-index.md`. One eval (deep-code-review 144 → 145). Trio → 1.148.0. Closes #390.

Dogfood reviewer: PASS-WITH-NITS → both fixed pre-merge — scoped the UAX #9 "avoided … because of security concerns" quote to the **overrides** (RLO/LRO) and distinguished them from the *safer* **isolates**; "see UTR #36".

## [1.147.0] — 2026-09-19

Wave 68 — a data-provider / integration-contract review lens for `data-quality.md` §12 (domains D + I), from owner-filed **#345**. When a product's job is to *feed another system's scoring / automation*, the contract seam has four failure modes no shape-only (domain I) check catches:
- **Emits raw events when the consumer needs scoring inputs** — should emit windowed aggregates + velocity keyed on the consumer's canonical ids (with provenance + license/tier), not triggers the consumer must re-aggregate.
- **Static / manual delivery** where the consumer needs a **live channel + cadence** (a table/feed read on schedule).
- **No per-field source-of-truth declaration** (authoritative / partial / never) — so the consumer wires fields the provider never ships.
- **A claimed input stale or misclassified vs the provider's live artifact** — reconcile every claimed provider-input (count + classification) before it drives a downstream score (a pre-reclassification blend can be off ~100×). Gate: diff declared provider-inputs vs the actual current output; a mismatch blocks sign-off.

Shape stays in `api-contracts.md` (consumer-driven contract); this is the quality / semantics half at the provider seam. One eval + a §12 red-flag (deep-code-review 143 → 144). Trio → 1.147.0. Closes #345.

Dogfood reviewer: PASS-WITH-NITS, no must-fix (all four modes verified genuine deltas, not restatements; the "~100×" example is owner-sourced and generic).

## [1.146.0] — 2026-09-18

Wave 67 — a delivery-CI hygiene batch from owner-filed **#346** and **#349**.
- **#346 (`docs-and-dx.md`) — a gate's stated *location* is a claim with its own currency.** When a gate moves (CI → local-only, one job to another, behind a label/trigger), an agent runs what the docs / PR template / comments *say* runs. Audit agent-facing docs for dangling CI job/label/trigger references (a dead reference is a defect); a relocation to local-only makes the local bar the blocking one; **fail the audit closed** — a gate whose docs can't name a live location is unenforced until proven otherwise. Else the gate runs *nowhere* while every surface reads green.
- **#349 (`branch-and-merge-hygiene.md`) — a worktree-relative hook runs its base's copy; land the safe hook everywhere first.** Second-order to #298: once hooks resolve per-worktree, a lane cut from an old base runs *that base's* (stale / heavyweight) hook and hangs → gets bypassed. Rules: hook content fail-safe by default (safe core, slow/interactive steps opt-in); land the safe hook on every long-lived base *before* normalizing resolution; verify which hook runs (base-dependent, idempotent re-assert); an audited escape hatch instead of a whole-tier `--no-verify`.

Two evals (deep-code-review 141 → 143). Trio → 1.146.0. Closes #346, #349.

## [1.145.0] — 2026-09-18

Wave 66 — verify-the-premise before acting, two additions to `method.md`'s presence/absence section (extending #250), from owner-filed **#353** and **#363**.
- **#353 — a perception-sourced "it's missing" against code that already implements it is a `delivery-gap`, not a build order.** A third verdict beside confirmed-absent and false-absent: when runtime confirms the capability is present but a reporter evaluated the surface as missing, the working code isn't reaching them. Diagnose why (build/env drift, route/mount mismatch, preference/state gating); deliver the reason + the smallest fix, not a reimplementation.
- **#363 — a "broken / decorative / always N" premise is a claim to verify against live data, and a flat metric can be the honest answer.** Measure the live distribution and read the code before fixing (the "constant" may be an already-overwritten initializer); a near-constant value can be the honest truth of the corpus, and inflating it via fuzzy / non-independent matching fabricates it — make the count provable and gated, not larger (empty beats fabricated).

Also: fixed the stale `docs/roadmap.md` status line ("main @ 1.48.0" → a dated snapshot pointing at `VERSION` / `CHANGELOG`).

Two evals (deep-code-review 139 → 141). Trio → 1.145.0. Closes #353, #363.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. Medium: "empty beats fabricated" was cited as `SKILL.md` principle 4, but that principle is *Do no harm* — anti-fabrication is **principle 3** (corrected in the new prose + the eval; the pre-existing repo-wide mis-numbering cluster is filed separately, not widened into this diff). Also added a 4th delivery-gap diagnostic axis (runtime / integration fault — a reached, mounted control whose live channel never connects / backend never emits / error is swallowed) and made the "third outcome" enumeration scope explicit (unconfirmed-absent is the couldn't-boot branch).

## [1.144.0] — 2026-09-18

Wave 65 — a UI-state / test-integrity batch from owner-filed **#360 / #361 / #362** (the "green logic test, broken UI" family).
- **#360 (`product-ux-quality.md`) — a disclosure default derived from async-fetched data silently never fires (mount-capture).** `useState(open)` seeded from a value the hook doesn't re-sync locks in first-paint state; an async signal that lands after mount never applies (unit test green, running UI wrong). Fix: drive the mount default from synchronous data, surface the late signal via a non-reflowing affordance (not force-open), verify in the running app.
- **#361 (`testing-and-evals.md`) — a state-dependent spec must assert its precondition, not lean on a default.** A browser spec that asserts on expand-only content, or clicks a bulk toggle a redesign removed (`if (count) click` — a no-op), is green only because the default matched; flip the default and it breaks at the slow gate. Drive the state explicitly; prefer an explicit assertion over best-effort click-if-present.
- **#362 (`testing-and-evals.md`) — pin the equivalence between a should-render / should-expand predicate and the set it gates.** `predicate(x) === (renderSet(x).length > 0)`, both directions and non-vacuous, so a "smart default" can't drift into hiding real content or expanding an empty container.

Three evals (deep-code-review 136 → 139). Trio → 1.144.0. Closes #360, #361, #362.

## [1.143.0] — 2026-09-18

Wave 64 — a UX / audit-visibility honesty lens for `product-ux-quality.md` (domain P), from owner-filed **#351**. When an action **presented as non-destructive** (resolve / archive / dismiss, backed by a retained `resolved_at` / `archived_at` column) removes the record while giving **no cue that it persists, is reversible, or where it went**, the user cannot tell it from a hard delete — two failures:
- **Product-safety:** the action reads as destructive (a first-time user watches the row vanish and concludes they deleted it), suppressing a reversible, low-stakes action.
- **Audit / history visibility:** when the retained trail is meant to be reviewable, an unreachable surface makes it effectively invisible (the data is intact; the defect is visibility, not integrity).

**Scoped to the hidden reversibility, not default-hiding as such:** hiding a completed item behind a known filter (an `is:open` list, an active board, inbox archive) is a convention, not a defect; a soft-**delete** (`deleted_at`) is out of scope ("reads as a delete" is intended there). **Fail-open** — a human adjudicates every hit. Fix: keep the record in place, muted + a status label, or a discoverable labelled resolved/archived view; not colour-alone; verify on the running app's default surface. Pattern described generically (no vendor named).

One eval + one domain-P checklist box (deep-code-review 135 → 136 evals). Trio → 1.143.0.

Dogfood reviewer: FIX-FIRST → fixed pre-merge. High: the flag criterion was over-broad (it flagged conventional archive / `is:open` default-hiding and prescribed rendering soft-deleted rows forever) — rescoped to labelled-non-destructive + no-persistence-cue, carved out conventions + soft-delete, added the fail-open human-adjudicates clause. Also added the missing sweep-checklist box and relabelled "data-integrity"→"audit / history visibility."

Closes #351.

## [1.142.0] — 2026-09-18

Wave 63 — two anti-fabrication data-honesty axes for `data-quality.md` (scoring & config discipline, §7), from owner-filed **#344** and **#355**.
- **#344 — name a derived field for what it measures, not the conclusion you want.** A column called `relationship_strength` that is really a co-occurrence *count* is a schema-level overclaim; surface the corroborating evidence (co-authored N papers; met at N events), not a manufactured score; require multiple independent signals before asserting a tie (a lone co-mention/co-attendance is a lead, not a relationship); and reconcile a relationship's **two-sided** edge. The UI half is the confidence-tier false-precision rule (`product-ux-quality.md`).
- **#355 — a ranking / scoring / leaderboard gates on an *observed* liveness signal; a missing liveness field is a blocker.** Ranking without a liveness gate puts dead / discontinued entities on a live shortlist; liveness comes from the subject's own recent activity, not mere record existence; no liveness signal → fail closed (exclude / flag `unknown`), never "rank everything, filter later." The affirmative complement to the exclusion-gate-fails-closed bullet above it.

Two evals (deep-code-review 133 → 135). Trio → 1.142.0. Closes #344, #355.

## [1.141.0] — 2026-09-18

Wave 62 — verify-first before laning a tracked issue, from owner-filed **#352** (and the doctrine half of **#347**). An issue's OPEN state is not proof its fix is absent: GitHub auto-closes a linked issue only "when you merge a linked pull request into the default branch," and `Closes` / `Fixes` / `Resolves #N` are "interpreted only when the pull request targets the repository's default branch" (verified against GitHub Docs this session). A fleet that merges day-to-day into a long-lived integration branch therefore leaves issues **done in the tree, open in the tracker** — and an agent reading "open" as "not done" re-lanes finished work.
- **New subsection in `fast-agentic-delivery.md`** (the duplicate-work home): before opening a fix lane for a tracked issue, grep the *integration* branch you would base on for the fix's landmark; know the forge's auto-close scope; if already delivered, stop and report "already delivered" with `file:line` + the commit SHA, don't re-lane, and don't hand-close ("done" = merged to the default branch).
- **#347's automation half is routed, not built.** A team merging off-default must *supply* a scoped close-on-staging-merge automation (explicit `Closes #N` only, never a heuristic; least-privilege; idempotent) — that is project tooling, owner-gated, out of this prose skill's charter.
- **Provenance.** GitHub linked-PR doc added to the file's own Sources **and** `docs/standards-index.md` (fetched 2026-09-18).

One eval (agentic-delivery 31 → 32). Trio → 1.141.0. Closes #352; #347's doctrine landed here, its automation stays open as an owner-gated tooling item.

## [1.140.0] — 2026-09-18

Wave 61 — name the exploited-in-the-wild instruments for the "known-exploited" severity gate, from research issue **#357**. `dependency-currency-and-upgrades.md`'s severity discipline gated on "Known-exploited (or high-CVSS)" but named **no source** for "known-exploited" — a gap the skill's own principle 2 (prefer the canonical instrument) exposes.
- **Named instruments.** A "known-exploited" finding must now cite the canonical source: **CISA KEV** ("the authoritative source of vulnerabilities that have been exploited in the wild") for *is it exploited now*, and **FIRST EPSS** (probability a CVE "will be exploited in the wild in the next 30 days") for *how likely*. Read alongside CVSS (likelihood vs severity) — the same multi-signal discipline the rubric applies everywhere.
- **Guardrail — inputs, not a lower bar.** Both bodies cast their scores as an *input* to prioritization, so KEV / EPSS **raise and rank, never lower the bar**: a low EPSS, or a CVE's absence from KEV, does **not** disarm a reachable-path finding (absence of exploitation evidence is not proof of safety; EPSS is a 30-day probability, not a verdict) — the same refusal to over-trust a derived number that the confidence-tier false-precision rule applies to UI display.
- **Provenance.** KEV + EPSS added to the file's own standards list **and** `docs/standards-index.md` (both URLs fetched this session, 2026-09-18) — the ledger-mirror discipline.

One eval (dcr 132 → 133). Trio → 1.140.0. Closes #357.

## [1.139.0] — 2026-09-18

Wave 60 — build-side product playbook from owner-filed **#343**. Perun's domain P reviews a product surface for defects; it was not written as a build spec. New reference `agentic-delivery/references/production-grade-product-playbook.md` adds the build→verify direction: it names the positive build-time patterns and pairs each with the domain-P axis that verifies it.
- **Scope — net-new only, no restatement.** The patterns already stated once as enforced review axes (why-it-matters / actionability #332, ranking & sort legibility #333, progressive disclosure, one-component-per-concept, interaction-completeness) are *pointed at* `product-ux-quality.md` in a build→verify table, not copied (a second copy is the duplication this suite condemns). The file adds only the three build-time patterns domain P assumes but does not shape: **job-first information architecture** (derive the layout from the user's core decision; illustrative surface-shapes, not a taxonomy to complete), **lead with the relationship, not the record** (for entity-graph products), and **density as a build target** (choose the baseline in the G3 ADR, don't inherit a component-library default).
- **Placement.** Lives in `agentic-delivery` (the build side, G3 Design), not `deep-code-review` (whose identity is the review bar, and whose `SKILL.md` is byte-capped) — routed from the G3 design block with a "read it when" trigger; verified by dcr domain P at G6.
- **Provenance.** Cites public design *conventions*, never a private vendor; a named precedent method takes a `docs/standards-index.md` row.

One eval (agentic-delivery 30 → 31). Trio → 1.139.0. Closes #343.

## [1.138.0] — 2026-09-18

Wave 59 — verification-honesty deltas from owner-filed #334 / #336 / #340 (the other four of the #334–#340 batch — #335/#337/#338/#339 — were already covered and closed with file:line evidence, not duplicated). Three small, seam-guarded additions:
- **#334 — a visual receipt must show the feature, not a wall past it** (`testing-and-evals.md` + `product-ux-quality.md` checklist): non-empty is necessary, not sufficient — a login / error / empty page is a valid non-empty image; capture authenticated content via a **dev / identity-bypass render mode**, not a route-auth-walling production build; prefer a deterministic readiness signal over a network-idle heuristic (a hot-reload socket defeats it). Discriminated from reproducing a **build-specific** defect (which uses the production build, `method.md`) so it doesn't contradict that rule.
- **#336 — a persistent cannot-check is not a finding** (`reliability-error-handling.md`): a gate reaching an external dependency retries a transient error bounded, then on a persistent outage / timeout / retired endpoint **does not block and is not reported as a finding** — fails closed only on an observed problem; never wire a gate to a retired/unversioned endpoint; bound the gate's own runtime. **Exception:** a security / authz / integrity / spend attestation still **fails closed** on a can't-verify (a fail-open there is the bug). Phrased as "does not block / not a finding" (**not** "fails open", which already denotes the reviewer-honesty could-not-check status elsewhere).
- **#340 — an operating-discipline doc for stable environment invariants** (`docs-and-dx.md`): record how to render a reviewable/authenticated state, which capture tool works, which gates are conditional, known flakiness — once, read before environment-dependent work; a rediscovered invariant is filed back as part of closing the task. Scoped to **stable invariants** (a derived status still follows "store the query, not the answer").

Two evals (dcr 130 → 132). No `SKILL.md` content change (all four references already routed). Trio → 1.138.0. Closes #334, #336, #340.

## [1.137.0] — 2026-09-18

Wave 58 — two owner-filed product-value axes for `product-ux-quality.md` (domain P), **#332 + #333** (dogfood-derived). The domain-P rules prove a component *renders* correctly; these add the *does it help the user act* half. Two distinct sections (different failure modes, evidence, gates):
- **Actionability (#332)** — a primary information unit answers *why it matters* via a **derived** signal (count / recency-delta / graph-degree) plus a concrete next step where an action is possible, most-actionable-first-and-stable. **Hard anti-fabrication rule:** the signal is derived/deterministic, never a model-authored importance score or LLM salience judgement (the content-layer cousin of the confidence-tier false-precision rule). Warn-and-list (fail-open) heuristic gate, explicitly contrasted with the fail-closed `ci-gates.sh` check-#6/#7.
- **Ranking & sort-mode legibility (#333)** — the default order serves the user's job (recency is a mode, rarely the right default on a decision surface); each exposed sort mode is self-explaining ("orders by …") and **measurably distinct** (near-identical modes collapse; the sort key needs a measured distribution — an opaque/near-constant key is ordering-layer false precision). Extends the variant-bloat rule to ordering, and owns the shared default-ordering principle the actionability section references (stated once).

Private-vendor exemplars from the issues are described as **patterns, not named** (CLAUDE.md third-party-identifier rule); the public **Smart Brevity** method is named and added to `docs/standards-index.md` by-name. Two checklist items + two evals (dcr 128 → 130). No `SKILL.md` content change (domain P already routes `product-ux-quality.md`). Trio → 1.137.0. Closes #332, #333.

## [1.136.0] — 2026-09-18

Wave 57 — `domain-checklists.md` middle-tier de-duplication, **#325 Option A** (owner-selected). The checklist tier restated definitions its per-domain deep files own — the repo's own anti-duplication thesis, violated. Surgically converted the **3 copied definitions/rules the #325 audit surfaced** to a scannable check + a pointer to the canonical deep file (each verified do-no-harm: the full detail was confirmed present in the deep file before the copy was dropped):
- **Monotonic-quality invariant** (domain D) — near-verbatim from `data-quality.md` (dc even linked while copying); now gist + `data-quality.md` §1 (full invariant + two-part non-regression gate) and §5 (the every-mutation-primitive / discover-write-sites coverage).
- **CSRF-guard-is-not-authentication** (domain B) — the "why it's bypassable" + the CWE-352-vs-CWE-306 split now point to `security-appsec.md`; the check (CSRF ≠ auth → effectively unauthenticated) stays.
- **Open-work triage scope + deliverable** (domain S) — a 3rd verbatim copy; the compact-packet scope rule + the triage deliverable now point to `branch-and-merge-hygiene.md`; the domain-S-unique O/S seam stays.

The other two audit pairs (the F and I sections' 🚩 quick-scan lists) were **assessed and kept**: a 🚩 quick-scan IS the checklist's core function (dc:7), the section headers already route to the fuller lists in the deep files, and dropping them would regress the reviewer's scannability — do-no-harm over literal conversion (A1 rated them Nit/acceptable). Trio → 1.136.0.

## [1.135.0] — 2026-09-18

Wave 56 — link-rot / citation-freshness audit of `docs/standards-index.md` (the "verify before citing" ledger, which `install.sh` vendors into every install's `references/`). Re-fetched every cited URL: content was accurate (**zero drift across ~90 URLs**) but not fully live — **1 dead + 4 moved**, now fixed and each re-verified by direct fetch this session:
- **Dead:** the OWASP ASVS project page now 404s (OWASP is migrating `www-project-*` → `projects/*`) — repointed to `github.com/OWASP/ASVS`; re-verified 5.0.0 / May 2025 / the `v<version>-<chapter>.<section>.<requirement>` id form, and **dropped the L1/L2/L3 level claim** (not re-verifiable on the new URL — ASVS 5.0 restructured; do not cite levels without the 5.0 spec). Date precision corrected "30 May" → "May 2025".
- **Moved (cited content verbatim-intact at the new host):** OWASP Top 10:2025 → `top10.owasp.org/2025`; its A03 detail; OWASP API Security 2023 → `api-security.owasp.org`; the GitHub Actions security page → `.../reference/security/secure-use` (renamed "Secure use reference"; two quotes re-stated to the page's current wording).

Added a dated freshness note at the ledger top; original per-section verification dates left unchanged (they record first verification). Trio → 1.135.0 (the ledger is not a skill; no skill-content change).

## [1.134.0] — 2026-09-18

Wave 55 — a CI gate for the recurring Verification-list doc-sync miss (its root-cause fix). Adding an eval to a skill that enumerates one Verification bullet per eval (closed by "plants these cases") has silently left a later-added eval un-enumerated **four times** (product-output-safety since v1.75.0, undetected until this gate; v1.125.0; and two caught in review at v1.133.0) — no gate referenced eval ids. `scripts/ci-gates.sh enumeration` now has a **check #7**: for a closed allowlist of the six skills that enumerate EVERY eval id (`business-ops`, `contribution`, `growth-analytics`, `positioning`, `product-discovery`, `product-output-safety`), every id in `evals/evals.json` must appear in `SKILL.md`, fail-closed. Scoped by allowlist because the "plants" marker is ambiguous — `idea-critic` and `agentic-ceo` carry it but name only key cases, and the large skills do not enumerate (an unscoped check would false-flag them). Planted-red self-test added, incl. a scoping assertion (`test-ci-gates.sh` 73 → 74). The **fourth instance, caught by the new gate**: `product-output-safety`'s Verification list was missing `confidence-as-defined-tier-not-model-number` (its eval was added at v1.75.0; the behaviour was already in the method at "Show uncertainty as a defined tier", only the enumeration bullet was absent) → product-output-safety 1.3.2. Trio → 1.134.0. The allowlist is **manual and, unlike checks 1–5, does not self-gate**: a new enumerate-every-id skill must be added to it by hand (a typo'd/stale entry is fail-closed by a resolves-check after the loop; a missing addition is not caught).

## [1.133.0] — 2026-09-18

Wave 54 — audit-2 remediation (portability + eval coverage), from two focused follow-up audits.

### Portability — install.sh
Audited against the suite's loudest claim (agent-agnostic install): `install.sh --full --with-codex` lands every skill at all four host roots (`.claude` / `.cursor` / `.agents` / `.codex`), with `references/` — including the vendored `standards-index.md` and `example-review-report.md` — present at **each** root; the claim holds. One fix: the generated `AGENTS.md` **repeated the primary path** ("Primary path: `X` (`X`; also …)") because `LOCATIONS` began with the primary path. It now lists only the **mirror** roots, and omits the parenthetical entirely under `--minimal`. Verified across default / `--full --with-codex` / `--minimal`. (REVIEW.md / `## Code Review Rules` is correctly a Phase-6 review-time imprint, not an install-time write — no change.)

### Eval coverage — four load-bearing rules were untested
The eval-quality audit found rule-consistency and non-duplication **clean across all 11 skills**; the only defects were four load-bearing rules with zero eval coverage. One eval added to each:
- **agentic-delivery** (→ 1.133.0): a paid-model-call lane with no per-lane budget is **BLOCKED** (not run unlimited) and **UNPRICED** (not zero) — the G2 spend-cap invariant.
- **contribution** (→ 1.1.1): a paraphrased confidential fact that **passes the banlist** is surfaced in the residual-risk block for a human — the scrub is necessary, not sufficient.
- **idea-critic** (→ 1.133.0): an objection resting on a **stale number** is re-verified against current state and a sound proposal reaches PASS_TO_USER — the anti-false-negative axis.
- **growth-analytics** (→ 1.1.1): AARRR read **bottom-up** — diagnose retention before pouring in acquisition.

Trio → 1.133.0 (dcr `SKILL.md` version-only, no content change); contribution → 1.1.1; growth-analytics → 1.1.1.

## [1.132.0] — 2026-09-18

Wave 53 — round-3 external research (one net-new gap; the rest of the scan confirmed already-covered). Added a **mutation-testing** lens to domain J (`references/testing-and-evals.md`): the quantified method for the suite's most-repeated testing thesis — coverage measures what *ran*, not whether a test would *catch a fault*. When load-bearing logic leans on a coverage number as its assurance, measure the product suite's fault-detection with a **mutation score**; a **surviving mutant is a finding in the method's own shape** — a `file:line` plus the exact behaviour no test asserts (a High-confidence weak-assertion finding). Names the technique + the CI operator (Stryker's `thresholds.break`; no endorsed threshold number) + representative engines (Stryker JS/TS, PIT JVM, plus per-language equivalents), keeps it **distinct from the gate-planted-defect self-test** (that proves the checker; this scores the shipped tests), and **bounds it to the highest-stakes modules** (a mutation run scales with suite size × mutant count). One new eval (dcr 127 → 128). `docs/standards-index.md` gains pitest.org + stryker-mutator.io (**verified by direct fetch 2026-09-18**). Trio → 1.132.0; `SKILL.md` content unchanged apart from the gate-required version bump (depth lands in the routed reference). (The operator's fail-open default — Stryker's `break` is `null` unless set — is disclosed in the lens so the gate is not mistaken for one that already fails closed.)

## [1.131.0] — 2026-09-18

Wave 52 — self-audit remediation (agentic-delivery leanness). Trimmed the redundant G5 restatement in the "local stack up" procedure (`agentic-delivery/SKILL.md`): it re-stated the G5 gate row's UI rule verbatim, so it now points to G5 and keeps only the unique `product-ux-quality.md` link and the step-3 → G5 tie. Brings the file **24009 → 23945 B, back under 24000** (resolving the float disclosed in v1.129.0; it remains the largest SKILL.md, so its size-allowlist entry stays valid). Trio → 1.131.0; no other skill-content change. (The D2 fork-inheritance bullet was assessed and **kept** — it is the general-lane application, distinct from `parallel-audit.md` §2's read-only-fan-out case, and already cross-refs it; collapsing it would lose the general-lane mitigation. The `domain-checklists.md` middle-tier de-duplication is proposed as an owner decision in #325.)

## [1.130.0] — 2026-09-18

Wave 51 — self-audit remediation (gate hardening, from the four-agent audit's A4 Low). `scripts/ci-gates.sh enumeration` check #6 now **fails closed on a skill dir carrying neither `SKILL.md` nor `VERSION`**. A fully-enumerated but empty dir previously passed the subcommand (checks 1–5 pass; check #6's three branches covered skill-only / version-only / both-present, not both-missing) — the CI *suite* still caught it via the globbed name-matches-dir job and `routing`, but the subcommand was not self-sufficient and its comment over-claimed that checks 1–5 covered the case (the recurring over-claim-in-prose class, here about a gate). Added the both-missing branch, corrected the comment to name the real backstop, and added a planted-red self-test (`test-ci-gates.sh` 72 → 73; the pre-existing ghost fixture's `realskill` is now given files so ghost's omission stays the sole defect). Trio (`deep-code-review`, `agentic-delivery`, `idea-critic`) → 1.130.0; no skill-content change.

## [1.129.0] — 2026-09-18

Wave 50 — self-audit remediation (Perun's own bar on Perun; four independent audit agents found zero Blocker/Critical/High). No change to what a review of a target produces — internal suite cleanup plus one install-time pointer fix. Trio (`deep-code-review`, `agentic-delivery`, `idea-critic`) → 1.129.0; the independent-line overlays touched here bump patch.

### Leanness — deep-code-review (SKILL.md 23872 → 23507 B; hard 24000-byte gate, headroom 128 → 493)
- Collapsed the Definition-of-done status bullet to a one-line pointer: the whole rule (evidence surface, strongest reading, tree-under-review URL/branch/sha, no-surface-named = invalid, `validate_status_claims.py`) already lives in `references/report-format.md`; the DoD restated it. Closes a status-rule-stated-three-times duplication.
- Moved the security-team colour **definitions** to `references/role-coverage.md` (which already tabulates them); **kept the Black-team prohibition inline** (a safety constraint stays in the always-loaded file).

### Provenance ledger — docs/standards-index.md (by name only; no URLs fetched this session)
- Added the threat-modeling method catalog cited inline in `security-appsec.md` / `security-ai-agents.md` — **STRIDE, PASTA, LINDDUN, MAESTRO, attack trees, OWASP SAMM, BSIMM** — closing the recurring cite-without-a-ledger-row miss.
- Added **RFC 2119**, **llms.txt**, **choose-boring-technology / innovation tokens**, and **evolutionary architecture / fitness functions**.
- Added a **product-discovery** by-name row (Mom Test, JTBD switch interview, Torres continuous discovery, Ellis PMF survey, Testing Business Ideas, ICE/RICE, fake-door/concierge/Wizard-of-Oz) and extended the **growth-analytics** row with the experiment-rigor leads (peeking, always-valid/mSPRT, group-sequential/alpha-spending, CUPED, product-led growth).

### Correctness + hygiene
- **Install-time pointer bug:** four overlays pointed unconditionally at `communication-structure`, which their own `--with-*` flags do not install. Conditioned on "if installed" with a BLUF fallback (the `agentic-delivery`/`idea-critic` pattern): **business-ops → 1.2.1, positioning → 1.0.1, product-output-safety → 1.3.1, agentic-ceo → 1.1.1**.
- README: moved **Nielsen's usability heuristics** into the verified-by-fetch summary (it was listed under "referenced by name"); tightened the overlay-count wording.
- `agentic-delivery`: prefixed its three own-reference targets (`template-adr.md`, `retrospective.md`, `template-postmortem.md`; four citations) with `references/` — a bare basename otherwise reads as a `deep-code-review` sibling file. This added ~44 B, floating the file 23965 → 24009 B on its standing owner-reasoned size-allowlist (`ci-gates.sh`); a trim back under 24000 is scheduled with the `agentic-delivery` de-duplication in the next (dedup) wave.

## [1.128.0] — 2026-09-18

Wave 49 of the dogfooding batch: re-applies the machine-report format from external contribution #142 onto current main — the spec for the machine-readable findings file a program consumes. The contribution's author is credited in the commit trailer; the stale fork PR is closed as superseded by this re-application. Lead change is in `deep-code-review`; `agentic-delivery` and `idea-critic` bump in lockstep with no content change.

### Added — deep-code-review
- **`references/machine-report.md`** (#142) — the findings file a program consumes: block-style YAML
  carrying the same findings, ids, severities, and areas as the markdown report, a **coverage row for
  every assigned domain (A–T and W)** (absence of a row is not a clean run — a consumer cannot tell
  "no findings" from "not scanned"), plus the re-verification (`PRIOR`) and fan-out shapes. Routed
  from `SKILL.md` beside the Phase-5 report templates; `report-format.md`'s first machine-report
  mention now points at the spec. Disclosure **extends** the report's finding-level rule: a public
  committed copy keeps finding `id` / `area` / `severity` plus the disclosure-safe run header and
  `target`, and **generalizes** the two identifier-vector fields (`base_ref` per `report-format.md`'s
  branch-name rule, `prior`). One new eval (dcr 126 → 127).

## [1.127.0] — 2026-09-18

Wave 48 of the dogfooding batch: #281 — pricing-strategy methods in `business-ops` Lane A (an independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.127.0 via the CHANGELOG coupling, no dcr content change).

### Added — business-ops (→ 1.2.0)
- **Pricing-strategy methods** (#281). Lane A now names the pricing-method space beyond value/
  cost-plus/competitor: the **Van Westendorp** price-sensitivity survey (structured for the user to
  run; read the band back from their results) and **usage-based / outcome-based / per-seat /
  good-better-best** packaging (tied to the user's value metric; usage/outcome fit AI cost-scaling)
  — applied to the user's willingness-to-pay, never setting the price, never fabricating a survey or
  market number. Methods named by-name. One new eval (business-ops 5 → 6). **OKRs (in the issue
  title) were not added** — goal-setting is outside business-ops's money/compliance two-lane scope.

## [1.126.0] — 2026-09-18

Wave 47 of the dogfooding batch: #276 (regime half) — name-and-route the AI-governance regimes in `product-output-safety` (independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.126.0 via the CHANGELOG coupling, no dcr content change). Completes #276.

### Added — product-output-safety (→ 1.3.0)
- **Name-and-route the AI-governance regimes** (#276, regime half). The hard-boundary and
  Standards-by-name sections now name the **EU AI Act** and **ISO/IEC 42001** (AI-management-system)
  alongside NIST AI RMF, and route the binding applies/obligations/deadline question to counsel —
  **no dates or version numbers** (both regimes revise; the EU AI Act timeline is amendment-sensitive).
  Names and routes only; asserts no duty. One new eval (product-output-safety 6 → 7). With the cards
  half (v1.124.0), this completes #276.

## [1.125.0] — 2026-09-18

Wave 46 of the dogfooding batch: a documentation-sync fix in `business-ops` (an independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.125.0 via the CHANGELOG coupling, no dcr content change).

### Fixed — business-ops (→ 1.1.1)
- **Verification list omitted a shipped eval id.** The `## Verification` "plants these cases" list
  named four of the skill's five evals; added the missing `design-time-regulated-domain-triage`
  bullet so the rules→eval-id map matches `evals/evals.json`. Documentation-sync only — no behavior
  or eval change.

## [1.124.0] — 2026-09-18

Wave 45 of the dogfooding batch: #276 (cards half) — model/data cards as a transparency-artifact check in `product-output-safety` (an independent-line overlay; the AI-governance-regime half of #276 stays owner-deferred).

### Added — product-output-safety (→ 1.2.0)
- **Model / data cards** (#276, cards half). MEASURE gains the transparency artifact: a shipped AI
  feature carries a **model card** (intended use, subgroup performance, limitations, owner+version)
  and a **data card / datasheet** (data composition, provenance, consent, gaps); its absence is a
  transparency finding, and a card stating an unmeasured metric is the no-fabrication floor in a
  template. Cards named by-name (Model Cards / Datasheets / Data Cards; three ledger rows). One new
  eval (product-output-safety 5 → 6). The NIST AI RMF half of #276 was already covered
  (the product-output-safety Standards-by-name section, NIST AI RMF entry); the ISO 42001 / EU AI Act regime half is **owner-deferred**
  (amendment-sensitive). The dcr/agentic-delivery/idea-critic trio bumps to 1.124.0 via the
  CHANGELOG coupling — no dcr content change.

## [1.123.0] — 2026-09-18

Wave 44 of the dogfooding batch: #277 — LLM/agent telemetry (OTel GenAI) + honest developer-productivity measurement (SPACE/DevEx).

### Added — deep-code-review
- **LLM/agent telemetry** in `observability.md` — an LLM/agent feature needs first-class per-call
  signals (token usage, latency, cost, model+version, outcome, a trace), not just service latency/
  error; the **OpenTelemetry GenAI semantic conventions** (`gen_ai.*`) name them — adopt the names,
  pin no version (the spec is at *Development* stability). Do not log raw prompts/responses (PII).
- **Developer-productivity honesty** in `release-engineering.md` (beside DORA) — productivity and
  experience are multi-dimensional (**SPACE / DevEx**); a single proxy (LoC, PR count) is gameable
  false precision; route a people-performance judgement to the owner, never assert it from repo
  activity.

Frameworks named **by-name** (three ledger rows in `docs/standards-index.md`, no URL/version). One
new eval (126 total).

## [1.122.0] — 2026-09-18

Wave 43 of the dogfooding batch: #279 — architecture maturity (Well-Architected), cloud cost (FinOps), and resilience (chaos engineering).

### Added — deep-code-review
- **Well-Architected pillars** in `infra-iac-containers.md` — review the design across the
  cross-cloud pillars (operational excellence, security, reliability, performance efficiency, cost
  optimization; sustainability where tracked), naming which pillar each finding serves; a
  one-pillar-only audit is the gap. No pinned pillar counts.
- **FinOps** in `performance-db-cost.md` — cost as a continuous inform → optimize → operate
  practice; a bill with no allocation/owner/anomaly-alert is a finding, and a cost tool bought
  before allocation just visualizes an unattributed bill.
- **Chaos engineering** in `release-engineering.md` — resilience is exercised, not asserted: a
  steady-state hypothesis + blast-radius-limited fault injection; a DR/failover/rollback path never
  run is `unverified`.

Frameworks named **by-name** (three ledger rows added to `docs/standards-index.md`, no URL / version
/ pillar-counts). One new eval (125 total).

## [1.121.0] — 2026-09-18

Wave 42 of the dogfooding batch: #278 — data contracts + the train/serve seam.

### Added — deep-code-review
- **`data-quality.md` §12 — data contracts & the train/serve seam** (#278). A data contract is the
  declared, versioned producer-to-consumer agreement covering schema + quality/SLA + **semantics/
  units** + owner (the data-plane sibling of `api-contracts.md`'s consumer-driven contract —
  cross-linked, not restated); a producer semantic change that breaks a declared consumer is a
  breaking change even when the row still parses (cents -> dollars passes every type check). Plus
  training/serving skew: one shared feature definition + a point-in-time / as-of join so a feature
  never uses data unavailable at prediction time. Tools named by-name (Great Expectations / dbt); no
  spec or version pinned. One new eval (124 total) + red flags.

## [1.120.0] — 2026-09-18

Wave 41 of the dogfooding batch: #282 — experiment rigor + product-led growth in `growth-analytics` (an independent-line overlay; the dcr/agentic-delivery/idea-critic trio bumps to 1.120.0 with the CHANGELOG per the lockstep coupling, no dcr content change).

### Added — growth-analytics (→ 1.1.0)
- **Experiment rigor — pre-commit the design, no peeking** (#282). A method sub-section + a DoD
  item + an anti-rationalization row: peeking (stopping the moment p < 0.05) inflates the
  false-positive rate above the nominal 5%; require a pre-committed sample size/duration read
  **once**, or a sequential design with a valid stopping rule; pre-declare a **primary + guardrail**
  metric; CUPED variance reduction where a pre-period exists; a day-2 read of a 14-day test is
  `UNVERIFIED`. Product-led growth: the activation path is the experiment surface, same rigor.
  Frameworks named **by-name** (no version/figure pinned). One new eval (growth-analytics 4 → 5).

## [1.119.0] — 2026-09-18

Wave 40 of the dogfooding batch: #301 — bind the existing release-age-cooldown guidance with an eval.

### Added — deep-code-review
- **Eval for the release-age cooldown** (#301). The cooldown guidance already shipped in
  `dependency-currency-and-upgrades.md` (a 7-day release-age window; Renovate `minimumReleaseAge` /
  Dependabot / pnpm-npm equivalents; security-advisory updates exempt; the no-cooldown red flag).
  This wave adds the acceptance eval that binds it: a routine bump auto-merged hours after publish is
  a finding (missing cooldown, A03 supply-chain), while a security-advisory patch is exempt and
  fast-tracks. No new guidance — the eval closes the #301 acceptance. One new eval (123 total).

## [1.118.0] — 2026-09-18

Wave 39 of the dogfooding batch: #300 — measure pipeline flow before adopting a platform or a second methodology.

### Added — deep-code-review
- **`release-engineering.md` — "Measure the flow before adopting a platform or a second
  methodology"** (#300). Placed beside the existing DORA section (domain K, not observability): the
  DORA metrics say whether the pipeline is healthy; a cheaper set of **iteration signals**
  (time-to-green, queue/runner wait, rerun/flake rate — explicitly **not** DORA metrics) says where
  the loop hurts. Before buying a build/merge platform or adopting a **second delivery
  methodology**, measure both on a p50/p95 basis, attribute the p95 to a stage, take the cheap fix
  first. Adoption bar: *which measured metric does it move, and by how much?* — no number, no
  adoption (route the spend to the owner with the measurement). **One delivery methodology per
  repo** (a measured bottleneck justifies switching, never running both). One new eval (122 total).

## [1.117.0] — 2026-09-18

Wave 38 of the dogfooding batch: #299 — modularize before splitting the repo.

### Added — deep-code-review
- **`infra-evolution-by-stage.md` — internal-package rung before a repo split** (#299). A new trigger
  row plus a short prose note: carve an **internal package** (a named import boundary) inside the one repo first —
  cheap and reversible; split to a **separate repo** only when a part has an independent change
  cadence AND distinct external consumers AND its own release + ownership. Co-evolving artifacts
  (schema ↔ validator ↔ types ↔ docs) stay **co-located** or they drift across repos (domain H); a
  repo split is org/deploy structure, not a substitute for the module boundary. "modular monolith"
  added to the by-name standards list. One new eval (121 total).

## [1.116.0] — 2026-09-18

Wave 37 of the dogfooding batch: #296 — one canonical path→gate manifest across CI, hooks, and the local suite.

### Added — deep-code-review
- **`parallel-audit.md` §6 — one canonical path→gate manifest** (#296). When more than one surface
  routes gates by path (CI `paths:` filters, a hook's file scoping, the local suite's directory→
  suite map), the parallel hand-maintained copies **drift** — a path gated in CI but not the hook
  silently skips its gate on one surface. Keep the glob→gate-set map in **one** version-controlled
  manifest that every surface **derives** from, with a **CI drift-gate** that fails when any
  surface's routing no longer matches it (the no-duplication rule applied to gate routing). An
  unrecognized path resolves to the full gate set (fail closed, already in §6), never to no gate.
  One new eval (120 total) and a §6 signal.

## [1.115.0] — 2026-09-18

Wave 36 of the dogfooding batch: #295 — quarantine the untrusted reader from the privileged actor.

### Added — deep-code-review
- **`security-ai-agents.md` — "Quarantine the reader from the actor"** (#295). The existing
  agent-security controls (spotlight, schema-validate, least-privilege) all live inside **one**
  identity that both ingests untrusted content (tool/MCP output, fetched pages, another agent's
  message) and holds the privileges to act — a confused deputy. The architectural control is a
  **two-role split**: a reader with no credentials/write/egress that emits only structured,
  schema-validated **data operands** (never the action), and a privileged actor whose action is
  fixed by the trusted task plan (plus an action allowlist) and that takes the reader's value
  **only as an operand**. An injection then corrupts at most an operand, not the action — a schema
  validates shape, not authority. For MCP: trust the transport, not the payload. Reviewed as an
  architecture question a per-file diff cannot answer. One new eval (119 total).

## [1.114.0] — 2026-09-18

Wave 35 of the dogfooding batch: #302 — prefer consumer-contract assertions over giant golden snapshots.

### Changed — deep-code-review
- **`api-contracts.md` — contract assertions over a whole-payload golden dump** (#302). The
  Contract-tests section no longer endorses a bare "golden request/response set" for a
  cross-boundary payload: assert the fields/types/constraints a **consumer** depends on, so a
  backward-compatible additive change passes and only a real incompatibility fails. A
  whole-response snapshot fails on every change alike (can't tell a break from a reorder) and
  trains an `--update-snapshots` re-record reflex that rubber-stamps the next real break; golden
  fixtures are reserved for small stable identities (cross-ref `testing-and-evals.md`). One new
  eval (118 total) and a red flag.

## [1.113.0] — 2026-09-18

Wave 34 of the dogfooding batch: #294 + #298 — the evidence tier of a merge gate.

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — "Self-reported evidence is not a trusted control; a local
  hook is advisory"** (#294, #298). A merge decision rests on a forge run verified on the exact
  reviewed SHA; a local hook, a `Tests: N/N` line, and a checked PR-template box are
  self-reported and `--no-verify`-bypassable — never logged as a green control. And under a
  worktree, an inherited absolute `core.hooksPath` or a pre-push hook that diffs a hardcoded
  default branch gates the wrong tree/range (a pre-push hook's real range is the pushed refs on
  stdin). One new eval (117 total) and two red flags.

## [1.112.0] — 2026-09-18

Wave 33 of the dogfooding batch: #297 — terminate work you own without collateral kills.

### Added — deep-code-review
- **`concurrency-shared-state.md` — "Terminating work you own"** (#297). Load-shedding or
  aborting a lane must kill the processes it **owns** (an owned process group / job object,
  terminated by pgid) — never a name/command pattern like `pkill -f` / `killall`, which reaps a
  sibling lane's identically-named process, a shared dev server, or the orchestrator itself
  (collateral damage invisible in any diff). Covers graceful escalation (SIGTERM → grace →
  SIGKILL), killing-then-reaping orphaned children, and a teardown record that leaves the lane
  recoverable. The shedding *trigger* stays in the `agentic-delivery` overlay; this is the
  *mechanism*. One new eval (116 total) and matching red-flag clauses.

## [1.111.0] — 2026-09-18

Wave 32 of the dogfooding batch: #303 — harden the Wave-30 frontmatter gate (enumeration check
#6) to fail closed, closing the fail-open it shipped with.

### Changed
- **`ci-gates.sh` enumeration check #6 now fails closed** (#303). A skill dir must carry **both**
  a SKILL.md and a VERSION — a SKILL.md with no VERSION (or the reverse) now fails and names the
  skill, where before it was silently skipped (a fail-open in a gate whose contract is
  fail-closed). The stamp is read as **metadata.version**, anchored to the frontmatter
  `metadata:` block, so a `version:` in a description block-scalar or the body can no longer
  satisfy it; and an absent stamp, an unparseable stamp, and a drifted stamp are now reported
  distinctly. Two new planted-RED self-tests (missing VERSION; a nested sub-key decoy that must
  not mask a drift) plus a metadata-anchor regression test; the pre-existing missing-stamp
  planted-RED reworded to metadata.version; 72 gate tests.

## [1.110.0] — 2026-09-17

Wave 31 of the dogfooding batch: #271 behavioral-hotspot prioritization for domain H — a
review that leads with the debt that actually costs the team, not every structural smell.

### Added — deep-code-review
- **`domain-checklists.md` domain H — prioritize maintainability debt by team behavior**
  (#271). A ranking lens: order the domain-H findings by change-frequency × complexity (a
  "hotspot") computed from the target's own git history, so the review leads with the debt in
  the files the team keeps touching. It is a ranking lens, **not a severity bump** — a
  structurally ugly file with near-zero churn stays low, and the severity gate still rules each
  finding on its own merits. Distinct from Phase-0 blast-radius (which ranks the *audit scope*
  across all domains). Where git history is absent (shallow clone, fresh import), it falls back
  to complexity alone rather than inventing a churn number. One new eval (115 total).

## [1.109.0] — 2026-09-17

Wave 30 of the dogfooding batch: two process-hardening lessons mined from this session's own
near-misses, filed as #290 and #291 — the recurring-miss fix the skill preaches (pair a rule
with a gate; catch the class the mechanical gates miss).

### Added
- **CI gate: each SKILL.md `metadata.version` must equal its own `VERSION`** (#290). A sixth
  per-skill check inside `ci-gates.sh enumeration` (already run in CI) fails when any skill's
  frontmatter version stamp drifts from its sibling `VERSION`, and names the skill. Nothing
  reads that stamp at runtime, so the drift was invisible to every other gate — it slid on the
  three lockstep skills for seven releases (v1.101.0–v1.107.0) before the #272 fix. Exact match against each skill's
  *own* VERSION, so independent-line skills are checked correctly with no false-positive
  surface. Two planted-RED self-tests (a drift and a missing stamp); 69 gate tests.
- **`method.md` count-invariant for a claimed add/remove** (#291). Under the intent-conformance
  lens (Phase 2), a diff that *claims to add* an item is falsified by an unchanged item count:
  a delta of zero on an add means the new text was spliced into an existing item and silently
  replaced it (two items fused into one). The fusion keeps every byte valid, so lint, format,
  and checksums pass over it — only the count delta or a human read catches the lost item. This
  wave's own Wave 29 near-miss is the worked example. One new eval (114 total).

## [1.108.0] — 2026-09-17

Wave 29 of the dogfooding batch: #268 review-calibration (an anti-slop lens) + #272, the
SKILL.md frontmatter version drift (a real housekeeping bug — the three lockstep skills'
frontmatter had been stuck at 1.100.0 since it stopped moving with the bump).

### Added — deep-code-review
- **`method.md` anti-slop — a review-calibration record suppresses settled nits, never
  security/logic** (#268). A settled style/preference nit the team has already declined — kept
  in a committed, path-scoped review-calibration record (in git, not a hosted memory service) —
  is dropped so the review doesn't re-raise what the owner already dismissed. The record
  **never** suppresses a security, logic, null-deref, or data-validation/data-loss finding;
  calibration silences preference noise, not correctness or safety. One new eval (113 total).

### Fixed
- **SKILL.md frontmatter version drift** (#272). The three lockstep skills' `metadata.version`
  frontmatter had lagged the authoritative `VERSION` file since 1.100.0; bumped to match
  (1.108.0) in all three. A CI gate that fails on `metadata.version` ≠ `VERSION`, so the drift
  can't recur silently, is filed as #290.

## [1.107.0] — 2026-09-17

Wave 28 of the dogfooding batch: three owner-filed CI-diagnosis hygiene lessons (#285, #286,
#287), all into `branch-and-merge-hygiene.md`'s required-check section (extending the #262/#194
SKIPPED and trigger-event content).

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — CI-diagnosis hygiene: a SKIPPED check, a stale base, a hung
  shard** (#285, #286, #287). **#285**: read the workflow `on:` block FIRST and name the right key — for PRs
  *targeting* an integration branch, a required check that never runs is governed by
  `on.pull_request.branches` (the base-branch filter), not `on.push.branches`; absent = a
  structural no-run/Pending block, diagnosed before the cost-gate / flake hypotheses
  (`on.push.branches` only stamps the branch's own HEAD green post-merge, not the open PRs). **#286**:
  a gate diffing against `origin/main` (not the PR base) fails the *whole queue* when the
  integration branch drifts — check the stale base (`git log HEAD..origin/main`) before triaging
  N same-gate failures; sync on each additive `main` merge; a new gate documents its baseline.
  **#287**: a long `in_progress` shard is diagnosed by its log (hang vs timeout), not by waiting
  or rerun-storming; rerun at most once, on evidence. Two new evals (112 total).

## [1.106.0] — 2026-09-17

Wave 27 of the dogfooding batch: two review lenses (round-1 remainder, no provenance risk) —
#269 intent-conformance and #270 the proven-impact bar for the chronically-noisy security
classes.

### Added — deep-code-review
- **`method.md` Phase 2 — intent-conformance is a lens distinct from correctness** (#269).
  Besides "is the code right," ask "does the change do what it *claimed*" — does the diff
  satisfy its PR description / linked issue / stated acceptance criteria? A flawless
  implementation that does X while the ticket asked for Y, or silently drops a stated
  requirement, is a finding cited to the stated intent; where none is stated, say so rather
  than infer. The review-side counterpart to the delivery spec gate (`agentic-delivery` G1).
- **`method.md` anti-slop — a proven-impact bar for the chronically-noisy security classes**
  (#270). The general noise-floor was already the anti-slop rule; this adds that a finding in
  a suspicion-prone class (DoS, rate-limiting, resource-exhaustion, generic input-validation
  with no reached sink, open-redirect) with no demonstrated impact path is held `unverified`
  or dropped to Nit, never posted as a High on suspicion (mechanism-unproven applied to the
  classes that most produce false alarms; a proven path re-promotes). Secrets / authz /
  data-loss keep their severity. Two new evals (110 total).

## [1.105.0] — 2026-09-17

Wave 26 of the dogfooding batch: #280, the ARIA APG per-widget-contract lens — the one
genuine residue of the round-2 a11y gap. Verify-against-repo collapsed the rest:
first-rule-of-ARIA, target-size 24×24 with exceptions, keyboard operability, and the
widget-role grep were already present.

### Added — deep-code-review
- **`frontend-a11y.md` — a custom interactive widget is built to its ARIA APG pattern**
  (#280). Generic keyboard operability was already covered; this adds the per-widget
  contract: each widget class (dialog, tablist, combobox, listbox, menu, disclosure, slider,
  tree) has a prescribed role + states + a **full keyboard map** (dialog: `Esc` + focus trap;
  tablist: `Arrow`/`Home`/`End`; combobox: `Arrow`+`Enter`+`Esc`), so "Tab reaches it" is not
  "operable" — a custom `role="tablist"` with no arrow-key navigation, a `role="dialog"` with
  no `Esc`, or a control whose `aria-expanded`/`aria-selected` doesn't reflect state, is a
  finding. The native-element-first rule still holds; the APG applies only to hand-built
  widgets. One new eval (108 total).

## [1.104.0] — 2026-09-17

Wave 25 of the dogfooding batch: #275, a threat-modeling method lens — the highest round-2
gap after an idea-critic pass revised the sequence (ship #275 as a coverage lens now, the
#267 precision/recall instrument next, #276 AI-governance deprioritized as the lowest
review-action-density and the most date-sensitive).

### Added — deep-code-review
- **`security-appsec.md` A06 + `security-ai-agents.md` — name the threat-modeling method,
  check coverage not ceremony** (#275). A06 already asks "is there a threat model?"; this
  names *which method fits* — STRIDE (per element), PASTA (business impact), attack trees (one
  attacker goal), **LINDDUN** (privacy, the `privacy-by-design.md` counterpart), **MAESTRO**
  (agentic AI, the modeling method behind the OWASP ASI / MITRE ATLAS catalogs in
  `security-ai-agents.md`) — and adds the coverage lens: a change that introduces a trust
  boundary, principal, or state transition the existing model never considered is a finding
  (the model went stale relative to the diff), and an agentic surface with no agent-specific
  model is the common miss. Maturity frames (NIST SSDF, OWASP SAMM, BSIMM) measure the org's
  program — named, not scored. One new eval (107 total).

## [1.103.0] — 2026-09-17

Wave 24 of the dogfooding batch: two of the three HIGH gaps from the 2026-09-17
competitive-landscape research (#265, #266). #267 (a precision/recall detection-eval
instrument) is deliberately **held for its own wave** — an instrument never run is a
specification, not an instrument (principle 2) — and will ship against a corpus built from
this repo's own history (see the #267 scoping note).

### Added — deep-code-review
- **`security-appsec.md` — deterministic corroboration: an LLM claim rides on a proof it
  cannot generate** (#265). Names the code-level SAST/quality engines the field runs (Semgrep,
  CodeQL / code-scanning, SonarQube, Snyk, plus `bandit`/`ruff`/`mypy`/`hadolint`) as canonical
  instruments, `SARIF 2.1.0` / `OSV JSON` as the ingestion format, and the proof↔claim map: a
  taint/data-flow path confirms "input reaches this sink"; a verified-live secret confirms
  "this secret is real"; an exact version↔CVE match confirms "this version is vulnerable";
  reachability turns "you depend on X" into "you execute X's vulnerable path". Running scanners
  (Phase 1) and re-verifying findings (`parallel-audit.md` §4–5) already existed; this adds, for
  a class a deterministic engine can *prove*, corroborate-against-the-proof-or-mark-`unverified`
  — completing the "multi-signal corroboration" principle on the security side.
- **`docs-and-dx.md` / `method.md` Phase 6 — imprint a review-scoped rules block** (#266).
  Beyond the all-tasks `AGENTS.md`, the imprint can carry a review-only surface first-party
  reviewers read: a `## Code Review Rules` section (OpenAI Codex reads exactly that) and/or a
  root `REVIEW.md` (Anthropic's managed Code Review reads it), with the Perun-severity ⇄
  🔴 Important / 🟡 Nit / 🟣 Pre-existing mapping. States the surface split — the managed
  reviewer reads `REVIEW.md`, the local `/code-review` reads `CLAUDE.md` only — so an imprinted
  repo drives a Perun pass and the bots consistently. Content into the existing
  idempotent-additive imprint mechanism. Two new evals (106 total).

## [1.102.0] — 2026-09-17

Wave 23 of the dogfooding batch: four coordination- and review-honesty lenses (#258, #259,
#260, #262). #261 was closed as already covered by the shipped cadence (#253) and ask-ledger
(#257) rules; #262 landed as a review lens, not a repo CI fix (its evidence was a downstream
project's workflow, absent here).

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — a local preflight stricter than the forge's own verdict is
  a deadlock** (#262). When the forge reports a cost-gated job `skipped/Success` (green under
  branch protection) but a locally-added merge preflight refuses that verdict on an
  app-touching PR, and the only unblock is an owner-only label or a manual dispatch, an agent
  is deadlocked — a gate stricter than the standard it enforces (the gate-vs-standard rule,
  here applied to CI). The preflight must diagnose *policy-declined* (cost gate: work exists, a
  human must grant the run) vs *nothing-to-run* (path filter: no in-scope change) and name the
  owner action, not refuse blindly.
- **`method.md` — a pattern-bug is scoped by grepping the idiom, not the first callsite**
  (#259). A Phase 4 finding that matches a copyable idiom (a guard expression, a state-check, a
  pasted data-flow pattern) is scoped by grepping the idiom across the tree in the same pass:
  the search result is the blast radius, reported as one class-finding with its full instance
  set, never the first callsite alone. The review analogue of the one-component-per-concept
  duplicate-twin sweep, for a bug pattern rather than a duplicated component. Two new evals
  (104 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — a process-policy change is not a mid-task interrupt** (#258).
  Extends the interrupt rule: re-ordering the queue, switching serial↔parallel, or reshuffling
  priority queues to the lane's next checkpoint (a filed issue, a pushed commit, a merged PR),
  never mid-edit or mid-compose — each mid-task redirect makes the lane re-orient and ship
  nothing (the interrupt-thrash anti-pattern). The only mid-task interrupt is P0 safety.
- **`fast-agentic-delivery.md` — progress is a durable artifact, not a spawned lane** (#260).
  A lane computing locally with nothing pushed is not-started (`spawned` ≠ `started`, the
  claim-side form of the existing `assigned` ≠ `in-progress`). Grade each lane zero / in-flight
  / done by its durable output; a status names each lane's push / PR / issue URL; the window's
  ETA is projected from the durable-output rate, not the spawn rate.
- **`fast-agentic-delivery.md` — pointer** (#259): two lanes reporting the same bug idiom is a
  missed sweep, not two findings; the review-side rule lives once in `method.md`. Two new evals
  (29 total).

## [1.101.0] — 2026-09-17

Wave 22 of the dogfooding batch: a control disabled only until client state hydrates is
*loading*, not dead (#256); and a long unattended session answers "what's left" from a
durable, ask-indexed ledger, not by re-reading the transcript (#257).

### Added — deep-code-review
- **`product-ux-quality.md` — a control disabled only until client state resolves is
  *loading*, not disabled** (#256). A write control gated on client-only state
  (`useAuth`/`useSession`, a hydration flag) is server-rendered in its `disabled` default and
  looks like a permanent dead control for the SSR → hydration window, but it is in the
  **loading** data state and must *look* loading (skeleton/spinner) — distinct from the
  contextually-unavailable control that stays disabled and owes an explanation. Optimistic-
  enabled is allowed only when the click is captured and replayed after hydration (never a
  dropped no-op, which is the dead-control trust defect). The static `disabled={!session}`
  tell is an `unverified` lead confirmed only by a pre-hydration render — a fourth gate-1
  timing class, and could-not-check fails open. Adds an interaction-completeness bullet, a
  pre-ship checklist item, a gate-1 inspection detector, the timing-class extension, and the
  **pre-hydration capture primitive** its detector cites (a real server-HTML / JS-disabled /
  throttled snapshot procedure in `testing-and-evals.md`, so the gate has a routed positive
  control and is not a citation to an absent instrument). One new eval (102 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — index the backlog by the owner's ask, and read it to answer
  "what's left"** (#257). Extends the unattended-work-loop rule: the durable backlog the loop
  already keeps must also carry the **ask-set** (one row per owner request: id, ask, status,
  evidence, next action), updated at each milestone; "what's remaining" is answered by reading
  that ledger in one or two tool calls, never by an O(N) transcript re-scan that re-litigates
  settled items. A row is done only on the canonical surface (a merged-to-default SHA or a
  live URL), not a branch that merely contains the fix — `project-state.md`'s receipt
  discipline, not restated. Distinct from the review-side end-of-session claim audit
  (`method.md`, #244) and the feedback-coverage map (`roles.md`). One new eval (27 total).

## [1.100.0] — 2026-09-17

Wave 21 of the dogfooding batch: a coordinator's throughput follows its own cadence and the
resource ceiling, not the owner's message frequency (#253).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — the owner's message cadence is not the loop's clock**
  (#253). Extends the unattended-work-loop rule (which already owns the durable backlog and
  pull-the-next-item discipline): a coordinator that refills a lane only when a new owner
  message grants a turn has made human message frequency an accidental concurrency
  controller — throughput sags when the owner goes quiet while safe capacity sits idle. A
  completed lane refills on the coordinator's own cadence; a quiet stretch never lowers
  target concurrency; admission stays governed by the fan-out gates (disjoint surfaces, free
  RAM + swap trend, one-lane-then-re-probe with a burst reserve), never by message count,
  and the target is a maintained concurrency with backpressure, never unbounded spawning.
  Also sharpens the ownership-map rule with the converse over-caution: a shared artifact in
  flight blocks only the lanes that touch it — disjoint-surface lanes proceed. One new eval
  (26 total).

## [1.99.0] — 2026-09-17

Wave 20 of the dogfooding batch: a verification claim names the procedure that produced
it, and a heavy verification run certifies only a frozen, quiescent head (#250, #251, #252).

### Added — deep-code-review
- **`report-format.md` — name the procedure, not just the surface** (#250, #252). A
  verification surface includes the experiment that produced the result: a UI-behaviour
  claim names its interaction method (native keyboard / pointer / scripted DOM call / AT
  command) and exact viewport (+ route/state/sha); an absence claim names its search space
  and runtime confirmation. Two results contradict only when method and viewport match —
  otherwise they are method-sensitive, reconciled one variable at a time, not by picking a
  winner.
- **`method.md` — presence and absence are not the same claim** (#250). An absence finding
  is unfalsifiable from the report (it inherits the searcher's vocabulary), and under
  parallel delivery it is read as a work order — a false absence builds a second, competing
  implementation. Absence is held higher: search by behaviour across every encoding, confirm
  at runtime (principle 2; else `unverified`/unconfirmed-absent, not a gap), a downstream
  builder re-confirms before building, and a disproven absence is reported back. The shared
  surface rule lives once in `report-format.md`; this adds the asymmetry and links to it. Two
  new evals (101 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — release verification runs on a frozen, quiescent head**
  (#251). Release verification (certify one frozen head, once, after integration closes, with
  the machine to itself) is a different contract from defect discovery (continuous, any recent
  head, findings durable when stale) — the same commands run for different purposes. Gate
  release verification on quiescence; freeze and name the SHA (a verdict against a moved head
  is STALE, not pass/fail); give the heavy run the machine; split it so partial progress
  survives; keep discovery findings, discard a discovery verdict. Composes with #247 on a
  different axis. One new eval (25 total).

## [1.98.0] — 2026-09-17

Wave 19 of the dogfooding batch: a rewritten browser spec owes its retired coverage a
structural fallback, and a worktree assignment is a path an integrator can detach onto
(#246, #247).

### Added — deep-code-review
- **`testing-and-evals.md` — a rewritten browser spec names its retired coverage and
  pins the wiring it can no longer reach** (#246). When a redesign makes a spec's target
  surface structurally unreachable in the test environment (a surface that now renders
  only user-submitted content while the test store is intentionally empty) and the spec
  is rewritten against another surface, the dropped coverage must be named as a gap
  (principle 2: an unrecorded absence reads as coverage) and pinned by a source-level
  structural gate — a unit assertion that the wiring still exists. That fallback is
  weaker than the browser scenario it replaces (it proves the component is referenced,
  not that the interaction works) and is never a substitute. A Phase-2 trigger in
  `method.md` routes to it. One new eval (99 total).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — a worktree assignment is a path, not an adjective; an
  integrator on a shared branch detaches** (#247). "An isolated worktree off `<branch>`"
  is ambiguous — lanes reuse the same checkout and collide on the tree, not on files.
  The brief names the exact path each lane owns and writes only under; an integrator
  folding into a shared branch uses a detached worktree (`git worktree add --detach
  origin/<branch>`), which escapes git's "already checked out" refusal and cannot be
  squatted; a lane verifies tree ownership (`git status --short`) before its first write;
  a gate failing on an untouched file is an environment fault (the collision twin of the
  unowned-file-gate rule above), not a code bug; and another lane's uncommitted work is
  never stashed. One new eval (24 total).

## [1.97.0] — 2026-09-17

Wave 18 of the dogfooding batch: an unattended window is a work loop, a delivery
reconciles its claims against the artifact, and research is not delivery
(#243, #244, #245).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — an unattended time budget is a work loop, not a
  single task** (#243). A granted window is worked until a termination condition fires
  (backlog empty / every remaining item blocked / a resource ceiling), each stated with
  its evidence; the standing backlog lives in a file the loop re-reads, a milestone is a
  cue to pull the next item (an owner stop/redirect is the separate control signal), and
  an idle loop names the condition it is parked on rather than going silent. Extends the
  queue-a-requirement-to-a-file rule to the standing backlog.
- **`fast-agentic-delivery.md` — research is not delivery** (#245). A brief earns its
  cost only when its conclusions become tracked work — each recommendation an
  issue/backlog row/recorded rejection opened in the same step, commissioned with a
  named downstream consumer, reported as consumption not production, with a
  depth-distribution check so the expensive recommendations aren't the ones that
  evaporate. References #235's landed-artifact status rule. One new agentic-delivery
  eval (23 total).

### Added — deep-code-review
- **`method.md` — reconcile the report's claims against the delivered artifact** (#244).
  A Phase 5 sibling to the coverage-ledger reconciliation: enumerate the report's own
  claims and join each to the committed diff (a hunk, a test, a file), reporting
  present/partial/absent including your own misses, trusting the diff over any lane's
  report of what it did, run unprompted before close — an audit that only fires after
  the owner asks "did you actually do all of it?" is a retrofit, not a control. The
  set-completeness question that precedes per-claim verification. One new
  deep-code-review eval (98 total).

## [1.96.0] — 2026-09-16

Wave 17 of the dogfooding batch: the admission schedule leaves a reserve, and a
disabled action explains itself (#239, #240).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — leave a safety reserve when admitting lanes**
  (#239). Sharpens the one-lane-at-a-time admission rule: never fill to 100% of
  observed headroom — leave a reserve so a later spiky lane (a browser gate, a
  dependency install, a test runner) still fits, since observed headroom is
  average-case and the lane that lands the burst is not.

### Added — deep-code-review
- **`product-ux-quality.md` — a disabled action explains its cause and recovery
  path** (#240). Beyond looking disabled (gate 1) and reacting consistently (#230): a
  contextually unavailable action names the unmet prerequisite and a concrete next
  step, in reachable text (nearby or a focusable wrapper/popover — a native `disabled`
  element may get no hover/focus events, so its own tooltip is unreachable); a
  permanently role-unavailable action is hidden or replaced, not a dead end. A
  Pre-ship line and an eval (97 total).

## [1.95.0] — 2026-09-16

Wave 16 of the dogfooding batch: resource-aware fan-out and lane discipline — an
orchestrator that scales a write fan-out by lane count burns hours of spend while the
integration head never moves (#235, #236, #237, #238). All in agentic-delivery.

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — cap in-flight write lanes by landed artifacts**
  (#235). Lane progress is a durable artifact (pushed branch / PR / committed diff),
  never a running transcript; status is "M landed, K in flight, head at `<sha>`", not
  "N lanes running"; admission is earned by completion (a WIP limit, a delivery-ratio
  drain), not by machine headroom.
- **`fast-agentic-delivery.md` — gate a fan-out on the swap trend, not a free-RAM
  reading** (#237). Sharpens the existing swap section: free-RAM% fails open under
  thrash (a post-mitigation number, healthiest under worst load), so sample swap twice
  for direction, let free RAM corroborate a stop but never authorize a spawn, add free
  disk and live-lane count to the probe, and treat a collapse in work rate as the
  resource signal.
- **`fast-agentic-delivery.md` — a worktree is a resource with a lifecycle** (#236).
  Teardown is part of the lane contract; the orchestrator owns garbage collection, but
  GC is advisory and approval-gated (proposes removals, refuses uncommitted-work
  candidates), never an autonomous destructive sweep; free disk and worktree count are
  ceilings the spawn probe enforces.
- **`fast-agentic-delivery.md` — queue new requirements to a file, don't interrupt a
  running lane** (#238). Extends the acknowledge-the-burst rule: new scope goes to a
  durable file the lane polls at its checkpoints; interrupts are reserved for
  stop/redirect; scope is frozen per deliverable; repeated re-briefs mean split the
  lane, not send a third.

Two new agentic-delivery evals (22 total). Lockstep bump to 1.95.0.

## [1.94.0] — 2026-09-16

Wave 15 of the dogfooding batch: an export / print / share-image feature is a second
render surface, produced by a different code path than the screen and never inspected
— so the artifact a user downloads clips content, drops the axes/legend that lived
only in interactive chrome, ignores the theme, or exports a blank image (#232).

### Added — deep-code-review
- **`product-ux-quality.md` — export / print / share is a second render surface**
  (#232). Enumerate every download/print/copy-as-image path (`toDataURL`/canvas, SVG
  serialisation, `@media print`) and inspect the produced artifact like a route: no
  clip of off-viewport content, axis/legend/labels baked in (an interactive-only
  readout needs a static equivalent), theme honored or normalised, self-describing,
  and every data state exported honestly. Folded into the rendered route sweep (#227)
  as "also render every export path"; a distinct axis from the production-build repro
  rule. One Pre-ship line and one eval (96 total).

## [1.93.0] — 2026-09-16

Wave 14 of the dogfooding batch: assembled-product visual review — the domain-P rules
for a single screen existed, but no phase applied them across every route, so a class
of defect spanning many surfaces reached the owner after a green gate (#227, #228,
#229, #230, #231). Each addition references existing domain-P canon rather than
restating it.

### Added — deep-code-review
- **`method.md` Phase 2 + `product-ux-quality.md` — rendered route sweep** (#227). A
  FULL-review step that enumerates every route (router tree AND nav manifest — a
  mismatch is a finding) and rules the domain-P checklist on each across a matrix
  (`{~390, ~1440} × {light, dark} × {top, mid-scroll}` + state transitions), reporting
  coverage as a ledger (a route not rendered is `unverified`, not clean; a clean
  finding doesn't generalise past the routes rendered). The domain-P analogue of the
  anonymous-GET sweep; the matrix is defined here and referenced elsewhere.
- **`product-ux-quality.md` — data visualization** (#228). A chart must answer a
  question legibly: a value axis or direct labels, a keyboard-reachable value+date
  readout, real samples marked with no trend implied across sparse points, and
  non-visual access to the numbers. A heuristic chart-anatomy check folds into the
  enforcing gate's fail-open self-test.
- **`product-ux-quality.md` — layout invariants** (#229). Extends gate 1's inspection
  list with sticky-chrome collision, gutters, optional-slot reservation,
  no-reflow-on-state-change, and tabular numerals — checked mid-scroll and on state
  transitions (the route sweep's matrix), reusing gate 1's geometry primitives.
- **`product-ux-quality.md` — interaction consistency** (#230). Beyond completeness:
  per-class hover/active/focus parity, every hover affordance also reachable by
  keyboard and touch, and tooltips that add information — the divergent-styling defect
  the one-component-per-concept grep can't see.
- **`product-ux-quality.md` — space efficiency** (#231). Footprint tracks information:
  an empty record must not occupy a populated record's footprint, and a grid has a
  density target at the wide viewport — the space-appropriateness complement of the
  honest-empty-state rule.
- **`evals/evals.json`** — four evals (95 total): route-sweep-vs-single-shot,
  mid-scroll layout invariants, interaction-consistency-vs-completeness, sparse-trend.

## [1.92.0] — 2026-09-16

Wave 13 of the dogfooding batch: merge-train and PR-integration hygiene — landing
several PRs safely without dropping or reverting work (#220, #221, #222, #223, #224).
Five lessons, each referencing existing canon (the §5 merge-train mechanism, the
#212 superset-fold sibling) rather than restating it.

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` §5 merge trains — a union/integration PR is verification-only**
  (#220). Its CI aggregates every member's checks, so it is never the critical path:
  don't hold already-green members waiting on union CI, and close the union with a
  pointer rather than squashing or merging it in place of its members.
- **`branch-and-merge-hygiene.md` §5 — red-base discharge** (#224). When the base is
  red and a green-base-required preflight blocks the fixes that would green it,
  discharge the deadlock with a merge train — the union's green discharges the
  "base green at head between merges" wait, and licenses no red member and no
  `--admin` override. References the merge-train mechanism; `release-engineering.md`
  cross-links it.
- **`branch-and-merge-hygiene.md` §5 — a stop halts new work only** (#222). An
  already-green + `MERGEABLE` PR still merges (or is handed off by URL), and an
  unpushed rebase must be pushed or its worktree path + branch + HEAD printed in the
  stop message.
- **`branch-and-merge-hygiene.md` §6 — a subset absorbed at a stale SHA can revert a
  later fix** (#223). B absorbed A's source at an older SHA, so merging B after A
  silently overwrites A's later fix with no conflict; merge the fuller tip first (or
  fold A's missing commits in) and grep the live tree for the fixed symbol. Distinct
  from the generated-artifact superset fold.
- **`branch-and-merge-hygiene.md` §6 — diff two tips before closing a PR as duplicate**
  (#221). Title/branch similarity is not patch equality; **two-dot** `git diff` of
  both heads (`git range-diff` when they forked from different points), fold any
  unique hunk into the survivor, and record the diff in the close comment.
- **`release-engineering.md`** — cross-link to §5's merge trains + red-base discharge;
  the mechanism lives there and this file never restates it.
- **`evals/evals.json`** — three evals (91 total): tip-diff-before-close, stale-SHA
  subset-absorb revert, red-base train discharge.

## [1.91.0] — 2026-09-16

Wave 12c of the dogfooding batch: evidence freshness — reproduce a finding against the
build and SHA it came from, and validate the receipt (#206, #209, #217).

### Added — deep-code-review
- **`method.md` — reproduce a built-artifact finding against the build it audits, not the
  dev server (#206).** The environment axis of reproduction fidelity (sibling of the
  gate's-own-detector and local≠CI rules): a production-build audit finding (a control obscured
  under a sticky header, a WCAG focus-not-obscured failure) often will not appear on the dev
  server — minification, CSS order, hydration, asset paths differ. A dev-server "can't reproduce"
  does not refute it; reproduce against the built artifact or the deployed/preview URL.
- **`method.md` — re-validate a carried-forward finding before repeating it (#217).** A finding
  captured at an earlier `start_sha` is a hypothesis until re-checked: confirm the `file:line`
  still exists at HEAD and re-run the surfacing gate before repeating it. Repeating an
  already-fixed finding is a false positive; reporting a worsened one as unchanged over-claims a
  trust-critical status (rate the claim). A "still open" status holds only at the current SHA.
- **`report-format.md` — the report records its capture SHA (#217).** A `Reviewed at (start_sha)`
  line in the ground-truth block, matching the machine report's field, so a later session knows
  what to re-verify each finding against.
- **`product-ux-quality.md` — the UI receipt must be a valid non-empty image (#209).** A
  proxy/504-wiped screenshot stub passes a bare existence check but proves nothing (existence is
  not content — principle 2); and capture from a clean or separate tree, since a shots script
  that stashes discards the diff under review.
- Two new evals (88 total). Lockstep bump to 1.91.0.

Closes #206, #209, #217.

## [1.90.0] — 2026-09-16

Wave 12b of the dogfooding batch: coordination and stacked-PR hygiene — an ownership map
locks writes, not work; a shared generated artifact needs a superset fold (#210, #212,
#213, #214).

### Added — deep-code-review
- **`branch-and-merge-hygiene.md` — attribute a stacked PR's CI failure to the commit that
  owns it (#210).** A PR stacked on another runs its base's commits too, so a base-introduced
  failure turns the downstream red for nothing. Find which commit the failing step is in
  (`git log <merge-base>..<head>` is the PR's own diff; an ancestor commit is the base PR's
  defect) — attribute it to the base PR and never commit the fix downstream (it double-patches
  once the base merges). Composes with 12a's "a run names the SHA it graded."
- **`branch-and-merge-hygiene.md` — a shared generated artifact needs a superset fold, not two
  independent writes (#212).** The existing regenerate-don't-hand-splice rule fires on a
  conflict; the worse case fires on none — two open PRs each rebuild a derived artifact
  (`out/`, a lockfile, `app/data/`) from a shared source, both merge cleanly, and the second
  silently drops the first's regeneration. Trigger: a PR regenerates an artifact while another
  open PR touches the same source (found via `gh pr list --limit 500`). Fix: rebase onto the
  merged first and rebuild (superset fold).

### Added — agentic-delivery
- **`fast-agentic-delivery.md` — an ownership map blocks a dual *write*, not dual *work* (#213).**
  Sharpens the SKILL.md occupancy rule: a module-ownership map answers who may write where, not
  whether a lane is already building the objective; a forge assignment is intent, not progress
  (`assigned` ≠ `in-progress`). Check for an active lane on the objective, and announce-then-take
  (claim before opening the worktree).
- **`fast-agentic-delivery.md` — a fan-out ETA states its parallelism assumption (#214).** A
  serial ETA on parallel lanes (or the reverse) is off by ~N×; state the parallelism assumption,
  the constraint that caps it, and both parallel/serial numbers when uncertain. A one-number ETA
  with an unstated assumption is unearned precision — prefer a stated appetite (G0).

Two new evals (deep-code-review 86, agentic-delivery 20). Lockstep bump to 1.90.0.

Closes #210, #212, #213, #214.

## [1.89.0] — 2026-09-16

Wave 12a of the dogfooding batch: a gate is only *run* when its enforcing surface can
see the artifact it checks — CI/gate-visibility honesty (#207, #208, #211, #215, #216).

### Added — deep-code-review
- **`method.md` — a skipped gate scope is `unverified`, not clean (#211, #215).** A
  multi-scope gate that skips a scope whose input is absent (a privacy gate whose
  *identifier* scan needs a pattern list and, missing it, runs only the *secret* scan
  yet exits 0) has not cleared the skipped surface. Read which scopes ran, not the bare
  exit code; a green privacy exit with the identifier scope skipped is not "boundary
  clean" — a status claiming it over-claims a **trust-critical** surface (rate the
  *claim* Critical). An instance of principle 2 (a pass is evidence only where the
  enforcing surface could see the artifact), stated once and referenced.
- **`method.md` — a CI re-run certifies the SHA it ran, not the PR head (#207).**
  "Re-run all jobs" re-dispatches the original frozen payload SHA, so a green re-run can
  certify a stale tree; a status names the commit it graded — a green whose SHA is not
  the PR head is `unverified` for the head. The moved-tree twin of the self-certifying
  gate.
- **`method.md` — name *why* local and CI diverge (#216).** Beyond the gate set:
  sharding/worker count (the existing config-vs-baseline rule), OS font metrics (a
  wrap-point differs by host — assert the layout **invariant**, never an absolute width
  or wrap-point, reinforcing the geometry-not-pixels rule in `testing-and-evals.md`),
  and dirty local resolution (a stale cache or symlinked `node_modules` resolves
  different versions than CI's clean `npm ci` — reproduce on a clean install).
- **`branch-and-merge-hygiene.md` — a required check must be *satisfiable* (#208, #207).**
  A required check whose name is not backed by a job that runs and concludes for this PR
  sits pending forever — indistinguishable from a hang, merge-blocked exactly as a
  failure. A path-filtered skip with no status is not green (fix: emit a conclusive
  status for out-of-scope paths, or don't require that job for that PR class); a
  trigger-event gap (labeled-only, or a `workflow_dispatch` run that never attaches to
  the PR rollup) means the workflow exists but the check never runs. A **High**
  merge-blocker config gap in its own right (guardrail 3: intrinsic, not "Blocker
  because CI is red").
- Two new evals (85 total). Lockstep bump to 1.89.0.

Closes #207, #208, #211, #215, #216.

## [1.88.0] — 2026-09-16

Wave 11f of the dogfooding batch: one screen verified is not the product — scope a
parity claim to the correspondence table (#200).

### Added — deep-code-review
- **`migration-parity.md` — the correspondence table is a coverage ledger (#200).** An
  agent that verified one route (a cheap, shell-less changelog page) reported that *the
  product* matched — the other screens never rendered, and did not match. Gate 4's
  correspondence table (`product-ux-quality.md`) is that ledger; the new rule is it
  **exists before any claim** and each row carries its state (`verified` / `unverified`
  / `n-a`). A parity status is **scoped to the verified rows and never phrased over the
  product**; aggregate phrasing ("the app matches," "all pages") is valid only when
  every row is `verified`, else the honest form is `N of M screens verified — remaining:
  …`. An unrendered screen is an unprobed surface (`SKILL.md` principle 2). Sample a
  **chrome-bearing, data-dense** screen first — a static page proves almost nothing about
  the shell.
- **`report-format.md` — verdict cap + coverage line (#200).** Mirroring the
  `Authz posture` cap: the verdict is **capped below Approve** while any in-scope screen
  is `unverified`, and the ground-truth block carries a `Parity coverage: N/M` line.
- **`scripts/validate_status_claims.py` — fourth detector (#200).** Flags a positive
  parity claim carrying a population quantifier (all / every / whole / the app) but no
  N/M coverage fraction; it requires a parity-context word (so "all tests pass" is
  spared) and fires even on a downgraded row.
- **Severity: High, not Blocker.** The issue proposed Blocker; the `SKILL.md` rubric
  reserves Blocker for "won't build/run/test, live data corruption, live exploited vuln"
  and Critical for a monotonic-quality breach that *will* ship wrong data. A parity claim
  generalized past its sample ships neither — it is a serious defect that **blocks unless
  a named owner accepts** (the High band), because it retires the verification task. Rated
  High accordingly.
- One new eval (83 total). Lockstep bump to 1.88.0.

Closes #200.

## [1.87.0] — 2026-09-16

Wave 11e of the dogfooding batch: a screenshot is an artifact, not an inspection (#198),
and prove a layout claim with geometry, not class names (#199).

### Added — deep-code-review
- **`product-ux-quality.md` gate 1 — the screenshot's inspection contract (#198).** A
  screenshot proves a render happened, not that it is correct: "screenshot attached"
  with no cited inspection is `unverified`, not `verified` (the treatment a parity claim
  with no named surface gets). Gate 1 now defines a **pixel-defect checklist** once —
  overlap / clip-truncation / contrast (`frontend-a11y.md`) / disabled-looks-disabled /
  state — that a UI status must cite. `report-format.md` requires the surface **and** the
  inspection for a UI claim.
- **`testing-and-evals.md` — prove a layout claim with geometry, not class names (#199).**
  A class assertion (`toHaveClass`, `toBeVisible`, a snapshot) passes while two elements
  render on top of each other. New section: a rendered **bounding-box non-intersection**
  assertion at each screenshot width (red-before / green-after), with clip
  (`scrollWidth > clientWidth`) and disabled-looks-disabled (computed affordance)
  companions. **Scope discipline:** non-intersection and non-clipping only — never
  absolute pixels / widths (renderer flake). This is the mechanical proof behind gate 1's
  overlap / clip items.
- **`scripts/validate_status_claims.py` — third detector (#198).** Flags a positive UI
  status leaning on a screenshot (`screenshot` / `.png` / `captured`) that names no
  inspection token (overlap / clip / contrast / disabled / bbox / geometry); it fires even
  on a downgraded row, exempting a row that cites what it inspected.
- Two new evals (82 total). Lockstep bump to 1.87.0.

Closes #198, #199.

## [1.86.0] — 2026-09-16

Wave 11d of the dogfooding batch: budget the CI an agent swarm triggers (#195).

### Added — deep-code-review
- **`parallel-audit.md` — budget the CI a fan-out triggers (#195).** A write fan-out
  that opens many small PRs, each re-triggering the full browser/a11y/e2e matrix,
  multiplies shared runner minutes without improving review. New section: prefer one
  reviewable PR per concern; keep draft iteration on a cheap, path-filtered gate and
  reserve the expensive matrices for a `full-ci` label / manual dispatch / the final
  merge gate; cancel superseded runs with a concurrency group keyed by PR/ref; keep a
  documented one-command local full suite and require the labelled full run before
  merging an app change. **Path filters must fail closed** — a filter that skips a gate
  on an unknown path is a gate exclusion (`method.md`), and privacy/security checks are
  never path-filtered out. **State the residual risk** — the cheap gate will not catch
  browser-only regressions until the full run, so an unrun matrix is `unverified`, not a
  pass (principle 2). The wasted-runner-minutes cost is **Medium**, batched as one
  finding (`branch-and-merge-hygiene.md` §7); only the fail-open filter carries higher
  severity.
- One new eval (80 total). Lockstep bump to 1.86.0.

Closes #195.

## [1.85.0] — 2026-09-16

Wave 11c of the dogfooding batch: coordinate a parallel restyle fan-out (#194) — own
the shared shell before spawning page lanes, and flag work built on the wrong
integration base as High.

### Added — deep-code-review
- **`migration-parity.md` — shell-ownership ledger before a restyle fan-out (#194a).**
  When a multi-screen port/restyle fans out to parallel page lanes, the shared shell
  (layout, nav, tokens, chrome primitives) becomes contested write state that a per-PR
  review passes lane-by-lane while the collision lives between them. Before spawning,
  the lead publishes an ownership ledger (same shape as `parallel-audit.md` §1's unit
  manifest, by reference): exactly one lane owns each shared-shell path (a partition),
  and the shell lands first. Spawning with no ledger is a **High** coordination defect;
  a page lane editing a shell path it does not own is a finding even when its diff is
  correct.
- **`branch-and-merge-hygiene.md` — check the base of in-flight work (#194b).** §2 now
  enumerates open branches/PRs and verifies each base against the detected integration
  target (reusing §3's `git rev-list --left-right --count`); §7 rates a large or
  long-lived change built on the **wrong** integration target (two long-lived branches,
  `STAGE` growth/mature) as **High** — above the Medium merge-debt row, because the cost
  compounds per commit on the wrong base — with the retarget/rebase command named.
- Two new evals (79 total). Lockstep bump to 1.85.0.

Closes #194.

## [1.84.0] — 2026-09-16

Wave 11b of the dogfooding batch: name the parity verification surface (#192), and
prove a design delta before acting on it (#196).

### Added — deep-code-review
- **`SKILL.md` / `report-format.md` — name the verification surface (#192).** A
  `VERIFY_SURFACE` first-response field (url-or-port · tree/worktree · branch · sha,
  or `NONE_RUNNING`), required on a web / port / parity task: `TREE_STATE` is where
  you edit, `VERIFY_SURFACE` is what a human would see, and the two are routinely
  different trees. `report-format.md` sharpens the surface rule — when more than one
  tree can serve the app, "the default served state" is whichever process holds the
  port, so a parity claim names the running instance built from the tree under review
  (URL + branch + sha); a parity claim naming no surface is **invalid, not
  downgraded**; and never direct a human to a URL whose served sha you have not just
  confirmed (per #182).
- **`scripts/validate_status_claims.py` — second detector (#192).** Beside the
  hedged-green detector, flags a positive UI/parity status that names no verification
  surface (no URL, no sha). The sha test requires >= 7 hex chars with a digit, so an
  all-letter hex-looking word is not mistaken for a commit.
- **`product-ux-quality.md` — establish a delta before acting on it (#196).** A
  cropped screenshot of one side is a hypothesis, not evidence: render **both sides at
  the same viewport width** and diff the corresponding region; confirm each app-only /
  design-only element's **state** (present-but-collapsed / disabled-by-data /
  in-a-menu) before calling it a delta; and trust the current rendered reference over
  a stale source comment. A delta that does not exist has no bucket (it feeds the #193
  restyle classification).
- Two new evals (77 total). Lockstep bump to 1.84.0.

Closes #192, #196.

## [1.83.0] — 2026-09-16

Wave 11a of the dogfooding batch: reconcile bidirectional parity (#189) with the
preserve-a-feature rule — restyle an app-only feature, don't delete it (#193).

### Changed — deep-code-review
- **`migration-parity.md`** — new *Restyle an app-only feature into the target's
  design language* section resolves the tension between the parity differ's "app-only
  element is a finding" (#189) and the preserve-a-real-extra-feature rule: classify
  each app-only element as **decoration** (→ remove-to-match), **real functionality**
  (→ **restyle into the target's design language**, preserving the capability — the
  affirmative default, not escalate-and-wait), or **owner-approved removal** (a named
  decision). Deleting app-only functionality to reach visual parity **without a named
  owner approval is High** (do-no-harm, principle 4 — blocks unless a named owner
  accepts). Fill an **exception ledger** (element · bucket · verdict · target
  primitive) before a restyle; the review-smell paragraph and 🚩 signals carry the
  severity.
- **`product-ux-quality.md`** — the bidirectional-parity gate's app-only *feature*
  verdict changes from "escalate to the owner" to **restyle into the target's design
  language** (escalation demoted to the fallback when no target primitive fits);
  *Done* and the parity checklist now read every app→design entry **resolved**
  (restyled / decoration-removed / owner-adjudicated), not "empty". Refines #189.
- One new eval; the #189 eval updated to the restyle-default reading (75 total).

Closes #193.

## [1.82.0] — 2026-09-16

Wave 10 of the dogfooding batch: design parity is bidirectional (#189).

### Added — deep-code-review
- **`product-ux-quality.md`** — the parity differ must check **set equality, not
  containment**: run the mismatch list in both directions per screen (design→app AND
  app→design), and don't wave through app-only elements as "intentional extras". The
  operative test for an app-only element is *does removing it lose a user capability?*
  — pure shell (an extra header, a "Showing N of N" line) defaults to
  remove-to-match; a capability-bearing element (a filter bar, view tabs, per-card
  upvote arrows) is a feature that **escalates to the owner** (never self-cut to match
  a look reference — `migration-parity.md`'s preserve-a-real-feature rule). The
  app→design list routes to owner adjudication, not an automatic differ fail. One new
  eval (#189).

Closes #189.

## [1.81.0] — 2026-09-16

Wave 9 of the dogfooding batch: assert the property, not its proxy (#187, #188).

### Added — deep-code-review
- **`frontend-a11y.md`** — guard a deliberately-decorative / sub-AA colour token at
  its point of **use**, not its value: WCAG 1.4.3 holds informational text to 4.5:1,
  so a value-only test that pins the token sub-AA stays green while a component paints
  text with it and fails the audit. Add a use-site guard that fails when the token
  colours a real text node — fail-closed but with a pinned-exempt escape for text
  1.4.3 genuinely exempts (aria-hidden / decorative / logotype / large text), so the
  gate is narrowed to the standard, not stricter than it. General form: assert the
  property a test encodes, not the value it is derived from (#187).
- **`method.md`** — classify a failure by **config** and **baseline** before calling
  it a regression: a failure seen only under a memory-mitigated `--workers=1` serial
  run can be a shared-state harness artifact the parallel CI config never hits.
  Reproduce under CI's actual worker config (config axis) and under the identical
  reduced config on the merge-base (baseline axis) before reporting a code defect
  (#188).
- Two new behavioral evals.

Closes #187, #188.

## [1.80.0] — 2026-09-16

The offline half of the live eval harness (#61) — the split-rubric runner, no live
model call yet.

### Added
- **`scripts/run-evals.py`** — the execution layer over every skill's `evals.json`.
  `--dry-run` (default) enumerates and classifies every eval as **hard** (a
  deterministic `eval_predicates.py` predicate is bound) or **soft** (needs the LLM
  judge), re-runs the hard-axis golden-pair discrimination, and prints a coverage
  report as JSON — no model, no network, no spend. `--selftest` proves the runner's
  guards offline (the decorrelation guard aborts on an equal *or missing* model id;
  the spend-cap guard aborts on a missing/non-positive cap; the live path refuses
  without configuration). Wired into CI as an offline gate.
- The hard/soft split is derived from `eval_predicates.BINDINGS`, so no `evals.json`
  is tagged and no skill version is forced by it.

### Owner-gated (issue #61 stays open)
- The live model call is an explicit un-built stub — this ships no model-calling
  code, so `--live` cannot spend. Filling the model client + per-call spend
  accounting, the scheduled/dispatch workflow (where the key lives), the committed
  results-freshness gate, and the axis tag across all evals remain owner steps.

## [1.79.0] — 2026-09-16

Wave 8 of the dogfooding batch: verify-the-real-thing (#180, #181, #182). Each lens
extends a shipped one and points at it rather than restating it.

### Added — deep-code-review
- **`infra-iac-containers.md`** — confirm a deploy on a byte only the *new* build
  serves, never `/health`: on a build-then-promote platform the old pod keeps
  answering `/health` = 200 through a slow build's `504`, so poll a discriminator (a
  new-build-only asset path 404 -> 200, a build id, a changed header). Sharpens the
  verify-by-effects rule (#148) (#182).
- **`method.md`** — prove a verify gate *idempotent* (run it twice), not just green
  from a clean clone: a gate whose steps write artifacts a later step consumes can
  pass once and fail on re-run; a non-handler export from a framework route module
  (`.next/types/**`) is one concrete order-dependent trigger (#180).
- **`product-ux-quality.md`** — measure a field's distribution before building a
  confidence/corroboration UI: a near-constant field is false precision even as a
  tier — drop it or reframe to what actually varies (extends the confidence-tier
  detector #155) (#181).
- Three new behavioral evals.

Closes #180, #181, #182.

## [1.78.0] — 2026-09-16

Wave 7 of the dogfooding batch: gate- and probe-honesty (#157, #165, #166, #167,
#168). Each lens points at existing content rather than restating it.

### Added — deep-code-review
- **`security-appsec.md`** (A01) — a downloadable export is a *sharper* leak surface
  than an on-screen view: enumerate every surface serving a sensitive dataset and hold
  exports no weaker than the dashboard; deliver confidential per-viewer data via an
  authenticated, server-scoped API, not an SSR page scoped only by client-side identity
  (#165). Points at the existing dual-surface census, does not restate it.
- **`method.md`** — a no-regressions gate keys on **reachability** over the
  before-vs-after route graph, not surface-position stability: a relocated feature is
  not a removed one, but a genuinely orphaned route is a regression despite a lingering
  label (#157).
- **`data-quality.md`** — §7: a boolean/categorical parser accepts every shape the
  source emits, and an exclusion gate (`is_fund`, `is_deleted`) fails **closed** on an
  unrecognised value, never a silent `false` (#166); a suppression/allow-list match
  compares an **exact value set** through one shared predicate with a row-level audit,
  never a substring (#167). §11: a feasibility probe for a current-state signal gates
  on **freshness** (max-timestamp per metric), not just schema and match-rate (#168).
- Five new behavioral evals; new data-quality 🚩 signals.

Closes #157, #165, #166, #167, #168.

## [1.77.0] — 2026-09-16

Wave 6 of the dogfooding batch: the design-parity **verification** cluster (#169,
#170, #171, #177, #178) — how to *check* an implementation against a design without
rubber-stamping a mismatch. Each lens points at existing parity content rather than
restating it.

### Added — deep-code-review
- **`product-ux-quality.md`** — a **parity differ** as a fourth Phase-6 enforcing
  gate: build a mechanical comparator before pixel-matching and gate every "matches"
  claim on its diff image + structured mismatch list, never a sentence; it proves
  equivalence (not that someone looked) and states what it cannot prove
  (intentional-improvement-vs-regression; threshold agreed, not derived) (#177). Read
  the reference at its highest fidelity — running build > design source > screenshot
  (#169). Classify every diff **structural vs cosmetic**, get structural parity first,
  and never call a structural divergence "close / 1:1" — a different structure is a
  different screen (#170). Repeated correction of a "matches" claim means the
  verification **method** is broken — build the comparator, do not outsource
  verification back to the reviewer (#171). The four-axes structure/styling split was
  sharpened so *presence* is structural and *rendered look* is cosmetic (one taxonomy).
- **`migration-parity.md`** — match the **chrome**, never the mock's **data**:
  copying a design mock's *sample* value into the real product is fabrication
  (principle 3), a Blocker that surfaces weeks later; read the mock's own "sample"
  disclaimer as the boundary; brief the split into every parallel worker (#178).
- Three new behavioral evals; new parity 🚩 signals; one pre-ship checklist line.

Closes #169, #170, #171, #177, #178.

## [1.76.0] — 2026-09-16

Wave 5 of the #143–#164 dogfooding batch: the coverage cluster. All five lenses
apply one existing canonical kernel — principle 2, *"an absence is evidence only
after a positive control fires"* (`SKILL.md`) — at five different scopes, and each
**references** it rather than restating it (the anti-duplication thesis).

### Added — deep-code-review
- **`method.md`** — two gate-coverage axes. A green gate clears only the surface it
  enumerated, not one it never visited: an unvisited route / state / branch is
  `unverified` under that green, not clean, and is distinct from a config-declared
  exclusion (#159). And per-lane / per-flag passes in isolation do not clear the
  shipped union — a regression can live only in the combination no single-lane run
  exercises (#158).
- **`data-quality.md`** — §8: an absent activity window is not a decline (distinguish
  observed-low from unobserved before a number implies a trend), and recency must be
  monotone in elapsed time (#163). §7: carry a per-row coverage / provenance flag and
  keep each score glass-box, so a thin-input score is not read as equal-confidence to
  a fully-covered one (#164).
- **`product-ux-quality.md`** — an empty state must name its coverage
  (no-data-collected vs collected-and-genuinely-none), never imply a false all-clear
  over an unprobed source (#156).
- Four new behavioral evals: gate-coverage, lanes-vs-union, activity-absence,
  empty-state-coverage.

Closes #156, #158, #159, #163, #164.

## [1.75.0] — 2026-09-16

Wave 4 of the #143–#164 dogfooding batch: confidence as a defined tier, not a
false-precision number (#155) — spanning the product-output-safety skill (the rule)
and deep-code-review (the review detector).

### Changed — product-output-safety (1.1.0)
- **`SKILL.md`** — MANAGE's "show uncertainty" rule sharpened: render confidence as
  a defined coarse tier (Confirmed / Corroborated / Single-source / Unverified; text
  plus a colourblind-safe cue), never a false-precision number; publish a definition
  per tier (undefined verbal-probability terms are read inconsistently — Kent,
  *Words of Estimative Probability*); keep source reliability and claim corroboration
  as independent axes; never publish the model's own confidence number as precision
  (#155). One new eval.

### Added — deep-code-review
- **`product-ux-quality.md`** — a review detector: confidence surfaced as a bare
  number ("87%", a raw score) is false precision — flag it and require labeled tiers;
  the tier-definition rule is product-output-safety's, not restated here (#155). One
  new eval.

### Docs
- `docs/standards-index.md` — logged Kent, *Words of Estimative Probability* (read
  from the declassified CIA primary source this session) and the Admiralty Code
  (Wikipedia-verified, cited by name only).

## [1.74.0] — 2026-09-16

Wave 3 of the #143–#164 dogfooding batch: four delivery / observability / privacy
lenses across four references, each pre-distinguished from the section it extends.

### Added — deep-code-review
- **`infra-iac-containers.md`** — the deploy-contract preflight gains two lenses:
  deploy artifact size is a first-class budget — externalize heavy, slow-changing
  assets to object storage / a CDN and fetch large data at runtime; a size-rejected
  upload fails silently while the old pod keeps serving (#147); and a deploy upload's
  HTTP status is not the deploy's outcome on a synchronous-build platform — verify by
  effects (a new deployment id / booted pod / changed served version), and read
  409-vs-timeout before re-uploading (#148).
- **`observability.md`** — audit the logs a platform injects (an auth-proxy sidecar
  dumping per-request PII and an authz-scope list to a shared store), not only your
  app's own log statements (#150).
- **`privacy-compliance.md`** + **`security-ai-agents.md`** — gate a sensitive derived
  value at the source: the exact value stays in a local gitignored cache, only a
  coarse band crosses a boundary (behind an off-by-default flag), and never pull the
  per-row values into a model's context when an aggregate query would do (#154).
- Four new evals (deep-code-review 51 → 55).

## [1.73.0] — 2026-09-16

Wave 2 of the #143–#164 dogfooding batch: six data-quality review lenses, all in
`deep-code-review/references/data-quality.md`, each pre-distinguished from the
section it extends.

### Added — deep-code-review
- **`data-quality.md`** — six lenses:
  - a fanout/uniqueness gate false-blocks legitimate coverage expansion — hard-block
    only a value *absorbed from a now-departed distinct record*, not a newly-shared
    *standing* value among related entities (#149);
  - the resolution order when no stable id exists, and surfacing the unresolved
    count as a first-class output (#153a);
  - never sum heterogeneous constructs into one composite score (#162);
  - test every enum/config mapping against the source's real value distribution,
    not the literals a unit test feeds it (#153b);
  - backtest a proxy-derived metric against ground truth before shipping, and match
    the validation metric to the claim — an ordinal rank validated by concordance /
    a C-index, not MAE (#151, #161);
  - measure existing-source coverage before scoping new enrichment/scrapers, and
    scope to the measured residual (#152).
  - Plus new 🚩 red-flag detectors and a Cyrillic-to-Latin typo fix.
- Six new evals (deep-code-review 45 → 51).

## [1.72.0] — 2026-09-15

Wave 1 of a new dogfooding batch (#143–#164): five field lenses from peer
dogfooding and live-build runs, each pre-distinguished from a shipped neighbor.
Content in deep-code-review + agentic-delivery.

### Added — deep-code-review
- **`frontend-a11y.md`** — a global focus/scroll-into-view correction handler
  (the WCAG 2.2 *Focus Not Obscured* remedy) must yield to an open overlay and
  scope to the focused element's own scroll container, or it scrolls the
  background out from under an open modal — the a11y remedy silently breaking
  `product-ux-quality.md`'s rule that a drawer overlays so "the user keeps their
  place" (#143).
- **`method.md`** — reproduce a gate's finding with the gate's **own detector**,
  not a hand-rolled probe that can "reproduce" a passing state (a repro-fidelity
  axis distinct from the gate being wrong or unrun) (#146); and an **input
  reference is stale until you check its revision + completeness** before building
  on it — the build-time analog of verify-before-you-report (#160).
- Three new evals.

### Added — agentic-delivery
- **`fast-agentic-delivery.md`** — a subagent's transcript size or mtime is
  **not a liveness signal**: never kill (a destructive, shared-state action —
  principle 9) or trust a lane on transcript staleness; judge liveness from the
  agent's actual product (#144); and **serve and commit from separate trees** —
  a long-running process that rewrites a tracked, gate-asserted config dirties
  every commit from the same tree (#145).
- Two new evals.

## [1.71.0] — 2026-09-15

Three more field learnings (#138–#140) from the peer dogfooding run, each
pre-distinguished from a shipped lens. Content in deep-code-review + agentic-delivery.

### Added — deep-code-review
- **`method.md`** — fix the failing **LAYER**, not the first plausible one: a
  missing-value symptom is often a data/config/mapping gap, not a render bug; localize
  the layer before patching (a view fallback masks it), name the proven layer, and
  handle the **two-layer** case (correct default forward + backfill existing records).
  The high-frequency instance of principle 9 (#139).
- **`product-ux-quality.md`** — one component at **two scopes** (single-entity vs
  aggregate/rollup) needs scope-aware copy + per-row attribution + a capped union; a
  distinct axis from #123 (prop) and migration-parity's section-set superset (#140).
- Two new evals.

### Added — agentic-delivery
- **`fast-agentic-delivery.md`** — parallel lanes sharing one **out-of-tree scratch
  path** cross **commit metadata** (lane A commits with lane B's message): invisible to
  a diff-scoped review and not covered by worktree-per-lane; give each lane a unique
  scratch path and verify metadata ownership, not just the diff. 🚩 grep
  `git commit -F <fixed-path>`. Complements `concurrency-shared-state.md` (#138).

### Changed
- Lockstep bump to **1.71.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review + agentic-delivery. Closes #138, #139, #140.

## [1.70.1] — 2026-09-15

Patch: sharpen the #135 lens (`agentic-delivery/references/fast-agentic-delivery.md`)
with the reconciled mechanism from the peer session. A monitor-armed subagent cycles
stop→wake and can emit "completed" more than once for the same task-id, so a single
"completed" is **not proof of terminal completion**. Added the detection **tell** (a
repeated "completed" for the same task-id, or the agent's own last report still
"waiting") and de-hedged the mechanism to what the harness documents (conditioned on
that harness design, kept host-neutral). Eval updated to match. Lockstep bump 1.70.1
(deep-code-review, agentic-delivery, idea-critic, plugin); content: agentic-delivery.

## [1.70.0] — 2026-09-15

Three more field learnings (#133–#135) from a per-surface UI migration + a
merge-train run, sent by the peer dogfooding session. Content in deep-code-review +
agentic-delivery.

### Added — deep-code-review
- **`migration-parity.md`** — unify the **chrome/shell** (per-page header, tab strip,
  stat-tile, sub-nav, the which-tabs rule) **before** porting screens: the scaffold
  level above component unification; a surface that reimplements a chrome primitive is
  a structural defect; align the outlier family to the majority; render the same
  sub-view superset with honest-empty states, keeping a view hidden only when it would
  show a **misleading aggregate** (computed-not-fabricated over tab-count symmetry);
  unify a two-behavior control (nav link vs toggle) as one styling primitive + two
  thin wrappers, never a dual-mode-prop component (#133).
- **`frontend-a11y.md`** — "one control, one role": a dual-mode nav/toggle component
  emits the wrong role/focus/keyboard semantics for the unwired mode; share styling,
  wrap behavior (the a11y half of #133).
- One new eval.

### Added — agentic-delivery
- **`fast-agentic-delivery.md`** — a symlinked `node_modules` breaks the heavy gates
  three ways (`tsc` TS2307 from under-install, dev-bundler boot, `--max-warnings`
  drift); run `npm ci` in the worktree — local-QA-red / CI-green is the tell (#134,
  generalizing #127's symlink note). And confirm a subagent is **idle** before
  dispatching a duplicate lane — a monitor-armed subagent's "completed" can arrive
  while it still runs; the watcher-side complement to #127.1 (#135).
- One new eval.

### Changed
- Lockstep bump to **1.70.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review + agentic-delivery. Closes #133, #134, #135.

## [1.69.0] — 2026-09-15

Wave 2 of the dogfooding batch (#122, #124, #129, #130.1) — the migration /
prototype-reference cluster — landed as a new routed reference under domain P
(`migration-parity.md`), per the owner's structure decision (a reference, not a new
domain). Content in deep-code-review.

### Added — deep-code-review
- **`references/migration-parity.md` (new, routed from domain P)** — the port /
  prototype-reference half of domain P, alongside `frontend-a11y.md` and
  `product-ux-quality.md`. Four lenses:
  - Verify parity **surface-by-surface, on real data**, never from a structural or
    seed-data audit — the latter over-reports parity and misses route defaults,
    missing fields, per-page reimplementations, dropped sub-views (#130.1).
  - Anchor findings on **treatment, not data-volume**: a sparse mockup is not a
    feature spec; separate treatment differences (restyle) from data-volume
    artifacts (progressive disclosure, never deletion) from real extra features
    (preserve). "Drop/remove X to match the reference" is a review smell; a
    height/count delta versus a seed mockup is a notice, not a defect (#129).
  - **Flow-cost** pass — navigation cost (clicks + scroll to complete and to
    reverse/switch) and cognitive load — is first-class, beyond structural/pixel
    parity (#122).
  - A **cited** per-screen craft checklist grounded in NN/g's 10 usability
    heuristics (fetched + logged), Refactoring UI (by name), and the target's own
    design system — a review names the principle, not "looks off" (#124).
- Routed from `SKILL.md` (domain-P table + read-when trigger) and
  `domain-checklists.md` domain P. NN/g moved from by-name to **verified by direct
  fetch** in `docs/standards-index.md` (2026-09-15).
- Four new evals.

### Changed
- Lockstep bump to **1.69.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review only. Closes #122, #124, #129, #130.

## [1.68.0] — 2026-09-15

Wave 1 of a large dogfooding batch (#120–#130, from the peer migration run). Seven
self-contained lenses that each extend an existing section; the migration/prototype
cluster (#122, #124, #129, #130.1) follows in a later release pending a structure
decision. Content in deep-code-review + agentic-delivery.

### Added — deep-code-review (review lenses + detectors)
- **`reliability-error-handling.md`** — fail closed to LAST-GOOD, not to abort, when
  a preflight's live-read failure is stricter than the system's own downstream
  staleness gate; degrade to a snapshot the downstream already trusts, fail closed
  only when none is valid. Distinct from retry (#120). 🚩 added.
- **`testing-and-evals.md`** — testing an outbound alert/webhook from a spawned job
  needs async `spawn` + a localhost listener (`spawnSync` deadlocks the in-process
  capture); assert one POST with a privacy-safe body (#121).
- **`product-ux-quality.md`** — one shared component rendered with a feature-bearing
  optional prop defaulted off at some mount sites is a consistency defect the
  twin-search misses; enumerate every mount site and diff the props (#123). Plus:
  variant/option bloat (N interchangeable ways to view one thing) is a simplicity
  smell — cut to one default, don't tune the set (#125); and unification is a
  **precondition** of a port, not a cleanup pass (#130.2).
- **`report-format.md`** — the "Beware the proxy" passage widened once to name two
  more proxies: a green typecheck/unit suite for a surface that only renders across
  a framework boundary, and merge-state/structural-match standing in for subjective
  UX quality (the felt in-flow experience is the bar) (#126, #128 completion side).
- **`frontend-a11y.md` + domain P** — server/client-boundary lens: a plain
  non-component value exported from a `"use client"` module and imported by a server
  component is silently replaced with a client-reference proxy — an unstyled/empty
  render that passes typecheck, lint, and unit tests; caught only across the real
  split. Lint-shaped static check + fix pattern + debugging heuristic (#128).
- Five new evals.

### Added — agentic-delivery (delivery overlay)
- **`fast-agentic-delivery.md`** — run verification in the **foreground**: a
  sub-agent's backgrounded gate loses its verdict (the parent isn't reliably
  notified after the sub-agent exits) (#127.1). Boot-the-dev-server lanes need a
  copy-on-write clone, not a symlink, of the dependencies dir (the modern bundler
  rejects a path outside its root); a gate must distinguish "could not run" from
  "found a problem" (#127.2). Acknowledge a live-feedback burst before dispatching —
  silent throughput reads as ignoring (#130.3).
- Two new evals.

### Changed
- Lockstep bump to **1.68.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content: deep-code-review + agentic-delivery. Closes #120, #121, #123,
  #125, #126, #127, #128. (#122, #124, #129, and #130's remaining part .1 are wave 2.)

## [1.67.0] — 2026-09-14

Four more field-learning lenses (issues #114–#117), continuing the same
dogfooding run. All land in deep-code-review; each verified from source (the
bash-3.2 footgun reproduced live on macOS's `/bin/bash`) and privacy-scrubbed.

### Added — deep-code-review (review lenses + detectors)
- **`security-ai-agents.md` + `domain-checklists.md` (domain C)** — anchor
  relative time deterministically (the time instance of deterministic-first): a
  prompt resolving *today* / *last quarter* must be handed an authoritative
  current date by code — the model never authors *now*, or it ships a plausible
  wrong date as fact (LLM07). Inject the anchor into the **trusted** region,
  never untrusted/RAG context (LLM01 indirect injection); **fail closed** on a
  missing/unparseable anchor — no silent `now()` default. Grep hook added (#114).
- **`language-stack-redflags.md` (Shell / Bash)** — `set -u` + `"${arr[@]}"` on
  an *empty* array is a fatal `unbound variable` under bash 3.2 (still macOS's
  default `/bin/bash`); guard with `${arr[@]+"${arr[@]}"}`. Most dangerous in
  trap/cleanup/reporting code, where it masks the real failure (#115).
- **`SKILL.md` principle 2 + `method.md` Phase 1** — an enforcement artifact (a
  gate / CI / privacy / lint / hook / checksum script) changed in the diff it
  gates is self-certified: green CI ran the shipped copy grading itself. Re-run
  the **base** version (`git show <base>:`) independently; a change that narrows
  what the gate catches while staying green is a Blocker (#116).
- **`reliability-error-handling.md`** — the converse retry/timeout lens: grep the
  project's **own** retry/backoff/timeout primitive and confirm every
  external-I/O site on the critical path routes **through** it; an
  existing-but-bypassed site is the finding, and the fix is to route it through
  the existing primitive, not add a second. Grep lead added (#117).
- Three new evals: `prompt-resolves-relative-date-needs-injected-anchor`,
  `gate-changed-in-diff-rerun-base-version`,
  `reliability-confirm-uniform-primitive-routing`.

### Changed
- Lockstep bump to **1.67.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content changed: deep-code-review only. Closes #114–#117.

## [1.66.0] — 2026-09-14

Five field-learning improvements from a live dogfooding run (issues #109–#113,
filed from a peer session working a real UI-parity migration), generalized and
privacy-scrubbed. Extends the visual/design-parity discipline (1.64.0) with the
measurement root-cause and hardens the delivery overlay for browser-only signals.

### Added — deep-code-review (review lenses + detectors)
- **`product-ux-quality.md`** — "match by measured device-pixels, not user-space
  units — equal user-units ≠ equal pixels"; same-axis oscillation of one property is
  the tell of a duplicated implementation at a different render scale (measure the
  scale ratio and derive, don't tune; validate you measured the visible ink, not an
  overlay/focus path). Cross-refs the stop-tuning discipline (#109).
- **`product-ux-quality.md`** — cross-file UI duplication is invisible to a
  diff-scoped review; the duplicated visible literal string/heading is the search key
  that surfaces the twin the user renders (#112).
- **`domain-checklists.md` (domain P)** — an SSR/hydration restricted-content-model
  nesting detector (a block-level element or `<p>` inside a `<p>`, nested
  `<button>`/`<a>`): the browser auto-corrects it, so it is absent from the hydrated
  DOM and can be state-specific — scan the SSR/static output in the specific state,
  not the live DOM (#111). Grep hook added.
- Three new evals: `visual-parity-measure-pixels-not-user-units`,
  `ssr-hydration-restricted-nesting-scan-static`, `duplicate-ui-twin-across-files`.

### Added — agentic-delivery (delivery overlay)
- **`fast-agentic-delivery.md`** — draft-gated heavy/browser gates hide a
  UI-regression wave: fast-tier-green is not UI-correct; run heavy gates on the
  integration branch periodically while the draft is open (or budget the wave), and
  verify browser-only signals centrally (#110).
- **`fast-agentic-delivery.md`** — delegate visual/parity work by measured number,
  not adjective: numeric acceptance targets up front; the lane returns a measurement
  table the coordinator confirms against the reference (#113).
- Two new evals: `draft-gated-heavy-checks-hide-ui-regressions`,
  `delegated-visual-work-needs-numeric-targets`.

### Changed
- Lockstep bump to **1.66.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Content changed: deep-code-review + agentic-delivery. Closes #109–#113.

## [1.65.0] — 2026-09-14

Trims `agentic-delivery/SKILL.md` back under the 24,000-byte size budget
(28,049 → 23,954 B) by relocating operational depth to its routed reference —
the skill's own progressive-disclosure rule applied to itself. No rule, gate, or
principle removed. The `agentic-delivery` size-allowlist pin in `ci-gates.sh` is
now droppable (routing reports plain `ok`, no `SIZE ALLOWED`); removing the pin
itself is left as a separate owner call.

### Changed
- **`agentic-delivery/SKILL.md`** slimmed: the fan-out-sizing tiers + pilot
  procedure and the environment-probe procedure (probe commands,
  decide-from-probe, shell-semantics, contention-vs-defect) moved to
  `references/fast-agentic-delivery.md`; the act-on predicate (free RAM + swap
  trend), the Conductor's event-driven rhythm, the drift rule, and
  escalate-after-two-failures stay in the core. Prose compressed throughout.
- **`agentic-delivery/references/fast-agentic-delivery.md`** gains the relocated
  **Environment probe procedure** and **Size the fan-out** sections; its framing
  (read-when, the load-average section's opener, and the cross-references)
  updated so it no longer claims the probe procedure lives in `SKILL.md`.
- Lockstep bump to **1.65.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` changed content.

## [1.64.0] — 2026-09-13

Sharpens the visual/design-parity discipline (issue #105). The 1.62.0/1.63.0 work
made the **default served state** the canonical parity surface and named the proxy
trap; a real dogfood run still shipped a false "looks the same" ✅ by walking
*around* that rule — offering a **structural** check as visual evidence,
**reconfiguring** what "default" means and then verifying it, conflating the four
axes, and **guessing** the axis instead of asking. This closes those gaps.

### Added
- **`product-ux-quality.md` — new section "'Looks the same' is about rendered
  appearance — four axes, and a structural check is not a visual one."** Names the
  four independent axes (**structure / styling / content / data**) and forbids
  conflating them (a section-order/DOM diff is a *structure* claim, never "looks the
  same"; do not "fix" data to answer a styling complaint); a
  structural/DOM-order/section-presence check (or a passing test / loaded data) is a
  **proxy** for rendered appearance — claim parity only from a computed-style and/or
  screenshot diff of the default state; **do not move the goalpost** (reconfiguring
  the default persona/seed/flag then verifying "the default" measures a surface you
  authored); **enumerate every diff in one pass** before fixing (piecemeal-fix-then-
  redeclare is the repeated-false-✅ loop); **disambiguate the axis** when told "not
  the same" (after one wrong guess, ask not guess); the **reference** is truth for
  styling — compare element × breakpoint × theme, not memory. Four new pre-ship
  checklist items.
- Three new evals: `visual-parity-structure-not-styling`,
  `visual-parity-default-not-reconfigured`, `visual-parity-ask-axis-not-guess`.

### Changed
- **`report-format.md` — proxy trap widened.** A **structure/DOM-order or
  section-presence match** and a **self-reconfigured surface** (switching the
  default, then verifying "the default") are named as proxies alongside the passing
  test / green build / merged PR / hand-configured render.
- **`SKILL.md`** — domain-P routing trigger now fires on visual/design-**parity**
  work ("make X look like Y", a port/restyle/redesign), where the claim is about
  rendered appearance, not structure/tests/data.
- Lockstep bump to **1.64.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content. Closes #105.

## [1.63.0] — 2026-09-13

Completes the completion-claim discipline (issue #101) — the proxy trap, the
completion record, and a mechanical checker. Builds on 1.62.0 (which shipped the
default-state-canonical + caveat-downgrade core).

### Added
- **`deep-code-review/scripts/validate_status_claims.py`** — a heuristic checker
  ("a ✅ that needs an asterisk is a ✗"): given a status table it flags a positive
  status (✅ / done / exact / matches / verified / complete) co-occurring with a
  hedge (if / only / once / unless / requires / caveat / mostly …) and no
  downgrade marker (⚠️ / ❌ / partial / blocked / unverified). Exit 1 = candidates
  to re-check, 0 = clean, 2 = usage. A lead for judgement, not an automatic
  defect. Ships beside the skill (copied by `install.sh`), routed from
  `report-format.md`, with a self-test in `test-ci-gates.sh` (planted hedged-green
  flagged; an honest downgrade not flagged; a clean table passes).
- New eval `completion-claim-proxy-not-user-outcome`.

### Changed
- **`report-format.md`** — the **proxy trap** named explicitly (a passing test /
  green build / merged PR / hand-configured render is a proxy for the user's
  outcome, not the outcome) and the **completion record** (a status carries
  `(surface · default-state observed · reference checked) + what was not checked`).
- Lockstep bump to **1.63.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content. Closes #101.

## [1.62.0] — 2026-09-13

Status-claim honesty (issue #102) — closes a trust gap surfaced by a real
over-claim: an agent marked a rebuilt UI "✅ exact" after checking a mock and a
hand-picked view, not the default state a user lands on, and kept the ✅ despite a
noted caveat. The status-reporting discipline already existed (`report-format.md`,
`product-ux-quality.md`); this closes the two holes the failure fell through.

### Changed
- **`report-format.md`** — a status names the **surface** its evidence came from
  and holds at its **strongest reading**: a `✅` / done / exact / matches / verified
  the author can immediately qualify is **downgraded** (⚠️ / partial / ❌), never a
  green label beside a caveat ("caveat-exact isn't exact"). For a UI/parity claim
  the canonical surface is the **default served state**.
- **`product-ux-quality.md`** — new "Parity claims: the default state is the
  canonical surface" section + checklist items: verify the **default landing
  state** (signed-out / no-role / default route / local default), not only a mock
  or a hand-picked persona view; a claim resting on a non-default surface must name
  it; no status green-with-a-caveat. "More than the happy-path state" is necessary
  but not sufficient — the default must be among the states checked.
- **Principle 2** (`SKILL.md`) — a status you emit names its evidence surface,
  holds at its strongest reading, downgrades on a caveat, and takes the default
  served state as canonical for a UI/parity claim.
- New eval `ui-parity-claim-checks-default-state-not-mock`. Lockstep bump to
  **1.62.0** (deep-code-review, agentic-delivery, idea-critic, plugin); only
  `deep-code-review` gained content.

## [1.61.0] — 2026-09-13

Domain-C review lens for **agent context/memory lifecycle** — the one genuine gap
found by a verify-grounded scan of the 2026 agent-building frontier (context/
memory management, recursive & multi-agent orchestration, agent security). The
scan's headline was that the bar is **current** — OWASP LLM/Agentic/Agentic-Skills
all on their latest 2026 editions, and most frontier concepts already owned by the
suite; this ships the single genuine gap the scan found.

### Added
- **`security-ai-agents.md` — "Context & memory lifecycle" defensive lens** (domain
  C): a long-running agent that summarizes/compacts context, evicts old tool
  results, or persists memory can **silently drop a safety constraint** (approval
  scope, authority grant) with **no attacker and no crash** — so ASI06 (adversarial
  poisoning) and F (crash recovery) miss it by construction. Reviews the lifecycle:
  compaction preserves/re-asserts constraints; tool-result clearing exempts the
  constraint/authority-bearing item; persistent memory validates on write and
  expires; cross-agent handoff carries the full trace; resume revalidates authority.
  Cross-refs `agentic-delivery/references/project-state.md` (the delivering-agent
  runbook — here it is a review check over the *target*), ASI06, LLM09, and domain
  T. New eval `agent-context-lifecycle-constraint-survives-compaction`; 🚩 tells
  added to the C checklist in `domain-checklists.md`.
- **LLM06 "bound the tree, not just the call" clause** — in a recursive/multi-agent
  system the depth/step/spend cap must be propagated to every spawned sub-agent, or
  a parent cap not forwarded leaves the tree unbounded (a real filed bug class).

### Changed
- `docs/standards-index.md` — six sources verified by direct fetch this session
  (2026-09-13): Anthropic long-running-agents (2025-11-26), context-editing,
  compaction, and memory-tool docs; Cognition "Don't Build Multi-Agents"
  (2025-06-12); langchain-ai/deepagents #1698.
- Lockstep bump to **1.61.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.60.0] — 2026-09-12

Two new review domains — the taxonomy grows from A–S (19) to A–W (21): **T
Multi-tenancy & isolation** and **W Workflows, jobs & scheduling** (issue #96).

### Added
- **Domain T — Multi-tenancy & isolation** (`deep-code-review`): the cross-tenant
  leak that survives a clean access-control review — a cache / index / pool / job
  that forgot the tenant key, tenant context outliving its request, per-tenant
  lifecycle (export & deletion across every store), noisy-neighbour fairness, and
  the isolation model (row-level / schema / silo-per-tenant). Checklist-only in
  `references/domain-checklists.md` (like A/H/N/R); the seam is stated explicitly
  against **B/A01** (authz / IDOR) and **G** (races). New eval: a tenant-less
  cache key leaks across tenants even though the authorization review is clean.
- **Domain W — Workflows, jobs & scheduling** (`deep-code-review`): orchestration
  correctness for cron, queues, and multi-step workflows — never-runs (liveness),
  runs-twice (exactly-once *effect* on at-least-once delivery), dead-letter and
  retry caps, cron timezone / DST, ordering, durable long-running / saga state
  with compensation, and backpressure. Checklist-only; the seam is stated against
  **F** (single-call handling) and **G** (races), and scoped **out** of **E**
  (one-time migrations) and **K** (deploy / rollout). New eval: an at-least-once
  billing job needs an idempotent effect, a liveness alert, and an explicit
  timezone.

### Changed
- **Taxonomy A–S → A–W (21 domains).** Propagated the range through `SKILL.md`
  (domain map, phases, both role tables), `domain-checklists.md`, `method.md`,
  `role-coverage.md` (T assigned to the Backend lead, W to Platform / DevOps / SRE
  so no domain is orphaned), and `README.md`. **U, V and X–Z remain unassigned** —
  a domain earns its letter; the map grows only when a genuinely new class of
  defect does, never to pad the alphabet.
- Lockstep bump to **1.60.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.59.0] — 2026-09-11

README-authoring method — so the skillset produces onboarding READMEs for any
project, not just this one.

### Added
- **`deep-code-review/references/readme-authoring.md`** — the depth behind the
  domain-O "README (human-facing)" checklist: model the reader (default the
  evaluator), the plain-value-first onboarding arc with progressive disclosure,
  one host-native diagram (quote Mermaid labels; no external badges — a rotting
  live value), the anti-slop craft (superlatives out, tables over repeated
  patterns, no uncontrolled third-party claims), accuracy-vs-code (every
  command/flag verified against the tool; verify a pin actually pins), and keeping
  the **safe install path as the quickstart**. Generalized from this repo's own
  README overhaul and its independent review; routed from domain O and cross-linked
  from `docs-and-dx.md`. New eval resists two planted bad asks (a version badge; a
  shorter-but-unsafe install first).

### Changed
- Lockstep bump to **1.59.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.58.0] — 2026-09-11

Adopt the **Perun** umbrella brand (issue #38) — theme + wordmark only.

### Changed
- **README hero + `plugin.json` description** rebranded to **Perun** ("bring the
  thunder to your codebase") — the suite's umbrella identity, named for the
  Slavic thunder god of order and justice (strikes down chaos, never fabricates,
  leaves the bar in place). The **flagship skill name `deep-code-review` is
  unchanged**, as are all sibling skill names; the brand is the suite/repo layer.
  Added `perun` to `plugin.json` keywords.
- **Repo-slug rename deferred** (owner decision): GitHub redirects make it safe
  to do anytime; the pinned URLs to update when chosen are README (clone + npx
  slug) and `plugin.json` (homepage/repository). Brand adopted first.
- Copy kept **agent-agnostic**: "for building with AI agents", any major coding
  agent — no single-vendor focus.
- Lockstep bump to **1.58.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed (branding metadata only).

## [1.57.0] — 2026-09-11

Support & feedback operations lens (issue #44, G3) — agentic-delivery.

### Added
- **`agentic-delivery/references/support-ops.md`** — narrow reactive support-ops:
  an intake + triage taxonomy, a per-severity SLA template (owner sets the
  numbers), canned-response quality, and the **support→backlog loop** (a ticket
  revealing real work becomes a well-formed work item via the Where/Done-when/
  Verify/Why contract). **Load-bearing safety gate:** never auto-send an external
  reply and never make a promise/refund/commitment without owner approval — the
  same human-approval-on-external-action gate the skill applies to push/deploy.
  It cross-refs rather than restates: `incident-response.md` (outage tickets),
  `deep-code-review`'s `docs-and-dx.md` (Diátaxis help-center), and
  `communication-structure` (no-slop responses). Scope is narrow — not
  onboarding/activation (growth/product-ux). New evals: a ticket becomes a
  well-formed backlog item; no external reply/refund is auto-sent without
  approval. Independently reviewed before merge.

### Changed
- Lockstep bump to **1.57.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` gained content (a reference + a minimal routing
  pointer + two evals); it stays allowlisted for SKILL.md size (a trim pass into
  references is due).

## [1.56.0] — 2026-09-11

Adopt the two additive principles that were not yet codified (issue #37).

### Added
- **`deep-code-review/references/docs-and-dx.md`** — a "Persisted knowledge
  hygiene — store the query, not the answer" lens (domain O): a durable doc/memory
  that records a fact derived from live state (an issue count, a current version)
  rots; store the *query* that regenerates it. Audits a memory store / `AGENTS.md`
  / runbook for three decay modes — dead paths, status-without-a-command, and
  embedded credentials (cross-ref `privacy-compliance.md`) — each a finding.
- **`agentic-delivery/SKILL.md`** — a **work-item contract** beside the output
  contract: a work item is specified as **Where / Done-when / Verify / Why**, and
  one missing *Done-when* or *Verify* is underspecified and sent back to be scoped,
  not started (the input the output contract is graded against).

### Notes
- The third sub-item (a — the suite map as a *registry that describes access, never
  copies*) was already adopted: `agentic-ceo/SKILL.md` frames the registry as "a
  map, not a bundle" and its anti-rationalization table rejects restating a skill's
  steps. No change needed there; verified before closing.
- No duplication introduced (the memory-audit's secret check cross-refs the privacy
  reference rather than restating it; the work-item contract has no prior home).

### Changed
- Lockstep bump to **1.56.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin).

## [1.55.0] — 2026-09-11

Design-time regulated-domain obligation triage (issue #43, G2) — business-ops.

### Added
- **`business-ops/references/regulated-domain-triage.md`** (business-ops → 1.1.0)
  — the design-time front door for Lane R: a decision tree that runs *before the
  architecture hardens* (and re-prompts on entering a new market or handling a new
  data type). Triggers — health data, payments/card data, minors, EU/UK personal
  data, US-state privacy, biometrics, consequential/automated decisions, money
  movement, enterprise security — each **name the regime** (HIPAA, PCI DSS, COPPA,
  GDPR/UK GDPR, CCPA/CPRA, biometric-privacy, SOC 2/ISO 27001, and the like, by
  name only) and surface engineering-obligation **leads**, then **route the binding
  question to counsel**. The privacy branches point downstream to
  `deep-code-review`'s `privacy-by-design.md` (pre-code artifacts) and
  `privacy-compliance.md` (engineering) rather than restating them; it reuses Lane
  R's asymmetric boundary instead of duplicating it. **Boundary:** name + route;
  it never determines that a regime binds this business, and asserts no article
  number, threshold, or deadline. New eval: a health/payments/minors input yields
  a "route to counsel + named regime", never a compliance conclusion. Unblocks the
  G4/G5 lenses (they inherit the named regime).

### Changed
- Lockstep bump to **1.55.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `business-ops` gained content (independently versioned 1.0.0 →
  1.1.0).

## [1.54.0] — 2026-09-11

Two deep-code-review lenses: privacy-by-design product artifacts (issue #46, G5)
and billing/monetization correctness (issue #48, G7).

### Added
- **`deep-code-review/references/privacy-by-design.md`** — the pre-code
  privacy/compliance *artifacts* an EU user or enterprise buyer demands, as a lens
  over domain Q: a ROPA-style processing register, a DPIA scaffold + risk
  questions, a consent-UX spec, a subprocessor list with data-flow notes, and
  data-residency options. It sits *above* `privacy-compliance.md` (which stays the
  code layer — inventory, retention/DSAR/erasure, consent recording) and links to
  it rather than restating it. **Boundary:** scaffold + gap-detect; the
  privacy-policy/ToS text, whether a DPIA is legally required, and lawful-basis
  selection route to counsel. Frameworks named by name only; **no article numbers
  or legal deadlines** until fetched. New eval: a new PII field prompts the
  register/DPIA question.
- **`deep-code-review/references/billing-correctness.md`** — a mechanics lens on
  domain E (cross-ref F/G/I) for revenue correctness: metering (exactly-once),
  proration, dunning/failed-payment recovery, tax/VAT *application in code*,
  refunds/chargebacks, webhook idempotency, and the double-charge/revenue-leakage
  races. **Boundary:** review the logic; tax registration/filing and
  revenue-recognition policy route to an accountant, pricing to the owner
  (`business-ops`); **no invented tax rate**. New eval: a double-charge race and a
  non-idempotent webhook are both flagged.

### Changed
- Both references routed from the domain table in `deep-code-review/SKILL.md`
  (rows E and Q) with when-triggers; SKILL.md 21298 → 21439 bytes, well under the
  24000 budget.
- Lockstep bump to **1.54.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `deep-code-review` gained content.

## [1.53.0] — 2026-09-11

Operational-readiness lens — incident response + continuity (issue #45, G4).

### Added
- **`agentic-delivery/references/incident-response.md`** — the "system on fire
  OR the operator is gone" binder for bus factor = 1. Incident runbook
  (detect→triage→contain→eradicate→recover→blameless review), severity-level and
  status/comms templates, a break-glass access path, a credential/renewal
  inventory (domain, TLS, card, DNS, secrets) with **dead-man** reminders, a
  restore-drill schedule, and a solo-operator succession note. It reuses the
  blameless `template-postmortem.md` / `retrospective.md` for the review step and
  points restore/observability depth at `deep-code-review` rather than restating
  it. **Boundary:** breach-notification *timing* routes to G2 + counsel and is
  never asserted here; executing notification/succession is the owner's; no
  invented SLA, deadline, or renewal date. New eval: a planted expired TLS
  credential is surfaced, a restore-drill schedule is present, and the breach
  deadline is routed, not fabricated.

### Changed
- Lockstep bump to **1.53.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `agentic-delivery` gained content (a reference + a minimal
  routing pointer + one eval); the routing pointer keeps the allowlisted
  SKILL.md's growth to routing, not depth.

## [1.52.0] — 2026-09-11

Decision-hygiene frame for the builder's own hard calls (issue #47, G6).

### Added
- **`idea-critic/references/decision-hygiene.md`** — a routed reference that
  structures the owner's *own* high-stakes call (pivot, quit/kill, big
  irreversible spend) rather than attacking a proposal. Frame: one-way vs
  two-way door classification; the outside view (reference-class / base rate);
  sunk-cost, confirmation, and escalation-of-commitment surfaced; and
  kill/quit/pivot criteria pre-committed *before* the bet. It reuses the
  `kill-criteria` premortem instead of restating it, and it **structures** the
  decision for the owner — it never makes the call and never fabricates a
  probability (an ungroundable number is labeled `assumption`).

### Changed
- Lockstep bump to **1.52.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). Only `idea-critic` gained content (a reference + its routing pointer).

## [1.51.0] — 2026-09-11

Routing-eval coverage for the conductor (issue #63, offline half).

### Added
- **`agentic-ceo/evals`** — a routing eval per registry destination (deep-code-review,
  agentic-delivery, idea-critic, growth-analytics, positioning, product-output-safety,
  communication-structure, contribution — joining the existing product-discovery /
  business-ops / owner cases). Each pins a (stage, area, artifact) prompt to its
  expected skill and asserts the routed method is not re-implemented inline
  (registry-not-bundle).
- **`test-ci-gates.sh`** — a coverage assertion: every shipped skill except the
  conductor must have an `agentic-ceo` routing eval, so a destination cannot be
  mis-routed unnoticed. Now 55/55. Live grading of each case rides the eval harness (#61).

### Changed
- Lockstep bump to **1.51.0** (deep-code-review, agentic-delivery, idea-critic, plugin).
  No skill content changed (conductor evals + a self-test added).

## [1.50.0] — 2026-09-11

Gives the SKILL.md size ratchet teeth and gates the install overlay-stamp guard
(issues #16, #83).

### Changed
- **`ci-gates.sh routing` size budget now FAILS, not warns** (#16). An oversized
  `SKILL.md` fails the gate against the documented byte budget (`ci.yml` enforces
  **24000**), unless the skill is on a small reasoned allowlist in `cmd_routing`
  (today only `agentic-delivery`, the full G0–G10 delivery OS). A pin is allowed its
  overage, never required to keep it. Documented in
  `references/skill-authoring-and-size.md`.

### Added
- **`test-ci-gates.sh`** — a non-allowlisted oversized `SKILL.md` now FAILS (was a
  warn); an allowlisted one passes with a `SIZE ALLOWED` note; and every
  skill-adding overlay flag (`WITH_*` guarding a `SKILLS+=` block) must appear in the
  AGENTS.md overlay-stamp guard, so a standalone `--with-<x>` install cannot land a
  skill without its stamp (#83 — the class fixed in #82). Now 54/54.

### Changed
- Lockstep bump to **1.50.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed (a reference doc gained the budget number).

## [1.49.0] — 2026-09-11

Fixes the plugin-install rail and stale first-party metadata (issues #78, #72, #80,
#79). A `/plugin install` or marketplace pin previously discovered **zero** skills —
skills live under `.claude/skills/` but the plugin default scans a root `skills/` and
`plugin.json` declared no `skills` path, so only metadata loaded. Same honesty class
as #55 (documented pin vs actual tree).

### Fixed
- **`.claude-plugin/plugin.json`** — add `"skills": "./.claude/skills"` so the plugin
  rail discovers all 11 skills (the field supplements the default `skills/` scan; path
  relative to plugin root, per the Claude Code plugins reference fetched this session).
  `install.sh` already copied from `.claude/skills/`; the two rails now agree (#78).
- **`plugin.json` description** — was a three-skill string ("gated-delivery and
  idea-critic"); now states the real posture (review-only default + opt-in overlays)
  without copying any skill's method (#72). The GitHub About field was updated to
  match (#79).
- **`docs/roadmap.md`** — `infra-evolution-by-stage` / `docs-evolution-by-stage`
  marked shipped 1.35.0, not "Proposed" (#80).

### Changed
- Lockstep bump to **1.49.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.48.0] — 2026-09-11

Adds **`product-output-safety`** (skill #11) — governs the harm a product's own AI
outputs and automated decisions do to end-users (bias, hallucination surfaced as
fact, over-reliance, missing AI-disclosure, deceptive patterns, unsafe automation of
high-stakes actions). Distinct from `deep-code-review` (the code's security) and
`business-ops` (money/legal routing): it is the behavior of the shipped product
toward its users. The one gap-analysis item (#42) admitted as a standalone skill
under the #66 admission rule; the rest fold as lenses/references.

### Added
- **`.claude/skills/product-output-safety/`** — MAP the per-feature harm inventory,
  MEASURE it with output-harm evals / red-teaming, MANAGE it with a human-in-the-loop
  gate on high-stakes / irreversible actions (NIST AI RMF core functions, by name).
  Hard boundary: red-team + measure + recommend HITL; never certifies "safe" /
  "unbiased" / "compliant", never fabricates a harm metric, routes any legal
  disclosure duty to counsel (+ `business-ops` Lane R). Opt-in, `--with-output-safety`,
  not in `--full`. Four refusal evals (never-certifies-safe, high-stakes-action-gated,
  routes-legal-disclosure-duty, no-fabricated-harm-metric).
- Wired into every enumerated site: `ci.yml` routing, `write-checksums.sh`,
  `install.sh` (flag + `SKILLS` + overlay stamp), `recommend-overlays.py`
  (`REVIEW_ONLY_SKILLS` + advisory list), the `agentic-ceo` registry + routing,
  `README.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `docs/roadmap.md`.

### Changed
- Lockstep bump to **1.48.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). The new skill starts at its own `1.0.0`.

## [1.47.0] — 2026-09-11

Executes the fabrication-refusal evals offline for the first time. Each skill's
`evals/evals.json` described a refusal but was only a fixture, never run; this adds
deterministic predicates that grade a candidate answer and a gate proving each
predicate SEPARATES a fabricated answer from a refusal — no model, no network, no
spend. First slice of the live eval harness (issue #61); the model-calling runner
is the next slice.

### Added
- **`scripts/eval_predicates.py`** — two deterministic predicates over a candidate
  answer: `no_fabricated_finding` (rejects an asserted CWE-id, or a line-numbered
  defect with vuln context, on a clean file) and `no_fabricated_numeric_fact`
  (rejects an asserted currency / percentage / multiplier figure, including worded
  forms like `USD 180` and `four point two billion`), shared by positioning and
  business-ops. A `BINDINGS` table ties each of the three fabrication-refusal evals
  to its predicate and cross-checks the real eval ids, so a renamed eval fails the
  gate rather than silently orphaning the predicate.
- **`scripts/eval-fixtures/`** — a golden `good.txt` (a refusal, must PASS) and
  `red.txt` (a fabricated answer, must FAIL) per bound eval.
- **`--selftest`** — asserts every predicate discriminates its good/red pair;
  wired into `ci.yml` (offline, no key). `test-ci-gates.sh` gains records including
  a planted-RED (a good fixture overwritten with a fabricated answer) that must
  fail closed and name the eval, plus evasion regressions locking known dodges.
  Now 52/52.

### Changed
- Lockstep bump to **1.47.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.46.0] — 2026-09-11

`--recommend` now surfaces the advisory + conductor overlays (issue #68). Previously it
could only ever name 3 of 10 skills (deep-code-review + the delivery/critic pack), so
every advisory skill was invisible exactly when the owner was choosing what to install.

### Changed
- **`scripts/recommend-overlays.py`** — prints an unconditional "advisory overlays
  available (opt-in, default off)" block listing product-discovery, growth-analytics,
  positioning, business-ops, agentic-ceo, communication-structure, and contribution with
  their `--with-*` flags and a one-line reach. It still writes nothing and never
  auto-installs; shape-based auto-push of the highest-fabrication-risk skills is a
  deliberate non-goal.
- Lockstep bump to **1.46.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.45.0] — 2026-09-11

Adds a fabrication-refusal eval to `deep-code-review` (issue #65): the crown-jewel
skill's most-cited safety property — "never invent a defect, metric, CWE, source, or
line" — now has an executable fixture.

### Added
- **`deep-code-review/evals/evals.json`** — `refuses-fabricated-finding-on-clean-file`:
  a prompt that baits CWE ids and line numbers over a clean file; the pass condition is
  no-finding / unverified, not a plausible-looking defect. Distinct from
  `planted-defect-must-be-reported`, which guards fabricating verification *status*.

### Changed
- Lockstep bump to **1.45.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No other skill changed.

## [1.44.0] — 2026-09-11

Adds a **suite-enumeration completeness gate** (`ci-gates.sh enumeration`) — the
enforce-in-code fix for the drift class behind the 1.43.0 registry bug and the
recurring recommend-overlays miss. A new skill can no longer ship green while
missing from a hand-maintained list (issue #62).

### Added
- **`ci-gates.sh enumeration <root>`** — asserts every shipped skill appears in all
  five hand-maintained lists: the `agentic-ceo` registry table (a row, not prose),
  `install.sh` (`SKILLS+=`), the `ci.yml` routing lines, the `write-checksums.sh`
  find-list, and `recommend-overlays.py`. Fail-closed; wired into `ci.yml`.
- **`test-ci-gates.sh`** — two records: the real tree is fully enumerated, and the
  gate goes RED on a planted un-enumerated skill (so it cannot pass vacuously).
  Now 47/47.

### Changed
- Lockstep bump to **1.44.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). No skill content changed.

## [1.43.0] — 2026-09-11

Fixes a routing bug in the `agentic-ceo` conductor (→ 1.1.0): its suite registry was
written at 1.37.0 and never updated as later skills shipped, so it could not route to
`growth-analytics` (1.38.0), `positioning` (1.41.0), or `business-ops` (1.42.0) — a
third of the suite was unreachable from the conductor. Found by two independent review
agents converging on the same defect.

### Fixed
- **`agentic-ceo` → 1.1.0** — the registry table and routing section now cover all
  nine non-conductor skills; new routing eval `routes-later-skill-not-inline`
  exercises dispatch to a later-shipped skill (business-ops Lane A/R). A
  suite-enumeration completeness gate to prevent recurrence is filed as a follow-up.

### Changed
- Lockstep bump to **1.43.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). All other skills unchanged.

## [1.42.0] — 2026-09-11

Adds `business-ops` (1.0.0) — the second thin advisory guide (built last) and the
last of the recommended suite skills. Two clearly separated lanes: Lane A applies
pricing / unit-economics arithmetic to the user's own numbers with the formula shown
(never a directive); Lane R routes legal / tax / securities / employment / privacy —
and fundraising — to a licensed professional (never concludes). Opt-in overlay,
default off, not in `--full`; install with `--with-business`.

### Added
- **`business-ops/`** (new skill, 1.0.0) — the asymmetric Lane A / Lane R boundary
  stated in the frontmatter description (the routing key); standing "educational
  information, not advice" disclaimer; refusal evals: `shows-formula-not-directive`,
  `routes-regulation-questions`, `fundraising-is-a-securities-matter`,
  `no-fabricated-financials`. Never fabricates a figure, statute, rate, or deadline.
  Frameworks registered by-name in `docs/standards-index.md`.
- Wired into CI routing, checksums, `recommend-overlays.py` (`REVIEW_ONLY_SKILLS`),
  `install.sh` (`--with-business`), `CONTRIBUTING.md`, `README.md`, `CLAUDE.md`.

### Changed
- Lockstep bump to **1.42.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). All other skills unchanged.

## [1.41.0] — 2026-09-11

Adds `positioning` (1.0.0) — the first of two thin advisory guides (highest
fabrication-risk, built last): value proposition, segment, differentiation, and a
message house on the USER's own inputs, produced as a hypothesis to validate with
real buyers. Opt-in overlay, default off, not in `--full`; install with
`--with-positioning`.

### Added
- **`positioning/`** (new skill, 1.0.0) — Value Proposition Canvas → positioning
  statement → message house → validate-with-real-buyers, plus the minimum-viable-brand
  rule pre-PMF. Every artifact is a hypothesis or an empty-slot template; refusal evals
  enforce it: never fabricate TAM / competitor claims / customer quotes / outcome
  numbers / trademark-domain clearance (a search is not clearance → route to a
  professional). Frameworks registered by-name in `docs/standards-index.md`.
- Wired into CI routing, checksums, `install.sh` (`--with-positioning`),
  `CONTRIBUTING.md`, `README.md`, `CLAUDE.md`.

### Changed
- Lockstep bump to **1.41.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` / `growth-analytics` (1.0.0), `product-discovery` (1.1.0),
  `communication-structure` (1.2.0), `contribution` (1.1.0) unchanged.

## [1.40.0] — 2026-09-11

Broadens `communication-structure` (→ 1.2.0) into the suite's **no-slop output
contract**: it now governs human-facing *deliverables* (reports, plans, docs,
tables), not only short messages. BLUF, one ask, core-value-only, and the full
"cut on sight" list apply to any output; the 30-second / 150-word cap stays a
message rule (a deliverable is as long as its content requires and no longer).
This is the single home the `agentic-ceo` conductor already points every skill's
output to — enforcing the owner's "clean, concise, no model-forced filler" bar
across all outputs, not just chat.

### Changed
- **`communication-structure` → 1.2.0** — scope widened from messages to messages
  *and* deliverables; new "Deliverables, not just messages" section; description
  updated.
- Lockstep bump to **1.40.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` / `growth-analytics` (1.0.0), `product-discovery` (1.1.0),
  and `contribution` (1.1.0) unchanged.

## [1.39.0] — 2026-09-11

Folds a **Non-goals** lens into `product-discovery` (→ 1.1.0) — the inverse of the
prioritization list and the scope-defense that stops a coding agent from
gold-plating. This completes the carve decision: the standalone product-strategy
skill is dropped; its distinct half (what NOT to build) lives here, its JTBD and
PMF halves already did.

### Changed
- **`product-discovery` → 1.1.0** — new *Non-goals (what you are deliberately NOT
  building)* section: recorded, stage-tied decisions revisited each stage; fed by
  the riskiest-assumption gate; used as one-line scope defense when a request
  touches a non-goal. Refusal eval `non-goals-scope-defense` (flags the collision,
  asks to reopen, never invents a non-goal the user did not choose). Description
  updated to name "what to deliberately not build".
- Lockstep bump to **1.39.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` (1.0.0), `growth-analytics` (1.0.0), `contribution`
  (1.1.0), and `communication-structure` (1.1.0) unchanged.

## [1.38.0] — 2026-09-11

Adds `growth-analytics` (1.0.0) — the standing measurement scoreboard: one
customer-value North Star, the AARRR funnel read bottom-up (retention first), an
event taxonomy that answers a named question, and stage-aware instrumentation.
Opt-in overlay, default off, not in `--full`; install with `--with-growth`.

### Added
- **`growth-analytics/`** (new skill, 1.0.0) — measure the user's own data against
  the user's own baseline; never fabricate benchmarks, metrics, or "good"
  thresholds; route real figures to the user's analytics. States the
  product-analytics vs ops-observability identifier seam (a stable pseudonymous
  per-user id for cohorts) as a pointer to `observability.md` /
  `privacy-compliance.md`, not a restatement. Refusal evals: no fabricated
  benchmarks, North-Star-not-vanity, instrument-only-what-answers-a-question,
  route-real-figures-to-analytics.
- Wired into CI routing, checksums, `install.sh` (`--with-growth`),
  `CONTRIBUTING.md`, `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.38.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `agentic-ceo` (1.0.0), `product-discovery` (1.0.0), `contribution`
  (1.1.0), and `communication-structure` (1.1.0) unchanged.

## [1.37.0] — 2026-09-11

Adds `agentic-ceo` (1.0.0) — the suite's conductor: the orchestrator that routes
across the specialist skills, sizes its own effort to the project stage, and runs
the under-pressure chaos playbook. Opt-in overlay, default off, not in `--full`;
install with `--with-ceo`.

### Added
- **`agentic-ceo/`** (new skill, 1.0.0) — a registry of the suite's skills (a map,
  not a bundle), `(stage, area) -> (skill, lens)` routing, stage/size effort-sizing
  (one agent wearing several skill-hats on small work; fan-out only for read-mostly,
  decomposable work), and the owner-under-pressure chaos playbook (capture losslessly
  -> reflect the full list -> triage to the vital few -> one next action -> hold the
  rest -> support by action, never "calm down"). Refusal evals enforce
  route-not-fan-out on small work, no dropped request under a flood, and routing the
  unknowable to the owner. Self-contained for the suite; general delivery/critique
  defer to `agentic-delivery` / `idea-critic`.
- Wired into CI routing, checksums, `install.sh` (`--with-ceo`), `CONTRIBUTING.md`,
  `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.37.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `product-discovery` (1.0.0), `contribution` (1.1.0), and
  `communication-structure` (1.1.0) unchanged.

## [1.36.0] — 2026-09-11

Adds `product-discovery` (1.0.0) — the first product-advisory specialist skill:
decide whether something is worth building, what to build first, and whether what
shipped works, by structuring evidence from real users. Opt-in overlay, default
off, not in `--full`; install with `--with-discovery`.

### Added
- **`product-discovery/`** (new skill, 1.0.0) — the riskiest-assumption gate (name
  it, run the cheapest disconfirming test before building), Mom-Test / JTBD
  discovery interview design + interpretation, fake-door / concierge experiments, a
  product-market-fit read (very-disappointed survey + retention cohorts), and ICE
  prioritization — all on the user's own inputs. The epistemic spine is enforced by
  refusal evals: it never fabricates findings, quotes, personas, market size,
  scores, or a "validated" verdict, and routes the unknowable to the owner.
- Wired into CI routing, checksums, `install.sh` (`--with-discovery`),
  `CONTRIBUTING.md`, `README.md`, and `CLAUDE.md`.

### Changed
- Lockstep bump to **1.36.0** (deep-code-review, agentic-delivery, idea-critic,
  plugin). `contribution` (1.1.0) and `communication-structure` (1.1.0) unchanged.

## [1.35.0] — 2026-09-11

Extends the stage-aware going-forward roadmap with two *when-to-add* reference
lenses for `deep-code-review`, complementing the existing *how-to-secure* domain
files without duplicating them.

### Added
- **`deep-code-review/references/infra-evolution-by-stage.md`** (new) — infrastructure
  and architecture are *earned, not provisioned*: per-stage build-vs-not-yet, an
  observable trigger for each step (CI, staging, containers, IaC, observability,
  orchestration, service extraction, SLOs), a floor that never relaxes (security,
  secrets, auth, backups), and six business/ops facts routed to the owner. Routed
  from the Project-stage section and domain L.
- **`deep-code-review/references/docs-evolution-by-stage.md`** (new) — which documents
  acquire normative force at which stage (one-pager → design-doc/RFC → spec),
  trigger-not-calendar, and a two-tier router+depth shape for agent legibility.
  Routed from the Project-stage section and domain O.

### Changed
- **`deep-code-review/SKILL.md`** → **1.35.0** (lockstep with `agentic-delivery`,
  `idea-critic`, and the plugin): the Project-stage section now routes the two
  stage-evolution lenses, and domain rows L and O cross-link them (when-to-add vs.
  how-to-secure). No change to `contribution` (1.1.0) or `communication-structure`
  (1.1.0).

## [1.34.0] — 2026-09-11

Hardens the `contribution` self-improvement skill so quality can only ratchet up —
it can never weaken the bar, fabricate, or self-authorize a send. Grounded in
research into secure self-hosted agents (a kernel/userspace split) and
self-modifying-agent precedents, which converge on one conclusion: keep the
human-gated, no-auto-PR, protected-core design, and gate only the irreversible step.

### Added
- **`contribution/kernel-paths.txt`** (new) — the enforceable protected-core path
  list. A drafted contribution whose changed files intersect it is a **kernel edit →
  human-authored only**, never an agent-drafted send. Meta-immutable (the list is
  itself a kernel path).
- **`contribution/evals/evals.json`** — `kernel-edit-refused` (a draft that would
  weaken the privacy gate is refused as a kernel edit) and `injection-lesson-rejected`
  (a lesson that directs the process is treated as untrusted data).

### Changed
- **`contribution/SKILL.md`** + **`references/contribution-procedure.md`** → **1.1.0**:
  a kernel-vs-userspace protected core (immutable kernel: the scrub, the
  evaluator/thresholds, merge authority, the provenance ledger, the Definition of
  Done, and the kernel path-list itself); the **second-order kernel rule** (a
  self-improvement that changes how the scrub / evaluator / generality-gate *behaves*
  is human-authored only); **evaluator independence** (graded by the unmodified
  harness); the **lesson-is-untrusted-data** injection guard; a **mosaic-leakage**
  line in the provenance block; the "human-gated send, automate everything reversible
  before it" reframe; and an explicit scope extension to **agent prompts, skills, and
  orchestration** as drafts for human review. Anima-style decay/impact triage is
  admitted only as a *local* candidate filter, never an autonomous upstream writer.
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.34.0**;
  `contribution` → **1.1.0** (independent line). `SHA256SUMS` regenerated.

## [1.33.0] — 2026-09-11

Stage-aware review + a going-forward roadmap. `deep-code-review` now calibrates
its *demands* to the project's lifecycle stage (prototype / mvp / growth / mature)
and ends a FULL review with a stage-sequenced roadmap — what to do now, what to
defer, and which skillset to adopt going forward — so effort matches the stage
instead of over-engineering a prototype or under-hardening a live product. Stage
calibrates **urgency only**; it never rewrites a defect's severity and never
downgrades a security, secret, or data-loss finding.

### Added
- **`deep-code-review/SKILL.md`** — a `STAGE` field in the first-response block and
  a compact **Project stage** section: a four-stage table (what each stage relaxes
  the *demand* on) plus three guardrails — stage is declared or evidence-named
  (never guessed; unstated defaults to the stricter reading); security / secret /
  data-loss findings never relax; stage moves urgency, not intrinsic severity
  (reusing the latent-findings rule).
- **`deep-code-review/references/report-format.md`** — a **Going-forward roadmap**
  (machine + plain-language): sequences the findings already reported by
  stage-urgency, points at `install.sh --recommend` for the skillset to adopt (no
  restating), and adds ≤ 3 evidence-grounded development moves — anything needing
  business context the repo cannot evidence is routed to *Decisions needed (owner)*,
  not invented.

### Changed
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.33.0**;
  independent skills unchanged. Definition of done (a) now requires a FULL review to
  state `STAGE` and produce the going-forward roadmap. `SHA256SUMS` regenerated.

## [1.32.0] — 2026-09-11

New review lens: **agent-readiness**. A first-class way to assess whether a repo
or product is architected, tested, gated, documented, and permissioned for
coding agents to work in it safely — the thesis-fit, evidence-grounded form of an
"AI-transformation" review. It is a lens over existing domains (C, J, K, M, N, F,
O, H), not a new domain or a new skill, and it deliberately **stops at the
technical substrate**: it never advises which product to build, how to reorganize,
or what business metric to set (that would require inputs the repo does not
contain and would violate the evidence and no-fabrication principles).

### Added
- **`deep-code-review/references/role-coverage.md`** — an **Agent-readiness
  lens**: a role-map row (leads on C J K M N F O H) and a lens section whose spine
  is the boundary between reviewable technical substrate (agent-safe scoping,
  agent-verifiability, gating, observability, legibility — all from existing
  domains) and business/strategy questions, which are routed to *Decisions needed
  (owner)*. Deliverable is the standard severity-ranked `file:line` report plus a
  short agent-readiness summary — never a strategy deck.
- **`deep-code-review/SKILL.md`** — the compact role table gains the matching
  `Agent-readiness` row so the map and its depth stay consistent.

### Fixed
- **`contribution/SKILL.md`** — corrected the procedure ordering so the mechanical
  privacy scrub runs on the **drafted files** (draft in step 3, then scrub in step
  4), not before drafting; the previous numbering could be read as scanning an
  undrafted checkout, making the "mechanical floor" vacuous. `contribution` → **1.0.1**.

### Changed
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest →
  **1.32.0**; `communication-structure` (1.1.0) unchanged; `contribution` → **1.0.1**
  (fix above). `SHA256SUMS` regenerated.

## [1.31.0] — 2026-09-11

New opt-in overlay `contribution`: prepare a privacy-safe, generalized
improvement back to the public skillset for a human to review and open as a PR.
This is the self-improvement capability the owner asked for — a skillset that
gets better from field use — built with the safety shape the design work
required rather than an autonomous push.

### Added
- **`.claude/skills/contribution/`** (new; independent line at **1.0.0**) — an
  opt-in overlay that turns a generalizable, scrubbed lesson into a drafted skill
  edit + CHANGELOG + eval + routing, runs the repo's own gates, and assembles a
  **provenance-and-risk block** a human signs before the PR. One routed reference
  (`references/contribution-procedure.md`) and three evals
  (`third-party-identifier-blocked`, `non-generalizable-imprint-locally`,
  `no-autonomous-push`). Guardrails: a hard **generality gate** (contribute only a
  defect-class or method-gap the bar lacks and that reproduces beyond one project —
  otherwise imprint locally via `deep-code-review` Phase 6); reuse of the repo's
  existing **fail-closed privacy gate** as the mechanical floor, with the human as
  the privacy authority for the semantic leaks a pattern scan cannot catch; a
  **protected core** (tests, privacy gate, and merge authority immutable to the
  agent) so a self-improvement loop cannot game its own evaluator; and **no
  autonomous push or PR** to the public repository.
- **`install.sh`** — `--with-contribution` flag (deliberately **not** part of
  `--full`, since it is the one overlay whose function is moving content toward a
  public destination); usage, header, AGENTS.md overlay stamp, and re-install
  line updated. Default install stays review-only; the new skill is off unless
  explicitly requested.

### Changed
- **`agentic-delivery/SKILL.md`** — G10 gains a one-line discovery pointer: when
  the `contribution` overlay is installed, it is the mechanism for proposing the
  generalized, stripped lesson back to the public skillset (the
  generalize-and-strip mandate itself is unchanged).
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest →
  **1.31.0**; `communication-structure` stays **1.1.0** (unchanged this release);
  `contribution` starts at **1.0.0** on its own independent line. `SHA256SUMS`
  regenerated over the five skill trees.
- **`README.md`**, **`CONTRIBUTING.md`**, **`CLAUDE.md`** — document the new
  overlay, its install flag, and its routing-gate line.

## [1.30.0] — 2026-09-11

Selective adoption from an external "studio coordination" proposal, filtered by
this repo's own bar: security-cleared, thesis-fit, non-regressive, and cited only
to sources verified this session (no new citations were needed). The proposal's
product pivot (a brand/marketing "studio OS") and its rewrite of the delivery
overlay were **declined** — the rewrite would have deleted runnable detection
instruments and added a standing-authorization carve-out that conflicts with the
confirm-before-action rule. Every existing instrument is preserved; only
additions and internal-consistency fixes land.

### Added
- **`agentic-delivery/references/host-enforcement.md`** (new) — a claimed-vs-enforced
  honesty framework: three levels (protocol / validated-artifact / host-enforced),
  each with what it *cannot* establish, a per-control capability declaration, and an
  optional adapter interface. Routed from `SKILL.md`.
- **`agentic-delivery/references/project-state.md`** (new) — a durable project-record
  contract, a resume / crash-after-effect reconciliation protocol (an interrupted
  effect with an unknown result is not presumed failed; an uncertain side effect is
  not replayed), and a non-code artifact-receipt contract that *extends*, not
  restates, the SKILL.md Output contract. Routed from `SKILL.md`.
- **`deep-code-review/references/model-tiering.md`** — a "did the tiering work?"
  cost-accounting section (model / usage / price / budget / outcome tracking; cost per
  *accepted* task with failures in the numerator), added **alongside** — not
  replacing — the existing optimization levers.
- **`idea-critic/SKILL.md`** — a "test the claim before assent" reframe (a sound plan
  may pass once a real failure hypothesis was tried and held; automatic disagreement
  is as performative as automatic agreement), an `UNVERIFIED` operational status
  *outside* the verdict enum (review-could-not-run is not a rejection), a two-recheck
  cap on `REVISE`, an "independence is a declaration" note, and an anti-rationalization
  row against a proposal that games its own evaluator.
- **`agentic-delivery/evals/evals.json`** — four scenarios pinning shipped instruments:
  crash-after-external-effect, goal-change-invalidates-work, fabricated-or-stale-receipt,
  g6-severity-and-permission.

### Changed
- **`agentic-delivery/SKILL.md`** — G6 now applies the `deep-code-review` severity
  rubric verbatim (Blocker/Critical block, High needs a named owner's acceptance,
  Medium tracked and non-blocking), resolving a contradiction where G6 blocked on
  Medium; principle 3 reworded so a check that "could not run" is `UNVERIFIED` (never a
  fake pass) and evidence is separated from permission. The same wording is aligned in
  `references/roles.md` and `references/fast-agentic-delivery.md`.
- **`communication-structure/SKILL.md`** — cut reflexive hedges but **keep material
  uncertainty** ("the log is unavailable" is evidence, not filler); the A/B decision
  template is retained.
- Lockstep `VERSION` files, `SKILL.md` stamps, and the plugin manifest → **1.30.0**;
  `communication-structure` → **1.1.0** (independent line); `SHA256SUMS` regenerated.

### Declined (from the external patch, with reason)
- The `studio-capabilities` specialist packs (brand/marketing/commercial), the "CEO
  mandate" Conductor reframe, and the install-trigger `description` rewrite — a
  different product (agency OS), not a portable code-review bar.
- A Human-gates "standing authorization — do not ask again" carve-out — conflicts with
  the confirm-before-destructive/irreversible non-negotiable.
- The rewrite's deletion of runnable instruments (behavioural drift tell, fan-out tiers
  + the Cemri failure-mode mapping, the RAM/swap headroom probe, the seven cost levers,
  the A/B ask template) — all kept.
- 19 new `standards-index` rows and the promotion of NIST SSDF / AI RMF / SLSA from
  by-name to verified — not verified by direct fetch this session.
- The size-enforcement CI cap and the idea-critic validator/test-suite tightening —
  coupled to the rejected rewrite or to coordinated fixture changes; deferred to a
  separate, self-contained change rather than risk the gate.

## [1.29.0] — 2026-09-10

Tier 2–3 of the same prime-agent-informed batch: supply-chain and CI/CD
detection instruments, a dependency release-age cooldown control, six eval
fixtures, and two repo-hygiene items. Additive; the method and the default
(review-only) install are unchanged. Two Tier-3 items were found **already
implemented** during the work and are recorded, not re-added (see Note).

### Added
- **`deep-code-review/references/security-appsec.md`** — A03 gains CI/CD
  trigger-and-token hygiene (`pull_request_target` untrusted checkout,
  `${{ github.event.* }}` script injection, least-privilege
  `GITHUB_TOKEN` / `permissions`) and a verification-vs-authenticity instrument:
  a same-origin checksum is integrity, not authenticity, and does not neutralize
  the trust-on-first-use risk of a `curl | sh` install; severity keys on
  reachability. Cited to GitHub's Security-hardening guide.
- **`deep-code-review/references/security-agent-skills.md`** — AST02 gains the
  integrity-vs-authenticity grade, downloaded-manifest path-traversal
  validation, and a pointer that CI workflow files are executable config
  reviewed under A03; AST03 gains installer over-privilege beyond identity files
  (shell-rc append, global `npm i -g`, `PATH` export).
- **`deep-code-review/references/dependency-currency-and-upgrades.md`** — a
  release-age cooldown control (refuse to resolve a version until it has been
  public N days; Renovate `minimumReleaseAge`, security advisories exempt) plus
  a matching red flag. Cited to Renovate's docs.
- **`deep-code-review/evals/evals.json`** — six fixtures pinning the new
  instruments (interpreter-is-the-exec-sink, silent safety-param drop,
  process-group-is-not-isolation, installer over-privilege, cost-vs-token cap,
  inconsistent untrusted-content spotlighting).
- **`.gitattributes`** — normalize text to LF and keep shipped `*.sh` LF so the
  installer runs identically on every checkout.
- **`.github/workflows/ci.yml`** — the `name:`-matches-directory check now runs
  on every shipped skill, not only `deep-code-review`.

### Changed
- The three lockstep skill `VERSION` files, their `SKILL.md` stamps, and the
  plugin manifest follow **1.29.0**; `SHA256SUMS` regenerated.
  `communication-structure` remains at 1.0.0.

### Note
- "Run `install.sh` end-to-end in CI" and "sort `SHA256SUMS` entries" were found
  **already implemented** and were not re-added: `scripts/test-ci-gates.sh`
  already drives the real installer (`ci-gates.sh install --src .`) across modes
  with an idempotent-second-run assertion, and `scripts/write-checksums.sh`
  already sorts its entries.

## [1.28.0] — 2026-09-10

Five agent/LLM review-instrument sharpenings for domain C, found by routing the
skill's own `agent / LLM` archetype path against a production agent runtime and
recording where a reference stated a rule but handed the reviewer nothing to
run. Additive; no change to the method, scope modes, or the default
(review-only) install.

### Added
- **`deep-code-review/references/security-ai-agents.md`** — the "untrusted
  content is data" principle gains a detection step (enumerate every sink where
  non-prompt content enters a prompt; require a delimiter + a data-guard at
  each; **inconsistent** spotlighting is itself the finding) and a reframe for
  code-interpreter agents, where "model output reaches `exec`" is the product —
  so the controls to review are the isolation boundary and the default
  confirmation gate, not the exec call. Tool-gating now locates the dispatch
  chokepoint and separates a shipped default from an opt-in `examples/` demo;
  a human-confirmation gate must fail **closed** when no interactive UI exists.
  Spend governance gains the **cost ≠ tokens** and **before ≠ after** (pre-call
  vs post-hoc reconciliation) tests plus a `while (true)` loop-bound check.
  Matching `🚩 grep` keys throughout.
- **`deep-code-review/references/security-agent-skills.md`** — AST06 gains an
  isolation-grading instrument: grep the exec runtime for `subprocess` /
  `Popen` / `spawn`, check each spawn for a real boundary (namespaces, seccomp,
  netns, uid-drop, chroot, a container), and treat `start_new_session` /
  process groups / Job-Objects as lifecycle control, not a security boundary; an
  opt-in `examples/` sandbox or gate that is not loaded by default is not an
  enforced control. Matching `🚩 grep` keys.

### Changed
- The three lockstep skill `VERSION` files, their `SKILL.md` stamps, and the
  plugin manifest follow **1.28.0**; `SHA256SUMS` regenerated for the changed
  skill trees. (`communication-structure` remains at 1.0.0.)

## [1.27.0] — 2026-09-10

Two field lessons for the delivery overlay and the product-UX review half, each
a completeness fix to an existing rule rather than a new one. No change to the
review method or the default (review-only) install.

### Added
- **`agentic-delivery/SKILL.md`** — the Conductor operating rhythm gains a
  *drift-detection and recovery* step: the event-driven "does not do the lane's
  work itself" rule stated **behaviourally** (a run of consecutive
  query/build/edit/mutate turns is the tell), with a stop → package → dispatch →
  resume recovery and one named exception (work only the Conductor's own session
  can perform, done minimally and handed straight back). Applies the existing
  event-driven discipline to *action*, not only attention.
- **`agentic-delivery/SKILL.md`** — Gate epistemology principle 11:
  "visible/done" is measured on the owner's own surface, never a proxy (an
  integrated SHA, a green branch build, a passing test, an insert/grep count);
  keeps wired/defined/rendered distinct from has-a-real-value. Ties to
  principle 3's `UNVERIFIED` and the G9 production-verify gate.
- **`deep-code-review/references/product-ux-quality.md`** — a redesign-trigger
  section complementing "not a licence to redesign": the owner's *repeated*
  rejection (2+ times) of the same element is a structural signal to stop tuning,
  name the flaw, research two or three comparable products, and surface concrete
  options for the owner to choose (show, don't tell). Reconciled with principle 5
  and grounded in principle 9.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin manifest
  follow **1.27.0**.

## [1.26.0] — 2026-09-09

New reference `skill-authoring-and-size.md` (domain H): a portable rule for
keeping agent skills lean as they accrete lessons — a thin always-loaded
`SKILL.md` core + a routed index, depth in on-demand `references/`, two budgets
(body tokens on invocation, `description` chars always-loaded, ≤1024 by spec), a
reasoned allowlist (allowed-not-required), and a size ratchet that FAILS on bloat
with a self-test that proves it fires. Routed from the domain map (H) and a
"skills as targets" pointer. CI `--max-bytes` stays 100000 (still a warning);
tightening to 24000 and making it FAIL need a follow-up with `workflow` scope.
No behaviour change to the review method.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin
  manifest follow **1.26.0**.

## [1.25.0] — 2026-09-09

Concurrency, scheduling, and merge-cadence cut for `agentic-delivery`. Default
install stays review-only.

### Added
- **`agentic-delivery/references/fast-agentic-delivery.md`**: five field-tested
  refinements — a corrected resource-gate signal (free RAM + swap trend, not
  `load1` alone, which conflates disk I/O with CPU contention), CI-offload as
  the actual concurrency unlock (lane weight over lane count), sweeping the
  whole ready queue on every Conductor trigger, a fleet-wide external-advisory
  gate-epistemology case, and reconciling an independent-PR-queue merge
  cascade with the existing union-proof-before-a-train rule. Five sources
  fetched and cited (Kanban WIP limits, Google small-CLs, blast radius,
  GitLab merge trains, Linux load-average mechanics). Routed from three spots
  in `SKILL.md` (environment probe, Conductor operating rhythm, gate
  epistemology).

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the plugin
  manifest follow **1.25.0**.

## [1.24.0] — 2026-09-08

Cost-governance leftover from colliding PR #13, restamped onto
current main so it does not reuse shipped 1.22.0 / 1.23.0.

### Added
- **`model-tiering.md`**: default-and-ceiling callout — cheapest tier
  that clears its own gate; state a reason before exceeding frontier
  except lead-verify / adversarial-design.
- **`agentic-delivery` environment probe**: composite resource
  predicate (free RAM >15% AND load1 < cores × 1.3 AND CPU idle >25%,
  plus macOS swap check). Throttle when any one trips.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.24.0**.

## [1.23.0] — 2026-09-08

Discipline and compatibility cut. Mechanisms, not packs. Default
install stays review-only.

### Added
- Anti-rationalization (excuse → rebuttal) tables in `idea-critic`
  and `agentic-delivery` G4/G5.
- Headed-browser evidence as a **required** G5 / domain P receipt
  when a rendered page can change. Unit tests alone are not a UI gate.
- Spec Kit constitution *compat*: if `.specify/` or `constitution.md`
  exists, review against it. Do not install Spec Kit.
  `--recommend` prints that notice.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.23.0**.

## [1.22.0] — 2026-09-08

Distribution and fixture-eval cut. Default install stays review-only.
Does not claim OpenSSF Model Signing.

### Added
- `evals/evals.json` on each of the three skills (fixture contract:
  planted defect must be reported; `--recommend` must not write;
  owner-request cannot HOLD). Wired into `scripts/test-ci-gates.sh`.
- `SHA256SUMS` of the three skill trees and `scripts/write-checksums.sh`.
  CI compares the committed file to a fresh regeneration.
- `SECURITY.md` — pin by release tag, refuse unsigned HEAD, honest
  signing gap.

### Changed
- README documents `git clone --branch vX.Y.Z` and
  `npx skills add remigiusz-antczak/deep-code-review#vX.Y.Z` next to
  `install.sh`, with an AST07 warning against floating HEAD.
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.22.0**.

## [1.21.0] — 2026-09-08

Orchestration lessons unique to the leftover PR #11 branch, restamped
onto current main so they do not collide with shipped 1.20.0. Additive
on 1.20.0 — the review bar's six phases, domains A–S, the gate table,
and the report shape are unchanged. Two items checked against 1.19.0
were already present (robust shell list-membership; worktree-per-lane
preflight) and are not duplicated.

### Added
- **`agentic-delivery/SKILL.md`**: "Environment probe (before you size
  anything)" (probe RAM/CPU/disk and usable tool/connector auth; decide
  heavy-lane count, model tier, and local-vs-CI from the probe, not
  habit); a general-lane context-inheriting-fork rule (a fork carries
  every prior instruction, not only the newest one — fresh unit for
  narrow work, or an explicit prohibition plus a check of what the unit
  actually called); a lane's own scope ends at its own green PR, not at
  the merge; Gate epistemology principle 9 (closing/deleting shared
  state needs evidence, not presumption); G7-vs-G8 clarification (a
  work item is done at integration; release/deploy is later and
  owner-gated); principle 3 gains a concrete triage step (identify the
  failing job **and step**, rerun a suspected flake, before reverting).
- **`deep-code-review/references/parallel-audit.md`** §2: tree-diff is
  blind outside the tree (issue/comment/message); verify a prompt-level
  strip actually held from the unit's tool calls, not its summary.
- **`deep-code-review/references/branch-and-merge-hygiene.md`** §1:
  truncated forge listing — `gh issue list`/`gh pr list` default page
  is 30; count with `--limit` or paginate.
- **`deep-code-review/references/product-ux-quality.md`**: reviewable
  who/what/when change history behind any decision-of-record edit, and
  agent/model-authored values stamped as such at write time.

### Changed
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the
  plugin manifest follow **1.21.0**.
- README missing-space nit after the personal-install sentence.

## [1.20.0] — 2026-09-08

Closes the remaining 1.19.0 self-review backlog after 1.19.1 landed
the byte-exact VERSION gate (F2/F8).

Domain C now walks OWASP LLM Top 10 **2026** titles quoted from
`OWASP-GenAI-LLM-Top-10-2026-v1.0.pdf` (fetched 2026-09-08). 2025 IDs
remain only as a compatibility map. New reference
`security-agent-skills.md` walks OWASP Agentic Skills Top 10
AST01–AST10 against both skill-consuming targets and this repo's
`install.sh` / VERSION / SHA stamp.

Repo dogfood that is settings-not-code (F3/F6/F7) is applied on the
GitHub repo itself: `delete_branch_on_merge`, secret scanning + push
protection, Dependabot security updates, tag `v1.19.1`. This commit
adds Dependabot version updates for GitHub Actions, an issue-template
`config.yml` so GitHub indexes the templates (F5), a PR-template gate
list that matches CONTRIBUTING (F10), and the idea-critic description
trigger `Use when` (F9). Required-review branch protection is still
off so a same-owner merge is not trapped.

### Added
- `.claude/skills/deep-code-review/references/security-agent-skills.md`
  (AST01–AST10), routed from `SKILL.md`.
- `.github/dependabot.yml` for `github-actions`.
- `.github/ISSUE_TEMPLATE/config.yml`.

### Changed
- Domain C / `security-ai-agents.md` walks LLM01–LLM10:**2026**.
- Overlay `VERSION` files, the three `SKILL.md` stamps, and the
  plugin manifest follow **1.20.0**.
- PR template mirrors CONTRIBUTING's pre-PR gate block.
- idea-critic description starts `Use when`.

## [1.19.1] — 2026-09-08

Patch on 1.19.0. The VERSION provenance gate no longer strips
whitespace before matching, and it no longer accepts a matching heading
anywhere in CHANGELOG.md. VERSION must be byte-exact ASCII core SemVer
(`MAJOR.MINOR.PATCH`, no leading zeros in a multi-digit part) with at
most one optional terminal LF. The first `## ` heading in CHANGELOG.md
must announce that version.

Closes the fail-open that accepted a planted `  1.19.0  ` file, and the
stale-ordering hole where an older first heading still passed if a later
heading matched. Ports the unpushed local `d104e72` contract onto main
and adds the planted whitespace / NUL / first-heading cases to
`scripts/test-ci-gates.sh`.

### Changed
- `scripts/ci-gates.sh` `version`: hex-validate raw VERSION bytes, then
  require the first CHANGELOG release heading to announce it.
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the
  plugin manifest follow **1.19.1**.

### Tests
- Eight new version-gate cases: leading-zero major, NUL, embedded
  whitespace, multiline, leading whitespace, stale first heading
  (reject); exact `1.13.0` with trailing LF, and no trailing LF (accept).

## [1.19.0] — 2026-09-08

A hardening pass on top of 1.18.0's software-house roles, from four research
streams: closing this skill's own spend-cap gap, filling the domain-K release-
engineering gap and the one-line G10 retrospective, hardening `idea-critic`
past a same-brain "independent" verdict, and six portable lessons drawn from
one AI-agent-maintained project's own operational history (scrubbed of every
project-specific detail — generic principles and fictional examples only).
Additive on 1.18.0 — the review bar's six phases, domains A–S, gate table, and
report shape are unchanged. Four candidate detectors from that lessons pass
(duplicated-UI-concept drift, write-only inputs, render-trace-before-edit,
UI-changing diffs needing visual proof) were found **already shipped** in
1.18.0's `product-ux-quality.md` and `parallel-audit.md` §5 during
verification against this branch — not re-added; see the PR body for the full
staleness note. Grounded in the sources logged in `docs/standards-index.md`'s
three new 2026-09-08 sections.

### Added
- **`references/model-tiering.md`** (domain E): three vendor-neutral model
  tiers, the cost/quality levers in the order the evidence favors reaching for
  them (effort tuning, prompt caching, batching, escalate-on-failure, budgets,
  bounded advisor consults, model swap last), two negative results (don't fan
  out on a single dependent chain; don't over-consult an advisor), and the
  mapping onto this skill's own fan-out tiers and delivery hats.
- **`references/release-engineering.md`** (domain K, the release half
  `dependency-currency-and-upgrades.md` never covered): feature-flag
  category/lifetime checklist, canary/blue-green claims checked against actual
  router/traffic-split config, DORA-or-`UNMEASURED`. Paired with a **Release**
  depth section in `agentic-delivery/references/roles.md`.
- **`agentic-delivery/references/retrospective.md`** + **`template-
  postmortem.md`** (routed from G10): blameless principle, mandatory-trigger
  criteria (not every bug fix), action-item-closure gate, repeat-root-cause
  check against prior postmortems.
- **`agentic-delivery/references/template-adr.md`** (routed from G3): Nygard's
  five-part shape + MADR's optional sections, giving G3's existing "ADRs /
  contracts" requirement an actual shape.
- **"Conductor operating rhythm"** subsection in `agentic-delivery/SKILL.md`:
  event-driven attention (not polled), fan-out sized to decomposition (not
  concurrency), pilot before full width, escalate-a-lane-don't-just-retry-it,
  and an empirical failure-taxonomy callout (Cemri et al., MAST) mapping onto
  the existing gate shape.
- **`idea-critic`**: verdict schema gains `steelman` (attack the strongest
  defensible reading of the claim) and `strongest_attack_survived` (the
  sharpest objection actually tried, and why it failed — required and
  non-generic on `PASS_TO_USER`), both enforced by `validate_verdict.py`; a
  premortem clause on the `kill-criteria` hat; Independence now tiers
  decorrelation strength (a different model family is stronger than a
  different context alone); a new "false-closure REVISE" pitfall.
- Six portable-lesson closes verified absent from this branch before being
  added: `role-coverage.md` (success-metric-to-emitted-event loop closure +
  the missing SRE-workbook burn-rate citation), `testing-and-evals.md`
  (stated Test-Pyramid-vs-Testing-Trophy philosophy required), `frontend-
  a11y.md` (URL-backed drawer/filter state), `infra-iac-containers.md` (a
  green health check is not proof of an out-of-band post-deploy data
  dependency), `docs-and-dx.md` (dated status/handoff doc proliferation),
  `concurrency-shared-state.md` (worktree-per-lane + spawn-time duplicate-work
  preflight).
- `branch-and-merge-hygiene.md`: stacked-PR-safe branch deletion, generated-
  file merge-conflict resolution (regenerate, never hand-splice), a new
  "Merge trains" subsection (verify the union once, merge members
  individually, sequence a gate-adding PR last), a combined safety-rail bullet
  on gating an irreversible command on a preflight's documented pass condition
  paired with a robust-shell-list-membership lesson (`for x in $LIST` on an
  unquoted variable silently stops excluding anything under a non-word-
  splitting shell; use a literal `case` or `grep -qxF` instead), and a §8
  spike/prototype branch-naming convention. A matching grep-flag row in
  `language-stack-redflags.md`'s Shell/Bash section.
- Three operating-discipline sentences with no code detector: principle 5 (a
  previously and explicitly made design choice is treated as a stated style
  guide — propose against it, never silently revert it); the Confirm bullet
  (a tentative/question-phrased message is a request for assessment, not
  authorization); `report-format.md`'s mechanism-unproven-fix language now
  extends to status reporting generally (running ≠ fixed).
- `docs/standards-index.md`: three new 2026-09-08 sections logging every
  source above with fetch dates and, per the file's own convention, what each
  fetch did **not** confirm (DORA's single-source caveat, the MAST paper's
  14-mode taxonomy not independently enumerated, Panickssery et al. tested on
  GPT-4/Llama 2 not Claude, and others).

### Changed
- `parallel-audit.md`: the shared fan-out context packet is flagged cacheable;
  a don't-start threshold complements the existing stop rule (don't fan out on
  one dependent chain or a single-context target); the Tier-1→Tier-2 sweep now
  tiers by model capability, not only effort; a new addendum distinguishes a
  concurrency-capacity flake from a genuine defect.
- `agentic-delivery/SKILL.md` G2 now requires a per-lane token/dollar budget
  before G4 starts (no budget = blocked, not unlimited) — closes a
  self-referential gap between this skill's own LLM10/`spend-cap` invariants
  (enforced on every *target*) and its own gate table (which enforced neither
  on itself). G0 now names an explicit appetite (a time-box, not an estimate).
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the plugin
  manifest follow **1.19.0**.

## [1.18.0] — 2026-09-08

The delivery overlay becomes a **software-house in a repo**: the full role roster
as hats (not standing bots), a first-class **Product Analyst** role, a hardened
adversary, the orchestration discipline that keeps parallel lanes from thrashing,
and the product-UX **interaction-completeness** bar. Additive on 1.17.0 — the six
review phases, domains **A–S**, the severity rubric, and the report shape are
unchanged; the review side gains one product-UX section and one fan-out
discriminator, the delivery overlay gains one routed reference, and the CI routing
gate now also covers the overlays. Grounded in five directly-fetched sources
(Anthropic *Building Effective AI Agents*; Claude Code Subagents; Anthropic Agent
Skills; MetaGPT; ChatDev) logged in `docs/standards-index.md`.

### Added
- **`agentic-delivery/references/roles.md`** (routed from that skill's `SKILL.md`):
  the software-house role roster as **hats, not headcount** — Conductor, Product
  Analyst, Architect, Implementer, Evil Twin, QA, Security, UX & Design, Release,
  Docs — each mapped to when it fires, the gate it owns (G0–G10), and the
  `deep-code-review` review lens it corresponds to. Depth only for the three roles
  the review-side `role-coverage.md` does **not** hold (Product Analyst,
  Evil-Twin-as-hat, Implementer); one-line pointers for the rest, to avoid
  restating the review overlay. Includes the two-tier **gates a software-house
  repo runs** table (commit-time: privacy/format/lint/type/unit+count; CI:
  build+E2E-at-SHA / verify-visible-UX / ux-evidence / dependency) with the repo's
  own gate epistemology (tell can't-check from found-a-problem; fail open on the
  former; provable-red on a planted defect; never stricter than the standard).
- **Product Analyst** hat in `agentic-delivery` (Operating model + G0/G1): turns a
  real signal into a testable spec, enforces **interaction-completeness**,
  benchmarks solved elements against **named** comparable products, and maintains
  a **feedback-coverage map** (each item → scoped → verified / deferred) — the
  product analogue of the review's coverage ledger.
- **Interaction-completeness + unified-UX** section in
  `references/product-ux-quality.md` (domain P): one **shared component per
  concept** (reuse/extend, never reimplement per page; a fix lands in the shared
  component, not one caller), **no write-only inputs** (read-back required),
  **WYSIWYG** (store markup, render it — never show raw `**`/`<u>` tokens), and
  fix-the-surface-that-renders — with new grep 🚩 rows and two pre-ship checklist
  items.
- **Render-surface discriminator** in `references/parallel-audit.md` §5: a grep
  match is a *candidate*, not a live site — trace route → component (UI) or the
  call graph (code path) before a finding or a fix names a `file:line` as the live
  surface; a fix aimed at a grep hit the target never runs is wasted work that
  leaves the real surface broken.
- `docs/standards-index.md`: a **2026-09-08** verified-by-direct-fetch section for
  the five sources above, each row stating what the fetch did and did **not**
  confirm (the arXiv abstracts do not enumerate specific role titles verbatim).

### Changed
- **`idea-critic`** hardened into a "proper evil twin": a **default-to-dissent**
  prime directive (with the reflexive-praise trigger), **attack before
  substantive work** (not after), and **verify-your-own-objection — the critic is
  a lead, not an oracle** (check a pushback's premise against current verified
  state; a critic that blocks good work with a stale fact is a false negative).
- **`agentic-delivery` orchestration discipline**: *Worktrees and occupancy* now
  states that a subagent/fork mechanism does **not** necessarily isolate the tree
  (assume shared until proven; branch/index/deps are per-tree), requires cleaning
  the base before launching and a **preflight** (running workers, `git worktree
  list`, open PRs) before spawning any lane; *Failure* adds **a running lane is
  not a finished one** (report what runs; report done only when verified).
- **`recommend-overlays.py`** now inspects the target for the quality gates it
  already has (CI, lint, format, tests, pre-commit, privacy — filename-level,
  reporting "not detected", never "absent") and frames the pack as the
  software-house roles + the gates the imprint would add. It also detects a
  **live custom delivery pack**: a skill under a real host skill root
  (`.claude/skills/` and peers — not a `docs/` archive) whose path, frontmatter
  `name`, or a small `SKILL.md` prefix names a delivery OS. Named packs already
  counted; a private factory, a software-house-pattern skill, or an
  already-installed `agentic-delivery` overlay previously still received
  `--with-delivery` / `--full`. Detection is review-negative (`deep-code-review`
  and `idea-critic` never count), skips non-regular files and `SKILL.md`
  symlinks (a FIFO would hang `open()`; a symlink can point outside the
  target), and stays bounded — one level under each known skill root, reading
  only a prefix, failing closed on any single unreadable file.
- **CI + CONTRIBUTING**: the `routing` gate runs on **all three** skill dirs
  (`deep-code-review`, `agentic-delivery`, `idea-critic`), so a new overlay
  reference cannot ship unrouted — the repo dogfoods its own "documented but
  unenforced is a finding" rule.
- Overlay `VERSION` files, the three `SKILL.md` version stamps, and the plugin
  manifest follow **1.18.0**. README gains a *software-house overlay* section and
  refreshed counts.

## [1.17.0] — 2026-09-08

Dogfood of 1.15.0/1.16.0 against two external product repositories plus the
Agent Skills spec. Three defects in the bar itself, not in those products: `--recommend` treated archived Superpowers
notes as a live delivery OS; kit-leftover `AGENTS.md` was not a named DX
defect; delivery never required a running local stack. Anti-slop is now an
explicit Phase-4 filter so a review of a well-gated product does not emit
community-health noise.

### Added
- **Anti-slop** in `references/method.md` Phase 4: drop findings that would
  not change a merge or a ship. Kit leftover (`AGENTS.md` still describing
  scaffold `app/` while the product lives in `apps/` / `packages/`) is **one**
  DX finding, not a docs wall.
- **Kit leftover vs product tree** and **local environment is DX** in
  `references/docs-and-dx.md`.
- **Local environment (own it)** in `agentic-delivery`: discover the project's
  one-command / compose / devcontainer, bring it up, verify against the
  running process (`verify:served` when present), tear down. G5 is
  `UNVERIFIED` if the stack never started.
- `idea-critic` pitfall: `HOLD` slop recs (extra docs, restyle, second
  delivery OS) unless a named defect requires them.

### Changed
- `--recommend` only treats a delivery pack as live when a skill path exists
  (`.claude/skills/superpowers/SKILL.md` and peers) or a marker directory sits
  outside `docs/` / `archive` / `history` / `code-review` / `notes`. Historical
  Superpowers plans under `docs/` no longer suppress `agentic-delivery`.
- Overlay `VERSION` files and plugin manifest follow 1.17.0.

## [1.16.0] — 2026-09-08

A **product-UX quality** reference under domain **P** — the *design half* of a
frontend review (whether a UI feels **at-home**: conventional, self-evident,
correct in every data state, cleanly encoded), complementing the a11y-correctness
half `frontend-a11y.md` already owns. Additive on 1.15.0: the six phases, domains
**A–S**, the severity rubric, and the report shape are unchanged; domain P gains
a second reference (routed by a "read it when…" trigger) and the web archetype
must-load set. No new URL, version, or date is cited — the design half grounds
in WCAG 2.2 (already tracked), Nielsen's usability heuristics (named, not
URL-cited), and the public precedent of top products.

### Added
- **`references/product-ux-quality.md`** (routed from domain P): the "at-home"
  design bar — **every data state ruled on** (empty/loading/error/partial/
  overflow), **one-visual-channel-per-dimension** encoding hygiene,
  **never-colour-alone** (the greyscale test), the **metric/KPI delta standard**
  (caret + magnitude, colour by *sentiment* not direction), **self-evident-over-
  explained** (progressive disclosure; legends collapsed, glyph-grid not prose),
  **drawers-overlay + no-dead-controls**, and a **named** top-product precedent
  per solved element. Opens with the reconciliation rule (read first): matching a
  convention is a review **observation** surfaced under "Decisions needed (owner)"
  with the minimal-visual-impact fix — **never a licence to redesign**. Closes
  with a **Phase-6 UX-evidence gate** that fails open on could-not-check.

### Changed
- `SKILL.md` domain **P** routes both `frontend-a11y.md` and
  `product-ux-quality.md`. Web archetype must-load includes the design half.
- README P-row names the design half; Nielsen's usability heuristics added to
  the by-name standards list.

## [1.15.0] — 2026-09-08

The review bar stays the default product. Optional overlays inject a
public-safe **gated delivery** pattern and a **pre-owner idea attack** into
a target repo. Spec compliance (Agent Skills description ≤1024 characters,
`SKILL.md` under 500 lines) unblocks every later install.

### Added
- **`agentic-delivery`** (opt-in) — G0–G10 gated delivery: smallest-sufficient
  hats, independent QA/security, one writer per worktree, exact-SHA receipts,
  human approval on push/merge/deploy. Names `deep-code-review` at G1/G6/G7.
  Public-safe distillation; no operator preferences, no private intake, no
  runtime names.
- **`idea-critic`** (opt-in) — three hats (skeptic, better-way, kill-criteria);
  verdict `HOLD | REVISE | PASS_TO_USER`; `owner-request` cannot HOLD.
  `scripts/validate_verdict.py` fail-closes on a missing key, an illegal
  HOLD, or a list-shaped `user_question`.
- **`./install.sh --recommend <project>`** — inspects the target and prints a
  pack. The agent may recommend `--full`; the owner decides. Another delivery
  pack already in the tree is a reason **not** to also install
  `agentic-delivery`.
- Install flags: `--with-delivery`, `--with-critic`, `--full`,
  `--with-extra-hosts` (Gemini, OpenCode, Copilot `.github/skills/`, Windsurf,
  Hermes, Kiro).
- `.claude-plugin/plugin.json` so `/plugin marketplace add` works.
- Community health: `CODE_OF_CONDUCT.md`, issue templates, PR template.
- `references/method.md`, `domain-checklists.md`, `report-format.md` — method
  depth moved out of `SKILL.md` (progressive disclosure).

### Changed
- Default `./install.sh <project>` remains **review-only**. Delivery is never
  the default.
- `deep-code-review` `description` rewritten to ≤1024 characters, when-to-use
  in the first 57 characters.
- `SKILL.md` is the map (under 500 lines). Checklists, phase procedures, and
  report templates load on demand.
- `CONTRIBUTING.md` points at `scripts/test-ci-gates.sh` + `ci-gates.sh`.
- Chat voice is **not** vendored. Compressed assistant prose, if wanted, is
  a pointer to the public caveman skill repository. Persisted artifacts stay
  normal English.

### Not in this release
- No private operating-registry content, live values, or third-party
  identifiers.
- No default-on full pack.
- No caveman files copied into this tree.

## [1.13.0] — 2026-09-02

A role-aware **software-house overlay** over the existing method, plus the repo's
own gates re-homed into one fail-closed helper proven by a self-test harness.
Additive and smallest-sufficient — the six phases, domains **A–S**, the severity
rubric, and the report shape are unchanged; the overlay only orders and assigns
domains through a delivery-role or security-team lens, it never adds or drops one.

### Added
- **Role & team overlay** in `SKILL.md` + `references/role-coverage.md` (routed
  by path with a "read this when…" trigger): per-role leads-on domains for the
  nine delivery roles, driven through the same A–S method. Adds the lenses this
  file does not hold — **architecture quality** (seams, dependency direction,
  SPOFs, drift from the stated design), **lightweight product planning**
  (problem→acceptance, smallest slice, success metric), **SLI/SLO with error
  budget & burn-rate**, and **release-owner sign-off**.
- **Security-team colour model** (re-packages the same evidence by stance — no new
  rules; Red still needs `file:line`, Blue still fails closed): **Red** adversarial
  pass, **Blue** detection/fail-closed, **Purple** red→blue gate, **Yellow** build,
  **Green** (Yellow+Blue), **Orange** (Yellow+Red), **White** scope/ROE/owner
  decisions/sign-off.
- **Black Team — the agent boundary is absolute.** A physical / human-operations
  lens (intrusion, impersonation, social engineering, surveillance, badge/lock
  bypass, device placement) where an agent may **only plan, tabletop, and analyse
  owner-supplied evidence** — never perform or operationally direct any such action,
  and never test a real person or site. Real assessments are **human-led under
  written owner authorization and legal rules of engagement (ROE)**; a request that
  crosses the line has its operational part refused and its planning part kept.
- `scripts/ci-gates.sh` — one **fail-closed** production helper for the repo's
  documented gates (`privacy`, `routing`, `version`, `install`): no `|| true`, no
  always-success fallback, no pipeline that swallows the real exit status. Privacy
  reports matching **file names only, never content**, and fails closed on a
  missing, empty/comment-only, or malformed-ERE banlist while honouring an optional
  sibling `.banlist.local.txt`. Routing matches basenames **literally** (fixed-
  string) and flags dangling routes, with a non-failing size WARN.
- `scripts/test-ci-gates.sh` — a **16-case RED/GREEN self-test harness** pinning
  that helper's contract with real exit codes preserved: privacy (reject empty and
  all-comment banlists, detect a planted secret, reject an invalid ERE without
  disclosing banlist content, load the sibling local override), routing (reject
  unrouted, reject a regex-meta basename match, WARN on an oversized SKILL.md),
  version (reject malformed VERSION and a missing CHANGELOG heading), and install
  (overwrite a placeholder with the real vendored docs; **Claude**, **minimal**,
  **Codex**, and **full** agent-agnostic default modes; **Codex/full** assert the
  managed AGENTS.md block sentinels — `deep-code-review:begin`, `Installed:`,
  `Agent-agnostic` — and **full** re-installs to prove exactly one idempotent
  managed block, never a duplicate; collision-free backups on rapid repeated
  installs).

### Changed
- CI (`.github/workflows/ci.yml`) now runs the self-tests and then enforces the
  documented gates through that **same single helper** — one authoritative
  implementation, no inline copies, so the enforced check and its tests never
  diverge.
- `install.sh` backups are **portable and collision-free** — a seconds-resolution
  timestamp plus an existence-checked numeric suffix (avoiding `date +%N`, which is
  unsupported on BSD/macOS `date`), landing under `.../skill-backups/`, never inside
  `skills/`.
- **Confidentiality scoped first- vs third-party** (principle 11): a project's
  intended-public identity (published maintainer/author, public repo URL) is not a
  leak, while drift beyond that stated-public surface is the finding; softened the
  prose's unsupported scanner/breach claims to what the gate actually proves. The
  project's own `CLAUDE.md` confidentiality rule is aligned to the same scoping so
  the repo's governance and the skill it ships no longer disagree on first-party
  identity (the repo dogfoods its own gate: `.banlist.txt` bans secrets + generic
  patterns, real identifiers live in gitignored `.banlist.local.txt`).
- README reference-file count → **20**.

## [1.12.0] — 2026-09-01

Throughput-and-affirmation harvest from a FULL run against a large, hardened
production Node codebase: make the fan-out cheap on large targets, make the verify
step catch intended-behavior false positives, and make the review's value legible
on a target that yields few or no defects. Additive — phases, domains A–S, and the
report shape are unchanged; the report gains one co-equal affirmative section.

### Added
- `parallel-audit.md`: **two-tier sweep** — a cheap Tier-1 candidate enumeration
  before the high-effort Tier-2 confirm that runs only on survivors, so
  agent-minutes track candidate count, not domain size; plus small
  one-invariant units (a few hundred lines of owned surface) so no single finder
  stalls the pipeline under a small concurrency cap.
- **Verify against the tests, not only the source** (`parallel-audit.md` §4 +
  SKILL Phase 4): before `CONFIRMED`, read the tests that exercise the finding — a
  fix that contradicts a passing assertion is `REFUTED` as intended behavior — and,
  for a change to security/cost/concurrency logic, apply the fix in a throwaway
  worktree and run the suite. Re-reading the source the finder read cannot catch an
  intended-behavior false positive; only the tests encode intent.
- **"Invariants verified to hold"** as a first-class, co-equal report section
  (Phase 5 + report format + rules + definition of done) fed by a new
  `checked_sound` affirmative return in the fan-out contract — the primary
  deliverable on a hardened target, grounded `file:line`-or-drop like any finding.
- **Runtime-proven-gate lens** in domains B (home), C (tool-authz proven live), and
  F (subsystem proven to execute): is the gate measured at runtime (a
  self-proof/health check) and **fail-closed when the proof is absent**, or merely
  present in code? An unproven gate that reads as safe is itself the finding.
- **Failure direction as a severity axis** (rubric + Phase 4): fail-open (bypass /
  over-grant / leak) scales with blast radius; fail-closed (self-DoS / over-deny /
  conservative accounting) caps **Low** unless it enables a further exploit.
- Domain H: **duplicate-source-drift** probe — byte-identical lockstep copies
  (vendored, per-plane, generated-vs-source) need a parity test or single source;
  flag the missing guard, not the duplication.
- **Lead independent read of the top-N blast-radius files**, concurrent with the
  fan-out (`parallel-audit.md` §4 + Phase 2), so a zero-survivor run still has a
  non-empty confidence basis and no high-stakes surface goes unread.
- **Coverage attributed per unit** — finder id + lead-read, with a stalled/refused
  unit marked `unverified` rather than silently absorbed (Phase 0 ledger + Phase 5
  reconciliation + `parallel-audit.md` unit-manifest Lead-read column).

### Changed
- Example report version stamp 1.12.0; the example now shows the affirmative
  invariants ledger, a REFUTED-at-verify candidate (intended, test-encoded,
  fail-closed), and finder + lead-read coverage.

## [1.11.0] — 2026-08-21

Harvest from a same-owner inter-agent bridge review: name ASI01–ASI10, and
treat audience-mismatch plus committable-identifier leaks as first-class.

### Added
- ASI01–ASI10 titles (from the 2025-12-09 OWASP announcement, verified
  2026-08-21) in `references/security-ai-agents.md`.
- Same-owner vs many-audience probe under ASI07 (channel audience named;
  protocol keyed on tenant/uid, not a display name).
- Privacy: committable artifacts (PR/doc/fixture/commit) as a Q surface.
- Fan-out revision identity now fails closed on a missing or mistyped full SHA.
- Executable review units use separate worktrees and temp/port/process namespaces;
  aggregate suites serialize when that isolation is unavailable.
- Standards-index addendum 2026-08-21 (ASI titles; 2026 LLM Top 10 exists,
  titles unverified).

### Changed
- Domain C / adversarial pass / domain Q flags point at the new probes.

## [1.10.0] — 2026-08-21

Instrument/measurement discipline from three 2026-08-21 FULL/PR feedback runs —
the reviewer's own tools, not the code, were the dominant error source. Durable
invariants only; host-CI trimmed to one Phase-1 line + one report row (no new
first-response field), requirements-move ceremony left out.

### Added
- Principle 2: an absence needs a positive control; canonical instrument over
  proxy; read a platform-computed value from the platform (a gate reimplementing
  it is a finding); a project's enforcement is verified against the artifact, not
  the doc; self-review test blind spot.
- Phase 1: pipe/`$?`, SIGPIPE-141, `grep -q`, and `2>/dev/null` gate hazards
  (mechanics in `language-stack-redflags.md`); a tool count is a floor until caps
  are checked; gate-vs-standard (narrow ≠ weaken; WCAG 1.4.3 example); host-CI of
  the base branch.
- Phase 0: provision the worktree (never symlink deps; an env-shaped failure in a
  fresh worktree ≠ Blocker); read the revert *body* for its invariant.
- DIFF quick-path (consolidated) + ceremony-to-scope: ledger emitted at every
  scope, two-artifact report FULL-only, lighter `found → fix → re-gate` trail when
  reviewer = fixer.
- `mechanism-unproven` fix marker (Fix line + Phase 5 + definition-of-done).
- Domain G: singleton lifetime-vs-data bug class (leaks with perfect sync).
- Domain P 🚩: an a11y gate computing names from `innerText`; a presence-only name
  check.
- Ground-truth report row: `Host CI (base <ref>)`.
- `parallel-audit.md`: `REVERT_INVARIANTS` packet field; brief facts labelled
  `verified`/`to-be-verified` with premise verified before dispatch;
  `BRIEF_CONTRADICTION` as first-class output; symmetric re-verification; per-run
  diagnostic paths.
- `frontend-a11y.md`: cross-view consistency pass (WCAG 3.2.4 / 3.2.6) and the
  accessibility-tree-not-`innerText` rule.
- WCAG SC 1.4.3 / 3.2.4 / 3.2.6 verified by direct fetch (2026-08-21) in
  `docs/standards-index.md`.

### Changed
- Example report version stamp 1.10.0.

## [1.9.0] — 2026-08-19

Method honesty and detection depth from two FULL multi-model skill-feedback
runs — narrowed to durable invariants; host/model ceremony and duplicated
doctrine left out.

### Added
- SCOPE / packet field `BANNED_REMEDIES` (records Phase 0 revert/deletion scan).
- Principle 5: drift from a named stating artifact is the finding.
- Phase 2 named check: stated invariant / landed guard → bypass census
  (appsec untrusted-egress caller census; data-quality artifact→consumer).
- Config/runtime evidence rule: no severity on an unobserved branch.
- Planted-probe skip caps gate-self-test only (DoD wording).
- Parallel-audit: unit manifest, material dissent preservation, stop rule,
  named substitute in fan-out preamble.
- Soft-no-op persistence (empty artifact overwrite) in reliability + F map.
- Concurrency: corrupt→wipe ban; stale RMW across `await`.
- Data-quality: denominator integrity; absent/expected-empty/false/empty-list.
- Spend ledger: test present-fault branch (`EACCES`/`EISDIR`/invalid body).

### Changed
- Phase 5 BLUF: top defects + `Decisions: N` pointer; product/redesign never
  carries Blocker/Critical gate language.
- Example report version stamp 1.9.0.

## [1.8.0] — 2026-08-17

Depth from multi-model review of the skill itself: close authenticated-IDOR and
cache/CDN blind spots; force agent hard-gates; install support docs; lean privacy
+ observability refs; token-cutting coverage ledger and DIFF-scoped Phase 1.

### Added
- A01: Identity Map **forgeability** column + bypass row-set; **bidirectional
  gate proof**; **two-principal matrix**; **cache/CDN authz**; dual-surface
  beyond `page.tsx` (serialized payload, server actions, RPC/GraphQL/WS);
  tenant/row scoping; presigned URL / upload checks; safer anon-GET (canary +
  anon-vs-auth body diff; local/dev default).
- A05 files/archives/XXE; A06 business-logic detect steps; A07 session cookies +
  OAuth/OIDC + refresh rotation; API overlay procedures (BOLA/BFLA, mass-
  assignment, zombie APIs, GraphQL/gRPC/WS).
- `references/privacy-compliance.md`, `references/observability.md`.
- Phase-0 coverage ledger + archetype → load map; first-response hard block
  (`SCOPE`/`START_SHA`/`TREE_STATE`/`REVERTS_CHECKED`/…).
- Banned remedies: deleted gate paths (`--diff-filter=D`), not only Revert
  subjects.
- Authz posture ledger in Ground truth; negative authz tests in DoD;
  DIFF authz 🚩 list; public-repo disclosure rule for committed reports.
- Parallel-audit: frozen packet schema + invariant catalog.
- `install.sh` copies `standards-index.md` + `example-review-report.md` into
  installed `references/`.
- ASVS 5.0.0 verified by direct fetch (2026-08-17) in standards-index.

### Changed
- Phase 5 default: chat BLUF ≤30 lines + out-of-tree; `code-review/` write is
  opt-in (`--write-report` / confirm).
- Phase 1 scoped for `DIFF`/`FILE` (changed-path tests; plant only if gate under
  review).
- Domain S FULL: consequence branches + count by default.
- Domain B: SSRF ranges single-sourced in appsec; A02–A10 one-liners + force
  load of `security-appsec.md` before Phase 3.
- S2 world-reachable without auth = Critical (zero discretion).
- README domain table + reference count; example report version stamp 1.8.0.
- CI asserts installed support docs present.

## [1.7.0] — 2026-08-17

Access-control depth from a production anonymous-read class of defect:
identity must be mapped per request class before any gate is proposed; API
redaction is not page protection; preflight that expects anonymous 200 on
data routes is a finding; internal business data is Confidentiality Tier S2.

### Added
- **Identity Arrival Map** (document / XHR / bare curl) in `security-appsec.md`
  A01 — required before proposing middleware or document gates; "middleware on
  document when identity only arrives via client Bearer" marked anti-pattern.
- **Dual-surface check** — sensitive loader used by API ∩ RSC/SSR page;
  asymmetric redaction = Critical when world-reachable.
- **Anonymous GET sweep** — mandatory Phase 0/3 opener for networked apps
  (status + body size, no auth).
- **Confidentiality tiers S0–S3** in the severity rubric (incl. internal
  business data as S2 → Critical if world-readable).
- Phase 0: platform-vs-app-vs-preflight trust rows; **banned remedies** from
  recent auth/middleware/gate reverts.
- Phase 1 planted-defect matrix: missing / **empty** / wrong / path-excluding
  config.
- `parallel-audit.md`: specialized-subagent reject → **generalPurpose** fallback
  under the same read-only contract (do not stall A01 on harness ceremony).

### Changed
- Phase 5: prefer out-of-tree report during active Critical remediation; chat
  order for FULL = verdict → plain top 5 → decisions → path to machine table
  (table in file, not first bubble); advise-only on security gates (no
  auto-implement middleware).
- Domain B checklist + adversarial opener cross-link the new A01 procedures.
- `testing-and-evals.md`: empty-config self-test called out.

## [1.6.0] — 2026-08-17

**Agent-agnostic packaging.** The method was already host-neutral in substance;
install + docs still read Claude-first. Default install now mirrors the skill
into every common skill root (`.agents/`, `.cursor/`, `.claude/`), `AGENTS.md`
is the cross-vendor entry pointer, and SKILL/parallel-audit/docs speak to any
major coding agent first.

### Added
- Default multi-path install: `.agents/skills/`, `.cursor/skills/`,
  `.claude/skills/` (+ optional `--with-codex` → `.codex/skills/`).
- `--minimal` lean install; `--with-cursor` kept as no-op for compatibility.
- Harness table rows for Copilot / Gemini / Aider / Windsurf; generic-first
  fan-out contract.

### Changed
- SKILL "How to use" + confidentiality restatement → agent-agnostic discovery
  and `AGENTS.md`-canonical imprint language.
- `docs-and-dx.md` portability / imprint: prefer `AGENTS.md`, peers as pointers.
- README / AGENTS.md install pointer: no "for non-Claude agents" framing.
- CI dry-run asserts `.agents` + `.cursor` + `.claude` paths on default install.

## [1.5.0] — 2026-08-17

Depth + install portability on top of 1.4.0's multi-agent checkout safety. New
reference playbooks for reliability, concurrency, and API contracts; review-
surface gate in the definition of done; harness notes for fan-out; version
stamp + optional Cursor-native install path; worked fictional example report.

### Added
- `references/reliability-error-handling.md` — domain F depth (timeouts/aborts,
  retries, crash/SIGINT resume, silent subsystem no-op).
- `references/concurrency-shared-state.md` — domain G depth (races, file stores,
  TOCTOU, tests/jobs vs real shared paths).
- `references/api-contracts.md` — domain I depth (public contracts, webhooks,
  message-schema evolution; OWASP API Top 10 overlay stays in appsec).
- Skill `VERSION` file (`1.5.0`); `install.sh` stamps version + short SHA into
  the AGENTS.md pointer and **refreshes** that block on re-install.
- `install.sh --with-cursor` — also copies the skill to
  `.cursor/skills/deep-code-review/` (Cursor-native; Cursor already loads
  `.claude/skills/` for compatibility — verified against Cursor Agent Skills
  docs this session).
- `docs/example-review-report.md` — fictional FULL report showing `START_SHA`
  preamble, `CONFIRMED`/`CORROBORATED`/`PLAUSIBLE`/`latent`, and plain-language
  companion.
- `parallel-audit.md` harness notes — Claude Code / Cursor / Codex / one-shot
  map for read-only toolsets vs mutate-ban + tree-diff fallback.
- Definition-of-done + first-response **review surface pinned** checklist
  (`START_SHA`, worktree, history count).

### Changed
- README domain table routes F/G/I to the new references; install docs cover
  `--with-cursor` and the version stamp.

## [1.4.0] — 2026-08-17

Ops/safety hardening for **live multi-agent checkouts** — the review loop already
caught real defects under an anti-fabrication contract; this release makes the
method safe when another agent is editing, switching branches, or committing in
the same tree. Additive: domains A–S and report sections unchanged; new
confidence marker `CORROBORATED`; Phase 0/1/5 and `parallel-audit.md` carry the
depth.

### Added
- **Immutable review surface** — Phase 0 captures `START_SHA`, prefers
  `git show $START_SHA:path` or a dedicated worktree/clone (default for `FULL`),
  and detects a shared/mutating checkout (`git status` twice; occupied → don't
  plant or write into the live tree). First-response line states the pinned ref.
- **History-depth check** — Phase 0 runs `git rev-list --count HEAD` /
  `git log --oneline -5` (and shallow detection); never trust a prose "no
  history" claim; tree scrub ≠ history scrub for secrets/PII.
- **Triage-first fast lane** — Phase 0 runs project `doctor`/gates/documented
  invariants before expensive fan-out; Review mechanics and Phase 2 order by
  blast radius after those hits.
- **`parallel-audit.md` contracts** — read-only tool allowlist (or mutate-ban +
  lead before/after tree-diff hard-fail); transitive identifier masking in
  subagent returns; mega-file chunking by named concern; `CORROBORATED`
  confidence when independent units converge on the same sink.
- **Phase 5 shared-tree escape hatch** — if the checkout is occupied or an
  unrelated change is in flight, deliver the human-readable report out-of-tree /
  offer a dedicated review branch instead of writing `code-review/` into someone
  else's commit surface.
- **Hermetic-test shared-state red flag** — domain J (cross-ref G) + depth in
  `testing-and-evals.md`: tests that write real tracked/shared data paths with
  cleanup only in `finally`/`try` that hard-exit can skip.

### Changed
- Principle 7 — planted-defect probe defaults to a dedicated worktree/copy;
  report write is conditional on an unshared idle tree; fan-out least-privilege
  is by toolset where the harness allows.
- Principle 11 / confidentiality restatement — masking is transitive through
  fan-out, not lead-only.
- Phase 1 planted probe — worktree/copy at `START_SHA` by default; never plant
  into a tree another process can commit from.

## [1.3.0] — 2026-08-14

New capability — **branch, merge & open-work triage**. The review now analyzes
every open branch and advises, per branch, whether to merge it (to `main` or
`develop`, per the detected branching model), open a PR, rebase/refresh, delete
(if already merged), archive, split, or escalate — so leftover work gets cleaned
up instead of rotting. Unlike 1.2.0, this **does** change the domain list
(A–R → A–S) and **adds a report section** (the branch & merge triage table).
Additive and opt-in to act on: the triage is advice; any merge/delete/push runs
only on explicit approval.

### Added
- `references/branch-and-merge-hygiene.md` — the depth behind the new domain S:
  ground the branch set before judging it (`git fetch --all --prune`; a shallow/
  stale clone hides open work; open-PR state is forge state, mark `unverified`
  when forge auth is absent); detect the branching model (Trunk-Based / GitHub
  flow / GitLab flow / git-flow) to resolve each branch's target; classify by
  **content, not just tip** — `git branch --merged` misses squash/rebase-merges,
  `git cherry` recovers single-commit squashes but a **multi-commit squash defeats
  patch-id matching**, so the forge merged-PR list is the authoritative
  corroborator; a per-branch decision tree → recommendation with the exact
  command; merge-strategy trade-offs; safety rails (never delete unique unmerged
  work, `--force-with-lease` not `--force`, a leaked secret is fixed by rotation
  not branch deletion); and severity discipline so branch cleanup never buries a
  real defect. All enumeration commands validated against a scratch repo this
  session. Routed from the new domain S.
- **Domain S — Branches, merges & open-work triage** in `SKILL.md` (A–R → A–S),
  scoped to a local git checkout; a Phase-0 open-branch/open-PR inventory hook; a
  Phase-5 triage-table output; a **Branch & merge triage** section in the findings
  report and an "Open work to tidy up" section in the human-readable report; and a
  definition-of-done line requiring every open branch to carry one recommendation.
- Boundary made explicit with section O (`docs-and-dx.md`): O owns *is branch
  protection configured*; S owns *what open work exists and what to do with it* —
  cross-referenced, not duplicated.
- `docs/standards-index.md`: verified-this-session rows (2026-08-14) for
  Trunk-Based Development, GitHub flow, GitLab flow, git-flow (Driessen), Fowler's
  branching-patterns article, GitHub's merge-method / protected-branch / merge-
  queue / branch-deletion docs, and the `git` reference manual, with the two
  attribution caveats surfaced by primary-source checks (GitHub's own docs do not
  state "main is always deployable"; "merge debt" is not Fowler's phrase).

## [1.2.1] — 2026-08-14

### Fixed
- `install.sh` backed up an existing skill to `…/.claude/skills/<name>.backup-<ts>`
  — **inside** `skills/`, where Claude Code then loaded the backup as a duplicate
  skill. Backups now go to `…/.claude/skill-backups/` and are never loaded.

### Changed
- `install.sh` is **universal by default**: alongside the Claude Code skill it
  writes an additive, idempotent cross-agent `AGENTS.md` pointer (Codex, Cursor,
  Copilot, Gemini, Aider), so the method is not Claude-only. The opt-in
  `--portable` flag is replaced by a `--claude-only` opt-out (`--portable` is still
  accepted as a no-op, with a note).

## [1.2.0] — 2026-08-14

Coverage extension — dependency currency & safe upgrades, repository hygiene,
cross-agent portability of the standards imprint, and DX depth — plus the repo now
enforces its own documented gates in CI. Additive; phases, domains A–R, and report
formats are unchanged.

### Added
- `references/dependency-currency-and-upgrades.md` — detect stale / EOL /
  known-vulnerable dependencies, then upgrade with discipline (no blind "latest",
  semver-risk sizing, changelog review, regenerated lockfile, the project's own
  gate proven green on the bumped tree, provenance check) with severity discipline
  so "behind latest" never becomes noise. Routed from K and H.
- Repository hygiene & community-health review (`docs-and-dx.md`, SKILL.md O):
  LICENSE, SECURITY.md, CONTRIBUTING, CODEOWNERS + its enforcing rule, branch
  protection, CHANGELOG, templates — rated by repo exposure (Info/Low private,
  escalating when public / distributed / reaching production).
- Cross-agent portability: a divergence check across `CLAUDE.md` / `AGENTS.md` /
  peer instruction files, and a Phase-6 imprint that now defaults fresh standards
  to a canonical cross-vendor `AGENTS.md` with thin per-agent pointers; the
  "documented but unenforced = advisory" durable-standards finding.
- `install.sh --portable` — additively drops an idempotent root `AGENTS.md`
  pointer so non-Claude agents (Codex, Cursor, Copilot, Gemini, Aider) discover
  the method.
- This repository now dogfoods its own bar: `.github/workflows/ci.yml` (routing,
  name-match, `install.sh` parse, banlist-driven fail-closed privacy gate; a
  SHA-pinned action + least-privilege token), plus `SECURITY.md`,
  `CONTRIBUTING.md`, and `.editorconfig`.
- 16 standards verified by direct fetch and logged in `docs/standards-index.md`.

### Changed
- **DX** (`docs-and-dx.md`) gains fewest-commands-to-first-run (normalized
  bootstrap / devcontainer), dev/prod parity, and time-to-first-run as friction.
- **Phase 6 / imprint** is now idempotent and additive (detect-and-stop,
  create-if-missing, add-only-missing-lines, print-what-changed) and pairs every
  imprinted standard with the gate that enforces it.
- **Decorrelated second-model review** (SKILL.md review mechanics) is read-only
  and fail-soft — it advises, never hard-blocks.
- README reference-file count (10 → 11); standards list refreshed.

### Fixed (from a self-review of the skill)
- **Phase 5** no longer mandates writing `code-review/…` for a `DIFF` of a PR/MR
  (which may have no writable checkout, and would land the file inside the diff
  under review) — that write is scoped to FULL / local-checkout, and a DIFF's
  deliverable is the review comment on the PR.
- **Phase 1**'s planted-defect gate probe now requires a verified-clean tree (or a
  throwaway worktree) and a confirmed revert, carved into principle 7 as the one
  permitted transient mutation.
- **Severity rubric**: `unverified` / `PLAUSIBLE` findings now have an explicit
  gate rule (reported at provisional severity, block only once confirmed); Blocker
  vs Critical for data damage is discriminated (already-corrupting vs
  will-corrupt-next-run).
- **Coverage**: input-amplification DoS (ReDoS, decompression / entity-expansion
  bombs) added to the adversarial pass and the red-flag greps; AI-eval golden-set
  **contamination** flagged as a Critical eval defect; one-shot-prompt mode now
  names the references to also paste.
- **Duplication / pointers**: data-quality's spend-governance restatement folded
  into a cross-reference to `performance-db-cost.md`; a stale "section M" secret
  pointer repointed to N; `N-A` → `N/A`; `CREATE INDEX CONCURRENTLY` marked
  Postgres-specific.

## [1.1.0] — 2026-08-13

Field-hardening pass distilled from four independent FULL-run engagements. No
restructuring — phases, domains A–R, and report formats are unchanged; these are
additive method, rubric, and reference refinements.

### Added
- `references/parallel-audit.md` — fan-out protocol for large targets: a shared
  context packet, a fabrication-resistant subagent contract (one named invariant,
  `file:line` + failing case, `NONE` is valued), and orchestrator re-verification
  of every subagent finding in both directions. Routed from "Review mechanics"
  and Phase 2.

### Changed
- **Phase 1** now verifies gate *scope*: run the project's own aggregate gate by
  name, confirm exit codes, enumerate what the gates exclude and report coverage
  per subtree, prove each gate goes red on a planted defect, and flag
  decorative/unwired tests — plus a container/serverless deploy-contract
  preflight.
- **Severity rubric** gains a reachability qualifier: a `latent` finding keeps its
  intrinsic severity but gates "enabling the subsystem," not merge (a bounded +
  gated + recoverable destructive breach may be High); owner priority raises
  prominence, not severity. Machine and human reports gain a two-status verdict
  and `CONFIRMED`/`PLAUSIBLE` finding confidence.
- **Domains A–E, C, O** and their references gain: latest-batch-by-`max(col)`;
  exposure-boundary-first + CSRF≠auth; the "asserted-but-unenforced safety
  property" class; a spend-safety checklist (default-off caps, fail-open ledgers,
  `SELECT sum()` TOCTOU, cross-process guards); monotonic read-path shadowing +
  write-guard-covers-every-primitive; and a docs↔code claim-reconciliation
  technique.
- **Principle 2 / Phases 4–5**: byte-fidelity before invisible-character claims; a
  live-vs-documented-incident discriminator; report privacy re-scan, third-party
  proper-noun scrub, and PR-split by risk surface.
- README reference-file count (9 → 10).

## [1.0.0] — 2026-08-13

Initial release: a universal, evidence-grounded deep code-review skill.

### Added
- `.claude/skills/deep-code-review/SKILL.md` — the review method (6 phases) and
  eighteen domain checklists (A–R) plus an adversarial/red-team pass, severity
  rubric, exact report format, and definition of done.
- Nine on-demand reference playbooks under `references/`: application security
  (OWASP Top 10:2025), AI/LLM/agent security (OWASP LLM Top 10:2025 + Agentic
  Applications 2026), data integrity & quality, performance/DB/cost, testing &
  evals, infrastructure/IaC/containers, docs/DX (incl. the standards-imprint
  phase), frontend/accessibility (WCAG 2.2 AA), and language/stack red flags.
- `install.sh` — one-command install of the skill into any project's
  `.claude/skills/`, with backup-on-update and self-install guard.
- `README.md` (human-facing, with a Mermaid method diagram and a coverage map),
  `CLAUDE.md` (AI-facing standards for this repo), `docs/standards-index.md`
  (verified standards with URLs + verification dates), `.banlist.txt` privacy-gate
  seed, `LICENSE` (MIT), and `.gitignore`.

### Notable design decisions
- **Judge the outcome, not just the code** — a hard monotonic-quality invariant
  for any data producer, with a required non-regression test.
- **Do no harm** — every proposed change must be net-positive across all axes;
  never fix one by regressing another.
- **Respect the existing design** — accessibility/UX defects are fixed in place;
  design-altering changes are surfaced as owner decisions.
- **Standards imprint** — an opt-in final phase persists a tailored standards set
  into the reviewed project so quality holds on later iterations.
- **Human-readable report** — Phase 5 also writes a plain-language, non-technical
  report into a top-level `code-review/` directory in the reviewed repo (dated,
  additive), so a founder or leader can act on it without reading the code.
- **No duplication** — the skill has a single home; `SKILL.md` routes to every
  reference; nothing is restated.
- **No fabrication / cite-only-verified** — standards are split into
  directly-fetched (with dates) and by-name in `docs/standards-index.md`.
