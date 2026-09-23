#!/usr/bin/env python3
"""feedback_ledger.py — one durable requirement ledger across every feedback source.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
An app often has to satisfy several requirement sources at once: feedback rows
exported from a survey tool as CSV, comments and notes in shared docs, action
items from meeting transcripts, and a design-tool export labelled "latest"
that does NOT carry all of that feedback. No lane can hold every source in its
context, so two failures repeat: a lane applies a piece of feedback, a later
lane re-aligns the screen to the "latest" design and silently OVERRIDES the
feedback the design never captured; or a piece of feedback is never applied at
all. This script keeps ONE ledger file that every lane reads instead of the
raw sources. The ledger, not any single source, is the requirement set; the
design export is one source among several.

THE MODEL (deterministic; the script never calls a model)
---------------------------------------------------------
Each ledger item is one requirement:
  id          stable 12-hex hash of normalized text + normalized target
  source      csv | doc | transcript | design (first source that reported it)
  source_ref  where in that source: spreadsheet row, comment id, timestamp
  date        YYYY-MM-DD; the newest date among all linked reports
  role        author ROLE only (e.g. "designer", "end user") — never a name
  target      "section" or "section/element"; the first segment must equal
              the section id used by the parity inventory (`data-section`)
  text        the requirement in words (email addresses are redacted)
  kind        add | change | remove | keep
  expect      the element key the requirement makes checkable, in
              parity_differ's item-key form `kind:role:label` or `kind:label`
              (e.g. `control:button:Export CSV`, `heading:h2:Reports`).
              For `remove` it is the element that must be absent.
  was         optional; for `change`, the element key being replaced
Transcripts and doc comments arrive already extracted to JSON/CSV by an agent
or a person; this script only normalizes, links, and compares.

Dedupe (cross-source linking): an incoming item joins an existing item when
it has the same id, OR the same normalized target and either near-identical
normalized text (difflib ratio >= 0.9) or the same (kind, expect, was). The
report is appended to the item's `refs` (so every source stays traceable) and
the incoming id is kept as an alias. Re-ingesting the same source row is a
no-op (idempotent).

Superseding (same element, several requests): items whose full target has an
element part ("section/element") and is identical are about the same thing.
The newest date wins and older items are SUPERSEDED. Items on the same date
cannot be ordered, so they are a feedback-vs-feedback conflict for the owner.
An owner decision (`decide --choose feedback`) makes its item win over every
item dated on or before the decision date; an item dated AFTER the decision is
new information and re-opens a conflict rather than silently winning. A
`design` or `other` answer lapses the same way when a source re-raises the
item after the decision date. Section-only targets never supersede each other.

COMMANDS
--------
  ingest --source csv|doc|transcript|design --file F [--map mapping.json]
      F is .csv (header row) or .json (a list of objects, or {"items": [...]}).
      The mapping maps ledger field -> source column; a value starting with
      "=" is a constant (e.g. {"kind": "=add"}). Required per row: text,
      target, kind, expect, date. Any bad row rejects the whole file and
      leaves the ledger untouched.
  delta --design F [--design-date YYYY-MM-DD]
      Classify every item against the latest design inventory:
      IN_DESIGN, NOT_IN_DESIGN (the design never captured it),
      CONFLICTS_WITH_DESIGN (the design shows the `was` element, or still
      shows what the item removes), or SUPERSEDED.
  status --app F [--date YYYY-MM-DD]
      Per live item: IMPLEMENTED, PENDING, or REGRESSED (was implemented at
      an earlier status run, now missing).
  conflicts
      Only the items needing an owner decision, each as a question of at
      most two lines with both options, dates, and source refs.
  decide --id ID --choose feedback|design|other --quote "<owner words>" --date D
      Records the OWNER's answer verbatim. The agent asks; it never decides.
      `design` declines the item; `other` closes it (ingest the owner's
      instruction as a new item).
  accept-file --design D --app A [--out F]
      Drafts parity_differ's 7-field accepted-deviations TSV
      (`section status item app-value count reason owner-quote-or-commit`)
      for every IMPLEMENTED item that intentionally deviates from the design
      (NOT_IN_DESIGN, or CONFLICTS_WITH_DESIGN decided `feedback`). D and A
      must be the HTML renders `delta` and `status` last read (sha256
      checked). The rows are the parity differ's own printed differences
      (its public `compare` result, the same dict `--json` prints), so
      section, item, and app-value are exact and `count` is the number of
      identical rows. A row is emitted only when an eligible item in its
      section covers it: EXTRA_IN_APP of the item's `expect` (add, keep,
      change); MISSING_IN_APP of its `expect` (remove) or `was` (change);
      CHANGED from `was` to `expect` (change). Every other difference stays
      open — the differ's work queue. The file is INERT until the OWNER
      reviews and commits it: parity_differ reads `--accept` from a
      committed blob whose every commit is owner-authored (no
      `Co-authored-by:` trailer). The ledger never self-authorizes: `decide`
      records the owner's words, and the owner commits the accept file.
      Once committed, it is the override guard: re-aligning to the design
      can no longer undo decided feedback.

INVENTORY INPUT (`--design` / `--app`)
--------------------------------------
  .json : parity_differ's JSON section list (`[{"id", "populated"}]`, or
          {"sections": [...]}) where each section also carries `inventory`,
          a list of item keys in parity_differ's `kind:role:label` form.
  HTML  : a rendered export read through the sibling
          `deep-code-review/scripts/parity_differ.py` public
          `inventory_keys` (imported, never copied; no private helper). An
          older sibling without it yields sections only; an item on such a
          section fails closed (exit 2), as does a class-based hiding token
          with no computed-visibility marker (presence is not guessed).

FILES
-----
  --ledger PATH (default `.claude/feedback-ledger.json`) plus a
  human-readable companion `<same name>.md`, rewritten on every change.
  Writes are atomic (temp file + rename).

EXIT CODES (fail closed)
------------------------
  0  clean for the command run
  1  open owner conflicts (delta, conflicts, accept-file), pending or
     regressed items (status), or an accept file that may be incomplete
     (an eligible item with no covering parity row)
  2  input error: missing/unreadable/malformed file, bad row, unknown id,
     empty owner quote, missing ledger, an inventory with no element data,
     or accept-file renders that differ from the ones delta/status read or
     that the parity differ cannot compare

USAGE
-----
  feedback_ledger.py [--ledger PATH] <command> [options]
  feedback_ledger.py --selftest
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import difflib
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path

# Loading the sibling parity_differ must not litter __pycache__ into a
# shipped, checksummed skill tree.
sys.dont_write_bytecode = True

CLEAN, OPEN, INPUT_ERROR = 0, 1, 2
DEFAULT_LEDGER = ".claude/feedback-ledger.json"
PARITY_DIFFER = Path(__file__).resolve().parents[2] / "deep-code-review" / "scripts" / "parity_differ.py"
SCHEMA = 1
SOURCES = ("csv", "doc", "transcript", "design")
KINDS = ("add", "change", "remove", "keep")
CHOICES = ("feedback", "design", "other")
FIELDS = ("text", "target", "kind", "expect", "was", "date", "role", "source_ref")
REQUIRED = ("text", "target", "kind", "expect", "date")
NEAR_DUP_RATIO = 0.9
# Every key the commands read from a stored item; a ledger item missing one fails closed.
_ITEM_KEYS = ("id", "target", "kind", "expect", "was", "text", "date", "refs", "aliases", "decisions")

IN_DESIGN = "IN_DESIGN"
NOT_IN_DESIGN = "NOT_IN_DESIGN"
CONFLICTS = "CONFLICTS_WITH_DESIGN"
SUPERSEDED = "SUPERSEDED"
IMPLEMENTED, PENDING, REGRESSED = "IMPLEMENTED", "PENDING", "REGRESSED"

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[T ][0-9:.]+(?:Z|[+-]\d{2}:?\d{2})?)?$")


class InputError(Exception):
    """Malformed or missing input; the caller exits 2 and writes nothing."""


# ---------------------------------------------------------------- normalizing

def norm_text(text: str) -> str:
    """Case-fold, turn every non-alphanumeric run into one space, and trim.

    Used for ids and near-duplicate matching, so punctuation, casing, and
    spacing differences between sources do not create separate items.
    """
    return " ".join(re.sub(r"[^0-9a-z]+", " ", text.casefold()).split())


def norm_target(target: str) -> str:
    """Normalize a `section[/element...]` target; raise InputError when empty.

    Each segment is whitespace-collapsed and case-folded. An empty segment
    (e.g. "reports//x" or "/x") is rejected rather than guessed at.
    """
    parts = [" ".join(p.split()).casefold() for p in target.split("/")]
    if not parts or any(not p for p in parts):
        raise InputError(f"target {target!r} has an empty segment")
    return "/".join(parts)


def norm_key(key: str) -> str:
    """Normalize a parity item key the way parity_differ compares labels."""
    return " ".join(key.split()).casefold()


def item_id(text: str, target: str) -> str:
    """Stable 12-hex id from normalized text + normalized target."""
    raw = f"{norm_text(text)}|{norm_target(target)}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def parse_date(value: str, where: str) -> str:
    """Return the YYYY-MM-DD part of an ISO date/datetime, or raise InputError."""
    match = _DATE.match(value.strip())
    if not match:
        raise InputError(f"{where}: date {value!r} is not ISO YYYY-MM-DD")
    try:
        _date.fromisoformat(match.group(1))
    except ValueError as exc:
        raise InputError(f"{where}: date {value!r} is not a real date") from exc
    return match.group(1)


def redact(text: str) -> str:
    """Replace email addresses with `[email]`; the ledger records roles, not people."""
    return _EMAIL.sub("[email]", text)


def one_line(text: str, limit: int = 0) -> str:
    """Collapse whitespace (tabs/newlines included); optionally truncate with '...'."""
    flat = " ".join(str(text).split())
    return flat if not limit or len(flat) <= limit else flat[: limit - 3] + "..."


# ------------------------------------------------------------------- ingest

def load_mapping(path: str | None) -> dict:
    """Read a field mapping {ledger_field: source_column | "=constant"}.

    Unknown ledger fields or non-string values fail closed. No path → {}.
    """
    if not path:
        return {}
    data = _read_json(path, "mapping")
    if not isinstance(data, dict):
        raise InputError("mapping must be a JSON object {ledger_field: column}")
    for key, value in data.items():
        if key not in FIELDS:
            raise InputError(f"mapping: unknown ledger field {key!r} (allowed: {', '.join(FIELDS)})")
        if not isinstance(value, str) or not value:
            raise InputError(f"mapping: value for {key!r} must be a non-empty string")
    return data


def _read_json(path: str, label: str):
    """Load JSON from `path`; any read/parse failure is an InputError."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise InputError(f"{label} file not found: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"{label} file unreadable or not JSON: {path} ({exc.__class__.__name__})") from exc


def load_rows(path: str) -> list[tuple[str, dict]]:
    """Read source rows as `[(default_source_ref, row_dict), ...]`.

    `.csv`: header row required; the default ref is the spreadsheet row
    number ("row 2" is the first data row). `.json`: a list of objects or
    {"items": [...]}; the default ref is "item N" (1-based). Other extensions,
    an empty file, or a non-object row fail closed.
    """
    lower = path.lower()
    if lower.endswith(".csv"):
        try:
            with open(path, encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh)
                rows = [(f"row {n}", dict(r)) for n, r in enumerate(reader, start=2)]
                header = reader.fieldnames
        except FileNotFoundError as exc:
            raise InputError(f"source file not found: {path}") from exc
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            raise InputError(f"source CSV unreadable: {path} ({exc.__class__.__name__})") from exc
        if not header:
            raise InputError(f"source CSV has no header row: {path}")
    elif lower.endswith(".json"):
        data = _read_json(path, "source")
        if isinstance(data, dict):
            data = data.get("items")
        if not isinstance(data, list):
            raise InputError("source JSON must be a list of objects or {\"items\": [...]}")
        rows = []
        for n, row in enumerate(data, start=1):
            if not isinstance(row, dict):
                raise InputError(f"source JSON item {n} is not an object")
            rows.append((f"item {n}", row))
    else:
        raise InputError(f"source file must be .csv or .json: {path}")
    if not rows:
        raise InputError(f"source file has no rows: {path}")
    return rows


def normalize_row(raw: dict, mapping: dict, source: str, default_ref: str) -> dict:
    """Turn one source row into a ledger report; raise InputError on any gap.

    Field lookup: the mapping's column (or "=constant"), else the ledger field
    name itself. Required fields must be non-empty; `kind` must be one of
    KINDS; `date` must be ISO. Names are never read — only `role`.
    """
    def get(field: str) -> str:
        """Resolve one ledger field from the row via the mapping."""
        spec = mapping.get(field, field)
        if spec.startswith("="):
            return spec[1:].strip()
        value = raw.get(spec)
        return "" if value is None else str(value).strip()

    ref = get("source_ref") or default_ref
    where = f"{source} {ref}"
    for field in REQUIRED:
        if not get(field):
            raise InputError(f"{where}: missing required field {field!r}")
    kind = get("kind").casefold()
    if kind not in KINDS:
        raise InputError(f"{where}: kind {get('kind')!r} not one of {', '.join(KINDS)}")
    target = " ".join(get("target").split())
    norm_target(target)  # validates
    text = redact(one_line(get("text")))
    return {
        "id": item_id(text, target),
        "source": source,
        "source_ref": one_line(ref),
        "date": parse_date(get("date"), where),
        "role": redact(one_line(get("role"))) or "unspecified",
        "target": target,
        "text": text,
        "kind": kind,
        "expect": one_line(get("expect")),
        "was": one_line(get("was")),
    }


def _same_requirement(item: dict, new: dict) -> bool:
    """True when `new` restates `item` (same target + near-same text or same anchor)."""
    if norm_target(item["target"]) != norm_target(new["target"]):
        return False
    if difflib.SequenceMatcher(None, norm_text(item["text"]), norm_text(new["text"])).ratio() >= NEAR_DUP_RATIO:
        return True
    return (item["kind"], norm_key(item["expect"]), norm_key(item["was"])) == (
        new["kind"], norm_key(new["expect"]), norm_key(new["was"]))


def merge_report(ledger: dict, new: dict) -> str:
    """Add one normalized report to the ledger; return "new", "linked", or "present".

    Links to an existing item by id/alias or by `_same_requirement`; a report
    whose (source, source_ref) is already recorded on that item is a no-op.
    """
    ref = {k: new[k] for k in ("source", "source_ref", "date", "role", "text")}
    for item in ledger["items"]:
        if item["id"] == new["id"] or new["id"] in item["aliases"] or _same_requirement(item, new):
            if any(r["source"] == ref["source"] and r["source_ref"] == ref["source_ref"] for r in item["refs"]):
                return "present"
            item["refs"].append(ref)
            item["date"] = max(item["date"], ref["date"])
            if new["id"] != item["id"] and new["id"] not in item["aliases"]:
                item["aliases"].append(new["id"])
            return "linked"
    ledger["items"].append({
        **new, "refs": [ref], "aliases": [], "design_state": None, "app_state": None,
        "ever_implemented": False, "implemented_on": None, "decisions": [],
    })
    return "new"


# ------------------------------------------------------------------- ledger

def empty_ledger() -> dict:
    """A new, empty ledger document."""
    return {"schema": SCHEMA, "items": [], "design": None, "app": None}


def load_ledger(path: str, create: bool = False) -> dict:
    """Load and shape-check the ledger; a missing file is an error unless `create`.

    The path must end in `.json`: the markdown companion is written beside it
    with a `.md` suffix, so any other suffix could make the render overwrite
    the ledger itself.
    """
    if not path.lower().endswith(".json"):
        raise InputError(f"ledger path must end in .json: {path}")
    if not os.path.exists(path):
        if create:
            return empty_ledger()
        raise InputError(f"ledger not found: {path} (run ingest first)")
    data = _read_json(path, "ledger")
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or not isinstance(data.get("items"), list):
        raise InputError(f"ledger {path} has an unknown shape or schema (expected schema {SCHEMA})")
    for item in data["items"]:
        if not isinstance(item, dict) or not all(k in item for k in _ITEM_KEYS):
            raise InputError(f"ledger {path} has a malformed item")
    return data


def _atomic_write(path: str, text: str) -> None:
    """Write `text` to `path` via a temp file in the same dir + os.replace."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".tmp-", suffix=os.path.basename(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def companion_path(path: str) -> str:
    """The human-readable render next to the ledger (`.json` → `.md`)."""
    return str(Path(path).with_suffix(".md"))


def save_ledger(path: str, ledger: dict) -> None:
    """Persist the ledger JSON and rewrite its markdown companion."""
    _atomic_write(path, json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
    _atomic_write(companion_path(path), render_markdown(ledger))


def find_item(ledger: dict, ident: str) -> dict:
    """Return the item whose id or alias is `ident`; raise InputError if none."""
    for item in ledger["items"]:
        if item["id"] == ident or ident in item.get("aliases", []):
            return item
    raise InputError(f"no ledger item with id {ident!r}")


def latest_decision(item: dict) -> dict | None:
    """The item's most recent owner decision, or None."""
    return item["decisions"][-1] if item.get("decisions") else None


def effective_decision(item: dict) -> dict | None:
    """The latest owner decision that still governs the item, or None.

    A `design` or `other` answer lapses when a source re-raises the item
    after the decision date (the item's newest report is newer), so a
    declined request raised again in a later meeting is asked again instead
    of silently vanishing. A `feedback` answer never lapses this way: a later
    restatement agrees with it.
    """
    dec = latest_decision(item)
    if dec and dec["choose"] != "feedback" and item["date"] > dec["date"]:
        return None
    return dec


# ------------------------------------------------------------------ resolve

def resolve(ledger: dict) -> dict:
    """Compute each item's lifecycle: {id: {"state", "by", "peers"}}.

    state is ACTIVE, SUPERSEDED, DECLINED (owner chose the design), or CLOSED
    (owner chose other). `peers` is the list of ids in an open
    feedback-vs-feedback conflict with this item (empty when none). Pure
    function of items + decisions; see the module docstring for the rules.
    """
    out = {}
    groups: dict[str, list[dict]] = {}
    for item in ledger["items"]:
        dec = effective_decision(item)
        state = {"design": "DECLINED", "other": "CLOSED"}.get(dec["choose"] if dec else "", "ACTIVE")
        out[item["id"]] = {"state": state, "by": None, "peers": []}
        target = norm_target(item["target"])
        if state == "ACTIVE" and "/" in target:
            groups.setdefault(target, []).append(item)
    for members in groups.values():
        if len(members) < 2:
            continue
        decided = [m for m in members if (effective_decision(m) or {}).get("choose") == "feedback"]
        if decided:
            winner = max(decided, key=lambda m: effective_decision(m)["date"])
            cutoff = effective_decision(winner)["date"]
            contenders = [winner] + [m for m in members if m is not winner and m["date"] > cutoff]
        else:
            newest = max(m["date"] for m in members)
            contenders = [m for m in members if m["date"] == newest]
            winner = contenders[0]
        for m in members:
            if m not in contenders:
                out[m["id"]].update(state="SUPERSEDED", by=winner["id"])
        if len(contenders) > 1:
            for m in contenders:
                out[m["id"]]["peers"] = [c["id"] for c in contenders if c is not m]
    return out


def open_conflicts(ledger: dict, life: dict) -> tuple[list[dict], list[list[dict]]]:
    """Return (undecided design conflicts, feedback-vs-feedback groups)."""
    design = [i for i in ledger["items"] if life[i["id"]]["state"] == "ACTIVE"
              and not life[i["id"]]["peers"] and i.get("design_state") == CONFLICTS
              and not effective_decision(i)]
    seen, ff = set(), []
    for item in ledger["items"]:
        peers = life[item["id"]]["peers"]
        if peers and item["id"] not in seen:
            group = [item] + [find_item(ledger, p) for p in peers]
            seen.update(g["id"] for g in group)
            ff.append(group)
    return design, ff


# --------------------------------------------------------------- inventory

def load_parity_differ():
    """Import deep-code-review's `parity_differ.py` from the sibling skill dir.

    Returns the module, or None when absent (callers exit 2). Path:
    `<skills-root>/deep-code-review/scripts/parity_differ.py`, the same host
    root this script was installed into. No side effect beyond the import.
    """
    path = PARITY_DIFFER
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("parity_differ", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_inventory(path: str, label: str, ids: dict | None = None) -> dict:
    """Read a design/app inventory as {normalized section id: set(keys) | None}.

    None for a section means "present, but no element inventory" — any item
    that needs it fails closed. See INVENTORY INPUT in the module docstring.
    When `ids` is given it is filled with {normalized id: id as exported}, so
    the accept file can name a section exactly as the parity differ sees it.
    """
    if not os.path.isfile(path):
        raise InputError(f"{label} inventory not found: {path}")
    if path.lower().endswith(".json"):
        data = _read_json(path, f"{label} inventory")
        if isinstance(data, dict):
            data = data.get("sections")
        if not isinstance(data, list):
            raise InputError(f"{label} inventory must be a section list or {{\"sections\": [...]}}")
        out = {}
        for row in data:
            if not isinstance(row, dict) or "id" not in row:
                raise InputError(f"{label} inventory has a section without an id")
            inv = row.get("inventory")
            if inv is not None and not (isinstance(inv, list) and all(isinstance(k, str) for k in inv)):
                raise InputError(f"{label} inventory section {row['id']!r}: inventory must be a list of strings")
            out[norm_key(str(row["id"]))] = None if inv is None else {norm_key(k) for k in inv}
            if ids is not None:
                ids[norm_key(str(row["id"]))] = str(row["id"])
    else:
        pd = load_parity_differ()
        if pd is None:
            raise InputError("sibling deep-code-review/scripts/parity_differ.py not found (fail closed)")
        if hasattr(pd, "inventory_keys"):
            side = pd.inventory_keys(path)
            if side is None:
                raise InputError(f"{label} export unreadable or has no data-section markers: {path}")
            hidden = [f"{s['id']}: {u}" for s in side for u in s["unresolved"]]
            if hidden:
                raise InputError(f"{label} export hides elements by class with no data-visible marker "
                                 f"({'; '.join(hidden[:3])}); re-export with computed visibility")
            out = {norm_key(s["id"]): None if s["items"] is None else {norm_key(k) for k in s["items"]}
                   for s in side}
            if ids is not None:
                ids.update({norm_key(s["id"]): s["id"] for s in side})
        else:
            sections = pd.extract_sections(path)
            if sections is None:
                raise InputError(f"{label} export unreadable or has no data-section markers: {path}")
            out = {norm_key(sid): None for sid, _populated in sections}
            if ids is not None:
                ids.update({norm_key(sid): sid for sid, _populated in sections})
    if not out:
        raise InputError(f"{label} inventory has no sections: {path}")
    return out


def _has(inv: dict, item: dict, key: str, label: str) -> bool:
    """True when the item's section in `inv` holds element `key`; fail closed on no inventory."""
    section = norm_target(item["target"]).split("/")[0]
    if section not in inv:
        return False
    keys = inv[section]
    if keys is None:
        raise InputError(f"{label} section {section!r} carries no element inventory; "
                         "export a rendered HTML DOM snapshot or a JSON inventory")
    return norm_key(key) in keys


def _file_meta(path: str, when: str | None) -> dict:
    """Identity of a compared inventory: basename, sha256, and date."""
    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    return {"file": os.path.basename(path), "sha256": digest, "date": when}


# ----------------------------------------------------------------- commands

def cmd_ingest(ledger_path: str, source: str, file: str, map_path: str | None) -> int:
    """Normalize and merge one source file; the whole file or nothing."""
    ledger = load_ledger(ledger_path, create=True)
    mapping = load_mapping(map_path)
    reports = [normalize_row(raw, mapping, source, ref) for ref, raw in load_rows(file)]
    tally = {"new": 0, "linked": 0, "present": 0}
    for rep in reports:
        tally[merge_report(ledger, rep)] += 1
    save_ledger(ledger_path, ledger)
    print(f"ingested {len(reports)} {source} row(s): {tally['new']} new item(s), "
          f"{tally['linked']} linked to existing item(s), {tally['present']} already recorded.")
    return CLEAN


def cmd_delta(ledger_path: str, design: str, design_date: str | None) -> int:
    """Classify every item against the latest design inventory."""
    ledger = load_ledger(ledger_path)
    when = parse_date(design_date, "--design-date") if design_date else None
    ids: dict = {}
    inv = load_inventory(design, "design", ids)
    life = resolve(ledger)
    for item in ledger["items"]:
        item["section"] = ids.get(norm_target(item["target"]).split("/")[0])
        if life[item["id"]]["state"] == "SUPERSEDED":
            item["design_state"] = SUPERSEDED
            continue
        if item["kind"] == "remove":
            state = CONFLICTS if _has(inv, item, item["expect"], "design") else IN_DESIGN
        elif _has(inv, item, item["expect"], "design"):
            state = IN_DESIGN
        elif item["kind"] == "change" and item["was"] and _has(inv, item, item["was"], "design"):
            state = CONFLICTS
        else:
            state = NOT_IN_DESIGN
        item["design_state"] = state
    ledger["design"] = _file_meta(design, when)
    save_ledger(ledger_path, ledger)
    for item in ledger["items"]:
        note = _life_note(item, life)
        print(f"{item['design_state']:<22} {item['id']}  {item['target']}  — {one_line(item['text'], 70)}{note}")
    design_open, ff = open_conflicts(ledger, life)
    counts = {s: sum(1 for i in ledger["items"] if i["design_state"] == s)
              for s in (IN_DESIGN, NOT_IN_DESIGN, CONFLICTS, SUPERSEDED)}
    print("delta: " + ", ".join(f"{v} {k}" for k, v in counts.items())
          + f"; {len(design_open) + len(ff)} open owner decision(s).")
    return OPEN if design_open or ff else CLEAN


def _life_note(item: dict, life: dict) -> str:
    """Suffix describing supersession, owner decisions, or a peer conflict."""
    info = life[item["id"]]
    dec = effective_decision(item)
    lapsed = latest_decision(item) if dec is None else None
    if info["state"] == "SUPERSEDED":
        return f"  [superseded by {info['by']}]"
    if info["state"] in ("DECLINED", "CLOSED"):
        return f"  [owner chose {dec['choose']} on {dec['date']}]"
    if info["peers"]:
        return f"  [conflicts with feedback {', '.join(info['peers'])}]"
    if dec:
        return f"  [owner chose {dec['choose']} on {dec['date']}]"
    if lapsed:
        return f"  [re-raised after owner chose {lapsed['choose']} on {lapsed['date']}]"
    return ""


def cmd_status(ledger_path: str, app: str, today: str | None) -> int:
    """Check every live item against the app inventory; detect regressions."""
    ledger = load_ledger(ledger_path)
    when = parse_date(today, "--date") if today else datetime.now(timezone.utc).date().isoformat()
    inv = load_inventory(app, "app")
    life = resolve(ledger)
    for item in ledger["items"]:
        if life[item["id"]]["state"] != "ACTIVE":
            item["app_state"] = None
            continue
        present = _has(inv, item, item["expect"], "app")
        done = not present if item["kind"] == "remove" else present
        if done:
            item["app_state"] = IMPLEMENTED
            if not item.get("ever_implemented"):
                item["ever_implemented"], item["implemented_on"] = True, when
        else:
            item["app_state"] = REGRESSED if item.get("ever_implemented") else PENDING
    ledger["app"] = _file_meta(app, when)
    save_ledger(ledger_path, ledger)
    counts = {IMPLEMENTED: 0, PENDING: 0, REGRESSED: 0}
    for item in ledger["items"]:
        state = item["app_state"]
        if state is None:
            print(f"{'closed':<12} {item['id']}  {item['target']}{_life_note(item, life)}")
            continue
        counts[state] += 1
        print(f"{state:<12} {item['id']}  {item['target']}  — {one_line(item['text'], 70)}")
    print("status: " + ", ".join(f"{v} {k}" for k, v in counts.items()) + ".")
    return OPEN if counts[PENDING] or counts[REGRESSED] else CLEAN


def _ref(item: dict) -> str:
    """`source source_ref, date` for the item's newest report."""
    newest = max(item["refs"], key=lambda r: r["date"])
    return f"{newest['source']} {newest['source_ref']}, {newest['date']}"


def conflict_questions(ledger: dict) -> tuple[list[str], int]:
    """Build the owner questions (<= 2 lines each) and count unclassified items."""
    life = resolve(ledger)
    design_open, ff = open_conflicts(ledger, life)
    design_meta = ledger.get("design") or {}
    design_when = design_meta.get("date") or f"export {design_meta.get('sha256', '')[:8] or 'unknown'}"
    lines, n = [], 0
    for item in design_open:
        n += 1
        shown = item["was"] if item["kind"] == "change" else item["expect"]
        lines.append(f"Q{n} [{item['id']}] {item['target']}: design ({design_when}) shows \"{shown}\"; "
                     f"feedback ({_ref(item)}) says {item['kind']} \"{item['expect']}\": "
                     f"\"{one_line(item['text'], 60)}\".")
        lines.append(f"    Keep feedback or design? Record: decide --id {item['id']} "
                     "--choose feedback|design|other --quote \"<owner words>\" --date YYYY-MM-DD")
    for group in ff:
        n += 1
        sides = " vs ".join(f"[{g['id']}] \"{one_line(g['text'], 50)}\" ({_ref(g)})" for g in group)
        lines.append(f"Q{n} {group[0]['target']}: {sides} — same date, or raised after an owner decision.")
        lines.append("    Which stands? Record on the winner: decide --id <winner> --choose feedback "
                     "--quote \"<owner words>\" --date YYYY-MM-DD")
    unclassified = sum(1 for i in ledger["items"] if life[i["id"]]["state"] == "ACTIVE"
                       and i.get("design_state") is None)
    return lines, unclassified


def cmd_conflicts(ledger_path: str) -> int:
    """Print only the items that need an owner decision."""
    ledger = load_ledger(ledger_path)
    lines, unclassified = conflict_questions(ledger)
    for line in lines:
        print(line)
    if unclassified:
        print(f"note: {unclassified} item(s) not yet compared with a design — run delta; "
              "their design conflicts are unknown.")
    if not lines and not unclassified:
        print("conflicts: none open.")
    return OPEN if lines or unclassified else CLEAN


def cmd_decide(ledger_path: str, ident: str, choose: str, quote: str, when: str) -> int:
    """Record the owner's answer verbatim on one item (never the agent's own call)."""
    ledger = load_ledger(ledger_path)
    item = find_item(ledger, ident)
    quote = redact(one_line(quote))
    if not quote:
        raise InputError("--quote must carry the owner's own words (empty quote refused)")
    item["decisions"].append({"choose": choose, "quote": quote, "date": parse_date(when, "--date")})
    save_ledger(ledger_path, ledger)
    print(f"recorded owner decision on {item['id']}: {choose} ({item['decisions'][-1]['date']}).")
    return CLEAN


def _deviating(ledger: dict) -> list[tuple[dict, dict | None]]:
    """(item, owner decision) for IMPLEMENTED items that deliberately deviate from the design.

    Eligible: ACTIVE with no peer conflict, and NOT_IN_DESIGN or
    CONFLICTS_WITH_DESIGN decided `feedback` (decision None otherwise).
    """
    life = resolve(ledger)
    out = []
    for item in ledger["items"]:
        dec = effective_decision(item)
        if life[item["id"]]["state"] != "ACTIVE" or life[item["id"]]["peers"]:
            continue
        if item.get("app_state") != IMPLEMENTED:
            continue
        decided = item.get("design_state") == CONFLICTS and dec and dec["choose"] == "feedback"
        if item.get("design_state") == NOT_IN_DESIGN or decided:
            out.append((item, dec if decided else None))
    return out


def _covers(item: dict, row: dict) -> bool:
    """True when parity row `row` is exactly the deviation `item` asks for (see accept-file)."""
    status, exp, was = row["status"], norm_key(item["expect"]), norm_key(item["was"] or "")
    if status == "EXTRA_IN_APP":
        return item["kind"] != "remove" and norm_key(row["item"]) == exp
    if status == "MISSING_IN_APP":
        return norm_key(row["item"]) == (exp if item["kind"] == "remove" else
                                         was if item["kind"] == "change" and was else None)
    return (status == "CHANGED" and item["kind"] == "change" and bool(was)
            and norm_key(row["design"] or "") == was and norm_key(row["app"] or "") == exp)


def accept_rows(ledger: dict, result: dict) -> tuple[list[list[str]], list[str], int]:
    """7-field accept rows from a parity result; plus uncovered items and open-row count.

    `result` is parity_differ's public `compare` dict (what `--json` prints).
    Only rows it printed are emitted, so section, item, and app-value are
    exact; identical rows (keyed as the differ keys them: item case-folded,
    app-value whitespace-collapsed) fold into one row with their count.
    Returns (rows, ids of eligible items no row matched, rows left open).
    Pure: reads the ledger and result, writes nothing.
    """
    by_section: dict = {}
    for item, dec in _deviating(ledger):
        by_section.setdefault(norm_target(item["target"]).split("/")[0], []).append((item, dec))
    groups: dict = {}
    covered_ids, open_rows = set(), 0
    for sec in result.get("sections") or []:
        for row in sec.get("rows") or []:
            hit = next(((it, dec) for it, dec in by_section.get(norm_key(sec["id"]), ())
                        if _covers(it, row)), None)
            if hit is None:
                open_rows += 1
                continue
            item, dec = hit
            covered_ids.add(item["id"])
            app = row["app"] or "-"
            key = (sec["id"], row["status"], norm_key(row["item"]), one_line(app))
            if key in groups:
                groups[key][4] += 1
                continue
            reason = one_line(f"feedback {item['id']}: {item['kind']} — {item['text']} ({_ref(item)})", 200)
            owner = (one_line(f"owner {dec['date']}: \"{dec['quote']}\"") if dec
                     else one_line(f"requirement source {_ref(item)}; the design never captured it"))
            groups[key] = [sec["id"], row["status"], row["item"], app, 1, reason, owner]
    rows = [[str(v) for v in g] for g in groups.values()]
    uncovered = [it["id"] for group in by_section.values() for it, _ in group if it["id"] not in covered_ids]
    return rows, uncovered, open_rows


def _check_render(ledger: dict, which: str, path: str) -> None:
    """Fail closed unless `path` is the exact render the last delta/status read."""
    meta = ledger.get(which)
    if not meta:
        raise InputError("run delta (design) and status (app) before accept-file")
    if not os.path.isfile(path):
        raise InputError(f"{which} render not found: {path}")
    if _file_meta(path, None)["sha256"] != meta["sha256"]:
        raise InputError(f"--{which} {path} is not the render the last "
                         f"{'delta' if which == 'design' else 'status'} read "
                         f"(sha256 {meta['sha256'][:12]}); re-run it on this file first")


def cmd_accept_file(ledger_path: str, design: str, app: str, out: str | None) -> int:
    """Draft parity_differ's 7-field accept TSV; inert until the owner commits it."""
    ledger = load_ledger(ledger_path)
    _check_render(ledger, "design", design)
    _check_render(ledger, "app", app)
    pd = load_parity_differ()
    if pd is None or not hasattr(pd, "compare"):
        raise InputError("sibling deep-code-review/scripts/parity_differ.py with compare() not found (fail closed)")
    result = pd.compare(design, app)
    if result.get("verdict") not in ("MATCH", "MISMATCH") or "sections" not in result:
        first = (result.get("report") or "").splitlines()[:1]
        raise InputError(f"parity differ could not compare the renders ({result.get('verdict')}): "
                         f"{first[0] if first else 'no report'}")
    blind = [sec["id"] for sec in result["sections"] if sec.get("design_items") is None]
    if blind:
        raise InputError(f"no element inventory for section(s) {', '.join(blind)} (a .json side); "
                         "accept-file needs both HTML renders")
    rows, uncovered, open_rows = accept_rows(ledger, result)
    text = io.StringIO()
    text.write("# Owner-accepted deviations drafted by feedback_ledger.py accept-file.\n")
    text.write(f"# design {ledger['design']['file']} {ledger['design']['sha256'][:12]}; "
               f"app {ledger['app']['file']} {ledger['app']['sha256'][:12]}.\n")
    text.write("# INERT until the owner reviews and commits it: parity_differ reads --accept from a\n"
               "# committed blob whose every commit is owner-authored (no Co-authored-by trailer).\n")
    text.write("section\tstatus\titem\tapp-value\tcount\treason\towner\n")
    for row in rows:
        text.write("\t".join(row) + "\n")
    if out:
        _atomic_write(out, text.getvalue())
        print(f"accept-file: wrote {len(rows)} row(s) to {out} — inert until the OWNER commits it "
              "(then: parity_differ.py --accept <file> --accept-rev <that commit>).")
    else:
        sys.stdout.write(text.getvalue())
    gaps = result.get("section_gaps") or {}
    n_gaps = len(gaps.get("missing") or []) + len(gaps.get("empty") or [])
    if open_rows or n_gaps:
        print(f"accept-file: {open_rows} parity difference(s) and {n_gaps} section gap(s) no decided "
              "item covers stay open — the parity differ's work queue.", file=sys.stderr)
    lines, unclassified = conflict_questions(ledger)
    life = resolve(ledger)
    unchecked = sum(1 for i in ledger["items"] if life[i["id"]]["state"] == "ACTIVE" and i.get("app_state") is None)
    if lines or unclassified or unchecked or uncovered:
        print(f"accept-file: may be incomplete — {len(lines) // 2} open owner decision(s), "
              f"{unclassified} item(s) without delta, {unchecked} without status, "
              f"{len(uncovered)} deviating item(s) with no matching parity row"
              f"{' (' + ', '.join(uncovered) + ')' if uncovered else ''}.", file=sys.stderr)
        return OPEN
    return CLEAN


# -------------------------------------------------------------------- render

def _cell(text) -> str:
    """Markdown-table-safe cell text."""
    return one_line("" if text is None else text).replace("|", "\\|")


def render_markdown(ledger: dict) -> str:
    """The human-readable companion: summary, open questions, full item table."""
    life = resolve(ledger)
    lines, unclassified = conflict_questions(ledger)
    out = ["# Feedback ledger", "",
           "Generated by `feedback_ledger.py` from the JSON ledger beside this file. "
           "Do not edit by hand; change it through the script.", ""]
    for label, key in (("Design compared", "design"), ("App checked", "app")):
        meta = ledger.get(key)
        out.append(f"- {label}: " + (f"{meta['file']} (sha256 {meta['sha256'][:12]}, {meta['date'] or 'undated'})"
                                     if meta else "not yet"))
    out.append(f"- Items: {len(ledger['items'])}; open owner decisions: {len(lines) // 2}; "
               f"not yet compared with a design: {unclassified}.")
    out += ["", "## Open owner decisions", ""]
    out += [f"    {line.strip()}" for line in lines] if lines else ["None."]
    out += ["", "## Items", "",
            "| ID | Target | Kind | Requirement | Sources | Date | Design | App | Lifecycle |",
            "|---|---|---|---|---|---|---|---|---|"]
    for item in ledger["items"]:
        sources = "; ".join(f"{r['source']} {r['source_ref']}" for r in item["refs"])
        out.append("| " + " | ".join(_cell(v) for v in (
            item["id"], item["target"], item["kind"], item["text"], sources, item["date"],
            item.get("design_state") or "-", item.get("app_state") or "-",
            (life[item["id"]]["state"] + _life_note(item, life)).strip())) + " |")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ selftest

def _selftest_owner_commit(tmp: str, design: str, app: str, tsv: str) -> dict:
    """Run parity_differ's CLI (`--json`) on an accept draft in a throwaway git repo.

    Returns {case: (exit code, verdict, "accepted_n=N")} for: no accept file;
    the draft uncommitted; the draft committed with a `Co-authored-by:`
    trailer (agent-assisted); the draft committed by the owner. Global/system
    git config is masked and DCR_OWNER_EMAIL is set only for the duration.
    Local, read-only apart from the temp repo; no network.
    """
    owner = "owner@example.com"
    repo = os.path.join(tmp, "owner-repo")
    os.makedirs(repo)
    keys = ("DCR_OWNER_EMAIL", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")
    saved = {k: os.environ.get(k) for k in keys}
    os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", DCR_OWNER_EMAIL=owner)
    out: dict = {}

    def git(*args: str) -> None:
        """Run one git command in the temp repo; raise on failure."""
        subprocess.run(["git", "-C", repo, "-c", f"user.email={owner}", "-c", "user.name=Jane Smith",
                        "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                       check=True, capture_output=True, text=True)

    def differ(label: str, accept: str | None) -> None:
        """Record the differ's exit code, verdict, and accepted count for one case."""
        cmd = [sys.executable, "-B", str(PARITY_DIFFER), "--design", design, "--app", app, "--json"]
        if accept:
            cmd += ["--accept", accept, "--accept-rev", "HEAD"]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        try:
            res = json.loads(proc.stdout)
        except json.JSONDecodeError:
            res = {"verdict": None, "report": proc.stdout + proc.stderr}
        out[label] = (proc.returncode, res.get("verdict"),
                      f"accepted_n={res['accepted_n']}" if "accepted_n" in res else res.get("report", "")[:200])

    try:
        git("init", "-q")
        differ("e2e-no-accept", None)
        for name, msg in (("agent.tsv", "chore: accept\n\nCo-authored-by: Assistant <bot@example.com>"),
                          ("owner.tsv", "chore: accept owner-reviewed deviations")):
            with open(os.path.join(repo, name), "w", encoding="utf-8") as fh:
                fh.write(tsv)
            git("add", name)
            git("commit", "-q", "-m", msg)
        with open(os.path.join(repo, "loose.tsv"), "w", encoding="utf-8") as fh:
            fh.write(tsv)
        differ("e2e-uncommitted", os.path.join(repo, "loose.tsv"))
        differ("e2e-agent-coauthored", os.path.join(repo, "agent.tsv"))
        differ("e2e-owner-committed", os.path.join(repo, "owner.tsv"))
    except (OSError, subprocess.CalledProcessError) as exc:
        out["error"] = (None, None, str(exc))
    finally:
        for key, val in saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
    return out


def _selftest() -> int:
    """Prove each rule FIRES on neutral offline fixtures; exit 0 only if all hold.

    Cases: cross-source dedupe + idempotent re-ingest; design-lag conflict and
    NOT_IN_DESIGN; JSON and HTML inventories classify alike; owner decision
    recorded then accept-file drafts the exact 7-field rows (parsed by
    parity_differ's own `parse_accept`), refuses a stale render, and never
    accepts an unrelated pairing; end to end, parity_differ's CLI reads the
    draft as MISMATCH -> inert (uncommitted or agent-attributed) -> an owner
    commit -> MATCH_WITH_ACCEPTED;
    regression detection; superseded ordering by date (ingest order reversed)
    plus a same-date feedback-vs-feedback conflict; a post-decision item
    re-opening the question; a declined item re-raised later being asked
    again; malformed input → 2 with the ledger left untouched; email
    redaction; HTML inventory path.
    """
    failures: list[str] = []

    def expect(label: str, cond: bool, detail: str = "") -> None:
        """Record a failed assertion."""
        if not cond:
            failures.append(f"{label}{': ' + detail if detail else ''}")

    with tempfile.TemporaryDirectory() as tmp:
        def path(name: str) -> str:
            """Absolute path inside the temp dir."""
            return os.path.join(tmp, name)

        def write(name: str, content) -> str:
            """Write a fixture (str or JSON-able) and return its path."""
            with open(path(name), "w", encoding="utf-8") as fh:
                fh.write(content if isinstance(content, str) else json.dumps(content))
            return path(name)

        ledger = path("ledger.json")

        def run(*args: str) -> tuple[int, str]:
            """Run the CLI in-process; return (exit code, stdout+stderr)."""
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                code = main(["--ledger", ledger, *args])
            return code, buf.getvalue()

        def read(name: str) -> str:
            """Full text of a file."""
            with open(name, encoding="utf-8") as fh:
                return fh.read()

        def items() -> list[dict]:
            """Current ledger items."""
            return json.loads(read(ledger))["items"]

        # 1. cross-source dedupe: survey CSV (mapped columns) + transcript JSON + doc JSON.
        survey = write("survey.csv",
                       "Row,Screen,Feedback,Submitted,Respondent role,Respondent email,Anchor,Replaces\n"
                       "7,reports/export,\"Change the Download button to Export CSV\",2026-09-10,"
                       "end user,jane@example.com,control:button:Export CSV,control:button:Download\n"
                       "8,reports/filters,Add a date range filter,2026-09-02,end user,,"
                       "control:combobox:Date range,\n"
                       "9,reports/summary,\"Keep the totals row (ask jane@example.com)\",2026-09-02,analyst,,"
                       "table-row:Totals,\n")
        mapping = write("map.json", {"source_ref": "Row", "target": "Screen", "text": "Feedback",
                                     "date": "Submitted", "role": "Respondent role",
                                     "expect": "Anchor", "was": "Replaces", "kind": "=change"})
        code, _ = run("ingest", "--source", "csv", "--file", survey, "--map", mapping)
        expect("ingest-csv", code == CLEAN, f"exit {code}")
        # the mapping's constant kind (=change) applies to every survey row
        transcript = write("transcript.json", {"items": [
            {"source_ref": "00:14:05", "target": "Reports / Export", "kind": "change",
             "text": "change the download button to export CSV!", "date": "2026-09-11",
             "role": "product owner", "expect": "control:button:Export CSV", "was": "control:button:Download"},
        ]})
        code, out = run("ingest", "--source", "transcript", "--file", transcript)
        expect("dedupe-exit", code == CLEAN, out)
        doc = write("doc.json", [
            {"source_ref": "comment 3", "target": "reports/export", "kind": "change",
             "text": "Rename that button so it reads Export CSV", "date": "2026-09-09", "role": "designer",
             "expect": "control:button:export csv", "was": "control:button:download"},
        ])
        run("ingest", "--source", "doc", "--file", doc)
        exports = [i for i in items() if norm_target(i["target"]) == "reports/export"]
        expect("dedupe-one-item", len(exports) == 1, f"{len(exports)} items")
        expect("dedupe-three-refs", exports and len(exports[0]["refs"]) == 3,
               str(exports and [r["source"] for r in exports[0]["refs"]]))
        expect("dedupe-newest-date", exports and exports[0]["date"] == "2026-09-11")
        code, out = run("ingest", "--source", "csv", "--file", survey, "--map", mapping)
        expect("idempotent-reingest", "3 already recorded" in out and len(items()) == 3, out)
        raw = read(ledger)
        expect("privacy-redaction", "example.com" not in raw and "[email]" in raw)
        expect("companion-render", os.path.isfile(companion_path(ledger)))

        # 2. superseded ordering by date (newer ingested FIRST), and same-date peer conflict.
        titles = write("titles.json", [
            {"source_ref": "comment 9", "target": "reports/title", "kind": "change", "date": "2026-09-05",
             "text": "Title should read Monthly reports", "expect": "heading:h1:Monthly reports",
             "was": "heading:h1:Reports"},
            {"source_ref": "comment 2", "target": "reports/title", "kind": "change", "date": "2026-09-01",
             "text": "Title should read Report center", "expect": "heading:h1:Report center",
             "was": "heading:h1:Reports"},
            {"source_ref": "comment 4", "target": "reports/legend", "kind": "add", "date": "2026-09-03",
             "text": "Show the legend above the chart", "expect": "text:Legend above"},
            {"source_ref": "comment 5", "target": "reports/legend", "kind": "add", "date": "2026-09-03",
             "text": "Show the legend under the chart", "expect": "text:Legend under"},
            {"source_ref": "comment 6", "target": "reports/banner", "kind": "remove", "date": "2026-09-04",
             "text": "Drop the promo banner", "expect": "text:Promo banner"},
            {"source_ref": "comment 7", "target": "reports/help", "kind": "add", "date": "2026-09-04",
             "text": "Link to the help page", "expect": "control:link:Help"},
            {"source_ref": "comment 8", "target": "reports/sort", "kind": "add", "date": "2026-09-04",
             "text": "Let users sort by date", "expect": "control:button:Sort by date"},
        ])
        run("ingest", "--source", "doc", "--file", titles)
        by_text = {i["text"]: i for i in items()}
        life = resolve(json.loads(read(ledger)))
        old = by_text["Title should read Report center"]
        new = by_text["Title should read Monthly reports"]
        expect("superseded-older", life[old["id"]]["state"] == "SUPERSEDED"
               and life[old["id"]]["by"] == new["id"], str(life[old["id"]]))
        expect("superseded-newer-active", life[new["id"]]["state"] == "ACTIVE")
        above = by_text["Show the legend above the chart"]
        expect("same-date-peer-conflict", life[above["id"]]["peers"] == [by_text["Show the legend under the chart"]["id"]])

        # 3. design-lag: design shows Download (was) -> CONFLICTS; date filter absent -> NOT_IN_DESIGN.
        design = write("design.json", [
            {"id": "Reports", "populated": True, "inventory": [
                "heading:h1:Monthly reports", "control:button:Download", "table-row:Totals",
                "text:Legend above", "text:Promo banner"]},
        ])
        code, out = run("delta", "--design", design, "--design-date", "2026-09-08")
        states = {i["target"]: i["design_state"] for i in items()}
        expect("delta-exit-open", code == OPEN, f"exit {code}")
        expect("delta-conflict", states.get("reports/export") == CONFLICTS, str(states))
        expect("delta-not-in-design", states.get("reports/filters") == NOT_IN_DESIGN, str(states))
        expect("delta-in-design", states.get("reports/summary") == IN_DESIGN, str(states))
        expect("delta-remove-conflict", states.get("reports/banner") == CONFLICTS, str(states))
        expect("delta-superseded", states.get("reports/title") in (IN_DESIGN, SUPERSEDED)
               and old["id"] in out and SUPERSEDED in out, out)
        code, out = run("conflicts")
        qs = [ln for ln in out.splitlines() if ln.startswith("Q")]
        expect("conflicts-open", code == OPEN and len(qs) == 3, out)
        design_q = [ln for ln in out.splitlines() if exports[0]["id"] in ln and "design (2026-09-08)" in ln]
        expect("conflicts-question-shape", design_q and "control:button:Download" in design_q[0]
               and "Export CSV" in design_q[0] and "transcript 00:14:05, 2026-09-11" in design_q[0], out)
        expect("conflicts-two-lines", all(ln.startswith(("Q", "    ")) for ln in out.splitlines()
                                          if not ln.startswith("note")), out)

        # 4. owner decisions recorded; accept-file carries the decided + design-lag items only.
        eid = exports[0]["id"]
        alias = exports[0]["aliases"][0] if exports[0]["aliases"] else eid
        code, _ = run("decide", "--id", alias, "--choose", "feedback", "--quote",
                      "Go with Export CSV, the design is behind.", "--date", "2026-09-12")
        expect("decide-by-alias", code == CLEAN, f"exit {code}")
        run("decide", "--id", above["id"], "--choose", "feedback", "--quote", "Above.", "--date", "2026-09-12")
        banner = [i for i in items() if i["target"] == "reports/banner"][0]
        run("decide", "--id", banner["id"], "--choose", "feedback", "--quote", "Remove it.", "--date", "2026-09-12")
        # a later restatement agrees with a "feedback" answer, so that answer does not lapse
        write("restate.json", [{"source_ref": "00:21:40", "target": "reports/banner", "kind": "remove",
                                "date": "2026-09-13", "text": "Drop the promo banner", "expect": "text:Promo banner"}])
        run("ingest", "--source", "transcript", "--file", path("restate.json"))
        code, out = run("conflicts")
        expect("conflicts-cleared", code == CLEAN and "none open" in out, out)
        app = write("app.json", [
            {"id": "reports", "populated": True, "inventory": [
                "heading:h1:Monthly reports", "control:button:Export CSV", "table-row:Totals",
                "control:combobox:Date range", "text:Legend above", "control:button:Sort by date"]},
        ])
        code, out = run("status", "--app", app, "--date", "2026-09-13")
        expect("status-one-pending", code == OPEN and "1 PENDING, 0 REGRESSED" in out, out)
        # 4b. the same design and app as HTML renders, read through parity_differ's public
        # inventory_keys; the states must equal the JSON-inventory run above.
        design_html = write("design-render.html", (
            '<main><section data-section="Reports"><h1>Monthly reports</h1><button>Download</button>'
            '<table><tr data-item><td>Totals</td></tr></table><p>Legend above</p>'
            '<p>Promo banner</p><p>Promo banner</p></section></main>'))
        app_html = write("app-render.html", (
            '<main><section data-section="Reports"><h1>Monthly reports</h1><button>Export CSV</button>'
            '<table><tr data-item><td>Totals</td></tr></table><label for="d">Date range</label>'
            '<select id="d"></select><p>Legend above</p><button>Sort By Date</button></section></main>'))
        run("delta", "--design", design, "--design-date", "2026-09-08")   # re-classify after decisions
        json_states = {i["id"]: (i["design_state"], i["app_state"]) for i in items()}
        run("delta", "--design", design_html, "--design-date", "2026-09-08")
        code, out = run("status", "--app", app_html, "--date", "2026-09-13")
        expect("html-status-one-pending", code == OPEN and "1 PENDING, 0 REGRESSED" in out, out)
        html_states = {i["id"]: (i["design_state"], i["app_state"]) for i in items()}
        expect("html-states-equal-json", html_states == json_states, f"{json_states} vs {html_states}")

        # 4c. accept-file drafts the differ's 7-field rows from the differ's own printed rows.
        accept = path("accept.tsv")
        code, out = run("accept-file", "--design", design_html, "--app", app_html, "--out", accept)
        expect("accept-exit", code == CLEAN, out)
        expect("accept-inert-notice", "inert until the OWNER commits it" in out, out)
        tsv = read(accept)
        rows = [ln.split("\t") for ln in tsv.splitlines() if ln and not ln.startswith("#")][1:]
        got = {tuple(r[:5]) for r in rows}
        want = {("Reports", "CHANGED", "control:button:Download", "control:button:Export CSV", "1"),
                ("Reports", "MISSING_IN_APP", "text:Promo banner", "-", "2"),
                ("Reports", "EXTRA_IN_APP", "control:combobox:Date range", "control:combobox:Date range", "1"),
                ("Reports", "EXTRA_IN_APP", "control:button:Sort By Date", "control:button:Sort By Date", "1")}
        expect("accept-rows-exact", got == want and len(rows) == len(want), tsv)
        expect("accept-seven-fields", rows and all(len(r) == 7 and all(r) for r in rows), tsv)
        expect("accept-owner-quote", any(r[1] == "CHANGED" and "Go with Export CSV" in r[6] for r in rows), tsv)
        expect("accept-inert-header", "INERT until the owner reviews and commits it" in tsv, tsv)
        pd = load_parity_differ()
        if pd is None or not hasattr(pd, "parse_accept"):
            failures.append("accept: sibling parity_differ.py with parse_accept not found")
        else:
            parsed, err = pd.parse_accept(tsv)
            expect("accept-parses-in-parity-differ", parsed is not None and len(parsed) == len(rows), str(err))
        # pure accept_rows: an eligible item no row covers is reported; a CHANGED row pairing
        # an item's key with an unrelated design element is never accepted.
        snap = json.loads(read(ledger))
        rws, unc, opn = accept_rows(snap, {"sections": []})
        expect("accept-rows-uncovered", rws == [] and len(unc) == 4 and opn == 0, f"{rws} {unc} {opn}")
        stray = {"sections": [{"id": "Reports", "rows": [
            {"status": "CHANGED", "item": "control:button:Share", "design": "control:button:Share",
             "app": "control:button:Export CSV"}]}]}
        rws, unc, opn = accept_rows(snap, stray)
        expect("accept-rows-unrelated-changed-open", rws == [] and opn == 1, f"{rws} {opn}")
        # stale or wrong renders fail closed
        code, out = run("accept-file", "--design", design_html, "--app", app, "--out", path("stale.tsv"))
        expect("accept-stale-render", code == INPUT_ERROR and not os.path.exists(path("stale.tsv")), out)

        # 4d. end to end: MISMATCH -> the owner commits the draft -> MATCH_WITH_ACCEPTED.
        # An agent-attributed or uncommitted copy of the same draft stays inert.
        e2e = _selftest_owner_commit(tmp, design_html, app_html, tsv)
        for label, (want_code, want_verdict) in (
                ("e2e-no-accept", (1, "MISMATCH")),
                ("e2e-uncommitted", (3, "COULD_NOT_CHECK")),
                ("e2e-agent-coauthored", (3, "COULD_NOT_CHECK")),
                ("e2e-owner-committed", (0, "MATCH_WITH_ACCEPTED"))):
            code, verdict, extra = e2e.get(label, (None, None, ""))
            expect(label, (code, verdict) == (want_code, want_verdict), f"{code} {verdict} {extra}")
        expect("e2e-accepted-n", e2e.get("e2e-owner-committed", (0, 0, ""))[2] == "accepted_n=5",
               str(e2e.get("e2e-owner-committed")))

        # an owner "design" answer removes an item at once, even before status re-runs
        sort_id = [i for i in items() if i["target"] == "reports/sort"][0]["id"]
        run("decide", "--id", sort_id, "--choose", "design", "--quote", "No sorting yet.", "--date", "2026-09-14")
        run("decide", "--id", eid, "--choose", "design", "--quote", "Keep Download after all.", "--date", "2026-09-14")
        code, out = run("accept-file", "--design", design_html, "--app", app_html, "--out", accept)
        tsv = read(accept)
        expect("accept-declined-excluded", code == CLEAN and "Export CSV" not in tsv
               and "Sort By Date" not in tsv and "2 parity difference(s)" in out, out + tsv)
        # a JSON render carries no element inventory for the differ: accept-file refuses rather
        # than drafting blind — whether the differ says COULD_NOT_CHECK or MISMATCH (a missing
        # section) with an inventory-less section beside it.
        json_app = write("json-app.json", [{"id": "Reports", "populated": True,
                                            "inventory": json.loads(read(app))[0]["inventory"]}])
        run("status", "--app", json_app, "--date", "2026-09-14")
        code, out = run("accept-file", "--design", design_html, "--app", json_app, "--out", path("blind.tsv"))
        expect("accept-json-side-could-not-check", code == INPUT_ERROR and "could not compare" in out
               and not os.path.exists(path("blind.tsv")), out)
        ledger_saved, ledger = ledger, path("blind-ledger.json")
        write("blind-items.json", [{"target": "a", "kind": "add", "date": "2026-09-01", "text": "Add Save",
                                    "expect": "control:button:Save"}])
        run("ingest", "--source", "doc", "--file", path("blind-items.json"))
        blind_design = write("blind-design.html", '<section data-section="a"><p data-item>x</p></section>'
                                                  '<section data-section="b"><p data-item>y</p></section>')
        blind_app = write("blind-app.json", [{"id": "a", "populated": True, "inventory": ["control:button:Save"]}])
        run("delta", "--design", blind_design)
        run("status", "--app", blind_app)
        code, out = run("accept-file", "--design", blind_design, "--app", blind_app, "--out", path("blind.tsv"))
        expect("accept-json-side-mismatch-refused", code == INPUT_ERROR and "both HTML renders" in out
               and not os.path.exists(path("blind.tsv")), out)
        ledger = ledger_saved

        # 5. regression: the filter disappears from the app after being implemented.
        app2 = write("app2.json", [
            {"id": "reports", "populated": True, "inventory": [
                "heading:h1:Monthly reports", "control:button:Download", "table-row:Totals", "text:Legend above"]},
        ])
        code, out = run("status", "--app", app2, "--date", "2026-09-15")
        filt = [i for i in items() if i["target"] == "reports/filters"][0]
        expect("regression-fires", code == OPEN and filt["app_state"] == REGRESSED, out)
        # a never-implemented item reads PENDING, not REGRESSED
        write("late.json", [{"target": "reports/footer", "kind": "add", "date": "2026-09-15",
                             "text": "Add a data freshness note", "expect": "text:Data as of"}])
        run("ingest", "--source", "transcript", "--file", path("late.json"))
        run("status", "--app", app2, "--date", "2026-09-15")
        foot = [i for i in items() if i["target"] == "reports/footer"][0]
        expect("pending-not-regressed", foot["app_state"] == PENDING, str(foot["app_state"]))
        code, out = run("conflicts")
        expect("unclassified-is-open", code == OPEN and "1 item(s) not yet compared" in out
               and not any(ln.startswith("Q") for ln in out.splitlines()), out)
        # an item dated after an owner decision re-opens the question instead of winning silently
        write("later.json", [{"source_ref": "comment 12", "target": "reports/legend", "kind": "add",
                              "date": "2026-09-13", "text": "Legend goes on the right", "expect": "text:Legend right"}])
        run("ingest", "--source", "doc", "--file", path("later.json"))
        life = resolve(json.loads(read(ledger)))
        right = [i for i in items() if i["text"] == "Legend goes on the right"][0]
        expect("decision-sticky-reopens", life[right["id"]]["peers"] == [above["id"]], str(life[right["id"]]))
        # a request the owner declined, re-raised by a later source, is asked again
        write("reraise.json", [{"source_ref": "00:03:10", "target": "reports/export", "kind": "change",
                                "date": "2026-09-16", "text": "Change the Download button to Export CSV",
                                "expect": "control:button:Export CSV", "was": "control:button:Download"}])
        run("ingest", "--source", "transcript", "--file", path("reraise.json"))
        life = resolve(json.loads(read(ledger)))
        code, out = run("conflicts")
        expect("declined-reraised-asked-again", life[eid]["state"] == "ACTIVE"
               and any(ln.startswith("Q") and eid in ln for ln in out.splitlines()), out)

        # 6. malformed input → 2, ledger untouched.
        before = read(ledger)
        bad_json = write("bad.json", "{not json")
        missing_expect = write("noexpect.json", [{"target": "a/b", "kind": "add", "text": "x", "date": "2026-09-01"}])
        bad_kind = write("badkind.json", [{"target": "a/b", "kind": "maybe", "text": "x", "date": "2026-09-01",
                                           "expect": "text:x"}])
        bad_date = write("baddate.json", [{"target": "a/b", "kind": "add", "text": "x", "date": "09/01/2026",
                                           "expect": "text:x"}])
        no_inv = write("noinv.json", [{"id": "reports", "populated": True}])
        cases = [
            ("bad-json", ("ingest", "--source", "doc", "--file", bad_json)),
            ("missing-expect", ("ingest", "--source", "doc", "--file", missing_expect)),
            ("bad-kind", ("ingest", "--source", "doc", "--file", bad_kind)),
            ("bad-date", ("ingest", "--source", "doc", "--file", bad_date)),
            ("bad-source", ("ingest", "--source", "email", "--file", bad_kind)),
            ("missing-file", ("ingest", "--source", "csv", "--file", path("nope.csv"))),
            ("unknown-id", ("decide", "--id", "ffffffffffff", "--choose", "feedback", "--quote", "x",
                            "--date", "2026-09-01")),
            ("empty-quote", ("decide", "--id", eid, "--choose", "feedback", "--quote", "  ", "--date", "2026-09-01")),
            ("no-inventory", ("delta", "--design", no_inv)),
            ("missing-design", ("delta", "--design", path("nope.json"))),
        ]
        for label, args in cases:
            try:
                code, out = run(*args)
            except SystemExit as exc:   # argparse usage errors
                code = exc.code
            expect(f"malformed-{label}", code == INPUT_ERROR, f"exit {code}")
        expect("malformed-ledger-untouched", read(ledger) == before)
        ledger_saved, ledger = ledger, path("absent.json")
        code, _ = run("status", "--app", app)
        expect("malformed-missing-ledger", code == INPUT_ERROR)
        ledger = path("notes.md")   # the render would overwrite a non-.json ledger
        code, _ = run("ingest", "--source", "doc", "--file", titles)
        expect("malformed-ledger-suffix", code == INPUT_ERROR and not os.path.exists(ledger))
        ledger = write("broken.json", {"schema": SCHEMA, "items": [{"id": "x", "target": "a/b", "kind": "add",
                                                                    "expect": "text:x", "refs": []}]})
        code, _ = run("conflicts")
        expect("malformed-ledger-item", code == INPUT_ERROR)
        ledger = ledger_saved

        # 7. HTML inventory goes through parity_differ's extractor (imported, not copied).
        html = write("design.html", '<main><section data-section="reports"><h1>Monthly reports</h1>'
                                    '<button data-item>Download</button></section></main>')
        if pd is None:
            failures.append("html: sibling parity_differ.py not found")
        else:
            try:
                inv = load_inventory(html, "design")
                capable = hasattr(pd, "inventory_keys")
                expect("html-inventory", (not capable and inv == {"reports": None})
                       or (capable and "control:button:download" in (inv.get("reports") or set())), str(inv))
                if not capable:
                    code, out = run("delta", "--design", html)
                    expect("html-no-inventory-fails-closed", code == INPUT_ERROR, out)
            except InputError as exc:
                failures.append(f"html: {exc}")
            if capable:
                hid = write("hidden.html", '<section data-section="reports"><button class="d-none">Help</button>'
                                           '</section>')
                code, out = run("status", "--app", hid)
                expect("html-unmarked-hiding-class-fails-closed", code == INPUT_ERROR and "data-visible" in out, out)

    if failures:
        print("SELFTEST FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELFTEST OK: dedupe=linked(3 sources) idempotent=ok superseded=by-date peer-conflict=ok "
          "design-lag=CONFLICTS/NOT_IN_DESIGN decide->accept-file(7-field,exact)=ok "
          "owner-commit(MISMATCH->MATCH_WITH_ACCEPTED)=ok regression=1 malformed=2")
    return 0


# ---------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    """CLI entry point; every InputError becomes exit 2 with no partial write."""
    parser = argparse.ArgumentParser(description="One durable requirement ledger across feedback sources.")
    parser.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"ledger path (default {DEFAULT_LEDGER})")
    parser.add_argument("--selftest", action="store_true", help="run the offline self-test")
    sub = parser.add_subparsers(dest="cmd")
    p = sub.add_parser("ingest", help="normalize + merge one source file")
    p.add_argument("--source", required=True, choices=SOURCES)
    p.add_argument("--file", required=True)
    p.add_argument("--map", dest="map_path")
    p = sub.add_parser("delta", help="classify items against the latest design inventory")
    p.add_argument("--design", required=True)
    p.add_argument("--design-date")
    p = sub.add_parser("status", help="check items against the app inventory")
    p.add_argument("--app", required=True)
    p.add_argument("--date")
    sub.add_parser("conflicts", help="list owner decisions needed")
    p = sub.add_parser("decide", help="record the owner's answer")
    p.add_argument("--id", required=True)
    p.add_argument("--choose", required=True, choices=CHOICES)
    p.add_argument("--quote", required=True)
    p.add_argument("--date", required=True)
    p = sub.add_parser("accept-file", help="draft parity_differ's accepted-deviations TSV (owner commits it)")
    p.add_argument("--design", required=True, help="the HTML design render delta last read")
    p.add_argument("--app", required=True, help="the HTML app render status last read")
    p.add_argument("--out")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    try:
        if args.cmd == "ingest":
            return cmd_ingest(args.ledger, args.source, args.file, args.map_path)
        if args.cmd == "delta":
            return cmd_delta(args.ledger, args.design, args.design_date)
        if args.cmd == "status":
            return cmd_status(args.ledger, args.app, args.date)
        if args.cmd == "conflicts":
            return cmd_conflicts(args.ledger)
        if args.cmd == "decide":
            return cmd_decide(args.ledger, args.id, args.choose, args.quote, args.date)
        if args.cmd == "accept-file":
            return cmd_accept_file(args.ledger, args.design, args.app, args.out)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return INPUT_ERROR
    parser.print_usage(sys.stderr)
    return INPUT_ERROR


if __name__ == "__main__":
    sys.exit(main())
