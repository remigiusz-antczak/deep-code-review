#!/usr/bin/env python3
"""SubagentStop hook: enforce a minimal, fields-only subagent handback.

Caps CHAT NARRATION only — a subagent's final chat message to its caller.
Deliverables (code, reports, long findings) belong in FILES, which are
uncapped by this hook; a compliant handback names the file path instead of
pasting its content into chat. Blocks (exit 2) a message longer than
MAX_CHARS or MAX_LINES; stderr carries the rewrite instruction. Per the
official docs (https://code.claude.com/docs/en/hooks, "Exit code 2 behavior
per event"), exit code 2 on SubagentStop "prevents the subagent from
stopping, continues the subagent" — so a block does not lose the subagent's
work, it sends the same turn back to compose a shorter handback.

EXEMPTION IS A NAME LIST, NOT A TOOL CHECK. A subagent is exempt (never
capped, at any length) iff its `agent_type` is listed in the comma-separated
HANDBACK_EXEMPT_TYPES env var. The default list is four built-in agent types
whose chat answer is itself the deliverable: `Explore`, `Plan`,
`claude-code-guide`, `statusline-setup`. This hook does NOT inspect an
agent's tools — it cannot tell whether a type has a Write tool. Do NOT add a
custom read-only review lane's type here: exempt means uncapped, which
reopens the cost problem on a harness with no report file. Instead raise
MAX_CHARS/MAX_LINES for that type only via a second, matcher-scoped
SubagentStop entry with env overrides (agentic-delivery/references/
host-enforcement.md). Setting HANDBACK_EXEMPT_TYPES REPLACES the default
list, so repeat the defaults you still want.

After MAX_BLOCKS blocks for one agent_id, this hook lets the stop through
unconditionally, so a subagent that cannot comply never loops forever. Block
counters live in per-agent_id state files under a temp dir (sanitized id;
directory overridable via HANDBACK_STATE_DIR, e.g. for isolated tests).
"""
import json
import os
import sys
import tempfile

MAX_CHARS = int(os.environ.get("HANDBACK_MAX_CHARS", "800"))
MAX_LINES = int(os.environ.get("HANDBACK_MAX_LINES", "10"))
MAX_BLOCKS = 3
# Default exempt agent-type NAMES (chat IS their deliverable). Matched by name
# only; override/extend via HANDBACK_EXEMPT_TYPES (replaces this list).
DEFAULT_EXEMPT_TYPES = "Explore,Plan,claude-code-guide,statusline-setup"
STATE_DIR = os.environ.get(
    "HANDBACK_STATE_DIR", os.path.join(tempfile.gettempdir(), "claude-handback-cap")
)


def _exempt_types():
    return set(filter(None, os.environ.get("HANDBACK_EXEMPT_TYPES", DEFAULT_EXEMPT_TYPES).split(",")))


def _state_path(agent_id):
    safe = "".join(c for c in agent_id if c.isalnum() or c in "-_") or "unknown"
    return os.path.join(STATE_DIR, safe)


def _read_blocks(path):
    try:
        with open(path) as fh:
            return int(fh.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def check(data):
    """Return the hook exit code (0 pass, 2 block) for one hook-input dict."""
    if str(data.get("agent_type") or "") in _exempt_types():
        return 0
    msg = data.get("last_assistant_message") or ""
    agent_id = str(data.get("agent_id") or "unknown")
    chars = len(msg)
    lines = msg.count("\n") + 1 if msg else 0
    if chars <= MAX_CHARS and lines <= MAX_LINES:
        return 0
    os.makedirs(STATE_DIR, exist_ok=True)
    path = _state_path(agent_id)
    blocks = _read_blocks(path)
    if blocks >= MAX_BLOCKS:
        return 0
    with open(path, "w") as fh:
        fh.write(str(blocks + 1))
    sys.stderr.write(
        f"Handback too long ({chars} chars, {lines} lines; cap {MAX_CHARS} chars / "
        f"{MAX_LINES} lines). Rewrite your final message as a fields-only handback: "
        "key=value lines only (verdict, branch/sha, file paths, gate results, open issues). "
        "No prose, no progress narration. Put any long content in a file and give its path.\n"
    )
    return 2


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # unparseable input: never wedge a subagent
    return check(data)


# ---------------------------------------------------------------------------
# --selftest — exercises check() directly (no subprocess, no real stdin) so
# the state dir and env overrides are trivially isolated per case.
# ---------------------------------------------------------------------------
def _selftest():
    import shutil

    global STATE_DIR
    tmp = tempfile.mkdtemp(prefix="handback-cap-selftest-")
    STATE_DIR = tmp
    passed = 0
    failed = 0

    def case(name, got, want):
        nonlocal passed, failed
        if got == want:
            passed += 1
            print(f"PASS  {name} (rc={got})")
        else:
            failed += 1
            print(f"FAIL  {name} (got rc={got}, want rc={want})")

    # short message passes
    case("short-passes", check({"agent_id": "a1", "last_assistant_message": "verdict=ok"}), 0)

    # long message (chars) blocks MAX_BLOCKS times then releases
    long_msg = "x" * 900
    for i in range(MAX_BLOCKS):
        case(f"long-blocks-{i+1}", check({"agent_id": "a2", "last_assistant_message": long_msg}), 2)
    case("long-releases-after-max-blocks", check({"agent_id": "a2", "last_assistant_message": long_msg}), 0)

    # >10 lines but <800 chars still blocks
    many_lines = "\n".join(["line"] * 15)
    case("many-lines-blocks", check({"agent_id": "a3", "last_assistant_message": many_lines}), 2)

    # garbage stdin (simulated: main() catches JSON errors; check() only takes dicts,
    # so exercise main()'s parse-failure path via a broken stdin stand-in)
    class _BadStdin:
        def read(self):
            return "not json"

    real_stdin = sys.stdin
    sys.stdin = _BadStdin()
    try:
        case("garbage-stdin-passes", main(), 0)
    finally:
        sys.stdin = real_stdin

    # per-agent_id counters are independent: a4 fresh, still blocks despite a2 exhausted
    case("independent-agent-id-still-blocks", check({"agent_id": "a4", "last_assistant_message": long_msg}), 2)

    # exempt type: 5000-char message always passes, no state file, no block count spent
    huge_msg = "y" * 5000
    case(
        "exempt-type-huge-message-passes",
        check({"agent_id": "a5", "agent_type": "Explore", "last_assistant_message": huge_msg}),
        0,
    )
    # same huge message, non-exempt type: blocks
    case(
        "non-exempt-type-huge-message-blocks",
        check({"agent_id": "a6", "agent_type": "builder", "last_assistant_message": huge_msg}),
        2,
    )

    # exemption is by listed NAME: a custom review-lane type is capped by
    # default, and exempt once added via HANDBACK_EXEMPT_TYPES.
    lane = {"agent_id": "a7", "agent_type": "security-reviewer", "last_assistant_message": huge_msg}
    case("custom-type-capped-by-default", check(dict(lane)), 2)
    saved = os.environ.get("HANDBACK_EXEMPT_TYPES")
    os.environ["HANDBACK_EXEMPT_TYPES"] = DEFAULT_EXEMPT_TYPES + ",security-reviewer"
    try:
        case("custom-type-exempt-via-env", check(dict(lane, agent_id="a8")), 0)
    finally:
        if saved is None:
            os.environ.pop("HANDBACK_EXEMPT_TYPES", None)
        else:
            os.environ["HANDBACK_EXEMPT_TYPES"] = saved

    # matcher-scoped env override raises the cap for one agent type (the
    # host-enforcement.md fix for a report-file-less review lane) — must be a
    # real subprocess: MAX_LINES/MAX_CHARS are read from os.environ at import,
    # so an in-process check() call can never see a per-invocation override.
    import subprocess

    twenty_lines = "\n".join(["ok"] * 20)  # 20 lines, well under 800 chars

    def run_subproc(agent_id, extra_env):
        env = dict(os.environ, HANDBACK_STATE_DIR=tmp)
        if "HANDBACK_MAX_LINES" not in extra_env:
            env.pop("HANDBACK_MAX_LINES", None)
        env.update(extra_env)
        payload = json.dumps({"agent_id": agent_id, "last_assistant_message": twenty_lines})
        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__)],
            input=payload, capture_output=True, text=True, env=env,
        )
        return proc.returncode

    case(
        "env-override-raises-cap-for-type",
        run_subproc("sub1", {"HANDBACK_MAX_LINES": "25"}),
        0,
    )
    case(
        "same-message-default-cap-blocks",
        run_subproc("sub2", {}),
        2,
    )

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nselftest: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main())
