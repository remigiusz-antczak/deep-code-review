#!/usr/bin/env python3
"""token_differ.py — the tier-1 design<->app design-token VALUE parity gate.

WHY THIS EXISTS (the failure it closes)
----------------------------------------
"The app uses the design's tokens" is usually checked by NAME — the app has a
`--color-brand-primary`, the design has `color.brand.primary`, so it "matches."
Names prove nothing: the app can carry every design name with different
values (a different token foundation), and then no per-screen restyle ever
converges. This tool resolves every alias on both sides, normalizes each
resolved value to a canonical form, and compares VALUES. It is tier 1 of the
check order in `references/migration-parity.md`: cheap and deterministic, run
before `parity_differ.py` (structural sections) and before any screenshot.

WHAT IT DOES NOT VERIFY (read before quoting a MATCH)
------------------------------------------------------
It verifies resolved token VALUES only. It does not verify that components
actually USE these tokens (a hard-coded `#f00` in a component is invisible to
it), selector/theme scoping, or anything rendered. A MATCH here is a
precondition for "aligned," never the claim itself.

CONTRACT (fail-closed; only one passing exit)
---------------------------------------------
* 0 MATCH — the ONLY pass: both sides readable and every compared token MATCH.
* 1 MISMATCH — at least one compared token is MISMATCH, MISSING_IN_APP, or
  UNRESOLVED. The per-token list is the work queue.
* 2 COULD_NOT_CHECK — either side (or a given --map) is missing, unreadable,
  empty, invalid, or yields zero tokens; a --map `$type` that is not a DTCG
  type is invalid. Never a pass. (argparse usage errors also exit 2 —
  equally non-passing.)
Per-token status:
* MATCH — resolved values are equal after normalization.
* MISMATCH — both resolved; values differ (both values printed).
* MISSING_IN_APP — the design token has no app counterpart.
* UNRESOLVED — a side could not be resolved or normalized: alias/var() cycle,
  undefined reference, a CSS property defined twice with different values
  (theme/selector scoping is not modeled — skip rather than guess), a CSS
  value with an unterminated quote/`url(` or an unbalanced bracket, a value
  that does not parse as its declared `$type`, a --map `$type` that
  contradicts a side's declared `$type`, or a composite-vs-scalar pair.
App-only tokens are reported as info and never fail.

INPUTS (either format on either side; `.json` = DTCG, anything else = CSS)
--------------------------------------------------------------------------
  DTCG  : W3C Design Tokens JSON. A token is an object with `$value`; `$type`
          is inherited from the closest parent group. Aliases `{group.token}`
          and local JSON Pointers `{"$ref": "#/group/token/$value"}` resolve;
          circular references are UNRESOLVED on every token in the chain.
  CSS   : `--name: value;` custom properties anywhere in the file (comments
          stripped, `!important` dropped). Values are tokenized respecting
          quotes and brackets: a `;` inside `"..."`, `'...'`, or `url(...)`
          does not end the value. Only a statement that starts with
          `--name:` is a declaration, so text inside an at-rule prelude
          (`@container style(--theme: dark)`) is never a token. `var(--x)`
          and `var(--x, fallback)` resolve recursively with cycle detection.
Normalization: colors (hex3/4/6/8, rgb/rgba, hsl/hsla, DTCG srgb objects,
`transparent`/`black`/`white`) -> rgba, equal within half an 8-bit step;
dimensions px/rem (rem x --root-px, default 16) -> px, other units compared
as-is; durations s/ms -> ms; font weights (DTCG keywords -> numbers) only when
the `$type` is fontWeight; font families -> lowercase unquoted list. A --map
`$type` column, else the design's `$type`, else the app's, drives
normalization of both sides (two different declared types -> MISMATCH,
with or without an override; an override that differs from a declared type
-> UNRESOLVED); an
untyped value is parsed as color, then dimension, then number, then a
whitespace-normalized string.

MAPPING: by name (DTCG `a.b.c` == CSS `--a-b-c`; case, `.`, `_`, `/` folded;
a fold collision on either side is UNRESOLVED), or an explicit `--map` TSV:
`design_name<TAB>app_name[<TAB>$type]` — only mapped rows are compared.

USAGE
-----
  token_differ.py --design <file> --app <file> [--map <tsv>] [--root-px 16]
  token_differ.py --selftest
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile

MATCH = 0
MISMATCH = 1
COULD_NOT_CHECK = 2

_NUM = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?"
_ALIAS_RE = re.compile(r"\{([^{}]+)\}")
# A custom-property declaration starts a CSS statement: `--name` then `:`.
_CSS_DECL_START_RE = re.compile(r"(--[A-Za-z0-9_-]+)\s*:")
_CLOSERS = {"(": ")", "[": "]", "{": "}"}
# Every `$type` the Design Tokens Format Module defines (7 simple, 6
# composite). A --map override outside this set is a map defect, not a type.
_DTCG_TYPES = frozenset({
    "color", "dimension", "fontFamily", "fontWeight", "duration", "cubicBezier", "number",
    "strokeStyle", "border", "transition", "shadow", "gradient", "typography",
})
# DTCG fontWeight keyword table (Design Tokens Format Module, fontWeight type).
_WEIGHTS = {
    "thin": 100, "hairline": 100, "extra-light": 200, "ultra-light": 200,
    "light": 300, "normal": 400, "regular": 400, "book": 400, "medium": 500,
    "semi-bold": 600, "demi-bold": 600, "bold": 700, "extra-bold": 800,
    "ultra-bold": 800, "black": 900, "heavy": 900, "extra-black": 950,
    "ultra-black": 950,
}
_NAMED_COLORS = {
    "transparent": ("color", 0.0, 0.0, 0.0, 0.0),
    "black": ("color", 0.0, 0.0, 0.0, 1.0),
    "white": ("color", 255.0, 255.0, 255.0, 1.0),
}
# Sub-keys of DTCG composite values whose type is fixed by the key itself.
_KEY_HINTS = {"color": "color", "fontFamily": "fontFamily",
              "fontWeight": "fontWeight", "duration": "duration", "delay": "duration"}


class Unresolved(Exception):
    """A value that cannot be resolved or normalized; `str(e)` is the reason."""


def _isnum(v: object) -> bool:
    """True for a real int/float (bool excluded), finite."""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


class _Side:
    """One loaded side: its tokens plus a memoized, cycle-detecting resolver.

    `tokens` maps name -> {"raw", "type", "conflict"[, "invalid"]}; names
    are DTCG dotted paths or CSS `--names`. `resolve()` raises Unresolved,
    never returns a guessed value; errors are memoized per token so a cycle
    is reported once per token, deterministically.
    """

    def __init__(self, path: str, fmt: str, tokens: dict) -> None:
        """Store the parsed tokens; `fmt` is "dtcg" or "css"."""
        self.path, self.fmt, self.tokens = path, fmt, tokens
        self._memo: dict = {}
        self._stack: list[str] = []

    def lookup(self, name: str) -> str | None:
        """Return the stored token name for an explicit --map name, or None."""
        if self.fmt == "css" and not name.startswith("--"):
            name = "--" + name
        return name if name in self.tokens else None

    def resolve(self, name: str):
        """Return the fully resolved value of token `name` (raises Unresolved)."""
        if name in self._memo:
            hit = self._memo[name]
            if isinstance(hit, Unresolved):
                raise hit
            return hit
        if name in self._stack:
            chain = self._stack[self._stack.index(name):] + [name]
            raise Unresolved("reference cycle: " + " -> ".join(chain))
        if name not in self.tokens:
            raise Unresolved(f"reference target {name!r} is not defined")
        token = self.tokens[name]
        self._stack.append(name)
        try:
            if token.get("invalid"):
                raise Unresolved(token["invalid"])
            if token["conflict"]:
                raise Unresolved(
                    "defined more than once with different values ("
                    + " | ".join(token["conflict"])
                    + "); selector/theme scoping is not modeled")
            try:
                value = self._css(token["raw"]) if self.fmt == "css" else self._tree(token["raw"])
            except RecursionError:
                raise Unresolved("reference chain too deep to resolve") from None
        except Unresolved as exc:
            self._memo[name] = exc
            raise
        finally:
            self._stack.pop()
        self._memo[name] = value
        return value

    def type_of(self, name: str, seen: frozenset = frozenset()) -> str | None:
        """Declared/inherited DTCG `$type`, else the referenced token's type."""
        token = self.tokens.get(name)
        if token is None or name in seen:
            return None
        if token["type"]:
            return token["type"]
        raw = token["raw"]
        if isinstance(raw, str) and _ALIAS_RE.fullmatch(raw.strip()):
            return self.type_of(raw.strip()[1:-1].strip(), seen | {name})
        if isinstance(raw, dict) and set(raw) == {"$ref"} and isinstance(raw["$ref"], str):
            segs = raw["$ref"][2:].split("/")
            if segs[-1:] == ["$value"]:
                return self.type_of(".".join(segs[:-1]), seen | {name})
        return None

    def _tree(self, value):
        """Resolve DTCG aliases / `$ref` pointers anywhere inside a value."""
        if isinstance(value, str):
            match = _ALIAS_RE.fullmatch(value.strip())
            return self.resolve(match.group(1).strip()) if match else value
        if isinstance(value, dict):
            if set(value) == {"$ref"}:
                return self._pointer(value["$ref"])
            return {k: self._tree(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._tree(v) for v in value]
        return value

    def _pointer(self, ref: object):
        """Resolve a local JSON Pointer that targets (inside) a token `$value`."""
        if not isinstance(ref, str) or not ref.startswith("#/"):
            raise Unresolved(f"unsupported $ref {ref!r} (only local '#/...' pointers)")
        segs = [s.replace("~1", "/").replace("~0", "~") for s in ref[2:].split("/")]
        if "$value" not in segs:
            raise Unresolved(f"$ref {ref!r} does not point into a token $value")
        cut = segs.index("$value")
        value = self.resolve(".".join(segs[:cut]))
        for seg in segs[cut + 1:]:
            if isinstance(value, dict) and seg in value:
                value = value[seg]
            elif isinstance(value, list) and seg.isdigit() and int(seg) < len(value):
                value = value[int(seg)]
            else:
                raise Unresolved(f"$ref {ref!r}: no {seg!r} inside the target value")
        return value

    def _css(self, text: str) -> str:
        """Substitute every `var(--x[, fallback])` in a CSS value, recursively."""
        out, pos, i = [], 0, 0
        while i < len(text):
            if text[i] in "\"'":
                # `var(` inside a quoted string is literal text, not a reference.
                i, _ok = _skip_string(text, i)
                continue
            if not (text.startswith("var(", i) and (i == 0 or not _is_ident_char(text[i - 1]))):
                i += 1
                continue
            end = _match_paren(text, i + 3)
            if end < 0:
                raise Unresolved(f"unbalanced var( in {text!r}")
            out.append(text[pos:i])
            ref, has_fallback, fallback = text[i + 4:end].partition(",")
            ref = ref.strip()
            if ref in self.tokens:
                out.append(self.resolve(ref))
            elif has_fallback:
                out.append(self._css(fallback.strip()))
            else:
                raise Unresolved(f"var({ref}) is not defined and has no fallback")
            pos = i = end + 1
        out.append(text[pos:])
        result = " ".join("".join(out).split())
        if not result:
            raise Unresolved("empty value")
        return result


def _dtcg_tokens(data: object) -> dict:
    """Walk a DTCG document into {dotted.path: token}, inheriting group `$type`."""
    tokens: dict = {}

    def walk(node: dict, path: list[str], inherited: str | None) -> None:
        """Recurse one group; `$`-prefixed keys are properties, not children."""
        group_type = node["$type"] if isinstance(node.get("$type"), str) else inherited
        for key, child in node.items():
            if key.startswith("$") or not isinstance(child, dict):
                continue
            if "$value" in child:
                own = child.get("$type")
                tokens[".".join(path + [key])] = {
                    "raw": child["$value"],
                    "type": own if isinstance(own, str) else group_type,
                    "conflict": None,
                }
            else:
                walk(child, path + [key], group_type)

    if isinstance(data, dict):
        walk(data, [], None)
    return tokens


def _is_ident_char(ch: str) -> bool:
    """True for a character that can continue a CSS identifier."""
    return ch.isalnum() or ch in "-_"


def _skip_string(text: str, i: int) -> tuple[int, bool]:
    """Skip the quoted string opening at `text[i]`; return (index after it, ok).

    Backslash escapes (including an escaped newline) stay inside the string.
    An unescaped newline or end of input leaves the string unterminated:
    ok is False and the index is where the string stopped.
    """
    quote, j = text[i], i + 1
    while j < len(text):
        ch = text[j]
        if ch == "\\":
            j += 2
            continue
        if ch == quote:
            return j + 1, True
        if ch == "\n":
            return j, False
        j += 1
    return len(text), False


def _match_paren(text: str, i: int) -> int:
    """Index of the `)` closing the `(` at `text[i]`, skipping strings; -1 if none."""
    depth, j = 0, i
    while j < len(text):
        ch = text[j]
        if ch in "\"'":
            j, _ok = _skip_string(text, j)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return -1


def _split_top_level(text: str, sep: str = ",") -> list[str]:
    """Split on `sep` outside quoted strings and brackets (`"A,B", serif` -> 2 parts)."""
    parts, stack, start, j = [], [], 0, 0
    while j < len(text):
        ch = text[j]
        if ch in "\"'":
            j, _ok = _skip_string(text, j)
            continue
        if ch in _CLOSERS:
            stack.append(_CLOSERS[ch])
        elif stack and ch == stack[-1]:
            stack.pop()
        elif ch == sep and not stack:
            parts.append(text[start:j])
            start = j + 1
        j += 1
    parts.append(text[start:])
    return parts


def _scan_statement(text: str, i: int, declaration: bool) -> tuple[str, int, str | None]:
    """Scan one CSS statement from `text[i]`; return (text, stop index, problem).

    Quoted strings, `url(...)` (quoted or not), and bracket nesting are kept
    whole, so a `;` inside `"a;b"`, `'a;b'`, or `url(data:...;...)` does not
    end the statement; comments become a single space. A declaration ends at
    a top-level `;` or at the `}` closing its rule block; anything else (a
    selector or an at-rule prelude such as `@container style(--x: y)`) also
    ends at the `{` opening its block. The stop index points AT the
    terminator. `problem` is None, or why the text is not trustworthy: an
    unterminated string or `url(`, or an unbalanced bracket.
    """
    parts: list[str] = []
    stack: list[str] = []
    problem: str | None = None
    while i < len(text):
        ch = text[i]
        if ch in "\"'":
            end, ok = _skip_string(text, i)
            parts.append(text[i:end])
            if not ok:
                problem = problem or "unterminated quoted string"
            i = end
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            parts.append(" ")
            i = len(text) if end < 0 else end + 2
            continue
        if (ch == "(" and i >= 3 and text[i - 3:i].lower() == "url"
                and (i < 4 or not _is_ident_char(text[i - 4]))):
            j = i + 1
            while j < len(text) and text[j].isspace():
                j += 1
            if j < len(text) and text[j] not in "\"'":
                # Unquoted url(): raw text up to `)`; quotes and `;` are literal.
                while j < len(text) and text[j] != ")":
                    j += 2 if text[j] == "\\" else 1
                if j >= len(text):
                    parts.append(text[i:])
                    problem = problem or "unterminated url("
                    i = len(text)
                    break
                parts.append(text[i:j + 1])
                i = j + 1
                continue
        if ch == "{" and not declaration:
            break
        if ch == "}" and "{" not in stack:
            break
        if ch == ";" and not stack:
            break
        if ch in _CLOSERS:
            stack.append(ch)
        elif ch in ")]}":
            if stack and _CLOSERS[stack[-1]] == ch:
                stack.pop()
            else:
                problem = problem or f"unbalanced {ch!r}"
                if ch == "}":
                    while stack and stack.pop() != "{":
                        pass
        parts.append(ch)
        i += 1
    if stack:
        problem = problem or f"unbalanced {stack[-1]!r}"
    return "".join(parts), i, problem


def _css_decls(raw: str) -> list[tuple[str, str, str | None]]:
    """List every `--name: value` declaration as (name, value, problem).

    Only a statement that STARTS with `--name:` is a declaration, so
    custom-property-looking text inside an at-rule prelude or a selector is
    never read as a token.
    """
    decls: list[tuple[str, str, str | None]] = []
    i = 0
    while i < len(raw):
        if raw[i].isspace() or raw[i] in "{};":
            i += 1
            continue
        if raw.startswith("/*", i):
            end = raw.find("*/", i + 2)
            i = len(raw) if end < 0 else end + 2
            continue
        match = _CSS_DECL_START_RE.match(raw, i)
        if match:
            value, i, problem = _scan_statement(raw, match.end(), declaration=True)
            decls.append((match.group(1), value, problem))
        else:
            _text, i, _problem = _scan_statement(raw, i, declaration=False)
    return decls


def _css_tokens(raw: str) -> dict:
    """Collect `--name: value` declarations; flag redefinitions and bad syntax.

    A name defined twice with different values carries `conflict`; a
    declaration whose value has an unterminated string/url( or an unbalanced
    bracket carries `invalid` (the reason). Both resolve as UNRESOLVED.
    """
    seen: dict[str, list[str]] = {}
    invalid: dict[str, str] = {}
    for name, value, problem in _css_decls(raw):
        value = " ".join(re.sub(r"!\s*important\s*$", "", value.strip(), flags=re.I).split())
        if problem and name not in invalid:
            invalid[name] = f"CSS value does not parse ({problem}): {value!r}"
        if value not in seen.setdefault(name, []):
            seen[name].append(value)
    return {name: {"raw": vals[0], "type": None, "conflict": vals if len(vals) > 1 else None,
                   "invalid": invalid.get(name)}
            for name, vals in seen.items()}


def load_side(path: str | None) -> _Side | None:
    """Load one side, or None (missing, unreadable, empty, invalid, no tokens).

    None is the single fail-closed signal: a caller must map it to
    COULD_NOT_CHECK, never treat it as an empty-but-valid side.
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
            tokens, fmt = _dtcg_tokens(json.loads(raw)), "dtcg"
        except (ValueError, RecursionError):
            return None
    else:
        tokens, fmt = _css_tokens(raw), "css"
    return _Side(path, fmt, tokens) if tokens else None


def _channel(part: str) -> float | None:
    """An rgb() channel ("255" or "50%") on the 0-255 scale, clamped."""
    match = re.fullmatch(rf"({_NUM})(%?)", part)
    if not match:
        return None
    value = float(match.group(1)) * (2.55 if match.group(2) else 1.0)
    return min(255.0, max(0.0, value))


def _fraction(part: str, bare_scale: float) -> float | None:
    """A percentage ("40%") or bare number (divided by `bare_scale`) as 0-1."""
    match = re.fullmatch(rf"({_NUM})(%?)", part)
    if not match:
        return None
    value = float(match.group(1)) / (100.0 if match.group(2) else bare_scale)
    return min(1.0, max(0.0, value))


def _hue(part: str) -> float | None:
    """An hsl() hue in degrees (unitless, deg, turn, rad)."""
    match = re.fullmatch(rf"({_NUM})(deg|turn|rad)?", part)
    if not match:
        return None
    scale = {"turn": 360.0, "rad": 180.0 / math.pi}.get(match.group(2) or "", 1.0)
    return float(match.group(1)) * scale


def parse_color(value: object) -> tuple | None:
    """Parse a color into ("color", r, g, b, a) (0-255 floats, alpha 0-1).

    Returns None when `value` is not color syntax at all; raises Unresolved
    for a DTCG color object it recognizes but cannot convert exactly (a
    non-srgb colorSpace) — its `hex` field is a lossy fallback, not used.
    """
    if isinstance(value, dict):
        if "colorSpace" not in value:
            return None
        if value.get("colorSpace") != "srgb":
            raise Unresolved(f"colorSpace {value.get('colorSpace')!r} not supported (only 'srgb')")
        comps, alpha = value.get("components"), value.get("alpha", 1)
        if not (isinstance(comps, list) and len(comps) == 3 and all(map(_isnum, comps))
                and _isnum(alpha)):
            raise Unresolved("srgb color needs 3 numeric components and a numeric alpha")
        return ("color", *(float(c) * 255 for c in comps), float(alpha))
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if text in _NAMED_COLORS:
        return _NAMED_COLORS[text]
    hexm = re.fullmatch(r"#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})", text)
    if hexm:
        digits = hexm.group(1)
        if len(digits) <= 4:
            digits = "".join(c * 2 for c in digits)
        vals = [int(digits[i:i + 2], 16) for i in range(0, len(digits), 2)]
        return ("color", *map(float, vals[:3]), vals[3] / 255 if len(vals) == 4 else 1.0)
    fnm = re.fullmatch(r"(rgba?|hsla?)\((.*)\)", text)
    if not fnm:
        return None
    parts = fnm.group(2).replace("/", " / ").replace(",", " ").split()
    alpha_part = None
    if "/" in parts:
        cut = parts.index("/")
        if len(parts) != cut + 2:
            return None
        parts, alpha_part = parts[:cut], parts[cut + 1]
    elif len(parts) == 4:
        alpha_part = parts.pop()
    if len(parts) != 3:
        return None
    alpha = 1.0 if alpha_part is None else _fraction(alpha_part, 1.0)
    if fnm.group(1).startswith("rgb"):
        chans = [_channel(p) for p in parts]
    else:
        hue, sat, light = _hue(parts[0]), _fraction(parts[1], 100.0), _fraction(parts[2], 100.0)
        if None in (hue, sat, light):
            return None

        def conv(n: int) -> float:
            """CSS Color 4 hsl->rgb for one channel, on the 0-255 scale."""
            k = (n + hue / 30) % 12
            return 255 * (light - sat * min(light, 1 - light) * max(-1, min(k - 3, 9 - k, 1)))

        chans = [conv(0), conv(8), conv(4)]
    if alpha is None or None in chans:
        return None
    return ("color", *chans, alpha)


def parse_dimension(value: object, root_px: float) -> tuple | None:
    """Parse "16px" / "1rem" / "200ms" / {"value", "unit"} to ("dim", unit, n).

    px and rem both canonicalize to px (rem x root_px); s and ms to ms; any
    other unit is kept as-is and only equals the same unit. Unitless -> None.
    """
    if isinstance(value, dict) and set(value) == {"value", "unit"}:
        if not (_isnum(value["value"]) and isinstance(value["unit"], str)):
            return None
        num, unit = float(value["value"]), value["unit"].strip().lower()
    elif isinstance(value, str):
        match = re.fullmatch(rf"({_NUM})([a-z%]+)", value.strip().lower())
        if not match:
            return None
        num, unit = float(match.group(1)), match.group(2)
    else:
        return None
    factor = {"px": ("px", 1.0), "rem": ("px", root_px), "ms": ("ms", 1.0), "s": ("ms", 1000.0)}
    canon_unit, mult = factor.get(unit, (unit, 1.0))
    return ("dim", canon_unit, num * mult)


def normalize(value: object, ttype: str | None, root_px: float) -> tuple:
    """Canonicalize one resolved value under a `$type` (raises Unresolved)."""
    if ttype == "color":
        canon = parse_color(value)
        if canon is None:
            raise Unresolved(f"not a recognized color: {value!r}")
        return canon
    if ttype in ("dimension", "duration"):
        if (_isnum(value) and value == 0) or (isinstance(value, str)
                                               and re.fullmatch(r"[+-]?0*\.?0+", value.strip())):
            return ("dim", "px" if ttype == "dimension" else "ms", 0.0)
        canon = parse_dimension(value, root_px)
        if canon is None:
            raise Unresolved(f"not a {ttype} with a unit: {value!r}")
        return canon
    if ttype == "fontWeight":
        text = str(value).strip().lower()
        num = _WEIGHTS.get(text)
        if num is None and re.fullmatch(_NUM, text):
            num = float(text)
        if num is None or not 1 <= num <= 1000:
            raise Unresolved(f"not a fontWeight (1-1000 or a DTCG keyword): {value!r}")
        return ("weight", float(num))
    if ttype == "fontFamily":
        names = _split_top_level(value) if isinstance(value, str) else value
        if not (isinstance(names, list) and names and all(isinstance(n, str) for n in names)):
            raise Unresolved(f"not a fontFamily (string or list of strings): {value!r}")
        cleaned = tuple(n.strip().strip("'\"").strip().lower() for n in names)
        if not all(cleaned):
            raise Unresolved(f"empty font family name in {value!r}")
        return ("family", cleaned)
    if ttype == "number":
        if _isnum(value) or (isinstance(value, str) and re.fullmatch(_NUM, value.strip())):
            return ("num", float(value))
        raise Unresolved(f"not a number: {value!r}")
    return _infer(value, root_px)


def _infer(value: object, root_px: float) -> tuple:
    """Canonicalize an untyped (or composite-typed) value structurally."""
    if isinstance(value, bool) or value is None:
        return ("str", json.dumps(value))
    if _isnum(value):
        return ("num", float(value))
    if isinstance(value, dict):
        canon = parse_color(value) or parse_dimension(value, root_px)
        if canon:
            return canon
        return ("map", tuple(sorted(
            (k, normalize(v, _KEY_HINTS.get(k), root_px)) for k, v in value.items())))
    if isinstance(value, list):
        return ("list", tuple(_infer(v, root_px) for v in value))
    text = str(value).strip()
    canon = parse_color(text) or parse_dimension(text, root_px)
    if canon:
        return canon
    if re.fullmatch(_NUM, text):
        return ("num", float(text))
    return ("str", re.sub(r"\s*,\s*", ",", " ".join(text.split())))


def _equal(a: tuple, b: tuple) -> bool:
    """Canonical equality; colors allow half an 8-bit step for float rounding."""
    if a[0] != b[0]:
        return False
    kind = a[0]
    if kind == "color":
        return (all(abs(x - y) <= 0.5 + 1e-6 for x, y in zip(a[1:4], b[1:4]))
                and abs(a[4] - b[4]) <= 0.5 / 255 + 1e-6)
    if kind == "dim":
        return a[1] == b[1] and abs(a[2] - b[2]) <= 1e-4
    if kind in ("num", "weight"):
        return abs(a[1] - b[1]) <= 1e-4
    if kind == "map":
        return ([k for k, _ in a[1]] == [k for k, _ in b[1]]
                and all(_equal(x, y) for (_, x), (_, y) in zip(a[1], b[1])))
    if kind == "list":
        return len(a[1]) == len(b[1]) and all(_equal(x, y) for x, y in zip(a[1], b[1]))
    return a[1] == b[1]


def _fmt(c: tuple) -> str:
    """Render a canonical value for the report."""
    def num(x: float) -> str:
        """Compact number."""
        return f"{round(x, 4):g}"
    kind = c[0]
    if kind == "color":
        return "rgba({},{},{},{})".format(*(int(x + 0.5) for x in c[1:4]), num(round(c[4], 3)))
    if kind == "dim":
        return f"{num(c[2])}{c[1]}"
    if kind in ("num", "weight"):
        return num(c[1])
    if kind == "family":
        return ", ".join(c[1])
    if kind == "map":
        return "{" + ", ".join(f"{k}: {_fmt(v)}" for k, v in c[1]) + "}"
    if kind == "list":
        return "[" + ", ".join(_fmt(v) for v in c[1]) + "]"
    return c[1]


def _fold(name: str) -> str:
    """Name-mode key: `color.brand` == `--color-brand` == `Color_Brand`."""
    return re.sub(r"[._/\s]+", "-", name.lstrip("-").lower())


def _load_map(path: str) -> list[tuple[str, str, str | None]]:
    """Parse a --map TSV; raises ValueError (-> COULD_NOT_CHECK) on any defect."""
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"--map unreadable ({path!r}): {exc}") from None
    rows = []
    for lineno, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = [f.strip() for f in line.split("\t")]
        if len(fields) not in (2, 3) or not all(fields):
            raise ValueError(f"--map line {lineno} is not 'design<TAB>app[<TAB>type]': {line!r}")
        if len(fields) == 3 and fields[2] not in _DTCG_TYPES:
            raise ValueError(f"--map line {lineno}: unknown $type {fields[2]!r} (expected one of "
                             f"{', '.join(sorted(_DTCG_TYPES))})")
        rows.append((fields[0], fields[1], fields[2] if len(fields) == 3 else None))
    if not rows:
        raise ValueError(f"--map has no rows ({path!r})")
    return rows


def _compare_one(design: _Side, dname: str | None, app: _Side, aname: str | None,
                 override: str | None, root_px: float) -> tuple[str, str]:
    """Classify one design->app pair into (status, detail)."""
    try:
        if dname is None:
            raise Unresolved("design token is not defined")
        dval = design.resolve(dname)
    except Unresolved as exc:
        return "UNRESOLVED", f"design side: {exc}"
    if aname is None:
        return "MISSING_IN_APP", "no app counterpart"
    try:
        aval = app.resolve(aname)
    except Unresolved as exc:
        return "UNRESOLVED", f"app side: {exc}"
    dtype, atype = design.type_of(dname), app.type_of(aname)
    # An override types an untyped side; it never silences a declared-type
    # disagreement, and it cannot overrule a type a side declares.
    if dtype and atype and dtype != atype:
        return "MISMATCH", f"declared $type differs: design {dtype} vs app {atype}"
    for side, declared in (("design", dtype), ("app", atype)):
        if override and declared and declared != override:
            return "UNRESOLVED", (f"--map $type {override} contradicts the {side} side's "
                                  f"declared $type {declared}")
    ttype = override or dtype or atype
    try:
        dcanon = normalize(dval, ttype, root_px)
    except Unresolved as exc:
        return "UNRESOLVED", f"design side: {exc}"
    try:
        acanon = normalize(aval, ttype, root_px)
    except Unresolved as exc:
        return "UNRESOLVED", f"app side: {exc}"
    composite = ("map", "list")
    if (dcanon[0] in composite) != (acanon[0] in composite):
        return "UNRESOLVED", "composite value vs scalar value; not comparable"
    if _equal(dcanon, acanon):
        return "MATCH", _fmt(dcanon)
    return "MISMATCH", f"design={_fmt(dcanon)} app={_fmt(acanon)}"


def compare(design_path: str | None, app_path: str | None, map_path: str | None = None,
            root_px: float = 16.0) -> tuple[int, list[tuple[str, str]], str]:
    """Diff two sides; return (exit_code, [(design_name, status)], report).

    Two-sided or no verdict: an unloadable side or --map returns
    COULD_NOT_CHECK before any token is compared.
    """
    design = load_side(design_path)
    if design is None:
        return COULD_NOT_CHECK, [], (
            f"COULD_NOT_CHECK: design side missing, unreadable, invalid, or has no tokens "
            f"({design_path!r}). Two-sided input is required; this is never a pass.")
    app = load_side(app_path)
    if app is None:
        return COULD_NOT_CHECK, [], (
            f"COULD_NOT_CHECK: app side missing, unreadable, invalid, or has no tokens "
            f"({app_path!r}). Two-sided input is required; this is never a pass.")

    info: list[str] = []
    # (design name, stored design name, app label, stored app name, $type
    # override, pre-decided (status, detail) or None)
    pairs: list[tuple] = []
    if map_path:
        try:
            rows = _load_map(map_path)
        except ValueError as exc:
            return COULD_NOT_CHECK, [], f"COULD_NOT_CHECK: {exc}. Never a pass."
        for dn, an, override in rows:
            pairs.append((dn, design.lookup(dn), an, app.lookup(an), override, None))
        used_app = {p[3] for p in pairs}
        unmapped = len(set(design.tokens) - {p[1] for p in pairs})
        if unmapped:
            info.append(f"info: {unmapped} design token(s) not in --map (not compared)")
    else:
        dkeys: dict[str, list[str]] = {}
        akeys: dict[str, list[str]] = {}
        for n in design.tokens:
            dkeys.setdefault(_fold(n), []).append(n)
        for n in app.tokens:
            akeys.setdefault(_fold(n), []).append(n)
        used_app = set()
        for dn in design.tokens:
            key = _fold(dn)
            cands = akeys.get(key, [])
            used_app.update(cands)
            if len(dkeys[key]) > 1 or len(cands) > 1:
                pre = ("UNRESOLVED", "name collision after case/separator folding: "
                       + ", ".join(dkeys[key] + cands))
                pairs.append((dn, dn, ", ".join(cands) or "?", None, None, pre))
            else:
                only = cands[0] if cands else None
                pairs.append((dn, dn, only or "?", only, None, None))
    app_only = [n for n in app.tokens if n not in used_app]
    if app_only:
        shown = ", ".join(app_only[:10]) + (" ..." if len(app_only) > 10 else "")
        info.append(f"info: {len(app_only)} app-only token(s), not compared and never a "
                    f"failure: {shown}")

    lines, results = [], []
    for dn, dstored, an, astored, override, pre in pairs:
        status, detail = pre or _compare_one(design, dstored, app, astored, override, root_px)
        results.append((dn, status))
        lines.append(f"{status:<15} {dn} -> {an}  {detail}")
    counts = {s: sum(1 for _, st in results if st == s)
              for s in ("MATCH", "MISMATCH", "MISSING_IN_APP", "UNRESOLVED")}
    code = MATCH if counts["MATCH"] == len(results) and results else MISMATCH
    header = (f"TOKEN PARITY: {'MATCH' if code == MATCH else 'MISMATCH'} — design={design_path} "
              f"({design.fmt}) app={app_path} ({app.fmt})"
              + (f" map={map_path}" if map_path else "") + f" root_px={root_px:g}")
    summary = (f"counts: compared={len(results)} match={counts['MATCH']} "
               f"mismatch={counts['MISMATCH']} missing_in_app={counts['MISSING_IN_APP']} "
               f"unresolved={counts['UNRESOLVED']}")
    scope = ("scope: verifies resolved token VALUES only, not that components use them; "
             "next run parity_differ.py (sections), screenshots last.")
    return code, results, "\n".join([header, *lines, summary, *info, scope])


def _selftest() -> int:
    """Run planted cases against committed fixtures + temp files; pin every verdict.

    Each case pins the exit code and, for the fixture runs, the exact status of
    every design token — so an edit that turns a fail-closed branch into a pass
    (a cycle that resolves, rem read as px, one side absent passing) fails here.
    """
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "tokens")
    design = os.path.join(here, "design.tokens.json")
    app = os.path.join(here, "app.css")
    mapping = os.path.join(here, "map_match.tsv")
    absent = os.path.join(here, "does-not-exist.json")
    failures: list[str] = []

    def check(label: str, got: tuple, want_code: int, want: dict | None = None,
              must_have: tuple[str, ...] = ()) -> None:
        """Assert one case's exit code, per-token statuses, and report substrings."""
        code, results, report = got
        if code != want_code:
            failures.append(f"{label}: exit {code}, want {want_code}")
        if want is not None and dict(results) != want:
            diff = {k: (dict(results).get(k), v) for k, v in want.items() if dict(results).get(k) != v}
            extra = set(dict(results)) - set(want)
            failures.append(f"{label}: status (got, want) {diff} extra {sorted(extra)}")
        for needle in must_have:
            if needle not in report:
                failures.append(f"{label}: report missing {needle!r}")

    matching = ["color.brand.primary", "color.brand.accent", "color.surface", "color.overlay",
                "color.link", "color.info", "color.focus", "spacing.md", "spacing.sm",
                "font.weight.bold", "font.family.body", "motion.fast"]
    want_full = {n: "MATCH" for n in matching}
    want_full.update({"color.text": "UNRESOLVED", "color.legacy": "MISSING_IN_APP",
                      "radius.lg": "MISMATCH", "radius.sm": "UNRESOLVED",
                      "loop.a": "UNRESOLVED", "loop.b": "UNRESOLVED"})
    check("full", compare(design, app), MISMATCH, want_full,
          ("reference cycle: loop.a -> loop.b -> loop.a", "design=12px app=10px",
           "defined more than once", "app-only token(s)", "--app-only-shadow",
           "counts: compared=18 match=12 mismatch=1 missing_in_app=1 unresolved=4",
           "VALUES only"))
    want_map = {n: "MATCH" for n in matching if n != "color.brand.accent"}
    check("mapped", compare(design, app, mapping), MATCH, want_map)
    # rem conversion is load-bearing: a wrong root size must flip rem rows.
    check("root-px", compare(design, app, mapping, root_px=10.0), MISMATCH,
          {**want_map, "spacing.md": "MISMATCH", "spacing.sm": "MISMATCH"})
    check("design-absent", compare(absent, app), COULD_NOT_CHECK, {})
    check("app-absent", compare(design, absent), COULD_NOT_CHECK, {})
    check("map-absent", compare(design, app, absent), COULD_NOT_CHECK, {})

    with tempfile.TemporaryDirectory() as tmp:
        def put(name: str, text: str) -> str:
            """Write one temp fixture and return its path."""
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            return path

        d_css = put("d.css", ":root { --c: #0066cc; --w: bold; }")
        a_css = put("a.css", ":root { --c: rgb(0, 102, 204); --w: 700; }")
        typed = put("typed.tsv", "--c\t--c\n--w\t--w\tfontWeight\n")
        check("css-untyped", compare(d_css, a_css), MISMATCH, {"--c": "MATCH", "--w": "MISMATCH"})
        check("css-map-type", compare(d_css, a_css, typed), MATCH, {"--c": "MATCH", "--w": "MATCH"})
        check("empty-side", compare(put("e.css", "  \n"), a_css), COULD_NOT_CHECK, {})
        check("invalid-json", compare(put("bad.json", "{nope"), a_css), COULD_NOT_CHECK, {})
        check("no-tokens-json", compare(put("flat.json", '{"c": "#fff"}'), a_css),
              COULD_NOT_CHECK, {})
        check("bad-map", compare(d_css, a_css, put("bad.tsv", "--c only-one-field-no-tab\n")),
              COULD_NOT_CHECK, {})
        check("fold-collision", compare(put("dup.css", "--brand-a: #fff; --Brand_A: #fff;"),
                                        put("one.css", "--brand-a: #fff;")), MISMATCH,
              {"--brand-a": "UNRESOLVED", "--Brand_A": "UNRESOLVED"}, ("name collision",))
        dangling = put("dangling.json", '{"c": {"$type": "color", "$value": "{nope.x}"}}')
        check("dangling-alias", compare(dangling, put("c.css", "--c: #fff;")), MISMATCH,
              {"c": "UNRESOLVED"}, ("'nope.x' is not defined",))

        # CSS values are tokenized respecting quotes and brackets: a `;`
        # inside a string or url() must not truncate the value (a truncated
        # prefix would compare equal on both sides and hide the difference).
        check("css-data-url", compare(
            put("durl-d.css", ":root { --icon: url(\"data:image/svg+xml;utf8,<svg fill='red'/>\");"
                              " --icon-raw: url(data:image/svg+xml;utf8,%3Csvg%20fill=red%3E); }"),
            put("durl-a.css", ":root { --icon: url(\"data:image/svg+xml;utf8,<svg fill='blue'/>\");"
                              " --icon-raw: url(data:image/svg+xml;utf8,%3Csvg%20fill=blue%3E); }")),
            MISMATCH, {"--icon": "MISMATCH", "--icon-raw": "MISMATCH"}, ("fill='blue'", "fill=blue"))
        check("css-quoted-semicolon", compare(
            put("q-d.css", ':root { --f: "A;B", serif; --g: "A;B", serif; --k: #fff; --s: "var(--k)"; }'),
            put("q-a.css", ':root { --f: "A;C", serif; --g: "A;B", serif; --k: #fff; --s: "#fff"; }')),
            MISMATCH, {"--f": "MISMATCH", "--g": "MATCH", "--k": "MATCH", "--s": "MISMATCH"},
            ('design="A;B",serif app="A;C",serif',))
        fam_map = put("fam.tsv", "--h\t--h\tfontFamily\n")
        check("css-family-quoted-comma", compare(
            put("fam-d.css", '--h: "A,B", serif;'), put("fam-a.css", '--h: "A", "B", serif;'),
            fam_map), MISMATCH, {"--h": "MISMATCH"}, ("design=a,b, serif app=a, b, serif",))
        # Custom-property-looking text in an at-rule prelude is not a token.
        check("css-container-prelude", compare(
            put("cq-d.css", "@container style(--theme: dark) { :root { --c: #fff; } }"),
            put("cq-a.css", ":root { --c: #fff; }")), MATCH, {"--c": "MATCH"})
        # Unbalanced quote / bracket / url( -> UNRESOLVED on that token only.
        check("css-unbalanced", compare(
            put("ub-d.css", ':root { --p: rgb(1, 2, 3; }\n:root { --w: #fff; }\n--u: "abc;'),
            put("ub-a.css", ':root { --p: rgb(1, 2, 3); --w: #fff; --u: "abc"; }')),
            MISMATCH, {"--p": "UNRESOLVED", "--w": "MATCH", "--u": "UNRESOLVED"},
            ("unbalanced '('", "unterminated quoted string"))
        check("css-unterminated-url", compare(
            put("uu-d.css", "--q: url(data:a;b"), put("uu-a.css", "--q: url(data:a;b);")),
            MISMATCH, {"--q": "UNRESOLVED"}, ("unterminated url(",))

        # A --map $type must be a DTCG type, and an override never silences
        # a declared-type disagreement or overrules a declared type.
        check("map-unknown-type", compare(d_css, a_css, put("colour.tsv", "--c\t--c\tcolour\n")),
              COULD_NOT_CHECK, {}, ("unknown $type 'colour'",))
        weight_json = put("w-d.json", '{"w": {"$type": "fontWeight", "$value": 700}}')
        check("map-type-keeps-declared-conflict", compare(
            weight_json, put("w-a.json", '{"w": {"$type": "number", "$value": 700}}'),
            put("num.tsv", "w\tw\tnumber\n")), MISMATCH, {"w": "MISMATCH"},
            ("declared $type differs: design fontWeight vs app number",))
        check("map-type-contradicts-declared", compare(
            weight_json, put("w-a.css", "--w: 700;"), put("num2.tsv", "w\t--w\tnumber\n")),
            MISMATCH, {"w": "UNRESOLVED"},
            ("--map $type number contradicts the design side's declared $type fontWeight",))

    if failures:
        print("SELFTEST FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("SELFTEST OK: full=1 (12 match, mismatch, missing, 2 cycles, conflict) mapped=0 "
          "root-px=1 css-untyped=1 css-map-type=0 fold-collision=1 dangling-alias=1 "
          "css-data-url=1 css-quoted-semicolon=1 css-family-quoted-comma=1 "
          "css-container-prelude=0 css-unbalanced=1 css-unterminated-url=1 "
          "map-type-keeps-declared-conflict=1 map-type-contradicts-declared=1 "
          "refuse(absent/empty/invalid/no-tokens/bad-map/map-unknown-type)=2")
    return 0


def _positive_float(text: str) -> float:
    """argparse type: a finite float > 0."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from None
    if not (math.isfinite(value) and value > 0):
        raise argparse.ArgumentTypeError(f"must be > 0: {text!r}")
    return value


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: `--selftest`, or `--design <f> --app <f>` (two-sided only)."""
    parser = argparse.ArgumentParser(
        description="Design<->app token VALUE parity gate. MATCH (exit 0) is the only pass.")
    parser.add_argument("--design", help="design tokens: DTCG .json or CSS custom properties")
    parser.add_argument("--app", help="app tokens: DTCG .json or CSS custom properties")
    parser.add_argument("--map", help="TSV design<TAB>app[<TAB>type]; compare only these rows")
    parser.add_argument("--root-px", type=_positive_float, default=16.0,
                        help="px per rem (default 16)")
    parser.add_argument("--selftest", action="store_true", help="run the planted-case self-test")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.design or not args.app:
        parser.error("--design and --app are both required (two-sided input, or no verdict)")
    code, _results, report = compare(args.design, args.app, args.map, args.root_px)
    print(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
