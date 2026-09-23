# Domain J checklist

Read this when domain J (Testing & evaluation) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### J. Testing & evaluation → `references/testing-and-evals.md`
Match coverage to what the project does; skip inapplicable types rather than
writing theater. Conditional depth: `references/testing-ui.md` when the target
ships rendered UI or browser / E2E specs; `references/testing-ai-evals.md` when
it has model-dependent output; `references/testing-ml.md` when it trains or
serves a model or commits notebooks.
- **Unit / integration / e2e / regression / security / property-fuzz /
  snapshot-weight-pin / AI-evals / non-functional** — apply what fits.
- **Test the failure, not just the feature** (every guard/refusal path);
  **red-first** (watch it fail before it passes); **adversarially test the
  checker itself** and self-test gates against a planted defect so a check can't
  rot into a no-op; **skip loudly** over absent input (never green over unread
  input); **verify the served response, not the repo**; keep tests **hermetic**;
  **probe the real fixture before pinning an expected value**.
- **AI evals** for model-dependent output: a labeled golden set with an accuracy
  threshold that **gates prompt/model-version changes**; the harness's own
  scoring is pure + unit-tested; self-consistency ≠ precision.
- 🚩 tests that assert nothing, trivial mocks, no test for the reported bug,
  hidden `skip`/`xfail`, coverage gamed, an AI feature with only mocked tests,
  **a test that writes a real tracked/shared data path instead of a temp dir —
  especially when cleanup lives only in `finally`/`try` that `process.exit` /
  SIGINT / overlapping runs can skip** (depth: `references/testing-and-evals.md`).
