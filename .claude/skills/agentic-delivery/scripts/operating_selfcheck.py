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
  `env` block (`WARN:` when `_FORCE=1` pins a haiku-class model).
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


SANDBOX_RED = ("MISSING RED: sandbox off -- an agent's `rm -rf` can delete your files; set sandbox.enabled=true and "
               "sandbox.allowUnsandboxedCommands=false (install.sh --apply-operating-layer)")


PIN_WARN = ("WARN: CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1 pins every subagent to a haiku-class model "
            "(overrides lane agents: junk commits, lost hand-backs); pin to sonnet or unset FORCE")


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
                "subagent-model-pin": "MISSING", "sandbox-on": SANDBOX_RED}
    try:
        with open(settings_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        reason = "COULD_NOT_CHECK: unreadable or malformed settings file"
        return {"subagent-start-injector": reason, "handback-cap-two-tier": reason,
                "subagent-model-pin": reason, "sandbox-on": reason}
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
    sb = data.get("sandbox", {}) if isinstance(data, dict) else {}
    sb = sb if isinstance(sb, dict) else {}
    return {
        "subagent-start-injector": "PRESENT" if any("subagent_start_inject.py" in c for c in start_cmds) else "MISSING",
        "handback-cap-two-tier": handback_status,
        "subagent-model-pin": PIN_WARN if (str(env.get("CLAUDE_CODE_SUBAGENT_MODEL_FORCE")) in ("1", "true")
                                           and "haiku" in str(env.get("CLAUDE_CODE_SUBAGENT_MODEL", "")).lower())
                              else "PRESENT" if "CLAUDE_CODE_SUBAGENT_MODEL" in env else "MISSING",
        "sandbox-on": "PRESENT" if sb.get("enabled") is True and sb.get("allowUnsandboxedCommands") is False
                      else SANDBOX_RED,
    }


def check_scripts(skill_root: str) -> dict:
    """`{item: status}` for the script-file-presence items, relative to `skill_root`."""
    probe = os.path.join(skill_root, "scripts", "host_probe.py")
    pacer = os.path.normpath(os.path.join(skill_root, "..", "agentic-ceo", "scripts", "token_report.py"))
    pacer_sibling_dir = os.path.dirname(os.path.dirname(pacer))
    ratchet = os.path.join(pacer_sibling_dir, "scripts", "token_ratchet.py")
    if os.path.isfile(pacer):
        pacer_status = "PRESENT"
    elif os.path.isdir(pacer_sibling_dir):
        pacer_status = "MISSING"
    else:
        pacer_status = "N/A: agentic-ceo not installed; add it with install.sh --with-ceo"
    return {
        "fan-out-probe": "PRESENT" if os.path.isfile(probe) else "MISSING",
        "usage-window-pacer": pacer_status,
        # token_ratchet.py = tokens per delivered PR vs a baseline; same N/A rule as the pacer
        "token-ratchet": ("PRESENT" if os.path.isfile(ratchet) else "MISSING")
        if os.path.isdir(pacer_sibling_dir) else pacer_status,
        # weekly_receipt.py = one-screen value card; presence only, WARN-level (never blocks)
        "weekly-receipt": ("PRESENT" if os.path.isfile(os.path.join(pacer_sibling_dir, "scripts", "weekly_receipt.py"))
                           else "MISSING") if os.path.isdir(pacer_sibling_dir) else pacer_status,
    }


def report(settings_path: str, skill_root: str) -> dict:
    """The full `{item: status}` report: settings-backed + script-file + protocol-only items."""
    out = {}
    out.update(check_settings(settings_path))
    out.update(check_scripts(skill_root))
    for item in PROTOCOL_ONLY:
        out[item] = "COULD_NOT_CHECK: protocol only, no host artifact -- see references/operating-discipline.md"
    return out


GH_WARN = ("WARN: sandbox on and gh not excluded -- gh may fail with `x509 ... OSStatus -26276`; run "
           "`/sandbox exclude \"gh *\"` (gh then runs unsandboxed; see docs/host-safety.md#common-sandbox-errors)")


def sandbox_gh_warn(settings_path: str) -> str | None:
    """`GH_WARN` when settings turn the sandbox on and no `sandbox.excludedCommands` entry covers `gh`.

    Reads settings only; None when the file is missing/unreadable, the sandbox is off, or gh is excluded.
    """
    try:
        with open(settings_path, encoding="utf-8") as fh:
            sb = json.load(fh).get("sandbox")
    except (OSError, ValueError, AttributeError):
        return None
    if not isinstance(sb, dict) or sb.get("enabled") is not True:
        return None
    ex = sb.get("excludedCommands")
    ex = ex if isinstance(ex, list) else []
    if any(isinstance(e, str) and (e.strip() == "gh" or e.strip().startswith(("gh ", "gh:"))) for e in ex):
        return None
    return GH_WARN


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-item present/missing/could-not-check report "
                                                  "for the always-on operating layer.")
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser.add_argument("--settings", default=".claude/settings.json")
    parser.add_argument("--skill-root", default=default_root)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--project", default=".", help="project root scanned for per-host sandbox status")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    rep = report(args.settings, args.skill_root)
    tsv = os.path.join(args.skill_root, "templates", "host-safety.tsv")
    if os.path.exists(tsv):  # per-host sandbox status (host_safety.py); absent in a trimmed install
        sys.path.insert(0, os.path.join(args.skill_root, "scripts"))
        import host_safety
        rep.update(host_safety.report(args.project, tsv))
    for item, status in sorted(rep.items()):
        print(f"{item}: {status}")
    warn = sandbox_gh_warn(args.settings)
    if warn:
        print(warn)
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

        case("before-merge-sandbox-red", before["sandbox-on"].startswith("MISSING RED"), True)
        half_path = os.path.join(tmp, "half.json")
        with open(half_path, "w", encoding="utf-8") as fh:
            json.dump({"sandbox": {"enabled": True}}, fh)
        case("sandbox-enabled-but-unsandboxed-allowed-red",
             check_settings(half_path)["sandbox-on"].startswith("MISSING RED"), True)

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
                "sandbox": {"enabled": True, "allowUnsandboxedCommands": False},
            }, fh)
        after = check_settings(after_path)
        case("after-merge-start-present", after["subagent-start-injector"], "PRESENT")
        case("after-merge-handback-two-tier-present", after["handback-cap-two-tier"], "PRESENT")
        case("after-merge-pin-present", after["subagent-model-pin"], "PRESENT")
        case("after-merge-sandbox-present", after["sandbox-on"], "PRESENT")

        case("no-settings-file-missing-not-could-not-check",
             check_settings(os.path.join(tmp, "does-not-exist.json"))["subagent-start-injector"], "MISSING")
        malformed_path = os.path.join(tmp, "malformed.json")
        with open(malformed_path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        case("malformed-settings-could-not-check",
             check_settings(malformed_path)["handback-cap-two-tier"].startswith("COULD_NOT_CHECK"), True)

        gh_path = os.path.join(tmp, "gh.json")
        for name, sb, want in (("off", {"enabled": False}, False), ("on-no-exclude", {"enabled": True}, True),
                               ("on-excluded", {"enabled": True, "excludedCommands": ["gh *"]}, False),
                               ("on-other-exclude", {"enabled": True, "excludedCommands": ["ghost"]}, True)):
            with open(gh_path, "w", encoding="utf-8") as fh:
                json.dump({"sandbox": sb}, fh)
            case(f"gh-warn-{name}", sandbox_gh_warn(gh_path) is not None, want)
        case("gh-warn-no-file", sandbox_gh_warn(os.path.join(tmp, "nope.json")), None)

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

        case("fake-skill-root-ratchet-na", fake["token-ratchet"].startswith("N/A"), True)
        case("fake-skill-root-receipt-na", fake["weekly-receipt"].startswith("N/A"), True)
        case("real-skill-root-receipt-present", real["weekly-receipt"], "PRESENT")
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
