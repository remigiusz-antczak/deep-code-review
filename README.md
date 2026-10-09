# Perun

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Perun replaces a plain "review this" request to an AI coding assistant with
written instructions it follows the same careful way every time, showing the
evidence for each problem it reports.**

Its main part is a **skill**: a text file of instructions the AI assistant reads
before it starts work.

**Not a developer?** Read [Perun for leaders](docs/for-leaders.md): what it gives
your team, a pilot plan, limits and an FAQ.

## Why it matters

The numbers below come from one test of held-out real bug fixes from
open-source projects ([full results](docs/bench/bench90-results.md)). The
assistant (Claude Code, run by [`scripts/bench_corpus.py`](scripts/bench_corpus.py))
saw only the code change, not the fix, and ran once per case. The cases' answers
are read only by the test runner, so Perun can't be tuned to them. The
[public manifest](scripts/eval-fixtures/bench/manifest.json) lists 27 other
cases to show how cases are built; it is not the set behind these numbers. A bug
counts as "caught" if the review named it. This is a clean 89-case run with isolated run directories; it replaces earlier 30-case and 64-case numbers.

- **Reviewing with repo access is the big win, and it is now the default.** An
  assistant that can read the surrounding code caught
  [64.4% of the bugs against 36.7% for a diff-only prompt](docs/bench/bench90-results.md)
  (+27.8 points, margin of error +18.9 to +37.8) with about 20 points fewer false
  alarms, at $0.073 against $0.082 per review. Perun's `/review` command and the
  opt-in PR workflow now always run in a checkout with read and search tools.
  Extra instructions on top (the long skill text, or a caller-tracing prompt) added cost or lost precision without a measured gain.
- **On this prompt-only benchmark, Perun's review is not measurably better than a plain prompt, and it costs about 2 times as much.**
  Bugs caught on 89 cases: [plain 36.0%, Perun one pass 32.6%](docs/bench/bench90-results.md)
  (-3.4 points, margin of error -10.1 to +3.4); two merged passes 39.3% (+3.4 points, -2.2 to +9.0).
- **False alarms are not measurably different either.** Share of flagged issues a verifier
  model judged real: plain 61.8%, one pass 65.3% (+3.5 points, -3.8 to +10.5). No difference clears zero.
  Perun still misses most bugs, so keep people reviewing too.
- **Shorter instructions to read.** AI tools charge by the *token* (a piece of a word).
  The instructions the assistant must read before each review shrank by
  [19%](CHANGELOG.md) (release 1.501.0, counted as characters divided by 4).
- **Safer AI agents.** An *agent* is an AI assistant that can run commands on
  your computer. The installer tells you how to switch on each agent's
  *sandbox* (a fence around what its commands can touch). No number is claimed:
  the effect has not been measured ([host safety](docs/host-safety.md)).

**Cost.** A review with Perun costs more than a plain one:
[$0.080 per code change for one pass against $0.043](docs/bench/bench90-results.md)
(about 1.9 times; $0.163 for two passes), as reported by the test runner.

Time saved and money saved have not been measured, so none are claimed. To
estimate them for your team, use the worked formula and the three-step pilot in
[Perun for leaders](docs/for-leaders.md).

## Quick start

You need `git`, a terminal, and an AI coding agent such as Claude Code or
Cursor (the installer lists the others it supports). No terminal? Paste the
skill into any AI chat instead: [getting started](docs/getting-started.md).

1. **Download Perun:**

   ```bash
   git clone --depth 1 https://github.com/remigiusz-antczak/deep-code-review.git
   ```

2. **Install it into your project.** It copies text files only, with no
   admin rights, and adds files only inside your project's `.claude`, `.cursor`
   and `.agents` folders ([`install.sh`](install.sh)):

   ```bash
   deep-code-review/install.sh /path/to/your/project
   ```

3. **Ask your agent to review a real file you care about.** Type
   `run a deep code review FILE src/checkout.py`. `FILE` is a literal keyword:
   type it as written, then put your own file's path after it.

4. **Check the install.** Run the command the installer printed last (shown
   below); it confirms Perun is installed and working:

   ```bash
   python3 deep-code-review/scripts/perun_doctor.py /path/to/your/project
   ```

What step 2 prints (shortened; your version and paths will differ). The last
line names the check in step 4:

```
installed: deep-code-review 1.535.0 (@ 84acfb19) -> your-project/.claude/skills/deep-code-review
safety: Claude Code: OS sandbox is off by default; set sandbox.enabled=true (or run /sandbox) and keep allowUnsandboxedCommands=false. https://code.claude.com/docs/en/sandboxing
Perun installed 1 skill(s) into 3 tool folder(s) of your-project.
Next, run this one command to confirm it works: python3 deep-code-review/scripts/perun_doctor.py your-project
```

The "safety" line is the sandbox setting to switch on for that agent. The "3
tool folders" are where different agents look for skills, so one install works
for several of them.

What step 3 gives you: a list of problems, worst first, on a six-step scale
from Blocker (stops the software working) to Nit (style only). Each problem
names the file and line, the evidence and a fix. A made-up example from the
[example report](docs/example-review-report.md):

```
### F3 - High - CONFIRMED
Inbound webhook accepts unsigned body
- Evidence: routes/hooks.mjs:22 parses JSON; no signature check.
- Fix: verify the signature; bind the account to the verified sender.
```

"CONFIRMED" means the assistant re-checked the problem against the exact code
it reviewed, not just suspected it.

## About the name

Perun is the project's name (after the Slavic thunder god of order). This
repository is called `deep-code-review`, after what it does.

## Who it's for

- **Engineers:** a repeatable review of a file, a branch or a whole project,
  with evidence for every problem.
- **Team leads:** a ranked report you can check, plus a pilot plan
  ([Perun for leaders](docs/for-leaders.md), [team install](docs/team-install.md)).
- **Non-technical teams:** no licence fee ([MIT](LICENSE)), only your AI usage
  cost, and a plain-English summary of risks and decisions
  ([Perun for leaders](docs/for-leaders.md)).

## Safety

Perun is instructions, not a service: your code goes only where your agent
already sends it. Switch on your agent's sandbox and keep human review
([host safety](docs/host-safety.md), [`SECURITY.md`](SECURITY.md)).

## Learn more

- [Perun for leaders](docs/for-leaders.md): a worked story, what each role
  gets, a pilot plan, limits, a glossary and an FAQ.
- [Getting started](docs/getting-started.md): every install option, optional
  skills, updating and removing.
- [Example report](docs/example-review-report.md); the
  [test method](scripts/bench_corpus.py) and
  [cases](scripts/eval-fixtures/bench/) behind the numbers.
- [Technical overview](docs/technical-overview.md),
  [token cost tips](docs/token-cost-tips.md),
  [running many agents](docs/for-fleets.md), [roadmap](docs/roadmap.md).
- Contributing: [`CONTRIBUTING.md`](CONTRIBUTING.md), rules in
  [`CLAUDE.md`](CLAUDE.md), verified standards in
  [`docs/standards-index.md`](docs/standards-index.md),
  [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md),
  [CI status](https://github.com/remigiusz-antczak/deep-code-review/actions/workflows/ci.yml).

[MIT](LICENSE). Credits and sources: [`docs/standards-index.md`](docs/standards-index.md).
