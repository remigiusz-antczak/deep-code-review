# Testing & evaluation review

Read this to judge whether the target is *actually* verified — not whether a
coverage number is high. Expands section J of `SKILL.md`. Match coverage to what
the project does; **skip test types that don't apply rather than writing
theater.**

---

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
- **Adversarially test the checker itself.** A gate/validator/parser is code
  too: feed it null-resolution, truncation, substring false-matches, empty
  input. In CI, **self-test every gate against a planted defect** so a check
  can't silently rot into a no-op that passes everything.
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
- **Coherence test for necessarily-duplicated logic.** Where logic is mirrored
  (a port, a re-implementation, a circular-import copy), link the source of
  truth in a comment **and** add a test that runs one fixture through both paths
  and asserts identical output.
- **Honest coverage taxonomy.** State what is automated vs. operationally
  checked vs. human-reviewed vs. not-applicable-with-reasoning. Document
  coverage gaps and skipped tests; never claim an assurance you don't have.

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
"update if it changes"; tests that hit the real network or real services; an AI
feature with only mocked unit tests and no eval bench; a coverage % cited as
proof of correctness; a threshold lowered in the same diff that would otherwise
fail.
