#!/usr/bin/env python3
"""parity_differ.py — the two-sided design<->app section-parity gate.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
An agent measures ONE side of a "does the app match the design" claim — a
screenshot, a page height, a token-name similarity, a lane's own self-report —
and reports "aligned." That is a confident WRONG pass whenever the app is
actually missing sections the design has, or renders sections empty where the
design shows them populated. Worse, a one-sided read tempts the fix in the
wrong direction: an agent "condenses" empty boxes to look tidy/compact when
the design in fact wants those boxes seeded with data.

This tool makes a one-sided or proxy input STRUCTURALLY UNABLE to emit a pass
or a similarity score. There is exactly one passing exit code (MATCH, 0) and
it requires both sides to be present and readable.

CONTRACT (fail-closed; every branch below is load-bearing, not cosmetic)
-------------------------------------------------------------------------
* MATCH (0) — the ONLY pass. Both sides present; every design section is
  present in the app; every design-populated section is populated in the app.
* MISMATCH (1) — lists the gap per section: "missing" (build it) or "empty"
  (seed it). That list IS the work queue for a mirror/restyle task.
* USAGE_ERROR (2) — bad CLI invocation (e.g. only one of --design/--app).
* COULD_NOT_CHECK (3) — either side is missing, unreadable, empty, or yields
  no sections. Never a score, never a pass — a one-sided input cannot compare.
* CANNOT_COMPARE (4) — the app is UNSEEDED: every design-populated section
  exists in the app but is uniformly empty. This is a precondition failure
  (seed the app's data), NOT a structural mismatch — it must never be "fixed"
  by condensing or deleting the empty sections. Distinct from MISMATCH so an
  agent cannot quietly reclassify "unseeded" as "aligned once trimmed down."
* Extra app sections beyond the design are reported as info ("kept as
  superset") and never cause a failure on their own.

SECTION-MARKER FORMAT (what the extractor looks for)
-----------------------------------------------------
Each side is a rendered HTML export or a `.json` section list.
  HTML  : a section is any element carrying `data-section="ID"`. A populated
          unit is any descendant carrying `data-item`. An explicit
          empty-state placeholder carries `data-empty`, or a class token
          containing the substring "empty" (e.g. "list empty-state"). A
          section is POPULATED iff it contains >= 1 `data-item` descendant;
          section order is preserved and a repeated `data-section` id is
          folded into the one earlier-seen section.
  JSON  : a list of `{"id": "...", "populated": true|false}` rows.
A missing file, an empty file, invalid JSON, or a side with zero recognized
sections all extract to `None` — which forces COULD_NOT_CHECK, never a pass.

USAGE
-----
  parity_differ.py --design <file> --app <file>
  parity_differ.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from html.parser import HTMLParser

# The whole point of naming these instead of using bare ints: only MATCH is a
# pass, so any caller/CI step gating on "exit 0" cannot be fooled by a
# mismatch, an unseeded app, or a one-sided input silently returning 0.
MATCH = 0
MISMATCH = 1
USAGE_ERROR = 2
COULD_NOT_CHECK = 3
CANNOT_COMPARE = 4

# Elements with no closing tag in HTML. Never pushed onto the open-tag stack,
# so a document full of bare `<img>`/`<input>`/... never desyncs it.
_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})


class _SectionExtractor(HTMLParser):
    """Stream-parse one HTML render into an ordered list of section records.

    Fail-closed / crash-closed intent: real design and app exports are not
    guaranteed to be well-formed (unbalanced tags, void elements written
    either way, stray end tags). This parser never raises on that input —
    an attribute marker is always attributed to the innermost currently-open
    `data-section`, and an end tag that has no matching open tag is simply
    ignored rather than corrupting the stack. Malformed markup degrades to
    "fewer markers recognized," never to an exception.
    """

    def __init__(self) -> None:
        """Set up the ordered section list, id lookup, and open-tag stack."""
        super().__init__(convert_charrefs=True)
        self.sections: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self._stack: list[tuple[str, str | None]] = []

    def _innermost_section(self) -> str | None:
        """Return the nearest currently-open `data-section` id, or None."""
        for _tag, sid in reversed(self._stack):
            if sid is not None:
                return sid
        return None

    def _record(self, attrs: list[tuple[str, str | None]]) -> str | None:
        """Apply one tag's attributes to the section they belong to.

        Registers a new section on `data-section`, and — fail-closed, never
        guessing which section an unattributed marker belongs to — counts a
        `data-item` / `data-empty` marker against the innermost open section
        (preferring a section this same tag just opened). Returns the tag's
        own `data-section` id, if any, so the caller knows whether to push it.
        """
        attr_map = dict(attrs)
        sid = attr_map.get("data-section")
        if sid is not None and sid not in self._by_id:
            record = {"id": sid, "items": 0, "empties": 0}
            self.sections.append(record)
            self._by_id[sid] = record

        target = sid if sid is not None else self._innermost_section()
        if target is not None and target in self._by_id:
            if "data-item" in attr_map:
                self._by_id[target]["items"] += 1
            classes = (attr_map.get("class") or "").split()
            if "data-empty" in attr_map or any("empty" in c for c in classes):
                self._by_id[target]["empties"] += 1
        return sid

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Open tag: record its markers, then push it unless it is void."""
        sid = self._record(attrs)
        if tag not in _VOID_TAGS:
            self._stack.append((tag, sid))

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        """Self-closed tag (`<x/>`): record markers; never push (no body)."""
        self._record(attrs)

    def handle_endtag(self, tag: str) -> None:
        """Pop to the nearest matching open tag; a stray end tag is a no-op.

        Fail-closed against imbalance: if `tag` is not found on the stack
        (e.g. a void element with a stray closing tag, or genuinely
        mismatched markup) the stack is left untouched rather than popping
        the wrong frame.
        """
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                del self._stack[i:]
                return


def extract_sections(path: str | None) -> list[tuple[str, bool]] | None:
    """Return this side's ordered `[(section_id, populated), ...]`, or None.

    None means "cannot be compared" and covers every fail-closed case in one
    place: no path given, file absent, unreadable, empty/whitespace-only,
    invalid JSON, or a side (HTML or JSON) that yields zero sections. A
    caller must treat None as COULD_NOT_CHECK, never as an empty-but-valid
    side.
    """
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except (OSError, UnicodeDecodeError):
        return None
    if not raw.strip():
        return None

    if path.lower().endswith(".json"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, list):
            return None
        rows = []
        for row in data:
            if isinstance(row, dict) and "id" in row:
                rows.append((str(row["id"]), bool(row.get("populated", False))))
        return rows or None

    parser = _SectionExtractor()
    parser.feed(raw)
    if not parser.sections:
        return None
    return [(s["id"], s["items"] > 0) for s in parser.sections]


def _render_verdict(design: list[tuple[str, bool]], app: list[tuple[str, bool]]) -> tuple[int, str]:
    """Classify two already-extracted sides into (exit_code, report).

    Fail-closed ordering matters: the UNSEEDED check runs before the
    MISMATCH check, so an app with every design-populated section present
    but empty is never reported (or "fixed") as a plain structural mismatch —
    it is a data-seeding precondition failure, always CANNOT_COMPARE first.
    """
    design_ids = [sid for sid, _ in design]
    design_pop = [sid for sid, populated in design if populated]
    app_map = dict(app)

    def app_state(sid: str) -> str:
        """Classify one design section id against the app's extract."""
        if sid not in app_map:
            return "missing"
        return "populated" if app_map[sid] else "empty"

    states = {sid: app_state(sid) for sid in design_ids}

    # UNSEEDED: >=2 design-populated sections, ALL present-but-empty in the
    # app (none missing). A single missing section among them means the gap
    # is structural, not a seeding problem — that falls through to MISMATCH.
    if len(design_pop) >= 2 and all(states[sid] == "empty" for sid in design_pop):
        names = ", ".join(design_pop)
        return CANNOT_COMPARE, (
            "CANNOT_COMPARE: app is UNSEEDED — every design-populated section "
            f"({names}) is present in the app but empty. "
            "seed the app's data to the design's data state first. "
            "Do NOT condense or remove the empty sections — the design wants "
            "them populated. This is a data-seeding precondition failure, not "
            "a structural gap, and it is never resolved by trimming."
        )

    missing = [sid for sid in design_ids if states[sid] == "missing"]
    empty = [sid for sid in design_pop if states[sid] == "empty"]
    extra = [sid for sid, _ in app if sid not in set(design_ids)]

    info_lines = []
    if extra:
        info_lines.append(
            "info: extra app section(s) beyond the design, kept as superset "
            f"(not a failure): {', '.join(extra)}"
        )

    if not missing and not empty:
        return MATCH, "\n".join([
            ("MATCH: every design section is present in the app, and every "
             "design-populated section is populated in the app."),
            *info_lines,
        ])

    gap_lines = [f"missing: section '{sid}' — build it (absent from the app)." for sid in missing]
    gap_lines += [f"empty:   section '{sid}' — seed it (present but no data-item in the app)." for sid in empty]
    return MISMATCH, "\n".join([
        (f"MISMATCH: {len(missing)} missing + {len(empty)} empty of "
         f"{len(design_ids)} design section(s). This list is the work queue."),
        *gap_lines,
        *info_lines,
    ])


def diff_sides(design_path: str | None, app_path: str | None) -> tuple[int, str]:
    """Compare a design render against an app render; return (exit_code, report).

    Two-sided or no output: a missing/unreadable/empty/sectionless side on
    EITHER end returns COULD_NOT_CHECK before any comparison runs, so a
    one-sided input can never fall through to MATCH/MISMATCH/CANNOT_COMPARE.
    """
    design = extract_sections(design_path)
    if design is None:
        return COULD_NOT_CHECK, (
            f"COULD_NOT_CHECK: design side unreadable, empty, or has no "
            f"sections ({design_path!r}). Two-sided input is required — a "
            "one-sided read cannot certify parity."
        )
    app = extract_sections(app_path)
    if app is None:
        return COULD_NOT_CHECK, (
            f"COULD_NOT_CHECK: app side unreadable, empty, or has no "
            f"sections ({app_path!r}). Two-sided input is required — a "
            "one-sided read cannot certify parity."
        )
    return _render_verdict(design, app)


def _selftest() -> int:
    """Run the committed fixtures and assert the exact verdict per case.

    This is the tool's own proof that it fires on real input, not just that
    it parses: each of the five checks below pins both the exit code and the
    presence/absence of specific substrings in the human-readable report, so
    a future edit that quietly turns a fail-closed branch into a pass (or
    lets "aligned" slip into the vocabulary) breaks this function loudly.
    """
    fixtures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "parity")
    design = os.path.join(fixtures_dir, "design.html")
    app_full = os.path.join(fixtures_dir, "app_full.html")
    app_partial = os.path.join(fixtures_dir, "app_partial.html")
    app_unseeded = os.path.join(fixtures_dir, "app_unseeded.html")
    nonexistent = os.path.join(fixtures_dir, "does-not-exist.html")

    failures: list[str] = []

    def check(label: str, code: int, report: str, want_code: int,
              must_have: tuple[str, ...] = (), must_not: tuple[str, ...] = ()) -> None:
        """Assert one case's exit code plus required/forbidden substrings."""
        if code != want_code:
            failures.append(f"{label}: exit {code}, want {want_code}")
        lowered = report.lower()
        for needle in must_have:
            if needle.lower() not in lowered:
                failures.append(f"{label}: report missing {needle!r}")
        for needle in must_not:
            if needle.lower() in lowered:
                failures.append(f"{label}: report must not contain {needle!r}")

    code, report = diff_sides(design, app_full)
    check("match", code, report, MATCH, must_have=("MATCH",))

    code, report = diff_sides(design, app_partial)
    check("mismatch", code, report, MISMATCH,
          must_have=("MISMATCH", "beta", "gamma", "delta"),
          must_not=("aligned",))

    code, report = diff_sides(design, app_unseeded)
    check("unseeded", code, report, CANNOT_COMPARE,
          must_have=("seed", "do not condense"),
          must_not=("aligned", "MISMATCH"))

    code, report = diff_sides(nonexistent, app_full)
    check("refuse-design-absent", code, report, COULD_NOT_CHECK,
          must_not=("aligned", "MATCH"))

    code, report = diff_sides(design, nonexistent)
    check("refuse-app-absent", code, report, COULD_NOT_CHECK,
          must_not=("aligned", "MATCH"))

    if failures:
        print("SELFTEST FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        "SELFTEST OK: match=0 mismatch=1 unseeded=4 "
        "refuse(design-absent)=3 refuse(app-absent)=3"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: `--selftest`, or `--design <f> --app <f>` (two-sided only)."""
    parser = argparse.ArgumentParser(
        description="Two-sided design<->app section-parity gate. MATCH (exit 0) is the only pass."
    )
    parser.add_argument("--design", help="design render: HTML file or .json section list")
    parser.add_argument("--app", help="app render: HTML file or .json section list")
    parser.add_argument("--selftest", action="store_true", help="run the committed-fixture self-test")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.design or not args.app:
        parser.error("--design and --app are both required (two-sided input, or no output)")
        return USAGE_ERROR  # pragma: no cover — parser.error() already exits(2)

    code, report = diff_sides(args.design, args.app)
    print(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
