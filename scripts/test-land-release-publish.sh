#!/usr/bin/env bash
# Test: `land-release.sh publish` (stub gh, fake bare remote under $TMPDIR): no-op when not on main, first run creates
# the release, a re-run updates notes, an existing tag is never moved, release_every batches.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/dcr-test-publish.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null RELEASE_DATE=2026-01-01
fail=0
ok() { if [ "$1" -eq 0 ]; then echo "PASS  $2"; else echo "FAIL  $2"; fail=1; fi; }
R="$WORK/repo"; mkdir "$R"
g() { git -C "$R" -c user.email=t@example.com -c user.name=T "$@"; }
git init -q --bare -b main "$WORK/origin.git"
rsync -a --exclude=.git --exclude=.claude/worktrees --exclude=changelog.d "$ROOT/" "$R/"
git -C "$R" init -q -b main; g remote add origin "$WORK/origin.git"
g add -A; g commit -q -m base; g push -q origin main
V0=$(cat "$R/.claude/skills/deep-code-review/VERSION"); exp="${V0%%.*}.$(( $(echo "$V0" | cut -d. -f2) + 1)).0"
# stub gh: logs argv; `release view` succeeds only after a create; copies --notes-file content
cat >"$WORK/gh" <<'S'
#!/usr/bin/env bash
echo "$*" >>"$STUB_LOG"
case "$1 $2" in
  "release view") [ -f "$STUB_LOG.created" ] ;;
  "release create") touch "$STUB_LOG.created"; shift 2; while [ $# -gt 0 ]; do [ "$1" = --notes-file ] && cp "$2" "$STUB_LOG.notes"; shift; done ;;
  "release edit") shift 2; while [ $# -gt 0 ]; do [ "$1" = --notes-file ] && cp "$2" "$STUB_LOG.notes"; shift; done ;;
esac
S
chmod +x "$WORK/gh"; export REPO_URL=https://github.com/acme/example GH="$WORK/gh" STUB_LOG="$WORK/gh.log"
pub() { (cd "$R" && bash scripts/land-release.sh publish 2>&1); }

g checkout -q -b lane main
mkdir "$R/changelog.d"; printf '### Added\n- publish test.\n' >"$R/changelog.d/t.md"; g add -A; g commit -q -m lane
(cd "$R" && bash scripts/land-release.sh) >/dev/null
out=$(pub); rc=$?
[ $rc -eq 0 ] && [ ! -e "$STUB_LOG" ] && [ -z "$(git -C "$WORK/origin.git" tag -l)" ]; ok $? "not on origin/main: no-op, exit 0, no gh call, no tag"
g push -q origin HEAD:main; REL=$(g rev-parse HEAD)
out=$(pub); rc=$?
[ $rc -eq 0 ] && grep -q "^release create v$exp --title Perun v$exp --notes-file .* --verify-tag --latest$" "$STUB_LOG"; ok $? "first publish creates the release with the required flags"
[ "$(git -C "$WORK/origin.git" rev-parse "v$exp^{commit}")" = "$REL" ]; ok $? "annotated tag pushed at the release commit"
grep -q 'publish test' "$STUB_LOG.notes" && grep -q 'Full changelog: https://github.com/acme/example/blob/main/CHANGELOG.md' "$STUB_LOG.notes" && ! grep -q '^## \[' "$STUB_LOG.notes"; ok $? "notes = CHANGELOG section for $exp plus full-changelog link"
out=$(pub); rc=$?
[ $rc -eq 0 ] && grep -q "^release edit v$exp --notes-file" "$STUB_LOG" && [ "$(grep -c '^release create' "$STUB_LOG")" -eq 1 ]; ok $? "re-run updates notes (no second create), exit 0"
# gh failure on first run leaves a tag but no release; the re-run completes it
git -C "$WORK/origin.git" tag -d "v$exp" >/dev/null; g tag -d "v$exp" >/dev/null; rm -f "$STUB_LOG" "$STUB_LOG.created"
out=$(GH=false pub); rc=$?
[ $rc -ne 0 ] && [ -n "$(git -C "$WORK/origin.git" tag -l "v$exp")" ]; ok $? "gh failure on first run exits non-zero, tag already pushed"
out=$(pub); rc=$?
[ $rc -eq 0 ] && grep -q "^release create v$exp" "$STUB_LOG"; ok $? "re-run after gh failure creates the release"
# missing CHANGELOG section is refused
git -C "$WORK/origin.git" tag -d "v$exp" >/dev/null; g tag -d "v$exp" >/dev/null; rm -f "$STUB_LOG" "$STUB_LOG.created"
sed -i.bak "s/^## \\[$exp\\]/## [x$exp]/" "$R/CHANGELOG.md"; g commit -qam nosection; g push -q origin HEAD:main
out=$(pub); rc=$?
[ $rc -eq 2 ] && grep -q "no CHANGELOG section for $exp" <<<"$out" && [ ! -e "$STUB_LOG" ]; ok $? "missing CHANGELOG section refused (exit 2), no gh create"
g reset -q --hard HEAD~1; g push -q -f origin HEAD:main 2>/dev/null
# existing tag never moved: remote tag on another commit refuses, tag stays
git -C "$WORK/origin.git" tag -d "v$exp" >/dev/null; git -C "$WORK/origin.git" tag "v$exp" "$(g rev-parse HEAD~1)"
g tag -d "v$exp" >/dev/null
out=$(pub); rc=$?
[ $rc -ne 0 ] && [ "$(git -C "$WORK/origin.git" rev-parse "v$exp")" = "$(g rev-parse HEAD~1)" ]; ok $? "remote tag on another commit is refused and left in place"
# release_every: minor not a multiple of N skips tag and release
git -C "$WORK/origin.git" tag -d "v$exp" >/dev/null; g tag -d "v$exp" >/dev/null 2>&1; rm -f "$STUB_LOG"
mkdir -p "$R/.perun"; echo '{"release_every": 1000000}' >"$R/.perun/policy.json"
out=$(pub); rc=$?
[ $rc -eq 0 ] && grep -q 'release_every=1000000, skipping' <<<"$out" && [ ! -e "$STUB_LOG" ] && [ -z "$(git -C "$WORK/origin.git" tag -l)" ]; ok $? "release_every=N skips non-multiple minors"
echo '{"release_every": 0}' >"$R/.perun/policy.json"
pub >/dev/null; [ $? -ne 0 ]; ok $? "release_every=0 fails closed"
exit $fail
