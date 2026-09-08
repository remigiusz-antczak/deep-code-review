## Summary

<!-- What changed and why. One short paragraph. -->

## Test plan

- [ ] `bash scripts/test-ci-gates.sh` (all cases pass)
- [ ] `bash scripts/ci-gates.sh routing --max-bytes 100000 .claude/skills/deep-code-review`
- [ ] `bash scripts/ci-gates.sh routing --max-bytes 100000 .claude/skills/agentic-delivery`
- [ ] `bash scripts/ci-gates.sh routing --max-bytes 100000 .claude/skills/idea-critic`
- [ ] `bash scripts/ci-gates.sh version .`
- [ ] `bash scripts/ci-gates.sh privacy --banlist .banlist.txt .`
- [ ] `bash -n install.sh`
- [ ] Description of each new/changed `SKILL.md` is ≤1024 characters
- [ ] Every `references/*.md` is routed from its skill's `SKILL.md`
- [ ] No third-party identifiers or secrets in the diff

## Notes

Persisted artifacts (this PR body included) are normal English.
