#!/usr/bin/env python3
"""Trigger lint: every routed reference's trigger shares vocabulary with its router line.

A reference file moved behind a trigger only loads when the agent reading the
router (a SKILL.md line, or a sibling reference, naming the file) can tell
WHEN to open it. For every `.claude/skills/<skill>/references/*.md` this
lint checks, deterministically and for free (no LLM call):

  1. the file opens with a trigger paragraph — the first paragraph in its
     first 25 lines that starts with "Read" (e.g. "Read this when ...");
  2. at least MIN_SHARED (2) content words of that trigger paragraph also
     appear on the router rows that name the file — in SKILL.md or a parent
     reference of the same skill only; INDEX.md (which copies every trigger
     verbatim) never counts. A router row is the table row naming the file,
     or the whole prose paragraph naming it (a route often spans lines).

Content words are lowercase runs of letters of length >= 2 minus a fixed
stop list. This is a floor, not proof that the right file loads at the right
moment: an LLM trigger eval checks that, once per release (see
agentic-delivery/references/cost-quality-guardrails.md). What the lint does
catch every run is a router line that names a file with no trigger cue at
all, and a reference that lost its trigger paragraph.

Usage: trigger_lint.py [ROOT]   (default ROOT: current directory)
Exit codes: 0 clean, 1 findings, 2 no skills directory (fail closed).
Side effects: none (reads files only).
"""
import glob
import os
import re
import sys

MIN_SHARED = 2
STOP = set("""
a an and are as at be by can do does each for from has have how if in into is it its
may more most no not of on one only or our same so such than that the then them they
this to two use via was we were what when which who why will with you your also all any
about above after again against alongside always another before being below between
beyond could every file files first their there these those under until using while
where whenever would should other target reads read review reviewing skill section
expands just like
""".split())


def words(text):
    """Content words of text (lowercased letter runs, length >= 2, minus STOP).

    File-path tokens (anything ending in .md) are dropped first, so a router
    line cannot pass on the file's own name alone.
    """
    text = re.sub(r"\S*\.md\b\S*", " ", text)
    return {w for w in re.findall(r"[a-z][a-z-]+", text.lower()) if w not in STOP}


def trigger(text):
    """The first paragraph in the first 25 lines that starts with 'Read', or ''."""
    out = []
    for line in text.split("\n")[:25]:
        s = line.strip().lstrip("*> ").strip()
        if not out and re.match(r"read\b", s, re.I):
            out.append(s)
        elif out:
            if not s:
                break
            out.append(s)
    return " ".join(out)


def router_rows(text, base):
    """Router rows naming base: a table row alone, or the whole prose paragraph."""
    rows = []
    for para in re.split(r"\n\s*\n", text):
        for ln in para.splitlines():
            if base in ln:
                rows.append(ln if ln.lstrip().startswith("|") else para)
    return rows


def lint(root):
    """Return a list of finding strings for every skill under root."""
    findings = []
    skills = sorted(glob.glob(os.path.join(root, ".claude", "skills", "*", "")))
    if not skills:
        raise FileNotFoundError(f"no .claude/skills/*/ under {root}")
    for skill in skills:
        refs = sorted(glob.glob(os.path.join(skill, "references", "*.md")))
        routers = [os.path.join(skill, "SKILL.md")] + refs
        texts = {}
        for f in routers:
            try:
                with open(f, encoding="utf-8") as fh:
                    texts[f] = fh.read()
            except OSError:
                texts[f] = ""
        for ref in refs:
            rel = os.path.relpath(ref, root)
            base = os.path.basename(ref)
            trig = trigger(texts[ref])
            if not trig:
                findings.append(f"NO TRIGGER: {rel} has no opening 'Read ...' trigger paragraph")
                continue
            # Router lines: lines naming the file in SKILL.md or a parent
            # reference of the same skill. INDEX.md (which copies each trigger
            # verbatim) and any file outside the skill never count.
            lines = [row for f in routers if f != ref for row in router_rows(texts[f], base)]
            if not lines:
                continue  # unrouted: the routing gate owns that failure
            shared = words(trig) & words(" ".join(lines))
            if len(shared) < MIN_SHARED:
                findings.append(f"TRIGGER NOT IN ROUTER: {rel} — no router line naming it shares a word "
                                f"with its trigger ({trig[:80]!r})")
    return findings


def main(argv):
    root = argv[0] if argv else "."
    try:
        findings = lint(root)
    except FileNotFoundError as exc:
        print(f"trigger_lint: {exc} (fail closed)", file=sys.stderr)
        return 2
    for f in findings:
        print(f, file=sys.stderr)
    print(f"trigger_lint: {len(findings)} finding(s)")
    return 1 if findings else 0


# ---------------------------------------------------------------------------
# --selftest — synthetic skill trees only (never the real repo's prose).
# ---------------------------------------------------------------------------
def _selftest():
    import shutil
    import tempfile

    passed = failed = 0

    def case(name, ok):
        nonlocal passed, failed
        passed += bool(ok)
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}")

    tmp = tempfile.mkdtemp(prefix="trigger-lint-selftest-")
    try:
        def tree(skill_md, refs):
            root = tempfile.mkdtemp(dir=tmp)
            d = os.path.join(root, ".claude", "skills", "demo")
            os.makedirs(os.path.join(d, "references"))
            with open(os.path.join(d, "SKILL.md"), "w") as fh:
                fh.write(skill_md)
            for name, body in refs.items():
                with open(os.path.join(d, "references", name), "w") as fh:
                    fh.write(body)
            return root

        good = "# Payments\n\nRead this when the target charges a card or issues a refund.\n"
        case("trigger-echoed-in-router-passes",
             lint(tree("`references/pay.md` — read it when a card is charged or a refund\nis issued.\n",
                       {"pay.md": good})) == [])
        one = lint(tree("Cards: `references/pay.md`, read it for a card.\n", {"pay.md": good}))
        case("one-shared-word-fails", len(one) == 1 and one[0].startswith("TRIGGER NOT IN ROUTER"))
        root = tree("See `references/pay.md`.\n", {"pay.md": good})
        with open(os.path.join(root, ".claude", "skills", "demo", "INDEX.md"), "w") as fh:
            fh.write("| `references/pay.md` | the target charges a card or issues a refund |\n")
        case("index-md-copy-of-trigger-does-not-count", len(lint(root)) == 1)
        case("table-row-is-its-own-router-row",
             len(lint(tree("| Refund card | `references/other.md` |\n| X | `references/pay.md` |\n",
                           {"pay.md": good, "other.md": "# O\n\nRead this when other things.\n"}))) == 2)
        case("parent-reference-can-route",
             lint(tree("Hub topics: `references/hub.md`.\n",
                       {"hub.md": "# Hub\n\nRead this when routing hub topics.\n\nCard refund work: `pay.md`.\n",
                        "pay.md": good})) == [])
        bare = lint(tree("See `references/pay.md`.\n", {"pay.md": good}))
        case("bare-router-line-fails", len(bare) == 1 and bare[0].startswith("TRIGGER NOT IN ROUTER"))
        nt = lint(tree("Refunds: `references/pay.md` card.\n", {"pay.md": "# Payments\n\nCards and refunds.\n"}))
        case("missing-trigger-paragraph-fails", len(nt) == 1 and nt[0].startswith("NO TRIGGER"))
        case("unrouted-left-to-routing-gate", lint(tree("Nothing.\n", {"pay.md": good})) == [])
        case("multi-line-trigger-paragraph-read",
             trigger("# T\n\n**Read this when** a queue\ndrains slowly.\n\nBody.") == "Read this when** a queue drains slowly.")
        case("no-skills-dir-exit-2", main([os.path.join(tmp, "empty")]) == 2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nselftest: {passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(main(sys.argv[1:]))
