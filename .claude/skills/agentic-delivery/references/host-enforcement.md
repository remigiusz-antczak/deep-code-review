# Host capability & enforcement contract

**Read this when** claiming that state, permissions, or spend are *enforced*
rather than merely followed, or when designing a host adapter for this overlay.
This file is a claim-honesty framework and an optional interface; **no hook,
sandbox, budget service, or durable runtime ships with these instructions.** It
applies `SKILL.md` principle 3 (evidence and permission are separate; a check
that could not run is `UNVERIFIED`, never a pass) to the coordination layer
itself.

## Claim only the level you observed

Three levels, and a markdown instruction or an unused example hook never reaches
the third:

| Level | What supports the claim | What it cannot establish |
|---|---|---|
| **Protocol** | The agent follows the skill and records its decisions/receipts | Cannot itself prevent bypass, lost state, a forbidden action, or overspend |
| **Validated artifact** | A named validator checks a specific schema/invariant against a pinned artifact, and its actual result is recorded | Shape validity is not receipt truth, live behaviour, or action authorization |
| **Host-enforced** | A tested adapter intercepts the real action boundary and denies disallowed actions using policy/state the worker cannot edit | Covers only the tested events/actions/host versions; other paths stay protocol-only |

Declare capability **per control** (state, permission, spend, isolation, model
choice, receipt capture), not once for a whole host. Record host + version, the
date observed, the level, the probe evidence, and the paths still unsupported. A
skill directory, a model name, a worktree, or a hook *example* is not evidence of
enforcement. Probe the actual tool/auth/model-control availability; label
inherited or unavailable controls as such, and **fail or narrow the dependent
action when a required control is absent** — never convert an unavailable check
into a pass or into authority.

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
