# AI evals — model-dependent output

Read this when the target calls an LLM, retrieves for generation (RAG), or runs a tool-using agent. Split from `testing-and-evals.md`; the general test taxonomy and smells there apply to every review.

## AI evals (for any model-dependent output)

A mocked-LLM unit test verifies **wiring, not model quality.** Model quality
needs its own harness:

- A **labeled golden set** scored for correctness/consistency (not vibes),
  tracked over time, with an **accuracy threshold that gates** prompt or
  model-version changes (a change that drops accuracy fails the build). The golden
  set must be **disjoint from the prompt / few-shot / fine-tune content** — a
  leaked example makes the bench measure memorization, not quality; treat
  contamination as a Critical eval defect.
- The harness's **own scoring logic is pure and unit-tested**, and it
  **fail-fasts on a malformed case** — silently skipping a case inflates the
  score.
- **Grounding / anti-fabrication checks** where claims reach users: every named
  entity and number in generated text must anchor to the input facts (match
  numbers on digit boundaries so a value can't pass on a fragment); ungrounded
  output is rejected to a deterministic fallback. Distinguish **anti-fabrication
  from anti-reasoning**: where the output's value *is* its reasoning, gate only
  the checkable facts plus a drift/overlap floor and a meta-leak guard, and allow
  inference language — don't force robotic restatement.
- Use **temperature 0** for judges/verifiers so the eval itself is deterministic.
- **Self-consistency / inter-model agreement is not precision.** Output quality
  is *unmeasured* until an expert rates a frozen, labeled cohort; don't stack
  features on an unvalidated base.
- A **decorrelated review ensemble** (multiple *different* models/reviewers, all
  must pass) catches a miss or an injection that lands on one reviewer; fail
  soft.
- **An LLM judge carries known biases — test for them structurally and cheaply,
  before trusting its scores.** Beyond temperature 0 and the frozen-cohort validation
  above (Zheng et al., 2023 document position, verbosity, and self-enhancement biases
  in strong judges): **(a) order-swap consistency** — for any pairwise/comparative
  judge, run it twice with the candidates' positions swapped; a flipped verdict is
  **positional bias** in the judge prompt itself, caught with two calls and zero human
  labels. **(b) judge/subject independence** — when the system under test and the judge
  share a model or vendor family, flag **self-preference** bias risk explicitly. **(c)
  verbosity correlation** — on the labeled cohort, check the judge's score against
  output length; a strong positive correlation with no length-normalized rubric is
  evidence it rewards length, not quality. And **name the agreement bar** the
  frozen-cohort check must clear — strong judges reach roughly **≥80%** agreement with
  human preference (Zheng et al., 2023) — and **re-check it when the judge model version
  changes**: an unpinned judge is the same latent-bug class as an unpinned embedding
  model (`data-ml.md`).
- **A retrieval-augmented (RAG) app is evaluated at the retrieval seam, not only
  end-to-end.** The generation-grounding check above is necessary but not
  sufficient: a faithful answer over the *wrong* retrieved context is still wrong,
  and a good end-to-end score can hide a retrieval miss the model papered over from
  parametric memory (which then fails silently when the knowledge base changes).
  Evaluate the two stages separately — **retrieval quality** (context *precision*:
  retrieved chunks are relevant; context *recall*: the needed facts were retrieved
  at all — measured @k, with chunk-boundary loss and reranking in view) and
  **generation faithfulness** (is the answer factually consistent with *that*
  retrieved context — groundedness), with **answer relevancy** (does it actually
  address the question) as a separate check. (RAG = a parametric generator plus a non-parametric
  retrieval component over external knowledge — Lewis et al., 2020. The metric names
  are operationalized by open-source eval libraries, e.g. RAGAS — a *tool*, not a
  standard: frame the concept, don't pin a vendor's exact formula.)
- **Any prompt assembler is evaluated at the *context-assembly* seam — input budget and
  placement, not only its upstream quality.** A RAG pipeline is one instance; a chat turn
  that concatenates a system prompt + conversation history + tool/function output + the
  user's message is another. Any assembler that joins parts with no budget guard has the
  same two silent-failure checks between "the right material was gathered" and "the model
  answered": **(a) input-budget overflow** — when the assembled input exceeds the model's
  context budget, is the check computed with the target model's **actual tokenizer** (not
  a char/word estimate), and on overflow are **whole lowest-priority units dropped** (for
  RAG, the lowest-ranked chunks), never a unit **truncated mid-content** (a mid-cut fact or
  citation the model then completes or misattributes)? **The drop-priority must be explicit
  and protect the load-bearing input** — a naive assembler that merely overflows silently
  sheds the *earliest* text, which is the **system instructions** (or clips a load-bearing
  data blob), so the model quietly stops following its own rules with no error raised; a
  chat assembler's priority is "shed the oldest turns, never the system prompt or the
  current user message." Force the overflow in a test and assert no partial unit reached the
  prompt, the dropped units were the lowest-priority (never the system prompt), and the drop
  was counted/logged. **(b) placement, not just fit** — even when everything fits, a unit
  ranked below #1 but still needed for the answer should sit at the **start or end**, not
  left buried mid-concatenation in raw score order (ranking is imperfect, so the part with
  the answer is not always the #1 hit): models access "relevant information in the middle of
  long contexts" markedly worse ("Lost in the Middle," Liu et al., 2023). This is **per-call
  prompt arithmetic** — distinct from a long-running agent's conversation compaction
  (`security-ai-agents.md`) and from an output `max_tokens` cap (that bounds what comes
  *out*; this bounds what goes *in*).
- **An agent (tool-using, multi-step) is evaluated on its trajectory, not only its
  final answer.** Score tool-call *selection* (did it pick the right tool), tool-call
  *arguments* (well-formed, correctly bound), and multi-step *task completion* (the
  sequence reached the goal without an unrecoverable wrong turn). A right final
  answer reached via a lucky or unsafe path is a latent failure, and a wrong tool
  choice is invisible to an output-only bench.

## Evaluating a code-review skill on real paired diffs
Score a review skill against defects mined from the repo's own fix history, as commit pairs with a machine-checkable oracle:
- **Pair each defect with its fix, not a guessed bug-introducing commit.** Require a regression test that fails at the parent and passes at the fix;
the fix-parent is the latest commit where the defect is provably present — run the test. The skill reviews the parent for recall and the fixed sha for
specificity; one finding naming the just-fixed defect is a suspected memorization leak — report that rate beside recall.
- **Measure false positives on the fixed sha and on separately sampled clean diffs.** A fixed sha can still hold a real latent defect, so human-sample
its findings before charging them; report the FP rate beside recall.
- **Match findings on mechanism, not location.** A finding counts only if it names the same root cause as the fix (a race is not a null dereference);
a location-only hit is a miss or at best partial. Report strict and partial recall separately — the gap is the vague-alarm rate.
Adjudicate borderline matches with an LLM judge under the bias controls above.
- **Dedup findings per defect before scoring.** Several findings on one defect earn one recall credit; every unmatched finding charges the FP budget —
but unmatched is not automatically false: human-label a sample, since some unmatched findings are real unknown defects.
- **Headline: recall at the severity gate the skill actually posts at, subject to the FP budget above.** Widening the gate trivially raises
recall; the budget is what binds.
- **State the selection bias: the corpus holds only test-catchable defects.** Requiring a failing regression test excludes design, performance,
security-by-omission, and docs defects, so measured recall is an upper bound for defects tests cannot express — say so beside the headline.
- **The instrument must score 1.0 on hand-written correct findings** derived from the ground-truth records, and 0 on deliberately wrong ones. If the
correct findings don't match, the matcher is broken — fix it before reviewing the skill.
- **Version the matching policy** (line tolerances, root-cause rules) — it is part of the instrument, and prompt tuning otherwise converges on its quirks.
Re-run the canaries on every matcher change.
- **Compare skill versions paired, not unpaired:** run both on the same defect set and read the discordant pairs, which carry the signal. Report
intervals, never bare point estimates.
- **Split CI by cost and determinism.** Every PR runs the offline part — corpus integrity, matcher unit tests, canaries, metric recomputation from
committed finding artifacts; the paid live harness runs on a schedule, append-only, with metric diffs surfacing as PR checks.
