# Changelog

All notable changes to this repository are documented here. Format loosely
follows Keep a Changelog; versioning follows Semantic Versioning.

## [1.2.1] — 2026-08-14

### Fixed
- `install.sh` backed up an existing skill to `…/.claude/skills/<name>.backup-<ts>`
  — **inside** `skills/`, where Claude Code then loaded the backup as a duplicate
  skill. Backups now go to `…/.claude/skill-backups/` and are never loaded.

### Changed
- `install.sh` is **universal by default**: alongside the Claude Code skill it
  writes an additive, idempotent cross-agent `AGENTS.md` pointer (Codex, Cursor,
  Copilot, Gemini, Aider), so the method is not Claude-only. The opt-in
  `--portable` flag is replaced by a `--claude-only` opt-out (`--portable` is still
  accepted as a no-op, with a note).

## [1.2.0] — 2026-08-14

Coverage extension — dependency currency & safe upgrades, repository hygiene,
cross-agent portability of the standards imprint, and DX depth — plus the repo now
enforces its own documented gates in CI. Additive; phases, domains A–R, and report
formats are unchanged.

### Added
- `references/dependency-currency-and-upgrades.md` — detect stale / EOL /
  known-vulnerable dependencies, then upgrade with discipline (no blind "latest",
  semver-risk sizing, changelog review, regenerated lockfile, the project's own
  gate proven green on the bumped tree, provenance check) with severity discipline
  so "behind latest" never becomes noise. Routed from K and H.
- Repository hygiene & community-health review (`docs-and-dx.md`, SKILL.md O):
  LICENSE, SECURITY.md, CONTRIBUTING, CODEOWNERS + its enforcing rule, branch
  protection, CHANGELOG, templates — rated by repo exposure (Info/Low private,
  escalating when public / distributed / reaching production).
- Cross-agent portability: a divergence check across `CLAUDE.md` / `AGENTS.md` /
  peer instruction files, and a Phase-6 imprint that now defaults fresh standards
  to a canonical cross-vendor `AGENTS.md` with thin per-agent pointers; the
  "documented but unenforced = advisory" durable-standards finding.
- `install.sh --portable` — additively drops an idempotent root `AGENTS.md`
  pointer so non-Claude agents (Codex, Cursor, Copilot, Gemini, Aider) discover
  the method.
- This repository now dogfoods its own bar: `.github/workflows/ci.yml` (routing,
  name-match, `install.sh` parse, banlist-driven fail-closed privacy gate; a
  SHA-pinned action + least-privilege token), plus `SECURITY.md`,
  `CONTRIBUTING.md`, and `.editorconfig`.
- 16 standards verified by direct fetch and logged in `docs/standards-index.md`.

### Changed
- **DX** (`docs-and-dx.md`) gains fewest-commands-to-first-run (normalized
  bootstrap / devcontainer), dev/prod parity, and time-to-first-run as friction.
- **Phase 6 / imprint** is now idempotent and additive (detect-and-stop,
  create-if-missing, add-only-missing-lines, print-what-changed) and pairs every
  imprinted standard with the gate that enforces it.
- **Decorrelated second-model review** (SKILL.md review mechanics) is read-only
  and fail-soft — it advises, never hard-blocks.
- README reference-file count (10 → 11); standards list refreshed.

### Fixed (from a self-review of the skill)
- **Phase 5** no longer mandates writing `code-review/…` for a `DIFF` of a PR/MR
  (which may have no writable checkout, and would land the file inside the diff
  under review) — that write is scoped to FULL / local-checkout, and a DIFF's
  deliverable is the review comment on the PR.
- **Phase 1**'s planted-defect gate probe now requires a verified-clean tree (or a
  throwaway worktree) and a confirmed revert, carved into principle 7 as the one
  permitted transient mutation.
- **Severity rubric**: `unverified` / `PLAUSIBLE` findings now have an explicit
  gate rule (reported at provisional severity, block only once confirmed); Blocker
  vs Critical for data damage is discriminated (already-corrupting vs
  will-corrupt-next-run).
- **Coverage**: input-amplification DoS (ReDoS, decompression / entity-expansion
  bombs) added to the adversarial pass and the red-flag greps; AI-eval golden-set
  **contamination** flagged as a Critical eval defect; one-shot-prompt mode now
  names the references to also paste.
- **Duplication / pointers**: data-quality's spend-governance restatement folded
  into a cross-reference to `performance-db-cost.md`; a stale "section M" secret
  pointer repointed to N; `N-A` → `N/A`; `CREATE INDEX CONCURRENTLY` marked
  Postgres-specific.

## [1.1.0] — 2026-08-13

Field-hardening pass distilled from four independent FULL-run engagements. No
restructuring — phases, domains A–R, and report formats are unchanged; these are
additive method, rubric, and reference refinements.

### Added
- `references/parallel-audit.md` — fan-out protocol for large targets: a shared
  context packet, a fabrication-resistant subagent contract (one named invariant,
  `file:line` + failing case, `NONE` is valued), and orchestrator re-verification
  of every subagent finding in both directions. Routed from "Review mechanics"
  and Phase 2.

### Changed
- **Phase 1** now verifies gate *scope*: run the project's own aggregate gate by
  name, confirm exit codes, enumerate what the gates exclude and report coverage
  per subtree, prove each gate goes red on a planted defect, and flag
  decorative/unwired tests — plus a container/serverless deploy-contract
  preflight.
- **Severity rubric** gains a reachability qualifier: a `latent` finding keeps its
  intrinsic severity but gates "enabling the subsystem," not merge (a bounded +
  gated + recoverable destructive breach may be High); owner priority raises
  prominence, not severity. Machine and human reports gain a two-status verdict
  and `CONFIRMED`/`PLAUSIBLE` finding confidence.
- **Domains A–E, C, O** and their references gain: latest-batch-by-`max(col)`;
  exposure-boundary-first + CSRF≠auth; the "asserted-but-unenforced safety
  property" class; a spend-safety checklist (default-off caps, fail-open ledgers,
  `SELECT sum()` TOCTOU, cross-process guards); monotonic read-path shadowing +
  write-guard-covers-every-primitive; and a docs↔code claim-reconciliation
  technique.
- **Principle 2 / Phases 4–5**: byte-fidelity before invisible-character claims; a
  live-vs-documented-incident discriminator; report privacy re-scan, third-party
  proper-noun scrub, and PR-split by risk surface.
- README reference-file count (9 → 10).

## [1.0.0] — 2026-08-13

Initial release: a universal, evidence-grounded deep code-review skill.

### Added
- `.claude/skills/deep-code-review/SKILL.md` — the review method (6 phases) and
  eighteen domain checklists (A–R) plus an adversarial/red-team pass, severity
  rubric, exact report format, and definition of done.
- Nine on-demand reference playbooks under `references/`: application security
  (OWASP Top 10:2025), AI/LLM/agent security (OWASP LLM Top 10:2025 + Agentic
  Applications 2026), data integrity & quality, performance/DB/cost, testing &
  evals, infrastructure/IaC/containers, docs/DX (incl. the standards-imprint
  phase), frontend/accessibility (WCAG 2.2 AA), and language/stack red flags.
- `install.sh` — one-command install of the skill into any project's
  `.claude/skills/`, with backup-on-update and self-install guard.
- `README.md` (human-facing, with a Mermaid method diagram and a coverage map),
  `CLAUDE.md` (AI-facing standards for this repo), `docs/standards-index.md`
  (verified standards with URLs + verification dates), `.banlist.txt` privacy-gate
  seed, `LICENSE` (MIT), and `.gitignore`.

### Notable design decisions
- **Judge the outcome, not just the code** — a hard monotonic-quality invariant
  for any data producer, with a required non-regression test.
- **Do no harm** — every proposed change must be net-positive across all axes;
  never fix one by regressing another.
- **Respect the existing design** — accessibility/UX defects are fixed in place;
  design-altering changes are surfaced as owner decisions.
- **Standards imprint** — an opt-in final phase persists a tailored standards set
  into the reviewed project so quality holds on later iterations.
- **Human-readable report** — Phase 5 also writes a plain-language, non-technical
  report into a top-level `code-review/` directory in the reviewed repo (dated,
  additive), so a founder or leader can act on it without reading the code.
- **No duplication** — the skill has a single home; `SKILL.md` routes to every
  reference; nothing is restated.
- **No fabrication / cite-only-verified** — standards are split into
  directly-fetched (with dates) and by-name in `docs/standards-index.md`.
