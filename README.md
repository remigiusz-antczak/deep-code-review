# Deep Code Review

**A universal, evidence-grounded code-review skill you can drop into any
repository.** It turns "look this over" into a rigorous, reproducible audit that
covers correctness, security, AI/LLM safety, data quality, performance and cost,
reliability, testing, infrastructure, docs, and accessibility — and ends with a
severity-ranked report you can act on. Works in any language or stack, as a
Claude Code skill, a one-shot prompt, or a human checklist.

---

## The problem it solves

An ad-hoc read-through finds the obvious bugs and misses the expensive ones: the
IDOR that leaks another tenant's data, the enrichment run that silently
overwrites a verified value with a blank, the N+1 that shows up only under load,
the LLM call that trusts a scraped web page as an instruction, the migration
that locks a table during deploy, the API called "every run" that quietly grows
the bill. Deep Code Review makes the review **systematic** — a fixed method,
domain checklists mapped to current standards, an adversarial pass, and a report
format — so the same rigor applies every time, on any project, by a human or an
agent.

Two things make it more than a checklist:

- **It judges the outcome, not just the code.** For data and ML pipelines it
  audits what the code *produces* — fabrication, duplication, entity-merge
  errors, silent quality regressions — against a hard "quality can only improve,
  never silently degrade" invariant.
- **It leaves the bar in place.** An optional final phase imprints a tailored
  standards set (`CLAUDE.md`/`AGENTS.md`, pre-commit gates, templates) into the
  reviewed project so the *next* contributor or agent holds the same quality,
  security, and efficiency bar — without re-deriving it.

---

## What it checks

The method walks eighteen domains (A–R); each has a red-flag list in `SKILL.md`
and a deep detection playbook in `references/`.

| Domain | Covers | Deep reference |
|---|---|---|
| A Correctness | logic, edge cases, money precision, time/UTC | — |
| B App security | OWASP Top 10:2025, injection, SSRF, authz, secrets | `security-appsec.md` |
| C AI / LLM / agents | OWASP LLM Top 10:2025 + Agentic 2026, injection, output handling | `security-ai-agents.md` |
| D Data integrity | monotonic quality, no-fabrication, entity resolution, evals | `data-quality.md` |
| E Performance & cost | N+1, indexes, migrations, API/LLM spend | `performance-db-cost.md` |
| F Reliability | error handling, retries, idempotency, rollbacks | — |
| G Concurrency | races, TOCTOU, shared-state writes | — |
| H Maintainability | dead code, duplication, feature flags, lockstep surfaces | — |
| I APIs & integration | contracts, webhooks, message-schema evolution | — |
| J Testing & evals | taxonomy, test-the-failure, AI eval harness | `testing-and-evals.md` |
| K Build / CI / supply chain | reproducible build, SHA-pinned actions, SBOM, signatures | — |
| L Infra / IaC / cloud | Docker, K8s, Terraform, IAM, network exposure | `infra-iac-containers.md` |
| M Observability | structured logs, no PII, honest failure accounting | — |
| N Config & secrets | env-only secrets, safe defaults, clean no-op | — |
| O Docs & DX | Diátaxis, C4, ADRs, one-command setup, standards imprint | `docs-and-dx.md` |
| P Frontend / a11y | WCAG 2.2 AA, Core Web Vitals, respect existing design | `frontend-a11y.md` |
| Q Privacy & licensing | data minimization, retention/erasure, license compat | — |
| R i18n & encoding | locale-aware formatting, Unicode normalization | — |
| + | per-language grep-able footguns | `language-stack-redflags.md` |

Plus a dedicated **adversarial / red-team pass** and a **useless-work audit**
(cost with no value: repeated identical API/LLM/DB calls, over-fetching,
"call it every run" patterns).

---

## How to use it

**Install into a project** (copies the skill into `.claude/skills/`):

```bash
git clone https://github.com/remigiusz-antczak/deep-code-review.git
cd deep-code-review
./install.sh /path/to/your/project      # defaults to the current directory
```

Then in that project:

```
/deep-code-review FULL                   # the whole repository
/deep-code-review DIFF origin/main       # a PR / branch vs a base
/deep-code-review FILE src/auth.ts        # a named set of files
```

**As a one-shot prompt** — paste `.claude/skills/deep-code-review/SKILL.md` into
any capable model, then name the target and scope.

**As a human checklist** — walk the domain sections (A–R) directly.

---

## How it works

```mermaid
flowchart LR
  P0[Phase 0<br/>Map the target] --> P1[Phase 1<br/>Ground truth<br/>build · test · lint]
  P1 --> P2[Phase 2<br/>Domain audits A–R]
  P2 --> P3[Phase 3<br/>Adversarial<br/>red-team pass]
  P3 --> P4[Phase 4<br/>Synthesize<br/>& rank severity]
  P4 --> P5[Phase 5<br/>Report<br/>file:line + fixes]
  P5 -.opt-in.-> P6[Phase 6<br/>Imprint standards<br/>into the repo]
  P2 -. loads on demand .- R[(references/)]
```

The report is severity-ranked (Blocker → Critical → High → Medium → Low → Nit),
every finding carries `file:line` evidence and a concrete fix, and unverifiable
items are marked `unverified` rather than guessed. See `SKILL.md` for the exact
report format and the definition of done.

It also writes a **plain-language report** a non-technical reader can act on into
a top-level `code-review/` directory in the reviewed repo — a traffic-light
health scorecard, the top risks in human terms, and the decisions that need an
owner — so a founder or leader can act on the outcome without reading the code.

---

## Standards it tracks

Verified for this release (full list with URLs and verification dates in
[`docs/standards-index.md`](docs/standards-index.md)): OWASP Top 10:2025, OWASP
Top 10 for LLM Applications 2025, OWASP Top 10 for Agentic Applications 2026,
OWASP API Security Top 10 (2023), OWASP ASVS 5.0, CWE Top 25 (2025), WCAG 2.2,
Google Engineering Practices, Diátaxis, and the C4 model. Referenced by name
(verify the current version before citing): OWASP WSTG, MITRE ATLAS, NIST SSDF
and AI RMF, SLSA, CIS Benchmarks, ISO/IEC 25010, Twelve-Factor, SemVer, and
Conventional Commits.

Standards move. The skill instructs the reviewer to **fetch the current version
before relying on version-specific detail, and to cite only URLs it has
verified** — never a remembered link.

---

## Repository layout

```
.
├── README.md                       # this file (human-facing)
├── CLAUDE.md                       # AI-facing standards for working in THIS repo
├── install.sh                      # copy the skill into a target project
├── .banlist.txt                    # privacy-gate seed (dogfooded)
├── docs/
│   └── standards-index.md          # verified standards, URLs, verification dates
└── .claude/skills/deep-code-review/
    ├── SKILL.md                    # the review method + all domain checklists
    └── references/                 # on-demand deep playbooks (9 files)
```

---

## Confidentiality & no fabrication

The skill enforces — and this repository dogfoods — two hard rules: **no
fabrication** (skip or flag rather than guess; no invented findings, data,
sources, metrics, CWEs, or line numbers) and **no private/identifying data** in
any committable artifact (real names, company/team names, emails, internal IDs,
hostnames, or identifying URLs), including git history. All examples use
fictional placeholders (`Acme Capital`, `jane@example.com`). A privacy gate that
finds a secret reports its `file:line` and never echoes the secret itself.

## Attribution & license

Inspired by open Claude Code setups (including
[`nickmaglowsch/claude-setup`](https://github.com/nickmaglowsch/claude-setup))
and grounded in the public standards listed above. Released under the
[MIT License](LICENSE).
