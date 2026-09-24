#!/usr/bin/env bash
# pre-push-verify.sh — pre-push hook template: reruns the project's fast
# lint+unit tier on the pushed range before `git push` is allowed to proceed.
#
# WHY THIS EXISTS (issue #1093): a rebase or merge-conflict resolution is
# unverified code even when the branch's earlier commits were hook-checked —
# `git rebase --continue` does not re-invoke pre-commit on the replayed
# commits, and a conflict resolved by hand can carry a fresh lint/test defect
# that only surfaces once it reaches CI. This hook shortens that feedback
# loop locally. It is still SELF-REPORT, not the control: `git push
# --no-verify` bypasses it with no trace, and it never runs at all unless
# `core.hooksPath` points at the directory holding it. CI on the reviewed SHA
# stays the trusted gate — see
# `.claude/skills/deep-code-review/references/branch-and-merge-hygiene.md`'s
# "Self-report ≠ control" (not restated here).
#
# CONFLICT-MARKER CHECK (issue #1094): a raw `<<<<<<<`/`=======`/`>>>>>>>`
# marker left in a conflict resolution is a lint-tier failure that a cheap
# model tier can miss and DCR_PREPUSH_CMD may not catch (e.g. a lint config
# that doesn't flag it). So this hook runs `git diff --check` over the pushed
# range itself, before and independently of DCR_PREPUSH_CMD -- it fires even
# when that command is unset and DCR_PREPUSH_ALLOW_UNSET=1 lets the push
# through otherwise. Only lines reporting "leftover conflict marker" fail the
# push; other `git diff --check` whitespace complaints (trailing whitespace,
# space-before-tab) are ignored -- this hook is not a whitespace linter, and
# failing pushes on pre-existing whitespace would be friction nobody asked
# for. The check is range-scoped (base_sha..local_sha), so a marker-shaped
# line already sitting in the base never blocks. KNOWN FALSE POSITIVE: a
# Markdown setext-style H1 underlined with exactly 7 `=` characters reads as
# a conflict marker to `git diff --check`. Escape hatch: mark the file (or
# extension) `conflict-marker-size=32` in `.gitattributes`, which raises the
# marker-run threshold above what a real marker (7 chars) ever reaches and
# silences the false positive without disabling the real check.
#
# INSTALL: `install.sh --with-gates` copies this file to
# `<target>/.githooks/pre-push` (never overwrites an existing file there —
# writes `.new` instead) and prints, but does not run, the one-time opt-in:
#   git config core.hooksPath .githooks
# Without that `git config` line, Git never looks in `.githooks/` and this
# file is inert.
#
# CONFIGURATION (env vars):
#   DCR_PREPUSH_CMD             the fast tier to run before allowing the
#                                push, e.g. "make lint test-unit". Run through
#                                `sh -c` with its stdin from /dev/null (so it
#                                can never consume the ref list this hook is
#                                still reading off its own stdin), so it may
#                                be a `&&`-chain or a pipeline. A non-zero
#                                exit REFUSES the push. Whitespace-only (e.g.
#                                exported but blank) is treated the same as
#                                unset, not as an empty-but-passing command.
#   DCR_PREPUSH_ALLOW_UNSET      when DCR_PREPUSH_CMD is unset (or
#                                whitespace-only), "1" lets the push through
#                                with a warning instead of failing closed.
#                                Unset, "0", or any other value: fails closed
#                                (the default — an unconfigured hook must not
#                                silently pass every push).
#   DCR_PREPUSH_DEFAULT_BRANCH   override the remote default branch used to
#                                compute the base for a brand-new branch
#                                push. Unset -> resolved from
#                                refs/remotes/<remote>/HEAD, falling back to
#                                "main" if that ref is not set locally (run
#                                `git remote set-head <remote> --auto` once
#                                to set it).
#
# For each pushed ref this script exports BASE_SHA / HEAD_SHA (the same
# convention `dcr-gates.sh` uses) describing the commit range being pushed,
# so DCR_PREPUSH_CMD may consult them (e.g. to invoke `dcr-gates.sh` itself,
# range-scoped) — a flat command that ignores them, like `make lint
# test-unit`, works unchanged.
#
# Git feeds the pushed refs to this hook's STDIN, one line per ref:
#   <local ref> <local sha> <remote ref> <remote sha>
# A deleted ref (local sha all zeros — 40 hex for SHA-1 or 64 for a
# SHA-256 repo, matched by `^0+$`, not a hardcoded 40-char literal) is
# skipped: nothing local to verify. A brand-new branch (remote sha all
# zeros, same either-length match) has no remote-side commit to diff
# against, so BASE_SHA becomes the merge-base of the local head and the
# remote's default branch (falling back to the local branch's root commit if
# no merge-base is found — e.g. an unrelated-history remote).
#
# PUSHED-RANGE HONESTY: this hook can only ever run DCR_PREPUSH_CMD against
# the tree that is actually checked out on disk right now — it cannot check
# out each pushed ref's exact commit first. So for every non-deleted pushed
# ref it refuses (clear message, fails closed) unless the pushed local sha
# equals `git rev-parse HEAD` AND the working tree is clean; otherwise a
# "pass" would silently verify a tree that is not the code being pushed.
#
# HOLD: while `$(git rev-parse --git-common-dir)/DCR_HOLD` or a repo-root
# `.dcr-hold` exists, this hook refuses EVERY push (deletes and empty ref
# lists included) and prints the file's first line as the reason. An
# operator creates one to freeze pushes (`echo "owner review" >
# "$(git rev-parse --git-common-dir)/DCR_HOLD"`) and deletes it to lift the
# hold. The common-dir file is shared by every linked worktree and is not
# a tracked file, so a lane cannot commit it away. A lane that repoints or
# "self-heals" `core.hooksPath` to this template does not escape the hold,
# because the check is in the hook itself. Like the rest of this hook it is
# self-report: `git push --no-verify`, or a `core.hooksPath` that points
# somewhere without this hook, skips it.
#
# Exit code: 0 iff every non-deleted pushed ref's tier run passed (or was
# explicitly allowed through unset/blank). Fails closed on every other path.
set -euo pipefail

remote_name="${1:-origin}"

die() {
  printf 'pre-push-verify: %s\n' "$*" >&2
  exit 1
}

# HOLD check (see HOLD above): runs before any ref is read.
hold_common="$(git rev-parse --git-common-dir 2>/dev/null || true)"
hold_top="$(git rev-parse --show-toplevel 2>/dev/null || true)"
for hold_file in "${hold_common:+${hold_common}/DCR_HOLD}" "${hold_top:+${hold_top}/.dcr-hold}"; do
  if [ -n "${hold_file}" ] && [ -e "${hold_file}" ]; then
    hold_reason="$(head -n 1 "${hold_file}" 2>/dev/null || true)"
    die "HOLD -- ${hold_file} exists, so every push is refused until it is removed. Reason: ${hold_reason:-(none given)}"
  fi
done

# is_zero_sha <sha> — true iff <sha> is non-empty and every char is '0'.
# Matches `^0+$` without hardcoding a length, so a 40-hex SHA-1 zero id and a
# 64-hex SHA-256 zero id (a SHA-256 repo's "no commit" sentinel) both count.
is_zero_sha() {
  case "$1" in
    ''|*[!0]*) return 1 ;;
    *) return 0 ;;
  esac
}

# is_blank <str> — true iff <str> is empty or contains only whitespace.
is_blank() {
  case "$1" in
    *[![:space:]]*) return 1 ;;
    *) return 0 ;;
  esac
}

# resolve_default_branch — print the remote's default branch name.
# DCR_PREPUSH_DEFAULT_BRANCH wins if set; otherwise read
# refs/remotes/<remote>/HEAD (set by `git clone` / `git remote set-head
# --auto`); otherwise fall back to "main".
resolve_default_branch() {
  if [ -n "${DCR_PREPUSH_DEFAULT_BRANCH:-}" ]; then
    printf '%s' "${DCR_PREPUSH_DEFAULT_BRANCH}"
    return 0
  fi
  head_ref="$(git symbolic-ref -q "refs/remotes/${remote_name}/HEAD" 2>/dev/null || true)"
  if [ -n "${head_ref}" ]; then
    printf '%s' "${head_ref#refs/remotes/${remote_name}/}"
    return 0
  fi
  printf 'main'
}

print_unset_help() {
  cat >&2 <<EOF
pre-push-verify: DCR_PREPUSH_CMD is not set (or whitespace-only) -- refusing to push (fail closed).
Configure the fast tier this hook must run before every push, e.g. in your
shell profile or a project-local env file your shell sources:
  export DCR_PREPUSH_CMD="make lint test-unit"
To push anyway with no configured tier (not recommended), set:
  export DCR_PREPUSH_ALLOW_UNSET=1
EOF
}

fail=0
saw_ref=0

# Captured once, before reading any ref: the tree this hook is actually able
# to verify. Every non-deleted pushed ref is checked against this snapshot
# (see PUSHED-RANGE HONESTY above) rather than re-read per ref, so a
# DCR_PREPUSH_CMD invocation that itself dirties the tree can't change the
# answer mid-loop.
current_head="$(git rev-parse HEAD 2>/dev/null || true)"
tree_is_dirty=1
if git diff-index --quiet HEAD -- 2>/dev/null && [ -z "$(git status --porcelain 2>/dev/null)" ]; then
  tree_is_dirty=0
fi

while read -r local_ref local_sha remote_ref remote_sha; do
  [ -n "${local_ref:-}" ] || continue
  saw_ref=1

  if is_zero_sha "${local_sha}"; then
    printf 'pre-push-verify: %s is a delete -- skipping\n' "${remote_ref}"
    continue
  fi

  if [ -z "${current_head}" ] || [ "${local_sha}" != "${current_head}" ]; then
    die "refusing ${local_ref} (${local_sha}) -- this hook can only verify the tree currently checked out (HEAD is ${current_head:-unknown}), and that does not match the commit being pushed. Check out ${local_sha} (or push from that commit) before pushing, or run DCR_PREPUSH_CMD yourself against the right tree."
  fi
  if [ "${tree_is_dirty}" -eq 1 ]; then
    die "refusing ${local_ref} -- the working tree is dirty, so this hook's checked-out tree no longer matches HEAD (${current_head}), which is what it verifies. Commit or stash your changes before pushing."
  fi

  if is_zero_sha "${remote_sha}"; then
    default_branch="$(resolve_default_branch)"
    default_ref="refs/remotes/${remote_name}/${default_branch}"
    base_sha=""
    if git rev-parse --verify -q "${default_ref}" >/dev/null 2>&1; then
      base_sha="$(git merge-base "${default_ref}" "${local_sha}" 2>/dev/null || true)"
    fi
    if [ -z "${base_sha}" ]; then
      printf 'pre-push-verify: %s is a new branch with no merge-base against %s -- verifying its full local history\n' \
        "${local_ref}" "${default_ref}" >&2
      base_sha="$(git rev-list --max-parents=0 "${local_sha}" | tail -n1)"
    fi
  else
    base_sha="${remote_sha}"
  fi

  export BASE_SHA="${base_sha}"
  export HEAD_SHA="${local_sha}"

  # Conflict-marker check (#1094): runs before, and independently of, the
  # DCR_PREPUSH_CMD unset check below, so it fires even when that command is
  # unset and DCR_PREPUSH_ALLOW_UNSET=1 would otherwise let the push through.
  # `git diff --check` exits 2 on any issue (marker or whitespace) -- the
  # trailing `|| true` on its command substitution keeps `set -e` from
  # aborting on that non-zero exit, then its stdout is filtered down to
  # marker lines only.
  marker_check_output="$(git diff --check "${base_sha}" "${local_sha}" 2>/dev/null || true)"
  marker_lines="$(printf '%s\n' "${marker_check_output}" | grep -F 'leftover conflict marker' || true)"
  if [ -n "${marker_lines}" ]; then
    printf '%s\n' "${marker_lines}" >&2
    printf 'pre-push-verify: FAIL -- rejecting push of %s (leftover conflict marker)\n' "${local_ref}" >&2
    fail=1
    continue
  fi

  if is_blank "${DCR_PREPUSH_CMD:-}"; then
    if [ "${DCR_PREPUSH_ALLOW_UNSET:-0}" = "1" ]; then
      printf 'pre-push-verify: DCR_PREPUSH_CMD is unset -- allowing push through (DCR_PREPUSH_ALLOW_UNSET=1)\n' >&2
      continue
    fi
    print_unset_help
    die "DCR_PREPUSH_CMD unset (see above)"
  fi

  printf 'pre-push-verify: %s (%s..%s): running: %s\n' "${local_ref}" "${base_sha}" "${local_sha}" "${DCR_PREPUSH_CMD}"
  if ! sh -c "${DCR_PREPUSH_CMD}" </dev/null; then
    printf 'pre-push-verify: FAIL -- rejecting push of %s (DCR_PREPUSH_CMD exited non-zero)\n' "${local_ref}" >&2
    fail=1
  fi
done

# No ref lines at all (git invoking the hook with an empty stdin) is not a
# failure -- there is nothing to verify.
[ "${saw_ref}" -eq 1 ] || exit 0

[ "${fail}" -eq 0 ] || die "one or more pushed refs failed the pre-push tier (see above)"
exit 0
