### Added
- Compact mode (`references/compact-mode.md`, under 2.5KB) for non-Claude or small-context models, routed from SKILL.md, with the measured cross-model bench in `docs/bench/`. On Qwen3-Coder-Next it beat a plain prompt by +0.167 recall (CI +0.033 to +0.300); gpt-oss and DeepSeek differences were within noise.

size-budget-raise: .claude/skills/deep-code-review/SKILL.md 23473→23590 one routing line to compact-mode.md
