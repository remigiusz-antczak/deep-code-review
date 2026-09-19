# Standards index

Every standard the skill relies on, split into what was **verified by direct
fetch** for this release and what is **referenced by name** (not fetched — verify
the current version before citing a specific URL). This split enforces the skill's
own rule: cite only URLs you have verified.

**Last link-rot re-verification: 2026-09-18** — every cited URL was re-fetched and
confirmed live and content-accurate, except five fixed in that pass: 1 dead (the OWASP
ASVS project page → 404, repointed to the ASVS repo) and 4 moved (OWASP Top 10:2025,
its A03 detail, OWASP API Security 2023, and the GitHub Actions security page → their
new canonical hosts, cited content verbatim-intact). Original verification dates below
are unchanged (they record first verification); only the five fixed URLs were touched.

Verification date for all direct fetches below: **2026-08-13**.

---

## Verified by direct fetch (2026-08-13)

| Standard | URL | What was confirmed |
|---|---|---|
| OWASP Top 10:2025 | https://top10.owasp.org/2025 | Categories A01–A10:2025 verbatim (A01 Broken Access Control … A10 Mishandling of Exceptional Conditions). |
| OWASP Top 10 for LLM Applications 2025 | https://genai.owasp.org/llm-top-10/ | LLM01–LLM10:2025 names verbatim. A 2026 edition now exists (verified 2026-08-21; see the verification addendum below). |
| OWASP Top 10 for LLM Applications 2025 (resource) | https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/ | Edition landing page; document publication 2024-11-17. |
| OWASP Top 10 for Agentic Applications 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | Framework exists; published 2025-12-09; peer-reviewed by 100+ practitioners. (ASI01–ASI10 titles later confirmed verbatim from the official 2025-12-09 announcement — see the 2026-08-21 addendum below; the authoritative PDF was not re-fetched and wins on any conflict.) |
| OWASP API Security Top 10 (2023) | https://api-security.owasp.org/editions/2023/en/0x11-t10 | API1–API10:2023 names verbatim. |
| CWE-502 — Deserialization of Untrusted Data | https://cwe.mitre.org/data/definitions/502.html | Deserializing attacker- or otherwise-untrusted serialized data. Security face: can enable RCE (never auto-deserialize untrusted input — `security-appsec.md` A08). Data-integrity face: a parser weaker than its builder reintroduces a fabricated value across serialize→parse — re-derive computed fields + validate element shape, never trust the serialized form (`data-quality.md`). Stable identifier; by-name. |
| CWE Top 25 (2025) | https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html | Official 2025 edition, last updated 2025-12-15; top entries (XSS, SQLi, CSRF, Missing Authorization, OOB Write, Path Traversal, Use-After-Free, OOB Read, OS Command Injection, Code Injection). |
| WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | W3C Recommendation, dated 2024-12-12; conformance levels A/AA/AAA; WCAG 3.0 still in development. |
| EU Accessibility Act (EAA) — Directive (EU) 2019/882 | https://eur-lex.europa.eu/eli/dir/2019/882/oj | "Directive (EU) 2019/882 … on the accessibility requirements for products and services." Covers consumer digital surfaces on the EU market — e-commerce, consumer banking / payment terminals, passenger-transport ticketing & self-service, e-readers, computers / operating systems. (The directive mandates functional accessibility requirements to be met via future harmonised standards; it does **not** name EN 301 549 or WCAG on this page — those appear in the skill body as engineering leads *by name only*, not sourced here.) In-scope / micro-enterprise exemption / timelines routed to counsel (not encoded). Fetched 2026-09-19. |
| EU NIS2 Directive — Directive (EU) 2022/2555 | https://eur-lex.europa.eu/eli/dir/2022/2555/oj | "Directive (EU) 2022/2555 … on measures for a high common level of cybersecurity across the Union … repealing Directive (EU) 2016/1148" (NIS2). Applies to medium-sized+ **essential** and **important** entities across covered sectors (energy, transport, digital infrastructure, cloud / data centres / DNS, online marketplaces / search / social networks, health, drinking/waste water, public administration, space, postal, trust services; financial entities fall under DORA, Regulation (EU) 2022/2554). The preamble previews risk-management-measure categories — risk assessment, incident handling, access control, basic cyber hygiene (zero-trust, updates, segmentation, identity/access), training, and physical/environmental security; the full measure set (including business continuity and supply-chain security) and the staged incident-reporting windows were **not** pinned down in the fetch and are cited by name only (reporting is to "the CSIRT, the competent authority or the single point of contact"). In-scope / essential-vs-important / authority / timelines / management accountability routed to counsel (not encoded). Fetched 2026-09-19. |
| W3C Global Privacy Control (GPC) | https://w3c.github.io/gpc/ | "a mechanism for expressing a person's general universal preference for a do-not-sell-or-share interaction in HTTP requests" — the `Sec-GPC` request header (value `1`) + the `navigator.globalPrivacyControl` boolean; excludes deletion / same-context use; "at least four states have specifically identified GPC as a valid means to exercise legal opt-out rights" (legal force jurisdiction-specific → route to counsel). Fetched 2026-09-19. |
| W3C Internationalization — authoring techniques | https://www.w3.org/International/techniques/authoring-html | "Choose UTF-8 for all content" + always declare encoding in-document; declare `lang` and `dir="rtl"`, "tightly wrap every opposite-direction phrase in markup that sets its base direction"; NFC recommended for identifiers. Fetched 2026-09-19. |
| Unicode UAX #15 — Normalization Forms | https://www.unicode.org/reports/tr15/ | Unicode 18.0.0 (2026-08-12); NFC/NFD/NFKC/NFKD; "None of the Normalization Forms are closed under string concatenation … even if two strings X and Y are normalized, their string concatenation X+Y is not guaranteed to be normalized." Fetched 2026-09-19. |
| Unicode UAX #9 — Bidirectional Algorithm | https://www.unicode.org/reports/tr9/ | Unicode 18.0.0 (2026-09-01); explicit directional-formatting controls — overrides (RLO/LRO), isolates (RLI/LRI/FSI/PDI, the safer mechanism), terminators (PDF/PDI); the overrides "are to be avoided wherever possible, because of security concerns" (see UTR #36 — the Trojan-Source class). Fetched 2026-09-19. |
| Unicode UTS #39 — Security Mechanisms | https://www.unicode.org/reports/tr39/ | Unicode 18.0.0; a stable UTS, citable as a normative reference. §4 Confusable Detection — the *skeleton* algorithm ("The strings X and Y are defined to be confusable if and only if skeleton(X) = skeleton(Y)"), single- / mixed- / whole-script confusables; §5.1 mixed-script detection (a string is mixed-script if its *resolved script set* is empty); §5.2 restriction levels (ASCII-Only / Single Script / Highly Restrictive / Moderately Restrictive / Minimally Restrictive / Unrestricted). Backs the confusable/homograph trust-signal check. Fetched 2026-09-19. |
| Unicode UAX #29 — Text Segmentation | https://www.unicode.org/reports/tr29/ | Unicode 18.0.0; a stable Standard Annex, integral to the Unicode Standard. §3 Grapheme Cluster Boundaries — the *extended grapheme cluster* may span multiple code points (base + combining marks, ZWJ emoji sequences, Hangul jamo); "user-perceived character counts … should correspond to the number of segments delimited by grapheme cluster boundaries" (the formal boundary spec is §3.1 / §3.1.1). Backs the grapheme-safe truncation/count check. Fetched 2026-09-19. |
| RFC 8259 — JSON Data Interchange Format | https://www.rfc-editor.org/rfc/rfc8259 | Internet Standard STD 90. §6 Numbers: "good interoperability can be achieved by implementations that expect no more precision or range than [IEEE 754 binary64] provide," and integers "in the range [-(2**53)+1, (2**53)-1] are interoperable in the sense that implementations will agree exactly on their numeric values." Backs the "integer past 2^53 is silently rounded across a JSON boundary" check. Fetched 2026-09-19. |
| RFC 8594 — The Sunset HTTP Header Field | https://www.rfc-editor.org/rfc/rfc8594 | Informational (current, not obsoleted; May 2019). Defines the `Sunset` response header — a single HTTP-date signaling that "a URI is likely to become unresponsive at a specified point in the future" (a hint, not a guarantee) — plus a `sunset` link relation. Does NOT define a `Deprecation` header (a separate RFC, cited by name only). Backs the machine-readable deprecation-window signal in the API breaking-change discipline. Fetched 2026-09-19. |
| PostgreSQL + MySQL docs — transaction isolation & DDL locking | https://www.postgresql.org/docs/current/transaction-iso.html | PostgreSQL default isolation is **Read Committed** ("Read Committed is the default isolation level in PostgreSQL"); lost update / write skew are not prevented there without `SELECT … FOR UPDATE` / a higher level; SERIALIZABLE — "applications … must be prepared to retry transactions due to serialization failures" (SQLSTATE `40001`). MySQL/InnoDB default is **REPEATABLE READ** (dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html). `ALTER TABLE` acquires `ACCESS EXCLUSIVE` unless noted (conflicts with all modes) — but `ADD FOREIGN KEY` takes only the weaker `SHARE ROW EXCLUSIVE`; `ADD CONSTRAINT … NOT VALID` + `VALIDATE CONSTRAINT` (`SHARE UPDATE EXCLUSIVE`) and `CREATE UNIQUE INDEX CONCURRENTLY` are the low-lock forms (sql-altertable.html). Head-of-line queue blocking is the lock-manager wait-queue rule — "granted immediately if it does not conflict with any existing or waiting lock request" (`src/backend/storage/lmgr/README`). Five pages fetched 2026-09-19. |
| MDN Web Docs — web frontend security (4 pages) | https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage | Four pages, each fetched 2026-09-19 — postMessage (`/docs/Web/API/Window/postMessage`), Subresource Integrity (`/docs/Web/Security/Subresource_Integrity`), Referrer-Policy (`/docs/Web/HTTP/Reference/Headers/Referrer-Policy`), Trusted Types API (`/docs/Web/API/Trusted_Types_API`). `Window.postMessage` — "always verify the sender's identity using the `origin` and possibly `source` properties" (receiver checks `event.origin` + message syntax; CWE-346). Subresource Integrity — an `integrity` hash (sha256/384/512) + `crossorigin` lets the browser refuse a CDN-altered resource. Referrer-Policy — controls the `Referer` header; modern default `strict-origin-when-cross-origin` (since the Nov-2020 revision), so the finding is a *weakened* policy or a token-bearing URL. Trusted Types — the `require-trusted-types-for 'script'` CSP directive forces DOM sinks to typed values (Baseline 2026; a tinyfill for older browsers stubs the API but enforces nothing). |
| CWE-1339 — Insufficient Precision or Accuracy of a Real Number | https://cwe.mitre.org/data/definitions/1339.html | "The product processes a real number with an implementation in which the number's representation does not preserve required accuracy and precision in its fractional part, causing an incorrect result." Taxonomy anchor for precision-loss-at-a-boundary; does NOT cover non-finite (NaN/Infinity) — those are cited as IEEE 754 behavior (see the by-name list), not to this CWE. Fetched 2026-09-19. |
| Unicode CLDR — plural rules | https://cldr.unicode.org/index/cldr-spec/plural-rules | Six plural categories (zero / one / two / few / many / other); "languages vary in how they handle plurals"; `other` is the required default every language has. Fetched 2026-09-19. |
| The Twelve-Factor App — IX Disposability | https://12factor.net/disposability | "For a web process, graceful shutdown is achieved by ceasing to listen on the service port (thereby refusing any new requests), allowing any current requests to finish, and then exiting"; "For a worker process, graceful shutdown is achieved by returning the current job to the work queue"; processes "minimize startup time" and are "robust against sudden death." Backs the graceful-shutdown goal in `reliability-error-handling.md`; the readiness/LB ordering there is this skill's own load-balanced extension, not stated by 12-Factor. Fetched 2026-09-19. |
| Google Engineering Practices — Standard of Code Review | https://google.github.io/eng-practices/review/reviewer/standard.html | Core standard: approve once the change "definitely improves the overall code health," even if imperfect. |
| Diátaxis | https://diataxis.fr/ | Four documentation types: Tutorials, How-to guides, Reference, Explanation. |
| C4 model | https://c4model.com/ | Four abstraction levels: Context, Container, Component, Code. |
| OWASP Top 10:2025 — A03 detail | https://top10.owasp.org/2025/A03_2025-Software_Supply_Chain_Failures | A03 absorbed the former A06:2021 "Vulnerable and Outdated Components"; explicitly covers software that is "vulnerable, unsupported, or out of date"; guidance to upgrade "in a risk-based, timely fashion" and to "deliberately choose which version of a dependency you use and upgrade only when there is need"; names OWASP Dependency-Track / Dependency-Check / retire.js as inventory tools. |
| OpenSSF Scorecard | https://github.com/ossf/scorecard | Automated repo security scorer (0–10 per check). Check names verbatim: `Maintained` (active within ~90 days), `Dependency-Update-Tool` (Dependabot/Renovate present), `Vulnerabilities` (unfixed vulns, via the OSV service), `Pinned-Dependencies`. |
| OSV | https://osv.dev/ | Distributed open-source vulnerability database spanning 40+ package ecosystems (npm, PyPI, Go, Maven, Debian, …); `osv-scanner` scans a lockfile or SBOM and queries by package version or commit hash. |
| Semantic Versioning | https://semver.org/ | MAJOR = "incompatible API changes"; MINOR = "add functionality in a backward compatible manner"; PATCH = "backward compatible bug fixes." |
| GitHub Dependabot — version updates | https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates | Opens automated PRs to update dependencies to the latest version "even when they don't have any vulnerabilities"; documented reviewer step is to "check that your tests pass, review the changelog and release notes." (This page did **not** state that Dependabot PRs auto-trigger CI or support grouping — those are not claimed by the skill.) |
| endoflife.date | https://endoflife.date/ | Tracks end-of-life / support-lifecycle dates for 400+ products (programming languages, frameworks, databases, OSes, devices, cloud services); offers an API. |
| CISA KEV (Known Exploited Vulnerabilities catalog) | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | CISA "maintains the authoritative source of vulnerabilities that have been exploited in the wild"; guidance: "Organizations should use the KEV catalog as an input to their vulnerability management prioritization framework" (an input to prioritization, not a standalone bar). Fetched 2026-09-18. |
| FIRST EPSS (Exploit Prediction Scoring System) | https://www.first.org/epss/ | "a data-driven machine-learning model that estimates the probability that a published CVE will be exploited in the wild" "in the next 30 days"; complements CVSS (EPSS = likelihood, CVSS = severity); maintained by the EPSS Special Interest Group at FIRST. Cast as an input to focus remediation effort, not a standalone verdict. Fetched 2026-09-18. |
| Package hallucination / slopsquatting (USENIX Security 2025) | https://www.usenix.org/system/files/usenixsecurity25-spracklen.pdf | Spracklen et al., "We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs" — across 576k samples / 16 models, at least 21.7% of packages recommended by open-source models and 5.2% by commercial models were non-existent; 205,474 unique hallucinated names; ~43% recurred on every one of 10 re-runs (a predictable pre-registration target). "Slopsquatting" = an attacker registering a hallucinated name. Verified against the USENIX PDF (fetched 2026-09-19); the authors' GitHub (Spracks/PackageHallucination) corroborates 205,474 names / 576k samples / 16 models and states a 19.7% overall (all-models) hallucination rate. |
| FIRST CVSS (Common Vulnerability Scoring System) | https://www.first.org/cvss/ | "CVSS provides a way to capture the principal characteristics of a vulnerability and produce a numerical score reflecting its severity"; currently v4.0; maintained by FIRST. Severity (how bad) — distinct from EPSS's exploitation likelihood and KEV's exploited-in-the-wild fact. Fetched 2026-09-18. |

Reference repository reviewed for patterns (not a standard):
`nickmaglowsch/claude-setup` — https://github.com/nickmaglowsch/claude-setup
(diff-scoped review packets; a decorrelated cross-model second opinion on
sensitive diffs — auth, payments, crypto, concurrency, DB migrations).

## Verified by direct fetch (2026-08-14) — meta-review additions

Verification date for the rows below: **2026-08-14**. Added while extending the
skill's documentation/DX, repository-hygiene, cross-agent-portability, and
durable-standards coverage.

| Standard / source | URL | What was confirmed |
|---|---|---|
| GitHub community health files | https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories | Recommended community-health files: README, CODE_OF_CONDUCT, LICENSE, CONTRIBUTING, SECURITY, and issue + pull-request templates; issue templates must live in `.github/ISSUE_TEMPLATE`. (Folder precedence for other files, and "LICENSE must be in-repo," were **not** reproduced on this fetch — not asserted by the skill.) |
| OpenSSF Best Practices Badge (passing criteria) | https://www.bestpractices.dev/en/criteria/0 | Passing-level **MUST** items used as hygiene checks: a FLOSS license posted in a standard location; a published process for reporting vulnerabilities; per-release human-readable release notes; at least one automated test suite. Documented contribution requirements is **SHOULD**, not MUST. |
| OpenSSF Scorecard — checks catalog | https://github.com/ossf/scorecard/blob/main/docs/checks.md | Verbatim check descriptions: Branch-Protection ("default and release branches are protected"), Code-Review ("requires human code review before pull requests … are merged"), CI-Tests ("runs tests before pull requests are merged"), License, Security-Policy, Maintained. (Distinct from the Scorecard repo-root row above.) |
| AGENTS.md | https://agents.md/ | "A simple, open format for guiding coding agents" — a cross-vendor Markdown file at the repo root; nested files take precedence for their subprojects. (No adoption count or governing body asserted.) |
| Claude Code — memory / CLAUDE.md | https://code.claude.com/docs/en/memory | CLAUDE.md and auto-memory are "context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead." Claude Code reads `CLAUDE.md`, not `AGENTS.md`; bridge an existing `AGENTS.md` via an `@AGENTS.md` import or `ln -s AGENTS.md CLAUDE.md`. Project file at `./CLAUDE.md` or `./.claude/CLAUDE.md`. |
| pre-commit | https://pre-commit.com/ | "A framework for managing and maintaining multi-language pre-commit hooks." Config `.pre-commit-config.yaml`; installed with `pre-commit install`; runs on staged files before a commit completes. |
| Development Containers | https://containers.dev/ | A dev container "allows you to use a container as a full-featured development environment" for consistency across local/remote/CI. (Exact config-file path not asserted.) |
| github/scripts-to-rule-them-all | https://github.com/github/scripts-to-rule-them-all | Normalized script names (`script/bootstrap`, `setup`, `update`, `server`, `test`, `cibuild`, `console`) so contributors "only need to know the pattern"; goal: contribute "without first learning how to bootstrap the project or how to get its tests to run." |
| EditorConfig | https://editorconfig.org/ | `.editorconfig` standardizes indent style/size, charset, end-of-line, trailing-whitespace, and final-newline across editors/IDEs. |
| Keep a Changelog 1.1.0 | https://keepachangelog.com/en/1.1.0/ | `CHANGELOG.md`; "Changelogs are for humans, not machines"; an `Unreleased` section; categories Added / Changed / Deprecated / Removed / Fixed / Security; newest version first. |

## Verified by direct fetch (2026-08-14) — branch & merge triage additions

Verification date for the rows below: **2026-08-14**. Added for the branch,
merge & open-work triage capability (`references/branch-and-merge-hygiene.md`,
`SKILL.md` domain S). The `git` enumeration commands were additionally validated
this session against a scratch repository covering normal-merge, single- and
multi-commit squash-merge, rebase-merge, stale-unmerged, diverged, and
deleted-remote branches.

| Standard / source | URL | What was confirmed |
|---|---|---|
| Trunk-Based Development | https://trunkbaseddevelopment.com/ | "developers collaborate on code in a single branch called 'trunk' and resist any pressure to create other long-lived development branches"; "all team members commit to trunk at least once every 24 hours"; short-lived review branches "should only last a couple of days" — beyond two days risks "a long-lived feature branch (the antithesis of trunk-based development)." No `develop` branch. |
| GitHub flow | https://docs.github.com/en/get-started/using-github/github-flow | Six ordered steps — create a branch → make changes → create a pull request → address review comments → merge your pull request → delete your branch — merging into "the default branch." The current docs contain **no** "main is always deployable" / deploy / production language (verified against the primary `github/docs` markdown); that property is attestable only via GitLab characterizing GitHub flow, not GitHub's own page. |
| GitHub — Linking a pull request to an issue | https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue | Auto-close is default-branch-scoped: "When you merge a linked pull request into the default branch of a repository, its linked issue is automatically closed"; the closing keywords (close/closes/closed, fix/fixes/fixed, resolve/resolves/resolved) are "interpreted only when the pull request targets the repository's default branch." Fetched 2026-09-18. |
| GitLab flow | https://about.gitlab.com/topics/version-control/what-is-gitlab-flow/ | "all features and fixes go to the `main` branch while enabling `production` and `stable` branches"; a pre-production branch takes bug fixes before production; "Commits flow downstream to ensure that every line of code is tested in all environments." The **"upstream first"** phrasing is confirmed from GitLab's archived FOSS docs (`gitlab-foss` `doc/workflow/gitlab_flow.md`, pinned commit, uses `master`), not this page; `docs.gitlab.com/topics/gitlab_flow/` returned a 302 to an auth endpoint this session and was not retrieved. |
| git-flow branching model (Vincent Driessen) | https://nvie.com/posts/a-successful-git-branching-model/ | Two long-lived branches — `master` ("production-ready state") + `develop` ("latest delivered development changes for the next release"); feature branches "Must merge back into: develop"; plus release and hotfix branches. Author's 2020 note: for continuous delivery "adopt a much simpler workflow (like GitHub flow) instead of trying to shoehorn git-flow." (Original uses `master`.) |
| Patterns for Managing Source Code Branches (M. Fowler) | https://martinfowler.com/articles/branching-patterns.html | Mainline = "A single, shared, branch that acts as the current state of the product"; Continuous Integration integrates to mainline "usually less than a day's work"; Feature Branching integrates "when the feature is complete"; smaller/more-frequent integrations carry "less risk," and "Branches inevitably diverge," making later merges harder. (The exact phrase "merge debt" does **not** appear on the page.) |
| GitHub — About merge methods on GitHub | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github | Merge commit (default): "all commits from the feature branch are added to the base branch in a merge commit" (uses `--no-ff`). Squash: "the pull request's commits are squashed into a single commit" for "a more streamlined Git history." Rebase: commits "added onto the base branch individually without a merge commit … resembles a fast-forward merge by maintaining a linear project history." An admin "can enforce one type of merge method … by only enabling the desired method." |
| GitHub — About protected branches | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches | Branch protection rules "define whether collaborators can delete or force push to the branch and set requirements for any pushes"; named settings incl. "Require pull request reviews before merging," "Require status checks before merging," "Require linear history," "Require merge queue," "Allow force pushes," "Allow deletions." |
| GitHub — Managing a branch protection rule | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule | Settings labelled "Require a pull request before merging," "Require approvals," "Require status checks to pass before merging," "Do not allow bypassing the above settings," "Restrict who can push to matching branches." (Verbatim labels differ from the About-protected-branches page; attributed separately.) |
| GitHub — Managing a merge queue | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue | "A merge queue helps increase velocity by automating pull request merges into a busy branch and ensuring the branch is never broken by incompatible changes"; each PR is grouped "with the latest version of the `base_branch` as well as changes from pull requests ahead of it in the queue"; required via the "Require merge queue" protection setting. |
| GitHub — Managing the automatic deletion of branches | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches | "You can have head branches automatically deleted after pull requests are merged"; "Branch protection rules and repository rules can also prevent branches being automatically deleted." |
| GitHub — Deleting and restoring branches in a pull request | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-branches-in-your-repository/deleting-and-restoring-branches-in-a-pull-request | A branch associated with a merged/closed PR can be deleted; "You can restore the head branch of a closed pull request." |
| git reference manual — branch / log / cherry / for-each-ref | https://git-scm.com/docs/git-branch · https://git-scm.com/docs/git-log · https://git-scm.com/docs/git-cherry · https://git-scm.com/docs/git-for-each-ref | `--merged [<commit>]` / `--no-merged [<commit>]` list branches whose tips **are / are not** reachable from `<commit>`. `git log <base>..<branch>` = commits reachable from `<branch>` but not `<base>`. `git cherry` = "Find commits yet to be applied to upstream" (prefix `-` = an equivalent is already upstream, `+` = not). `git for-each-ref --sort=committerdate refs/heads` orders local branches by last-commit date (`committerdate` is a numeric sort key; `-` prefix reverses). |

## Verified by direct fetch (2026-08-17) — ASVS

Verification date: **2026-08-17**.

| Standard / source | URL | What was confirmed |
|---|---|---|
| OWASP ASVS | https://github.com/OWASP/ASVS | Latest stable version **5.0.0** (dated May 2025). Preferred requirement id form `v<version>-<chapter>.<section>.<requirement>` (e.g. `v5.0.0-1.2.5`); a bare `1.2.5` refers to the latest version. Use as a verification checklist — claiming "ASVS covered" in a review requires naming the exact chapters/requirements actually checked, not a bare "ASVS" label. (Repointed 2026-09-18 from the retired `owasp.org/www-project-application-security-verification-standard/`, now 404; ASVS 5.0's assurance-level model was **not** re-verified this session — do not cite L1/L2/L3 without checking the 5.0 spec.) |

## Verified by direct fetch (2026-08-17) — install / Cursor portability

Verification date for the row below: **2026-08-17**. Added for `install.sh
--with-cursor` and global `~/.cursor/skills/` installs.

| Standard / source | URL | What was confirmed |
|---|---|---|
| Cursor — Agent Skills | https://cursor.com/docs/skills | Skills load from `.agents/skills/`, `.cursor/skills/`, `~/.agents/skills/`, `~/.cursor/skills/`; **also** from Claude/Codex dirs (`.claude/skills/`, `.codex/skills/`, and the `~/` variants) for compatibility. Each skill is a folder with `SKILL.md` (YAML `name` + `description`); optional `references/`, `scripts/`, `assets/`. |

## Verified by direct fetch (2026-08-21) — WCAG success-criteria details

Verification date for the rows below: **2026-08-21**. Added for the a11y
gate-vs-standard rule (`SKILL.md` Phase 1) and the cross-view consistency pass
(`references/frontend-a11y.md`). Each row fetched from its W3C "Understanding"
page this session.

| Standard / source | URL | What was confirmed |
|---|---|---|
| WCAG 2.2 SC 1.4.3 Contrast (Minimum) | https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html | Level AA. Inactive-component exception, verbatim: text/images of text "that are part of an inactive user interface component … have no contrast requirement"; inactive = "not available for user interaction (e.g., a disabled control in HTML)." Basis for "a contrast gate flagging disabled controls is stricter than its standard." |
| WCAG 2.2 SC 3.2.4 Consistent Identification | https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html | Level AA. Requirement verbatim: "Components that have the same functionality within a set of web pages are identified consistently." Basis for the same-action-two-labels cross-view finding. |
| WCAG 2.2 SC 3.2.6 Consistent Help | https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html | Level A; new in WCAG 2.2. Repeated help mechanisms (human contact details/mechanism, self-help, automated contact) "occur in the same order relative to other page content, unless a change is initiated by the user." Sibling criterion for help/contact placement. |

## Verified by direct fetch (2026-09-08) — software-house roles & agent orchestration

Verification date for the rows below: **2026-09-08**. Added for the delivery
role roster (`agentic-delivery/references/roles.md`), the evaluator/adversary
framing (`idea-critic`), and the orchestration discipline (worktree isolation,
preflight, render-surface discriminator) in `agentic-delivery` and
`references/parallel-audit.md`. Each row fetched this session; where a claim was
not on the fetched page, the row says so.

| Standard / source | URL | What was confirmed |
|---|---|---|
| Anthropic — Building Effective AI Agents | https://www.anthropic.com/engineering/building-effective-agents | Published 2024-12-19. Named workflow patterns verbatim: **Prompt chaining**, **Routing**, **Parallelization** ("LLMs work simultaneously on a task and have their outputs aggregated"), **Orchestrator-workers** ("a central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results"), **Evaluator-optimizer** ("one LLM call generates a response while another provides evaluation and feedback in a loop"), and autonomous **Agents**. Guidance: prefer the simplest sufficient structure; add multi-step/agentic complexity only when simpler solutions fall short. |
| Claude Code — Subagents | https://code.claude.com/docs/en/sub-agents | `docs.claude.com/en/docs/claude-code/sub-agents` 301→ this URL this session. "Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent permissions." Least privilege via a `tools` allowlist or `disallowedTools` denylist. Single-responsibility: "Define a custom subagent when you keep spawning the same kind of worker with the same instructions." Parallelism: "For independent investigations, spawn multiple subagents to work simultaneously." |
| Anthropic — Agent Skills (overview) | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview | `docs.claude.com/…/agent-skills/overview` 302→ this URL this session. `SKILL.md` YAML frontmatter requires `name` + `description`. **Progressive disclosure**: Level 1 metadata always loaded (~100 tokens/skill), Level 2 SKILL.md body loaded when triggered, Level 3 bundled resources/scripts read only as needed. `description` ≤1024 chars; `name` ≤64 chars, lowercase/digits/hyphens, cannot contain "anthropic"/"claude". Claude Code discovers filesystem Skills in `~/.claude/skills/` (personal) or `.claude/skills/` (project). "Compose capabilities: Combine Skills for complex, multistep tasks." Security note: use only trusted Skills; externally-fetched content is a risk surface. |
| MetaGPT (Hong et al.) | https://arxiv.org/abs/2308.00352 | Title "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework." Abstract confirmed: it "encodes Standardized Operating Procedures (SOPs) into prompt sequences," assigns "diverse roles to various agents" in "an assembly line paradigm," lets agents "verify intermediate results and reduce errors," and targets "cascading hallucinations caused by naively chaining LLMs." (The specific product-manager/architect/engineer/QA role list is **not** quoted verbatim from the abstract fetched this session.) |
| ChatDev (Qian et al.) | https://arxiv.org/abs/2307.07924 | Title "ChatDev: Communicative Agents for Software Development." Abstract confirmed: specialized LLM-driven agents collaborate across the software lifecycle — "design, coding, and testing" — guided in what to communicate (a chat chain) and how (via "communicative dehallucination"). (Specific role titles such as CEO/CTO and a documentation phase are **not** quoted verbatim from the abstract fetched this session.) |

## Verified by direct fetch (2026-09-08) — model-tiering, release engineering & retrospectives

Verification date for the rows below: **2026-09-08**. Added for
`references/model-tiering.md`, `references/release-engineering.md`,
`agentic-delivery/references/retrospective.md` + `template-postmortem.md` +
`template-adr.md`, the G0 appetite line, and the §8 spike/prototype-branch
convention in `branch-and-merge-hygiene.md`.

| Standard / source | URL | What was confirmed |
|---|---|---|
| Claude docs — Choosing the right model | https://platform.claude.com/docs/en/about-claude/models/choosing-a-model | Names the three-tier model family and the general guidance to match model strength to task complexity rather than run everything on the strongest tier. |
| Claude docs — Optimizing for cost and intelligence | https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence | Source for `model-tiering.md`'s levers: effort/reasoning-depth tuning as a same-model lever; prefix/prompt caching as the largest single cost lever on an agentic task (cost grows roughly with the square of turn count without it); the Batch API as a flat discount for unattended work; escalate-on-failure (cheap-first, re-run failures at full strength) reaching comparable pass rate for meaningfully less cost than running everything strong; a per-lane token budget as a direct cost/quality dial; a bounded advisor-consult pattern (a couple of calls per task) as a cheaper alternative to a full model swap, with a measured quality regression if over-used; and judging model choice by cost-per-*solved*-task rather than cost-per-token, since a pricier-per-token model can solve enough more tasks to cost less overall. |
| Claude docs — Prompt caching | https://platform.claude.com/docs/en/build-with-claude/prompt-caching | A cached prefix is billed well below fresh input on re-send; supports the "mark the shared fan-out packet cacheable" addition in `parallel-audit.md` §1. |
| Claude docs — Batch processing | https://platform.claude.com/docs/en/build-with-claude/batch-processing | Confirms the batch-API discount mechanism for unattended/async work named in `model-tiering.md`. |
| Aider — "Separating code reasoning and editing" | https://aider.chat/2024/09/26/architect.html | 2024-09-26. A production-shipped instance of a strong-model-plans / cheaper-model-executes split (architect/editor mode), cited as prior art for tiering plan vs. execute onto different model strengths — not quoted for specific pass-rate numbers here, since those are model-version-dated and not load-bearing for this skill's vendor-neutral guidance. |
| RouteLLM (Ong, Almahairi, Wu, Chiang, Wu, Gonzalez, Stoica, Zhang) | https://arxiv.org/abs/2406.18665 | Demonstrates the general routing principle: dynamically routing between a strong and weak LLM cuts cost substantially without giving up response quality, and a trained router transfers across different strong/weak model pairs at test time — general support for "tier by task, not by default," not a specific number this skill asserts. |
| DORA — Core metrics | https://dora.dev/guides/dora-metrics-four-keys/ | The framework is **five** metrics in two categories: Throughput (change lead time, deployment frequency, failed-deployment recovery time) and Instability (change fail rate, deployment rework rate — the share of deployments that are unplanned but happen as a result of a production incident). **Single-source caveat:** confirmed by direct fetch of this page only; re-verify against a second source before treating these exact names as final, since DORA revises this page over time. |
| DORA — research programme | https://dora.dev/research/ , https://dora.dev/ | A Google Cloud–led research programme; DORA Core is framed as the most firmly-established findings, intended as a practitioner guide. |
| *Accelerate* (Forsgren, Humble, Kim) | https://itrevolution.com/product/accelerate/ | Publisher landing page only — confirms authorship and the State of DevOps report lineage, not a source for specific statistical claims (marketing copy, not the study itself). |
| Martin Fowler — Feature Toggles | https://martinfowler.com/articles/feature-toggles.html | Four categories confirmed verbatim: Release Toggles ("should generally not stick around much longer than a week or two"), Experiment Toggles (A/B/cohort), Ops Toggles (operator kill-switch), Permissioning Toggles (feature by segment). Toggle debt named explicitly: "Savvy teams view the Feature Toggles in their codebase as inventory which comes with a carrying cost." |
| Martin Fowler — Canary Release | https://martinfowler.com/bliki/CanaryRelease.html | Traffic split to a small subset first (random sample / internal users / demographic), widened as confidence grows; names a "cluster immune system" — automatic rollback on business-metric regression, not error rate alone. |
| Martin Fowler — Blue-Green Deployment | https://martinfowler.com/bliki/BlueGreenDeployment.html | Two near-identical environments; cutover is a router flip; rollback is flipping the router back. |
| Google SRE book — Postmortem Culture: Learning from Failure | https://sre.google/sre-book/postmortem-culture/ | Blameless principle verbatim: "assumes that everyone involved in an incident had good intentions and did the right thing with the information they had." Trigger criteria: user-visible downtime/degradation past a threshold, data loss, on-call intervention, resolution time above a threshold, a monitoring failure that delayed detection, or a stakeholder request. |
| Google SRE book — Example Postmortem (Shakespeare Search) | https://sre.google/sre-book/example-postmortem/ | Template section order confirmed: Summary → Impact → Root Causes → Trigger → Resolution → Detection → Action Items → Lessons Learned (what went well / poorly / where we got lucky) → Timeline → Supporting information. Action items carry an owner, a type, and a bug-tracker reference. |
| Google SRE workbook — Alerting on SLOs | https://sre.google/workbook/alerting-on-slos/ | Multiwindow, multi-burn-rate mechanism: for a 99.9% SLO, page at a 14.4× burn rate over 1h/5m windows, page at 6× over 6h/30m, ticket at 1× over 3d/6h — the short window exists so the alert clears minutes after the issue resolves rather than staying hot on stale data. This is the citation for `role-coverage.md`'s existing, previously-uncited burn-rate language; treat this row as adding the source and the exact window/multiplier values, not as an independently re-verified claim that the pre-existing prose matched these numbers line-by-line before this citation was added. |
| Michael Nygard — "Documenting Architecture Decisions" | http://cognitect.com/blog/2011/11/15/documenting-architecture-decisions | The original ADR post. Section set confirmed verbatim: Title (short noun phrase), Context (neutral statement of forces), Decision (full sentences, active voice, "We will…"), Status (proposed/accepted/deprecated/superseded), Consequences (all of them, not just the positive). Numbered sequentially, never reused; "should be one or two pages long." |
| MADR (Markdown Architectural Decision Records) | https://adr.github.io/madr/ | Template headers confirmed: Context and Problem Statement, Decision Drivers (optional), Considered Options, Decision Outcome (with optional Consequences/Confirmation), Pros and Cons of the Options (optional), More Information (optional) — only the first three are core, the rest explicitly removable. |
| Shape Up — Ch.3 "Set Boundaries" (Appetite) | https://basecamp.com/shapeup/1.2-chapter-03 | Verbatim: "An appetite is completely different from an estimate. Estimates start with a design and end with a number. Appetites start with a number and end with a design" — "fixed time, variable scope." Basis for G0's appetite line in `agentic-delivery/SKILL.md`. |
| Shape Up — Ch.4 "Find the Elements" (Breadboarding, Fat Marker Sketches) | https://basecamp.com/shapeup/1.3-chapter-04 | A breadboard "has all the components and wiring of a real device but no industrial design"; a fat marker sketch is deliberately too broad to add detail, so the team can't skip ahead to the wrong fidelity. Cited as the design-side precedent for a disposable-by-construction exploration; `branch-and-merge-hygiene.md` §8 applies the same idea to a branch-naming convention, not to Shape Up's own design ritual. |
| Test Pyramid (Ham Vocke, on Martin Fowler's site) | https://martinfowler.com/articles/practical-test-pyramid.html | 2018-02-26. Three layers bottom-to-top — Unit, Service/Integration, UI/E2E — attributed to Mike Cohn's original pyramid. "Write lots of small and fast unit tests. Write some more coarse-grained tests and very few high-level tests." |
| Testing Trophy (Kent C. Dodds) | https://kentcdodds.com/blog/write-tests | 2019-07-13. Layers bottom-to-top: Static, Unit, Integration, E2E. An explicit, named departure from the classic pyramid's unit-heavy shape — integration tests as the best confidence/speed trade-off for a modern, I/O-heavy app. |

## Verified by direct fetch (2026-09-08) — idea-critic hardening & Conductor operating rhythm

Verification date for the rows below: **2026-09-08**. Added for
`idea-critic/SKILL.md`'s `steelman` / `strongest_attack_survived` /
premortem / model-family-decorrelation additions, and `agentic-delivery/
SKILL.md`'s Conductor operating rhythm subsection.

| Standard / source | URL | What was confirmed |
|---|---|---|
| Anthropic — How we built our multi-agent research system | https://www.anthropic.com/engineering/multi-agent-research-system | 2025-06-13. Verbatim: "Agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats." Subagents given only "simple, short instructions" were observed duplicating each other's work (two independently re-investigating the same ground); the fix stated is that "each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries." Scaling tiers confirmed: 1 agent for simple fact-finding, 2-4 subagents for a direct comparison, 10+ only for a complex, clearly-divided task. Over-parallelization ("spawning 50 subagents for simple queries") named as an observed failure. |
| Anthropic — Effective context engineering for AI agents | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | 2025-09-29. Verbatim, under "Sub-agent architectures": a subagent "returns only a condensed, distilled summary of its work (often 1,000-2,000 tokens)... the detailed search context remains isolated within sub-agents, while the lead agent focuses on synthesizing and analyzing the results." Basis for the Conductor's event-driven, status-only attention model. |
| Claude Code — Best practices for agentic coding | https://code.claude.com/docs/en/best-practices | Verbatim, on adversarial review: "A reviewer prompted to find gaps will usually report some, even when the work is sound, because that is what it was asked to do... Tell the reviewer to flag only gaps that affect correctness or the stated requirements, and treat the rest as optional" — the demand-characteristic bias `idea-critic`'s steelman + `strongest_attack_survived` fields are designed against (force the record to be specific, not merely present). Also verbatim: "a fresh context improves code review since Claude won't be biased toward code it just wrote," cited in `roles.md`'s Independence bullet. |
| MAST — "Why Do Multi-Agent LLM Systems Fail?" (Cemri, Pan, Yang, Agrawal, Chopra, Tiwari, Keutzer, Parameswaran, Klein, Ramchandran, Zaharia, Gonzalez, Stoica) | https://arxiv.org/abs/2503.13657 | Submitted 2025-03-17. Abstract confirmed verbatim: three failure categories — "(i) system design issues, (ii) inter-agent misalignment, (iii) task verification" — across 14 unique failure modes and 1600+ annotated traces from 7 open-source multi-agent frameworks. The abstract does **not** enumerate the 14 individual failure-mode names — only the 3 category names are verbatim-confirmed here; the skill cites only the categories, not the full taxonomy. |
| Nemeth, Brown & Rogers (2001), "Devil's advocate versus authentic dissent: stimulating quantity and quality" | *European Journal of Social Psychology*, 31(6), 707–720. DOI: 10.1002/ejsp.58 | Verified via Crossref bibliographic API (abstract snippet, not full text — publisher returned 403 to direct fetch): "authentic minority was superior to all three forms of 'devil's advocate'" — assigned/manufactured dissent underperformed genuine dissent on stimulating group thought. Treat the mechanism as solidly established; the exact conditions tested and effect sizes are unconfirmed from this session's fetch. |
| Nemeth, C. J. (2018), *In Defense of Troublemakers: The Power of Dissent in Life and Business* | Basic Books. ISBN 978-0465096299 | Verified via Wikipedia's "Devil's advocate" article quoting the book directly: "Inauthentic dissent (assigning someone to act as a Devil's advocate) is considerably less effective in improving group decision-making than authentic dissent," and can leave people "more entrenched in their original beliefs." Secondary paraphrase of a trade book, not a primary journal source — light corroboration for the Nemeth et al. 2001 finding and for `idea-critic`'s false-closure-REVISE pitfall, not standalone grounding. |
| Panickssery, Bowman & Feng (2024), "LLM Evaluators Recognize and Favor Their Own Generations" | https://arxiv.org/abs/2404.13076 | "GPT-4 and Llama 2 have non-trivial accuracy at distinguishing themselves from other LLMs and humans," and self-recognition capability correlates with self-preference bias. Tested on GPT-4 and Llama 2 only — **not** Claude; transfer to other model families is a reasonable inference cited as such in `idea-critic`'s Independence step, not an independently tested finding. |
| Pre-mortem (Klein, G. (2007), "Performing a Project Premortem," *Harvard Business Review*, 85(9): 18–19) | Verified via Wikipedia's "Pre-mortem" article, cross-referenced by Kahneman, *Thinking, Fast and Slow* (2011) | A premortem assumes the project has already failed and works backward to explain why — a different elicitation frame from "what might go wrong," credited with increasing the likelihood the main threats get identified. No quantified effect size confirmed from this session's fetch; cited via Wikipedia's citation of the HBR piece, not the piece itself. |

## Verified by direct fetch (2026-09-09) — `agentic-delivery/references/fast-agentic-delivery.md`

Verification date for the rows below: **2026-09-09**. Added for the new concurrency-,
scheduling-, and merge-cadence reference in the `agentic-delivery` skill.

| Standard / source | URL | What was confirmed |
|---|---|---|
| Kanban University, *Kanban Guide* | https://kanban.university/kanban-guide/ | A WIP limit's stated purpose, verbatim: "balance utilization and still ensure the flow of work"; "limiting the work that is allowed to enter the system is an important key to reducing delay and context switching which may result in poor timeliness, quality, and potentially waste"; a WIP limit as "an enabling constraint, which gives focus and develops behaviors such as collaboration and finishing started items with high quality." |
| Google Engineering Practices — Small CLs | https://google.github.io/eng-practices/review/developer/small-cls.html | "100 lines is usually a reasonable size for a CL, and 1000 lines is usually too large, but it's up to the judgment of your reviewer." Small CLs are reviewed more quickly and more thoroughly, introduce fewer bugs ("it's easier for you and your reviewer to reason effectively about the impact"), waste less effort on a wrong direction, and simplify rollback. |
| Wikipedia — Blast radius (computing sense) | https://en.wikipedia.org/wiki/Blast_radius | "In cloud computing, the term blast radius is used to designate the impact that a security breach of one single component of an application could have on the overall composite application." A sibling technical-debt sense: "how many otherwise redundant edits on different scripts would need to be made when changing something small" — the lockstep-surfaces problem named directly. |
| GitLab Docs — Merge trains | https://docs.gitlab.com/ci/pipelines/merge_trains/ | "Use merge trains to put merge requests in a queue. Each merge request is compared to the other, earlier merge requests, to ensure they all work together." Names the problem directly: "two merge requests can each pass their own pipeline, but their combined changes can still conflict." Each queued pipeline runs the change combined with the target branch **and** every earlier queued change (a third queued MR's pipeline tests all three, combined). |
| Brendan Gregg — Linux Load Averages: Solving the Mystery | https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html | "Adding the uninterruptible state means that Linux load averages can increase due to a disk (or NFS) I/O workload, not just CPU demand." Worked example: "a heavily disk-bound system might be extremely sluggish but only have a TASK_RUNNING [CPU-runnable] average of 0.1"; a decomposed `tar` archival showed a load average of 1.19 including 0.67 from uninterruptible disk reads against only 0.37 actual CPU utilization — the basis for "don't gate concurrency on `load1` alone." |

## Verified by direct fetch (2026-09-10) — dependency cooldown & CI/CD hardening

Verification date for the rows below: **2026-09-10**. Added for the
release-age-cooldown control (`references/dependency-currency-and-upgrades.md`)
and the CI/CD trigger-and-token hardening instrument (`references/security-appsec.md`
A03, cross-referenced from `references/security-agent-skills.md` AST02).

| Standard / source | URL | What was confirmed |
|---|---|---|
| Renovate — `minimumReleaseAge` | https://docs.renovatebot.com/configuration-options/ | Supply-chain cooldown option: "Suppress branch/PR creation for X days" / "Prevent holding broken npm packages"; Renovate delays proposing an update until a package has been public for the configured duration, reducing exposure to newly-published malicious or broken releases. Associated option `minimumReleaseAgeBehaviour`. (Dependabot `cooldown` and npm/pnpm `min-release-age`-style keys were **not** fetched this session — confirm the exact key per ecosystem before citing.) |
| GitHub Actions — Secure use reference | https://docs.github.com/en/actions/reference/security/secure-use | Privileged workflows (`pull_request_target` / `workflow_run`) share the main-branch cache and may hold write access + secrets, so they "must not explicitly check out untrusted code" (verbatim). For inline scripts, "the preferred approach to handling untrusted input is to set the value of the expression to an intermediate environment variable" rather than inlining `${{ github.event.* }}` into a `run:` script. Set the default `GITHUB_TOKEN` to "read access only for repository contents," escalating per job as required. (`persist-credentials` on `actions/checkout` still **not** on this page. Repointed 2026-09-18 — the page was renamed from "Security hardening for GitHub Actions" to "Secure use reference".) |
| NIST AI Risk Management Framework — core functions (verified 2026-09-11) | https://www.nist.gov/itl/ai-risk-management-framework | The four core function names — **Govern, Map, Measure, Manage** — appear on the official NIST ITL framework page. Only the function names were confirmed here; the full AI RMF 1.0 (AI 100-1) and the Generative AI Profile (AI 600-1) control specifics were **not** fetched this session — cite those by name only (see the by-name list below). |

## Verified by direct fetch (2026-09-13) — agent context/memory lifecycle

Verification date for the rows below: **2026-09-13**. Added for the domain-C
"context & memory lifecycle" review lens (`references/security-ai-agents.md`) and
its 🚩 tells (the non-adversarial sibling to ASI06, plus the LLM06 tree-budget
clause). Each row fetched this session; where a date or claim was not on the
fetched page, the row says so.

| Standard / source | URL | What was confirmed |
|---|---|---|
| Anthropic — Effective harnesses for long-running agents | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | Published 2025-11-26. Long-running agents "running out of context in the middle of [an] implementation, leaving the next session to start with a feature half-implemented and undocumented"; mitigations named — a progress file, git history, a feature checklist, and context compaction. Basis for the "constraint/state must survive compaction" lens. Newer than the already-indexed "Effective context engineering" (2025-09-29). |
| Anthropic — Context editing (docs) | https://platform.claude.com/docs/en/build-with-claude/context-editing | Undated page. Automatic clearing of the oldest tool results at a token threshold, replaced with placeholder text; strategy `clear_tool_uses_20250919`, option `clear_tool_inputs`; **`exclude_tools`** = "tool names whose tool uses and results should never be cleared. Useful for preserving important context." Basis for "exempt the constraint/authority-bearing result from clearing." |
| Anthropic — Compaction (docs) | https://platform.claude.com/docs/en/build-with-claude/compaction | Undated page. "Compaction extends the effective context length … by automatically summarizing older context when approaching the context window limit"; later requests drop content blocks before the `compaction` block. A custom `instructions` string "don't supplement the default prompt. They replace it completely" — basis for "a replacing summary instruction must still carry the constraints." Config `compact_20260112` (seen in a page example). |
| Anthropic — Memory tool (docs) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool | Undated page. Client-side persistent store under `/memories`; tool `memory_20250818`. Verbatim security guidance: "add validation that strips sensitive data before your handler writes the file"; "Periodically delete memory files that haven't been accessed in a long time" (expiry); path-traversal protection required. Injected prompt: "ASSUME INTERRUPTION: Your context window might be reset at any moment, so you risk losing any progress that is not recorded in your memory directory"; pairs with compaction to "preserve the information that must survive summarization." Basis for the memory write-validation + expiry checks. |
| Cognition — Don't Build Multi-Agents | https://cognition.com/blog/dont-build-multi-agents | By Walden Yan, dated 2025-06-12 on the page. Verbatim: "Share context, and share full agent traces, not just individual messages"; parallel subagents that "cannot see what the other was doing … end up being inconsistent." Basis for "handoff carries the full trace, not just the latest message." |
| langchain-ai/deepagents #1698 | https://github.com/langchain-ai/deepagents/issues/1698 | Filed issue (open, labeled a bug); issue date not separately confirmed on this fetch. Title verbatim: "`SubAgentMiddleware` does not propagate `recursion_limit` to subagent graphs — subagents silently use default limit of 25" (root cause: `ainvoke` called without a `config`). Basis for the "bound the tree, not just the call — propagate the cap to spawned sub-agents" clause under LLM06. |

## Verified by direct fetch (2026-09-15) — usability heuristics

Verification date for the row below: **2026-09-15**. Added for the cited
design-quality checklist in `references/migration-parity.md` (#124).

| Standard / source | URL | What was confirmed |
|---|---|---|
| Nielsen Norman Group — 10 Usability Heuristics for User Interface Design | https://www.nngroup.com/articles/ten-usability-heuristics/ | By Jakob Nielsen; published 1994-04-24, last reviewed 2024-01-30. The 10 heuristic names (wording and order verbatim; the source renders them in Title Case): 1 Visibility of system status; 2 Match between the system and the real world; 3 User control and freedom; 4 Consistency and standards; 5 Error prevention; 6 Recognition rather than recall; 7 Flexibility and efficiency of use; 8 Aesthetic and minimalist design; 9 Help users recognize, diagnose, and recover from errors; 10 Help and documentation. Page states the 10 have "remained relevant and unchanged since 1994." |

## Referenced by name (not fetched this session — verify before citing a URL)

- **Published metric/measurement standards** — cited in `data-quality.md` §7 (#396) as the
  constructive escape from an invented score: **CHAOSS** (community activity/health metrics +
  metric-models), **Fellegi-Sunter** (probabilistic record-linkage match tiers, incl. a
  possible-match "skip" band), **W3C PROV** (provenance/lineage), **rel=me / ORCID / schema.org
  `sameAs`** (identity), **network-science structural-position measures** (Freeman betweenness centrality; Burt structural
  holes), **ESCO / O*NET** (skills taxonomies). Named by name only — not fetched this session;
  verify each current spec/URL before citing a version or a specific claim.
- **OWASP WSTG** — how-to-test companion for each web risk.
- **OWASP Cheat Sheet Series** — concrete implementation guidance.
- **MITRE CWE / CVE** — weakness and vulnerability naming.
- **OWASP ASVS 5.0** — Application Security Verification Standard; V3 "Web Frontend Security" groups the browser-native controls in `frontend-a11y.md`: postMessage origin/syntax (§3.5.5), Subresource Integrity (§3.6.1), Referrer-Policy (§3.4.5), clickjacking / frame-ancestors (§3.4.6). Trusted Types is **not** an ASVS V3 requirement — it is a related MDN-sourced control, cited to MDN only. §-numbers from the 5.0 spec text; by name only.
- **IEEE 754** — binary floating-point arithmetic (`NaN` comparison-false / total-ordering
  semantics, `±Infinity`, subnormals). Referenced in `domain-checklists.md` domain A and
  `api-contracts.md` for non-finite propagation and the double-precision safe-integer range (the
  range itself is corroborated by RFC 8259 §6 in the table above). Named by name only — not
  fetched this session (paywalled ANSI/IEEE standard).
- **MITRE ATLAS** — adversarial-ML and agent-tool attack techniques.
- **Threat-modeling methods** (named by `security-appsec.md` A06 and
  `security-ai-agents.md`): **STRIDE** (per-element spoofing / tampering / repudiation /
  info-disclosure / DoS / elevation), **PASTA** (risk/impact-centric), **attack trees**,
  **LINDDUN** (privacy threats), and **MAESTRO** (agentic-AI threat modeling,
  complementary to the OWASP ASI / MITRE ATLAS catalogs); plus the program-maturity
  frames **OWASP SAMM** and **BSIMM** (measure the org's program, not a diff — name,
  don't score). Named methods only — no URL fetched this session; verify before citing
  specifics.
- **NIST SSDF (SP 800-218)** and the **NIST AI RMF Generative AI Profile (AI 600-1)**
  — secure-development and AI-risk lifecycle framing. (The AI RMF core function names
  are verified in the table above; these document/profile specifics were not fetched.)
- **CIS Benchmarks** — OS/container/cloud hardening baselines.
- **AWS / Azure / GCP Well-Architected Frameworks** — cloud architecture-review pillars
  (operational excellence, security, reliability, performance efficiency, cost optimization;
  sustainability on some clouds). Pillar sets and counts differ and are revised per cloud — cite
  the common set by name, do not pin a count.
- **FinOps (FinOps Foundation)** — cloud cost as a continuous practice; the inform → optimize →
  operate loop. Named by name only.
- **Chaos engineering (Principles of Chaos)** — steady-state hypothesis + blast-radius-limited
  fault injection to verify resilience. Named by name only.
- **Release It! (Michael Nygard, 2nd ed.)** — stability patterns/antipatterns (bulkheads, circuit
  breaker, timeouts, fail-fast, steady state, shed load, cascading failure). Backs the bulkhead /
  resource-isolation section in `reliability-error-handling.md`. Named by name only (book).
- **OpenTelemetry GenAI semantic conventions** (`gen_ai.*`) — LLM/agent telemetry attribute names
  (token usage, model, operation, outcome). **Still at *Development* stability and revised often —
  cite the convention names by name only; pin no version and no specific attribute list.**
- **SPACE framework** — multi-dimensional developer productivity (satisfaction, performance,
  activity, communication, efficiency). Named by name only.
- **DevEx (developer experience)** — the flow/feedback-loop/cognitive-load framing of developer
  productivity. Named by name only.
- **Model Cards** (Mitchell et al.), **Datasheets for Datasets** (Gebru et al.), **Data Cards**
  (Pushkarna et al.) — AI transparency artifacts documenting intended use, data provenance,
  subgroup performance, and limitations. Named by name only (papers not fetched this session).
- **EU AI Act** and **ISO/IEC 42001** (AI-management-system standard) — AI-governance regimes.
  Named by name only; **date/amendment-sensitive** (its obligation timeline has been revised over
  time) — name and route to counsel, never encode a deadline or version.
- **ISO/IEC 25010** — software product-quality model (the axes this review
  covers).
- **Smart Brevity** (Axios; VandeHei, Allen & Schwartz) — lead each information unit
  with *what's new* **and** *why it matters*; the actionability pattern named in
  `product-ux-quality.md`. Named by name only — no URL fetched this session.
- **The Twelve-Factor App** — config/dependency/deploy hygiene.
- **RFC 2119** — requirement-keyword conventions (MUST / SHOULD / MAY), named by
  `docs-evolution-by-stage.md`. Named by name only.
- **llms.txt** — proposed convention for an LLM-oriented repo/site guide, named by
  `docs-evolution-by-stage.md`. Named by name only; a proposal, not a ratified standard.
- **"Choose boring technology" / innovation tokens** (McKinley) and **evolutionary
  architecture / fitness functions** (Ford, Parsons & Kua) — architecture-evolution
  leads named by `infra-evolution-by-stage.md`. Named by name only.
- **Conventional Commits** — commit-message discipline. (Semantic Versioning
  graduated to the verified table above this session.)
- **OWASP Dependency-Check / Dependency-Track**, **retire.js**, **Renovate**,
  **Trivy / Grype**, and the per-ecosystem auditors (**pip-audit**,
  **govulncheck**, **cargo audit**, **bundler-audit**) — SCA and
  dependency-update tooling named in `dependency-currency-and-upgrades.md`. Tools,
  not standards; confirm the current invocation per ecosystem at review time.
- **Cross-agent instruction-file conventions** — Cursor (`.cursor/rules` /
  `.cursorrules`), GitHub Copilot (`.github/copilot-instructions.md`), Windsurf
  (`.windsurf/rules` / `.windsurfrules`), Gemini CLI (`GEMINI.md`), Aider
  (`CONVENTIONS.md`). The file **names** are corroborated by the verified Claude
  Code memory doc above; per-agent semantics, frontmatter, and size caps were not
  independently fetched — confirm at imprint time.
- **Scrum Guide — Definition of Done** — the concept the skill's definition-of-done
  checklist rests on ("the state of the Increment when it meets the quality
  measures required"); cite the Scrum Guide directly if a version-specific claim
  is needed.
- **Chaos-playbook / orchestration frameworks** (named by `agentic-ceo`): GTD
  capture-and-clarify; incident command (single commander, unity-of-command,
  activity log); emergency-severity triage; "the ONE thing"; psychological
  reactance; motivational-interviewing reflective listening. Named leads only — no
  URL or figure fetched this session; verify before citing specifics. (WIP limits
  and orchestrator–worker delegation are already registered above.)
- **Product-discovery frameworks** (named by `product-discovery`): the Mom Test
  (Fitzpatrick); the jobs-to-be-done switch interview (Christensen; Klement); Torres
  continuous-discovery / opportunity-solution tree; the Ellis "very disappointed"
  product-market-fit survey; Testing Business Ideas (Bland & Osterwalder) experiment
  library; ICE / RICE prioritization; and fake-door / concierge / Wizard-of-Oz
  validation. Named leads only — no URL or figure fetched this session; verify before
  citing a specific figure or threshold.
- **Product-analytics frameworks** (named by `growth-analytics`): AARRR / "Pirate
  Metrics" (McClure); the North Star Metric framework; vanity-vs-actionable metrics;
  retention cohort analysis; "one metric that matters"; activation / aha-moment
  analysis; and the experiment-rigor leads — peeking / fixed-horizon vs sequential
  testing, always-valid / anytime-valid inference (mSPRT, confidence sequences),
  group-sequential / alpha-spending designs, CUPED variance reduction, and
  product-led growth. Named leads only — no URL or figure fetched this session; verify
  before citing a specific figure or threshold.
- **Positioning / brand frameworks** (named by `positioning`): the Value Proposition
  Canvas and business-model design (Osterwalder & Pigneur); positioning (Ries & Trout;
  April Dunford's obviously-awesome positioning); the message house / messaging
  framework; jobs-to-be-done as a positioning lens; minimum-viable-brand; premature
  scaling as a pre-PMF anti-pattern (Startup Genome; lean-startup). Named leads only —
  no URL or figure fetched this session; verify before citing a specific claim.
- **Business / unit-economics frameworks** (named by `business-ops`): unit economics
  (LTV, CAC, LTV:CAC, payback, contribution margin); value-based, cost-plus, and
  competitor-anchored pricing; the Van Westendorp price-sensitivity meter and usage-based /
  outcome-based / good-better-best packaging models; runway / burn / break-even; the securities-offering boundary (equity / SAFE
  fundraising); worker-classification tests; the GDPR/CCPA obligation triage (routed,
  not concluded). Named leads only — no URL, figure, statute, or rate fetched this
  session; route regulation questions to a licensed professional.
- **Regulated-domain regimes** (named by `business-ops`'s `regulated-domain-triage.md`
  and the `deep-code-review` privacy lenses): **PCI DSS** (card-data security
  standard), **SOC 2** and **ISO/IEC 27001** (security-attestation / ISMS
  frameworks), alongside the privacy regimes already covered in
  `privacy-compliance.md` (GDPR, UK GDPR, CCPA/CPRA, HIPAA, COPPA, and biometric-
  privacy statutes). Named leads only — no URL, article number, threshold, or
  deadline fetched this session; the triage **names the regime and routes to
  counsel**, never concludes it binds. (ISO/IEC 27001 is security/ISMS — distinct
  from ISO/IEC 25010, the product-quality model listed above.)

> When the skill needs a version-specific detail from any of these, it must fetch
> the current source at review time and cite only the URL it verified.

---

## Verification addendum (2026-08-21)

| Standard | URL | What was confirmed |
|---|---|---|
| OWASP Top 10 for Agentic Applications 2026 (announcement) | https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/ | ASI01–ASI10 titles verbatim from the 2025-12-09 announcement: Agent Goal Hijack; Tool Misuse; Identity & Privilege Abuse; Agentic Supply Chain Vulnerabilities; Unexpected Code Execution; Memory & Context Poisoning; Insecure Inter-Agent Communication; Cascading Failures; Human-Agent Trust Exploitation; Rogue Agents. PDF not re-fetched this session — PDF wins on conflict. |
| OWASP Top 10 for Agentic Applications 2026 (resource) | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | Resource page still current 2026-08-21; published 2025-12-09. |
| OWASP GenAI LLM Top 10 2026 | https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/ | A 2026 LLM edition exists (page dated 2026-08-03). Numbered titles **not** confirmed verbatim from the PDF this session. Do **not** claim the 2025 LLM Top 10 is the latest edition; keep citing 2025 names until 2026 titles are fetched. |

## Verification addendum (2026-09-08)

| Standard | URL | What was confirmed |
|---|---|---|
| OWASP Top 10 for LLM Applications 2026 (PDF) | https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/ (download `OWASP-GenAI-LLM-Top-10-2026-v1.0.pdf`, 122 pages) | Titles quoted from the PDF table of contents: LLM01:2026 Prompt Injection; LLM02:2026 Sensitive Information Disclosure; LLM03:2026 Excessive Agency; LLM04:2026 Supply Chain; LLM05:2026 Data and Model Poisoning; LLM06:2026 Unbounded Consumption; LLM07:2026 Misinformation; LLM08:2026 Hidden Context Exposure; LLM09:2026 Vector and Embedding Weaknesses; LLM10:2026 Improper Output Handling. Official `/llm-top-10/` HTML still listed 2025 cards on this fetch — PDF wins. |
| OWASP Agentic Skills Top 10 (AST01–AST10) | https://owasp.org/www-project-agentic-skills-top-10/ | Titles and severities quoted from the summary table: AST01 Malicious Skills (Critical); AST02 Supply Chain Compromise (Critical); AST03 Over-Privileged Skills (High); AST04 Insecure Metadata (High); AST05 Untrusted External Instructions (High); AST06 Weak Isolation (High); AST07 Update Drift (Medium); AST08 Poor Scanning (Medium); AST09 No Governance (Medium); AST10 Cross-Platform Reuse (Medium). Project badge version-1.0-2026, updated March 2026. |

## Verification addendum (2026-09-16)

| Standard | URL | What was confirmed |
|---|---|---|
| Sherman Kent, *Words of Estimative Probability* | https://www.cia.gov/resources/csi/studies-in-intelligence/archives/vol-8-no-4/words-of-estimative-probability/ (declassified PDF: https://www.cia.gov/resources/csi/static/Words-of-Estimative-Probability.pdf) | Read the declassified PDF (pages 1–4) directly this session. CIA *Studies in Intelligence*, Vol. 8 No. 4 (1964); released via CIA Historical Review Program 1993. Confirmed thesis: undefined verbal-probability terms are read inconsistently — Kent's own Board of National Estimates read "serious possibility" (NIE 29-51) anywhere from 20:80 to 80:20 odds; the subtitle states "the case for consistent, unambiguous usage of a few key odds expressions." Cite for the read-inconsistently / define-the-tiers point only; assert no canonical numeric mapping. |
| Admiralty Code (NATO System; intelligence source & information reliability) | https://en.wikipedia.org/wiki/Admiralty_code | **Wikipedia — tertiary source; cite by name only, not as a primary authority.** Two independent axes: source reliability A–F (A completely reliable … F reliability cannot be judged) × information credibility 1–6 (1 confirmed by other sources … 6 truth cannot be judged); "each descriptor is considered in isolation." Confirms the independent-axes framing only. |

## Verified by direct fetch (2026-09-17) — SARIF interchange format

Verification date for the row below: **2026-09-17**. Added for the deep-code-review
`security-appsec.md` deterministic-corroboration lens (the ingestion-format citation).

| Standard | URL | What was confirmed |
|---|---|---|
| SARIF (Static Analysis Results Interchange Format) 2.1.0 | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html | OASIS Standard "Static Analysis Results Interchange Format (SARIF) Version 2.1.0 Plus Errata 01", dated 28 August 2023; defines "a standard format for the output of static analysis tools." Cited as the interchange format for ingesting deterministic scanner findings into a review. |

## Verified by direct fetch (2026-09-17) — ARIA APG

Verification date for the row below: **2026-09-17**. Added for the deep-code-review
`frontend-a11y.md` per-widget APG-contract lens.

| Standard | URL | What was confirmed |
|---|---|---|
| W3C ARIA Authoring Practices Guide (APG) | https://www.w3.org/WAI/ARIA/apg/ | W3C guide, title "ARIA Authoring Practices Guide (APG)"; purpose "how to apply accessibility semantics to common design patterns and widgets" via "ARIA roles, states and properties and by implementing keyboard support," with a per-pattern functional example. Confirms the APG supplies per-widget role/state/keyboard-interaction patterns for hand-built widgets. Cited as the per-widget contract in `frontend-a11y.md` (specific keys per widget — e.g. tablist Arrow/Home/End — are the APG's documented pattern behavior). |

## Verified by direct fetch (2026-09-18) — mutation testing

Verification date for the rows below: **2026-09-18**. Added for the deep-code-review
`testing-and-evals.md` mutation-testing lens (measuring the product suite's
fault-detection, not only line coverage).

| Standard / tool | URL | What was confirmed |
|---|---|---|
| PIT (pitest) — mutation testing | https://pitest.org/ | "Traditional test coverage (i.e line, statement, branch, etc.) measures only which code is executed by your tests. It does not check that your tests are actually able to detect faults in the executed code"; "The quality of your tests can be gauged from the percentage of mutations killed." Cited for coverage-measures-execution-not-fault-detection and the mutation-score concept; PIT is the JVM engine. |
| Stryker Mutator — configuration (`thresholds.break`) | https://stryker-mutator.io/docs/stryker-js/configuration/ | The `thresholds` config exposes `break`: "mutation score < break: Error! Stryker will exit with exit code 1, indicating a build failure." Cited as the available CI-gate operator (exit non-zero below a set score). **`break` defaults to `null` — "Set `break` to `null` (default) to never let your build fail" — so it gates only once explicitly set** (`high`/`low` default 80/60 and only colour the report). No specific threshold value is endorsed — treat the number as per-repo. Stryker is the JS/TS engine. |

## Verified by direct fetch (2026-09-19) — RAG retrieval-seam & agent-trajectory evals

Verification date for the rows below: **2026-09-19**. Added for the deep-code-review
`testing-and-evals.md` LLM-application eval lens (RAG retrieval quality + generation
faithfulness/relevancy + agent trajectory).

| Standard / tool | URL | What was confirmed |
|---|---|---|
| Lewis et al. (2020), "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" | https://arxiv.org/abs/2005.11401 | NeurIPS 2020. RAG = models that "combine pre-trained parametric and non-parametric memory for language generation" — a generator plus a retrieval component over external knowledge. The technique anchor for evaluating a RAG app at the retrieval seam. Fetched 2026-09-19. |
| RAGAS — RAG evaluation library | https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/ | Open-source eval library (a **tool**, not a standards body). The cited available-metrics index page lists the metric *names* (context precision, context recall, faithfulness, response relevancy, …); the per-metric definitions used in the skill were read on the sub-pages this session — faithfulness = factual consistency with the retrieved context; response relevancy = the answer addresses the question; context precision / recall = the retrieved context is relevant / complete. Cited as a tool that names the concepts; the skill frames the concept, not a vendor's exact formula. Fetched 2026-09-19. |

## Verified by direct fetch (2026-09-19) — post-quantum cryptography (A04)

Verification date for the rows below: **2026-09-19**. Added for the deep-code-review
`security-appsec.md` A04 crypto-agility / post-quantum-readiness dimension. Names are
the NIST standards' own; no compliance deadline is encoded (the review finding is a
non-agile primitive on long-lived data, not a date-driven mandate).

| Standard / tool | URL | What was confirmed |
|---|---|---|
| NIST FIPS 203 — ML-KEM | https://csrc.nist.gov/pubs/fips/203/final | "Module-Lattice-Based Key-Encapsulation Mechanism Standard"; standardizes **ML-KEM** (params ML-KEM-512/768/1024), "believed to be secure, even against adversaries who possess a quantum computer." Published 2024-08-13. Fetched 2026-09-19. |
| NIST FIPS 204 — ML-DSA | https://csrc.nist.gov/pubs/fips/204/final | "Module-Lattice-Based Digital Signature Standard"; standardizes **ML-DSA** for digital signatures, quantum-resistant. Published 2024-08-13. Fetched 2026-09-19. |
| NIST FIPS 205 — SLH-DSA | https://csrc.nist.gov/pubs/fips/205/final | "Stateless Hash-Based Digital Signature Standard"; standardizes **SLH-DSA**, "based on SPHINCS+." Published 2024-08-13. Fetched 2026-09-19. |

## Verified by direct fetch (2026-09-19) — EU CRA & VEX (supply-chain regulation)

Verification date for the rows below: **2026-09-19**. Added for the `business-ops`
regulated-domain-triage (CRA name-and-route) and the deep-code-review `security-appsec.md`
A03 (VEX). Named as regimes/artifacts; no compliance deadline or conformity conclusion is
encoded (business-ops routes applicability to counsel).

| Standard / tool | URL | What was confirmed |
|---|---|---|
| EU Cyber Resilience Act (CRA) — Regulation (EU) 2024/2847 | https://eur-lex.europa.eu/eli/reg/2024/2847/oj | "Regulation (EU) 2024/2847 … on horizontal cybersecurity requirements for products with digital elements." Manufacturer obligation categories confirmed: security-by-design; vulnerability handling + coordinated-vulnerability-disclosure + a security-update / support period; automatic-update + end-of-support transparency; stricter conformity assessment for "important"/"critical" categories. Exact timelines/class routed to counsel (not encoded). Fetched 2026-09-19. |
| CISA VEX — Vulnerability Exploitability eXchange (status & justification) | https://www.cisa.gov/resources-tools/resources/vulnerability-exploitability-exchange-vex-status-justification-document-june-2022 | CISA-published (June 2022, community-led). A producer-issued per-CVE assertion of whether a product is affected; status values NOT AFFECTED (with a justification), AFFECTED, FIXED, UNDER INVESTIGATION; complements (does not replace) an SBOM. Fetched 2026-09-19. |

## Verified by direct fetch (2026-09-19) — ML pipeline correctness (leakage, reproducibility, label quality)

Verification date for the rows below: **2026-09-19**. Added for the deep-code-review
`testing-and-evals.md` ML-pipeline-correctness lens (leakage + reproducibility) and
`data-quality.md` label-quality bullet.

| Standard / tool | URL | What was confirmed |
|---|---|---|
| scikit-learn — Common pitfalls (data leakage) | https://scikit-learn.org/stable/common_pitfalls.html | "data leakage occurs when information that would not be available at prediction time is used when building the model" → "overly optimistic performance estimates"; "Always split the data into train and test subsets first, particularly before any preprocessing"; "never call `fit` on the test data"; a Pipeline prevents leakage in CV/tuning. Fetched 2026-09-19. |
| Breck et al. (2017), "The ML Test Score" | https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/ | IEEE Big Data 2017; a rubric of "28 specific tests and monitoring needs" for ML production-readiness. Cited for the reproducible-training principle (retrain on the same data → the same model; seed the RNG). The specific rubric-item text was NOT reproduced on the fetched landing page — cited by paper for the principle, not a verbatim quote. Fetched 2026-09-19. |
| Northcutt, Athalye, Mueller (2021), "Pervasive Label Errors in Test Sets…" | https://arxiv.org/abs/2103.14749 | NeurIPS 2021 (Datasets & Benchmarks). "Errors in test sets are numerous and widespread: we estimate an average of at least 3.3% errors across the 10 datasets"; correcting them can flip benchmark rankings (smaller models can overtake larger); ~half of algorithmically-flagged errors confirmed genuine by crowdsourcing. Fetched 2026-09-19. |


## Verified by direct fetch (2026-09-19) — MCP (Model Context Protocol) security

Verification date for the rows below: **2026-09-19**. Added for the deep-code-review
`security-ai-agents.md` MCP server/client security section. The OWASP MCP Top 10 is named
as a **beta** regime only; its category IDs are not walked as current.

| Standard / tool | URL | What was confirmed |
|---|---|---|
| MCP Security Best Practices (official spec) | https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices | Names, with `MUST`/`SHOULD` controls: **Confused Deputy** (OAuth proxy w/ static client-id + dynamic registration + consent cookie -> per-client consent MUST run before the third-party flow; exact `redirect_uri` match; `state` set only after consent); **Token Passthrough** ("MCP servers MUST NOT accept any tokens that were not explicitly issued for the MCP server"); SSRF on OAuth metadata discovery; one-click local-server consent (show the exact command); scope minimization. Fetched 2026-09-19. |
| OWASP MCP Top 10 | https://owasp.org/www-project-mcp-top-10/ | Official OWASP project, "OWASP MCP Top 10," **Phase-3 Beta Release and Pilot Testing** ("We are here right now"); lead Vandana Verma Sehgal; scope = MCP-enabled systems lifecycle, ten risk categories (`MCPxx:2025`). Named as a beta regime; categories NOT enumerated as current. Fetched 2026-09-19. |
| Tool-description poisoning & rug-pull (Willison / Invariant Labs) | https://simonwillison.net/2025/Apr/9/mcp-prompt-injection/ | Post dated 2025-04-09. Tool-description poisoning: instructions in a tool docstring are "visible to the LLM, not normally displayed to users" (Invariant Labs demo: an `add()` docstring makes the model read a private file and pass it as a parameter). Rug pull: "MCP tools can mutate their own definitions after installation"; clients "do not notify users about changes to the tool description" -> mitigation: alert on description change. Fetched 2026-09-19. |


## Verified by direct fetch (2026-09-19) — ML fairness / bias

Verification date for the rows below: **2026-09-19**. Added for the deep-code-review
`testing-and-evals.md` ML-fairness detection lens. No legal disparate-impact threshold is
encoded (the code check is measure + deliberate handling + documentation; the legal
determination routes to counsel).

| Standard / tool | URL | What was confirmed |
|---|---|---|
| NIST SP 1270 — Bias in AI | https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.1270.pdf | "Towards a Standard for Identifying and Managing Bias in Artificial Intelligence" (March 2022, 86 pp). Identifies **three categories of bias** — systemic, statistical/computational, human; three mitigation challenges — datasets, testing-and-evaluation (TEVV), human factors. Framing: computational fairness metrics are necessary but "human and systemic institutional and societal factors are significant sources of AI bias as well, and are currently overlooked"; and "Trustworthy and Responsible AI is not just about whether a given AI system is biased, fair or ethical, but whether it does what is claimed." PDF read directly 2026-09-19. |
| Model Cards for Model Reporting (Mitchell et al., 2019) | https://arxiv.org/abs/1810.03993 | FAT* '19. Proposes model cards documenting benchmarked evaluation "across different cultural, demographic, or phenotypic groups (e.g., race, geographic location, sex, Fitzpatrick skin type) and intersectional groups," plus the model's intended-use context, performance-evaluation procedures, and limitations. Fetched 2026-09-19. |
| RFC 9457 — Problem Details for HTTP APIs | https://www.rfc-editor.org/rfc/rfc9457.html | Obsoletes RFC 7807. Defines media type `application/problem+json` (and `application/problem+xml`); core members `type`/`status`/`title`/`detail`/`instance` (§3.1) plus extension members (§3.2). Fetched + verified 2026-09-19. |
| Google AIP-134 — Standard methods: Update | https://google.aip.dev/134 | Full-replacement update via `PUT` / `update_mask="*"`; warns "API producers need to be conscious of how adding new, mutable fields to a resource will be handled when consumers use `*` without knowledge of said new, mutable fields" — an old client's read-modify-write round-trip clears a field it predates (the Book/rating example). Fetched + verified 2026-09-19. |
| CWE-203 — Observable Discrepancy | https://cwe.mitre.org/data/definitions/203.html | "The product behaves differently or sends different responses under different circumstances in a way that is observable to an unauthorized actor." Examples cover user/account enumeration and timing side-channels. Fetched + verified 2026-09-19. |
| NIST Privacy Framework — CT.DP-P Disassociated Processing | https://csf.tools/reference/pf/pf-v1-0/ct-p/ct-dp-p/ | Control-P category "Disassociated Processing": CT.DP-P1 "processed to limit observability and linkability", CT.DP-P2 "limit the identification of individuals (de-identification, tokenization)", CT.DP-P3 "limit the formulation of inferences about individuals." Fetched + verified 2026-09-19. |
| WAI-ARIA (using-aria) — Rules of ARIA Use | https://www.w3.org/TR/using-aria/ | 4th rule verbatim: "Do not use role='presentation' or aria-hidden='true' on a focusable element." Prevents a focusable element hidden from assistive tech while still in the tab order. Fetched + verified 2026-09-19. |
| WCAG 2.2 SC 2.2.1 Timing Adjustable | https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html | Level A. For a time limit: turn off, adjust (>=10x default before encountering it), or extend (warned before expiry, given >=20s + a simple action, and able to extend at least ten times). Exceptions: real-time event, essential, >20 hours. Fetched + verified 2026-09-19. |
| WCAG 2.2 SC 2.2.2 Pause, Stop, Hide | https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html | Level A. Moving/blinking/scrolling that auto-starts, lasts >5s, in parallel with other content needs a pause/stop/hide (unless essential); auto-updating content has no 5s grace. Fetched + verified 2026-09-19. |
| Core Web Vitals (web.dev) | https://web.dev/articles/vitals | Thresholds assessed at the 75th percentile of real-user page loads (field data). "Only field measurement can accurately capture the complete picture"; lab (Lighthouse) "is not a substitute for field measurement." Fetched + verified 2026-09-19. |
| WCAG 2.2 SC 2.3.3 Animation from Interactions | https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html | Level AAA. "Motion animation triggered by interaction can be disabled, unless the animation is essential to the functionality or the information being conveyed." Applies to interaction-INITIATED non-essential motion (parallax, decorative transitions); SC 2.2.2 governs automatically-started animation instead. Fetched + verified 2026-09-19. |
| SLSA v1.0 — Build track levels | https://slsa.dev/spec/v1.0/levels | Build L1 "provenance exists" (trivial to forge, may be unsigned); L2 adds signed provenance from a hosted build platform and "downstream verification of provenance includes validating the authenticity of the provenance"; L3 adds a hardened, tamper-resistant build. Consumer verification compares expected vs actual provenance — subject digest, builder identity, canonical source. Fetched + verified 2026-09-19. |
| W3C Trace Context | https://www.w3.org/TR/trace-context/ | `traceparent` = `version-trace-id-parent-id-trace-flags` (e.g. `00-0af7…-b7ad…-01`). A vendor receiving `traceparent`/`tracestate` "MUST send it to outgoing requests" — the propagation that keeps a distributed trace unbroken across services/vendors. Fetched + verified 2026-09-19. |
| Go Memory Model | https://go.dev/ref/mem | "A data race is defined as a write … happening concurrently with another read or write … unless all the accesses involved are atomic (sync/atomic)." "Programs with races are incorrect." A racy read of a value larger than one word "can lead to inconsistent values not corresponding to a single write" and, for interface/map/slice/string, "arbitrary memory corruption." Fetched + verified 2026-09-19. |
| C++ data races (cppreference) | https://en.cppreference.com/w/cpp/language/multithread | "If a data race occurs, the behavior of the program is undefined" — a conflicting non-atomic access unordered by happens-before. Basis for the C/C++ "data race = UB" scoping (contrast Go's "incorrect"). Fetched + verified 2026-09-19. |
| Rust data races (Reference) | https://doc.rust-lang.org/reference/behavior-considered-undefined.html | "Data races." listed among behaviors considered undefined; "`unsafe` only means that avoiding undefined behavior is on the programmer; it does not change anything about the fact that Rust programs must never cause undefined behavior." Backs the "Rust `unsafe` data race = UB" scoping alongside C/C++ (contrast Go's "incorrect"/tearing). Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — data-pipeline contract & lineage standards

| Standard / source | URL | What was confirmed |
|---|---|---|
| Confluent — Schema Evolution and Compatibility | https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html | Compatibility modes: BACKWARD ("consumers using new schema can read data written with old schema") needs "upgrade all consumers before you start producing new events"; FORWARD ("consumers using old schema can read data written with new schema") needs "first upgrade all producers ... then upgrade the consumers"; FULL is both (add/remove optional only), producers/consumers upgrade "independently"; the `*_TRANSITIVE` variants check against all previous versions, not just the last; NONE disables checks; default BACKWARD. Fetched + verified 2026-09-19. |
| OpenLineage — Column-Level Lineage facet | https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet | Records "which input columns are used to produce which output columns and in what way": each output field maps to inputFields (each with namespace, dataset `name`, field) + transformations (type DIRECT/INDIRECT; subtypes e.g. IDENTITY/AGGREGATION are DIRECT, JOIN/FILTER are INDIRECT; plus a masking flag). Answers "Which root input columns are used to construct column x?" Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — GitHub pull_request webhook taxonomy

| Standard / source | URL | What was confirmed |
|---|---|---|
| GitHub — pull_request webhook activity types | https://docs.github.com/en/webhooks/webhook-events-and-payloads | The `pull_request` event supports distinct activity types incl. `opened`, `edited`, `labeled`, `unlabeled`, `synchronize`, `closed`, `ready_for_review` (full list on page); `labeled`/`unlabeled` are separate actions from `edited`, so a label add/remove does **not** fire `edited`. Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — reliability under stress (retry budgets & deadline propagation)

| Standard / source | URL | What was confirmed |
|---|---|---|
| Google SRE book — Addressing Cascading Failures | https://sre.google/sre-book/addressing-cascading-failures/ | Retry budget: "Limit retries per request. Don't retry a given request indefinitely." A process-wide ceiling — "only allow 60 retries per minute in a process, and if the retry budget is exceeded, don't retry; just fail the request." Layered amplification: attempts multiply across stack layers — "a single user action may create 64 attempts (4^3) on the database." Fetched + verified 2026-09-19. |
| gRPC — Deadlines | https://grpc.io/docs/guides/deadlines/ | Deadline propagation: "gRPC converts the deadline to a timeout from which the already elapsed time is already deducted," so a downstream inherits the caller's remaining time (automatic in Java/Go, explicit opt-in in C++). Basis for "propagate the remaining deadline, don't reset a fresh timeout per hop." Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — HTTP caching & PostgreSQL CONCURRENTLY

| Standard / source | URL | What was confirmed |
|---|---|---|
| RFC 9111 — HTTP Caching | https://www.rfc-editor.org/rfc/rfc9111 | §4.4 (invalidation): a cache "MUST invalidate the target URI" on a non-error response to an unsafe request method; related URIs (Location/Content-Location) are only "candidates for invalidation" and never cross-origin — derived-key fan-out is the application's job. §4.1 (Vary): "MUST NOT use that stored response without revalidation unless all the presented request header fields nominated by that Vary field value match"; a Vary value containing "*" "always fails to match." Fetched + verified 2026-09-19. |
| PostgreSQL — CREATE INDEX (CONCURRENTLY) | https://www.postgresql.org/docs/current/sql-createindex.html | A failed concurrent build "will fail but leave behind an 'invalid' index" that "will be ignored for querying purposes ... however it will still consume update overhead"; recover by dropping and retrying, or "rebuild the index with REINDEX INDEX CONCURRENTLY." "A regular CREATE INDEX command can be performed within a transaction block, but CREATE INDEX CONCURRENTLY cannot." Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — time, dates & time zones

| Standard / source | URL | What was confirmed |
|---|---|---|
| TC39 Temporal — time zones & offsets | https://tc39.es/proposal-temporal/docs/timezone.html | Wall-clock time "depends on the time zone of the clock"; exact time "is the same everywhere"; `Temporal.ZonedDateTime` "encapsulates ... an exact time ... its wall-clock equivalent ... and the time zone that links the two." Basis for the instant-vs-wall-clock distinction. Fetched + verified 2026-09-19. |
| PEP 495 — Local Time Disambiguation | https://peps.python.org/pep-0495/ | "A local time that falls in the fold is called ambiguous"; "A local time that falls in the gap is called missing"; "The `fromutc()` method should never produce a time in the gap." Basis for fold/gap disambiguation at DST transitions. Fetched + verified 2026-09-19. |
| IANA tz database — Theory and pragmatics | https://data.iana.org/time-zones/tzdb/theory.html | "The `tz` database predicts future timestamps, and current predictions will be incorrect after future governments change the rules ... software can mess up after the rule change if it blithely relies on conversions made before the change." Basis for treating tzdata as a stale-able dependency + re-resolving future wall-clock times. Fetched + verified 2026-09-19. |
| Google — Leap Smear | https://developers.google.com/time/smear | "instead of applying leap seconds to our servers using clock steps, we have 'smeared' the extra second across the hours before and after each leap." Basis for the leap-second / duration caveat (choose a consistent approach; don't assume 86,400 s/day). Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — online experimentation infrastructure

| Standard / source | URL | What was confirmed |
|---|---|---|
| Google — Overlapping Experiment Infrastructure | https://research.google/blog/overlapping-experiment-infrastructure-more-better-faster-experimentation/ | "Google's infrastructure supports this vast experimentation by using orthogonal diversion criteria for experiments in different 'layers' so that each event (e.g. a web search) can be assigned to multiple experiments." Basis for isolating concurrent experiments (orthogonal layers / mutual exclusion) so they don't confound. Companion paper: Tang et al., "Overlapping Experiment Infrastructure," KDD 2010 (by name). Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — webhooks (provider side)

| Standard / source | URL | What was confirmed |
|---|---|---|
| Standard Webhooks (community spec) | https://github.com/standard-webhooks/standard-webhooks | Outbound-webhook signing convention: the message's "ID, timestamp and body are concatenated (delimited by full-stops) and then signed" with HMAC-SHA256 (`msg_id.timestamp.payload`); headers `webhook-id` / `webhook-timestamp` / `webhook-signature`; the signature header is "a space delimited list of signatures" to "support zero downtime secret rotation"; verify `webhook-timestamp` "is within some allowable tolerance ... to prevent replay attacks." A multi-vendor community spec (guided by an ~8-company technical steering committee), not an IETF/W3C standard — cite as a convention. Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-19) — streaming transports (WebSocket / SSE)

| Standard / source | URL | What was confirmed |
|---|---|---|
| WHATWG HTML — Server-sent events (§9.2) | https://html.spec.whatwg.org/multipage/server-sent-events.html | Reconnection re-sends the last id: "Set (`Last-Event-ID`, lastEventIDValue) in request's header list" when the last event ID string is not empty; the reconnection time "must initially be an implementation-defined value, probably in the region of a few seconds," with "an exponential backoff delay" on repeated failure. Fetched + verified 2026-09-19. |
| RFC 6455 — The WebSocket Protocol | https://www.rfc-editor.org/rfc/rfc6455 | A Ping "may serve either as a keepalive or as a means to verify that the remote endpoint is still responsive"; "Upon receipt of a Ping frame, an endpoint MUST send a Pong frame in response, unless it already received a Close frame"; "Message fragments MUST be delivered to the recipient in the order sent by the sender" (ordering is per-connection). Fetched + verified 2026-09-19. |
| WHATWG — WebSocket `bufferedAmount` | https://websockets.spec.whatwg.org/ | `bufferedAmount` = "the number of bytes of application data ... that have been queued using `send()` but that ... had not yet been transmitted to the network"; the flow-control example paces sends "at whatever rate the network _can_ handle," checking `bufferedAmount`. Basis for per-connection send-side backpressure. Fetched + verified 2026-09-19. |

## Verified by direct fetch (2026-09-20) — concurrency lock-ordering / deadlock prevention

| Standard / source | URL | What was confirmed |
|---|---|---|
| PostgreSQL Documentation — 13.3.4 Deadlocks (Explicit Locking) | https://www.postgresql.org/docs/current/explicit-locking.html | Consistent lock ordering is the primary defense: "The best defense against deadlocks is generally to avoid them by being certain that all applications using a database acquire locks on multiple objects in a consistent order." Retry is the fallback: "If it is not feasible to verify this in advance, then deadlocks can be handled on-the-fly by retrying transactions that abort due to deadlocks." Fetched + verified 2026-09-20. |
| cppreference — std::scoped_lock | https://en.cppreference.com/w/cpp/thread/scoped_lock | A multi-mutex lock primitive that avoids deadlock regardless of the order mutexes are passed: "If several mutexes are given, deadlock avoidance algorithm is used as if by std::lock." Basis for citing a deadlock-avoiding multi-lock primitive as an alternative to a hand-maintained global order. Fetched + verified 2026-09-20. |

## Verified by direct fetch (2026-09-20) — JWT algorithm confusion (A07)

| Standard / source | URL | What was confirmed |
|---|---|---|
| OWASP ASVS v5.0.0 — V9.1.2 (Self-contained Tokens) | https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x18-V9-Self-contained-Tokens.md | 9.1.2 (**Level 1**, confirmed at source): "Verify that only algorithms on an allowlist can be used to create and verify self-contained tokens, for a given context. The allowlist must include the permitted algorithms, ideally only either symmetric or asymmetric algorithms, and must not include the 'None' algorithm. If both symmetric and asymmetric must be supported, additional controls will be needed to prevent key confusion." (Verified 2026-09-20 against tag v5.0.0_release; discharges the line-115 ASVS-5.0 level caveat for V9.1.2 ONLY.) |
| OWASP JSON Web Token Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html | alg:none — "Make sure that `"alg":"none"` is not accepted by your JWT parser." Algorithm/key-type confusion — "if possible, hardcode the accepted algorithms and do not mix public-key digital signatures algorithms and MAC algorithms." Fetched + verified 2026-09-20. |

## Verified by direct fetch (2026-09-20) — session termination & timeout (A07)

| Standard / source | URL | What was confirmed |
|---|---|---|
| OWASP ASVS v5.0.0 — V7 Session Management (7.3.1 / 7.3.2 / 7.4.1) | https://github.com/OWASP/ASVS/blob/v5.0.0_release/5.0/en/0x16-V7-Session-Management.md | 7.4.1 (**L1**): "Verify that when session termination is triggered (such as logout or expiration), the application disallows any further use of the session … Applications using self-contained tokens will need a solution such as maintaining a list of terminated tokens, disallowing tokens produced before a per-user date and time or rotating a per-user signing key." 7.3.1 (L2) inactivity timeout and 7.3.2 (L2) absolute maximum session lifetime, each "such that re-authentication is enforced according to risk analysis and documented security decisions." Verified 2026-09-20 at tag v5.0.0_release. |
| OWASP Session Management Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html | Idle ranges: "Common idle timeouts ranges are 2-5 minutes for high-value applications and 15-30 minutes for low risk applications." Absolute: "an appropriate absolute timeout range could be between 4 and 8 hours." Fetched + verified 2026-09-20. |

## Verified by direct fetch (2026-09-20) — supply chain: committed binary artifacts

| Standard / source | URL | What was confirmed |
|---|---|---|
| OpenSSF Scorecard — Binary-Artifacts check | https://github.com/ossf/scorecard/blob/main/docs/checks.md | "Risk: `High` (non-reviewable code)". "This check determines whether the project has generated executable (binary) artifacts in the source repository." Remediation steps: "Remove the generated executable artifacts from the repository." / "Build from source." (The Binary-Artifacts section specifically; distinct from the other Scorecard rows above that cite the same catalog URL.) Fetched + verified 2026-09-20. |
