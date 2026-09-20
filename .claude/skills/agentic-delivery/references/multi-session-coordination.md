# Multi-session / peer coordination

**Read this when** two or more independent agent sessions — separate
processes, machines, or accounts — coordinate on one shared repo through an
async, lock-free channel (a tracker issue, a committed registry file, a
shared doc), with **no single session holding both as its own subagent
lanes.** Different axis from `fast-agentic-delivery.md`, whose one
orchestrator directly dispatches, watches, and kills its own lanes: here
neither side has that view of the other, and the shared channel can be
stale, unread, or already contradicted by the time it's read. Use
`fast-agentic-delivery.md` for worktree occupancy, ownership maps, and a
lane's own liveness inside one session; use this file for the peer-to-peer
case that model doesn't cover.

## A prose claim doesn't scale or machine-check — commit a structured registry instead

"I'm taking X, Y, Z" in a shared thread forces every peer to *semantically
parse* prose to find a collision, and claim volume across a long thread gets
skimmed past — two independently-claimed items touched the same shared
component, caught only because a peer happened to re-read both, not because
anything checked it (#593). Commit a small, parseable claim registry
instead — one entry per active peer/lane, minimally `agent_id`,
`path_globs`/`issue_refs`, `pr_url` (a claim can lag its own PR),
`claimed_at`/`status` for staleness, and an `exclusive_role` field naming the
single current holder of any exclusive step (e.g. who may run the merge), so the
collision probe below has a well-known field to check. The registry, not the thread, is the
source of truth for "is this spoken for." Multi-machine sibling of
`fast-agentic-delivery.md`'s ownership-map / claim-staleness rule (which
already covers *reconciling* a stale claim) — this section is about
*shape*: machine-readable and diffable, never prose a peer must interpret.

## Collision-check mechanically before you claim or write — never "read the thread and hope"

Reading the thread and diffing open PRs by hand before every claim, or
before a shared exclusive step (a merge only one side should run), is easy
to skip under volume (#597). Fold it into one deterministic pre-write probe
run before any write-lane or exclusive step: (a) glob-match planned paths
against the claim registry's active entries; (b) diff live open-PR file
lists against the same paths — a claim can lag its PR; (c) check the one
well-known "exclusive role" field and refuse if another peer holds it and is
still live. Output is go/no-go plus the exact colliding file, issue, or PR —
never a prose inference a peer might skip.

## No live peer, no coordination lift — verify liveness before spending the budget

A shared board looks like collaboration whether or not anyone reads it. One
peer can post status and "guidance" for hours while the other side is
inactive and get zero lift for it — "sync with the peer" gets followed
literally even into a void (#709). Before writing a hand-off, check an
explicit liveness signal: the peer's process/session is up, or it posted
within a recent window — the same don't-infer-aliveness-from-a-stale-artifact
discipline as `fast-agentic-delivery.md`'s transcript-is-not-liveness
section, applied there to a lane's transcript and here to a peer's last
board post. No live peer: stop writing essays, degrade to solo at full
tilt, and escalate the absence rather than silently compensating. **🚩
tell:** a one-sided board — every recent entry from the same peer — with no
liveness check before the next post.

## A sync that reads only the newest entry silently drops what landed between reads

Reading a board by its newest comment alone *feels* like syncing — it is
polling — but it's a roughly one-entry window: a peer's playbook, discovery,
or collision flag a few comments back goes missed for hours, and the poster
reasonably assumes a posted hand-off was received and stops repeating it
(#711). Track a **high-water mark** — the last comment id/timestamp actually
processed — and read/act on the **full range** since it, never only the
tail; on re-engaging after an idle gap, back-read the whole gap. Compounds
with the liveness check above: a live peer still yields zero lift if it
reads shallowly.

## Two peers proposing opposite splits at once is a race on the division of labor — reconcile deterministically

An append-only board has no compare-and-swap: "read latest, then post" is
not atomic, so two peers can read the same prior state and post **opposite**
work-splits seconds apart, each reasonable, each stale the moment the other
lands (#713). Don't re-negotiate; resolve by a fixed rule: (1) **in-flight
work is the anchor** — whatever either peer already started stays with that
peer, never reassigned; (2) unstarted work defaults to a **pre-agreed, fixed
partition** (by directory/subsystem); (3) real collision-safety is a
**per-item claim with an action-time recheck**, not the coarse split; (4)
**first-to-reconcile-wins** — whoever notices the crossed splits first posts
the reconciliation and both adopt it, rather than re-proposing. **🚩 tell:**
two peers each claiming the other's already-claimed area, with a third
re-proposal instead of rule (4).
