# Verification stage — independent verifiers between candidates and findings

**Read this when** a `DIFF` or `FULL` review reaches Phase 4 with candidate findings
(from your own pass, a fan-out, or the seeded gap-hunt pass in
`method-situational.md`), before Phase 5 files anything. `FILE` scope may use it.
Expands Phase 4 "snippet-or-drop" in `method.md`: that step is the author
re-reading its own claim; this stage hands the claim to a reader who did not write it.
The report fields it adds are in `machine-report.md`.

A reviewer that re-checks its own finding in the same context mostly agrees with
itself. Self-critique with no outside signal fails or degrades; critique that
touches the code or a tool works. So the verifier's job is to **get an external
signal for each claim**, not to re-judge it.

## 1. Procedure

1. **Freeze the candidates** as a findings list (`file`, `line`, `text` = the
   mechanism plus the concrete failing input; `id` optional). Do not attach
   severity, confidence or your reasoning: a verifier that sees them anchors on them.
2. **Batch, then dispatch.** `python3 scripts/verify_findings.py prompts FINDINGS.json --batch 5 --ref <START_SHA>`
   (shipped with this repository's `scripts/`; copy or port it, or write the same
   prompt by hand) emits one self-contained prompt per batch of at most 5
   findings. Batching bounds cost: the verifier's fixed context is paid per
   batch, not per finding (§4).
3. **One fresh context per batch.** A new subagent per prompt, run in parallel,
   with read access to the tree at `START_SHA` and a shell for probes. With no
   subagents, run each batch as a **separate pass after writing the candidate list
   to a scratch file**: reopen every cited location cold, and try to falsify the
   claim before agreeing with it. Record the verifier as `separate-pass`; it is
   the same model in the same session, so treat its `confirmed` as weaker.
4. **Each verdict needs an external signal**, in this order of preference:
   read or grep the cited code and its callers (`basis: tool`); run the failing
   input, a one-line probe, a test or a linter, or the target's review check
   runner when the checkout ships one; only then a model-only judgement, labelled
   `basis: model-only`. Probe with side-effect-free commands only (text tools, a
   shell syntax check); never run the reviewed script itself, and a claim that
   needs a billable or shared-state call stays `unverified` (`could-not-check`).
5. **Merge fail-closed.** `python3 scripts/verify_findings.py merge FINDINGS.json verdicts-*.txt`
   returns `confirmed`, `unverified`, a `refuted_count`, and `counts`. A missing,
   malformed, conflicting, evidence-free or `model-only` answer is `unverified`; a
   verifier that timed out leaves its batch `unverified`, never `confirmed`.

## 2. What the report shows

| Verdict | In the report |
|---|---|
| `confirmed` | A normal finding, `confidence: CONFIRMED`, the verifier's evidence kept. Only these count in severity totals and the verdict. |
| `unverified` | A separate **Unverified** list under the findings (what would settle it); never in the totals, never silently promoted. |
| `refuted` | Dropped. Print the count (`Verification: 14 candidates, 8 confirmed, 3 unverified, 3 refuted`). If you disagree with a refutation, re-raise it only with counter-evidence from the code. |

`strength` rows and Phase 1 ground-truth results are not verified here (they already
carry command output). The seeded gap-hunt pass's "verify-merge" in
`method-situational.md` is this stage run on that pass's new findings.

## 3. Measured

Held-out fixture `scripts/eval-fixtures/heldout/pr1354-ops-scripts` (4 ops scripts as new-file diffs, 6 real bugs), scored by
`scripts/score_review.py`. Eight first-pass reviews (six earlier runs plus two new, `sonnet`), 101 candidate findings, verified in batches of 5 by fresh `sonnet` contexts with read, grep, and probe-only shell (no model-only confirmation counted). Directional, one diff, one model; the verifier prompt was edited once after a first measurement on this same data.

| Metric (mean of 8 runs) | Single pass (no verification) | After verification, confirmed list | After verification, confirmed + separate unverified list |
|---|---|---|---|
| Recall of the 6 bugs | 5.25 | 3.13 | 5.25 |
| Strict precision (bugs matched / findings listed) | 0.51 | 0.53 | 0.51 |
| Findings listed | 12.6 | 6.6 | 12.6 |
| Cost vs one pass | 1x | 2.05x (about $0.41 vs $0.20) | same |

- **Verdicts on 101 candidates:** 53 confirmed with a tool-backed signal, 44 confirmed by model-only judgement (downgraded to unverified), 4 unverified by the verifier, **0 refuted**.
- **Nothing was dropped, so precision did not improve.** Verifiers confirmed or left open every candidate and refuted none; 26 of the 53 tool-confirmed findings match none of the 6 known bugs, so they are either real extras or verifier agreement with a wrong claim, and this fixture cannot tell which. Strict precision stays near 0.5. What the stage adds on this diff is a tier: 6.6 findings per review with a quoted tool signal, 6.0 flagged as not reproduced.
- **The recall cost is real if the unverified list is not read.** The confirmed list alone holds 3.13 of 6 bugs; the others sit in the unverified list, because a read-only verifier could not run a script to show them (a missing `lsof`, a path with a space, an archive collision). Keep the unverified list next to the findings, and give verifiers a sandbox where they can run the target's own checks when you want those confirmed.
- **Model-only and tool-backed confirmations were equally precise** (23 of 44 versus 27 of 53 matched a known bug), so the fail-closed rule is a safety choice here, not something this fixture shows to improve precision. A fixture with injected false findings would test it; none exists yet.

## 4. Cost

Measured on the same 8 runs: a verifier batch of 5 cost about $0.07 and a run needed 3 (about $0.21 per review), against about $0.20 for the first pass in the same harness, so the stage doubles the cost of a review (2.05x; 1.5x against the $0.43 single pass in `method-situational.md`, which paid a larger session context). Raise the batch size to cut it; verifier context is paid per batch.
