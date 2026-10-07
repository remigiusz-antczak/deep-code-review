#!/usr/bin/env bash
# install.sh — install deep-code-review (and optional overlays) into a project.
#
# Usage:
#   ./install.sh [--minimal] [--with-codex] [TARGET_DIR]
#   ./install.sh --with-delivery [--with-critic] [TARGET_DIR]
#   ./install.sh --full [TARGET_DIR]
#   ./install.sh --with-gates [TARGET_DIR]
#   ./install.sh --with-delivery --with-operating-layer [TARGET_DIR]
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
#   --with-growth        also growth-analytics (North Star + AARRR + event taxonomy; not in --full)
#   --with-positioning   also positioning (value prop / message house; a hypothesis, never fabricated market facts; not in --full)
#   --with-business      also business-ops (Lane A pricing/unit-economics apply vs Lane R legal/tax/securities route; not in --full)
#   --with-output-safety also product-output-safety (govern harm from the product's own AI outputs; HITL on high-stakes actions; not in --full)
#   --full               review + delivery + critic + comms
#   --recommend          inspect TARGET, print a pack, install nothing
# CI enforcement (mechanism, not a skill; opt-in; never overwrites a file):
#   --with-gates         also write .github/workflows/dcr-gates.yml +
#                         scripts/dcr-gates.sh, wiring the INSTALLED skill's
#                         own gate scripts (fix_class_gate, binaries_gate)
#                         into the target's own CI; and .githooks/pre-push, a
#                         local hook that reruns the fast lint+unit tier
#                         before every push (opt in yourself: git config
#                         core.hooksPath .githooks -- never run by this
#                         script). Prints (does not write) a settings.json
#                         snippet for agentic-delivery's two-tier SubagentStop
#                         handback_cap hook and its SubagentStart
#                         subagent_start_inject hook.
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
  --with-growth        Also install growth-analytics (North Star + AARRR + event taxonomy; default off, not in --full)
  --with-positioning   Also install positioning (value prop / message house; a hypothesis, never fabricated market facts; default off, not in --full)
  --with-business      Also install business-ops (Lane A pricing/unit-economics apply vs Lane R legal/tax/securities route; default off, not in --full)
  --with-output-safety Also install product-output-safety (govern harm from the product's own AI outputs; HITL on high-stakes actions; default off, not in --full)
  --full               Review + delivery + critic + comms
  --with-gates         Write .github/workflows/dcr-gates.yml + scripts/dcr-gates.sh,
                       wiring the INSTALLED skill's own gate scripts (fix_class_gate,
                       binaries_gate) into the target's own CI, plus
                       .githooks/pre-push (reruns the fast lint+unit tier before every
                       push -- opt in yourself with `git config core.hooksPath
                       .githooks`, never run by this script); never overwrites an
                       existing file at any of these paths (writes .new instead).
                       See --with-operating-layer for the SubagentStart/SubagentStop
                       settings snippet. Mechanism, not a skill.
  --with-operating-layer
                       Write .claude/settings.operating-layer.json.new: the
                       SubagentStart house-default injector, the two-tier
                       SubagentStop handback_cap, and the subagent model pin
                       (agentic-delivery/references/operating-discipline.md).
                       Never overwrites an existing file at that path (writes
                       .new-1, .new-2, ... instead). Requires --with-delivery.
  --apply-operating-layer
                       Instead of writing a .new snippet, jq-merge the operating-layer
                       hooks/env (plus model "sonnet" if unset) into
                       TARGET/.claude/settings.local.json idempotently (backup first;
                       fails closed if jq is missing) and write
                       .claude/agents/delivery-lane.md if absent. Implies
                       --with-operating-layer; requires --with-delivery.
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
WITH_GROWTH=0
WITH_POSITIONING=0
WITH_BUSINESS=0
WITH_OUTPUT_SAFETY=0
WITH_GATES=0
WITH_OPERATING_LAYER=0
APPLY_OPLAYER=0
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
    --with-growth) WITH_GROWTH=1 ;;
    --with-positioning) WITH_POSITIONING=1 ;;
    --with-business) WITH_BUSINESS=1 ;;
    --with-output-safety) WITH_OUTPUT_SAFETY=1 ;;
    --with-gates) WITH_GATES=1 ;;
    --with-operating-layer) WITH_OPERATING_LAYER=1 ;;
    --apply-operating-layer) WITH_OPERATING_LAYER=1; APPLY_OPLAYER=1 ;;
    --full) WITH_DELIVERY=1; WITH_CRITIC=1; WITH_COMMS=1 ;;
    --recommend) RECOMMEND_ONLY=1 ;;
    --with-cursor) echo "note: --with-cursor is default now; ignoring." >&2 ;;
    -p|--portable) echo "note: --portable is default; ignoring (use --minimal / --claude-only to narrow)." >&2 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "error: unknown option: ${arg}" >&2; usage; exit 2 ;;
    *) POSITIONAL+=("${arg}") ;;
  esac
done

if [[ "${WITH_OPERATING_LAYER}" -eq 1 && "${WITH_DELIVERY}" -eq 0 ]]; then
  echo "error: --with-operating-layer requires --with-delivery (writes an agentic-delivery snippet)" >&2
  exit 1
fi

if [[ "${APPLY_OPLAYER}" -eq 1 ]] && ! command -v jq >/dev/null 2>&1; then
  echo "error: --apply-operating-layer needs jq (fail closed); install jq or use --with-operating-layer" >&2
  exit 1
fi

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
  # Never ship local Python bytecode caches (created by running a script selftest).
  find "${dest}" -name __pycache__ -type d -prune -exec rm -rf {} +
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
if [[ "${WITH_GROWTH}" -eq 1 ]]; then
  SKILLS+=("growth-analytics")
fi
if [[ "${WITH_POSITIONING}" -eq 1 ]]; then
  SKILLS+=("positioning")
fi
if [[ "${WITH_BUSINESS}" -eq 1 ]]; then
  SKILLS+=("business-ops")
fi
if [[ "${WITH_OUTPUT_SAFETY}" -eq 1 ]]; then
  SKILLS+=("product-output-safety")
fi

for skill in "${SKILLS[@]}"; do
  for host in "${HOSTS[@]}"; do
    install_skill_copy \
      "${skill}" \
      "${TARGET_DIR}/${host}/skills/${skill}" \
      "${TARGET_DIR}/${host}/skill-backups"
  done
done

# write_gate_file <src> <dest> <executable:0|1> — copy a CI-gates template
# into the target. NEVER overwrites an existing file at <dest>: if one is
# already there, writes <dest>.new (or .new-N on a further collision) instead
# and prints a note so the owner reviews/merges by hand. This is the only
# writer for --with-gates output; both call sites below share it so the
# never-overwrite rule cannot drift between the workflow and the runner.
write_gate_file() {
  local src="$1" dest="$2" make_exec="$3"
  mkdir -p "$(dirname "${dest}")"
  if [[ -e "${dest}" ]]; then
    local newdest="${dest}.new"
    if [[ -e "${newdest}" ]]; then
      local n=1
      while [[ -e "${newdest}-${n}" ]]; do
        n=$((n + 1))
      done
      newdest="${newdest}-${n}"
    fi
    cp "${src}" "${newdest}"
    [[ "${make_exec}" -eq 1 ]] && chmod +x "${newdest}"
    echo "note: ${dest} already exists -> wrote ${newdest} instead (review and merge by hand)"
  else
    cp "${src}" "${dest}"
    [[ "${make_exec}" -eq 1 ]] && chmod +x "${dest}"
    echo "installed: ${dest}"
  fi
}

if [[ "${WITH_GATES}" -eq 1 ]]; then
  GATES_SRC="${SCRIPT_DIR}/.claude/skills/${REVIEW_NAME}/templates"
  if [[ ! -f "${GATES_SRC}/dcr-gates.yml" || ! -f "${GATES_SRC}/dcr-gates.sh" || ! -f "${GATES_SRC}/pre-push-verify.sh" || ! -f "${GATES_SRC}/integrator-gate.sh" ]]; then
    echo "error: cannot find ${GATES_SRC}/{dcr-gates.yml,dcr-gates.sh,pre-push-verify.sh,integrator-gate.sh}" >&2
    exit 1
  fi
  write_gate_file "${GATES_SRC}/dcr-gates.yml" "${TARGET_DIR}/.github/workflows/dcr-gates.yml" 0
  write_gate_file "${GATES_SRC}/dcr-gates.sh" "${TARGET_DIR}/scripts/dcr-gates.sh" 1
  write_gate_file "${GATES_SRC}/pre-push-verify.sh" "${TARGET_DIR}/.githooks/pre-push" 1
  write_gate_file "${GATES_SRC}/integrator-gate.sh" "${TARGET_DIR}/scripts/integrator-gate.sh" 1
  cat <<'EOF'

CI enforcement wired (--with-gates), MINIMUM-COST PROFILE by default:
  .github/workflows/dcr-gates.yml  PR-into-main ONLY (ready_for_review +
                                    synchronize; drafts skipped); no push
                                    trigger, no schedule; SHA-pinned checkout,
                                    workflow-level concurrency cancels a
                                    superseded run
  scripts/dcr-gates.sh             calls the INSTALLED skill's own gate scripts
                                    (fix_class_gate, binaries_gate) by resolved
                                    path -- no duplicated gate logic, no copies
  .githooks/pre-push               reruns the fast lint+unit tier (DCR_PREPUSH_CMD)
                                    before every push -- catches an unverified rebase-
                                    conflict-resolution commit locally, before CI. Not
                                    wired yet: run this yourself (not run by install.sh)
                                    to opt in:
                                      git config core.hooksPath .githooks
                                    Then set DCR_PREPUSH_CMD (e.g. "make lint test-unit")
                                    in your shell profile. It is self-report, not a
                                    substitute for CI -- see the hook's own header.
  scripts/integrator-gate.sh       run this on an integration branch's merge
                                    result instead of adding hosted CI to it --
                                    see its own header and
                                    agentic-delivery/references/host-enforcement.md's
                                    "Minimum-cost CI & token profile"
Edit the workflow's trigger branch if this repo's default branch isn't `main`.

MINIMUM-COST PROFILE CHECKLIST -- these are OWNER actions; install.sh never
automates them (they need forge/org privileges this script does not have):
  [ ] If this repo has a separate integration branch (development, staging,
      ...): add branch protection/ruleset restricting merge AND push to ONE
      integrator identity -- a deterministic script (never an LLM session),
      run from launchd/cron with its gate token in the OS keychain, plus a
      documented break-glass path for running it by hand. That identity runs
      `scripts/integrator-gate.sh --target-branch <branch>`, which pushes the
      merge result to a scratch ref, gates it, and only on a pass
      fast-forwards the branch -- never `[skip ci]` on that branch. Do NOT
      add hosted CI to it.
  [ ] If a required status check is needed on the integration branch: have
      integrator-gate.sh post it using a SEPARATE, low-privilege token from
      whatever pushes -- never the same identity (it would be forgeable).
  [ ] Set a soft spend budget (GitHub Settings > Billing) with alerts at
      50/80/100% of your cap -- never a hard stop that could block real CI.
  [ ] Confirm plan/ownership before relying on GitHub's merge queue: it needs
      a public repo, or a private repo owned by an org on GitHub Enterprise
      Cloud -- Team, Pro, and personal-account repos get none of it.
  [ ] Run `python3 .claude/skills/deep-code-review/scripts/ci_cost_lint.py --gate .`
      before merging any new/changed workflow file.

Optional, only useful alongside --with-delivery: --with-operating-layer WRITES the
two-tier SubagentStop hand-back cap, the SubagentStart house-default injector, and
the subagent model pin as a settings.operating-layer.json.new snippet to merge by
hand -- see agentic-delivery/references/operating-discipline.md (the always-on
operating layer's one entry point) and its "Install and self-check" section.
EOF
fi

if [[ "${WITH_OPERATING_LAYER}" -eq 1 ]]; then
  OPLAYER_SRC="${SCRIPT_DIR}/.claude/skills/agentic-delivery/templates/operating-layer.settings.json"
  if [[ ! -f "${OPLAYER_SRC}" ]]; then
    echo "error: cannot find ${OPLAYER_SRC}" >&2
    exit 1
  fi
  OPLAYER_DEST="${TARGET_DIR}/.claude/settings.operating-layer.json.new"
  mkdir -p "$(dirname "${OPLAYER_DEST}")"
  if [[ "${APPLY_OPLAYER}" -eq 1 ]]; then
    OPLAYER_LOCAL="${TARGET_DIR}/.claude/settings.local.json"
    [[ -f "${OPLAYER_LOCAL}" ]] || echo '{}' > "${OPLAYER_LOCAL}"
    # Append template hook entries not already present; existing env/model win.
    # Placeholder matchers (contain "<") never fire: skip them, tell the operator.
    echo "warning: skipped template hook entries with a placeholder matcher (e.g. <your-read-only-review-type>); add a SubagentStop entry with your real review agent type by hand" >&2
    jq --slurpfile t "${OPLAYER_SRC}" '
      ($t[0]) as $t
      | reduce ($t.hooks | keys[]) as $e (.;
          (.hooks[$e] // []) as $a
          | .hooks[$e] = $a + ($t.hooks[$e] | map(select(((.matcher // "") | contains("<") | not) and (. as $x | $a | index([$x]) | not)))))
      | .env = ($t.env + (.env // {}))
      | .model //= "sonnet"' "${OPLAYER_LOCAL}" > "${OPLAYER_LOCAL}.tmp"
    if cmp -s "${OPLAYER_LOCAL}" "${OPLAYER_LOCAL}.tmp"; then
      rm -f "${OPLAYER_LOCAL}.tmp"
    else
      cp "${OPLAYER_LOCAL}" "${OPLAYER_LOCAL}.bak"
      mv "${OPLAYER_LOCAL}.tmp" "${OPLAYER_LOCAL}"
    fi
    OPLAYER_AGENT="${TARGET_DIR}/.claude/agents/delivery-lane.md"
    if [[ ! -e "${OPLAYER_AGENT}" ]]; then
      mkdir -p "$(dirname "${OPLAYER_AGENT}")"
      cat > "${OPLAYER_AGENT}" <<'AGENT'
---
name: delivery-lane
description: Default delivery lane for bounded implementation work. Terse, cheap, one-line hand-back.
model: sonnet
---
Do the assigned bounded task with the simplest change that works. Read only the line ranges you need. Run the project's own gates before claiming done. Final message is one line: status, evidence (sha/path/test), next step.
AGENT
    fi
    echo "applied operating layer to ${OPLAYER_LOCAL} (backup: .bak if changed); verify with:"
    echo "  python3 .claude/skills/agentic-delivery/scripts/operating_selfcheck.py --settings .claude/settings.local.json"
  else
  if [[ -e "${OPLAYER_DEST}" ]]; then
    OPLAYER_N=1
    while [[ -e "${OPLAYER_DEST}-${OPLAYER_N}" ]]; do
      OPLAYER_N=$((OPLAYER_N + 1))
    done
    OPLAYER_DEST="${OPLAYER_DEST}-${OPLAYER_N}"
  fi
  cp "${OPLAYER_SRC}" "${OPLAYER_DEST}"
  echo "wrote ${OPLAYER_DEST} -- merge its \"hooks\"/\"env\" keys into ${TARGET_DIR}/.claude/settings.json by hand, then verify with:"
  echo "  python3 .claude/skills/agentic-delivery/scripts/operating_selfcheck.py"
  fi
fi

# Record the flags so scripts/update-installed.sh can replay this install.
mkdir -p "${TARGET_DIR}/.claude"
{ for a in "$@"; do [[ "${a}" == -* ]] && printf '%s\n' "${a}"; done; true; } > "${TARGET_DIR}/.claude/.dcr-install-flags"

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
  LOCATIONS=""
  if [[ "${MINIMAL}" -eq 0 ]]; then
    LOCATIONS="also .cursor/skills/ and .agents/skills/"
  fi
  if [[ "${WITH_CODEX}" -eq 1 ]]; then
    LOCATIONS="${LOCATIONS:+${LOCATIONS}; }.codex/skills/"
  fi
  if [[ "${WITH_EXTRA}" -eq 1 ]]; then
    LOCATIONS="${LOCATIONS:+${LOCATIONS}; }extra hosts (.gemini .opencode .github .windsurf .hermes .kiro)"
  fi
  # Primary path is stated once; the parenthetical lists only the MIRROR roots
  # (empty under --minimal, so no bare "()" and no path repeated).
  if [[ -n "${LOCATIONS}" ]]; then
    PRIMARY_PATH_LINE="Primary path: \`.claude/skills/${REVIEW_NAME}/SKILL.md\` (${LOCATIONS})."
  else
    PRIMARY_PATH_LINE="Primary path: \`.claude/skills/${REVIEW_NAME}/SKILL.md\`."
  fi
  REVIEW_BLOCK="$(cat <<EOF
<!-- deep-code-review:begin -->
## Code review — deep-code-review
Installed: **${VERSION}** (@ \`${INSTALL_SHA}\`). Agent-agnostic method.
${PRIMARY_PATH_LINE} Scope: \`FULL\` | \`DIFF <base-ref>\` | \`FILE <paths>\`; or \`/deep-code-review <scope>\`.
Re-run upstream \`install.sh\` to refresh.
<!-- deep-code-review:end -->
EOF
)"
  upsert_agents_block "${AGENTS}" "deep-code-review:begin" "deep-code-review:end" "${REVIEW_BLOCK}"

  if [[ "${WITH_DELIVERY}" -eq 1 || "${WITH_CRITIC}" -eq 1 || "${WITH_COMMS}" -eq 1 || "${WITH_CONTRIBUTION}" -eq 1 || "${WITH_DISCOVERY}" -eq 1 || "${WITH_CEO}" -eq 1 || "${WITH_GROWTH}" -eq 1 || "${WITH_POSITIONING}" -eq 1 || "${WITH_BUSINESS}" -eq 1 || "${WITH_OUTPUT_SAFETY}" -eq 1 ]]; then
    OVERLAY_LINES=""
    if [[ "${WITH_DELIVERY}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`agentic-delivery\`"
    fi
    if [[ "${WITH_CRITIC}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`idea-critic\`"
    fi
    if [[ "${WITH_COMMS}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`communication-structure\`"
    fi
    if [[ "${WITH_CONTRIBUTION}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`contribution\`"
    fi
    if [[ "${WITH_DISCOVERY}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`product-discovery\`"
    fi
    if [[ "${WITH_CEO}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`agentic-ceo\`"
    fi
    if [[ "${WITH_GROWTH}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`growth-analytics\`"
    fi
    if [[ "${WITH_POSITIONING}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`positioning\`"
    fi
    if [[ "${WITH_BUSINESS}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`business-ops\`"
    fi
    if [[ "${WITH_OUTPUT_SAFETY}" -eq 1 ]]; then
      OVERLAY_LINES="${OVERLAY_LINES} \`product-output-safety\`"
    fi
    OVERLAY_BLOCK="$(cat <<EOF
<!-- dcr-overlays:begin -->
## Optional overlays (deep-code-review ${VERSION} @ \`${INSTALL_SHA}\`)
Installed, each at \`.claude/skills/<name>/SKILL.md\`:${OVERLAY_LINES}. Persisted artifacts stay normal English.
Re-run upstream \`install.sh\` with the same \`--with-*\` flags (or \`--full\`) to refresh.
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
  echo "  janitor:  schedule unattended cleanup (previews first, then runs every 15 min): bash .claude/skills/agentic-delivery/scripts/install_janitor.sh <repo>..."
  echo "            installed? bash .claude/skills/agentic-delivery/scripts/install_janitor.sh --check"
fi
if [[ "${WITH_CRITIC}" -eq 1 ]]; then
  echo "  critic:   load idea-critic before a plan reaches the owner"
fi
if [[ "${WITH_COMMS}" -eq 1 ]]; then
  echo "  comms:    load communication-structure before any human-facing message"
fi
if [[ "${WITH_GATES}" -eq 1 ]]; then
  echo "  gates:    dcr-gates.yml + scripts/dcr-gates.sh wired -- push/open a PR to run them"
fi
if [[ "${WITH_OPERATING_LAYER}" -eq 1 ]]; then
  [[ "${APPLY_OPLAYER}" -eq 1 ]] && echo "  operating-layer: applied to .claude/settings.local.json" || echo "  operating-layer: settings.operating-layer.json.new written -- merge it, then run operating_selfcheck.py"
fi
