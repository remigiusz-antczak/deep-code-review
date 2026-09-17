# Review method — phases 0–6

Read this when executing a review: after stating `SCOPE` / `START_SHA` / `COVERAGE_LEDGER`, work the phases in order. This file holds the full phase procedures. `SKILL.md` keeps the map, principles, and gates.

## The review method

Work the phases in order. Skip a phase only when it provably does not apply, and
say so.

**Phase 0 — Map the target.**
- **Pin the review surface first.** On a git checkout: `START_SHA=$(git
  rev-parse HEAD)`; state it in the first-response line. Prefer reading via
  `git show $START_SHA:path` (or a dedicated worktree at that SHA). For `FULL`,
  default to a **dedicated `git worktree` or throwaway clone** so a concurrent
  agent cannot change what you are reading mid-review. **Detect a
  shared/mutating checkout:** run `git status --porcelain` twice a few seconds
  apart; note `git rev-parse --show-toplevel` vs any other agent working trees
  you can see. If the tree is dirty with unrelated in-flight work, or status
  changes between checks, treat it as occupied — use the worktree/clone and do
  not plant probes or write deliverables into the live tree.
- **Establish real history depth — never trust a prose claim.** Run
  `git rev-list --count HEAD` and `git log --oneline -5` (and
  `git rev-parse --is-shallow-repository`). A README that says "single commit /
  no history" while the count is large is a docs finding; more importantly it
  changes remediation (a tree scrub does **not** clean prior commits — secrets/
  PII in history need rotation + history remediation as an **owner decision**,
  not a silent filter rewrite). Cross-ref domain S / Q and principle 2.
- Entry points, pipeline stages, request/data flow (sources → processing →
  sinks), external dependencies, and trust boundaries (where untrusted input
  enters). Inventory every `TODO`/`FIXME`/`HACK`/`XXX`/"pending"/"temporary"
  marker in code **and** docs. **On a FULL / repo-level review (or when the
  request names branches or cleanup), also inventory the open branches and their
  merge state** — refresh first (`git fetch --all --prune`; an un-refreshed clone
  hides open work), then list branches with their last-commit age, ahead/behind,
  and any open PR — the raw material for the branch triage (domain S;
  `references/branch-and-merge-hygiene.md`). Skip this for a narrow `DIFF`/
  `FILE`, which stays a compact packet.
- Detect language(s), frameworks, build system, package manager, test runner, CI.
  State in one paragraph: what problem this code solves and how. For anything
  with a network or untrusted-input surface, sketch a **trust-boundary table** —
  `untrusted input → who can set it → what validates/authorizes it → what it can
  reach`; rows that reach money, writes, or secrets with an empty validation
  column are the adversarial pass's starting list. **Three enforcement rows are
  mandatory** (do not collapse them): (1) what the **host platform** claims to
  enforce (docs, portal, edge product); (2) what **this app's code** actually
  enforces; (3) what **preflight/CI** asserts (anonymous `200` on a
  data-bearing route is a **finding**, not a green check — it encodes the hole as
  health). Platform docs that call something "personalization" or "member
  context" (or similar) are **not** authorization unless the app proves it. For
  embedded / iframe / portal-hosted apps, also complete the **Identity Arrival Map**
  in `references/security-appsec.md` (document vs XHR vs bare curl) **before**
  proposing any gate.
- **Abuse row (optional, high-yield).** For trust-boundary rows that reach
  **money, writes, or secrets** — and only those — add six cells naming who could
  **Spoof / Tamper / Repudiate / Leak / Flood / Elevate** through that row, one
  short phrase each or `—`. Six cells on three rows beats a full threat model
  nobody finishes; the empty cells are the questions Phase 3 answers. Depth on
  the design-level version of this lives under **A06 Insecure Design** in
  `references/security-appsec.md`.
- **Banned remedies from recent reverts.** Scan recent history for auth /
  middleware / gate outages that were rolled back, e.g.
  `git log --oneline --grep='Revert' -i -20` and subject matches for
  `auth`/`middleware`/`gate`/`access`. **Also hunt gates that were deleted rather
  than reverted:**
  `git log --diff-filter=D --oneline -- '*middleware*' '*auth*' '*guard*' '*authz*'`
  — a gate path that once existed and no longer does is itself a **banned
  remedy**: do not propose re-adding it until the removal's root cause is
  named and addressed (the deletion is evidence the shape failed here). Treat
  reverted approaches the same way unless the revert message's root cause is
  explicitly addressed in the new proposal. **Cite the output in
  `REVERTS_CHECKED`** (commits, or `NONE`) and record the concrete rejected
  approaches in **`BANNED_REMEDIES`** (or `NONE`) — a reviewer who only reads `HEAD`
  (no middleware file) otherwise re-recommends the exact fix that already caused
  an outage. **Read the revert *body*, don't just count the revert** — one authored
  by whoever shipped the failure often states the root cause and the **invariant it
  establishes**; carry both forward as design constraints, since a new remedy that
  contradicts the invariant is the banned one in different clothing
  (`references/parallel-audit.md` carries it into fan-out as `REVERT_INVARIANTS`).
- **Triage-first (cheap, before fan-out).** Run the project's own
  `doctor`/preflight and any documented invariant checks; grep/scan the
  invariants the project itself claims; note obvious exposure (world-readable
  static dirs, unauthenticated health that leaks config). For networked apps,
  run the **anonymous GET sweep** early (`references/security-appsec.md`) —
  highest-yield catch for world-readable data routes. Report what these
  surface immediately — they often yield a large share of final value and scope
  the expensive Phase-2 fan-out. Then order the remaining audit by blast radius
  (Review mechanics).
- **Emit the coverage ledger** (the `COVERAGE_LEDGER` promised in the first
  response) before any domain work: the resolved archetype; which of domains
  **A–W** apply and which are N/A with the one-line reason; the `references/*.md`
  files this target **must** load; and whether an **anonymous GET sweep** and a
  **two-principal object-swap** are planned (`Y/N` each, with the reason for any
  `N`). **When the audit fans out, the ledger also tracks, per unit, who covers it
  — finder id *and* lead-read `Y/N`** — so a stall is visible (`references/parallel-audit.md`
  unit manifest). **Phase 5 reconciles the report against this ledger** — a domain
  the ledger called applicable but the report never rules on, or a fan-out unit
  whose finder never completed, is `unverified`, not a silent omission.

**Phase 1 — Establish ground truth.** Install/build with the documented steps;
record every deviation (a broken "one-command setup" is a finding). **Run the
project's own one-command aggregate gate by name** (`make check` / `npm run
verify` / …), not a hand-picked subset — and **never record a gate as clean
without confirming its exit code**; empty output is not a pass. **A pipe reports
the last stage's status, not the gate's** — capture then read `$?`, or the gate is
`unverified` (`gate | tail`, SIGPIPE `141`, `grep -q` inversion:
`references/language-stack-redflags.md`). **Never `2>/dev/null` a fact-establishing
step** — it turns "does not exist" into "clean" — and a gate that would "look
passed" if absent is itself a finding. Run the full test
suite (pass/fail, coverage, skipped/flaky), linters, type-checkers, formatters,
and any wired security/dependency scanners. Then, before trusting "green":
- **Enumerate what the gates exclude, and audit it separately.** Read the
  lint/type/test/CI config for `exclude`/`ignore`/path-filter entries and any
  nested project with its own manifest; run each excluded subtree's own gate or
  state it has none. Report coverage **per subtree** (`root: N pass (excludes
  X)` + `X: M pass (separate gate)`) — never an unqualified "tests pass" when any
  code is gate-excluded. "Green root gate + excluded privileged subtree" is a
  finding in its own right: coverage gaps concentrate where risk does.
- **Prove each gate can fail.** Confirm the gate actually runs in CI, then —
  **by default in a dedicated throwaway worktree/copy at `START_SHA`** (never
  plant into a working tree another process can commit from; a verified-clean
  live tree is allowed only when you have confirmed the checkout is unshared and
  idle) — plant a minimal defect it should catch (a throw, an undefined
  identifier, a banned string, a format break), confirm it goes **red and the
  reported count/exit changes**, then revert and **confirm the revert**. (This
  transient, self-reverting probe is the one code mutation the read-only default
  permits — principle 7.) A gate that stays green on a planted defect is a
  **Blocker/Critical reported before any code finding** — it invalidates the
  ground truth everything else builds on. **Planted-defect matrix (config
  gates):** exercise at least (a) **missing** config, (b) **empty /
  whitespace-only** config, (c) **wrong** config (wrong pattern / stale path),
  and (d) config that **excludes the path under test**. "Missing file fail-closed"
  does **not** prove empty-file fail-closed — empty banlists and blank allow-lists
  are a common silent green. Trace which test files the gate actually invokes;
  tests present but unwired are "decorative" (procedures:
  `references/testing-and-evals.md`).
- **A gate reports only on the scopes that actually ran — a skipped scope is
  `unverified`, not clean.** A pass is evidence only where the enforcing surface
  could **see** the artifact it checks (`SKILL.md` principle 2). A multi-scope gate
  that **skips** a scope whose input is absent — a privacy gate whose *identifier*
  scan needs a pattern list (`.banlist.local.txt`, a `PRIVACY_BANLIST_EXTRA`) and,
  when it is missing, runs only the *secret* scan yet still exits 0 — has not
  cleared the skipped surface. Read **which scopes ran**, not the bare exit code; if
  the gate prints only a pass, missing per-scope reporting is itself the gap. A
  green privacy exit with the identifier scope skipped is **not** "boundary clean":
  a status claiming it is over-claims a **trust-critical** surface — rate the
  *claim* **Critical**, not the gate. Same shape as the empty-banlist silent green
  above — the check ran, but not over the thing you needed cleared.
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
- **Check a firing gate against its own standard first.** A gate *stricter* than
  the spec it implements (e.g. a contrast gate flagging disabled controls, which
  WCAG 2.2 SC 1.4.3 exempts) yields a "fix" that regresses another axis
  (principle 4): record the citation and **narrow the gate, saying so in writing**
  — narrowing an over-strict rule and weakening a real one look identical in the
  diff and are opposite acts.
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
  being wrong or unrun (the bullets above and `domain-checklists.md`'s "a
  non-empty result is not proof the layer ran"), from repro-fidelity w.r.t.
  **conditions** (`parallel-audit.md`'s reproduce-at-low-concurrency), and from
  `report-format.md`'s `mechanism-unproven` (a fix you *could not* reproduce;
  this is a repro you *did* run, with the wrong mechanism), and from repro-fidelity
  w.r.t. the **build environment** (the production-build bullet next).
- **Reproduce a built-artifact finding against the build it audits, not the dev
  server.** The same rule at the environment axis: an audit gate that scores the
  **production build** (a bundled/minified deploy artifact) can surface a real defect
  — a control obscured by a sticky header, a WCAG focus-not-obscured failure — that
  the **dev server never shows**, because minification, CSS ordering, hydration
  timing, and asset paths differ between them. A dev-server "I can't reproduce it"
  does **not** refute a production-build finding; reproduce against the same artifact
  the gate scored (build it, or hit the deployed/preview URL), the way the local≠CI
  rule names the divergent axis (below). Chasing it on the dev server fixes the wrong
  tree, or dismisses a live defect.
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
  status holds only at the current SHA.
- **A green gate clears only the surface it enumerated — not one it never
  visited.** A gate that ran and passed proves something about the routes,
  states, and inputs its coverage set actually reached; a surface it never
  enumerated (a route the sweep never requested, a state no fixture constructed,
  a branch no test input exercises) is `unverified` under that green, not clean.
  (A gate the config *declares* excluded is a different gap — enumerate those per
  the gate-exclusion bullet above; this is the surface nothing pointed at.) Read
  the gate's coverage set and confirm it **includes** the surface in question
  before reading its pass as a clearance — SKILL.md principle 2 (*an absence is
  evidence only after a positive control fires*) at gate-coverage scope. This is
  the **unvisited** surface: distinct from a gate that cannot fail (above) and
  from a probe that observed the wrong thing (detector fidelity, above) — here
  the gate fails correctly, it was simply never pointed here.
- **Lanes that pass in isolation do not clear their union.** Per-module,
  per-lane, or per-flag gates each green on their own say nothing about the
  integrated path they compose: a regression can live only in the combination —
  a shared resource, an ordering, a flag interaction — that no single-lane run
  exercises. Gate the **union that actually ships**, not only the parts; a suite
  that only ever runs the parts has left the combination surface unenumerated
  (same principle-2 scope: the union is a positive control no lane fired).
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
- **Read the host CI, not only your own shell.** Fetch the base branch's latest
  pipeline conclusion (`gh run list --branch <base> --limit 5`, or the forge
  equivalent); "green locally" is not "green in CI" (different OS image, browser
  binaries, gate set). A red, unexplained base is `unverified` ground truth — say
  whether it is a flake, pre-existing and unrelated, or caused by this work — and
  you cannot show a change "regresses no axis" against a baseline already failing.
- **Name *why* local and CI diverge — sources beyond the gate set.** (a)
  **Sharding / worker count** (the config-vs-baseline rule below): a spec order or a
  `--workers=1` fallback that never occurs under CI's sharded config. (b) **OS font
  metrics** — a CI image rounds glyph advance and line-wrap differently than a
  laptop, so a label wrapping at one width locally lays out under a tighter cap
  remotely; this is exactly why a layout assertion must test the **invariant** (does
  the text overflow its box? do two boxes intersect?), never an **absolute width or
  wrap-point** (`references/testing-and-evals.md`, geometry-not-pixels) — the
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
  artifact (the baseline half of the unexplained-base rule above). Report which
  config and which baseline the failure belongs to — "fails under `--workers=1`
  locally" and "fails the gate CI runs" are different findings.
- **Deploy-contract preflight** (containerized/serverless targets): lockfile
  committed ↔ install command, entrypoint/CMD file mode, build-time vs runtime
  data dependencies, and **boot the documented-minimal config and hit the
  health/readiness path** as a first-class Blocker gate (procedures:
  `references/infra-iac-containers.md`).

**How much ground truth the scope owes** (don't run a `FULL` gate ritual to
review ten lines, and don't skip it on a repo):

| Scope | Gate work owed |
|---|---|
| `FULL` | The whole matrix above: aggregate gate by name + exit code, per-subtree coverage, and the planted-defect probe (missing / empty / wrong / path-excluding config). |
| `DIFF` / `FILE` | Run the tests that **cover the changed paths**, and read the **CI path-filters** for those paths — a change under a filtered-out path is effectively ungated, which is a finding. **Plant only when the gate itself is what changed**; otherwise state the probe as out of scope. |

**A tool-produced count is a floor until you check for a cap.** Before quoting a
count a script emits, grep the script for a `limit`/`slice`/`head`/`take`/`break`
or early return on that collection and label the number `>= n` when one exists —
an instrument that stops recording at six reports six, not the total (distinct
from the caps *you* impose).

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

If a pipeline/app exists and running it is cheap, safe, and non-destructive, run
it and capture the **before** output for a later quality-delta. Never touch paid
APIs or production data without approval. Anything that won't build, test, or run
as documented is a Blocker until proven otherwise.

**Phase 2 — Domain audits.** Walk every applicable domain section (A–W). For
each, produce findings with `file:line` + impact + fix. Load the domain's
`references/*.md` for detection procedures. Domains that don't apply are marked
N/A with a one-line reason. Start from Phase 0's triage-first hits and blast-
radius order. **Stated invariant / landed guard → bypass census:** when a module
states an invariant or a guard lands on one path, inventory callers/entry points
that can skip it (procedure: `references/security-appsec.md` for untrusted egress;
`references/data-quality.md` for artifact→consumer). When the target is large,
run these as parallel one-invariant audits under the contract in
`references/parallel-audit.md` — read-only toolset, pinned `START_SHA`,
identifier masking — and re-verify every subagent finding at source before it
enters the report. **Concurrently with the fan-out, the lead reads the top-N
highest-blast-radius files independently and adversarially** (N sized to the
target; Phase 0's triage ranks blast radius) — so a hardened, zero-survivor
fan-out still has a **non-empty confidence basis**, the finders' empty returns are
cross-checked by a second independent read, and a slow or stalled unit never leaves
the highest-stakes surface unread. Phase 5 reports this lead-read coverage
alongside finder coverage. **A refused delegation is not a blocked domain:** if a
specialized subagent rejects a free-form domain prompt (fixed prompt shape,
single-shot, wrong review type), immediately retry **once** with a
general-purpose subagent or run the audit in-process — under the same read-only,
pinned-ref contract — and note the substitution. Never let a harness's prompt
contract stall **A01/domain B**; the fallback is the audit, not a skip. Depth:
`references/parallel-audit.md`.

**Product UI (domain P) → rendered route sweep.** On a `FULL` or broad-`DIFF`
review of a product UI, enumerate every route and rule domain P on each across the
render matrix, reporting coverage as a ledger — the domain-P analogue of Phase 3's
anonymous-GET sweep, and the step that turns per-route rules into whole-product
coverage. Procedure and the matrix: `references/product-ux-quality.md` (*Rendered
route sweep*). A route not rendered is `unverified`, not clean.

**Rewritten browser spec → account for the retired coverage.** When a `DIFF` rewrites an
existing browser/E2E spec because its target surface became unreachable in the test
environment, do not pass the rewrite on its new-surface green: check that the coverage
the old spec provided is named as a gap and pinned by a source-level structural fallback,
and flag its absence as a finding. Procedure: `references/testing-and-evals.md` (*A
rewritten browser spec names its retired coverage*).

**Phase 3 — Adversarial / red-team pass.** Switch to attacker mindset (section
below). For any networked app, work these **openers in order** before the
creative attacks — they are ordered by yield, and each one narrows the next:
1. **Anonymous GET sweep** — every documented GET with no cookies and no Bearer;
   flag every large or identity-bearing `200`.
2. **Two-principal object-swap** — authenticate as A, request B's object ids; a
   `200` is IDOR regardless of how the UI hides it.
3. **Dual-surface every caller of the same loader** — the API handler *and* every
   RSC/SSR page/route that calls it; one redacting while another does not is the
   common shape.
4. **Then** injection, SSRF, traversal, prompt injection, exhaustion, races.

Procedures for all four are in `references/security-appsec.md`. Then actively try
to break auth, inject, exfiltrate, exhaust, poison, and to find useless/costly
work. Assume a hostile user **and** a hostile upstream.

**Phase 4 — Synthesize & rank.** Deduplicate, assign severity, separate blocking
from non-blocking. Note systemic patterns (one root cause behind many symptoms)
rather than listing every instance. **A finding matching a copyable idiom** — a guard
expression, a state-check, a data-flow pattern pasted rather than abstracted
(`disabled={!x}`, an unchecked identity flag, a hydration-gate) — is scoped by **grepping
the idiom across the tree in the same pass**: the search result *is* the blast radius,
reported as one class-finding with its full instance set (how many sites, and where),
never the first callsite alone. Stopping at one site under-scopes the finding and leaks a
second fix into a later increment — the review analogue of the *one component per concept*
duplicate-twin sweep (`product-ux-quality.md`), for a bug pattern rather than a duplicated
component; after the fix, a re-grep of the idiom confirms none remain (the class is closed
only when that search returns clean — a zero-survivor check, principle 2). Also identify
**compounds** — findings from
different domains where one disables another's safeguard; a compound's severity
is the joint effect, which can exceed either part, so state it as one finding
with the fix order. **Distinguish a live defect from a documented past one:**
comments often narrate fixed incidents in present tense — before reporting, check
(a) is there a test pinning the corrected behavior? and (b) does
`git log -S'<symbol>' --oneline` show the fix already landed? If either is yes,
it is a historical note, not a finding. **Distinguish a defect from intended
behavior a test encodes:** before reporting, check whether the proposed fix would
break an existing **passing** test — if it would, the flagged behavior is intended
by design (the fix is wrong, not the code), so it is `REFUTED`, not a defect.
Re-reading the source the finder read cannot catch this class — the source looks
exactly as described; only the tests and the suite encode intent, so locate the
tests that exercise the finding, and for a change to security/cost/concurrency
logic apply the fix in a throwaway worktree and run the suite before confirming
(`references/parallel-audit.md` §4). **Weigh the failure direction** (fail-open vs
fail-closed) as an explicit severity axis — see the rubric below. **Snippet-or-drop:** every surviving
finding carries a **verbatim snippet re-read at the pinned ref** — `git show
$START_SHA:<file>` (or a byte dump per principle 2 when the claim hinges on
invisible characters). A finding you cannot quote at `START_SHA` is `unverified`
with the artifact named, or it is dropped; a paraphrase from memory is how a
plausible-but-absent line number reaches the report. A **quantitative** claim (a
count, a metric, a before/after delta) likewise names the ref it was measured at,
inline — "N at `origin/main`", or "in the uncommitted tree" when the working tree
is the subject; on a dirty checkout those are two different products.

**Presence and absence are not the same claim.** A **presence** finding carries its own
evidence — the file and line — and a reader checks it in seconds. An **absence** finding
("X is missing," "there is no Y") claims that *no* implementation exists anywhere, and it
is **unfalsifiable from the report alone**: the report cannot show the thing it did not
find, so an absence inherits the **searcher's vocabulary** — any capability written in an
idiom the searcher did not try reads as missing. Absence findings are the
highest-leverage and least-verified thing an audit emits, because under parallel delivery
an absence is read as a **work order** (build the missing thing), and a false absence
becomes a second, competing implementation next to the working one. So hold an absence to
a higher bar: (a) **search by behaviour, not one idiom** — enumerate the encodings a
concept can take (a focus ring is `ring` / `outline` / `stroke` / `box-shadow` / a
rendered overlay; navigation is a route / query param / hash / id-keyed overlay; state is
a class / data-attr / ARIA / component state) and grep all of them, since one pattern is
one hypothesis, not a survey; (b) **confirm the absence at runtime** — render it and look
(principle 2: *an absence is evidence only after a positive control fires*); if you could
not boot (memory pressure, no build), the finding is **`unverified` — unconfirmed-absent**,
not a gap; (c) when it leaves for a downstream builder, the brief instructs the builder to
**re-confirm the gap before building** and report back if the capability already exists;
(d) a disproven absence is **reported back loudly** to whoever holds the inventory, or the
same false gap is re-briefed to the next lane. The verification surface a finding names
(`report-format.md`, *name the procedure*) includes, for an absence, the search space it
covered.

**Anti-slop (drop before the report).** A finding that does not change an
owner action is not a finding. Drop or demote to Nit/Info:
- a missing community-health file on a **private** repo with no outside
  contributors (already batched in `docs-and-dx.md`);
- restyling, renaming, or "consider maybe" with no defect;
- a second copy of a fact the project's own gate already enforces and the
  review already confirmed green;
- a recommendation that would break a passing test (already `REFUTED`);
- a kit leftover (`AGENTS.md` / `CLAUDE.md` still describing a scaffold
  `app/` layout while the real product lives in `apps/` or `packages/`) —
  that **is** a finding, but **one** DX finding with the smallest fix
  (rewrite the leftover to match the tree, or delete it). Do not also
  emit a wall of "add more docs" on the same files.
Chat BLUF lists **confirmed defects that would change a merge or a
ship**, not a catalogue of every possible improvement.

**Phase 5 — Report.** **Default delivery is two artifacts, and neither is a
commit into the reviewed repo:** (1) a **chat BLUF, ≤30 lines** — one-line
verdict, the top ≤5 **confirmed defects** in plain language, a one-line
`Decisions: N` pointer (not product ideas filling defect slots), and the path to
the full technical table; and (2) the **full report written out-of-tree**
(`~/Downloads/`, session scratch, or the PR comment). **The full report carries an
"Invariants verified to hold" section, co-equal with the findings table** — the
specific security/correctness properties each unit (and the lead's independent
read) opened the code and confirmed, each grounded at `file:line` with the same
snippet-or-drop rigor a defect gets. On a **hardened target this is the primary
deliverable**: a finding-count report has the least to say exactly when the owner
needs the most reassurance, and "here are the N properties we opened the code and
proved" is worth more than "we found nothing." An affirmative claim is as
falsifiable as a defect claim — drop any you cannot quote at `START_SHA`.
Product/redesign ideas go
under **Decisions needed (owner)** — they never carry Blocker/Critical gate
language. Severity still follows consequence: a product choice that creates a
Critical defect remains a defect. **Never paste the machine findings table as
the first chat bubble** — a 15-domain table buries the verdict it was supposed
to deliver. **The two-artifact report is owed on `FULL`;** on a `DIFF`/`FILE` you
are also fixing, a compact `found → root cause → fix → re-gate` trail may stand in
for the out-of-tree report (snippet-or-drop still applies).

**Fix the failing layer, not the first plausible one.** A "missing value / blank
field / missing tag" symptom on a rendered surface is not automatically a *render*
bug — the render path is often already correct and the gap is one layer down: the
field is empty **at the source**, or a **config / derivation / mapping** step never
ran. **Localize before patching** — prove which layer fails (*is the value present at
the source? does the derivation/mapping run? is it purely a render bug?*) and fix
**that** one; a presentation "fix" over a data gap is a no-op at best, and a
hard-coded view fallback is worse — it **masks** the gap and reads as resolved.
**Name the proven-failing layer in the finding** so a downstream implementer doesn't
re-patch the wrong one. And watch the **two-layer** case: a durable fix usually needs
both a **correct default going forward** *and* a **backfill of the existing records**
that already carry the gap — fix only the default and old data stays broken; fix only
the backfill and new data re-breaks. (The specific, high-frequency instance of
principle 9, *root-cause not symptom*.)

**Writing into the repo's `code-review/` directory is opt-in.** It requires the
user's explicit confirmation (or an explicit `--write-report`), *and* an unshared,
idle checkout; on an incident day or with a hotfix in flight, stay out-of-tree and
offer to commit on a **dedicated review branch** afterward. Never write into a
checkout another agent is committing from. When the report **is** committed, see
"Human-readable report" below for the template and the post-write privacy re-scan.

**On a public remote, a fork, or any repo whose history strangers can read, a
committed report is disclosure.** Commit only **finding ID + severity + area** —
the reproduction, the payload, the exact route/parameter, and the sample of
exposed data stay in the session output or a **private security advisory/PR**
until the fix ships. A committed review that hands a reader a working exploit for
an unpatched hole is a net-negative deliverable (principle 4).

**Reconcile against Phase 0's coverage ledger before you close.** Every domain the
ledger called applicable is ruled on (finding, clean, or `unverified` + artifact),
every must-load reference was actually loaded, and the planned anon-GET /
two-principal probes either ran or are reported as not-run with the reason. A
ledger line with no verdict means the review is unfinished, and the verdict says so.
**When the audit fanned out, reconcile coverage per unit — who actually covered it
(finder id **and** lead-read `Y/N`) — and mark any unit whose finder did not
complete (slow, capped-out, crashed, refused) `unverified`, never absorbed into an
implied all-clear.** The "no silent caps" principle applies to the fan-out's own
completeness, not only to sampling inside a unit.

**Reconcile the report's *claims* against the delivered artifact, not only its
coverage.** The ledger reconciliation above asks *did every applicable surface get
ruled on*; this asks the sibling question — *does the artifact contain everything the
report says it does*. Enumerate the report's own claims — each finding's asserted
fix-state, each definition-of-done line, each "changed X" — as a list, and join every
one to the artifact that would prove it (a committed hunk, a passing test, a file that
exists), reporting **present, partial, or absent** and surfacing your own misses, not
only confirming hits. Join to the **committed diff**, never to a sub-agent's or a
lane's *report* of what it did — the per-unit rule above records the lead's own
independent read (`lead-read Y/N`), not the finder's word that a unit is clean, and the
same holds for what a delegate claims it changed. Run this
**before you close, unprompted**: a completeness audit that only fires after the owner
asks "did you actually do all of it?" is not a control but a retrofit, and the
question itself is the signal the audit was owed earlier. It is cheap — the claim list
already exists and the diff is already in hand. This is the *set-completeness* question
that precedes per-claim verification: whether every claimed item is present at all,
before asking whether each is backed by a real surface rather than a favorable proxy.

**For a `DIFF` of a PR/MR** (often
a fork or an API-fetched change with no writable checkout) **the deliverable is
the review comment on the PR itself, not a committed file** — never add
`code-review/…` inside the very diff under review. **After writing it into the
repo, re-run the project's own privacy/name gate and link-check over the new
file** — it is untracked content the gate scans, and writing it can turn a clean
tree red. Surface every decision that needs a human owner. **Advise fixes; do
not auto-implement security/authz gates in this phase** — "helpful middleware"
is how outages ship when the Identity Arrival Map was skipped; security changes
ride a **separate** PR. **Split the remediation by risk surface:** when the
review yields both routine fixes and a change to a security/permission/authz
boundary, land them in **separate PRs** — the security-critical diff on its own,
small, flagged for a decorrelated reviewer, never buried under nit commits. Fixes
ride on a branch + PR (gated on approval), never a direct push to the default
branch. **For a FULL / repo-level review with open branches, also emit the
branch & merge triage** (domain S) — one recommendation per branch with the
exact command; acting on any of it (merge, delete, push, rebase) is
destructive/shared-state and runs only on explicit approval.

**A `mechanism-unproven` fix does not close its finding.** Report it as *mitigation
applied, cause unconfirmed*, keep the finding open at its original severity, and
name what would settle it (N green runs on the same job; the repro landing
red-first). For an intermittent failure "the symptom stopped" is not evidence —
never write "fixed" where the mechanism was only inferred.

**Phase 6 — Imprint standards (opt-in; writes to the repo).** Offer to persist a
tailored standards set so the bar holds on future iterations — a canonical
cross-vendor `AGENTS.md` (with `CLAUDE.md` and any peer agent files as thin
pointers to it), the pre-commit/CI gates, templates, and — where the repo will be
reviewed by a first-party bot — an optional **review-scoped rules block**
(`REVIEW.md` or a `## Code Review Rules` section, `references/docs-and-dx.md`),
distilled from this review's findings and the project's actual stack. This phase **writes**, so
it requires confirmation and must be net-positive and non-destructive:
**idempotent and additive** — detect-and-stop if present, create-if-missing
(never silently overwrite a good file), add only missing lines to a shared file,
and print what changed; defer to an existing style guide. **Pair each imprinted
standard with the gate that enforces it** — a doc alone is advisory — and if the
repo carries more than one agent-instruction file (`CLAUDE.md`/`AGENTS.md`/peers),
keep them from diverging. See `references/docs-and-dx.md`.

---

