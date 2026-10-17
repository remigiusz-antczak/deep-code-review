# contribution and product-output-safety against their rivals, fresh held-out, 2026-10-17

BLUF: on 30 fresh scenarios per skill, product-output-safety (unedited) beats its rival, 0.867 [0.750, 0.950] (DeepSeek-V4-Flash, slot-1 0.552; GLM-5.2 gives 0.717 [0.567, 0.850]). contribution does not: 0.333 [0.200, 0.483] at best (unedited, GLM-5.2) with no judge passing the position-bias gate. Both candidate SKILL.md edits were reverted; only the bench is committed. Spend $0.00 (PCSS only).

- Rule and arms: `PREREGISTERED.md`, hashes in `SHA256-frozen.txt` (the two SKILL.md lines are the edited v1 texts, reproduced by applying `edits-reverted.patch` to `frozen/<skill>.v0.md`), `PREREGISTERED-ADDENDUM-1.md` (bench.py fix), `PREREGISTERED-ADDENDUM-2.md` (results and decisions).
- Scenarios: `scripts/eval-fixtures/rival/<skill>/heldout30.json` (30 each, blind writer, fictional names, disjoint from the tune and 10-scenario sets). Seeds and briefs in `prompts/`.
- Raw outputs and every judge verdict: `results/<arm>/<skill>/`. Reproduce with `python3 docs/bench/contrib-safety-1017/bench.py run v0|v1 <out>` (PCSS key from `.env`; the rival text is fetched from its public URL and cached).
- Tune split (n = 6 and 10, never a verdict): edits moved contribution 0.167 to 0.417 and product-output-safety 0.500 to 0.600, and neither gain carried to the fresh set. Lesson: n = 6 to 10 scenarios cannot separate a 0.2 effect from judge and sampling noise.
- Why contribution still loses (tune reasons, not tested as a fix): the skill is written for contributions to the skillset, while the scenarios ask for help with someone else's project; judges prefer the rival's longer, step-by-step answers with concrete sanitization examples. A response-shape section did not move this on 30 scenarios.
