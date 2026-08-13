#!/usr/bin/env bash
# install.sh — install the deep-code-review skill into a target project.
#
# Usage:
#   ./install.sh [--portable] [TARGET_DIR]
#
# Copies the deep-code-review Claude Code skill into
#   <TARGET_DIR>/.claude/skills/deep-code-review/
# so you can invoke `/deep-code-review <scope>` in that project.
#
#   --portable   Also drop a root AGENTS.md pointer so non-Claude agents
#                (Codex, Cursor, Copilot, Gemini, Aider, …) discover the method.
#                Additive and idempotent: never overwrites an existing AGENTS.md;
#                appends a clearly-marked pointer block only if not already there.
#   -h, --help   Show this help.
#
#   - TARGET_DIR defaults to the current working directory.
#   - Re-running updates an existing install in place; any existing skill is
#     moved to a timestamped backup first.
#   - No network, no sudo, fully local and reversible.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
install.sh — install the deep-code-review skill into a target project.

Usage:
  ./install.sh [--portable] [TARGET_DIR]

  --portable   Also drop a root AGENTS.md pointer so non-Claude agents
               (Codex, Cursor, Copilot, Gemini, Aider) discover the method.
               Additive + idempotent: never overwrites an existing AGENTS.md.
  -h, --help   Show this help.

TARGET_DIR defaults to the current working directory.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="deep-code-review"
SRC="${SCRIPT_DIR}/.claude/skills/${SKILL_NAME}"

PORTABLE=0
POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    -p|--portable) PORTABLE=1 ;;
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

if [[ -e "${DEST}" ]]; then
  BACKUP="${DEST}.backup-$(date +%Y%m%d-%H%M%S)"
  echo "note: existing skill found -> backing up to ${BACKUP}"
  mv "${DEST}" "${BACKUP}"
fi

cp -R "${SRC}" "${DEST}"

echo "installed: ${SKILL_NAME} -> ${DEST}"

# --portable: drop a cross-agent AGENTS.md pointer (additive + idempotent),
# so agents that read AGENTS.md natively (Codex, Cursor, Copilot, Gemini, Aider)
# discover the installed method. This mirrors the skill's own imprint contract:
# create-if-missing, append-only, never overwrite, and print what changed.
if [[ "${PORTABLE}" -eq 1 ]]; then
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
    echo "portable: AGENTS.md already has the deep-code-review pointer -> left as-is"
  elif [[ -f "${AGENTS}" ]]; then
    printf '\n%s\n' "${BLOCK}" >> "${AGENTS}"
    echo "portable: appended deep-code-review pointer -> ${AGENTS}"
  else
    printf '# AGENTS.md\n\n%s\n' "${BLOCK}" > "${AGENTS}"
    echo "portable: created ${AGENTS} with the deep-code-review pointer"
  fi
  echo "  non-Claude agents (Codex, Cursor, Copilot, Gemini, Aider) read AGENTS.md natively."
fi

echo "invoke it in ${TARGET_DIR} with:  /deep-code-review <scope>"
echo "  scopes: FULL (whole repo) | DIFF <base-ref> (a PR/branch) | FILE <paths>"
