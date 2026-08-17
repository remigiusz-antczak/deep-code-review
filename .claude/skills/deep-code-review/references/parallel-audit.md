# Parallel / fan-out review — protocol & anti-fabrication contract

Read this when the target is large enough to review across **parallel
subagents** (a `FULL` run of a large repo, or several focused domain passes at
once). A fan-out is very effective — but without a strict contract it manufactures
plausible-but-fake findings and re-derives project context N times. Expands the
"Review mechanics" note in `SKILL.md`; it operationalizes the "a second opinion
should be decorrelated" principle at scale.

The governing fact: **subagents share the orchestrator's blind spots and carry
their own authority into the report.** Both have to be engineered against.

---

## 0. Same pinned surface for every unit

Hand every audit the Phase-0 `START_SHA` (or the dedicated worktree path at that
SHA). Units read via `git show $START_SHA:path` / files in that worktree — never
"whatever is checked out now." A live tree another agent is editing will otherwise
produce disagreeing `file:line` citations and findings about code that does not
exist on the reviewed ref. If the harness cannot isolate a worktree, the lead
records that limitation and still requires every citation to resolve at
`START_SHA` on re-verify.

**Mega-files / huge blobs:** when a single file is too large to hold in one
context (tens of KB of dense logic, generated bundles, vendored trees), split by
**named concern** (auth surface, write path, egress, parser) with overlapping
seams of ~50–100 lines so call edges are not orphaned — still one invariant per
unit. Prefer symbol/grep entry points over linear whole-file reads. Do not invent
line numbers for unread regions; unread → `unverified` or out of scope.

---

## 1. Assemble the shared context packet once, hand it to every subagent

A subagent that re-discovers the project from scratch spends most of its budget
re-reading what the lead already knows, and judges against a slightly different
bar. Assemble **one** packet and give the identical copy to each unit:

- **The project's hard rules, distilled** — the no-fabrication + confidentiality
  bar (including **mask identifiers in your return**), the data-integrity
  invariants (if a data product), the LLM-safety rules (if it calls a model).
  One screen, not the whole `SKILL.md`.
- **`START_SHA` / worktree path** — the only tree they may cite.
- **The Phase-1 ground-truth summary** — what built, what passed, coverage, and
  the **gate scope** (which subtrees the gate excludes — see `SKILL.md` Phase 1).
- **Triage-first hits already found** — so units do not re-derive them; they may
  deepen a hit, not duplicate it as new.
- **The already-cleared list** — files/areas the lead has audited and that are
  therefore **not** to be re-reviewed.

Then give each subagent only its **unique scope + questions**. This pays the
domain-context duplication once instead of once per unit.

---

## 2. Read-only by toolset, not only by instruction

Review is read-only (principle 7). Fan-out units must not be able to mutate the
reviewed project just because the prompt said "don't edit."

- **Prefer a harness-enforced read-only tool allowlist:** Read / Grep / Glob /
  `git show` / `git log` / `git grep` (and similarly non-mutating inspect). No
  Edit, Write, apply-patch, or mutating shell (`git commit`, `git push`,
  `git checkout`, `git reset`, `rm`, redirects that overwrite project files).
- **If the harness cannot restrict tools,** the prompt must **forbid all mutating
  commands explicitly**, and the lead **snapshots the tree before fan-out**
  (`git status --porcelain` + `git rev-parse HEAD`) and **diffs after**. Any
  unexpected change → hard-fail the fan-out, restore from `START_SHA` /
  worktree, and discard that unit's unverified output until re-run read-only.
- Context-inheriting forks are especially dangerous: strip unrelated parent
  instructions ("open a PR", "commit this") from the unit prompt; give only the
  packet + one invariant.

### Harness notes (map the allowlist; do not pretend every host enforces it)

State in the fan-out preamble which case you are in. Prompt-only "don't edit"
is never enough by itself. **Contract is host-neutral** — only the spawn
mechanism changes.

| Host / pattern | How to get read-only audits | Fallback when you cannot |
|---|---|---|
| **Generic / any agent** | Spawn or hand off with an explicit tool allowlist: Read / Grep / Glob / non-mutating git only. Pass identical packet + `START_SHA` + one invariant. | Mutate-ban in prompt + lead before/after `git status` / `HEAD` diff; hard-fail on drift. Prefer a dedicated worktree the unit cannot push from. |
| **Cursor** (Task / subagents / skills) | Skills under `.cursor/skills/` or `.agents/skills/` (also loads `.claude/skills/` / `.codex/skills/`). Restrict tools when the Task UI offers it; otherwise treat as unrestricted. | Same tree-diff hard-fail. |
| **Claude Code** (subagents / Task) | Prefer a subagent/tool allowlist with no Edit/Write. Slash-invoke `/deep-code-review` when installed under `.claude/skills/`. | Mutate-ban + tree-diff. |
| **Codex** | May load `.codex/skills/` or follow `AGENTS.md`. Assume full Edit/Write/shell unless sandboxed. | Mutate-ban + tree-diff; worktree. |
| **Copilot / Gemini / Aider / Windsurf** | Usually instruction-file driven (`AGENTS.md`, copilot-instructions, `GEMINI.md`, `.windsurf/rules`). No reliable tool lockdown — sequential in-process invariants under principle 7, or external read-only checkout. | Same. |
| **One-shot paste** (no subagents) | No fan-out — run invariants sequentially in-process under principle 7. | N/A |

If the host documents a "read-only" / "ask" / "plan" mode, use it for audit
units and still re-verify at `START_SHA` — mode labels are not evidence.

---

## 3. The fabrication-resistant subagent contract

Put every clause in each subagent's prompt. A clean large tree will otherwise
hand back a hundred confident inventions.

- **One named invariant per unit**, not "find problems in domain X." ("No
  update path can lower a populated field." "Every paid call is behind a
  pre-call cap.") A unit hunting a specific invariant reports real breaks; a unit
  told to "look for issues" fabricates to look thorough.
- **A finding requires `file:line` + the concrete failing input/state**, and that
  `file:line` must resolve at `START_SHA`. No failing case → not a finding. Ban
  severity words without a reproduction.
- **`NONE` is a correct, expected, valued answer.** Say so explicitly, or the
  unit invents an issue rather than return empty.
- **Cap findings (~5)** and **prefer running a probe over speculating** — a
  five-line script that proves the break is worth more than a paragraph of
  "this could…". Probes that need a planted defect run only in the lead's
  dedicated worktree (Phase 1), never in a shared live tree.
- **Mask real identifiers in the unit's own output** before returning to the
  lead: emails, people/company names, internal IDs, hostnames, secret-shaped
  strings → role placeholders or redacted forms (`j***e@e***.com`). Fan-out is
  how PII otherwise reaches the lead's context and the report. Do not echo
  secret values even redacted if a fingerprint/`file:line` suffices.

---

## 4. The orchestrator re-verifies every survivor — in both directions

No subagent finding enters the report on the subagent's authority. For each
survivor the lead **re-opens `file:line` at `START_SHA` and confirms against
source, adversarially** — and verification runs **two ways**:

- **Refute false positives.** Try to break the claim; a finding that can't be
  reproduced at source is dropped, not softened. A citation that only exists on
  another branch / dirty tree is contamination — exclude it.
- **Test whether a `NONE`/caveat understated a gap.** A unit that returned
  "NONE, minor caveat" may have missed that the caveat *is* the finding.
  Verification catches **under**-reports, not only over-reports.

**Confidence marker on every finding** (surface it in the report):
- `CONFIRMED` — the lead independently re-verified it at `file:line` on
  `START_SHA`.
- `CORROBORATED` — two or more independent audit units (different invariants /
  angles) hit the same sink or defect class; still lead-re-verify before it
  blocks a gate, but treat convergence as a stronger signal than either alone.
- `PLAUSIBLE` — subagent-reported, not yet lead-verified. A sibling of the
  `unverified` convention; **never silently promoted** to a bare finding.

---

## 5. Subagents inherit the reviewer's blind spots — inject the discriminators

A tool that renders bytes, and a repo that documents its own past, fool every
unit the same way. Put both discriminators in **every** subagent prompt, and have
the orchestrator apply them to security-critical claims itself:

- **Byte-fidelity** (cross-ref principle 2, domains C & R): the viewer may
  collapse NUL / zero-width / bidi / BOM to whitespace or drop them. Any finding
  that hinges on an invisible or easily-confused character — "this delimiter is
  absent," "this comment is stale," "these two strings differ" — is checked at
  the byte level (`xxd` / `od` / a code-point dump) before it is asserted, and
  treated as `unverified` until then. This kills false "stale comment" findings
  **and** catches real invisible-character injection the render hides.
- **Live defect vs documented past one** (cross-ref Phase 4): comments often
  narrate fixed incidents in present tense (`Audit 2026-…`, `Bug B`, `live
  incident …`). Before reporting, apply the discriminator: (a) is there a test
  pinning the corrected behavior? (b) does `git log -S'<symbol>' --oneline` (or
  `git log -L`) show the fix already landed? If either is yes, it is a historical
  note, not a finding. A fan-out will otherwise re-report the repo's own
  changelog as new bugs, once per unit. Pair with Phase 0's **measured** history
  depth — do not argue from a README claim that history is absent.

---

**Delivery:** when a fan-out yields both routine fixes and a change to a
security/permission/authz boundary, split the remediation by risk surface (see
`SKILL.md` Phase 5) — the security-critical diff rides its own small PR for a
decorrelated reviewer, never buried under nits. Report files follow Phase 5's
shared-tree escape hatch.
