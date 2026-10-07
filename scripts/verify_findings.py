#!/usr/bin/env python3
"""Independent verification stage helper: batch candidate findings into verifier prompts, merge verdicts back.

  verify_findings.py prompts FINDINGS.json [--batch N] [--ref SHA]   -> JSON list of {batch, ids, prompt}
  verify_findings.py merge FINDINGS.json VERDICTS...                 -> JSON report on stdout
  verify_findings.py --selftest

FINDINGS.json is a list of objects with `file` and `text` (the same shape score_review.py reads); `id`,
`line` and `severity` are optional (missing ids become F1..Fn by position). Each verifier prompt goes to
a FRESH context (a subagent, or a separate pass when none exist) that sees only its batch and the code,
never the first pass's reasoning. A verifier answers with one JSON object per line:
`{"id": "F1", "verdict": "confirmed|refuted|unverified", "basis": "tool|model-only", "evidence": "file:line or command + output"}`;
prose around those lines is ignored. `basis: tool` means an external signal settled it (a read or grep of the
cited code, a run command, a test or linter result); `model-only` is a judgement with no such signal.

merge fails closed: a finding counts as `confirmed` only with a `confirmed` verdict, non-empty evidence AND
`basis: tool` (self-critique without an external signal degrades, so model-only and a missing basis never
settle anything); a missing, malformed, conflicting, or unknown-verdict answer is `unverified`, never dropped
and never promoted. Only a tool-backed `refuted` is dropped, and it is counted, not hidden.
Report: confirmed (reportable findings), unverified (listed separately), refuted_count, counts.
Verdict ids that match no finding are listed under `unknown_ids`. Exit 0 ok, 2 bad input. Stdlib only.
"""
import argparse
import json
import sys
from pathlib import Path

VERDICTS = ("confirmed", "refuted", "unverified")
PROMPT = """You are an independent verifier. You did not write these findings and have not seen the reviewer's reasoning. Treat each claim as false until the code proves it.
Target: the working tree{ref}. For EACH finding below, try to reproduce it: read the cited code and its callers, or run a minimal check/test (use the repo's review check runner when one exists). Then answer.
Prefer an external signal over your own judgement. `basis: tool` means your evidence quotes what a tool returned: the cited line you read, a grep hit, or the output of a command, test or linter you ran (a small probe of the exact shell or regex behaviour counts). `basis: model-only` means the conclusion rests on reasoning or recalled knowledge with no such quoted output; it is the last resort.
- confirmed: you reproduced it or can cite the exact `file:line` (or command + output) that proves it. Evidence is required.
- refuted: the code or a guard you can cite shows the claim is wrong, already handled, or not in the changed scope. Cite it.
- unverified: you could not settle it either way (say what is missing). Do not guess.
Output ONLY one JSON object per line, one per finding, no other text:
{{"id": "<id>", "verdict": "confirmed|refuted|unverified", "basis": "tool|model-only", "evidence": "<file:line or command + output>"}}

Findings:
{findings}
"""


def load(path):
    """Read a findings list; fill missing ids by position. Raises ValueError on a bad shape or duplicate ids."""
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(items, list) or not all(isinstance(f, dict) for f in items):
        raise ValueError("findings must be a JSON list of objects")
    out = [{**f, "id": str(f.get("id") or f"F{i}")} for i, f in enumerate(items, 1)]
    if len({f["id"] for f in out}) != len(out):
        raise ValueError("duplicate finding ids")
    return out


def prompts(findings, batch=5, ref=None):
    """Split findings into batches of `batch` and render one verifier prompt per batch."""
    batch = max(1, batch)
    res = []
    for n, i in enumerate(range(0, len(findings), batch), 1):
        grp = findings[i:i + batch]
        lines = [f'- {f["id"]}: {f.get("file", "?")}' + (f':{f["line"]}' if f.get("line") else "") + f' - {f.get("text", "")}' for f in grp]
        res.append({"batch": n, "ids": [f["id"] for f in grp],
                    "prompt": PROMPT.format(ref=f" at {ref}" if ref else "", findings="\n".join(lines))})
    return res


def parse_verdicts(text):
    """Pull `{"id", "verdict", ...}` objects out of a verifier's answer, ignoring surrounding prose."""
    out, dec, i = [], json.JSONDecoder(), text.find("{")
    while i != -1:
        try:
            o, end = dec.raw_decode(text, i)  # handles braces inside strings, e.g. "${VAR}" in evidence
        except ValueError:
            i, end = text.find("{", i + 1), None
            continue
        if isinstance(o, dict) and "id" in o and "verdict" in o:
            out.append(o)
        i = text.find("{", end)
    return out


def merge(findings, answers):
    """Fold verdict dicts into findings. Fail closed: only evidence-backed confirmed/refuted move a finding."""
    by_id = {}
    for a in answers:
        v, ev = str(a.get("verdict", "")).strip().lower(), str(a.get("evidence") or "").strip()
        ok = v in VERDICTS and ev and str(a.get("basis", "")).strip().lower() == "tool"
        by_id.setdefault(str(a["id"]), []).append((v, ev) if ok else ("unverified", ev))
    conf, unv, refuted = [], [], 0
    for f in findings:
        got = by_id.get(f["id"], [])
        kinds = {v for v, _ in got}
        v = kinds.pop() if len(kinds) == 1 else "unverified"  # missing or conflicting verifiers settle nothing
        if v == "confirmed":
            conf.append({**f, "verdict": v, "evidence": got[0][1]})
        elif v == "refuted":
            refuted += 1
        else:
            unv.append({**f, "verdict": "unverified"})
    return {"confirmed": conf, "unverified": unv, "refuted_count": refuted,
            "counts": {"candidates": len(findings), "confirmed": len(conf), "unverified": len(unv), "refuted": refuted},
            "unknown_ids": sorted(set(by_id) - {f["id"] for f in findings})}


def selftest():
    fs = [{"id": "F1", "file": "a.sh", "line": 3, "text": "x"}, {"id": "F2", "file": "b.sh", "text": "y"}, {"id": "K", "file": "c.sh", "text": "z"}]
    ps = prompts(fs, 2)
    ans = parse_verdicts('prose\n{"id":"F1","verdict":"confirmed","basis":"tool","evidence":"a.sh:3"}\n{"id":"F2","verdict":"confirmed","basis":"tool","evidence":""}')
    r = merge(fs, ans)
    return ([len(ps), ps[0]["ids"], ps[1]["ids"]] == [2, ["F1", "F2"], ["K"]] and "a.sh:3" in ps[0]["prompt"]
            and [f["id"] for f in r["confirmed"]] == ["F1"] and [f["id"] for f in r["unverified"]] == ["F2", "K"])


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["prompts", "merge"])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--batch", type=int, default=5)
    ap.add_argument("--ref")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        ok = selftest()
        print("verify_findings selftest:", "ok" if ok else "FAIL")
        return 0 if ok else 1
    if not a.cmd or not a.paths or (a.cmd == "merge" and len(a.paths) < 2):
        ap.error("need prompts FINDINGS.json | merge FINDINGS.json VERDICTS...")
    try:
        fs = load(a.paths[0])
        if a.cmd == "prompts":
            out = prompts(fs, a.batch, a.ref)
        else:
            out = merge(fs, [v for p in a.paths[1:] for v in parse_verdicts(Path(p).read_text(encoding="utf-8"))])
    except (OSError, ValueError) as e:
        print(f"verify_findings: bad input ({type(e).__name__}: {e})", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
