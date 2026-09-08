# Branches, merges & open-work triage

Read this on a **FULL / repo-level review** of a git repository with more than one
branch, or whenever the request names branch cleanup or open work — "clean up the
branches", "what's still open", "should this be merged to main or develop?", "does
this need a PR?", "which branches are stale / already merged / safe to delete?". It
is **N/A by scope on a narrow `DIFF`/`FILE`** (a PR/branch reviewed against a base
stays a compact packet) unless branch cleanup was explicitly asked. It expands
section **S** of `SKILL.md` with the detection commands, the per-branch decision
tree, the merge-strategy trade-offs, and the safety rails for acting on the
recommendation.
The deliverable is a **triage of all open work**: for every branch, one
recommendation and the exact command to carry it out.

Standards this file tracks (verified URLs + dates in `docs/standards-index.md`):
Trunk-Based Development, GitHub flow, GitLab flow, the git-flow branching model
(Vincent Driessen), Martin Fowler's *Patterns for Managing Source Code Branches*,
GitHub's merge-method and protected-branch docs, and the `git` reference manual
for the enumeration commands below.

**Boundary with `docs-and-dx.md` (section O) — no overlap.** O owns *is the
branch protection configured* (required PR / reviews / status checks, no
force-push, CODEOWNERS enforcement) as a repo-posture check. **This file owns
*what open work exists and what should happen to each piece of it*.** The one
seam — "must this particular merge go through a PR?" — is resolved here by
*reading* O's posture and cross-referencing it, never by restating the protection
checklist. Where the review fixes land (a branch + PR, security split off) is
`SKILL.md` Phase 5; this file triages the branches that already exist.

---

## 1 — Ground the branch set before judging it (fail closed, never "clean")

Every command below reads **local refs**. Local refs are only as current as the
last fetch, so an un-refreshed or shallow clone makes a repo with a dozen open
branches *look* empty — the exact "empty output is not a pass" trap the skill
condemns (`SKILL.md` principle 2). Before any triage:

- **Refresh and prune first:** `git fetch --all --prune`. A shallow clone
  (`git rev-parse --is-shallow-repository` → `true`) cannot see full history and
  its merged/unmerged answers are unreliable — say so and `git fetch --unshallow`
  or re-clone before trusting the result.
- **Open-PR / merged-PR state is forge state, not git state.** Whether a branch
  has an open PR, or was already **squash/rebase-merged via a PR**, lives on
  GitHub/GitLab/etc., not in local refs. Read it with `gh pr list --state all`
  (or the forge API). If that auth/tooling is absent, the PR column is
  **`unverified`** — name it as the resolving artifact (`SKILL.md` principle 3),
  do **not** infer "no PR" from its absence.
- **Forge-only branches you never fetched are invisible to git entirely.** State
  the coverage honestly: "triaged N local + M fetched remote branches; forge PR
  state <read via gh | unverified: no forge auth>." A triage that silently omits
  un-fetched branches is a false all-clear.
- **A truncated listing is not a complete count — the same trap at a different
  threshold.** `gh issue list` / `gh pr list` (and most forge list APIs) default
  to a page of **30** items; counting or triaging with no `--limit` (or no
  pagination loop) silently truncates there and under-reports everything past
  it — a real backlog of over a hundred can get reported as thirty. Before
  stating any count read from a forge list, pass a limit that comfortably
  exceeds the expected total (`--limit 500`, or paginate on a returned cursor)
  and say what limit was used. "Empty output is not a pass" above and
  "truncated output is not the total" are the same failure: trusting a list's
  *shape* without checking whether the list is actually complete.

Fail closed: if you cannot refresh the refs or read PR state, the triage is
`unverified` with the missing artifact named — never a confident "nothing to
clean up."

## 2 — Detect the branching model → this sets each branch's merge target

The user's "merge to develop **or** main" is answered here: **which** long-lived
branch feature work integrates into depends on the model the repo actually uses.
Detect it from the refs and docs, don't assume:

| Model | Long-lived branches | Feature work targets | Branch lifetime | Signals to detect it |
|---|---|---|---|---|
| **Trunk-Based Development** | one trunk (`main`) | **`main`** (trunk) directly, or a short-lived branch merged back fast | hours–2 days | single long-lived branch; short branch list; CI to main |
| **GitHub flow** | one (`main`), the default branch | **`main`** via PR, then delete the branch | short | PR-per-change; `main` default; branches deleted on merge |
| **git-flow (Driessen)** | **`main` + `develop`** | **`develop`** for features; `release/*` and `hotfix/*` off/onto `main` | mixed; some long-lived | a `develop` branch exists; `release/*`, `hotfix/*`, `feature/*` prefixes |
| **GitLab flow** | `main` + environment or `release/*` branches | **`main`** first ("upstream first"), then promoted downstream | short feature, long env | `production`/`staging`/`pre-prod` or `release/*` env branches |

Detect the repo's default branch on a clone with
`git symbolic-ref refs/remotes/origin/HEAD` — **it is often unset** (`fatal: … is
not a symbolic ref`); run `git remote set-head origin -a` first, or read
`gh repo view --json defaultBranchRef`. Then: **if a `develop` branch exists and
carries commits `main` doesn't, treat features as targeting `develop`** and
`release/*`/`hotfix/*` as targeting `main`; otherwise the target is the default
branch (`main`). State the detected model in one line before recommending targets —
if it's ambiguous (e.g. a lone `develop` with no supporting-branch convention),
that ambiguity is itself an owner decision, not a guess.

## 3 — Enumerate & classify every branch (validated commands)

Run these against the refreshed refs. Each row is a classification signal, not a
verdict — the verdict comes from the tree in §4. (All commands below were
validated against a scratch repo covering normal-merge, single- and multi-commit
squash-merge, rebase-merge, stale-unmerged, diverged, and deleted-remote cases.)

| Question | Command | Reading |
|---|---|---|
| Already merged (tip is an ancestor)? | `git branch --merged <target>` / `git branch -r --merged origin/<target>` | listed → tip is reachable from target; a normal or fast-forward/rebase merge |
| Not merged by tip? | `git branch --no-merged <target>` | listed → tip not an ancestor — but this **also lists squash-merged branches** whose content already landed (§ trap) |
| Content already applied (squash/rebase/cherry-pick)? | `git cherry -v <target> <branch>` | `-` = that commit is already upstream; `+` = not; **no output = fully applied** |
| Unique commits to bring in | `git log --oneline <target>..<branch>` / `git rev-list --count <target>..<branch>` | the work that a merge/PR would actually add |
| Ahead **and** behind (diverged)? | `git rev-list --left-right --count <target>...<branch>` | `A⇥B` → A commits only on target, B only on branch; both > 0 = diverged, needs rebase/merge before it lands cleanly |
| Staleness + tracking, sorted oldest-first | `git for-each-ref --sort=committerdate --format='%(refname:short) %(committerdate:relative) %(upstream:track)' refs/heads` | last-commit age per branch; drives the stale bucket |
| Remote branch deleted, local ref lingering | same `for-each-ref` → `%(upstream:track)` is `[gone]` (or `git branch -vv` shows `: gone]`) | the merged-and-cleaned-up-remotely case — safe to prune the local ref |
| Never pushed (the **only** copy) | `%(upstream:short)` empty in `for-each-ref` | work exists **nowhere but this disk** — deletion is data loss (§6) |

**The squash-merge trap (verified, and the most common false positive).**
`git branch --merged` reports a squash- or rebase-merged branch as **un**merged,
because its tip was never made an ancestor of the target. `git cherry` recovers
the **single-commit** squash and any rebase/cherry-pick (patch-ids match), **but a
multi-commit branch squashed into one commit defeats patch-id matching** — cherry
still shows `+` for every commit though the content is fully in `main`. So the
**forge's merged-PR list is the authoritative corroborator** for "already merged":
before recommending "open a PR / N commits to merge", cross-check
`gh pr list --state merged --head <branch>`. Recommending a merge for
already-merged work manufactures a conflict-laden PR — a fabricated finding.

## 4 — The decision tree (one recommendation per branch, target from §2)

Walk top-down; the first match wins. Every "merge/PR" resolves its **target** from
the detected model (§2) — `develop` under git-flow, else the default branch.

1. **Content already in the target** (normal-merged, or squash/rebase-merged
   confirmed by cherry *or* the forge merged-PR list) → **delete the branch**
   (local `git branch -d`; remote `git push origin --delete <b>`; local `[gone]`
   ref → `git fetch --prune` already flagged it). `-d` refuses if git thinks it's
   unmerged — for a confirmed squash-merge use `-D` **only after** the forge
   confirms the merge. **Before any delete, check for a stacked PR first**
   (§6) — a branch can be safely merged-away by every check above and still be
   the *base* of another open PR.
2. **Never pushed and holds unique commits (only copy)** → **push first**
   (`git push -u origin <b>`) so it's recoverable, *then* apply the rest of the
   tree. Never delete an unpushed unique branch (§6).
3. **Unmerged, coherent, ready, target is protected / needs review** → **open a
   PR** to the resolved target. If the branch is behind, rebase/refresh it first
   (step 6). Read O's protection posture to know whether a PR is *required* vs a
   direct merge is allowed.
4. **Unmerged, coherent, ready, trunk-based repo with no PR requirement** →
   **merge to trunk** (fast-forward or per the repo's merge strategy, §5) — or
   still prefer a PR if any status check or reviewer gate applies.
5. **Unmerged but mixes unrelated work, or bundles a security/permission change
   with routine edits** → **split**: the security-relevant part rides its own
   small PR (this *is* `SKILL.md` Phase 5's split-by-risk-surface rule); or
   **cherry-pick the one good commit** out of an otherwise-stale branch and drop
   the rest.
6. **Diverged (ahead + behind) or behind the target** → **rebase or merge the
   target in** to make it land cleanly, then re-triage (usually → step 3). Rebase
   only unshared/personal branches; a **shared** branch is merged, not rebased
   (§6).
7. **Stale + WIP + no clear owner intent** → **escalate to the owner** (a
   "Decisions needed" item) with the age, the unique-commit count, and the last
   author; do not guess whether abandoned work should ship.
8. **Open PR that should not be merged** (superseded, wrong approach) →
   **close as superseded** (don't merge, don't silently delete the discussion) —
   or **convert to draft** if it should stay visible and CI'd but not mergeable.
9. **Worth keeping but not now** → **tag-then-delete**: `git tag archive/<b> <b>`
   (or an `archive/*` ref) then delete the branch — reversible, and it clears the
   branch list without losing the work (§6).

## 5 — Merge strategy & "PR or direct merge?"

Match the repo's existing convention first (read merged history:
`git log --merges --oneline -20` — many merge commits ⇒ merge-commit repo;
near-linear ⇒ squash/rebase). The three GitHub methods and their trade-offs:

- **Merge commit** (default, `--no-ff`): preserves every commit and records a
  merge commit — full history, non-linear graph. Best when the individual commits
  are meaningful and you want an explicit integration point.
- **Squash and merge**: collapses the branch to a **single** commit on the
  target — clean, linear history, one revert unit; loses intra-branch granularity
  (and creates the §3 cherry trap for future triage).
- **Rebase and merge**: replays each commit onto the target with **no** merge
  commit — linear history that keeps individual commits. Rewrites the commits'
  identity, so it's for branches that were never depended on downstream.

**PR vs direct merge** is decided by O's protection posture, not preference: if
the target requires a PR + review + passing checks (a protected branch), the
recommendation is **always a PR** regardless of model. A merge queue, where
present, automates merges into a busy protected branch and tests each change
against the latest base so the branch is never broken by incompatible changes —
recommend it instead of racing merges. Never recommend a direct push to a
protected default branch (`SKILL.md` Phase 5).

### Merge trains — landing several ready PRs without a platform merge queue

When several independently-green PRs are ready at once and no merge queue is
available, merging one at a time and waiting for the base's CI between each
serializes for no benefit — the base was already known-green before each
subsequent PR's own checks ran. A **merge train** verifies the *combination*
once instead:

1. Build a **throwaway integration branch** off the target with every
   candidate PR's head merged in. Resolve any collision **keep-both**, never
   dropping one side — a generated/compiled-file collision follows §6's
   regenerate-don't-hand-splice rule.
2. Run the **full aggregate gate once** on that union. Green means the combined
   tree is sound.
3. Merge the member PRs **individually and back-to-back**, preserving each
   one's own commits and issue-closing keyword. **Never squash the union into
   one commit** — that orphans every member PR's own issue and review thread
   instead of closing them.
4. Discard the integration branch; it is never itself merged.

**Sequence a gate-adding PR last within the batch.** A PR that adds a new
required gate, merged first, forces every other PR in the batch to retrofit a
gate that didn't exist when it was authored — extra round-trips for no benefit.
When triaging several ready branches at once, check whether any changes
required-CI/gate configuration and put it at the back of the landing order.

## 6 — Safety rails (acting on the triage is destructive / shared-state)

Triage is **advice**; carrying it out mutates shared state. Under `SKILL.md`
principle 7 and the global "confirm before destructive/irreversible/shared-state"
rule, produce the recommendation + the exact command, and **execute only on
explicit approval** — the same opt-in bar as the Phase 6 imprint.

- **Never delete unique unmerged work.** Deleting a branch whose commits exist
  nowhere else is irreversible data loss. Gate every delete on "content is in the
  target (§3 confirmed) **or** it's tagged/pushed elsewhere." Prefer
  **tag-then-delete** so any delete is reversible.
- **A branch can be safely merged-away and still be another PR's base — check
  before deleting *any* branch, even a confirmed-merged one.** If another open
  PR uses this branch as its **base** (a stacked PR reviewing changes on top of
  an unmerged branch), deleting the base auto-closes the stacked PR on most
  forges, with no reopen/retarget once the base ref is gone — even though the
  underlying commits may survive a while in reflog/backup. Check first:
  `gh pr list --state open --base <branch>`. If any exist, retarget them
  (`gh pr edit <n> --base <new-base>`) or get explicit confirmation that losing
  that PR's thread is acceptable — every time, not only when a stack is
  suspected.
- **Never hand-resolve a merge conflict inside a generated/compiled file.**
  When two branches both regenerate the same derived artifact (a build output,
  a compiled config, a generated manifest/index) and a merge conflicts inside
  it, take either side, then **re-run the generator** against the merged source
  inputs — never hand-splice the two conflicting versions. A hand-merged
  generated file can be syntactically valid and still contain a combination no
  run of the generator would ever produce, and the corruption is often silent
  until a much later read (cross-ref domain H: a generated/source pair needs a
  parity test or a single generated source so this doesn't drift over time —
  this is the same failure at the moment of a merge conflict, not over time).
- **Never rewrite shared history.** Rebase/force-push only branches that are
  personal and undepended-on. When a force is genuinely needed, it is
  **`git push --force-with-lease`** (refuses if the remote moved under you), never
  `--force`. A rebase of a shared branch is a merge instead.
- **Deleting a branch does not scrub its objects.** A branch that ever carried a
  **secret or PII** is not remediated by deleting the branch — the objects remain
  reachable on the remote until GC/forge cleanup, and clones already have them.
  The remediation is **credential rotation** (and history purge / forge support),
  not `git push --delete`. Flag this as its own line, never "delete fixes it."
- **Remote deletes and history rewrites are confirmed, explicit, one at a time** —
  no batch `--delete` of a list the user hasn't seen and approved.
- **Gate an irreversible command on the verdict string, not just "ran" — and
  make sure a list-membership guard actually checks the list.** Two related
  failure shapes, both "the guard didn't guard because the shell's real
  semantics differ from the author's mental model":
  - A preflight/safety script's *contract* is often to print a pass/fail
    verdict while still exiting 0 (so a human watching sees the message) — or
    its exit code is checked but the next command runs unconditionally
    regardless. `./preflight.sh; ./publish.sh` (a bare `;`, or two unconditional
    steps) fires the irreversible command whether or not the gate passed. Before
    recommending or running a merge/delete/publish/deploy command, confirm the
    preceding gate's **documented pass condition** (an exact string and/or exit
    code checked with `&&`/`if`), not merely that it ran without erroring.
  - A **safety-critical exclusion list** (a held/blocked/do-not-merge set) is
    commonly checked with `for x in $LIST; do [ "$x" = "$item" ] && skip; done`
    — this silently breaks under any shell where an unquoted `$LIST` does not
    word-split (zsh, by default, does not; `for x in $LIST` then iterates
    **once** with `x` bound to the whole string, so the comparison almost never
    matches and the exclusion never fires). A script that is meant to run in
    "the reviewer's shell" cannot assume bash's word-splitting semantics. Use a
    **literal `case`/explicit split** instead — `case "$item" in
    id1|id2|id3) skip ;; esac`, or a line-based exact match
    (`printf '%s\n' "$LIST" | grep -qxF "$item"`) — for any exclusion check
    that gates an irreversible or shared-state action (a held-PR exclusion in a
    merge script is the canonical instance: a silently-broken guard here
    doesn't fail loud, it just merges the thing that was supposed to be
    excluded). Detector: grep scripts/CI config for a for-loop iterating an
    unquoted variable immediately followed by a merge/delete/publish/deploy
    call, and confirm the loop actually iterates more than once against a
    multi-item fixture in the shells the script claims to support.

## 7 — Severity discipline (don't turn cleanup into noise)

Branch hygiene has the same noise failure mode as dependency currency
(`dependency-currency-and-upgrades.md` §3): forty stale branches become forty
Lows that bury a real Critical. **Batch routine cleanup as ONE finding carrying
the triage table**; escalate a branch to its own finding only on consequence:

- **An unmerged security/bug fix sitting on a stale branch** (the fix exists but
  was never shipped) → **High** — the vulnerability is live *and* the fix is
  already written but unreleased.
- **A branch that is the only copy of real work** (never pushed) → **High** as a
  data-loss risk until it's pushed/tagged.
- **A long-lived `develop`/`release/*` badly diverged from `main`** → Medium
  merge-debt (Fowler: integration frequency; the longer branches live apart, the
  worse the eventual merge).
- **A branch carrying committed secrets/PII** → severity per the exposure
  boundary (`security-appsec.md`), and the remediation is rotation, not deletion
  (§6).
- **Everything else** — merged-and-undeleted, stale WIP, gone-upstream local
  refs, behind-but-clean → **one batched Low/Info** with the triage table and a
  recommendation to enable "auto-delete branch on merge" so it stops recurring.

Never let the volume of routine branch cleanup outrank a real defect.

## 8 — Spike / prototype branches (a naming convention, not a new gate)

A deliberately fidelity-capped, disposable-by-construction exploration (Shape
Up's breadboard/fat-marker-sketch idea, applied to code instead of design) is
cheap to discard *if it's marked as one before it's built*. This rides the
branch-pattern logic this domain already owns — not a new file, not a new gate:

- **Gate:** a branch matching a spike/prototype naming convention (`spike/*`,
  `prototype/*`, or the project's own documented equivalent) declares its
  timebox and throwaway status (in the branch's first commit message or a
  linked issue), and never merges to the target **as-is** — it is rewritten to
  production quality or explicitly "graduated" (renamed/re-based onto a normal
  feature branch) first. **Trigger:** branch-name pattern match only, at merge
  time — never fires on an ordinary feature branch. **Owning hat:** Release &
  docs (this domain already owns branch triage).
- **Planted-defect test:** a `spike/foo` branch merged directly to the target
  with no rewrite and no graduation marker → the gate flags it.

## Triage table (the deliverable — emitted in the report)

```
| Branch | Last commit | State | Unique commits | Open PR | Recommendation | Command |
|--------|-------------|-------|----------------|---------|----------------|---------|
| feature/x | 3 days ago | unmerged, ready | 4 | none | Open PR → develop | gh pr create -B develop -H feature/x |
| bugfix/y | 6 months ago | squash-merged (PR #42) | 0* | merged | Delete | git push origin --delete bugfix/y |
| spike/z  | 1 year ago  | stale WIP, only copy | 12 | none | Escalate to owner; push to preserve | git push -u origin spike/z |
```
`0*` = cherry shows commits but the forge confirms the PR merged (multi-commit
squash). Mark any PR column `unverified` when forge auth was absent (§1).

## 🚩 Red flags

- A `develop` branch that hasn't merged to `main` in months (git-flow gone stale).
- Dozens of merged-but-undeleted branches and **no** "auto-delete on merge".
- Long-lived `feature/*` branches many commits behind the target (merge debt).
- A branch with an unmerged security fix — the patch exists but never shipped.
- A branch that only exists on one machine (no upstream) — one disk failure from
  lost work.
- Recommending "merge / open a PR" for a branch the forge already merged via
  squash (the §3 trap) — a fabricated, conflict-generating finding.
- `git push --force` (not `--force-with-lease`) anywhere near a shared branch.
- "Just delete the branch" offered as the fix for a leaked secret.
- A branch deleted with no check for a stacked PR using it as base.
- A generated/compiled-file merge conflict resolved by hand-splicing instead of
  regenerating from the merged source inputs.
- A runbook/script chaining a preflight and an irreversible command with a bare
  `;` (or two unconditional steps) instead of the preflight's documented pass
  condition.
- A safety-critical exclusion/allowlist check built on an unquoted
  `for x in $VAR` loop with no verification it actually iterates per-item in
  the shells the script claims to support.
- A `spike/*`/`prototype/*` branch merged to the target as-is, with no rewrite
  and no graduation marker.
- A merge-train batch landing a gate-adding PR before the PRs it would force to
  retrofit that gate.

## Cross-references

- **`docs-and-dx.md` (section O)** — the branch-*protection* posture (required PR,
  reviews, checks, no force-push, CODEOWNERS). This file reads that posture to
  decide "PR vs direct merge"; it does not restate it.
- **`SKILL.md` Phase 0** — the open-branch / open-PR inventory that feeds this
  triage. **Phase 5** — where the triage table is emitted and where review fixes
  ride a branch + PR (security split off).
- **`security-appsec.md`** — a branch carrying secrets/PII is rated by the
  exposure boundary there; the §6 rotation-not-deletion rule applies.
- **`SKILL.md` severity rubric** — `latent`/consequence-scaled ratings; §7 mirrors
  the dependency-currency severity discipline.
