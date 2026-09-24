# Threat modeling — a diff-scoped procedure

Read this when a change adds a trust boundary, an auth path, a data flow to a new party, an agent or tool capability, or a file or network input, and the review needs a threat model sized to the diff rather than to the whole system. Which method fits (STRIDE, PASTA, attack trees, LINDDUN, MAESTRO) and the "coverage, not ceremony" lens live in `appsec-design.md`; this file is the procedure you run once the method is picked.

The four steps answer the four questions shared by the Threat Modeling Manifesto and the OWASP Threat Modeling Cheat Sheet: *What are we working on? What can go wrong? What are we going to do about it? Did we do a good enough job?* Time-box it to minutes. Record it in the report (`report-format.md`): the summary on the Ground truth "Threat model" line, each open threat as a Findings row (Area `Security/<category>`), each mitigation proven by a test as an Invariants row, and each accept or transfer under Decisions needed (owner). A model of the diff, finished, beats a model of the system nobody finishes.

**Skip rule.** A change that crosses no new boundary (a refactor behind an unchanged interface, a copy edit) gets one line — `Threat model: no new boundary (evidence: <file:line of the unchanged entry point>)` — not a table.

## Step 1 — Data-flow table (what are we working on?)

List every hop the diff adds or changes, including stores and the return path. Keep only rows that cross a trust boundary; that column is what makes the table a threat model and not an architecture diagram. This extends the Phase 0 trust-boundary table in `method.md` (who can set the input, what validates it, what it reaches) with the boundary each hop crosses.

| # | Source | Sink | Data | Boundary crossed | Control at the crossing (file:line) |
|---|---|---|---|---|---|
| 1 | … | … | … | internet → app / app → store / app → third party / tool output → model / model → tool | … or `none` |

## Step 2 — Per-boundary threats (what can go wrong?)

Walk the full set only on **sensitive rows**: rows that reach money, writes, secrets, or personal data (the same cut as the abuse row in `method.md`, plus personal data). Every other row gets one line, `Row <n>: not sensitive — <why>`, so the time box holds.

On each sensitive row, walk the six STRIDE categories (Microsoft's definitions): **Spoofing** (using another user's authentication information), **Tampering** (malicious modification of data), **Repudiation** (a user denies an action and no one can prove otherwise), **Information disclosure** (exposure to people not supposed to have access), **Denial of service** (valid users denied service), **Elevation of privilege** (an unprivileged user gains privileged access). Write one short phrase per category, or `—` with a reason. A `—` without a reason is an unanswered question, not a clear cell.

When the row carries personal data, also walk the seven LINDDUN threat types: **Linking**, **Identifying**, **Non-repudiation**, **Detecting**, **Data disclosure**, **Unawareness & unintervenability**, **Non-compliance**.

The abuse row in `method.md` is the Phase 0 shorthand for this walk; this step is the full version, carried into Steps 3 and 4.

## Step 3 — Map each threat to an existing check (link, don't restate)

Each threat becomes a probe against a check this skill already carries. Open the linked section and run its detect steps against the diff. A threat that maps to no check becomes its own probe and, if it holds, a finding.

| Threat | Where the check lives |
|---|---|
| Spoofing | `security-appsec.md` A07; `appsec-tokens.md`; `appsec-login.md`; `appsec-edge.md` (forgeable identity headers); `api-contracts.md` § Webhooks — consuming; `appsec-crypto.md` (constant-time compare) |
| Tampering | `security-appsec.md` A05 (injection) and A08 (integrity); `appsec-files.md`; `appsec-supply.md`; `api-contracts.md` (schema validation at the boundary) |
| Repudiation | `security-appsec.md` A09; `appsec-approvals.md` (who approved a consequential action) |
| Information disclosure | `security-appsec.md` A01 (dual surface, tenant scoping), A04 → `appsec-crypto.md`, § Secrets; `observability.md` (what logs and traces carry) |
| Denial of service | `security-appsec.md` A06 (rate limits, quotas) and A10; `security-api.md` (request-body ceiling); `reliability-error-handling.md`; `performance-db-cost.md` |
| Elevation of privilege | `security-appsec.md` A01 (server-side authorization) and A06 (client-trust fields); `appsec-approvals.md`; `domain-t.md` (cross-tenant reach) |
| Linking, Identifying | `privacy-compliance.md` § Linkability & re-identification |
| Non-repudiation (privacy) | `privacy-compliance.md` § Retention, DSAR & erasure (records that tie an action to a person, kept or shared beyond need) |
| Detecting | `security-appsec.md` A07 (account enumeration) |
| Data disclosure | `privacy-compliance.md` § Minimization & purpose limitation, § Analytics, telemetry & third-party SDKs |
| Unawareness & unintervenability | `privacy-compliance.md` § Consent & lawful basis, § Retention, DSAR & erasure |
| Non-compliance | `privacy-compliance.md` § Cross-border data transfer & residency; `privacy-by-design.md` (DPIA scaffold) |

## Step 4 — Disposition, residual risk, owner decision (what are we doing about it?)

Give every threat one of the four responses the OWASP cheat sheet names: **Mitigate** (cite the control's file:line and the test that proves it), **Eliminate** (remove the feature or component), **Transfer** (shift responsibility to another party, and name who), or **Accept**. Whatever is not fully mitigated gets a residual-risk line:

```
Residual: <row #> <category> — <what remains and why> — <severity> — owner: <role> — decision: accept | mitigate by <YYYY-MM-DD> | block
```

Severity follows the rubric in `SKILL.md`: a High residual blocks unless a named owner accepts it. The reviewer records the risk; the owner decides. A mitigation you did not run is `unverified`, not Mitigate.

**Did we do a good enough job?** Every sensitive row has all six STRIDE cells (plus LINDDUN where it carries personal data), every other row has its one-line reason, every cell maps to a check or a named new probe, and every cell not proven mitigated has a residual line. State any gap in the coverage ledger.

## Agent / LLM slice

When the flow includes a model or an agent, Step 1 gains three boundary rows that ordinary web models miss: **tool or retrieved output → model context** (untrusted content entering the instruction channel), **model → tool call** (a model decision driving a privileged action), and **tool → external party** (egress). Map them to `security-ai-agents.md`:

| Threat on the agent rows | Where the check lives |
|---|---|
| Tampering or spoofing through tool output (indirect prompt injection) | LLM01:2026 Prompt Injection; ASI01 Agent Goal Hijack; § MCP, part 3 (tool metadata is an untrusted instruction surface) |
| Elevation through the agent (excessive agency) | LLM03:2026 Excessive Agency; ASI02 Tool Misuse; ASI03 Identity & Privilege Abuse; `appsec-approvals.md` |
| Information disclosure through tools (exfiltration) | LLM02:2026 Sensitive Information Disclosure; the lethal-trifecta conjunction probe; LLM10:2026 Improper Output Handling |
| Denial of service or runaway spend | LLM06:2026 Unbounded Consumption |
| Repudiation of agent actions | `security-appsec.md` A09 applied to tool calls: log which principal the agent acted for |

This is the diff-sized version. A new autonomous agent surface still needs MAESTRO (`appsec-design.md`); a change that ships or installs a skill also walks `security-agent-skills.md`.

## Worked example — a new inbound webhook receiver

A diff adds `POST /webhooks/payments`. A provider (Acme Payments) calls it; the handler verifies an HMAC signature, marks the order paid, and enqueues a receipt email. The diff ships a test for each control the table cites.

| # | Source | Sink | Data | Boundary crossed | Control at the crossing |
|---|---|---|---|---|---|
| 1 | Acme Payments (internet) | `POST /webhooks/payments` | event JSON + signature | internet → app | HMAC check over raw body (handler:12), constant-time |
| 2 | webhook handler | `orders` table | order id, status | app → data store | parameterized update (repo:40) |
| 3 | webhook handler | email queue | customer email, amount | app → downstream party | none |

All three rows are sensitive (row 1 drives a write, row 2 writes, row 3 carries personal data).

- **Row 1.** S forged sender → mitigated: HMAC check plus bad-signature test (`api-contracts.md` § Webhooks — consuming). T replayed body → open: no timestamp window or stored delivery id. R disputed delivery → mitigated: event id and verdict logged (A09). I → `—`, fixed `400` with an empty body. D flood or oversized body → open: no body ceiling (`security-api.md`) or rate limit (A06). E trusted `status` → mitigated: status re-read from the provider API (A06 client-trust fields).
- **Row 2.** S `—`, app's own credential; T mitigated by the parameterized update (A05); R carried by row 1's log; I `—`, write-only; D `—`, one write per verified event; E `—`, a paid transition only, guarded in row 1.
- **Row 3.** S `—`, internal queue; T `—`, payload built server-side; R `—`, no user action; I and LINDDUN data disclosure → mitigated: only email and amount sent (`privacy-compliance.md` § Minimization & purpose limitation); D `—`, bounded by row 1; E `—`, the consumer holds no privilege. Other LINDDUN types: `—`, no new identifier or profile.

Residual lines for the two open cells:

```
Residual: 1 T — replayed events re-mark orders; no timestamp window or delivery-id store — Medium — owner: payments lead — decision: mitigate by 2026-10-31
Residual: 1 D — no request-body ceiling or per-source rate limit — Medium — owner: platform lead — decision: mitigate by 2026-10-31
```

Sources: OWASP Threat Modeling Cheat Sheet, Microsoft Threat Modeling Tool STRIDE categories, the Threat Modeling Manifesto, LINDDUN threat types, and the OWASP Top 10 for LLM Applications. URLs and verification dates are in `standards-index.md`.
