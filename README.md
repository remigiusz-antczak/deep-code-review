# Perun

[![gates](https://github.com/remigiusz-antczak/deep-code-review/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/remigiusz-antczak/deep-code-review/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Perun makes your AI coding agent review code the same careful way every
time. Each problem it reports points to the exact file and line and comes with
a fix. Anything it can't prove is marked `unverified` instead of guessed.**

Perun is a set of skills: plain-text instruction files that an AI coding agent
reads when a task matches. The default skill, `deep-code-review`, turns "look
this over" into a fixed audit of correctness, security, AI/LLM safety, data
quality, performance and cost, reliability, testing, infrastructure, docs, and
accessibility, and ends in a report ranked by severity. It works on any
language, on any agent that can read files, and as a one-shot prompt or a human
checklist. Ten opt-in skills extend it to gated delivery, planning, and product
work. Free (MIT), runs fully local; you pay only for your agent's model usage.

**Start here:** [Quick start](#quick-start) ·
[New to AI agents](#new-to-ai-agents) ·
[Already using an agent](#already-using-claude-code-cursor-or-codex) ·
[Running agent fleets](#running-agent-fleets) · [What's new](#whats-new) ·
[FAQ](#faq)

## Quick start

**No install (any AI chat):** copy
[`.claude/skills/deep-code-review/SKILL.md`](.claude/skills/deep-code-review/SKILL.md)
into the chat, paste one file you care about, and ask
`Review this with scope FILE.`

**Install into a project (three commands, from a pinned release):**

```bash
git clone --branch vX.Y.Z --depth 1 https://github.com/remigiusz-antczak/deep-code-review.git
cd deep-code-review && shasum -a 256 -c SHA256SUMS   # Linux: sha256sum -c SHA256SUMS
./install.sh /path/to/your/project                   # review only (the default)
```

> [!IMPORTANT]
> Replace `vX.Y.Z` with the latest tag on the Releases page and keep the
> checksum step. Don't `curl | bash` an unpinned `HEAD`; the review itself flags
> that as a supply-chain risk.

Then ask your agent `run a deep code review DIFF origin/main`.

---

## What problems it solves

Each row is a shipped mechanism; the version is where
[`CHANGELOG.md`](CHANGELOG.md) records it.

| Problem | Without Perun | With Perun | Since |
|---|---|---|---|
| A design port looks right but is incomplete | A pixel or size diff passes a page with a missing button or row. | `parity_differ.py` compares each section's element inventory (headings, text, controls, images, list rows) between design and app. Sizes are never inputs; one missing element shows completeness below 100%. A structurally wrong port fails even when the pixel difference is tiny. | 1.442.0, 1.447.0 |
| Subagents flood the chat | Every helper agent returns a long report, multiplied across a fleet. | A `SubagentStop` hook blocks a final message over 800 characters or 10 lines; the deliverable goes in a file. | 1.434.0 |
| Lessons stay advice | A lesson is written into the instructions and an agent skips it. | Perun's CI fails a commit that edits skill instructions without also touching a test, eval, or script, unless it states a `No-Mechanism-Reason:`. | 1.436.0 |
| "Deployed" is taken on faith | A green CI badge counts as proof the change is live. | `surface_check.py` compares the running app's build id with the commit; a missing id reports `COULD_NOT_CHECK`, never a pass. | 1.441.0 |
| Owner requests get lost | Asks disappear when an agent's context is compacted. | `task_ledger.py` keeps every ask verbatim; "done" needs evidence (a commit, URL, issue, or test id). | 1.442.0 |
| Tests pass until a date | A fixture built from a fixed "now" passes until the calendar crosses a threshold, then fails every branch at once. | The review flags the pattern and asks for an injected clock (or fixtures derived from the real clock) plus tests before, at, and after the threshold. | 1.446.0 |

---

## What you get

| Outcome | What it looks like |
|---|---|
| A report you can act on | Findings ranked Blocker → Critical → High → Medium → Low → Nit, each with `file:line` evidence and a fix. See the [fictional example report](docs/example-review-report.md). |
| A summary for non-coders | A traffic-light health scorecard, the top risks in plain terms, and the decisions that need an owner. |
| Broad, fixed coverage | 21 audit domains (lettered A–W), an adversarial red-team pass, and a check for costly work that adds no value (repeated identical API/LLM/DB calls, over-fetching). |
| Lower context cost | The method files every review must read dropped from 65,903 to 28,025 estimated tokens (a FULL repo review: 87,137 to 36,096), about 57% less. A web review's must-read set dropped from 86,820 to at most 23,349. CI blocks either number from growing. |
| Checks that run, not just advice | 25 shipped gate scripts carry a `--selftest` that proves they catch a planted violation, run in CI on every change. `--with-gates` wires the review's own gates into your repo's CI. |
| A bar that stays | An optional final phase writes an `AGENTS.md` and pre-commit/CI gates into your repo, so the next contributor or agent, from any vendor, is held to the same bar. |

Where the numbers come from: token figures are characters ÷ 4, from
[`CHANGELOG.md`](CHANGELOG.md) and the CI ceilings in
[`scripts/mustload-budgets.tsv`](scripts/mustload-budgets.tsv); the domain count
is the domain map in
[`SKILL.md`](.claude/skills/deep-code-review/SKILL.md); the script count is the
`.claude/skills/*/scripts/*.py` files with a `--selftest`, each invoked in
[`ci.yml`](.github/workflows/ci.yml).

---

## Pick your path

### New to AI agents

An **AI coding agent** is a program (for example Claude Code, Cursor, or Codex)
that uses an AI model to read, edit, and run code in your project when you ask
in plain words. A **skill** is a folder of written instructions the agent loads
when your request matches it. Think of it as handing a new colleague the team's
review checklist.

Start with the no-install option in [Quick start](#quick-start): it needs only
a chat window. Step-by-step, including installing into a real project:
[`docs/getting-started.md`](docs/getting-started.md).

### Already using Claude Code, Cursor, or Codex

Install with the three commands in [Quick start](#quick-start). Then ask your
agent `run a deep code review DIFF origin/main`, or use
`/deep-code-review FULL`, `/deep-code-review FILE src/auth.ts` on hosts with
slash commands.

**What changes:** the installer copies the skill into `.claude/skills/`,
`.cursor/skills/`, and `.agents/skills/`, and adds a version-stamped pointer to
`AGENTS.md`. Any agent in the repo now reviews with the same phases, the same
severity scale, and the same "no evidence, no finding" rule. Run
`./install.sh --recommend /path/to/your/project` first to see a suggested
overlay pack without writing anything. Codex, other hosts, updating, and
uninstalling: [`docs/getting-started.md`](docs/getting-started.md).

### Running agent fleets

The delivery overlay (`--with-delivery`, included in `--full`) and the
conductor overlay (`--with-ceo`) ship fleet rules as scripts that exit
non-zero instead of prose an agent may skip:

- **Handback cap:** an opt-in `SubagentStop` hook blocks a subagent's final
  chat message over 800 characters or 10 lines; the deliverable goes in a file.
- **Owner priority and ledgers:** `focus_gate.py` blocks work outside an
  owner-committed priority until its acceptance command passes or the work is
  blocked on someone else. `task_ledger.py` keeps every owner ask verbatim, so
  none is lost when context compacts.
- **Coordination:** isolation checks at lane start, claim tie-breaks, a
  cross-lane test lock, and a typed coordination board.
- **Merge train:** `merge_train.py` compares against freshly fetched refs and
  fixes a red base forward only under an owner-authored grant.
- **Proof of done:** `lane_guard.py handback` accepts a lane's claim only when
  the cited commit is the branch head and every cited file is committed at it;
  `surface_check.py` checks a "deployed" claim against the running build.

Every mechanism, what it blocks, and how to switch it on:
[`docs/for-fleets.md`](docs/for-fleets.md).

---

## How it works

```
 you: "review this"
        |
        v
 +-------------+  reads    SKILL.md: the map (max 24 KB). Scope, phases,
 | your agent  | --------> severity scale, and which file to read when.
 +-------------+                  |
        |                         | routes on a stated trigger
        |                         v
        |  loads only    references/*.md: depth for security, data,
        |  what applies  accessibility, one file per language family ...
        |
        |  runs          scripts/: gates that answer with an exit code
        |                (fix has a test, no committed binaries, ...)
        v
 severity-ranked report: file:line evidence and a fix for every finding
```

The review runs in fixed phases: pin the exact commit, gather ground truth
(build, tests, lint), audit each applicable domain, run the adversarial pass,
then rank, deduplicate, and report. The full method, first-response block,
and domain map live in [`SKILL.md`](.claude/skills/deep-code-review/SKILL.md).

---

## Skill catalog

Only `deep-code-review` installs by default. Everything else is opt-in.

| Skill | Use it to… | Install |
|---|---|---|
| `deep-code-review` | review, harden, or quality-gate a repo, PR, or diff | **default** |
| `agentic-delivery` | build a feature or migration under gated, multi-role delivery | `--with-delivery` · in `--full` |
| `idea-critic` | attack a plan or a "we should" before it reaches you | `--with-critic` · in `--full` |
| `communication-structure` | write a short, direct PR body, status update, or report | `--with-comms` · in `--full` |
| `agentic-ceo` | route a multi-skill session and size the effort to the project | `--with-ceo` |
| `product-discovery` | decide if it's worth building, what comes first, and whether it's working | `--with-discovery` |
| `growth-analytics` | pick a North Star metric, read the funnel, design events | `--with-growth` |
| `positioning` | shape the value proposition and message, as a hypothesis to test | `--with-positioning` |
| `business-ops` | do pricing arithmetic, or route a legal/tax question to a professional | `--with-business` |
| `product-output-safety` | govern harm from your product's own AI outputs | `--with-output-safety` |
| `contribution` | turn a reusable lesson into a privacy-safe upstream PR | `--with-contribution` |

The advisory skills work only on your own inputs and evidence. They never invent
market, financial, or security facts. If you already run another delivery
framework, keep it and install review only; don't run two delivery systems on
the same project.

---

## Token and context efficiency

Every token an agent reads costs money and crowds its working memory. Perun
keeps that load small:

- **Progressive disclosure.** `SKILL.md` is a map; depth sits in routed
  reference files loaded only on a stated trigger. Large references index their
  own sub-files, so a web review reads the accessibility basics and skips the
  data-pipeline depth.
- **Frozen budgets.** CI caps every skill map at 24,000 bytes, freezes each
  reference's byte size, and pins each review type's must-read token total.
  Raising a size budget needs an explicit `size-budget-raise:` marker.
- **Lookup tables, not browsing.** Every skill ships a generated `INDEX.md`
  (file → when to read it → estimated tokens → headings), so an agent opens one
  file instead of scanning references. CI fails when an index goes stale.
- **Short handbacks.** The handback cap and one-line reporting default stop
  per-lane narration multiplying across a fleet.
- **Measure and cap it.** `agentic-ceo/scripts/token_report.py --session <transcript>`
  reports main-agent vs subagent tokens and each subagent's startup and output
  cost. `--budget` adds per-lane caps (tool calls, tokens, startup overhead)
  and an orchestration-share ceiling (default 20%); each breach names the fix.
- **Host settings.** The verified Claude Code settings that cut per-turn tokens
  are documented in
  [`host-enforcement.md`](.claude/skills/agentic-delivery/references/host-enforcement.md).
- **Optional companions.** For shorter assistant chat, add
  [caveman](https://github.com/JuliusBrussee/caveman); for a minimal-code bias on
  plumbing, bug-fix, and QA work, add
  [ponytail](https://github.com/DietrichGebert/ponytail) (pin a reviewed release;
  exempt design-port work, where exact fidelity and required tests beat minimal
  code). Neither is bundled. Code, PR bodies, and docs stay in normal English.

---

## What's new

The latest five releases; full detail in [`CHANGELOG.md`](CHANGELOG.md).

- **1.451.0** — Diff-scoped threat modeling for changes adding a trust boundary; value-first README.
- **1.450.0** — `lesson_replay.py`: an advisory self-improvement signal that reports whether each new lesson's eval or selftest is actually tied to the change.
- **1.449.0** — Token budget gate: `token_report.py --budget` caps each lane and the orchestrator's share.
- **1.448.0** — Keystone fix-forward for a red base under an owner grant; verified lane hand-back.
- **1.447.0** — Design parity: structure checks, same-crop guard, owner-approved ignores, baseline mode.
---

## FAQ

**What does it cost?** Perun is free (MIT). You pay only for your agent's model
usage. The fixed method load is about 28,000 estimated tokens per review
(36,100 for a FULL repo review), plus the references that apply and your code.
Start with `DIFF` or `FILE` scope to keep a first run small.

**Is it safe to install?** `install.sh` copies skill folders and writes a
marked block in `AGENTS.md`: no network, no sudo. An existing skill is backed up under
`.<host>/skill-backups/`, never overwritten. `SHA256SUMS` covers the skill
trees. It is a content hash, not a signature. See [`SECURITY.md`](SECURITY.md).

**Does my code leave my machine?** Perun itself sends nothing; it's text files
your agent reads. Your code goes wherever your agent already sends it. The
review may have the agent fetch public standards pages (such as OWASP) to
confirm current versions. The skill bans secrets, personal data, and private identifiers from anything it writes to
your repo, and its privacy gate reports a hit's location, never the secret.

**Which agents are supported?** Any that can read files: Claude Code, Cursor,
Codex, Copilot, Gemini, Aider, Windsurf, OpenCode, Hermes, Kiro, or a plain chat
model given the pasted `SKILL.md`.

**How is this different from a good prompt?** A prompt gets you one pass that
the model shapes itself. Perun fixes the method: a pinned commit, the same
domains every time, a required evidence line per finding, an adversarial pass,
and a definition of done. The routed references hold detection depth no single
prompt carries, and CI-tested scripts check what prose alone can't.

**When should I not use it?** For a throwaway script where a quick read is
enough, or alongside another delivery framework (install review only).

**Where is it going?** [`docs/roadmap.md`](docs/roadmap.md). How Perun reviews
its own changes: [`docs/self-improvement.md`](docs/self-improvement.md).

---

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md); [`CLAUDE.md`](CLAUDE.md) holds the
rules. In short: each skill has one home under `.claude/skills/`, nothing is
duplicated, every reference is routed from its `SKILL.md`, and every cited
standard is verified and dated in
[`docs/standards-index.md`](docs/standards-index.md). Security reports:
[`SECURITY.md`](SECURITY.md). Conduct:
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## License and attribution

[MIT](LICENSE). Inspired by open coding-agent setups (including
[`nickmaglowsch/claude-setup`](https://github.com/nickmaglowsch/claude-setup))
and grounded in the public standards listed in
[`docs/standards-index.md`](docs/standards-index.md). Named for the Slavic
thunder god of order.
