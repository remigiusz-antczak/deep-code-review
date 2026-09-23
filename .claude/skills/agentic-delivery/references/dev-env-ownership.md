# Fast agentic delivery — dev-environment hygiene and shared ownership

Read this when: booting a dev server in a lane, separating the serving tree from the committing tree, re-running a
generator after commit, gating an absolute-count ratchet under parallel lanes, handling a live-feedback burst or
new mid-task requirements, applying an ownership map, probing contention against a PR's changed-file list,
verifying a "the served environment is on the latest commit" claim, or bringing up the local stack for G5. Part
of the `fast-agentic-delivery.md` lesson ledger — its index, sources, and cross-references live there; an
"above"/"below" pointer to a section not in this file resolves through that index.

---

## Boot-the-dev-server lanes need a copy, not a symlink, of the dependencies dir

Any worktree that runs the **heavy gates** needs its own real install — run `npm ci` in it (or a
**copy-on-write clone** of a real `node_modules` on the same volume). To share one installed-dependencies
directory across throwaway worktrees, lanes sometimes **symlink** it; edit-only checks (typecheck/lint/unit)
*seem* to tolerate the symlink, but it breaks the heavy gates three ways:
- **Under-install** — a dep present in the lockfile but absent from the shared tree makes `tsc` fail with
  **TS2307** ("cannot find module") — a false type error, not a real one.
- **Bundler boot** — the **modern dev bundler** rejects a dependency path that resolves *outside* its inferred
  project root ("points out of the filesystem root"), so the dev server never starts and the browser/UX gate
  reports a **false** "could not run."
- **Warning drift** — a symlinked tree yields phantom lint warnings, so a `--max-warnings` ratchet false-fails
  on a count that isn't real.

The tell is **local QA red where CI is green**; `npm ci` on the same tree settles all three — the fix is
mechanical (install, don't link). Reserve the symlink for edit-only fast-tier lanes. And a gate must distinguish
**"could not run" (infra)** from **"found a problem"** — a bundler-boot failure, or a TS2307 from an
under-installed symlink, is the former, never a content finding (the gate-epistemology distinction, principle 3
above).

## Serve and commit from separate trees — a long-running process dirties a gate-asserted config

A long-running process — a dev server, a codegen/asset watcher — that **rewrites a tracked config file on boot**
(regenerates or normalizes in place a config the toolchain owns) deadlocks the commit workflow when both share
**one working tree**: a test or pre-commit gate that pins that file's **exact content** sees it dirty for the
process's **entire lifetime**, so every commit from that tree fails on a "modified config" nobody edited — or
forces a stop-server / restore-file / re-commit dance. **Serve from a different tree than you commit from** (a
dedicated worktree/checkout for the running stack, so the commit tree stays clean); if one tree is unavoidable,
make the process write to a **gitignored/untracked** path, or stop it and restore the file before committing.
Where a legitimate tool rewrites the file, prefer a gate that asserts its **shape/schema** over its exact bytes.
Distinct from "never `build` against a directory a running server is serving" (a stale-asset *ship* failure —
wrong build output) and from the out-of-tree-scratch metadata-crossing section above: this is a single-tree
**serve-vs-commit deadlock** where a running process dirties a **tracked, gate-asserted** file so the commit
gate itself fails.

## A hard-reset sync loop on a live-served worktree silently kills the dev server

The mirror of the serve-vs-commit deadlock above: a background loop that **`git reset --hard`** (or `checkout`)
a worktree **while a dev server is serving from it** yanks the files out from under the running process. Many
dev servers (or their file-watchers) **exit cleanly** when their entry file vanishes or is rewritten mid-run —
**exit 0, no error** — and the next UX gate hits a dead port (`connection refused`), a **false failure** that
reads as a code defect. Don't hard-reset a served tree on
a sync loop: **serve from a tree the sync loop never touches** (the separate-tree rule above), prefer a
**fast-forward-only** update over a hard reset on any served tree, and put the dev server under a
**health-checked supervisor** that restarts it after a sync (the UX gate waits on that health check) so a
legitimate resync does not read as a broken build. A surface a **human** watches never restarts per sync: the gap
(connection refused, then a cold compile) reads as "feature gone", and debouncing only shortens it. Update it
atomically — a deployed preview, or a warmed standby (a second tree behind a small proxy on the public port,
switched once its main routes answer, both backends on one shared local data store); restart in place only when
the active backend fails its health check. Check a "feature X is gone" report against the restart log before
treating it as a regression.

## "Latest" means the process restarted and a fetched page proves it — the serving tree's git HEAD is not evidence

A different axis from every liveness rule above and in `verification-handback.md` (those ask *is the process
alive*; this asks *does what it serves match the merge*) — `verification-handback.md`'s *A transcript's size or
mtime is not a liveness signal* section is the process-aliveness cousin, not this rule. A served UI's freshness
claim needs **both**: (1) evidence the serving process **restarted after** the merge — a recorded restart
timestamp/PID change, a supervisor log, or proof its hot-reload path actually re-served the changed files — and
(2) a **fetched page** from the running surface showing the newest merged change. Git state of the serving
directory/worktree satisfies neither: a long-lived dev server that only hot-reloaded, or never restarted, keeps
serving the pre-merge build even while `git log`/`git status` in its checkout show the merge landed — "the
serving tree's git HEAD matches the branch" is not "the running process serves it." `surface_check.py served --url
… --expect-sha … --probe …` is the mechanism for (2): it fetches the running
app and extracts the build/commit id the **serving process itself** reports, refusing a data timestamp or a
git-HEAD read as a substitute; `scripts/surface_check.py` lives in this skill's own `agentic-delivery/scripts/`.
Report `UNMEASURED`/`UNVERIFIED`, never "latest," when only the serving tree's git state was checked.

## Re-running the generator after the commit re-stamps its own output — a one-shot dirty tree that hangs the push

The one-shot cousin of the serve-vs-commit deadlock above: there a *long-running* process holds a tracked file
dirty for its whole lifetime; here a *single* rebuild-commit-then-verify sequence dirties its own just-cleaned
tree in one step. A lane that
**rebuilds a generated/compiled artifact, commits it, then runs the mandated verify gate before pushing** can
re-dirty the tree the commit just cleaned — when the verify gate **re-invokes the same generator** and that
generator embeds a **self-referential field that changes on every run by design**: a wall-clock build time, the
current commit SHA, a build counter, a checksum-of-self. The re-run rewrites that field inside the file it just
committed; the new value can never match the committed one, so `git status` is
**dirty again the instant after a clean commit**. The subsequent `git push` (or a pre-push clean-tree check)
then can't proceed — and the naive fix, re-commit the diff, **loops**, because the next verify run stamps it
again.

Why it slips: `git status` is clean the moment `git commit` returns, so "committed the rebuild" reads as done;
the re-dirtying happens one step later, inside the gate whose *job* is to re-derive the artifact and prove it
matches its sources. When the generator embeds such a field,
**"prove the tree is fresh (rebuild + diff)" and "the tree stays byte-identical to what's committed" are mutually exclusive**
— verifying freshness is exactly what re-dirties the tree. Neither the generator (correct both times) nor the
commit (succeeded) is broken in isolation; only the composition — commit, then re-verify with a self-stamping
generator — produces the hang.

Any one of three closes it; prefer the first:

- **Make the build reproducible** so the verify re-run is byte-identical and there is nothing to reconcile:
  derive the embedded commit id from the *committed* commit (or the merge-base) rather than HEAD-at-build-time,
  pin the timestamp to a **source-controlled value** (the commit's own date, or a fixed epoch) instead of
  wall-clock, and drop a self-timestamp or checksum-of-self that carries no real information. This attacks the
  root — the field stops changing between runs.
- **Order the pipeline so the generate step runs *before* the commit** and is never re-run between commit and
  push; the verify step then *checks* the committed artifact (diff / hash / schema-assert it) without
  *regenerating* it.
- **If the verify gate must regenerate** (its charter is to prove freshness), exclude the declared changing
  field(s) from the clean-tree check via a normalizing filter, or immediately discard a diff confined to those
  fields (`git restore` / `git checkout -- <path>`) — never re-commit it (that loops) and never leave it dirty.

For the autonomous lane: a dirty tree that appears **immediately after the lane's own rebuild commit**, on only
known generated paths, with the diff **confined to the one declared self-referential field**, is a
*distinguishable, higher-confidence* signal than a dirty tree on unrelated edits — self-heal by discarding that
diff, never loop a re-commit, and escalate only when a *non-stamp* data row actually differs (a real freshness
miss, not the churn). Distinct from the serve-vs-commit deadlock above (a process dirtying a file for its whole
lifetime, not a discrete one-shot sequence) and from the fresh-worktree provisioning gap in "A worktree's own
gate can fire on a file it does not own" above (there the toolchain was simply not installed yet; here it is
installed and correct, and *re-running* it is what dirties the tree).

**🚩** a rebuild-commit-then-verify sequence whose verify step re-runs the generator; a dirty tree on only a
generated file's stamp line right after that file's own commit; an auto-pusher that re-commits the same one-line
diff more than once.

## An absolute-count ratchet is contended shared state under parallel lanes — gate on the delta, not the tree total

A gate that asserts an **absolute count over the whole tree** — `--max-warnings N`, a coverage-percent floor, a
total-bundle-size budget — is a **shared counter**, and under parallel write-lanes each lane is
**blind to the others' deltas**:

- Lane A rebases, sees `N-1 / N` ("one slot left"), adds one warning of its own and pushes green, taking the
  last slot.
- Lane B, branched from the **same base**, adds one warning of its own and pushes — the tree is now `N+1`, so
  **B goes red** even though B's own diff is **no worse** than A's. B is punished for **arriving second**.

The failure **scales with fan-out width** and is **invisible until the second lane's CI runs** — the first lane
sees only headroom. It is the same shape as capping in-flight lanes by a shared count rather than by landed
artifacts (above): the quantity each lane must respect is the **delta it owns**, not a tree-wide total it shares
with lanes it cannot see.

- **Gate on the per-diff delta** — "this change introduces **no new** warnings versus its **merge base**" — not
  on the absolute tree count. A per-diff check is **order-independent**: every lane is measured against its own
  base, so no lane can consume another's slot. Keep the absolute count as a **slow-moving burndown target** (a
  report or a non-blocking trend), never the per-PR gate under fan-out.
- **Brief every lane to fix any warning its own diff introduces** before pushing, and
  **never raise the ceiling to pass** — bumping `N` to land is decoration, the ratchet inverted (a ratchet only
  tightens).
- **🚩 grep:** an absolute `--max-warnings <N>`, a whole-tree coverage-percent floor, or a total-bundle-size
  budget used as the **per-PR** gate in a repo that fans work out to **parallel lanes** — gate the delta
  instead.

Distinct from the phantom-warning `--max-warnings` false-fail above (a symlinked dep tree inflating the
**count** — an *infra* "could not run", not a real regression): there the count is **wrong**; here it is
**right but contended**. Same shape as any absolute-threshold gate on a shared counter — under concurrency, gate
on the **delta the change owns**.

**A further trap survives even after gating on the delta: a revert can be blocked by the very gate it needs to bypass.**
A ratchet is forward/tightening-only by design, which traps a **revert**: undoing a redundant bump to the
baseline is judged against the tree's **current, still-regressed count**, so the revert itself fails the gate
the ratchet exists to enforce (observed: a baseline bumped `1015→1016` by three redundant lanes — the lane that
tried to revert its own bump back to `1015` could not, since the real count was already `1016` and the pre-push
hook had no override).
**A forward-progress ratchet that also blocks a revert-to-green is misconfigured — a revert must not be gated by the metric it is restoring.**
Give it an audited revert path judged against the targeted commit, not current HEAD, or a delta gate (above) so
a redundant bump never needs a same-day revert.

## Acknowledge a live-feedback burst before dispatching — silent throughput reads as ignoring

When the owner is present and firing many separate pieces of feedback, silently dispatching background work —
producing no acknowledgement — reads as *not listening* and escalates frustration, even when work is in fact
running in parallel. Throughput without a reply is indistinguishable from ignoring them. On each burst, the
**first** action is to capture every item into a visible tracked list and reply with the ordered plan plus what
is already in flight; **dispatch second**. One honest "captured all N, here is the order, these three are
already running" beats silent parallelism. Acknowledge first, optimise throughput second.

## Queue new requirements to a file the lane polls — interrupt only to stop or redirect

The burst rule above captures incoming feedback to a tracked list; when that feedback is
**new scope for a running lane**, the list must be a **durable file the lane polls at its own checkpoints**, not
an interrupt. The failure it prevents is **a lane busy for hours that ships nothing** — a single implementation
lane interrupted and re-briefed a half-dozen times, each ask legitimate, each landing mid-orient so the lane
restarts its orientation and never reaches a commit; and each message *grows* scope while retiring none, so the
definition of done recedes faster than the lane implements.

- **New scope goes to a file, not a message** — a checklist in the repo or an agreed scratch path the lane reads
  at its checkpoints, finishing the unit it is on before picking up the queue. A requirement buried in a
  transcript is only as durable as the lane.
- **Interrupt only for a genuine control signal** — stop, abandon, or a correction that invalidates work in
  progress. "Also do X" is not a control signal, **and neither is a process-policy change** — re-ordering the
  queue, switching serial↔parallel, reshuffling priority: those queue to the lane's next **checkpoint** (a filed
  issue, a pushed commit, a merged PR — never a mid-edit or mid-compose state), because each mid-task redirect
  makes the lane re-orient and ship nothing (the *interrupt-thrash* anti-pattern). A genuine control signal —
  including a **P0 safety** issue (imminent data loss, a secret leak, a destructive irreversible action), the
  clearest case since it invalidates continuing — still interrupts at once; a process-policy change is not one,
  and waits for the checkpoint.
- **Freeze scope per deliverable** — a lane ships against the scope it was given; later asks are the next
  increment. Prefer a **shippable slice that then stops** over a consolidated deliverable with no stopping point
  — the slice lands artifacts under exactly the conditions where the growing lane lands none.
- **Count the re-briefs** — more than one or two scope-extending messages to the same in-flight lane is the
  signal that the scope was mis-sized: **split it**, don't send a third.

**The inverse case: a correction to a brief already dispatched to a whole cohort is two actions, not one.** The
rule above covers new scope arriving for a *single* lane that polls its own file; a fix to a shared brief or
template already fanned out to N lanes is a different shape — unless every lane in that cohort was itself set up
to poll a shared file per the discipline above, a lane briefed with the content **inlined at spawn time** holds
its own frozen copy and has nothing left to poll, so the fix does not reach it on its own. Treat the correction
as two actions, always: (1) **fix the template** so every future dispatch carries the correction, and (2)
**enumerate the in-flight cohort still running the stale version and remediate each one directly** — a targeted
re-brief, a kill-and-respawn, or an explicit accept-as-is — never assume fixing the source alone reaches lanes
already spawned from it. Catch this before it costs N corrections:
**discover the brief's own format/gate requirements with one dry run before fanning it out** — one lane through
the brief, checked against the actual downstream format/gate it will be judged by — the
*pilot before full fan-out* rule above, narrowed to one lane because the target is the brief's own correctness,
not the task boundary.

## An ownership map blocks a dual *write*, not dual *work* — and "assigned" is not "in progress"

The *Worktrees and occupancy* rule in `SKILL.md` (claim the work before starting, one writer per worktree)
prevents two lanes **writing the same file**. It does not prevent two lanes **working the same objective** from
different files: a module-ownership map saying "lane A owns `api/`, lane B owns `web/`" answers
*who may write where*, not *is anyone already building this*. Read as a work-lock, it spawns a duplicate lane on
a feature already in flight. Before starting, check for an **active lane on the objective**, not just file
ownership — and treat a forge **assignment as intent, not progress**: an assigned issue with no draft PR, no
worktree, and no commits is unclaimed in practice (`assigned` ≠ `in-progress`). That absence-check is only as
complete as the surface it runs on: `gh pr list` and issue state show **forge** signals, never a **local-only**
branch, worktree, or unpushed commit on another machine or another agent's checkout — so a lane that queries the
forge alone can read *unclaimed* while a real one is mid-flight. Scan local git too (`git branch`,
`git worktree list`, `git stash list`), but treat any hit as a **lead to check for liveness**, not proof of an
active lane — a `worktree list` entry proves only that something *once* ran (the transcript-is-not-liveness rule
above); cross-check a real liveness signal, then adopt-and-re-verify the work or reconcile the dead lane, never
trust its state blind. A **claim/ownership record** whose last progress predates a stated
**staleness threshold** — the liveness signal defined by that rule (a new commit, a PR comment, a touched claim
record) gone quiet — is treated as **dead and reconciled**, never respected indefinitely: a crashed lane that
left a claim behind otherwise locks its own objective forever, and reclaiming a stale *claim* is cheap and
reversible. Declaring a *running lane* dead is the higher bar — that still needs the transcript-is-not-liveness
rule's positive actual-product signal, **never elapsed time alone** (killing a live lane is destructive;
reconciling a stale claim is not). **Announce-then-take:** claim the objective (a draft PR, or a posted "taking
this") **before** opening the worktree, never after — take-then-announce races two lanes onto the same work. And
**two lanes reporting the same bug idiom at different callsites is a *missed sweep*, not two findings** — grep it,
land every instance in one lane, one follow-up confirms none remain (its full instance set is scoped
once, `deep-code-review` `method.md` Phase 4).

**The converse over-caution: a shared artifact in flight blocks only the lanes that touch it.** Withholding
*every* lane because one in-flight branch edits a shared file (a design-token file, a lockfile, a config) is the
mirror error — disjoint-surface lanes that never touch that artifact are safe to run in parallel, and pausing
them idles capacity for a conflict that cannot occur. Gate a lane on whether **its own** surface overlaps an
in-flight write, not on whether **any** shared write is open.

**A read-only *review* of a contested surface is wasted even though it cannot write-conflict.** The converse
above clears a lane whose surface is disjoint from every in-flight write — read literally that also
*greenlights* a review lane, since it writes nothing and never conflicts. But a defect sweep against a base an
in-flight or held branch is mid-rewriting is throwaway: its findings go stale the instant that branch lands,
and a fix dispatched from them collides with it (#912). The write-conflict gate is the wrong gate for a
read-only lane — the real test is whether the owning branch is
**rewriting the code the finding would be about**. Run the same in-flight-ownership probe first (forge state
*and* local git); if a branch owns the surface, **review that branch's tip, not the stale base** (a PR review
whose findings land *with* the change) or **defer** until it lands (`multi-session-coordination.md`'s
*in-flight work is the anchor*) — **not** "review nothing anyone touches": findings on a **different axis**,
or a region the branch does not touch, are safe to file now — only the overlap is contested (a static domain
partition, `multi-session-coordination.md`, keeps most review lanes clear of it already). Any finding carried
across a landing is a lead, re-confirmed at the new head, never a verdict (*discovery findings are durable as
leads; a discovery verdict is disposable*, above).

**When one redesign contests the *whole* surface, repoint the lens class, not just the base.** The rule above
handles a contested *file set* — review the owning branch's tip, or defer. A large redesign/release PR that
rewrites an entire UI surface contests something bigger: an entire **review-lens class** — accessibility, visual
polish, design-system conformance, empty/loading/error states — since *every* finding any of those lenses
produces lands on a file the redesign already rewrites, so nothing is actionable until it merges, and several
lanes re-derive that same conclusion at full cost. Reviewing the tip helps little — it is a many-hundred-file
work-in-progress whose findings churn until it lands. Repoint the **lens rotation itself** onto dimensions a UI
redesign structurally does not touch — non-UI logic, data/model layers, shared utilities, API/data-access,
security — whose findings are actionable now *and* survive the landing (the *different-axis survivors* above,
now an **active routing decision**, not a passive "safe to file"). Cache the contested set once on the shared
channel so no lane re-derives it (the paginate-then-reconcile probe below, defeated by a truncated file list
failing open — #936); resume UI lenses once the redesign merges. Distinct from #936's
*route the peripheral fixes now, hold the contested ones* — routes **fix** lanes by file; this repoints
**review** lenses off a contested *dimension* onto an uncontested one.

**A commit or PR attribution trailer names the agent that actually did the work.** Under a shared commit
template, the co-author / attribution trailer must name the *real* executing agent or model per lane — a
template that **hardcodes one model name** makes history lie about who produced what, the same wrong-producer /
false-attribution failure the review side treats as a correctness defect. Parameterize the trailer or let each
lane stamp its own identity at commit time, never inheriting the orchestrator's identity by default —
provenance hygiene for a fleet, the delivery-side analogue of the evidence-provenance the review side already
demands.

## A contention probe against a truncated file list fails open — reconcile the returned count against the PR's own changed-file total

The ownership-map probe above answers *is this file being rewritten under me?* by reading a PR's changed files.
When that read is a **single un-paginated CLI/API call**, it returns one page, not the whole set — and a
membership test against a truncated list does not merely under-count (the
*truncated listing is not a complete count* trap in `deep-code-review`'s `branch-and-merge-hygiene.md`), it
**fails open**: a target file that sits *past* the first page reads as **absent → uncontested → safe**, so the
probe green-lights a lane onto a file an open PR is actively rewriting. On a large release PR the effect is
systemic — most files fall past the first page, so most contention checks return a false *safe* and the
orchestrator keeps dispatching lanes onto doomed fixes that collide the instant the release lands (#936).

- **Paginate, then reconcile the length.** Pull the full list
  (`gh api repos/OWNER/REPO/pulls/<n>/files --paginate --jq '.[].filename'`) and
  **cross-check its length against the PR's own reported changed-file count** before trusting any membership
  test — a returned length short of the reported total means the list is truncated and every *absent* answer is
  `UNVERIFIED`, not safe. Count-reconciliation is **threshold-independent**: it holds whatever the page size is,
  where "pass a bigger `--limit`" only patches the one number you happened to know.
- **Enumerate the contested set once, then dispatch against the cache.** Compute the release PR's full file set
  a single time (re-fetch on a stated staleness bound) and check each candidate lane against that cache — not a
  fresh truncated probe per dispatch, which re-pays the fail-open on every lane.
- **A giant release PR makes routine fixes to its files net-negative until it merges — report that, not "idle."**
  While the release is open, a fix to any file it rewrites is throwaway (the
  *read-only review of a contested surface is wasted* rule, above). The honest status is
  **"most work is waiting on the release,"** not "producers are idle" — state the operator's own metric, the
  same reconcile-against-the-operator's-number discipline the tracker section below applies.
- **🚩 tell:** a contention / ownership probe that reads *absent from a `--json files` page* as *uncontested*
  with no count-reconciliation, on a repo with a many-hundred-file release PR open.

## Local environment — the five-step stack procedure

The procedure behind `SKILL.md` **Local environment (own it)** and its G5 rule.

1. **Discover** the project's one-command path (`README` / `package.json` /
   `compose.yaml` / `.devcontainer` / `Makefile`) — prefer what the repo
   documents; do not invent a second stack.
2. **Bring it up** in the writer's worktree; record the command, URL/port, and
   the health probe that returned 200. A missing prerequisite's `doctor` output
   is the receipt — do not skip to "tests passed on the host."
3. **Verify against the running process**, not only the repository: served
   smoke, empty/error UI states where a UI exists, the project's own
   `verify:served` if it has one.
4. **Tear down** with the matching command; leave no orphan listener.
5. **Never** `npm run build` (or equivalent) against a directory a running
   server is serving — that stale-asset bug is a known ship failure; use the
   project's isolated verify dir.
