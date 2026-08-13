#!/usr/bin/env bash
# install.sh — install the deep-code-review skill into a target project.
#
# Usage:
#   ./install.sh [TARGET_DIR]
#
# Copies the deep-code-review Claude Code skill into
#   <TARGET_DIR>/.claude/skills/deep-code-review/
# so you can invoke `/deep-code-review <scope>` in that project.
#
#   - TARGET_DIR defaults to the current working directory.
#   - Re-running updates an existing install in place; any existing skill is
#     moved to a timestamped backup first.
#   - No network, no sudo, fully local and reversible.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="deep-code-review"
SRC="${SCRIPT_DIR}/.claude/skills/${SKILL_NAME}"

TARGET_DIR="${1:-$(pwd)}"
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
echo "invoke it in ${TARGET_DIR} with:  /deep-code-review <scope>"
echo "  scopes: FULL (whole repo) | DIFF <base-ref> (a PR/branch) | FILE <paths>"
