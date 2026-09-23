# Perun

**A code-review and quality bar your AI coding agent follows: every finding
carries `file:line` evidence and a concrete fix, and anything the evidence
can't confirm is marked `unverified` instead of guessed.**

Perun is a set of skills: plain-text instruction files that an AI coding agent
reads when a task matches. The default skill, `deep-code-review`, turns "look
this over" into a fixed, repeatable audit of correctness, security, AI/LLM
safety, data quality, performance and cost, reliability, testing,
infrastructure, docs, and accessibility. It ends in a severity-ranked report.
It works on any language or stack, on any agent that can read files, and as a
one-shot prompt or a human checklist. Ten opt-in skills extend it to gated
delivery, planning, and product work. MIT-licensed, runs fully local.

**Start here:** [New to AI agents](#new-to-ai-agents) ·
[Already using an agent](#already-using-claude-code-cursor-or-codex) ·
[Running agent fleets](#running-agent-fleets) · [FAQ](#faq)

---

## What you get

| Outcome | What it looks like |
|---|---|
| A report you can act on | Findings ranked Blocker → Critical → High → Medium → Low → Nit, each with `file:line` evidence and a fix. See the [fictional example report](docs/example-review-report.md). |
| A summary for non-coders | A traffic-light health scorecard, the top risks in plain terms, and the decisions that need an owner. |
| Broad, fixed coverage | 21 audit domains (lettered A–W), an adversarial red-team pass, and a check for costly work that adds no value (repeated identical API/LLM/DB calls, over-fetching). |
| Lower context cost | The method files every review must read dropped from 65,903 to 35,848 estimated tokens (a FULL repo review: 87,137 to 47,442), about 46% less. A web review's must-read set dropped from 86,820 to at most 23,349. CI blocks either number from growing. |
| Checks that run, not just advice | 23 shipped gate scripts prove they catch a planted violation in CI on every change. `--with-gates` wires the review's own gates into your repo's CI. |
| A bar that stays | An optional final phase writes an `AGENTS.md` and pre-commit/CI gates into your repo, so the next contributor or agent, from any vendor, is held to the same bar. |

Token figures are characters ÷ 4, from [`CHANGELOG.md`](CHANGELOG.md) (1.439.0–1.443.0)
and the CI ceilings in [`scripts/mustload-budgets.tsv`](scripts/mustload-budgets.tsv).

---

## Pick your path

### New to AI agents

An **AI coding agent** is a program (for example Claude Code, Cursor, or Codex)
that uses an AI model to read, edit, and run code in your project when you ask
in plain words. A **skill** is a folder of written instructions the agent loads
when your request matches it. Think of it as handing a new colleague the team's
review checklist.

The quickest way to try Perun, with no install:

1. Open [`.claude/skills/deep-code-review/SKILL.md`](.claude/skills/deep-code-review/SKILL.md) and copy it.
2. Paste it into any AI chat, then paste one file you care about.
3. Ask: `Review this with scope FILE.`

Step-by-step, including installing into a real project:
[`docs/getting-started.md`](docs/getting-started.md).

### Already using Claude Code, Cursor, or Codex

Install into your project with three commands, from a pinned release:

```bash
git clone --branch vX.Y.Z --depth 1 https://github.com/remigiusz-antczak/deep-code-review.git
cd deep-code-review && shasum -a 256 -c SHA256SUMS   # Linux: sha256sum -c SHA256SUMS
./install.sh /path/to/your/project                   # review only (the default)
```

> [!IMPORTANT]
> Replace `vX.Y.Z` with the latest tag on the Releases page and keep the
> checksum step. Don't `curl | bash` an unpinned `HEAD`; the review itself flags
> that as a supply-chain risk.

Then ask your agent `run a deep code review DIFF origin/main`, or use
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
- **Proof of done:** `surface_check.py` checks a "deployed" claim against the
  running build, not a green CI badge.

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
- **Short handbacks.** The handback cap and one-line reporting default stop
  per-lane narration multiplying across a fleet.
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

## FAQ

**What does it cost?** Perun is free (MIT). You pay only for your agent's model
usage. The fixed method load is about 35,800 estimated tokens per review
(47,400 for a FULL repo review), plus the references that apply and your code.
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
