# Data quality depth — graphs and diagrams authored as data

Read this when the target or diff authors or validates a graph, diagram, ring, or state machine as data (a node list, edges, an `anchor` / `startNode` field, a topology or closure check). Split from `data-quality.md`, whose core checks (monotonic writes, provenance, units, nulls, joins and keys, dedupe, freshness, idempotent writes) apply to every data review.

## Graph and diagram data (depth of `data-quality.md` §4)

- **A structural / topology validity gate on a graph *authored as data* never checks that a
  separate `anchor` / `startNode` field agrees with the declared entry — closure and
  start-designation are orthogonal, so a valid ring can still begin at the wrong step.** A
  diagram authored as data — an ordered node list, directed edges, a prose narrative of step
  order, and an explicit `anchor` / `startNode` a renderer reads to decide where to begin
  walking the cycle — carries that anchor as a **denormalized restatement** of *where the ring
  begins*, and nothing forces it to equal the **declared entry**: the node list's first element
  and the narrative's first clause. A gate asserting *the edges form one closed cycle covering
  every node* passes green on a perfectly valid ring — so a reviewer reads "validated" — yet it
  never checks *which* node is declared the start, so an anchor set to the last node (or an
  arbitrary "most interesting" one) sails through and **every consumer renders the ring rotated
  to the wrong step** — a wrong-start, not a broken graph. Detection compares the anchor to the
  declared entry (`anchor == nodes[0]`, and the narrative's first clause), **never** "is the
  anchor a valid node id" — validity of the topology is the wrong question. Fix **by
  construction**: derive the anchor *from* the declared entry, or gate the two authored fields
  into equality so they cannot drift (`data-quality.md` §2, *make a dishonest value unrepresentable*). Because
  such a diagram is usually emitted by a **template / porting script / author habit**, one wrong
  anchor is a strong prior that its **siblings from the same authoring pass carry the same
  disagreement** — run the outward instance-set sweep across every sibling, not just the file in
  hand (`method.md` Phase 4). **Discriminators:** the named-quantity rule in `data-quality.md` §4 flags a
  *quantity* that drifted **stale** across copies (repetition is not corroboration); here a
  *start-designation* is authored **wrong from origin** and a green **topology** gate supplies
  the false assurance. The partition / ring validity gate in `language-stack-redflags.md` is a
  partitioning *routine's* off-by-one that **falsely rejects** a valid decomposition; this is
  authored *data* whose gate **falsely accepts** by omitting a whole dimension. And `data-scoring.md`'s
  stated-precedence rule is authority **direction** — one source *outranks* another and must
  reach the decision field; here the anchor and the declared entry are **co-equal** fields that
  must simply be **equal**, and no gate compares them.

**🚩 red flags** (this file):
a graph / diagram authored as data whose closure / topology validity gate stays green while a separate `anchor` / `startNode` field disagrees with the declared entry (the node-list first element / the narrative's first clause), rendering the cycle rotated to the wrong start — and batch-inherited across every sibling from the same authoring pass.
