#!/usr/bin/env bash
# install.sh — install the deep-code-review skill into a project, for ANY agent.
#
# Usage:
#   ./install.sh [--claude-only] [TARGET_DIR]
#
# Installs the review method so any coding agent can run it:
#   - copies the skill to <TARGET_DIR>/.claude/skills/deep-code-review/ (Claude
#     Code loads it natively; those files are also the canonical copy other agents
#     read); and
#   - writes/updates a root AGENTS.md pointer so cross-agent tools (Codex, Cursor,
#     Copilot, Gemini, Aider, …) discover the method. Additive + idempotent: never
#     overwrites an existing AGENTS.md; appends a marked block only if absent.
#
#   --claude-only   Install just the Claude Code skill; skip the AGENTS.md pointer.
#   -h, --help      Show this help.
#
#   - TARGET_DIR defaults to the current working directory.
#   - Re-running updates in place; any existing skill is moved to a timestamped
#     backup under <TARGET_DIR>/.claude/skill-backups/ — never inside skills/, so a
#     backup is never loaded as a duplicate skill.
#   - No network, no sudo, fully local and reversible.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
install.sh — install the deep-code-review skill into a project, for ANY agent.

Usage:
  ./install.sh [--claude-only] [TARGET_DIR]

By default installs the skill AND writes a cross-agent AGENTS.md pointer, so any
coding agent (Claude Code, Codex, Cursor, Copilot, Gemini, Aider) can run it. The
AGENTS.md write is additive + idempotent and never overwrites an existing file.

  --claude-only   Install just the Claude Code skill; skip the AGENTS.md pointer.
  -h, --help      Show this help.

TARGET_DIR defaults to the current working directory.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="deep-code-review"
SRC="${SCRIPT_DIR}/.claude/skills/${SKILL_NAME}"

WRITE_AGENTS=1
POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    --claude-only) WRITE_AGENTS=0 ;;
    -p|--portable) echo "note: --portable is now the default; ignoring (use --claude-only to opt out)." >&2 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "error: unknown option: ${arg}" >&2; usage; exit 2 ;;
    *) POSITIONAL+=("${arg}") ;;
  esac
done

TARGET_DIR="${POSITIONAL[0]:-$(pwd)}"
DEST="${TARGET_DIR}/.claude/skills/${SKILL_NAME}"

if [[ ! -f "${SRC}/SKILL.md" ]]; then
  echo "error: cannot find ${SRC}/SKILL.md" >&2
  echo "Run this script from inside a cloned deep-code-review repository." >&2
  exit 1
fi

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "error: target directory does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

# Refuse to install into itself (would create a recursive copy).
if [[ "$(cd "${TARGET_DIR}" && pwd)" == "${SCRIPT_DIR}" ]]; then
  echo "error: target is the repository itself; choose another project directory." >&2
  exit 1
fi

mkdir -p "${TARGET_DIR}/.claude/skills"

# Back up an existing install OUTSIDE skills/, so the backup is never loaded as a
# duplicate skill (Claude Code loads every SKILL.md under .claude/skills/).
if [[ -e "${DEST}" ]]; then
  BACKUP_DIR="${TARGET_DIR}/.claude/skill-backups"
  mkdir -p "${BACKUP_DIR}"
  BACKUP="${BACKUP_DIR}/${SKILL_NAME}-$(date +%Y%m%d-%H%M%S)"
  echo "note: existing skill found -> backing up to ${BACKUP}"
  mv "${DEST}" "${BACKUP}"
fi

cp -R "${SRC}" "${DEST}"
echo "installed: ${SKILL_NAME} -> ${DEST}"

# Cross-agent pointer (default). Additive + idempotent, mirroring the skill's own
# imprint contract: create-if-missing, append-only, never overwrite, print change.
if [[ "${WRITE_AGENTS}" -eq 1 ]]; then
  AGENTS="${TARGET_DIR}/AGENTS.md"
  MARKER="deep-code-review:begin"
  read -r -d '' BLOCK <<'EOF' || true
<!-- deep-code-review:begin -->
## Code review — deep-code-review

This repository ships a universal, deep code-review method at
`.claude/skills/deep-code-review/SKILL.md` (depth in its `references/`). Any
coding agent can run it: read `SKILL.md`, state the scope
(`FULL` | `DIFF <base-ref>` | `FILE <paths>`), then work its phases in order,
loading `references/*.md` on demand as `SKILL.md` routes to them. It yields a
severity-ranked findings report plus a plain-language report under `code-review/`.
<!-- deep-code-review:end -->
EOF
  if [[ -f "${AGENTS}" ]] && grep -q "${MARKER}" "${AGENTS}"; then
    echo "agents: AGENTS.md already has the deep-code-review pointer -> left as-is"
  elif [[ -f "${AGENTS}" ]]; then
    printf '\n%s\n' "${BLOCK}" >> "${AGENTS}"
    echo "agents: appended deep-code-review pointer -> ${AGENTS}"
  else
    printf '# AGENTS.md\n\n%s\n' "${BLOCK}" > "${AGENTS}"
    echo "agents: created ${AGENTS} with the deep-code-review pointer"
  fi
  echo "  read natively by Claude Code, Codex, Cursor, Copilot, Gemini, Aider."
fi

echo "run it:  read .claude/skills/${SKILL_NAME}/SKILL.md, then name a scope"
echo "  scopes: FULL (whole repo) | DIFF <base-ref> (a PR/branch) | FILE <paths>"
echo "  (Claude Code shortcut: /deep-code-review <scope>)"
