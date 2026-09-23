# Domain S checklist

Read this when domain S (Branches, merges & open-work triage) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### S. Branches, merges & open-work triage → `references/branch-and-merge-hygiene.md`
Apply on a **FULL / repo-level review**, or whenever the request names branches,
cleanup, or open work; **N/A by scope on a narrow `DIFF`/`FILE`**. The scope rule
(a base-reviewed PR/branch stays a compact packet — don't triage every branch to
review a ten-line change) and the deliverable (a **triage of all open work**: one
recommendation + the exact command per branch) are owned by
`references/branch-and-merge-hygiene.md`. Distinct from section O, which owns whether
branch *protection* is configured — this owns *what open work exists and what to
do with it*; the one seam ("must this merge go through a PR?") reads O's posture.
Landing and merge-gate mechanics (merge trains, stale greens, stuck required
checks): `references/merge-operations.md` — read it when landing or sequencing PRs.
- **Ground the branch set before judging it** — `git fetch --all --prune` first;
  an un-refreshed/shallow clone hides open branches and a "nothing to clean up" is
  then a false all-clear (principle 2). **Open-PR / merged-PR state is forge state,
  not git state** (`gh pr list`); if forge auth is absent, mark that column
  `unverified`, never infer "no PR."
- **Detect the branching model → it sets each branch's target.** The user's "merge
  to develop **or** main" is answered by the model in use: **git-flow** (a
  `develop` branch exists) merges features to `develop` and `release/*`/`hotfix/*`
  to `main`; **trunk-based / GitHub flow / GitLab flow** integrate to the default
  branch (`main`). State the detected model before recommending targets.
- **Classify by content, not just tip.** `git branch --merged` misses squash- and
  rebase-merged branches; `git cherry` recovers single-commit squashes and
  rebases but **a multi-commit squash defeats patch-id matching** — so the forge's
  merged-PR list is the authoritative "already merged" corroborator. Recommending
  a merge/PR for already-merged work is a fabricated, conflict-generating finding.
- **One recommendation per branch**, target resolved from the model: merge /
  open a PR / rebase-or-refresh / **delete-if-merged** / **split** (security part
  onto its own PR — Phase 5) / **cherry-pick the one good commit** / **close-as-
  superseded** / **convert-to-draft** / **tag-then-delete** (reversible) /
  **escalate to owner** (stale WIP). Carrying any of these out is
  destructive/shared-state — **advise + give the command, execute only on
  approval** (principle 7); **never delete unique unmerged work** (data loss —
  push or tag it first), never rewrite shared history (`--force-with-lease`, never
  `--force`).
- **A leaked secret is not remediated by deleting the branch** — the objects stay
  reachable on the remote until GC/forge cleanup and clones already have them;
  the fix is **credential rotation** (cross-ref B), not `git push --delete`.
- **Default depth on `FULL`: escalate the consequence branches, count the rest.**
  Name and rule on the branches whose consequence is real — an **unmerged security
  or bug fix**, a branch that is the **only copy** of work, a **badly diverged
  long-lived** `develop`/`release/*` — and give the remainder a **one-line count**
  ("11 merged-but-undeleted, 3 stale WIP; cleanup commands on request"). Produce
  the **full per-branch table only when the user asked for cleanup or branch
  triage**; an unrequested 40-row table is what pushes the Criticals off-screen.
- **Severity discipline** (mirrors K/dependency currency): batch routine cleanup
  as **one** Low/Info finding carrying the triage table; escalate individually only
  on consequence — an **unmerged security/bug fix on a stale branch** (written but
  never shipped) is **High**, a **branch that is the only copy** of real work is a
  **High** data-loss risk, a long-lived `develop`/`release/*` badly diverged is
  Medium merge-debt. Don't let branch-cleanup volume outrank a real defect.
- 🚩 a `develop` unmerged to `main` for months; dozens of merged-but-undeleted
  branches with no auto-delete-on-merge; a long-lived branch many commits behind
  its target; an unmerged security fix; a branch with no upstream (only copy); a
  "merge this" recommendation for a branch the forge already squash-merged;
  `git push --force` near a shared branch; "just delete the branch" offered as the
  fix for a committed secret.
