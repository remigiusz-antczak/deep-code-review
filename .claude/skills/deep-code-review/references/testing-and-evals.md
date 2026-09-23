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
- **AI evals** — for any model-dependent output (see `testing-ai-evals.md`).
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
- **Before you write that fallback test, confirm the fallback *exists*: a doc-comment can enumerate a branch the body never implements — so there is no code for a dead-code or coverage tool to flag.** The bullet above assumes the fallback is present and merely unexercised; the sharper defect is a docstring that promises resolution/degradation steps in sequence ("matches exactly, else falls back to a fuzzy/alias match, else gives up"; "on timeout, retries against the replica") when the body implements only the first step and unconditionally returns the not-found/error result otherwise. The described branch has **no code path at all — only its description exists** — which makes it invisible to exactly the tools a reviewer trusts: a dead-code or lint pass sees **no unreachable statement** (there is no branch to flag), and coverage stays **green** (there is no line to leave uncovered).
  Fixtures never expose it either, because the primary path satisfies every already-normalized value the suite and today's production data happen to carry; the gap only bites when a real user or a new data source supplies the more natural input the fallback was *documented* to handle, and a resolvable reference then silently degrades (to unlinked text, a hard error, an unhandled timeout) with no signal. Only reading the doc **against** the code catches it.
  Detection is mechanical: for every exported symbol whose doc-comment names more than one behavior / fallback / error, list each promised branch, grep the body for a corresponding code path, and confirm a test **forces its triggering condition** — a promised branch with neither code nor test is the finding (trying to write that forcing test is itself what surfaces the absence: there is nothing to make it pass). Report it even when today's data can only ever reach the primary path — "currently unreached" is a property of today's fixtures, not of the code's correctness — at reduced severity, but state plainly whether it is reachable now (same latent-but-reported discipline as `data-quality.md`'s bare-id merge rule).
  Fix by implementing the branch (with the forcing test above) **or** by correcting the comment to claim only what the code does; the doc fix is cheap and is **never skipped even when the real fix is deferred**, because an inaccurate contract comment actively misleads the next caller — who relies on it *without* re-reading the implementation — into depending on behavior that isn't there, which is worse than no comment. This is **not** the stale-comment case (a comment that was once true and drifted — e.g. a suppression/allowlist entry's justification that has gone stale; `method.md`'s carried-forward-justification rule) — it was never true — and **not** `security-ai-agents.md`'s asserted-but-unenforced safety property (there the code exists at the call site and a lower layer drops it; here there is no code for the promised branch at all); it is the source-doc-comment, test-limbed specialization of `docs-and-dx.md`'s "reconcile load-bearing claims against the code."
- **Probe the real function on the real fixture before pinning an expected
  value.** Never hand-guess an expected string — a guessed expectation encodes a
  misunderstanding as a green test.
- **A regression test's oracle must be independent of the code under test —
  never derive `expected` by running the very detector being tested.**
  Confirming a checker catches a defect by running it on the fixture and
  copying its own output as `expected` is circular: the test can only ever
  agree with whatever the checker currently does, so a real defect ships baked
  into its own expected value and the test passes forever, unable to catch it
  (the failure mode: a self-referential oracle hid a real defect). This scopes
  the probe-the-real-function bullet above to *already-trusted* behavior — it
  never licenses generating a detector's own regression oracle from itself.
  Build the oracle independently: a hand-verified fixture, a planted defect
  whose verdict is known before the gate ever runs (the planted-defect matrix,
  `SKILL.md`), or a value computed by a different method. Discriminator vs the
  tautological-generator bullet below: same self-reference, opposite side —
  that generator samples from the rule it asserts; this oracle is computed by
  the code it asserts against.
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
  the production build — `method-situational.md`; this is capturing *feature* evidence past an
  auth gate.)
- **Meaningful assertions.** Not `assertTrue(true)`; not a mock that makes the
  test pass trivially; not coverage inflated by tests that assert nothing.
- **A deep-equality assertion on a large or *cyclic* object graph can *hang* the runner
  instead of failing fast.** Passing a big, deeply-connected, or self-referential object as
  the `actual` value of an equality assert (`assert.deepEqual`, `expect(node).toEqual(...)`,
  an `assertEqual(node, expected, msg)` with the whole live node as the first arg) makes most
  assertion libraries **deep-traverse and pretty-print** that value to build the failure diff —
  and on a large or circular graph that formatting step blows the test-runner's per-test
  timeout, so a check that *should* fail in a millisecond instead **times out** with no usable
  diff and reads as a slow/flaky suite rather than the real assertion failure. The trap is
  worst exactly when the assert is *meant* to fail (the value is wrong), because the failure
  path **is** the expensive-formatting path — a passing run never triggers it, so it slips
  every green CI. Assert on a **small scalar drawn from** the object — an `id`, a `length`, a
  status flag, a bounded serialized projection — never the live node itself; if structure must
  be compared, snapshot a **bounded, acyclic** projection. (A cyclic graph also throws
  `TypeError: Converting circular structure to JSON` under a naive `JSON.stringify` expectation
  — a louder symptom of the same "don't hand a live object graph to a formatter" root cause.)
  Distinct from the weak-assertion bullet above: that asserts too *little*; this asserts on too
  *much*, and the whole cost lands on the failure path where no green run exercises it.
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
- **A fixed-duration `sleep(N)`-then-assert is a timing bet a busy CI lane loses — assert the
  observable readiness signal, not wall-clock duration.** The wait assumes N ms always suffices;
  under multi-lane CI (several jobs contending for the same host's CPU) the identical operation
  that finishes in 50ms alone can take 600ms starved, so a 500ms wait flakes only under load —
  never locally, where nothing contends — and reads as environment noise rather than a timing bug
  in the test itself. Poll for the actual condition (an emitted event, a changed node, a resolved
  promise) with a generous upper bound; never assert against a fixed sleep. Distinct from the
  chronically-flaky-test bullet above — that is the *triage* once a test is already known-flaky
  (quarantine + fix root cause, one clause of which is this same await-not-sleep fix); this names
  the CI-contention *trigger* so the test is authored correctly the first time.
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
- **When one check is copy-pasted per sibling field/type, diff the copies' *guard
  conditions*, not just their overall shape.** A reconciliation or diff check — compare an
  authored/declared value against a derived/computed one and flag disagreement — is often
  written **separately for each of N sibling fields or entity types** (one block per column,
  per resource kind, per metric), the N blocks near-identical but for the field they name.
  Read one at a time, every block looks internally consistent and plausible, so the review
  waves each through. The bug that hides here is a **dropped edge-case guard in exactly one
  copy** — an `if (authored == null) continue`, a "skip legacy rows", a rounding/tolerance
  clause, a "both sides present" precondition — that the *other* copies keep and this one lost
  (a bad merge, a hand-edit, a copy taken before the guard was added). It leaves **no idiom to
  grep** (the copies differ by design, by field name) and no single copy reads as wrong; it is
  visible only **relative to its siblings**. Detection: line the N copies up and **diff their
  guard/branch conditions against each other**, treating the set as mutually cross-checking —
  the copy with one fewer guard clause than the rest is the finding. Fix: collapse the N copies
  into **one parameterized check** (the no-duplication cure — then there is one guard set, not
  N to keep in sync); if they must stay separate, restore the missing guard and add a test that
  pins the shared precondition across all of them. Distinct from the outward/inward completeness
  sweeps in `method.md` (those propagate or verify **one fix** across the tree or within the
  fixed file, greppable by a shared idiom; this cross-diffs **N pre-existing parallel copies**
  whose only shared signal is their *structure*, driven by no fix), from the coherence test
  above (which runs one fixture through mirrored paths asserting *identical* output —
  inapplicable when each copy targets a different field), and from the sentinel-sibling
  comparator in `lang-js-ts.md` (value-set completeness inside **one** function;
  this is guard-set parity across **N** functions).
- **A store with interchangeable backends fails on the one the tests never instantiate — and a
  faithful fake cannot catch it.** When one interface has several implementations chosen at runtime
  (an in-memory/file store for dev/CI, a SQL database in prod), a field added to the model must be
  threaded through **every** backend's write/read/serialize path. The trap is that this is *not* a
  drifting double: the in-memory store keeps the whole object, so it retains the new field for free
  and has **no place for the omission to live**, while the SQL backend carries a failure surface the
  fake's mechanics don't possess at all — a hand-written `INSERT`/`UPDATE` column list (or a
  migration, or a DTO mapping) with no compile-time tie to the model type, so the field is silently
  dropped on the production path while every test stays green. The check a reviewer skips: **a green
  run proves nothing until you read which implementation the harness instantiated** — that lives in
  the test config, not the diff, and if it's the fast fake, the SQL path was never run. Detection:
  grep the SQL backend's `INSERT`/`UPDATE`/`SET` (and any history/mirror sync) for the new column — a
  field present in the type but absent from an `UPDATE`'s `SET` is the signature — and round-trip the
  new field create→edit→read-back through the **production** backend, not the default fake (the
  both-paths coherence test above), or derive the column list from the type so it can't drift.
  Distinct from the test-double-fidelity rule in the taxonomy (a double whose *returned shape* is
  wrong; here the fake is behaviorally correct, just more permissive than the real store) and from
  `data-quality.md` §6's dual-registered-entity rule (which store *owns* a field across two co-existing
  stores; this is one write through one of two implementations of the same store).
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

## Conditional depth — load only what the target has

- Rendered UI, browser, or E2E specs → `testing-ui.md` (layout geometry, pre-hydration capture, rewritten specs, state-dependent specs).
- Model-dependent output (LLM features, RAG, agents) → `testing-ai-evals.md`.
- Classical ML pipelines, served models, fairness, or notebooks → `testing-ml.md`.

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
  case in `testing-ui.md` (a spec dropped because its surface became *unreachable*, owed a named gap): here the
  surface is reachable and the constraint is **still intended** — the test is not stale, it is
  load-bearing.

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
