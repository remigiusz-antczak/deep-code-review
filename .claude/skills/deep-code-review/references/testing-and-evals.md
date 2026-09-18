# Testing & evaluation review

Read this to judge whether the target is *actually* verified — not whether a
coverage number is high. Expands section J of `SKILL.md`. Match coverage to what
the project does; **skip test types that don't apply rather than writing
theater.**

---

## Pick and name a test-shape philosophy first

Two named, citable shapes disagree on emphasis — that disagreement is itself
useful, so don't silently pick one: the **Test Pyramid** (Cohn/Fowler — mostly
unit, some integration, few e2e; optimizes for speed and low flakiness, fits a
small team or complex pure domain logic) and the **Testing Trophy** (Kent C.
Dodds — mostly integration, thinner static/unit layers, a thin e2e cap;
optimizes for confidence-per-test, fits an I/O- and UI-heavy app where unit
tests would mostly re-test mocks). A heavily skewed suite (e.g. 90% e2e,
near-zero unit) with **no stated philosophy anywhere in the repo** is a
finding — the same way this skill already treats an undocumented architecture
as the finding, not the architecture's shape. Neither shape is "correct" in
the abstract; require the project to name which one it follows (or an
explicit third choice), not which one this review prefers.

## The test taxonomy (apply what fits)

- **Unit** — every exported function and its edge cases; pure logic isolated
  from I/O.
- **Integration** — the real seams between modules/services/DB (not everything
  mocked into a tautology).
- **End-to-end** — the actual pipeline/user flow, start to finish.
- **Regression** — a failing test written **first** for every bug fixed (fails
  on the old code, passes after). No bug is "done" without one.
- **Security** — injection (SQL/XSS/command), authz/IDOR, SSRF, and — for LLM
  code — prompt-injection/jailbreak, output-handling, and unbounded-consumption
  cases (see `security-ai-agents.md`).
- **Property / fuzz** — for parsers, validators, and anything taking wild input.
- **Snapshot / weight-pin** — stable identities (ids, dedup/join keys,
  normalized values) and every scoring weight/threshold, so a silent change is
  caught as a reviewed diff.
- **AI evals** — for any model-dependent output (see below).
- **Non-functional** — performance/load/stress/spike/endurance where relevant,
  and accessibility (see `frontend-a11y.md`).

## What good tests do (and the smells that betray bad ones)

- **Test the failure, not just the feature.** Every refusal/guard path — a
  rejected input, an over-cap request, a denied scope, a bad signature — needs a
  test asserting it actually refuses. Write the red case and watch it fail
  **first**; a test that has never failed proves nothing.
- **Probe the real function on the real fixture before pinning an expected
  value.** Never hand-guess an expected string — a guessed expectation encodes a
  misunderstanding as a green test.
- **Reviewing your own diff? The tests inherit your blind spot.** The mind that
  wrote the bug wrote the tests, so they exercise the axis you considered and hold
  fixed the one the bug hides on. For each new test ask what it does *not* vary —
  second call, concurrent call, empty input, second run — and add that case
  (cross-ref G's singleton-lifetime class).
- **Adversarially test the checker itself.** A gate/validator/parser is code
  too: feed it null-resolution, truncation, substring false-matches, empty
  input. In CI, **self-test every gate against a planted defect** so a check
  can't silently rot into a no-op that passes everything — include
  **empty/whitespace-only config** (not only a missing file); see Phase 1's
  planted-defect matrix in `SKILL.md`.
- **Trace which tests the gate actually runs.** Enumerate the test files, then
  read the gate/CI command and list which it invokes. Tests present in the tree
  but wired to no gate are **decorative** — a finding; name the highest-stakes
  untested logic. (Pair with the planted-defect self-test above: prove the gate
  both *runs* the test and *goes red* when it should — and that the reported
  count changes, so a test can't be silently skipped.)
- **Never report success over input you didn't read.** When a required input is
  absent, **skip loudly** (or fail) — a green tick over unread input is worse
  than a red one, because it looks like assurance.
- **Verify the served response, not the repository.** Typecheck, unit tests, and
  a production build can all pass while the served page/endpoint is broken
  (stale, unstyled, misconfigured). Assert against what ships. Corollary: don't
  mutate content-hashed assets a running process is still serving.
- **A visual receipt must show the feature, not a wall past it.** When the review
  needs a screenshot of a changed screen, non-empty is **necessary, not sufficient**
  — an error, login, or empty-state page is a valid non-empty image that proves
  nothing about the change. Capture authenticated content through a **dev /
  identity-bypass render mode**, not a production build that auth-walls every route
  (which screenshots a login page perfectly). Prefer a **deterministic readiness
  signal** (a specific selector / text is present) over a network-idle heuristic,
  which a live hot-reload socket keeps busy so the capture waits forever and yields
  zero images. (Distinct from reproducing a **build-specific** defect, which must use
  the production build — `method.md`; this is capturing *feature* evidence past an
  auth gate.)
- **Meaningful assertions.** Not `assertTrue(true)`; not a mock that makes the
  test pass trivially; not coverage inflated by tests that assert nothing.
- **Mutation testing when a coverage number is doing the assurance work.**
  Line/branch coverage shows what *ran*, not whether a test would *catch a fault*
  in it (`pitest.org`); a suite can hit a high percentage and assert almost
  nothing. When load-bearing logic leans on a coverage figure as its assurance,
  measure the **product suite's** fault-detection with **mutation testing**
  (distinct from self-testing a *gate* against a planted defect, above — this
  scores the shipped tests, not the checker): seed small faults and read the
  **mutation score** (percentage of mutants killed). A **surviving mutant is a
  finding in this method's own shape** — a `file:line` plus the exact behaviour no
  test asserts (a High-confidence weak-assertion finding, not a style nit); triage
  survivors on critical paths first. Name the technique + the CI operator (e.g.
  Stryker's `thresholds.break` — it exits non-zero below a set score, but
  **defaults to `null` = never fails the build**, so it fail-closes only once you
  *set* it (the `high`/`low` thresholds default to 80/60 and merely colour the
  report — a decorative gate if mistaken for one; cross-ref the fail-open severity
  axis); choose the break value per repo, do not import a number) rather than a
  single tool; representative engines are **Stryker** (JS/TS) and **PIT** (JVM),
  plus per-language equivalents. **Bound it to the highest-stakes modules** — a
  mutation run scales with suite size × mutant count, so a repo-wide mandate is an
  over-ask.
- **Deterministic & hermetic.** No real network, no real DNS, no writes outside
  a temp dir, no wall-clock/timezone flakiness. Inject a **seam** (a resolver, a
  store directory, a clock) rather than the real dependency. When a module
  latches config at import time, set the temp config **before** the first
  import. Sanitize the environment passed to any spawned subprocess down to an
  explicit allowlist — children inherit the full parent env by default, which
  both leaks secrets and lets a test operate on real shared state.
- **Tests must not write real shared/production data paths.** A suite that
  points the server-under-test at a tracked, shared, or default data directory
  (no temp-dir / network-dir override) will intermittently corrupt real state —
  especially when "restore" lives only in `finally`/`try`/`afterEach` that a
  hard exit (`process.exit`, SIGINT, worker crash) or overlapping runs can skip.
  Rate as High/Critical by consequence (data loss, PII mix-up, flaky CI that
  mutates the operator's machine). Fix pattern: inject a store root, default
  tests to an OS temp dir, make cleanup signal-safe or use unique per-run dirs
  the OS reaps. Cross-ref domain G when the path is also a concurrent writer.
- **Testing an outbound alert/webhook from a spawned job needs async spawn + a
  localhost listener.** The natural test — run a scheduled/unattended job to a
  failure and assert its alert fired with a privacy-safe body — deadlocks under
  `spawnSync`: the blocking call freezes the test's event loop, so an in-process
  `http.createServer` can't accept the child's POST *during* the run and the
  request is never captured. Use async `child_process.spawn` (await `close`) so the
  loop services child and listener concurrently; collect requests into an array and
  assert after close. Keep it localhost (`127.0.0.1:0`, random port — no external
  traffic) and assert the body carries only aggregate/privacy-safe fields (terminal
  state, exit code, failed step *names*), **not** the failing command's output.
  Pairs with domain W's liveness-alert requirement — the alert must exist; this
  proves it fires, correctly and safely.
- **Coherence test for necessarily-duplicated logic.** Where logic is mirrored
  (a port, a re-implementation, a circular-import copy), link the source of
  truth in a comment **and** add a test that runs one fixture through both paths
  and asserts identical output.
- **Honest coverage taxonomy.** State what is automated vs. operationally
  checked vs. human-reviewed vs. not-applicable-with-reasoning. Document
  coverage gaps and skipped tests; never claim an assurance you don't have.

## Prove a rendered-layout claim with geometry, not class names

A UI test that asserts **the class that is supposed to produce a layout** —
`expect(pill).toHaveClass(…)`, `toBeVisible()`, a markup snapshot — proves only that
the author wrote the class they typed; it passes while the two elements render **on
top of each other**. Overlap, collision, and clipping are **geometric** properties,
provable cheaply and deterministically, and a class assertion can never catch them.

For any pair of adjacent elements whose collision is user-visible (a label + its
status pill / badge, a row's text + its action cluster, a header + an overflow
control), the test that counts is a **rendered bounding-box assertion**, run at
**each width the project already screenshots** (an overlap is width-dependent and
usually shows only at the narrow one):

```js
// Playwright: adjacent elements must not intersect at the target width.
// boundingBox() returns null for a non-rendered element — assert presence first.
const a = await label.boundingBox();
const b = await pill.boundingBox();
expect(a && b).toBeTruthy();             // both rendered (not null)
const intersects = (r1, r2) =>
  r1.x < r2.x + r2.width && r2.x < r1.x + r1.width &&
  r1.y < r2.y + r2.height && r2.y < r1.y + r1.height;
expect(intersects(a, b)).toBe(false);    // non-intersection
expect(a.width).toBeGreaterThan(0);      // and neither collapsed to zero
```

Equivalent primitives elsewhere: `getBoundingClientRect()` pairs in a browser-backed
unit runner, or `elementHandle.boundingBox()` per locator. Two companion assertions
share the mechanism:
- **Clip / truncation:** `scrollWidth > clientWidth` on an element that must not
  ellipsise.
- **Disabled-looks-disabled:** assert the **computed** affordance (`opacity`,
  `cursor`, or painted colour) of a disabled control, not the `disabled` attribute or
  the class — an attribute that blocks the click while the control still *styles* as
  live is a dead control that looks clickable.

**Scope discipline — invariants, not pixels.** These assertions are for
**non-intersection and non-clipping**, which hold on every renderer. They are **not**
for absolute positions or exact widths, which are renderer- and font-metric-dependent
and produce the cross-OS flake the bar warns against (the renderer-tolerance / pinned-
exception discipline, `product-ux-quality.md` gate 3). The assertion is "these two do
not overlap," never "this is 132px wide." Show it **red before / green after** the
fix, like any regression test. This is the mechanical proof behind the
screenshot-inspection checklist's **overlap** and **clip** items
(`product-ux-quality.md` gate 1).

## Capturing the pre-hydration render — the disabled-until-hydrated write control

The geometry assertions above run against the *hydrated* DOM, and one gate-1 defect is
invisible there: a write control gated on client-only state (`useSession` / `useAuth`) is
server-rendered `disabled` and enables only once the client bundle hydrates, so for the
SSR → hydration window it looks like a permanent dead control (`product-ux-quality.md` gate 1,
*not-dead-before-hydration*). Catching it needs a snapshot taken **before the client bundle
runs** — three captures, cheapest first:

- **Server HTML** — fetch the route's server-rendered markup with no JS executed (the raw
  SSR/SSG response, the same bytes the user first receives) and parse it.
- **JS-disabled render** — load the route with scripting off (Playwright:
  `browser.newContext({ javaScriptEnabled: false })`), which freezes the pre-hydration paint.
- **Throttled capture** — screenshot within the hydration window under slow-CPU emulation;
  least reliable (a race), used only when the two above cannot reach the route.

The assertion is the same across all three: a control that **will** become interactive must
not present as a bare `disabled` (or `aria-disabled="true"`) with **no loading sibling in its
container** in that pre-hydration snapshot — it carries a skeleton/spinner affordance, or is
optimistically enabled (its click captured for replay, never a no-op).

```js
// Playwright: the pre-hydration paint must not show a dead write control.
const ctx = await browser.newContext({ javaScriptEnabled: false });
const page = await ctx.newPage();
await page.goto(url);                               // server HTML, no hydration
// scope to the control's own wrapper so the affordance is a sibling, not page-global
// (a page-wide match would pass on any unrelated spinner; a broken scope that matches
// nothing would fail every disabled control — stricter than the standard, gate 1 forbids):
const box = page.locator('[data-testid="composer"]'); // the write control's container
const btn = box.getByRole('button', { name: /add|submit|post/i });
const disabled = (await btn.getAttribute('disabled')) !== null
  || (await btn.getAttribute('aria-disabled')) === 'true';
const affordance = await box
  .locator('[aria-busy="true"], [data-loading], .skeleton, [role="status"]').count() > 0;
expect(disabled && !affordance).toBe(false);        // dead-until-hydrated is the defect
```

This is the **positive control** for the *not-dead-before-hydration* detector — the instrument
that converts the static `disabled={!session}` *lead* into a finding (principle 2: *an absence
is evidence only after a positive control fires*). Where the harness cannot produce any of the
three captures for a route, the item is **could-not-check** and fails **open**; a missing
snapshot is not a clean pass (`product-ux-quality.md` gate 1). It complements
`domain-checklists.md`'s SSR/static-HTML inspection, which catches hydration-*nesting* faults
in the same server-rendered output.

## A rewritten browser spec names its retired coverage and pins the wiring it can no longer reach

The geometry assertions above prove a rendered claim you can still reach. This is the
opposite case: a redesign makes a spec's target surface **structurally unreachable in the
test environment** — a surface that now renders only user-submitted content while the
test store is intentionally empty, so there is nothing to drive the interaction — and the
spec is correctly rewritten against a different surface. The trap is that the rewrite
**silently drops** what the old spec covered: surface A and surface B both exercised an
overlay; B is redesigned to nothing-to-click; the spec moves A-only; a later change
removes B's wiring (the feed's import of the shared overlay-link component) and **no test
goes red**, because the only spec that covered B is gone.

When a spec is rewritten because its surface became unreachable, three things are owed —
and their absence is a finding:

1. **Name the retired coverage as a gap.** What did the old spec assert that the new one
   does not? A dropped assertion is an *absence*, and an unrecorded absence reads as
   coverage (principle 2: *an absence is evidence only after a positive control fires*).
   Record it where coverage gaps are already tracked (the *honest coverage taxonomy*
   above), not in a commit message the next reader never sees.
2. **State whether the wiring is now unverifiable via a browser test** without seeding
   the store (or standing up a costly fixture), and why — so the gap is a decision, not
   an accident.
3. **Add a source-level structural gate that pins the wiring** the browser spec can no
   longer reach: a unit/source assertion that the feed component still imports and uses
   the shared overlay-link component (the pattern the codebase's other overlay-wiring
   tests already use). This guarantee is **weaker** than the browser scenario it replaces
   — it proves the component is *referenced*, not that the interaction *works* — so it is
   a **named fallback for a retired check, never a substitute** that lets a team trade
   rendered coverage for import checks and call the surface covered.

## A state-dependent spec must assert its precondition, not lean on a default

A browser / E2E spec that depends on an **implicit UI default** passes only by
coincidence, and the coincidence breaks silently:
- **A flipped default breaks specs that leaned on the old one — at the browser tier,
  not on commit.** A spec that asserts on content visible only while a card is
  *expanded*, or that clicks a bulk "Expand all" a redesign already removed
  (`if (await btn.count()) await btn.click()` — a no-op when the count is `0`), is
  green *only because the default happened to match what it needed*. Flip the default
  and it fails on the slow gate. Make each such spec **drive the state it needs
  explicitly** (open/collapse the specific control by its own affordance), and prefer
  an explicit state assertion over a best-effort "click if present" — a control the
  redesign has since removed silently leaves the precondition unmet.
- **Pin the equivalence between a "should-render / should-expand" predicate and the
  set it gates.** When one boolean decides whether to show or expand something and a
  *separate* path builds what renders inside, independent computation lets them drift —
  the predicate says "expand" but the body is empty, or it collapses a group that has
  content. Derive both from the same source where possible, and pin
  `predicate(x) === (renderSet(x).length > 0)` **in both directions and non-vacuously**
  (at least one input exercising each branch), so a later edit to either side cannot
  silently make them disagree — the class of bug where a "smart default" hides real
  content or expands an empty container.

## AI evals (for any model-dependent output)

A mocked-LLM unit test verifies **wiring, not model quality.** Model quality
needs its own harness:

- A **labeled golden set** scored for correctness/consistency (not vibes),
  tracked over time, with an **accuracy threshold that gates** prompt or
  model-version changes (a change that drops accuracy fails the build). The golden
  set must be **disjoint from the prompt / few-shot / fine-tune content** — a
  leaked example makes the bench measure memorization, not quality; treat
  contamination as a Critical eval defect.
- The harness's **own scoring logic is pure and unit-tested**, and it
  **fail-fasts on a malformed case** — silently skipping a case inflates the
  score.
- **Grounding / anti-fabrication checks** where claims reach users: every named
  entity and number in generated text must anchor to the input facts (match
  numbers on digit boundaries so a value can't pass on a fragment); ungrounded
  output is rejected to a deterministic fallback. Distinguish **anti-fabrication
  from anti-reasoning**: where the output's value *is* its reasoning, gate only
  the checkable facts plus a drift/overlap floor and a meta-leak guard, and allow
  inference language — don't force robotic restatement.
- Use **temperature 0** for judges/verifiers so the eval itself is deterministic.
- **Self-consistency / inter-model agreement is not precision.** Output quality
  is *unmeasured* until an expert rates a frozen, labeled cohort; don't stack
  features on an unvalidated base.
- A **decorrelated review ensemble** (multiple *different* models/reviewers, all
  must pass) catches a miss or an injection that lands on one reviewer; fail
  soft.

## Business rules as executable specs

Encode load-bearing business rules as acceptance tests so the build fails if the
code stops honoring one (e.g. a required-criterion recognizer, a keyword lexicon
maintained as a **tested superset** of the spec). Calibrate any threshold
against **both** a ground-truth **recall** bench and a **noise/precision** bench
— never "by feel."

---

**🚩 red flags**: no test for the reported bug; tests that never fail; mocks
that make the assertion trivial; a checker with no test of its own; `skip`/
`xfail` hiding a broken case; hard-coded expected values with a comment like
"update if it changes"; tests that hit the real network or real services; **tests
that write a real tracked/shared data path with cleanup only in `finally`/`try`**;
an AI feature with only mocked unit tests and no eval bench; a coverage % cited
as proof of correctness; a threshold lowered in the same diff that would otherwise
fail; a heavily skewed pyramid-or-trophy shape with no stated test philosophy
anywhere in the repo.
