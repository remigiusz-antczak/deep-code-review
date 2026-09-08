#!/usr/bin/env python3
"""Recommend which overlay skills a target repo should install.

Inspects a project directory and prints a pack. Never writes. The owner
decides; an agent may recommend --full but must not install delivery into
a repo that already has another delivery pack without saying so.

Stdlib only. Bounded walk — no recursive glob of the whole tree.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}

DELIVERY_DIR_MARKERS = {
    "superpowers",
    "gstack",
    "spec-kit",
    ".specify",
}
WEB_FILES = {
    "package.json",
    "next.config.js",
    "next.config.mjs",
    "vite.config.ts",
    "vite.config.js",
    "index.html",
}
API_FILES = {
    "openapi.yaml",
    "openapi.yml",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
}
IAC_FILES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "kustomization.yaml",
    "terraform.tf",
}
IAC_DIR_NAMES = {"terraform", "helm", "charts", "infra", "deploy"}
AGENT_FILES = {"SKILL.md", "AGENTS.md", "CLAUDE.md"}
REVIEW_PATHS = (
    ".claude/skills/deep-code-review/SKILL.md",
    ".agents/skills/deep-code-review/SKILL.md",
    ".cursor/skills/deep-code-review/SKILL.md",
)


def walk(root: Path, max_depth: int = 3) -> list[Path]:
    out: list[Path] = []
    def _walk(cur: Path, depth: int) -> None:
        try:
            children = list(cur.iterdir())
        except OSError:
            return
        for child in children:
            if child.name in SKIP_DIRS or child.name.startswith("skill-backups"):
                continue
            out.append(child)
            if child.is_dir() and depth < max_depth:
                _walk(child, depth + 1)
    _walk(root, 0)
    return out


def recommend(root: Path) -> dict:
    entries = walk(root)
    names = {p.name for p in entries}
    review_present = any((root / m).is_file() for m in REVIEW_PATHS)
    other_delivery = bool(names & DELIVERY_DIR_MARKERS) or any(
        "superpowers" in p.parts or "gstack" in p.parts for p in entries
    )
    web = bool(names & WEB_FILES)
    api = bool(names & API_FILES)
    iac = bool(names & IAC_FILES) or bool(names & IAC_DIR_NAMES)
    agentic = bool(names & AGENT_FILES)

    skills = ["deep-code-review"]
    reasons = ["review bar — always"]
    flags: list[str] = []

    if other_delivery:
        reasons.append(
            "another delivery pack detected — do not also install agentic-delivery"
        )
    elif web or api or iac:
        skills.append("agentic-delivery")
        flags.append("--with-delivery")
        reasons.append(
            "multi-file product / service / infra — gated delivery pays"
        )
    elif agentic:
        reasons.append(
            "agent-instruction surface only — review is enough unless a "
            "feature spans QA+security"
        )

    if "agentic-delivery" in skills or (agentic and not other_delivery):
        if "idea-critic" not in skills:
            skills.append("idea-critic")
            flags.append("--with-critic")
            reasons.append(
                "plans will be proposed — attack them before the owner sees them"
            )

    if "agentic-delivery" in skills and "idea-critic" in skills:
        pack_flag = "--full"
    elif flags:
        pack_flag = " ".join(flags)
    else:
        pack_flag = "(default — review only)"

    return {
        "review_present": review_present,
        "other_delivery": other_delivery,
        "skills": skills,
        "pack_flag": pack_flag,
        "reasons": reasons,
        "shape": {"web": web, "api": api, "iac": iac, "agentic": agentic},
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="project directory to inspect")
    args = parser.parse_args(argv[1:])
    root = Path(args.target).resolve()
    if not root.is_dir():
        print(f"recommend: not a directory: {root}", file=sys.stderr)
        return 2
    rec = recommend(root)
    print(f"target: {root}")
    print(
        f"shape: web={rec['shape']['web']} api={rec['shape']['api']} "
        f"iac={rec['shape']['iac']} agentic={rec['shape']['agentic']}"
    )
    print(f"review already installed: {rec['review_present']}")
    print(f"other delivery pack: {rec['other_delivery']}")
    print(f"recommend skills: {', '.join(rec['skills'])}")
    print(f"install flag: ./install.sh {rec['pack_flag']} {root}")
    print("why:")
    for r in rec["reasons"]:
        print(f"  - {r}")
    print()
    print("Owner decides. Agent may recommend --full. Do not install")
    print("overlays without a yes. Caveman is not in this pack — see")
    print("https://github.com/JuliusBrussee/caveman if compressed chat")
    print("is wanted; persisted artifacts stay normal English.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
