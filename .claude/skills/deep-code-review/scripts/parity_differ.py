#!/usr/bin/env python3
"""parity_differ.py — the two-sided design<->app parity gate: sections first,
then the element inventory of every matched section.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
An agent measures ONE side of a "does the app match the design" claim — a
screenshot, a page height, a token-name similarity, a lane's own self-report —
and reports "aligned." That is a confident WRONG pass whenever the app is
actually missing sections the design has, or renders sections empty where the
design shows them populated. Worse, a one-sided read tempts the fix in the
wrong direction: an agent "condenses" empty boxes to look tidy/compact when
the design in fact wants those boxes seeded with data.

Section presence alone is too coarse: an app can render every section
non-empty and still be missing buttons, headings, tabs, or rows. Agents then
fill the gap with element SIZES ("heights within 2%"), which is the worst
completeness proxy there is. So inside every section present on both sides,
this tool diffs an element INVENTORY — the things a user can read or operate.

This tool makes a one-sided or proxy input STRUCTURALLY UNABLE to emit a pass
or a similarity score. Exit 0 requires both sides to be present and readable.

SIZE IS NEVER AN INPUT
----------------------
Size, height, width, bounding boxes, pixel counts, and every other geometric
measurement are NEVER inputs to the verdict. The parser does not read
`width`/`height` attributes or layout; it reads inline `style` only to skip
`display:none` / `visibility:hidden` / `opacity:0` subtrees. A taller, wider,
or denser app with an equal inventory is a MATCH; a same-size app missing one
button is a MISMATCH. Geometry belongs only to layout-defect checks (overlap,
clipping, viewport fit), never to a "complete" or "matches" verdict. A
`data-lines` count (LINE COUNTS below) is a count of rendered line boxes set by
the capture, not a measurement: the parser never sees a height.

CONTRACT (fail-closed; every branch below is load-bearing, not cosmetic)
-------------------------------------------------------------------------
* MATCH (0) — the plain pass. Both sides present; every design section is
  present in the app; every design-populated section is populated in the app;
  and every matched section's inventory is equal.
* MATCH_WITH_ACCEPTED (0, printed distinctly with `accepted_n=N`) — as MATCH,
  except N differences remain, each covered by a row of an OWNER-AUTHORED
  `--accept` file. Never reported as a plain MATCH.
* MATCH_WITH_IGNORED (0, printed distinctly with `ignored_n=N`) — as MATCH
  or MATCH_WITH_ACCEPTED, except N design elements are excluded by
  owner-authored `ignore` rows (IGNORED below). Never a plain MATCH.
* MISMATCH (1) — lists the gap per section: "missing" (build it) or "empty"
  (seed it), then per section MISSING_IN_APP / EXTRA_IN_APP / CHANGED /
  MOVED inventory rows. That list IS the work queue for a mirror/restyle task. The
  report carries a fixed precondition line: both renders must share the same
  auth + data state, or a signed-out app render reports every gated section
  as "missing" and points the fix in the wrong direction (build, not sign
  in). The line scopes this matched-state diff only; the signed-out default
  surface remains a separate required parity check.
* USAGE_ERROR (2) — bad CLI invocation (e.g. only one of --design/--app).
* COULD_NOT_CHECK (3) — either side is missing, unreadable, empty, or yields
  no sections; a section uses a class-based hiding token with no computed-
  visibility marker (VISIBILITY below); the `--accept` file is not owner-
  authored, not committed, or malformed; a would-be MATCH rests on a side
  with no inventory (a `.json` section list) or on zero matched element
  pairs; or fewer inventory pairs matched than the caller's `--min-pairs N`
  (a harness that compared an empty or wrong page — this outranks MISMATCH,
  whose work queue would then point the wrong way). N is caller-supplied,
  never guessed. Never a score, never a pass. Style never exits 3.
* CANNOT_COMPARE (4) — the app is UNSEEDED: every design-populated section
  exists in the app but is uniformly empty. This is a precondition failure
  (seed the app's data), NOT a structural mismatch — it must never be "fixed"
  by condensing or deleting the empty sections. Distinct from MISMATCH so an
  agent cannot quietly reclassify "unseeded" as "aligned once trimmed down."
* STYLE_DIFF (5) — `--style` only: the inventory passes but a text-matched
  pair differs in computed style (COMPUTED STYLE below).
* STYLE_COULD_NOT_CHECK (6) — `--style` only: the inventory passes but style
  is unverifiable — a malformed `data-cs`, zero text-matched style pairs, or
  fewer than the caller's `--style-min-pairs N` (its own floor; the
  inventory's `--min-pairs` never applies to style). Never a pass.
  For both style exits: a failing inventory exit (1/3/4) always wins, with
  the style lines appended; STYLE_MATCH leaves MATCH (0) as is; `verdict`
  stays the completeness verdict and `style.verdict` (STYLE_MATCH /
  STYLE_DIFF / STYLE_COULD_NOT_CHECK) is reported separately.
* BLOCKED_BY_FOUNDATION (7) — `--workflow` only: the inventory and tokens
  are comparable, but the token stage mismatches or a FOUNDATION/PRIMITIVE
  style row is un-accepted; every section verdict is withheld (WORKFLOW).
* REGRESSION (8) — `--baseline` only: a run that passed before (its
  recorded fingerprint) now shows new deltas; only those are listed
  (BASELINE). Distinct from MISMATCH (1), the never-passed work queue.
* COULD_NOT_CHECK_CROP (9) — the design and app captures of a section are
  not the same crop (SAME-CROP GUARD); that section is UNVERIFIED and
  unscored while the others are scored and listed. Outranks MISMATCH;
  `--min-pairs` COULD_NOT_CHECK outranks it.
* Extra app sections beyond the design are reported as info ("kept as
  superset") and never cause a failure on their own. Extra ITEMS inside a
  matched section are EXTRA_IN_APP rows and do fail until resolved or
  accepted — an app-only element is a finding, never a silent bonus.

SECTION-MARKER FORMAT (what the extractor looks for)
-----------------------------------------------------
Each side is a rendered HTML export (DOM snapshot) or a `.json` section list.
  HTML  : a section is any element carrying `data-section="ID"`. A populated
          unit is any descendant carrying `data-item`. An explicit
          empty-state placeholder carries `data-empty`, or a class token
          containing the substring "empty" (e.g. "list empty-state"). A
          section is POPULATED iff it contains >= 1 `data-item` descendant;
          section order is preserved and a repeated `data-section` id is
          folded into the one earlier-seen section.
  JSON  : a list of `{"id": "...", "populated": true|false}` rows. A JSON
          side carries no inventory, so it can fail but never pass.
A missing file, an empty file, invalid JSON, or a side with zero recognized
sections all extract to `None` — which forces COULD_NOT_CHECK, never a pass.

VISIBILITY (the export contract)
--------------------------------
Not inventoried: items outside every `data-section`; subtrees that carry the
`hidden` attribute, `aria-hidden="true"`, `data-visible="false"`, or inline
`display:none` / `visibility:hidden` / `opacity:0`; a `<dialog>` without
`open`; a `<details>` without `open` (its first-level `<summary>` stays
visible); canvas/video/iframe/object fallback content; and script/style/
template/noscript/head/datalist. Stylesheet rules are not evaluated, so a
class can hide an element this parser cannot see through. The export must
therefore carry COMPUTED visibility: every element with a class token in
`hidden`, `sr-only`, `invisible`, `d-none`, `visually-hidden` must also carry
`data-visible="true"` or `data-visible="false"` (e.g. set from
`getComputedStyle` / `checkVisibility()` when the DOM is snapshotted). Such
a class with no marker is COULD_NOT_CHECK, never a guess.

IGNORED (`data-parity-ignore`) — visible, never silent
------------------------------------------------------
An element carrying `data-parity-ignore` (value optional: a short id such as
`live-clock`) is excluded with its whole subtree from the inventory, from
populated-ness, from class-hiding checks, and from `--style`, on the side
that carries it; a `data-section` carrying it registers no section. Every
ignored root is listed in the report (`ignored: N element(s) ...`, per side,
with its section and id — the attribute value, else the tag with its
`data-section` or `id`, else `<tag>`) and in `--json` as `ignored`.
A DESIGN-side ignore removes a requirement, so each needs an owner-authored
accept row `ignore<TAB><section, or - outside every section><TAB><id>`
(ACCEPTED DEVIATIONS trust); without one the run is COULD_NOT_CHECK. With
it the verdict is MATCH_WITH_IGNORED (never a plain MATCH) and the
section reads PASS_WITH_IGNORED. An APP-side ignore pairs with a design
ignore of the same section + id; unpaired, it is an open `EXTRA_IN_APP
ignored:<id>` row (acceptable like any row), and it never hides a design
element, which stays MISSING_IN_APP. Mark volatile or harness-only content
(clocks, ads, dev banners) on both captures.

SAME-CROP GUARD — COULD_NOT_CHECK_CROP (9)
------------------------------------------
The design is the reference; anchors are only the visible texts of
`data-anchor` elements (a plain heading is never an anchor). For every section
present on both sides: when the design section has anchors, the app section
must show at least one of those texts; and the app section may not carry a
`data-anchor` that the design anchors only in a different section (a page
header or KPI card leaked into the crop). A failing section alone is
UNVERIFIED and unscored (`crop_problems`); the others are still scored and
listed, and the exit is 9. A heading missing from one section and extra in
another is a MOVED row (an open difference), not a crop problem.

ELEMENT INVENTORY (per section, HTML sides only)
------------------------------------------------
Each item is `kind:role:label`:
  heading   — h1..h6 or role=heading (aria-level, default 2): `heading:h2:Text`.
  control   — role + VISIBLE text, then the accessible name when it differs:
              button (incl. input button types and summary), link (a[href]),
              textbox/combobox/checkbox/radio/slider (input/select/textarea),
              tab, menuitem, and any element with an explicit interactive
              role. Visible text is the content text (value for input
              buttons; the associated <label> text for form fields). The
              accessible name follows aria-labelledby, aria-label, <label>,
              content, value, alt, title; it is appended as
              `[source: name]` when it differs from the visible text, or
              `[no accessible name]`. A placeholder is NEVER a label: it is
              compared as `[placeholder: text]`. An image inside a control is
              part of its visible text; an icon-font `<i class>` inside one
              is appended as `[icon: classes]`. So a button whose visible
              text differs from the design is CHANGED even when its
              aria-label matches.
  image     — img (alt; alt="" is decorative and skipped), svg, role=img
              (aria-label, else <title>/text).
  media     — canvas, video, iframe, object: `media:video:title` (aria-label,
              else title).
  icon      — an icon-font `<i class>` with no text (even when aria-hidden):
              `icon:classes` (aria-label wins).
  option    — every `<option>` of a select: `option:Text`.
  list/table— one container item per list/table with its row count
              (`list:#1`, ordinal within the section), plus one
              `list-item:` / `table-row:` item per row labelled by its
              first-cell text (a list item's full text).
  state     — every `data-state="VALUE"` marker: `state:VALUE`.
  text      — every remaining visible text run, merged across inline tags
              and split at block boundaries.
Labels are whitespace-normalized and case-folded for comparison; order is
ignored (multiset). COUNTS ARE ALWAYS COMPARED: list/table row counts and the
number of masked value slots are never masked, so render both sides on the
same data state (the precondition line). Text inside a `data-sample` /
`data-value` element is masked to one `<value>` token per element only when
BOTH sides' section carries such a marker — a one-sided marker cannot hide a
difference — and a slot holding a broken render (empty, undefined, null, NaN,
Invalid Date, [object Object], or an unrendered `{{...}}` / `${...}`) is
compared verbatim, never masked. Leftover design/app items are paired into
CHANGED rows (same kind and label, different role; then same kind and role,
different label); the rest are MISSING_IN_APP / EXTRA_IN_APP, except that a
heading MISSING_IN_APP in one section and EXTRA_IN_APP in another becomes one
MOVED row (`heading:... -> section 't'`). Completeness =
matched items / design items, per section and overall — items, never pixels;
the percentage is floored and any shortfall prints `(<100%)`.
LINE COUNTS: a heading, control, image, option, list/table row, or the block
holding a text run may carry `data-lines="N"` — the number of rendered line
boxes (e.g. distinct line tops of `range.getClientRects()` over its text),
set by the capture. It joins the item key as `[lines: N]`, so 2-line rows
against 1-line design rows are CHANGED rows even when every text matches;
a one-sided `data-lines` is a CHANGED row too (export it on both sides). A
value that is not a positive integer (`[1-9][0-9]*`) is COULD_NOT_CHECK.

ACCEPTED DEVIATIONS (`--accept FILE [--accept-rev REV]`) — OWNER-AUTHORED ONLY
-----------------------------------------------------------------------------
Tab-separated rows, 7 non-empty fields:
  section  status  item  app-value  count  reason  owner-quote-or-commit
`status` is MISSING_IN_APP / EXTRA_IN_APP / CHANGED / MOVED; `item` is the row's item
key as printed (design key for MISSING/CHANGED, app key for EXTRA);
`app-value` is the exact app side as printed (`-` for MISSING_IN_APP) — so an
accepted CHANGED row pins the app value and a different one is a new, open
difference; `count` is how many identical rows it covers (a surplus row stays
open). Blank lines, `#` comments, and a `section` header row are skipped; a
malformed or duplicate row fails closed. The file is read from its COMMITTED
blob at `--accept-rev` (default HEAD; working-tree edits are inert) and must
be owner-authored: with agentic-delivery's `focus_gate.py` installed
alongside, its commit-authorship trust is reused (every surviving line and
the last touch by an owner email, no `Co-authored-by:` trailer); otherwise
`--accept-rev` is required and every commit touching the file (`git log`)
must be by an email in `DCR_OWNER_EMAIL`. Set that from protected
configuration: commit authorship is unauthenticated metadata, so this blocks
an agent following its own attribution convention, not a forger.
An accepted row still prints (ACCEPTED) and never counts as matched; a row
covering fewer differences than its count prints as info (stale).
Style approvals live in the same file (same trust): a row whose first field
is `style` or `rule` and whose second is not a status above is
  style  <scope: global|section id>  <property>  <design-value>  <app-value>  <reason>  <owner>
  rule   min-<property>  <N>px  <reason>  <owner>
A `style` row accepts every style difference on that property with exactly
that normalized design -> app value pair (its section before `global`); a
rule accepts a design px value below N rendered at exactly N (e.g. `rule
min-font-size 12px`: a design 11px text is satisfied by 12px). Accepted
style rows print as ACCEPTED, never STYLE_DIFF; a style verdict whose every
difference is accepted is STYLE_MATCH_WITH_ACCEPTED (exit 0); an unused style
row or rule prints as info (stale); an unknown property/rule fails closed.
  visual-reviewed  <section id>  <reason>  <owner>
marks a section with no text-bearing `data-cs` (image, chart, map) as
owner-reviewed: its style reads `visual-reviewed` instead of `no pairs`, so
it can PASS. It never rescues a page-wide STYLE_COULD_NOT_CHECK, and on a
section that has style pairs it prints as info (stale).
  threshold  <section id>  <style-identity %>
sets that section's style bar (default strict: any open row fails): when its
identity — pairs with no un-accepted difference / its pairs — is at least
the percentage (above 0, at most 100), its open rows print as tolerated
(`THRESHOLD ... N row(s) tolerated`) and the style verdict is
STYLE_MATCH_WITH_ACCEPTED; below it they stay open. A threshold never waives
a FOUNDATION or PRIMITIVE row; one on a section with no open row is stale.
  ignore  <section id, or - outside every section>  <data-parity-ignore id>
authorizes one design-side ignore (IGNORED); an unused one is stale info.

COMPUTED STYLE (`--style`) — reported separately, never a completeness input
------------------------------------------------------------------------------
Export contract: an element to style-check carries
`data-cs='{"line-height":"20px", ...}'`, a JSON object holding a non-empty
value for EVERY property in `_STYLE_PROPS` (font-family, font-size, font-weight,
line-height, letter-spacing, color, background-color, padding,
border-radius, box-shadow), set from `getComputedStyle` when the DOM is
snapshotted, e.g. `el.setAttribute('data-cs', JSON.stringify(
Object.fromEntries(PROPS.map(p => [p, getComputedStyle(el)
.getPropertyValue(p)]))))`. Export both sides from the same browser: values
compare as normalized text (case, whitespace, quotes), with no unit
conversion. A visible `data-cs` element is paired by section + role
(heading level, control role, explicit `role`, else `text`) + its full
visible text (masked as in the inventory), duplicates in document order;
a design element left unpaired is then paired by its identical OWN text
nodes (not its children's) within the same section + role, so a style diff
survives a changed child label; an element with no visible text or no
counterpart is not style-checked. The report adds identity (pairs with no
un-accepted difference / pairs, beside raw style-identical), `mismatch
count per property`, and up to 10 `top style diffs (text | prop | design |
app)`, most frequent property first.
Rows print grouped by property. A property is one FOUNDATION row — a global
type/box mismatch to fix before any per-section work — instead of one row
per pair only when it differs on more than half of all pairs AND on pairs
in >= 2 sections AND on >= max(3, `--style-min-pairs`) pairs; a narrower
majority (2 pairs, or one section) prints per pair. Style verdict:
STYLE_MATCH, STYLE_DIFF, or STYLE_COULD_NOT_CHECK (a malformed `data-cs`,
zero pairs, or fewer than `--style-min-pairs`). Owner style approvals:
ACCEPTED DEVIATIONS above; FOUNDATION and PRIMITIVE count open rows only.

PER-SECTION PASS + PROGRESS
---------------------------
Every run that compares inventories ends with `sections passed k/n` and one
row per section: PASS iff the section is present (populated where the
design is), every inventory row is matched or accepted, and — with
`--style` — it has style pairs and no un-accepted style row. FAIL on a gap
or open row; UNVERIFIED when inventory or style could not be checked (never
a pass). Without `--style` the table is labelled inventory-only.

WORKFLOW (`--workflow --design-tokens F --app-tokens F [--token-map F]`)
------------------------------------------------------------------------
One foundation-first gate: (1) tokens — `token_differ.py` on the two token
exports (COULD_NOT_CHECK there is exit 3); (2) primitives — open FOUNDATION
properties plus PRIMITIVE rows: a (role, property) differing on more than
half of that role's pairs in >= 2 sections (a heading size wrong on every
screen); (3) sections — the table above, style always on. While a token
mismatches or a primitive is open, exit is BLOCKED_BY_FOUNDATION (7) and each
section reads BLOCKED_BY_FOUNDATION: fix the foundation once, not per
section. Inventory COULD_NOT_CHECK / CANNOT_COMPARE outrank it; a would-be
MATCH with an UNVERIFIED section exits 6.

REPORT (`--report out.html [--design-shots DIR] [--app-shots DIR]`)
-------------------------------------------------------------------
A self-contained HTML file per section: verdict, design|app side by side
(`DIR/<section id>.png|jpg|jpeg|webp|gif|svg` embedded as a data URI, else a
sandboxed srcdoc iframe of that render showing only that section, led by a
`default-src 'none'` CSP meta), then its open inventory rows, style rows,
and accepted rows, escaped; no script or network fetch. Evidence for a
human before "ready", never a verdict.

BASELINE (`--baseline F [--write-baseline]`) — regression net, not `--workflow`
--------------------------------------------------------------------------------
`--write-baseline` records the APP side's fingerprint to F — per section its
inventory keys (masked where the app marks sample values) and, with
`--style`, each text-bearing `data-cs` element's normalized values — only
when the run exits 0; a failing run writes nothing (`baseline not written`).
Over an existing F its deltas vs this run are printed first; any delta (or an
unreadable / other-`--style` F) leaves F as is and exits REGRESSION unless
`--accept-regression` is given. F may not be the design, app, accept, or
report path (usage error). Without `--write-baseline`, F is read: unreadable, malformed, or recorded with a different
`--style` is COULD_NOT_CHECK; a section or item REMOVED, an item ADDED inside a
baseline section, or a STYLE_CHANGED value is REGRESSION (8), listing only
those deltas plus the design comparison's one-line verdict. A section new
since the baseline is info. No delta keeps the comparison's own exit (a design
change the app never had stays MISMATCH) and prints `baseline: 0 new delta(s)`;
under COULD_NOT_CHECK_CROP the deltas are appended and exit 9 stands.

USAGE
-----
  parity_differ.py --design <file> --app <file> [--accept <tsv> [--accept-rev REV]]
                   [--min-pairs N] [--style [--style-min-pairs N]] [--json]
                   [--baseline F [--write-baseline [--accept-regression]]]
                   [--workflow --design-tokens F --app-tokens F [--token-map F]
                    [--token-min-pairs N]] [--report F [--design-shots D] [--app-shots D]]
  parity_differ.py --selftest
Public API for sibling scripts: `compare()` (the dict `--json` prints),
`run_workflow()` (the same dict plus `workflow`), `write_report()`,
`inventory_keys()` and `read_side()` (one side, never a verdict),
`crop_problems()`, and `fingerprint()` / `diff_baseline()` /
`apply_baseline()` (BASELINE).
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import functools
import html
import importlib.util
import io
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path

sys.dont_write_bytecode = True

# The whole point of naming these instead of using bare ints: only MATCH (and
# its distinctly printed MATCH_WITH_ACCEPTED form) exits 0, so any caller/CI
# step gating on "exit 0" cannot be fooled by a mismatch, an unseeded app, or
# a one-sided input silently returning 0.
MATCH = 0
MISMATCH = 1
USAGE_ERROR = 2
COULD_NOT_CHECK = 3
CANNOT_COMPARE = 4
STYLE_DIFF = 5                                # --style only; inventory passed
STYLE_COULD_NOT_CHECK = 6                     # --style only; inventory passed, style unverifiable
BLOCKED_BY_FOUNDATION = 7                     # --workflow only; a foundation stage is failing
REGRESSION = 8                                # --baseline only; a new delta vs a passing run
COULD_NOT_CHECK_CROP = 9                      # the two captures of a section are not the same crop
MATCH_WITH_ACCEPTED = "MATCH_WITH_ACCEPTED"   # verdict name; exit code is MATCH
MATCH_WITH_IGNORED = "MATCH_WITH_IGNORED"     # verdict name; exit code is MATCH (owner ignore rows)
# FOUNDATION breadth floors (COMPUTED STYLE): pairs and distinct sections.
_FOUNDATION_MIN_PAIRS = 3
_FOUNDATION_MIN_SECTIONS = 2

_VERDICT_NAMES = {MATCH: "MATCH", MISMATCH: "MISMATCH", USAGE_ERROR: "USAGE_ERROR",
                  COULD_NOT_CHECK: "COULD_NOT_CHECK", CANNOT_COMPARE: "CANNOT_COMPARE",
                  BLOCKED_BY_FOUNDATION: "BLOCKED_BY_FOUNDATION", STYLE_DIFF: "STYLE_DIFF",
                  STYLE_COULD_NOT_CHECK: "STYLE_COULD_NOT_CHECK", REGRESSION: "REGRESSION",
                  COULD_NOT_CHECK_CROP: "COULD_NOT_CHECK_CROP"}
# Computed-style properties every `data-cs` export must carry (COMPUTED STYLE).
_STYLE_PROPS = ("font-family", "font-size", "font-weight", "line-height", "letter-spacing",
                "color", "background-color", "padding", "border-radius", "box-shadow")

# Elements with no closing tag in HTML. Never pushed onto the open-tag stack,
# so a document full of bare `<img>`/`<input>`/... never desyncs it.
_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})
# Subtrees that never render visible inventory.
_SKIP_TAGS = frozenset({"script", "style", "template", "noscript", "head", "datalist"})
# A text run is closed at any of these boundaries; inline tags (span, b, a...)
# merge into the surrounding run so markup-only differences never fire.
_BLOCK_TAGS = frozenset({
    "address", "article", "aside", "blockquote", "body", "br", "dd", "details",
    "dialog", "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer",
    "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "html", "li",
    "main", "menu", "nav", "ol", "p", "pre", "section", "table", "tbody", "td",
    "tfoot", "th", "thead", "tr", "ul",
})
_INTERACTIVE_ROLES = frozenset({
    "button", "link", "tab", "checkbox", "radio", "switch", "menuitem",
    "menuitemcheckbox", "menuitemradio", "textbox", "searchbox", "combobox",
    "slider", "spinbutton",
})
_INPUT_ROLES = {"button": "button", "submit": "button", "reset": "button",
                "image": "button", "checkbox": "checkbox", "radio": "radio",
                "range": "slider"}
_FORM_FIELDS = frozenset({"input", "select", "textarea"})
_MEDIA_TAGS = frozenset({"canvas", "video", "iframe", "object"})
# Class tokens that hide an element through a stylesheet this parser cannot
# evaluate; the export must resolve them with `data-visible` (VISIBILITY).
_HIDING_CLASSES = frozenset({"hidden", "sr-only", "invisible", "d-none", "visually-hidden"})
_ROW_STATUSES = ("MISSING_IN_APP", "EXTRA_IN_APP", "CHANGED", "MOVED")
# Masked text is wrapped per chunk as OPEN <element serial> SEP text CLOSE, so
# contiguous chunks of one masked element fold into one token while separate
# elements stay separate tokens (their count is compared).
_MASK_OPEN, _MASK_SEP, _MASK_CLOSE = "", "", ""
_MASK_SPAN = re.compile(f"{_MASK_OPEN}(\\d+){_MASK_SEP}(.*?){_MASK_CLOSE}", re.DOTALL)
_VALUE_TOKEN = "<value>"
# A value slot holding one of these is a broken render, compared verbatim.
_BROKEN_VALUE = re.compile(r"\b(?:undefined|null|NaN|Invalid Date)\b|\[object Object\]|\{\{|\$\{",
                           re.IGNORECASE)
_HIDDEN_STYLE = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden"
    r"|(?<![\w-])opacity\s*:\s*(?:0*\.?0+|0+\.)%?\s*(?:!important\s*)?(?:;|$)", re.IGNORECASE)


class _Frame:
    """One open element on the parser stack plus its inventory role."""

    __slots__ = (
        "anccap",
        "bodyhide",
        "capture",
        "cells",
        "container",
        "control",
        "cs",
        "cscap",
        "csown",
        "hidden",
        "id",
        "idcap",
        "ignored",
        "item",
        "kind",
        "lines",
        "maskid",
        "notext",
        "row",
        "section",
        "sid",
        "tag",
    )

    def __init__(self, tag: str, sid: str | None) -> None:
        """Start a frame with no inventory role; the caller fills the rest."""
        self.tag, self.sid = tag, sid
        self.section: str | None = None
        self.hidden = self.notext = self.bodyhide = self.ignored = False
        self.maskid: int | None = None          # serial of the enclosing masked element
        self.kind: str | None = None
        self.item: dict | None = None
        self.capture: list[str] | None = None   # owning: text is a label, not free text
        self.idcap: list[str] | None = None     # passive: text kept for aria-labelledby
        self.id: str | None = None
        self.container: dict | None = None
        self.row: dict | None = None
        self.cells = 0
        self.control: dict | None = None
        self.cs: dict | None = None             # this element's computed-style record
        self.anccap: list[str] | None = None    # passive: a data-anchor element's text
        self.lines: str | None = None           # its data-lines (rendered line-box count)
        self.cscap: list[str] | None = None     # passive: its full visible text
        self.csown: list[str] | None = None     # its OWN text nodes (field-B pairing)


class _SectionExtractor(HTMLParser):
    """Stream-parse one HTML render into section records plus their inventory.

    Fail-closed / crash-closed intent: real design and app exports are not
    guaranteed to be well-formed (unbalanced tags, void elements written
    either way, stray end tags). This parser never raises on that input —
    an attribute marker is always attributed to the innermost currently-open
    `data-section`, and an end tag that has no matching open tag is simply
    ignored rather than corrupting the stack. Malformed markup degrades to
    "fewer markers recognized," never to an exception. Frames still open at
    end of input are finalized by `finish()`.
    """

    def __init__(self) -> None:
        """Set up the ordered section list, id lookup, and open-tag stack."""
        super().__init__(convert_charrefs=True)
        self.sections: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self._stack: list[_Frame] = []
        self._ids: dict[str, str] = {}
        self._labels: list[dict] = []
        self._controls: list[dict] = []
        self._buf: list[str] = []
        self._buf_section: str | None = None
        self._mask_seq = 0
        self._buf_lines: str | None = None
        self.ignored: list[dict] = []   # every data-parity-ignore root, never silent

    def _innermost_section(self) -> str | None:
        """Return the nearest currently-open `data-section` id, or None."""
        for frame in reversed(self._stack):
            if frame.sid is not None:
                return frame.sid
        return None

    def _record(self, attrs: list[tuple[str, str | None]]) -> str | None:
        """Apply one tag's section markers to the section they belong to.

        Registers a new section on `data-section`, and — fail-closed, never
        guessing which section an unattributed marker belongs to — counts a
        `data-item` / `data-empty` marker against the innermost open section
        (preferring a section this same tag just opened). Returns the tag's
        own `data-section` id, if any, so the caller knows whether to push it.
        """
        attr_map = dict(attrs)
        if "data-parity-ignore" in attr_map or (self._stack and self._stack[-1].ignored):
            return None   # an ignored subtree registers no section and counts no marker
        sid = attr_map.get("data-section")
        if sid is not None and sid not in self._by_id:
            record = {"id": sid, "items": 0, "empties": 0, "inv": [], "marked": False, "anchors": [], "bad_lines": [],
                      "unresolved": [], "styles": [], "cs_bad": []}
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

    # -- inventory helpers -------------------------------------------------

    def _emit(self, section: str | None, kind: str, role: str = "",
              label: str | None = "", count: int | None = None) -> dict | None:
        """Append one inventory item to its section (items outside sections drop)."""
        if section is None or section not in self._by_id:
            return None
        item = {"kind": kind, "role": role, "label": label, "count": count}
        self._by_id[section]["inv"].append(item)
        return item

    def _flush(self) -> None:
        """Close the pending free-text run into one `text` item."""
        if self._buf:
            text = "".join(self._buf)
            if _MASK_SPAN.sub(r"\2", text).strip():
                item = self._emit(self._buf_section, "text", "", text)
                if item is not None and self._buf_lines:
                    item["lines"] = self._buf_lines
        self._buf, self._buf_section, self._buf_lines = [], None, None

    def _nearest_kind(self, kind: str) -> _Frame | None:
        """Return the innermost open frame of inventory `kind`, or None."""
        for frame in reversed(self._stack):
            if frame.kind == kind:
                return frame
        return None

    def _inventory_start(self, tag: str, attr_map: dict, sid: str | None) -> _Frame:
        """Classify one start tag into an inventory role; return its frame."""
        parent = self._stack[-1] if self._stack else None
        frame = _Frame(tag, sid)
        frame.section = sid if sid is not None else self._innermost_section()
        classes = (attr_map.get("class") or "").split()
        marker = (attr_map.get("data-visible") or "").strip().lower()
        frame.ignored = bool(parent and parent.ignored)
        if not frame.ignored and "data-parity-ignore" in attr_map:
            frame.ignored = True
            self._log_ignored(tag, attr_map, frame.section)
        shown = parent is None or not (parent.hidden or parent.kind == "media"
                                       or (parent.bodyhide and tag != "summary"))
        vis_hidden = bool(
            frame.ignored or not shown or tag in _SKIP_TAGS or "hidden" in attr_map or marker == "false"
            or (tag == "dialog" and "open" not in attr_map)
            or _HIDDEN_STYLE.search(attr_map.get("style") or ""))
        frame.hidden = vis_hidden or (attr_map.get("aria-hidden") or "").lower() == "true"
        frame.bodyhide = tag == "details" and "open" not in attr_map
        own_mark = "data-sample" in attr_map or "data-value" in attr_map
        if parent is not None and parent.maskid is not None:
            frame.maskid = parent.maskid
        elif own_mark:
            self._mask_seq += 1
            frame.maskid = self._mask_seq
        frame.notext = bool((parent and parent.notext) or tag in ("select", "textarea"))
        if tag in _BLOCK_TAGS or sid is not None:
            self._flush()
        sec = frame.section
        role = (attr_map.get("role") or "").strip().lower().split(" ")[0]
        if not vis_hidden and tag == "i" and classes and not role:
            ctrl = self._nearest_kind("control")   # an aria-hidden icon still renders
            frame.kind = "icon"
            frame.item = {"ctrl": ctrl.control if ctrl else None, "section": sec, "text": "",
                          "label": attr_map.get("aria-label") or " ".join(sorted(classes))}
        if frame.hidden:
            return frame
        if sec in self._by_id and not marker and _HIDING_CLASSES.intersection(classes):
            self._by_id[sec]["unresolved"].append(
                f"<{tag} class=\"{' '.join(sorted(_HIDING_CLASSES.intersection(classes)))}\">")
        if own_mark and sec in self._by_id:
            self._by_id[sec]["marked"] = True
        if attr_map.get("id"):
            frame.id, frame.idcap = attr_map["id"], []
        if attr_map.get("data-state"):
            self._emit(sec, "state", "", attr_map["data-state"])

        in_control = self._nearest_kind("control") is not None
        if role in _INTERACTIVE_ROLES or (not role and self._is_native_control(tag, attr_map)):
            self._start_control(frame, tag, attr_map, role)
        elif role == "heading" or (not role and re.fullmatch(r"h[1-6]", tag)):
            level = attr_map.get("aria-level") if role == "heading" else tag[1]
            frame.kind, frame.capture = "heading", []
            frame.item = self._emit(sec, "heading", f"h{level or 2}", None)
            if frame.item is not None:
                frame.item["aria"] = attr_map.get("aria-label")
        elif role in ("img", "image") or (not role and tag in ("img", "svg")):
            self._start_image(frame, tag, attr_map, in_control)
        elif not role and tag in _MEDIA_TAGS:
            frame.kind, frame.notext = "media", True   # fallback content never renders
            self._emit(sec, "media", tag, attr_map.get("aria-label") or attr_map.get("title") or "")
        elif not role and tag == "option":
            frame.kind, frame.capture = "option", []
            frame.item = self._emit(sec, "option", "", attr_map.get("label"))
        elif tag == "label" and not role:
            frame.kind, frame.capture = "label", []
            frame.item = {"text": "", "for": attr_map.get("for"), "section": sec, "used": False}
            self._labels.append(frame.item)
        elif role == "list" or (not role and tag in ("ul", "ol", "menu")):
            frame.container = self._start_container(sec, "list")
        elif role in ("table", "grid", "treegrid") or (not role and tag == "table"):
            frame.container = self._start_container(sec, "table")
        elif role == "listitem" or (not role and tag == "li"):
            self._start_row(frame, "list", owning=True)
        elif role == "row" or (not role and tag == "tr"):
            self._start_row(frame, "table", owning=False)
        elif role in ("cell", "gridcell", "rowheader", "columnheader") or (
                not role and tag in ("td", "th")):
            row_frame = self._nearest_kind("row")
            if row_frame is not None:
                row_frame.cells += 1
                if row_frame.cells == 1:
                    frame.kind, frame.capture, frame.row = "cell0", [], row_frame.row
        raw_lines = attr_map.get("data-lines")
        if raw_lines is not None and not re.fullmatch(r"[1-9][0-9]*", raw_lines.strip()):
            if sec in self._by_id:   # fail closed: never a guessed count
                self._by_id[sec]["bad_lines"].append(f'<{tag} data-lines="{raw_lines}">')
            raw_lines = None
        frame.lines = str(int(raw_lines)) if raw_lines is not None else None
        target = (frame.item if frame.kind in ("heading", "image", "option") else frame.row if frame.kind == "row"
                  else frame.control["item"] if frame.kind == "control" else None)
        if frame.lines and target is not None:
            target["lines"] = frame.lines   # a text run takes its block's count at _flush
        if "data-anchor" in attr_map and sec in self._by_id:
            frame.anccap = []
        if "data-cs" in attr_map and sec in self._by_id:
            self._start_style(frame, tag, attr_map["data-cs"], role)
        return frame

    def _log_ignored(self, tag: str, attr_map: dict, section: str | None) -> None:
        """Record one `data-parity-ignore` root: its section and a printable id.

        The id is the attribute's value when non-empty, else the tag with its
        `data-section` or `id` attribute (e.g. `<div id="x">`), else `<tag>`.
        Descendants of an ignored root are not logged separately.
        """
        label = (attr_map.get("data-parity-ignore") or "").strip()
        if not label:
            extra = next((f' {k}="{attr_map[k]}"' for k in ("data-section", "id") if attr_map.get(k)), "")
            label = f"<{tag}{extra}>"
        self.ignored.append({"section": section, "id": label})

    def _start_style(self, frame: _Frame, tag: str, raw: str | None, role: str) -> None:
        """Record one visible `data-cs` element for the `--style` pairing.

        The record is appended in document order and its text is filled at
        `_finalize`. A `data-cs` that is not a JSON object carrying every
        `_STYLE_PROPS` key as a non-empty string/number is logged to the section's
        `cs_bad` list (fail closed; never a guessed value).
        """
        sec = self._by_id[frame.section]
        try:
            props = json.loads(raw or "")
        except json.JSONDecodeError:
            props = None
        if not isinstance(props, dict) or any(   # "" = the browser did not serialize it
                not isinstance(props.get(p), (str, int, float)) or not str(props[p]).strip()
                for p in _STYLE_PROPS):
            sec["cs_bad"].append(f"<{tag} data-cs>")
            return
        if frame.kind == "heading" and frame.item is not None:
            role = frame.item["role"]
        elif frame.kind == "control" and frame.control["item"] is not None:
            role = frame.control["item"]["role"]
        frame.cs = {"role": role or "text", "text": "",
                    "props": {p: str(props[p]) for p in _STYLE_PROPS}}
        frame.cscap, frame.csown = [], []
        sec["styles"].append(frame.cs)

    @staticmethod
    def _is_native_control(tag: str, attr_map: dict) -> bool:
        """True for a natively interactive element (no explicit role)."""
        if tag == "input":
            return (attr_map.get("type") or "text").lower() != "hidden"
        return (tag in ("button", "select", "textarea", "summary")
                or (tag == "a" and "href" in attr_map))

    def _start_control(self, frame: _Frame, tag: str, attr_map: dict, role: str) -> None:
        """Register a control item whose label resolves at `finish()`."""
        if not role:
            if tag == "input":
                role = _INPUT_ROLES.get((attr_map.get("type") or "text").lower(), "textbox")
            else:
                role = {"a": "link", "select": "combobox", "textarea": "textbox"}.get(tag, "button")
        label_frame = self._nearest_kind("label")
        ctrl = {"item": self._emit(frame.section, "control", role, None), "attrs": attr_map,
                "tag": tag, "text": "", "icons": [],
                "wrap": label_frame.item if label_frame else None}
        frame.kind, frame.control = "control", ctrl
        if tag not in _VOID_TAGS and tag != "select":
            frame.capture = []
        self._controls.append(ctrl)

    def _start_image(self, frame: _Frame, tag: str, attr_map: dict, in_control: bool) -> None:
        """Register an image item, or fold its label into the enclosing control."""
        aria = attr_map.get("aria-label")
        alt = attr_map.get("alt")
        if tag == "img":
            label = aria if aria is not None else alt
            if in_control:
                if label:
                    self._feed_captures(" " + label + " ")
            elif not (alt == "" and not aria):   # alt="" = decorative, not inventoried
                self._emit(frame.section, "image", "", label or "")
            return
        if in_control:
            frame.notext = bool(aria)   # aria-label wins; else <title>/text labels it
            if aria:
                self._feed_captures(" " + aria + " ")
            return
        frame.kind, frame.capture = "image", []
        frame.item = self._emit(frame.section, "image", "", None)
        if frame.item is not None:
            frame.item["aria"] = aria

    def _start_container(self, section: str | None, kind: str) -> dict | None:
        """Open a list/table container item with a running row count."""
        if section not in self._by_id:
            return None
        ordinal = 1 + sum(1 for i in self._by_id[section]["inv"] if i["kind"] == kind)
        return self._emit(section, kind, "", f"#{ordinal}", 0)

    def _start_row(self, frame: _Frame, kind: str, owning: bool) -> None:
        """Open one list/table row: bump its container count, emit its item."""
        for f in reversed(self._stack):
            if f.container is not None and f.container["kind"] == kind:
                f.container["count"] += 1
                break
        frame.kind = "row"
        frame.row = self._emit(frame.section, f"{kind}-{'item' if kind == 'list' else 'row'}", "", "")
        if owning:
            frame.capture = []

    def _feed_captures(self, text: str) -> bool:
        """Send text to every open capture; True if an owning capture took it."""
        owned = False
        for f in self._stack:
            if f.hidden or f.kind == "option":
                continue
            if f.capture is not None:
                f.capture.append(text)
                owned = True
            if f.idcap is not None:
                f.idcap.append(text)
            if f.cscap is not None:
                f.cscap.append(text)
            if f.anccap is not None:
                f.anccap.append(text)
        return owned

    def _finalize(self, frame: _Frame) -> None:
        """Close one frame: fill its item label from the captured text."""
        if frame.tag in _BLOCK_TAGS or frame.sid is not None:
            self._flush()
        if frame.cs is not None:
            frame.cs["text"] = "".join(frame.cscap)
            frame.cs["own"] = "".join(frame.csown)
        if frame.anccap is not None:
            self._by_id[frame.section]["anchors"].append("".join(frame.anccap))
        if frame.kind == "icon":
            text = " ".join(frame.item["text"].split())
            if not text or frame.hidden:   # a visible text run inside <i> is italic text
                label = frame.item["label"] + (f" {text}" if text else "")
                if frame.item["ctrl"] is not None:
                    frame.item["ctrl"]["icons"].append(label)
                else:
                    self._emit(frame.item["section"], "icon", "", label)
            return
        if frame.hidden:
            return
        text = "".join(frame.capture) if frame.capture is not None else ""
        if frame.idcap is not None:
            self._ids[frame.id] = "".join(frame.idcap)
        if frame.kind == "heading" and frame.item is not None:
            aria = frame.item.pop("aria", None)
            frame.item["label"] = text
            if aria:
                frame.item.update(name=aria, source="aria-label")
        elif frame.kind == "image" and frame.item is not None:
            frame.item["label"] = frame.item.pop("aria", None) or text
        elif frame.kind == "option" and frame.item is not None:
            frame.item["label"] = frame.item["label"] or text
        elif frame.kind == "label":
            frame.item["text"] = text
        elif frame.kind == "control":
            frame.control["text"] = text
        elif frame.kind == "row" and frame.row is not None and frame.capture is not None or frame.kind == "cell0" and frame.row is not None:
            frame.row["label"] = text

    # -- HTMLParser callbacks ------------------------------------------------

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Open tag: record its markers, then push it unless it is void."""
        sid = self._record(attrs)
        frame = self._inventory_start(tag, dict(attrs), sid)
        if tag not in _VOID_TAGS:
            self._stack.append(frame)
        else:
            self._finalize(frame)

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        """Self-closed tag (`<x/>`): record markers; never push (no body)."""
        sid = self._record(attrs)
        self._finalize(self._inventory_start(tag, dict(attrs), sid))

    def handle_endtag(self, tag: str) -> None:
        """Pop to the nearest matching open tag; a stray end tag is a no-op.

        Fail-closed against imbalance: if `tag` is not found on the stack
        (e.g. a void element with a stray closing tag, or genuinely
        mismatched markup) the stack is left untouched rather than popping
        the wrong frame. Every popped frame is finalized innermost-first.
        """
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].tag == tag:
                while len(self._stack) > i:
                    self._finalize(self._stack.pop())
                return

    def handle_data(self, data: str) -> None:
        """Route visible text to open label captures, else the free-text run."""
        top = self._stack[-1] if self._stack else None
        if top is None:
            return
        icon = self._nearest_kind("icon")
        if icon is not None and not top.ignored:
            icon.item["text"] += data
        text = (f"{_MASK_OPEN}{top.maskid}{_MASK_SEP}{data}{_MASK_CLOSE}"
                if top.maskid is not None else data)
        if top.kind == "option" and not top.hidden:
            top.capture.append(text)   # option text never leaks into a wrapping label
            return
        if top.hidden or top.notext or top.bodyhide:
            return
        if top.csown is not None:
            top.csown.append(text)
        if not self._feed_captures(text):
            if self._buf_section is None:
                self._buf_section = self._innermost_section()
                block = next((f for f in reversed(self._stack) if f.tag in _BLOCK_TAGS or f.sid is not None), None)
                self._buf_lines = block.lines if block is not None else None
            self._buf.append(text)

    def finish(self) -> None:
        """Finalize open frames and resolve deferred control names.

        Per control: visible text (content; value for input buttons; the
        associated <label> text for form fields) and the accessible name with
        its source (aria-labelledby, aria-label, <label>, content, value,
        alt, title — never the placeholder, which is kept apart).
        """
        while self._stack:
            self._finalize(self._stack.pop())
        self._flush()
        by_for = {lb["for"]: lb for lb in self._labels if lb["for"]}
        for ctrl in self._controls:
            attrs, item, tag = ctrl["attrs"], ctrl["item"], ctrl["tag"]
            label_text = ""
            if tag in _FORM_FIELDS:
                for lb in (by_for.get(attrs.get("id") or ""), ctrl["wrap"]):
                    if lb is not None and lb["text"].strip():
                        lb["used"] = True
                        label_text = label_text or lb["text"]
            itype = (attrs.get("type") or "text").lower() if tag == "input" else ""
            value = None
            if itype in ("button", "submit", "reset"):
                value = attrs.get("value") or {"submit": "Submit", "reset": "Reset"}.get(itype)
            visible = value if value is not None else (label_text if tag in _FORM_FIELDS else ctrl["text"])
            candidates = []
            if attrs.get("aria-labelledby"):
                candidates.append(("aria-labelledby", " ".join(
                    self._ids.get(i, "") for i in attrs["aria-labelledby"].split())))
            candidates += [("aria-label", attrs.get("aria-label")), ("label", label_text)]
            if tag not in _FORM_FIELDS:
                candidates.append(("content", ctrl["text"]))
            if tag == "input":
                candidates += [("value", value), ("alt", attrs.get("alt"))]
            candidates.append(("title", attrs.get("title")))
            source, name = next(((s, n) for s, n in candidates if n and n.strip()), ("none", ""))
            if item is not None:
                item.update(label=visible or "", name=name, source=source,
                            placeholder=attrs.get("placeholder"), icons=ctrl["icons"])
        for lb in self._labels:   # an orphan <label> is still visible text
            if not lb["used"] and lb["text"].strip():
                self._emit(lb["section"], "text", "", lb["text"])


def extract_side(path: str | None) -> list[dict] | None:
    """Return this side's ordered section records, or None if it cannot compare.

    Section view of `read_side` (the same records, without its ignored list).
    """
    return read_side(path)[0]


def read_side(path: str | None) -> tuple[list[dict] | None, list[dict]]:
    """Return `(sections, ignored)` for one side; `sections` is None if it cannot compare.

    `ignored` lists every `data-parity-ignore` root as `{"section", "id"}`
    (`section` None outside every section): excluded from inventory,
    populated-ness, and style, and reported so ignoring is never silent. A
    `.json` side has no ignored list. Each section record is `{"id",
    "populated", "inventory", "marked", "unresolved", "styles", "cs_bad",
    "anchors", "bad_lines"}` (`anchors`: the visible text of each
    `data-anchor` element; `bad_lines`: each `data-lines` value that is not
    a positive integer — the caller fails closed);
    `inventory` is a list of raw items for an HTML side and None for a
    `.json` side (which carries no inventory); `unresolved` lists
    class-based hiding tokens that carry no `data-visible` marker
    (VISIBILITY); `styles` lists `data-cs` records `{"role", "text", "own",
    "props"}` (`own` = its own text nodes; None for `.json`) and `cs_bad`
    the malformed ones. None for the whole side covers every fail-closed
    case in one place: no path given, file absent, unreadable,
    empty/whitespace-only, invalid JSON, or zero sections. A caller must
    treat None as COULD_NOT_CHECK, never as an empty-but-valid side.
    """
    if not path or not os.path.isfile(path):
        return None, []
    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except (OSError, UnicodeDecodeError):
        return None, []
    if not raw.strip():
        return None, []

    if path.lower().endswith(".json"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None, []
        if not isinstance(data, list):
            return None, []
        rows = [{"id": str(row["id"]), "populated": bool(row.get("populated", False)),
                 "inventory": None, "marked": False, "unresolved": [], "styles": None,
                 "cs_bad": [], "anchors": [], "bad_lines": []}
                for row in data if isinstance(row, dict) and "id" in row]
        return rows or None, []

    parser = _SectionExtractor()
    parser.feed(raw)
    parser.close()
    parser.finish()
    if not parser.sections:
        return None, parser.ignored
    return [{"id": s["id"], "populated": s["items"] > 0, "inventory": s["inv"],
             "marked": s["marked"], "unresolved": s["unresolved"], "styles": s["styles"],
             "cs_bad": s["cs_bad"], "anchors": s["anchors"], "bad_lines": s["bad_lines"]}
            for s in parser.sections], parser.ignored


def extract_sections(path: str | None) -> list[tuple[str, bool]] | None:
    """Return this side's ordered `[(section_id, populated), ...]`, or None.

    Section-level view of `extract_side` (same fail-closed None contract).
    """
    side = extract_side(path)
    return None if side is None else [(s["id"], s["populated"]) for s in side]


def _mask_group(chunks: list[str]) -> str:
    """One masked element's text -> `<value>`, unless it is a broken render."""
    content = "".join(chunks)
    if not content.strip() or _BROKEN_VALUE.search(content):
        return f" {content} "
    return f" {_VALUE_TOKEN} "


def _clean(label: str | None, mask: bool) -> str:
    """Whitespace-normalize a label, masking or unwrapping marked data values.

    With `mask`, each masked ELEMENT becomes one `<value>` token (contiguous
    chunks of the same element fold together; separate elements stay
    separate, so their count is compared); a broken-render value stays
    verbatim. Without `mask`, the marked text is compared as-is.
    """
    text = label or ""
    if mask:
        parts, pos, group, gid = [], 0, None, None
        for m in _MASK_SPAN.finditer(text):
            gap = text[pos:m.start()]
            if group is not None and gid == m.group(1) and not gap.strip():
                group.append(gap + m.group(2))
            else:
                if group is not None:
                    parts.append(_mask_group(group))
                parts.append(gap)
                group, gid = [m.group(2)], m.group(1)
            pos = m.end()
        if group is not None:
            parts.append(_mask_group(group))
        text = "".join(parts) + text[pos:]
    return " ".join(_MASK_SPAN.sub(r"\2", text).split())


def _prepare(inventory: list[dict], mask: bool) -> list[dict]:
    """Turn raw items into comparable `{kind, role, disp, cmp, count, key}` rows.

    A control/heading label is its visible text, followed by `[source: name]`
    when the accessible name differs (or `[no accessible name]`), any
    `[icon: ...]`, and `[placeholder: ...]` — a placeholder is never a label.
    """
    out = []
    for raw in inventory:
        disp = _clean(raw["label"], mask)
        notes = []
        if raw.get("source") == "none":
            notes.append("no accessible name")
        elif raw.get("source"):
            name = _clean(raw.get("name"), mask)
            if name.casefold() != disp.casefold():
                notes.append(f"{raw['source']}: {name}")
        notes += [f"icon: {_clean(i, mask)}" for i in raw.get("icons") or ()]
        if (raw.get("placeholder") or "").strip():
            notes.append(f"placeholder: {_clean(raw['placeholder'], mask)}")
        if raw.get("lines"):
            notes.append(f"lines: {raw['lines']}")
        disp = " ".join([disp, *(f"[{n}]" for n in notes)]).strip()
        role = raw["role"]
        key = f"{raw['kind']}:{role}:{disp}" if role else f"{raw['kind']}:{disp}"
        out.append({"kind": raw["kind"], "role": role, "disp": disp, "cmp": disp.casefold(),
                    "count": raw["count"], "key": key})
    return out


def _show(item: dict) -> str:
    """Printable form of one item (containers carry their row count)."""
    return f"{item['key']} ({item['count']} rows)" if item["count"] is not None else item["key"]


def inventory_keys(path: str | None) -> list[dict] | None:
    """Public one-side inventory: `[{"id", "populated", "items", "unresolved"}]`.

    For callers that must ask "does this side show element K?" without a
    two-sided verdict (agentic-delivery's `feedback_ledger.py`). `items` lists
    each item key exactly as a diff row prints it (`kind:role:label`, unmasked,
    since masking needs both sides), or is None for a `.json` side (no
    inventory). `unresolved` is `extract_side`'s class-hiding list; a non-empty
    one means presence cannot be trusted and the caller must fail closed. None
    for the whole side under `extract_side`'s contract. Never a verdict.
    """
    side = extract_side(path)
    if side is None:
        return None
    return [{"id": s["id"], "populated": s["populated"], "unresolved": list(s["unresolved"]),
             "items": None if s["inventory"] is None
             else [it["key"] for it in _prepare(s["inventory"], False)]} for s in side]


def diff_inventory(design: list[dict], app: list[dict], mask: bool) -> dict:
    """Diff two sections' raw inventories; return matched/total/rows.

    Multiset comparison on (kind, role, case-folded label); container items
    compare by (kind, ordinal) and row count — counts are always compared.
    Leftovers pair into CHANGED rows (same kind+label with a different role
    first, then same kind+role with a different label), the rest become
    MISSING_IN_APP / EXTRA_IN_APP. Pure function of the two inventories — no
    size or geometry input exists.
    """
    d_items, a_items = _prepare(design, mask), _prepare(app, mask)
    rows: list[dict] = []
    matched = 0
    a_cont = {(i["kind"], i["cmp"]): i for i in a_items if i["count"] is not None}
    d_cont_keys = set()
    for it in (i for i in d_items if i["count"] is not None):
        d_cont_keys.add((it["kind"], it["cmp"]))
        other = a_cont.get((it["kind"], it["cmp"]))
        if other is None:
            rows.append({"status": "MISSING_IN_APP", "item": it["key"], "design": _show(it), "app": None})
        elif other["count"] == it["count"]:
            matched += 1
        else:
            rows.append({"status": "CHANGED", "item": it["key"], "design": _show(it), "app": _show(other)})
    for key, other in a_cont.items():
        if key not in d_cont_keys:
            rows.append({"status": "EXTRA_IN_APP", "item": other["key"], "design": None, "app": _show(other)})

    d_nc = [i for i in d_items if i["count"] is None]
    a_nc = [i for i in a_items if i["count"] is None]
    used = [False] * len(a_nc)
    d_left = []
    for it in d_nc:
        hit = next((j for j, o in enumerate(a_nc) if not used[j] and o["kind"] == it["kind"]
                    and o["role"] == it["role"] and o["cmp"] == it["cmp"]), None)
        if hit is None:
            d_left.append(it)
        else:
            used[hit] = True
            matched += 1
    a_left = [o for j, o in enumerate(a_nc) if not used[j]]
    for same in (lambda d, a: d["cmp"] == a["cmp"], lambda d, a: d["role"] == a["role"]):
        still = []
        for it in d_left:
            hit = next((o for o in a_left if o["kind"] == it["kind"] and same(it, o)), None)
            if hit is None:
                still.append(it)
            else:
                a_left.remove(hit)
                rows.append({"status": "CHANGED", "item": it["key"], "design": it["key"], "app": hit["key"]})
        d_left = still
    rows += [{"status": "MISSING_IN_APP", "item": i["key"], "design": i["key"], "app": None} for i in d_left]
    rows += [{"status": "EXTRA_IN_APP", "item": o["key"], "design": None, "app": o["key"]} for o in a_left]
    return {"matched": matched, "total": len(d_items), "rows": rows}


def _style_norm(value: str) -> str:
    """Canonical text of one computed value: case, whitespace, and quotes folded."""
    text = " ".join(value.replace('"', "").replace("'", "").split()).casefold()
    return re.sub(r"\s*([,()])\s*", r"\1", text)


def _px(value: str) -> float | None:
    """A single `<number>px` computed value as a float, else None (no unit conversion)."""
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)px", _style_norm(value))
    return float(m.group(1)) if m else None


def _style_accept(accept: dict, row: dict) -> dict | None:
    """The owner accept entry covering one style diff row, else None.

    A `style` row matches on property + normalized design and app values, its
    section scope before `global`; a `min-<property>` rule covers a design px
    value below its minimum that the app renders at exactly that minimum.
    """
    d, a = _style_norm(row["design"]), _style_norm(row["app"])
    for scope in (row["section"], "global"):
        hit = accept.get(("style", scope, row["property"], d, a))
        if hit is not None:
            return hit
    rule = accept.get(("rule", row["property"]))
    dp, ap = _px(d), _px(a)
    if rule is not None and dp is not None and ap is not None and dp < rule["min"] == ap:
        return rule
    return None


def diff_styles(design: list[dict], app: list[dict], min_pairs: int | None = None,
                accept: dict | None = None) -> dict:
    """Pair `data-cs` elements across two sides and diff their computed styles.

    Pure except that it counts `used` on the matching `accept` entries. Pairs
    by (section, role, case-folded visible text), masked as the inventory
    masks when both sections carry value markers; duplicates pair in document
    order; a design element left unpaired is retried on its identical OWN
    text nodes (same section + role). Returns `{"verdict", "pairs",
    "identical", "identity", "unpaired", "foundation", "primitives",
    "section_pairs", "accepted", "tolerated", "per_property", "top", "rows",
    "lines"}` (`identity` = pairs with no un-accepted difference;
    `per_property` = differing pairs per property, most first; `top` = up to
    10 open rows), each row `{"section", "element", "property", "design",
    "app", "foundation", "accepted", "tolerated"}` (+ `reason`/`owner` when
    accepted or tolerated by an owner `threshold`, `_apply_thresholds`). A row covered by an owner
    `style`/`rule` accept entry (`_style_accept`) is ACCEPTED and never counts
    toward FOUNDATION or STYLE_DIFF. A property is FOUNDATION only when its
    OPEN rows differ on more than half of all pairs AND on pairs in >= 2
    sections AND on >= max(3, `min_pairs`) pairs; otherwise its rows print per
    pair. A PRIMITIVE is a (role, property) whose open rows span >= 2 sections
    and more than half of that role's pairs, on a property not already
    FOUNDATION (a `--workflow` blocker). STYLE_COULD_NOT_CHECK on any
    malformed `data-cs`, zero pairs, or fewer pairs than `min_pairs` (the
    caller's `--style-min-pairs`, never the inventory floor);
    STYLE_MATCH_WITH_ACCEPTED when every difference is accepted. Style never
    feeds inventory completeness.
    """
    accept = accept or {}
    bad = [f"{side} section '{s['id']}': {b}" for side, recs in (("design", design), ("app", app))
           for s in recs for b in s["cs_bad"]]
    app_map = {s["id"]: s for s in app}
    pairs, unpaired = [], 0
    for sec in design:
        a_sec = app_map.get(sec["id"]) or {}
        mask = sec["marked"] and a_sec.get("marked", False)
        a_recs = list(a_sec.get("styles") or ())
        pool: dict = {}
        for rec in a_recs:
            pool.setdefault((rec["role"], _clean(rec["text"], mask).casefold()), []).append(rec)
        taken, left = set(), []
        for rec in sec["styles"] or ():
            text = _clean(rec["text"], mask)
            hits = pool.get((rec["role"], text.casefold())) if text else None
            if hits:
                hit = hits.pop(0)
                taken.add(id(hit))
                pairs.append((sec["id"], f"{rec['role']}:{text}", rec["props"], hit["props"]))
            elif text:
                left.append(rec)
        # Second pass (field-B rule) for leftovers only: identical OWN text nodes.
        own_pool: dict = {}
        for rec in a_recs:
            own = _clean(rec.get("own"), mask)
            if id(rec) not in taken and own:
                own_pool.setdefault((rec["role"], own.casefold()), []).append(rec)
        for rec in left:
            own = _clean(rec.get("own"), mask)
            hits = own_pool.get((rec["role"], own.casefold())) if own else None
            if hits:
                pairs.append((sec["id"], f"{rec['role']}:{own}", rec["props"], hits.pop(0)["props"]))
            else:
                unpaired += 1
    by_prop: dict = {p: [] for p in _STYLE_PROPS}
    identical = 0
    sec_ident: Counter = Counter()   # per section: pairs with no un-accepted difference
    for sid, element, d, a in pairs:
        diffs = [p for p in _STYLE_PROPS if _style_norm(d[p]) != _style_norm(a[p])]
        identical += not diffs
        clean = True
        for p in diffs:
            row = {"section": sid, "element": element, "property": p, "design": d[p], "app": a[p],
                   "tolerated": False}
            hit = _style_accept(accept, row)
            row["accepted"] = hit is not None
            clean = clean and hit is not None
            if hit is not None:
                hit["used"] += 1
                row.update(reason=hit["reason"], owner=hit["owner"])
            by_prop[p].append(row)
        sec_ident[sid] += clean
    n = len(pairs)
    opened = {p: [r for r in by_prop[p] if not r["accepted"]] for p in _STYLE_PROPS}
    # A global type/box claim needs breadth, not just a majority: a majority
    # of 2 pairs, or of pairs all in one section, is a local diff.
    floor = max(_FOUNDATION_MIN_PAIRS, min_pairs or 0)
    foundation = [p for p in _STYLE_PROPS
                  if 2 * len(opened[p]) > n and len(opened[p]) >= floor
                  and len({r["section"] for r in opened[p]}) >= _FOUNDATION_MIN_SECTIONS]
    role_pairs = Counter(el.split(":", 1)[0] for _, el, _, _ in pairs)
    groups: dict = {}
    for p in _STYLE_PROPS:
        for r in opened[p] if p not in foundation else ():
            groups.setdefault((r["element"].split(":", 1)[0], p), []).append(r)
    primitives = [{"role": role, "property": p, "pairs": len(g), "of": role_pairs[role],
                   "sections": len({r["section"] for r in g}),
                   "common": Counter((r["design"], r["app"]) for r in g).most_common(1)[0][0]}
                  for (role, p), g in groups.items()
                  if len({r["section"] for r in g}) >= _FOUNDATION_MIN_SECTIONS and 2 * len(g) > role_pairs[role]]
    sec_pairs = Counter(sid for sid, _, _, _ in pairs)
    thr_lines = _apply_thresholds(accept, opened, foundation, primitives, sec_pairs, sec_ident)
    opened = {p: [r for r in g if not r["tolerated"]] for p, g in opened.items()}
    rows = [dict(r, foundation=p in foundation) for p in _STYLE_PROPS for r in by_prop[p]]
    n_open = sum(len(g) for g in opened.values())
    n_tol = sum(r["tolerated"] for r in rows)
    n_acc = len(rows) - n_open - n_tol
    ident = sum(sec_ident.values())
    head = (f"style: {n} text-matched pair(s); style-identical {identical}/{n} = {_pct(identical, n)}; "
            f"identity (owner-accepted ignored) {ident}/{n} = {_pct(ident, n)}; "
            f"{unpaired} design element(s) with no counterpart not style-checked.")
    per_property = {p: len(by_prop[p]) for p in sorted(_STYLE_PROPS, key=lambda q: (-len(by_prop[q]),
                                                                                    _STYLE_PROPS.index(q)))
                    if by_prop[p]}
    top = sorted((r for p in _STYLE_PROPS for r in opened[p]), key=lambda r: -per_property[r["property"]])[:10]
    if bad or not n or (min_pairs is not None and n < min_pairs):
        verdict = "STYLE_COULD_NOT_CHECK"
        why = (f"malformed data-cs (needs a JSON object with {', '.join(_STYLE_PROPS)}): "
               f"{'; '.join(bad[:5])}" if bad else
               "no text-matched data-cs pairs — export computed styles on both sides" if not n else
               f"{n} style pair(s), below the caller's --style-min-pairs {min_pairs}")
        lines = [f"STYLE_COULD_NOT_CHECK: {why}.", head]
    elif n_open:
        verdict = "STYLE_DIFF"
        n_pairs = len({(r["section"], r["element"]) for g in opened.values() for r in g})
        lines = [(f"STYLE_DIFF: {n_open} property difference(s) on {n_pairs} of {n} pair(s); "
                 f"{len(foundation)} FOUNDATION propert(ies); {n_acc} owner-accepted. "
                 "Reported apart from completeness."), head]
    elif n_acc or n_tol:
        verdict = "STYLE_MATCH_WITH_ACCEPTED"
        lines = [(f"STYLE_MATCH_WITH_ACCEPTED (accepted={n_acc}{f', tolerated={n_tol}' if n_tol else ''}): "
                 "not a plain STYLE_MATCH — every style difference is a row, rule, or section threshold "
                 "of the owner-authored accept file."), head]
    else:
        verdict = "STYLE_MATCH"
        lines = ["STYLE_MATCH: every text-matched pair is identical on every compared property.", head]
    lines += thr_lines
    for p in _STYLE_PROPS:
        group = opened[p]
        if p in foundation:
            (d, a), _ = Counter((r["design"], r["app"]) for r in group).most_common(1)[0]
            lines.append(f"FOUNDATION {p}: differs on {len(group)}/{n} pairs in "
                         f"{len({r['section'] for r in group})} section(s) (most common: {d} -> {a}) "
                         "— fix the global type/box foundation before any per-section work.")
        elif group:
            lines.append(f"STYLE_DIFF {p} ({len(group)} pair(s)):")
            lines += [f"  section '{r['section']}' {r['element'][:60]}: {r['design']} -> {r['app']}"
                      for r in group]
    if per_property:
        lines.append("mismatch count per property: " + ", ".join(f"{p}={k}" for p, k in per_property.items()))
    if top:
        lines.append("top style diffs (text | prop | design | app):")
        lines += [f"  {r['element'].split(':', 1)[1][:60]} | {r['property']} | {r['design']} | {r['app']}"
                  for r in top]
    acc = Counter((r["property"], r["design"], r["app"], r["reason"], r["owner"]) for r in rows if r["accepted"])
    lines += [f"ACCEPTED {p}: {d} -> {a} on {k} pair(s)  [{why}; {who}]" for (p, d, a, why, who), k in acc.items()]
    stale = [" ".join(k) for k, row in accept.items()
             if len(k) != 4 and k[0] not in ("visual-reviewed", "ignore") and not row["used"]]
    if stale:
        lines.append(f"info: style accept row(s)/rule(s) matching no difference (stale): {', '.join(stale)}")
    return {"verdict": verdict, "pairs": n, "identical": identical, "identity": ident, "unpaired": unpaired,
            "foundation": foundation, "primitives": primitives, "accepted": n_acc, "tolerated": n_tol,
            "per_property": per_property, "top": [{k: r[k] for k in ("section", "element", "property", "design",
                                                                     "app")} for r in top],
            "section_pairs": dict(sec_pairs), "rows": rows, "lines": lines}


def _apply_thresholds(accept: dict, opened: dict, foundation: list, primitives: list, sec_pairs: Counter,
                      sec_ident: Counter) -> list[str]:
    """Apply owner `threshold` accept rows; return their report lines.

    For a section with a `("threshold", section)` entry and >= 1 open style
    row: when its identity (pairs with no un-accepted difference / its
    pairs) is at least the threshold, every open row there that is not a
    FOUNDATION property or a PRIMITIVE (role, property) is marked
    `tolerated` (side effect on the rows in `opened`; the entry's `used` is
    counted). Below the threshold, rows stay open. A threshold never waives
    a FOUNDATION or PRIMITIVE row; an entry for a section with no open row
    stays unused (reported stale by the caller).
    """
    prim = {(p["role"], p["property"]) for p in primitives}
    lines = []
    for key, entry in accept.items():
        if key[0] != "threshold":
            continue
        sid = key[1]
        rows = [r for g in opened.values() for r in g if r["section"] == sid]
        if not rows:
            continue
        entry["used"] += 1
        k, total = sec_ident[sid], sec_pairs[sid]
        what = f"THRESHOLD section '{sid}': style identity {k}/{total} = {_pct(k, total)}"
        if k * 100 < entry["pct"] * total:
            lines.append(f"{what} < owner threshold {entry['shown']}% — its {len(rows)} row(s) stay open.")
            continue
        ok = [r for r in rows if r["property"] not in foundation
              and (r["element"].split(":", 1)[0], r["property"]) not in prim]
        for r in ok:
            r.update(tolerated=True, reason=f"owner threshold {entry['shown']}%", owner="accept file")
        kept = (f"{len(rows) - len(ok)} FOUNDATION/PRIMITIVE row(s) stay open (never waived by a threshold)"
                if len(rows) > len(ok) else "")
        done = f"{len(ok)} row(s) tolerated" if ok else ""
        lines.append(f"{what} >= owner threshold {entry['shown']}% — {'; '.join(x for x in (done, kept) if x)}.")
    return lines


def _norm(text: str | None) -> str:
    """Collapse whitespace (accept-row and diff-row keys compare on this)."""
    return " ".join((text or "").split())


def parse_accept(text: str) -> tuple[dict | None, str | None]:
    """Parse accept-file text into `{(section, status, item_cf, app_value): row}`.

    Pure. Returns `(rows, None)` or `(None, error)`: fail closed on any row
    without all 7 non-empty fields, an unknown status, a count that is not a
    positive integer, an app-value that is not `-` exactly for
    MISSING_IN_APP, or a duplicate key. `item` compares case-folded (as the
    diff does); `app-value` compares exactly after whitespace collapse.
    A row whose first field is `style` or `rule` and whose second is not an
    inventory status is a style approval: `style scope property design-value
    app-value reason owner` (scope `global` or a section id; values compare
    normalized) keyed `("style", scope, property, design, app)`, or `rule
    min-<property> <N>px reason owner` keyed `("rule", property)`. An unknown
    property or rule, or a malformed value, fails closed. `visual-reviewed
    section reason owner` is keyed `("visual-reviewed", section)`;
    `threshold section pct` (exactly 3 fields, 0 < pct <= 100, optional `%`)
    is keyed `("threshold", section)` with a `Fraction` `pct`.
    """
    rows: dict = {}
    first = True
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = [f.strip() for f in line.split("\t")]
        header, first = first and fields[0].lower() == "section", False
        if header:   # the first non-comment row may be a column header
            continue
        kind = fields[0] if fields[0] in ("style", "rule", "visual-reviewed", "threshold", "ignore") \
            and fields[1:2] != [] and fields[1] not in _ROW_STATUSES else None
        if kind == "ignore":
            if len(fields) != 3 or not all(fields):
                return None, (f"accept file row {n}: an ignore row needs 3 non-empty fields (ignore, section "
                              "or - outside every section, data-parity-ignore id)")
            key = ("ignore", fields[1], fields[2])
            if key in rows:
                return None, f"accept file row {n} duplicates an earlier row"
            rows[key] = {"used": 0}
            continue
        if kind == "threshold":
            pct = re.fullmatch(r"(\d{1,3}(?:\.\d+)?)%?", fields[2]) if len(fields) == 3 else None
            if pct is None or not all(fields) or not 0 < Fraction(pct.group(1)) <= 100:
                return None, (f"accept file row {n}: a threshold row needs 3 non-empty fields (threshold, "
                              "section, style-identity % above 0 and at most 100)")
            key = ("threshold", fields[1])
            if key in rows:
                return None, f"accept file row {n} duplicates an earlier row"
            rows[key] = {"pct": Fraction(pct.group(1)), "shown": fields[2].rstrip("%"), "used": 0}
            continue
        if kind == "visual-reviewed":
            if len(fields) != 4 or not all(fields):
                return None, (f"accept file row {n}: a visual-reviewed row needs 4 non-empty fields "
                              "(visual-reviewed, section, reason, owner)")
            key, entry = ("visual-reviewed", fields[1]), {}
        elif kind == "rule":
            prop = fields[1][4:] if fields[1].startswith("min-") else ""
            if len(fields) != 5 or not all(fields) or prop not in _STYLE_PROPS or _px(fields[2]) is None:
                return None, (f"accept file row {n}: a rule needs 5 non-empty fields (rule, min-<property>, "
                              f"<N>px, reason, owner) with a property from {', '.join(_STYLE_PROPS)}")
            key, entry = ("rule", prop), {"min": _px(fields[2])}
        elif kind == "style":
            if len(fields) != 7 or not all(fields) or fields[2] not in _STYLE_PROPS:
                return None, (f"accept file row {n}: a style row needs 7 non-empty fields (style, scope, "
                              f"property, design-value, app-value, reason, owner) with a property from "
                              f"{', '.join(_STYLE_PROPS)}")
            key, entry = ("style", fields[1], fields[2], _style_norm(fields[3]), _style_norm(fields[4])), {}
        if kind:
            if key in rows:
                return None, f"accept file row {n} duplicates an earlier row"
            rows[key] = {**entry, "used": 0, "reason": fields[-2], "owner": fields[-1]}
            continue
        if len(fields) != 7 or not all(fields):
            return None, (f"accept file row {n} needs 7 non-empty tab-separated fields (section, "
                          "status, item, app-value, count, reason, owner-quote/commit)")
        section, status, item, app, count, reason, owner = fields
        if status not in _ROW_STATUSES:
            return None, f"accept file row {n}: status {status!r} is not one of {', '.join(_ROW_STATUSES)}"
        if not re.fullmatch(r"[1-9][0-9]*", count):
            return None, f"accept file row {n}: count {count!r} is not a positive integer"
        if (status == "MISSING_IN_APP") != (app == "-"):
            return None, f"accept file row {n}: app-value must be '-' exactly when status is MISSING_IN_APP"
        key = (section, status, _norm(item).casefold(), _norm(app))
        if key in rows:
            return None, f"accept file row {n} duplicates an earlier row"
        rows[key] = {"count": int(count), "used": 0, "reason": reason, "owner": owner}
    return rows, None


@functools.lru_cache(maxsize=1)
def _focus_gate():
    """Import agentic-delivery's `focus_gate.py` from the sibling skill dir.

    Returns the module, or None when it is not installed alongside (or fails
    to import) — the caller then requires `--accept-rev` and the `git log`
    owner check. Side effect: none beyond the import (no bytecode written).
    """
    path = Path(__file__).resolve().parents[2] / "agentic-delivery" / "scripts" / "focus_gate.py"
    if not path.is_file():
        return None
    sys.path.insert(0, str(path.parent))   # focus_gate imports its sibling refix_gate
    try:
        spec = importlib.util.spec_from_file_location("focus_gate", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:   # noqa: BLE001 — any import failure falls back, fail closed
        return None
    finally:
        sys.path.remove(str(path.parent))


def _git(repo: str, args: list) -> str:
    """Run `git -C repo <args>`; raise RuntimeError on a non-zero exit."""
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {args[0]} failed (rc={proc.returncode})")
    return proc.stdout


def read_owner_authored(path: str, rev: str | None = None,
                        use_focus_gate: bool | None = None) -> tuple[str | None, str | None, str | None]:
    """Read `path` from its committed blob and verify owner authorship.

    Returns `(text, source, None)` when trusted, else `(None, None, reason)`.
    With focus_gate importable (and `use_focus_gate` not False), reuses its
    `load_record` commit-authorship trust (commit route only) at `rev`
    (default HEAD); owners come from its `resolve_owners`. Otherwise `rev` is
    required and every commit touching the file must be authored by an email
    in `DCR_OWNER_EMAIL` with no `Co-authored-by:` trailer. `use_focus_gate`
    False forces the fallback (self-test hook). Never raises; runs only local
    read-only git commands.
    """
    fg = _focus_gate() if use_focus_gate is not False else None
    if fg is None and not rev:
        return None, None, ("--accept-rev is required when agentic-delivery's focus_gate.py is "
                            "not installed alongside (authorship is checked on a committed blob)")
    rev = rev or "HEAD"
    if rev.startswith("-"):   # never let a revision be parsed as a git option
        return None, None, f"invalid --accept-rev {rev!r}"
    try:
        abspath = os.path.realpath(os.path.abspath(path))
        top = os.path.realpath(_git(os.path.dirname(abspath), ["rev-parse", "--show-toplevel"]).strip())
        rel = Path(os.path.relpath(abspath, top)).as_posix()
        text = _git(top, ["show", f"{rev}:{rel}"])
        if fg is not None:
            git = fg.real_git(top)
            _, trusted, source, reasons = fg.load_record(
                git, rel, rev, fg.resolve_owners(None, git), commit_only=True)
            return (text, source, None) if trusted else (None, None, "; ".join(reasons))
        owners = {e.strip("<>").casefold() for e in re.split(r"[,\s]+", os.environ.get("DCR_OWNER_EMAIL", ""))
                  if e.strip("<>")}
        if not owners:
            return None, None, "no owner email configured (DCR_OWNER_EMAIL)"
        log = _git(top, ["log", "--format=%H%x1f%ae%x1f%(trailers:key=Co-authored-by,valueonly)%x1e",
                         rev, "--", rel])
    except (OSError, RuntimeError) as exc:
        return None, None, f"accept file not verifiable at {rev}:{path} ({exc})"
    commits = [c.strip().split("\x1f") for c in log.split("\x1e") if c.strip()]
    reasons = [] if commits else ["no commit touches the accept file"]
    for parts in commits:
        sha, email, coauthor = parts[0][:7], parts[1].strip().casefold(), "".join(parts[2:]).strip()
        if email not in owners:
            reasons.append(f"commit {sha} by {email or '?'} is not the owner")
        elif coauthor:
            reasons.append(f"commit {sha} carries a Co-authored-by trailer (agent-assisted)")
    if reasons:
        return None, None, "; ".join(reasons)
    return text, f"owner-log {commits[0][0][:7]}", None


def load_accept(path: str | None, rev: str | None = None,
                use_focus_gate: bool | None = None) -> tuple[dict | None, str | None, str | None]:
    """Load an owner-authored accepted-deviations file.

    Returns `(rows, None, source)` on success or `(None, error, None)` — fail
    closed when the file is not owner-authored/committed
    (`read_owner_authored`) or malformed (`parse_accept`). `path=None` means
    no file was given and yields an empty mapping.
    """
    if path is None:
        return {}, None, None
    text, source, err = read_owner_authored(path, rev, use_focus_gate)
    if err is not None:
        return None, f"accept file is not owner-authored or not committed: {err}", None
    rows, err = parse_accept(text)
    return (rows, None, source) if err is None else (None, err, None)


def _pct(matched: int, total: int) -> str:
    """Completeness, floored to 0.1%; any shortfall prints `(<100%)`; `n/a` when total is 0."""
    if not total:
        return "n/a"
    if matched >= total:
        return "100.0%"
    tenths = matched * 1000 // total
    return f"{tenths // 10}.{tenths % 10}% (<100%)"


_PRECONDITION = (
    "precondition: both renders must share the same auth + data state "
    "(for gated sections: dev identity past sign-in on both sides, seeded) "
    "— a section gated behind sign-in reads as 'missing' on a signed-out "
    "render; confirm before building. This matched-state diff does not "
    "replace the signed-out default-surface check.")
_BASIS = ("basis: element inventory (headings, visible text, controls by role + visible text + "
          "accessible name, images, media, icons, options, list/table rows, data-state) — size, "
          "height, width, bounding boxes, and pixel counts are never inputs.")


def compare(design_path: str | None, app_path: str | None, accept_path: str | None = None,
            accept_rev: str | None = None, use_focus_gate: bool | None = None,
            min_pairs: int | None = None, style: bool = False,
            style_min_pairs: int | None = None) -> dict:
    """Compare a design render against an app render; return the full result.

    The result dict carries `exit_code`, `verdict`, `report` (human text) and,
    once both sides load, `sections` / `overall` completeness, `accepted_n`,
    `pairs` (matched element pairs), and `style` (`diff_styles`' dict when
    `style`, else None). Two-sided or no output: a missing/unreadable/empty/
    sectionless side on EITHER end, an unresolved class-based hiding token,
    or an accept file that is not owner-authored or is malformed returns
    COULD_NOT_CHECK before any comparison runs; so do zero pairs on a
    would-be pass and fewer inventory pairs than `min_pairs` on any verdict.
    `verdict` stays the completeness verdict; a passing inventory takes the
    style exit (STYLE_DIFF / STYLE_COULD_NOT_CHECK). `style_min_pairs` floors
    style pairs only; `min_pairs` never reaches style. `use_focus_gate` is
    passed to `read_owner_authored`. A section failing the same-crop guard
    (`crop_problems`) is UNVERIFIED and unscored while the rest is scored,
    exit COULD_NOT_CHECK_CROP; a design-side `data-parity-ignore` without an
    owner `ignore` row is COULD_NOT_CHECK; `ignored` lists each side's
    ignored roots (also printed in the report).
    """
    def early(code: int, report: str) -> dict:
        """Result for a verdict reached before any inventory comparison."""
        return {"exit_code": code, "verdict": _VERDICT_NAMES[code], "report": report}

    design, d_ignored = read_side(design_path)
    if design is None:
        return early(COULD_NOT_CHECK, (
            f"COULD_NOT_CHECK: design side unreadable, empty, or has no "
            f"sections ({design_path!r}). Two-sided input is required — a "
            "one-sided read cannot certify parity."))
    app, a_ignored = read_side(app_path)
    if app is None:
        return early(COULD_NOT_CHECK, (
            f"COULD_NOT_CHECK: app side unreadable, empty, or has no "
            f"sections ({app_path!r}). Two-sided input is required — a "
            "one-sided read cannot certify parity."))
    unresolved = [f"{side} section '{s['id']}': {u}" for side, recs in (("design", design), ("app", app))
                  for s in recs for u in s["unresolved"]]
    if unresolved:
        return early(COULD_NOT_CHECK, (
            "COULD_NOT_CHECK: class-based hiding with no computed-visibility marker — "
            f"{'; '.join(unresolved[:5])}. Re-export the DOM with data-visible=\"true\" or "
            "\"false\" on every element carrying hidden, sr-only, invisible, d-none, or "
            "visually-hidden; stylesheet visibility is not guessed."))
    bad_lines = [f"{side} section '{s['id']}': {b}" for side, recs in (("design", design), ("app", app))
                 for s in recs for b in s["bad_lines"]]
    if bad_lines:
        return early(COULD_NOT_CHECK, (
            f"COULD_NOT_CHECK: data-lines must be a positive integer line-box count — {'; '.join(bad_lines[:5])}. "
            "Re-export the count; it is never guessed."))
    accept, err, accept_source = load_accept(accept_path, accept_rev, use_focus_gate)
    if accept is None:
        return early(COULD_NOT_CHECK, f"COULD_NOT_CHECK: {err} — acceptance cannot be verified.")
    # A design-side ignore removes a requirement: only an owner row may do that.
    uncovered = [r for r in d_ignored if ("ignore", r["section"] or "-", r["id"]) not in accept]
    if uncovered:
        return early(COULD_NOT_CHECK, (
            "COULD_NOT_CHECK: design-side data-parity-ignore without an owner-authored accept row "
            "ignore<TAB><section><TAB><id> (section - outside every section): "
            f"{', '.join(_ignored_label(r) for r in uncovered)} — ignoring a design element removes a "
            "requirement, so the owner decides it."))
    for r in d_ignored:
        accept[("ignore", r["section"] or "-", r["id"])]["used"] += 1
    crop = crop_problems(design, app)

    design_ids = [s["id"] for s in design]
    design_pop = [s["id"] for s in design if s["populated"]]
    app_map = {s["id"]: s for s in app}
    states = {sid: ("missing" if sid not in app_map else
                    "populated" if app_map[sid]["populated"] else "empty") for sid in design_ids}

    # UNSEEDED: >=2 design-populated sections, ALL present-but-empty in the
    # app (none missing). A single missing section among them means the gap
    # is structural, not a seeding problem — that falls through to MISMATCH.
    if len(design_pop) >= 2 and all(states[sid] == "empty" for sid in design_pop):
        return early(CANNOT_COMPARE, (
            "CANNOT_COMPARE: app is UNSEEDED — every design-populated section "
            f"({', '.join(design_pop)}) is present in the app but empty. "
            "seed the app's data to the design's data state first. "
            "Do NOT condense or remove the empty sections — the design wants "
            "them populated. This is a data-seeding precondition failure, not "
            "a structural gap, and it is never resolved by trimming."))

    missing = [sid for sid in design_ids if states[sid] == "missing"]
    empty = [sid for sid in design_pop if states[sid] == "empty"]
    extra = [s["id"] for s in app if s["id"] not in set(design_ids)]
    d_ign_keys = {(r["section"], r["id"]) for r in d_ignored}
    a_unpaired = [r for r in a_ignored if r["section"] is not None and (r["section"], r["id"]) not in d_ign_keys]

    sections, no_inventory = [], []
    for sec in design:
        sid, d_inv = sec["id"], sec["inventory"]
        entry = {"id": sid, "state": states[sid], "rows": []}
        a_sec = app_map.get(sid)
        sections.append(entry)
        if d_inv is None or (a_sec is not None and a_sec["inventory"] is None):
            no_inventory.append(sid)
            entry.update(design_items=None, matched=None, completeness_pct=None)
            continue
        if sid in crop:   # not the same crop: this section alone is unscored (UNVERIFIED)
            entry.update(design_items=None, matched=None, completeness_pct=None, crop=crop[sid])
            continue
        if a_sec is None:
            diff = {"matched": 0, "total": len(d_inv), "rows": []}
        else:
            diff = diff_inventory(d_inv, a_sec["inventory"], sec["marked"] and a_sec["marked"])
            # An app-side ignore with no design counterpart hides app content: open row.
            diff["rows"] += [{"status": "EXTRA_IN_APP", "item": f"ignored:{r['id']}", "design": None,
                              "app": f"ignored:{r['id']}"} for r in a_unpaired if r["section"] == sid]
        entry.update(design_items=diff["total"], matched=diff["matched"],
                     completeness_pct=_pct(diff["matched"], diff["total"]), rows=diff["rows"])
    _fold_moves(sections)

    tot_matched = tot_items = open_rows = accepted_n = 0
    for entry in sections:
        if entry["design_items"] is None:
            continue
        sid = entry["id"]
        for row in entry["rows"]:
            hit = accept.get((sid, row["status"], _norm(row["item"]).casefold(), _norm(row["app"]) or "-"))
            row["accepted"] = hit is not None and hit["used"] < hit["count"]
            if row["accepted"]:
                hit["used"] += 1
                row.update(reason=hit["reason"], owner=hit["owner"])
                accepted_n += 1
            else:
                open_rows += 1
        tot_matched += entry["matched"]
        tot_items += entry["design_items"]

    overall_known = not no_inventory
    overall = {"design_items": tot_items if overall_known else None,
               "matched": tot_matched if overall_known else None,
               "completeness_pct": _pct(tot_matched, tot_items) if overall_known else None}
    completeness = (f"{tot_matched}/{tot_items} design items matched ({_pct(tot_matched, tot_items)})"
                    + (" in the same-crop sections" if crop else "")
                    if overall_known else "completeness unknown (a side carries no inventory)")

    body = []
    body += [f"missing: section '{sid}' — build it (absent from the app)." for sid in missing]
    body += [f"empty:   section '{sid}' — seed it (present but no data-item in the app)." for sid in empty]
    for entry in sections:
        if entry.get("crop"):
            body.append(f"section '{entry['id']}': COULD_NOT_CHECK_CROP, not scored — {'; '.join(entry['crop'])}.")
            continue
        if entry["design_items"] is None:
            body.append(f"section '{entry['id']}': inventory unavailable (a .json side has none).")
            continue
        body.append(f"section '{entry['id']}': {entry['matched']}/{entry['design_items']} design items "
                    f"matched ({entry['completeness_pct']}).")
        for row in entry["rows"]:
            detail = (f"{row['design']} -> {row['app']}" if row["status"] in ("CHANGED", "MOVED")
                      else row["design"] or row["app"])
            tag = "ACCEPTED " + row["status"] if row["accepted"] else row["status"]
            suffix = f"  [{row['reason']}; {row['owner']}]" if row["accepted"] else ""
            body.append(f"  {tag:<24} {detail}{suffix}")
    info = []
    if extra:
        info.append("info: extra app section(s) beyond the design, kept as superset "
                    f"(not a failure): {', '.join(extra)}")
    stale = [f"{k[0]}/{k[1]}/{k[2]} ({row['used']} of {row['count']} used)"
             for k, row in accept.items() if len(k) == 4 and row["used"] < row["count"]]
    if stale:
        info.append(f"info: accept row(s) covering fewer differences than their count (stale): {', '.join(stale)}")
    stale = [f"{k[1]}/{k[2]}" for k, row in accept.items() if k[0] == "ignore" and len(k) == 3 and not row["used"]]
    if stale:
        info.append(f"info: ignore row(s) matching no design-side data-parity-ignore (stale): {', '.join(stale)}")
    n_ignored = len(d_ignored) + len(a_ignored)
    if n_ignored:
        info.append(_ignored_line(d_ignored, a_ignored))

    verdict = None
    if min_pairs is not None and tot_matched < min_pairs:
        code = COULD_NOT_CHECK
        report = [
            (f"COULD_NOT_CHECK: {tot_matched} design/app element pair(s) matched, below the "
             f"caller's --min-pairs {min_pairs} — the harness likely compared an empty or wrong "
             "page. Spot-check the pair list below; no verdict or work queue from this run is "
             "trusted."),
            *body, _BASIS, *info]
    elif crop:
        code = COULD_NOT_CHECK_CROP
        report = [
            (f"COULD_NOT_CHECK_CROP: {len(crop)} section(s) whose design and app captures are not the same "
             f"crop ({', '.join(crop)}) are UNVERIFIED and unscored — re-capture them. The other sections are "
             f"scored below: {len(missing)} missing + {len(empty)} empty; {open_rows} unaccepted inventory "
             f"difference(s); {completeness}."),
            _PRECONDITION, *body, _BASIS, *info]
    elif missing or empty or open_rows:
        code = MISMATCH
        report = [
            (f"MISMATCH: {len(missing)} missing + {len(empty)} empty of {len(design_ids)} "
             f"design section(s); {open_rows} unaccepted inventory difference(s); "
             f"{completeness}. This list is the work queue."),
            _PRECONDITION, *body, _BASIS, *info]
    elif no_inventory:
        code = COULD_NOT_CHECK
        report = [
            ("COULD_NOT_CHECK: sections match, but element inventory is unavailable for "
             f"section(s) {', '.join(no_inventory)} — export both rendered DOM snapshots "
             "as HTML; section presence alone cannot certify completeness."),
            *body, _BASIS, *info]
    elif not tot_matched:
        code = COULD_NOT_CHECK
        report = [
            ("COULD_NOT_CHECK: zero design/app element pairs matched — an empty comparison is "
             "never a MATCH; confirm both exports carry visible inventory."),
            *body, _BASIS, *info]
    elif d_ignored:
        code, verdict = MATCH, MATCH_WITH_IGNORED
        report = [
            (f"MATCH_WITH_IGNORED (ignored_n={len(d_ignored)}, accepted_n={accepted_n}): not a plain MATCH — "
             f"{len(d_ignored)} design element(s) are excluded by owner-authored ignore rows ({accept_source}); "
             f"every remaining design item is matched or accepted; element inventory {completeness}."),
            *body, _BASIS, *info]
    elif accepted_n:
        code, verdict = MATCH, MATCH_WITH_ACCEPTED
        report = [
            (f"MATCH_WITH_ACCEPTED (accepted_n={accepted_n}): not a plain MATCH — every design "
             "section is present and populated, and every inventory difference is a row of the "
             f"owner-authored accept file ({accept_source}); element inventory {completeness}."),
            *body, _BASIS, *info]
    else:
        code = MATCH
        report = [
            ("MATCH: every design section is present in the app, and every "
             "design-populated section is populated in the app; element inventory "
             f"{completeness}." + (f" {n_ignored} element(s) excluded by data-parity-ignore (listed below)."
                                   if n_ignored else "")),
            *body, _BASIS, *info]
    verdict = verdict or _VERDICT_NAMES[code]
    inv_unverified = code == COULD_NOT_CHECK
    style_res = diff_styles(design, app, style_min_pairs, accept) if style else None
    if style_res is not None:
        if code == MATCH and style_res["verdict"] not in ("STYLE_MATCH", "STYLE_MATCH_WITH_ACCEPTED"):
            code = STYLE_DIFF if style_res["verdict"] == "STYLE_DIFF" else STYLE_COULD_NOT_CHECK
            report = style_res["lines"] + report   # the headline names what set the exit
        else:
            report += style_res["lines"]
    visual = {k[1]: row for k, row in accept.items() if k[0] == "visual-reviewed" and len(k) == 2}
    passed = _section_verdicts(sections, set(missing) | set(empty), inv_unverified, style_res, visual,
                               {r["section"] for r in d_ignored if r["section"] is not None})
    if style_res is not None:
        report += [f"ACCEPTED visual-reviewed {sid}: no text-bearing data-cs; owner-reviewed  "
                   f"[{row['reason']}; {row['owner']}]" for sid, row in visual.items() if row["used"]]
        stale = [sid for sid, row in visual.items() if not row["used"]]
        if stale:
            report.append(f"info: visual-reviewed row(s) for a section that has style pairs or is "
                          f"otherwise unverified (stale): {', '.join(stale)}")
    report += _section_table(sections, passed, style_res)
    return {"exit_code": code, "verdict": verdict, "overall": overall, "pairs": tot_matched,
            "min_pairs": min_pairs, "style_min_pairs": style_min_pairs, "style": style_res, "accepted_n": accepted_n, "sections": sections,
            "sections_passed": passed, "sections_total": len(sections),
            "section_gaps": {"missing": missing, "empty": empty},
            "ignored": {"design": d_ignored, "app": a_ignored},
            "extra_sections": extra, "report": "\n".join(report)}


_BASELINE_FORMAT = "parity_differ-baseline/1"


def fingerprint(app_path: str | None, style: bool) -> dict | None:
    """The app side's inventory (+ style) fingerprint for `--baseline`; None without inventory.

    Per section, in order: `items` = every inventory key as a diff row prints
    it (containers with their row count), masked where the app section
    carries `data-sample`/`data-value` markers so sample values never read
    as drift; with `style`, `styles` = `[element, {property: normalized
    value}]` per text-bearing `data-cs` element in document order.
    `data-parity-ignore` subtrees are already excluded by the parser.
    """
    side = extract_side(app_path)
    if side is None or any(s["inventory"] is None for s in side):
        return None
    secs = []
    for s in side:
        mask = s["marked"]
        styles = [[f"{r['role']}:{_clean(r['text'], mask)}", {p: _style_norm(v) for p, v in r["props"].items()}]
                  for r in s["styles"] if style and _clean(r["text"], mask)]
        secs.append({"id": s["id"], "items": sorted(_show(i) for i in _prepare(s["inventory"], mask)),
                     "styles": styles})
    return {"format": _BASELINE_FORMAT, "style": style, "sections": secs}


def _load_baseline(path: str) -> tuple[dict | None, str | None]:
    """Read and shape-check a `--baseline` file; `(data, None)` or `(None, reason)`."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        ok = (data["format"] == _BASELINE_FORMAT and isinstance(data["style"], bool)
              and all(isinstance(s["id"], str) and all(isinstance(i, str) for i in s["items"])
                      and all(isinstance(el, str) and isinstance(props, dict) for el, props in s["styles"])
                      for s in data["sections"]))
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
        return None, f"unreadable or malformed ({type(exc).__name__})"
    return (data, None) if ok else (None, f"not a {_BASELINE_FORMAT} file")


def diff_baseline(base: dict, cur: dict) -> tuple[list[dict], list[str]]:
    """New deltas of a current fingerprint vs a baseline one: `(rows, new_section_ids)`.

    Pure. Rows are `{"status", "section", "detail"}`: REMOVED (a baseline
    section or item gone; items compare case-folded as a multiset), ADDED (an
    item not in the baseline, inside a baseline section), STYLE_CHANGED (the
    same element — role + text, duplicates in order — with a different
    normalized value). A section new since the baseline is returned apart
    (info, like an extra app section in the design comparison).
    """
    cur_map = {s["id"]: s for s in cur["sections"]}
    rows = []
    for b in base["sections"]:
        sid, c = b["id"], cur_map.get(b["id"])
        if c is None:
            rows.append({"status": "REMOVED", "section": sid, "detail": "(whole section)"})
            continue
        shown = {i.casefold(): i for i in b["items"] + c["items"]}
        bi, ci = Counter(i.casefold() for i in b["items"]), Counter(i.casefold() for i in c["items"])
        rows += [{"status": "REMOVED", "section": sid, "detail": shown[k]} for k in (bi - ci).elements()]
        rows += [{"status": "ADDED", "section": sid, "detail": shown[k]} for k in (ci - bi).elements()]
        pool: dict = {}
        for el, props in c["styles"]:
            pool.setdefault(el.casefold(), []).append(props)
        for el, props in b["styles"]:
            hits = pool.get(el.casefold())
            now = hits.pop(0) if hits else None
            rows += [{"status": "STYLE_CHANGED", "section": sid, "detail": f"{el} {p}: {v} -> {now.get(p)}"}
                     for p, v in props.items() if now is not None and now.get(p) != v]
    base_ids = {b["id"] for b in base["sections"]}
    return rows, [s["id"] for s in cur["sections"] if s["id"] not in base_ids]


def _delta_lines(rows: list[dict]) -> list[str]:
    """One indented report line per baseline delta row."""
    return [f"  {r['status']:<14} section '{r['section']}' {r['detail']}" for r in rows]


def apply_baseline(result: dict, app_path: str, path: str, style: bool, write: bool,
                   accept_regression: bool = False) -> dict:
    """Write or check a `--baseline` regression net on `compare`'s result; return it.

    Write (`write`): only a passing run (exit 0) is recorded — a failing run
    leaves the file untouched with a `baseline not written` line. Over an
    existing file its deltas vs this run are printed first; when there are
    any (or the old file is unreadable or has another `--style`) the file is
    overwritten only with `accept_regression`, else it stays as is and the
    exit is REGRESSION (8). The write is a side effect; OSError propagates.
    Check: COULD_NOT_CHECK / CANNOT_COMPARE stand unchecked; an unreadable,
    malformed, or other-`--style` baseline is COULD_NOT_CHECK; any new delta
    (`diff_baseline`) is REGRESSION (8) and the report lists ONLY those
    deltas plus a one-line design-comparison verdict — except under
    COULD_NOT_CHECK_CROP, which keeps its exit and appends the deltas; no
    delta keeps the comparison's own exit and appends `baseline: 0 new delta(s)`.
    """
    code = result["exit_code"]
    result["baseline"] = {"path": path, "written": False, "regressions": []}
    if write:
        if code != MATCH:
            result["report"] += (f"\nbaseline not written: the run did not pass (exit {code}); a baseline "
                                 "records a passing run only.")
            return result
        fp = fingerprint(app_path, style)
        lines, gate = [], None
        if os.path.exists(path):
            old, err = _load_baseline(path)
            if old is not None and old["style"] != style:
                err = f"recorded with style={old['style']}, this run style={style}"
            if err is not None:
                gate = f"the existing file is {err}"
            else:
                rows, _ = diff_baseline(old, fp)
                result["baseline"]["regressions"] = rows
                lines = [f"baseline: {len(rows)} delta(s) vs the existing {path}:", *_delta_lines(rows)] if rows else []
                gate = f"{len(rows)} new delta(s) vs the existing baseline (listed)" if rows else None
        if gate is not None and not accept_regression:
            result.update(exit_code=REGRESSION, verdict="REGRESSION")
            result["report"] += "\n" + "\n".join([
                *lines, (f"baseline not overwritten: {gate}; re-recording would hide them — pass "
                         "--accept-regression to record this run as the new baseline.")])
            return result
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(fp, fh, indent=1, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        result["baseline"]["written"] = True
        result["report"] += "\n" + "\n".join([
            *lines, *([f"accepted by --accept-regression: {gate}."] if gate else []),
            (f"baseline written: {path} ({len(fp['sections'])} section(s), "
             f"{sum(len(s['items']) for s in fp['sections'])} item(s), "
             f"{sum(len(s['styles']) for s in fp['sections'])} style element(s)).")])
        return result
    if code in (COULD_NOT_CHECK, CANNOT_COMPARE):
        result["report"] += "\nbaseline: not checked (the comparison itself could not run)."
        return result
    base, err = _load_baseline(path)
    cur = fingerprint(app_path, style)
    if base is not None and base["style"] != style:
        err = f"recorded with style={base['style']}, this run style={style}; re-run alike or re-record it"
    elif base is not None and cur is None:
        err = "the app side carries no inventory"
    if err is not None:
        result.update(exit_code=COULD_NOT_CHECK, verdict="COULD_NOT_CHECK")
        result["report"] = (f"COULD_NOT_CHECK: baseline {path}: {err} — the regression net cannot be "
                            "checked.\n" + result["report"])
        return result
    rows, new_ids = diff_baseline(base, cur)
    result["baseline"]["regressions"] = rows
    info = ([f"info: section(s) new since the baseline (not a regression): {', '.join(new_ids)}"]
            if new_ids else [])
    if not rows or code == COULD_NOT_CHECK_CROP:
        result["report"] += "\n" + "\n".join([f"baseline: {len(rows)} new delta(s) vs {path}.",
                                              *_delta_lines(rows), *info])
        return result
    ign = result.get("ignored") or {}
    was = result["verdict"] if code == MATCH else _VERDICT_NAMES[code]
    result.update(exit_code=REGRESSION, verdict="REGRESSION")
    result["report"] = "\n".join([
        (f"REGRESSION: {len(rows)} new delta(s) vs baseline {path} (recorded from a passing run) — "
         "something that passed before changed; only these new deltas are listed."),
        *_delta_lines(rows), *info,
        f"design comparison: {was} (exit {code}); rerun without --baseline for its full list.",
        *([_ignored_line(ign.get("design", []), ign.get("app", []))] if ign.get("design") or ign.get("app") else [])])
    return result


def _ignored_label(r: dict) -> str:
    """`section 'x' id` or `(outside sections) id` for one ignored root."""
    return (f"section '{r['section']}'" if r["section"] is not None else "(outside sections)") + f" {r['id']}"


def _ignored_line(d_ignored: list[dict], a_ignored: list[dict]) -> str:
    """One report line listing every `data-parity-ignore` root per side (count + ids)."""
    def side(label: str, rows: list[dict]) -> str:
        """`label: section 'x' id, (outside sections) id` or `label: none`."""
        return f"{label}: {', '.join(_ignored_label(r) for r in rows) if rows else 'none'}"
    return (f"ignored: {len(d_ignored) + len(a_ignored)} element(s) excluded by data-parity-ignore "
            f"from inventory and style — {side('design', d_ignored)}; {side('app', a_ignored)}.")


def _fold_moves(sections: list[dict]) -> None:
    """Fold a heading MISSING_IN_APP in one section + the same heading EXTRA_IN_APP in another into MOVED.

    Side effect on the entries' `rows`: the MISSING row becomes `{"status":
    "MOVED", "item", "design": key, "app": "section '<t>'"}` in the design's
    section and the matching EXTRA row in section t is removed. Headings
    only (case-folded key); a MOVED row is an open difference like any other.
    """
    for e in sections:
        for row in e["rows"]:
            if row["status"] != "MISSING_IN_APP" or not row["item"].startswith("heading:"):
                continue
            hit = next(((t, x) for t in sections if t is not e for x in t["rows"]
                        if x["status"] == "EXTRA_IN_APP" and (x["app"] or "").casefold() == row["item"].casefold()),
                       None)
            if hit is not None:
                hit[0]["rows"].remove(hit[1])
                row.update(status="MOVED", app=f"section '{hit[0]['id']}'")


def crop_problems(design: list[dict], app: list[dict]) -> dict:
    """Same-crop guard, design as the reference: `{section id: [problem, ...]}` for the app crops.

    Pure. Anchors are only the visible texts of `data-anchor` elements
    (whitespace-normalized, case-folded); a plain heading is never an
    anchor. Per section present on both sides with inventory: (1) when the
    design section has anchors, the app section's item labels or anchors
    must include at least one; (2) the app section may not carry a
    `data-anchor` whose text the design anchors only in a different
    section (a page header or KPI card leaked into the crop). The design
    side is never checked against the app. Empty dict = every crop is the
    same; only the listed sections are unscored.
    """
    def anchors(sec: dict) -> dict:
        """Case-folded data-anchor text -> printable text for one section."""
        return {_clean(t, False).casefold(): _clean(t, False) for t in sec["anchors"] if _clean(t, False)}

    d_anc = {s["id"]: anchors(s) for s in design}
    app_map = {s["id"]: s for s in app}
    out: dict = {}
    for sec in design:
        sid, a_sec = sec["id"], app_map.get(sec["id"])
        if a_sec is None or sec["inventory"] is None or a_sec["inventory"] is None:
            continue
        own, a_anc = d_anc[sid], anchors(a_sec)
        seen = {_clean(i["label"], False).casefold() for i in a_sec["inventory"]} | set(a_anc)
        if own and not set(own) & seen:
            out.setdefault(sid, []).append(
                f"app crop of section '{sid}' shares none of its design anchors ({', '.join(own.values())})")
        for cf, shown in a_anc.items():
            other = None if cf in own else next((t for t, anc in d_anc.items() if t != sid and cf in anc), None)
            if other is not None:
                out.setdefault(sid, []).append(
                    f"app crop of section '{sid}' holds anchor '{shown}' of neighbouring section '{other}'")
    return out


def _section_verdicts(sections: list[dict], gaps: set, inv_unverified: bool, style_res: dict | None,
                      visual: dict | None = None, ignored: set | None = None) -> int:
    """Set each section entry's `inventory`, `style`, and `verdict`; return the PASS count.

    A section entry carrying `crop` (same-crop guard) is UNVERIFIED; a
    passing section id in `ignored` (holds an owner-ignored design element)
    reads PASS_WITH_IGNORED, never a plain PASS, and still counts as passed.

    PASS iff the section is present (and populated where the design is),
    every inventory row is matched or owner-accepted, and — with `--style` —
    its style pairs exist and every style row is matched or accepted. FAIL on
    a gap, an open inventory row, or an open style row; UNVERIFIED when the
    inventory or style could not be checked (never counted as a pass). A
    section with no style pair on an otherwise checkable page whose id has an
    owner `visual-reviewed` accept entry in `visual` reads `visual-reviewed`
    instead of UNVERIFIED; that entry's `used` is counted (side effect).
    """
    visual = visual or {}
    rows = style_res["rows"] if style_res else []
    for e in sections:
        n_open = sum(not r["accepted"] for r in e["rows"])
        n_acc = len(e["rows"]) - n_open
        e["inventory"] = ("n/a" if e["design_items"] is None else e["state"] if e["id"] in gaps
                          else f"{n_open} open" if n_open else f"ACCEPTED({n_acc})" if n_acc else "MATCH")
        s_open = sum(r["section"] == e["id"] and not r["accepted"] and not r["tolerated"] for r in rows)
        s_acc = sum(r["section"] == e["id"] and r["accepted"] for r in rows)
        s_tol = sum(r["section"] == e["id"] and r["tolerated"] for r in rows)
        s_unver = style_res is not None and (style_res["verdict"] == "STYLE_COULD_NOT_CHECK"
                                             or not style_res["section_pairs"].get(e["id"]))
        seen = s_unver and style_res["verdict"] != "STYLE_COULD_NOT_CHECK" and e["id"] in visual
        if seen:
            visual[e["id"]]["used"] += 1
            s_unver = False
        e["style"] = ("-" if style_res is None else f"{s_open} open" if s_open else "no pairs" if s_unver
                      else "visual-reviewed" if seen else f"ok +{s_acc} acc +{s_tol} tol" if s_acc and s_tol
                      else f"ok +{s_acc} accepted" if s_acc else f"ok +{s_tol} tolerated" if s_tol else "ok")
        e["verdict"] = ("FAIL" if e["inventory"] not in ("MATCH", "n/a") and not e["inventory"].startswith("ACC")
                        else "UNVERIFIED" if inv_unverified or e["inventory"] == "n/a"
                        else "FAIL" if s_open else "UNVERIFIED" if s_unver else "PASS")
        if e.get("crop"):
            e["inventory"], e["verdict"] = "crop", "UNVERIFIED"
        elif e["verdict"] == "PASS" and e["id"] in (ignored or ()):
            e["verdict"] = "PASS_WITH_IGNORED"   # an owner ignore row removed a design element here
    return sum(e["verdict"] in ("PASS", "PASS_WITH_IGNORED") for e in sections)


def _section_table(sections: list[dict], passed: int, style_res: dict | None) -> list[str]:
    """The per-section progress table: `sections passed k/n` plus one row per section.

    Without `--style` the table is labelled inventory-only and has no style
    column, so an inventory-only PASS never reads as a styling pass.
    """
    if style_res is None:
        out = [(f"sections passed {passed}/{len(sections)} (inventory only) — PASS = inventory MATCH "
               "or MATCH_WITH_ACCEPTED:"), f"  {'section':<24} {'inventory':<14} verdict"]
        return out + [f"  {e['id'][:24]:<24} {e['inventory']:<14} {e['verdict']}" for e in sections]
    out = [(f"sections passed {passed}/{len(sections)} — PASS = inventory MATCH or "
           "MATCH_WITH_ACCEPTED and no un-accepted style difference:"),
           f"  {'section':<24} {'inventory':<14} {'style':<18} verdict"]
    return out + [f"  {e['id'][:24]:<24} {e['inventory']:<14} {e['style']:<18} {e['verdict']}"
                  for e in sections]


def _token_differ():
    """Import the sibling `token_differ.py` (same scripts dir); None when absent or broken."""
    path = Path(__file__).resolve().with_name("token_differ.py")
    try:
        spec = importlib.util.spec_from_file_location("token_differ", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:   # noqa: BLE001 — absent or broken sibling: the caller fails closed
        return None


def run_workflow(design_path: str | None, app_path: str | None, design_tokens: str | None,
                 app_tokens: str | None, token_map: str | None = None, accept_path: str | None = None,
                 accept_rev: str | None = None, use_focus_gate: bool | None = None,
                 min_pairs: int | None = None, style_min_pairs: int | None = None,
                 token_min_pairs: int | None = None) -> dict:
    """Foundation-first parity: tokens -> primitives -> sections; return `compare`'s dict + `workflow`.

    Stage 1 runs `token_differ.compare` on the token exports; stage 2 is the
    open FOUNDATION properties and PRIMITIVE (role, property) rows of
    `diff_styles` (style always on); stage 3 is the per-section table. Exit:
    COULD_NOT_CHECK when the tokens cannot be compared (or token_differ.py
    is absent) — every section verdict then reads UNVERIFIED and passed is
    0; `compare`'s COULD_NOT_CHECK / CANNOT_COMPARE stand; otherwise
    BLOCKED_BY_FOUNDATION while tokens mismatch or any foundation/primitive
    row is un-accepted — every section verdict then reads
    BLOCKED_BY_FOUNDATION (a withheld verdict is kept as `own_verdict`).
    With no usable style pair stage 2 reads COULD_NOT_CHECK, never clean. A
    would-be MATCH with an UNVERIFIED section becomes STYLE_COULD_NOT_CHECK.
    """
    td = _token_differ()
    t_code, t_report = COULD_NOT_CHECK, "token_differ.py not found beside parity_differ.py"
    if td is not None:
        t_code, _, t_report = td.compare(design_tokens, app_tokens, token_map, min_pairs=token_min_pairs)
    t_name = "MATCH" if td and t_code == td.MATCH else "MISMATCH" if td and t_code == td.MISMATCH else "COULD_NOT_CHECK"
    res = compare(design_path, app_path, accept_path, accept_rev, use_focus_gate, min_pairs,
                  style=True, style_min_pairs=style_min_pairs)
    st = res.get("style") or {"verdict": "STYLE_COULD_NOT_CHECK", "foundation": [], "primitives": []}
    prim_cnc = st["verdict"] == "STYLE_COULD_NOT_CHECK"   # no usable style pair: stage 2 checked nothing
    prims = [f"PRIMITIVE {p['role']} {p['property']}: differs on {p['pairs']}/{p['of']} {p['role']} pair(s) "
             f"in {p['sections']} section(s) (most common: {p['common'][0]} -> {p['common'][1]})"
             for p in st["primitives"]]
    found = [f"FOUNDATION {p}" for p in st["foundation"]] + prims
    blocked = t_name == "MISMATCH" or bool(found)
    stages = [f"workflow stage 1 tokens: {t_name} (token_differ.py)",
              *(f"  {line}" for line in t_report.splitlines() if not line.startswith("MATCH ")),
              "workflow stage 2 primitives: " + ("; ".join(found) if found else
                                                 "COULD_NOT_CHECK (no usable style pair; never assumed clean)"
                                                 if prim_cnc else "clean (no open FOUNDATION or PRIMITIVE row)")]
    code = res["exit_code"]
    if t_name == "COULD_NOT_CHECK":
        code = COULD_NOT_CHECK
        head = ("COULD_NOT_CHECK: the token stage could not compare — export both sides' design tokens "
                "(--design-tokens / --app-tokens); the foundation is never assumed clean. "
                "Section verdicts are withheld.")
        for e in res.get("sections", []):
            e["own_verdict"], e["verdict"] = e["verdict"], "UNVERIFIED"
    elif code in (COULD_NOT_CHECK, CANNOT_COMPARE, COULD_NOT_CHECK_CROP):
        head = f"workflow: stopped at {_VERDICT_NAMES[code]} (see below)."
    elif blocked:
        code = BLOCKED_BY_FOUNDATION
        head = ("BLOCKED_BY_FOUNDATION: fix the foundation once before any per-section work — "
                f"tokens {t_name}; {len(found)} open foundation/primitive row(s). Section verdicts are withheld.")
        for e in res.get("sections", []):
            e["own_verdict"], e["verdict"] = e["verdict"], "BLOCKED_BY_FOUNDATION"
    elif prim_cnc:
        code = STYLE_COULD_NOT_CHECK if code == MATCH else code
        head = ("workflow: stage 2 primitives COULD_NOT_CHECK — export data-cs on both sides' text "
                f"elements; section stage exit {code}.")
    elif code == MATCH and res.get("sections_passed") != res.get("sections_total"):
        code = STYLE_COULD_NOT_CHECK
        head = ("STYLE_COULD_NOT_CHECK: a section has no style pair — export data-cs on its text "
                "elements; an unverified section is never ready.")
    else:
        head = f"workflow: foundation clean; section stage exit {code}."
    if "sections" in res:
        withheld = ("BLOCKED_BY_FOUNDATION" if code == BLOCKED_BY_FOUNDATION
                    else "UNVERIFIED: token stage could not compare" if t_name == "COULD_NOT_CHECK" else "")
        passed = 0 if withheld else res["sections_passed"]
        stages.append(f"workflow stage 3 sections: passed {passed}/{res['sections_total']}"
                      + (f" ({withheld})" if withheld else ""))
        table = _section_table(res["sections"], passed, st)
        lines = res["report"].splitlines()
        res["report"] = "\n".join(lines[:-len(table)] + table)
        res["sections_passed"] = passed
    res.update(exit_code=code, workflow={"tokens": t_name, "foundation": st["foundation"],
                                         "primitives": st["primitives"], "blocked": code == BLOCKED_BY_FOUNDATION})
    res["report"] = "\n".join([head, *stages, res["report"]])
    return res


_SHOT_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
# Leads every report srcdoc: blocks every network fetch (images, fonts, @import, frames).
_SRCDOC_CSP = ('<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
               'img-src data:; style-src \'unsafe-inline\'; font-src data:">')


def _shot(folder: str | None, sid: str) -> str | None:
    """`<folder>/<sid>.<image ext>` as a data URI, or None (no folder, unsafe id, or no file)."""
    if not folder or sid != os.path.basename(sid) or sid.startswith("."):
        return None
    for ext in _SHOT_EXT:
        path = os.path.join(folder, sid + ext)
        if os.path.isfile(path):
            mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
            with open(path, "rb") as fh:
                return f"data:{mime};base64,{base64.b64encode(fh.read()).decode('ascii')}"
    return None


def write_report(result: dict, out: str, design_path: str | None, app_path: str | None,
                 design_shots: str | None = None, app_shots: str | None = None) -> None:
    """Write a self-contained HTML per-section evidence report to `out`.

    Per section: its verdict, design|app side by side — the screenshot
    `<shots dir>/<section id>.<png|jpg|jpeg|webp|gif|svg>` embedded as a data
    URI when given, else a sandboxed `srcdoc` iframe of that render with
    every other section hidden — then its inventory rows, style rows, and
    accepted rows. Every value is HTML-escaped; no script, network, or
    external asset is emitted, and each srcdoc opens with a `default-src
    'none'` CSP meta (`_SRCDOC_CSP`) so an export's own absolute or relative
    image, font, and @import URLs never fetch.
    Side effect: writes `out`; raises OSError when it cannot.
    """
    def esc(value) -> str:
        """HTML-escape one value (quotes included)."""
        return html.escape(str(value), quote=True)

    def doc(path: str | None) -> str | None:
        """The render's text for srcdoc, or None when it is not a readable HTML file."""
        if not path or path.lower().endswith(".json") or not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()

    def pane(label: str, shots: str | None, raw: str | None, sid: str) -> str:
        """One side of the side-by-side: a screenshot, an isolated iframe, or a note."""
        uri = _shot(shots, sid)
        if uri:
            body = f'<img alt="{esc(label)} {esc(sid)}" src="{uri}">'
        elif raw is not None:
            # CSS string: every char outside [A-Za-z0-9_-] as a hex escape (quotes, `<`, non-ASCII).
            sel = '"' + "".join(c if re.fullmatch(r"[A-Za-z0-9_-]", c) else f"\\{ord(c):x} " for c in sid) + '"'
            hide = (f"<style>[data-section]:not([data-section={sel}]):not(:has([data-section={sel}]))"
                    "{display:none!important}</style>")
            body = f'<iframe sandbox="" srcdoc="{esc(_SRCDOC_CSP + raw + hide)}"></iframe>'
        else:
            body = "<p>no render or screenshot available</p>"
        return f"<div><h4>{esc(label)}</h4>{body}</div>"

    def table(head: tuple, rows: list[tuple]) -> str:
        """An escaped HTML table, or "none" when there are no rows."""
        if not rows:
            return "<p>none</p>"
        cells = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
        return "<table><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + f"</tr>{cells}</table>"

    d_raw, a_raw = doc(design_path), doc(app_path)
    style_rows = (result.get("style") or {}).get("rows", [])
    parts = [f"<h1>Parity report (exit {esc(result['exit_code'])})</h1>",
             f"<p><strong>{esc(result['report'].splitlines()[0])}</strong></p>"]
    if "sections_total" in result:
        parts.append(f"<p>sections passed {esc(result['sections_passed'])}/{esc(result['sections_total'])}</p>")
    for e in result.get("sections", []):
        sid = e["id"]
        inv = [(r["status"], r["design"] or "-", r["app"] or "-") for r in e["rows"] if not r["accepted"]]
        sty = [(r["element"], r["property"], r["design"], r["app"], "FOUNDATION" if r["foundation"] else "STYLE_DIFF")
               for r in style_rows if r["section"] == sid and not r["accepted"] and not r["tolerated"]]
        acc = [(r["status"], r["design"] or "-", r["app"] or "-", r["reason"], r["owner"])
               for r in e["rows"] if r["accepted"]]
        acc += [(f"style {r['property']}", r["design"], r["app"], r["reason"], r["owner"])
                for r in style_rows if r["section"] == sid and (r["accepted"] or r["tolerated"])]
        parts.append(
            f'<section><h2>{esc(sid)} — {esc(e.get("verdict", "?"))}</h2>'
            f'<div class="sbs">{pane("design", design_shots, d_raw, sid)}{pane("app", app_shots, a_raw, sid)}</div>'
            f"<h3>Inventory differences</h3>{table(('status', 'design', 'app'), inv)}"
            f"<h3>Style differences</h3>{table(('element', 'property', 'design', 'app', 'kind'), sty)}"
            f"<h3>Accepted (owner)</h3>{table(('row', 'design', 'app', 'reason', 'owner'), acc)}</section>")
    parts.append(f"<h2>Full report</h2><pre>{esc(result['report'])}</pre>")
    css = ("body{font:14px system-ui,sans-serif;margin:24px}.sbs{display:grid;grid-template-columns:1fr 1fr;"
           "gap:12px}iframe,img{width:100%;min-height:360px;border:1px solid #999}table{border-collapse:collapse}"
           "td,th{border:1px solid #ccc;padding:2px 6px;text-align:left}pre{white-space:pre-wrap}")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Parity report</title>'
                 f"<style>{css}</style></head><body>{''.join(parts)}</body></html>\n")


def diff_sides(design_path: str | None, app_path: str | None, accept_path: str | None = None,
               accept_rev: str | None = None) -> tuple[int, str]:
    """Compare a design render against an app render; return (exit_code, report).

    Thin wrapper over `compare`; same fail-closed contract and exit codes.
    """
    result = compare(design_path, app_path, accept_path, accept_rev)
    return result["exit_code"], result["report"]


def _selftest() -> int:
    """Run the committed fixtures and assert the exact verdict per case.

    This is the tool's own proof that it fires on real input, not just that
    it parses: each case pins the exit code and required/forbidden report
    substrings, and the inventory cases pin the EXACT row set, so a future
    edit that quietly turns a fail-closed branch into a pass, drops an
    inventory kind, or lets size leak into the verdict breaks this loudly.
    The accept-file cases commit into a throwaway local git repo (no
    network) with global/system git config masked, so they are hermetic.
    """
    fixtures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "parity")

    def fx(name: str) -> str:
        """Absolute path of one committed parity fixture."""
        return os.path.join(fixtures_dir, name)

    design, app_full = fx("design.html"), fx("app_full.html")
    nonexistent = fx("does-not-exist.html")
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

    def rows_of(result: dict) -> set[tuple[str, str, str]]:
        """Every inventory row as (section, status, item)."""
        return {(s["id"], r["status"], r["item"]) for s in result.get("sections", [])
                for r in s["rows"]}

    code, report = diff_sides(design, app_full)
    check("match", code, report, MATCH, must_have=("MATCH", "100.0%"))

    code, report = diff_sides(design, fx("app_partial.html"))
    check("mismatch", code, report, MISMATCH,
          must_have=("MISMATCH", "beta", "gamma", "delta", "same auth",
                     "default-surface check"),
          must_not=("aligned",))

    code, report = diff_sides(design, fx("app_unseeded.html"))
    check("unseeded", code, report, CANNOT_COMPARE,
          must_have=("seed", "do not condense"),
          must_not=("aligned", "MISMATCH"))

    code, report = diff_sides(nonexistent, app_full)
    check("refuse-design-absent", code, report, COULD_NOT_CHECK,
          must_not=("aligned", "MATCH"))

    code, report = diff_sides(design, nonexistent)
    check("refuse-app-absent", code, report, COULD_NOT_CHECK,
          must_not=("aligned", "MATCH"))

    # Every section non-empty, yet 3 buttons and 1 heading are gone: section
    # presence would pass; the inventory must list exactly those four.
    inv_design = fx("inv_design.html")
    res = compare(inv_design, fx("inv_app_missing.html"))
    want = {("overview", "MISSING_IN_APP", "control:button:Share"),
            ("holdings", "MISSING_IN_APP", "control:button:Add holding"),
            ("activity", "MISSING_IN_APP", "control:button:Load more"),
            ("activity", "MISSING_IN_APP", "heading:h2:Recent activity")}
    check("inventory-missing", res["exit_code"], res["report"], MISMATCH,
          must_have=("4 unaccepted", "size, height, width", "(<100%)"), must_not=("aligned",))
    if rows_of(res) != want:
        failures.append(f"inventory-missing: rows {sorted(rows_of(res))}, want {sorted(want)}")
    if res["overall"]["design_items"] - res["overall"]["matched"] != 4:
        failures.append(f"inventory-missing: overall {res['overall']}, want exactly 4 unmatched")

    # Taller/wider app (sizes, spacers, wrappers, other sample values marked on
    # both sides) with an equal inventory: size must never move the verdict.
    res = compare(inv_design, fx("inv_app_taller.html"))
    check("inventory-taller", res["exit_code"], res["report"], MATCH, must_have=("100.0%",))

    res = compare(inv_design, fx("inv_app_changed.html"))
    want = {("overview", "CHANGED", "text:Welcome back, Jane Smith")}
    check("inventory-changed", res["exit_code"], res["report"], MISMATCH,
          must_have=("good morning, jane smith",))
    if rows_of(res) != want:
        failures.append(f"inventory-changed: rows {sorted(rows_of(res))}, want {sorted(want)}")

    # Floored percentage: 1999/2000 is 99.95% and must never round up to 100.
    for (m, t), want_pct in {(1999, 2000): "99.9% (<100%)", (9999, 10000): "99.9% (<100%)",
                             (1, 3): "33.3% (<100%)", (5, 5): "100.0%", (0, 0): "n/a"}.items():
        if _pct(m, t) != want_pct:
            failures.append(f"pct-floor: _pct({m}, {t}) = {_pct(m, t)!r}, want {want_pct!r}")

    with tempfile.TemporaryDirectory() as tmp:
        def write(name: str, text: str) -> str:
            """Write one throwaway fixture into the temp dir; return its path."""
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            return path

        def pair(label: str, d_body: str, a_body: str, want_code: int,
                 want_rows: set | None = None) -> dict:
            """Diff one inline design/app section pair; pin exit code and exact row set."""
            wrap = '<section data-section="s"><p data-item>x</p>{}</section>'
            r = compare(write(f"{label}-d.html", wrap.format(d_body)),
                        write(f"{label}-a.html", wrap.format(a_body)))
            check(label, r["exit_code"], r["report"], want_code)
            if want_rows is not None and rows_of(r) != {("s", st, it) for st, it in want_rows}:
                failures.append(f"{label}: rows {sorted(rows_of(r))}, want {sorted(want_rows)}")
            return r

        one = '<section data-section="s"><p data-item>Balance <span data-value>$40</span></p></section>'
        other = '<section data-section="s"><p data-item>Balance $75</p></section>'
        code, report = diff_sides(write("d.html", one), write("a.html", other))
        check("mask-one-sided", code, report, MISMATCH, must_have=("CHANGED",))

        icon = ('<section data-section="s"><p data-item>x</p><button>'
                '<svg><title>Close dialog</title></svg></button></section>')
        side = extract_side(write("icon.html", icon))
        labels = [i["label"] for i in side[0]["inventory"] if i["kind"] == "control"] if side else []
        if labels != ["Close dialog"]:
            failures.append(f"icon-button-label: {labels}, want ['Close dialog']")

        js = write("side.json", '[{"id": "s", "populated": true}]')
        code, report = diff_sides(js, js)
        check("json-no-inventory", code, report, COULD_NOT_CHECK, must_not=("MATCH:",))

        # Public one-side inventory: keys exactly as diff rows print them; a
        # .json side has none; a hiding class is surfaced, not guessed.
        keys = inventory_keys(write("keys.html", '<section data-section="s"><h2>Totals</h2>'
                                    '<button aria-label="Save changes">Save</button>'
                                    '<button class="d-none">Ghost</button></section>'))
        want_keys = ["heading:h2:Totals", "control:button:Save [aria-label: Save changes]",
                     "control:button:Ghost"]
        if not keys or len(keys) != 1 or keys[0]["id"] != "s" or keys[0]["populated"] \
                or keys[0]["items"] != want_keys or not keys[0]["unresolved"]:
            failures.append(f"inventory-keys: {keys}")
        if inventory_keys(js) != [{"id": "s", "populated": True, "unresolved": [], "items": None}] \
                or inventory_keys(nonexistent) is not None:
            failures.append("inventory-keys: .json side must carry items=None; an absent side None")

        # 1. Hidden: closed dialog/details bodies and opacity:0 are not inventoried
        # (open ones and opacity:0.5 are); a hiding class needs the export's marker.
        pair("hidden-dialog", "", "<dialog><button>Delete</button></dialog>", MATCH)
        pair("open-dialog", "", "<dialog open><button>Delete</button></dialog>", MISMATCH,
             {("EXTRA_IN_APP", "control:button:Delete")})
        pair("hidden-details", "<details><summary>More</summary></details>",
             "<details><summary>More</summary><p>Secret terms</p></details>", MATCH)
        pair("open-details", "<details open><summary>More</summary></details>",
             "<details open><summary>More</summary><p>Secret terms</p></details>", MISMATCH,
             {("EXTRA_IN_APP", "text:Secret terms")})
        pair("opacity-zero", "", '<button style="opacity: 0;">Ghost</button>', MATCH)
        pair("opacity-half", "", '<button style="opacity:0.5">Ghost</button>', MISMATCH,
             {("EXTRA_IN_APP", "control:button:Ghost")})
        r = pair("hiding-class-unmarked", "", '<button class="btn d-none">Ghost</button>', COULD_NOT_CHECK)
        check("hiding-class-unmarked", r["exit_code"], r["report"], COULD_NOT_CHECK,
              must_have=("data-visible", "d-none"), must_not=("MATCH:",))
        pair("hiding-class-marked-false", "", '<button class="d-none" data-visible="false">Ghost</button>', MATCH)
        pair("hiding-class-marked-true", "", '<button class="sr-only" data-visible="true">Ghost</button>',
             MISMATCH, {("EXTRA_IN_APP", "control:button:Ghost")})

        # 2. Label precedence: visible text is compared apart from the accessible
        # name; a matching aria-label cannot hide a visible-text change, and a
        # placeholder is never a label.
        pair("visible-text-vs-aria", '<button aria-label="Save changes">Save</button>',
             '<button aria-label="Save changes">Submit</button>', MISMATCH,
             {("CHANGED", "control:button:Save [aria-label: Save changes]")})
        pair("placeholder-not-label", '<label for="e">Email</label><input id="e">',
             '<input placeholder="Email">', MISMATCH,
             {("CHANGED", "control:textbox:Email")})
        pair("aria-heading", "<h2>Totals</h2>", '<h2 aria-label="Totals">Sums</h2>', MISMATCH,
             {("CHANGED", "heading:h2:Totals")})

        # 3. Coverage: media, icon fonts, select options, masked-slot counts, and
        # broken values in a masked slot.
        media = ('<canvas aria-label="Price chart">fallback</canvas><video title="Intro"></video>'
                 '<iframe title="Map"></iframe><object title="Report"></object>')
        pair("media", media, "", MISMATCH,
             {("MISSING_IN_APP", "media:canvas:Price chart"), ("MISSING_IN_APP", "media:video:Intro"),
              ("MISSING_IN_APP", "media:iframe:Map"), ("MISSING_IN_APP", "media:object:Report")})
        pair("icon-font", '<button><i class="icon icon-trash" aria-hidden="true"></i></button><i class="icon-star"></i>',
             '<button><i class="icon icon-pencil" aria-hidden="true"></i></button>', MISMATCH,
             {("CHANGED", "control:button:[no accessible name] [icon: icon icon-trash]"),
              ("MISSING_IN_APP", "icon:icon-star")})
        pair("select-options", '<label>Currency <select><option>USD</option><option>EUR</option></select></label>',
             '<label>Currency <select><option>USD</option></select></label>', MISMATCH,
             {("MISSING_IN_APP", "option:EUR")})
        pair("mask-count", "<p>Totals <span data-value>1</span> <span data-value>2</span> <span data-value>3</span></p>",
             "<p>Totals <span data-value>9</span></p>", MISMATCH)
        pair("mask-one-element", "<p>Totals <span data-value>$<b>40</b></span></p>",
             "<p>Totals <span data-sample>$75</span></p>", MATCH)
        pair("mask-broken-value", "<p>Balance <span data-value>$40</span></p>",
             "<p>Balance <span data-value>undefined</span></p>", MISMATCH)
        pair("mask-empty-slot", "<p>Balance <span data-value>$40</span></p>",
             "<p>Balance <span data-value></span></p>", MISMATCH)

        # 4. Accept file: committed, owner-authored, keyed by status + app value
        # with a count; the verdict is MATCH_WITH_ACCEPTED, never plain MATCH.
        _selftest_accept(tmp, write, check, failures, inv_design, fx)

        # 5. --min-pairs floor (#1112) and --style computed-style diff (#1108).
        _selftest_floor_style(write, check, failures, design, app_full)

    if failures:
        print("SELFTEST FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        "SELFTEST OK: match=0 mismatch=1 unseeded=4 refuse(design-absent)=3 "
        "refuse(app-absent)=3 inventory(missing)=1 inventory(taller)=0 "
        "inventory(changed)=1 pct(floor)=ok mask(one-sided)=1 icon-button-label=ok "
        "json(no-inventory)=3 hidden(dialog,details,opacity,class)=ok label(visible,placeholder)=ok "
        "coverage(media,icon,option,mask-count,broken)=ok accept(owner,count,pin,untrusted)=ok "
        "inventory-keys=ok min-pairs(floor,outranks-mismatch,zero-pairs)=ok "
        "style(foundation,opt-in,normalized,inventory-wins,malformed,empty-value,no-export,floor,"
        "floor-separate,needs-style)=ok foundation-breadth(one-section,two-pairs,default,style-floor)=ok "
        "style-accept(global,section,pin,rule,malformed)=ok sections(pass,fail,unverified,inventory-only)=ok "
        "workflow(tokens,foundation,primitive,accepted,local,unreadable,withheld,no-style-pairs,cli)=ok "
        "visual-reviewed(owner,agent,has-pairs,page-could-not-check)=ok report(shots,escape,accepted,csp,css-escape)=ok "
        "ignore(owner-row,agent,design-missing,app-unpaired,app-cannot-hide,section,style)=ok threshold(met,not-met,scoped,foundation,primitive,malformed,agent)=ok "
        "style-identity(counts,top,accepted-ignored,own-text)=ok lines(rows,heading,size-free,one-sided,invalid)=ok "
        "crop(app-leak-scoped,design-reference,plain-heading,moved-heading,no-anchor,shared-heading,workflow)=ok "
        "baseline(write,refuse,clean,removed,style,superset,design-change,masked,malformed,overwrite,path-guard,cli)=ok"
    )
    return 0


_ST_BASE = {"font-family": "Inter, sans-serif", "font-size": "14px", "font-weight": "400",
            "line-height": "20px", "letter-spacing": "0px", "color": "rgb(17, 24, 39)",
            "background-color": "rgba(0, 0, 0, 0)", "padding": "0px", "border-radius": "0px",
            "box-shadow": "none"}


def _st_page(over: dict | None = None, bold: tuple | None = None, attr: str | None = None,
             sids: tuple = ("overview", "holdings", "activity"), over_in: tuple | None = None,
             tags: tuple = ("h2", "button", "p")) -> str:
    """Self-test page: sections (default three) x (heading, button, text), each carrying data-cs.

    `over` applies to every section (or only those in `over_in`) and only to
    elements whose tag is in `tags`; `bold` makes one (section, tag) 600.
    """
    out = []
    for sid in sids:
        els = []
        here = over if over_in is None or sid in over_in else None
        for tag, text in (("h2", sid.title()), ("button", f"Open {sid}"), ("p", f"{sid} note")):
            props = {**_ST_BASE, **((here or {}) if tag in tags else {}),
                     **({"font-weight": "600"} if bold == (sid, tag) else {})}
            els.append(f"<{tag} data-cs='{attr if attr is not None else json.dumps(props)}'>{text}</{tag}>")
        out.append(f'<section data-section="{sid}"><div data-item>x</div>{"".join(els)}</section>')
    return "".join(out)


def _selftest_floor_style(write, check, failures: list, design: str, app_full: str) -> None:
    """`--min-pairs` floor and `--style` self-test cases (inline fixtures)."""
    res = compare(design, app_full)
    got = res.get("pairs") or 0
    r = compare(design, app_full, min_pairs=got + 1)
    check("floor-below", r["exit_code"], r["report"], COULD_NOT_CHECK,
          must_have=(f"--min-pairs {got + 1}", "wrong page"), must_not=("MATCH:",))
    r = compare(design, app_full, min_pairs=got)
    check("floor-at", r["exit_code"], r["report"], MATCH)
    # A wrong page with the same section ids: MISMATCH would queue a rebuild;
    # below the caller's floor it is COULD_NOT_CHECK instead.
    d = write("fl-d.html", '<section data-section="s"><p data-item>x</p><h2>Totals</h2>'
                           '<button>Save</button></section>')
    a = write("fl-a.html", '<section data-section="s"><p data-item>x</p><h2>Sign in</h2></section>')
    check("floor-no-flag-mismatch", *diff_sides(d, a), MISMATCH)
    r = compare(d, a, min_pairs=3)
    check("floor-outranks-mismatch", r["exit_code"], r["report"], COULD_NOT_CHECK,
          must_have=("1 design/app element pair(s)",), must_not=("MISMATCH",))
    empty = write("fl-empty.html", '<section data-section="s"></section>')
    check("zero-pairs-never-match", *diff_sides(empty, empty), COULD_NOT_CHECK,
          must_have=("zero design/app element pairs",), must_not=("MATCH:",))
    try:
        _min_pairs("0")
        failures.append("min-pairs-type: 0 accepted, want ArgumentTypeError")
    except argparse.ArgumentTypeError:
        pass

    base, page = _ST_BASE, _st_page
    sd = write("st-d.html", page())
    sa = write("st-a.html", page({"line-height": "24px"}, bold=("holdings", "button")))
    r = compare(sd, sa, style=True)
    st = r.get("style") or {}
    check("style-foundation", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("FOUNDATION line-height: differs on 9/9", "STYLE_DIFF font-weight (1 pair(s))",
                     "section 'holdings' button:Open holdings: 400 -> 600"))
    rows = sorted((x["property"], x["foundation"]) for x in st.get("rows", []))
    if (r.get("verdict") != "MATCH" or st.get("foundation") != ["line-height"]
            or rows != [("font-weight", False)] + [("line-height", True)] * 9
            or r["report"].count("20px -> 24px") != 1 or not r["report"].startswith("STYLE_DIFF:")):
        failures.append(f"style-foundation: verdict {r.get('verdict')} style {st.get('foundation')} rows {rows}")
    r = compare(sd, sa)
    check("style-opt-in", r["exit_code"], r["report"], MATCH, must_not=("FOUNDATION", "STYLE"))
    norm = write("st-n.html", page({"color": "rgb(17,24,39)", "font-family": '"Inter",SANS-SERIF'}))
    r = compare(sd, norm, style=True)
    check("style-normalized", r["exit_code"], r["report"], MATCH, must_have=("STYLE_MATCH", "style-identical 9/9 = 100.0%"))
    wrong = write("st-w.html", page({"line-height": "24px"}).replace("Open activity", "Launch activity"))
    r = compare(sd, wrong, style=True)
    check("style-inventory-wins", r["exit_code"], r["report"], MISMATCH, must_have=("FOUNDATION line-height",))
    r = compare(sd, write("st-bad.html", page(attr='{"color": "red"}')), style=True)
    check("style-malformed", r["exit_code"], r["report"], STYLE_COULD_NOT_CHECK, must_have=("malformed data-cs",))
    blank = page({"padding": ""})   # an unserialized shorthand on BOTH sides is not "equal"
    r = compare(write("st-bd.html", blank), write("st-ba.html", blank), style=True)
    check("style-empty-value", r["exit_code"], r["report"], STYLE_COULD_NOT_CHECK, must_have=("malformed data-cs",))
    r = compare(sd, write("st-none.html", re.sub(r" data-cs='[^']*'", "", page())), style=True)
    check("style-no-export", r["exit_code"], r["report"], STYLE_COULD_NOT_CHECK, must_have=("no text-matched",))
    # --style-min-pairs is the style floor; the inventory's --min-pairs never reaches style.
    r = compare(sd, norm, style=True, style_min_pairs=10)   # 12 inventory pairs, 9 style pairs
    check("style-floor", r["exit_code"], r["report"], STYLE_COULD_NOT_CHECK,
          must_have=("STYLE_COULD_NOT_CHECK:", "9 style pair(s), below the caller's --style-min-pairs 10"))
    r = compare(sd, norm, style=True, min_pairs=10)
    check("style-floor-separate", r["exit_code"], r["report"], MATCH,
          must_have=("STYLE_MATCH",), must_not=("COULD_NOT_CHECK",))
    r = compare(sd, sa, style=True, min_pairs=13)   # inventory floor still outranks style
    check("style-inventory-floor-wins", r["exit_code"], r["report"], COULD_NOT_CHECK,
          must_have=("--min-pairs 13",))
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            main(["--design", sd, "--app", sa, "--style-min-pairs", "3"])
        failures.append("style-min-pairs-needs-style: accepted without --style")
    except SystemExit as exc:
        if exc.code != USAGE_ERROR:
            failures.append(f"style-min-pairs-needs-style: exit {exc.code}, want {USAGE_ERROR}")
    # FOUNDATION needs breadth: >half of pairs AND >= 2 sections AND >= max(3, floor) pairs.
    one = page(sids=("overview",))
    r = compare(write("fd1-d.html", one), write("fd1-a.html", page({"line-height": "24px"}, sids=("overview",))),
                style=True)
    check("foundation-one-section", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("STYLE_DIFF line-height (3 pair(s))",), must_not=("FOUNDATION line-height",))
    def heads(over: dict | None = None) -> str:
        """Two sections, one data-cs heading each: two style pairs across two sections."""
        cs = json.dumps({**base, **(over or {})})
        return "".join(f"<section data-section=\"{s}\"><div data-item>x</div><h2 data-cs='{cs}'>{s}</h2></section>"
                       for s in ("left", "right"))
    r = compare(write("fd2-d.html", heads()), write("fd2-a.html", heads({"line-height": "24px"})), style=True)
    check("foundation-two-pairs", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("STYLE_DIFF line-height (2 pair(s))", "2 text-matched pair(s)"),
          must_not=("FOUNDATION line-height",))
    six = write("fd6-a.html", page({"line-height": "24px"}, over_in=("overview", "holdings")))
    r = compare(sd, six, style=True)
    check("foundation-at-default-floor", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("FOUNDATION line-height: differs on 6/9 pairs in 2 section(s)",))
    r = compare(sd, six, style=True, style_min_pairs=7)
    check("foundation-style-floor", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("STYLE_DIFF line-height (6 pair(s))",), must_not=("FOUNDATION line-height",))


def _selftest_accept(tmp: str, write, check, failures: list, inv_design: str, fx) -> None:
    """Accept-file self-test cases against a throwaway local git repo."""
    owner, agent = "owner@example.com", "lane-bot@example.com"
    repo = os.path.join(tmp, "repo")
    os.makedirs(repo)
    saved = {k: os.environ.get(k) for k in ("DCR_OWNER_EMAIL", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")}
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", DCR_OWNER_EMAIL=owner)
    try:
        def commit(email: str, rel: str, body: str, msg: str = "chore: accept") -> str:
            """Write `rel` in the repo and commit it as `email`; return its path."""
            path = os.path.join(repo, rel)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            _git(repo, ["add", rel])
            _git(repo, ["-c", f"user.email={email}", "-c", "user.name=Jane Smith", "-c",
                        "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", msg])
            return path

        _git(repo, ["init", "-q"])
        with open(fx("inv_accept.tsv"), encoding="utf-8") as fh:
            good = fh.read()
        changed = fx("inv_app_changed.html")
        fg_present = _focus_gate() is not None
        rev = None if fg_present else "HEAD"   # without focus_gate, --accept-rev is required

        acc = commit(owner, "accept.tsv", good)
        res = compare(inv_design, changed, acc, rev)
        check("accept-owner", res["exit_code"], res["report"], MATCH,
              must_have=("MATCH_WITH_ACCEPTED (accepted_n=1)", "ACCEPTED CHANGED",
                         "owner-commit" if fg_present else "owner-log"),
              must_not=("stale", "MATCH: every"))
        if res.get("verdict") != MATCH_WITH_ACCEPTED or res.get("accepted_n") != 1:
            failures.append(f"accept-owner: verdict {res.get('verdict')} accepted_n {res.get('accepted_n')}")

        r = compare(inv_design, changed, acc, None, use_focus_gate=False)
        check("accept-fallback-needs-rev", r["exit_code"], r["report"], COULD_NOT_CHECK,
              must_have=("--accept-rev",))
        r = compare(inv_design, changed, acc, "HEAD", use_focus_gate=False)
        check("accept-fallback-owner", r["exit_code"], r["report"], MATCH,
              must_have=("MATCH_WITH_ACCEPTED", "owner-log"))

        agent_file = commit(owner, "agent.tsv", good)
        commit(agent, "agent.tsv", good.replace("new onboarding tone", "tone"))
        for fg in (None, False):
            r = compare(inv_design, changed, agent_file, "HEAD", use_focus_gate=fg)
            check(f"accept-agent-authored(fg={fg})", r["exit_code"], r["report"], COULD_NOT_CHECK,
                  must_have=("not the owner",), must_not=("MATCH",))

        co = commit(owner, "co.tsv", good, "chore: accept\n\nCo-authored-by: Assistant <bot@example.com>")
        for fg in (None, False):
            r = compare(inv_design, changed, co, "HEAD", use_focus_gate=fg)
            check(f"accept-coauthored(fg={fg})", r["exit_code"], r["report"], COULD_NOT_CHECK,
                  must_have=("Co-authored-by",))

        r = compare(inv_design, changed, acc, "--output=x")
        check("accept-rev-option-injection", r["exit_code"], r["report"], COULD_NOT_CHECK,
              must_have=("invalid --accept-rev",))
        loose = os.path.join(repo, "uncommitted.tsv")   # working-tree edit, never committed
        with open(loose, "w", encoding="utf-8") as fh:
            fh.write(good)
        r = compare(inv_design, changed, loose, "HEAD")
        check("accept-uncommitted", r["exit_code"], r["report"], COULD_NOT_CHECK, must_not=("MATCH",))
        del os.environ["DCR_OWNER_EMAIL"]
        r = compare(inv_design, changed, acc, "HEAD")
        check("accept-no-owner-configured", r["exit_code"], r["report"], COULD_NOT_CHECK,
              must_have=("no owner email configured",))
        os.environ["DCR_OWNER_EMAIL"] = owner

        bad = commit(owner, "bad.tsv", "overview\tCHANGED\ttext:Welcome back, Jane Smith\t\t1\treason\towner\n")
        r = compare(inv_design, changed, bad, "HEAD")
        check("accept-malformed", r["exit_code"], r["report"], COULD_NOT_CHECK, must_not=("MATCH:",))
        legacy = commit(owner, "legacy.tsv", "overview\ttext:Welcome back, Jane Smith\treason\towner\n")
        r = compare(inv_design, changed, legacy, "HEAD")
        check("accept-legacy-4-field", r["exit_code"], r["report"], COULD_NOT_CHECK, must_have=("7 non-empty",))

        pin = commit(owner, "pin.tsv", good.replace("text:Good morning, Jane Smith", "text:Good evening, Jane Smith"))
        r = compare(inv_design, changed, pin, "HEAD")
        check("accept-changed-pins-app-value", r["exit_code"], r["report"], MISMATCH, must_have=("stale",))

        two = '<section data-section="s"><p data-item>x</p><button>Save</button><button>Save</button></section>'
        d2, a2 = write("two-d.html", two), write("two-a.html", '<section data-section="s"><p data-item>x</p></section>')
        row = "s\tMISSING_IN_APP\tcontrol:button:Save\t-\t{}\tremoved\towner quote: \"drop Save\"\n"
        r = compare(d2, a2, commit(owner, "count1.tsv", row.format(1)), "HEAD")
        check("accept-count-surplus-open", r["exit_code"], r["report"], MISMATCH, must_have=("1 unaccepted",))
        r = compare(d2, a2, commit(owner, "count2.tsv", row.format(2)), "HEAD")
        check("accept-count-exact", r["exit_code"], r["report"], MATCH, must_have=("accepted_n=2",))

        # 5. Style approvals, the per-section table, --workflow, and --report.
        _selftest_workflow(tmp, write, check, failures,
                           lambda rel, body, email=owner: commit(email, rel, body))
        # 6. data-parity-ignore, per-section thresholds, style identity, --baseline.
        _selftest_extras(tmp, write, check, failures,
                         lambda rel, body, email=owner: commit(email, rel, body))
    finally:
        for key, val in saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val


def _selftest_workflow(tmp: str, write, check, failures: list, commit) -> None:
    """Style accept rows/rules, per-section PASS table, `--workflow`, and `--report` cases.

    `commit(rel, body[, email])` commits one accept file as the owner (see
    `_selftest_accept`); every accept file is read at HEAD.
    """
    page = _st_page
    sd, twin = write("wf-d.html", page()), write("wf-twin.html", page())
    lh = write("wf-lh.html", page({"line-height": "24px"}))   # a global FOUNDATION line-height diff
    row = "style\tglobal\tline-height\t20px\t{}\tlooser body rhythm\towner quote: \"keep 24px\"\n"
    glob = commit("st-g.tsv", row.format("24px"))

    # 1. Style approvals: a value pair (global / section scope) and a min-<property> rule.
    r = compare(sd, lh, glob, "HEAD", style=True)
    check("style-accept-global", r["exit_code"], r["report"], MATCH,
          must_have=("STYLE_MATCH_WITH_ACCEPTED (accepted=9)", "ACCEPTED line-height: 20px -> 24px on 9 pair(s)"),
          must_not=("STYLE_DIFF", "FOUNDATION line-height"))
    r = compare(sd, lh, commit("st-pin.tsv", row.format("26px")), "HEAD", style=True)
    check("style-accept-pins-app-value", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("FOUNDATION line-height", "stale"))
    bold_h, bold_o = write("wf-bh.html", page(bold=("holdings", "button"))), write("wf-bo.html", page(bold=("overview", "button")))
    sec = commit("st-s.tsv", "style\tholdings\tfont-weight\t400\t600\tbrand CTA\towner quote: \"bold CTA\"\n")
    r = compare(sd, bold_h, sec, "HEAD", style=True)
    check("style-accept-section", r["exit_code"], r["report"], MATCH, must_have=("ACCEPTED font-weight: 400 -> 600",))
    r = compare(sd, bold_o, sec, "HEAD", style=True)
    check("style-accept-section-scoped", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("section 'overview' button:Open overview: 400 -> 600", "stale"))
    rule = commit("rule.tsv", "rule\tmin-font-size\t12px\taccessibility floor\towner quote: \"nothing under 12px\"\n")
    d11, d13 = write("wf-d11.html", page({"font-size": "11px"})), write("wf-d13.html", page({"font-size": "13px"}))
    a12, a13 = write("wf-a12.html", page({"font-size": "12px"})), write("wf-a13.html", page({"font-size": "13px"}))
    r = compare(d11, a12, rule, "HEAD", style=True)
    check("style-rule-min-font-size", r["exit_code"], r["report"], MATCH,
          must_have=("STYLE_MATCH_WITH_ACCEPTED (accepted=9)", "accessibility floor"))
    for label, d, a in (("style-rule-design-above-min", d13, a12), ("style-rule-app-not-at-min", d11, a13)):
        r = compare(d, a, rule, "HEAD", style=True)
        check(label, r["exit_code"], r["report"], STYLE_DIFF, must_have=("FOUNDATION font-size",))
    for label, body in (("style-row-unknown-property", "style\tglobal\tmargin\t0px\t4px\tr\to\n"),
                        ("style-row-short", "style\tglobal\tline-height\t20px\tr\to\n"),
                        ("rule-unknown-property", "rule\tmin-colour\t12px\tr\to\n"),
                        ("rule-not-px", "rule\tmin-font-size\t12\tr\to\n"),
                        ("visual-row-short", "visual-reviewed\tactivity\tr\n")):
        r = compare(sd, lh, commit(f"{label}.tsv", body), "HEAD", style=True)
        check(label, r["exit_code"], r["report"], COULD_NOT_CHECK, must_have=("accept file row 1",))
    parsed, err = parse_accept("style\tMISSING_IN_APP\tcontrol:button:Save\t-\t1\tr\to\n")
    if err or list(parsed or ()) != [("style", "MISSING_IN_APP", "control:button:save", "-")]:
        failures.append(f"accept-section-named-style: {parsed} {err}")

    # 2. Per-section PASS rule + progress metric.
    def verdicts(res: dict) -> dict:
        """Section id -> verdict."""
        return {e["id"]: e["verdict"] for e in res.get("sections", [])}

    r = compare(sd, bold_h, style=True)
    check("section-table", r["exit_code"], r["report"], STYLE_DIFF, must_have=("sections passed 2/3 —",))
    if verdicts(r) != {"overview": "PASS", "holdings": "FAIL", "activity": "PASS"} or r.get("sections_passed") != 2:
        failures.append(f"section-table: {verdicts(r)} passed={r.get('sections_passed')}")
    r = compare(sd, bold_h, sec, "HEAD", style=True)
    check("section-table-accepted", r["exit_code"], r["report"], MATCH, must_have=("sections passed 3/3", "ok +1 accepted"))
    r = compare(sd, bold_h)
    check("section-table-inventory-only", r["exit_code"], r["report"], MATCH,
          must_have=("sections passed 3/3 (inventory only)",))
    r = compare(sd, write("wf-inv.html", page().replace("Open activity", "Launch activity")), style=True)
    if verdicts(r).get("activity") != "FAIL" or r.get("sections_passed") != 2:
        failures.append(f"section-table-inventory-fail: {verdicts(r)}")
    stripped = re.sub(r"(<section data-section=\"activity\".*?</section>)",
                      lambda m: re.sub(r" data-cs='[^']*'", "", m.group(1)), page())
    r = compare(sd, write("wf-np.html", stripped), style=True)
    if verdicts(r).get("activity") != "UNVERIFIED" or "no pairs" not in r["report"]:
        failures.append(f"section-table-no-pairs-unverified: {verdicts(r)}")

    # 3. --workflow: tokens -> primitives -> sections; a failing foundation blocks every section.
    tok_d = write("wf-t.json", '{"color": {"$type": "color", "brand": {"$value": "#ff0000"}}}')
    tok_ok, tok_bad = write("wf-ok.css", ":root { --color-brand: #f00; }"), write("wf-bad.css", ":root { --color-brand: #00f; }")
    r = run_workflow(sd, twin, tok_d, tok_ok)
    check("workflow-clean", r["exit_code"], r["report"], MATCH,
          must_have=("workflow stage 1 tokens: MATCH", "stage 2 primitives: clean", "passed 3/3"))
    r = run_workflow(sd, twin, tok_d, tok_bad)
    check("workflow-tokens-block", r["exit_code"], r["report"], BLOCKED_BY_FOUNDATION,
          must_have=("BLOCKED_BY_FOUNDATION:", "tokens: MISMATCH", "passed 0/3 (BLOCKED_BY_FOUNDATION)"))
    if set(verdicts(r).values()) != {"BLOCKED_BY_FOUNDATION"} or \
            {e["own_verdict"] for e in r["sections"]} != {"PASS"}:
        failures.append(f"workflow-tokens-block: {verdicts(r)}")
    r = run_workflow(sd, lh, tok_d, tok_ok)
    check("workflow-foundation-block", r["exit_code"], r["report"], BLOCKED_BY_FOUNDATION,
          must_have=("FOUNDATION line-height",))
    r = run_workflow(sd, lh, tok_d, tok_ok, accept_path=glob, accept_rev="HEAD")
    check("workflow-foundation-accepted", r["exit_code"], r["report"], MATCH, must_have=("passed 3/3",))
    heads = write("wf-h.html", page({"font-size": "16px"}, tags=("h2",)))   # 3 of 9 pairs: no FOUNDATION
    r = compare(sd, heads, style=True)
    check("primitive-per-pair-without-workflow", r["exit_code"], r["report"], STYLE_DIFF,
          must_not=("FOUNDATION font-size", "PRIMITIVE"))
    r = run_workflow(sd, heads, tok_d, tok_ok)
    check("workflow-primitive-block", r["exit_code"], r["report"], BLOCKED_BY_FOUNDATION,
          must_have=("PRIMITIVE h2 font-size: differs on 3/3 h2 pair(s) in 3 section(s)",))
    r = run_workflow(sd, bold_h, tok_d, tok_ok)
    check("workflow-local-diff-not-blocked", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("stage 2 primitives: clean", "passed 2/3"), must_not=("BLOCKED_BY_FOUNDATION:",))
    r = run_workflow(sd, twin, os.path.join(tmp, "absent.json"), tok_ok)
    check("workflow-tokens-unreadable", r["exit_code"], r["report"], COULD_NOT_CHECK,
          must_have=("token stage could not compare", "passed 0/3 (UNVERIFIED"))
    if set(verdicts(r).values()) != {"UNVERIFIED"} or r.get("sections_passed") != 0:
        failures.append(f"workflow-tokens-unreadable-withholds: {verdicts(r)} passed={r.get('sections_passed')}")
    nocs = write("wf-nocs.html", re.sub(r" data-cs='[^']*'", "", page()))
    r = run_workflow(sd, nocs, tok_d, tok_ok)   # zero style pairs: stage 2 checked nothing
    check("workflow-no-style-pairs", r["exit_code"], r["report"], STYLE_COULD_NOT_CHECK,
          must_have=("stage 2 primitives: COULD_NOT_CHECK",), must_not=("primitives: clean", "foundation clean"))
    # A chart/map section has no text-bearing data-cs: UNVERIFIED (exit 6) until the
    # OWNER commits a visual-reviewed row; an agent-authored one fails the trust gate.
    np_ = write("wf-np.html", stripped)
    r = run_workflow(sd, np_, tok_d, tok_ok)
    check("workflow-visual-default-unverified", r["exit_code"], r["report"], STYLE_COULD_NOT_CHECK)
    vis = "visual-reviewed\tactivity\tchart-only section\towner quote: \"chart reviewed\"\n"
    r = run_workflow(sd, np_, tok_d, tok_ok, accept_path=commit("vis.tsv", vis), accept_rev="HEAD")
    check("workflow-visual-reviewed", r["exit_code"], r["report"], MATCH,
          must_have=("passed 3/3", "visual-reviewed", "chart-only section"))
    if verdicts(r).get("activity") != "PASS":
        failures.append(f"workflow-visual-reviewed: {verdicts(r)}")
    r = run_workflow(sd, np_, tok_d, tok_ok, accept_path=commit("vis-a.tsv", vis, "lane-bot@example.com"),
                     accept_rev="HEAD")
    check("workflow-visual-agent-authored", r["exit_code"], r["report"], COULD_NOT_CHECK,
          must_have=("not the owner",))
    r = compare(sd, bold_h, commit("vis-h.tsv", vis.replace("activity", "holdings")), "HEAD", style=True)
    check("visual-reviewed-needs-no-pairs", r["exit_code"], r["report"], STYLE_DIFF, must_have=("stale",))
    if verdicts(r).get("holdings") != "FAIL":
        failures.append(f"visual-reviewed-needs-no-pairs: {verdicts(r)}")
    r = compare(sd, write("wf-nocs2.html", re.sub(r" data-cs='[^']*'", "", page())),
                commit("vis-all.tsv", vis), "HEAD", style=True)
    if verdicts(r).get("activity") != "UNVERIFIED":   # a page-wide STYLE_COULD_NOT_CHECK is never rescued
        failures.append(f"visual-reviewed-page-could-not-check: {verdicts(r)}")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = main(["--design", sd, "--app", lh, "--workflow", "--design-tokens", tok_d, "--app-tokens", tok_ok])
    if rc != BLOCKED_BY_FOUNDATION:
        failures.append(f"workflow-cli: exit {rc}, want {BLOCKED_BY_FOUNDATION}")
    for label, argv in (("workflow-needs-tokens", ["--workflow"]), ("tokens-need-workflow", ["--app-tokens", tok_ok]),
                        ("shots-need-report", ["--design-shots", tmp])):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["--design", sd, "--app", twin, *argv])
            failures.append(f"{label}: accepted")
        except SystemExit as exc:
            if exc.code != USAGE_ERROR:
                failures.append(f"{label}: exit {exc.code}, want {USAGE_ERROR}")

    # 4. --report: self-contained HTML, escaped, screenshots embedded by section id.
    shots_d, shots_a = os.path.join(tmp, "shots-d"), os.path.join(tmp, "shots-a")
    for folder in (shots_d, shots_a):
        os.makedirs(folder)
        with open(os.path.join(folder, "overview.png"), "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\nfixture")
    rep = os.path.join(tmp, "report.html")

    def run_report(argv: list) -> tuple[int, str]:
        """Run main() with --report; return (exit, report HTML)."""
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main([*argv, "--report", rep])
        with open(rep, encoding="utf-8") as fh:
            return rc, fh.read()

    rc, page_html = run_report(["--design", sd, "--app", bold_h, "--style", "--design-shots", shots_d,
                                "--app-shots", shots_a])
    if rc != STYLE_DIFF or page_html.count("data:image/png;base64,") != 2 or "srcdoc=" not in page_html \
            or "sections passed 2/3" not in page_html or "holdings — FAIL" not in page_html \
            or "font-weight" not in page_html or "<script" in page_html or re.search(r"https?:", page_html):
        failures.append(f"report-shots: exit {rc}")
    srcdocs = [html.unescape(v) for v in re.findall(r'srcdoc="([^"]*)"', page_html)]
    if not srcdocs or not all(d.startswith(_SRCDOC_CSP) for d in srcdocs):
        failures.append("report-srcdoc-csp: a srcdoc lacks the leading no-network CSP meta")
    uni = write("wf-u.html", page(sids=("r\u00e9sum\u00e9", "b")))   # a non-ASCII section id
    write_report(compare(uni, uni), rep, uni, uni)
    with open(rep, encoding="utf-8") as fh:
        sels = re.findall(r':not\(\[data-section="((?:[^"\\]|\\.)*)"\]\)', html.unescape(fh.read()))
    decoded = {re.sub(r"\\([0-9a-fA-F]{1,6})\s?|\\(.)", lambda m: chr(int(m[1], 16)) if m[1] else m[2], x)
               for x in sels}   # CSS string escapes, decoded per CSS Syntax
    if decoded != {"r\u00e9sum\u00e9", "b"}:
        failures.append(f"report-css-escape: selectors decode to {sorted(decoded)}")
    xss = write("wf-x.html", '<section data-section="s"><p data-item>x</p><p>&lt;img src=x onerror=alert(1)&gt;</p></section>')
    rc, page_html = run_report(["--design", xss, "--app", write("wf-xa.html", '<section data-section="s"><p data-item>x</p></section>')])
    if rc != MISMATCH or "<img src=x onerror" in page_html or "MISSING_IN_APP" not in page_html:
        failures.append(f"report-escapes: exit {rc}")
    write_report(compare(sd, bold_h, sec, "HEAD", style=True), rep, sd, bold_h)
    with open(rep, encoding="utf-8") as fh:
        if "brand CTA" not in fh.read():
            failures.append("report-accepted-rows: owner reason missing")
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rc = main(["--design", sd, "--app", twin, "--report", os.path.join(tmp, "no-dir", "r.html")])
    if rc != USAGE_ERROR:
        failures.append(f"report-unwritable: exit {rc}, want {USAGE_ERROR}")


def _selftest_extras(tmp: str, write, check, failures: list, commit) -> None:
    """`data-parity-ignore`, `threshold` accept rows, style identity, and `--baseline` cases.

    `commit(rel, body[, email])` commits one accept file as the owner (see
    `_selftest_accept`); every accept file is read at HEAD.
    """
    page = _st_page
    wrap = '<section data-section="s"><p data-item>x</p>{}</section>'

    def two(label: str, d_body: str, a_body: str, **kw) -> dict:
        """Compare one inline design/app section pair."""
        return compare(write(f"{label}-d.html", wrap.format(d_body)),
                       write(f"{label}-a.html", wrap.format(a_body)), **kw)

    # 1. data-parity-ignore: excluded from inventory and style, always listed.
    # A design-side ignore needs an owner `ignore` accept row; an app-side one
    # with no design counterpart (same section + id) stays an open row.
    clock_d = '<p>Updated <span data-parity-ignore="clock">10:41</span></p>'
    clock_a = '<p>Updated <span data-parity-ignore="clock">11:02</span></p>'
    r = two("ig-both", clock_d, clock_a)
    check("ignore-design-needs-owner-row", r["exit_code"], r["report"], COULD_NOT_CHECK,
          must_have=("owner-authored", "ignore<TAB><section><TAB><id>", "section 's' clock"), must_not=("MATCH:",))
    ig_acc = commit("ig.tsv", "ignore\ts\tclock\n")
    r = two("ig-both", clock_d, clock_a, accept_path=ig_acc, accept_rev="HEAD")
    check("ignore-both-sides-owner", r["exit_code"], r["report"], MATCH,
          must_have=("MATCH_WITH_IGNORED", "2 element(s) excluded", "design: section 's' clock",
                     "app: section 's' clock", "PASS_WITH_IGNORED"), must_not=("MATCH: every",))
    if r.get("verdict") != "MATCH_WITH_IGNORED" or \
            [len(r.get("ignored", {}).get(k, ())) for k in ("design", "app")] != [1, 1]:
        failures.append(f"ignore-both-sides-owner: {r.get('verdict')} ignored {r.get('ignored')}")
    r = two("ig-both", clock_d, clock_a, accept_path=commit("ig-a.tsv", "ignore\ts\tclock\n", "lane-bot@example.com"),
            accept_rev="HEAD")
    check("ignore-row-agent-authored", r["exit_code"], r["report"], COULD_NOT_CHECK, must_have=("not the owner",))
    r = two("ig-dmiss", '<button data-parity-ignore="share">Share</button>', "")
    check("ignore-design-hides-missing", r["exit_code"], r["report"], COULD_NOT_CHECK, must_have=("section 's' share",))
    banner = '<div data-parity-ignore="dev-banner"><button class="d-none">Reset seed</button></div>'
    r = two("ig-app", "", banner)
    check("ignore-app-unpaired-open", r["exit_code"], r["report"], MISMATCH,
          must_have=("EXTRA_IN_APP", "ignored:dev-banner", "app: section 's' dev-banner"), must_not=("data-visible",))
    ext = commit("ig-ext.tsv", "s\tEXTRA_IN_APP\tignored:dev-banner\tignored:dev-banner\t1\tharness banner\towner\n")
    r = two("ig-app", "", banner, accept_path=ext, accept_rev="HEAD")
    check("ignore-app-unpaired-accepted", r["exit_code"], r["report"], MATCH, must_have=("MATCH_WITH_ACCEPTED",))
    r = two("ig-hides-design", "<button>Share</button>", "<button data-parity-ignore>Share</button>")
    check("ignore-cannot-hide-design-item", r["exit_code"], r["report"], MISMATCH,
          must_have=("MISSING_IN_APP", "control:button:Share", "app: section 's' <button>"))
    promo = '<section data-section="promo" data-parity-ignore="promo"><p data-item>Sale</p></section>'
    sec_d, sec_a = write("ig-sec-d.html", wrap.format("") + promo), write("ig-sec-a.html", wrap.format(""))
    r = compare(sec_d, sec_a)
    check("ignore-section-needs-owner-row", r["exit_code"], r["report"], COULD_NOT_CHECK,
          must_have=("(outside sections) promo",))
    r = compare(sec_d, sec_a, commit("ig-sec.tsv", "ignore\t-\tpromo\n"), "HEAD")
    check("ignore-section-owner", r["exit_code"], r["report"], MATCH,
          must_have=("MATCH_WITH_IGNORED", "design: (outside sections) promo"), must_not=("missing:",))
    bad_cs = "<p data-parity-ignore=\"ad\" data-cs='{\"color\": \"red\"}'>Sponsored</p>"
    r = compare(write("ig-st-d.html", page()),
                write("ig-st-a.html", page().replace("</section>", bad_cs + "</section>", 1)), style=True)
    check("ignore-style", r["exit_code"], r["report"], MISMATCH,
          must_have=("STYLE_MATCH", "ignored:ad", "app: section 'overview' ad"), must_not=("malformed",))

    # 2. Per-section style-identity thresholds: owner-authored, default strict.
    sd, bold_h = write("x-d.html", page()), write("x-bh.html", page(bold=("holdings", "button")))
    r = compare(sd, bold_h, commit("thr60.tsv", "threshold\tholdings\t60\n"), "HEAD", style=True)
    check("threshold-met", r["exit_code"], r["report"], MATCH,
          must_have=("STYLE_MATCH_WITH_ACCEPTED",
                     ("THRESHOLD section 'holdings': style identity 2/3 = 66.6% (<100%) >= owner threshold 60%"),
                     "1 row(s) tolerated", "sections passed 3/3", "+1 tolerated"),
          must_not=("STYLE_DIFF font-weight",))
    r = compare(sd, bold_h, commit("thr70.tsv", "threshold\tholdings\t70%\n"), "HEAD", style=True)
    check("threshold-not-met", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("style identity 2/3 = 66.6% (<100%) < owner threshold 70%", "STYLE_DIFF font-weight"))
    r = compare(sd, bold_h, commit("thr-other.tsv", "threshold\toverview\t50\n"), "HEAD", style=True)
    check("threshold-section-scoped", r["exit_code"], r["report"], STYLE_DIFF, must_have=("stale",))
    found = write("x-f.html", page({"line-height": "24px"}, tags=("h2", "button")))   # 6/9, 3 sections
    r = compare(sd, found, commit("thr-f.tsv", "threshold\toverview\t30\n"), "HEAD", style=True)
    check("threshold-never-waives-foundation", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("FOUNDATION line-height",), must_not=("tolerated",))
    prim = write("x-p.html", page({"font-size": "16px"}, tags=("h2",)))   # h2 font-size in 3/3 sections
    r = compare(sd, prim, commit("thr-p.tsv", "threshold\toverview\t60\n"), "HEAD", style=True)
    check("threshold-never-waives-primitive", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("1 FOUNDATION/PRIMITIVE row(s) stay open",), must_not=("tolerated",))
    if ((r.get("style") or {}).get("primitives") or [{}])[0].get("property") != "font-size":
        failures.append(f"threshold-never-waives-primitive: primitives {(r.get('style') or {}).get('primitives')}")
    for label, body in (("threshold-zero", "threshold\tholdings\t0\n"),
                        ("threshold-over-100", "threshold\tholdings\t101\n"),
                        ("threshold-not-number", "threshold\tholdings\tmost\n"),
                        ("threshold-extra-field", "threshold\tholdings\t90\treason\n")):
        r = compare(sd, bold_h, commit(f"{label}.tsv", body), "HEAD", style=True)
        check(label, r["exit_code"], r["report"], COULD_NOT_CHECK, must_have=("accept file row 1",))
    r = compare(sd, bold_h, commit("thr-agent.tsv", "threshold\tholdings\t60\n", "lane-bot@example.com"),
                "HEAD", style=True)
    check("threshold-agent-authored", r["exit_code"], r["report"], COULD_NOT_CHECK, must_have=("not the owner",))

    # 3. Style identity: per-property mismatch counts, top diffs, accepted-ignored
    # identity, and an own-text second pass for pairs whose full text differs.
    sa = write("x-sa.html", page({"line-height": "24px"}, bold=("holdings", "button")))
    r = compare(sd, sa, style=True)
    st = r.get("style") or {}
    check("style-identity-report", r["exit_code"], r["report"], STYLE_DIFF,
          must_have=("mismatch count per property: line-height=9, font-weight=1",
                     "top style diffs (text | prop | design | app):",
                     "  Open holdings | font-weight | 400 | 600", "  Holdings | line-height | 20px | 24px"))
    if st.get("per_property") != {"line-height": 9, "font-weight": 1} or len(st.get("top") or ()) != 10:
        failures.append(f"style-identity-report: per_property {st.get('per_property')} top {len(st.get('top') or ())}")
    lh = write("x-lh.html", page({"line-height": "24px"}))
    glob = commit("x-g.tsv", "style\tglobal\tline-height\t20px\t24px\tlooser rhythm\towner quote: \"keep 24px\"\n")
    r = compare(sd, lh, glob, "HEAD", style=True)
    check("style-identity-accepted-ignored", r["exit_code"], r["report"], MATCH,
          must_have=("style-identical 0/9", "identity (owner-accepted ignored) 9/9 = 100.0%"),
          must_not=("top style diffs",))
    cs = json.dumps(_ST_BASE)
    cs_b = json.dumps({**_ST_BASE, "font-weight": "600"})
    r = two("own", f"<button data-cs='{cs}'>Open <span>holdings</span></button>",
            f"<button data-cs='{cs_b}'>Open <span>reports</span></button>", style=True)
    check("style-own-text-pairing", r["exit_code"], r["report"], MISMATCH,
          must_have=("section 's' button:Open: 400 -> 600",))
    if (r.get("style") or {}).get("pairs") != 1:
        failures.append(f"style-own-text-pairing: pairs {(r.get('style') or {}).get('pairs')}, want 1")

    # 5. Structural line counts: `data-lines` (rendered line boxes, a count,
    # never a height) joins the item key, so 2-line rows vs 1-line design rows FAIL.
    rows_d = '<ul><li data-lines="1">Alpha</li><li data-lines="1">Beta</li></ul><p data-lines="1">Caption</p>'
    r = two("ln-rows", rows_d, rows_d.replace('data-lines="1"', 'data-lines="2"'))
    check("lines-two-vs-one", r["exit_code"], r["report"], MISMATCH,
          must_have=("list-item:Alpha [lines: 1] -> list-item:Alpha [lines: 2]", "text:Caption [lines: 1]",
                     "3 unaccepted"))
    r = two("ln-h", '<h2 data-lines="1">Totals</h2>', '<h2 data-lines="2">Totals</h2>')
    check("lines-heading", r["exit_code"], r["report"], MISMATCH, must_have=("heading:h2:Totals [lines: 1]",))
    r = two("ln-eq", rows_d, rows_d.replace("<ul>", '<ul style="padding:40px" height="900">'))
    check("lines-equal-size-free", r["exit_code"], r["report"], MATCH)
    r = two("ln-one", rows_d, rows_d.replace(' data-lines="1"', ""))
    check("lines-one-sided-surfaces", r["exit_code"], r["report"], MISMATCH, must_have=("[lines: 1]",))
    for label, bad in (("lines-not-number", "two"), ("lines-zero", "0"), ("lines-leading-zero", "01")):
        r = two(label, rows_d, rows_d.replace('data-lines="1"', f'data-lines="{bad}"', 1))
        check(label, r["exit_code"], r["report"], COULD_NOT_CHECK, must_have=(f'data-lines="{bad}"',),
              must_not=("MISMATCH:",))

    # 6. Same-crop guard (design is the reference): the app crop must share a
    # design data-anchor and hold no neighbour's data-anchor; only that section
    # is UNVERIFIED, the rest is still scored. A moved heading is a MOVED row.
    kpis = ('<section data-section="kpis"><p data-item>x</p><div data-anchor>Total value</div>{}</section>')
    hold = '<section data-section="holdings"><p data-item>x</p><h2>Holdings</h2>{}</section>'
    d_crop = write("cr-d.html", kpis.format("<button>Export</button>") + hold.format(""))
    leak = write("cr-leak.html", kpis.format("") + hold.format("<div data-anchor>Total value</div>"))
    r = compare(d_crop, leak)
    check("crop-app-leak-scoped", r["exit_code"], r["report"], COULD_NOT_CHECK_CROP,
          must_have=("COULD_NOT_CHECK_CROP:",
                     "app crop of section 'holdings' holds anchor 'Total value' of neighbouring section 'kpis'",
                     "MISSING_IN_APP", "control:button:Export", "sections passed 0/2"),
          must_not=("EXTRA_IN_APP", "MATCH:"))
    if {e["id"]: e["verdict"] for e in r.get("sections", [])} != {"kpis": "FAIL", "holdings": "UNVERIFIED"}:
        failures.append(f"crop-app-leak-scoped: sections {[(e['id'], e['verdict']) for e in r.get('sections', [])]}")
    listed = "<p data-anchor>Holdings list</p>"
    r = compare(write("cr-dleak.html", kpis.format("") + hold.format("<div data-anchor>Total value</div>" + listed)),
                write("cr-a.html", kpis.format("") + hold.format(listed)))
    check("crop-design-is-reference", r["exit_code"], r["report"], MISMATCH, must_not=("COULD_NOT_CHECK_CROP",))
    head = '<section data-section="header"><p data-item>x</p><h1>Dashboard</h1></section>'
    r = compare(write("cr-hd.html", head + hold.format("")),
                write("cr-ha.html", head + hold.format("<h3>Dashboard</h3>")))
    check("crop-plain-heading-is-extra", r["exit_code"], r["report"], MISMATCH,
          must_have=("EXTRA_IN_APP", "heading:h3:Dashboard"), must_not=("COULD_NOT_CHECK_CROP",))
    moved_d = hold.format("<h3>Recent</h3>") + '<section data-section="activity"><p data-item>x</p></section>'
    moved_a = hold.format("") + '<section data-section="activity"><p data-item>x</p><h3>Recent</h3></section>'
    r = compare(write("cr-md.html", moved_d), write("cr-ma.html", moved_a))
    check("moved-heading-row", r["exit_code"], r["report"], MISMATCH,
          must_have=("MOVED", "heading:h3:Recent -> section 'activity'"),
          must_not=("EXTRA_IN_APP", "MISSING_IN_APP", "COULD_NOT_CHECK_CROP"))
    moved = {(s["id"], row["status"], row["item"]) for s in r.get("sections", []) for row in s["rows"]}
    if moved != {("holdings", "MOVED", "heading:h3:Recent")}:
        failures.append(f"moved-heading-row: rows {sorted(moved)}")
    anch = '<section data-section="holdings"><p data-item>x</p><h2 data-anchor>Holdings</h2><p>Rows</p></section>'
    r = compare(write("cr-sd.html", anch), write("cr-sa.html", anch.replace("Holdings", "Activity")))
    check("crop-no-shared-anchor", r["exit_code"], r["report"], COULD_NOT_CHECK_CROP,
          must_have=("app crop of section 'holdings' shares none of its design anchors (Holdings)",))
    dup = ''.join(f'<section data-section="{s}"><p data-item>x</p><h3>Details</h3></section>' for s in ("a", "b"))
    r = compare(write("cr-dup.html", dup), write("cr-dup2.html", dup))
    check("crop-shared-heading-not-leak", r["exit_code"], r["report"], MATCH)
    tok_d = write("cr-t.json", '{"color": {"$type": "color", "brand": {"$value": "#ff0000"}}}')
    r = run_workflow(d_crop, leak, tok_d, write("cr-bad.css", ":root { --color-brand: #00f; }"))
    check("crop-outranks-workflow-block", r["exit_code"], r["report"], COULD_NOT_CHECK_CROP,
          must_not=("BLOCKED_BY_FOUNDATION:",))

    # 4. --baseline regression net: write only from a passing run with
    # --write-baseline; later runs list only new deltas, exit REGRESSION (8).
    def cli(argv: list) -> tuple[int, str]:
        """Run main(argv); return (exit, stdout)."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            try:
                rc = main(argv)
            except SystemExit as exc:
                rc = exc.code
        return rc, out.getvalue()

    base = os.path.join(tmp, "base.json")
    extra = '<section data-section="promo"><p data-item>Spring sale</p></section>'
    twin_x = write("bl-twin.html", page() + extra)
    rc, out = cli(["--design", sd, "--app", twin_x, "--style", "--baseline", base, "--write-baseline"])
    check("baseline-write", rc, out, MATCH, must_have=("baseline written",))
    if not os.path.isfile(base):
        failures.append("baseline-write: no baseline file")
    refused = os.path.join(tmp, "refused.json")
    rc, out = cli(["--design", sd, "--app", bold_h, "--style", "--baseline", refused, "--write-baseline"])
    check("baseline-write-refused", rc, out, STYLE_DIFF, must_have=("baseline not written",))
    if os.path.exists(refused):
        failures.append("baseline-write-refused: a failing run wrote a baseline")
    rc, out = cli(["--design", sd, "--app", twin_x, "--style", "--baseline", base])
    check("baseline-clean", rc, out, MATCH, must_have=("baseline: 0 new delta(s)",))
    rc, out = cli(["--design", sd, "--app", write("bl-rm.html", re.sub(
        r"<button data-cs='[^']*'>Open activity</button>", "", page()) + extra), "--style", "--baseline", base])
    check("baseline-regression-removed", rc, out, REGRESSION,
          must_have=("REGRESSION:", "REMOVED", "section 'activity' control:button:Open activity"),
          must_not=("MISSING_IN_APP",))
    rc, out = cli(["--design", sd, "--app", write("bl-bh.html", page(bold=("holdings", "button")) + extra),
                   "--style", "--baseline", base])
    check("baseline-regression-style", rc, out, REGRESSION,
          must_have=("STYLE_CHANGED", "section 'holdings' button:Open holdings font-weight: 400 -> 600"))
    rc, out = cli(["--design", sd, "--app", write("bl-promo.html", page() + extra.replace("Spring", "Summer")),
                   "--style", "--baseline", base])
    check("baseline-regression-superset-section", rc, out, REGRESSION,
          must_have=("section 'promo' text:Spring sale", "ADDED"))
    rc, out = cli(["--design", write("bl-d2.html", page().replace("</section>", "<p>New copy</p></section>", 1)),
                   "--app", twin_x, "--style", "--baseline", base])
    check("baseline-design-change-is-mismatch", rc, out, MISMATCH, must_have=("baseline: 0 new delta(s)",))
    vd = '<section data-section="s"><p data-item>Balance <span data-value>{}</span></p></section>'
    vbase = os.path.join(tmp, "vbase.json")
    rc, out = cli(["--design", write("bl-vd.html", vd.format("$10")), "--app", write("bl-va.html", vd.format("$40")),
                   "--baseline", vbase, "--write-baseline"])
    check("baseline-masked-write", rc, out, MATCH)
    rc, out = cli(["--design", write("bl-vd.html", vd.format("$10")), "--app", write("bl-vb.html", vd.format("$75")),
                   "--baseline", vbase])
    check("baseline-masked-value-not-regression", rc, out, MATCH, must_have=("baseline: 0 new delta(s)",))
    for label, argv in (("baseline-absent", ["--baseline", os.path.join(tmp, "nope.json")]),
                        ("baseline-malformed", ["--baseline", write("bl-bad.json", "{not json")]),
                        ("baseline-style-flag-differs", ["--baseline", vbase])):
        rc, out = cli(["--design", sd, "--app", twin_x, "--style", *argv])
        check(label, rc, out, COULD_NOT_CHECK, must_have=("baseline",))
    # Re-recording over an existing baseline shows its deltas and needs
    # --accept-regression before it overwrites a regression.
    base2 = os.path.join(tmp, "base2.json")
    cli(["--design", sd, "--app", twin_x, "--style", "--baseline", base2, "--write-baseline"])
    with open(base2, encoding="utf-8") as fh:
        before = fh.read()
    promo2 = write("bl-promo2.html", page() + extra.replace("Spring", "Summer"))
    rc, out = cli(["--design", sd, "--app", promo2, "--style", "--baseline", base2, "--write-baseline"])
    check("baseline-overwrite-refused", rc, out, REGRESSION,
          must_have=("baseline not overwritten", "REMOVED", "section 'promo' text:Spring sale", "--accept-regression"))
    with open(base2, encoding="utf-8") as fh:
        if fh.read() != before:
            failures.append("baseline-overwrite-refused: the existing baseline changed")
    rc, out = cli(["--design", sd, "--app", promo2, "--style", "--baseline", base2, "--write-baseline",
                   "--accept-regression"])
    check("baseline-overwrite-accepted", rc, out, MATCH,
          must_have=("baseline written", "accepted by --accept-regression", "ADDED"))
    rc, out = cli(["--design", sd, "--app", promo2, "--style", "--baseline", base2, "--write-baseline"])
    check("baseline-rewrite-no-delta", rc, out, MATCH, must_have=("baseline written",))
    for label, argv in (("accept-regression-needs-write", ["--baseline", base, "--accept-regression"]),
                        ("baseline-path-is-app", ["--baseline", twin_x]),
                        ("baseline-path-is-design", ["--baseline", sd, "--write-baseline"])):
        rc, _ = cli(["--design", sd, "--app", twin_x, "--style", *argv])
        if rc != USAGE_ERROR:
            failures.append(f"{label}: exit {rc}, want {USAGE_ERROR}")
    with open(sd, encoding="utf-8") as fh:
        if "parity_differ-baseline" in fh.read():
            failures.append("baseline-path-is-design: the design render was overwritten")
    for label, argv in (("write-baseline-needs-baseline", ["--write-baseline"]),
                        ("baseline-not-with-workflow", ["--baseline", base, "--workflow", "--design-tokens", sd,
                                                        "--app-tokens", sd])):
        rc, _ = cli(["--design", sd, "--app", twin_x, *argv])
        if rc != USAGE_ERROR:
            failures.append(f"{label}: exit {rc}, want {USAGE_ERROR}")


def _min_pairs(text: str) -> int:
    """argparse type for `--min-pairs` / `--style-min-pairs`: an integer >= 1 (a floor of 0 checks nothing)."""
    if not re.fullmatch(r"[1-9][0-9]*", text.strip()):
        raise argparse.ArgumentTypeError(f"must be an integer >= 1: {text!r}")
    return int(text)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: `--selftest`, or `--design <f> --app <f>` (two-sided only)."""
    parser = argparse.ArgumentParser(
        description="Two-sided design<->app parity gate (sections + element inventory). "
                    "MATCH (exit 0) is the only pass; size is never an input."
    )
    parser.add_argument("--design", help="design render: HTML DOM snapshot or .json section list")
    parser.add_argument("--app", help="app render: HTML DOM snapshot or .json section list")
    parser.add_argument("--accept", help="owner-authored accepted-deviations TSV (7 fields; see module doc)")
    parser.add_argument("--accept-rev", help="git revision to read and verify the accept file at "
                                             "(default HEAD; required without focus_gate.py)")
    parser.add_argument("--min-pairs", type=_min_pairs, help="COULD_NOT_CHECK when fewer matched "
                        "element pairs than N (your floor for this page; never guessed)")
    parser.add_argument("--style", action="store_true", help="also diff computed styles (data-cs) of "
                        "text-matched pairs; reported apart from completeness")
    parser.add_argument("--style-min-pairs", type=_min_pairs, help="with --style: STYLE_COULD_NOT_CHECK "
                        "(exit 6) when fewer text-matched style pairs than N; separate from --min-pairs")
    parser.add_argument("--workflow", action="store_true", help="foundation-first gate: tokens -> "
                        "primitives -> sections (implies --style; exit 7 BLOCKED_BY_FOUNDATION)")
    parser.add_argument("--design-tokens", help="with --workflow: design token export (DTCG .json or CSS)")
    parser.add_argument("--app-tokens", help="with --workflow: app token export (DTCG .json or CSS)")
    parser.add_argument("--token-map", help="with --workflow: token_differ.py --map TSV")
    parser.add_argument("--token-min-pairs", type=_min_pairs, help="with --workflow: token_differ.py --min-pairs")
    parser.add_argument("--report", help="write a self-contained per-section HTML evidence report here")
    parser.add_argument("--design-shots", help="with --report: dir of design screenshots named <section id>.png")
    parser.add_argument("--app-shots", help="with --report: dir of app screenshots named <section id>.png")
    parser.add_argument("--baseline", help="regression net: report only new deltas vs this passing-run "
                        "fingerprint (exit 8 REGRESSION)")
    parser.add_argument("--write-baseline", action="store_true", help="with --baseline: record this run's "
                        "fingerprint there, only when the run passes")
    parser.add_argument("--accept-regression", action="store_true", help="with --write-baseline: overwrite an "
                        "existing baseline even though this run shows new deltas vs it")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON (board posts)")
    parser.add_argument("--selftest", action="store_true", help="run the committed-fixture self-test")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.design or not args.app:
        parser.error("--design and --app are both required (two-sided input, or no output)")
        return USAGE_ERROR  # pragma: no cover — parser.error() already exits(2)
    if args.accept_rev and not args.accept:
        parser.error("--accept-rev needs --accept")
    if args.style_min_pairs is not None and not (args.style or args.workflow):
        parser.error("--style-min-pairs needs --style")
    if args.workflow and not (args.design_tokens and args.app_tokens):
        parser.error("--workflow needs --design-tokens and --app-tokens (the foundation is never assumed)")
    if not args.workflow and (args.design_tokens or args.app_tokens or args.token_map or args.token_min_pairs):
        parser.error("--design-tokens/--app-tokens/--token-map/--token-min-pairs need --workflow")
    if (args.design_shots or args.app_shots) and not args.report:
        parser.error("--design-shots/--app-shots need --report")
    if args.write_baseline and not args.baseline:
        parser.error("--write-baseline needs --baseline <file> (a baseline is only written explicitly)")
    if args.baseline and args.workflow:
        parser.error("--baseline is not supported with --workflow")
    if args.accept_regression and not args.write_baseline:
        parser.error("--accept-regression needs --write-baseline")
    if args.baseline and os.path.realpath(args.baseline) in {
            os.path.realpath(p) for p in (args.design, args.app, args.accept, args.report) if p}:
        parser.error("--baseline must not be the --design, --app, --accept, or --report path")

    if args.workflow:
        result = run_workflow(args.design, args.app, args.design_tokens, args.app_tokens, args.token_map,
                              args.accept, args.accept_rev, min_pairs=args.min_pairs,
                              style_min_pairs=args.style_min_pairs, token_min_pairs=args.token_min_pairs)
    else:
        result = compare(args.design, args.app, args.accept, args.accept_rev,
                         min_pairs=args.min_pairs, style=args.style, style_min_pairs=args.style_min_pairs)
        if args.baseline:
            try:
                apply_baseline(result, args.app, args.baseline, args.style, args.write_baseline,
                               args.accept_regression)
            except OSError as exc:
                print(f"parity_differ: cannot write --baseline {args.baseline}: {exc}", file=sys.stderr)
                return USAGE_ERROR
    if args.report:
        try:
            write_report(result, args.report, args.design, args.app, args.design_shots, args.app_shots)
        except OSError as exc:
            print(f"parity_differ: cannot write --report {args.report}: {exc}", file=sys.stderr)
            return USAGE_ERROR
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else result["report"])
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
