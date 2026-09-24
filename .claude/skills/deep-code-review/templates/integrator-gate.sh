#!/usr/bin/env bash
# integrator-gate.sh — run the local gate on the exact merge result an
# integration branch is about to receive, and only when invoked with a
# SEPARATE gate identity, post the result as a commit status.
#
# WHY THIS EXISTS: the minimum-cost profile
# (`agentic-delivery/references/host-enforcement.md`, "Minimum-cost CI &
# token profile") puts ZERO GitHub-hosted CI on an integration branch --
# instead, branch protection restricts merge/push to one integrator identity,
# who runs this script on the merge result before merging. If that branch's
# protection needs a required status, GitHub's commit-statuses endpoint
# accepts any push-access token for any SHA (verified:
# docs.github.com/en/rest/commits/statuses, "Users with push access in a
# repository can create commit statuses for a given SHA") -- so a status
# minted by the SAME token that just pushed proves nothing about whether a
# gate ran. This script refuses to post in that case instead of quietly
# going along with it.
#
# THIS SCRIPT DOES NOT MERGE arbitrary content -- it gates the exact
# COMMITTED HEAD (the caller has already produced and committed the merge
# result). It refuses to run against a dirty tree (unstaged, staged, or
# untracked changes) in --target-branch mode: the gate must test precisely
# what HEAD names, never a `--no-commit` staging area or a working copy that
# could differ from what actually gets pushed. Two modes:
#
#   TARGET-BRANCH MODE (--target-branch): a commit status needs a SHA that
#   already exists on GitHub, and a required check on a protected branch
#   evaluates the PR/push head, not an unpublished local merge. So this mode
#   force-pushes the gated SHA (never a moving `HEAD`) to a disposable
#   scratch ref (--scratch-ref, default `refs/integrator/tmp`), gates and
#   (optionally) posts status against THAT published SHA, and only on a gate
#   pass fast-forwards the target branch to that same SHA -- a plain,
#   non-forced push, so git itself refuses a non-fast-forward (a stale or
#   diverged run can never silently overwrite history). Refuses
#   outright if any commit in the pushed range carries a `[skip ci]`/
#   `[ci skip]` marker: a skip-ci merge into the branch main CI protects
#   defeats the backstop main CI exists to be.
#
#   LEGACY / SHA MODE (--sha, no --target-branch): the caller already
#   published the merge result some other way; this script only gates and
#   (optionally) posts status on the given SHA -- no push, no fast-forward.
#
# USAGE:
#   integrator-gate.sh --repo OWNER/REPO --target-branch NAME --push-token-env VARNAME
#       [--remote NAME]                 (default: "origin"; only used to read
#                                        the current state via `git fetch` --
#                                        both pushes always go to
#                                        github.com/REPO, authenticated with
#                                        the push token, never the ambient
#                                        remote's own credentials)
#       [--scratch-ref REF]             (default: "refs/integrator/tmp")
#       [--gate-cmd CMD]                (default: "bash scripts/dcr-gates.sh"
#                                        -- the SAME tracked entry point
#                                        ci.yml calls; never a second,
#                                        undocumented local-only script)
#       [--push-token-env VARNAME]      (env var holding a token with push
#                                        access to REPO; REQUIRED with
#                                        --target-branch -- both the scratch
#                                        push and the fast-forward are
#                                        performed AS this identity via a
#                                        credential helper, so "separate
#                                        identity" is real, not a second,
#                                        unrelated variable compared by name)
#       [--gate-token-env VARNAME]      (env var HOLDING the status-posting
#                                        token; unset -> gate runs, no status
#                                        posted)
#       [--context NAME]                (commit-status context; default
#                                        "integrator-gate")
#   integrator-gate.sh --repo OWNER/REPO --sha SHA [other flags as above,
#       minus --target-branch/--remote/--scratch-ref; --push-token-env is
#       only required here alongside --gate-token-env, since nothing pushes]
#   integrator-gate.sh --selftest
#
# EXIT CODES: 0 iff the gate command passed AND (no status was requested, or
# the status posted successfully with a verified-separate identity) AND, in
# target-branch mode, the fast-forward succeeded. Non-zero on gate failure, a
# same-identity refusal, a skip-ci marker, a dirty working tree, an
# unresolvable fetch/merge-base, a non-fast-forward target, or a missing
# required argument -- fails closed, never silently skips the check it was
# asked to run.
set -euo pipefail

die() {
  printf 'integrator-gate: %s\n' "$*" >&2
  exit 1
}

GATE_CMD="bash scripts/dcr-gates.sh"
REPO=""
SHA=""
TARGET_BRANCH=""
REMOTE="origin"
SCRATCH_REF="refs/integrator/tmp"
GATE_TOKEN_ENV=""
PUSH_TOKEN_ENV=""
CONTEXT="integrator-gate"
SELFTEST=0

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --sha) SHA="$2"; shift 2 ;;
    --target-branch) TARGET_BRANCH="$2"; shift 2 ;;
    --remote) REMOTE="$2"; shift 2 ;;
    --scratch-ref) SCRATCH_REF="$2"; shift 2 ;;
    --gate-cmd) GATE_CMD="$2"; shift 2 ;;
    --gate-token-env) GATE_TOKEN_ENV="$2"; shift 2 ;;
    --push-token-env) PUSH_TOKEN_ENV="$2"; shift 2 ;;
    --context) CONTEXT="$2"; shift 2 ;;
    --selftest) SELFTEST=1; shift ;;
    *) die "unknown argument: $1" ;;
  esac
done

# require_clean_tree — refuse unless the working tree matches HEAD exactly:
# no unstaged, staged, or untracked changes. The gate must test precisely
# the committed HEAD, never a `--no-commit` staging area or a working copy
# that could differ from what actually gets pushed.
require_clean_tree() {
  [ -z "$(git status --porcelain --untracked-files=all 2>/dev/null)" ] \
    || die "REFUSE -- working tree is not clean (unstaged, staged, or untracked changes present); commit the merge result first, then re-run against that exact HEAD"
}

# skip_ci_marker_in_range <base> — true iff any commit in <base>..HEAD carries
# a `[skip ci]`/`[ci skip]` marker (case-insensitive) in its message. The
# caller guarantees <base> is non-empty (fail-closed happens before this is
# called, not inside it).
skip_ci_marker_in_range() {
  git log --format=%B "$1..HEAD" | grep -qiE '\[(skip ci|ci skip)\]'
}

# login_for_token <token> — print the `gh api user` login for <token>, or
# nothing (caller checks for empty) on any failure. Never leaks the token
# itself into output; only the resolved login.
login_for_token() {
  GH_TOKEN="$1" gh api user --jq .login 2>/dev/null || true
}

# post_status <token> <state> <description> — post a commit status to
# REPO/SHA/CONTEXT using <token>'s identity.
post_status() {
  GH_TOKEN="$1" gh api "repos/${REPO}/statuses/${SHA}" \
    -f "state=$2" -f "context=${CONTEXT}" -f "description=$3" >/dev/null
}

# push_as <token> <refspec> [--force] — push <refspec> to REPO on github.com,
# authenticated AS <token>'s identity via a credential helper that reads it
# from an env var, never argv (a URL with an embedded token would appear in
# `ps` output to any local user — the same reason login_for_token never
# prints a token). This is what makes "the push was performed by a separate,
# verified identity" a real property of the push instead of a second,
# unrelated variable merely compared by name. INTEGRATOR_GATE_TEST_REMOTE_URL
# overrides the destination — a --selftest-only escape hatch to push to a
# local bare repo instead of github.com; never set it outside a test.
push_as() {
  local token="$1" refspec="$2" force_flag=()
  [ "${3:-}" = "--force" ] && force_flag=(--force)
  local url="${INTEGRATOR_GATE_TEST_REMOTE_URL:-https://github.com/${REPO}.git}"
  # "${arr[@]+"${arr[@]}"}": bash 3.2 (macOS's default) treats an empty array
  # as unset under `set -u`, which would abort here; this form expands to
  # nothing instead (same guard this repo's other scripts use).
  GIT_PUSH_TOKEN="${token}" git -c credential.helper= \
    -c 'credential.helper=!f() { echo username=x-access-token; echo "password=$GIT_PUSH_TOKEN"; }; f' \
    push "${force_flag[@]+"${force_flag[@]}"}" "${url}" "${refspec}"
}

run_gate() {
  # shellcheck disable=SC2086
  sh -c "${GATE_CMD}"
}

main() {
  local push_token=""
  if [ -n "${TARGET_BRANCH}" ]; then
    [ -z "${SHA}" ] || die "--sha is not used with --target-branch (SHA is computed from HEAD)"
    [ -n "${REPO}" ] || die "--repo OWNER/REPO is required with --target-branch (needed to authenticate the push)"
    [ -n "${PUSH_TOKEN_ENV:-}" ] || die "--push-token-env is required with --target-branch (the push must be performed with a real, verifiable identity, not ambient git credentials)"
    push_token="${!PUSH_TOKEN_ENV:-}"
    [ -n "${push_token}" ] || die "${PUSH_TOKEN_ENV} is unset or empty"

    require_clean_tree

    # Fetch first: a stale local remote-tracking ref (from before this run)
    # must never stand in for the branch's actual current state. No
    # resolvable base after fetching is a fail-closed refusal, not a skip --
    # a skip-ci scan that silently never ran is worse than an explicit stop.
    git fetch --quiet "${REMOTE}" "${TARGET_BRANCH}" \
      || die "could not fetch ${REMOTE}/${TARGET_BRANCH} -- refusing (fail closed, no base to compare against)"
    local base
    base="$(git rev-parse --verify -q "${REMOTE}/${TARGET_BRANCH}" 2>/dev/null || true)"
    [ -n "${base}" ] || die "no ${REMOTE}/${TARGET_BRANCH} ref after fetch -- refusing (fail closed, no base to compare against)"
    base="$(git merge-base "${base}" HEAD 2>/dev/null || true)"
    [ -n "${base}" ] || die "no merge-base between ${REMOTE}/${TARGET_BRANCH} and HEAD -- refusing (fail closed, unrelated histories?)"

    if skip_ci_marker_in_range "${base}"; then
      die "REFUSE -- a commit in this range carries a [skip ci]/[ci skip] marker; never honored on ${TARGET_BRANCH}, the branch main CI protects"
    fi

    SHA="$(git rev-parse HEAD)"
    printf 'integrator-gate: pushing %s to scratch ref %s (as push-token identity)\n' "${SHA}" "${SCRATCH_REF}"
    push_as "${push_token}" "${SHA}:${SCRATCH_REF}" --force
  else
    [ -n "${SHA}" ] || die "--sha SHA is required (or use --target-branch)"
  fi

  local want_status=0 gate_token="" push_login=""
  if [ -n "${GATE_TOKEN_ENV}" ]; then
    [ -n "${REPO}" ] || die "--repo OWNER/REPO is required to post a status"
    want_status=1
    # Identity separation is verified BEFORE the gate even runs: a
    # misconfigured (same-identity) credential is refused up front, on
    # every path -- never only on the success branch.
    [ -n "${PUSH_TOKEN_ENV:-}" ] || die "--gate-token-env given without --push-token-env -- refusing to post (an unverifiable identity is not a verified-separate one)"
    [ -n "${push_token}" ] || push_token="${!PUSH_TOKEN_ENV:-}"
    gate_token="${!GATE_TOKEN_ENV:-}"
    [ -n "${gate_token}" ] || die "${GATE_TOKEN_ENV} is unset or empty"
    [ -n "${push_token}" ] || die "${PUSH_TOKEN_ENV} is unset or empty"

    local gate_login
    gate_login="$(login_for_token "${gate_token}")"
    push_login="$(login_for_token "${push_token}")"
    [ -n "${gate_login}" ] || die "could not resolve identity for --gate-token-env ${GATE_TOKEN_ENV} (gh api user failed)"
    [ -n "${push_login}" ] || die "could not resolve identity for --push-token-env ${PUSH_TOKEN_ENV} (gh api user failed)"
    if [ "${gate_login}" = "${push_login}" ]; then
      die "REFUSE -- gate token and push token are the same identity (login=${gate_login}); posting a status from this token would be forgeable, not a real gate. Use a separate, low-privilege gate credential."
    fi
  fi

  if ! run_gate; then
    printf 'integrator-gate: FAIL -- gate command exited non-zero: %s\n' "${GATE_CMD}" >&2
    [ "${want_status}" -eq 1 ] && post_status "${gate_token}" "failure" "local gate failed"
    return 1
  fi
  printf 'integrator-gate: gate PASSED: %s\n' "${GATE_CMD}"

  if [ "${want_status}" -eq 0 ]; then
    printf 'integrator-gate: no --gate-token-env given -- gate ran, no status posted\n'
  else
    post_status "${gate_token}" "success" "local gate passed"
    printf 'integrator-gate: posted success status to %s@%s (gate identity separate from push identity: %s)\n' "${REPO}" "${SHA}" "${push_login}"
  fi

  if [ -n "${TARGET_BRANCH}" ]; then
    printf 'integrator-gate: fast-forwarding %s to %s (as push-token identity)\n' "${TARGET_BRANCH}" "${SHA}"
    # Plain (non-forced) push of the exact gated SHA -- never HEAD, which
    # could have moved since the gate ran -- so git itself refuses a
    # non-fast-forward and a stale or diverged run can never silently
    # overwrite history.
    push_as "${push_token}" "${SHA}:refs/heads/${TARGET_BRANCH}"
  fi
}

# ---------------------------------------------------------------------------
# --selftest: stubs `gh` on PATH, proves the same-identity refusal, the
# different-identity success path, and that a failing gate never posts.
# ---------------------------------------------------------------------------
selftest() {
  local failures=0
  local tmp
  tmp="$(mktemp -d)"
  trap 'rm -rf "${tmp}"' RETURN

  local calls="${tmp}/calls.log"
  : > "${calls}"

  cat > "${tmp}/gh" <<'STUB'
#!/usr/bin/env bash
# Fake `gh`: `api user` returns a login keyed off GH_TOKEN's value;
# `api repos/.../statuses/...` just logs the call.
if [ "$1" = "api" ] && [ "$2" = "user" ]; then
  case "${GH_TOKEN:-}" in
    tok-alice) echo 'alice' ;;
    tok-bob)   echo 'bob' ;;
    *)         exit 1 ;;
  esac
  exit 0
fi
if [ "$1" = "api" ]; then
  echo "$2 $*" >> "$GH_STUB_CALLS"
  echo '{}'
  exit 0
fi
exit 1
STUB
  chmod +x "${tmp}/gh"
  export GH_STUB_CALLS="${calls}"
  export PATH="${tmp}:${PATH}"

  local self="$1"
  export SAME_A="tok-alice" SAME_B="tok-alice"
  export DIFF_A="tok-alice" DIFF_B="tok-bob"

  # Case 1: same identity for gate and push tokens -> refuse, no status call.
  : > "${calls}"
  if bash "${self}" --repo o/r --sha deadbeef --gate-cmd true \
      --gate-token-env SAME_A --push-token-env SAME_B; then
    echo "FAIL: same-identity case did not refuse"
    failures=$((failures + 1))
  fi
  if [ -s "${calls}" ]; then
    echo "FAIL: same-identity case posted a status (calls: $(cat "${calls}"))"
    failures=$((failures + 1))
  fi

  # Case 2: different identities -> posts a success status.
  : > "${calls}"
  if ! bash "${self}" --repo o/r --sha deadbeef --gate-cmd true \
      --gate-token-env DIFF_A --push-token-env DIFF_B; then
    echo "FAIL: different-identity case did not succeed"
    failures=$((failures + 1))
  fi
  if ! grep -q 'statuses/deadbeef' "${calls}"; then
    echo "FAIL: different-identity case did not post a status (calls: $(cat "${calls}"))"
    failures=$((failures + 1))
  fi

  # Case 3: gate command fails -> never posts, even with distinct identities.
  : > "${calls}"
  if bash "${self}" --repo o/r --sha deadbeef --gate-cmd false \
      --gate-token-env DIFF_A --push-token-env DIFF_B; then
    echo "FAIL: failing gate command reported success"
    failures=$((failures + 1))
  fi
  if grep -q 'state=success' "${calls}"; then
    echo "FAIL: failing gate command posted a success status"
    failures=$((failures + 1))
  fi

  # Case 4: --gate-token-env without --push-token-env refuses (misconfig).
  : > "${calls}"
  if bash "${self}" --repo o/r --sha deadbeef --gate-cmd true \
      --gate-token-env DIFF_A; then
    echo "FAIL: gate-token-env without push-token-env did not refuse"
    failures=$((failures + 1))
  fi

  # ---------------------------------------------------------------------
  # Cases 5-11: --target-branch mode -- a real local "remote" bare repo, no
  # network. INTEGRATOR_GATE_TEST_REMOTE_URL redirects push_as() to that
  # local bare repo instead of github.com (see push_as's own doc comment --
  # a --selftest-only escape hatch). Proves the skip-ci refusal, the
  # scratch-push + fast-forward on a gate pass, a gate failure never
  # advancing the target branch, the clean-tree requirement, the required
  # --push-token-env, and fail-closed on an unresolvable fetch/base.
  # ---------------------------------------------------------------------
  local remote_dir="${tmp}/remote.git" work_dir="${tmp}/work"
  git init --quiet --bare "${remote_dir}"
  git clone --quiet "${remote_dir}" "${work_dir}"
  (
    cd "${work_dir}"
    git config user.email test@example.com
    git config user.name "Integrator Test"
    git commit --quiet --allow-empty -m "initial"
    git branch -M development
    git push --quiet -u origin development
  )
  initial_sha="$(git -C "${work_dir}" rev-parse development)"
  export INTEGRATOR_GATE_TEST_REMOTE_URL="${remote_dir}"
  export FAKE_PUSH_TOKEN="tok-push-fake"
  tb_args=(--repo o/r --push-token-env FAKE_PUSH_TOKEN --target-branch development)

  # Case 5: a [skip ci] marker in range refuses before any push happens.
  ( cd "${work_dir}" && git commit --quiet --allow-empty -m "fix: thing [skip ci]" )
  if (cd "${work_dir}" && bash "${self}" "${tb_args[@]}" --gate-cmd true); then
    echo "FAIL: skip-ci marker did not refuse"
    failures=$((failures + 1))
  fi
  if [ "$(git -C "${remote_dir}" rev-parse development)" != "${initial_sha}" ]; then
    echo "FAIL: skip-ci refusal must not advance the target branch"
    failures=$((failures + 1))
  fi
  if git -C "${remote_dir}" rev-parse --verify -q refs/integrator/tmp >/dev/null; then
    echo "FAIL: skip-ci refusal must not push to the scratch ref either"
    failures=$((failures + 1))
  fi
  ( cd "${work_dir}" && git reset --quiet --hard "${initial_sha}" )

  # Case 6: clean commit, passing gate -> scratch ref + fast-forward both land.
  ( cd "${work_dir}" && git commit --quiet --allow-empty -m "feat: thing" )
  clean_sha="$(git -C "${work_dir}" rev-parse HEAD)"
  if ! (cd "${work_dir}" && bash "${self}" "${tb_args[@]}" --gate-cmd true); then
    echo "FAIL: clean commit with passing gate did not succeed"
    failures=$((failures + 1))
  fi
  if [ "$(git -C "${remote_dir}" rev-parse development)" != "${clean_sha}" ]; then
    echo "FAIL: passing gate must fast-forward the target branch"
    failures=$((failures + 1))
  fi
  if [ "$(git -C "${remote_dir}" rev-parse refs/integrator/tmp)" != "${clean_sha}" ]; then
    echo "FAIL: passing gate must push the scratch ref to the same SHA"
    failures=$((failures + 1))
  fi

  # Case 7: a failing gate never advances the target branch, even though the
  # scratch ref still reflects the tested (failing) commit.
  ( cd "${work_dir}" && git commit --quiet --allow-empty -m "feat: broken" )
  broken_sha="$(git -C "${work_dir}" rev-parse HEAD)"
  if (cd "${work_dir}" && bash "${self}" "${tb_args[@]}" --gate-cmd false); then
    echo "FAIL: failing gate reported success"
    failures=$((failures + 1))
  fi
  if [ "$(git -C "${remote_dir}" rev-parse development)" != "${clean_sha}" ]; then
    echo "FAIL: failing gate must not advance the target branch"
    failures=$((failures + 1))
  fi
  if [ "$(git -C "${remote_dir}" rev-parse refs/integrator/tmp)" != "${broken_sha}" ]; then
    echo "FAIL: failing gate's scratch ref must still reflect the tested commit"
    failures=$((failures + 1))
  fi
  ( cd "${work_dir}" && git reset --quiet --hard "${clean_sha}" )

  # Case 8: a dirty working tree (untracked file) refuses before touching
  # anything -- no fetch, no push, no gate run.
  : > "${work_dir}/untracked-scratch-file"
  if (cd "${work_dir}" && bash "${self}" "${tb_args[@]}" --gate-cmd true); then
    echo "FAIL: dirty working tree (untracked file) did not refuse"
    failures=$((failures + 1))
  fi
  if [ "$(git -C "${remote_dir}" rev-parse development)" != "${clean_sha}" ]; then
    echo "FAIL: dirty-tree refusal must not advance the target branch"
    failures=$((failures + 1))
  fi
  rm -f "${work_dir}/untracked-scratch-file"

  # Case 9: --target-branch without --push-token-env refuses (the push must
  # be a real, verifiable identity, never ambient git credentials).
  if (cd "${work_dir}" && bash "${self}" --repo o/r --target-branch development --gate-cmd true); then
    echo "FAIL: --target-branch without --push-token-env did not refuse"
    failures=$((failures + 1))
  fi

  # Case 10: an unresolvable fetch (bogus remote name) fails closed instead
  # of silently skipping the skip-ci scan.
  if (cd "${work_dir}" && bash "${self}" --repo o/r --push-token-env FAKE_PUSH_TOKEN \
      --target-branch development --remote does-not-exist --gate-cmd true); then
    echo "FAIL: unresolvable fetch did not refuse (fail closed)"
    failures=$((failures + 1))
  fi
  if [ "$(git -C "${remote_dir}" rev-parse development)" != "${clean_sha}" ]; then
    echo "FAIL: unresolvable-fetch refusal must not advance the target branch"
    failures=$((failures + 1))
  fi

  if [ "${failures}" -eq 0 ]; then
    printf 'integrator-gate: SELFTEST OK: 10/10 cases passed\n'
    return 0
  fi
  printf 'integrator-gate: SELFTEST FAILED: %d case(s)\n' "${failures}"
  return 1
}

if [ "${SELFTEST}" -eq 1 ]; then
  # Resolve an ABSOLUTE self path: selftest() cds into a scratch work dir
  # before invoking this script again, so a relative $0 (e.g. run as
  # `bash templates/integrator-gate.sh --selftest` from a different cwd,
  # including this repo's own root) would silently break, not error --
  # bash would just fail to find it.
  self_abs="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  selftest "${self_abs}"
  exit $?
fi

main
