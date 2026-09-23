# Lane preamble — paste into every lane brief

Fill `<angle-bracket>` placeholders before pasting. Every rule below is a hard
default for this lane, not a suggestion.

## Identity & isolation
- First command: `python3 .claude/skills/agentic-delivery/scripts/lane_guard.py --expect-branch <branch>`. Refusal → stop; hand back the `LANE_GUARD REFUSE:` line plus changed files.
- One writer per worktree. Never bare `git stash` (stack is shared — use a WIP commit instead). Never `--no-verify`. Never force-push without an owner-authored grant on file.

## Scope
- Before editing: `python3 .claude/skills/agentic-delivery/scripts/focus_gate.py check --item <issue>` and `python3 .claude/skills/agentic-delivery/scripts/claim_probe.py --repo <owner/name> --issue <issue> --ref '#<issue>' --paths <glob>`.
- Any ask outside this brief's scope: `python3 .claude/skills/agentic-ceo/scripts/task_ledger.py add --ask "<text>"` — never a private note or a silent scope-creep edit.

## Communication
- Caveman ultra in chat/reasoning: terse fragments, no filler/hedging/pleasantries. Code, commits, and docs stay normal prose.
- NO POLLING. Never sleep/loop waiting on background work — end the turn and wait for the notification instead.
- Final message is one line: `status | evidence | next`. Deliverables (code, reports, findings) live in files; never paste them into chat.
- Board posts only through `python3 .claude/skills/agentic-delivery/scripts/board_post.py --repo <owner/name> --issue <issue> --type <CLAIM|RELEASE|HANDOFF|BLOCKER> ...` — typed posts, never free-form chat to a shared board.

## Verification
- No "done" without evidence: a test id, an exact sha, or a file path — never a bare assertion.
- Deployed/served claim: `python3 .claude/skills/agentic-delivery/scripts/surface_check.py served --url <url> --expect-sha <sha> ...`.
- CI-checks claim: `python3 .claude/skills/agentic-delivery/scripts/surface_check.py checks --gh-repo <owner/name> --sha <sha> ...`.
- Design port: `python3 .claude/skills/deep-code-review/scripts/parity_differ.py --design <design-file> --app <app-file>` — report the inventory MATCH/gap it prints, never a size measured by hand. Use the `<design-lane>` agent type, if this host defines one, for design ports.

## Stop conditions
- Blocked: record the block and the next item; don't retry the same fix a third time.
- Destructive or external action (force-push, deploy, secrets/IAM, external send, mass delete): gated — ask the owner, don't act.
