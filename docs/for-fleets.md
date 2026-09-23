# Perun for agent fleets

**If you run several agents in parallel, install the delivery overlay and wire
the gates: `./install.sh --full --with-gates /path/to/project`, plus
`--with-ceo` for the owner task ledger.** Each rule below is a script with an
exit code, so a lane that breaks it is stopped rather than reminded. Every
script below runs its own self-test (`--selftest`) in this repository's CI.
What Perun is: [the README](../README.md). Basic install:
[`getting-started.md`](getting-started.md).

## What `--with-gates` writes

| File | What it does |
|---|---|
| `.github/workflows/dcr-gates.yml` | Runs the gates on push and PR. Edit the trigger branch if your default branch isn't `main`. |
| `scripts/dcr-gates.sh` | Calls the gate scripts inside the installed skills; holds no copy of their logic, so re-running `install.sh` upgrades the checks. |
| `.githooks/pre-push` | Reruns your fast lint + unit tier (`DCR_PREPUSH_CMD`) before each push. Off until you run `git config core.hooksPath .githooks`. |

It never overwrites an existing file at these paths; it writes `<path>.new`
instead. Always on: `fix_class_gate.py` (every `fix:` commit touches a pinned
test or carries a `No-Test-Reason:` trailer) and `binaries_gate.py` (no
committed screenshots, archives, or build output). The `DCR_*` flags below are
opt-in and off by default; the header of `scripts/dcr-gates.sh` documents each
flag's inputs (for example, `DCR_FOCUS_GATE` needs `DCR_OWNER_EMAIL` from
protected CI config). A flag set without its skill installed fails, never
skips.

## Mechanisms

| Need | Script | Blocks or reports | Switch on |
|---|---|---|---|
| Short subagent handbacks | `agentic-delivery/scripts/handback_cap.py` | A subagent's final chat message over 800 characters or 10 lines (defaults; `HANDBACK_MAX_CHARS`, `HANDBACK_MAX_LINES`). The subagent is sent back to shorten it, not killed. | `SubagentStop` hook in `.claude/settings.json`; `install.sh --with-gates` prints the snippet. |
| Stay on the owner's priority | `agentic-delivery/scripts/focus_gate.py` | Work outside an owner-committed `.claude/PRIORITY.md` until its acceptance command passes on a clean checkout, or the priority is blocked on another party with evidence. Agent-written or over-broad records are rejected. | `DCR_FOCUS_GATE=1` |
| No cosmetic work over an aged P0 | `agentic-delivery/scripts/priority_gate.py` | A presentation-only PR while an aged priority issue has no PR citing it. | `DCR_PRIORITY_GATE=1` |
| Stop re-fixing the same file | `agentic-delivery/scripts/refix_gate.py` | Re-touching a file a `fix:` commit touched in the last 72 hours (default) without a test or eval change or a `Refix-Reason:` trailer. | `DCR_REFIX_GATE=1` |
| Closing keywords stay in scope | `deep-code-review/scripts/closes_lint.py` | A `closes #N` for an issue or PR the change doesn't own. | `DCR_CLOSES_LINT=1` |
| Keep every owner ask | `agentic-ceo/scripts/task_ledger.py` | One `.claude/TASKS.md` per project: asks verbatim, `done` needs evidence (sha, URL, `#N`, or test id), `next` returns one item, `reconcile` finds asks lost to compaction. | Run by the conductor (`--with-ceo`). |
| One requirement list across sources | `agentic-delivery/scripts/feedback_ledger.py` | Merges feedback exports, doc comments, transcripts, and design exports; turns each disagreement into an owner question; never decides. | Run on demand. |
| Isolated lanes | `agentic-delivery/scripts/lane_guard.py` | A write-lane not in its own linked worktree on its expected branch, or sharing it with another live process. | First step of every write-lane. |
| No double-claimed work | `agentic-delivery/scripts/claim_probe.py` | Starting an item that overlaps an open PR, branch, or live claim; crossed claims resolve to the earliest. | Before each claim. |
| Coordination board | `agentic-delivery/scripts/board_post.py`, `board_sync.py`, `board_state.py` | Typed, capped, privacy-linted posts on one issue; read from a per-agent cursor; render current state into the issue body. | Per the delivery skill. |
| Parallel test runs | `agentic-delivery/scripts/serial_gate.py` | Path-scoped test selection that falls back to the full suite when unsure, plus a kernel lock for shared-state steps. | Per lane. |
| Is a quiet lane alive? | `agentic-delivery/scripts/lane_liveness.py` | Reports liveness from positive evidence; never issues a kill verdict. | On demand. |
| Returning reviewer | `agentic-delivery/scripts/review_digest.py` | A change digest since the last review, instead of a full re-read. | On demand. |
| "Deployed" means deployed | `agentic-delivery/scripts/surface_check.py` | A done/deployed claim whose running build id doesn't match the sha; a failed check is `COULD_NOT_CHECK`, never a pass. | Before claiming done. |

Paths are relative to `.claude/skills/` in the installed project. Each script
documents itself in its header and prints usage with `--help`.

## Keep token cost down

- Brief lanes to a one-line handback (`status | evidence | next`) with the
  deliverable in a file; the cap above is the backstop.
- Apply the Claude Code settings that cut per-turn tokens (Bash output cap,
  skill-listing budget, subagent prompt cache), documented with starting values
  in [`host-enforcement.md`](../.claude/skills/agentic-delivery/references/host-enforcement.md).
- Load only the skills a lane needs. Each skill's `SKILL.md` routes to its
  references on explicit triggers, so a lane that doesn't hit a trigger never
  reads that depth.

## Where the doctrine lives

- Parallel sessions, claims, and the board:
  [`multi-session-coordination.md`](../.claude/skills/agentic-delivery/references/multi-session-coordination.md)
- Running without an owner present:
  [`unattended-operating-mode.md`](../.claude/skills/agentic-delivery/references/unattended-operating-mode.md)
- Proving a handback's claims:
  [`verification-handback.md`](../.claude/skills/agentic-delivery/references/verification-handback.md)
- Lane speed and handback size:
  [`fast-agentic-delivery.md`](../.claude/skills/agentic-delivery/references/fast-agentic-delivery.md)
