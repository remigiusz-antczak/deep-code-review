# Benchmark results: 87 held-out cases (2026-10-09)

This page replaces the earlier 30-case numbers (31% vs 21% of bugs found), which came from a smaller sample and are superseded.

## Bottom line

- One Perun pass did not find more bugs than a plain "review this" prompt at this sample size (recall 0.356 against 0.379, difference -0.023, interval spans zero).
- Perun's two independent passes plus union (the high-stakes default) had significantly higher verified precision than a plain prompt (+0.076, interval excludes zero), so fewer false alarms. Its recall gain (+0.046) is not significant.
- The two-pass setting costs about 3.2 times a plain review.

## Results

| Setup | Recall (adjudicated) | Verified precision | Findings | Cost per review | Cost per review incl. verification |
|---|---|---|---|---|---|
| Plain prompt | 0.379 | 0.594 | 219 | $0.059 | $0.118 |
| Perun, single pass | 0.356 | 0.633 | 196 | $0.096 | $0.152 |
| Perun, two independent passes plus union | 0.425 | 0.670 | 306 | $0.188 | $0.296 |

Paired 95% bootstrap intervals:

| Comparison | Recall difference | Verified precision difference |
|---|---|---|
| Single pass minus plain | -0.023 [-0.092, +0.046] | +0.039 [-0.033, +0.111] |
| Two passes minus plain | +0.046 [-0.023, +0.115] | +0.076 [+0.013, +0.139] (significant) |
| Two passes minus single pass | +0.069 [+0.023, +0.126] | not computed |

Cost ratio, two passes to plain (review only): 3.20x. Single pass to plain: 0.096 / 0.059, about 1.6x.

Strict recall (the review named the exact fix location) was 0.529 for plain and 0.540 for single-pass Perun; it was not computed for two passes.

## Recall by language (plain vs single-pass Perun)

| Language | Cases | Plain recall | Single-pass recall |
|---|---|---|---|
| go | 31 | 0.387 | 0.452 |
| js | 17 | 0.176 | 0.118 |
| python | 25 | 0.560 | 0.480 |
| shell | 14 | 0.286 | 0.214 |

Per-language numbers are small samples; do not read a language ranking into them.

## Method

- Corpus: 90 held-out real bug fixes from open-source projects; 87 used, 3 excluded because the run errored. The reviewing model sees only the code change, not the fix. Case answers are read only by the test runner and are not published.
- Model: Sonnet, one replicate (one run per case and setup), test split.
- Recall: share of known bugs a review named, as judged by an independent verifier model (adjudicated). Verified precision: share of a review's findings the verifier judged real or matching a known bug.
- Two-pass setup: pass one plus one fresh independent pass, merged. A second-pass finding in the same file within 3 lines of a first-pass finding is dropped as a duplicate; recall still credits a second-pass match.
- Intervals: paired bootstrap over cases, 10,000 resamples, seed 1.
- Runner: [`scripts/bench_corpus.py`](../../scripts/bench_corpus.py).

## Caveats

- Two passes: 23 of the 87 single-pass records were overwritten by a foreign process mid-run, so for those 23 cases the two-pass setup used two fresh passes instead of reusing the original first pass. The other 64 reuse the original single-pass output.
- One replicate, one model family, one corpus: results are directional.
- Recall intervals for single-pass and two-pass versus plain include zero. Only the two-pass precision gain excludes zero.
- Verification is done by a model, not a human.
