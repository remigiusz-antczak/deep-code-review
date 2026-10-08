# Host safety: what each agent host can and cannot contain

BLUF: only some hosts have an OS-level sandbox, and none of them is on by default except where noted. Perun installs skills into every host below but sets a safety config only where it already writes a project settings file (Claude Code, via the operating layer). For every other host `install.sh` prints a one-line warning with the doc link, and `operating_selfcheck.py` reports per-host status. Hosts with no OS sandbox should run agents in a dev container or VM.

Facts verified 2026-10-07 from the vendor docs listed in [standards-index.md](standards-index.md). "Not documented" means the page fetched did not say; re-check before relying on it. Deny rules and allowlists are matched on command text, so they reduce accidents but do not stop a determined or confused agent; an OS sandbox or container is the real boundary.

| Host (install dir) | OS sandbox? Default | Switch (file or key) | Perun sets | You must set | Residual risk |
|---|---|---|---|---|---|
| Claude Code (`.claude`) | Yes (macOS, Linux, WSL2). Off | `sandbox.enabled: true`, `allowUnsandboxedCommands: false` in settings, or `/sandbox` | Operating layer (`--apply-operating-layer`) writes these into `.claude/settings.local.json` where it carries the sandbox default | Enable it if you skip the operating layer; native Windows has no sandbox | Shell only: file tools, MCP servers and hooks run outside it; deny rules are text-only |
| Cursor (`.cursor`) | Yes (Seatbelt; Landlock + seccomp). Auto-review default runs non-allowlisted commands sandboxed "when possible" | `.cursor/sandbox.json` (`readBoundary`, `additionalReadPaths`, network); `.cursor/permissions.json` (`allow_instructions`, `block_instructions`) | Nothing | Stay out of Run Everything (no sandbox, no review) | Allowlisted calls run immediately and unsandboxed; "when possible" is not a guarantee |
| Codex (`.codex`) | Yes (Seatbelt; `bwrap` + seccomp). On: `workspace-write` in version-controlled folders, `read-only` elsewhere; network off | `~/.codex/config.toml`: `sandbox_mode`, `approval_policy`, `[sandbox_workspace_write] network_access` | Nothing | Never use `danger-full-access`, `--yolo` or `--dangerously-bypass-approvals-and-sandbox` | Writes inside the workspace are allowed; `.git`, `.agents/`, `.codex/` stay read-only |
| Gemini CLI (`.gemini`) | Yes (Seatbelt or Docker/Podman). Off | `tools.sandbox: true` in `.gemini/settings.json`, `-s`, or `GEMINI_SANDBOX`; `SEATBELT_PROFILE` | Nothing (the project file is not one Perun writes) | Enable the sandbox; never `--yolo` or `--approval-mode yolo`; consider `permissive-closed` or stricter | Default Seatbelt profile `permissive-open` allows network |
| GitHub Copilot (`.github`) | VS Code agent: yes, off. Copilot CLI: none documented. Cloud agent: network firewall, not a host sandbox | VS Code: `chat.agent.sandbox.enabled`; approvals: `chat.tools.terminal.autoApprove`, `chat.tools.global.autoApprove`; CLI: `--deny-tool`, `--allow-tool` | Nothing | Enable the VS Code sandbox (Linux needs `bubblewrap`, `socat`); never `chat.tools.global.autoApprove`; CLI: avoid `--allow-all`/`--yolo` | Sandbox defaults still allow network and unsandboxed retry; CLI has no OS boundary |
| OpenCode (`.opencode`) | No | `permission` in `opencode.json` (`allow`/`ask`/`deny`, bash patterns) | Nothing | Deny destructive patterns (for example `"rm *": "deny"`); never `"permission": "allow"`; use a container | Most tools default to `allow`; patterns are text-only |
| Windsurf (`.windsurf`) | Not documented | Terminal auto-execution level plus allow and deny lists (UI); team admins can cap the level | Nothing | Avoid Turbo; keep a deny list; use a container | Turbo runs everything outside the deny list |
| Hermes Agent (`.hermes`) | Only via a container backend. `local` has none | `terminal.backend` and `approvals.mode` in `~/.hermes/config.yaml` | Nothing | Set a container backend; keep `approvals.mode` `smart` or `manual`; never `--yolo`, `/yolo`, `HERMES_YOLO_MODE=1` | Container backends skip approvals: the container is then the only boundary |
| Kiro (`.kiro`) | Not documented | `~/.kiro/settings/permissions.yaml` (capabilities `shell`, `fs_write`; deny beats ask beats allow) | Nothing | Deny risky `shell` and `fs_write` patterns; use a container | Permissions are app-level; untrusted-workspace prompts are the only extra guard |
| Shared (`.agents`) | Depends on the agent that reads it | See that agent's row | Nothing | Follow the row of every agent you point at it | Codex keeps `.agents/` read-only; others may not |

Not an install target but common: Aider has no sandbox documented; avoid `--yes-always` and run it in a container.

## Universal rule

Hosts without an OS sandbox (OpenCode, Windsurf, Kiro, Hermes `local`, Copilot CLI, Aider) should run agents inside a [dev container](https://containers.dev/) or VM, so the container is the filesystem boundary. See [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers): with an isolated container volume the workspace is not bound to your local filesystem. Do not mount your home directory or credentials into it.

## Autonomy-ready defaults

The operating layer turns the Claude Code sandbox on with defaults chosen so agents can run common dev commands with no prompts and no manual permission edits after install. `install.sh` merges them into `.claude/settings.local.json`: your existing values win and lists are unioned. Source: [Configure the sandboxed Bash tool](https://code.claude.com/docs/en/sandboxing), fetched 2026-10-08. Check a machine with `python3 .claude/skills/agentic-delivery/scripts/sandbox_probe.py` (also part of `perun_doctor.py`): it runs harmless checks and prints the exact fix for each failure.

| Key | Value | Why | Tradeoff |
| --- | --- | --- | --- |
| `sandbox.enabled` | `true` | OS-enforced boundary around shell commands, so a stray `rm -rf` cannot reach your files | Shell only: file tools, MCP servers and hooks run outside it |
| `sandbox.autoAllowBashIfSandboxed` | `true` (the documented default, set explicitly) | Sandboxed commands run without a prompt; this is what makes autonomous runs possible | The sandbox, not you, approves each command; `rm`/`rmdir` on critical paths still prompt |
| `sandbox.allowUnsandboxedCommands` | `false` | No unsandboxed retry, so a blocked command cannot escape the sandbox | A command the sandbox breaks must be excluded or run by you with the `!` prefix |
| `sandbox.excludedCommands` | `["gh *"]` | `gh` (a Go CLI) may fail TLS verification under Seatbelt; the documented fix is to exclude it | `gh` runs outside the sandbox with your GitHub credentials and no filesystem or network limits |
| `permissions.allow` | read-only `gh` subcommands: `gh pr view`/`list`/`diff`/`checks`, `gh issue view`/`list`, `gh run view`/`list`, `gh repo view` | Excluded commands go through the regular permission flow; this removes the prompt for the common read calls | Every other `gh` call (create, merge, `gh api`, aliases, extensions) still prompts. A blanket `Bash(gh *)` is not used: `gh alias set --shell` and `gh extension install` let a later `gh <name>` run any program outside the sandbox with no prompt |
| `permissions.deny` | `rm -rf`/`-fr`/`-r`/`-R`, `sudo`, `gh alias`, `gh extension`, `gh repo delete`, `gh release delete` | Stops these calls outright instead of prompting | Rules match command text, so other spellings or a script that runs them are not caught; the narrow `gh` allow list above is the main control |
| `sandbox.network.allowedDomains` | `github.com`, `*.github.com`, `*.githubusercontent.com`, `registry.npmjs.org`, `*.npmjs.org`, `pypi.org`, `files.pythonhosted.org` | The list starts empty; these pre-allow git, npm and pip hosts so fetches do not prompt | Broad domains such as `github.com` can be a data-exfiltration path |
| `sandbox.network.allowLocalBinding` | `true` | Dev servers and test harnesses can listen on localhost (macOS) | Sandboxed commands can reach every service listening on localhost |
| `sandbox.filesystem.allowWrite` | `["~/.cache", "~/.npm"]` | Package managers write their caches outside the project | Sandboxed commands can write (and poison) those caches |

Not set, because each removes isolation for a whole tool: `docker` is incompatible with the sandbox (exclude it yourself, for example `/sandbox exclude "docker compose *"`); `open`/`osascript` fail with `-600` (exclude `open *` or set `allowAppleEvents` in user settings). For jest, pass `--no-watchman`. Protected paths such as `.claude/skills` stay write-denied with no exemption, so a `git checkout` or `git merge` that touches them fails with `unable to unlink old`; run that command yourself.

## Common sandbox errors

With the Claude Code sandbox on (the default Perun sets), two failures are common. The [autonomy-ready defaults](#autonomy-ready-defaults) already apply both fixes; this table is for setups that skipped or overrode them.

| Exact error | Cause | User-run fix | Tradeoff |
| --- | --- | --- | --- |
| `gh` fails with `x509: OSStatus -26276` | The sandbox blocks the macOS keychain/trust service `gh` uses to verify TLS certificates | `/sandbox exclude "gh *"` | Every `gh` call runs outside the sandbox, so a confused agent's `gh` command has your GitHub credentials and no filesystem or network limits. Keep the pattern narrow (`gh *`, not `*`) |
| A dev server fails to bind with `EPERM` / "Operation not permitted" | Local port binding is off in the sandbox | `sandbox.network.allowLocalBinding: true` in settings (applies without restart) | Sandboxed commands can open listening ports on localhost, reachable by other local processes |

`operating_selfcheck.py` prints a `WARN` when the sandbox is on and `gh` is not in `sandbox.excludedCommands`.

## Where this is enforced

- `install.sh` reads [`host-safety.tsv`](../.claude/skills/agentic-delivery/templates/host-safety.tsv) and prints one `safety:` line per installed host.
- `python3 .claude/skills/agentic-delivery/scripts/operating_selfcheck.py` (or `host_safety.py` alone) prints `host-safety-<host>: ON | OFF | COULD_NOT_CHECK | NO_OS_SANDBOX` for each installed host. `ON`/`OFF` appear only where a project file proves it (Claude Code settings, `.gemini/settings.json`); user-level switches report `COULD_NOT_CHECK`.

Non-Claude models: for hosts running a non-Claude model or a small context window, use [compact mode](../.claude/skills/deep-code-review/references/compact-mode.md) instead of the full SKILL.md. Measured on 30 held-out bugs, 1 replicate, one verifier ([data](bench/xmodel2-summary.md)): the full SKILL.md never beat a plain prompt (gpt-oss recall 0.167 to 0.067); compact beat plain on Qwen3-Coder-Next by +0.167 (95% CI +0.033 to +0.300), while gpt-oss (0.233 vs 0.167) and DeepSeek (0.200 vs 0.233) were within noise. Verified precision fell for Qwen (0.75 to 0.43) and gpt-oss (0.74 to 0.57).
