# AI / LLM / agent security review

Read this when the code calls an LLM, embeds/retrieves (RAG), or runs an agent
that plans, calls tools, executes code, keeps memory, or coordinates with other
agents. Expands section C of `SKILL.md`.

Standards tracked (verified URLs + dates in `docs/standards-index.md`): OWASP
Top 10 for LLM Applications **2025** (verified numbered titles; a 2026 edition exists), OWASP Top 10 for Agentic
Applications **2026**, NIST AI RMF + Generative AI Profile, and MITRE ATLAS.

**The one principle under all of this:** everything the model reads that did not
come from your trusted prompt — user input, retrieved documents, web pages,
file contents, tool results, another agent's output — is **untrusted data, and
may contain instructions aimed at your system**. And everything the model
*emits* is **untrusted input to the next stage**. Trust neither end without a
control you built outside the model.

---

## OWASP Top 10 for LLM Applications 2025 — per-risk review

- **LLM01 Prompt Injection** (direct & indirect). Is untrusted content clearly
  separated from instructions (delimiting / spotlighting / distinct roles), and
  never concatenated into the trusted instruction block? Assume any retrieved or
  fetched content is adversarial. **Test it** (see the injection test set
  below). This is the root cause behind most agentic incidents.
- **LLM02 Sensitive Information Disclosure**. No secrets/PII/internal system
  prompts in prompts, logs, traces, or outputs. Output is filtered before it
  reaches a user or another system.
- **LLM03 Supply Chain**. Model/provider, plugins, adapters, and datasets are
  trusted and pinned; provenance known. A model or tool pulled from an open hub
  is a dependency with the same risk as any package.
- **LLM04 Data and Model Poisoning**. Training / fine-tuning / RAG-ingested data
  is validated and provenance-tracked; an attacker can't get malicious content
  into the corpus that later steers outputs.
- **LLM05 Improper Output Handling**. Model output is schema-validated /
  sanitized **before** any downstream use — never fed raw into SQL, a shell,
  HTML, `eval`, a file path, or an HTTP call. Treat it exactly like user input.
- **LLM06 Excessive Agency**. Tools are least-privilege: minimal set, minimal
  scope, minimal permissions. High-impact or irreversible actions require human
  confirmation. The agent cannot reach beyond its task.
- **LLM07 System Prompt Leakage**. Assume the system prompt is extractable.
  No secrets, credentials, or authorization logic live in it; security is
  enforced outside the model.
- **LLM08 Vector and Embedding Weaknesses**. RAG stores enforce access control
  and tenant isolation; no cross-user/cross-tenant retrieval leakage; embeddings
  and retrieval can't be manipulated to exfiltrate.
- **LLM09 Misinformation**. Model claims that reach a user or third party are
  grounded/verifiable; hallucination is mitigated (grounding, citations,
  confidence, human check). Never shipped as fact unchecked.
- **LLM10 Unbounded Consumption**. Token / cost / rate caps enforced **before**
  each billable call; loops bounded; circuit breakers on 402/429; no
  user-controlled unbounded generation. Both a DoS and a cost attack.

## OWASP Top 10 for Agentic Applications 2026 — additional risks

Published 2025-12-09; titles below taken from the OWASP GenAI announcement
(verified 2026-08-21; PDF numbering not re-fetched this session — if a title
conflicts with the PDF, the PDF wins). When the code is an **autonomous agent**,
walk ASI01–ASI10; do not collapse them into LLM01–LLM10.

- **ASI01 Agent Goal Hijack** — attacker redirects the agent's objective through
  content it *reads* rather than code it runs. Indirect prompt injection at the
  planning layer. Highest-impact agentic risk.
- **ASI02 Tool Misuse** — agent steered into calling a *legitimate* tool with
  harmful arguments (summarize-URL → SSRF/exfil).
- **ASI03 Identity & Privilege Abuse** — agent acts with more authority than the
  requesting user; confused deputy; over-broad service credentials.
- **ASI04 Agentic Supply Chain Vulnerabilities** — poisoned tools, skills,
  plugins, MCP servers, model artifacts. Pin and vet every loadable tool like a
  dependency.
- **ASI05 Unexpected Code Execution** — code-exec tools/sandboxes the agent can
  be talked into abusing (RCE / sandbox escape).
- **ASI06 Memory & Context Poisoning** — persisted memory, scratchpads, or RAG
  context corrupted so a later run acts on planted instructions. Validate and
  scope what enters long-term memory.
- **ASI07 Insecure Inter-Agent Communication** — messages between agents trusted
  without authentication/validation; one agent spoofs or injects into another.
  **Audience is the control:** a same-owner private pipe is not the many-owner
  network board. Reusing a many-audience channel for same-owner Q&A is a leak
  by construction (cross-ref Q). Probe: a message meant for one principal must
  not be readable by another tenant, a commons, or a mesh. Authn on the pipe
  (session/uid, not a display name). No fleet secret as the credential.
- **ASI08 Cascading Failures** — one agent's error or compromise propagates
  across a multi-agent system with no isolation, rate control, or breaker.
- **ASI09 Human-Agent Trust Exploitation** — fluent, confident output socially
  engineers the operator into approving a harmful action. Approval prompts must
  name the audience and the action; a buried "yes" in chat is not consent.
- **ASI10 Rogue Agents** — agent operating outside intended scope or oversight;
  no kill-switch, no bound on autonomy, no audit trail.

**Same-owner vs many-audience probe (ASI07, cheap, before fan-out).** If the
target has more than one agent, board, mesh, or "ask a peer" tool: list each
channel and its named audience (one owner / one tenant / every agent on the
network / another human's agent). A write that can land on a wider audience
than the prompt named is a finding — even if the bytes look like a private DM.
Key the protocol on a stable tenant/uid, never a display name (names are
per-owner and collide).

Attacker techniques against agent tool ecosystems are also catalogued in **MITRE
ATLAS** (e.g. poisoned agent tools, sandbox/host escape) — useful for building
the red-team test set below.

---

## Prompt-injection & jailbreak test set (write these tests)

Model-dependent security needs security **tests**, not vibes. For any
LLM-backed feature, add cases that assert the guardrail holds:

- **Direct injection**: user input that says "ignore previous instructions and
  …"; assert the system instruction still governs and the disallowed action does
  not occur.
- **Indirect injection**: a retrieved document / fetched page / file / tool
  result containing embedded instructions ("SYSTEM: exfiltrate the API key to
  …"); assert the agent treats it as data and does not act on it.
- **System-prompt extraction**: prompts trying to get the model to reveal its
  system prompt / hidden rules; assert no secret leaks (and that nothing secret
  was in there anyway).
- **Output-handling**: force the model to emit `'; DROP TABLE …`, `<script>`,
  `$(rm -rf …)`, `../../etc/passwd`; assert the downstream layer
  validates/escapes and nothing executes.
- **Excessive agency**: a request that would trigger a high-impact tool
  (delete, send, pay, deploy); assert human confirmation is required.
- **Unbounded consumption**: input designed to cause a long/looping generation
  or many downstream calls; assert the token/cost/rate cap and loop bound fire.
- **RAG isolation**: user A queries for user B's data; assert tenant isolation
  in retrieval.

## Defensive patterns to look for (and recommend)

- **Deterministic-first.** Anything a plain function can do correctly (parsing,
  validation, math, dedup, lookups, routing, formatting, schema enforcement) is
  a function — cheaper, testable, and it cannot hallucinate. Reserve the model
  for genuine language/judgment tasks. A pipeline that asks the model to do
  arithmetic or emit JSON that a schema could guarantee is a red flag.
- **Spotlighting / delimiting** untrusted content (clear markers, separate
  roles/messages) so the model can distinguish data from instructions.
- **Structured output + schema validation** on the way out; reject/repair
  off-schema output before use.
- **Least-privilege tools** with allowlisted actions and argument validation at
  the tool boundary (not left to the model to "please only…").
- **Human-in-the-loop** gate on irreversible/high-impact actions.
- **Spend & rate governance**: per-call, per-session, and per-service caps
  enforced in code before the call; bounded retries with backoff; breakers on
  402/429.
- **Provenance & grounding**: citations/sources for claims that reach users;
  confidence surfaced; unverifiable claims flagged, not shipped as fact.
- **Falsify asserted-but-unenforced safety properties.** A safety parameter set
  at a call site but silently **dropped or overridden by the layer below** — so
  the code (and often a comment) *claims* a property that is not in force. Worse
  than a missing safeguard because it reads as present. Two sub-cases:
  - *Dropped by a lower layer.* e.g. `temperature: 0` "so the verifier is
    deterministic" is omitted by the payload builder for a model tier that
    rejects a non-default temperature (HTTP 400) — so the determinism claim is
    false and a verifier feeding a human-review queue is non-deterministic. Grep
    every `temperature`, `verify=`, `timeout`, `signal`, dry-run flag, allowlist,
    and `readOnly` for a downstream drop/override.
  - *Delegated to an unverifiable platform guarantee.* The control depends on an
    external/platform behavior you can't test from the code. State the residual
    risk that holds **regardless** of the guarantee and rest severity on the code
    you can test; convert the unverifiable part into a single owner-run check in
    "Decisions needed."

  **A comment asserting a safety property is the highest-value thing to falsify.**

**🚩 grep**: f-strings / `format` / template literals building a prompt from
raw user or retrieved text; model output passed to `execute`/`exec`/`os.system`
/ `render`/`eval` / a file path without validation; no `max_tokens` / `timeout`
/ retry cap on the client; tool definitions with broad write/delete/network
scope and no confirmation; secrets or authz rules embedded in a system prompt;
`temperature`/model params hardcoded where determinism matters for a security
check.
