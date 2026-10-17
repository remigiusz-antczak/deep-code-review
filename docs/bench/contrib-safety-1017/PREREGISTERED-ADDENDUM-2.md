# Addendum 2 (after both arms were scored; the decision rule is unchanged)

Held-out results (n = 30 fresh scenarios per skill, `results/<arm>/<skill>/verdict.json`):

| Skill | Arm | Judge used (slot-1 rate) | Win rate [95% CI] | Strict W / tie-or-split / L | Other judge (sensitivity) |
|---|---|---|---|---|---|
| contribution | v1 edited | GLM-5.2 (0.559) | 0.293 [0.155, 0.431], n = 29 | 5 / 7 / 17 | DeepSeek-V4-Flash 0.333 [0.217, 0.450], slot-1 0.667 |
| contribution | v0 unedited | none, both judges biased (0.627, 0.633) | no verdict | n/a | DeepSeek-V4-Flash 0.317 [0.217, 0.433]; GLM-5.2 0.333 [0.200, 0.483] |
| product-output-safety | v1 edited | DeepSeek-V4-Flash (0.556) | 0.767 [0.633, 0.883] | 19 / 8 / 3 | GLM-5.2 0.717 [0.600, 0.833], slot-1 0.550 |
| product-output-safety | v0 unedited | DeepSeek-V4-Flash (0.552) | 0.867 [0.750, 0.950] | 24 / 4 / 2 | GLM-5.2 0.717 [0.567, 0.850], slot-1 0.517 |

Decisions:

- contribution: v1 fails the keep rule (lower bound 0.155, not above 0.5) and the unedited skill does no better. Edit reverted; the patch is kept in `edits-reverted.patch`.
- product-output-safety: v1 meets every clause of the keep rule, but the unedited skill scores higher on the same scenarios (0.867 against 0.767, intervals overlapping) and also clears 0.5. The edit has no measured benefit, so it is reverted too: the keep rule is a necessary condition ("keep only if"), and 838 extra bytes of skill text with no gain is a cost. The shipped skill is unchanged and it clears the bar on this set. The 0.400 baseline on 10 scenarios was a small-n, judge-dependent reading, not a stable loss; a second judge gives 0.717 for both arms.
- One missing v1 contribution verdict (n = 29) was retried once by the harness on the second invocation and failed again; it stays out of the score.
