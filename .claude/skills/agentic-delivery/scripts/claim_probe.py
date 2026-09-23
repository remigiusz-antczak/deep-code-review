#!/usr/bin/env python3
"""claim_probe.py — pre-write collision probe: GO or NO-GO before starting an item.

WHY THIS EXISTS (the failure it closes)
---------------------------------------
Reading the coordination thread and eyeballing open PRs by hand before every
claim is skipped under volume, and a claim can lag its own PR: two sessions on
two machines started the same item because neither check was run (#597,
#1102). This script is that check as one command. Before a write lane or an
exclusive step, it compares what you plan to touch against:

  1. live board CLAIMs — the board issue folded by board_state.fold (the one
     TTL implementation: an expired claim does not block, a renewed one does;
     your own claims, named by --agent, are skipped) — and the latest board
     AUDIT verdict on the item you name: `done` or `na` is NO-GO, because a
     peer already measured it as nothing to build (#1071). A fresh AUDIT
     `verdict:gap` supersedes it once a re-measure shows otherwise;
  2. every open PR, drafts included — its full, paginated file list against
     --paths, its title and head branch against --keyword, and its title and
     body against any `#<n>` --ref;
  3. every pushed branch with no open PR — its name against --keyword and its
     changed files (compare against the default branch) against --paths.

It prints GO, or NO-GO with one evidence line per collision (the claim and
holder, the PR number and file, or the branch and file).

MATCHING
--------
--paths takes files, directories, or fnmatch globs (`*` also crosses `/`;
`**/` may match zero directories). Two literal paths collide when equal or
when one is a directory prefix of the other. A glob and a literal collide when
the glob matches the literal, or the literal and the glob's fixed prefix nest
either way (`src/lib` vs `src/**/*.py`, `docs` vs `*.md`: a literal may be a
directory). A PR or branch file is known to be a file, so for it only a direct
match counts. Two globs collide when their fixed prefixes nest — conservative,
so it can say NO-GO for two disjoint globs under one directory, never GO for
overlapping ones. A claim ref collides when it equals a --ref token (an issue
`#<n>` or bare `<n>`, or a label such as an exclusive-role seat), when an item
claim `#<n>` equals a --keyword `<n>` or `#<n>`, or when it overlaps a --paths
entry. With no --ref at all, every live item claim `#<n>` is NO-GO evidence:
paths and keywords cannot say which item you are starting, so name it.

FAIL CLOSED
-----------
Any `gh` error, undecodable output, a board comment list shorter than the
issue's own count, a PR file list at GitHub's 3000-file cap, a branch compare
at its 300-file cap, or more un-PR'd branches than --max-branches exits 2 and
prints no verdict. Exit 2 means "not verified", never GO.

LIMITS: it sees only what reached the forge. A peer's local-only worktree with
no claim, branch, or PR is invisible (dev-env-ownership.md): claim first. Peer
text (titles, branch names, file names) is printed through board_common's
snippet sanitiser, so it cannot inject terminal escapes.

USAGE
-----
  claim_probe.py --repo OWNER/NAME --issue N --ref '#123' --paths web/** [--paths api/x.py]
                 [--keyword theme] [--agent my-id]
                 [--ignore-pr 7] [--ignore-branch my-branch] [--max-branches 50]
  claim_probe.py --selftest

Exit codes: 0 GO; 1 NO-GO (evidence printed); 2 error / not verified.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatchcase
from urllib.parse import quote, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_common as bc  # noqa: E402  (sibling module, path set above)
import board_state as bs  # noqa: E402

GO = 0
NOGO = 1
ERROR = 2

MAX_PR_FILES = 3000  # GitHub returns at most 3000 files for one pull request
MAX_COMPARE_FILES = 300  # GitHub's compare endpoint lists at most 300 files
DEFAULT_MAX_BRANCHES = 50
_WILD = "*?["


def is_glob(path: str) -> bool:
    """True iff `path` holds an fnmatch wildcard. Pure."""
    return any(ch in path for ch in _WILD)


def norm(path: str) -> str:
    """Strip a leading `./` and trailing `/` so `web/` and `web` compare equal; `.` is the whole repo. Pure."""
    path = path.strip()
    while path.startswith("./"):
        path = path[2:]
    path = path.rstrip("/")
    return "*" if path == "." else path


def fixed_root(glob: str) -> str:
    """The directory part of `glob` before its first wildcard ('' = repo root). Pure."""
    head = glob[: min(glob.index(ch) for ch in _WILD if ch in glob)]
    return head.rsplit("/", 1)[0] if "/" in head else ""


def _under(path: str, root: str) -> bool:
    return root == "" or path == root or path.startswith(root + "/")


def overlaps(a: str, b: str, a_is_file: bool = False) -> bool:
    """True iff paths/globs `a` and `b` can name a common file (see MATCHING). Pure.

    A literal of unknown kind may be a directory, so it also collides with a
    glob whose fixed root contains it (`src/lib` vs `src/**/*.py`, `docs` vs
    `*.md`). Pass `a_is_file=True` when `a` is known to be a file (a PR or
    compare entry): nothing sits beneath a file, so only a direct match counts.
    """
    a, b = norm(a), norm(b)
    if not a or not b:
        return False
    ga, gb = is_glob(a), is_glob(b)
    if not ga and not gb:
        return _under(a, b) or _under(b, a)
    if ga and gb:
        ra, rb = fixed_root(a), fixed_root(b)
        return _under(ra, rb) or _under(rb, ra)
    glob, lit = (a, b) if ga else (b, a)
    zero_dir = glob.replace("/**/", "/").removeprefix("**/")
    if fnmatchcase(lit, glob) or fnmatchcase(lit, zero_dir):
        return True
    may_be_dir = not (a_is_file and lit == a)
    return may_be_dir and (_under(fixed_root(glob), lit) or _under(lit, fixed_root(glob)))


def _cites(text: str, ref: str) -> bool:
    """True iff `text` cites issue ref `#<n>` as a whole token (so #11 never matches #110). Pure."""
    return bool(re.search(rf"(?<![0-9A-Za-z_]){re.escape(ref)}(?![0-9])", text or ""))


def _item_ref(token: str):
    """`#<n>` for an issue ref written `#<n>` or bare `<n>`, else None. Pure.

    So `--ref 1102`, `--keyword 1102`, and a claim `#1102` all name one item;
    a leading zero is dropped (`#01102` is `#1102`).
    """
    m = re.fullmatch(r"#?([0-9]+)", (token or "").strip())
    return f"#{int(m.group(1))}" if m else None


def _kw_hits(text: str, keywords) -> list:
    low = (text or "").lower()
    return [k for k in keywords if k.lower() in low]


def _show(text: str, limit: int = 80) -> str:
    return bc.snippet(text, False, limit) or "-"


def probe(repo: str, issue: int, paths, refs, keywords, agent: str, ignore_prs, ignore_branches,
          max_branches: int, now: datetime, runner) -> tuple:
    """Run every check; return `(evidence_lines, counts)`. NO-GO iff evidence is non-empty.

    Side-effects: `gh api` reads only, through `runner` (the board issue and
    its comments, the repo, open PRs and their file lists, branches, and one
    compare per un-PR'd branch when --paths is set). Raises bc.ForgeError on
    any failed, malformed, or capped read — the caller exits 2.
    """
    evidence, counts = [], {"claims": 0, "prs": 0, "branches": 0}
    _, comments = bs.read_board(repo, issue, runner)
    kw_items = {_item_ref(k) for k in keywords} - {None}
    state = bs.fold(comments, now)
    for ref, au in sorted(state["audits"].items()):
        item = _item_ref(ref) if ref.startswith("#") else None
        if au["verdict"] != "gap" and (ref in refs or (item and (item in refs or item in kw_items))):
            evidence.append(f"audit  {_show(ref)} verdict:{au['verdict']} at {au['sha']} by agent:{au['agent']} "
                            f"(board comment {au['id']}): a peer measured nothing to build; if that is stale, "
                            "re-measure and post AUDIT verdict:gap before starting")
    for ref, cl in sorted(state["claims"].items()):
        if cl["expired"] or cl["agent"] == agent:
            continue
        counts["claims"] += 1
        held = (f"claim  {_show(ref)} held by agent:{cl['agent']} until {bc.format_ts(cl['expires'])} "
                f"(board comment {cl['id']})")
        item = _item_ref(ref) if ref.startswith("#") else None
        named = ref in refs or (item and (item in refs or item in kw_items))
        if named or (not ref.startswith("#") and any(overlaps(ref, p) for p in paths)):
            evidence.append(held)
        elif item and not refs:
            # Paths and keywords cannot say which item you are starting; an item
            # claim is only ruled out by naming your own item with --ref.
            evidence.append(f"{held}: no --ref names your item, so it cannot be ruled out "
                            f"(re-run with --ref '#<n>')")

    base = f"repos/{repo}"
    default = bc.gh_object(runner, base).get("default_branch")
    if not isinstance(default, str) or not default:
        raise bc.ForgeError(f"{base} returned no default_branch")
    pr_heads = set()
    for pr in bc.gh_list(runner, f"{base}/pulls?state=open&per_page=100"):
        num, head = pr.get("number"), (pr.get("head") or {}).get("ref") or ""
        head_repo = ((pr.get("head") or {}).get("repo") or {}).get("full_name") or ""
        if head_repo.lower() == repo.lower():  # a fork's same-named head must not hide our branch
            pr_heads.add(head)
        if num in ignore_prs:
            continue
        counts["prs"] += 1
        tag = f"#{num}{' draft' if pr.get('draft') else ''} {_show(pr.get('title'), 60)!r}"
        why = [f"keyword {k!r}" for k in _kw_hits(f"{pr.get('title')} {head}", keywords)]
        why += [f"cites {r}" for r in refs if r.startswith("#") and _cites(f"{pr.get('title')}\n{pr.get('body')}", r)]
        if paths:
            files = [f.get("filename", "") for f in bc.gh_list(runner, f"{base}/pulls/{num}/files?per_page=100")]
            if len(files) >= MAX_PR_FILES:
                raise bc.ForgeError(f"PR #{num} lists {len(files)} files (GitHub cap {MAX_PR_FILES}): cannot rule it out")
            why += [_show(f) for f in files if any(overlaps(f, p, a_is_file=True) for p in paths)][:3]
        if why:
            evidence.append(f"pr     {tag}: {', '.join(why)}")

    branches = [b.get("name", "") for b in bc.gh_list(runner, f"{base}/branches?per_page=100")]
    todo = [b for b in branches if b and b != default and b not in pr_heads and b not in ignore_branches]
    if paths and len(todo) > max_branches:
        raise bc.ForgeError(f"{len(todo)} branches have no open PR (over --max-branches {max_branches}): "
                            "raise the cap or prune stale branches")
    for name in todo:
        counts["branches"] += 1
        why = [f"keyword {k!r}" for k in _kw_hits(name, keywords)]
        if paths:
            cmp_path = f"{base}/compare/{quote(default, safe='/')}...{quote(name, safe='/')}"
            files = [f.get("filename", "") for f in bc.gh_object(runner, cmp_path).get("files") or []]
            if len(files) >= MAX_COMPARE_FILES:
                raise bc.ForgeError(f"branch {_show(name)} compare lists {len(files)} files (cap {MAX_COMPARE_FILES})")
            why += [_show(f) for f in files if any(overlaps(f, p, a_is_file=True) for p in paths)][:3]
        if why:
            evidence.append(f"branch {_show(name)} (no PR): {', '.join(why)}")
    return evidence, counts


def run(args, runner, out, err) -> int:
    """Validate inputs, run the probe, print the verdict. Returns the exit code."""
    paths = [norm(p) for p in args.paths if norm(p)]
    refs = {_item_ref(r) or r.strip() for r in args.ref if r.strip()}  # `1102` and `#1102` name one item
    keywords = [k.strip() for k in args.keyword if k.strip()]  # an empty keyword would match everything
    if not (args.repo and bc.validate_repo(args.repo) and args.issue and args.issue > 0):
        err.write("claim_probe: --repo OWNER/NAME and --issue N (>0, the board) are required\n")
        return ERROR
    if not (paths or refs or keywords):
        err.write("claim_probe: give at least one --paths, --ref, or --keyword; nothing to probe is not GO\n")
        return ERROR
    try:
        now = bc.parse_ts(args.now) if args.now else datetime.now(timezone.utc).replace(microsecond=0)
    except ValueError:
        err.write("claim_probe: --now must be YYYY-MM-DDTHH:MM:SSZ\n")
        return ERROR
    try:
        evidence, counts = probe(args.repo, args.issue, paths, refs, keywords, args.agent or "",
                                 set(args.ignore_pr), set(args.ignore_branch), args.max_branches, now, runner)
    except (bc.ForgeError, KeyError, TypeError, ValueError, AttributeError) as exc:
        err.write(f"claim_probe: {exc}; NOT VERIFIED (exit 2, do not start)\n")
        return ERROR
    seen = f"{counts['claims']} live claims, {counts['prs']} open PRs, {counts['branches']} un-PR'd branches checked"
    if evidence:
        out.write(f"claim_probe: NO-GO — {len(evidence)} collision(s) ({seen})\n")
        out.write("".join(f"  {line}\n" for line in evidence))
        return NOGO
    out.write(f"claim_probe: GO — nothing collides ({seen})\n")
    return GO


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser (shared by main and the selftest)."""
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--repo")
    p.add_argument("--issue", type=int, help="the coordination board issue")
    p.add_argument("--paths", action="append", default=[], help="planned file, directory, or glob (repeatable)")
    p.add_argument("--ref", action="append", default=[],
                   help="your item or role ref, e.g. '#123' or a label (repeatable); "
                        "without one, any live item claim is NO-GO")
    p.add_argument("--keyword", action="append", default=[], help="case-insensitive match on PR titles/branches")
    p.add_argument("--agent", help="your board agent id; your own claims are skipped")
    p.add_argument("--ignore-pr", action="append", type=int, default=[], help="your own PR number (repeatable)")
    p.add_argument("--ignore-branch", action="append", default=[], help="your own branch (repeatable)")
    p.add_argument("--max-branches", type=int, default=DEFAULT_MAX_BRANCHES)
    p.add_argument("--now", help="evaluate claim expiry at this UTC time; default: now")
    p.add_argument("--selftest", action="store_true")
    return p


# --------------------------------------------------------------------------
# selftest (offline: a fake forge answers every gh call)
# --------------------------------------------------------------------------

T0 = "2026-01-05T10:00:00Z"
REPO = "o/r"


class FakeForge(bc.FakeGh):
    """bc.FakeGh (board issue + comments) plus the repo, PR, branch, and compare reads."""

    def __init__(self, comments=(), prs=(), files=None, branches=(), compare=None):
        super().__init__(list(comments))
        self.prs, self.files, self.branches, self.compare = list(prs), dict(files or {}), list(branches), dict(compare or {})
        self.count_override = None

    def __call__(self, args, cwd=None):
        if self.fail:
            self.calls.append(list(args))
            return 1, "", "HTTP 502: simulated outage"
        if len(args) >= 3 and args[:2] == ["gh", "api"]:
            path = urlsplit(args[-1]).path
            rows = None
            if args[2] == "--paginate":
                if path == f"repos/{REPO}/pulls":
                    rows = self.prs
                elif m := re.fullmatch(rf"repos/{REPO}/pulls/(\d+)/files", path):
                    rows = [{"filename": f} for f in self.files.get(int(m.group(1)), [])]
                elif path == f"repos/{REPO}/branches":
                    rows = [{"name": b} for b in self.branches]
                if rows is not None:
                    self.calls.append(list(args))
                    pages = [rows[i : i + bc.PAGE_SIZE] for i in range(0, len(rows), bc.PAGE_SIZE)] or [[]]
                    return 0, "".join(json.dumps(p) for p in pages), ""
            elif len(args) == 3:
                if path == f"repos/{REPO}":
                    self.calls.append(list(args))
                    return 0, json.dumps({"default_branch": "main"}), ""
                if path.startswith(f"repos/{REPO}/compare/main..."):
                    self.calls.append(list(args))
                    name = path.split("...", 1)[1]
                    return 0, json.dumps({"files": [{"filename": f} for f in self.compare.get(name, [])]}), ""
                if path == f"repos/{REPO}/issues/1" and self.count_override is not None:
                    self.calls.append(list(args))
                    return 0, json.dumps({"comments": self.count_override, "body": ""}), ""
        return super().__call__(args, cwd)


def _c(cid: int, minutes: int, body: str) -> dict:
    return bc.make_comment(cid, body, bc.format_ts(bc.parse_ts(T0) + timedelta(minutes=minutes)))


def _forge(**kw) -> FakeForge:
    """Baseline world: beta holds `web` (ttl 60) and the `merge` seat; draft PR #42 on api/x.py, no claim on it."""
    comments = kw.pop("comments", [
        _c(1, 0, "[agent:beta] CLAIM refs:web,merge ttl:60\ntaking the web lane and the merge seat"),
        _c(2, 1, "[agent:gamma] CLAIM refs:docs/old ttl:5\nshort one, long expired by now"),
    ])
    prs = kw.pop("prs", [{"number": 42, "draft": True, "title": "Tighten the parser", "body": "Closes #1102",
                          "head": {"ref": "lane-api", "repo": {"full_name": REPO}}}])
    files = kw.pop("files", {42: ["api/x.py", "api/y.py"]})
    return FakeForge(comments, prs, files, kw.pop("branches", ["main", "lane-api", "feat-lib"]),
                     kw.pop("compare", {"feat-lib": ["lib/z.py"]}))


def _probe(forge, *argv, now_min: int = 10):
    """Run the CLI against `forge`; return (rc, stdout, stderr)."""
    out, err = bs._Sink(), bs._Sink()
    args = build_parser().parse_args(["--repo", REPO, "--issue", "1", "--now",
                                      bc.format_ts(bc.parse_ts(T0) + timedelta(minutes=now_min)), *argv])
    return run(args, forge, out, err), out.text, err.text


def _selftest() -> int:
    def live_claim_no_go():
        rc, out, err = _probe(_forge(), "--paths", "web/a.ts")
        return rc == NOGO and "claim  web held by agent:beta" in out, (rc, out, err)

    def lagging_pr_same_paths_no_go():
        rc, out, err = _probe(_forge(), "--paths", "api/x.py")
        return rc == NOGO and "#42 draft" in out and "api/x.py" in out and "claim " not in out, (rc, out, err)

    def disjoint_go_and_really_read():
        forge = _forge()
        rc, out, err = _probe(forge, "--paths", "docs/y.md")
        read = {c[-1] for c in forge.calls}
        needed = {f"repos/{REPO}/pulls/42/files?per_page=100", f"repos/{REPO}/compare/main...feat-lib"}
        return rc == GO and "GO" in out and needed <= read, (rc, out, err, sorted(read))

    def gh_error_exits_2():
        forge = _forge()
        forge.fail = True
        rc, out, err = _probe(forge, "--paths", "docs/y.md")
        return rc == ERROR and out == "" and "NOT VERIFIED" in err, (rc, out, err)

    def expired_claim_does_not_block():
        rc, out, err = _probe(_forge(), "--paths", "web/a.ts", now_min=61)
        return rc == GO, (rc, out, err)

    def own_claim_skipped():
        rc, out, err = _probe(_forge(), "--paths", "web/a.ts", "--agent", "beta")
        return rc == GO, (rc, out, err)

    def renewed_claim_still_blocks():
        comments = [_c(1, 0, "[agent:beta] CLAIM refs:web ttl:30\nx"), _c(2, 25, "[agent:beta] CLAIM refs:web ttl:30\nheartbeat")]
        rc, out, err = _probe(_forge(comments=comments), "--paths", "web/**", now_min=40)
        return rc == NOGO and "claim  web" in out, (rc, out, err)

    def exclusive_role_ref_no_go():
        rc, out, err = _probe(_forge(), "--ref", "merge")
        return rc == NOGO and "claim  merge held by agent:beta" in out, (rc, out, err)

    def pr_citing_ref_no_go_boundary():
        rc, out, _ = _probe(_forge(), "--ref", "#1102")
        rc2, out2, _ = _probe(_forge(), "--ref", "#110")
        return rc == NOGO and "cites #1102" in out and rc2 == GO, (rc, out, rc2, out2)

    def branch_without_pr_no_go():
        rc, out, err = _probe(_forge(), "--paths", "lib/**")
        return rc == NOGO and "branch feat-lib (no PR): lib/z.py" in out, (rc, out, err)

    def keyword_hits_branch_and_pr():
        rc, out, err = _probe(_forge(), "--keyword", "LIB", "--keyword", "parser")
        return rc == NOGO and "feat-lib" in out and "keyword 'parser'" in out, (rc, out, err)

    def fork_head_does_not_hide_branch():
        prs = [{"number": 9, "title": "fork work", "body": "",
                "head": {"ref": "feat-lib", "repo": {"full_name": "x/fork"}}}]
        rc, out, err = _probe(_forge(prs=prs, files={9: []}), "--paths", "lib/z.py")
        return rc == NOGO and "branch feat-lib (no PR): lib/z.py" in out, (rc, out, err)

    def ignored_own_pr_and_branch_go():
        rc, out, err = _probe(_forge(), "--paths", "api/**", "--paths", "lib/z.py",
                              "--ignore-pr", "42", "--ignore-branch", "feat-lib")
        return rc == GO, (rc, out, err)

    def truncated_board_exits_2():
        forge = _forge()
        forge.count_override = 5
        rc, out, err = _probe(forge, "--paths", "docs/y.md")
        return rc == ERROR and "truncated" in err, (rc, out, err)

    def pr_file_cap_exits_2():
        forge = _forge(files={42: [f"gen/f{i}.txt" for i in range(MAX_PR_FILES)]})
        rc, out, err = _probe(forge, "--paths", "docs/y.md")
        return rc == ERROR and "cap" in err, (rc, out, err)

    def branch_overflow_exits_2():
        forge = _forge(branches=["main"] + [f"b{i}" for i in range(3)])
        rc, out, err = _probe(forge, "--paths", "docs/y.md", "--max-branches", "2")
        return rc == ERROR and "max-branches" in err, (rc, out, err)

    def nothing_to_probe_exits_2():
        rc, _, err = _probe(_forge())
        rc2, _, err2 = _probe(_forge(), "--keyword", " ", "--ref", "")
        return rc == ERROR and "nothing to probe" in err and rc2 == ERROR, (rc, err, rc2, err2)

    def peer_title_sanitised():
        prs = [{"number": 7, "title": "evil \x1b[31m`x`", "body": "", "head": {"ref": "h"}}]
        rc, out, err = _probe(_forge(prs=prs, files={7: ["web/q.ts"]}), "--paths", "web/q.ts", "--agent", "beta")
        return rc == NOGO and "\x1b" not in out and "`" not in out, (rc, out, err)

    def overlap_matrix():
        table = [("web", "web/a.ts", True), ("web/a.ts", "web", True), ("web/", "web", True),
                 ("web/a.ts", "web/b.ts", False), ("webx/a", "web", False), ("web/**", "web/a/b.ts", True),
                 ("src/**/*.py", "src/x.py", True), ("src/*.py", "src/x.md", True), ("web/*.ts", "web", True),
                 ("web/*.ts", "api/*.py", False), ("*.md", "docs/y.md", True), ("./api/x.py", "api/x.py", True),
                 (".", "any/deep/file.py", True),
                 # A literal directory under the glob's fixed root (either order) can hold a match.
                 ("src/**/*.py", "src/lib", True), ("src/lib", "src/**/*.py", True), ("*.md", "docs", True),
                 ("docs", "*.md", True), ("web/*.ts", "api", False), ("src/*.py", "srcx", False)]
        bad = [(a, b, want) for a, b, want in table if overlaps(a, b) != want]
        # A known file (a PR or compare entry) holds nothing beneath it: only a direct match counts.
        files = [("src/x.md", "src/*.py", False), ("src/x.py", "src/*.py", True), ("docs", "*.md", False)]
        bad += [(a, b, want, "file") for a, b, want in files if overlaps(a, b, a_is_file=True) != want]
        return not bad, bad

    def claim_item_ref_matches_keyword_and_ref():
        comments = [_c(1, 0, "[agent:beta] CLAIM refs:#1102 ttl:60\ntaking the item")]
        runs = {flag: _probe(_forge(comments=comments, prs=[]), *flag)
                for flag in (("--keyword", "1102"), ("--ref", "#1102"), ("--ref", "1102"), ("--keyword", "#1102"))}
        miss = {f: r for f, r in runs.items() if not (r[0] == NOGO and "claim  #1102 held by agent:beta" in r[1])}
        rc, out, err = _probe(_forge(comments=comments, prs=[]), "--ref", "#110", "--keyword", "110")
        return not miss and rc == GO, (miss, rc, out, err)

    def live_item_claim_without_ref_no_go():
        comments = [_c(1, 0, "[agent:beta] CLAIM refs:#77 ttl:60\nx"), _c(2, 1, "[agent:beta] CLAIM refs:#78 ttl:5\nx")]
        rc, out, err = _probe(_forge(comments=comments, prs=[]), "--paths", "docs/y.md")
        own = _probe(_forge(comments=comments, prs=[]), "--paths", "docs/y.md", "--agent", "beta")
        named = _probe(_forge(comments=comments, prs=[]), "--paths", "docs/y.md", "--ref", "#5")
        return (rc == NOGO and "claim  #77" in out and "no --ref" in out and "#78" not in out
                and own[0] == GO and named[0] == GO), (rc, out, err, own, named)

    def audited_done_or_na_no_go():
        comments = [_c(1, 0, "[agent:alpha] AUDIT refs:#3,#4 sha:abc1234 verdict:done\nalready shipped"),
                    _c(2, 1, "[agent:alpha] AUDIT refs:#5 sha:abc1234 verdict:gap\nreal gap"),
                    _c(3, 2, "[agent:alpha] AUDIT refs:#6 sha:abc1234 verdict:na\nno counterpart"),
                    _c(4, 3, "[agent:gamma] AUDIT refs:#4 sha:def5678 verdict:gap\nre-measured: regressed")]
        done = _probe(_forge(comments=comments, prs=[]), "--ref", "#3")
        na = _probe(_forge(comments=comments, prs=[]), "--keyword", "6")
        gap = _probe(_forge(comments=comments, prs=[]), "--ref", "#5")
        superseded = _probe(_forge(comments=comments, prs=[]), "--ref", "#4")
        return (done[0] == NOGO and "audit  #3 verdict:done at abc1234 by agent:alpha (board comment 1)" in done[1]
                and na[0] == NOGO and "audit  #6 verdict:na" in na[1]
                and gap[0] == GO and superseded[0] == GO), (done, na, gap, superseded)

    cases = [
        ("audited-done-or-na-no-go", audited_done_or_na_no_go),
        ("live-claim-no-go", live_claim_no_go),
        ("lagging-pr-same-paths-no-go", lagging_pr_same_paths_no_go),
        ("disjoint-go-and-really-read", disjoint_go_and_really_read),
        ("gh-error-exits-2", gh_error_exits_2),
        ("expired-claim-does-not-block", expired_claim_does_not_block),
        ("own-claim-skipped", own_claim_skipped),
        ("renewed-claim-still-blocks", renewed_claim_still_blocks),
        ("exclusive-role-ref-no-go", exclusive_role_ref_no_go),
        ("pr-citing-ref-no-go-boundary", pr_citing_ref_no_go_boundary),
        ("branch-without-pr-no-go", branch_without_pr_no_go),
        ("keyword-hits-branch-and-pr", keyword_hits_branch_and_pr),
        ("fork-head-does-not-hide-branch", fork_head_does_not_hide_branch),
        ("ignored-own-pr-and-branch-go", ignored_own_pr_and_branch_go),
        ("truncated-board-exits-2", truncated_board_exits_2),
        ("pr-file-cap-exits-2", pr_file_cap_exits_2),
        ("branch-overflow-exits-2", branch_overflow_exits_2),
        ("nothing-to-probe-exits-2", nothing_to_probe_exits_2),
        ("peer-title-sanitised", peer_title_sanitised),
        ("overlap-matrix", overlap_matrix),
        ("claim-item-ref-matches-keyword-and-ref", claim_item_ref_matches_keyword_and_ref),
        ("live-item-claim-without-ref-no-go", live_item_claim_without_ref_no_go),
    ]
    return bc.run_checks("claim_probe", cases)


def main(argv=None) -> int:
    """CLI entry point. Returns the process exit code."""
    args = build_parser().parse_args(argv)
    if args.selftest:
        return _selftest()
    return run(args, bc.default_runner, sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
