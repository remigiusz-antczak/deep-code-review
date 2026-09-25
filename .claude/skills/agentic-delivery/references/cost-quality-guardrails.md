# Cost vs quality guardrails

Read this when a change cuts cost — a cheaper model tier, a lane or tool-call
cap, a must-load section moved behind a trigger, fewer review hats — or when
dispatching or reviewing a lane whose model and reviewer depend on the paths it
touches, or when judging whether a past cost cut let a defect escape.

**Bottom line.** Cut spend where it buys nothing; never cut the checks that
catch defects. Every cost cut ships with a deterministic mechanism that proves
quality held, and any escaped Blocker traced to a cut reverts that cut. The
four mechanisms below are free to run (git, grep, and hooks; no paid calls).

| Guardrail | Mechanism | Fails when |
|---|---|---|
| Review tiers | `templates/review-tiers.tsv` + `scripts/tier_gate.py` | a tier-1 commit lacks `Model: opus` or an independent, receipted `Reviewed-By:`; a tier-2 commit lacks the reviewer trailer; with `--github`, a tier-1/2 PR has no APPROVED review from another login |
| Lane caps | `scripts/lane_cap.py` (PostToolUse) + `scripts/handback_cap.py` (SubagentStop) | with `HANDBACK_REQUIRE_STATUS=1`, a handback carries no status (blocked); the cap itself only injects a checkpoint, never blocks |
| Must-load cuts | `scripts/floor-anchors.tsv` + `scripts/trigger_lint.py`, both run by the suite repository's `scripts/test-ci-gates.sh` | a floor rule's heading or body anchor is empty or gone; a routed reference loses its trigger or its router row shares fewer than two words with it |
| Escaped defects | `Regression-Of:` / `Cost-Cut:` trailers + `scripts/escaped_defects.py` | an escaped Blocker traces to a cut; two cuts share one window; a cut lands inside the baseline |

## 1. Review tiers — one list for dispatch and review

The dispatcher is often a cheaper model classifying its own work, with a cost
incentive to call it minor. So the tier comes from paths, not judgment: one
checked-in file, `templates/review-tiers.tsv`, maps path globs to tiers. The
dispatch step and the review step both read it; no second list exists.

- **Tier 1** — security, enforcement, gates, hooks, skill prose (in a skill
  repo the prose *is* the behavior), agent instructions, merge-ready logic,
  data-loss paths. Runs on the strongest allowed model and needs an
  independent reviewer.
- **Tier 2** — feature code, and any path no row matches. Default model tier;
  independent reviewer.
- **Tier 3** — documentation outside the skill and hook directories. The
  author may self-review.

A path matching several rows takes the strictest tier, so a skill reference
that also matches `*.md` stays tier 1. Globs for short words are anchored to a
boundary (`/`, `_`, `-`, `.`), so `gate` does not catch `delegate`, `auth` does
not catch `author`, and `merge` does not catch `emergency`. Agent definitions
(`.claude/agents/`), slash commands (`.claude/commands/`), and each skill's
`INDEX.md` routing table are tier 1 too. Dispatch: run
`python3 scripts/tier_gate.py --classify <changed paths>` and pick the model
from the `strictest` line. Review: the commit (or squash) carries the
trailers, and `python3 scripts/tier_gate.py <base>..<head>` gates every
first-parent commit in the range, merge commits included (judged by their diff
against the first parent) — exit 1 on any failing commit, exit 2 when the tiers
file or range is unreadable (fail closed); `--advisory` prints the same
findings and exits 0. `TIER_STRONG_MODELS` (comma-separated, default `opus`)
names the models that satisfy tier 1.

The reviewer trailer is `Reviewed-By: <id> receipt:<ref>`. The id (with any
`<email>` removed) must differ from both the author and the committer, and no
email in it may be theirs. The receipt must exist: a path committed in that
commit or at HEAD, a commit sha in the repository, or a GitHub pull-request
review or comment URL that `gh api` can fetch (without the GitHub CLI a URL
receipt fails closed). On GitHub, `tier_gate.py --github <PR>` judges the pull
request instead: a tier-1 or tier-2 PR needs an APPROVED review from a login
other than the PR author.

**What this cannot prove.** The gate shows that a different, named identity
left a checkable artifact. It cannot show the reviewer read the diff, and a
single shared account — or one person holding two identities — cannot prove
independence at all. Give the reviewer its own account (a reviewer bot works)
and gate on its APPROVED review with `--github`. The review's content stays
the reviewer's receipt (`verification-handback.md`). This repository runs the
range gate in CI as advisory, and its release squash commits carry both
trailers.

- **A terse-commit convention caps prose, never the required trailers.** This skill puts several **required**
  trailer lines on a commit — `Tests: X/X` (`roles.md`), `Regression-Of:` / `Severity:` / `Cost-Cut:` (the
  escaped-defects section below), and the tier trailers this section gates (`Model:`, `Reviewed-By:`). A
  separate, generic terse-commit convention (a fixed line count for the whole body) collides with that
  requirement: one observed run exceeded a 5-line commit-body cap roughly 30% of the time trying to fit the
  required trailers in. Fixing this at the convention layer, not by dropping a trailer: **a line-count cap on a
  commit body counts prose only — exactly the trailer keys this skill requires (`Tests:`, `Regression-Of:`,
  `Severity:`, `Cost-Cut:`, `Model:`, `Reviewed-By:`) are additional and never counted against it; no other
  line earns the exemption.** State the split explicitly wherever the cap is configured (prose lines vs. those
  named trailer lines), so a commit that is short on rationale but carries every required trailer still passes,
  and a commit padded with trailers is never penalized for "exceeding" a cap meant for prose. Terseness on the
  prose side follows the same billed-output logic as a lane's handback: `fanout-host-sizing.md`'s *A lane's own
  handback is billed output* heading.

## 2. Lane caps — cap what the lane can observe

A lane cannot see its own token count while it runs; `token_report.py` reads
the session log only afterwards. Tool calls are observable: every one fires
`PostToolUse`. `scripts/lane_cap.py` counts them per `agent_id`, which the
host sends only inside a subagent — the main thread is never counted — against
`LANE_TOOL_CAP_<TYPE>` for the subagent's type (for example
`LANE_TOOL_CAP_SECURITY_REVIEWER`), falling back to `LANE_TOOL_CAP`:

- at 80% of the cap it injects *"checkpoint now: write handback marked
  UNVERIFIED with remaining work"*;
- at the cap and after, it injects *"stop: hand back UNVERIFIED"*.

It injects `hookSpecificOutput.additionalContext` and always exits 0. It never
blocks a tool: `PostToolUse` cannot block (the tool already ran), and a stuck
counter must not wedge a lane. No cap set means off. Counters are written
atomically (temp file, then rename) and counter files idle for over 7 days are
pruned. Set caps per lane type at the measured p90 after a week of
`token_report.py` data, not before.

```json
{ "hooks": { "PostToolUse": [ { "hooks": [ { "type": "command",
    "command": "LANE_TOOL_CAP=150 python3 .claude/skills/agentic-delivery/scripts/lane_cap.py" } ] } ] } }
```

The enforcing half is at the handback. With `HANDBACK_REQUIRE_STATUS=1`,
`scripts/handback_cap.py` (`SubagentStop`) also blocks a handback with no
status: a line must start (any case, optionally after `status=`) with
`verified` (a green gate or a confirmed effect at the exact SHA) or
`unverified` (anything else, with the remaining work named), or use the host
style `status | evidence | next` with status `done`, `verified`, or
`unverified`. The orchestrator never counts unverified work as done. The check
is opt-in so an existing install's handbacks are not suddenly rejected; exempt
types skip it, and the same three-block release valve prevents a loop. `token_report.py
--budget` stays as the after-the-fact audit.

## 3. Must-load cuts — deterministic lint every run, LLM evals per release

Moving a must-load section behind a trigger saves tokens on every run, but
only if the trigger still fires. Two free checks run in the skill suite's own
repository CI via its repo-root `scripts/test-ci-gates.sh` (a target repo that
vendors skills can copy both):

- **Floor anchors.** `scripts/floor-anchors.tsv` lists fixed-string anchors
  for the rules that decide a Blocker verdict — the evidence standard,
  green on the reviewed head, owner-gated actions, and core security basics.
  Each row pins the rule's heading and a phrase from its body, so keeping the
  heading while gutting the rule still fails; an empty anchor fails too. The
  check fails when any anchor leaves its must-load file. Moving one is a
  deliberate floor change: edit the rule, the row, and say why; never delete a
  row to go green.
- **Trigger lint.** `scripts/trigger_lint.py` requires every routed
  `references/*.md` to open with a "Read …" trigger paragraph, and at least two
  of that paragraph's content words to appear on a router row naming the file:
  its table row, or the whole prose paragraph, in the `SKILL.md` or a parent
  reference. `INDEX.md`, which copies every trigger verbatim, never counts.
  File names are stripped first, so a bare "see `x.md`" line cannot pass on the
  name alone. This is a floor, not proof of loading.

LLM trigger evals (does the agent actually open the file when the trigger
applies?) cost money per run, so they run once per release, not on every cut.

## 4. Escaped defects — attribute, then revert

An escaped defect is a bug found after merge. Its fix commit carries
`Regression-Of: <sha of the commit that introduced it>` and, when known,
`Severity: <Blocker|Critical|High|Medium|Low>`; an `escaped` issue label is
optional. A cost cut is a commit carrying `Cost-Cut: <what was cut>`.

`scripts/escaped_defects.py --since <date> [--until <date>]
[--baseline-start <date>] [--gh]` counts fix commits with `Regression-Of:` in
the window, ties each one whose target is a `Cost-Cut:` commit, and counts the
window's cuts (`--gh` adds the labelled-issue count when the GitHub CLI is
installed). A `Regression-Of:` sha that does not resolve is reported
`UNRESOLVED` and never attributed. The rules, each an exit-1 finding:

- **Revert rule.** Any escaped Blocker traced to a cut prints `REVERT <sha>`;
  that cut is reverted. No trend reading — weekly counts are too small.
- **One cut per measurement window**, so an escape can be attributed.
- **Four-week baseline first.** With `--baseline-start`, a cut dated inside
  the first 28 days fires.

## 5. Gate/acceptance/release tooling is itself a deliverable — version it, don't leave it in scratch

The tooling that *proves* a release is safe — a merge/train orchestrator, a duplicate-detector, an acceptance
suite, a release-candidate script, load-test tooling — is as load-bearing as the feature code it gates, and cuts
the same corner when it lives only in a session-scoped temp/scratch directory: no review, no commit history, no
tests, and it disappears the moment the session or machine restarts. One observed run: a post-mortem inventory
found every piece of tooling that had gated that night's merges — the merge/train orchestrator, the
duplicate-detector, a visual-diff pairing tool, a test-queue manager, a full multi-persona acceptance suite
(roughly 1,800 lines), and the release-candidate script (roughly 1,000 lines) — living only under a session-scoped
temp path; one contributor had three separately hand-maintained copies of part of it across different working
directories.

- **Version it before or alongside the release it gates** — the repository, with its own tests and a short
  README/usage note — same bar as product code, not a personal scratch copy.
- **"The thing that proved this release lives only in a temp directory and disappears on restart" is a finding
  worth raising on its own**, independent of whatever the tooling was checking: a reviewer looking at the shipped
  release otherwise has no way to see what the acceptance run that gated it actually checked.
- **Two sessions independently building overlapping tooling is itself the signal** the tool belongs in the repo:
  hand-synced copies drift from each other, and drift here is drift in the thing everyone trusted to say "safe to
  ship."

## Related

- Claimed vs enforced grading for each mechanism: `host-enforcement.md`.
- Review-side model tiers: `deep-code-review`'s `model-tiering.md`, which
  reads the same tiers file.
