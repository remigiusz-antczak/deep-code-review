# Lane preamble — paste into every lane brief

Fill `<angle-bracket>` placeholders before pasting. Every rule below is a hard
default for this lane, not a suggestion.

## Identity & isolation
- First command: `python3 .claude/skills/agentic-delivery/scripts/lane_guard.py --expect-branch <branch>`. Refusal → stop; hand back the `LANE_GUARD REFUSE:` line plus changed files.
- One writer per worktree. Never bare `git stash` (stack is shared — use a WIP commit instead). Never `--no-verify`. Never force-push without an owner-authored grant on file.

## Scope
- Before starting: `python3 .claude/skills/agentic-delivery/scripts/focus_gate.py check --item <issue>`, then `python3 .claude/skills/agentic-delivery/scripts/claim_probe.py --repo <owner/name> --issue <issue> --ref '#<issue>' --paths <glob> --agent <agent-id> --claim --post` (checks and, only on GO, posts the CLAIM in one call) — abort if it prints NO-GO (a YIELD readout is always also NO-GO).
- Any ask outside this brief's scope: `python3 .claude/skills/agentic-ceo/scripts/task_ledger.py add --ask "<text>"` — never a private note or a silent scope-creep edit.

## Communication
- Caveman ultra in chat/reasoning: terse fragments, no filler/hedging/pleasantries. Code, commits, and docs stay normal prose.
- NO POLLING. Never hand-roll a sleep/loop waiting on background work; use the bounded wait below.
- Never end your turn with background jobs running (browser tests, builds; kill your own dev servers): `python3 .claude/skills/agentic-delivery/scripts/lane_guard.py wait --pid <pid> --port <port> --file <output> --timeout <s> && lane_guard.py handback …`. `COULD_NOT_CHECK` → hand back what is still running, not "waiting".
- Final message is one line: `status | evidence | next`. Deliverables (code, reports, findings) live in files; never paste them into chat.
- Board posts only through `python3 .claude/skills/agentic-delivery/scripts/board_post.py --repo <owner/name> --issue <issue> --type <CLAIM|RELEASE|HANDOFF|BLOCKER> ...` — typed posts, never free-form chat to a shared board.

## Verification
- No "done" without evidence: a test id, an exact sha, or a file path — never a bare assertion.
- Parked/handback claim: `python3 .claude/skills/agentic-delivery/scripts/lane_guard.py handback --sha <sha> --base <dispatch-base> --branch <branch> --cite <path> --artifact-root <dir>` (one `--cite` per committed evidence file; absolute artifacts must sit under `--artifact-root`). A refusal means not parked.
- Deployed/served claim: `python3 .claude/skills/agentic-delivery/scripts/surface_check.py served --url <url> --expect-sha <sha> ...`.
- CI-checks claim: `python3 .claude/skills/agentic-delivery/scripts/surface_check.py checks --gh-repo <owner/name> --sha <sha> ...`.
- Design port: `python3 .claude/skills/deep-code-review/scripts/parity_differ.py --design <design-file> --app <app-file>` — report the inventory MATCH/gap it prints, never a size measured by hand. Use the `<design-lane>` agent type, if this host defines one, for design ports.

## Stop conditions
- Tool-call budget: at most `<tool-call cap>` tool calls (150 is a starting value; tune it from `python3 .claude/skills/agentic-ceo/scripts/token_report.py --budget`). At the cap, commit work in progress and hand back `BLOCKED | budget | <what remains>` instead of continuing.
- Blocked: record the block and the next item; don't retry the same fix a third time.
- Question for an absent owner: `python3 .claude/skills/agentic-ceo/scripts/task_ledger.py defer --id <T-###> --question "<q>" --default "<choice taken>"`, state the default in your handback, then continue with `task_ledger.py next`. Human-gate (shared push, deploy, external send, secret/scope change) or destructive/irreversible without a standing grant: never default, always `--park`. Never idle waiting for an answer.
- Destructive or external action (force-push, deploy, secrets/IAM, external send, mass delete): gated — ask the owner, don't act.
