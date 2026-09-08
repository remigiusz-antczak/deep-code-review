# Findings report — exact format

Read this when writing Phase 5 artifacts (chat BLUF, full technical table, plain-language report). Templates and rules live here so `SKILL.md` stays the map.

## Findings report — exact format

```
# Code Review — <target> (<FULL|DIFF|FILE>, base <ref>)

## Verdict
<Approve | Approve-with-nits | Changes-requested | Blocked> — one-line reason.
(When the repo has distinct risk surfaces — e.g. a live service plus a disabled
subsystem — give a **two-status verdict**, each scoped: e.g. "🟡 running system ·
🔴 enabling <subsystem>".)
(On a networked target the verdict is **capped below Approve** while any
data-bearing entry point is still listed as untested in `Authz posture` —
unprobed is `unverified`, not clean.)
Counts: Blocker N · Critical N · High N · Medium N · Low N · Nit N

## Ground truth
- Build: <ok / failed: …>
- Tests: <X/Y pass, Z skipped, coverage — scoped per subtree if any gate
  excludes code, e.g. `root: N (excludes X)` + `X: M (separate gate)`>
- Host CI (base <ref>): <pass | FAIL: <job> › <step> (run <id>) | NO_CI |
  unverified: no forge auth>
- Gate scope & self-test: <what the gates exclude; each gate proven red on a
  planted defect incl. empty/whitespace config where applicable, or
  `unverified`/skipped with reason — skip caps self-test only>
- Lint/type/scan: <results>
- Authz posture: <N entry points · anon probed N · cross-account M · untested: …>
- Pipeline/app run: <before-state metrics, or N/A>

## Findings
| ID | Sev | Area | Location | Issue | Impact | Fix |
|----|-----|------|----------|-------|--------|-----|
| F1 | Critical | Security/A05 | api/users.py:88 | SQL built by string concat | SQLi, full DB read | Parameterize / bound params |

## Detailed findings (Blocker / Critical / High only)
### F1 — <title>  [Critical]
- Where: <file:line>
- What: <precise description>
- Why it matters: <impact / exploit / wrong result>
- Evidence: <failing case, query plan, repro, or the offending snippet>
- Fix: <smallest correct change; root-cause where possible> — mark
  `mechanism-unproven` when the failure was never reproduced under your control
  (CI-only, intermittent, environment-specific), and name what would prove it (the
  failing seed, the constrained repro, the assertion that fails red first).

**The same evidence bar extends to status reporting, not only fix-closure.**
"N agents are working on this" or "should be fixed now," said before any lane
has produced a verified, green result, overstates progress the same way a
`mechanism-unproven` fix would if reported as simply "fixed." A task is
*running* until it has a green PR, a passing test you personally ran, or a
browser-verified change — report that state honestly, not as progress toward
done. Completion language ("fixed", "done", "shipped") with no citation (a PR
link, a run URL, a commit SHA, a screenshot) in the same message is the smell.

## Invariants verified to hold (affirmative — co-equal with Findings)
| Invariant | Where proven | What proves it | Confidence |
|-----------|--------------|----------------|------------|
| Tenant selection is JWT-`sub`-only; no body/query/header can select a tenant | api/mw/tenant.ts:31 | anon-GET → 401 and two-principal swap → 403; no untrusted tenant source in the loader | CONFIRMED |
(Primary deliverable on a hardened target — not "we found nothing" but the specific
properties opened and proven. Each row grounded at `file:line`@`START_SHA` with the
same snippet-or-drop rigor a finding gets; drop any you cannot quote. Coverage —
finder id + lead-read — reconciled per Phase 5.)

## Quality delta (if the pipeline ran)
| Metric | Before | After (if fixed) | Notes |
|---|---|---|---|
| Dedup rate / Fill rate / Records | … | … | |

## Branch & merge triage (FULL / repo-level review with open branches; else N/A)
Detected model: <trunk-based | GitHub flow | GitLab flow | git-flow> → target <main|develop>.
Coverage: <N local + M remote branches; PR state via gh | unverified: no forge auth>.
| Branch | Last commit | State | Unique commits | Open PR | Recommendation | Command |
|--------|-------------|-------|----------------|---------|----------------|---------|
| feature/x | 3 days ago | unmerged, ready | 4 | none | Open PR → develop | gh pr create -B develop -H feature/x |
| bugfix/y | 6 months ago | squash-merged (PR #42) | 0* | merged | Delete | git push origin --delete bugfix/y |
(Routine cleanup batched here as one Low/Info finding; consequence branches —
unmerged security fix, only-copy work — escalated in the findings table above.)

## Decisions needed (owner)
- <question> — needs <role/owner>.  (Includes any design-altering a11y/UX change.)

## What's good
- <brief; what to keep / what was done right>

## Standards imprint (Phase 6, if opted in)
- <what was added/merged into AGENTS.md (and peer pointers) / gates / templates,
  or "not requested">

## Human-readable report (default out-of-tree; in-repo on request)

Alongside the machine-actionable report above, produce a **plain-language report a
non-technical reader can act on**. It goes out-of-tree by default (`~/Downloads/`,
session scratch, or the PR comment); on the user's explicit request — and only on
an unshared, idle checkout — write it into a top-level `code-review/` directory
(create it if absent) so it is easy to find from the repo root, using a dated file
plus an index so history is preserved and nothing is overwritten. On a public
remote, apply Phase 5's disclosure limit: IDs, severities, and areas only. A
worked fictional example (machine + plain-language, with `CORROBORATED` /
`latent`) lives in `docs/example-review-report.md` in the skill repository, copied
to `references/example-review-report.md` by `install.sh`.

- `code-review/README.md` — index: one line per review (date · verdict · link).
- `code-review/review-YYYY-MM-DD.md` — the report for this run.

This output is additive and reversible (a new dated file); it never edits code.
Keep the language jargon-free — explain each risk as *what could happen*, not as
a CWE number — and link each item to its technical finding ID so an engineer can
jump to the detail. Relative links in this file resolve **from `code-review/`**
(e.g. `../docs/x.md`), and a new top-level dir must satisfy any doc-link gate.
Scrub **third-party proper nouns** too (public event/conference/product names are
usually not on a derived deny-set, so they pass the privacy gate but still leak
context) — keep committed findings generic. **Branch names and PR titles are an
identifier vector** — real ones carry client names, ticket IDs, and personal
prefixes (`feature/acme-integration`, `jane/wip-payroll`); generalize them in the
committed report (`feature/<redacted>`, "the client-integration branch") and keep
the raw branch/PR triage in the session output, which is not committed. After
writing, run the project's privacy/name gate over this file (Phase 5).

Template for `code-review/review-YYYY-MM-DD.md`:

```
# Code review — <project>, <date>

## In one line
<🟢 Healthy | 🟡 Needs attention | 🔴 Not ready to ship> — <one plain sentence>.
<If the project has two risk surfaces (e.g. what runs today vs. a switched-off
part), give one status for each — e.g. "🟡 what runs today · 🔴 before turning on
<the part>".>

## What this project does
<one short paragraph in plain language: the problem it solves and how>

## Health at a glance
| Area | Status | In plain words |
|---|---|---|
| Security | 🟢/🟡/🔴 | <e.g. "Strangers cannot reach other people's data" or "…they can — fix first"> |
| Correctness | 🟢/🟡/🔴 | <does it produce the right results?> |
| Data quality | 🟢/🟡/🔴 | <is the data real, and never overwritten with something worse?> |
| Speed & cost | 🟢/🟡/🔴 | <fast enough, and not paying for repeated/needless work?> |
| Reliability | 🟢/🟡/🔴 | <does it recover from errors without losing or corrupting data?> |
| Tests | 🟢/🟡/🔴 | <is it checked automatically so a change can't quietly break it?> |
| Documentation | 🟢/🟡/🔴 | <can a new person understand, set up, and run it?> |

## The most important things to fix (plain language)
1. **<plain-language title>** — what could go wrong, in human terms, and why it
   matters. *(Technical detail: F1.)*
2. …

## What's already good
- <what to keep — credit the things done right>

## Open work to tidy up (if there are leftover branches)
<plain language: how many unfinished/leftover branches exist, and what should
happen — e.g. "8 are already merged and safe to remove; 1 holds an unfinished fix
that was never shipped; 1 exists only on one machine and should be backed up." A
short "clean up / finish / decide" list, not the technical commands.>

## Decisions we need from you
- <owner decision — includes any fix that would noticeably change the current
  look/design, so you can point to a style guide or say it's a prototype>

## If nothing is fixed
<the practical risk in one or two sentences — data loss, a breach, a growing
bill, users blocked>

## How to read this
🟢 fine · 🟡 improve soon · 🔴 fix before shipping. The full technical report,
with exact file locations and fixes, is in <the findings above / the PR / link>.
```

---
