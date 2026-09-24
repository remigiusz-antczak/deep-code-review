# Dependency upgrades at scale (many repos / many packages / agents doing the bumps)

Read this when the request is not "review one bump" but "catch up N repos" or
"clear the outdated-dependency backlog" — an update bot or an agent is opening
or driving many upgrade PRs at once. This extends
`dependency-currency-and-upgrades.md` §2 (the single-bump discipline still
applies to every PR this file's batching produces) with the **batching,
cadence, and reviewer-checklist** layer that discipline doesn't cover on its
own. Do not restate §1–§4 of that file here — this is additive, not a second
copy.

Standards this file tracks (verified URLs + dates in `docs/standards-index.md`):
Renovate (automerge, `packageRules`/`separateMajorMinor`, scheduling), GitHub
Dependabot grouped updates, npm `audit signatures` (registry-signature +
provenance verification).

---

## 1 — Batch by risk tier, one ecosystem per PR

Never let one PR mix ecosystems (npm + pip in the same diff) or risk tiers
(patch fixes buried next to a major rewrite) — a reviewer (human or agent)
cannot approve a patch bump and reject a major in the same click, and a red
CI run doesn't tell you which of forty changes caused it.

1. **Split by ecosystem first.** One PR per package manager
   (`package.json`/`requirements.txt`/`go.mod`/…) even when a bot could
   technically group across them — different lockfiles, different audit tools,
   different reviewers.
2. **Split by tier second**, per Dependabot's documented grouping pattern: a
   group scoped to `update-types: ["minor", "patch"]` is safe to batch into
   one PR — its own docs show "All major updates will continue to be raised
   as individual pull requests" when a group excludes them, a documented
   pattern, not an unconditional default. Renovate's equivalent is
   `separateMajorMinor` (isolate majors into their own PRs) and
   `separateMinorPatch` (split minor from patch when even that grouping is too
   coarse for the target).
3. **Batching within a tier is fine; batching across tiers is not.** Twenty
   patch bumps in one ecosystem, one PR, is the *point* of grouping — it turns
   currency debt into one reviewable diff instead of twenty. Ten majors in one
   PR is not batching, it's ten unreviewed migrations wearing one diff. A
   security-advisory update never joins a tier batch either — it keeps its own
   fast-lane PR (`dependency-currency-and-upgrades.md` §2.6), and a batch is
   only valid grouping when it reverts as one group (§3.4 rollback).
4. **A PR that arrives already mixing tiers/ecosystems gets split before
   review, not reviewed as-is** — see the reviewer checklist (§4).

## 2 — Cadence: schedule the noise, cool down the risk

- **Schedule the sweep**, don't run it "always on" — Renovate's own rationale:
  "Because Renovate defaults to 'always on' and 'open PRs right away' it can
  overwhelm you with 'new PR' notifications. Use the schedule to control when
  Renovate looks for updates." At scale (many repos) an unscheduled sweep is a
  reviewer-attention denial-of-service, not a favor.
- **Cooldown, as standing bot policy, not a per-PR call.**
  `dependency-currency-and-upgrades.md` §2.5 sets the release-age cooldown
  itself and its security-advisory exemption; at scale, encode it once in the
  bot config so every repo gets it, rather than deciding per PR — otherwise a
  compromised or broken just-published release lands across dozens of repos
  before any single per-PR decision would catch it.
- **Automerge only the tier that earns it.** Automerge patch/minor once the
  aggregate gate is green and the release has cleared cooldown — "we recommend
  you enable automerge for any dependency update where you would select
  'merge' anyway" (Renovate). Never automerge a major; "most people would want
  to leave major dependency updates to a human to review first" (Renovate's
  own stated default reasoning).

## 3 — Per-bump discipline inside a batch (agent-runnable checklist)

Run this on **every** PR the batching above produces — batching changes the
grouping, not the bar each bump must clear
(`dependency-currency-and-upgrades.md` §2 still applies per dependency):

1. **Changelog / breaking-change scan** — `dependency-currency-and-upgrades.md`
   §2.3, plus: read *every* version between pinned and target, not just the
   target's own notes (a transitive minor can hide a breaking change a
   maintainer mis-classified).
2. **Lockfile-only vs manifest change — know which one shipped.** A patch/
   minor bump inside the manifest's existing semver range often only moves the
   **lockfile** (the manifest range didn't need to change) — lower risk, easy
   to eyeball. A bump that also edits the **manifest** version range is a
   deliberate range widen/raise and gets the full review; don't wave through a
   lockfile-only diff as "just formatting" without checking *what* moved and
   why (a lockfile-only PR can still pull in a new transitive package — see
   §4).
3. **Gate + canary** — `dependency-currency-and-upgrades.md` §2.4 (aggregate
   gate on the bumped tree) and §2.7 (canary/staged rollout for a bump that
   can't be fully exercised in CI).
4. **Rollback** — `dependency-currency-and-upgrades.md` §2.7: the pinned prior
   version is the revert target, so the lockfile diff stays the whole rollback.

## 4 — What a reviewer (human or agent) checks in a bump PR

A bump PR gets the same scrutiny as any other diff, aimed at what's specific
to a dependency change:

- **Tier/ecosystem purity** — does this PR mix a major with minors/patches, or
  more than one package manager? If yes, send it back to be split (§1) before
  reviewing content.
- **Lockfile diff sanity** — does the lockfile diff match the manifest diff
  (no manifest change with a sprawling unrelated lockfile rewrite, no lockfile
  drift with no manifest change at all)? A lockfile out of sync with the
  manifest is itself a red flag (`dependency-currency-and-upgrades.md`
  🚩 list).
- **New transitive dependencies** — did the bump pull in packages that weren't
  there before? Each new transitive is new supply-chain surface
  (`appsec-supply.md` A03) even though no one directly asked for it; a bump
  that triples the dependency count for a patch-level version change deserves
  a question before merge.
- **New or changed install/postinstall/lifecycle scripts** — a `postinstall`
  (or `preinstall`/`prepare`) script appearing in a new or bumped package runs
  arbitrary code at install time; flag it even on an otherwise-clean bump and
  confirm what it does before approving.
- **License changes** — did any updated (or newly-pulled-transitive) package
  change license terms? Cross-ref `SKILL.md` Q; a license change is a legal
  question, not a code-quality one, and doesn't get waved through with the
  version bump.
- **Registry-signature / provenance verification where available** — npm's
  `audit signatures` "will also verify the provenance attestations of
  downloaded packages"; run it (or the ecosystem equivalent) on the bumped
  lockfile before trusting a jump, especially a major or a freshly-published
  release (`dependency-currency-and-upgrades.md` §2.5).
- **Green gate, not just green diff** — never approve a bump PR on diff
  inspection alone; the aggregate gate result on the bumped tree is the
  evidence (§3.3).

## 🚩 Red flags (bulk-specific, additive to `dependency-currency-and-upgrades.md`'s list)

- A single PR spanning multiple ecosystems or mixing a major with minor/patch
  bumps — batching collapsed tiers instead of separating them.
- Automerge enabled for major updates, or for any tier with no cooldown/gate
  in front.
- A bot sweep running unscheduled across many repos, generating more PRs than
  reviewers can clear — currency work as attention-DoS.
- A bump PR reviewed and merged without checking for new transitive deps or a
  new install-time script, because "it's just a version bump."

## Cross-references

- **`dependency-currency-and-upgrades.md`** — the per-dependency upgrade
  discipline (semver risk sizing, changelog read, gate, cooldown, EOL-as-
  migration) this file's batching sits on top of; read that file first.
- **A03 (`appsec-supply.md`)** — transitive-dependency and install-script
  supply-chain surface referenced in §4.
- **`SKILL.md` Q** — license-change handling referenced in §4.
