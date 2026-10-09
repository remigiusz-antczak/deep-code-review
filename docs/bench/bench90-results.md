# Benchmark results: held-out cases (2026-10-09)

This page replaces the earlier 30-case numbers (31% vs 21% of bugs found), which came from a smaller sample and are superseded. A clean full re-run with an isolated harness (branch `fix/bench-run-isolation`) is pending; until it lands, treat these numbers as provisional.

## Bottom line

- One Perun pass did not find more bugs than a plain "review this" prompt: recall 0.391 for both on the 64 cases with intact records (difference +0.000, interval -0.078 to +0.078).
- Adding a second independent pass and taking the union raised recall by +0.016 over one pass (0.416 against 0.391, interval 0.000 to +0.047). That is a small gain, not shown to be real.
- No precision (false-alarm) claim is made: precision has not been recomputed on clean data.
- A single Perun pass costs about 1.6 times a plain review.

## Results (64 cases with intact records)

| Setup | Recall (adjudicated) |
|---|---|
| Plain prompt | 0.391 |
| Perun, single pass | 0.391 |
| Perun, two independent passes plus union | 0.416 |

Paired 95% bootstrap intervals: Perun single pass minus plain, +0.000 [-0.078, +0.078]; two-pass union minus single pass, +0.016 [0.000, +0.047].

Plain prompt on all 87 usable cases: recall 0.379.

Cost per review (review only): plain $0.059, Perun single pass $0.096 (about 1.6 times).

## Method

- Corpus: 90 held-out real bug fixes from open-source projects; 87 usable, 3 excluded because the run errored. The reviewing model sees only the code change, not the fix. Case answers are read only by the test runner and are not published.
- Model: Sonnet, one replicate (one run per case and setup), test split.
- Recall: share of known bugs a review named, as judged by an independent verifier model (adjudicated).
- Two-pass setup: a single pass plus one fresh independent pass, merged; a second-pass finding in the same file within 3 lines of a first-pass finding is dropped as a duplicate.
- Intervals: paired bootstrap over cases, 10,000 resamples, seed 1.
- Runner: [`scripts/bench_corpus.py`](../../scripts/bench_corpus.py).

## Caveats

- A stray driver process overwrote the Perun records of 23 of the 87 cases mid-run, so every Perun and two-pass number above uses only the 64 cases with intact records. Earlier two-pass figures that included the 23 overwritten cases were invalid and are withdrawn.
- Precision and two-pass cost were not recomputed on clean data and are not reported.
- One replicate, one model family, one corpus; all intervals include zero or touch it. Results are directional.
- Verification is done by a model, not a human.
- Per-language breakdowns are withheld until the clean re-run.
