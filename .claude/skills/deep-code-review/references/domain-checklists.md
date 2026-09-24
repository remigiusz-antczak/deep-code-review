# Domain audit checklists (A–W)

Read this when walking a domain in Phase 2 (or a DIFF quick-path that touches that domain). This is the index: each domain's checklist expands the one-line map in `SKILL.md` and lives in its own `domain-<letter>.md`. Load the linked per-domain `references/*.md` for detection procedures.

## Domain audit checklists (A–W)

> Each item folds in the *why*. A "🚩" line lists patterns to grep/scan for.
> To turn any red flag into a grep for the target's language, see
> `references/language-stack-redflags.md`.

Each domain's checklist is its own file. Load only the files for the domains the coverage ledger marks applicable; a domain marked N/A (with its one-line reason) loads nothing.

| Domain | Checklist |
|---|---|
| A. Correctness & logic | `domain-a.md` |
| B. Security — application (OWASP Top 10:2025) | `domain-b.md` |
| C. Security — AI / LLM / agents | `domain-c.md` |
| D. Data integrity & data quality | `domain-d.md` |
| E. Performance, efficiency & cost | `domain-e.md` |
| F. Reliability & error handling | `domain-f.md` |
| G. Concurrency & shared state | `domain-g.md` |
| H. Tech debt, dead code & maintainability | `domain-h.md` |
| I. API, interface, contracts & integration | `domain-i.md` |
| J. Testing & evaluation | `domain-j.md` |
| K. Build, CI/CD, supply chain & release | `domain-k.md` |
| L. Infrastructure as code, containers & cloud | `domain-l.md` |
| M. Observability (logs, metrics, traces) | `domain-m.md` |
| N. Configuration, secrets & environments | `domain-n.md` |
| O. Documentation & developer experience | `domain-o.md` |
| P. Frontend / UI / UX / accessibility | `domain-p.md` |
| Q. Privacy, compliance & licensing | `domain-q.md` |
| R. Internationalization, encoding & localization | `domain-r.md` |
| S. Branches, merges & open-work triage | `domain-s.md` |
| T. Multi-tenancy & isolation | `domain-t.md` |
| W. Workflows, jobs & scheduling | `domain-w.md` |

---
