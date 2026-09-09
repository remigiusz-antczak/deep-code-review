# Fast agentic delivery: concurrency, scheduling & merge cadence

Read this when: sizing a heavy-lane fan-out on a shared machine beyond a
single spawn decision, choosing between a merge cascade and a merge train for
a queue of already-green PRs, diagnosing a fleet-wide red that no single diff
caused, or reviewing (domain K/S in the sibling `deep-code-review` skill)
whether a target project's own fleet-scale CI/merge behavior holds up under
N-agent load. Complements — and does not restate — the environment probe's
composite predicate, the Conductor's event-driven rhythm, gate-epistemology
principles 3 and 6, and the worktree/occupancy rules already in `SKILL.md`.

---

## Gate on free RAM and the swap trend — `load1` is not a reliable signal alone

The environment probe's composite predicate used to include `load1 < cores ×
1.3` as a primary term. **That bullet is now corrected directly in
`SKILL.md`** — free RAM and the swap trend primary, CPU idle secondary,
`load1` a weak corroborating signal at most; this section is the mechanism
and the worked example behind that fix, not a second, competing rule.
Linux/macOS load averages count threads in uninterruptible I/O-wait, not only
CPU-runnable ones — "adding the uninterruptible state means that Linux load
averages can increase due to a disk (or NFS) I/O workload, not just CPU
demand," with a worked example where "a heavily disk-bound system might be
extremely
sluggish but only have a TASK_RUNNING [CPU-runnable] average of 0.1" (Gregg;
source below). Observed directly on a 14-core host: `load1` sat at 7
(comfortably under an 18-ish `cores × 1.3` ceiling) while CPU idle read
81% — the elevated `load1` was disk I/O from several concurrent dependency
installs, not CPU contention, so it neither flagged the real problem nor
stayed a trustworthy "all clear." The actual failure was memory: swap grew
from roughly 4 GB to 12 GB, driven by the many headless-browser processes a
full local browser-suite lane boots (CI-offload, below), and lanes died on
their own timeout once swap pressure hit — independent of what `load1` read
at the time, and despite the host reporting a comfortable 86% free RAM
shortly before. **Corrected signal hierarchy:** free RAM and the **swap
trend** (is it climbing, not just its current level) are primary — spawn
while free RAM stays above a working buffer (~15%) and swap is not actively
growing; back off the instant swap starts ballooning, before free RAM alone
would look low. CPU idle is a useful secondary confirmation of real
headroom. **Do not gate on `load1` alone** — at most a weak corroborating
signal, never the deciding term, because it cannot distinguish CPU
contention from disk I/O. Whatever the exact predicate, **spawn one heavy
lane at a time, re-sample after a settle window, then decide on the next** —
never compute a ceiling and dispatch straight up to it.

## Sweep the whole ready queue on every trigger, not just the triggering item

The Conductor's attention is correctly event-driven, not polled — but a
Conductor that reacts only to the specific thing it is waiting on (one
lane's own completion, say) can sit through several such events while a
**different, already-green, already-mergeable** PR sits idle in the same
queue, simply because nothing about that other PR generated an event. The
fix: whenever the Conductor's attention *is* triggered by any of the four
named events, spend one cheap pass over the **entire** ready queue (a status
check per candidate PR) before returning to waiting — not only the item that
triggered the check. This is a completeness fix to what a checkpoint covers,
not a change to the event-driven model itself.

## A third gate-epistemology case: a correct, external, fleet-wide finding

Principle 3 separates *the check could not run* (fail open, `UNVERIFIED`)
from *a real defect the diff introduced* (fail closed). A newly-published,
correctly-detected dependency-vulnerability advisory is neither: the gate is
right, the finding is real, and it is shared across every open change **and
the mainline itself**, with no relationship to any one diff. One observed
instance: a real advisory reddened the mainline and every open PR in a queue
at once with zero code change from any of them; the fix that actually
unblocked the fleet was **one coordinated dependency-lockfile bump**, landed
as a fix-forward, after which the rest of the queue needed to resync against
the new mainline rather than each independently rediscover the same fix.
Name this case explicitly — it saves the diagnosis time of treating a
fleet-wide, external-cause red as N unrelated regressions. It is a
**diagnosis shortcut, not a new merge authority**: it does not license
merging onto a red mainline beyond whatever narrow, human-approved
change-control path a project already has for exactly this case (one
reviewed, unblocking fix).

## An independent-PR-queue cascade is a cadence choice, not a new authority

Gate epistemology principle 6 requires union proof before a merge train —
not restated here. A related but distinct situation: a **queue of PRs that
are each already independently green**, with no known interaction between
them (typically right after the single common blocker above is fixed and the
whole queue needs to resync). Landing that queue does not need a new,
lighter-weight merge authority — it needs **cadence**: run the project's own
merge-authority check against every queued PR on a short interval, rather
than merging one PR and waiting for the mainline's full CI resolution before
even looking at the next. **The one thing this must not become:** a second,
separate pre-check (e.g., asking the forge "is this mergeable?" through a
different call than the authoritative merge gate itself) that races the
platform's own status — mature merge tooling names this exact anti-pattern
from a past incident and refuses it by design, calling only the one
authoritative gate, every attempt, never pre-checking through a second path.
A cascade is **weaker evidence than a union-proven train**: a train proves
the *combination* is sound before any member merges; a cascade only proves
each member was independently green and re-confirms that at each step.
Defensible specifically right after a single common blocker clears and every
queued PR was already independently green — not a general substitute for a
train when queued PRs might still conflict with each other.

## CI-offload the heavy gate by default — lane weight, not lane count, drives memory cost

A lane that runs a project's full local aggregate gate — a real build plus
the complete browser/E2E suite plus any slow lint/audit step — boots many
headless-browser processes per run and is the dominant memory cost on a
shared machine, not merely "one more lane." A lane running only the fast
tier (lint, unit, type-check, at most one targeted spec relevant to the
diff) costs a small fraction of that. With several full-gate lanes running
at once, the machine's memory gets consumed even when each lane's own
resource check passed at spawn time, because the check ran before the
browser-heavy phase started, not during it. Default a lane's own local
verification to the fast tier, and let CI's own — ideally
already-parallelized — jobs carry the full matrix. This sharpens "verify on
CI, treat a local run as the pre-check, never the evidence": defaulting
every lane to the light tier is the actual concurrency unlock — it is what
lets several lanes run inside the RAM budget one full-gate lane alone would
otherwise consume — not a smarter resource-gate formula (previous section).

## A worktree's own gate can fire on a file it does not own

A definitions- or content-only change can rebuild a generated artifact that
is *mirrored* into a directory owned by a different toolchain (for example, a
compiled data file synced into an application directory whose own
pre-commit gate fires on any staged path under it). In a **fresh** isolated
worktree — before that toolchain's own install step has run — the mirrored
file alone can trip that gate and fail closed, even though the change never
touched that toolchain's code. Two portable fixes, either sufficient: (a)
provision the *whole* worktree's toolchain (run every subtree's own install
step) before the first commit, even when the change looks confined to one
subtree; or (b) scope a definitions/content-only lane to skip staging the
generated mirror at all, letting a downstream build step regenerate it. This
is a **provisioning gap, not a defect in either gate** — each gate does
exactly what it is supposed to; the worktree was simply not fully set up for
the one it tripped.

---

## Sources

Fetched fresh for this file, verified 2026-09-09:

1. Kanban University, *Kanban Guide*. A WIP limit's purpose, verbatim:
   "balance utilization and still ensure the flow of work"; "limiting the
   work that is allowed to enter the system is an important key to reducing
   delay and context switching"; a WIP limit as "an enabling constraint."
   https://kanban.university/kanban-guide/
2. Google Engineering Practices, *Small CLs*. "100 lines is usually a
   reasonable size for a CL, and 1000 lines is usually too large"; small
   changes are reviewed more quickly and thoroughly, introduce fewer bugs,
   and simplify rollback.
   https://google.github.io/eng-practices/review/developer/small-cls.html
3. Wikipedia, *Blast radius* (computing sense). "The impact that a security
   breach of one single component of an application could have on the
   overall composite application"; a sibling technical-debt sense naming
   lockstep-edit surfaces directly.
   https://en.wikipedia.org/wiki/Blast_radius
4. GitLab Docs, *Merge trains*. "Two merge requests can each pass their own
   pipeline, but their combined changes can still conflict"; each queued
   pipeline runs combined with the target branch **and** every earlier
   queued change.
   https://docs.gitlab.com/ci/pipelines/merge_trains/
5. Brendan Gregg, *Linux Load Averages: Solving the Mystery*. "Adding the
   uninterruptible state means that Linux load averages can increase due to
   a disk (or NFS) I/O workload, not just CPU demand"; worked example, "a
   heavily disk-bound system might be extremely sluggish but only have a
   TASK_RUNNING average of 0.1" — the basis for "don't gate on `load1`
   alone" above.
   https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html

## Cross-references

- `SKILL.md` **Environment probe** — the composite resource predicate this
  file's load-average section refines; not restated here.
- `SKILL.md` **Conductor operating rhythm** — the event-driven attention
  model this file's queue-sweep section extends.
- `SKILL.md` **Gate epistemology**, principles 3 and 6 — the two existing
  cases this file adds a third case to, and the union-proof rule the cascade
  section stays subordinate to.
- `SKILL.md` **Worktrees and occupancy** / **Local environment (own it)** —
  where the worktree-provisioning gotcha's two fixes belong in practice.
- `deep-code-review`'s `release-engineering.md` — the review-time audit of a
  *target's* release pipeline (feature flags, canary, DORA); this file is the
  authoring-time counterpart for the project's own fleet, not a target's.
- `docs/standards-index.md` — fetch dates and full citations for the five
  sources above.
