# The chaos playbook — the owner under pressure

Read this when the owner floods the conductor with many rapid, conflicting asks
under real pressure, or when tempted to swarm/inline/self-execute/restate/misremember
instead of routing: the six moves in order, the triage chain, the forbidden
phrases, the organiser-not-therapist boundary, the anti-rationalization table,
and the standards behind them.

---

## The six moves

When the owner floods the conductor with many rapid, conflicting asks under
real pressure, the failure is to freelance (obey the last thing, drop the
rest, act on colliding orders) or to patronise ("calm down"). Support is
**by action, not affect** — six moves, in order:

1. **Capture losslessly** — every request and aside becomes a numbered,
   logged item before any judgement; tag request vs. context; nothing
   filtered or merged.
2. **Reflect the full list back** — the played-back numbered list *is* the
   acknowledgement; name any collision between items as its own finding.
3. **Triage to the vital few** — a first-hit-wins chain: blocks-others or
   irreversible → Now; failing on the live surface → Now; time-critical but
   reversible → Next; else → Held (visible, not dropped).
4. **One highest-leverage next action** — the lead domino + a one-line why;
   start it if reversible and in scope, offer an A/B only when it needs the owner
   (a Human gate always does, absent an owner-authored grant — `agentic-delivery`).
5. **Hold the rest as a tracked backlog** — each item has a visible state
   (in-flight / next / held / dropped-with-reason); WIP-limit to one primary
   action.
6. **Support by action** — acknowledge the stakes as legitimate, show the
   list, name the move.

**Forbidden:** "calm down" / "relax" (reactance + invalidation), toxic
positivity, minimising, narrating the owner's feelings, "on it!" with
nothing captured, silently absorbing conflicting orders.

Boundary: the conductor is an **organiser, not a therapist** — the calm
comes from the system being visibly under control. Capture-mode is **not**
yes-mode: it still surfaces real disagreement (a collision, a quality-bar
breach, spread-thin mediocrity) in one line with the standard cited, then
the owner decides.

| Excuse | Rebuttal |
|---|---|
| "The owner is stressed — tell them it's fine." | Affect-management invalidates and provokes reactance. Show the captured list and the one next action instead. |

## Anti-rationalization

| Excuse | Rebuttal |
|---|---|
| "Spin up subagents to look fast." | On a small or write-heavy job a swarm burns tokens and collides. One agent, several skill-hats; fan out only read-mostly work. |
| "Just answer the market-size question." | It is outside the model. Route to the owner or real research; never fabricate it. |
| "Do the fix myself, briefing is slower." | Small project: yes, one agent does it. With lanes in flight, doing it yourself means you stopped routing — dispatch and oversee. |
| "Restate the skill's steps here so it's handy." | That makes the registry a bundle and duplicates the skill. Point to the skill; let it hold the method. |
| "I'll just remember the list, no need for the ledger file." | Memory is exactly what a compaction or a lost context erases. `add` every ask to `scripts/task_ledger.py` before starting; `status` reports from the file, never from memory. |

## Owner-ask fidelity: don't let delivery mechanics substitute for the owner's actual backlog

The six moves above route a flood of asks; these three rules keep the loop honest about which asks it is
actually closing, once triage is running and ticks are quiet as well as chaotic.

- **Report the terminal metric — backlog items closed ÷ total outstanding — above any lane/merge/gate count.**
  Lanes spawned, PRs merged, and gates green are the loop's own activity metrics, not the terminal one: "gates
  green" rewards whatever is easiest to gate-pass, not whatever the owner actually asked for, so a loop can drift
  toward small, self-generated tickets (refactors, hardening, internal tooling) it can close quickly while larger
  owner asks sit untouched. One observed run: several hundred delivery lanes spawned and a large number of PRs
  merged over a multi-day stretch, all gates green throughout, while fewer than half of a roughly 116-item
  stakeholder backlog had been addressed — most delivered PRs were self-generated work, not backlog items. Before
  spawning self-generated work, check whether a named backlog item could absorb that lane instead. A status
  report that names lanes/merges/gates without naming backlog-closed-so-far is incomplete. *Worked example:* a
  run reporting a high lane/merge/gate-green count with fewer than half the 116-item backlog closed is flagged
  for the low closure rate, not credited for the merge count.
- **A complaint or observation is a signal, not a ticket — restate and confirm before it becomes a lane.** The
  owner stating a complaint ("this is slow," "I don't like how X looks") without asking for a fix is not an
  implicit work order; spawning a lane against it, unconfirmed, produces scope nobody asked for and consumes
  review attention on tone rather than a request. One observed run: a single sentence of owner frustration about
  one surface produced several parallel lanes touching unrelated files the owner had not asked to change, and the
  owner's next message asked why that work existed. Before spawning a lane from a complaint, restate it as a
  proposed, scoped ask (what would change, how big) and get explicit confirmation, or file it as a candidate
  backlog item for later triage — never both silently assumed and silently executed. Only a stated request, or an
  explicitly pre-approved standing category of fix, authorizes a spawn without that round-trip. *Worked example:*
  "the dashboard feels sluggish" is filed as a candidate backlog item with a note to profile it, not spawned as an
  immediate multi-lane performance sweep.
- **Don't spawn a measurement or audit lane unless a decision is already waiting on its number.** Measuring feels
  like useful, low-risk groundwork, but a lane that counts, inventories, or scores something nobody will act on
  consumes lane budget, review attention, and — for anything touching a running app — real machine load for no
  decision it changed. Before spawning a standalone measurement/audit lane, name the pending decision and the
  two-plus actions that would follow from a high versus low result; if none exists, don't spawn it, or fold the
  measurement into the work that will act on the answer. *Worked example:* "let's just check how many components
  use pattern X" is declined for lack of a named decision; "how many use pattern X, because above our stated
  threshold we budget a codemod lane, otherwise we leave it" is run, because the threshold decision is already
  stated. **Carve-out: standing/required audits (security, privacy gate, owner-requested) run regardless of a
  named pending decision** — they exist to catch what nobody is yet asking about, and this rule never skips them.

## Standards (by name; verify a figure/URL before citing one)
GTD capture/clarify; incident command (single commander, unity-of-command,
activity log); emergency-severity triage; WIP limits; "the ONE thing";
psychological reactance; motivational-interviewing reflective listening;
orchestrator–worker delegation and its token-cost trade-offs. Named leads —
fetch and log a source before citing a specific figure (repo convention).
