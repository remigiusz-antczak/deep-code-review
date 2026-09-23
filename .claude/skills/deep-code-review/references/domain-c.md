# Domain C checklist

Read this when domain C (Security — AI / LLM / agents) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### C. Security — AI / LLM / agents → `references/security-ai-agents.md`
Apply if the code calls an LLM, embeds/retrieves, or runs an agent. Maps to
OWASP Top 10 for LLM Applications **2026** (LLM01–LLM10:2026) and the OWASP
Top 10 for Agentic Applications 2026. When the target **is or installs a
skill**, also walk AST01–AST10 in `references/security-agent-skills.md`. Eval
depth (golden sets, judge calibration, the context-assembly seam):
`references/testing-ai-evals.md` — read it when model-dependent output needs a
test or eval gate.
- **Untrusted-in / untrusted-out**: everything the model reads that isn't your
  trusted prompt is data that may contain instructions; everything it emits is
  untrusted input to the next stage. Fence/delimit untrusted content; **strip
  control chars and zero-width/bidi Unicode** (invisible-instruction smuggling)
  and cap length; **schema-validate every output before any use**; never feed
  raw output into SQL/shell/HTML/`eval`/a path/a fetch. Watch the **multimodal
  blind spot** — text inside images/PDFs bypasses text-layer sanitization.
- **Authorize in the infrastructure, not the prompt** — default-deny tool /
  command allow-lists; re-check authorization **fail-closed inside** tool
  execution, not only at the tool-offer layer. **Least-privilege tools**;
  human-in-the-loop on irreversible/high-impact actions; scope every
  approval/consent token to the specific action **and stage** it authorizes.
  **Prove the re-check fires at runtime** — a self-proof / health check that
  exercises it — not merely that the code path exists; an unproven tool-authz gate
  must fail closed, or it is a finding (the runtime-proven-gate lens, domain B).
- **Deterministic-first**: the model never authors a number, score, status,
  gate, **or the current date/time** — deterministic code does; the model only
  phrases/adjudicates behind hard gates, with a deterministic fallback and a
  counter for how often it fires. Use
  **temperature 0** for judges/verifiers. Ground claims to the input;
  **log a redacted fingerprint** of output, never the raw text.
- **Bound consumption** (LLM06:2026, was LLM10:2025): token/cost/rate caps enforced *before* each
  billable call; loop caps; breakers on 402/429; a **no-model fast path** for
  rejected/unauthenticated input so a flood can't burn budget.
- **A prompt assembler needs an explicit input budget and drop-priority** — any single
  call that concatenates a system prompt + history + tool output + user input (RAG is one
  case, not the only one) overflows silently and typically sheds the *earliest* text, i.e.
  the **system instructions**, so the model stops following its own rules with no error.
  This is **per-call** assembly, distinct from the long-running-agent compaction/memory
  case (🚩 below) — the budget + drop-priority + placement seam check is
  `references/testing-ai-evals.md` (context-assembly seam).
- **A safety param set at a call site is a claim, not a guarantee** — confirm the
  layer below actually applies it. A `temperature`, `verify=`, `timeout`, `signal`,
  dry-run flag, allowlist, or `readOnly` can be silently dropped/overridden by a
  lower layer, or delegated to an unverifiable platform guarantee; a comment
  asserting a safety property is the highest-value thing to falsify (the class
  and its two sub-cases are in `references/security-ai-agents.md`).
- 🚩 f-string/format prompts from raw input, output → `execute`/`render`
  unchecked, no `max_tokens`/`timeout`/retry cap, broad-scope tools with no
  confirmation, secrets/authz in the system prompt, a safety param asserted at
  the call site but dropped downstream, a same-owner ask written to a
  many-audience board/mesh, inter-agent messages keyed on a display name
  instead of a tenant/uid, an approval prompt that does not name the audience, a
  long-running agent whose compaction/memory can silently drop a safety
  constraint or whose sub-agents run without the parent's cap (context/memory
  lifecycle — depth in `references/security-ai-agents.md`).
