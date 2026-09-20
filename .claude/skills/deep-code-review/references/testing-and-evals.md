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
- **A test double must not drift from what the real dependency actually returns.** A mock/stub
  that returns a **shape, null-vs-empty, status code, or error the live dependency never
  produces** leaves the suite green while the real integration is broken — the classic
  "all tests pass, prod is down." Verify the double against the real contract: a shared
  contract-test suite run against **both** the real service and the double, a recorded real
  interaction (VCR/cassette), or a type/schema generated from the provider — not a hand-written
  fixture encoding the author's *assumption* of the response. (Distinct from the tautology smell
  above — that's a mock that makes the assertion trivially pass; this is a mock whose *behavior*
  is wrong.)
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
  **first**; a test that has never failed proves nothing. Extend this past
  **security/guard** paths to **reliability fallback** paths: a circuit-breaker
  open-state, a retry-exhausted / dead-letter branch, a cache-miss serve-stale, a
  generation-failure fallback each needs a test that **forces the triggering
  condition and asserts the fallback branch's *output* is correct** — not merely
  that it doesn't crash, and not merely that a fired-counter incremented. The code
  path you never run is the one that silently rots: an unexercised fallback gets
  broken by an unrelated edit with no red test, invisible until the real dependency
  fails in production. A past game-day / chaos exercise (`release-engineering.md`)
  proves the infra path ran **once**; it is not a substitute for a repo-owned
  regression test that keeps the branch honest on every future change.
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
- **A passing type-check / compile is a *partial* gate — after a conflict
  resolution on a long-behind branch, run the full suite.** A clean compile proves
  the tree type-checks, not that it still *behaves* as pinned. A three-way merge can
  be type-correct yet wrong: the branch pins a behavior with a test asserting a
  specific behavior (an emitted event name, a serialized field, a default value) the other
  side refactored away; the resolution compiles against the new shape while a
  behaviorally-pinned test still asserts the old one — the type checker never sees
  it, the suite does (and the longer the branch was behind, the likelier). Classify
  a type-check / compile pass as **necessary, never sufficient**; run the behavioral
  + regression suite after a conflict resolution before declaring it correct. When a
  pinned test breaks under the resolution, treat it as a signal to re-examine the
  resolution — **not** a cue to delete or "update" the test to match the merged code
  (it may pin behavior the other side still depends on).
- **A property test whose generator encodes the invariant it checks is
  tautological.** If the input generator is built from the same rule the assertion
  verifies, it can never produce the case that violates it — the test passes
  vacuously and guards nothing. The generator must sample the input space
  **independently of the property's *conclusion*** — constraining it to the property's
  **precondition** (only sorted inputs for a sort property, only valid emails for a
  formatting property) is legitimate and often necessary; the smell is specifically a
  generator built from the same rule the **assertion** checks, so the violating case can
  never be generated and the test passes vacuously (the property-test sibling of the mocked-into-a-tautology
  integration smell above).
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
- **Continuous, coverage-guided fuzzing as CI infrastructure — not a one-off property
  test.** The taxonomy above lists property/fuzz as a *shape*; the assurance that finds
  *new* bugs is a **coverage-guided fuzzer run continuously** (OSS-Fuzz / ClusterFuzzLite,
  `go test -fuzz`, `cargo fuzz` / libFuzzer, Atheris), mutating inputs against live
  coverage feedback so it keeps finding crashes indefinitely — a different assurance than
  a hand-written property test that exercises its own corpus once. OpenSSF Scorecard's
  Fuzzing check (**"Risk: `Medium` (possible vulnerabilities in code)"**) reasons that
  "Regular fuzzing is important to detect vulnerabilities that may be exploited by others,
  especially since attackers can also use fuzzing to find the same flaws." (Scorecard also credits non-coverage-guided property-testing libraries — fast-check, QuickCheck/Hedgehog, proper, FsCheck — so a passing Scorecard Fuzzing score alone is not evidence of *continuous coverage-guided* fuzzing; apply the wired-to-CI + crash-corpus bar below regardless of the score.) The review
  question is not "is there a fuzz target" but **is it wired to a job that runs on a
  schedule / in CI, and does a crash reach a human** — findings triaged into a committed
  **crash corpus that becomes regression tests**, not a log nobody reads. A fuzz target
  defined in-repo but attached to no fuzzing job or service is **decorative** — the same
  "a gate must be proven to run" bar this file holds mutation testing and self-tests to.
  Scope it (like mutation testing above) to the highest-stakes parsers / decoders /
  deserializers / protocol boundaries, where input reaches attacker-controlled bytes.
- **Deterministic & hermetic.** No real network, no real DNS, no writes outside
  a temp dir, no wall-clock/timezone flakiness. Inject a **seam** (a resolver, a
  store directory, a clock) rather than the real dependency. When a module
  latches config at import time, set the temp config **before** the first
  import. Sanitize the environment passed to any spawned subprocess down to an
  explicit allowlist — children inherit the full parent env by default, which
  both leaks secrets and lets a test operate on real shared state.
- **A test that shells a real external binary must probe it for functional success
  and skip loudly on any failure — not merely check the binary is on `PATH`.** CI is
  "present but different/broken," not "absent": a bare presence check (`which chrome`,
  `command -v ffmpeg`) only proves the binary **exists** — it never executes it; the test
  then invokes it for real — a headless browser, `git`, `ffmpeg`, a database CLI —
  and that invocation can fail for reasons a presence check never sees. A
  headless-Chromium binary running as root in a container commonly needs its
  sandbox set up explicitly (a non-root container user, or an explicit launch flag)
  or the launch crashes before it renders anything; a `git commit` depends on a
  resolvable `user.email`/`user.name` and can fail outright rather than silently
  falling back — verified directly in a scratch repo: forcing the identity to an
  explicit empty string (`git -c user.email= -c user.name= commit`) raises `fatal:
  empty ident name (for <>) not allowed`, exit 128, while the same repo and command
  with a real identity supplied inline (`git -c user.email=… -c user.name=…`) exits
  0 regardless of the runner's ambient config. Two requirements: (1) gate on a
  **functional smoke** — the binary actually produced the artifact or exited 0 on a
  trivial real invocation — giving a required *binary* the same discipline this
  file already gives a required *input*: **skip loudly** (above) with the captured
  failure, never a silent pass; (2) the test **supplies its own required launch
  configuration** explicitly rather than inheriting the runner's ambient defaults —
  `git -c user.email=… -c user.name=…` against its **own temp repo**, an explicit
  launch flag for a browser harness rather than assuming the CI image happens to
  have the sandbox pre-configured. Distinct from the
  network/DNS/clock/tmpdir hermeticity above (the test's *own* execution
  environment), the test-double-fidelity rule above (a **mock** drifting from a
  **live service**'s contract — this is a **real binary**, present, behaving
  differently under CI), and the verification-gate cannot-check rule
  (`reliability-error-handling.md` — governs how a gate **reports** its own harness
  crashing at setup; this governs the test's **probe**, so the crash is caught by a
  functional check and prevented by explicit config up front rather than merely
  reported after the fact).
- **Randomized test order + a logged seed.** A suite that always runs in file / declaration
  order can pass not because its tests are independent but because they always run the one
  order that happens to work — hiding inter-test state pollution (a module-level cache, a
  shared fixture, a leaked singleton, an env var one test sets and another reads). Run with
  **randomized order and a recorded seed** (`pytest-randomly`; Jest `--randomize` +
  `--seed`; JUnit `MethodOrderer.Random`); a failure that appears only under randomization
  is real order-dependence, and the same seed reproduces it. Keep it on in CI so a new
  coupling surfaces immediately. Distinct from the *environment* determinism above
  (network/DNS/clock) — this is **execution-order** coupling between tests.
- **A chronically flaky test is quarantined and fixed, not retried until green.** A test that
  passes and fails on the same code is a real signal (a race, an order/time/network dependence,
  a leaked fixture) — a blanket **retry-until-green** in CI masks it, manufactures false
  confidence, and once the team learns to re-run red a *genuine* regression hides in the noise.
  Move a known-flaky test to a **non-blocking quarantine** with a tracked owner and a fix
  deadline (not a permanent dumping ground), and fix the underlying nondeterminism (pin the
  clock/seed, remove the shared state, await the real condition instead of `sleep`). A standing
  CI retry count `> 0` used to paper over flakes — rather than a bounded retry on a genuinely
  external flake with the rate tracked — is the finding.
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
- **Local/CI parity includes the *resource envelope*, not just the commands.** A gate whose parallelism is
  tuned for CI's cores/RAM (`--workers=N`, `-j N`, a fixed pool size) can OOM or crash the *same* gate on a
  lower-headroom dev host — green in CI, unrunnable locally, so a contributor can't reproduce it. Size
  concurrency to the host (detect cores / free memory, or cap it) or make it a documented, overridable knob,
  never a hardcoded CI-shaped constant. "Runs in CI" is not "runs on the machine a human debugs it on."

## A green run is a sample, not a proof, when the trigger is nondeterministic or the run is too costly to repeat

Some fixes can't be validated in one session: a **nondeterministic trigger** (a browser
degradation that appears ~1 run in N), or a validation run so long (~20 min each) that one pass
is not proof. Shipping such a fix on a **single green run is a false "done"** — the failure
recurs later, far from the change. **Distinguish "validated" from "happened to pass once,"** and
label accordingly.
- **Ship the part you *can* validate** — e.g. crash-recovery for a *reproducible* mid-pass browser
  death, validated by catching a real crash and re-running the pass on a fresh browser.
- **Name the part you can't** as a **Known-limitation** in the PR body, with a concrete proposed
  follow-up (e.g. a per-pass timeout routed into the existing discard-and-retry path) — explicitly
  deferred because its trigger is nondeterministic and unvalidatable in one lane. A **named
  residual is honest; a silent one ships a false "done."**
- **Don't let "while I'm here" scope-creep** bolt an **unproven** refactor onto an
  otherwise-validated PR — it re-buries the validated change under unvalidated risk; make it a
  separate, properly-validated change.
- **Symmetric with the placebo.** The same judgment that refuses an *unvalidatable* fix also
  refuses one **proven not to work** (a "lower the concurrency" change that still crashed). Ship
  only what you've shown to hold; everything else is a named residual or a separate change.

This *ran-green-but-once* residual and a *deferred / never-run* gate (`parallel-audit.md`'s "an
unrun matrix is `unverified`, not a pass") resolve the same way — **name the residual, never a
silent pass** (`SKILL.md` principle 2: an absence is evidence only after a positive control fires);
they differ only in cause — here the gate ran green *once*, there it never ran.

## A gate's committed fixture is part of its contract — a clean-clone gate must be satisfiable without the gitignored data

A gate that asserts real-data-shaped output — required copy, a populated section, a field's
presence — is honest on a clean clone only if the **committed fixture** can produce what it
checks. If the sample fixture omits the fields the assertion needs (they live only in the real,
gitignored bundle), the gate is **red on a clean clone by construction**: green for anyone
working from a populated checkout, red for everyone on a fresh clone/worktree, while the repo's
own "green `verify` from a clean clone" Definition-of-Done claim is quietly false.

The committed fixture is part of the gate's contract. Resolve it one of two ways:
- **Enrich the fixture** so it exercises every field/section the gate asserts (a clean clone can
  render every required-copy check), or
- **Scope the real-data-only assertions to a real-bundle run**, and on the clean-clone run assert
  only what the fixture can produce.

Verify by running the gate from a **truly clean clone** (no gitignored data present), not from
your populated tree: red there means the fixture or the assertion scope is wrong, and any "green
from a clean clone" claim stays `unverified` until it holds — the resolving artifact is the clean
run, not the convenient one (`SKILL.md` principle 3). **Signal:** when several contributors
independently hit the *same* gate failure and each "fixes" it by copying the real gitignored data
into their checkout, the defect is the fixture/gate contract, not their environments — the
workaround masks a standing Definition-of-Done violation.

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

## A negative-assertion (assert-absent) test is a ratified constraint — never loosen it to ship a conflicting feature

A test that asserts something is **absent** — `assert.doesNotMatch(brief, /ProgressBar/)`, "no
attainment %", "no dashed drop-target" — encodes a **deliberate, often-ratified design
constraint**: *this surface must not show X.* When a new feature request conflicts with one
("add progress bars" vs a Brief that pins **no** `ProgressBar`), an agent faces a fork:
- **Wrong:** delete or loosen the guardrail to make the feature pass — the code-review equivalent
  of pulling the smoke detector. It **silently reverses a ratified decision** and removes the very
  record that decision left behind.
- **Right:** read the negative test as **evidence the constraint is intentional** — ship only the
  part that doesn't violate it, and report the conflicting part as **BLOCKED-ON-OWNER** (they can
  split / reopen, or loosen the test themselves, explicitly). (Observed: a lane asked for a live
  OKR dashboard added the honest **coverage** stat but **not** an attainment-% meter, because a
  guardrail test pinned the omit-percentage contract — a test-layer enforcement of *show coverage, not
  a grade* in `product-ux-quality.md`.)
- **Review lens:** a diff that **loosens or removes an assertion — especially an absence
  assertion — while adding a feature** is a red flag: check whether it silently reverses a
  recorded decision. Changing a ratified constraint is an **explicit, owner-visible** decision (its
  own reasoned commit), never a side effect of a feature PR. Distinct from the retired-coverage
  case above (a spec dropped because its surface became *unreachable*, owed a named gap): here the
  surface is reachable and the constraint is **still intended** — the test is not stale, it is
  load-bearing.

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
- **An LLM judge carries known biases — test for them structurally and cheaply,
  before trusting its scores.** Beyond temperature 0 and the frozen-cohort validation
  above (Zheng et al., 2023 document position, verbosity, and self-enhancement biases
  in strong judges): **(a) order-swap consistency** — for any pairwise/comparative
  judge, run it twice with the candidates' positions swapped; a flipped verdict is
  **positional bias** in the judge prompt itself, caught with two calls and zero human
  labels. **(b) judge/subject independence** — when the system under test and the judge
  share a model or vendor family, flag **self-preference** bias risk explicitly. **(c)
  verbosity correlation** — on the labeled cohort, check the judge's score against
  output length; a strong positive correlation with no length-normalized rubric is
  evidence it rewards length, not quality. And **name the agreement bar** the
  frozen-cohort check must clear — strong judges reach roughly **≥80%** agreement with
  human preference (Zheng et al., 2023) — and **re-check it when the judge model version
  changes**: an unpinned judge is the same latent-bug class as an unpinned embedding
  model (`data-quality.md`).
- **A retrieval-augmented (RAG) app is evaluated at the retrieval seam, not only
  end-to-end.** The generation-grounding check above is necessary but not
  sufficient: a faithful answer over the *wrong* retrieved context is still wrong,
  and a good end-to-end score can hide a retrieval miss the model papered over from
  parametric memory (which then fails silently when the knowledge base changes).
  Evaluate the two stages separately — **retrieval quality** (context *precision*:
  retrieved chunks are relevant; context *recall*: the needed facts were retrieved
  at all — measured @k, with chunk-boundary loss and reranking in view) and
  **generation faithfulness** (is the answer factually consistent with *that*
  retrieved context — groundedness), with **answer relevancy** (does it actually
  address the question) as a separate check. (RAG = a parametric generator plus a non-parametric
  retrieval component over external knowledge — Lewis et al., 2020. The metric names
  are operationalized by open-source eval libraries, e.g. RAGAS — a *tool*, not a
  standard: frame the concept, don't pin a vendor's exact formula.)
- **A RAG app is also evaluated at the *context-assembly* seam — input budget and
  chunk placement, not only retrieval.** Two silent-failure checks between "the right
  chunks were retrieved" and "the model answered": **(a) input-budget overflow** — when
  the top-k chunks exceed the model's context budget, is the check computed with the
  target model's **actual tokenizer** (not a char/word estimate), and on overflow are
  **whole lowest-ranked chunks dropped**, never a chunk **truncated mid-content** (a
  mid-cut fact or citation the model then completes or misattributes)? Force the overflow
  in a test and assert no partial chunk reached the prompt, the dropped chunks were the
  lowest-ranked, and the drop was counted/logged. **(b) placement, not just fit** — even
  when everything fits, a chunk ranked below #1 but still needed for the answer should sit
  at the **start or end**, not left buried mid-concatenation in raw retrieval-score order
  (ranking is imperfect, so the chunk with the answer is not always the #1 hit): models access "relevant
  information in the middle of long contexts" markedly worse ("Lost in the Middle," Liu et
  al., 2023). This is **per-call prompt arithmetic** — distinct from a long-running agent's
  conversation compaction (`security-ai-agents.md`) and from an output `max_tokens` cap
  (that bounds what comes *out*; this bounds what goes *in*).
- **An agent (tool-using, multi-step) is evaluated on its trajectory, not only its
  final answer.** Score tool-call *selection* (did it pick the right tool), tool-call
  *arguments* (well-formed, correctly bound), and multi-step *task completion* (the
  sequence reached the goal without an unrecoverable wrong turn). A right final
  answer reached via a lucky or unsafe path is a latent failure, and a wrong tool
  choice is invisible to an output-only bench.

## ML pipeline correctness — data leakage & training reproducibility

Distinct from AI evals above (which score a model's *output*): these are the
*pipeline* defects that make a reported metric **false** — the classical-ML sibling
of the LLM golden-set contamination rule. (Temporal / as-of *feature* leakage in a
train/serve pipeline is in `data-quality.md` §12; this is the train/test
split-hygiene and reproducibility half.)
- **Split first; never fit on test.** Data leakage is "information that would not be
  available at prediction time is used when building the model," giving "overly
  optimistic performance estimates" (scikit-learn). Check: the data is **split into
  train/test before any preprocessing**; a scaler / encoder / imputer is **fit on the
  training subset only** (fitting on all data leaks the test distribution — a
  Pipeline keeps cross-validation and tuning from leaking); **no target leakage** (a
  feature derived from the label or from the future); and **no duplicate rows across
  splits**. A leaked split doesn't fail — it *passes too well*, so the tell is an
  implausibly high score, not an error.
- **The split must respect group and time structure, and resampling happens inside the split.** Beyond fit-on-train, the *split strategy itself* leaks when rows aren't i.i.d.: a plain `KFold` scatters **correlated rows that share a group** (many samples per patient / user / device) across train and test, so the model memorizes the group and the score doesn't predict a genuinely new group — "the i.i.d. assumption is broken if the underlying generative process yields groups of dependent samples"; use `GroupKFold`, which "ensures that the same group is not represented in both testing and training sets" (scikit-learn). For **time-ordered** data a shuffled `KFold`/`ShuffleSplit` trains on the future to predict the past — the same source warns these "would result in unreasonable correlation between training and testing instances ... on time series data"; use a forward-chaining `TimeSeriesSplit`. And **class-imbalance resampling (SMOTE / over- / under-sampling) belongs inside the fold, on train only**: resampling the whole dataset before the split both leaks and makes the *test set artificially balanced* — the model then "will not be tested on a dataset with class distribution similar to the real use-case" (imbalanced-learn) — so the metric describes a distribution production never sees. All three **pass too well** rather than erroring, the same tell as the leaked-split rule above. (Distinct from the as-of *feature* leakage in `data-quality.md` §12 — this is split *structure*.)
- **Training is reproducible, so a metric delta is attributable.** Retraining on the
  same data should yield the same model; unseeded RNG and unpinned data / model / code
  versions make a score change unattributable — you can't tell a real regression from
  noise. Seed the training RNG and pin the data + model + code version behind each
  reported number (Breck et al., *The ML Test Score*, 2017).

## ML in production — drift monitoring & safe model rollout

The lifecycle sibling of the two sections above: §"ML pipeline correctness" verifies the model
was **trained** honestly and `data-quality.md` §12 verifies a feature is **computed the same**
for training and serving — this is the **post-deployment** half, where a model that was correct
at ship time silently decays, or a swap ships a quietly worse one. Both are invisible to the
checks that guard training.
- **Monitor drift, not just uptime.** A served model **silently loses accuracy** (no error is
  thrown) as the live input distribution drifts from the training distribution **over time** —
  distinct from `data-quality.md` §12's train/serve *parity* check (two computation paths at one
  instant); this compares live inputs to the training baseline as time passes. Monitor the **input-feature
  distribution** and the **prediction distribution** (a sudden shift in either is the early
  signal), plus realized **performance against ground truth** — but **ground truth often lags** (the
  label for today's prediction lands days or weeks later), so quality is delayed and the thing
  you alert on in the meantime is a **proxy** (distribution shift, a confidence drop). A model
  with green infra dashboards and no distribution/quality monitoring is unmonitored where it
  matters (cf. the monitoring category of the ML Test Score cited above; the generic signal
  plumbing is `observability.md`).
- **Roll a new model out behind a quality gate, not a health check.** A new model version is a
  behavior change, not just a deploy — and **green error-rate and latency do not mean the new
  model is as good** (they miss a quieter, worse model). Prove the candidate on **prediction
  quality** first: **shadow** it (run it on live traffic in parallel, compare outputs, serve
  none), or **canary / champion-challenger** to a slice with a **prediction-quality** promotion
  gate (not just error/latency), keeping a **rollback path** to the incumbent. Because ground
  truth lags, a model canary needs a **longer, quality-based bake** than a code canary —
  promoting on a few minutes of green health is how a worse model reaches everyone. This
  specializes the generic canary/rollback discipline in `release-engineering.md` to the ML case,
  where the load-bearing signal is delayed prediction quality, not error rate.

## ML fairness — detect it in review, never certify it

**Scope gate — apply this first.** This lens applies only when the model makes a
**consequential decision about people** (credit, hiring, housing, moderation, benefits,
ranking that gates access) **and** the data carries at least one group dimension or a proxy
for one. If you cannot name the decision, the affected people, and a group dimension present
in the data, the lens **does not apply — say so and stop**. Hunting fairness in a model with
no protected-group dimension manufactures a finding — the "stricter than the standard" defect
(`method.md`).

Where it applies, bias is **systemic, statistical, and human** (NIST SP 1270); computational
metrics are necessary, not sufficient. The review question mirrors this suite's own thesis —
*not just whether the model is biased, but whether it does what is claimed* (NIST SP 1270).
Detect, do not grade:

- **Protected attributes and proxies.** Is a protected characteristic (race, sex, age, …) used
  as a feature — **disparate treatment** — or **not used but proxied** by a correlated feature
  (zip, name, device, purchase history) — **disparate impact**? A proxy claim is **demonstrated**
  — show the feature's correlation with the group attribute *in this data* — never asserted from
  a stereotype; and **absence of the protected attribute does not establish fairness**, since a
  model can discriminate through proxies alone. Dropping a suspected proxy without measuring
  outcomes is not a fix — it removes signal untested and other proxies may remain.
- **Fairness is measured, and the metric is chosen on purpose.** A consequential model gated
  only on **aggregate** accuracy carries no fairness signal — it can be accurate overall and
  systematically worse for a subgroup. Require a **disaggregated** evaluation by group, and
  require the team to **state which fairness metric they target and justify it against the
  decision** (demographic parity and error-rate balance answer different questions — the metric
  must fit the decision, not be picked for looking best). The **absence of any stated, justified
  choice** is the finding — not your preferred metric. Show coverage; never a fabricated
  "0% bias" (the coverage-not-grade rule; `product-output-safety` MEASURE).
- **Documentation.** On a consequential model, flag a **missing model card** — intended use,
  out-of-scope uses, and **per-subgroup** measured performance (Mitchell et al., 2019).
  `product-output-safety` (when installed) prescribes *producing* the card; in review, flag that
  it is **absent**.
- **Dataset bias is a data-quality dimension.** Group representativeness in the training set is
  the statistical-bias leg — measure it as a completeness/representativeness dimension under
  `data-quality.md` §4, do not re-derive it here.

**🚩** a consequential-decision model whose only gate is aggregate accuracy; a protected
attribute or a demonstrated proxy in the feature set with no disaggregated evaluation; a
"fair" / "unbiased" claim carrying no named metric, no per-group numbers, and no model card.

This is the **detection** lens for a default review; the output-harm guardrail — inventory the
bias harm, never certify "unbiased", report residual risk — is the `product-output-safety`
overlay, not restated here. Whether a demonstrated disparity is **unlawful
discrimination** is a legal determination — route it to counsel (`business-ops` Lane R names the
regime); the code finding is the **missing measurement or unstated metric**, never a legal verdict.

## Notebook review — hidden state & committed outputs (data-science code)

A Jupyter/Colab notebook is code with two failure modes a normal source review misses, both distinct from the
ML-pipeline correctness above:
- **Out-of-order execution → hidden state.** A notebook's results reflect the order cells were *run*, not
  top-to-bottom source order; an output can depend on a variable set by a cell since edited, moved, or deleted,
  so the committed `.ipynb` may not reproduce from a clean kernel. The only honest check is **Restart & Run
  All** (or `jupyter nbconvert --execute` / `nbclient` in CI) from a fresh kernel — a notebook that only works
  in its author's live session is not reproducible, and "it ran for me" is not evidence. 🚩 a committed
  notebook with non-monotonic `execution_count`s, or a CI that never executes it fresh.
- **Committed output cells leak data and secrets.** `.ipynb` stores cell *outputs* in the file: a printed
  `df.head()` with real rows (PII), an API token echoed in a repr, credentials in a traceback, a base64 image,
  or megabytes of data — committed into git history where a diff-scoped review never looks. Strip outputs before
  commit (`nbstripout`, a `--clear-output` pre-commit hook, or a CI gate); a secret that reached a commit is compromised and must be **rotated**, not just stripped (cross-ref `security-appsec.md` Secrets), and treat a committed output cell like any other emitted value (cross-ref `observability.md` Logs & traces and `privacy-compliance.md`). 🚩 an
  `.ipynb` with populated `outputs` / `execution_count` in the diff and no output-stripping gate.

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
as proof of correctness; a type-check / compile pass trusted as the full suite after a conflict
resolution; a property test whose generator is built from the invariant it asserts (passes vacuously);
a threshold lowered in the same diff that would otherwise
fail; a heavily skewed pyramid-or-trophy shape with no stated test philosophy
anywhere in the repo; a served ML model with no drift monitoring on its input or
prediction distribution; a new model version promoted on latency/error-rate alone,
with no prediction-quality gate, shadow/canary, or rollback path; an
absence / negative assertion loosened or removed in the same diff that adds a
conflicting feature (silently reversing a ratified must-not-show-X constraint); a fix for a
nondeterministic or costly-to-repeat failure shipped on a single green run with no named residual
(validated is not happened-to-pass-once), or an unproven refactor scope-crept onto an
otherwise-validated PR; a reliability fallback path (circuit-open, retry-exhausted /
dead-letter, cache-miss serve-stale, generation-failure) whose only evidence is a fired-counter or a
one-time game-day, with no test that forces the trigger and asserts the branch's output.
