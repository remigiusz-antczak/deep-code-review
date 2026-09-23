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
clipping, viewport fit), never to a "complete" or "matches" verdict.

CONTRACT (fail-closed; every branch below is load-bearing, not cosmetic)
-------------------------------------------------------------------------
* MATCH (0) — the plain pass. Both sides present; every design section is
  present in the app; every design-populated section is populated in the app;
  and every matched section's inventory is equal.
* MATCH_WITH_ACCEPTED (0, printed distinctly with `accepted_n=N`) — as MATCH,
  except N differences remain, each covered by a row of an OWNER-AUTHORED
  `--accept` file. Never reported as a plain MATCH.
* MISMATCH (1) — lists the gap per section: "missing" (build it) or "empty"
  (seed it), then per section MISSING_IN_APP / EXTRA_IN_APP / CHANGED
  inventory rows. That list IS the work queue for a mirror/restyle task. The
  report carries a fixed precondition line: both renders must share the same
  auth + data state, or a signed-out app render reports every gated section
  as "missing" and points the fix in the wrong direction (build, not sign
  in). The line scopes this matched-state diff only; the signed-out default
  surface remains a separate required parity check.
* USAGE_ERROR (2) — bad CLI invocation (e.g. only one of --design/--app).
* COULD_NOT_CHECK (3) — either side is missing, unreadable, empty, or yields
  no sections; a section uses a class-based hiding token with no computed-
  visibility marker (VISIBILITY below); the `--accept` file is not owner-
  authored, not committed, or malformed; or a would-be MATCH rests on a side
  with no inventory (a `.json` section list). Never a score, never a pass.
* CANNOT_COMPARE (4) — the app is UNSEEDED: every design-populated section
  exists in the app but is uniformly empty. This is a precondition failure
  (seed the app's data), NOT a structural mismatch — it must never be "fixed"
  by condensing or deleting the empty sections. Distinct from MISMATCH so an
  agent cannot quietly reclassify "unseeded" as "aligned once trimmed down."
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
different label); the rest are MISSING_IN_APP / EXTRA_IN_APP. Completeness =
matched items / design items, per section and overall — items, never pixels;
the percentage is floored and any shortfall prints `(<100%)`.

ACCEPTED DEVIATIONS (`--accept FILE [--accept-rev REV]`) — OWNER-AUTHORED ONLY
-----------------------------------------------------------------------------
Tab-separated rows, 7 non-empty fields:
  section  status  item  app-value  count  reason  owner-quote-or-commit
`status` is MISSING_IN_APP / EXTRA_IN_APP / CHANGED; `item` is the row's item
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

USAGE
-----
  parity_differ.py --design <file> --app <file> [--accept <tsv> [--accept-rev REV]] [--json]
  parity_differ.py --selftest
"""
from __future__ import annotations

import argparse
import functools
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
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
MATCH_WITH_ACCEPTED = "MATCH_WITH_ACCEPTED"   # verdict name; exit code is MATCH

_VERDICT_NAMES = {MATCH: "MATCH", MISMATCH: "MISMATCH", USAGE_ERROR: "USAGE_ERROR",
                  COULD_NOT_CHECK: "COULD_NOT_CHECK", CANNOT_COMPARE: "CANNOT_COMPARE"}

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
_ROW_STATUSES = ("MISSING_IN_APP", "EXTRA_IN_APP", "CHANGED")
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
        "bodyhide",
        "capture",
        "cells",
        "container",
        "control",
        "hidden",
        "id",
        "idcap",
        "item",
        "kind",
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
        self.hidden = self.notext = self.bodyhide = False
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
        sid = attr_map.get("data-section")
        if sid is not None and sid not in self._by_id:
            record = {"id": sid, "items": 0, "empties": 0, "inv": [], "marked": False,
                      "unresolved": []}
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
                self._emit(self._buf_section, "text", "", text)
        self._buf, self._buf_section = [], None

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
        shown = parent is None or not (parent.hidden or parent.kind == "media"
                                       or (parent.bodyhide and tag != "summary"))
        vis_hidden = bool(
            not shown or tag in _SKIP_TAGS or "hidden" in attr_map or marker == "false"
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
        return frame

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
        return owned

    def _finalize(self, frame: _Frame) -> None:
        """Close one frame: fill its item label from the captured text."""
        if frame.tag in _BLOCK_TAGS or frame.sid is not None:
            self._flush()
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
        if icon is not None:
            icon.item["text"] += data
        text = (f"{_MASK_OPEN}{top.maskid}{_MASK_SEP}{data}{_MASK_CLOSE}"
                if top.maskid is not None else data)
        if top.kind == "option" and not top.hidden:
            top.capture.append(text)   # option text never leaks into a wrapping label
            return
        if top.hidden or top.notext or top.bodyhide:
            return
        if not self._feed_captures(text):
            if self._buf_section is None:
                self._buf_section = self._innermost_section()
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

    Each record is `{"id", "populated", "inventory", "marked", "unresolved"}`;
    `inventory` is a list of raw items for an HTML side and None for a `.json`
    side (which carries no inventory); `unresolved` lists class-based hiding
    tokens that carry no `data-visible` marker (VISIBILITY). None for the
    whole side covers every fail-closed case in one place: no path given,
    file absent, unreadable, empty/whitespace-only, invalid JSON, or zero
    sections. A caller must treat None as COULD_NOT_CHECK, never as an
    empty-but-valid side.
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
        rows = [{"id": str(row["id"]), "populated": bool(row.get("populated", False)),
                 "inventory": None, "marked": False, "unresolved": []}
                for row in data if isinstance(row, dict) and "id" in row]
        return rows or None

    parser = _SectionExtractor()
    parser.feed(raw)
    parser.close()
    parser.finish()
    if not parser.sections:
        return None
    return [{"id": s["id"], "populated": s["items"] > 0, "inventory": s["inv"],
             "marked": s["marked"], "unresolved": s["unresolved"]} for s in parser.sections]


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
        disp = " ".join([disp, *(f"[{n}]" for n in notes)]).strip()
        role = raw["role"]
        key = f"{raw['kind']}:{role}:{disp}" if role else f"{raw['kind']}:{disp}"
        out.append({"kind": raw["kind"], "role": role, "disp": disp, "cmp": disp.casefold(),
                    "count": raw["count"], "key": key})
    return out


def _show(item: dict) -> str:
    """Printable form of one item (containers carry their row count)."""
    return f"{item['key']} ({item['count']} rows)" if item["count"] is not None else item["key"]


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
            accept_rev: str | None = None, use_focus_gate: bool | None = None) -> dict:
    """Compare a design render against an app render; return the full result.

    The result dict carries `exit_code`, `verdict`, `report` (human text) and,
    once both sides load, `sections` / `overall` completeness and
    `accepted_n`. Two-sided or no output: a missing/unreadable/empty/
    sectionless side on EITHER end, an unresolved class-based hiding token,
    or an accept file that is not owner-authored or is malformed returns
    COULD_NOT_CHECK before any comparison runs. `use_focus_gate` is passed
    to `read_owner_authored`.
    """
    def early(code: int, report: str) -> dict:
        """Result for a verdict reached before any inventory comparison."""
        return {"exit_code": code, "verdict": _VERDICT_NAMES[code], "report": report}

    design = extract_side(design_path)
    if design is None:
        return early(COULD_NOT_CHECK, (
            f"COULD_NOT_CHECK: design side unreadable, empty, or has no "
            f"sections ({design_path!r}). Two-sided input is required — a "
            "one-sided read cannot certify parity."))
    app = extract_side(app_path)
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
    accept, err, accept_source = load_accept(accept_path, accept_rev, use_focus_gate)
    if accept is None:
        return early(COULD_NOT_CHECK, f"COULD_NOT_CHECK: {err} — acceptance cannot be verified.")

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

    sections, no_inventory = [], []
    tot_matched = tot_items = open_rows = accepted_n = 0
    for sec in design:
        sid, d_inv = sec["id"], sec["inventory"]
        entry = {"id": sid, "state": states[sid], "rows": []}
        a_sec = app_map.get(sid)
        if d_inv is None or (a_sec is not None and a_sec["inventory"] is None):
            no_inventory.append(sid)
            entry.update(design_items=None, matched=None, completeness_pct=None)
            sections.append(entry)
            continue
        if a_sec is None:
            diff = {"matched": 0, "total": len(d_inv), "rows": []}
        else:
            diff = diff_inventory(d_inv, a_sec["inventory"], sec["marked"] and a_sec["marked"])
        for row in diff["rows"]:
            hit = accept.get((sid, row["status"], _norm(row["item"]).casefold(), _norm(row["app"]) or "-"))
            row["accepted"] = hit is not None and hit["used"] < hit["count"]
            if row["accepted"]:
                hit["used"] += 1
                row.update(reason=hit["reason"], owner=hit["owner"])
                accepted_n += 1
            else:
                open_rows += 1
        tot_matched += diff["matched"]
        tot_items += diff["total"]
        entry.update(design_items=diff["total"], matched=diff["matched"],
                     completeness_pct=_pct(diff["matched"], diff["total"]), rows=diff["rows"])
        sections.append(entry)

    overall_known = not no_inventory
    overall = {"design_items": tot_items if overall_known else None,
               "matched": tot_matched if overall_known else None,
               "completeness_pct": _pct(tot_matched, tot_items) if overall_known else None}
    completeness = (f"{tot_matched}/{tot_items} design items matched ({_pct(tot_matched, tot_items)})"
                    if overall_known else "completeness unknown (a side carries no inventory)")

    body = []
    body += [f"missing: section '{sid}' — build it (absent from the app)." for sid in missing]
    body += [f"empty:   section '{sid}' — seed it (present but no data-item in the app)." for sid in empty]
    for entry in sections:
        if entry["design_items"] is None:
            body.append(f"section '{entry['id']}': inventory unavailable (a .json side has none).")
            continue
        body.append(f"section '{entry['id']}': {entry['matched']}/{entry['design_items']} design items "
                    f"matched ({entry['completeness_pct']}).")
        for row in entry["rows"]:
            detail = (f"{row['design']} -> {row['app']}" if row["status"] == "CHANGED"
                      else row["design"] or row["app"])
            tag = "ACCEPTED " + row["status"] if row["accepted"] else row["status"]
            suffix = f"  [{row['reason']}; {row['owner']}]" if row["accepted"] else ""
            body.append(f"  {tag:<24} {detail}{suffix}")
    info = []
    if extra:
        info.append("info: extra app section(s) beyond the design, kept as superset "
                    f"(not a failure): {', '.join(extra)}")
    stale = [f"{s}/{st}/{i} ({row['used']} of {row['count']} used)"
             for (s, st, i, _), row in accept.items() if row["used"] < row["count"]]
    if stale:
        info.append(f"info: accept row(s) covering fewer differences than their count (stale): {', '.join(stale)}")

    verdict = None
    if missing or empty or open_rows:
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
             f"{completeness}."),
            *body, _BASIS, *info]
    return {"exit_code": code, "verdict": verdict or _VERDICT_NAMES[code], "overall": overall,
            "accepted_n": accepted_n, "sections": sections,
            "section_gaps": {"missing": missing, "empty": empty},
            "extra_sections": extra, "report": "\n".join(report)}


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
        "coverage(media,icon,option,mask-count,broken)=ok accept(owner,count,pin,untrusted)=ok"
    )
    return 0


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
    finally:
        for key, val in saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val


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

    result = compare(args.design, args.app, args.accept, args.accept_rev)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else result["report"])
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
