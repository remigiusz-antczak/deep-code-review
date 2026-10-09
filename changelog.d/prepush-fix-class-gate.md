### Fixed
- `pre-push-verify.sh` now runs CI's "Fix commits carry a pinned test" and "Prose lessons carry a mechanism" steps over the whole branch range (merge-base with the default branch to HEAD), reading the steps straight from `.github/workflows/ci.yml` so the globs cannot drift. A SKILL.md or reference edit without a test/eval in the same commit is refused locally with the fix hint (refs #1380).

