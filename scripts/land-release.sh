#!/usr/bin/env bash
# land-release.sh [--regen] — stamp a release at merge time so parallel lanes never collide on a version.
#
# Lanes do NOT bump. A lane adds changelog.d/<slug>.md (the body that goes under the release heading,
# e.g. "### Added" + bullets) and, before pushing, runs `land-release.sh --regen` to refresh the
# generated artifacts (INDEX.md files, SHA256SUMS, size-budgets.tsv rows) so its own CI stays green.
#
# Land mode (no flag), run on the lane branch at merge time, serialized by a lock under the git common
# dir (shared by every worktree): merges origin/main (generated-file conflicts are resolved by
# regenerating; any other conflict aborts), takes the next minor version from main's VERSION, stamps the
# lockstep set (3 VERSION files, 3 SKILL.md metadata.version, plugin.json), folds every fragment into
# CHANGELOG.md under a new heading, deletes the fragments, regenerates, and makes one commit. Push/merge
# is the caller's. A lane that lands second just re-runs this: no rebump by hand, no force-push.
#
# size-budgets.tsv rows are rewritten to current sizes; a raise still needs the `size-budget-raise:`
# marker in the fragment (enforced by `ci-gates.sh size-ratchet`).
# Env: REMOTE (origin), BASE_BRANCH (main), RELEASE_DATE (today). Exit 0 ok, 1 failure, 2 usage.
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE=${REMOTE:-origin} BASE_BRANCH=${BASE_BRANCH:-main}
mode=land
case "${1:-}" in "") ;; --regen) mode=regen ;; *) echo "usage: land-release.sh [--regen]" >&2; exit 2 ;; esac

LOCK="$(git rev-parse --git-common-dir)/land-release.lock"
mkdir "$LOCK" 2>/dev/null || { echo "land-release: lock held ($LOCK); another land is running" >&2; exit 1; }
trap 'rmdir "$LOCK"' EXIT

GENERATED='SHA256SUMS|scripts/size-budgets.tsv|\.claude/skills/(.*/)?INDEX\.md'
SKILLS="deep-code-review agentic-delivery idea-critic"

regen() {
  # Rewrite size rows in place (comments, order and the hand-kept README.md row survive): existing skill
  # rows take the current size, rows of deleted files drop, new files append.
  find .claude/skills \( -name SKILL.md -o -path '*/references/*.md' \) -type f | LC_ALL=C sort |
    while IFS= read -r f; do printf '%s\t%s\n' "$f" "$(LC_ALL=C wc -c <"$f" | tr -d '[:space:]')"; done >sizes.new
  awk -F'\t' -v OFS='\t' 'NR==FNR{sz[$1]=$2; next}
    /^#/||/^$/{print; next}
    $1 in sz{print $1, sz[$1]; next}
    $1 !~ /^\.claude\/skills\//{print}' sizes.new scripts/size-budgets.tsv >scripts/size-budgets.new
  awk -F'\t' 'NR==FNR{have[$1]=1; next} !($1 in have)' scripts/size-budgets.new sizes.new >>scripts/size-budgets.new
  mv scripts/size-budgets.new scripts/size-budgets.tsv; rm sizes.new
  python3 scripts/skill_index.py >/dev/null
  bash scripts/write-checksums.sh >/dev/null   # pin LAST, after every skill-tree edit
}

if [ "$mode" = regen ]; then regen; exit 0; fi

[ -z "$(git status --porcelain)" ] || { echo "land-release: dirty tree" >&2; exit 1; }
git fetch -q "$REMOTE" "$BASE_BRANCH"
if ! git merge -q --no-edit "$REMOTE/$BASE_BRANCH" >/dev/null 2>&1; then
  conflicts=$(git diff --name-only --diff-filter=U)
  bad=$(printf '%s\n' "$conflicts" | grep -vE "^($GENERATED)$" || true)
  [ -z "$bad" ] || { git merge --abort; printf 'land-release: non-generated conflicts:\n%s\n' "$bad" >&2; exit 1; }
  for f in $conflicts; do git checkout -q --theirs -- "$f"; git add "$f"; done   # regenerated below
  git commit -q --no-edit
fi

shopt -s nullglob; frags=(changelog.d/*.md); shopt -u nullglob
[ "${#frags[@]}" -gt 0 ] || { echo "land-release: no changelog.d/*.md fragment; nothing to land" >&2; exit 1; }

IFS=. read -r maj min _ <.claude/skills/deep-code-review/VERSION
ver="$maj.$((min + 1)).0"
for s in $SKILLS; do
  d=.claude/skills/$s
  echo "$ver" >"$d/VERSION"
  sed -E "s/^(  version: \")[0-9.]+(\")/\1$ver\2/" "$d/SKILL.md" >"$d/SKILL.md.new" && mv "$d/SKILL.md.new" "$d/SKILL.md"
done
sed -E "s/^(  \"version\": \")[0-9.]+(\")/\1$ver\2/" .claude-plugin/plugin.json >p.new && mv p.new .claude-plugin/plugin.json

{ printf '## [%s] — %s\n\n' "$ver" "${RELEASE_DATE:-$(date +%F)}"
  for f in "${frags[@]}"; do cat "$f"; echo; done
} >release.new
awk 'NR==FNR{r=r $0 "\n"; next} !d && /^## /{printf "%s", r; d=1} {print}' release.new CHANGELOG.md >CHANGELOG.new
mv CHANGELOG.new CHANGELOG.md; rm release.new
git rm -q "${frags[@]}"
regen
git add -A CHANGELOG.md .claude-plugin .claude/skills SHA256SUMS scripts/size-budgets.tsv
git commit -q -m "release: $ver (stamped at land time)"
echo "land-release: $ver"
