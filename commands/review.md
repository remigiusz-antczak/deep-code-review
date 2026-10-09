---
description: Run a deep code review of a diff, files, or the whole repo
argument-hint: "[--high-stakes] [DIFF <base> | FULL | FILE <paths>]"
disable-model-invocation: true
---
Load the `deep-code-review` skill and run a review with scope: $ARGUMENTS

If no scope was given, use `DIFF origin/main`. Run in a checkout of the repo (at the PR head for a PR) with Read, Grep and Glob, never on a pasted diff alone. Follow the skill's method, report template and
definition of done; report only findings you verified against source.

Model: the normal review is one pass on the efficient model (Sonnet). With `--high-stakes` (release, security,
or data-loss-path change), run the same single pass on Opus; do not add a second pass. This stays allowed when
`tokens=efficient`, because the change is explicitly high-stakes.
