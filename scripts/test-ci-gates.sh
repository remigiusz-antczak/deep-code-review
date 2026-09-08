#!/usr/bin/env bash
#
# Contract self-tests for scripts/ci-gates.sh (Deep Code Review CI gates).
#
# Exercises scripts/ci-gates.sh with the subcommands `privacy`, `routing`,
# `version`, and `install`. That production helper exists at the current HEAD,
# so every case is expected to PASS (GREEN) here. The same cases still prove RED
# during TDD: run against a checkout without the helper (or one whose behaviour
# regresses) they FAIL. Real exit codes are always preserved — no `|| true`, no
# always-success fallback, and no pipeline that swallows the exit status of the
# command under test.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GATES="$ROOT/scripts/ci-gates.sh"
WORK="$ROOT/.dcr-test-work"

# Documented SKILL.md size budget (bytes). Exceeding it must WARN, not fail.
SKILL_BUDGET=1024

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

rm -rf "$WORK"
mkdir -p "$WORK"

pass=0
fail=0
GATE_RC=0

# record <0|1> <label>  — 0 == case passed, non-zero == case failed.
record() {
  if [ "$1" -eq 0 ]; then
    printf 'PASS  %s\n' "$2"
    pass=$((pass + 1))
  else
    printf 'FAIL  %s\n' "$2"
    fail=$((fail + 1))
  fi
}

# gate <cmd...> — run the tested helper through bash, capturing its REAL exit code into
# GATE_RC without masking it. Output is kept for postcondition inspection.
gate() {
  if bash "$@" >"$WORK/last.log" 2>&1; then
    GATE_RC=0
  else
    GATE_RC=$?
  fi
}

# ---------------------------------------------------------------------------
# precondition — the helper under test must exist as a regular file.
#
# Without this guard a missing scripts/ci-gates.sh would silently corrupt the
# result: a command that cannot run exits non-zero, and every rejection case
# reads a non-zero exit as success. The RED harness would then falsely go
# green while proving nothing. Fail loudly and early instead, so a missing
# helper makes this harness FAIL.
# ---------------------------------------------------------------------------
if [ ! -f "$GATES" ]; then
  printf 'PRECONDITION FAIL: helper file not found: %s\n' "$GATES" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# privacy — banlist hygiene and secret detection
# ---------------------------------------------------------------------------

mkdir -p "$WORK/scan"
# Build the planted secret at runtime so this harness file itself never carries
# a literal match for the repo's pre-commit secret grep.
planted="AKIA$(printf 'X%.0s' {1..16})"
printf 'aws_key = %s\n' "$planted" >"$WORK/scan/planted.txt"

# A valid banlist: comment plus a real pattern (the pattern text below does not
# itself match AKIA[0-9A-Z]{16}, so it is safe to commit).
printf '# known secret shapes\nAKIA[0-9A-Z]{16}\n' >"$WORK/banlist.valid"
: >"$WORK/banlist.empty"
printf '# only comments\n#   nothing actionable\n' >"$WORK/banlist.comments"

gate "$GATES" privacy --banlist "$WORK/banlist.empty" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then record 0 "privacy: reject empty banlist"; else record 1 "privacy: reject empty banlist"; fi

gate "$GATES" privacy --banlist "$WORK/banlist.comments" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then record 0 "privacy: reject all-comment banlist"; else record 1 "privacy: reject all-comment banlist"; fi

gate "$GATES" privacy --banlist "$WORK/banlist.valid" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then record 0 "privacy: detect planted banned secret"; else record 1 "privacy: detect planted banned secret"; fi

# A banlist carrying an invalid extended regular expression (a lone opening
# bracket has no closing `]`). The gate must fail closed: an unusable pattern
# cannot be silently skipped, because a skipped pattern scans nothing and lets a
# banned string through undetected. Reject the run instead.
#
# It must also fail *privately*: the banlist may hold real secret shapes, so a
# diagnostic that echoes the offending pattern would leak banlist content into
# CI logs. The planted invalid pattern here is a lone opening bracket `[`; the
# gate must therefore (a) exit non-zero, (b) say the offending content was
# withheld, and (c) never reproduce the `[` in its output. Fixed-string greps
# (-F) are used so the bracket is matched literally, not as a regex.
printf '# broken pattern below\n[\n' >"$WORK/banlist.badregex"
gate "$GATES" privacy --banlist "$WORK/banlist.badregex" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ] \
  && grep -qiF 'content withheld' "$WORK/last.log" \
  && ! grep -qF '[' "$WORK/last.log"; then
  record 0 "privacy: reject banlist with invalid ERE (fail closed, without disclosing banlist content)"
else
  record 1 "privacy: reject banlist with invalid ERE (fail closed, without disclosing banlist content)"
fi

# The documented optional local override: a primary .banlist.txt is loaded
# together with its sibling .banlist.local.txt when that sibling exists, so an
# operator can extend the committed policy locally without editing it. This case
# proves BOTH files are loaded, not just the primary. The primary here carries a
# single valid pattern that deliberately does NOT match the planted secret, while
# the sibling local file carries the banned shape (the same AKIA[0-9A-Z]{16} regex
# already used above). If the gate read only the primary, the planted secret would
# slip through and the scan would report clean; the run must reject only because
# the sibling local banlist is loaded alongside the primary. Content stays hidden:
# no secret literal is written — the planted fixture is the runtime-built one from
# above, and only the regex shape (never a live key) is placed in the local file.
localdir="$WORK/banlist-local"
mkdir -p "$localdir"
printf '# primary policy (nonmatching)\nNOMATCH_[A-Z]+\n' >"$localdir/.banlist.txt"
printf 'AKIA[0-9A-Z]{16}\n' >"$localdir/.banlist.local.txt"

gate "$GATES" privacy --banlist "$localdir/.banlist.txt" "$WORK/scan"
if [ "$GATE_RC" -ne 0 ]; then
  record 0 "privacy: load optional sibling .banlist.local.txt alongside primary .banlist.txt"
else
  record 1 "privacy: load optional sibling .banlist.local.txt alongside primary .banlist.txt"
fi

# ---------------------------------------------------------------------------
# routing — every references/*.md must be routed from SKILL.md
# ---------------------------------------------------------------------------

unrouted="$WORK/skill-unrouted"
mkdir -p "$unrouted/references"
printf '# Skill\n\nSee references/routed.md for depth.\n' >"$unrouted/SKILL.md"
printf 'routed depth\n' >"$unrouted/references/routed.md"
printf 'orphaned depth\n' >"$unrouted/references/unrouted.md"

gate "$GATES" routing "$unrouted"
if [ "$GATE_RC" -ne 0 ]; then record 0 "routing: reject unrouted reference"; else record 1 "routing: reject unrouted reference"; fi

# Basenames must be matched literally, not as regexes. The reference file is
# references/literal.md, but SKILL.md only mentions references/literalXmd. If the
# gate treats the basename as a pattern, the `.` in `literal.md` matches the `X`
# in `literalXmd` and the orphan is falsely considered routed. A literal match
# sees no mention of literal.md, so the reference is unrouted and must be
# rejected.
literal="$WORK/skill-literal"
mkdir -p "$literal/references"
printf '# Skill\n\nSee references/literalXmd for depth.\n' >"$literal/SKILL.md"
printf 'literal depth\n' >"$literal/references/literal.md"

gate "$GATES" routing "$literal"
if [ "$GATE_RC" -ne 0 ]; then record 0 "routing: reject reference matched only via regex-meta basename"; else record 1 "routing: reject reference matched only via regex-meta basename"; fi

# Oversized SKILL.md that is otherwise well-routed: must PASS but emit a warning.
big="$WORK/skill-big"
mkdir -p "$big/references"
printf '# Skill\n\nSee references/routed.md for depth.\n' >"$big/SKILL.md"
head -c $((SKILL_BUDGET * 4)) </dev/zero | tr '\0' 'x' >>"$big/SKILL.md"
printf 'routed depth\n' >"$big/references/routed.md"

gate "$GATES" routing --max-bytes "$SKILL_BUDGET" "$big"
if [ "$GATE_RC" -eq 0 ] && grep -qi 'warn' "$WORK/last.log"; then
  record 0 "routing: warn (non-failing) when SKILL.md exceeds size budget"
else
  record 1 "routing: warn (non-failing) when SKILL.md exceeds size budget"
fi

# ---------------------------------------------------------------------------
# version — VERSION format and matching CHANGELOG heading
# ---------------------------------------------------------------------------

vbad="$WORK/ver-malformed"
mkdir -p "$vbad"
printf 'banana\n' >"$vbad/VERSION"
printf '# Changelog\n\n## banana\n' >"$vbad/CHANGELOG.md"

gate "$GATES" version "$vbad"
if [ "$GATE_RC" -ne 0 ]; then record 0 "version: reject malformed VERSION"; else record 1 "version: reject malformed VERSION"; fi

vnochg="$WORK/ver-nochangelog"
mkdir -p "$vnochg"
printf '1.2.3\n' >"$vnochg/VERSION"
printf '# Changelog\n\n## 9.9.9 - earlier\n' >"$vnochg/CHANGELOG.md"

gate "$GATES" version "$vnochg"
if [ "$GATE_RC" -ne 0 ]; then record 0 "version: reject missing matching CHANGELOG heading"; else record 1 "version: reject missing matching CHANGELOG heading"; fi

# ---------------------------------------------------------------------------
# install — behaviour of the real installer against the real repo
# ---------------------------------------------------------------------------

skill_rel=".claude/skills/deep-code-review"
# The installer vendors the repository's standards index into the skill. Pin the
# exact source path and destination name — no ls/head pipeline picking an
# arbitrary reference, and no always-success fallback that could mask a missing
# source. If the source is absent, cmp below fails and the case records FAIL.
ref_src="$ROOT/docs/standards-index.md"
ref_name="standards-index.md"

# 1) installer overwrites a placeholder reference with the real docs content.
dest1="$WORK/dest-placeholder"
mkdir -p "$dest1/$skill_rel/references"
printf 'PLACEHOLDER\n' >"$dest1/$skill_rel/references/$ref_name"
gate "$GATES" install --src "$ROOT" --dest "$dest1" --mode claude
installed="$dest1/$skill_rel/references/$ref_name"
if [ "$GATE_RC" -eq 0 ] && ! grep -q 'PLACEHOLDER' "$installed" && cmp -s "$installed" "$ref_src"; then
  record 0 "install: overwrite placeholder reference with real docs content"
else
  record 1 "install: overwrite placeholder reference with real docs content"
fi

# 2) claude-only mode preserves a preexisting AGENTS.md and creates no
#    cursor/agents paths of its own.
dest2="$WORK/dest-claude-only"
mkdir -p "$dest2"
printf 'PREEXISTING-AGENTS' >"$dest2/AGENTS.md"
gate "$GATES" install --src "$ROOT" --dest "$dest2" --mode claude
if [ "$GATE_RC" -eq 0 ] \
  && [ "$(cat "$dest2/AGENTS.md")" = "PREEXISTING-AGENTS" ] \
  && [ ! -e "$dest2/.cursor" ] \
  && [ ! -e "$dest2/.cursorrules" ] \
  && [ ! -e "$dest2/.agents" ]; then
  record 0 "install: claude-only preserves AGENTS.md, no cursor/agents paths"
else
  record 1 "install: claude-only preserves AGENTS.md, no cursor/agents paths"
fi

# 2a) minimal mode on a fresh destination installs the claude skill only and
#     creates none of the cursor/agents/codex skill roots.
dest_min="$WORK/dest-minimal"
mkdir -p "$dest_min"
gate "$GATES" install --src "$ROOT" --dest "$dest_min" --mode minimal
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_min/$skill_rel/SKILL.md" ] \
  && [ ! -e "$dest_min/.cursor" ] \
  && [ ! -e "$dest_min/.agents" ] \
  && [ ! -e "$dest_min/.codex" ]; then
  record 0 "install: minimal creates claude skill, no cursor/agents/codex roots"
else
  record 1 "install: minimal creates claude skill, no cursor/agents/codex roots"
fi

# 2b) codex mode on a fresh destination installs the claude skill plus the
#     cursor/agents/codex skill roots and leaves the managed AGENTS.md pointer.
#     Assert the block sentinels install.sh actually writes — the
#     `deep-code-review:begin` marker it keys its idempotent re-install replace
#     on, plus the `Installed:` and `Agent-agnostic` lines — not merely that
#     AGENTS.md is non-empty (a non-empty but unstamped file would still pass a
#     bare `-s` check while breaking re-install).
dest_codex="$WORK/dest-codex"
mkdir -p "$dest_codex"
gate "$GATES" install --src "$ROOT" --dest "$dest_codex" --mode codex
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_codex/$skill_rel/SKILL.md" ] \
  && [ -e "$dest_codex/.cursor" ] \
  && [ -e "$dest_codex/.agents" ] \
  && [ -e "$dest_codex/.codex" ] \
  && [ -s "$dest_codex/AGENTS.md" ] \
  && grep -q 'deep-code-review:begin' "$dest_codex/AGENTS.md" \
  && grep -q 'Installed:' "$dest_codex/AGENTS.md" \
  && grep -q 'Agent-agnostic' "$dest_codex/AGENTS.md"; then
  record 0 "install: codex creates claude/cursor/agents/codex roots + stamped AGENTS.md pointer"
else
  record 1 "install: codex creates claude/cursor/agents/codex roots + stamped AGENTS.md pointer"
fi

# 2c) full (agent-agnostic default) mode: the bare `install.sh TARGET` path the
#     CI used to run first and the helper's own `full|default` branch — untested
#     until now. It must create the claude + cursor + agents skill roots and a
#     stamped AGENTS.md, but NOT the codex root. A second install must then leave
#     exactly ONE managed block (idempotent replace via the marker), never a
#     duplicate appended block — the same re-install hygiene the collision-free
#     backup fix protects.
dest_full="$WORK/dest-full"
mkdir -p "$dest_full"
gate "$GATES" install --src "$ROOT" --dest "$dest_full" --mode full
rc_full_first=$GATE_RC
gate "$GATES" install --src "$ROOT" --dest "$dest_full" --mode full
n_blocks=0
[ -f "$dest_full/AGENTS.md" ] && n_blocks="$(grep -c 'deep-code-review:begin' "$dest_full/AGENTS.md")"
if [ "$rc_full_first" -eq 0 ] && [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_full/$skill_rel/SKILL.md" ] \
  && [ -e "$dest_full/.cursor" ] \
  && [ -e "$dest_full/.agents" ] \
  && [ ! -e "$dest_full/.codex" ] \
  && grep -q 'Installed:' "$dest_full/AGENTS.md" \
  && grep -q 'Agent-agnostic' "$dest_full/AGENTS.md" \
  && [ "$n_blocks" -eq 1 ]; then
  record 0 "install: full default creates claude/cursor/agents (no codex) + one idempotent AGENTS.md block"
else
  record 1 "install: full default creates claude/cursor/agents (no codex) + one idempotent AGENTS.md block"
fi

# 3) rapid repeated installs create distinct backups of the prior skill.
dest3="$WORK/dest-backups"
mkdir -p "$dest3/$skill_rel"
printf 'v0\n' >"$dest3/$skill_rel/SKILL.md"
gate "$GATES" install --src "$ROOT" --dest "$dest3" --mode claude
rc_first=$GATE_RC
gate "$GATES" install --src "$ROOT" --dest "$dest3" --mode claude
rc_second=$GATE_RC
if [ "$rc_first" -eq 0 ] && [ "$rc_second" -eq 0 ]; then
  backups=( "$dest3/.claude/skill-backups/deep-code-review-"* )
  n_backups=0
  for b in "${backups[@]}"; do
    [ -e "$b" ] && n_backups=$((n_backups + 1))
  done
  if [ "$n_backups" -ge 2 ]; then
    record 0 "install: rapid repeated installs create distinct backups"
  else
    record 1 "install: rapid repeated installs create distinct backups"
  fi
else
  record 1 "install: rapid repeated installs create distinct backups"
fi

# 4) default/full review-only must NOT install overlay skills.
dest_no_ov="$WORK/dest-no-overlay"
mkdir -p "$dest_no_ov"
gate "$GATES" install --src "$ROOT" --dest "$dest_no_ov" --mode full
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_no_ov/$skill_rel/SKILL.md" ] \
  && [ ! -e "$dest_no_ov/.claude/skills/agentic-delivery" ] \
  && [ ! -e "$dest_no_ov/.claude/skills/idea-critic" ]; then
  record 0 "install: default full is review-only (no overlay skills)"
else
  record 1 "install: default full is review-only (no overlay skills)"
fi

# 5) overlays mode installs review + agentic-delivery + idea-critic and an overlay stamp.
dest_ov="$WORK/dest-overlays"
mkdir -p "$dest_ov"
gate "$GATES" install --src "$ROOT" --dest "$dest_ov" --mode overlays
if [ "$GATE_RC" -eq 0 ] \
  && [ -f "$dest_ov/$skill_rel/SKILL.md" ] \
  && [ -f "$dest_ov/.claude/skills/agentic-delivery/SKILL.md" ] \
  && [ -f "$dest_ov/.claude/skills/idea-critic/SKILL.md" ] \
  && grep -q 'dcr-overlays:begin' "$dest_ov/AGENTS.md" \
  && grep -q 'agentic-delivery' "$dest_ov/AGENTS.md"; then
  record 0 "install: overlays mode copies delivery+critic and stamps AGENTS.md"
else
  record 1 "install: overlays mode copies delivery+critic and stamps AGENTS.md"
fi

# 6) --recommend inspects and writes nothing.
dest_rec="$WORK/dest-recommend"
mkdir -p "$dest_rec"
gate "$GATES" install --src "$ROOT" --dest "$dest_rec" --mode recommend
if [ "$GATE_RC" -eq 0 ] \
  && [ ! -e "$dest_rec/.claude" ] \
  && [ ! -e "$dest_rec/AGENTS.md" ] \
  && grep -qi 'recommend' "$WORK/last.log"; then
  record 0 "install: recommend is read-only"
else
  record 1 "install: recommend is read-only"
fi

# 7) --recommend treats archived Superpowers notes as history, not a live pack.
python3 - "$ROOT/scripts/recommend-overlays.py" "$WORK" <<'PY' || true
import importlib.util, sys, json
from pathlib import Path
mod_path = Path(sys.argv[1])
work = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("recommend", mod_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

hist = work / "hist-superpowers"
(hist / "docs" / "superpowers" / "plans").mkdir(parents=True)
(hist / "docs" / "superpowers" / "plans" / "old.md").write_text("archive\n")
(hist / "package.json").write_text("{}\n")
rec = mod.recommend(hist)
Path(work / "rec-hist.json").write_text(json.dumps(rec))

live = work / "live-superpowers"
(live / ".claude" / "skills" / "superpowers").mkdir(parents=True)
(live / ".claude" / "skills" / "superpowers" / "SKILL.md").write_text("# Superpowers\n")
(live / "package.json").write_text("{}\n")
rec2 = mod.recommend(live)
Path(work / "rec-live.json").write_text(json.dumps(rec2))
PY
if python3 - "$WORK" <<'PY'
import json, sys
from pathlib import Path
work = Path(sys.argv[1])
hist = json.loads((work / "rec-hist.json").read_text())
live = json.loads((work / "rec-live.json").read_text())
ok = (hist.get("other_delivery") is False) and ("agentic-delivery" in hist.get("skills", []))
ok = ok and (live.get("other_delivery") is True) and ("agentic-delivery" not in live.get("skills", []))
sys.exit(0 if ok else 1)
PY
then
  record 0 "recommend: archive superpowers is not a live delivery pack"
else
  record 1 "recommend: archive superpowers is not a live delivery pack"
fi

# 8) --recommend also treats a live CUSTOM delivery pack (a gated-delivery skill
#    under a live skill root, or an already-installed agentic-delivery) as
#    another delivery OS, so --full does not stack a second one. A live
#    review-only skill and archived delivery notes must NOT suppress. A SKILL.md
#    that is a symlink or a FIFO must be skipped (no hang, no out-of-tree read).
#    Fictional skill names only (factory / security-review); no real product names.
python3 - "$ROOT/scripts/recommend-overlays.py" "$WORK" <<'PY' || true
import importlib.util, sys, json, os, signal
from pathlib import Path
mod_path = Path(sys.argv[1])
work = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("recommend", mod_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def skill(root, rel, body):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)

# A) live custom delivery skill under .claude/skills/ — must suppress.
a = work / "cust-deliver"
skill(a, ".claude/skills/factory/SKILL.md",
      "---\nname: factory\n"
      "description: Gated multi-role delivery overlay — software-house pattern, "
      "gates G0 through G10, one writer per worktree.\n---\n"
      "# Factory\nA gated delivery OS. G0 intake, G10 learn; independent QA and security.\n")
(a / "package.json").write_text("{}\n")
Path(work / "rec-cust-deliver.json").write_text(json.dumps(mod.recommend(a)))

# B) live review-only skill under .claude/skills/ — must NOT suppress.
b = work / "cust-review"
skill(b, ".claude/skills/security-review/SKILL.md",
      "---\nname: security-review\n"
      "description: Audit code for vulnerabilities and unsafe patterns; produce a "
      "findings report. Read-only.\n---\n"
      "# Security Review\nAn audit skill. Inspect auth, input handling, and "
      "dependencies. A review of code, not a pipeline that builds or releases it.\n")
(b / "package.json").write_text("{}\n")
Path(work / "rec-cust-review.json").write_text(json.dumps(mod.recommend(b)))

# C) already-installed agentic-delivery stub — counts as a live delivery pack.
c = work / "cust-installed"
skill(c, ".claude/skills/agentic-delivery/SKILL.md",
      "---\nname: agentic-delivery\ndescription: Gated delivery overlay "
      "(installed stub).\n---\n# Agentic Delivery\nInstalled delivery overlay.\n")
(c / "package.json").write_text("{}\n")
Path(work / "rec-cust-installed.json").write_text(json.dumps(mod.recommend(c)))

# D) archived custom delivery notes under docs/ — must NOT count (no live path).
d = work / "cust-archive"
skill(d, "docs/factory/SKILL.md",
      "---\nname: factory\ndescription: Gated delivery overlay notes — "
      "software-house pattern, G0 through G10.\n---\n# Factory (archived)\n"
      "Old gated delivery plans. software-house pattern, shipping loop.\n")
(d / "package.json").write_text("{}\n")
Path(work / "rec-cust-archive.json").write_text(json.dumps(mod.recommend(d)))

# E) SKILL.md is a symlink to a delivery-named file — must skip (F1).
e = work / "cust-symlink"
skill_dir = e / ".claude" / "skills" / "factory"
skill_dir.mkdir(parents=True, exist_ok=True)
outside = work / "cust-symlink-outside.md"
outside.write_text("---\nname: factory\ndescription: software-house gated delivery G0 G10.\n---\n")
(skill_dir / "SKILL.md").symlink_to(outside)
(e / "package.json").write_text("{}\n")
Path(work / "rec-cust-symlink.json").write_text(json.dumps(mod.recommend(e)))

# F) SKILL.md is a FIFO — must skip without hanging (F1). Alarm so a missing
#    is_file() guard cannot stall CI.
f = work / "cust-fifo"
fifo_dir = f / ".claude" / "skills" / "factory"
fifo_dir.mkdir(parents=True, exist_ok=True)
os.mkfifo(fifo_dir / "SKILL.md")
(f / "package.json").write_text("{}\n")
class _FifoHang(Exception):
    pass
def _alarm(_signum, _frame):
    raise _FifoHang("FIFO open hung")
signal.signal(signal.SIGALRM, _alarm)
signal.alarm(2)
try:
    rec_f = mod.recommend(f)
    fifo_ok = True
except _FifoHang:
    rec_f = {"other_delivery": None, "skills": []}
    fifo_ok = False
finally:
    signal.alarm(0)
rec_f["_fifo_ok"] = fifo_ok
Path(work / "rec-cust-fifo.json").write_text(json.dumps(rec_f))
PY

if python3 - "$WORK/rec-cust-deliver.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is True and "agentic-delivery" not in r.get("skills", [])) else 1)
PY
then record 0 "recommend: live custom delivery skill suppresses agentic-delivery"; else record 1 "recommend: live custom delivery skill suppresses agentic-delivery"; fi

if python3 - "$WORK/rec-cust-review.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: live review-only skill does not suppress agentic-delivery"; else record 1 "recommend: live review-only skill does not suppress agentic-delivery"; fi

if python3 - "$WORK/rec-cust-installed.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is True and "agentic-delivery" not in r.get("skills", [])) else 1)
PY
then record 0 "recommend: installed agentic-delivery counts as a live delivery pack"; else record 1 "recommend: installed agentic-delivery counts as a live delivery pack"; fi

if python3 - "$WORK/rec-cust-archive.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: archived custom delivery notes do not count"; else record 1 "recommend: archived custom delivery notes do not count"; fi

if python3 - "$WORK/rec-cust-symlink.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: SKILL.md symlink is skipped"; else record 1 "recommend: SKILL.md symlink is skipped"; fi

if python3 - "$WORK/rec-cust-fifo.json" <<'PY'
import json, sys
from pathlib import Path
r = json.loads(Path(sys.argv[1]).read_text())
sys.exit(0 if (r.get("_fifo_ok") is True and r.get("other_delivery") is False and "agentic-delivery" in r.get("skills", [])) else 1)
PY
then record 0 "recommend: SKILL.md FIFO is skipped without hang"; else record 1 "recommend: SKILL.md FIFO is skipped without hang"; fi

# ---------------------------------------------------------------------------
# idea-critic verdict validator
# ---------------------------------------------------------------------------

VALIDATOR="$ROOT/.claude/skills/idea-critic/scripts/validate_verdict.py"
if [ ! -f "$VALIDATOR" ]; then
  record 1 "idea-critic: validator present"
else
  record 0 "idea-critic: validator present"
  # Every fixture below carries steelman + strongest_attack_survived so each
  # case dies at the assertion it names, not at the missing-key check —
  # a fixture missing either new key would report PASS for the wrong reason
  # (silently vacuous; this is exactly the class of defect the planted-defect
  # discipline exists to catch, applied to this harness's own fixtures).
  printf '%s\n' '{"verdict":"HOLD","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"NONE","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.illegal.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.illegal.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject owner-request+HOLD"
  else
    record 0 "idea-critic: reject owner-request+HOLD"
  fi
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"a real attack, survived because x","questions_parent_must_resolve":"NONE","user_question":["a","b"],"dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.listq.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.listq.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject list-shaped user_question"
  else
    record 0 "idea-critic: reject list-shaped user_question"
  fi
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"a real attack, survived because x","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.ok.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.ok.json" >/dev/null 2>&1; then
    record 0 "idea-critic: accept a complete PASS_TO_USER verdict"
  else
    record 1 "idea-critic: accept a complete PASS_TO_USER verdict"
  fi
  # steelman: empty is rejected regardless of verdict.
  printf '%s\n' '{"verdict":"HOLD","independence":"inline","origin":"agent-originated","claim":"x","steelman":"","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"NONE","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.emptysteelman.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.emptysteelman.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject empty steelman"
  else
    record 0 "idea-critic: reject empty steelman"
  fi
  # strongest_attack_survived: empty on PASS_TO_USER is rejected (this is
  # the fixture that proves the gate can actually fail — I1's own bar).
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.emptyattack.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.emptyattack.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject empty strongest_attack_survived on PASS_TO_USER"
  else
    record 0 "idea-critic: reject empty strongest_attack_survived on PASS_TO_USER"
  fi
  # strongest_attack_survived: a generic/performative phrase on PASS_TO_USER
  # is rejected — "no issues found" is present but defeats the field's point.
  printf '%s\n' '{"verdict":"PASS_TO_USER","independence":"inline","origin":"owner-request","claim":"x","steelman":"s","hats_run":"all","assumptions":"NONE","better_ways":"NONE","kill_criteria":"NONE","strongest_attack_survived":"no issues found","questions_parent_must_resolve":"NONE","user_question":"NONE","dissent_ledger":"n","remaining_risk":"n"}' >"$WORK/verdict.genericattack.json"
  if python3 "$VALIDATOR" --file "$WORK/verdict.genericattack.json" >/dev/null 2>&1; then
    record 1 "idea-critic: reject generic/performative strongest_attack_survived on PASS_TO_USER"
  else
    record 0 "idea-critic: reject generic/performative strongest_attack_survived on PASS_TO_USER"
  fi
fi

# ---------------------------------------------------------------------------
# Agent Skills frontmatter — description ≤1024
# ---------------------------------------------------------------------------

desc_ok=1
for skill_md in "$ROOT"/.claude/skills/*/SKILL.md; do
  [ -f "$skill_md" ] || continue
  python3 - "$skill_md" <<'PY' || desc_ok=0
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
if not text.startswith("---"):
    sys.exit(1)
end = text.find("\n---\n", 3)
fm = text[4:end]
lines = fm.splitlines()
desc = []
in_d = False
for line in lines:
    if line.startswith("description:"):
        in_d = True
        rest = line.split("description:", 1)[1].strip()
        if rest and rest not in (">-", "|", ">"):
            desc.append(rest)
        continue
    if in_d:
        if line and not line.startswith(" ") and not line.startswith("\t") and ":" in line:
            break
        desc.append(line.strip())
text_desc = " ".join(x for x in desc if x not in (">-", "|", ">"))
sys.exit(0 if 1 <= len(text_desc) <= 1024 else 1)
PY
done
if [ "$desc_ok" -eq 1 ]; then
  record 0 "frontmatter: every skill description is 1–1024 chars"
else
  record 1 "frontmatter: every skill description is 1–1024 chars"
fi

# ---------------------------------------------------------------------------

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
