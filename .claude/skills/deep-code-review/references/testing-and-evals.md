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
  tautological-generator bullet (`testing-situational.md`): same self-reference, opposite side —
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
- **Meaningful assertions.** Not `assertTrue(true)`; not a mock that makes the
  test pass trivially; not coverage inflated by tests that assert nothing.
- **Deterministic & hermetic.** No real network, no real DNS, no writes outside
  a temp dir, no wall-clock/timezone flakiness. Inject a **seam** (a resolver, a
  store directory, a clock) rather than the real dependency. When a module
  latches config at import time, set the temp config **before** the first
  import. Sanitize the environment passed to any spawned subprocess down to an
  explicit allowlist — children inherit the full parent env by default, which
  both leaks secrets and lets a test operate on real shared state.
- **Randomized test order + a logged seed.** A suite that always runs in file / declaration
  order can pass not because its tests are independent but because they always run the one
  order that happens to work — hiding inter-test state pollution (a module-level cache, a
  shared fixture, a leaked singleton, an env var one test sets and another reads). Run with
  **randomized order and a recorded seed** (`pytest-randomly`; Jest `--randomize` +
  `--seed`; JUnit `MethodOrderer.Random`); a failure that appears only under randomization
  is real order-dependence, and the same seed reproduces it. Keep it on in CI so a new
  coupling surfaces immediately. Distinct from the *environment* determinism above
  (network/DNS/clock) — this is **execution-order** coupling between tests.
- **Tests must not write real shared/production data paths.** A suite that
  points the server-under-test at a tracked, shared, or default data directory
  (no temp-dir / network-dir override) will intermittently corrupt real state —
  especially when "restore" lives only in `finally`/`try`/`afterEach` that a
  hard exit (`process.exit`, SIGINT, worker crash) or overlapping runs can skip.
  Rate as High/Critical by consequence (data loss, PII mix-up, flaky CI that
  mutates the operator's machine). Fix pattern: inject a store root, default
  tests to an OS temp dir, make cleanup signal-safe or use unique per-run dirs
  the OS reaps. Cross-ref domain G when the path is also a concurrent writer.
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

## Conditional depth — load only what the target has

- Rendered UI, browser, or E2E specs → `testing-ui.md` (layout geometry, pre-hydration capture, rewritten specs, state-dependent specs).
- Model-dependent output (LLM features, RAG, agents) → `testing-ai-evals.md`.
- Classical ML pipelines, served models, fairness, or notebooks → `testing-ml.md`.
- A doc-comment promising a fallback, a conflict resolution, property/fuzz/mutation assurance or a coverage figure cited as assurance, a hanging equality assert, a shelled real binary, flaky tests / retries / fixed sleeps, a spawned-job alert, N copy-pasted sibling checks, interchangeable store backends, a one-green-run fix, a gate needing gitignored data, or a loosened assert-absent test → `testing-situational.md`.

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
