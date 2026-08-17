# Documentation, DX & standards-imprint

Read this when reviewing (or writing) a project's documentation, its setup /
developer experience, its **repository hygiene** (license, security policy,
contribution + ownership files, branch protection, changelog), its **cross-agent
instruction files** (`CLAUDE.md` / `AGENTS.md` and peers), or when the review
should **leave durable standards behind** so future contributors and agents hold
the quality bar on later iterations. Expands section O of `SKILL.md`.

---

## Documentation architecture

Good docs aren't one long file — they answer distinct needs in distinct places.

- **Diátaxis** — four types, kept separate: **Tutorials** (learning-oriented,
  get a newcomer to a first success), **How-to guides** (task-oriented, achieve
  a specific goal), **Reference** (information-oriented, describe the API/config
  precisely), **Explanation** (understanding-oriented, the why and the
  trade-offs). A page that tries to be all four serves none. Misfiled content is
  a finding.
- **C4 model** for the architecture diagram — four zoom levels: **Context**
  (the system and its users/externals), **Container** (the deployable
  apps/services/stores), **Component** (the major parts inside a container),
  **Code** (only where it earns its place). Most READMEs need Context +
  Container. Use Mermaid so the diagram lives in version control and can't rot
  into a stale PNG.
- **ADRs (Architecture Decision Records)** — one short record per significant,
  hard-to-reverse decision: context, the decision, the alternatives, the
  consequences. They give future readers (human and AI) the *rationale trail* a
  diff can't.

## README (human-facing) — leadership-grade

- **BLUF**: the first lines say what it is, what problem it solves, and — for a
  data product — what sources go in, how they're processed, and what comes out.
  Plain language a non-technical founder/leader scans in under a minute; no
  jargon, no marketing superlatives, numbers over adjectives.
- An **architecture + data-flow diagram** (Mermaid or a committed image) near
  the top. **Cross-link** related docs so a non-technical reader can navigate.
- **Setup is one command** with minimal manual steps and an `.env.example`.
- Status is explicit (✅ live / ⏳ pending, with owner + date). Docs must match
  reality — a doc that lies is worse than a missing doc.
- **Never bake live metrics into prose** (they drift the moment they're
  written); cite the command that prints the current number instead.

## AI-facing doc (`CLAUDE.md` / `AGENTS.md`)

Written so any coding agent can pick it up and comply: the code standards, repo
conventions, how to build/test/run, the **definition of done**, and the hard
confidentiality + no-fabrication rules. It is the mechanism by which quality
survives the *next* contributor — see "Standards imprint" below.

- **Portability & interop (check for divergence).** Prefer a canonical root
  **`AGENTS.md`** (cross-vendor). Peer files — `CLAUDE.md`, `.github/copilot-
  instructions.md`, Cursor `.cursor/rules` / skills, Windsurf `.windsurf/rules`,
  `GEMINI.md`, Aider `CONVENTIONS.md` — must be **thin pointers**, not forks.
  Bridge hosts that only read another name (e.g. Claude Code → `@AGENTS.md`
  import or symlink). **If the repo already standardizes on one file, defer to
  it** and fill gaps. Two instruction files with conflicting rules is the
  finding — not which filename is "primary."
- **A standards doc is context, not enforcement.** Prose in `AGENTS.md` / peers
  guides an agent but binds nothing unless a **gate** backs it (pre-commit,
  required CI). "Documented but unenforced" is the highest-value durable-
  standards finding (see the imprint below).

## Developer experience

- **One-command setup**, and a **`doctor`/preflight** that names each missing
  piece with an actionable fix line, prints **no secret values**, and exits
  non-zero **only** on a genuine blocker (not on an optional key the user may
  not need).
- **Fewest commands to first run.** clone→run and clone→green-test should each be
  a single normalized command — a `script/bootstrap` + `script/test` convention,
  a `make` / `just` target, or a devcontainer — so a newcomer needs the *pattern*,
  not project-specific knowledge, to build or test. A long or undocumented
  time-to-first-run is DX friction (Info), not a defect; a **CONTRIBUTING that
  promises a workflow the scripts don't actually run** is a real finding. Watch
  **dev/prod parity** — local backing services/versions that diverge from
  production can hide correctness bugs.
- **Document the missing-prerequisite → symptom map** for any gitignored setup:
  each absent file surfaces at a different step with an error that reads like a
  code defect. Record which absence causes which failure so each newcomer
  doesn't rediscover it.
- **Single source of truth** for any cross-referenced fact (a doc index, a
  count, a schema/field list) — a pointer can't drift, a duplicate always will.
  Enforce a CI **doc↔code sync check** that fails when a tracked doc, field, or
  count drifts.
- **Reconcile load-bearing claims against the code.** For each doc claim using
  *optional / required / always / never / all / every*, locate the code that
  enforces it and confirm. A mismatch is a finding; a mismatch on a
  **deploy-contract** claim (what is required to run) is at least High.
- **Enumerate "lockstep surfaces"** — the sets of files that must change
  together (schema ↔ validator ↔ type ↔ prompt ↔ docs ↔ test). Misalignment
  surfaces as silent runtime breakage, not a compile error, so name them.
- **Document what is deliberately *not* tested or *not* applicable, and why**, so
  silence is never mistaken for a gap.

---

## Repository hygiene & community health

A healthy repository ships more than code. Check for the community-health files
and process controls below, but **rate each by the exposure the repo actually
has** — on a private/internal repo most are Info/Low; each escalates when the
repo is **public, distributed/packaged, or accepts outside contributions** (the
same baseline-plus-trigger logic as the `SKILL.md` severity rubric). Don't emit a
wall of Mediums on a private repo — batch the Info/Low items and let the trigger
decide escalation.

- **LICENSE** — absent → legal reuse is undefined. Low for a private repo; **High
  once public or published to a package registry** (an undefined license blocks
  lawful use). OpenSSF passing criteria require a FLOSS license in a standard
  location.
- **SECURITY.md** — no vulnerability-disclosure channel. Low; Medium once public
  or externally used (OpenSSF: a project MUST publish how to report a
  vulnerability).
- **CONTRIBUTING** / **CODE_OF_CONDUCT** — Info; Low for a public project taking
  outside contributions. A CONTRIBUTING that documents a build/test flow the repo
  can't actually run is a real finding (cross-ref DX above).
- **CODEOWNERS — only as strong as its enforcing rule.** CODEOWNERS alone merely
  *requests* review; it binds a merge only when branch protection enables "require
  review from Code Owners." Present but unenforced on sensitive paths → Medium.
- **Branch protection / required checks** on the default and release branches:
  require a PR + human review + passing status checks before merge, and block
  force-push. Missing → Medium (maps to OpenSSF Scorecard *Branch-Protection* /
  *Code-Review* / *CI-Tests*); **High if unreviewed pushes reach production.**
- **CHANGELOG / release notes** — versioned releases with no human-readable change
  summary. Info; Low once consumers must track versions. Keep a Changelog:
  `CHANGELOG.md`, an `Unreleased` section, categories
  Added/Changed/Deprecated/Removed/Fixed/Security (OpenSSF: release notes MUST be
  human-readable).
- **Issue / PR templates** — `.github/ISSUE_TEMPLATE` and a PR template mirroring
  the definition of done. Info.

Do **not** re-home posture other sections already own: `.gitignore` / secret
hygiene is section N; general style consistency is section H.

**🚩**: a public repo with no LICENSE or SECURITY.md; CODEOWNERS with no "require
Code Owner review" rule; a default branch mergeable with no review or passing
checks; force-push allowed on a release branch; versioned releases with no
changelog.

---

## Standards imprint — leave the bar in place (Phase 6 of the review)

A review that only finds problems lets quality regress on the next iteration.
The highest-leverage durable output is to **persist a tailored standards set
into the reviewed project** so future contributors and agents maintain the
quality, security, safety, and efficiency bar automatically.

**This phase writes to the repository — it is opt-in and requires confirmation.**
It must be *net-positive and non-destructive* (see the "do no harm" principle in
`SKILL.md`): merge and augment, **never silently overwrite** a good existing
doc. If the project already has a standards doc or a style guide, **defer to it**
and fill gaps; if a proposed addition would substantially change existing
conventions or design, surface it as an owner decision rather than imposing it.

What to imprint (tailored to the project's actual stack and to this review's
findings — not a generic dump):

1. **AI-facing standards doc — canonical `AGENTS.md`.** Write the standards once
   in a root `AGENTS.md` (cross-vendor), and make every other agent file a **thin
   pointer** to it, not a copy: `CLAUDE.md` via `@AGENTS.md` / symlink where
   needed, plus one-line pointers for Cursor rules, Copilot instructions,
   `GEMINI.md`, Aider `read:`, Windsurf rules — whatever the repo's toolchain
   actually uses. **If the repo already standardizes on a specific agent file,
   defer to it** — fill gaps, don't relocate it. Keep the canonical file concise
   and push depth into referenced files. Contents: code standards, definition of
   done, stack-specific red flags this review surfaced, data-integrity
   invariants (if a data product), LLM-safety rules (if it calls a model), and
   the hard no-fabrication + confidentiality rules — so the *next* agent of any
   vendor complies without re-deriving them.
2. **Pre-commit / CI gates**: lint (0 warnings), format, type-check, tests, a
   **privacy/secret gate that fails closed when its banned-terms input is
   missing and reports `file:line` only — never echoing the matched secret**,
   and dependency/secret scanning. The gate scans the lines a branch *adds*; a
   green gate is a floor, not a certificate.
3. **Templates**: `.env.example` (secret-free), an ADR template, a PR checklist
   mirroring the definition of done, a `.banlist.txt` seed (real identifiers go
   in a gitignored local file), and the editor/versioning conventions that keep
   diffs clean across contributors — `.editorconfig`, a `CHANGELOG.md` (Keep a
   Changelog), and Conventional Commits where releases are versioned.

**Write it safely — the imprint is idempotent and additive.** It creates, it does
not clobber: **detect and stop** if the standard already exists; **create-if-
missing, never overwrite** a good file; when touching a shared file like
`.gitignore`, **add only the missing lines** (grouped under a labeled comment),
never removing or duplicating existing entries; and **print exactly what was added
vs. already present** so the change is auditable. And remember a doc alone is
advisory — **pair each load-bearing standard with the gate that enforces it** (a
pre-commit hook / required CI check) or it will not survive the next session.

### Minimal `AGENTS.md` skeleton to imprint (canonical — point `CLAUDE.md` and peers at it)

```markdown
# Engineering standards (AI-facing)

## What this is
<one paragraph: problem, and how it's solved — sources → processing → output>

## How to work here
- Build / test / run: <one-command each>
- Definition of done: builds; tests pass (state X/X); lint+format+type+security
  scan clean; docs updated; no dead code; every export documented + tested.
- Match the surrounding code's patterns; smallest change that is correct.

## Hard rules (never violate)
- No fabrication: skip or flag rather than guess — no invented data, sources,
  metrics, or citations. Omit any claim you can't verify.
- Confidentiality: no real names, company/team names, emails, internal IDs, or
  identifying URLs in code, comments, docs, commits, or PR bodies — including
  git history. Fictional placeholders in fixtures. Scan before every commit;
  fail closed on any hit.
- Secrets via env/secret manager only.
- Do no harm: every change is net-positive across correctness, security,
  performance, tests, docs, data quality, and accessibility — never fix one axis
  by regressing another.
- Confirm before anything destructive, irreversible, billable, or shared-state.

## Project-specific standards (from the review)
<stack-specific red flags, data invariants, LLM-safety rules, perf/cost budgets>
```

---

**🚩 red flags**: a README describing an aspirational system; stale setup steps;
undocumented env vars; no architecture diagram; "see the code for details"; live
counts hard-coded in prose; a decision with no rationale anywhere; a project with
strict standards in a contributor's head but nothing an agent can read and apply;
conflicting agent-instruction files (`CLAUDE.md` vs `AGENTS.md`); a standards doc
that no gate enforces.
