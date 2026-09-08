# Model-tiering & cost-efficiency

Read this when choosing which model tier a fan-out unit, a delivery lane, or an
`idea-critic` hat runs on — or when reviewing a target's own LLM-call cost
posture (domain E, cross-ref `security-ai-agents.md`'s LLM10 Unbounded
Consumption). Written vendor-neutral first: `parallel-audit.md` already
maintains a host matrix (Cursor, Codex, Copilot, Gemini, Aider, one-shot paste),
so the rubric below has to survive outside any one vendor. A Claude-family
worked example follows because it is the best-evidenced case and the host this
skill runs on most often.

---

## The three tiers (vendor-neutral)

**Default and ceiling.** Default every task or lane to the cheapest tier that
clears its own gate; promote only on evidence — a failed cheap attempt, or a
stated high-blast decision — never start at frontier for routine work. State a
reason before exceeding frontier/reasoning-class for anything short of the
lead-verify and adversarial-design work the mapping below names; an unstated
escalation is a budget drain, not a judgment call.

| Tier | Use for | Claude-family analogue |
|---|---|---|
| **Fast/cheap** | Classification, extraction, candidate-sweep enumeration (Tier 1 of a fan-out — `parallel-audit.md`), mechanical formatting, single-grep-shaped invariant checks | Haiku-class |
| **Mid/balanced** | Everyday implementation, Tier-2 confirm-on-survivors, most Builder-hat work, routine QA | Sonnet-class |
| **Frontier/reasoning** | Planning and synthesis (Conductor), architecture and adversarial design, lead re-verify on anything that could become Blocker/Critical, high-blast `idea-critic` hats, long-horizon multi-hour autonomous work | Opus-class / extended-thinking-class |

## The levers, in the order the evidence favors reaching for them

Every lever below has a measured before/after number behind it (Claude
cost-optimization guidance, `docs/standards-index.md`); the *shape* of each
lever — a reasoning-effort knob, a cacheable stable prefix, an async/unattended
queue, a budget ceiling, escalate-on-failure, model swap last — applies to any
provider with an equivalent primitive, even where the exact mechanism differs.

1. **Tune effort/reasoning-depth before switching models — where the host
   exposes the knob.** Not every host in `parallel-audit.md`'s own matrix
   (Copilot, Gemini, Aider, one-shot paste) exposes one, so this lever silently
   no-ops on some of them — check for it before relying on it. Where it exists,
   tuning effort down often costs little quality for real savings on knowledge
   work, and the tradeoff stays favorable at a middle setting even on
   long-horizon coding. Same-model, zero-architecture change — try it first.
2. **Turn on prefix/prompt caching before any other lever.** An agentic task
   resends its whole growing conversation every turn, so cost grows roughly with
   the square of turn count; a cached prefix is billed far below fresh input.
   Cache reads are routinely the largest single component of task cost — worth
   more than most model-choice decisions. `parallel-audit.md` §1's "assemble the
   shared context packet once, hand it to every subagent" is already a stable,
   reused prefix by construction; mark it cacheable rather than re-deriving it
   per unit.
3. **Batch anything unattended.** A flat, large discount on every token
   (cached tokens included) in exchange for async turnaround is the
   second-largest free lever after caching for work no one is waiting on —
   evaluation runs, backfills, scheduled jobs, and a `FULL` review's Tier-1
   candidate sweep are exactly this shape.
4. **Escalate-on-failure instead of running everything at full strength.**
   Running cheap first and only re-running failures at full strength reaches the
   same pass rate for roughly half the cost of running everything strong from
   the start — this is precisely what `parallel-audit.md`'s Tier-1→Tier-2 split
   already does at the *effort* level; do it at the *model* level too (Tier 1 on
   fast/cheap, promote only survivors to Tier 2 on mid/frontier).
5. **Set a per-lane token budget sized to observed usage, then tighten.** A
   generous budget still cuts cost meaningfully; a tight one cuts more, for a
   real but bounded quality cost — start near a loop's 90th-percentile usage,
   then tighten. This is the concrete mechanism behind `agentic-delivery`'s G2
   spend-cap gate: a number, not just a price label.
6. **Escalate to a stronger model for one hard decision, not the whole task —
   and prompt for a bounded consult rate.** A cheap executor calling a stronger
   advisor mid-task for specific hard decisions measurably improves accuracy for
   a fraction of running the advisor's model the whole time — but only when
   consultation stays rare (on the order of a couple of calls per task); consult
   on nearly every step and the pairing costs several times more for no quality
   gain. This is the lighter alternative to a fully independent `idea-critic`
   session for low-to-medium-blast decisions — see that skill's Independence
   step for when a full second session is required instead.
7. **Only then, swap the whole task to a stronger model — and judge it by cost
   per *solved* task, never cost per token.** A pricier-per-token model at
   modest effort can solve meaningfully more tasks for *less* total cost than a
   cheaper model that fails more often; on harder tasks this gap widens, because
   pass rate rises faster than price across model generations.

## Two negative results to guard against explicitly

- **Don't fan out or delegate when the work is one dependent chain or fits a
  single context.** An orchestrator earns its cost only when there is real bulk
  to hand off — the plan, handoff, and merge it requires are free to a single
  model on anything smaller, and on hard non-bulk work a solo model has been
  measured to beat the coordinator outright at meaningfully lower cost. This is
  the don't-start threshold `parallel-audit.md`'s stop rule is missing the
  complement of — see that file's Tier section.
- **Don't over-consult an advisor.** Consulting on nearly every turn degenerates
  the pairing into "run the frontier model for the whole task, plus overhead" —
  measured at several times the cost for no quality gain. Prompt the executor
  for a bounded cadence (on the order of one consult before substantive work and
  one before finishing), not a per-turn habit.

## Mapping onto this skill's own units and hats

| Unit | Recommended tier | Rationale |
|---|---|---|
| Fan-out Tier-1 candidate sweep (`parallel-audit.md`) | Fast/cheap, batched if the whole run is unattended | Enumeration only, no proof required — the whole point of Tier 1 |
| Fan-out Tier-2 confirm + fix-against-suite | Mid | Needs real code judgment but bounded to one invariant + its tests |
| Lead re-verify / `CONFIRMED` promotion / top-N blast-radius independent read | Frontier — never delegate | Highest consequence of being wrong; this is the report's authority |

If the `agentic-delivery` and `idea-critic` overlays are installed, the same
tiers extend to their units — see `roles.md`'s roster and `idea-critic`'s
Independence step for where each hat sits; do not restate that mapping here.

---

Cross-references: the fan-out mechanics and Tier-1/Tier-2 split this file
extends live in `parallel-audit.md`; the LLM-cost attack surface (unbounded
consumption) this file's tiering discipline mitigates lives in
`security-ai-agents.md`; verified sources and fetch dates in
`docs/standards-index.md`.
