# Standards index

Every standard the skill relies on, split into what was **verified by direct
fetch** for this release and what is **referenced by name** (not fetched — verify
the current version before citing a specific URL). This split enforces the skill's
own rule: cite only URLs you have verified.

Verification date for all direct fetches below: **2026-08-13**.

---

## Verified by direct fetch (2026-08-13)

| Standard | URL | What was confirmed |
|---|---|---|
| OWASP Top 10:2025 | https://owasp.org/Top10/2025/ | Categories A01–A10:2025 verbatim (A01 Broken Access Control … A10 Mishandling of Exceptional Conditions). |
| OWASP Top 10 for LLM Applications 2025 | https://genai.owasp.org/llm-top-10/ | 2025 is the current edition; LLM01–LLM10:2025 names verbatim. No 2026 LLM edition was referenced by the authoritative page as of this date. |
| OWASP Top 10 for LLM Applications 2025 (resource) | https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/ | Edition landing page; document publication 2024-11-17. |
| OWASP Top 10 for Agentic Applications 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | Framework exists; published 2025-12-09; peer-reviewed by 100+ practitioners. (The ASI01–ASI10 titles were corroborated across secondary sources but not confirmed verbatim from the authoritative PDF — the skill presents the risk themes and points here for the authoritative list.) |
| OWASP API Security Top 10 (2023) | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ | API1–API10:2023 names verbatim. |
| CWE Top 25 (2025) | https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html | Official 2025 edition, last updated 2025-12-15; top entries (XSS, SQLi, CSRF, Missing Authorization, OOB Write, Path Traversal, Use-After-Free, OOB Read, OS Command Injection, Code Injection). |
| WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | W3C Recommendation, dated 2024-12-12; conformance levels A/AA/AAA; WCAG 3.0 still in development. |
| Google Engineering Practices — Standard of Code Review | https://google.github.io/eng-practices/review/reviewer/standard.html | Core standard: approve once the change "definitely improves the overall code health," even if imperfect. |
| Diátaxis | https://diataxis.fr/ | Four documentation types: Tutorials, How-to guides, Reference, Explanation. |
| C4 model | https://c4model.com/ | Four abstraction levels: Context, Container, Component, Code. |

Reference repository reviewed for patterns (not a standard):
`nickmaglowsch/claude-setup` — https://github.com/nickmaglowsch/claude-setup
(diff-scoped review packets; a decorrelated cross-model second opinion on
sensitive diffs — auth, payments, crypto, concurrency, DB migrations).

## Referenced by name (not fetched this session — verify before citing a URL)

- **OWASP ASVS 5.0** — released May 2025 (confirmed via search, not a direct
  fetch); use for verification depth beyond the Top 10.
- **OWASP WSTG** — how-to-test companion for each web risk.
- **OWASP Cheat Sheet Series** — concrete implementation guidance.
- **MITRE CWE / CVE** — weakness and vulnerability naming.
- **MITRE ATLAS** — adversarial-ML and agent-tool attack techniques.
- **NIST SSDF (SP 800-218)** and **NIST AI RMF + Generative AI Profile (AI 600-1)**
  — secure-development and AI-risk lifecycle framing.
- **SLSA** — build/supply-chain provenance levels.
- **CIS Benchmarks** — OS/container/cloud hardening baselines.
- **ISO/IEC 25010** — software product-quality model (the axes this review
  covers).
- **The Twelve-Factor App** — config/dependency/deploy hygiene.
- **Semantic Versioning** + **Conventional Commits** — versioning and commit
  discipline.

> When the skill needs a version-specific detail from any of these, it must fetch
> the current source at review time and cite only the URL it verified.
