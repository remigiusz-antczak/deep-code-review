# Review method — situational checks

Read this when `method.md` routes here: a gate verdict is disputed, a finding must be reproduced, local and CI disagree, the target is containerized, native, or built against an exported reference, or a premise claims something is missing or broken. Split from `method.md`; bare "above" / "below" cross-references point within this file, and every other method rule stays in `method.md`.

**Phase 1 — gate disputes and target-shape preflights.**

- **Check a firing gate against its own standard first.** A gate *stricter* than
  the spec it implements (e.g. a contrast gate flagging disabled controls, which
  WCAG 2.2 SC 1.4.3 exempts) yields a "fix" that regresses another axis
  (principle 4): record the citation and **narrow the gate, saying so in writing**
  — narrowing an over-strict rule and weakening a real one look identical in the
  diff and are opposite acts. **The mirror: when the gate already matches its
  standard, a fix that would make it fail is what's wrong, not the gate** — do
  not weaken or suppress a correctly-calibrated gate to land it. Two correct
  constraints in apparent tension is a design problem, not a gate problem: find
  the design that satisfies both, or route it as an owner trade-off (principle
  4) — never a unilateral weakening. (A ratified assert-absent test is the same
  shape: `testing-and-evals.md`'s never-loosen-a-negative-assertion rule.)
- **Reproduce a gate's finding with the gate's own detector, not a hand-rolled
  probe.** Validating a fix aimed at an automated gate (linter, schema/contract
  validator, audit/policy gate) with a **bespoke approximation** ("I grep for
  X") that observes a *different thing* than the gate can "reproduce" a
  **passing** state (or a different failure): the fix targets the wrong cause,
  the gate stays red next run — or goes green for an unrelated reason and the
  real defect ships. **Read the gate's own detection source** (its rule, query,
  or script) and replicate it exactly — same matcher, inputs, config, and
  file/state — or better, **run the actual gate**; a probe is a fallback only
  when the gate cannot run, and must mirror its mechanism (reproduce the gate's
  **red** for the same reason first, then confirm the fix turns both green).
  This is repro fidelity w.r.t. the **detector** — distinct from the gate itself
  being wrong or unrun (`method.md` Phase 1 and `domain-b.md`'s "a
  non-empty result is not proof the layer ran"), from repro-fidelity w.r.t.
  **conditions** (`parallel-audit.md`'s reproduce-at-low-concurrency), and from
  `report-format.md`'s `mechanism-unproven` (a fix you *could not* reproduce;
  this is a repro you *did* run, with the wrong mechanism), and from repro-fidelity
  w.r.t. the **build environment** (the production-build bullet next).
- **Reproduce a built-artifact finding against the build it audits, not the dev
  server.** The same rule at the environment axis: a gate scoring the **production
  build** can surface a real defect (a WCAG focus-not-obscured failure under a sticky
  header) the **dev server never shows**, because minification, CSS ordering,
  hydration timing, and asset paths differ. A dev-server "I can't reproduce it" does
  **not** refute a production-build finding; reproduce against the artifact the gate
  scored (build it, or hit the deployed/preview URL), per the local≠CI rule (below).
  Converse: a dev-only symptom (hot-reload remount, dev-mode double-invoked effects, a
  dev overlay) is not a finding until a scripted path reproduces it on a production
  build. Exception: if the symptom traces in the code to a missing cleanup (an
  effect that subscribes, listens, or schedules and never tears down) or a
  non-idempotent effect (it posts, charges, or appends on every run), that code
  defect **is** the finding, cited at its `file:line` — dev double-invocation
  exists to surface exactly that, and a remount or re-run in production hits it too.
- **A no-regressions gate keys on *reachability*, not surface-position stability.**
  A destructive-change gate that watches a surface label or slot (a top-level nav
  entry, a route path, a menu position) false-fires on a legitimate reorganisation —
  a feature **moved** under a new parent reads as **removed** — and, worse, a
  label-presence check misses a genuinely **orphaned** route (still in the menu,
  reachable by nobody). Compute the invariant over the **before-vs-after reachability
  graph**: every prior capability still reachable through *some* path is not a
  regression no matter where it now sits; a capability reachable by no path is a
  regression no matter what label lingers. (For a nav/route reorg, "reachable" also
  means its deep-link history still resolves, not just that a menu entry exists.)
  Relocation is not removal, and a stable label is not proof of reachability.
- **Prove a verify gate *idempotent* — run it twice — not just green from a clean
  clone.** A gate whose steps **write artifacts a later step consumes** can pass
  once and fail on the **next** run against what the first run generated. Archetype:
  a `typecheck → build` pipeline where the build emits generated route types
  (`.next/types/**`) that a *subsequent* standalone `tsc --noEmit` then rejects — CI
  on a clean clone never sees it, the human re-running locally hits a confusing red,
  and the gate looks flaky when it is actually **order-dependent**. Run the gate
  **twice** (or clean the generated dirs first) and treat a second-run failure as a
  real finding. One concrete trigger: a **non-handler export from a framework route
  module** (a helper, constant, or classifier beside the handlers in a Next.js App
  Router `route.ts`) makes the generated validator reject the module — move pure
  logic to a sibling module.
- **Name *why* local and CI diverge — sources beyond the gate set.** (a)
  **Sharding / worker count** (the config-vs-baseline rule below): a spec order or a
  `--workers=1` fallback that never occurs under CI's sharded config. (b) **OS font
  metrics** — a CI image rounds glyph advance and line-wrap differently than a
  laptop, so a label wrapping at one width locally lays out under a tighter cap
  remotely; this is exactly why a layout assertion must test the **invariant** (does
  the text overflow its box? do two boxes intersect?), never an **absolute width or
  wrap-point** (`references/testing-ui.md`, geometry-not-pixels) — the
  invariant holds on both hosts, the pixel does not. (c) **Dirty local resolution** —
  a stale build cache or a **symlinked `node_modules`** borrowed from another
  worktree resolves different module versions than CI's clean `npm ci`, so
  `tsc`/lint/bundler disagree; reproduce a local-only green on a **clean install**
  before trusting it. "Green locally" stays `unverified` for CI until the divergent
  axis is named.
- **Classify a failure by *config* and *baseline* before calling it a regression.**
  A suite OOM-killed at its default parallel fan-out and re-run at `--workers=1` to
  fit memory changes the **execution model**, not just the speed: serial specs
  sharing one stateful backend pollute a later spec's precondition, so a failure
  seen *only* under the reduced config can be a harness artifact the sharded CI
  config never hits — not a product regression. The mirror error is as easy: a
  change *can* genuinely make a suite serial-fragile, so "it's just `--workers=1`" is
  also unverified. Two cheap runs settle it — **config axis:** reproduce the suspect
  specs under CI's *actual* worker config (a handful of specs won't OOM); pass there
  and it is not a gate failure. **Baseline axis:** run them under the *identical*
  reduced config on the merge-base; pass-baseline + fail-branch is a real
  code-introduced sensitivity worth hardening, fail-both is a pre-existing harness
  artifact (the baseline half of `method.md`'s unexplained-base rule). Report which
  config and which baseline the failure belongs to — "fails under `--workers=1`
  locally" and "fails the gate CI runs" are different findings.
- **Deploy-contract preflight** (containerized/serverless targets): lockfile
  committed ↔ install command, entrypoint/CMD file mode, build-time vs runtime
  data dependencies, and **boot the documented-minimal config and hit the
  health/readiness path** as a first-class Blocker gate (procedures:
  `references/infra-iac-containers.md`).

**An input reference is stale until you check its revision and completeness.** A
build/mirror/import task that consumes an **exported reference** — a design export, a
spec bundle, a data snapshot — is only as current and complete as that export: confirm
its **revision/timestamp** and **completeness** (actual vs expected item count) against
the authoritative source *before* building on it, or the output is confidently wrong and
still passes its own gates (the build-time analog of verify-before-you-report — an export
that silently lost half its items yields a mirror that faithfully reproduces the loss;
distinct from `data-quality.md`'s freshness/completeness *scoring dimensions* for a target's
own pipeline — this is input-export hygiene before you build). A cheap up-front
freshness/completeness check is owed by any "build against a reference"
workflow.

**Memory-unsafe code raises the floor.** If the target contains native C/C++ or
`unsafe` Rust on a reviewed path, a plain green test run is not ground truth: run
the sanitizer/race build the project provides (ASan/UBSan/MSan, `-race`,
`cargo miri`/`cargo test` under sanitizers) — or record the memory-safety verdict
as `unverified` and **name the artifact that would settle it** (the sanitizer job,
the fuzz corpus, the `unsafe` block's stated invariant), per principle 3.

**Phase 4 — premise checks.**

**A perception-sourced "it's missing" against code that already implements it is a
`delivery-gap`, not a build order.** When step (b) of `method.md`'s presence/absence rule confirms the capability *is*
present yet a reporter evaluated the surface as missing — "the product feels
static," "nothing responds," "there is no empty state," filed against code that
inspection shows already handles it — the perception is real evidence, and the two
reflexes are both wrong: **rebuilding** ships a second competing implementation (the
false-absence failure in `method.md`); **dismissing** ("works on my machine") ignores a real
user-visible fault. The finding is a **third verdict — `delivery-gap`**: the working
code is not reaching the surface the reporter saw. Diagnose *why* along three axes:
**build / environment drift** (a stale bundle, a symlinked `node_modules`, the
reporter on an old deploy — the surface they saw is not this tree); **route / mount
mismatch** (it renders on a route, flag, or persona the reporter never reached);
**preference / state gating** (gated on a default, role, or saved state that
suppresses it for them); or a **runtime / integration fault** (reached and mounted,
but the live channel never connects, the backend never emits, or an error is
swallowed). The deliverable is the *reason it did not reach them* plus the smallest
fix to close the gap — not a reimplementation. (Extends #250: the third outcome when
you *can* confirm the capability at runtime — beside confirmed-absent and
false-absent; unconfirmed-absent is the couldn't-boot branch in `method.md`.)

**A "broken / decorative / always N" premise is a claim to verify against live data,
not a fact to act on — and a flat metric can be the honest answer.** The same
discipline, one step earlier: a task or stakeholder's "field X is hardcoded /
decorative — make it real" is an *unverified claim*. Reproduce it first — measure the
live distribution and read the current code — before writing any fix; the "constant"
may be an initializer a later pass already overwrites, so the premise is stale and the
fix a no-op. And when the measurement holds — the value genuinely does **not** move —
that can be the honest truth of the corpus, not a defect to engineer away. Before
"making it vary," ask what moving it would *require*: if the only lever is
fuzzy/approximate matching or counting non-independent sources, inflating the number
**fabricates** it — the anti-fabrication rule applied to an "improve this metric" task
(an inflated-but-fake number is worse than an honest flat one; empty beats fabricated,
`SKILL.md` principle 3, *No fabrication*). The honest deliverable is to make the count **provable** —
retain the distinct corroborating evidence, add a gate that fails if a count ever
outruns its evidence — not larger. (The scored / shown cousins live in
`data-quality.md` scoring discipline and the confidence-tier false-precision rule in
`ux-dataviz.md`.)
