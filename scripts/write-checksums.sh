#!/usr/bin/env bash
# Write SHA256SUMS for the five shipped skill trees (AST02 pin surface).
# Paths are repo-relative, sorted, LC_ALL=C. SHA256SUMS itself is excluded.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="${1:-SHA256SUMS}"
export LC_ALL=C
{
  find .claude/skills/deep-code-review \
       .claude/skills/agentic-delivery \
       .claude/skills/idea-critic \
       .claude/skills/communication-structure \
       .claude/skills/contribution \
       .claude/skills/product-discovery \
       .claude/skills/agentic-ceo \
       -type f ! -name SHA256SUMS | sort
} | while IFS= read -r f; do
  sha256sum "$f"
done >"$OUT"
printf 'wrote %s (%s files)\n' "$OUT" "$(wc -l <"$OUT" | tr -d ' ')"
