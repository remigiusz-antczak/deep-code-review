#!/usr/bin/env python3
"""operating_selfcheck.py — per-item PRESENT / MISSING / COULD_NOT_CHECK report
for the always-on operating layer `references/operating-discipline.md` names.

WHY THIS EXISTS
---------------
Installing the skills reproduces the review method, not the operating
discipline: the host settings (`SubagentStart` house-default injector,
two-tier `SubagentStop` hand-back cap, subagent model pin) live OUTSIDE
anything the skill tree ships, so a second machine runs uncapped, unpinned,
and un-paced until someone notices. This script is the self-check step:
after `install.sh --with-operating-layer` writes the settings snippet and an
owner merges it, run this to confirm each item actually landed, item by item,
never a single "all green" that could hide one missed merge.

WHAT IT CHECKS, AND HOW
------------------------
Three items are **host-settable**, read from a `.claude/settings.json`-shaped
file (`--settings`, default `.claude/settings.json`):
- `subagent-start-injector` — a `SubagentStart` hook command containing
  `subagent_start_inject.py`.
- `handback-cap-two-tier` — two or more `SubagentStop` hook entries whose
  command contains `handback_cap.py` (one entry is the default cap only, not
  the second, `matcher`-scoped tier `host-enforcement.md` documents).
- `subagent-model-pin` — `CLAUDE_CODE_SUBAGENT_MODEL` in the settings file's
  `env` block.
A settings file that does not exist at all reports all three `MISSING` (a
fresh install has none yet); an existing but unreadable/malformed one reports
all three `COULD_NOT_CHECK` instead — genuinely ambiguous, never guessed.

Two items are **script-file presence**, resolved relative to this script's
own installed skill directory (`--skill-root`, default: two directories up
from this file):
- `fan-out-probe` — `scripts/host_probe.py`.
- `usage-window-pacer` — the sibling `agentic-ceo` skill's
  `scripts/token_report.py`; `N/A: ... install.sh --with-ceo` (not `MISSING`) when that
  sibling skill isn't installed at all, since its absence is a project
  choice, not a broken install of this one.

The remaining layer items (model-and-effort-routing doctrine, conductor
rules, cross-session coordination, safety rules) are **protocol-only** — no
host artifact represents them, so they always report `COULD_NOT_CHECK:
protocol only, no host artifact` and point back at
`references/operating-discipline.md`.

USAGE
-----
  operating_selfcheck.py [--settings FILE] [--skill-root DIR]
  operating_selfcheck.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import sys

PROTOCOL_ONLY = (
    "model-and-effort-routing-doctrine",
    "conductor-rules",
    "cross-session-coordination",
    "safety-rules",
)


def _flatten_commands(hook_entries: list) -> list:
    """Every `command` string nested under one hook-event's entry list."""
    out = []
    for entry in hook_entries or []:
        for h in (entry or {}).get("hooks", []) or []:
            cmd = h.get("command")
            if cmd:
                out.append(cmd)
    return out


def check_settings(settings_path: str) -> dict:
    """`{item: status}` for the three host-settable items in one settings file.

    A settings file that does not exist at all unambiguously means the
    operating-layer snippet was never merged: all three report `MISSING`,
    not `COULD_NOT_CHECK` (a fresh install has no `.claude/settings.json`
    until an owner writes one). An existing-but-unreadable/malformed file is
    genuinely ambiguous (owner content, corrupted, wrong shape) and reports
    `COULD_NOT_CHECK` instead — never guessed either way.
    """
    if not os.path.exists(settings_path):
        return {"subagent-start-injector": "MISSING", "handback-cap-two-tier": "MISSING",
                "subagent-model-pin": "MISSING"}
    try:
        with open(settings_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        reason = "COULD_NOT_CHECK: unreadable or malformed settings file"
        return {"subagent-start-injector": reason, "handback-cap-two-tier": reason,
                "subagent-model-pin": reason}
    hooks = data.get("hooks", {}) if isinstance(data, dict) else {}
    start_cmds = _flatten_commands(hooks.get("SubagentStart", []))
    stop_cmds = _flatten_commands(hooks.get("SubagentStop", []))
    handback_hits = sum(1 for c in stop_cmds if "handback_cap.py" in c)
    if any("<" in str(e.get("matcher", "")) for e in hooks.get("SubagentStop", []) if isinstance(e, dict)):
        handback_hits = min(handback_hits, 1)  # placeholder matcher never fires
    if handback_hits >= 2:
        handback_status = "PRESENT"
    elif handback_hits == 1:
        handback_status = "MISSING (one tier only -- no real matcher-scoped second SubagentStop entry)"
    else:
        handback_status = "MISSING"
    env = data.get("env", {}) if isinstance(data, dict) else {}
    return {
        "subagent-start-injector": "PRESENT" if any("subagent_start_inject.py" in c for c in start_cmds) else "MISSING",
        "handback-cap-two-tier": handback_status,
        "subagent-model-pin": "PRESENT" if "CLAUDE_CODE_SUBAGENT_MODEL" in env else "MISSING",
    }


def check_scripts(skill_root: str) -> dict:
    """`{item: status}` for the script-file-presence items, relative to `skill_root`."""
    probe = os.path.join(skill_root, "scripts", "host_probe.py")
    pacer = os.path.normpath(os.path.join(skill_root, "..", "agentic-ceo", "scripts", "token_report.py"))
    pacer_sibling_dir = os.path.dirname(os.path.dirname(pacer))
    if os.path.isfile(pacer):
        pacer_status = "PRESENT"
    elif os.path.isdir(pacer_sibling_dir):
        pacer_status = "MISSING"
    else:
        pacer_status = "N/A: agentic-ceo not installed; add it with install.sh --with-ceo"
    return {
        "fan-out-probe": "PRESENT" if os.path.isfile(probe) else "MISSING",
        "usage-window-pacer": pacer_status,
    }


def report(settings_path: str, skill_root: str) -> dict:
    """The full `{item: status}` report: settings-backed + script-file + protocol-only items."""
    out = {}
    out.update(check_settings(settings_path))
    out.update(check_scripts(skill_root))
    for item in PROTOCOL_ONLY:
        out[item] = "COULD_NOT_CHECK: protocol only, no host artifact -- see references/operating-discipline.md"
    return out


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-item present/missing/could-not-check report "
                                                  "for the always-on operating layer.")
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--settings", default=".claude/settings.json")
    parser.add_argument("--skill-root", default=default_root)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    for item, status in sorted(report(args.settings, args.skill_root).items()):
        print(f"{item}: {status}")
    return 0


# ---------------------------------------------------------------------------
# --selftest — exercises check_settings()/check_scripts() directly.
# ---------------------------------------------------------------------------
def _selftest() -> int:
    import tempfile

    passed = 0
    failed = 0

    def case(name, got, want):
        nonlocal passed, failed
        if got == want:
            passed += 1
            print(f"PASS  {name}")
        else:
            failed += 1
            print(f"FAIL  {name} (got {got!r}, want {want!r})")

    tmp = tempfile.mkdtemp(prefix="operating-selfcheck-selftest-")
    try:
        before_path = os.path.join(tmp, "before.json")
        with open(before_path, "w", encoding="utf-8") as fh:
            json.dump({}, fh)
        before = check_settings(before_path)
        case("before-merge-start-missing", before["subagent-start-injector"], "MISSING")
        case("before-merge-handback-missing", before["handback-cap-two-tier"], "MISSING")
        case("before-merge-pin-missing", before["subagent-model-pin"], "MISSING")

        one_tier_path = os.path.join(tmp, "one_tier.json")
        with open(one_tier_path, "w", encoding="utf-8") as fh:
            json.dump({"hooks": {"SubagentStop": [
                {"hooks": [{"type": "command", "command": "python3 .../handback_cap.py"}]}]}}, fh)
        one_tier = check_settings(one_tier_path)
        case("one-tier-handback-not-present", one_tier["handback-cap-two-tier"].startswith("MISSING"), True)

        after_path = os.path.join(tmp, "after.json")
        with open(after_path, "w", encoding="utf-8") as fh:
            json.dump({
                "hooks": {
                    "SubagentStart": [{"hooks": [{"type": "command",
                        "command": "HOUSE_DEFAULTS_FILE=x python3 .../subagent_start_inject.py"}]}],
                    "SubagentStop": [
                        {"hooks": [{"type": "command", "command": "python3 .../handback_cap.py"}]},
                        {"matcher": "reviewer", "hooks": [{"type": "command",
                            "command": "HANDBACK_MAX_LINES=25 python3 .../handback_cap.py"}]},
                    ],
                },
                "env": {"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"},
            }, fh)
        after = check_settings(after_path)
        case("after-merge-start-present", after["subagent-start-injector"], "PRESENT")
        case("after-merge-handback-two-tier-present", after["handback-cap-two-tier"], "PRESENT")
        case("after-merge-pin-present", after["subagent-model-pin"], "PRESENT")

        case("no-settings-file-missing-not-could-not-check",
             check_settings(os.path.join(tmp, "does-not-exist.json"))["subagent-start-injector"], "MISSING")
        malformed_path = os.path.join(tmp, "malformed.json")
        with open(malformed_path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        case("malformed-settings-could-not-check",
             check_settings(malformed_path)["handback-cap-two-tier"].startswith("COULD_NOT_CHECK"), True)

        # script-file presence against this repo's own real, installed skill root
        real_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        real = check_scripts(real_root)
        case("real-skill-root-fan-out-probe-present", real["fan-out-probe"], "PRESENT")

        fake_root = os.path.join(tmp, "no-such-skill")
        os.makedirs(fake_root)
        fake = check_scripts(fake_root)
        case("fake-skill-root-fan-out-probe-missing", fake["fan-out-probe"], "MISSING")
        case("fake-skill-root-pacer-could-not-check",
             fake["usage-window-pacer"].startswith("N/A") and "--with-ceo" in fake["usage-window-pacer"], True)

        full = report(after_path, real_root)
        for item in PROTOCOL_ONLY:
            case(f"protocol-only-{item}-could-not-check", full[item].startswith("COULD_NOT_CHECK"), True)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nselftest: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
