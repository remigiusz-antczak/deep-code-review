# Domain O checklist

Read this when domain O (Documentation & developer experience) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### O. Documentation & developer experience → `references/docs-and-dx.md`
- **README (human-facing)**: BLUF (what it is, the problem, how it's solved —
  sources → processing → output) in plain language for a non-technical reader;
  an architecture + data-flow diagram (Mermaid / C4); cross-linked docs;
  one-command setup + `.env.example`. Never bake live metrics into prose — cite
  the command. **AI-facing doc** (`AGENTS.md` canonical; `CLAUDE.md` / peers as
  pointers): standards,
  conventions, definition of done, hard rules. Structure docs by **Diátaxis**;
  record significant decisions as **ADRs**.
- **DX**: a `doctor`/preflight that names each missing piece with a fix, prints
  no secrets, and fails only on a genuine blocker; a documented
  missing-prerequisite → symptom map; a **single source of truth** for
  cross-referenced facts enforced by a doc↔code sync check — reconcile each
  load-bearing *optional/required/always/never/all/every* claim against the code
  that enforces it (a mismatch on a deploy-contract claim is at least High);
  document what is deliberately **not** tested/N/A and why.
- **Repository hygiene & cross-agent standards**: community-health files matched
  to the repo's exposure (LICENSE, SECURITY.md, CONTRIBUTING, CODEOWNERS **plus
  the rule that enforces it**, CHANGELOG) and a protected default/release branch
  (PR + review + passing checks, no force-push) — rated Info/Low on a private
  repo, escalating when public/distributed/reaching prod. Agent-instruction files
  (`AGENTS.md` canonical; `CLAUDE.md`/peers as pointers) must not diverge — one
  canonical, the rest point
  to it. **A standards doc with no enforcing gate is advisory** and won't survive
  the next session. (Depth + per-item severities in `references/docs-and-dx.md`.)
- 🚩 aspirational README, stale setup, undocumented env vars, no diagram, "see
  the code," live counts hard-coded in prose, conflicting agent-instruction
  files,  a public repo with no LICENSE/SECURITY.md, a default branch mergeable with no
  review, a standards doc no gate enforces.
