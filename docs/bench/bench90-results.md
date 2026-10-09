# Benchmark results: held-out cases, clean re-run (2026-10-09)

This page replaces the earlier 30-case numbers and the 64-case interim numbers. It is a clean re-run of 89 cases with isolated run directories (harness branch `fix/bench-run-isolation`).

## Bottom line

- On this prompt-only benchmark, Perun's review is not measurably better than a plain "review this" prompt, and it costs about 2 times as much per review.
- No difference clears zero: every paired 95% interval below includes 0.
- One Perun pass found slightly fewer bugs than plain (0.326 against 0.360); two independent passes plus union found slightly more (0.393). Neither gap is distinguishable from noise.
- Verified precision (share of flagged issues judged real) was 0.653 for Perun against 0.618 for plain, also not distinguishable.

## Results (89 cases, Sonnet, one replicate)

| Setup | Recall (adjudicated) | Recall vs plain [95% CI] | Verified precision | Precision vs plain [95% CI] | Findings | Cost per review (review only) |
|---|---|---|---|---|---|---|
| Plain prompt | 0.360 | - | 0.618 | - | 220 | $0.043 |
| Perun, single pass | 0.326 | -0.034 [-0.101, +0.034] | 0.653 | +0.035 [-0.038, +0.105] | 196 | $0.080 |
| Perun, two independent passes plus union | 0.393 | +0.034 [-0.022, +0.090] | 0.653 | +0.035 [-0.036, +0.100] | 291 | $0.163 |

Cost including the verifier pass: plain $0.082, single $0.119, two-pass $0.240. Single-pass review cost is about 1.9 times plain; two-pass about 3.8 times.

## Method

- Corpus: 90 held-out real bug fixes from open-source projects; 89 used. One case was excluded because the second Perun pass returned no JSON array. The reviewing model sees only the code change, not the fix. Case answers are read only by the test runner and are not published.
- Model: Sonnet, one replicate (one run per case and setup), test split. Three setups ran concurrently, one case at a time each, each model call under a 900 second alarm.
- Recall: share of known bugs a review named, as judged by an independent verifier model (adjudicated).
- Verified precision: (findings judged real or matching a known bug) divided by findings.
- Two-pass setup: a single pass plus one fresh independent pass, merged; a second-pass finding in the same file within 3 lines of a first-pass finding is dropped as a duplicate.
- Intervals: paired bootstrap over cases, 10,000 resamples, seed 1.
- Runner: [`scripts/bench_corpus.py`](../../scripts/bench_corpus.py).

## Caveats

- One replicate, one model family, one corpus; all intervals include zero. Results are directional.
- Verification is done by a model, not a human.
- This measures prompt-only review of a diff. It does not measure Perun's tool-using, multi-step workflows.
- Per-language breakdowns are not reported.
