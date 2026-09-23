# Domain K checklist

Read this when domain K (Build, CI/CD, supply chain & release) is applicable in Phase 2 — the coverage ledger marks it, or a DIFF quick-path touches it. Split from `domain-checklists.md`, whose preamble (the 🚩 convention and the language-grep pointer) applies here.

### K. Build, CI/CD, supply chain & release → `references/release-engineering.md`
Two halves: build/supply-chain (below) and the **release** half — feature-flag
lifecycle, canary/blue-green claims vs actual config, DORA-or-`UNMEASURED` —
`references/release-engineering.md`.
- One-command reproducible build; lockfiles committed and honored; CI gates
  merge on lint + format + type + tests + security/dependency scan.
- Third-party CI actions **pinned to a commit SHA** (not `@main`/`@v3`), bumped
  by a bot that passes the same gates; secrets from the CI store, never echoed
  (`set -x` leaks). **Package-signature verification is blocking**; transitive-CVE
  audit is advisory. SBOM + build provenance (SLSA) for releases; rollbacks
  possible; **verify identifier ownership before deploy** (a slug/app-id another
  service owns gets silently clobbered).
- **Dependency currency & safe upgrades** → `references/dependency-currency-and-upgrades.md`.
  Are third-party deps, runtimes, and base images on a supported **latest-stable**
  version, with no known-vulnerable or EOL/unmaintained/deprecated components
  (audit the **committed lockfile**, transitive deps included)? And is upgrading
  *disciplined*: one dep/group at a time, changelog/migration read, risk sized by
  the **semver delta** (a MAJOR is a breaking change by definition), lockfile
  regenerated, the new release checked it isn't itself malicious (cross-ref A03),
  and the project's **own aggregate gate proven green on the bumped tree** before
  merge? Staleness is an A03 security risk; a blind jump to "latest" is how a
  breaking or hijacked version lands — the review closes the *risky* gap through
  the gate, it does not bump everything. Rank by exploitable consequence: a
  known-exploited CVE on a reachable path is Critical/High; merely-behind-latest
  with no vuln is Low/`Nit:` currency debt (batch it, recommend an update bot),
  never outranking a real defect.
- The **privacy/PII gate fails closed when its banned-terms input is missing**,
  scans the lines a branch adds (fork PRs included), and never echoes a match.
- 🚩 green CI that skips tests, secrets in CI logs, actions on a mutable tag, no
  dependency scan, non-reproducible build, deploy without ownership check, a
  known-vulnerable or **EOL** dependency/runtime/base image shipping, a single
  "update all dependencies" commit with no per-dep test evidence, no update-bot
  config (`dependabot.yml`/`renovate.json`) beside a long tail of outdated deps.
