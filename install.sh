#!/usr/bin/env bash
# install.sh — install the deep-code-review skill into a project, for ANY agent.
#
# Usage:
#   ./install.sh [--claude-only] [--with-cursor] [TARGET_DIR]
#
# Installs the review method so any coding agent can run it:
#   - copies the skill to <TARGET_DIR>/.claude/skills/deep-code-review/ (Claude
#     Code loads it natively; Cursor also discovers .claude/skills/ for
#     compatibility; those files are the canonical copy); and
#   - writes/updates a root AGENTS.md pointer so cross-agent tools (Codex,
#     Cursor, Copilot, Gemini, Aider, …) discover the method. Additive: never
#     overwrites an existing AGENTS.md body; refreshes the marked block on
#     re-install so the version stamp stays current.
#
#   --claude-only   Install just the Claude Code skill; skip the AGENTS.md pointer.
#   --with-cursor   Also copy the skill to <TARGET_DIR>/.cursor/skills/deep-code-review/
#                   (Cursor-native path; optional — Cursor already loads .claude/skills/).
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
  ./install.sh [--claude-only] [--with-cursor] [TARGET_DIR]

By default installs the skill AND writes a cross-agent AGENTS.md pointer, so any
coding agent (Claude Code, Codex, Cursor, Copilot, Gemini, Aider) can run it. The
AGENTS.md write is additive and never overwrites unrelated content; on re-install
it refreshes the marked deep-code-review block (version stamp).

  --claude-only   Install just the Claude Code skill; skip the AGENTS.md pointer.
  --with-cursor   Also install to .cursor/skills/deep-code-review/ (Cursor-native).
  -h, --help      Show this help.

TARGET_DIR defaults to the current working directory.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="deep-code-review"
SRC="${SCRIPT_DIR}/.claude/skills/${SKILL_NAME}"

WRITE_AGENTS=1
WITH_CURSOR=0
POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    --claude-only) WRITE_AGENTS=0 ;;
    --with-cursor) WITH_CURSOR=1 ;;
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

VERSION="unknown"
if [[ -f "${SRC}/VERSION" ]]; then
  VERSION="$(tr -d '[:space:]' < "${SRC}/VERSION")"
fi
INSTALL_SHA="unknown"
if git -C "${SCRIPT_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  INSTALL_SHA="$(git -C "${SCRIPT_DIR}" rev-parse --short HEAD)"
fi

install_skill_copy() {
  local dest="$1"
  local backup_root="$2"
  mkdir -p "$(dirname "${dest}")"
  if [[ -e "${dest}" ]]; then
    mkdir -p "${backup_root}"
    local backup="${backup_root}/${SKILL_NAME}-$(date +%Y%m%d-%H%M%S)"
    echo "note: existing skill found -> backing up to ${backup}"
    mv "${dest}" "${backup}"
  fi
  cp -R "${SRC}" "${dest}"
  echo "installed: ${SKILL_NAME} ${VERSION} (@ ${INSTALL_SHA}) -> ${dest}"
}

mkdir -p "${TARGET_DIR}/.claude/skills"
# Back up an existing install OUTSIDE skills/, so the backup is never loaded as a
# duplicate skill (Claude Code loads every SKILL.md under .claude/skills/).
install_skill_copy "${DEST}" "${TARGET_DIR}/.claude/skill-backups"

if [[ "${WITH_CURSOR}" -eq 1 ]]; then
  install_skill_copy \
    "${TARGET_DIR}/.cursor/skills/${SKILL_NAME}" \
    "${TARGET_DIR}/.cursor/skill-backups"
fi

# Cross-agent pointer (default). Additive + idempotent, mirroring the skill's own
# imprint contract: create-if-missing, refresh marked block, never wipe the file.
if [[ "${WRITE_AGENTS}" -eq 1 ]]; then
  AGENTS="${TARGET_DIR}/AGENTS.md"
  MARKER_BEGIN="deep-code-review:begin"
  MARKER_END="deep-code-review:end"
  BLOCK="$(cat <<EOF
<!-- ${MARKER_BEGIN} -->
## Code review — deep-code-review

Installed: **${VERSION}** (@ \`${INSTALL_SHA}\`).

This repository ships a universal, deep code-review method at
\`.claude/skills/deep-code-review/SKILL.md\` (depth in its \`references/\`). Any
coding agent can run it: read \`SKILL.md\`, state the scope
(\`FULL\` | \`DIFF <base-ref>\` | \`FILE <paths>\`), then work its phases in order,
loading \`references/*.md\` on demand as \`SKILL.md\` routes to them. It yields a
severity-ranked findings report plus a plain-language report under \`code-review/\`.
Re-run the upstream \`install.sh\` to refresh this stamp.
<!-- ${MARKER_END} -->
EOF
)"
  if [[ -f "${AGENTS}" ]] && grep -q "${MARKER_BEGIN}" "${AGENTS}"; then
    # Refresh the marked block so the version/SHA stamp stays current.
    block_file="$(mktemp)"
    out_file="$(mktemp)"
    printf '%s\n' "${BLOCK}" > "${block_file}"
    awk -v begin="<!-- ${MARKER_BEGIN} -->" -v end="<!-- ${MARKER_END} -->" \
      -v bf="${block_file}" '
      BEGIN {
        while ((getline line < bf) > 0) { newblock = newblock line ORS }
        close(bf)
      }
      $0 == begin { printf "%s", newblock; skip=1; next }
      skip && $0 == end { skip=0; next }
      !skip { print }
    ' "${AGENTS}" > "${out_file}"
    mv "${out_file}" "${AGENTS}"
    rm -f "${block_file}"
    echo "agents: refreshed deep-code-review pointer (v${VERSION} @ ${INSTALL_SHA}) -> ${AGENTS}"
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
if [[ "${WITH_CURSOR}" -eq 1 ]]; then
  echo "  Cursor: also at .cursor/skills/${SKILL_NAME}/ (invoke /deep-code-review)"
fi
