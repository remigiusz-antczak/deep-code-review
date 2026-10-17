#!/usr/bin/env python3
"""Held-out re-test driver for contribution and product-output-safety (PCSS only, $0).

  bench.py write   draw 30 fresh scenarios per skill from the blind writer briefs (never shows skill text)
  bench.py run ARM  ARM = v0 (unedited SKILL.md, frozen copy) or v1 (the shipped SKILL.md); both against the rival
Reuses scripts/rival_eval.py end to end (same generator, rubric-free judges, both orders, slot-1 gate, bootstrap seed 1);
the verdict rule is the one in PREREGISTERED.md, computed here from the harness output.
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent.parent / "scripts"))
import rival_eval as R

SKILLS = {"contribution": ("contribution_seeds.txt", "scripts/eval-fixtures/rival/contribution/brief.txt"),
          "product-output-safety": ("pos_seeds.txt", "pos_brief.txt")}


def write():
    for skill, (seeds_f, brief_f) in SKILLS.items():
        brief = (R.ROOT / brief_f).read_text() if brief_f.startswith("scripts") else (HERE / "prompts" / brief_f).read_text()
        seeds = [l for l in (HERE / "prompts" / seeds_f).read_text().splitlines() if l[:2].isdigit()]
        out = []
        for i in range(0, len(seeds), 10):
            use = seeds[i:i + 10]
            for _ in range(6):
                txt = R.chat(R.GEN_MODEL, "You write evaluation scenarios.", brief.replace("{N}", str(len(use))) + "\n" + "\n".join(use) + "\n", max_tokens=12000, temperature=0.7)
                arr = R.jparse(txt)
                if not isinstance(arr, list):  # writer ignored JSON: "NN text" paragraphs
                    bits = re.split(r"(?m)^(\d\d)[ \t]*\n?", txt)
                    arr = [{"id": a, "prompt": " ".join(b.split())} for a, b in zip(bits[1::2], bits[2::2]) if b.strip()]
                if isinstance(arr, list) and len(arr) == len(use) and all(isinstance(x, dict) and {"id", "prompt"} <= set(x) for x in arr):
                    out += [{"id": "n" + u[:2], "prompt": x["prompt"]} for u, x in zip(use, arr)]
                    break
            else:
                raise SystemExit(f"{skill}: writer failed for seeds {i}")
        (R.FIX / skill / "heldout30.json").write_text(json.dumps(out, indent=1) + "\n")
        print(skill, len(out))


def sens(res, d):
    """Amendment 1: score every scenario with BOTH judges on the cached outputs (reported, never the verdict). -> {judge: {n, win_rate, ci95, slot1}}"""
    d = next((d).glob("heldout30-*"))
    sc = R.load_scenarios(res["skill"], "heldout30")
    outs = {a: {x["id"]: (next((d / "outputs" / a).glob(x["id"] + "-*.txt"), None) or Path("/dev/null")).read_text() for x in sc} for a in R.ARMS}
    out = {}
    for m in R.JUDGES:
        vs = {x["id"]: [R.judge_one(m, x, a, b, d, outs) for a, b in (R.ARMS, R.ARMS[::-1])] for x in sc}
        v = [R.scenario_score([R.order_score(t, a) for t, a in zip(p, R.ARMS)]) for p in vs.values() if None not in p]
        rate = R.slot1_rate([t for p in vs.values() for t in p])
        out[m] = dict(n=len(v), win_rate=round(sum(v) / len(v), 3), ci95=[round(x, 3) for x in R.boot(v)], slot1=None if rate is None else round(rate, 3)) if v else None
    return out


def run(arm, out):
    for skill in SKILLS:
        orig = R.config(skill)
        perun = orig["perun"] if arm == "v1" else str(HERE / "frozen" / f"{skill}.v0.md")
        R.config = lambda s, o=orig, p=perun: {**o, "perun": p}
        res = R.run_skill(skill, "heldout30", "pcss", Path(out) / arm, 6, 0)
        R.config = lambda s: json.loads((R.FIX / s / "rival.json").read_text())
        v = list(res["per_scenario"].values())
        res["strict"] = {"win": v.count(1.0), "tie_or_split": v.count(0.5), "loss": v.count(0.0)}
        res["pass"] = bool(v) and len(v) >= 30 and res["ci95"][0] > 0.5
        res["sensitivity"] = sens(res, Path(out) / arm / skill)
        keys = ("judge", "slot1_rate", "n", "win_rate", "ci95", "strict", "pass", "sensitivity")
        (Path(out) / arm / skill / "verdict.json").write_text(json.dumps({k: res.get(k) for k in keys}, indent=1) + "\n")
        print(skill, arm, {k: res.get(k) for k in keys})


if __name__ == "__main__":
    write() if sys.argv[1] == "write" else run(sys.argv[2], sys.argv[3])
