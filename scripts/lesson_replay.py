#!/usr/bin/env python3
"""lesson_replay.py — advisory signal that a lesson's mechanism is tied to the lesson.

WHY THIS EXISTS
---------------
`fix_class_gate.py --trigger-glob` (CI step "Prose lessons carry a
mechanism") proves a commit that edits skill prose also touched an eval, a
script, or a gate test. It cannot tell whether that mechanism has anything
to do with the lesson: an eval case that asserts only what the skillset
already said, or a script selftest that still passes with the change
reverted, passes the gate anyway. This probe replays each lesson commit and
prints one line per lesson:

  REPLAYS          the changed eval case or selftest is tied to the change:
                   a case's assertion names a term the lesson newly added,
                   or reverting a changed script hunk fails an assertion in
                   that script's selftest (evidence printed)
  VACUOUS          a checkable mechanism shows no such tie
  COULD_NOT_CHECK  no deterministic check applies (reason printed)

This is an advisory signal, not proof. A reviewer judges every line.

WHAT IS A LESSON
----------------
A non-merge commit in `--base..--head` that adds or modifies a path matching
a `--trigger-glob` (default: every skill's SKILL.md and references/*.md),
unless every such path is a SKILL.md frontmatter version-stamp-only change
(the same rule and helpers as fix_class_gate.py trigger mode, imported from
it). Each lesson is compared to its first parent. Merge commits are skipped
here; fix_class_gate.py trigger mode judges evil merges.

HOW EACH MECHANISM IS CHECKED
-----------------------------
Eval cases (files matching `--eval-glob`, `{"evals": [{"id": ...}]}`): a
case is changed when its id is absent at the parent or its content differs.
New terms are word tokens (lowercase, 4+ characters) in the lesson's added
prose lines that appear nowhere in the parent's prose or eval files (so a
term the same case, or any case, already asserted never counts), minus any
token equal to a changed path's file stem or written as a `--flag`. A
changed case whose `expected_output` or `expectations` names a new term is
tied. One tied case makes the lesson REPLAYS; the line reports tied n/m and
the untied case ids. No tied case -> VACUOUS. No new term at all ->
COULD_NOT_CHECK.

Script selftests (modified `.py` files matching `--script-glob` that contain
`--selftest`): the commit's tree is exported with `git archive`, the
selftest must pass there, then each changed hunk is reverted to the parent's
lines one at a time (mutation) and the selftest rerun. Only an assertion
failure counts: an `AssertionError`, or the selftest's own `FAIL` line with
no other exception. A revert that only crashes (NameError, ImportError, any
other exception, or a non-zero exit without a FAIL line) or times out is
inconclusive. Any assertion failure -> REPLAYS. Otherwise any crash or
timeout -> COULD_NOT_CHECK (never VACUOUS). Every hunk reverted with the
selftest still passing -> VACUOUS. A new script (no parent to replay
against), a selftest that does not pass at the commit, the hunk cap, or the
run time budget (`--budget`) -> COULD_NOT_CHECK.

A lesson is REPLAYS if any mechanism replays, else VACUOUS if any mechanism
is vacuous, else COULD_NOT_CHECK (including other test surfaces such as
scripts/test-ci-gates.sh, a declared `No-Mechanism-Reason:`, or no
mechanism at all, which fix_class_gate.py owns).

HONESTY LIMITS
--------------
Token overlap is gameable: an eval can name a new term without testing the
behaviour, and it proves nothing about whether a grader would fail a
response lacking the lesson. A reverted hunk can fail an assertion for a
reason unrelated to the lesson; the probe shows some changed line is pinned,
not which. VACUOUS and COULD_NOT_CHECK are leads for the reviewer, not
verdicts on the lesson.

EXIT CODES
----------
  0  advisory mode (default), or `--gate` with no VACUOUS lesson
  1  `--gate` and at least one VACUOUS lesson. `--gate` blocks only VACUOUS;
     COULD_NOT_CHECK is printed with its reason and never blocks
  2  fail closed: not a git repo, unresolvable or all-zeros `--base`/`--head`

USAGE
-----
  lesson_replay.py --base <ref> --head <ref> [--gate] [--trigger-glob G ...]
                   [--eval-glob G ...] [--script-glob G ...]
                   [--max-mutants N] [--timeout SECONDS] [--budget SECONDS]
  lesson_replay.py --selftest
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
import importlib.util
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

_FCG_PATH = Path(__file__).resolve().parents[1] / ".claude/skills/deep-code-review/scripts/fix_class_gate.py"
_spec = importlib.util.spec_from_file_location("fix_class_gate", _FCG_PATH)
fcg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fcg)

DEFAULT_TRIGGERS = (".claude/skills/*/SKILL.md", ".claude/skills/*/references/*.md")
DEFAULT_EVALS = (".claude/skills/*/evals/evals.json",)
DEFAULT_SCRIPTS = (".claude/skills/*/scripts/*.py", "scripts/*.py")
ZERO_SHA = fcg.ZERO_SHA
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{2,}[a-z0-9]")
FLAG_RE = re.compile(r"--([a-z0-9][a-z0-9_-]*)")
EXC_RE = re.compile(r"^([A-Za-z_][\w.]*(?:Error|Exception))\b", re.M)


def _git(repo: str, *args: str) -> str:
    """Run git in `repo` and return stdout; raises fix_class_gate.GitError on failure."""
    return fcg._run_git(repo, list(args))


def tokens(text: str) -> set[str]:
    """Lowercased word tokens of 4+ characters (letters, digits, `_`, `-` inside)."""
    return set(TOKEN_RE.findall(text.lower()))


def _flags(text: str) -> set[str]:
    """Names written as `--flag` in `text`, lowercased (never tie terms)."""
    return set(FLAG_RE.findall(text.lower()))


def _show(repo: str, rev: str, path: str) -> str | None:
    """File content at `rev:path`, or None when the path does not exist there."""
    r = subprocess.run(["git", "-C", repo, "show", f"{rev}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _corpus_tokens(repo: str, rev: str, globs: list) -> set[str]:
    """Tokens of every prose and eval file at `rev` (what the skillset already said)."""
    paths = [p for p in _git(repo, "ls-tree", "-r", "--name-only", rev).splitlines()
             if fcg._matches_any(p, globs)]
    blobs = subprocess.run(["git", "-C", repo, "cat-file", "--batch=%(objectname)"],
                           input="".join(f"{rev}:{p}\n" for p in paths), capture_output=True,
                           text=True, errors="replace").stdout
    return tokens(blobs)


def _cases(text: str | None) -> dict[str, str]:
    """Map eval id -> canonical JSON of the case; {} for a missing file. Raises ValueError on bad JSON."""
    if text is None:
        return {}
    return {c["id"]: json.dumps(c, sort_keys=True) for c in json.loads(text)["evals"]}


def check_evals(repo: str, parent: str, sha: str, paths: list[str], new_terms: set[str]):
    """Verdict tuple (verdict, detail) for changed eval cases, or None when no case changed."""
    changed = []
    for p in paths:
        try:
            old, new = _cases(_show(repo, parent, p)), _cases(_show(repo, sha, p))
        except (ValueError, KeyError, TypeError) as exc:
            return "COULD_NOT_CHECK", f"{p}: unreadable evals ({exc.__class__.__name__})"
        changed += [json.loads(v) for k, v in new.items() if old.get(k) != v]
    if not changed:
        return None
    if not new_terms:
        return "COULD_NOT_CHECK", "added prose introduces no term new to the skill prose and evals"
    tied, untied = [], []
    for case in changed:
        assertion = json.dumps([case.get("expected_output", ""), case.get("expectations", [])])
        hit = sorted(tokens(assertion) & new_terms - _flags(assertion))
        (tied if hit else untied).append(f"{case['id']} names '{hit[0]}'" if hit else case["id"])
    n = f"tied {len(tied)}/{len(changed)} changed cases"
    if tied:
        rest = f"; untied: {', '.join(untied[:3])}{' ...' if len(untied) > 3 else ''}" if untied else ""
        return "REPLAYS", f"eval {tied[0]}; {n}{rest}"
    return "VACUOUS", f"{n}: no changed eval case names a term new to this lesson"


def _run_selftest(root: Path, path: str, timeout: float) -> str:
    """Outcome of `python3 path --selftest` in `root`: pass, assert, crash, or timeout."""
    try:
        proc = subprocess.run([sys.executable, path, "--selftest"], cwd=root, capture_output=True,
                              text=True, errors="replace", timeout=max(timeout, 0.1))
    except subprocess.TimeoutExpired:
        return "timeout"
    if proc.returncode == 0:
        return "pass"
    out = proc.stdout + proc.stderr
    excs = EXC_RE.findall(out)
    if any(not e.endswith("AssertionError") for e in excs):
        return "crash"
    return "assert" if excs or re.search(r"^FAIL\b", out, re.M) else "crash"


def check_script(repo: str, parent: str, sha: str, path: str, args):
    """Mutation replay of one changed script: revert each hunk; an assertion must fail on one."""
    old = _show(repo, parent, path)
    if old is None:
        return "COULD_NOT_CHECK", f"{path}: new script, no parent to replay against"
    budget_msg = "COULD_NOT_CHECK", f"{path}: run time budget (--budget {args.budget:g}s) exhausted"
    if time.monotonic() >= args.deadline:
        return budget_msg
    new = _show(repo, sha, path) or ""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        blob = subprocess.run(["git", "-C", repo, "archive", "--format=tar", sha],
                              capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
            tar.extractall(root, filter="data")

        def remaining() -> float:
            return min(args.timeout, args.deadline - time.monotonic())

        if _run_selftest(root, path, remaining()) != "pass":
            return "COULD_NOT_CHECK", f"{path}: selftest does not pass at the commit"
        a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
        hunks = [op for op in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()
                 if op[0] != "equal"]
        seen = {"pass": 0, "crash": 0, "timeout": 0}
        for _, i1, i2, j1, j2 in hunks[:args.max_mutants]:
            if time.monotonic() >= args.deadline:
                return budget_msg
            mutant = "".join(b[:j1] + a[i1:i2] + b[j2:])
            try:
                compile(mutant, path, "exec")
            except SyntaxError:
                continue
            (root / path).write_text(mutant)
            outcome = _run_selftest(root, path, remaining())
            (root / path).write_text(new)
            if outcome == "assert":
                return "REPLAYS", f"{path}: reverting hunk at line {j1 + 1} fails an assertion in its selftest"
            seen[outcome] += 1
        if len(hunks) > args.max_mutants:
            return "COULD_NOT_CHECK", f"{path}: {len(hunks)} hunks exceed --max-mutants {args.max_mutants}"
        if seen["crash"] or seen["timeout"]:
            return "COULD_NOT_CHECK", (f"{path}: no revert failed an assertion; {seen['crash']} crashed, "
                                       f"{seen['timeout']} timed out")
        if not seen["pass"]:
            return "COULD_NOT_CHECK", f"{path}: no hunk revert compiles"
        return "VACUOUS", f"{path}: selftest passes with each of {seen['pass']} changed hunk(s) reverted"


def replay_commit(repo: str, sha: str, args) -> tuple[str, str] | None:
    """Classify one commit; None when it files no lesson."""
    parents = fcg._parents(repo, sha)
    if not parents:
        return "COULD_NOT_CHECK", "root commit, no parent to replay against"
    parent = parents[0]
    changed = [p for p in _git(repo, "diff", "--no-ext-diff", "--name-only", "--no-renames",
                                "--diff-filter=AM", parent, sha).splitlines() if p]
    prose = [p for p in changed if fcg._matches_any(p, args.trigger_rx)]
    if not prose or all(fcg._version_stamp_only(repo, parent, sha, p) for p in prose):
        return None
    diff = _git(repo, "diff", "--no-ext-diff", "--no-color", "-U0", "--no-renames", parent, sha, "--", *prose)
    added = "\n".join(ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
    stems = {Path(p).stem.lower() for p in changed}
    new_terms = (tokens(added) - _corpus_tokens(repo, parent, args.trigger_rx + args.eval_rx)
                 - stems - _flags(added))
    results = []
    evals = [p for p in changed if fcg._matches_any(p, args.eval_rx)]
    checks = [lambda: check_evals(repo, parent, sha, evals, new_terms)] if evals else []
    checks += [lambda p=p: check_script(repo, parent, sha, p, args)
               for p in changed if p.endswith(".py") and fcg._matches_any(p, args.script_rx)
               and "--selftest" in (_show(repo, sha, p) or "")]
    for check in checks:  # cheapest first; the first REPLAYS decides the lesson
        r = check()
        if r and r[0] == "REPLAYS":
            return r
        results += [r] if r else []
    for r in results:
        if r[0] == "VACUOUS":
            return r
    if results:
        return results[0]
    if fcg._trailer_value(repo, sha, "No-Mechanism-Reason").strip():
        return "COULD_NOT_CHECK", "declares No-Mechanism-Reason"
    return "COULD_NOT_CHECK", "no replayable mechanism (evals.json case or script selftest)"


def run(argv: list[str]) -> int:
    """CLI entry: print one verdict line per lesson plus a summary; return the exit code."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--gate", action="store_true", help="exit 1 when any lesson is VACUOUS (only VACUOUS)")
    ap.add_argument("--trigger-glob", action="append")
    ap.add_argument("--eval-glob", action="append")
    ap.add_argument("--script-glob", action="append")
    ap.add_argument("--max-mutants", type=int, default=25)
    ap.add_argument("--timeout", type=float, default=120.0, help="seconds per selftest run")
    ap.add_argument("--budget", type=float, default=600.0, help="seconds for all script replays in this run")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest()
    args.trigger_rx = fcg._compile_globs(tuple(args.trigger_glob or DEFAULT_TRIGGERS))
    args.eval_rx = fcg._compile_globs(tuple(args.eval_glob or DEFAULT_EVALS))
    args.script_rx = fcg._compile_globs(tuple(args.script_glob or DEFAULT_SCRIPTS))
    args.deadline = time.monotonic() + args.budget
    if not args.base or not args.head or ZERO_SHA in (args.base, args.head):
        print("lesson_replay: ERROR --base and --head must name real commits (not all-zeros)")
        return 2
    if not fcg._is_git_repo(args.repo):
        print(f"lesson_replay: ERROR not a git repository: {args.repo}")
        return 2
    base, head = fcg._resolve_commit(args.repo, args.base), fcg._resolve_commit(args.repo, args.head)
    if not base or not head:
        print(f"lesson_replay: ERROR cannot resolve --base {args.base} / --head {args.head}")
        return 2
    try:
        shas = fcg._list_range_shas(args.repo, base, head)
    except fcg.GitError as exc:
        print(f"lesson_replay: ERROR cannot walk the range: {exc}")
        return 2
    counts = {"REPLAYS": 0, "VACUOUS": 0, "COULD_NOT_CHECK": 0}
    for sha in shas:
        res = replay_commit(args.repo, sha, args)
        if res:
            counts[res[0]] += 1
            print(f"{res[0]} {sha[:9]} {fcg._subject(args.repo, sha)} -- {res[1]}")
    print("lesson_replay: " + ", ".join(f"{v} {k}" for k, v in counts.items())
          + (" (--gate blocks VACUOUS only)" if args.gate else " (advisory signal, not proof)"))
    return 1 if args.gate and counts["VACUOUS"] else 0


# ---------------------------------------------------------------- selftest

_TOOL = '''import sys
def f(x):
    return x + 1
def _selftest():
    assert f(1) == 2
    return 0
if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else 0)
'''


def _selftest() -> int:
    """Plant one lesson per verdict in a throwaway repo and assert each classification."""
    fails = []

    def check(name: str, cond: bool) -> None:
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        repo = str(tmp)
        sk = Path(tmp, ".claude/skills/s")
        (sk / "scripts").mkdir(parents=True)
        env = ["-c", "user.name=Jane Smith", "-c", "user.email=jane@example.com"]
        _git(repo, "init", "-q")

        def commit(msg: str, prose: str | None = None, cases: list | None = None,
                   tool: str | None = None, extra: dict | None = None) -> str:
            if prose is not None:
                (sk / "SKILL.md").write_text(prose)
            if cases is not None:
                (sk / "evals").mkdir(exist_ok=True)
                (sk / "evals/evals.json").write_text(json.dumps({"evals": cases}))
            if tool is not None:
                (sk / "scripts/tool.py").write_text(tool)
            for rel, body in (extra or {}).items():
                Path(tmp, rel).parent.mkdir(parents=True, exist_ok=True)
                Path(tmp, rel).write_text(body)
            _git(repo, "add", "-A")
            _git(repo, *env, "commit", "-q", "--allow-empty", "-m", msg)
            return _git(repo, "rev-parse", "HEAD").strip()

        def case(cid: str, expect: str) -> dict:
            return {"id": cid, "prompt": "p", "expected_output": expect, "expectations": [expect]}

        base_prose = '---\nversion: "1.0.0"\n---\nAlways check widgets before shipping.\n'
        c0 = commit("feat: base", base_prose, [case("widgets", "checks widgets")], _TOOL)
        p1 = base_prose + "Reject frobnicated payloads.\n"
        c1 = commit("feat: tied eval", p1, [case("widgets", "checks widgets"),
                                            case("frob", "rejects frobnicated payloads")])
        p2 = p1 + "Quarantine zorbified inputs.\n"
        c2 = commit("feat: vacuous eval", p2, [case("widgets", "checks widgets"),
                                               case("frob", "rejects frobnicated payloads"),
                                               case("dup", "always checks widgets before shipping")])
        p3 = p2 + "Always check payloads before shipping.\n"
        c3 = commit("feat: no new term", p3, [case("widgets", "checks widgets, always")])
        c4 = commit("feat: pinned script", p3 + "Tool adds two.\n",
                    tool=_TOOL.replace("x + 1", "x + 2").replace("== 2", "== 3"))
        c5 = commit("feat: unpinned script", p3 + "Tool gains doubler.\n",
                    tool=_TOOL.replace("x + 1", "x + 2").replace("== 2", "== 3")
                    + "def g(x):\n    return x * 2\n")
        c7 = commit("feat: new script", p3 + "Tool adds two.\nTool gains doubler.\nNew helper.\n",
                    extra={".claude/skills/s/scripts/new.py": _TOOL})
        c8 = commit("docs: unrelated", extra={"README.md": "hello\n"})
        c9 = commit("feat: gate-only", p3 + "Tool adds two.\nTool gains doubler.\nNew helper.\n"
                    "Gate line.\n", extra={"scripts/test-ci-gates.sh": "true\n"})

        def verdicts(base: str, head: str, *extra_args: str) -> tuple[int, str]:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = run(["--repo", repo, "--base", base, "--head", head, *extra_args])
            return rc, buf.getvalue()

        def line_for(out: str, sha: str) -> str:
            return next((ln for ln in out.splitlines() if f" {sha[:9]} " in ln), "")

        rc, out = verdicts(c0, c9)
        check("eval naming a new prose term -> REPLAYS", line_for(out, c1).startswith("REPLAYS")
              and "frob names 'frobnicated'" in line_for(out, c1))
        check("eval naming only old terms -> VACUOUS", line_for(out, c2).startswith("VACUOUS"))
        check("prose with no new term -> COULD_NOT_CHECK", line_for(out, c3).startswith("COULD_NOT_CHECK")
              and "no term new" in line_for(out, c3))
        check("script hunk revert fails selftest -> REPLAYS", line_for(out, c4).startswith("REPLAYS")
              and "fails an assertion" in line_for(out, c4))
        check("script selftest ignores changed hunk -> VACUOUS", line_for(out, c5).startswith("VACUOUS"))
        check("new script -> COULD_NOT_CHECK", "new script, no parent" in line_for(out, c7))
        check("non-prose commit is not listed", line_for(out, c8) == "")
        check("gate-test-only mechanism -> COULD_NOT_CHECK", line_for(out, c9).startswith("COULD_NOT_CHECK"))
        check("advisory mode exits 0 despite VACUOUS", rc == 0 and "(advisory signal, not proof)" in out)
        check("--gate exits 1 on VACUOUS", verdicts(c0, c9, "--gate")[0] == 1)
        check("--gate exits 0 when every lesson REPLAYS", verdicts(c0, c1, "--gate")[0] == 0)
        check("--gate never blocks COULD_NOT_CHECK", verdicts(c2, c3, "--gate")[0] == 0)
        check("all-zeros base fails closed (2)", verdicts(ZERO_SHA, c1)[0] == 2)
        check("unresolvable base fails closed (2)", verdicts("no-such-ref", c1)[0] == 2)
        c10 = commit("chore: stamp only", p3.replace("1.0.0", "1.0.2") + "Tool adds two.\n"
                     "Tool gains doubler.\nNew helper.\nGate line.\n")
        check("pure version-stamp commit is not listed", line_for(verdicts(c9, c10)[1], c10) == "")
        p10 = p3.replace("1.0.0", "1.0.2") + "Tool adds two.\nTool gains doubler.\nNew helper.\nGate line.\n"
        seed = [case("widgets", "checks widgets, always"), case("seed", "sanitize glorped headers")]
        c11 = commit("test: seed an eval", cases=seed)
        c12 = commit("feat: term only new to prose", p10 + "Sanitize glorped headers, blip.\n",
                     seed + [case("glorp", "sanitize glorped headers")])
        p12 = p10 + "Sanitize glorped headers, blip.\n"
        c13 = commit("feat: stem and flag terms", p12 + "Run zapper nightly --dryrun.\n",
                     seed + [case("glorp", "sanitize glorped headers"), case("zap", "runs zapper with --dryrun")],
                     extra={"docs/zapper.txt": "z\n"})
        p13 = p12 + "Run zapper nightly --dryrun.\n"
        t5 = _TOOL.replace("x + 1", "x + 2").replace("== 2", "== 3") + "def g(x):\n    return x * 2\n"
        t14 = t5.replace("def _selftest():\n", "def k():\n    return 1\ndef _selftest():\n    assert k() == 1\n")
        c14 = commit("feat: crash-only revert", p13 + "Helper k.\n", tool=t14)
        commit("chore: hang k", tool=t14.replace("    return 1\n", "    while True:\n        pass\n"))
        c16 = commit("feat: hang-only revert", p13 + "Helper k.\nHelper k fixed.\n", tool=t14)
        _, out2 = verdicts(c10, c16, "--timeout", "3")
        check("eval term already in the parent's evals -> VACUOUS", line_for(out2, c12).startswith("VACUOUS"))
        check("seed eval commit without prose is not listed", line_for(out2, c11) == "")
        check("path-stem and --flag terms never tie -> VACUOUS", line_for(out2, c13).startswith("VACUOUS"))
        check("revert that only crashes (NameError) -> COULD_NOT_CHECK",
              line_for(out2, c14).startswith("COULD_NOT_CHECK") and "crashed" in line_for(out2, c14))
        check("revert that only hangs -> COULD_NOT_CHECK, never VACUOUS",
              line_for(out2, c16).startswith("COULD_NOT_CHECK") and "timed out" in line_for(out2, c16))
        _, out3 = verdicts(c3, c4, "--budget", "0")
        check("exhausted run budget -> COULD_NOT_CHECK", line_for(out3, c4).startswith("COULD_NOT_CHECK")
              and "budget" in line_for(out3, c4))
    print(f"lesson_replay selftest: {'FAIL' if fails else 'PASS'} ({len(fails)} failed)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
