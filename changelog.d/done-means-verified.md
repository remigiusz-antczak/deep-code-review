### Added
- agentic-delivery: `lane_guard.py handback --receipt FILE [--deployed]` refuses a UI-touching change with no `journey: <page> <steps> PASS` receipt line, and a deploy with no `postdeploy-logs: clean` line (absent = "deployed, unverified"). Doctrine in `verification-handback.md` **Done means verified**, including the secret/required-env rules.
- communication-structure: status vocabulary (merged / deployed / verified-on-<page>), `status_vocab_lint.py` flagging unverified "live"/"done", and an eval case.

size-budget-raise: .claude/skills/agentic-delivery/SKILL.md 23993→24216 journey and postdeploy receipt pointers in the G5/G9 rows
size-budget-raise: .claude/skills/agentic-delivery/references/verification-handback.md 57146→58477 Done means verified section
size-budget-raise: .claude/skills/communication-structure/SKILL.md 7281→7661 status vocabulary rule
