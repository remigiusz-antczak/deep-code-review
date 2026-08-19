# Changelog

All notable changes to this repository are documented here. Format loosely
follows Keep a Changelog; versioning follows Semantic Versioning.

## [1.9.0] — 2026-08-19

Method honesty and detection depth from two FULL multi-model skill-feedback
runs — narrowed to durable invariants; host/model ceremony and duplicated
doctrine left out.

### Added
- SCOPE / packet field `BANNED_REMEDIES` (records Phase 0 revert/deletion scan).
- Principle 5: drift from a named stating artifact is the finding.
- Phase 2 named check: stated invariant / landed guard → bypass census
  (appsec untrusted-egress caller census; data-quality artifact→consumer).
- Config/runtime evidence rule: no severity on an unobserved branch.
- Planted-probe skip caps gate-self-test only (DoD wording).
- Parallel-audit: unit manifest, material dissent preservation, stop rule,
  named substitute in fan-out preamble.
- Soft-no-op persistence (empty artifact overwrite) in reliability + F map.
- Concurrency: corrupt→wipe ban; stale RMW across `await`.
- Data-quality: denominator integrity; absent/expected-empty/false/empty-list.
- Spend ledger: test present-fault branch (`EACCES`/`EISDIR`/invalid body).

### Changed
- Phase 5 BLUF: top defects + `Decisions: N` pointer; product/redesign never
  carries Blocker/Critical gate language.
- Example report version stamp 1.9.0.

## [1.8.0] — 2026-08-17

Depth from multi-model review of the skill itself: close authenticated-IDOR and
cache/CDN blind spots; force agent hard-gates; install support docs; lean privacy
+ observability refs; token-cutting coverage ledger and DIFF-scoped Phase 1.

### Added
- A01: Identity Map **forgeability** column + bypass row-set; **bidirectional
  gate proof**; **two-principal matrix**; **cache/CDN authz**; dual-surface
  beyond `page.tsx` (serialized payload, server actions, RPC/GraphQL/WS);
  tenant/row scoping; presigned URL / upload checks; safer anon-GET (canary +
  anon-vs-auth body diff; local/dev default).
- A05 files/archives/XXE; A06 business-logic detect steps; A07 session cookies +
  OAuth/OIDC + refresh rotation; API overlay procedures (BOLA/BFLA, mass-
  assignment, zombie APIs, GraphQL/gRPC/WS).
- `references/privacy-compliance.md`, `references/observability.md`.
- Phase-0 coverage ledger + archetype → load map; first-response hard block
  (`SCOPE`/`START_SHA`/`TREE_STATE`/`REVERTS_CHECKED`/…).
- Banned remedies: deleted gate paths (`--diff-filter=D`), not only Revert
  subjects.
- Authz posture ledger in Ground truth; negative authz tests in DoD;
  DIFF authz 🚩 list; public-repo disclosure rule for committed reports.
- Parallel-audit: frozen packet schema + invariant catalog.
- `install.sh` copies `standards-index.md` + `example-review-report.md` into
  installed `references/`.
- ASVS 5.0.0 verified by direct fetch (2026-08-17) in standards-index.

### Changed
- Phase 5 default: chat BLUF ≤30 lines + out-of-tree; `code-review/` write is
  opt-in (`--write-report` / confirm).
- Phase 1 scoped for `DIFF`/`FILE` (changed-path tests; plant only if gate under
  review).
- Domain S FULL: consequence branches + count by default.
- Domain B: SSRF ranges single-sourced in appsec; A02–A10 one-liners + force
  load of `security-appsec.md` before Phase 3.
- S2 world-reachable without auth = Critical (zero discretion).
- README domain table + reference count; example report version stamp 1.8.0.
- CI asserts installed support docs present.

## [1.7.0] — 2026-08-17

Access-control depth from a production anonymous-read class of defect:
identity must be mapped per request class before any gate is proposed; API
redaction is not page protection; preflight that expects anonymous 200 on
data routes is a finding; internal business data is Confidentiality Tier S2.

### Added
- **Identity Arrival Map** (document / XHR / bare curl) in `security-appsec.md`
  A01 — required before proposing middleware or document gates; "middleware on
  document when identity only arrives via client Bearer" marked anti-pattern.
- **Dual-surface check** — sensitive loader used by API ∩ RSC/SSR page;
  asymmetric redaction = Critical when world-reachable.
- **Anonymous GET sweep** — mandatory Phase 0/3 opener for networked apps
  (status + body size, no auth).
- **Confidentiality tiers S0–S3** in the severity rubric (incl. internal
  business data as S2 → Critical if world-readable).
- Phase 0: platform-vs-app-vs-preflight trust rows; **banned remedies** from
  recent auth/middleware/gate reverts.
- Phase 1 planted-defect matrix: missing / **empty** / wrong / path-excluding
  config.
- `parallel-audit.md`: specialized-subagent reject → **generalPurpose** fallback
  under the same read-only contract (do not stall A01 on harness ceremony).

### Changed
- Phase 5: prefer out-of-tree report during active Critical remediation; chat
  order for FULL = verdict → plain top 5 → decisions → path to machine table
  (table in file, not first bubble); advise-only on security gates (no
  auto-implement middleware).
- Domain B checklist + adversarial opener cross-link the new A01 procedures.
- `testing-and-evals.md`: empty-config self-test called out.

## [1.6.0] — 2026-08-17

**Agent-agnostic packaging.** The method was already host-neutral in substance;
install + docs still read Claude-first. Default install now mirrors the skill
into every common skill root (`.agents/`, `.cursor/`, `.claude/`), `AGENTS.md`
is the cross-vendor entry pointer, and SKILL/parallel-audit/docs speak to any
major coding agent first.

### Added
- Default multi-path install: `.agents/skills/`, `.cursor/skills/`,
  `.claude/skills/` (+ optional `--with-codex` → `.codex/skills/`).
- `--minimal` lean install; `--with-cursor` kept as no-op for compatibility.
- Harness table rows for Copilot / Gemini / Aider / Windsurf; generic-first
  fan-out contract.

### Changed
- SKILL "How to use" + confidentiality restatement → agent-agnostic discovery
  and `AGENTS.md`-canonical imprint language.
- `docs-and-dx.md` portability / imprint: prefer `AGENTS.md`, peers as pointers.
- README / AGENTS.md install pointer: no "for non-Claude agents" framing.
- CI dry-run asserts `.agents` + `.cursor` + `.claude` paths on default install.

## [1.5.0] — 2026-08-17

Depth + install portability on top of 1.4.0's multi-agent checkout safety. New
reference playbooks for reliability, concurrency, and API contracts; review-
surface gate in the definition of done; harness notes for fan-out; version
stamp + optional Cursor-native install path; worked fictional example report.

### Added
- `references/reliability-error-handling.md` — domain F depth (timeouts/aborts,
  retries, crash/SIGINT resume, silent subsystem no-op).
- `references/concurrency-shared-state.md` — domain G depth (races, file stores,
  TOCTOU, tests/jobs vs real shared paths).
- `references/api-contracts.md` — domain I depth (public contracts, webhooks,
  message-schema evolution; OWASP API Top 10 overlay stays in appsec).
- Skill `VERSION` file (`1.5.0`); `install.sh` stamps version + short SHA into
  the AGENTS.md pointer and **refreshes** that block on re-install.
- `install.sh --with-cursor` — also copies the skill to
  `.cursor/skills/deep-code-review/` (Cursor-native; Cursor already loads
  `.claude/skills/` for compatibility — verified against Cursor Agent Skills
  docs this session).
- `docs/example-review-report.md` — fictional FULL report showing `START_SHA`
  preamble, `CONFIRMED`/`CORROBORATED`/`PLAUSIBLE`/`latent`, and plain-language
  companion.
- `parallel-audit.md` harness notes — Claude Code / Cursor / Codex / one-shot
  map for read-only toolsets vs mutate-ban + tree-diff fallback.
- Definition-of-done + first-response **review surface pinned** checklist
  (`START_SHA`, worktree, history count).

### Changed
- README domain table routes F/G/I to the new references; install docs cover
  `--with-cursor` and the version stamp.

## [1.4.0] — 2026-08-17

Ops/safety hardening for **live multi-agent checkouts** — the review loop already
caught real defects under an anti-fabrication contract; this release makes the
method safe when another agent is editing, switching branches, or committing in
the same tree. Additive: domains A–S and report sections unchanged; new
confidence marker `CORROBORATED`; Phase 0/1/5 and `parallel-audit.md` carry the
depth.

### Added
- **Immutable review surface** — Phase 0 captures `START_SHA`, prefers
  `git show $START_SHA:path` or a dedicated worktree/clone (default for `FULL`),
  and detects a shared/mutating checkout (`git status` twice; occupied → don't
  plant or write into the live tree). First-response line states the pinned ref.
- **History-depth check** — Phase 0 runs `git rev-list --count HEAD` /
  `git log --oneline -5` (and shallow detection); never trust a prose "no
  history" claim; tree scrub ≠ history scrub for secrets/PII.
- **Triage-first fast lane** — Phase 0 runs project `doctor`/gates/documented
  invariants before expensive fan-out; Review mechanics and Phase 2 order by
  blast radius after those hits.
- **`parallel-audit.md` contracts** — read-only tool allowlist (or mutate-ban +
  lead before/after tree-diff hard-fail); transitive identifier masking in
  subagent returns; mega-file chunking by named concern; `CORROBORATED`
  confidence when independent units converge on the same sink.
- **Phase 5 shared-tree escape hatch** — if the checkout is occupied or an
  unrelated change is in flight, deliver the human-readable report out-of-tree /
  offer a dedicated review branch instead of writing `code-review/` into someone
  else's commit surface.
- **Hermetic-test shared-state red flag** — domain J (cross-ref G) + depth in
  `testing-and-evals.md`: tests that write real tracked/shared data paths with
  cleanup only in `finally`/`try` that hard-exit can skip.

### Changed
- Principle 7 — planted-defect probe defaults to a dedicated worktree/copy;
  report write is conditional on an unshared idle tree; fan-out least-privilege
  is by toolset where the harness allows.
- Principle 11 / confidentiality restatement — masking is transitive through
  fan-out, not lead-only.
- Phase 1 planted probe — worktree/copy at `START_SHA` by default; never plant
  into a tree another process can commit from.

## [1.3.0] — 2026-08-14

New capability — **branch, merge & open-work triage**. The review now analyzes
every open branch and advises, per branch, whether to merge it (to `main` or
`develop`, per the detected branching model), open a PR, rebase/refresh, delete
(if already merged), archive, split, or escalate — so leftover work gets cleaned
up instead of rotting. Unlike 1.2.0, this **does** change the domain list
(A–R → A–S) and **adds a report section** (the branch & merge triage table).
Additive and opt-in to act on: the triage is advice; any merge/delete/push runs
only on explicit approval.

### Added
- `references/branch-and-merge-hygiene.md` — the depth behind the new domain S:
  ground the branch set before judging it (`git fetch --all --prune`; a shallow/
  stale clone hides open work; open-PR state is forge state, mark `unverified`
  when forge auth is absent); detect the branching model (Trunk-Based / GitHub
  flow / GitLab flow / git-flow) to resolve each branch's target; classify by
  **content, not just tip** — `git branch --merged` misses squash/rebase-merges,
  `git cherry` recovers single-commit squashes but a **multi-commit squash defeats
  patch-id matching**, so the forge merged-PR list is the authoritative
  corroborator; a per-branch decision tree → recommendation with the exact
  command; merge-strategy trade-offs; safety rails (never delete unique unmerged
  work, `--force-with-lease` not `--force`, a leaked secret is fixed by rotation
  not branch deletion); and severity discipline so branch cleanup never buries a
  real defect. All enumeration commands validated against a scratch repo this
  session. Routed from the new domain S.
- **Domain S — Branches, merges & open-work triage** in `SKILL.md` (A–R → A–S),
  scoped to a local git checkout; a Phase-0 open-branch/open-PR inventory hook; a
  Phase-5 triage-table output; a **Branch & merge triage** section in the findings
  report and an "Open work to tidy up" section in the human-readable report; and a
  definition-of-done line requiring every open branch to carry one recommendation.
- Boundary made explicit with section O (`docs-and-dx.md`): O owns *is branch
  protection configured*; S owns *what open work exists and what to do with it* —
  cross-referenced, not duplicated.
- `docs/standards-index.md`: verified-this-session rows (2026-08-14) for
  Trunk-Based Development, GitHub flow, GitLab flow, git-flow (Driessen), Fowler's
  branching-patterns article, GitHub's merge-method / protected-branch / merge-
  queue / branch-deletion docs, and the `git` reference manual, with the two
  attribution caveats surfaced by primary-source checks (GitHub's own docs do not
  state "main is always deployable"; "merge debt" is not Fowler's phrase).

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
