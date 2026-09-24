#!/usr/bin/env python3
"""ci_cost_lint.py — flag GitHub Actions workflows that waste CI runner minutes.

WHY THIS EXISTS
----------------
A fleet of agents pushing branches burns runner minutes fast: duplicate runs
(push AND pull_request firing on the same commits), no cancel-in-progress (a
stale run keeps burning while a newer push already superseded it), no
timeout-minutes (a hung job burns its whole default budget), an over-frequent
schedule, an oversized build matrix, or a workflow that reruns on every
docs-only edit. This lint flags each lever with the concrete fix; it never
edits a workflow itself.

WHAT IT PARSES
---------------
A minimal, stdlib-only YAML SUBSET — no PyYAML dependency (this repo's own CI
has no `pip install` step, so a PyYAML import cannot be relied on to exist).
Supports block mappings, block sequences (`- item` and `- key: value`), flow
sequences/maps (`[a, b]`, `{a: b}`) closed on one line, quoted/bare scalars,
and comments; block scalars (`key: |` / `key: >`) are recognized and their
body skipped (this lint never needs literal step-script text, only
structural keys). This is NOT a general YAML parser: anchors (`&name`),
aliases (`*name`), a flow collection split across multiple lines, and a
second `---` document-start marker (multi-document YAML) are all explicitly
unsupported and RAISE rather than being silently mis-parsed. Two structural
invariants are enforced the same way: the top-level parse must consume every
line (leftover lines mean the indentation didn't resolve the way this
subset's block parser expects), and a plain scalar value can never be
followed by a more-deeply-indented line (that shape is either a multi-line
plain scalar, which this subset does not fold, or invalid indentation).
Any of these raises `UnsupportedYAML`, caught once per file and reported as
a single PARSE-ERROR finding (non-advisory, so it exits non-zero under
`--gate`) — fails closed: never silently skipped, never crashes the scan.

CHECKS (one line per finding, name + fix)
-------------------------------------------
1. CONCURRENCY   — a `pull_request`-triggered workflow with no top-level
   `concurrency:` carrying a truthy `cancel-in-progress`. A superseded push
   keeps its old run burning instead of being canceled.
2. TIMEOUT       — a job with no `timeout-minutes`. GitHub applies its own
   large default ceiling per job when unset (verify the current number on
   GitHub's docs before citing it as fixed), so a hang burns most of that
   budget before GitHub itself intervenes.
3. DUP-TRIGGER   — both `push` (to the default branch) and `pull_request`
   trigger the same workflow while required-status-checks are STRICT (branch
   must be up to date before merge) — the push-after-merge re-runs what the
   PR already ran. Strictness is read via `--repo` (a live `gh api` call) or
   asserted with `--strict-protection`; with neither, this prints as an
   ADVISORY line (never blocks `--gate`) because the lint cannot tell.
4. SCHEDULE      — a `schedule:` cron whose minute field is not a single
   fixed value (i.e. `*`, a list, or a step) fires more than once an hour.
5. MATRIX-SIZE   — a job's `strategy.matrix` combinatorial size (product of
   its list-valued axes, `include`/`exclude` excluded) exceeds `--matrix-max`
   (default 6).
6. PATHS-FILTER  — (always ADVISORY, never blocks `--gate`) a workflow whose
   steps look test-only (a `pytest`/`go test`/`npm test`/… signal) but whose
   `push`/`pull_request` trigger has no `paths`/`paths-ignore`, so a docs-only
   change still runs it.

EXIT CODES
-----------
Default mode prints every finding and exits 0 (advisory only — see the repo
CLAUDE.md owner priority: informational by default, enforced only when a repo
opts in). `--gate` exits 1 if any BLOCKING finding fired (checks 1, 2, 4, 5,
a PARSE-ERROR, and check 3 only when strictness is actually known) — an
ADVISORY finding (check 6, or check 3 with unknown strictness) never trips
`--gate`. Exit 2 (fail closed, not "no findings") if `root` itself does not
exist; a root that exists but has no `.github/workflows/` is a legitimate
clean scan (exit 0, no findings).
`--selftest` runs the built-in RED/GREEN cases and ignores all other args.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any

OK = 0
GATE_FAIL = 1
ERROR = 2
PARSE_ERROR_TAG = "PARSE-ERROR"

TEST_SIGNAL_RE = re.compile(
    r"\b(pytest|go\s+test|npm\s+test|yarn\s+test|make\s+test|unittest|jest|rspec|cargo\s+test)\b",
    re.IGNORECASE,
)

# A bare anchor (`&name`) or alias (`*name`) reference — not a quoted string,
# not a flow-collection marker (those are `[`/`{`), not a lone unnamed `*`.
_ANCHOR_ALIAS_RE = re.compile(r"^[&*][A-Za-z0-9_-]+")


class UnsupportedYAML(ValueError):
    """A construct outside this file's minimal YAML subset (see module
    docstring): an anchor/alias, a flow collection split across lines, a
    second document-start marker, or a structurally invalid indentation
    shape (unconsumed lines, or a scalar followed by deeper-indented
    content). Always caught by `lint_workflow` and turned into one
    PARSE-ERROR finding per file — never propagates to a crash."""

# ---------------------------------------------------------------------------
# Minimal stdlib YAML-subset parser (see module docstring for its contract).
# ---------------------------------------------------------------------------


def _strip_comment(line: str) -> str:
    in_s = in_d = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "#" and not in_s and not in_d:
            if i == 0 or line[i - 1] in " \t":
                return line[:i]
    return line


def _clean_lines(text: str) -> list[tuple[int, str]]:
    """Return [(indent, content)] with comments/blanks/doc-markers dropped and
    every block-scalar (`|`/`>`) body flattened away (never needed here).

    A single leading `---` (the common, harmless single-document marker) is
    tolerated; a SECOND `---` anywhere after it means a second YAML document
    follows, which this subset does not parse (it would otherwise silently
    fold the second document's keys into the first) — raises UnsupportedYAML.
    """
    prepped: list[tuple[int, str] | None] = []
    seen_doc_start = False
    for raw in text.split("\n"):
        line = _strip_comment(raw.expandtabs(2))
        stripped = line.strip()
        if stripped == "---":
            if seen_doc_start:
                raise UnsupportedYAML("a second '---' document-start marker (multi-document YAML) is not supported")
            seen_doc_start = True
            prepped.append(None)
            continue
        if stripped in ("", "..."):
            prepped.append(None)
            continue
        indent = len(line) - len(line.lstrip(" "))
        prepped.append((indent, line.strip()))

    out: list[tuple[int, str]] = []
    i, n = 0, len(prepped)
    while i < n:
        item = prepped[i]
        if item is None:
            i += 1
            continue
        indent, content = item
        out.append((indent, content))
        i += 1
        if re.search(r":\s*[|>][+\-0-9]*\s*$", content):
            while i < n:
                nxt = prepped[i]
                if nxt is not None and nxt[0] <= indent:
                    break
                i += 1
    return out


def _split_flow(inner: str) -> list[str]:
    parts, cur, in_s, in_d = [], "", False, False
    for ch in inner:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        if ch == "," and not in_s and not in_d:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def _flow_is_unclosed(s: str) -> bool:
    """True iff `s` opens a flow collection (`[`/`{`) whose brackets are not
    balanced by the end of this single line — i.e. it continues on the next
    line, which this subset does not support (see UnsupportedYAML)."""
    s = s.strip()
    if not s or s[0] not in "[{":
        return False
    depth = 0
    in_s = in_d = False
    for ch in s:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        elif not in_s and not in_d:
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1
    return depth != 0


def _reject_unsupported_value(rest: str) -> None:
    """Raise UnsupportedYAML for a value this minimal subset cannot parse
    correctly: an anchor/alias, or a flow collection split across lines.
    Silently falling through to `_parse_scalar` on either would store the
    wrong value instead of failing closed."""
    stripped = rest.strip()
    if _ANCHOR_ALIAS_RE.match(stripped):
        raise UnsupportedYAML(f"YAML anchor/alias syntax is not supported: {stripped!r}")
    if _flow_is_unclosed(stripped):
        raise UnsupportedYAML(f"a flow collection split across multiple lines is not supported: {stripped!r}")


def _parse_scalar(s: str) -> Any:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s in ("null", "~", ""):
        return None
    return s


def _parse_flow(s: str) -> Any:
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [] if not inner else [_parse_scalar(x) for x in _split_flow(inner)]
    if s.startswith("{") and s.endswith("}"):
        inner = s[1:-1].strip()
        d: dict[Any, Any] = {}
        for pair in _split_flow(inner):
            if ":" in pair:
                k, v = pair.split(":", 1)
                d[_parse_scalar(k)] = _parse_scalar(v)
        return d
    return None


def _parse_block(lines: list[tuple[int, str]], i: int, indent: int):
    if i >= len(lines) or lines[i][0] != indent:
        return None, i
    if lines[i][1] == "-" or lines[i][1].startswith("- "):
        return _parse_seq(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_seq(lines: list[tuple[int, str]], i: int, indent: int):
    result: list[Any] = []
    while i < len(lines) and lines[i][0] == indent and (
        lines[i][1] == "-" or lines[i][1].startswith("- ")
    ):
        content = lines[i][1]
        rest = "" if content == "-" else content[1:].lstrip()
        if rest == "":
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                val, i = _parse_block(lines, i, lines[i][0])
            else:
                val = None
            result.append(val)
        elif ":" in rest and not rest.lstrip().startswith(("[", "{", '"', "'")):
            synth_indent = indent + (len(content) - len(rest))
            item_lines = [(synth_indent, rest)]
            i += 1
            while i < len(lines) and lines[i][0] >= synth_indent:
                item_lines.append(lines[i])
                i += 1
            val, _ = _parse_map(item_lines, 0, synth_indent)
            result.append(val)
        else:
            _reject_unsupported_value(rest)
            flow = _parse_flow(rest)
            result.append(flow if flow is not None else _parse_scalar(rest))
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                raise UnsupportedYAML(
                    f"sequence item {rest!r} is followed by deeper-indented content"
                    " (unsupported multi-line scalar or invalid indentation)"
                )
    return result, i


def _parse_map(lines: list[tuple[int, str]], i: int, indent: int):
    result: dict[Any, Any] = {}
    while i < len(lines) and lines[i][0] == indent:
        content = lines[i][1]
        if content.startswith("- "):
            break
        if ":" not in content:
            i += 1
            continue
        key, _, rest = content.partition(":")
        key = _parse_scalar(key)
        rest = rest.strip()
        i += 1
        if rest == "":
            if i < len(lines) and lines[i][0] > indent:
                val, i = _parse_block(lines, i, lines[i][0])
            else:
                val = None
            result[key] = val
        else:
            _reject_unsupported_value(rest)
            flow = _parse_flow(rest)
            result[key] = flow if flow is not None else _parse_scalar(rest)
            if i < len(lines) and lines[i][0] > indent:
                raise UnsupportedYAML(
                    f"scalar value for key {key!r} is followed by deeper-indented content"
                    " (unsupported multi-line scalar or invalid indentation)"
                )
    return result, i


def parse_workflow_yaml(text: str) -> dict[Any, Any]:
    lines = _clean_lines(text)
    if not lines:
        return {}
    val, idx = _parse_block(lines, 0, lines[0][0])
    if idx != len(lines):
        # A dedicated safety net behind the local checks above: any
        # indentation shape this subset's block parser can't resolve
        # (including one neither the anchor/alias/flow/deeper-indent checks
        # caught directly) leaves a remainder here instead of silently
        # dropping it.
        raise UnsupportedYAML(
            f"could not fully parse as this YAML subset: {len(lines) - idx} line(s)"
            " left unconsumed after the top-level block"
        )
    return val if isinstance(val, dict) else {}


# ---------------------------------------------------------------------------
# Branch-protection strictness lookup (best-effort; never raises).
# ---------------------------------------------------------------------------


def _lookup_strict(repo: str, branch: str) -> bool | None:
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/branches/{branch}/protection/required_status_checks"],
            capture_output=True, text=True, check=False, timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError):
        return None
    strict = data.get("strict")
    return strict if isinstance(strict, bool) else None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _normalize_on(on_val: Any) -> dict[str, Any]:
    if isinstance(on_val, str):
        return {on_val: None}
    if isinstance(on_val, list):
        return {k: None for k in on_val if isinstance(k, str)}
    if isinstance(on_val, dict):
        return on_val
    return {}


def _has_paths_filter(trigger_val: Any) -> bool:
    return isinstance(trigger_val, dict) and bool(
        trigger_val.get("paths") or trigger_val.get("paths-ignore")
    )


def _matrix_size(matrix: dict[Any, Any]) -> int:
    """GitHub Actions matrix combinatorial size, approximated the same way
    GitHub expands it: the cross product of the list-valued axes, minus one
    combination per `exclude` row, plus one combination per `include` row
    (each `include`/`exclude` row is counted as exactly one combination —
    this does not verify a row's keys actually match a generated axis
    combination, so a no-op exclude row would be undercounted as a real
    removal; documented approximation, not a GitHub-semantics replica)."""
    axes = {
        k: v for k, v in matrix.items()
        if k not in ("include", "exclude") and isinstance(v, list)
    }
    exclude = matrix.get("exclude")
    include = matrix.get("include")
    if axes:
        size = 1
        for v in axes.values():
            size *= max(len(v), 1)
        if isinstance(exclude, list):
            size = max(size - len(exclude), 0)
        if isinstance(include, list):
            size += len(include)
        return size
    return len(include) if isinstance(include, list) else 0


def _cron_more_than_hourly(cron: str) -> bool:
    fields = cron.split()
    if len(fields) != 5:
        return False  # malformed cron is not this lint's concern
    minute = fields[0]
    return any(ch in minute for ch in ("*", ",", "/", "-"))


def lint_workflow(
    path: str, text: str, *, matrix_max: int, strict: bool | None,
) -> list[tuple[str, bool, str]]:
    """Return [(CHECK, is_advisory, message)] for one workflow file's text."""
    findings: list[tuple[str, bool, str]] = []
    try:
        wf = parse_workflow_yaml(text)
    except Exception as exc:  # fail closed: report, never crash the scan
        return [(PARSE_ERROR_TAG, False, f"{path}: could not parse as YAML-subset ({exc})")]

    on_norm = _normalize_on(wf.get("on") if isinstance(wf, dict) else None)
    has_pr = "pull_request" in on_norm
    has_push = "push" in on_norm
    push_val = on_norm.get("push")
    pr_val = on_norm.get("pull_request")

    push_branches = push_val.get("branches") if isinstance(push_val, dict) else None
    push_targets_default = not isinstance(push_branches, list) or bool(
        set(push_branches) & {"main", "master"}
    )

    # 1. CONCURRENCY
    if has_pr:
        concurrency = wf.get("concurrency")
        civ = concurrency.get("cancel-in-progress") if isinstance(concurrency, dict) else None
        configured = civ is True or (isinstance(civ, str) and civ.strip().lower() not in ("", "false"))
        if not configured:
            findings.append((
                "CONCURRENCY", False,
                f"{path}: pull_request trigger with no concurrency cancel-in-progress"
                " — add `concurrency: {group: ${{ github.workflow }}-${{ github.ref }},"
                " cancel-in-progress: true}`",
            ))

    # 2. TIMEOUT
    jobs = wf.get("jobs") if isinstance(wf.get("jobs"), dict) else {}
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        if "timeout-minutes" not in job:
            findings.append((
                "TIMEOUT", False,
                f"{path}: job '{job_id}' has no timeout-minutes"
                " — add `timeout-minutes: N` to bound a hung run",
            ))

    # 3. DUP-TRIGGER
    if has_pr and has_push and push_targets_default:
        if strict is True:
            findings.append((
                "DUP-TRIGGER", False,
                f"{path}: push(default branch) + pull_request both trigger under strict"
                " required-status-checks — a merge re-runs what the PR already ran;"
                " drop `push` or scope it with `paths`",
            ))
        elif strict is None:
            findings.append((
                "DUP-TRIGGER", True,
                f"{path}: push(default branch) + pull_request both trigger — ADVISORY:"
                " branch-protection strictness unknown (pass --repo or --strict-protection)",
            ))

    # 4. SCHEDULE
    schedule = on_norm.get("schedule")
    if isinstance(schedule, list):
        for entry in schedule:
            cron = entry.get("cron") if isinstance(entry, dict) else None
            if isinstance(cron, str) and _cron_more_than_hourly(cron):
                findings.append((
                    "SCHEDULE", False,
                    f"{path}: schedule cron '{cron}' fires more than once an hour"
                    " — widen the interval",
                ))

    # 5. MATRIX-SIZE
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            continue
        strategy = job.get("strategy")
        matrix = strategy.get("matrix") if isinstance(strategy, dict) else None
        if isinstance(matrix, dict):
            size = _matrix_size(matrix)
            if size > matrix_max:
                findings.append((
                    "MATRIX-SIZE", False,
                    f"{path}: job '{job_id}' matrix size {size} exceeds --matrix-max"
                    f" {matrix_max} — narrow the matrix or split into separate workflows",
                ))

    # 6. PATHS-FILTER (always advisory)
    if (has_push or has_pr) and TEST_SIGNAL_RE.search(text):
        if not _has_paths_filter(push_val) and not _has_paths_filter(pr_val):
            findings.append((
                "PATHS-FILTER", True,
                f"{path}: looks test-only but push/pull_request has no paths/paths-ignore"
                " filter — a docs-only change still triggers it (ADVISORY)",
            ))

    return findings


def scan(
    root: str, *, matrix_max: int, strict: bool | None,
) -> list[tuple[str, bool, str]]:
    """Scan `root`'s `.github/workflows/*.yml(.yaml)`.

    Fails closed on a nonexistent `root` (raises FileNotFoundError — the
    caller cannot tell "nothing to scan" from "scanned nothing because the
    path was wrong"). A `root` that exists but has no `.github/workflows/`
    is a legitimate, clean scan: returns `[]`, does not raise.
    """
    if not os.path.isdir(root):
        raise FileNotFoundError(f"ci_cost_lint: root not found: {root}")
    wf_dir = os.path.join(root, ".github", "workflows")
    findings: list[tuple[str, bool, str]] = []
    if not os.path.isdir(wf_dir):
        return findings
    for name in sorted(os.listdir(wf_dir)):
        if not name.endswith((".yml", ".yaml")):
            continue
        full = os.path.join(wf_dir, name)
        rel = os.path.join(".github", "workflows", name)
        with open(full, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        findings.extend(lint_workflow(rel, text, matrix_max=matrix_max, strict=strict))
    return findings


# ---------------------------------------------------------------------------
# Selftest — planted RED/GREEN cases, no network, no fixture repo checked in.
# ---------------------------------------------------------------------------


def _selftest() -> int:
    failures: list[str] = []
    cases = 0

    def check(name: str, findings: list[tuple[str, bool, str]], want_checks: set[str]) -> None:
        nonlocal cases
        cases += 1
        got = {c for c, _adv, _msg in findings}
        if got != want_checks:
            failures.append(f"{name}: got checks {sorted(got)}, want {sorted(want_checks)}")

    clean = """
on:
  push:
    branches: [main]
  pull_request:
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  build:
    timeout-minutes: 10
    strategy:
      matrix:
        os: [ubuntu-latest]
    steps:
      - run: echo hi
"""
    findings = lint_workflow("clean.yml", clean, matrix_max=6, strict=False)
    check("clean-workflow-no-findings", findings, set())

    no_concurrency = """
on:
  pull_request:
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
    findings = lint_workflow("no-concurrency.yml", no_concurrency, matrix_max=6, strict=None)
    check("missing-concurrency-fires", findings, {"CONCURRENCY"})

    no_timeout = """
on:
  push:
jobs:
  build:
    steps:
      - run: echo hi
"""
    findings = lint_workflow("no-timeout.yml", no_timeout, matrix_max=6, strict=None)
    check("missing-timeout-fires", findings, {"TIMEOUT"})

    dup_strict = """
on:
  push:
    branches: [main]
  pull_request:
concurrency:
  cancel-in-progress: true
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
    findings = lint_workflow("dup-strict.yml", dup_strict, matrix_max=6, strict=True)
    check("dup-trigger-strict-blocks", findings, {"DUP-TRIGGER"})
    dup_msg = next(m for c, _a, m in lint_workflow("d.yml", dup_strict, matrix_max=6, strict=True) if c == "DUP-TRIGGER")
    if "ADVISORY" in dup_msg:
        failures.append("dup-trigger-strict-blocks: message wrongly marked ADVISORY")

    findings = lint_workflow("dup-unknown.yml", dup_strict, matrix_max=6, strict=None)
    check("dup-trigger-unknown-advisory", findings, {"DUP-TRIGGER"})
    advisory_flag = next(adv for c, adv, _m in findings if c == "DUP-TRIGGER")
    if not advisory_flag:
        failures.append("dup-trigger-unknown-advisory: expected advisory=True")

    findings = lint_workflow("dup-not-strict.yml", dup_strict, matrix_max=6, strict=False)
    check("dup-trigger-not-strict-silent", findings, set())

    freq_schedule = """
on:
  schedule:
    - cron: '*/5 * * * *'
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
    findings = lint_workflow("freq.yml", freq_schedule, matrix_max=6, strict=None)
    check("frequent-cron-fires", findings, {"SCHEDULE"})

    hourly_schedule = """
on:
  schedule:
    - cron: '0 * * * *'
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
    findings = lint_workflow("hourly.yml", hourly_schedule, matrix_max=6, strict=None)
    check("exactly-hourly-cron-clean", findings, set())

    big_matrix = """
on:
  push:
jobs:
  build:
    timeout-minutes: 5
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        node: [16, 18, 20]
        arch: [x64, arm64]
    steps:
      - run: echo hi
"""
    findings = lint_workflow("matrix.yml", big_matrix, matrix_max=6, strict=None)
    check("oversized-matrix-fires", findings, {"MATRIX-SIZE"})
    size_msg = next(m for c, _a, m in findings if c == "MATRIX-SIZE")
    if "size 12" not in size_msg:
        failures.append(f"oversized-matrix-fires: expected size 12 in message, got {size_msg!r}")

    no_paths_test_wf = """
on:
  push:
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: pytest tests/
"""
    findings = lint_workflow("test.yml", no_paths_test_wf, matrix_max=6, strict=None)
    check("test-only-no-paths-advisory", findings, {"PATHS-FILTER"})
    adv = next(a for c, a, _m in findings if c == "PATHS-FILTER")
    if not adv:
        failures.append("test-only-no-paths-advisory: expected advisory=True")

    with_paths_test_wf = """
on:
  push:
    paths:
      - 'src/**'
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: pytest tests/
"""
    findings = lint_workflow("test-scoped.yml", with_paths_test_wf, matrix_max=6, strict=None)
    check("test-only-with-paths-clean", findings, set())

    unparseable = "not: [a, b: c: d\n  - broken indent *&^"
    findings = lint_workflow("broken.yml", unparseable, matrix_max=6, strict=None)
    # A minimal-parser mismatch must never be silently swallowed into an
    # empty-and-clean result; lint_workflow's own try/except turns the
    # raise into exactly one PARSE-ERROR finding (non-advisory, so --gate
    # still fails the file) instead of crashing the whole scan.
    check("malformed-yaml-is-one-parse-error-not-silently-clean", findings, {"PARSE-ERROR"})
    pe_advisory = next(a for c, a, _m in findings if c == "PARSE-ERROR")
    if pe_advisory:
        failures.append("malformed-yaml: PARSE-ERROR must not be advisory (must block --gate)")

    anchor_wf = """
on:
  push:
jobs:
  build: &anchor
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
    findings = lint_workflow("anchor.yml", anchor_wf, matrix_max=6, strict=None)
    check("anchor-syntax-is-parse-error", findings, {"PARSE-ERROR"})

    alias_wf = """
on:
  push:
defaults:
  run:
    shell: *shell_ref
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
    findings = lint_workflow("alias.yml", alias_wf, matrix_max=6, strict=None)
    check("alias-syntax-is-parse-error", findings, {"PARSE-ERROR"})

    split_flow_wf = """
on:
  push:
jobs:
  build:
    timeout-minutes: 5
    strategy:
      matrix:
        os: [
          ubuntu-latest,
          macos-latest
        ]
    steps:
      - run: echo hi
"""
    findings = lint_workflow("split-flow.yml", split_flow_wf, matrix_max=6, strict=None)
    check("flow-collection-split-across-lines-is-parse-error", findings, {"PARSE-ERROR"})

    multi_doc_wf = """
---
on:
  push:
jobs:
  build:
    timeout-minutes: 5
---
jobs:
  other:
    timeout-minutes: 5
"""
    findings = lint_workflow("multi-doc.yml", multi_doc_wf, matrix_max=6, strict=None)
    check("second-document-marker-is-parse-error", findings, {"PARSE-ERROR"})

    scalar_then_deeper_wf = """
on:
  push:
jobs:
  build:
    timeout-minutes: 5
      note: this line should not exist here
    steps:
      - run: echo hi
"""
    findings = lint_workflow("scalar-deeper.yml", scalar_then_deeper_wf, matrix_max=6, strict=None)
    check("scalar-followed-by-deeper-indent-is-parse-error", findings, {"PARSE-ERROR"})

    unconsumed_wf = """
on:
  push:
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: echo hi
      lonely line with no colon or dash
"""
    findings = lint_workflow("unconsumed.yml", unconsumed_wf, matrix_max=6, strict=None)
    check("unconsumed-top-level-lines-is-parse-error", findings, {"PARSE-ERROR"})

    # Direct unit check on the matrix-size formula: 2x2 axes (4) minus 2
    # exclude rows (2) plus 1 include row (3). Exclude-count != include-count
    # deliberately, so a version that ignores exclude/include entirely (still
    # reporting the plain 4-axis product) is caught rather than coincidentally
    # matching on a fixture where the two adjustments cancel out.
    adj_size = _matrix_size({
        "os": ["ubuntu-latest", "macos-latest"],
        "node": [16, 18],
        "exclude": [
            {"os": "macos-latest", "node": 16},
            {"os": "ubuntu-latest", "node": 18},
        ],
        "include": [{"os": "windows-latest", "node": 20}],
    })
    if adj_size != 3:
        failures.append(f"matrix-size exclude/include adjustment: got {adj_size}, want 3")

    matrix_adj_wf = """
on:
  push:
jobs:
  build:
    timeout-minutes: 5
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        node: [16, 18]
        exclude:
          - os: macos-latest
            node: 16
          - os: ubuntu-latest
            node: 18
        include:
          - os: windows-latest
            node: 20
    steps:
      - run: echo hi
"""
    findings = lint_workflow("matrix-adj.yml", matrix_adj_wf, matrix_max=2, strict=None)
    check("matrix-size-with-exclude-include-fires-at-lowered-cap", findings, {"MATRIX-SIZE"})
    adj_msg = next(m for c, _a, m in findings if c == "MATRIX-SIZE")
    if "size 3" not in adj_msg:
        failures.append(f"matrix-size-with-exclude-include: expected size 3 in message, got {adj_msg!r}")

    cron_range_wf = """
on:
  schedule:
    - cron: '0-30 * * * *'
jobs:
  build:
    timeout-minutes: 5
    steps:
      - run: echo hi
"""
    findings = lint_workflow("cron-range.yml", cron_range_wf, matrix_max=6, strict=None)
    check("cron-minute-range-fires", findings, {"SCHEDULE"})

    with tempfile.TemporaryDirectory() as tmp:
        missing_root = os.path.join(tmp, "does-not-exist")
        try:
            scan(missing_root, matrix_max=6, strict=None)
            failures.append("nonexistent-root: scan() did not raise FileNotFoundError")
        except FileNotFoundError:
            pass
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            rc = main([missing_root])
        if rc != ERROR:
            failures.append(f"nonexistent-root: main() exit {rc}, want {ERROR}")

        empty_root = os.path.join(tmp, "no-workflows-here")
        os.makedirs(empty_root)
        try:
            empty_findings = scan(empty_root, matrix_max=6, strict=None)
        except Exception as exc:  # pragma: no cover - failure path asserted below
            failures.append(f"root-without-workflows-dir: scan() raised unexpectedly: {exc}")
        else:
            if empty_findings != []:
                failures.append(f"root-without-workflows-dir: expected [], got {empty_findings}")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main([empty_root])
        if rc != OK:
            failures.append(f"root-without-workflows-dir: main() exit {rc}, want {OK}")
    cases += 1

    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"SELFTEST OK: {cases}/{cases} cases passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Flag GitHub Actions workflows that waste CI runner minutes."
    )
    parser.add_argument("root", nargs="?", help="repository root to scan (expects .github/workflows/)")
    parser.add_argument("--gate", action="store_true", help="exit 1 if any BLOCKING finding fired")
    parser.add_argument("--matrix-max", type=int, default=6, metavar="N",
                         help="max tolerated matrix combinatorial size (default: 6)")
    parser.add_argument("--strict-protection", action="store_true",
                         help="assume required-status-checks are strict for every scanned workflow")
    parser.add_argument("--repo", metavar="OWNER/REPO",
                         help="look up live branch-protection strictness via `gh api` (network + gh auth required)")
    parser.add_argument("--default-branch", default="main", metavar="NAME",
                         help="default branch name for --repo's protection lookup (default: main)")
    parser.add_argument("--selftest", action="store_true", help="run the built-in selftest and exit")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.root:
        parser.error("root directory is required")
        return GATE_FAIL  # pragma: no cover — parser.error() already exits(2)

    strict: bool | None = True if args.strict_protection else None
    if strict is None and args.repo:
        strict = _lookup_strict(args.repo, args.default_branch)

    try:
        findings = scan(args.root, matrix_max=args.matrix_max, strict=strict)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return ERROR
    blocking = 0
    for check_name, advisory, msg in findings:
        tag = "ADVISORY" if advisory else check_name
        print(f"{tag}: {msg}")
        if not advisory:
            blocking += 1

    if not findings:
        print("ci_cost_lint: ok (no findings)")

    if args.gate and blocking:
        return GATE_FAIL
    return OK


if __name__ == "__main__":
    sys.exit(main())
