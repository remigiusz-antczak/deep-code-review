# Machine report — the findings file a program can consume

**Read this when** writing Phase 5, when the run is a **re-verification** of an
earlier review (`PRIOR <path>`), or when another tool — an aggregator, a
dashboard, a CI gate, a second reviewer — will consume the findings rather than
a person reading the markdown. Expands Phase 5 in `method.md` and the templates
in `report-format.md`.

The markdown report is for a reader. This file is the same review for a
program: **what was looked at, what was not, and what was found — in that
order**, because a consumer that only sees findings cannot tell "no findings in
domain L" from "domain L was never opened."

---

## 1. Where it goes, and the two invariants

It rides **with the full technical table**: out-of-tree by default (session
scratch, the PR comment's attachment, `~/Downloads/`), and into the repo's
`code-review/` only under the same confirmation the report needs
(`findings-YYYY-MM-DD.yaml` beside `review-YYYY-MM-DD.md`, same date, same
run). **Disclosure extends the report's finding-level rule.** The committed
report keeps finding **`id` / `area` / `severity` only** (`report-format.md`); a
committed machine copy also keeps the disclosure-safe run header — `tool`,
`skill_version`, `date`, `scope`, `start_sha`, `archetype`, `stage` — and
`target` (its field definition already bars a private name — an already-public
name, or a role). It **generalizes the two identifier-vector fields**: `base_ref`
follows `report-format.md`'s branch-name rule (a real branch carries client and
ticket names → `feature/<redacted>`), and `prior` keeps only a generic dated
filename (a path can carry the same). `coverage`, `polarity`, observations,
evidence, and fixes stay out-of-tree until the fix ships.
`coverage` withheld from a public copy is not a clean run — the
every-domain-row invariant below governs the out-of-tree artifact.

- **Same findings, same ids, same severities as the markdown.** If they
  disagree, the file is wrong; fix it first. A consumer must never have to read
  the prose to trust the file.
- **A coverage row for every assigned domain, every run.** Absence of a row is
  not clean. This is Phase 0's `COVERAGE_LEDGER` and Phase 5's reconciliation
  written down where a program can read them.

**Style:** block-style YAML. Inline flow *maps* (`{a: b}`), anchors, and
chomped block scalars break minimal readers and get dropped silently; inline
flow *sequences of scalars* (`[a, b]`) are fine. No tabs.

## 2. The shape

```yaml
review:
  tool: deep-code-review
  skill_version: "1.128.0"
  date: 2026-09-15
  scope: FULL                  # FULL | DIFF | FILE
  base_ref: null               # the DIFF base, else null
  start_sha: 0123abc           # every evidence line resolves at this ref
  target: "the service"        # first-party public name where it is already published; a role otherwise
  archetype: api               # from the first-response block
  stage: growth                # prototype | mvp | growth | mature | UNVERIFIED
  prior: null                  # path of the prior machine report re-verified, else null

ground_truth:                  # each: ok | failed | not-run, with a note on anything not ok
  build: ok
  tests: ok
  host_ci: unverified          # pass | failed | no-ci | unverified
  gate_self_test: not-run      # proven-red | not-proven | not-run  (skip caps only this claim)
  lint_type_scan: ok
  authz_posture: "9 entry points · anon probed 9 · two-principal 6 · untested: /export"
  parity_coverage: "N/A"       # UI/parity target: "N/M screens verified · unverified: …" (report-format.md); caps the verdict below Approve while any screen is unverified or no correspondence table exists
  pipeline_run: not-run
  notes:
    - "gate_self_test: live tree occupied; no dedicated worktree — probe not run"
    - "pipeline_run: needs live credentials; read-only engagement"

coverage:                      # ONE ROW PER ASSIGNED DOMAIN (A–T and W). No row = not clean.
  A:
    status: scanned            # scanned | partial | not-scanned | not-applicable
    finder: unit-3             # fan-out only: the unit that covered it
    lead_read: true            # fan-out only: did the lead re-read it
  B:
    status: partial
    note: "mutating routes and webhook handlers only; UI routes not read"
  L:
    status: not-applicable
    note: "no IaC, containers, or cloud config in the tree"
  P:
    status: not-scanned
    note: "outside the engagement's slices; owner asked for the API surface"

findings:
  - id: F1
    title: "Status aggregation ignores the source-of-truth hierarchy"
    area: A                    # the domain letter (drives any downstream mapping)
    tag: "correctness"         # free text: OWASP/CWE/LLM id, sub-area, whatever helps
    severity: Critical         # Blocker | Critical | High | Medium | Low | Nit — gap rows only
    polarity: gap              # gap | strength
    confidence: CONFIRMED      # CONFIRMED | CORROBORATED | PLAUSIBLE | unverified
    latent: false              # true when real but not currently reachable (rubric)
    mechanism_unproven: false  # true when the failure was never reproduced under your control
    observation: >
      One sentence: the fact and the concrete failing case.
    evidence:
      - src/lib/aggregate.ts:486
      - src/lib/alert.ts:35
    fix: >
      The smallest correct change; root-cause where possible. Required on every gap row.
    compounds: [F27]           # other finding ids this one combines with (Phase 4)
    prior_id: null             # when re-verifying: the id this row corresponds to in `review.prior`
    prior_status: null         # fixed | still-open | changed — only with prior_id
  - id: F8
    title: "Tenant selection is JWT-sub-only"
    area: T
    polarity: strength         # an "Invariants verified to hold" row: evidence, no severity
    confidence: CONFIRMED
    observation: >
      No body, query, or header can select a tenant; anon GET → 401, two-principal swap → 403.
    evidence:
      - api/mw/tenant.ts:31
  - id: F12
    title: "Recipient list may be caller-controlled"
    area: B
    severity: High
    polarity: gap
    confidence: unverified
    resolves_with: "the recipients table schema (is org_id NOT NULL?)"
    observation: >
      …
    evidence:
      - src/app/api/email/route.ts:40
    fix: >
      …

prior_not_rechecked: []        # prior ids not re-examined this run (with `review.prior` set)
```

Field rules, beyond the comments above:

- **`coverage` is complete** — every assigned domain (A–T and W; U/V/X–Z are
  unassigned — `SKILL.md`'s domain map), including on `DIFF` and
  `FILE` scopes (where most rows are `not-applicable` or `partial` with the
  slice named). `scanned` needs no note; every other status needs one. On a
  fan-out, `finder` and `lead_read` carry the unit manifest's attribution
  (`parallel-audit.md`); a unit whose finder never completed is `unverified`
  in the note, never `scanned`.
- **`polarity: strength` rows are the "Invariants verified to hold" table**
  (the units' `checked_sound` lists after lead re-verify): evidence and
  confidence, no severity. Never file a strength as a `Low`.
- **`confidence`** (tiers defined in `parallel-audit.md` §4): `CONFIRMED` (lead re-verified at
  `start_sha`), `CORROBORATED` (independent units hit the same sink, then lead
  re-verified), `PLAUSIBLE` (unit-reported, not lead-verified — never silently
  promoted), `unverified` (with `resolves_with` naming the artifact that would
  settle it).
- **`fix` is required on every `gap` row**; "investigate" is not a fix. A fix
  whose mechanism was never reproduced carries `mechanism_unproven: true` and
  the finding stays open.
- **Ids are stable within a run and traceable across runs.** Number `F1…Fn`
  in severity order as the report does; `prior_id` links a row to the earlier
  file so a consumer can compute fixed / still-open / changed without a person
  writing the table.

## 3. Re-verifying a prior review (`PRIOR <path>`)

When invoked with a prior machine report — or when `code-review/` already
holds one for the same target and the user has not said otherwise:

1. **Re-verify every prior finding first**, before new hunting. Each gets a
   row with `prior_id` and `prior_status`, at the current `start_sha`:
   - `fixed` — the failing case no longer reproduces; cite the line that
     closes it, and file it as a `strength` row (a fix that held is an
     invariant to re-check next time).
   - `still-open` — reproduces as before; the row carries the current lines.
   - `changed` — the code moved but the defect persists in a new shape;
     describe the new failing case.
2. **List what you did not re-check** in `prior_not_rechecked`. An omitted
   prior id is indistinguishable from a fixed one to a consumer — the silent
   failure this file exists to prevent.
3. Only then spend the remaining budget on new findings.

The report gains a `## Re-verification` table from these rows
(`report-format.md`).

## 4. Fan-out: rows in, one file out

Units return **findings and `checked_sound` rows in the shape above** for
their owned paths — never their own verdict, count line, or report sections.
The lead re-verifies (`parallel-audit.md` §4), sets `confidence`, merges into
**one** report and **one** file, and fills every coverage row from the unit
manifest. Per-unit reports concatenated end to end carry N verdicts and no
run-level coverage; they are not a report.

## 5. What a consumer may and may not infer

- Findings present in a domain ⇒ that domain was at least `partial`.
- No findings in a domain ⇒ **nothing**, until its coverage row says `scanned`.
- A prior id absent from both `findings` and `prior_not_rechecked` is a defect
  in the file, not a fixed finding.
- Severity is the reviewer's property judgment at the recorded stage; the
  verdict lives in the report and is issued over scanned domains only. A
  consumer deriving its own gate should do the same.
