---
description: Run a deep code review of a diff, files, or the whole repo
argument-hint: "[--high-stakes] [DIFF <base> | FULL | FILE <paths>]"
disable-model-invocation: true
---
Review scope: $ARGUMENTS. If no scope was given, use `DIFF origin/main`. Run in a checkout of the repo (at the PR head
for a PR) with Read, Grep and Glob, never on a pasted diff alone.

For `DIFF` and `FILE` scope, do not load the `deep-code-review` skill (about 6k tokens re-read every turn; the repo's
own benchmark found extra instructions did not help). Read the changed code and its callers, then report only issues you
can point to in the code (file:line) with why it breaks, severity-ranked, verified against source. Nothing run or
verified is not a finding.

For `FULL` scope, or with `--high-stakes` (release, security, or data-loss-path change), load the `deep-code-review`
skill and follow its method, report template and definition of done.

Model: the normal review is one pass on the efficient model (Sonnet). With `--high-stakes`, run the same single pass on
Opus; do not add a second pass. This stays allowed when `tokens=efficient`, because the change is explicitly high-stakes.
