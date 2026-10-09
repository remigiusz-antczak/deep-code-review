#!/usr/bin/env python3
"""Review benchmark runner: real bug-fix corpus, strict train/test split, reviewer arms, strict + verified precision.

  bench_corpus.py split IDS...                    print the deterministic split for case ids
  bench_corpus.py public-manifest --corpus D      manifest safe to commit (TEST ids hashed, SHAs dropped)
  bench_corpus.py run    --corpus D --arm A --runs R [--rep N] [--base RUN] [--split test] [--skill DIR] [--jobs N]
  bench_corpus.py verify --corpus D --arm A --out RUN [--split test]
  bench_corpus.py report --corpus D --out RUN [--split test]

Every `run` writes a fresh immutable run dir R/<arm>-<rep>-<UTC timestamp>/ made with mkdir (never reused: a second
driver that picks the same name is refused), holding manifest.json (model, skill SHA, settings) and, once every case
finished, a COMPLETE marker. `verify` and `report` read exactly one run dir and refuse one without COMPLETE.
`perun-gap` needs --base, a complete run dir of the perun arm; its records are copied in, the base stays untouched.

Corpus layout (one dir per case): change.patch (what the reviewer sees), ground-truth.json (score_review.py
format: one bug with a `match` regex), meta.json (url, licence, SHAs, label), optional context/ (pre-fix file
the verifier may read). manifest.json at the corpus root lists {id, split}.

Split rule: real cases sorted by sha256(id); the first len//3 are TRAIN, the rest TEST. A case already public
in this repository (the PR #1354 held-out fixture) is TRAIN by rule, never TEST. TEST ground truth must never
reach anyone tuning the skill: only the runner and the verifier read it.

Arms: perun (skill, one pass), perun-gap (the perun pass + a seeded gap-hunt pass, union; needs the perun arm run first), plain (no skill), tools
(shellcheck on shell cases, semgrep elsewhere, when installed). Reviewers are `claude -p` sessions with only
read tools, no user settings, and see change.patch alone. Verifier: a separate session reads the patch and the
pre-fix file and labels each strict-unmatched finding real | gt_same | not_a_bug | unverifiable (gt_same = same bug as
the reference, i.e. a matcher miss). Metrics: strict recall/precision (score_review.py), adjudicated recall
(verifier says gt_same), verified precision ((real + gt_same) / findings), cost and wall time. Stdlib only.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".claude/skills/deep-code-review/scripts"))
import score_review as sr  # noqa: E402

PRODUCER = """Review the change in ./change.patch (a diff of one or more source files; no git history exists, do not search outside this directory). Find real defects the change introduces: wrong behavior, unhandled edge cases, fail-open checks, injection, resource or data-loss bugs. Skip style nits. Write no files.
Your FINAL message must be ONLY a JSON array, no prose and no code fence: [{"file": "<basename>", "line": <int or null>, "severity": "high|medium|low", "text": "<the bug mechanism and a concrete failing input, one or two sentences>"}]. Use [] if you find nothing."""
PERUN = "Load and follow .claude/skills/deep-code-review/SKILL.md and apply its method end to end: read SKILL.md and every reference it routes DIFF-mode reviews to before you review. Review in DIFF mode. " + PRODUCER
GAP = """A first review of ./change.patch already reported these findings:
{seed}
Re-review the same change and hunt ONLY for defects the first pass missed; do not repeat or rephrase anything listed. Verify each candidate against the diff before reporting it. Write no files.
Your FINAL message must be ONLY a JSON array of the NEW findings, same shape as above: [{{"file": "<basename>", "line": <int or null>, "severity": "high|medium|low", "text": "<mechanism and failing input>"}}]. Use [] if nothing new."""
VERIFY = """You verify code-review findings. ./change.patch is the reviewed change; ./context/ holds the pre-fix version of the changed file(s). Write no files.
REFERENCE BUG (known real defect in this change): {bug}
For each finding below decide, by reading the code: "gt_same" ONLY if its mechanism is the reference bug (same root cause, any wording; naming the right file or a nearby symptom is not enough), "real" if it is a different genuine defect you can confirm from the code, "not_a_bug" if the code does not behave as claimed or it is style/by-design, "unverifiable" if the code cannot settle it.
FINDINGS:
{findings}
Your FINAL message must be ONLY a JSON array: [{{"i": <index>, "verdict": "real|gt_same|not_a_bug|unverifiable", "reason": "<one sentence>"}}]."""
GAP_SKILL = "Load and follow .claude/skills/deep-code-review/SKILL.md for method. "
ARMS = ("perun", "perun-gap", "plain", "tools")


def split_ids(real, public=()):
    order = sorted(real, key=lambda i: hashlib.sha256(i.encode()).hexdigest())
    n = len(real) // 3
    return {**{i: "train" for i in order[:n]}, **{i: "test" for i in order[n:]}, **{i: "train" for i in public}}


def public_manifest(man):
    """Manifest safe to commit: TEST entries get an opaque hashed id and lose the fix/intro SHAs (they point at the answer)."""
    out = []
    for m in man:
        if m["split"] == "test":
            real = m["id"]
            m = {k: v for k, v in m.items() if k not in ("fix_sha", "intro_sha", "id")}
            m["id"] = "test-" + hashlib.sha256(("test:" + real).encode()).hexdigest()[:10]
        out.append(m)
    return sorted(out, key=lambda m: (m["split"] == "test", m["id"]))  # hashed ids sorted: order must not leak real names


MODEL = "sonnet"
CLAUDE_ARGS = ["-p", "--setting-sources", "project,local", "--output-format", "json",
               "--no-session-persistence", "--allowedTools", "Read", "Grep", "Glob"]


def claude(prompt, cwd, model=MODEL):
    """One read-only `claude -p` session; returns (final text, cost usd, seconds, turns, error).

    No user settings, no persistence. `error` is "" on success; a timeout, spawn failure, non-zero exit, unparsable
    JSON, an `is_error` result or empty output all set it, so the caller records the case as errored, never as a miss."""
    t = time.time()
    try:
        p = subprocess.run(["claude", *CLAUDE_ARGS[:1], "--model", model, *CLAUDE_ARGS[1:]],
                           input=prompt, capture_output=True, text=True, cwd=cwd, timeout=1500)
    except (subprocess.TimeoutExpired, OSError) as e:
        return "", 0.0, time.time() - t, 0, type(e).__name__
    try:
        j = json.loads(p.stdout)
    except ValueError:
        return "", 0.0, time.time() - t, 0, f"exit {p.returncode}, unparsable output"
    txt, cost, turns = j.get("result") or "", float(j.get("total_cost_usd") or 0), int(j.get("num_turns") or 0)
    err = "claude reported an error" if (j.get("is_error") or p.returncode) else "" if txt.strip() else "empty output"
    return txt, cost, time.time() - t, turns, err


def parse_array(text, key="text"):
    """Last top-level JSON array in text, filtered to dicts carrying `key`; None when no array parses (a valid [] is [])."""
    for m in reversed([m.start() for m in re.finditer(r"\[", text)]):
        try:
            v = json.loads(text[m:text.rindex("]") + 1])
        except ValueError:
            continue
        if isinstance(v, list):
            return [x for x in v if isinstance(x, dict) and key in x]
    return None


def cases(corpus, split):
    man = {m["id"]: m["split"] for m in json.loads((corpus / "manifest.json").read_text())}
    return sorted(i for i, s in man.items() if s == split and (corpus / i).is_dir())


def workspace(corpus, cid, skill):
    w = Path(tempfile.mkdtemp(prefix="bench-"))  # opaque name: a path must never carry the case id (it describes the bug)
    shutil.copy(corpus / cid / "change.patch", w)
    if skill:
        shutil.copytree(skill, w / ".claude/skills/deep-code-review")
    return w


def tool_findings(corpus, cid):
    meta = json.loads((corpus / cid / "meta.json").read_text())
    out = []
    for f in meta["files"]:
        p = corpus / cid / "context" / Path(f).name
        if meta["lang"] == "shell" and shutil.which("shellcheck"):
            r = subprocess.run(["shellcheck", "-f", "json", str(p)], capture_output=True, text=True)
            out += [{"file": Path(f).name, "line": x["line"], "text": f"SC{x['code']}: {x['message']}"} for x in json.loads(r.stdout or "[]")]
        elif meta["lang"] != "shell" and shutil.which("semgrep"):
            r = subprocess.run(["semgrep", "--config", "p/default", "--metrics", "off", "--json", "--quiet", str(p)], capture_output=True, text=True)
            try:
                out += [{"file": Path(f).name, "line": x["start"]["line"], "text": x["check_id"] + ": " + x["extra"]["message"]} for x in json.loads(r.stdout or "{}").get("results", [])]
            except ValueError:
                pass
    return out


def ask(prompt, w, key="text"):
    """claude() + parse_array(): (items, cost, seconds, turns, raw, error); error also set when no JSON array came back."""
    txt, cost, sec, turns, err = claude(prompt, w)
    items = None if err else parse_array(txt, key)
    return items, cost, sec, turns, txt, err or ("" if items is not None else "no JSON array in output")


def run_case(corpus, cid, arm, out, skill):
    """Run one arm on one case and write out/<arm>/<cid>.json. A failed case carries `error` and no findings."""
    d = out / arm; d.mkdir(parents=True, exist_ok=True)
    bad = lambda e: dict(id=cid, arm=arm, findings=[], cost=0.0, seconds=0.0, error=e)
    if arm == "tools":
        t = time.time()
        rec = dict(id=cid, arm=arm, findings=tool_findings(corpus, cid), cost=0.0, seconds=round(time.time() - t, 2), error="")
    elif arm == "perun-gap" and not (out / "perun" / f"{cid}.json").exists():
        rec = bad(f"missing perun output for {cid}: run --arm perun first")
    else:
        w = workspace(corpus, cid, skill if arm.startswith("perun") else None)
        try:
            if arm == "perun-gap":  # pass 1 = the perun arm's record; this adds the seeded gap pass
                p1 = json.loads((out / "perun" / f"{cid}.json").read_text())
                if p1.get("error"):
                    rec = bad("perun pass errored: " + p1["error"])
                else:
                    new, c2, s2, t2, raw2, err = ask(GAP_SKILL + GAP.format(seed=json.dumps(p1["findings"], indent=1)), w)
                    rec = dict(id=cid, arm=arm, findings=p1["findings"] + (new or []), cost=round(p1["cost"] + c2, 4),
                               seconds=round(p1["seconds"] + s2, 1), turns=p1["turns"] + t2, raw=p1["raw"] + "\n=====GAP=====\n" + raw2, error=err)
            else:
                f, cost, sec, turns, raw, err = ask(PERUN if arm == "perun" else PRODUCER, w)
                rec = dict(id=cid, arm=arm, findings=f or [], cost=round(cost, 4), seconds=round(sec, 1), turns=turns, raw=raw, error=err)
        finally:
            shutil.rmtree(w, ignore_errors=True)
    (d / f"{cid}.json").write_text(json.dumps(rec, indent=1))
    return cid, ("ERROR " + rec["error"]) if rec["error"] else len(rec["findings"]), rec["cost"]


def verify_case(corpus, cid, arm, out):
    """Label every finding of out/<arm>/<cid>.json (blind to the matcher); a verifier failure sets `verify_error` (case leaves the metrics)."""
    p = out / arm / f"{cid}.json"
    if not p.exists():
        return cid, f"ERROR no {arm} output to verify"
    rec = json.loads(p.read_text())
    if rec.get("error"):
        return cid, "ERROR skipped, run errored: " + rec["error"]
    truth = json.loads((corpus / cid / "ground-truth.json").read_text())
    extras = list(enumerate(rec["findings"]))
    rec["verdicts"] = {}; rec.pop("verify_error", None)
    if extras:
        w = Path(tempfile.mkdtemp(prefix="verify-"))
        try:
            shutil.copy(corpus / cid / "change.patch", w)
            if (corpus / cid / "context").is_dir():
                shutil.copytree(corpus / cid / "context", w / "context")
            bug = "; ".join(b["bug"] for b in truth["bugs"])
            listing = "\n".join(f"{i}. [{f.get('file')}:{f.get('line')}] {f.get('text')}" for i, f in extras)
            vs, cost, _, _, _, err = ask(VERIFY.format(bug=bug, findings=listing), w, "verdict")
            rec["verify_cost"] = round(cost, 4)
            if err:
                rec["verify_error"] = err
            for v in vs or []:
                rec["verdicts"][str(v.get("i"))] = {"verdict": v.get("verdict"), "reason": v.get("reason")}
        finally:
            shutil.rmtree(w, ignore_errors=True)
    p.write_text(json.dumps(rec, indent=1))
    return cid, ("ERROR " + rec["verify_error"]) if rec.get("verify_error") else len(extras)


def metrics(corpus, ids, arm, out):
    """Aggregate one arm over `ids`. Errored cases (run or verifier failure) leave every denominator and count in `errors`.

    recall_strict / precision_strict use the regex matcher; recall_adjudicated counts a case when the verifier labelled a
    finding gt_same; precision_verified = findings labelled real or gt_same / findings (matcher-independent)."""
    n_bug = hit = adj = nf = matched = good = k = err = 0; cost = sec = vcost = 0.0
    for cid in ids:
        p = out / arm / f"{cid}.json"
        rec = json.loads(p.read_text()) if p.exists() else {"error": "no output"}
        if rec.get("error") or rec.get("verify_error") or ("verdicts" not in rec and arm != "tools" and rec["findings"]):
            err += 1
            continue
        k += 1; truth = json.loads((corpus / cid / "ground-truth.json").read_text())
        s = sr.score(truth, rec["findings"]); v = rec.get("verdicts", {}).values()
        n_bug += s["bugs"]; hit += len(s["hit"]); nf += s["findings"]
        adj += s["bugs"] if any(x.get("verdict") == "gt_same" for x in v) else 0
        matched += sum(1 for f in rec["findings"] if sr.score(truth, [f])["hit"])
        good += sum(1 for x in v if x.get("verdict") in ("real", "gt_same"))
        cost += rec["cost"]; sec += rec["seconds"]; vcost += rec.get("verify_cost", 0)
    r = lambda a, b: round(a / b, 3) if b else None
    return dict(arm=arm, cases=k, errors=err, bugs=n_bug, findings=nf, recall_strict=r(hit, n_bug), recall_adjudicated=r(adj, n_bug),
                precision_strict=r(matched, nf), precision_verified=r(good, nf), cost_usd=round(cost, 3),
                verify_cost_usd=round(vcost, 3), seconds=round(sec, 1))


def tree_sha(skill):
    """sha256 over the sorted relative paths and bytes of the skill dir; None for an arm without a skill."""
    if not skill:
        return None
    h = hashlib.sha256()
    for f in sorted(p for p in Path(skill).rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        h.update(f.relative_to(skill).as_posix().encode() + b"\0" + f.read_bytes())
    return h.hexdigest()


def start_run(runs, arm, rep, skill=None, split="test", jobs=1, base=None):
    """Create runs/<arm>-<rep>-<UTC timestamp>/ with mkdir (no exist_ok) and write manifest.json; returns the new dir.

    Raises FileExistsError when that name is taken, so two drivers can never share a run dir. Side effect: creates
    `runs` if missing."""
    runs = Path(runs); runs.mkdir(parents=True, exist_ok=True)
    d = runs / f"{arm}-{rep}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    d.mkdir()
    man = dict(arm=arm, rep=rep, model=MODEL, claude_args=CLAUDE_ARGS, skill_sha256=tree_sha(skill), split=split, jobs=jobs,
               base=str(base) if base else None, started=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (d / "manifest.json").write_text(json.dumps(man, indent=1))
    return d


def require_complete(run):
    """Refuse anything that is not one finished run dir (manifest + COMPLETE marker)."""
    if not ((run / "manifest.json").is_file() and (run / "COMPLETE").is_file()):
        raise SystemExit(f"{run}: not a complete run dir (needs manifest.json and COMPLETE); refusing to read it")
    return run


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", choices=("split", "public-manifest", "run", "verify", "report"))
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--corpus", type=Path); ap.add_argument("--out", type=Path); ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--runs", type=Path); ap.add_argument("--rep", type=int, default=1); ap.add_argument("--base", type=Path)
    ap.add_argument("--split", default="test"); ap.add_argument("--skill", type=Path); ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)
    if a.cmd == "split":
        print(json.dumps(split_ids(a.ids), indent=1)); return 0
    if a.cmd == "public-manifest":
        print(json.dumps(public_manifest(json.loads((a.corpus / "manifest.json").read_text())), indent=1)); return 0
    ids = cases(a.corpus, a.split)
    if a.cmd == "run":
        if not a.runs:
            ap.error("run needs --runs")
        if a.arm == "perun-gap":
            if not a.base:
                ap.error("perun-gap needs --base, a complete perun run dir")
            require_complete(a.base)
        try:
            a.out = start_run(a.runs, a.arm, a.rep, a.skill, a.split, a.jobs, a.base)
        except FileExistsError as e:
            raise SystemExit(f"refusing to start: run dir exists: {e.filename}")
        if a.arm == "perun-gap":
            shutil.copytree(a.base / "perun", a.out / "perun")
        print("run dir:", a.out, flush=True)
    else:
        require_complete(a.out)
    if a.cmd == "report":
        print(json.dumps([metrics(a.corpus, ids, arm, a.out) for arm in ARMS if (a.out / arm).is_dir()], indent=1)); return 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        fn = (lambda c: run_case(a.corpus, c, a.arm, a.out, a.skill)) if a.cmd == "run" else (lambda c: verify_case(a.corpus, c, a.arm, a.out))
        for r in ex.map(fn, ids):
            print(*r, flush=True)
    if a.cmd == "run":
        (a.out / "COMPLETE").write_text(f"{len(ids)} cases\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
