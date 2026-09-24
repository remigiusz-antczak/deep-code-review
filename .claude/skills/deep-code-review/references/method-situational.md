# Review method — situational checks

Read this when `method.md` routes here: a gate verdict is disputed, a green, CI status, re-run, or coverage figure is cited as evidence, a gate changed in the diff, a finding is carried forward, the target has a suppression ratchet, gates run per lane, a finding must be reproduced, local and CI disagree, the target is containerized, native, or built against an exported reference, or a premise claims something is missing or broken. Split from `method.md`; bare "above" / "below" cross-references point within this file, and every other method rule stays in `method.md`.

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
  shape: `testing-situational.md`'s never-loosen-a-negative-assertion rule.)
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

**Phase 1 — trusting a green, self-graded, or carried-forward verdict.**

- **`method.md`'s planted-defect matrix proves a gate fails closed — it says nothing about which
  rule or query category the gate actually has turned on.** Alongside (a)-(d),
  read the enabled config itself (not just its presence) and record, by name,
  the active tier/category set: a linter's baseline config vs. a broader,
  opt-in one (typescript-eslint's own rule docs name the *exact* config that
  enables each rule, not just its coarser recommended/strict label — confirmed:
  `no-floating-promises`, `no-misused-promises`, and `unbound-method` are each
  enabled by extending `recommended-type-checked`; `no-unnecessary-condition`
  requires the separately-named `strict-type-checked`. A project extending only
  `recommended-type-checked` — already type-aware, already catching the
  promise/unbound-method class — has no guarantee it also carries
  `strict-type-checked`'s additional checks, `no-unnecessary-condition` among
  them: verify the actual config name, don't infer coverage from "type-aware
  rules are on"), a SAST
  tool's default query suite vs. a broader named one (CodeQL ships three
  distinct suites — `default`, `security-extended`, `security-and-quality`), or
  a linter's documented default rule selection vs. an expanded one (ruff's
  `select` setting docs document a default selection distinct from `select`,
  and show `extend-select` adding whole categories "on top of the defaults" —
  e.g. flake8-bugbear `B` — confirming a real default/expanded split without this
  skill pinning exact counts, which drift across releases). A gate that is
  present, non-empty, correctly scoped, and not excluding the changed path can
  still be calibrated to a tier that structurally cannot catch the class in
  question — that gap is invisible to (a)-(d) because the config isn't missing,
  empty, wrong, or path-excluding, it is simply narrower than the review needs.
  When it is, name the omitted class in the report (e.g. "this config's enabled
  rules don't include the check that would flag a type-proven-unreachable
  branch") as a fact for the reviewer/owner to weigh — this records what the
  gate cannot see, it does not mandate raising the tier (principle 5: judge a
  gate's calibration in context, don't impose a stricter one).
- **A gate changed in the diff it gates is self-certified — re-run its base
  version.** When the diff touches an **enforcement artifact** (a gate / CI /
  privacy / lint / hook / checksum script that decides pass-fail), the green run
  used the **shipped, possibly-weakened** copy grading itself. Judge the change
  with the **base** copy instead: `git show <BASE>:path/to/gate.sh >
  /tmp/base-gate.sh && bash /tmp/base-gate.sh` against the new tree (or diff
  base-vs-head of the script and read what the change stops catching). A gate
  that only ever grades its own author is `unverified`; a change that **narrows**
  what it catches while staying green is a Blocker on the same footing as a
  planted defect that survives.
- **A CI re-run certifies the SHA it ran, not the PR head.** "Re-run all jobs" on
  most forges re-dispatches the **original, frozen payload SHA**, so a re-run that
  goes green can be certifying a **stale tree** after the head moved on — the
  moved-tree twin of the self-certifying gate above: a status names the surface it
  graded, here the **commit**, so a green whose SHA is not the PR's current head is
  `unverified` for the head. Read the run's commit, not only its colour.
- **Re-validate a carried-forward finding before repeating it — a finding without a
  re-run is a hypothesis.** A finding captured at one SHA (the report's `START_SHA`,
  `report-format.md`) is current only for that tree; before repeating it in a later
  session, re-check the `file:line` still exists at HEAD **and** re-run the gate or
  probe that surfaced it. Carried forward unchecked it is `unverified`, not
  still-open, and the report's `START_SHA` is what tells a follow-up what to re-check
  against. It prevents two failures: repeating a finding **already fixed** in the
  intervening commits (a false positive that spends the owner's trust), and — worse —
  repeating one that **changed or worsened** as if unchanged, which over-claims a
  **trust-critical** status (rate that *claim*, not the staleness). A "still open"
  status holds only at the current SHA. **Mandatory before acting on or closing any
  carried-forward finding or tracked issue:** re-check the fix's landmark reference or
  changed symbol against the target branch's current HEAD, then re-run the repro —
  `scripts/closes_lint.py --reverify <issue#|sha|symbol> --branch origin/main` fetches
  `origin` first, confirms the fix is present **and not later reverted**, and prints
  `STILL_OPEN` / `FIXED_AT <sha>` / `COULD_NOT_CHECK`.
- **A justification carried forward inside the *target's own* suppression list
  is a claim to re-verify, not a fact — and a green ratchet proves only that
  nothing was *added*.** Distinct from re-validating your own carried-forward
  finding (above): a shrink-only allowlist / ratchet in the target — a
  `.trivyignore` or audit-allowlist row, a lint-suppression or type-error
  baseline, a `# nosec` / `// eslint-disable` reason, a CODEOWNERS exception —
  carries a per-entry comment saying *why* it is still there ("false positive";
  "upstream fix pending, tracked in TICKET-123"). That comment was once true;
  when its blocking cause quietly goes away (the fix shipped, the ticket closed,
  the false positive became real) the entry and its prose are re-emitted verbatim
  into each regenerated baseline, so a dead rationale reads as current fact and
  the suppression is never re-examined — a list that only ever loosens. Two
  moves. **(1) Check the prose like an assertion:** it names something specific —
  a symbol, a call, a ticket id — so it is as falsifiable as a unit-test
  expectation; grep the current file for the blamed symbol (zero hits predate a
  since-landed fix), `git log -S` for when it left, read the linked issue's real
  state — *before* you repeat it, size work against it, or report it as status. A
  second reviewer who trusts the prose and restates it in a new issue/report has
  not corroborated it: that is one unverified claim copied twice, not two
  confirmations. **(2) Confirm the ratchet tightens:** its passing gate
  enumerates only "is this entry still present," never "is its reason still true"
  (`method.md`'s green-gate-clears-only-what-it-enumerated rule), so diff the entry
  **set** across baseline revisions and flag a list where entries only ever
  arrive and none ever leaves. Fix: each entry needs an expiry or re-verification
  trigger (a date, a linked-issue state check, a periodic sweep) — the lifecycle
  a grant needs beyond correct-scope-at-creation (`infra-iac-containers.md`) and
  the *allowed-not-required* discipline a size-pin already carries
  (`skill-authoring-and-size.md`). **Not** the phantom-contract case
  (`testing-situational.md`: a doc-comment naming a branch the code **never**
  implemented — never true); here the comment **was** true and drifted.
- **Lanes that pass in isolation do not clear their union.** Per-module,
  per-lane, or per-flag gates each green on their own say nothing about the
  integrated path they compose: a regression can live only in the combination —
  a shared resource, an ordering, a flag interaction — that no single-lane run
  exercises. Gate the **union that actually ships**, not only the parts; a suite
  that only ever runs the parts has left the combination surface unenumerated
  (same principle-2 scope: the union is a positive control no lane fired).

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
`data-scoring.md` and the confidence-tier false-precision rule in
`ux-dataviz.md`.)
