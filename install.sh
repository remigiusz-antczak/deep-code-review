#!/usr/bin/env bash
# install.sh — install deep-code-review (and optional overlays) into a project.
#
# Usage:
#   ./install.sh [--minimal] [--with-codex] [TARGET_DIR]
#   ./install.sh --with-delivery [--with-critic] [TARGET_DIR]
#   ./install.sh --full [TARGET_DIR]
#   ./install.sh --recommend [TARGET_DIR]
#
# Default (agent-agnostic): copies the REVIEW skill into every common skill
# root the major hosts discover, and writes/refreshes a root AGENTS.md pointer:
#   - .agents/skills/deep-code-review/   (Agent Skills / open standard)
#   - .cursor/skills/deep-code-review/   (Cursor)
#   - .claude/skills/deep-code-review/   (Claude Code; Cursor/Codex also load)
# Optional hosts:
#   --with-codex         also .codex/skills/
#   --with-extra-hosts   also .gemini .opencode .github .windsurf .hermes .kiro
# Overlay skills (opt-in; default stays review-only):
#   --with-delivery      also agentic-delivery
#   --with-critic        also idea-critic
#   --with-comms         also communication-structure
#   --with-contribution  also contribution (prepare upstream PRs; not in --full)
#   --with-discovery     also product-discovery (worth-building / PMF / prioritization; not in --full)
#   --with-ceo           also agentic-ceo (suite conductor: routing + effort-sizing + chaos playbook; not in --full)
#   --full               review + delivery + critic + comms
#   --recommend          inspect TARGET, print a pack, install nothing
# Narrow:
#   --minimal            only .claude/skills/ + AGENTS.md
#   --claude-only        only .claude/skills/ ; skip AGENTS.md
#   --with-cursor        no-op (Cursor path is now part of the default set)
#
# Source of truth in the upstream repo remains the trees under
# .claude/skills/<name>/ — install copies *from* there; never duplicates
# a skill inside the upstream repository itself.
#
# Backups land under <TARGET>/.<host>/skill-backups/ —
# never inside skills/, so backups are never loaded as duplicate skills.
# No network, no sudo, fully local and reversible.

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
install.sh — install deep-code-review for any coding agent.

Usage:
  ./install.sh [--minimal] [--with-codex] [--claude-only] [TARGET_DIR]
  ./install.sh --with-delivery [--with-critic] [TARGET_DIR]
  ./install.sh --full [TARGET_DIR]
  ./install.sh --recommend [TARGET_DIR]

Default: install REVIEW ONLY into .agents/skills/, .cursor/skills/, and
.claude/skills/, plus an AGENTS.md pointer (version-stamped; refreshed
on re-install). Overlay skills are opt-in.

  --minimal            Only .claude/skills/ + AGENTS.md
  --with-codex         Also .codex/skills/
  --with-extra-hosts   Also Gemini, OpenCode, Copilot, Windsurf, Hermes, Kiro
  --claude-only        Only .claude/skills/; skip AGENTS.md
  --with-cursor        Accepted as no-op (Cursor path is default now)
  --with-delivery      Also install agentic-delivery (gated delivery overlay)
  --with-critic        Also install idea-critic (pre-owner idea attack)
  --with-comms         Also install communication-structure (BLUF messages)
  --with-contribution  Also install contribution (prepare upstream PRs; default off, not in --full)
  --with-discovery     Also install product-discovery (worth-building / PMF / prioritization; default off, not in --full)
  --with-ceo           Also install agentic-ceo (suite conductor: routing, effort-sizing, chaos playbook; default off, not in --full)
  --full               Review + delivery + critic + comms
  --recommend          Inspect TARGET and print a recommended pack; no writes
  -h, --help           Show this help

TARGET_DIR defaults to the current working directory.

An agent should run --recommend, tell the owner the pack, and wait for a
yes before --with-delivery / --full. Default install stays review-only so
a second delivery OS already in the project is not doubled.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REVIEW_NAME="deep-code-review"

WRITE_AGENTS=1
MINIMAL=0
WITH_CODEX=0
WITH_EXTRA=0
WITH_DELIVERY=0
WITH_CRITIC=0
WITH_COMMS=0
WITH_CONTRIBUTION=0
WITH_DISCOVERY=0
WITH_CEO=0
RECOMMEND_ONLY=0
POSITIONAL=()
for arg in "$@"; do
  case "${arg}" in
    --claude-only) WRITE_AGENTS=0; MINIMAL=1 ;;
    --minimal) MINIMAL=1 ;;
    --with-codex) WITH_CODEX=1 ;;
    --with-extra-hosts) WITH_EXTRA=1 ;;
    --with-delivery) WITH_DELIVERY=1 ;;
    --with-critic) WITH_CRITIC=1 ;;
    --with-comms) WITH_COMMS=1 ;;
    --with-contribution) WITH_CONTRIBUTION=1 ;;
    --with-discovery) WITH_DISCOVERY=1 ;;
    --with-ceo) WITH_CEO=1 ;;
    --full) WITH_DELIVERY=1; WITH_CRITIC=1; WITH_COMMS=1 ;;
    --recommend) RECOMMEND_ONLY=1 ;;
    --with-cursor) echo "note: --with-cursor is default now; ignoring." >&2 ;;
    -p|--portable) echo "note: --portable is default; ignoring (use --minimal / --claude-only to narrow)." >&2 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "error: unknown option: ${arg}" >&2; usage; exit 2 ;;
    *) POSITIONAL+=("${arg}") ;;
  esac
done

TARGET_DIR="${POSITIONAL[0]:-$(pwd)}"

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "error: target directory does not exist: ${TARGET_DIR}" >&2
  exit 1
fi

if [[ "$(cd "${TARGET_DIR}" && pwd)" == "${SCRIPT_DIR}" ]]; then
  echo "error: target is the repository itself; choose another project directory." >&2
  exit 1
fi

if [[ "${RECOMMEND_ONLY}" -eq 1 ]]; then
  exec python3 "${SCRIPT_DIR}/scripts/recommend-overlays.py" "${TARGET_DIR}"
fi

SRC_REVIEW="${SCRIPT_DIR}/.claude/skills/${REVIEW_NAME}"
if [[ ! -f "${SRC_REVIEW}/SKILL.md" ]]; then
  echo "error: cannot find ${SRC_REVIEW}/SKILL.md" >&2
  echo "Run this script from inside a cloned deep-code-review repository." >&2
  exit 1
fi

VERSION="unknown"
if [[ -f "${SRC_REVIEW}/VERSION" ]]; then
  VERSION="$(tr -d '[:space:]' < "${SRC_REVIEW}/VERSION")"
fi
INSTALL_SHA="unknown"
if git -C "${SCRIPT_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  INSTALL_SHA="$(git -C "${SCRIPT_DIR}" rev-parse --short HEAD)"
fi

install_skill_copy() {
  local skill_name="$1"
  local dest="$2"
  local backup_root="$3"
  local src="${SCRIPT_DIR}/.claude/skills/${skill_name}"
  if [[ ! -f "${src}/SKILL.md" ]]; then
    echo "error: cannot find ${src}/SKILL.md" >&2
    exit 1
  fi
  mkdir -p "$(dirname "${dest}")"
  if [[ -e "${dest}" ]]; then
    mkdir -p "${backup_root}"
    # Portable, collision-free backup name: a seconds-resolution timestamp plus
    # an existence-checked numeric suffix, so rapid repeated installs within the
    # same second never reuse a name. Avoids `date +%N` (unsupported on BSD/macOS
    # date), which is why a plain timestamp alone would collide.
    local backup="${backup_root}/${skill_name}-$(date +%Y%m%d-%H%M%S)"
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
  cp -R "${src}" "${dest}"
  # Support docs the review skill cites — must resolve after install.
  if [[ "${skill_name}" == "${REVIEW_NAME}" ]]; then
    mkdir -p "${dest}/references"
    if [[ -f "${SCRIPT_DIR}/docs/standards-index.md" ]]; then
      cp "${SCRIPT_DIR}/docs/standards-index.md" "${dest}/references/standards-index.md"
    fi
    if [[ -f "${SCRIPT_DIR}/docs/example-review-report.md" ]]; then
      cp "${SCRIPT_DIR}/docs/example-review-report.md" "${dest}/references/example-review-report.md"
    fi
  fi
  local skill_ver="unknown"
  if [[ -f "${src}/VERSION" ]]; then
    skill_ver="$(tr -d '[:space:]' < "${src}/VERSION")"
  fi
  echo "installed: ${skill_name} ${skill_ver} (@ ${INSTALL_SHA}) -> ${dest}"
}

# Host roots that receive every selected skill.
HOSTS=()
HOSTS+=(".claude")
if [[ "${MINIMAL}" -eq 0 ]]; then
  HOSTS+=(".cursor" ".agents")
fi
if [[ "${WITH_CODEX}" -eq 1 ]]; then
  HOSTS+=(".codex")
fi
if [[ "${WITH_EXTRA}" -eq 1 ]]; then
  HOSTS+=(".gemini" ".opencode" ".github" ".windsurf" ".hermes" ".kiro")
fi

SKILLS=("${REVIEW_NAME}")
if [[ "${WITH_DELIVERY}" -eq 1 ]]; then
  SKILLS+=("agentic-delivery")
fi
if [[ "${WITH_CRITIC}" -eq 1 ]]; then
  SKILLS+=("idea-critic")
fi
if [[ "${WITH_COMMS}" -eq 1 ]]; then
  SKILLS+=("communication-structure")
fi
if [[ "${WITH_CONTRIBUTION}" -eq 1 ]]; then
  SKILLS+=("contribution")
fi
if [[ "${WITH_DISCOVERY}" -eq 1 ]]; then
  SKILLS+=("product-discovery")
fi
if [[ "${WITH_CEO}" -eq 1 ]]; then
  SKILLS+=("agentic-ceo")
fi

for skill in "${SKILLS[@]}"; do
  for host in "${HOSTS[@]}"; do
    install_skill_copy \
      "${skill}" \
      "${TARGET_DIR}/${host}/skills/${skill}" \
      "${TARGET_DIR}/${host}/skill-backups"
  done
done

upsert_agents_block() {
  local agents="$1"
  local marker_begin="$2"
  local marker_end="$3"
  local block="$4"
  if [[ -f "${agents}" ]] && grep -q "${marker_begin}" "${agents}"; then
    local block_file out_file
    block_file="$(mktemp)"
    out_file="$(mktemp)"
    printf '%s\n' "${block}" > "${block_file}"
    awk -v begin="<!-- ${marker_begin} -->" -v end="<!-- ${marker_end} -->" \
      -v bf="${block_file}" '
      BEGIN {
        while ((getline line < bf) > 0) { newblock = newblock line ORS }
        close(bf)
      }
      $0 == begin { printf "%s", newblock; skip=1; next }
      skip && $0 == end { skip=0; next }
      !skip { print }
    ' "${agents}" > "${out_file}"
    mv "${out_file}" "${agents}"
    rm -f "${block_file}"
    echo "agents: refreshed ${marker_begin} (v${VERSION} @ ${INSTALL_SHA}) -> ${agents}"
  elif [[ -f "${agents}" ]]; then
    printf '\n%s\n' "${block}" >> "${agents}"
    echo "agents: appended ${marker_begin} -> ${agents}"
  else
    printf '# AGENTS.md\n\n%s\n' "${block}" > "${agents}"
    echo "agents: created ${agents} with ${marker_begin}"
  fi
}

if [[ "${WRITE_AGENTS}" -eq 1 ]]; then
  AGENTS="${TARGET_DIR}/AGENTS.md"
  LOCATIONS=".claude/skills/${REVIEW_NAME}/SKILL.md"
  if [[ "${MINIMAL}" -eq 0 ]]; then
    LOCATIONS="${LOCATIONS}; also .cursor/skills/ and .agents/skills/"
  fi
  if [[ "${WITH_CODEX}" -eq 1 ]]; then
    LOCATIONS="${LOCATIONS}; .codex/skills/"
  fi
  if [[ "${WITH_EXTRA}" -eq 1 ]]; then
    LOCATIONS="${LOCATIONS}; extra hosts (.gemini .opencode .github .windsurf .hermes .kiro)"
  fi
  REVIEW_BLOCK="$(cat <<EOF
<!-- deep-code-review:begin -->
## Code review — deep-code-review

Installed: **${VERSION}** (@ \`${INSTALL_SHA}\`).

Agent-agnostic deep code-review method (same phases on any coding agent).
Primary path: \`.claude/skills/${REVIEW_NAME}/SKILL.md\` (${LOCATIONS}).
Depth lives in that skill \`references/\` directory.

How to run: read \`SKILL.md\`, state scope (\`FULL\` | \`DIFF <base-ref>\` |
\`FILE <paths>\`), work phases in order, load \`references/*.md\` on demand as
routed. Or invoke \`/deep-code-review <scope>\` where slash-skills are supported.
Yields a severity-ranked findings report (chat BLUF by default; full table
out-of-tree or, with explicit confirmation, under \`code-review/\`).

Re-run upstream \`install.sh\` to refresh this stamp.
<!-- deep-code-review:end -->
EOF
)"
  upsert_agents_block "${AGENTS}" "deep-code-review:begin" "deep-code-review:end" "${REVIEW_BLOCK}"

  if [[ "${WITH_DELIVERY}" -eq 1 || "${WITH_CRITIC}" -eq 1 || "${WITH_COMMS}" -eq 1 || "${WITH_CONTRIBUTION}" -eq 1 ]]; then
    OVERLAY_LINES=""
    if [[ "${WITH_DELIVERY}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES}
- \`agentic-delivery\` — gated G0–G10 delivery plus the software-house role
  roster (Conductor, Product Analyst, Architect, Implementer, Evil Twin, QA,
  Security, UX & Design, Release, Docs — hats, not standing bots;
  \`references/roles.md\`). Load it for features that span implementation +
  QA + security. Names \`deep-code-review\` at specification, review, and
  integrate."
    fi
    if [[ "${WITH_CRITIC}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES}
- \`idea-critic\` — attack a plan or \"we should\" before the owner sees it.
  Three hats; HOLD / REVISE / PASS_TO_USER. Owner-request cannot HOLD."
    fi
    if [[ "${WITH_COMMS}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES}
- \`communication-structure\` — makes a PR body, issue/PR comment, or status
  update BLUF, one ask, scannable, zero AI-slop by default. Governs
  persisted-message structure and length, not chat voice (see below)."
    fi
    if [[ "${WITH_CONTRIBUTION}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES}
- \`contribution\` — prepare a privacy-safe, generalized improvement back to the
  public skillset for a human to review and open as a PR. The agent drafts and
  gates the change and flags residual risk; a human is the privacy authority and
  the only one who pushes. Default off; never auto-PRs."
    fi
    if [[ "${WITH_DISCOVERY}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES}
- \`product-discovery\` — decide whether something is worth building, what to
  build first, and whether what shipped works, by structuring evidence from real
  users (Mom Test, JTBD, riskiest-assumption gate, PMF read, ICE). Never
  fabricates findings, personas, scores, or a validated verdict. Default off."
    fi
    if [[ "${WITH_CEO}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES}
- \`agentic-ceo\` — the suite's conductor: routes (stage, area) to the right skill
  and lens, sizes effort to the project (no swarm on small work), and runs the
  under-pressure chaos playbook. Routes; never duplicates a skill. Default off."
    fi
    OVERLAY_BLOCK="$(cat <<EOF
<!-- dcr-overlays:begin -->
## Optional overlays

Installed alongside deep-code-review **${VERSION}** (@ \`${INSTALL_SHA}\`).
These are optional; default \`install.sh\` does not add them.
${OVERLAY_LINES}

Do not also run a second delivery OS on this repo. Persisted artifacts
(code, PR bodies, docs) stay normal English. Chat voice is not vendored
here — if compressed assistant prose is wanted, add JuliusBrussee/caveman
separately.

Re-run upstream \`install.sh --with-delivery\` / \`--with-critic\` /
\`--with-comms\` / \`--with-contribution\` / \`--with-discovery\` / \`--with-ceo\` / \`--full\` to refresh this stamp.
<!-- dcr-overlays:end -->
EOF
)"
    upsert_agents_block "${AGENTS}" "dcr-overlays:begin" "dcr-overlays:end" "${OVERLAY_BLOCK}"
  fi
  echo "  works with Cursor, Claude Code, Codex, Copilot, Gemini, Aider, Windsurf, OpenCode, Hermes, Kiro, ..."
fi

echo "run it:  ask your agent for a deep code review, or /deep-code-review <scope>"
echo "  scopes: FULL | DIFF <base-ref> | FILE <paths>"
echo "  read:   .claude/skills/${REVIEW_NAME}/SKILL.md (mirrors under other hosts when installed)"
if [[ "${WITH_DELIVERY}" -eq 1 ]]; then
  echo "  delivery: load agentic-delivery for gated multi-role work"
fi
if [[ "${WITH_CRITIC}" -eq 1 ]]; then
  echo "  critic:   load idea-critic before a plan reaches the owner"
fi
if [[ "${WITH_COMMS}" -eq 1 ]]; then
  echo "  comms:    load communication-structure before any human-facing message"
fi
