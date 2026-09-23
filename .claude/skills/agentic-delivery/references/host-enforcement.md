# Host capability & enforcement contract

**Read this when** claiming that state, permissions, or spend are *enforced*
rather than merely followed, briefing a worktree-isolated write-lane, or
designing a host adapter for this overlay.
A claim-honesty framework plus an optional interface: **no sandbox, budget
service, or durable runtime ships here** (only the two scripts named below). It
applies `SKILL.md` principle 3 (a check that could not run is `UNVERIFIED`,
never a pass) to the coordination layer itself.

## Claim only the level you observed

Three levels, and a markdown instruction or an unused example hook never reaches
the third:

| Level | What supports the claim | What it cannot establish |
|---|---|---|
| **Protocol** | The agent follows the skill and records its decisions/receipts | Cannot itself prevent bypass, lost state, a forbidden action, or overspend |
| **Validated artifact** | A named validator checks a specific schema/invariant against a pinned artifact, and its actual result is recorded | Shape validity is not receipt truth, live behaviour, or action authorization |
| **Host-enforced** | A tested adapter intercepts the real action boundary and denies disallowed actions using policy/state the worker cannot edit | Covers only the tested events/actions/host versions; other paths stay protocol-only |

Declare capability **per control** (state, permission, spend, isolation, model
choice, tool/capability access, receipt capture), not once for a whole host. Record host + version, the
date observed, the level, the probe evidence, and the paths still unsupported. A
skill directory, a model name, a worktree, or a hook *example* is not evidence of
enforcement. Probe the actual tool/auth/model-control availability; label
inherited or unavailable controls as such, and **fail or narrow the dependent
action when a required control is absent** — never convert an unavailable check
into a pass or into authority.

A prompt-level "do not use tool X" is a **protocol** control only — instructions are not a sandbox.
The **host-enforced** form spawns the worker with an allowed-tools set that excludes X (or denies it
at the execution boundary); the protocol fallback audits the receipt's tool calls afterward. Declare
tool access at the level you can enforce; narrow the dependent action when only the prompt exists.

## Isolated write-lanes: guard first, stop at the first refusal

Isolation is a control too: a lane that lost it writes a shared tree. A write-lane brief's first
command is `git rev-parse HEAD && python3 .claude/skills/agentic-delivery/scripts/lane_guard.py
--expect-branch <branch>` — the direct read probes any command-wrapping hook; `lane_guard.py`
(`--selftest`) prints one quotable `LANE_GUARD REFUSE:` line and exits non-zero unless the cwd is a
linked worktree on the expected, non-default branch. At that or any later refusal the lane stops and
hands back the line plus its changed files. The brief names the dodges as out of bounds, own branch
included: an absolute binary path, a wrapper (`env`, `sh -c`, a script), a subshell — all
permission-laundering (`multi-session-coordination.md`). The orchestrator audits live processes
(`pgrep -fl 'git push'`), not only lane reports. Without host isolation, the orchestrator makes each
worktree (`git worktree add`) and spawns the lane there, confined by the brief; blocked work is
re-shipped by a fresh lane in a fresh worktree, never salvaged via git in the blocked tree. Each
receipt records its isolation mode (host / orchestrator-worktree).

## Optional adapter interface (proposed, not shipped)

If a host exposes the events, an adapter normalizes only those it actually has;
missing events stay explicit gaps.

| Event | Required adapter behaviour |
|---|---|
| Session start / resume / checkpoint | Load and write the project record (`project-state.md`); reconcile live owners and unknown effects before admitting any retry |
| Task dispatch / completion | Bind owner, scope, dependencies, and budget; capture the real tool/artifact receipt separately from the worker's own summary |
| Before a paid or consequential action | Check current authority, required evidence, state revision, and the resource bound; reserve capacity atomically before admitting the action |
| Result / failure / cancellation | Observe the actual result and usage; reconcile the reservation; record pending/unknown effects; keep failed-attempt costs |
| Objective / permission change | Invalidate affected queued work and stale grants; cancel where supported and reconcile in-flight effects |

Reservations must cover outstanding work **plus** the next permitted call
(tool/provider charges included); deny admission if the bound cannot hold. An
estimate with no bounded call or stop mechanism is not a hard cap. A cancellation
*request* is not proof of cancellation — hold the reservation for unknown or
in-flight charges until the status is observed, and record overshoot honestly.
Replay must deduplicate by event identity while re-checking permission afresh: a
duplicate receipt must never bill or publish twice.

Protect policy, grants, counters, and receipt sources from the worker they
constrain; scope credentials at the real execution boundary — ordinary worktree
isolation and model instructions are **not** a security sandbox. For every
receipt, name its trust boundary (a provider/runner observation versus the
agent's own assertion).

**Before raising a claim to host-enforced,** exercise allow/deny,
malformed/stale events, replay, crash-after-effect, cancellation, revoked
authorization, and missing-hook cases, and record the observed result for that
host version and covered path. Downgrade the claim where support is missing;
never assert a cross-host conformance result you did not observe.

## Subagent handback: fields-only, mechanically capped (a Host-enforced instance)

Chat narration a subagent hands back to its caller is billed output nobody
re-reads — `fanout-host-sizing.md`'s cost argument, made a **hook** here
instead of a prompt instruction alone (a prompt-level "keep it short" stays
Protocol above, never Host-enforced). The cap is on **chat narration only**:
deliverables (code, reports, long findings) go in files, which are
uncapped — a compliant handback names the file path instead of pasting its
content into chat. A handback is **fields-only**: verdict, branch/SHA, file
paths, gate results, open issues, as key=value or short lines. The
orchestrator never relays a subagent's prose; it reads the fields and the
named files.

Install (`SubagentStop`; no `matcher` runs on every agent, a `matcher` scopes
it to named agent types):

```json
"hooks": {
  "SubagentStop": [
    { "hooks": [{ "type": "command",
        "command": "python3 .claude/skills/agentic-delivery/scripts/handback_cap.py" }] }
  ]
}
```

`scripts/handback_cap.py` — **use this when** a subagent's chat handback is
landing in an orchestrator's context uncapped. Stdlib-only; blocks (exit 2,
which per the host's docs continues the subagent instead of stopping it, so no
work is lost) a chat handback over 800 chars / 10 lines; exempts only agent
types named in `HANDBACK_EXEMPT_TYPES` (default: 4 built-in types) — it never
inspects tools, so add a custom read-only review lane's type there; releases
after 3 blocks per agent so it never loops forever. `--selftest` proves it fires.

## Subagent model + cache-TTL pin (a Host-enforced instance, Claude Code)

A CLAUDE.md line telling every subagent "default to the cheapest tier" is
**Protocol** only — a subagent's own `model:` frontmatter still wins over it.
On Claude Code, `CLAUDE_CODE_SUBAGENT_MODEL` (an alias or model ID) plus
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` in `settings.json`'s `env` block is
**Host-enforced** instead: with both set, every subagent, teammate, and
workflow agent runs on the named model regardless of its own `model:`
frontmatter; with only the `FORCE` var set, they run on the main
conversation's model (requires Claude Code v2.1.257+).

Cache lifetime is the sibling spend control, same enforcement split: the main
conversation's `promptCacheTtl` setting or `CLAUDE_CODE_PROMPT_CACHE_TTL` env
var, and every other request's (including subagents') `subagentPromptCacheTtl`
setting or `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` env var, pin a `5m`/`1h`
cache TTL bucket at the host level (both require v2.1.242+); a single
subagent can instead opt into its own TTL via `experimental.cacheTtl` in its
own frontmatter (v2.1.248+; per-agent, so it is Protocol, not Host-enforced,
unless the host-level setting also constrains it). Declare which of the three
is actually set — an undeclared default silently runs the 5-minute floor.

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "haiku",
    "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1",
    "CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL": "1h"
  }
}
```
