# Data quality depth — shared accessors over polymorphic shapes

Read this when the target or diff serves several record shapes or types through one generic list / search / filter path (a shared key accessor, a per-type scope or tag accessor, a polymorphic union). Split from `data-quality.md`, whose core checks (monotonic writes, provenance, units, nulls, joins and keys, dedupe, freshness, idempotent writes) apply to every data review.

## Shared accessors over polymorphic shapes (depth of `data-quality.md` §5)

- **A shared accessor over polymorphic shapes silently no-ops for the shape whose
  key it doesn't reach — the read-side sibling of the erosion-guard rule in `data-quality.md` §5.** A
  generic exact-key filter serving several record shapes from one path often matches
  against a **hardcoded OR-list of top-level field names**
  (`[row.fooId, row.barKey, …].filter(Boolean).includes(key)`, or an equivalent `??`
  chain). It works for every shape whose id is a plain top-level property and
  **silently returns empty — no error** — for any shape whose id is **nested** under a
  sub-object (`metadata` / `frontmatter` / `attributes` / `config`): none of the
  top-level candidates is ever truthy, so the list is empty and `[].includes(key)` is
  always `false`, and that collection reads as "nothing ever matches" instead of
  failing loudly. It survives review because each shape works alone and a **per-shape**
  search/scope accessor (built correctly, reaching into the nested field) usually masks
  it, so a smoke test on the common shapes passes. Catch it: enumerate **every** shape
  the filter serves and check each one's real field nesting **at its schema/type, not
  by assumption**; if a sibling accessor already reaches the nested key correctly while
  the shared filter does not, that inconsistency confirms a genuine gap, not a
  limitation; and if the endpoint documents the parameter as working uniformly across
  shapes, the silent per-shape gap is a broken promise (a contract breach on par with a public-API change, `api-contracts.md`). Fix: a per-shape accessor
  registry (`shape → (row) => key | null`), mirroring the per-shape accessors the code
  already has for other concerns — not another ad-hoc entry bolted onto the top-level list. Unlike the erosion-guard’s open-ended write-site surface (`data-quality.md` §5), the shape set is closed and type-checkable, so the registry can be exhaustiveness-checked rather than discovered. Regression-test one fetch-by-real-key per shape, not just the first-tested one.
- **An accessor returning an empty collection to signal "not applicable" is indistinguishable,
  to a generic membership filter, from "applies but matches nothing."** One generic list/search
  path often serves several row shapes and narrows by a `scope`/dimension filter through a
  per-type accessor — `SCHEMAS[type].keys(row) → string[]`, matched via
  `keys(row).includes(requested)`. Some types are legitimately never scoped by that dimension, so
  their accessor is a constant `() => []` — the author's way of saying "N/A here," sometimes with
  a comment saying so. The generic filter can't see the comment: `[].includes(requested)` is
  `false` whether the type is inapplicable or genuinely scoped-and-empty, so the whole type
  silently drops out of results whenever any caller passes that filter — no error, just fewer
  rows. This is the *design-intent* sibling of the nested-key accessor gap above: there the
  accessor is empty **by mistake** (unreachable nesting); here it is empty **on purpose**, and
  the generic predicate still can't tell the two apart. Represent inapplicability explicitly
  instead of overloading empty — a whole-type bypass from that filter's domain, a sentinel
  (`null`) the filter special-cases before calling `.includes()`/`.some()`, or excluding the type
  from the filter's domain entirely — never a bare empty collection a generic predicate reads as
  exclusion. (Same "generic code can't see a per-type intent" shape as `product-ux-quality.md`'s
  empty-state coverage rule — an empty render that can't tell "not queried" from "genuinely
  zero," there at the UI layer.) Most dangerous when the endpoint's own contract documents the
  filter as *narrowing* results rather than *excluding whole types*: supplying it then does the
  exact opposite of what the docs promise, silently (cross-ref `api-contracts.md` — behavior that
  diverges from the documented contract). Regression-test: a scoped search call, run against a
  fixture that includes an N/A-by-design type, must still return that type's rows.

**🚩 red flags** (this file):
a `scopeKeys`/`tags`/`labels`-style per-type accessor with a constant `[]` return (or a `// not scoped by X` comment) feeding a shared `.includes()`/`.some()` filter with no whole-type bypass, silently dropping that type from every scoped result;
