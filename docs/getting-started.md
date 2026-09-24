# Getting started with Perun

**You can try the review with no install by pasting one file into an AI chat.
To make every agent in a project use it, run `install.sh` from a pinned
release.** This page covers both, plus updating and removal. What Perun is and
which skills exist: [the README](../README.md).

## 1. Try it without installing

This works in any AI chat, with or without a coding agent.

1. Open [`SKILL.md`](../.claude/skills/deep-code-review/SKILL.md) and copy all
   of it.
2. Start a new chat. Paste the skill, then paste the file you want reviewed.
3. Ask: `Review this with scope FILE.`

A chat model sees only what you paste. It gets the method, severity scale, and
domain map, but not the detailed reference files, and it can't run your tests.
Treat this as a preview. For a full review, install Perun into a project where
an agent can read the files and run the build.

## 2. Install into a project

You need `git`, a terminal, and a coding agent that can open your project
(Claude Code, Cursor, Codex, Copilot, Gemini, Aider, Windsurf, OpenCode, Hermes,
Kiro, or similar).

```bash
git clone --branch vX.Y.Z --depth 1 https://github.com/remigiusz-antczak/deep-code-review.git
cd deep-code-review && shasum -a 256 -c SHA256SUMS   # Linux: sha256sum -c SHA256SUMS
./install.sh --recommend /path/to/your/project       # optional: see a suggested pack, writes nothing
./install.sh /path/to/your/project                   # review only (the default)
```

Replace `vX.Y.Z` with the latest tag on the repository's Releases page. Every
line of the checksum output should end in `OK`.

The default install copies `deep-code-review` into `.claude/skills/`,
`.cursor/skills/`, and `.agents/skills/` of your project and creates or updates
a marked block in `AGENTS.md` that records the installed version and commit. It
makes no network calls and needs no `sudo`.

### Choose where it lands

| Flag | Effect |
|---|---|
| *(none)* | `.claude/`, `.cursor/`, `.agents/` skill roots + `AGENTS.md` |
| `--with-codex` | also `.codex/skills/` |
| `--with-extra-hosts` | also the Gemini, OpenCode, Copilot, Windsurf, Hermes, and Kiro roots |
| `--minimal` | only `.claude/skills/` + `AGENTS.md` |
| `--claude-only` | only `.claude/skills/`, no `AGENTS.md` |

Add overlay skills with the flags in the README's
[skill catalog](../README.md#skill-catalog); `--full` adds delivery, critic, and
comms in one go. `./install.sh --help` is the authoritative list.

## 3. Run your first review

Open the project in your agent and ask in plain words, or use the slash command
where your agent supports one:

```
run a deep code review DIFF origin/main    # just the changes on this branch
/deep-code-review FILE src/auth.ts         # named files
/deep-code-review FULL                     # the whole repository
```

Start with `DIFF` or `FILE`: they read less and cost less than `FULL`. The
agent first prints a short block stating the scope, the exact commit it pinned,
and the project type, then works through the phases. You get a short summary
in chat; the full findings table goes outside the repo unless you ask for it in
a `code-review/` folder. A worked example:
[`example-review-report.md`](example-review-report.md).

## 4. Update or remove

**Update:** pull or check out a newer release tag in your clone, verify the
checksums, and run `install.sh` again with the same flags. It copies files; it
never symlinks, so nothing changes until you re-run it.

To compare an installed copy's version with upstream `main`, run
`scripts/skill-drift-check.sh` from the clone. It reads
`~/.claude/skills/deep-code-review/VERSION` by default; for a project install,
set `DCR_INSTALLED_VERSION_FILE=/path/to/your/project/.claude/skills/deep-code-review/VERSION`.
It needs an authenticated `gh` CLI, exits `1` only when both versions were read
and differ, and exits `0` when they match or it can't check. `main` can be ahead
of the latest release tag, so a mismatch right after a pinned install is
expected.

**Remove:** delete the skill folders it created under `.claude/skills/`,
`.cursor/skills/`, `.agents/skills/` (and any extra host roots), and delete the
`<!-- deep-code-review:begin -->` … `<!-- deep-code-review:end -->` block from
`AGENTS.md` (plus the `dcr-overlays` block if you installed overlays). If the
installer replaced an older copy, that copy is under `.<host>/skill-backups/`.

## Next

- Running several agents in parallel: [`for-fleets.md`](for-fleets.md).
- Install safety and verification: [`SECURITY.md`](../SECURITY.md).
