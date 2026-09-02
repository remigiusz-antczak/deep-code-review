#!/usr/bin/env bash
# install.sh — install the deep-code-review skill into a project, for ANY agent.
#
# Usage:
#   ./install.sh [--minimal] [--with-codex] [TARGET_DIR]
#
# Default (agent-agnostic): copies the skill into every common skill root the
# major hosts discover, and writes/refreshes a root AGENTS.md pointer:
#   - .agents/skills/deep-code-review/   (Agent Skills / open standard)
#   - .cursor/skills/deep-code-review/   (Cursor)
#   - .claude/skills/deep-code-review/   (Claude Code; Cursor/Codex also load)
# Optional:
#   --with-codex   also .codex/skills/deep-code-review/
#   --minimal      only .claude/skills/ + AGENTS.md (legacy lean install)
#   --claude-only  only .claude/skills/ ; skip AGENTS.md (compat alias)
#   --with-cursor  no-op (Cursor path is now part of the default set)
#
# Source of truth in the upstream repo remains a single tree under
# .claude/skills/deep-code-review/ — install copies *from* there; never duplicates
# the skill inside the upstream repository itself.
#
# Backups land under <TARGET>/.{agents,cursor,claude,codex}/skill-backups/ —
# never inside skills/, so backups are never loaded as duplicate skills.
# No network, no sudo, fully local and reversible.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
install.sh — install deep-code-review for any coding agent.

Usage:
  ./install.sh [--minimal] [--with-codex] [--claude-only] [TARGET_DIR]

Default: install into .agents/skills/, .cursor/skills/, and .claude/skills/,
plus an AGENTS.md pointer (version-stamped; refreshed on re-install).

  --minimal       Only .claude/skills/ + AGENTS.md
  --with-codex    Also .codex/skills/
  --claude-only   Only .claude/skills/; skip AGENTS.md
  --with-cursor   Accepted as no-op (Cursor path is default now)
  -h, --help      Show this help

TARGET_DIR defaults to the current working directory.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="deep-code-review"
SRC="${SCRIPT_DIR}/.claude/skills/${SKILL_NAME}"

WRITE_AGENTS=1
MINIMAL=0
WITH_CODEX=0
POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    --claude-only) WRITE_AGENTS=0; MINIMAL=1 ;;
    --minimal) MINIMAL=1 ;;
    --with-codex) WITH_CODEX=1 ;;
    --with-cursor) echo "note: --with-cursor is default now; ignoring." >&2 ;;
    -p|--portable) echo "note: --portable is default; ignoring (use --minimal / --claude-only to narrow)." >&2 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "error: unknown option: ${arg}" >&2; usage; exit 2 ;;
    *) POSITIONAL+=("${arg}") ;;
  esac
done

TARGET_DIR="${POSITIONAL[0]:-$(pwd)}"

if [[ ! -f "${SRC}/SKILL.md" ]]; then
  echo "error: cannot find ${SRC}/SKILL.md" >&2
  echo "Run this script from inside a cloned deep-code-review repository." >&2
  exit 1
fi

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "error: target directory does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

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
    # Portable, collision-free backup name: a seconds-resolution timestamp plus
    # an existence-checked numeric suffix, so rapid repeated installs within the
    # same second never reuse a name. Avoids `date +%N` (unsupported on BSD/macOS
    # date), which is why a plain timestamp alone would collide.
    local backup="${backup_root}/${SKILL_NAME}-$(date +%Y%m%d-%H%M%S)"
    if [[ -e "${backup}" ]]; then
      local n=1
      while [[ -e "${backup}-${n}" ]]; do
        n=$((n + 1))
      done
      backup="${backup}-${n}"
    fi
    echo "note: existing skill found -> backing up to ${backup}"
    mv "${dest}" "${backup}"
  fi
  cp -R "${SRC}" "${dest}"
  # Support docs the skill cites — must resolve after install (not only in upstream repo).
  if [[ -f "${SCRIPT_DIR}/docs/standards-index.md" ]]; then
    cp "${SCRIPT_DIR}/docs/standards-index.md" "${dest}/references/standards-index.md"
  fi
  if [[ -f "${SCRIPT_DIR}/docs/example-review-report.md" ]]; then
    cp "${SCRIPT_DIR}/docs/example-review-report.md" "${dest}/references/example-review-report.md"
  fi
  echo "installed: ${SKILL_NAME} ${VERSION} (@ ${INSTALL_SHA}) -> ${dest}"
}

# Always install the Claude-compatible path (many hosts also discover it).
install_skill_copy \
  "${TARGET_DIR}/.claude/skills/${SKILL_NAME}" \
  "${TARGET_DIR}/.claude/skill-backups"

if [[ "${MINIMAL}" -eq 0 ]]; then
  install_skill_copy \
    "${TARGET_DIR}/.cursor/skills/${SKILL_NAME}" \
    "${TARGET_DIR}/.cursor/skill-backups"
  install_skill_copy \
    "${TARGET_DIR}/.agents/skills/${SKILL_NAME}" \
    "${TARGET_DIR}/.agents/skill-backups"
fi

if [[ "${WITH_CODEX}" -eq 1 ]]; then
  install_skill_copy \
    "${TARGET_DIR}/.codex/skills/${SKILL_NAME}" \
    "${TARGET_DIR}/.codex/skill-backups"
fi

if [[ "${WRITE_AGENTS}" -eq 1 ]]; then
  AGENTS="${TARGET_DIR}/AGENTS.md"
  MARKER_BEGIN="deep-code-review:begin"
  MARKER_END="deep-code-review:end"
  LOCATIONS=".claude/skills/${SKILL_NAME}/SKILL.md"
  if [[ "${MINIMAL}" -eq 0 ]]; then
    LOCATIONS="${LOCATIONS}; also .cursor/skills/ and .agents/skills/"
  fi
  if [[ "${WITH_CODEX}" -eq 1 ]]; then
    LOCATIONS="${LOCATIONS}; .codex/skills/"
  fi
  BLOCK="$(cat <<EOF
<!-- ${MARKER_BEGIN} -->
## Code review — deep-code-review

Installed: **${VERSION}** (@ \`${INSTALL_SHA}\`).

Agent-agnostic deep code-review method (same phases on any coding agent).
Primary path: \`.claude/skills/${SKILL_NAME}/SKILL.md\` (${LOCATIONS}).
Depth lives in that skill \`references/\` directory.

How to run: read \`SKILL.md\`, state scope (\`FULL\` | \`DIFF <base-ref>\` |
\`FILE <paths>\`), work phases in order, load \`references/*.md\` on demand as
routed. Or invoke \`/deep-code-review <scope>\` where slash-skills are supported.
Yields a severity-ranked findings report (chat BLUF by default; full table
out-of-tree or, with explicit confirmation, under \`code-review/\`).

Re-run upstream \`install.sh\` to refresh this stamp.
<!-- ${MARKER_END} -->
EOF
)"
  if [[ -f "${AGENTS}" ]] && grep -q "${MARKER_BEGIN}" "${AGENTS}"; then
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
  echo "  works with Cursor, Claude Code, Codex, Copilot, Gemini, Aider, Windsurf, ..."
fi

echo "run it:  ask your agent for a deep code review, or /deep-code-review <scope>"
echo "  scopes: FULL | DIFF <base-ref> | FILE <paths>"
echo "  read:   .claude/skills/${SKILL_NAME}/SKILL.md (mirrors under .cursor/.agents/ when default install)"
