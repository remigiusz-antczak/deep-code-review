# Branches, merges & open-work triage

Read this on a **FULL / repo-level review** of a git repo with more than one branch, or whenever the request
names branch cleanup or open work — "clean up the branches", "what's still open", "should this merge to main
or develop?", "does this need a PR?", "which branches are stale / already merged / safe to delete?". **N/A by
scope on a narrow `DIFF`/`FILE`** (a PR/branch reviewed against a base stays a compact packet) unless branch
cleanup was explicitly asked. Expands section **S** of `SKILL.md`: detection commands, per-branch decision
tree, merge-strategy trade-offs, and safety rails for acting on the recommendation. The deliverable is a
**triage of all open work**: one recommendation per branch, plus the exact command to carry it out.

Standards this file tracks (verified URLs + dates in `docs/standards-index.md`): Trunk-Based Development,
GitHub flow, GitLab flow, the git-flow branching model (Vincent Driessen), Martin Fowler's *Patterns for
Managing Source Code Branches*, GitHub's merge-method and protected-branch docs, and the `git` reference
manual for the enumeration commands below.

**Boundary with `docs-and-dx.md` (section O) — no overlap.** O owns *is branch protection configured*
(required PR / reviews / status checks, no force-push, CODEOWNERS) as a repo-posture check. **This file owns
*what open work exists and what should happen to each piece of it*.** The one seam — "must this merge go
through a PR?" — is resolved by *reading* O's posture and cross-referencing it, never restating the protection
checklist. Where review fixes land (a branch + PR, security split off) is `SKILL.md` Phase 5; this file
triages branches that already exist.

---

## 1 — Ground the branch set before judging it (fail closed, never "clean")

Every command below reads **local refs**, only as current as the last fetch — an un-refreshed or shallow clone
makes a repo with a dozen open branches *look* empty, the exact "empty output is not a pass" trap the skill
condemns (`SKILL.md` principle 2). Before any triage:

- **Refresh and prune first:** `git fetch --all --prune`. A shallow clone
  (`git rev-parse --is-shallow-repository` → `true`) can't see full history, so its merged/unmerged answers
  are unreliable — say so and `git fetch --unshallow` or re-clone before trusting the result.
- **Open-PR / merged-PR state is forge state, not git state.** Whether a branch has an open PR, or was already
  **squash/rebase-merged via a PR**, lives on GitHub/GitLab/etc., not local refs. Read it with
  `gh pr list --state all` (or the forge API). Absent that auth/tooling, the PR column is **`unverified`** —
  name it as the resolving artifact (`SKILL.md` principle 3); do **not** infer "no PR" from its absence.
- **Forge-only branches you never fetched are invisible to git entirely.** State the coverage honestly:
  "triaged N local + M fetched remote branches; forge PR state <read via gh | unverified: no forge auth>." A
  triage that silently omits un-fetched branches is a false all-clear.
- **A truncated listing is not a complete count — the same trap at a different threshold.** `gh issue list` /
  `gh pr list` (and most forge list APIs) default to a page of **30**; counting or triaging with no `--limit`
  (or no pagination loop) silently truncates there and under-reports everything past it — a real backlog of
  over a hundred can read as thirty. Before stating any count from a forge list, pass a limit that comfortably
  exceeds the expected total (`--limit 500`, or paginate on a returned cursor) and say what limit was used.
  "Empty output is not a pass" above and "truncated output is not the total" are the same failure: trusting a
  list's *shape* without checking whether it's actually complete.

Fail closed: if refs can't be refreshed or PR state read, the triage is `unverified` with the missing artifact
named — never a confident "nothing to clean up."

## 2 — Detect the branching model → this sets each branch's merge target

The user's "merge to develop **or** main" is answered here: **which** long-lived branch feature work
integrates into depends on the model the repo actually uses. Detect it from refs and docs, don't assume:

| Model | Long-lived branches | Feature work targets | Branch lifetime | Signals to detect it |
|---|---|---|---|---|
| **Trunk-Based Development** | one trunk (`main`) | **`main`** (trunk) directly, or a short-lived branch merged back fast | hours–2 days | single long-lived branch; short branch list; CI to main |
| **GitHub flow** | one (`main`), the default branch | **`main`** via PR, then delete the branch | short | PR-per-change; `main` default; branches deleted on merge |
| **git-flow (Driessen)** | **`main` + `develop`** | **`develop`** for features; `release/*` and `hotfix/*` off/onto `main` | mixed; some long-lived | a `develop` branch exists; `release/*`, `hotfix/*`, `feature/*` prefixes |
| **GitLab flow** | `main` + environment or `release/*` branches | **`main`** first ("upstream first"), then promoted downstream | short feature, long env | `production`/`staging`/`pre-prod` or `release/*` env branches |

Detect the repo's default branch with `git symbolic-ref refs/remotes/origin/HEAD` — **often unset**
(`fatal: … is not a symbolic ref`); run `git remote set-head origin -a` first, or read
`gh repo view --json defaultBranchRef`. Then: **if a `develop` branch exists and carries commits `main`
doesn't, treat features as targeting `develop`** and `release/*`/`hotfix/*` as targeting `main`; otherwise the
target is the default branch (`main`). State the detected model in one line before recommending targets — if
ambiguous (e.g. a lone `develop` with no supporting-branch convention), that's an owner decision, not a guess.

**Check the base of work *in flight*, not only the target of finished branches.** Once the model names the
integration target, enumerate in-flight work against it: open PRs
(`gh pr list --state open --limit 500 --json number,baseRefName,headRefName,changedFiles` — pass a limit
exceeding the expected total and say which, per §1; the default 30 silently truncates) **and** pushed branches
with no PR yet (§3's `for-each-ref` enumeration — where retargeting is still cheapest). Verify each one's
**base** against that target with the §3 divergence count
(`git rev-list --left-right --count <integration-target>...<branch>`). A large change branched off the
**wrong** base — e.g. off `main` while features integrate into `develop`, which carries commits `main` lacks —
is written against a product state that no longer exists on the integration line; merging it later conflicts
with or reverts those commits, and every lane built on that base inherits the problem. A PR's own green checks
say nothing about whether its **base** is right; that's a §7 severity call, below.

## 3 — Enumerate & classify every branch (validated commands)

Run these against refreshed refs. Each row is a classification signal, not a verdict — the verdict comes from
the §4 tree. (All commands below were validated against a scratch repo covering normal-merge, single- and
multi-commit squash-merge, rebase-merge, stale-unmerged, diverged, and deleted-remote cases.)

| Question | Command | Reading |
|---|---|---|
| Already merged (tip is an ancestor)? | `git branch --merged <target>` / `git branch -r --merged origin/<target>` | listed → tip is reachable from target; a normal or fast-forward/rebase merge |
| Not merged by tip? | `git branch --no-merged <target>` | listed → tip not an ancestor — but this **also lists squash-merged branches** whose content already landed (§ trap) |
| Content already applied (squash/rebase/cherry-pick)? | `git cherry -v <target> <branch>` | `-` = that commit is already upstream; `+` = not; **no output = fully applied** |
| Unique commits to bring in | `git log --oneline <target>..<branch>` / `git rev-list --count <target>..<branch>` | the work a merge/PR would actually add |
| Ahead **and** behind (diverged)? | `git rev-list --left-right --count <target>...<branch>` | `A⇥B` → A commits only on target, B only on branch; both > 0 = diverged, needs rebase/merge before it lands cleanly |
| Staleness + tracking, sorted oldest-first | `git for-each-ref --sort=committerdate --format='%(refname:short) %(committerdate:relative) %(upstream:track)' refs/heads` | last-commit age per branch; drives the stale bucket |
| Remote branch deleted, local ref lingering | same `for-each-ref` → `%(upstream:track)` is `[gone]` (or `git branch -vv` shows `: gone]`) | merged-and-cleaned-up-remotely — safe to prune the local ref |
| Never pushed (the **only** copy) | `%(upstream:short)` empty in `for-each-ref` | work exists **nowhere but this disk** — deletion is data loss (§6) |

**The squash-merge trap (verified, and the most common false positive).** `git branch --merged` reports a
squash- or rebase-merged branch as **un**merged, since its tip never became an ancestor of the target.
`git cherry` recovers the **single-commit** squash and any rebase/cherry-pick (patch-ids match), **but a
multi-commit branch squashed into one commit defeats patch-id matching** — cherry still shows `+` for every
commit though the content is fully in `main`. So the **forge's merged-PR list is the authoritative
corroborator** for "already merged": before recommending "open a PR / N commits to merge," cross-check
`gh pr list --state merged --head <branch>`. Recommending a merge for already-merged work manufactures a
conflict-laden PR — a fabricated finding.

## 4 — The decision tree (one recommendation per branch, target from §2)

Walk top-down; the first match wins. Every "merge/PR" resolves its **target** from the detected model (§2) —
`develop` under git-flow, else the default branch.

1. **Content already in the target** (normal-merged, or squash/rebase-merged confirmed by cherry *or* the
   forge merged-PR list) → **delete the branch** (local `git branch -d`; remote
   `git push origin --delete <b>`; local `[gone]` ref → `git fetch --prune` already flagged it). `-d` refuses
   if git thinks it's unmerged — for a confirmed squash-merge use `-D` **only after** the forge confirms the
   merge. **Before any delete, check for a stacked PR first** (§6) — a branch can be safely merged-away by
   every check above and still be the *base* of another open PR.
2. **Never pushed and holds unique commits (only copy)** → **push first** (`git push -u origin <b>`) so it's
   recoverable, *then* apply the rest of the tree. Never delete an unpushed unique branch (§6).
3. **Unmerged, coherent, ready, target is protected / needs review** → **open a PR** to the resolved target.
   If the branch is behind, rebase/refresh it first (step 6). Read O's protection posture to know whether a PR
   is *required* vs a direct merge is allowed.
4. **Unmerged, coherent, ready, trunk-based repo with no PR requirement** → **merge to trunk** (fast-forward
   or per the repo's merge strategy, §5) — or still prefer a PR if any status check or reviewer gate applies.
5. **Unmerged but mixes unrelated work, or bundles a security/permission change with routine edits** →
   **split**: the security-relevant part rides its own small PR (this *is* `SKILL.md` Phase 5's
   split-by-risk-surface rule); or **cherry-pick the one good commit** out of an otherwise-stale branch and
   drop the rest.
6. **Diverged (ahead + behind) or behind the target** → **rebase or merge the target in** to land cleanly,
   then re-triage (usually → step 3). Rebase only unshared/personal branches; a **shared** branch is merged,
   not rebased (§6). For a **long-open** branch this is necessary but not sufficient — rebasing and re-running
   CI doesn't prove the merge won't revert work the target landed since the branch forked; verify its effect
   against current HEAD first (§6, long-open-PR bullet).
7. **Stale + WIP + no clear owner intent** → **escalate to the owner** (a "Decisions needed" item) with the
   age, unique-commit count, and last author; don't guess whether abandoned work should ship.
8. **Open PR that should not be merged** (superseded, wrong approach) → **close as superseded** (don't merge,
   don't silently delete the discussion) — or **convert to draft** if it should stay visible and CI'd but not
   mergeable.
9. **Worth keeping but not now** → **tag-then-delete**: `git tag archive/<b> <b>` (or an `archive/*` ref) then
   delete the branch — reversible, clears the branch list without losing the work (§6).

## 5 — Merge strategy & "PR or direct merge?"

Match the repo's existing convention first (read merged history: `git log --merges --oneline -20` — many merge
commits ⇒ merge-commit repo; near-linear ⇒ squash/rebase). The three GitHub methods and their trade-offs:

- **Merge commit** (default, `--no-ff`): preserves every commit and records a merge commit — full history,
  non-linear graph. Best when individual commits are meaningful and an explicit integration point is wanted.
- **Squash and merge**: collapses the branch to a **single** commit on the target — clean, linear history, one
  revert unit; loses intra-branch granularity (and creates the §3 cherry trap for future triage).
- **Rebase and merge**: replays each commit onto the target with **no** merge commit — linear history that
  keeps individual commits. Rewrites the commits' identity, so it's for branches never depended on downstream.

**PR vs direct merge** is decided by O's protection posture, not preference: if the target requires a PR +
review + passing checks (a protected branch), the recommendation is **always a PR** regardless of model. A
merge queue, where present, automates merges into a busy protected branch and tests each change against the
latest base so the branch is never broken by incompatible changes — recommend it instead of racing merges.
Never recommend a direct push to a protected default branch (`SKILL.md` Phase 5).

**The rest of §5 — landing and merge-pipeline mechanics** (merge trains, the mergeable snapshot, stale greens, red bases, hung or unsatisfiable required checks, PR-body gates, the merge base, self-reported evidence, worktree hooks, stacked-PR CI attribution, stop semantics) **lives in `merge-operations.md`.** Load it when landing or sequencing PRs, or when a merge gate or required check is stuck, stale, red, or in question.

## 6 — Safety rails (acting on the triage is destructive / shared-state)

Triage is **advice**; carrying it out mutates shared state. Under `SKILL.md` principle 7 and the global
"confirm before destructive/irreversible/shared-state" rule, produce the recommendation + the exact command,
and **execute only on explicit approval** — the same opt-in bar as the Phase 6 imprint.

- **Never delete unique unmerged work.** Deleting a branch whose commits exist nowhere else is irreversible
  data loss. Gate every delete on "content is in the target (§3 confirmed) **or** it's tagged/pushed
  elsewhere." Prefer **tag-then-delete** so any delete is reversible.
- **A branch can be safely merged-away and still be another PR's base — check before deleting *any* branch,
  even a confirmed-merged one.** If another open PR uses this branch as its **base** (a stacked PR reviewing
  changes on top of an unmerged branch), deleting the base auto-closes the stacked PR on most forges, with no
  reopen/retarget once the base ref is gone — even though the underlying commits may survive a while in
  reflog/backup. Check first: `gh pr list --state open --base <branch>`. If any exist, retarget them
  (`gh pr edit <n> --base <new-base>`) or get explicit confirmation that losing that PR's thread is acceptable
  — every time, not only when a stack is suspected.
- **Once a stacked PR has already auto-closed this way, pushing more commits to its branch does not revive it
  — it recreates a bare orphan branch with no PR attached**, so the work must be re-proposed as a new PR
  (retargeted onto the shared base, or rebased onto the parent's post-merge commits) rather than "fixed" by
  pushing again. Prevent it instead: retarget the child PR onto the shared base **before** merging the parent
  (`gh pr edit <n> --base <shared-base>`), or open the child against the shared base from the start and rebase
  onto the parent's commits rather than branching off the parent's own branch — the check-before-delete
  mechanics are the bullet above. **Corollary for reading PR state during any triage:** a forge's `closed`
  state doesn't distinguish "closed via merge" from "closed unmerged" — this orphan-close and a normal
  squash/merge both read `closed`. Before treating a closed PR as done or its branch as safe to delete, check
  the `merged` field too (`gh pr view --json state,mergedAt`), never `state` alone.
- **Never hand-resolve a merge conflict inside a generated/compiled file.** When two branches both regenerate
  the same derived artifact (a build output, a compiled config, a generated manifest/index) and a merge
  conflicts inside it, take either side, then **re-run the generator** against the merged source inputs —
  never hand-splice the two conflicting versions. A hand-merged generated file can be syntactically valid and
  still contain a combination no run of the generator would ever produce, and the corruption is often silent
  until a much later read (cross-ref domain H: a generated/source pair needs a parity test or a single
  generated source so this doesn't drift over time — same failure, at the moment of a merge conflict rather
  than over time).
- **Two PRs regenerating the same artifact can both be valid with *no* conflict — a silent regression, not a
  merge error.** The rule above fires on a conflict; the worse case fires on none. When two open PRs each
  rebuild a derived artifact (`out/`, a lockfile, a compiled index, `app/data/`) from a shared source tree,
  each writes a valid file from its **own** base, git merges both cleanly, and whichever lands second
  **silently drops the first's regeneration** — nothing marks it. Trigger to watch: this PR regenerates an
  artifact **and another open PR touches the same source** that produces it
  (`gh pr list --state open --limit 500` — the `--limit` matters, §1). Fix: the second PR **rebases onto the
  merged first and rebuilds** from the combined source (a superset fold), never layering its own partial
  build. Flag a generated-artifact PR as **superset-fold-required** while a sibling source PR is open.
- **A PR whose *only* conflict is a generated/compiled artifact re-conflicts on every same-class merge — a
  structural loop, not a normal rebase-able conflict.** When the sole conflicting path is a **derived file
  neither side hand-edited** (a lockfile, a bundled `dist/`, a checksums/manifest file, a generated schema or
  client) and many open PRs regenerate it from a shared source, "rebase and it's clean" is false **by
  construction**: each same-class PR that lands **rewrites that serialization**, so a branch you just rebased
  green re-conflicts before it can merge, and under steady merge volume it re-stales faster than any
  human/agent can rebase — an unwinnable loop that reads as a perpetually "almost-ready" PR while compute
  burns on re-rebasing. Distinct from the silent-drop case above, which fires on *no* conflict (last writer
  wins); this fires on a conflict that **never clears**. Distinct, too, from §5's sweep-while-resolving
  treadmill (a *coordinator* re-dirties a cluster with a concurrent merge sweep): this needs no coordinator —
  ambient merge cadence alone drives it. **After the second re-conflict whose only path is a generated
  artifact, stop rebasing** and change strategy: get the PR green + mergeable **once** and land it inside a
  window where no same-class PR merges (§5's freeze-the-merge-step / a single merge-seat holding the class's
  other merges for the brief handoff), always **taking trunk's copy and re-running the generator** rather than
  hand-splicing (the regenerate-from-merged-inputs rule above). **Durable fix — stop conflicting at all:**
  regenerate the artifact as a **post-merge / CI step** (or stop committing it and build it in CI), or
  serialize the class and regenerate it **last**, so same-class PRs never block each other on it. A local git
  merge driver looks like the durable fix but only mitigates *your* local merge — see the next bullet. **🚩**
  rising rebase attempts per merged PR whose only conflicting path is a generated file; treating a
  generated-only conflict as resolve-by-rebase.
- **A git merge driver resolves the artifact conflict only on a *local* merge/rebase — the forge's server-side
  merge never runs it, so the PR still shows CONFLICTING.** Registering a custom driver
  (`.gitattributes merge=<driver>` + a resolver script set up per-clone) so conflicts in the artifact
  auto-resolve (take either side + regenerate) fixes only a **local** `git merge`/`rebase` on a clone where
  the driver is registered. A merge driver is a **client-side** feature — registered per-clone in local git
  config, run only by git on a clone that has it — so a host computing mergeability and merging on **its own
  servers** has no reason to run your repo's local resolver and treats the artifact as an ordinary conflict.
  On **GitHub** this is observable: the "Merge" button / merge API / auto-merge / merge queue and its
  mergeability computation **ignore custom `.gitattributes merge=` drivers** (should generalize to other
  forges but is **not independently verified** here, per the async-mergeability note in §5) — so a PR whose
  only conflict is the driver-handled artifact still displays **CONFLICTING indefinitely**, the host merge
  button stays disabled, and auto-merge never fires, even though the conflict is trivially auto-resolvable on
  any driver-registered clone. Teams then waste effort "rebasing to fix it" through the host UI (which can't),
  conclude the driver is broken (it isn't), or build a second driver (redundant). **Don't read
  host-CONFLICTING on a driver-managed path as a real conflict** — confirm whether the *only* conflicting path
  is the driver-managed artifact. **Land it via a local merge/rebase on a driver-registered clone, then push
  the resolved head:** the local resolution leaves no conflict, so the push flips the host to MERGEABLE and
  the normal host merge then works; **document the mechanic next to the driver** ("resolve/land locally; the
  host won't run this driver"). The rule uniting both bullets: **a merge driver is a client-side convenience
  for your own merge; it never changes the PR's forge-visible state** — the only host-visible fix is a
  **pushed commit that carries no conflict** (regenerate-and-push, or don't commit the artifact and build it
  in CI, previous bullet). **🚩** a PR stuck at host-CONFLICTING whose only conflicting path is a
  driver-managed generated file.
- **A subset absorbed at a stale SHA can revert a later fix — no conflict, last writer wins.** Distinct from
  the superset-fold case above (a *derived* file rebuilt from source): here PR B **absorbed PR A's own source
  content** at an **older** tip, missing A's later commits (say a disabled-submit guard A fixed in
  follow-ups). Merge A, then merge B, and B's stale copy of those files silently overwrites A's fix — git sees
  no conflict, so nothing warns. Before landing: if B's history carries a **subset of A at older SHAs** (same
  files, earlier commits), don't merge B as-is after A — merge the **fuller tip first** and rebase B onto it,
  replaying only B's unique commits, **or** fold A's missing commits into B and merge B once. After landing,
  **grep the live tree for the fixed symbol** (the guard, the hard limit); never trust "B included A."
- **A long-open PR is reviewed against its own fork point, so its diff cannot reveal a revert of work the base
  shipped after it branched.** Distinct from the subset-absorb case above (two open PRs, B holding a stale
  subset of A): here **one** PR sat open while the integration branch raced hundreds of commits ahead, and the
  trap is that the **review surface itself is merge-base-relative**. A PR's "Files changed" view is
  **typically** merge-base-relative — as is `git diff <base>...<branch>`, which `git-diff(1)` defines as
  `git diff $(git merge-base <base> <branch>) <branch>` — showing only what the branch changed *since it
  forked*. That looks correct (it **is** the intended change from the old fork point) but is **blind by
  construction** to everything the base landed on those same files afterward. So green + mergeable + a clean
  Files-changed is a **false all-clear**: where the branch edited a file the base has since advanced (a landed
  fix, a hardening), merging can drop that newer work. A plain three-way merge would at least **conflict
  loudly** where both sides edited the same lines — but the silent paths don't: a **squash-merge** lands the
  branch's tree for the files it changed (the base's newer content in them goes with it — the §5 squash
  trade-off / §3 cherry trap), an automated resolution **toward the branch** (`--theirs`, the §6 hazard below)
  takes the stale side outright, and even a **textually clean** merge can defeat the fix **semantically** when
  the branch edited a different region (a caller) than the base hardened (the callee). The branch's own green
  proves nothing either — it ran against its fork-point view of the world. **Two-dot
  `git diff <base>..<branch>` is the mirror trap:** it *over*-reports, flagging every file the base advanced
  but the branch never touched as a **phantom reversion** the real three-way merge would not produce — a lead
  to triage, never the verdict. Take the verdict against **current HEAD**: list the paths the PR touches
  (`git diff --name-only $(git merge-base <base> <branch>) <branch>`), ask whether the base landed commits on
  any of them since the fork (`git log $(git merge-base <base> <branch>)..<base> -- <those paths>` — non-empty
  means the PR's tree predates real work there), and prove the actual effect by **trial-merging onto current
  HEAD** — the throwaway integration branch of §5, cut off HEAD — and diffing that result against HEAD.
  **Notation follows the question:** merge-base-relative (three-dot) is right for *what did this branch write*
  and correctly suppresses the two-dot phantom reversions (the duplicate-close bullet below picks notation the
  same way), but it **cannot** answer *would merging undo shipped work* — that needs the base's post-fork
  side, which three-dot excludes. **"Rebase and re-run CI" is necessary, not sufficient:** a rebase can
  silently keep the stale side of exactly those files. If the PR's intent already landed on the base (its
  linked issues closed elsewhere), it's **verify-then-close**, not merge; closing someone else's PR is an
  owner call (§6 opening) — surface the touched-path-vs-HEAD evidence, don't act unilaterally.
- **"Is X shipped / live / already fixed?" is a *containment* question against the ref that governs "shipped"
  — a commit-grep on whatever checkout you have out, or a "the PR is merged" status, answers a different
  one.** A `git log --grep` / `-S` hit, a green "Files changed", or a merged-PR record only proves the change
  exists on **some** ref — the branch currently checked out, or the integration branch a PR merged **into**.
  Where a long-lived integration / `development` branch runs far ahead of the line that actually governs
  "shipped" (the release branch, the ref deploy promotes from — often **not** the integration tip, and never a
  **stale local checkout** drifted behind its own remote), a large amount of merged, grep-visible work is
  integration-only and **not live**; the naive check then invites a wrong action — dispatching a
  doc-correction PR to match a "shipped" model, telling a stakeholder a feature is live, closing a
  deploy-readiness item. So **name which ref governs "shipped"** first (where deploy promotes from, not where
  the newest work lands), then test **containment against that ref** with the §3 toolkit pointed at it, not at
  your current branch: `git merge-base --is-ancestor <landed-sha> origin/<governing-ref>` proves containment
  **only while the SHA is preserved** (a normal / fast-forward merge). Under a **squash / rebase /
  cherry-pick** the original SHA is not an ancestor though the content shipped — the §3 squash-merge
  false-negative, the mirror trap — so corroborate the way §3 does but **against the governing ref**: grep
  **its tree** for the landed symbol (`git grep <symbol> origin/<governing-ref>`,
  `git show origin/<governing-ref>:<path>`), `git cherry`, or the forge record of the PR that merged **into
  that ref**. "Merged" with no target named is the ambiguity: **merged-to-integration** (done,
  integration-first) and **promoted-to-release** (shipped) are different milestones — scope every status claim
  to the one you verified. Distinct from the stale-base silent-revert above (*would merging undo shipped work*
  — needs the base's post-fork side); this is *did the work reach the governing line* — needs containment
  against that ref. The same branch-blindness defeats the "is this finding already fixed?" reproduce check in
  `method.md` (its `git log -S` run on the wrong checkout clears a defect still live on the deploy line), and
  it's the verification the "a merged PR is a **proxy**, not the outcome" rule (`report-format.md`) leaves
  unspecified. Treat a governing branch thousands of commits behind its integration branch, with a conflicting
  / stale reconcile PR, as a **release-readiness blocker in its own right**: surface it early — when the
  frontier is genuinely exhausted the honest state is "gated on the promotion / owner," not more
  integration-only work that widens the gap.
- **Before closing a PR as duplicate or superseded, diff the two tips — title or branch similarity is not
  patch equality.** Two PRs that look like the same fix can differ in a hunk only one carries (one tip gates a
  `useReducedMotion` check behind a mount guard — `mounted ? … : false` — the other reads it directly);
  closing the "duplicate" drops that hunk silently. Compare the heads first: **two-dot**
  `git diff <tip-A> <tip-B>` when they share a base (the literal difference between the two trees — empty iff
  the tips are identical), or `git range-diff <base>..<tip-A> <base>..<tip-B>` to compare the two **patch
  series** when the PRs forked from different points, which a plain two-dot pollutes with mainline drift. (Not
  three-dot `A...B` — that diffs from the merge-base, the `git log` commit-range idiom, so it can't tell you
  what B has that A lacks.) If B carries hunks A doesn't, **fold them into A** (rebase or cherry-pick) and
  *then* close B with a pointer; close-as-duplicate is safe only when that diff is empty or B ⊆ A with no
  unique lines. Put the **diff result in the close comment** as evidence; "looks the same," a shared branch
  name, or a shared issue number is never sufficient alone.
- **Never rewrite shared history.** Rebase/force-push only branches that are personal and undepended-on. When
  a force is genuinely needed, it's **`git push --force-with-lease`** (refuses if the remote moved under you),
  never `--force`. A rebase of a shared branch is a merge instead.
- **Deleting a branch does not scrub its objects.** A branch that ever carried a **secret or PII** isn't
  remediated by deleting it — the objects remain reachable on the remote until GC/forge cleanup, and clones
  already have them. The remediation is **credential rotation** (and history purge / forge support), not
  `git push --delete`. Flag this as its own line, never "delete fixes it."
- **Remote deletes and history rewrites are confirmed, explicit, one at a time** — no batch `--delete` of a
  list the user hasn't seen and approved.
- **Gate an irreversible command on the verdict string, not just "ran" — and make sure a list-membership guard
  actually checks the list.** Two related failure shapes, both "the guard didn't guard because the shell's
  real semantics differ from the author's mental model":
  - A preflight/safety script's *contract* is often to print a pass/fail verdict while still exiting 0 (so a
    human watching sees the message) — or its exit code is checked but the next command runs unconditionally
    regardless. `./preflight.sh; ./publish.sh` (a bare `;`, or two unconditional steps) fires the irreversible
    command whether or not the gate passed. Before recommending or running a merge/delete/publish/deploy
    command, confirm the preceding gate's **documented pass condition** (an exact string and/or exit code
    checked with `&&`/`if`), not merely that it ran without erroring.
  - A **safety-critical exclusion list** (a held/blocked/do-not-merge set) is commonly checked with
    `for x in $LIST; do [ "$x" = "$item" ] && skip; done` — this silently breaks under any shell where an
    unquoted `$LIST` doesn't word-split (zsh, by default, doesn't; `for x in $LIST` then iterates **once**
    with `x` bound to the whole string, so the comparison almost never matches and the exclusion never fires).
    A script meant to run in "the reviewer's shell" can't assume bash's word-splitting semantics. Use a
    **literal `case`/explicit split** instead — `case "$item" in id1|id2|id3) skip ;; esac`, or a line-based
    exact match (`printf '%s\n' "$LIST" | grep -qxF "$item"`) — for any exclusion check gating an irreversible
    or shared-state action (a held-PR exclusion in a merge script is the canonical instance: a silently-broken
    guard here doesn't fail loud, it just merges the thing supposed to be excluded). Detector: grep scripts/CI
    config for a for-loop iterating an unquoted variable immediately followed by a merge/delete/publish/deploy
    call, and confirm the loop actually iterates more than once against a multi-item fixture in the shells the
    script claims to support.
- **Automated conflict resolution is gated on a marker-grep, not on `git add` exiting 0.** `git add` stages
  whatever is on disk — conflict markers and all — so a resolution step whose
  `git checkout --theirs -- <path>` silently failed can still be staged and committed with `<<<<<<<` /
  `=======` / `>>>>>>>` in the tree (caught, if at all, only by a later parse error). Two mechanical
  backstops, both required for agent/automated resolution where no human eyeballs the diff: **quote/escape
  every path with glob metacharacters** (`git checkout --theirs -- 'app/kpis/[key]/page.tsx'`, or disable
  globbing with the shell's own switch — `set -f` in bash/POSIX sh, but `setopt noglob` / a `noglob`
  precommand in **zsh**, where `set -f` is NO_RCS and leaves globbing on — since a `[param]` / `*` / `?` path
  glob-expands differently per shell, zsh erroring on a no-match while bash may pass the literal, so an
  unquoted resolution silently no-ops); and **grep the staged tree for conflict markers before every commit,
  gating on the result** —
  `git grep --cached -qE '^(<{7}|={7}|>{7})' && { echo 'unresolved markers'; exit 1; }` (exit 0 = a marker was
  found → block), or git's built-in `git diff --cached --check`. A bare `git diff -G` *prints* the hunk but
  **exits 0**, so it doesn't gate — and `add` success is never proof of resolution; the gating marker-grep
  plus a build/parse is.
- **Update a branch another worktree still holds with a detached-HEAD fast-forward, never a force-push.** When
  the branch you must update is already checked out in another (often stalled) worktree,
  `git worktree add <branch>` refuses and force-pushing to escape it **strands** that lane — discards commits
  the lane had already pushed (orphaned on the remote) and leaves its local ref and unpushed work on a
  now-diverged branch. The non-destructive primitive: `git worktree add --detach <dir> origin/<branch>`, do
  the work there (merge the base in, resolve, run gates), then push `HEAD:<branch>` — a **fast-forward** when
  the remote ref is an ancestor of your new HEAD (verify that first; if diverged, it needs a real merge, not a
  push). The "already checked out" collision is usually a symptom of stale worktrees never pruned —
  `git worktree prune` (and removing a merged lane's tree) clears it.

## 7 — Severity discipline (don't turn cleanup into noise)

Branch hygiene has the same noise failure mode as dependency currency (`dependency-currency-and-upgrades.md`
§3): forty stale branches become forty Lows that bury a real Critical. **Batch routine cleanup as ONE finding
carrying the triage table**; escalate a branch to its own finding only on consequence:

- **An unmerged security/bug fix sitting on a stale branch** (the fix exists but was never shipped) → **High**
  — the vulnerability is live *and* the fix is already written but unreleased.
- **A branch that is the only copy of real work** (never pushed) → **High** as a data-loss risk until it's
  pushed/tagged.
- **A large or long-lived change built on the *wrong* integration target** — not the one §2 detected (a case
  arising only where two long-lived branches exist, so there *is* an alternative target) → **High**, distinct
  from and **above** the Medium merge-debt row below: the cost compounds with every commit added on the wrong
  base, and unwinding it later is a forced retarget/rebase of work already built. Intrinsic severity stays
  High at every stage (guardrail 3, `SKILL.md`); stage calibrates only the **urgency** — block-now on a
  `growth`/`mature` line vs tracked on a `prototype` — never the severity. State the left⇥right commit counts
  measured and name the **retarget/rebase-before-more-work-lands** command in the finding.
- **A long-lived `develop`/`release/*` badly diverged from `main`** → Medium merge-debt (Fowler: integration
  frequency; the longer branches live apart, the worse the eventual merge).
- **A branch carrying committed secrets/PII** → severity per the exposure boundary (`security-appsec.md`);
  remediation is rotation, not deletion (§6).
- **Everything else** — merged-and-undeleted, stale WIP, gone-upstream local refs, behind-but-clean → **one
  batched Low/Info** with the triage table and a recommendation to enable "auto-delete branch on merge" so it
  stops recurring.

Never let the volume of routine branch cleanup outrank a real defect.

## 8 — Spike / prototype branches (a naming convention, not a new gate)

A deliberately fidelity-capped, disposable-by-construction exploration (Shape Up's
breadboard/fat-marker-sketch idea, applied to code instead of design) is cheap to discard *if marked as one
before it's built*. This rides the branch-pattern logic this domain already owns — not a new file, not a new
gate:

- **Gate:** a branch matching a spike/prototype naming convention (`spike/*`, `prototype/*`, or the project's
  own documented equivalent) declares its timebox and throwaway status (in the branch's first commit message
  or a linked issue), and never merges to the target **as-is** — it's rewritten to production quality or
  explicitly "graduated" (renamed/re-based onto a normal feature branch) first. **Trigger:** branch-name
  pattern match only, at merge time — never fires on an ordinary feature branch. **Owning hat:** Release &
  docs (this domain already owns branch triage).
- **Planted-defect test:** a `spike/foo` branch merged directly to the target with no rewrite and no
  graduation marker → the gate flags it.

## Triage table (the deliverable — emitted in the report)

```
| Branch | Last commit | State | Unique commits | Open PR | Recommendation | Command |
|--------|-------------|-------|----------------|---------|----------------|---------|
| feature/x | 3 days ago | unmerged, ready | 4 | none | Open PR → develop | gh pr create -B develop -H feature/x |
| bugfix/y | 6 months ago | squash-merged (PR #42) | 0* | merged | Delete | git push origin --delete bugfix/y |
| spike/z  | 1 year ago  | stale WIP, only copy | 12 | none | Escalate to owner; push to preserve | git push -u origin spike/z |
```
`0*` = cherry shows commits but the forge confirms the PR merged (multi-commit squash). Mark any PR column
`unverified` when forge auth was absent (§1).

## 🚩 Red flags

- A `develop` branch unmerged to `main` for months (git-flow gone stale).
- Dozens of merged-but-undeleted branches and **no** "auto-delete on merge".
- Long-lived `feature/*` branches many commits behind the target (merge debt).
- An in-flight branch/PR whose **base is not the detected integration target** (e.g. based on `main` while
  features integrate into `develop`) — for a large or long-lived change, a **High** wrong-base defect (§7),
  not Medium merge-debt.
- A branch with an unmerged security fix — the patch exists but never shipped.
- A branch that only exists on one machine (no upstream) — one disk failure from lost work.
- Recommending "merge / open a PR" for a branch the forge already merged via squash (the §3 trap) — a
  fabricated, conflict-generating finding.
- `git push --force` (not `--force-with-lease`) anywhere near a shared branch.
- "Just delete the branch" offered as the fix for a leaked secret.
- A branch deleted with no check for a stacked PR using it as base.
- A generated/compiled-file merge conflict resolved by hand-splicing instead of regenerating from the merged
  source inputs.
- A runbook/script chaining a preflight and an irreversible command with a bare `;` (or two unconditional
  steps) instead of the preflight's documented pass condition.
- A safety-critical exclusion/allowlist check built on an unquoted `for x in $VAR` loop with no verification
  it actually iterates per-item in the shells the script claims to support.
- A `spike/*`/`prototype/*` branch merged to the target as-is, with no rewrite and no graduation marker.
- A merge-train batch landing a gate-adding PR before the PRs it would force to retrofit that gate.
- A new PR-body / commit-trailer / committed-artifact gate landed with **no update to its standing producers**
  (PR template, Dependabot/Renovate, release/agent bots) — every automated PR is refused (green on its real
  work, red on the new gate) until noticed (§5 covers only in-batch ordering).
- A union/integration branch merged or squashed in place of its member PRs, or already-green members held
  waiting on the union's aggregate CI.
- An `--admin`/force-merge used to escape a red base, instead of discharging it with a verified merge train.
- A `STOP` that leaves a green + `MERGEABLE` PR neither merged under standing approval nor handed off by URL,
  or an unpushed rebase abandoned off the remote.
- A PR merged after another that absorbed its files at an older SHA — a stale subset silently reverting the
  later fix, with no conflict to warn.
- A **long-open PR** approved on its "Files changed" / own-base diff (fork-point-relative, so blind to what
  the target shipped on those files since it branched) — or waved through on "rebase + re-run CI" — with no
  check of the target's post-branch commits on the paths it touches; a squash, a toward-the-branch resolution,
  or a semantically-coupled clean merge then drops that newer work with no conflict to catch it.
- An "X is shipped / live" or "already fixed" claim resting on a commit-grep, a "Files changed" diff, or a
  merged-PR status on the **current / integration branch**, with no containment check against the ref that
  governs deploy — on a repo where integration runs far ahead of the release line, much grep-visible / merged
  work is not live.
- A batch merged off one up-front green + `MERGEABLE` snapshot with **no per-merge re-check**, or a **merge
  sweep run concurrently with a conflict-resolution lane** against the same base — the moving base head flips
  later members back to `CONFLICTING` while their checks stay green.
- A merge on a **finished green that no longer matches the merge target** — a body/metadata edit, base
  retarget, or description amend the gate's trigger ignored, or a **rebuild whose fresh run is still in
  flight** — trusting the check's colour without reading the head / input digest it ran against.
- A PR closed as duplicate/superseded on title or branch similarity with no tip-diff evidence in the close
  comment.
- A local hook, a `Tests: N/N` line, or a checked PR-template box logged as a passing control (self-reported,
  `--no-verify`-bypassable) instead of a forge run pinned to the reviewed SHA.
- Under a worktree: an inherited absolute `core.hooksPath`, or a pre-push hook whose range is a hardcoded
  default branch instead of the pushed refs on stdin — gates run against the wrong tree or the wrong range.
- A programmatic conflict resolution that stages with a quoted `git add` **without** grepping the staged tree
  for `<<<<<<<` / `=======` / `>>>>>>>`, or an unescaped `[param]` / glob-metachar path in a `git checkout` /
  `add` (a no-match glob silently no-ops the resolution).
- A **force-push** used to update a branch checked out in another worktree (strands that lane's unpushed work
  on a diverged branch + discards its pushed commits) instead of a detached-HEAD fast-forward.

## Cross-references

- **`docs-and-dx.md` (section O)** — the branch-*protection* posture (required PR, reviews, checks, no
  force-push, CODEOWNERS). This file reads that posture to decide "PR vs direct merge"; it does not restate
  it.
- **`SKILL.md` Phase 0** — the open-branch / open-PR inventory that feeds this triage. **Phase 5** — where the
  triage table is emitted and where review fixes ride a branch + PR (security split off).
- **`security-appsec.md`** — a branch carrying secrets/PII is rated by the exposure boundary there; the §6
  rotation-not-deletion rule applies.
- **`SKILL.md` severity rubric** — `latent`/consequence-scaled ratings; §7 mirrors the dependency-currency
  severity discipline.
