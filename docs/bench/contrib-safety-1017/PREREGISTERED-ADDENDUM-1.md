# Addendum 1 (after the first held-out run, before any re-run)

The first run printed: contribution v1 verdict FAIL, product-output-safety v1 verdict PASS; the v0 arm then crashed in `bench.py` on a skill with no healthy judge (`KeyError: 'win_rate'`), so product-output-safety v0 was not run. These changes to `bench.py` do not touch scenarios, skill texts, the rule, or any v1 verdict:

1. `verdict.json` is written with `.get`, so an arm with no healthy judge reports `null` instead of crashing.
2. A `sens` step scores every scenario with both judges on the cached outputs and reports each judge's win rate, CI and slot-1 rate. Reported only; the keep rule still uses the judge the harness selects.

The v1 outputs and judge verdicts are cached and reused; only the v0 arm and the missing second judge are newly called. The keep decision for each skill was fixed by the original rule before this addendum: contribution reverted, product-output-safety kept.
