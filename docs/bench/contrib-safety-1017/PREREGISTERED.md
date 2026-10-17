# Preregistration: contribution and product-output-safety against their rivals (2026-10-17)

Written and hashed (SHA256-frozen.txt) before any held-out generation or judge call. Every model call goes to the PCSS endpoint ($0); no `claude -p`.

## Baseline

Frozen held-out set of 10 (docs/bench/rival-eval-baseline-1017): contribution 0.200 [0.000, 0.450] against daymade github-contributor, product-output-safety 0.400 [0.150, 0.700] against promptfoo redteam-setup (judge GLM-5.2; the DeepSeek-V4-Flash judge was position-biased there).

## Root cause (tune split only, `scripts/eval-fixtures/rival/<skill>/tune.json`, judge reasons)

- contribution: the skill is written for contributions to the skillset, so on a request about someone else's project it gate-kept ("do not submit your current fix") and gave a short generic template. Judges preferred the rival for before/after sanitization examples, a ready-to-paste draft, a fallback timeline, and a concrete workflow for the user's stated difficulty. Edit: one section, "Helping with a pull request, issue or reply on another project".
- product-output-safety: the legal-routing bullet said "never assert the duty", and the answer deflected the legal question; judges named the regime in the rival and asked for it. The plan also recited the checklist instead of fitting the stated team size and deadline. Edit: name the regime and the question for counsel (still never "this binds you"); a "fit the plan to the stated team and clock" bullet.

Tune results after the edits (n = 6 and 10, noisy, never a verdict): contribution 0.167 to 0.417 (DeepSeek-V4-Flash); product-output-safety 0.500 to 0.600 (GLM-5.2). Edits were not tuned further.

## Held-out set (fresh, frozen)

30 scenarios per skill, `scripts/eval-fixtures/rival/<skill>/heldout30.json`, drawn by the blind writer (Qwen3.5-397B-A17B, temperature 0.7) from 30 new seeds per skill (`prompts/`), fictional companies and people only, no skill text shown to the writer. Checked disjoint from the tune and 10-scenario held-out sets by 6-word shingle overlap (none above 0.3).

## Arms and judges

Generator for both arms: Qwen3.5-397B-A17B, thinking off, temperature 0.3, no tools, the harness's GEN_TASK wrapper. Arms: v1 = the edited `SKILL.md` (hash in SHA256-frozen.txt) against the rival; v0 = the unedited `SKILL.md` (frozen copy) against the same rival text, reported for honesty. Judge: the harness's rubric-free blind A/B in both orders; DeepSeek-V4-Flash unless its slot-1 rate is outside 0.4 to 0.6, then GLM-5.2; no healthy judge means no verdict. The generator is never a judge. A scenario scores 1 only when v1 wins in both orders, 0 only when it loses in both, else 0.5. CI = percentile bootstrap, 10,000 resamples, seed 1.

## Keep rule (stated before any call)

Keep a skill's edit only if all hold: n = 30 scored scenarios; 95% CI lower bound above 0.5; a judge with a healthy slot-1 rate scored it, and that rate is reported; strict both-order agreement scoring as above. Otherwise revert the edit (SKILL.md, its eval, its changelog line) and ship the bench only. One run per arm; no re-runs, no judge swapping, no scenario edits after seeing a result. The other judge's number is reported as a sensitivity check but does not change the rule.
