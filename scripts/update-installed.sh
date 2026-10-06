#!/usr/bin/env bash
# Re-run install.sh on each TARGET with the flags recorded by its last install
# (TARGET/.claude/.dcr-install-flags), so installed skills track this checkout.
# First fetches this checkout and fast-forwards it when behind its upstream;
# refuses on a dirty tree, diverged history, or no upstream (DCR_NO_PULL=1 skips).
# Usage: scripts/update-installed.sh TARGET...
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ $# -gt 0 ]] || { echo "usage: $0 TARGET..." >&2; exit 2; }
if [[ "${DCR_NO_PULL:-0}" != 1 ]]; then
  git -C "${HERE}" fetch -q || { echo "error: git fetch failed in ${HERE}" >&2; exit 1; }
  git -C "${HERE}" rev-parse -q --verify '@{u}' >/dev/null \
    || { echo "error: ${HERE} has no upstream branch; set one or use DCR_NO_PULL=1" >&2; exit 1; }
  if [[ "$(git -C "${HERE}" rev-parse HEAD)" != "$(git -C "${HERE}" rev-parse '@{u}')" ]]; then
    [[ -z "$(git -C "${HERE}" status --porcelain --untracked-files=no)" ]] \
      || { echo "error: ${HERE} has uncommitted changes; commit or stash, then retry" >&2; exit 1; }
    git -C "${HERE}" pull -q --ff-only \
      || { echo "error: ${HERE} cannot fast-forward (diverged from upstream); resolve manually" >&2; exit 1; }
  fi
fi
echo "dcr version: $(cat "${HERE}/.claude/skills/deep-code-review/VERSION")"
for t in "$@"; do
  m="${t}/.claude/.dcr-install-flags"
  if [[ ! -f "${m}" ]]; then
    # Pre-marker install: infer one flag per installed sibling skill, plus the operating layer.
    inf=()
    for p in agentic-delivery:--with-delivery idea-critic:--with-critic communication-structure:--with-comms \
      contribution:--with-contribution product-discovery:--with-discovery agentic-ceo:--with-ceo \
      growth-analytics:--with-growth positioning:--with-positioning business-ops:--with-business \
      product-output-safety:--with-output-safety; do
      [[ -d "${t}/.claude/skills/${p%%:*}" ]] && inf+=("${p#*:}")
    done
    grep -qs subagent_start_inject.py "${t}/.claude/settings.local.json" && inf+=(--apply-operating-layer)
    [[ -d "${t}/.claude/skills/deep-code-review" ]] \
      || { echo "error: no install marker at ${m} and no deep-code-review skill to infer from; run install.sh once first" >&2; exit 1; }
    mkdir -p "${t}/.claude"
    printf '%s\n' ${inf[@]+"${inf[@]}"} > "${m}"
    echo "no install marker in ${t}; inferred flags: ${inf[*]:-(none, review-only)}; wrote ${m}"
  fi
  flags=()
  while IFS= read -r l; do [[ -n "${l}" ]] && flags+=("${l}"); done < "${m}"
  bash "${HERE}/install.sh" ${flags[@]+"${flags[@]}"} "${t}"
done
