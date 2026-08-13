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

## 1. Assemble the shared context packet once, hand it to every subagent

A subagent that re-discovers the project from scratch spends most of its budget
re-reading what the lead already knows, and judges against a slightly different
bar. Assemble **one** packet and give the identical copy to each unit:

- **The project's hard rules, distilled** — the no-fabrication + confidentiality
  bar, the data-integrity invariants (if a data product), the LLM-safety rules
  (if it calls a model). One screen, not the whole `SKILL.md`.
- **The Phase-1 ground-truth summary** — what built, what passed, coverage, and
  the **gate scope** (which subtrees the gate excludes — see `SKILL.md` Phase 1).
- **The already-cleared list** — files/areas the lead has audited and that are
  therefore **not** to be re-reviewed.

Then give each subagent only its **unique scope + questions**. This pays the
domain-context duplication once instead of once per unit.

## 2. The fabrication-resistant subagent contract

Put every clause in each subagent's prompt. A clean large tree will otherwise
hand back a hundred confident inventions.

- **One named invariant per unit**, not "find problems in domain X." ("No
  update path can lower a populated field." "Every paid call is behind a
  pre-call cap.") A unit hunting a specific invariant reports real breaks; a unit
  told to "look for issues" fabricates to look thorough.
- **A finding requires `file:line` + the concrete failing input/state.** No
  failing case → not a finding. Ban severity words without a reproduction.
- **`NONE` is a correct, expected, valued answer.** Say so explicitly, or the
  unit invents an issue rather than return empty.
- **Cap findings (~5)** and **prefer running a probe over speculating** — a
  five-line script that proves the break is worth more than a paragraph of
  "this could…".

## 3. The orchestrator re-verifies every survivor — in both directions

No subagent finding enters the report on the subagent's authority. For each
survivor the lead **re-opens `file:line` and confirms against source,
adversarially** — and verification runs **two ways**:

- **Refute false positives.** Try to break the claim; a finding that can't be
  reproduced at source is dropped, not softened.
- **Test whether a `NONE`/caveat understated a gap.** A unit that returned
  "NONE, minor caveat" may have missed that the caveat *is* the finding.
  Verification catches **under**-reports, not only over-reports.

**Confidence marker on every finding** (surface it in the report):
- `CONFIRMED` — the lead independently re-verified it at `file:line`.
- `PLAUSIBLE` — subagent-reported, not yet lead-verified. A sibling of the
  `unverified` convention; **never silently promoted** to a bare finding.

## 4. Subagents inherit the reviewer's blind spots — inject the discriminators

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
  changelog as new bugs, once per unit.

---

**Delivery:** when a fan-out yields both routine fixes and a change to a
security/permission/authz boundary, split the remediation by risk surface (see
`SKILL.md` Phase 5) — the security-critical diff rides its own small PR for a
decorrelated reviewer, never buried under nits.
