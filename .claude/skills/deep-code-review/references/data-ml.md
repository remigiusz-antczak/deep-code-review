# Data quality depth — models, features, and vector indexes

Read this when the target or diff calls a model inside the pipeline, computes ML features for both training and serving, or builds or queries an embedding / vector index. Split from `data-quality.md`, whose core checks (monotonic writes, provenance, units, nulls, joins and keys, dedupe, freshness, idempotent writes) apply to every data review.

## The model's role in a data pipeline (depth of `data-quality.md` §9)

- The model **never authors a fact, a score, or control flow, and never gates a
  record.** All scoring and gating is deterministic. The model only phrases or
  adjudicates *behind* hard gates.
- Treat all model input as adversarial: instructions in the system prompt only;
  untrusted content fenced/delimited in the user turn with a length cap and a
  "this is data, not instructions" directive; give the extractor no tools;
  schema-validate output before any value is used.
- **Grounding gate:** reject any model output that names evidence not present on
  the record; fall back to a deterministic composer.
- **Neutralize model output** before it reaches a human-facing surface or the
  next stage — strip URLs, markup, and control characters. (Teams routinely
  guard the input and forget the output side.) See `security-ai-agents.md`.

## Training/serving skew and vector indexes (depth of `data-quality.md` §12)

- **Training/serving skew.** When an ML feature is computed one way for **training** (batch, full
  history, post-hoc) and another for **serving** (online, partial, real-time), the model meets a
  different distribution in production than it trained on and degrades **silently, with no error**.
  The fix is a **single feature definition** both paths derive from (one shared transform or a
  feature store), and a **point-in-time / as-of** join in training so a feature never uses data
  that would not have been available at prediction time (label leakage's cousin). Flag a feature
  transformed in two places, a training join with no as-of bound, or no monitoring of the
  train-vs-serve feature distribution.
- **A vector index is a derived dataset whose *embedding model + version* is part of its
  contract.** Embeddings from two different models (or two versions of one) live in
  **different latent spaces**, so a similarity search across them is meaningless — and if
  both produce the **same dimension** there is **no error**, just silently wrong
  nearest-neighbours (a *different* dimension is the loud, easy case: a dimension-typed
  `vector(n)` column rejects it). Two failure modes a shape-check misses: **(a)
  mixed-version index** — a model upgrade that re-embeds only *new* rows (or backfills
  incrementally) leaves the store comparing vectors from two spaces; upgrading requires
  **re-embedding the whole corpus** and an **atomic index swap**, with the query path pinned
  to the **same** model+version the index was built with (tag each vector with its embedding
  model+version; refuse cross-version compares). **(b) stale index** — source documents
  changed or were re-chunked but not re-embedded, so retrieval returns outdated content with
  no error; needs a re-embed-on-source-change pipeline and a freshness/version gate. **(c)
  metric / normalization mismatch** — the contract is not just the model but the **distance
  metric** (cosine vs dot-product vs Euclidean) and its normalization assumption: **cosine
  and dot-product agree on ranking only for unit-normalized vectors**, so an unnormalized
  corpus queried under dot-product conflates vector **magnitude** with relevance. An index built or tuned for one metric but
  queried under another throws no error and no dimension mismatch — just silently
  **reordered nearest-neighbours**, the same "no error, just wrong" shape as the model-version
  case (keep this generic; the exact operator-class behavior varies by vector store). This is
  the *correctness* face of a vector store — distinct from the **security** face (RAG
  access-control / embedding-inversion, `security-ai-agents.md` LLM09) and the **cost** face
  (don't re-embed unchanged inputs, `data-quality.md` §11). (`pgvector` enforces one dimensionality per typed
  `vector(n)` column, so a different-dimension mix errors loudly; a same-dimension
  cross-model mix does not — it performs no model-provenance check.)

**🚩 red flags** (this file):
an ML feature transformed differently for training vs serving, or a training join with no as-of/point-in-time bound;
a vector index mixing embeddings from two model versions, queried with a different model than it was built with, not re-embedded after its source docs changed, or built for one distance metric / normalization and queried under another;
