#!/usr/bin/env bash
# dcr-gates.sh — run the INSTALLED deep-code-review skill's own gate scripts
# in THIS repo's CI (or locally). Copied verbatim by `install.sh --with-gates`
# to <target>/scripts/dcr-gates.sh; never modified by the installer once
# copied — edit it in place if this project's test-glob or allowlist needs
# differ from the defaults below.
#
# WHY THIS EXISTS: the skillset's mechanisms (fix_class_gate.py,
# binaries_gate.py, and friends) only enforce anything inside the
# deep-code-review repository's own CI. A project that installs the skill
# gets the doctrine as prose an agent may or may not follow, and the
# mechanism itself never runs here. This script is the opt-in bridge:
# `install.sh --with-gates` + `.github/workflows/dcr-gates.yml` wires it into
# this repo's CI so the same enforcement fires on every push/PR.
#
# ONE IMPLEMENTATION — no duplicated gate logic. Every check below calls a
# script living INSIDE the installed skill tree (resolved dynamically below);
# this file only resolves paths and wires exit codes together. Upgrading the
# skill (re-running install.sh) upgrades the checks this file runs, with zero
# edits here.
#
# Configuration (env vars, all optional):
#   DCR_TEST_GLOBS         space-separated globs a fix commit's test-surface
#                           touch must match (passed to fix_class_gate.py
#                           --test-glob, once per glob, as literal patterns —
#                           never expanded against this directory). Unset ->
#                           the script's own defaults (tests/** etc; see its
#                           --help).
#   DCR_BINARIES_ALLOWLIST path to the binaries-gate allowlist file. Unset ->
#                           <repo-root>/scripts/binaries-allowlist.tsv if it
#                           exists, else no exemptions.
#   BASE_SHA / HEAD_SHA     the commit range fix_class_gate.py checks. In CI,
#                           set these from the event (see the shipped
#                           workflow template). Locally, defaults to
#                           HEAD~1..HEAD when both are unset.
#
# Exit code: 0 iff every gate below passed. Fails closed — an unresolvable
# skill install, a gate or selftest script missing from that install, or any
# gate script itself failing to run, is a failure, not a skip.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { printf 'dcr-gates: %s\n' "$*" >&2; exit 1; }

# Every host root install.sh can write a skill into, in the same order
# install.sh tries them. The first host carrying deep-code-review's SKILL.md
# is treated as THE install location for every skill this runner looks for.
HOST_CANDIDATES=(.claude .agents .cursor .codex .gemini .opencode .github .windsurf .hermes .kiro)

# find_skill_root <skill-name> — print the first host's copy of <skill-name>
# with a real SKILL.md, or print nothing (caller checks for empty).
find_skill_root() {
  local skill="$1" host
  for host in "${HOST_CANDIDATES[@]}"; do
    if [ -f "${REPO_ROOT}/${host}/skills/${skill}/SKILL.md" ]; then
      printf '%s/%s/skills/%s' "${REPO_ROOT}" "${host}" "${skill}"
      return 0
    fi
  done
  return 1
}

REVIEW_ROOT="$(find_skill_root deep-code-review)" \
  || die "no installed deep-code-review skill found under ${REPO_ROOT} (checked: ${HOST_CANDIDATES[*]}). Run install.sh first."
printf 'dcr-gates: using deep-code-review at %s\n' "${REVIEW_ROOT}"

DELIVERY_ROOT="$(find_skill_root agentic-delivery || true)"
if [ -n "${DELIVERY_ROOT}" ]; then
  printf 'dcr-gates: using agentic-delivery at %s\n' "${DELIVERY_ROOT}"
fi

FAIL=0

# ---------------------------------------------------------------------------
# 1) fix_class_gate — every fix(...) commit in range touches a pinned test,
#    or carries a non-empty No-Test-Reason: trailer.
# ---------------------------------------------------------------------------
FIX_CLASS_GATE="${REVIEW_ROOT}/scripts/fix_class_gate.py"
if [ -f "${FIX_CLASS_GATE}" ]; then
  BASE_SHA="${BASE_SHA:-}"
  HEAD_SHA="${HEAD_SHA:-}"
  if [ -z "${BASE_SHA}" ] && [ -z "${HEAD_SHA}" ]; then
    # `--verify` (not a bare `rev-parse <ref>`): on an unresolvable ref, plain
    # `git rev-parse HEAD~1` still prints the literal ref text to STDOUT
    # (alongside the fatal error on stderr) despite its non-zero exit — a
    # known git quirk. `--verify` never does that, so a failure here is
    # reliably empty, not the poisoned literal string "HEAD~1".
    HEAD_SHA="$(git -C "${REPO_ROOT}" rev-parse --verify -q HEAD 2>/dev/null || true)"
    BASE_SHA="$(git -C "${REPO_ROOT}" rev-parse --verify -q 'HEAD~1' 2>/dev/null || true)"
  fi
  if [ -z "${BASE_SHA}" ] || [ -z "${HEAD_SHA}" ]; then
    if [ -n "${CI:-}" ]; then
      # In CI the workflow must supply a resolvable range; a missing one is a
      # misconfiguration, never a pass.
      printf 'dcr-gates: FAIL fix_class_gate (BASE_SHA/HEAD_SHA unresolvable in CI)\n'
      FAIL=1
    else
      printf 'dcr-gates: fix_class_gate skipped (local run, no range: single-commit repo?)\n'
    fi
  else
    glob_args=()
    if [ -n "${DCR_TEST_GLOBS:-}" ]; then
      # `read -ra` splits on whitespace WITHOUT pathname expansion, so a glob
      # like `tests/*` reaches fix_class_gate.py as a pattern, not as whatever
      # files it happens to match in the current directory.
      read -r -a test_globs <<<"${DCR_TEST_GLOBS}"
      for g in "${test_globs[@]+"${test_globs[@]}"}"; do
        glob_args+=(--test-glob "$g")
      done
    fi
    # fix_class_gate.py resolves the range against its OWN process cwd (it
    # takes no --repo flag), so this must run with cwd == REPO_ROOT — never
    # wherever dcr-gates.sh itself happened to be invoked from.
    if (cd "${REPO_ROOT}" && python3 "${FIX_CLASS_GATE}" --base "${BASE_SHA}" --head "${HEAD_SHA}" "${glob_args[@]+"${glob_args[@]}"}"); then
      printf 'dcr-gates: fix_class_gate PASS\n'
    else
      printf 'dcr-gates: fix_class_gate FAIL\n' >&2
      FAIL=1
    fi
  fi
else
  printf 'dcr-gates: fix_class_gate.py not found at %s (FAIL, fail closed)\n' "${FIX_CLASS_GATE}" >&2
  FAIL=1
fi

# ---------------------------------------------------------------------------
# 2) binaries_gate — no git-tracked file at a banned image/media/archive/
#    build-output extension.
# ---------------------------------------------------------------------------
BINARIES_GATE="${REVIEW_ROOT}/scripts/binaries_gate.py"
if [ -f "${BINARIES_GATE}" ]; then
  allow_args=()
  if [ -n "${DCR_BINARIES_ALLOWLIST:-}" ]; then
    allow_args=(--allowlist "${DCR_BINARIES_ALLOWLIST}")
  fi
  if python3 "${BINARIES_GATE}" "${allow_args[@]+"${allow_args[@]}"}" "${REPO_ROOT}"; then
    printf 'dcr-gates: binaries_gate PASS\n'
  else
    printf 'dcr-gates: binaries_gate FAIL\n' >&2
    FAIL=1
  fi
else
  printf 'dcr-gates: binaries_gate.py not found at %s (FAIL, fail closed)\n' "${BINARIES_GATE}" >&2
  FAIL=1
fi

# ---------------------------------------------------------------------------
# 3) selftests of every shipped gate script this runner knows how to call —
#    proves each fires on a planted violation before its result is trusted,
#    independent of this repo's own history/content.
# ---------------------------------------------------------------------------
SELFTEST_SCRIPTS=(
  "${REVIEW_ROOT}/scripts/fix_class_gate.py"
  "${REVIEW_ROOT}/scripts/binaries_gate.py"
  "${REVIEW_ROOT}/scripts/parity_differ.py"
)
if [ -n "${DELIVERY_ROOT}" ]; then
  SELFTEST_SCRIPTS+=(
    "${DELIVERY_ROOT}/scripts/serial_gate.py"
    "${DELIVERY_ROOT}/scripts/handback_cap.py"
  )
fi
for script in "${SELFTEST_SCRIPTS[@]}"; do
  if [ ! -f "${script}" ]; then
    # Every listed script ships with its skill; a missing one means a partial
    # or tampered install, never a reason to skip its selftest.
    printf 'dcr-gates: selftest script not found at %s (FAIL, fail closed)\n' "${script}" >&2
    FAIL=1
    continue
  fi
  if python3 "${script}" --selftest; then
    :
  else
    printf 'dcr-gates: selftest FAILED for %s\n' "${script}" >&2
    FAIL=1
  fi
done

[ "${FAIL}" -eq 0 ] || die "one or more gates failed (see above)"
printf 'dcr-gates: all gates passed\n'
