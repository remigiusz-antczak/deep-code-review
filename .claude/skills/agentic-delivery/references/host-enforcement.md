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
(`--selftest`) requires `--expect-branch` (`--allow-any-branch` waives it, never in a lane brief),
prints one quotable `LANE_GUARD REFUSE:` line and exits non-zero unless the cwd is a linked worktree
on exactly that branch and it is not a default one (origin/HEAD's target, `main`, `master`, or the
main checkout's branch). At that refusal, or any later git or file-write refusal, the lane stops and
hands back the line plus its changed files; any other missing control narrows only the dependent
action (above). The brief names the dodges as out of bounds, own branch
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
content into chat. **The default handback is one line:** `status | evidence |
next` (verdict; branch/SHA, gate results, or file paths as the checkable
evidence; the next action or open issue) — key=value or short fields, never
prose. **No polling.** Never sleep/loop waiting on background work in a
subagent turn — end the turn and let the notification resume it; a poll loop
bills chat narration nobody reads, the same waste this cap targets. The 800-char/10-line hook below is the **backstop** that catches a
drift back to narration; it is not itself the target shape, and passing it
is not a substitute for actually being one line. The orchestrator never
relays a subagent's prose; it reads the fields and the named files.

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
inspects tools, so a custom read-only review lane is capped by default too;
releases after 3 blocks per agent so it never loops forever. `--selftest`
proves it fires.

**A harness with no report file** (a review lane's findings ARE its chat
answer) still needs a cap — never exempt it: exempt means uncapped, which
reopens the cost problem. Raise the cap for that agent type only, via a
second, `matcher`-scoped `SubagentStop` entry with env overrides:

```json
{ "matcher": "security-reviewer", "hooks": [{ "type": "command",
    "command": "HANDBACK_MAX_LINES=25 HANDBACK_MAX_CHARS=2000 python3 .claude/skills/agentic-delivery/scripts/handback_cap.py" }] }
```

## Subagent model + cache-TTL pin (a Host-enforced instance, Claude Code)

A CLAUDE.md line telling every subagent "default to the cheapest tier" is
**Protocol** only — a subagent's own `model:` frontmatter still wins over it.
On Claude Code, `CLAUDE_CODE_SUBAGENT_MODEL` (an alias or model ID) plus
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` in `settings.json`'s `env` block is
**Host-enforced** instead (v2.1.257+): every subagent, teammate, and workflow
agent's `model:` field (built-in Explore and Plan included) is ignored and they
run on the named model; with only `FORCE` set, on the main conversation's
model. Exceptions to declare: a fork, and a skill run in a subagent with
`model: inherit`, still run on the main conversation's model; with only
`FORCE` set, built-in Explore keeps its cap (Opus, on the Claude API).

Cache lifetime is the sibling spend control. Defaults: on a Claude subscription
within plan usage, the main conversation gets `1h` and every other request
(subagents, workflows, teammates, forks, compaction) `5m`, except a few
server-controlled helper requests (`1h`); on usage credits, an API key, or a
cloud provider, both get `5m`. Pins take `5m`/`1h` (v2.1.242+): the main
conversation's `promptCacheTtl` setting / `CLAUDE_CODE_PROMPT_CACHE_TTL` env
var, everything else's `subagentPromptCacheTtl` / `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL`.
First match wins: `FORCE_PROMPT_CACHING_5M=1` (both buckets) → the bucket's env
var → its setting → a subagent's own `experimental.cacheTtl` frontmatter
(v2.1.248+; `1h` ignored while a subscription is on usage credits) →
`ENABLE_PROMPT_CACHING_1H=1` (both buckets) → the bucket default. The
frontmatter is per-agent (Protocol); the other-requests env/setting pin or
`FORCE_PROMPT_CACHING_5M` overrides it.
Declare which control is set, and its bucket default.

```json
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "haiku",
    "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1",
    "CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL": "1h"
  }
}
```

## Per-turn token levers (a Host-enforced instance, Claude Code)

Five `settings.json` keys cut what reaches context every turn — the host
clamps or truncates before Claude ever sees the excess, so a worker cannot
prompt its way past them (Host-enforced by the ladder above). Verified
against `settings-reference.md` / `tools-reference.md`
(`docs/standards-index.md`, 2026-09-23).

| Setting | Saves | Start at | Trade-off |
|---|---|---|---|
| `bashOutputMaxChars` | Inline chars of a *successful* Bash/PowerShell result; unset = ~30,000 inline, clamped 4,000–128,000 (v2.1.261+) | `10000` | Overflow lands in a session-dir file plus a 2,000-char preview — Claude must `Read` it back when it needs the tail |
| `skillListingMaxDescChars` | Chars of each skill's `description`+`when_to_use` resent every turn; default `1536` | `300` | A cut mid-sentence can drop the phrase that would have triggered auto-invocation of a rarely-used skill |
| `skillListingBudgetFraction` | Listing size as a fraction of the context window; default `0.01` (1%); over budget, Claude Code drops descriptions (names survive) of the least-used skills first | keep `0.01` unless 50+ skills are installed | Lower it and fewer full descriptions survive, so Claude self-selects an idle skill less often |
| `skillOverrides` | Whole skill entries — `"name-only"` drops the description, `"user-invocable-only"` hides from Claude but keeps `/name`, `"off"` hides both | `"name-only"` on every skill irrelevant to this project | Miscalled on a skill Claude actually needed, it never self-invokes; only above `"off"` does `/name` still work |
| `subagentPromptCacheTtl` | Cache write/read cost across a subagent's own turns and resumed runs (not the per-turn caps above); unset → `5m` (subagents sit outside the main-conversation bucket even on a subscription) | leave `5m` for one-shot subagents | `1h` writes at the higher cache-write rate — pays off only if that subagent is reused inside the hour, else pure loss |

`CLAUDE_CODE_SUBAGENT_MODEL` (+`_FORCE`) is the sibling model-pin lever —
see "Subagent model + cache-TTL pin" above; not restated here.

```json
{
  "bashOutputMaxChars": 10000,
  "skillListingMaxDescChars": 300,
  "skillOverrides": { "<skill-irrelevant-to-project>": "name-only" },
  "subagentPromptCacheTtl": "5m"
}
```
