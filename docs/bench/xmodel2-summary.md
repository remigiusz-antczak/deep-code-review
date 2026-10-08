# Perun xmodel bench 2 (PCSS, public corpus-all TEST split, first 30 by sha256 order, 1 replicate, T=0.2, max_tokens 8000)
Arms: plain / full SKILL.md (system) / compact perun-compact.md (system). Same JSON-output PRODUCER task. Scorer scripts/score_review.py strict recall. Verified precision = (matched + verifier real/gt_same)/findings; ONE fixed verifier (gpt-oss_120b) for all arms (it also self-verifies its own findings). Empty = parse failure or zero findings. GLM-5.3-Flash skipped: earlier 32000-token run still failed 4/10 plain, 2/10 Perun, not workable. Bootstrap: 10000 paired case resamples.

```
model	arm	cases	parse_fail	bugs	hit	findings	recall	verified_precision	empty_rate	avg_tokens
gpt-oss_120b	plain	30	0	30	5	68	0.167	0.735	0.10	2185
gpt-oss_120b	full	30	0	30	2	76	0.067	0.671	0.07	1756
gpt-oss_120b	compact	30	1	30	7	68	0.233	0.574	0.07	2756
DeepSeek-V4-Flash	plain	30	1	30	7	85	0.233	0.529	0.07	691
DeepSeek-V4-Flash	full	30	6	30	6	94	0.200	0.617	0.23	2039
DeepSeek-V4-Flash	compact	30	0	30	6	137	0.200	0.620	0.00	599
Qwen3-Coder-Next	plain	30	0	30	1	4	0.033	0.750	0.97	16
Qwen3-Coder-Next	full	30	0	30	3	40	0.100	0.400	0.77	147
Qwen3-Coder-Next	compact	30	3	30	6	122	0.200	0.426	0.37	884
```

Recall deltas (95% bootstrap CI):
- gpt-oss_120b recall compact-plain: +0.067 [95% CI -0.067,+0.200] n=30
- gpt-oss_120b recall full-plain: -0.100 [95% CI -0.200,+0.000] n=30
- gpt-oss_120b recall compact-full: +0.167 [95% CI +0.033,+0.300] n=30 EXCLUDES 0
- DeepSeek-V4-Flash recall compact-plain: -0.033 [95% CI -0.133,+0.067] n=30
- DeepSeek-V4-Flash recall full-plain: -0.033 [95% CI -0.133,+0.067] n=30
- DeepSeek-V4-Flash recall compact-full: +0.000 [95% CI -0.133,+0.133] n=30
- Qwen3-Coder-Next recall compact-plain: +0.167 [95% CI +0.033,+0.300] n=30 EXCLUDES 0
- Qwen3-Coder-Next recall full-plain: +0.067 [95% CI +0.000,+0.167] n=30
- Qwen3-Coder-Next recall compact-full: +0.100 [95% CI -0.033,+0.233] n=30

Verdict: compact beats plain with CI excluding 0 only for Qwen3-Coder-Next (+0.167, mostly by escaping the harness bail-out: empty 0.97 -> 0.37). gpt-oss +0.067 and DeepSeek -0.033 are inside noise; full SKILL.md never beats plain (gpt-oss -0.100, CI touches 0). Compact beats full for gpt-oss (+0.167). Verified precision falls for Qwen (0.75 on 4 findings -> 0.43 on 122) and gpt-oss (0.74 -> 0.57). Caveats: 30 bugs, 1 replicate, one verifier, 7-8 compact parse failures-ish (1 gpt-oss, 3 Qwen).
