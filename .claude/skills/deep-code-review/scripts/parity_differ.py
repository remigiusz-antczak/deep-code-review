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
or a similarity score. There is exactly one passing exit code (MATCH, 0) and
it requires both sides to be present and readable.

SIZE IS NEVER AN INPUT
----------------------
Size, height, width, bounding boxes, pixel counts, and every other geometric
measurement are NEVER inputs to the verdict. The parser does not read
`width`/`height` attributes or layout; it reads inline `style` only to skip
`display:none` / `visibility:hidden` subtrees. A taller, wider, or denser app
with an equal inventory is a MATCH; a same-size app missing one button is a
MISMATCH. Geometry belongs only to layout-defect checks (overlap, clipping,
viewport fit), never to a "complete" or "matches" verdict.

CONTRACT (fail-closed; every branch below is load-bearing, not cosmetic)
-------------------------------------------------------------------------
* MATCH (0) — the ONLY pass. Both sides present; every design section is
  present in the app; every design-populated section is populated in the app;
  and every matched section's inventory is equal, or each difference is a row
  in the owner-accepted deviations file (`--accept`).
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
  no sections; the `--accept` file is missing, unreadable, or has a row
  without all four fields; or a would-be MATCH rests on a side with no
  inventory (a `.json` section list). Never a score, never a pass.
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

ELEMENT INVENTORY (per section, HTML sides only)
------------------------------------------------
Items outside every `data-section`, and subtrees that are `hidden`,
`aria-hidden="true"`, `display:none`, `visibility:hidden`, or script/style/
template/noscript/head, are not inventoried. Each item is `kind:role:label`:
  heading   — h1..h6 or role=heading (aria-level, default 2): `heading:h2:Text`.
  control   — role + accessible label: button (incl. input button types and
              summary), link (a[href]), textbox/combobox/checkbox/radio/slider
              (input/select/textarea), tab, menuitem, and any element with an
              explicit interactive role. Label order: aria-labelledby,
              aria-label, <label for>/wrapping <label>, content text, value,
              alt, title, placeholder. An image inside a control is part of
              its label, not a separate item.
  image     — img (alt; alt="" is decorative and skipped), svg, role=img
              (aria-label, else <title>/text).
  list/table— one container item per list/table with its row count
              (`list:#1`, ordinal within the section), plus one
              `list-item:` / `table-row:` item per row labelled by its
              first-cell text (a list item's full text).
  state     — every `data-state="VALUE"` marker: `state:VALUE`.
  text      — every remaining visible text run, merged across inline tags
              and split at block boundaries.
Labels are whitespace-normalized and case-folded for comparison; order is
ignored (multiset). Text inside `data-sample` / `data-value` elements is
masked to one placeholder only when BOTH sides' section carries such a
marker — a one-sided marker cannot hide a difference. Leftover design/app
items are paired into CHANGED rows (same kind and label, different role;
then same kind and role, different label); the rest are MISSING_IN_APP /
EXTRA_IN_APP. Completeness = matched items / design items, per section and
overall — items, never pixels.

ACCEPTED DEVIATIONS (`--accept FILE`)
-------------------------------------
Tab-separated rows: `section<TAB>item<TAB>reason<TAB>owner-quote-or-commit`.
`item` is the row's item key as printed (design key for MISSING/CHANGED, app
key for EXTRA). Blank lines, `#` comments, and a `section` header row are
skipped. A row with any empty field fails closed (COULD_NOT_CHECK). An
accepted row still prints (ACCEPTED) and never counts as matched; an unused
row prints as info.

USAGE
-----
  parity_differ.py --design <file> --app <file> [--accept <tsv>] [--json]
  parity_differ.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from html.parser import HTMLParser

# The whole point of naming these instead of using bare ints: only MATCH is a
# pass, so any caller/CI step gating on "exit 0" cannot be fooled by a
# mismatch, an unseeded app, or a one-sided input silently returning 0.
MATCH = 0
MISMATCH = 1
USAGE_ERROR = 2
COULD_NOT_CHECK = 3
CANNOT_COMPARE = 4

_VERDICT_NAMES = {MATCH: "MATCH", MISMATCH: "MISMATCH", USAGE_ERROR: "USAGE_ERROR",
                  COULD_NOT_CHECK: "COULD_NOT_CHECK", CANNOT_COMPARE: "CANNOT_COMPARE"}

# Elements with no closing tag in HTML. Never pushed onto the open-tag stack,
# so a document full of bare `<img>`/`<input>`/... never desyncs it.
_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})
# Subtrees that never render visible inventory.
_SKIP_TAGS = frozenset({"script", "style", "template", "noscript", "head"})
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
_MASK_OPEN, _MASK_CLOSE = "", ""
_VALUE_TOKEN = "<value>"
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.IGNORECASE)


class _Frame:
    """One open element on the parser stack plus its inventory role."""

    __slots__ = (
        "capture",
        "cells",
        "container",
        "control",
        "hidden",
        "id",
        "idcap",
        "item",
        "kind",
        "masked",
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
        self.hidden = self.masked = self.notext = False
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
            record = {"id": sid, "items": 0, "empties": 0, "inv": [], "marked": False}
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
            if text.replace(_MASK_OPEN, "").replace(_MASK_CLOSE, "").strip():
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
        frame.hidden = bool(
            (parent and parent.hidden) or tag in _SKIP_TAGS or "hidden" in attr_map
            or (attr_map.get("aria-hidden") or "").lower() == "true"
            or _HIDDEN_STYLE.search(attr_map.get("style") or ""))
        own_mark = "data-sample" in attr_map or "data-value" in attr_map
        frame.masked = bool((parent and parent.masked) or own_mark)
        frame.notext = bool((parent and parent.notext) or tag in ("select", "textarea"))
        if tag in _BLOCK_TAGS or sid is not None:
            self._flush()
        if frame.hidden:
            return frame
        sec = frame.section
        if own_mark and sec in self._by_id:
            self._by_id[sec]["marked"] = True
        if attr_map.get("id"):
            frame.id, frame.idcap = attr_map["id"], []
        if attr_map.get("data-state"):
            self._emit(sec, "state", "", attr_map["data-state"])

        role = (attr_map.get("role") or "").strip().lower().split(" ")[0]
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
                "tag": tag, "text": "", "wrap": label_frame.item if label_frame else None}
        frame.kind, frame.control = "control", ctrl
        if tag not in _VOID_TAGS:
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
            if f.hidden:
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
        if frame.hidden:
            return
        text = "".join(frame.capture) if frame.capture is not None else ""
        if frame.idcap is not None:
            self._ids[frame.id] = "".join(frame.idcap)
        if frame.kind in ("heading", "image") and frame.item is not None:
            frame.item["label"] = frame.item.pop("aria", None) or text
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
        if top is None or top.hidden or top.notext:
            return
        text = f"{_MASK_OPEN}{data}{_MASK_CLOSE}" if top.masked else data
        if not self._feed_captures(text):
            if self._buf_section is None:
                self._buf_section = self._innermost_section()
            self._buf.append(text)

    def finish(self) -> None:
        """Finalize open frames and resolve deferred control labels."""
        while self._stack:
            self._finalize(self._stack.pop())
        self._flush()
        by_for = {lb["for"]: lb for lb in self._labels if lb["for"]}
        for ctrl in self._controls:
            attrs, item = ctrl["attrs"], ctrl["item"]
            candidates = []
            if attrs.get("aria-labelledby"):
                candidates.append(" ".join(self._ids.get(i, "") for i in attrs["aria-labelledby"].split()))
            candidates.append(attrs.get("aria-label"))
            if ctrl["tag"] in _FORM_FIELDS:
                for lb in (by_for.get(attrs.get("id") or ""), ctrl["wrap"]):
                    if lb is not None and lb["text"].strip():
                        lb["used"] = True
                        candidates.append(lb["text"])
            candidates += [ctrl["text"]]
            if ctrl["tag"] == "input":
                itype = (attrs.get("type") or "text").lower()
                candidates.append(attrs.get("value") or {"submit": "Submit", "reset": "Reset"}.get(itype))
                candidates.append(attrs.get("alt"))
            candidates += [attrs.get("title"), attrs.get("placeholder")]
            label = next((c for c in candidates if c and c.strip()), "")
            if item is not None:
                item["label"] = label
        for lb in self._labels:   # an orphan <label> is still visible text
            if not lb["used"] and lb["text"].strip():
                self._emit(lb["section"], "text", "", lb["text"])


def extract_side(path: str | None) -> list[dict] | None:
    """Return this side's ordered section records, or None if it cannot compare.

    Each record is `{"id", "populated", "inventory", "marked"}`; `inventory`
    is a list of raw items for an HTML side and None for a `.json` side
    (which carries no inventory). None for the whole side covers every
    fail-closed case in one place: no path given, file absent, unreadable,
    empty/whitespace-only, invalid JSON, or zero sections. A caller must
    treat None as COULD_NOT_CHECK, never as an empty-but-valid side.
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
                 "inventory": None, "marked": False}
                for row in data if isinstance(row, dict) and "id" in row]
        return rows or None

    parser = _SectionExtractor()
    parser.feed(raw)
    parser.close()
    parser.finish()
    if not parser.sections:
        return None
    return [{"id": s["id"], "populated": s["items"] > 0, "inventory": s["inv"],
             "marked": s["marked"]} for s in parser.sections]


def extract_sections(path: str | None) -> list[tuple[str, bool]] | None:
    """Return this side's ordered `[(section_id, populated), ...]`, or None.

    Section-level view of `extract_side` (same fail-closed None contract).
    """
    side = extract_side(path)
    return None if side is None else [(s["id"], s["populated"]) for s in side]


def _clean(label: str | None, mask: bool) -> str:
    """Whitespace-normalize a label, masking or unwrapping marked data values."""
    text = label or ""
    if mask:
        text = re.sub(f"{_MASK_OPEN}.*?{_MASK_CLOSE}", f" {_VALUE_TOKEN} ", text, flags=re.DOTALL)
        text = re.sub(rf"(?:{re.escape(_VALUE_TOKEN)}\s*)+", f"{_VALUE_TOKEN} ", text)
    text = text.replace(_MASK_OPEN, "").replace(_MASK_CLOSE, "")
    return " ".join(text.split())


def _prepare(inventory: list[dict], mask: bool) -> list[dict]:
    """Turn raw items into comparable `{kind, role, disp, cmp, count, key}` rows."""
    out = []
    for raw in inventory:
        disp = _clean(raw["label"], mask)
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
    compare by (kind, ordinal) and row count. Leftovers pair into CHANGED
    rows (same kind+label with a different role first, then same kind+role
    with a different label), the rest become MISSING_IN_APP / EXTRA_IN_APP.
    Pure function of the two inventories — no size or geometry input exists.
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


def load_accept(path: str | None) -> tuple[dict | None, str | None]:
    """Parse an owner-accepted deviations TSV into `{(section, item): row}`.

    Returns `(rows, None)` on success or `(None, error)` — fail closed on a
    missing/unreadable file or any row lacking one of its four non-empty
    fields (section, item, reason, owner-quote/commit). `path=None` means no
    file was given and yields an empty mapping.
    """
    if path is None:
        return {}, None
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"accept file unreadable ({path!r}: {exc.__class__.__name__})"
    rows: dict = {}
    first = True
    for n, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = [f.strip() for f in line.split("\t")]
        header, first = first and fields[0].lower() == "section", False
        if header:   # the first non-comment row may be a column header
            continue
        if len(fields) != 4 or not all(fields):
            return None, (f"accept file row {n} needs 4 non-empty tab-separated fields "
                          "(section, item, reason, owner-quote/commit)")
        key = (fields[0], " ".join(fields[1].split()).casefold())
        rows[key] = {"reason": fields[2], "owner": fields[3], "used": False}
    return rows, None


def _pct(matched: int, total: int) -> str:
    """Completeness as a percentage string; `n/a` when there is nothing to match."""
    return f"{100.0 * matched / total:.1f}%" if total else "n/a"


_PRECONDITION = (
    "precondition: both renders must share the same auth + data state "
    "(for gated sections: dev identity past sign-in on both sides, seeded) "
    "— a section gated behind sign-in reads as 'missing' on a signed-out "
    "render; confirm before building. This matched-state diff does not "
    "replace the signed-out default-surface check.")
_BASIS = ("basis: element inventory (headings, visible text, controls by role + label, images, "
          "list/table rows, data-state) — size, height, width, bounding boxes, and pixel "
          "counts are never inputs.")


def compare(design_path: str | None, app_path: str | None,
            accept_path: str | None = None) -> dict:
    """Compare a design render against an app render; return the full result.

    The result dict carries `exit_code`, `verdict`, `report` (human text) and,
    once both sides load, `sections` / `overall` completeness. Two-sided or no
    output: a missing/unreadable/empty/sectionless side on EITHER end, or a
    bad accept file, returns COULD_NOT_CHECK before any comparison runs.
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
    accept, err = load_accept(accept_path)
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
            hit = accept.get((sid, row["item"].casefold()))
            row["accepted"] = hit is not None
            if hit is not None:
                hit["used"] = True
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
    stale = [f"{s}/{i}" for (s, i), row in accept.items() if not row["used"]]
    if stale:
        info.append(f"info: accept row(s) matched no difference (stale): {', '.join(stale)}")

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
    else:
        code = MATCH
        accepted_note = f"; {accepted_n} owner-accepted deviation(s)" if accepted_n else ""
        report = [
            ("MATCH: every design section is present in the app, and every "
             "design-populated section is populated in the app; element inventory "
             f"{completeness}{accepted_note}."),
            *body, _BASIS, *info]
    return {"exit_code": code, "verdict": _VERDICT_NAMES[code], "overall": overall,
            "sections": sections, "section_gaps": {"missing": missing, "empty": empty},
            "extra_sections": extra, "report": "\n".join(report)}


def diff_sides(design_path: str | None, app_path: str | None,
               accept_path: str | None = None) -> tuple[int, str]:
    """Compare a design render against an app render; return (exit_code, report).

    Thin wrapper over `compare`; same fail-closed contract and exit codes.
    """
    result = compare(design_path, app_path, accept_path)
    return result["exit_code"], result["report"]


def _selftest() -> int:
    """Run the committed fixtures and assert the exact verdict per case.

    This is the tool's own proof that it fires on real input, not just that
    it parses: each case pins the exit code and required/forbidden report
    substrings, and the inventory cases pin the EXACT row set, so a future
    edit that quietly turns a fail-closed branch into a pass, drops an
    inventory kind, or lets size leak into the verdict breaks this loudly.
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
          must_have=("4 unaccepted", "size, height, width"), must_not=("aligned",))
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

    res = compare(inv_design, fx("inv_app_changed.html"), fx("inv_accept.tsv"))
    check("inventory-accepted", res["exit_code"], res["report"], MATCH,
          must_have=("1 owner-accepted", "ACCEPTED CHANGED"), must_not=("stale",))

    with tempfile.TemporaryDirectory() as tmp:
        def write(name: str, text: str) -> str:
            """Write one throwaway fixture into the temp dir; return its path."""
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            return path

        bad = write("bad.tsv", "overview\ttext:Welcome back, Jane Smith\t\tno owner\n")
        code, report = diff_sides(inv_design, fx("inv_app_changed.html"), bad)
        check("accept-malformed", code, report, COULD_NOT_CHECK, must_not=("MATCH:",))

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

    if failures:
        print("SELFTEST FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        "SELFTEST OK: match=0 mismatch=1 unseeded=4 refuse(design-absent)=3 "
        "refuse(app-absent)=3 inventory(missing)=1 inventory(taller)=0 "
        "inventory(changed)=1 inventory(accepted)=0 accept(malformed)=3 "
        "mask(one-sided)=1 icon-button-label=ok json(no-inventory)=3"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: `--selftest`, or `--design <f> --app <f>` (two-sided only)."""
    parser = argparse.ArgumentParser(
        description="Two-sided design<->app parity gate (sections + element inventory). "
                    "MATCH (exit 0) is the only pass; size is never an input."
    )
    parser.add_argument("--design", help="design render: HTML DOM snapshot or .json section list")
    parser.add_argument("--app", help="app render: HTML DOM snapshot or .json section list")
    parser.add_argument("--accept", help="owner-accepted deviations TSV: section, item, reason, owner-quote/commit")
    parser.add_argument("--json", action="store_true", help="print the full result as JSON (board posts)")
    parser.add_argument("--selftest", action="store_true", help="run the committed-fixture self-test")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if not args.design or not args.app:
        parser.error("--design and --app are both required (two-sided input, or no output)")
        return USAGE_ERROR  # pragma: no cover — parser.error() already exits(2)

    result = compare(args.design, args.app, args.accept)
    print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else result["report"])
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
