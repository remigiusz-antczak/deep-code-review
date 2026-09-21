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

**Check the base of work *in flight*, not only the target of finished branches.**
Once the model names the integration target, enumerate in-flight work against it: open
PRs (`gh pr list --state open --limit 500 --json number,baseRefName,headRefName,changedFiles`
— pass a limit that exceeds the expected total and say which, per §1; the default 30
silently truncates) **and** pushed branches that have no PR yet (§3's `for-each-ref`
enumeration — the case where retargeting is still cheapest). Verify each one's **base**
against that target with the §3 divergence count
(`git rev-list --left-right --count <integration-target>...<branch>`). A large change
branched off the **wrong** base — e.g. off `main` while features integrate into
`develop`, which carries commits `main` lacks — is written against a product state
that no longer exists on the integration line; merging it later either conflicts with
or reverts those commits, and every lane built on that base inherits the problem. A
PR's own green checks say nothing about whether its **base** is the right one; that is
a §7 severity call, below.

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
   (§6). For a **long-open** branch this is necessary but not sufficient — rebasing
   and re-running CI does not prove the merge won't revert work the target landed
   since the branch forked; verify its effect against current HEAD first (§6,
   long-open-PR bullet).
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

**The union verifies the combination; it is not on the critical path.** Its CI
aggregates every member's checks, so it concludes no sooner than the slowest
member and usually later — treating "union CI still pending or red" as a reason to
hold members that are each already green re-serializes the very wait the train
exists to remove. Once the aggregate gate is green the proof is in hand: merge the
green members (step 3) and **close the union with a pointer to where they landed**.
"Wait for union CI, then squash/merge the union" fails twice over — the wait is
redundant and merging the union orphans its members' issues (step 3).

**Sequence a gate-adding PR last within the batch.** A PR that adds a new
required gate, merged first, forces every other PR in the batch to retrofit a
gate that didn't exist when it was authored — extra round-trips for no benefit.
When triaging several ready branches at once, check whether any changes
required-CI/gate configuration and put it at the back of the landing order.

### Mergeable is a snapshot against a moving base head — re-check before each merge; freeze the sweep while a resolver runs

"Green + mergeable" is a **snapshot against the current base head, not a durable
property**. Landing PR A can flip an overlapping PR B from MERGEABLE back to
CONFLICTING — A touched a file B also touches, so B now needs a rebase — while
**B's checks stay green** (they ran against the old base; only its mergeability
changed). This bites at two scales:

- **Snapshot-then-batch (the coordinator *reads* staleness).** A coordinator that
  snapshots "these five are green + mergeable" and merges them one by one finds
  PRs 2..5 increasingly CONFLICTING as earlier ones land — then stalls, or (worse)
  force-merges onto a base the PR was never tested against. **Re-check mergeability
  immediately before *each* merge, never once at the top of the batch** — mergeable
  has a shelf life of "until the next overlapping merge." **Group the batch by the
  file sets each PR touches: serial-with-rebase *within* a group, parallel only
  *across* disjoint groups.** Merging two PRs that share a hot file as if
  independent is the bug. (The merge-train union above surfaces these collisions up
  front and proves the *combination builds* — but it does **not** make a conflicting
  member mergeable: the union branch is thrown away and the member branches are left
  unchanged, so each member still resolves against the moving target and the
  per-merge re-check still applies at step 3. Sequence the resolver first, *then* run
  the train.)

- **Sweep-while-resolving (the coordinator *causes* the staleness).** Running a
  **merge sweep** (landing green PRs into a shared base) **concurrently with** a
  **resolver lane** (rebasing a conflict-prone set against that same base) makes
  the sweep the very thing re-dirtying the cluster it is trying to land: every
  merge moves the base head and invalidates the resolution the resolver just
  computed, so the PRs it was making mergeable flip back to conflicting — an
  unbounded treadmill where the broadest, hottest-file PRs never converge.
  **Freeze the *merge* step — not the build step — while a resolver is active
  against the base:** lanes keep taking PRs to green (no stall, no visible
  slowdown), green PRs **queue** instead of merging, the **hardest-to-rebase set
  lands first** against a now-stable base, then the queue drains back-to-back.
  Freezing the merge rather than pausing all work removes the invalidation without
  dropping throughput.

**A third state — `UNKNOWN` while the forge recomputes.** Distinct from the MERGEABLE↔CONFLICTING
flip above: **GitHub** computes mergeability **asynchronously** (not independently verified for other
forges), so right after any base-changing merge an overlapping PR's `mergeable` field is briefly
**`null` / `UNKNOWN`** while the recompute runs — that is *not-yet-known*, not CONFLICTING. A batch
merger that treats `UNKNOWN` as CONFLICTING skips a PR that is actually fine (landing only the
**first** of a back-to-back set); one that treats it as MERGEABLE merges blind. **Poll until it
settles** to a definite state (a bounded 2–4 tries with short backoff), retry **only `UNKNOWN`**, and
never auto-retry a definite `CONFLICTING` as if it were transient.

Both value-flip cases above are the **stale-base failure below at the mergeability layer** — a quantity
computed against one base head, consumed against another — except the moving head
breaks *mergeability* here, not a gate's diff. A fleet coordinator applies this
whenever it batches merges; `agentic-delivery`'s `fast-agentic-delivery.md`
cross-references here rather than restating it.

### A finished check's green can be stale off a prior evaluation — confirm it ran against the current head, and know each gate's trigger model

A green that already **finished** is not durable either — the reviewed object can change under it,
so the check you see may not have run against what you are about to **merge**. This is distinct from
the moving-base cases (the mergeability-snapshot above; the stale-base gate-diff below): here the
base need not move at all. Two ways a finished green goes stale:

- **Trigger coverage — the check never re-ran.** Most gates re-evaluate only on a **subset of
  events** (typically a new push / new head). A mutation **outside** that set — **editing the body
  or metadata**, **retargeting the base**, a bot **amending the description**, or a gate reading a
  **cached artifact / body** captured at an earlier run — never fires the check, so its last verdict
  certifies the **pre-mutation** state.
- **Timing — the check will re-run but has not yet.** A mutation that **does** fire the trigger — a
  **rebuild / rebase** that pushes a new head — has a run **still in flight**, so the green you
  currently see belongs to the **pre-rebuild** head. Merging now lands an **intermediate** state the
  gate never certified for the final head: wait for the fresh run to conclude, and do not merge a
  change another lane is still rebuilding.

Either way the green is real; it just certifies a state that no longer exists. So before merging,
**confirm the green reflects the current head / inputs**: read the **SHA (or input digest)** the
passing check actually ran against and compare it to what you are about to merge (the
pin-the-verdict-to-the-exact-SHA discipline, `method.md`). And **know each gate's trigger model** —
which events re-evaluate it and which do not — so a mutation the triggers **do not cover**, or a run
**still in flight**, is recognized as **invalidating**, not trusted. These are the verdict-staleness
siblings of the moving-base cases: there the *base* moved under a still-valid check; here the
*reviewed object* changed — via an event the check never saw, or one whose run has not concluded.
(Distinct, too, from a required check that simply never ran for this PR — the config-gap blocker
below.)

- **🚩** merging on a green produced **before** a body/metadata edit, a base retarget, or a rebuild
  the gate's triggers ignore; a "these are green" batch snapshot consumed after any such mutation;
  trusting a check's **colour** without reading the head / input digest it actually ran against.

### Red base: discharge the deadlock with a train, never an override

When the target branch itself is red, a merge preflight that requires the base
green refuses the very fix PRs that would green it — a **deadlock**, not a per-PR
failure. Agents stall, invent one-off exceptions, or serial-wait forever. The
escape is the merge train above, used deliberately as the *discharge* vehicle:

1. **Discharge (preferred).** Union the individually-green fix members, run the
   aggregate gate once, and on green merge them back-to-back (the merge-train
   procedure above). The union's green **is** the proof the preflight's "base green
   at head between merges" wait
   was asking for, so it **discharges** that wait — which the red base cannot
   otherwise satisfy.
2. **Serial fallback.** Wait for the base to rebuild between merges only when a
   true dependency stack cannot share one union.
3. **What the union green does *not* license.** Not merging a **red** member, not
   an `--admin` / force-merge past the gate, not an undocumented "just merge
   anyway." A red member is still red; only the *base-green-between-merges* wait is
   discharged, because the union already proved the combined tree.

Name this the **red-base discharge** and put one of the two vehicles on the
record; an oral-only exception ("we just merged past it that once") is itself the
finding. A red base is the release pipeline's blocked state, so
`release-engineering.md` cross-links here — but the discharge *mechanism* is the
merge train, so it lives here and that file never restates it.

### A union / merge-train gate that HANGS or is BROKEN in-env (not fails) silently stalls the pipeline

A train's aggregate gate can **hang** — a wedged runner, a deadlocked build, a lost webhook —
rather than fail, and a coordinator waiting on it stops merging everything queued behind it, with
no red status to react to. **Detect it by liveness, not elapsed time alone.** During the gate
**run** the base head is stationary *by design* (nothing lands until the gate concludes), so the
live signal is the **gate job's own output** — no new log output past ~2× its normal window is a
hang (the *long `in_progress` shard* rule below, applied to the conductor); cancel and root-cause,
don't passively wait. During the merge **drain** (members landing back-to-back), a **base head that
stops advancing** past ~2× the per-member cadence is the hang signal there. Emit progress (members
landed / remaining) so a stall is visible instead of reading as healthy idle.

A hung heavy gate is a **can't-check (`UNVERIFIED`), not a pass** — it never authorizes the merge.
But don't block the queue forever: **timebox** it and fall back to the **deterministic runnable
subset** (lint / unit / type-check) as a **proof-of-record** for what *can* be checked, escalating
the heavy gate's absence — that subset is a degraded record, **not** the union's combined-build
proof, so it does not license merging a member the union never validated. And keep flaky / heavy
browser / visual gates in **per-change pre-merge checks**, not as a blocking term of the batch
union, so one wedged heavy gate cannot stall the whole train.

A heavy gate **broken in this environment** — its own harness crashes, a dependency it needs is down —
is the **crash cousin** of the hang above, and it is likewise a **can't-check, not a red**: "could not
check" is not "found a problem" (the gate discipline in `product-ux-quality.md`). It must **fail-open
for the batch proof** — drop that one broken term and run the deterministic runnable subset — so
batching **continues** rather than collapsing the whole train to serial merging; one broken tool must
not halt all batching. The hang and the crash differ in the **response** and in **what evidence
survives**: a hang is **timeboxed then escalated** (validity genuinely unknown, the gate may still be
running) and leaves *no* completed union run; a crash is **definitively broken here and safe to route
around now** and leaves the run's **other** terms genuinely complete. Both keep the flaky / heavy gate
out of the blocking union term, and both hold the **same floor at the grain each leaves intact**: a
hang validated nobody, so nobody merges on the reduced record (the floor above); a crash validated
everyone *except* a member whose essential check **was** the crashed term, so only those members are
held back. Fail-open means the tool's *own crash* is not a red — **never** that an unvalidated member
merges. **Treat a
throughput-gating tool as P0:** a broken gate that fails one PR is a normal bug, but one sitting in the
batch-proof path throttles *every* merge — its blast radius is the whole delivery rate, so it jumps
the queue ahead of a gate that only affects the correctness of a single change.

### A required check must be *satisfiable* — pending forever blocks merge like a red

A branch-protection **required check** gates merges only if some job actually
reports a conclusion for *this* PR. When the required *name* is not backed by a job
that runs and concludes here, the check sits **pending forever** — indistinguishable
from a hang, and merge-blocked exactly as a failure is (its enforcing surface never
saw this PR — `SKILL.md` principle 2). Two ways it happens:

- **A required check with *no status* blocks merge — but distinguish "never ran"
  from "ran and reported skipped."** When `on: pull_request: paths:` filters a whole
  **workflow** out for an out-of-scope PR (only `units/**` changed, so the required
  `app-browser` workflow never triggers), the check gets **no run at all**; the
  enforcer reads "no status" as not-green and the PR is unmergeable without an
  override. Fix: give the required workflow a **pass-through job** that always
  triggers and exits 0 on out-of-scope paths (so it reports a conclusive Success),
  or don't name a legitimately-absent workflow in the required list. **Contrast** a
  **job** skipped by a job-level `if:` inside a workflow that *did* run — the forge
  reports it **skipped/Success**, which satisfies the required check and needs no
  pass-through. The trap is the **missing status**, not the skip itself. But the
  pass-through **cuts both ways**: it is legitimate only when **nothing was in scope**
  (a path filter genuinely excluded this diff). It is a **false-green hole** when there
  **is** something to check and the *event* — not the paths — routed around the real
  checker: a required workflow whose real job runs on `push` / `synchronize` but whose
  pass-through also fires on an `edited` (title/body) event reports a conclusive
  **Success** for a PR whose code the checker never re-ran. Make the pass-through
  reachable **only** on the paths/events where the real check is genuinely N/A — never
  an unconditional `exit 0` that green-lights an event the real job ignores. A
  **locally-added merge preflight** can invert this: when the forge itself reports a job
  **skipped/Success** — a job-level cost-gate `if:` an agent cannot flip without an
  owner-only label or a manual dispatch — a preflight that **refuses** that green verdict
  is *stricter than the required check it stands in for* and **deadlocks** anyone without
  the owner lever (the gate-vs-standard rule — a gate must never be stricter than the
  standard it enforces, `product-ux-quality.md` / `frontend-a11y.md` — applied to CI).
  Such a preflight must **diagnose why** a check is absent — *policy-declined* (cost gate:
  work exists, a human must grant the run) vs *nothing-to-run* (path filter: no in-scope
  change) — and **name the owner action**, not refuse blindly; conflating the two reports
  a false block and pushes the agent toward the very label it is barred from adding.
- **Trigger-event gap.** A required job whose workflow omits the event that fires
  the PR never starts *for this PR*: a `full-ci` job with no `labeled` trigger, in a
  label-driven flow, never begins; a `workflow_dispatch` run carries its own
  `run_id` and never attaches to the PR's check rollup, so the preflight never sees
  it. The workflow **existing** is not the check **running** — verify the required
  name maps to a job whose triggers include how this PR is actually checked.
- **A required check that never runs on a PR — read the `on:` block FIRST, and name the right
  trigger key.** A PR's required check reports on the **PR head**, so the run that satisfies it
  is a **`pull_request`-triggered** run — filtered by **`on.pull_request.branches`, which
  matches the PR's *base* (target) branch**. So when PRs *targeting* a long-lived integration
  branch show the check as **no-run / Pending** (the #262 *no-status* case that blocks merge —
  not the *skipped/Success* case that satisfies it), the load-bearing key is the `pull_request`
  **base** filter: is the target branch in `on.pull_request.branches`? Absent = **structural**
  (the check can never report on those PRs), not a flake. A **distinct** concern in the same
  `on:` block: `on.push.branches` must list the integration branch to stamp *its own HEAD*
  green via a push run **after merge** — that HEAD-provability point does **not** unblock the
  open PRs. Diagnose in order: (1) target branch in `on.pull_request.branches`? — this is what
  unblocks the PRs; (2) a job-level cost-gate `if:` (label/dispatch, above); (3) a path filter
  (diff out of scope — OK); (4) *only then* rerun / flake / timeout — and separately, is the
  branch in `on.push.branches` so its HEAD is provable? Reading the `on:` block beats N
  PR-level reruns chasing the wrong key.
- **Stale-base fails the whole queue at once.** A gate that diffs the PR head against
  **`origin/main`** (not the PR *base*) turns one additive commit on `main` — a new row,
  fixture, or schema entry the integration branch hasn't pulled — into a simultaneous failure
  of **every** PR queued against that branch, with no regression in any of them. When N PRs
  fail the *same* gate at once, check `git log HEAD..origin/main --oneline` for a stale base
  **before** triaging them individually; one `git merge origin/main` on the integration branch
  clears them all. Sync the integration branch on **each** additive `main` merge, not only
  before the final train; and a new gate that baselines on `origin/main` must **document that
  assumption** (prefer the PR base for a long-lived-branch workflow).
- **A change-detection gate's hardcoded base is the scope-selection sibling of stale-base —
  loud when the branch outruns the stale ref, silently skipped when that ref won't resolve.** The bug above corrupts a gate's *verdict*; the same mistake in
  a **change-detection** step — a path filter / "did `app/` change?" / "did any migration
  touch?" check deciding whether a downstream job **runs at all** — corrupts its *scope decision*
  instead. Anti-pattern: a diff pinned to a **hardcoded release-branch constant**
  (`git diff origin/release-v2...HEAD -- app/`) instead of the branch's actual base — its
  configured upstream `@{u}`, the PR's declared target (`github.event.pull_request.base.ref` in
  CI), or a computed merge-base (`git diff "$(git merge-base <base> HEAD)" HEAD`, i.e. `<base>...HEAD`) (the pinned *ref* is the defect; merge-base diff
  semantics are the right choice for a scope check, not the problem). A hardcoded constant fails
  **two** ways. **Loud:** once the branch runs **ahead** of the stale cut, the diff span balloons
  to the branch's whole history since the cut, so the filter reports every gated path touched on
  **every** push (a "changed" verdict that no longer reflects this push — noise and wasted CI, not
  a correctness bug by itself). **Silent (the dangerous one):** a literal ref is a **resolvability**
  hazard the computed forms mostly avoid — in a shallow / partial CI checkout (`fetch-depth: 1`,
  `origin/release-v2` never fetched) `git diff origin/release-v2...HEAD` **errors**
  (`fatal: bad revision`), and a naive `… | grep -q '^db/migrations/'` reads the empty/failed
  output as **no match**, so the job **skips** a real change with nothing turning red. (The
  positional "branch is *behind* the ref" case does **not** empty the diff — three-dot / merge-base
  semantics correctly report the branch's downstream commits; the silent skip comes from the ref
  failing to *resolve*, not from the branch's position.) Fix: derive the base at run time (never a
  literal branch/tag name), **ensure that base ref is actually present in the checkout** (fetch it /
  adequate depth), **fail closed** — a change-detection diff that errors or can't resolve its base
  must run the job (or fail the run), never silently skip — and **have the gate name the base it
  diffed against** (and whether the diff resolved) in its output, so a bare true/false can't hide a
  wrong-base or unresolved-ref result behind a correct-looking "nothing in scope." Distinct from the PR-*targeting* wrong-base
  rule (below — which branch a PR opens/merges against) and a pre-push hook's hardcoded range
  (below — fixed via stdin-derived pushed refs, since a hook has no upstream to read); three
  mechanisms, one root cause: a constant standing in for a computed base.
- **A long `in_progress` shard is diagnosed by its log, not by waiting or re-running.** Past
  ~2× a shard's normal duration, **read that shard's log before acting**: a **hang** (no new
  output for minutes — a deadlocked browser, a port that never opened) is cancelled and
  root-caused before any rerun; a **timeout** (the log shows a test hitting its limit) is left
  to fail cleanly, then the specific test is triaged. Rerun **at most once, only after**
  diagnosis — a rerun with no known cause is spend with no expected change, and parallel reruns
  (*rerun-storm*) multiply runner cost for zero new signal; treating an hour-long `in_progress`
  as normal (*passive wait*) is the mirror error. Cancel with a note naming the evidence (last
  log line, elapsed time) so the next reader knows it was a hang, not a flake or a stale push.

- **The branch-protection required-check *name* list and the workflow’s job names are two
  enumerations that drift.** Distinct from the trigger-config case above (a check that never
  fires for a PR): here a job is **renamed or retired** in the workflow while branch protection
  still *requires* the **old** status-check name — the old name now has no producer, reports no
  status forever, and blocks **every** PR (and the mirror: a check dropped from the workflow but
  left required). It reads as "a required check never ran," but the cause is a stale hardcoded
  name, not a trigger gap. Keep the two sets **in sync**: derive the required-check list from the
  workflow definition, or add a test asserting `{required-check names} ⊆ {job names the workflow
  can emit}` so a rename fails CI **loudly** instead of silently wedging the queue (the **Lockstep
  surfaces** discipline, `domain-checklists.md` — file sets that must change together). A retired
  check name often has **more than one consumer** — branch protection, a local merge-preflight
  script, a merge-queue config — so when a gate moves or is renamed, audit **every** consumer,
  not just the one that surfaced the block.

Read the check's **conclusion**, never the bare colour; a required check with no run
for this PR is a **High** merge-blocker in its own right — name it a config gap (the
check is unsatisfiable as wired), not a flake to wait out.

### A new PR-body / artifact gate is a contract with its producers — co-evolve them, or every automated PR silently fails it

Adding a gate that requires a convention in the PR **body** or a committed
**artifact** — a `Verify:` line, a changelog fragment, an evidence image, a commit
trailer — silently fails **every producer that does not yet emit it**. Sequencing
the gate last in one landing batch (§5, *merge trains*) handles the PRs already
*in flight*; it does nothing for **standing** producers — the PR template,
Dependabot / Renovate, a release-drafter bot, an agent delivery swarm — which keep
emitting the old shape on **every future run** until their **definition** is
updated. A human author adapts on their next PR; automation cannot, and piles up
green-but-refused PRs until someone notices.

- **Co-evolve the gate and its producers in one change.** Landing a body / artifact
  gate means updating the PR template, the bot/agent prompts, and any PR-generating
  scaffolding **together** — the gate and every client of its contract move as one
  commit.
- **Grandfather or ramp.** A warn-only period — or a *future* cutover date *T* — buys
  time while the producers catch up. A past-dated grandfather exempts only the in-flight
  backlog: a standing producer's next run is always after *T*, so it strands anyway.
- **Make the failure name the exact fix** — the literal line or field to add — so
  any producer, human or agent, can self-correct from the failure text alone.
- **Inventory the producers before adding the gate.** The template, Dependabot /
  Renovate, release bots, and agent swarms are each a **client** of the new
  convention; the one you do not list is the one that strands.

A gate is a contract with its producers: change the contract without moving the
producers and you break them silently — and an **automated** producer cannot "just
adapt" the way a human reviewer does. **In review**, a diff that adds or tightens a
PR-body / commit-trailer / committed-artifact requirement is incomplete unless the
same change updates that artifact's producers (or ramps the gate) — the
standing-producer generalization of the merge-train ordering rule (§5). The
message-payload sibling — a new **required field** breaking old producers and
in-flight messages — is `api-contracts.md`.

### The merge gate verifies WHERE a PR merges, not only that it is green — check the base branch

A PR-open command run without an explicit base falls back to whatever the tool picks — for `gh pr create`, a per-branch `gh-merge-base` git config if one was set, otherwise the **repo default branch** (the common case for a lane that never configured that). When the
intended integration branch is *not* the default (work lands on `development`, but `main` is the
protected / owner-gated default), a lane whose brief says "base `development`" in prose but runs
`gh pr create` / the API call **without the base flag** silently opens against the protected
branch — and a merge step that verifies checks-green + mergeable but **not the base** then merges
it into the protected branch, a governance breach even when the code is green.

- **Every PR-open passes the base explicitly** (`--base <integration-branch>`); never rely on the
  command's default-to-repo-default behavior.
- **Base-branch identity is a merge-eligibility axis**, next to state / mergeable / checks-green:
  the gate reads the PR's *actual* base and **refuses** anything whose base is not the expected
  integration branch — a green PR against the wrong branch is not mergeable.
- **Recovery when a PR already merged to the protected branch**: do **not** auto-revert the
  protected branch (that is itself a gated, owner-level change) — surface it for an owner decision,
  and separately port the change onto the integration branch so the two do not diverge.

### Self-reported evidence is not a trusted control; a local hook is advisory

A merge decision rests on **trusted** evidence — a run the forge verified on the **exact commit
under review** (a required check must actually report a conclusion for this PR, above; that
conclusion names the SHA it graded, `method.md`). Anything an author can produce or skip locally
is **advisory**, never a passing control:

- **Self-report ≠ control.** A local hook (pre-commit / pre-push), a `Tests: N/N` line in a
  commit or PR body, and a checked PR-template box are all self-reported: `git commit` / `git
  push --no-verify` bypasses the hook with no trace in the result, and the text is typed, not
  executed. "The repo has hooks" or "the PR says tests pass" is **never** logged as a green
  control — record only a forge run pinned to the reviewed SHA (a required status that never ran
  is the merge-blocker above, not "the author ran it locally").
- **A *drifted local copy* of a CI gate is a false green even when the author ran it in good
  faith.** The rule above covers a local check *skipped or bypassed*; the subtler case is one
  that **ran and passed and still means nothing** — the same gate lives as both a CI job and a
  local convenience copy (a `pre-push` script, a `make verify` / `scripts/check.sh` target, a
  vendored paste of the CI logic), and the local copy **drifts behind** the CI definition. It
  reports green on a change CI will reject; the author reasonably says "it passed locally" and
  reads the red CI as a flake — grounds for an `--admin` override that then merges what CI would
  have caught. Fix: **single-source the gate logic** — the local entry point **invokes the exact
  script the CI job runs** (one file, two callers), or a version/digest check **refuses to pass
  locally when the two diverge** — so a local pass can never mean *less* than a CI pass. This is
  the gate-logic case of *audit every consumer when a gate moves* above (a local merge-preflight
  is one such consumer) and of domain H's duplicate-source-drift (one source, not two copies that
  fall out of step); the trusted control stays the forge run pinned to the reviewed SHA. (The
  sibling **design** question — an evidence gate must require a source that *renders for the
  reviewer*, an uploaded attachment, not a raw-content-host link that only *looks* like evidence —
  is `product-ux-quality.md`'s "gate on visibility, not presence.")
- **The *absence* of a hold marker is not authorization — a mutable-text hold can be edited away.**
  The mirror of the rule above: where a merge is blocked by a "DO NOT MERGE" / hold marker in a
  **mutable** surface (a PR-body line, a checklist box, a label a bot can toggle), its
  **disappearance** is self-reported too — anyone, or an automated body-edit, can clear it with no
  approving review and no trace. A preflight that reads "no hold marker present → clear to merge"
  is fooled by deletion-by-edit. Back a hold **out of band** (a branch-protection rule, a required
  review, a status check the author cannot toggle), never mutable body text alone; make
  body-editing automation **append/insert-only** with a before/after diff; and treat a hold-marker
  *disappearance with no corresponding approving review* as **STILL HELD** (fail closed).
- **Hooks under a worktree gate the wrong thing.** In a linked worktree (the multi-lane setup
  this file's red flags cover), a hook wired for the primary checkout misfires: an **absolute
  `core.hooksPath`** is shared by every worktree, so a hook authored for the primary checkout
  also fires in every sibling — and one that resolves paths from a hardcoded location rather than
  the invocation then examines the wrong tree; and a pre-push hook that diffs a **hardcoded
  default branch** gates the wrong range. A
  pre-push hook's real range is the pushed refs it receives on **stdin** (`<local-ref>
  <local-sha> <remote-ref> <remote-sha>`) — derive scope from the event, not a constant, and
  don't bake an absolute hooks path a sibling worktree will inherit. A hook that silently gates
  the wrong files is worse than none: it reports green over unexamined changes — another reason
  the hook tier is advisory and the forge run is the trusted gate.
- **A git-tracked file the build regenerates poisons a clean-tree gate run in the same working tree.** If a build step
  rewrites a **committed, tracked** file (a generated bundle, a `dist/` artifact, a lockfile a
  postinstall touches), any gate that asserts a clean working tree — a merge preflight, a
  pre-commit/pre-push hook, `git diff --exit-code` in CI — goes **red on a dirty tree the build
  itself created**, not on a real defect, so running the build to satisfy one gate breaks the
  next. Fix at the source: **don't track a build output** (gitignore it, generate at build
  time), or if it must be tracked, regenerate deterministically and commit it as its own step,
  and scope the clean-tree check to **exclude the generated path**, or run the clean-tree check in a
  **fresh checkout the build never ran in** (the merge-train's throwaway integration branch, above, does
  exactly this) — never "run the build, then assert the tree is clean" in the same working tree.
  (Distinct from the run-twice idempotency check, which is about an *untracked* generated artifact
  polluting a later step across runs; this is a *git-tracked* artifact whose committed baseline the
  build invalidates on every run.)

### A worktree-relative hook runs its base's copy — land the safe hook everywhere first

Resolving hooks relative to the invoking worktree (the fix above) has a
second-order failure: each worktree then runs the hook **as checked out at its own
base**. A worktree cut from an old commit or a long-lived feature base runs *that
base's* hook — not the one the team now intends — so if an older hook is slow,
prompts interactively, or hangs on a step the environment no longer satisfies,
every lane off that base inherits the breakage, misattributes it to "flaky / slow
tooling," and starts bypassing the whole tier (worse than no tier — everyone still
believes it runs).
- **Hook content is fail-safe by default.** The committed hook runs a fast,
  always-safe core and makes every slow, environment-dependent, or interactive
  step **opt-in** (an env flag or a marker file), so an old copy can never hang or
  block a push on a step the environment cannot satisfy. A hook that can hang is a
  hook that will be bypassed.
- **Order matters: land the safe hook on every base people branch from *before*
  normalizing the path.** Because a worktree-relative hook runs the base's copy,
  the fail-safe hook must already be merged into the default branch *and* every
  long-lived integration / feature base first; normalizing resolution while old
  bases still carry the old hook guarantees stale-hook execution.
- **"Which hook runs here" is base-dependent — verify it.** Confirm the worktree's
  hook matches the intended version; make hook installation idempotently re-assert
  the current version rather than trusting inheritance.
- **A push-blocking step needs an audited, reason-required escape hatch**, so a
  genuinely stuck lane is never forced into a traceless whole-tier bypass (which
  disables *every* step, not the one bad step).

### On a stacked PR, attribute a CI failure to the commit that owns it

A PR stacked on another (B's base is A's branch, not the mainline) contains A's
commits, so B's own CI runs them too — and a failure A introduced turns B red
without B changing anything. Before diagnosing (or "fixing") a red on a stacked PR,
find which commit the failing step belongs to: `git log <merge-base>..<head>` is the
PR's **own** diff, and a failing step in an **ancestor** commit from the base branch
is the **base PR's** defect, not this one's. (Knowing which *run* the red is even
for is the companion rule — a run's conclusion names the SHA it graded, `method.md`.)
Attribute it to the base PR and let it fix there; **never commit the fix onto the
downstream PR** — once the base merges the same fix lands twice, a double-patch or a
conflict. A stacked PR is only truly green once its base has merged and it has been
re-run on the mainline.

### A stop halts new work — a MERGEABLE PR and an unpushed rebase are not "new work"

`STOP` / interrupt means **no new lanes, no new commits, no new scope**. It does
**not** pause landing a PR that is already green and `MERGEABLE` against its
intended base, and it does not license leaving committed work stranded off the
remote. Two things must be true before a stop is actually complete:

- **The MERGEABLE set is not silently abandoned — but a stop grants no new merge
  approval.** Enumerate the open PRs that are green + `MERGEABLE`; finished work must
  not vanish because a stop arrived. Merging is a shared-state action, so §6's gate
  still holds: **merge only what already had standing approval** (per its preflight —
  the red-base discharge above governs *how* such a merge lands, not *whether* you may
  fire it), and for everything else the stop-complete step is to **hand it off by
  URL** to the next owner. A green PR left un-merged and handed off is not the loss;
  an irreversible merge fired *because* a stop arrived — approval a stop cannot itself
  grant — is the §6 regression.
- **No unpushed commit is left silent.** An interrupted rebase/amend often leaves
  the new SHA **local only**; a stop taken there can strand it forever (a later push
  flake then loses it). Push before stopping, or print the recovery triple in the
  stop message — the **absolute worktree path**, the **branch**, and
  `git rev-parse HEAD` — so another lane can retrieve the tree. "Push failed / a
  flake" is not a completed stop: retry the push or hand off the path.

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
- **Two PRs regenerating the same artifact can both be valid with *no* conflict — a
  silent regression, not a merge error.** The rule above fires on a conflict; the
  worse case fires on none. When two open PRs each rebuild a derived artifact
  (`out/`, a lockfile, a compiled index, `app/data/`) from a shared source tree,
  each writes a valid file from its **own** base, git merges both cleanly, and
  whichever lands second **silently drops the first's regeneration** — nothing marks
  it. Trigger to watch: this PR regenerates an artifact **and another open PR touches
  the same source** that produces it (`gh pr list --state open --limit 500` — the
  `--limit` matters, §1). Fix: the second PR **rebases onto the merged first and
  rebuilds** from the combined source (a superset fold), never layering its own
  partial build. Flag a generated-artifact PR as **superset-fold-required** while a
  sibling source PR is open.
- **A PR whose *only* conflict is a generated/compiled artifact re-conflicts on
  every same-class merge — a structural loop, not a normal rebase-able conflict.**
  When the sole conflicting path is a **derived file neither side hand-edited** (a
  lockfile, a bundled `dist/`, a checksums/manifest file, a generated schema or
  client) and many open PRs regenerate it from a shared source, "rebase and it's
  clean" is false **by construction**: each same-class PR that lands **rewrites that
  serialization**, so a branch you just rebased green re-conflicts before it can
  merge, and under steady merge volume it re-stales faster than any human/agent can
  rebase — an unwinnable loop that reads as a perpetually "almost-ready" PR while
  compute burns on re-rebasing. Distinct from the silent-drop case above, which
  fires on *no* conflict (last writer wins); this fires on a conflict that **never
  clears**. Distinct, too, from §5's sweep-while-resolving treadmill (a *coordinator*
  re-dirties a cluster with a concurrent merge sweep): this needs no coordinator —
  ambient merge cadence alone drives it. **After the second re-conflict whose only
  path is a generated artifact, stop rebasing** and change strategy: get the PR green
  + mergeable **once** and land it inside a window where no same-class PR merges
  (§5's freeze-the-merge-step / a single merge-seat holding the class's other merges
  for the brief handoff), always **taking trunk's copy and re-running the generator**
  rather than hand-splicing (the regenerate-from-merged-inputs rule above). **Durable
  fix — stop conflicting at all:** regenerate the artifact as a **post-merge / CI
  step** (or stop committing it and build it in CI), or serialize the class and
  regenerate it **last**, so same-class PRs never block each other on it. A local git
  merge driver looks like the durable fix but only mitigates *your* local merge — see
  the next bullet. **🚩** rising rebase attempts per merged PR whose only conflicting
  path is a generated file; treating a generated-only conflict as resolve-by-rebase.
- **A git merge driver resolves the artifact conflict only on a *local* merge/rebase
  — the forge's server-side merge never runs it, so the PR still shows CONFLICTING.**
  Registering a custom driver (`.gitattributes merge=<driver>` + a resolver script
  set up per-clone) so conflicts in the artifact auto-resolve (take either side +
  regenerate) fixes only a **local** `git merge`/`rebase` on a clone where the driver
  is registered. A merge driver is a **client-side** feature — registered per-clone
  in local git config, run only by git on a clone that has it — so a host that
  computes mergeability and merges on **its own servers** has no reason to run your
  repo's local resolver and treats the artifact as an ordinary conflict. On
  **GitHub** this is observable: the "Merge" button / merge API / auto-merge / merge
  queue and its mergeability computation **ignore custom `.gitattributes merge=`
  drivers** (the mechanism should generalize to other forges but is **not
  independently verified** here, per the async-mergeability note in §5) — so a PR
  whose only conflict is the driver-handled artifact still displays **CONFLICTING
  indefinitely**, the host merge
  button stays disabled, and auto-merge never fires, even though the conflict is
  trivially auto-resolvable on any driver-registered clone. Teams then waste effort
  "rebasing to fix it" through the host UI (which can't), conclude the driver is
  broken (it isn't), or build a second driver (redundant). **Don't read
  host-CONFLICTING on a driver-managed path as a real conflict** — confirm whether the
  *only* conflicting path is the driver-managed artifact. **Land it via a local
  merge/rebase on a driver-registered clone, then push the resolved head:** the local
  resolution leaves no conflict, so the push flips the host to MERGEABLE and the
  normal host merge then works; **document the mechanic next to the driver**
  ("resolve/land locally; the host won't run this driver"). The rule uniting both
  bullets: **a merge driver is a client-side convenience for your own merge; it never
  changes the PR's forge-visible state** — the only host-visible fix is a **pushed
  commit that carries no conflict** (regenerate-and-push, or don't commit the artifact
  and build it in CI, previous bullet). **🚩** a PR stuck at host-CONFLICTING whose
  only conflicting path is a driver-managed generated file.
- **A subset absorbed at a stale SHA can revert a later fix — no conflict, last
  writer wins.** Distinct from the superset-fold case above (which is a
  *derived* file rebuilt from source): here PR B **absorbed PR A's own source
  content** at an **older** tip, missing A's later commits (say a disabled-submit
  guard that A fixed in follow-ups). Merge A, then merge B, and B's stale copy of
  those files silently overwrites A's fix — git sees no conflict, so nothing warns.
  Before landing: if B's history carries a **subset of A at older SHAs** (same
  files, earlier commits), do not merge B as-is after A — merge the **fuller tip
  first** and rebase B onto it, replaying only B's unique commits, **or** fold A's
  missing commits into B and merge B once. After landing, **grep the live tree for
  the fixed symbol** (the guard, the hard limit); never trust "B included A."
- **A long-open PR is reviewed against its own fork point, so its diff cannot
  reveal a revert of work the base shipped after it branched.** Distinct from the
  subset-absorb case above (two open PRs, B holding a stale subset of A): here
  **one** PR sat open while the integration branch raced hundreds of commits ahead,
  and the trap is that the **review surface itself is merge-base-relative**. A PR's
  "Files changed" view is **typically** merge-base-relative — as is `git diff
  <base>...<branch>`, which `git-diff(1)` defines as `git diff $(git merge-base <base>
  <branch>) <branch>` — showing only what the branch changed *since it forked*. That
  looks correct because it **is** the intended change seen from the old fork point, and
  it is **blind by construction** to everything the base landed on those same files
  afterward. So green + mergeable + a clean Files-changed is a **false all-clear**:
  where the branch edited a file the base has since advanced (a landed fix, a
  hardening), merging can drop that newer work. A plain three-way merge would at least
  **conflict loudly** where both sides edited the same lines — but the silent paths
  don't: a **squash-merge** lands the branch's tree for the files it changed (the
  base's newer content in them goes with it — the §5 squash trade-off / §3 cherry
  trap), an automated resolution **toward the branch** (`--theirs`, the §6 hazard
  below) takes the stale side outright, and even a **textually clean** merge can defeat
  the fix **semantically** when the branch edited a different region (a caller) than
  the base hardened (the callee). The branch's own green proves nothing either — it ran
  against its fork-point view of the world. **Two-dot `git diff <base>..<branch>` is the mirror trap:** it
  *over*-reports, flagging every file the base advanced but the branch never touched as
  a **phantom reversion** the real three-way merge would not produce — a lead to
  triage, never the verdict. Take the verdict against **current HEAD**: list the paths
  the PR touches (`git diff --name-only $(git merge-base <base> <branch>) <branch>`),
  ask whether the base landed commits on any of them since the fork
  (`git log $(git merge-base <base> <branch>)..<base> -- <those paths>` — non-empty
  means the PR's tree predates real work there), and prove the actual effect by
  **trial-merging onto current HEAD** — the throwaway integration branch of §5, cut off
  HEAD — and diffing that result against HEAD. **Notation follows the question:**
  merge-base-relative (three-dot) is right for *what did this branch write* and
  correctly suppresses the two-dot phantom reversions (the duplicate-close bullet below
  picks notation the same way), but it **cannot** answer *would merging undo shipped
  work* — that needs the base's post-fork side, which three-dot excludes. **"Rebase and
  re-run CI" is necessary, not sufficient:** a rebase can silently keep the stale side
  of exactly those files. If the PR's intent already landed on the base (its linked
  issues closed elsewhere), it is **verify-then-close**, not merge; closing someone
  else's PR is an owner call (§6 opening) — surface the touched-path-vs-HEAD evidence,
  don't act unilaterally.
- **"Is X shipped / live / already fixed?" is a *containment* question against the ref
  that governs "shipped" — a commit-grep on whatever checkout you have out, or a "the PR
  is merged" status, answers a different one.** A `git log --grep` / `-S` hit, a green
  "Files changed", or a merged-PR record only proves the change exists on **some** ref —
  the branch currently checked out, or the integration branch a PR merged **into**. Where
  a long-lived integration / `development` branch runs far ahead of the line that actually
  governs "shipped" (the release branch, the ref deploy promotes from — often **not** the
  integration tip, and never a **stale local checkout** drifted behind its own remote), a
  large amount of merged, grep-visible work is integration-only and **not live**; the naive
  check then invites a wrong action — dispatching a doc-correction PR to match a "shipped"
  model, telling a stakeholder a feature is live, closing a deploy-readiness item. So
  **name which ref governs "shipped"** first (where deploy promotes from, not where the
  newest work lands), then test **containment against that ref** with the §3 toolkit pointed
  at it, not at your current branch: `git merge-base --is-ancestor <landed-sha>
  origin/<governing-ref>` proves containment **only while the SHA is preserved** (a normal /
  fast-forward merge). Under a **squash / rebase / cherry-pick** the original SHA is not an
  ancestor though the content shipped — the §3 squash-merge false-negative, the mirror trap —
  so corroborate the way §3 does but **against the governing ref**: grep **its tree** for the
  landed symbol (`git grep <symbol> origin/<governing-ref>`, `git show
  origin/<governing-ref>:<path>`), `git cherry`, or the forge record of the PR that merged
  **into that ref**. "Merged" with no target named is the ambiguity: **merged-to-integration**
  (done, integration-first) and **promoted-to-release** (shipped) are different milestones —
  scope every status claim to the one you verified. Distinct from the stale-base silent-revert
  above (*would merging undo shipped work* — needs the base's post-fork side); this is *did the
  work reach the governing line* — needs containment against that ref. The same branch-blindness
  defeats the "is this finding already fixed?" reproduce check in `method.md` (its `git log -S`
  run on the wrong checkout clears a defect still live on the deploy line), and it is the
  verification the "a merged PR is a **proxy**, not the outcome" rule (`report-format.md`) leaves
  unspecified. Treat a governing branch thousands of commits behind its integration branch, with a
  conflicting / stale reconcile PR, as a **release-readiness blocker in its own right**: surface it
  early, and when the frontier is genuinely exhausted the honest state is "gated on the promotion /
  owner," not more integration-only work that widens the gap.
- **Before closing a PR as duplicate or superseded, diff the two tips — title or
  branch similarity is not patch equality.** Two PRs that look like the same fix can
  differ in a hunk only one carries (one tip gates a `useReducedMotion` check behind
  a mount guard — `mounted ? … : false` — and the other reads it directly); closing
  the "duplicate" drops that hunk silently. Compare the heads first: **two-dot**
  `git diff <tip-A> <tip-B>` when they share a base (the literal difference between
  the two trees — empty iff the tips are identical), or
  `git range-diff <base>..<tip-A> <base>..<tip-B>` to compare the two **patch series**
  when the PRs forked from different points, which a plain two-dot pollutes with
  mainline drift. (Not three-dot `A...B` — that diffs from the merge-base, the
  `git log` commit-range idiom, so it can't tell you what B has that A lacks.) If B
  carries hunks A doesn't, **fold them into A** (rebase or cherry-pick) and *then*
  close B with a pointer; close-as-duplicate is safe only when that diff is empty or
  B ⊆ A with no unique lines. Put the **diff result in the close comment** as the
  evidence; "looks the same," a shared branch name, or a shared issue number is never
  sufficient on its own.
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
- **Automated conflict resolution is gated on a marker-grep, not on `git add` exiting 0.**
  `git add` stages whatever is on disk — conflict markers and all — so a resolution step whose
  `git checkout --theirs -- <path>` silently failed can still be staged and committed with
  `<<<<<<<` / `=======` / `>>>>>>>` in the tree (caught, if at all, only by a later parse error).
  Two mechanical backstops, both required for agent/automated resolution where no human eyeballs
  the diff: **quote/escape every path with glob metacharacters** (`git checkout --theirs --
  'app/kpis/[key]/page.tsx'`, or disable globbing with the shell's own switch — `set -f` in
  bash/POSIX sh, but `setopt noglob` / a `noglob` precommand in **zsh**, where `set -f` is NO_RCS
  and leaves globbing on — because a `[param]` / `*` / `?` path glob-expands differently per shell,
  zsh erroring on a no-match while bash may pass the literal, so an unquoted resolution silently
  no-ops); and **grep the staged tree for conflict
  markers before every commit, gating on the result** — `git grep --cached -qE
  '^(<{7}|={7}|>{7})' && { echo 'unresolved markers'; exit 1; }` (exit 0 = a marker was found →
  block), or git's built-in `git diff --cached --check`. A bare `git diff -G` *prints* the hunk
  but **exits 0**, so it does not gate — and `add` success is never proof of resolution; the
  gating marker-grep plus a build/parse is.
- **Update a branch another worktree still holds with a detached-HEAD fast-forward, never a
  force-push.** When the branch you must update is already checked out in another (often stalled)
  worktree, `git worktree add <branch>` refuses and force-pushing to escape it **strands** that
  lane — it discards commits the lane had already pushed (orphaned on the remote) and leaves its
  local ref and unpushed work on a now-diverged branch. The non-destructive primitive: `git worktree add
  --detach <dir> origin/<branch>`, do the work there (merge the base in, resolve, run gates), then
  push `HEAD:<branch>` — a **fast-forward** when the remote ref is an ancestor of your new HEAD
  (verify that first; if it diverged, it needs a real merge, not a push). The "already checked
  out" collision is usually a symptom of stale worktrees never pruned — `git worktree prune`
  (and removing a merged lane's tree) clears it.

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
- **A large or long-lived change built on the *wrong* integration target** — not the
  one §2 detected (a case that arises only where two long-lived branches exist, so
  there *is* an alternative target) → **High**, distinct from and **above** the Medium
  merge-debt row below: the cost compounds with every commit added on the wrong base,
  and unwinding it later is a forced retarget/rebase of work already built. Intrinsic
  severity stays High at every stage (guardrail 3, `SKILL.md`); stage calibrates only
  the **urgency** — block-now on a `growth`/`mature` line vs tracked on a `prototype` —
  never the severity. State the left⇥right commit counts measured and name the
  **retarget/rebase-before-more-work-lands** command in the finding.
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
- An in-flight branch/PR whose **base is not the detected integration target** (e.g.
  based on `main` while features integrate into `develop`) — for a large or long-lived
  change, a **High** wrong-base defect (§7), not Medium merge-debt.
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
- A new PR-body / commit-trailer / committed-artifact gate landed with **no update to
  its standing producers** (PR template, Dependabot/Renovate, release/agent bots) — every
  automated PR is refused (green on its real work, red on the new gate) until noticed (§5
  covers only in-batch ordering).
- A union/integration branch merged or squashed in place of its member PRs, or
  already-green members held waiting on the union's aggregate CI.
- An `--admin`/force-merge used to escape a red base, instead of discharging it with
  a verified merge train.
- A `STOP` that leaves a green + `MERGEABLE` PR neither merged under standing
  approval nor handed off by URL, or an unpushed rebase abandoned off the remote.
- A PR merged after another that absorbed its files at an older SHA — a stale subset
  silently reverting the later fix, with no conflict to warn.
- A **long-open PR** approved on its "Files changed" / own-base diff (fork-point-relative,
  so blind to what the target shipped on those files since it branched) — or waved through
  on "rebase + re-run CI" — with no check of the target's post-branch commits on the paths
  it touches; a squash, a toward-the-branch resolution, or a semantically-coupled clean
  merge then drops that newer work with no conflict to catch it.
- An "X is shipped / live" or "already fixed" claim resting on a commit-grep, a "Files
  changed" diff, or a merged-PR status on the **current / integration branch**, with no
  containment check against the ref that governs deploy — on a repo where integration runs
  far ahead of the release line, much grep-visible / merged work is not live.
- A batch merged off one up-front green + `MERGEABLE` snapshot with **no per-merge
  re-check**, or a **merge sweep run concurrently with a conflict-resolution lane**
  against the same base — the moving base head flips later members back to
  `CONFLICTING` while their checks stay green.
- A merge on a **finished green that no longer matches the merge target** — a body/metadata edit,
  base retarget, or description amend the gate's trigger ignored, or a **rebuild whose fresh run is
  still in flight** — trusting the check's colour without reading the head / input digest it ran
  against.
- A PR closed as duplicate/superseded on title or branch similarity with no tip-diff
  evidence in the close comment.
- A local hook, a `Tests: N/N` line, or a checked PR-template box logged as a passing
  control (self-reported, `--no-verify`-bypassable) instead of a forge run pinned to
  the reviewed SHA.
- Under a worktree: an inherited absolute `core.hooksPath`, or a pre-push hook whose
  range is a hardcoded default branch instead of the pushed refs on stdin — gates run
  against the wrong tree or the wrong range.
- A programmatic conflict resolution that stages with a quoted `git add` **without** grepping the
  staged tree for `<<<<<<<` / `=======` / `>>>>>>>`, or an unescaped `[param]` / glob-metachar path
  in a `git checkout` / `add` (a no-match glob silently no-ops the resolution).
- A **force-push** used to update a branch checked out in another worktree (strands that lane's
  unpushed work on a diverged branch + discards its pushed commits) instead of a detached-HEAD
  fast-forward.

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
