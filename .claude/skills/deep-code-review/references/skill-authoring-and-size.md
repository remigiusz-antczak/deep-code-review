# Skill authoring & size — keep SKILL.md lean

**Read this when** the target repository ships or installs agent skills
(`**/SKILL.md`, `.claude/skills/`, `.cursor/skills/`, `.agents/skills/`, …), or
when a `SKILL.md` is large, duplicative, or growing every time a lesson is
learned. This is a maintainability lens (domain H) on the skills themselves; for
their *security* see `security-agent-skills.md`.

## The problem

A skill accretes lessons. `SKILL.md` is pulled into the agent's context whenever
the skill is invoked, and its YAML `description` is loaded for **every** installed
skill on **every** session. So a skill that answers "where does this new lesson
go?" with "another paragraph in `SKILL.md`" becomes an unbounded, always-paid
context tax — the opposite of the leanness the skill is supposed to buy.

## The pattern: progressive disclosure

- **A thin, always-loaded core.** `SKILL.md` holds the non-negotiables, the
  method/spine, and a **routed index** — a short "read this when…" table. Nothing
  situational lives inline.
- **Depth in on-demand references.** `references/*.md` carry the procedures,
  payloads, tables, and worked examples, read only when the agent follows a
  pointer. This is the pattern this very skill uses (one map + `references/`).
- **Every reference is routed.** A reference the core never links is dead weight;
  a pointer to a missing file is a broken promise. Both are findings.
- **One fact per entry; compact on write.** When a lesson is codified, it is ONE
  line in the core index plus depth in a reference — not a restatement. Merge
  near-duplicates, prune superseded notes. A second copy of a checklist or
  definition is a duplication finding (this repo's own thesis).

## The size ratchet (flag when absent)

Standards that no gate enforces are a finding. A skill repo should cap SKILL.md
mechanically, the same way this repo gates routing:

- **Two budgets, because they are paid at different times.** Cap the `SKILL.md`
  **body** (an on-invocation cost; a token estimate of chars/4 is enough) and the
  **`description`** (an always-loaded, per-session cost; the Agent Skills spec
  caps it at 1024 characters). Measure and report both.
- **A documented budget, enforced** — a cheap CI/test check that FAILS when a
  `SKILL.md` bloats past the budget, not a warning nobody reads. The enforced body
  budget is **24000 bytes** (`ci.yml` runs `ci-gates.sh routing --max-bytes 24000`);
  over it FAILS, unless the skill is on the reasoned allowlist in `cmd_routing`
  (today only `agentic-delivery`, the full G0–G10 delivery OS).
- **A reasoned allowlist for genuine exceptions.** Every pin names the skill and a
  reason. Mirror the ratchet discipline: a pin is **allowed** its overage, never
  **required** to exhibit it — a skill that has since slimmed back under budget
  makes its pin a non-blocking notice, not a pass-forcing crutch.
- **A self-test that proves the detector fires** on an oversized fixture, so the
  ratchet cannot decay into decoration.

## Review checklist

- [ ] `SKILL.md` is a thin core + routed index, not a monolith. Situational depth
      is in `references/`.
- [ ] Every `references/*.md` is routed from `SKILL.md`; every routed path exists.
- [ ] No duplicated checklist/definition across `SKILL.md` and its references, or
      across sibling skills.
- [ ] `description` is within the 1024-char spec cap and is not a second copy of
      the body.
- [ ] A size gate caps SKILL.md (body + description) and **fails** on bloat, with a
      reasoned allowlist and a self-test that proves it fires. If the standard is
      documented but unenforced, that is the finding.
