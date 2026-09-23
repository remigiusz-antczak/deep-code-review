# Domain H checklist

Read this when domain H (Tech debt, dead code & maintainability) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### H. Tech debt, dead code & maintainability
- **Dead code & deps** removed (unreferenced code is maintenance + attack
  surface). **Duplication** unified judiciously — but three similar lines beat a
  wrong abstraction, and a one-caller "helper" is premature; where logic *must*
  be mirrored, link the source of truth in a comment **and** add a coherence test
  running one fixture through both paths. **Copies that must stay byte-for-byte in
  lockstep** — vendored modules, per-runtime-plane duplicates, generated-vs-source
  pairs — need a **parity test or a single generated source**, or they silently
  drift; flag the *missing guard*, not the duplication itself (a drifting second
  copy of a crypto/auth module would encrypt/decrypt or authorize differently on
  each plane — a security hazard, cross-ref B). A hand-maintained **allow-list of value
  combinations** (e.g. `(kind, category)` pairs) is a generated-vs-source pair like the others
  above — coupled to whatever generator/emitter actually produces those
  combinations: diff the allow-list against **every combination the generator can
  emit**; a combo the generator emits but the list omits silently drops or rejects
  it downstream. **One** implementation with **no** duplicate can
  still drift at its *callers*: when a single shared classifier/scorer/function serves two call
  sites that each build its inputs differently, the divergence lives in the **adapters**, not the
  core — test that the two call sites **agree on a shared fixture**, and derive their inputs from
  **one spec**, or one caller silently feeds the shared logic a different shape than the other.
  The same adapter drift shows up **at fix time**: patching a shared
  request/mutation body-builder (or a shared endpoint client) only where the bug
  was reported leaves its siblings on the old shape — grep every other call site
  to the same endpoint/mutation before closing the fix and **diff the field sets**
  each one sends, the field-shape analogue of scoping a fix to its full instance
  set rather than the first callsite (Phase 4). **Two duplicated *implementations* drift the same
  way on a semantic value** (distinct from the one-implementation-drifting-at-its-callers case
  just above): any **derived display value** computed as more than one helper — avatar initials,
  a truncated/short label, a masked id: grep the name *family* (every
  initials/short-label helper), not just the one function a report names. Where
  the canonical helper encodes a **data-minimization cap** (initials-only,
  last-4-only), a sibling that shows more is a **compliance gap, not a style
  nit** (cross-ref Q privacy).
- **Complexity**: one thing per function; shallow nesting; named constants/enums
  over magic values in one place. **Naming & structure** navigable by human and
  AI. **Dependencies current and safely upgraded** — see K and
  `references/dependency-currency-and-upgrades.md` (currency + safe-bump
  discipline; A03 for supply-chain integrity). Consistency with the surrounding
  code.
- **A source file git classifies as binary is unreviewable — never embed a raw NUL
  byte; escape other control bytes.** A tracked source file containing a raw **NUL**
  (`0x00`) — e.g. a delimiter constant written literally instead of escaped — is
  classified **binary** by git (the heuristic keys on the NUL): `git diff` /
  `git show` / `git log -p` print `Binary files … differ` (and `git diff --stat`
  shows `Bin`) instead of a text diff, so the change can't be read in its PR
  (`git blame` still runs, but garbled attribution is the only view left). `grep` /
  `ripgrep` won't print the matching line by default (suppressed, or reported only as
  `Binary file … matches`); `-a` / `--text` (grep) or `--text` (rg) forces it — so
  the file's identifiers can't be searched as written. A **non-NUL control byte**
  (`0x1F` etc.) does *not* flip git to binary — the file stays text — but the byte
  renders invisibly in the diff and is untypeable / un-greppable as written: a
  milder but real form of the same defect. Either way the code may run perfectly —
  this is a reviewability/maintainability defect **orthogonal to correctness**,
  invisible to a test- or correctness-focused pass. Use the language's escape (`\0`,
  `\x1f`) — ASCII, diffable, greppable, byte-identical at runtime. A commit/CI gate
  can flag any tracked source-path file git treats as binary (or containing a NUL) —
  cheap and deterministic (domain K).
- **A committed compiled/binary artifact is unreviewable code — a supply-chain
  surface, distinct from the NUL-byte case above.** The bullet above is a *text*
  source file git *misclassifies* as binary (a diffability defect); this is a
  *genuinely* compiled, opaque blob — a `.jar`/`.dll`/`.so`/`.dylib`/`.wasm`/`.pyc`,
  a prebuilt bundle, or a vendored SDK binary — deliberately checked into the tree.
  Nobody can source-diff it, so a **malicious swap is indistinguishable from a
  legitimate rebuild** in `git log` (OpenSSF Scorecard rates a checked-in binary
  **"Risk: `High` (non-reviewable code)"**). Build it from source in CI, or fetch it
  at build/run time from a registry/release-asset store; if a binary genuinely must
  be vendored (a licensed SDK, a firmware blob), pin it by content hash with
  recorded provenance beside it so a swap is detectable (domain K / A03, and A08 integrity failures). 🚩
  `git ls-files` showing a tracked `.exe`/`.dll`/`.so`/`.jar`/`.wasm`/`.pyc`; a
  `vendor/`/`third_party/` directory holding compiled output with no source or build
  recipe.
- **Feature-flag lifecycle**: each flag has an owner, a kill-switch, a test for
  both states, and a staleness/removal policy; dead flags are removed.
- **Lockstep surfaces** enumerated — the file sets that must change together
  (schema ↔ validator ↔ type ↔ prompt ↔ docs ↔ test).
- 🚩 commented-out blocks, `v2`/`_old`/`copy` files, duplicate helpers, dead
  flags, unused imports/deps, god-functions, byte-identical duplicated modules
  (per-plane, vendored) with no parity guard; a tracked source file git classifies
  as binary (a raw NUL byte) — undiffable, greppable only with `-a`/`--text`; a
  non-NUL control byte rendering invisibly in the diff.
- **Prioritize debt by team behavior (hotspot).** Rank the maintainability findings above by
  **change-frequency × complexity** from the target's own git history: the debt in the files the
  team keeps touching costs the most to live with. Severity stays the **primary** sort — a
  low-churn **High** still outranks a high-churn **Medium** (never bury it, principle 6) — and
  churn is the **tiebreak among findings of equal severity**: a structurally ugly file with
  **near-zero churn** ranks last in its band, a moderately-complex file rewritten every week
  leads its band. This is a **ranking lens, not a severity bump** — it never inflates a low-churn
  smell into a Blocker/High, nor demotes a real finding below its severity (the severity gate
  rules each finding on its own merits). Distinct from Phase-0 blast-radius, which ranks the
  *audit scope* across all domains: this ranks *maintainability debt* by where the team works.
  Compute churn from the target's own git history (e.g.
  `git log --format= --name-only <range> | sort | uniq -c | sort -rn`); where history is absent
  (shallow clone, fresh import), say so and fall back to complexity alone rather than invent a
  churn number.
