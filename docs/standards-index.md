# Standards index

Every standard the skill relies on, split into what was **verified by direct
fetch** for this release and what is **referenced by name** (not fetched — verify
the current version before citing a specific URL). This split enforces the skill's
own rule: cite only URLs you have verified.

Verification date for all direct fetches below: **2026-08-13**.

---

## Verified by direct fetch (2026-08-13)

| Standard | URL | What was confirmed |
|---|---|---|
| OWASP Top 10:2025 | https://owasp.org/Top10/2025/ | Categories A01–A10:2025 verbatim (A01 Broken Access Control … A10 Mishandling of Exceptional Conditions). |
| OWASP Top 10 for LLM Applications 2025 | https://genai.owasp.org/llm-top-10/ | 2025 is the current edition; LLM01–LLM10:2025 names verbatim. No 2026 LLM edition was referenced by the authoritative page as of this date. |
| OWASP Top 10 for LLM Applications 2025 (resource) | https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/ | Edition landing page; document publication 2024-11-17. |
| OWASP Top 10 for Agentic Applications 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | Framework exists; published 2025-12-09; peer-reviewed by 100+ practitioners. (The ASI01–ASI10 titles were corroborated across secondary sources but not confirmed verbatim from the authoritative PDF — the skill presents the risk themes and points here for the authoritative list.) |
| OWASP API Security Top 10 (2023) | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ | API1–API10:2023 names verbatim. |
| CWE Top 25 (2025) | https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html | Official 2025 edition, last updated 2025-12-15; top entries (XSS, SQLi, CSRF, Missing Authorization, OOB Write, Path Traversal, Use-After-Free, OOB Read, OS Command Injection, Code Injection). |
| WCAG 2.2 | https://www.w3.org/TR/WCAG22/ | W3C Recommendation, dated 2024-12-12; conformance levels A/AA/AAA; WCAG 3.0 still in development. |
| Google Engineering Practices — Standard of Code Review | https://google.github.io/eng-practices/review/reviewer/standard.html | Core standard: approve once the change "definitely improves the overall code health," even if imperfect. |
| Diátaxis | https://diataxis.fr/ | Four documentation types: Tutorials, How-to guides, Reference, Explanation. |
| C4 model | https://c4model.com/ | Four abstraction levels: Context, Container, Component, Code. |
| OWASP Top 10:2025 — A03 detail | https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/ | A03 absorbed the former A06:2021 "Vulnerable and Outdated Components"; explicitly covers software that is "vulnerable, unsupported, or out of date"; guidance to upgrade "in a risk-based, timely fashion" and to "deliberately choose which version of a dependency you use and upgrade only when there is need"; names OWASP Dependency-Track / Dependency-Check / retire.js as inventory tools. |
| OpenSSF Scorecard | https://github.com/ossf/scorecard | Automated repo security scorer (0–10 per check). Check names verbatim: `Maintained` (active within ~90 days), `Dependency-Update-Tool` (Dependabot/Renovate present), `Vulnerabilities` (unfixed vulns, via the OSV service), `Pinned-Dependencies`. |
| OSV | https://osv.dev/ | Distributed open-source vulnerability database spanning 40+ package ecosystems (npm, PyPI, Go, Maven, Debian, …); `osv-scanner` scans a lockfile or SBOM and queries by package version or commit hash. |
| Semantic Versioning | https://semver.org/ | MAJOR = "incompatible API changes"; MINOR = "add functionality in a backward compatible manner"; PATCH = "backward compatible bug fixes." |
| GitHub Dependabot — version updates | https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates | Opens automated PRs to update dependencies to the latest version "even when they don't have any vulnerabilities"; documented reviewer step is to "check that your tests pass, review the changelog and release notes." (This page did **not** state that Dependabot PRs auto-trigger CI or support grouping — those are not claimed by the skill.) |
| endoflife.date | https://endoflife.date/ | Tracks end-of-life / support-lifecycle dates for 400+ products (programming languages, frameworks, databases, OSes, devices, cloud services); offers an API. |

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
| OWASP ASVS (project) | https://owasp.org/www-project-application-security-verification-standard/ | Latest stable version is **5.0.0** (news: released 30 May 2025). Requirement id form `v<version>-<chapter>.<section>.<requirement>` (e.g. `v5.0.0-1.2.5`). Use as L1/L2/L3 verification checklist — claiming "ASVS covered" in a review requires naming level + chapters actually checked. |

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

## Referenced by name (not fetched this session — verify before citing a URL)

- **OWASP WSTG** — how-to-test companion for each web risk.
- **OWASP Cheat Sheet Series** — concrete implementation guidance.
- **MITRE CWE / CVE** — weakness and vulnerability naming.
- **MITRE ATLAS** — adversarial-ML and agent-tool attack techniques.
- **NIST SSDF (SP 800-218)** and **NIST AI RMF + Generative AI Profile (AI 600-1)**
  — secure-development and AI-risk lifecycle framing.
- **SLSA** — build/supply-chain provenance levels.
- **CIS Benchmarks** — OS/container/cloud hardening baselines.
- **ISO/IEC 25010** — software product-quality model (the axes this review
  covers).
- **The Twelve-Factor App** — config/dependency/deploy hygiene.
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

> When the skill needs a version-specific detail from any of these, it must fetch
> the current source at review time and cite only the URL it verified.
