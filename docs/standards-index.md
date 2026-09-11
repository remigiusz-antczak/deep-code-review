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
| OWASP Top 10 for LLM Applications 2025 | https://genai.owasp.org/llm-top-10/ | LLM01–LLM10:2025 names verbatim. A 2026 edition now exists (verified 2026-08-21; see the verification addendum below). |
| OWASP Top 10 for LLM Applications 2025 (resource) | https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/ | Edition landing page; document publication 2024-11-17. |
| OWASP Top 10 for Agentic Applications 2026 | https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ | Framework exists; published 2025-12-09; peer-reviewed by 100+ practitioners. (ASI01–ASI10 titles later confirmed verbatim from the official 2025-12-09 announcement — see the 2026-08-21 addendum below; the authoritative PDF was not re-fetched and wins on any conflict.) |
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
| GitHub Actions — Security hardening for GitHub Actions | https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions | Verbatim: `pull_request_target` / `workflow_run` used with an untrusted checkout "expose the repository to security compromises" and "must not explicitly check out untrusted code." Untrusted `${{ github.event.* }}` should be routed through an intermediate `env:` variable rather than inlined into a `run:` script (the value "is stored in memory and used as a variable, and doesn't interact with the script generation process"). Set the default `GITHUB_TOKEN` to "read access only for repository contents," escalating per job as required. (`persist-credentials` on `actions/checkout` was **not** found on this page.) |
| NIST AI Risk Management Framework — core functions (verified 2026-09-11) | https://www.nist.gov/itl/ai-risk-management-framework | The four core function names — **Govern, Map, Measure, Manage** — appear on the official NIST ITL framework page. Only the function names were confirmed here; the full AI RMF 1.0 (AI 100-1) and the Generative AI Profile (AI 600-1) control specifics were **not** fetched this session — cite those by name only (see the by-name list below). |

## Referenced by name (not fetched this session — verify before citing a URL)

- **OWASP WSTG** — how-to-test companion for each web risk.
- **OWASP Cheat Sheet Series** — concrete implementation guidance.
- **MITRE CWE / CVE** — weakness and vulnerability naming.
- **MITRE ATLAS** — adversarial-ML and agent-tool attack techniques.
- **NIST SSDF (SP 800-218)** and the **NIST AI RMF Generative AI Profile (AI 600-1)**
  — secure-development and AI-risk lifecycle framing. (The AI RMF core function names
  are verified in the table above; these document/profile specifics were not fetched.)
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
- **Nielsen's usability heuristics** — named grounding for domain P's design
  half (`references/product-ux-quality.md`). No URL cited this session; fetch
  before quoting a numbered heuristic or year.
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
- **Product-analytics frameworks** (named by `growth-analytics`): AARRR / "Pirate
  Metrics" (McClure); the North Star Metric framework; vanity-vs-actionable metrics;
  retention cohort analysis; "one metric that matters"; activation / aha-moment
  analysis. Named leads only — no URL or figure fetched this session; verify before
  citing a specific figure or threshold.

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
