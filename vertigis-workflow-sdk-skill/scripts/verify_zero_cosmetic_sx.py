#!/usr/bin/env python3
"""verify_zero_cosmetic_sx.py - Zero-Cosmetic-SX, 8px spacing grid and non-MUI containment.

Single implementation of three rules:
  NO_COSMETIC_SX       cosmetic keys (borders, radii, backgrounds, shadows, colour, typography) in
                       sx / style / styles dictionaries / styled(); they belong in src/tokens/muiTheme.ts.
  STANDARDIZED_SPACING spacing values off the MUI 8px grid (0, 0.5, 1, 1.5, 2, 2.5, 3, 4), raw lengths.
  NON_MUI_CONTAINMENT  <canvas>, <img>, <iframe> whose nearest JSX parent is not Paper or Card.

The skill validators (checks_tsx.py) import check_source() from this file, and projects run it
standalone via `npm run verify:styles`, so both always agree. Identical copy in both VertiGIS SDK
skills and both SDK templates. Standard library only.

Usage:    python scripts/verify_zero_cosmetic_sx.py [project-dir-or-file]   (default: .)
Suppress: // vertigis-rule-disable RULE_ID -- <reason>   (this or the previous line)
          /* vertigis-rule-disable-file RULE_ID -- <reason> */
Exit:     0 clean, 1 violations, 2 bad arguments.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

BANNED_COSMETIC_PROPERTIES = frozenset({
    # Borders & outlines
    "border", "borderWidth", "borderStyle", "borderColor",
    "borderTop", "borderBottom", "borderLeft", "borderRight",
    "borderTopWidth", "borderBottomWidth", "borderLeftWidth", "borderRightWidth",
    "borderTopStyle", "borderBottomStyle", "borderLeftStyle", "borderRightStyle",
    "borderTopColor", "borderBottomColor", "borderLeftColor", "borderRightColor",
    "outline", "outlineColor", "outlineWidth", "outlineStyle",
    # Corner radii
    "borderRadius", "borderTopLeftRadius", "borderTopRightRadius",
    "borderBottomLeftRadius", "borderBottomRightRadius",
    # Backgrounds & layers
    "background", "backgroundColor", "bgcolor", "bgColor",
    "backgroundImage", "backgroundSize", "backgroundPosition", "backgroundRepeat",
    "backdropFilter",
    # Shadows & elevation
    "boxShadow", "textShadow", "filter",
    # Colour & typography (use <Typography variant=...> and the color prop)
    "color", "textColor", "textDecoration", "textTransform",
    "fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing",
})
SPACING_PROPERTIES = frozenset({
    "p", "px", "py", "pt", "pb", "pl", "pr",
    "padding", "paddingTop", "paddingBottom", "paddingLeft", "paddingRight", "paddingX", "paddingY",
    "gap", "rowGap", "columnGap",
    "m", "mx", "my", "mt", "mb", "ml", "mr",
    "margin", "marginTop", "marginBottom", "marginLeft", "marginRight", "marginX", "marginY",
})
SPACING_ATTRIBUTES = SPACING_PROPERTIES | {"spacing", "rowSpacing", "columnSpacing"}
SYSTEM_PROP_TAGS = frozenset({"Box", "Stack", "Grid", "Container"})
ALLOWED_SPACING_STEPS = (0, 0.5, 1, 1.5, 2, 2.5, 3, 4)
SPACING_KEYWORDS = {"auto", "0", "inherit", "initial", "unset"}
NON_MUI_ELEMENTS = frozenset({"canvas", "img", "iframe"})
MUI_CONTAINERS = frozenset({"Paper", "Card", "CardContent", "CardMedia", "CardActionArea"})
RULES = ("NO_COSMETIC_SX", "STANDARDIZED_SPACING", "NON_MUI_CONTAINMENT", "MARGIN_LEAKAGE")

SKIP_DIRS = {"node_modules", "dist", "build", "coverage", ".git", ".tgrep", ".venv", "__pycache__"}
NUMBER = re.compile(r"-?(\d+(\.\d+)?|\.\d+)")
QUOTED = re.compile(r"([\"'`])(.*)\1", re.S)
LENGTH = re.compile(r"(?<![\w.-])-?(\d*\.\d+|\d+)(px|rem|em|%|vh|vw|vmin|vmax|ch|ex|pt)(?![\w.%])")
VAR_CALL = re.compile(r"var\((?:[^()]|\([^()]*\))*\)")
SPACING_CALL = re.compile(r"\bspacing\(([^()]*)\)")
ENTRY = re.compile(r"(?:([\"'])(.*?)\1|(\[[^\]]*\])|([\w$]+))\s*:(?!:)\s*(.*)", re.S)
IDENT = re.compile(r"[\w$]+")
TAG_START = re.compile(r"<([A-Za-z][\w.]*)")
CLOSE_TAG = re.compile(r"</([A-Za-z][\w.]*)\s*>")
STYLE_ATTR = re.compile(r"(?<![\w$.-])(sx|style)\s*=\s*(?=\{)")
SX_PROPERTY = re.compile(r"(?<![\w$.])[\"']?sx[\"']?\s*:\s*(?=[{\[(])")
STYLE_DICT = re.compile(r"\b(?:const|let|var)\s+(?:[\w$]*(?:[sS]tyles|Sx|SX)|sx[A-Z][\w$]*)\b[^=;]*=\s*")
ANY_CONST = re.compile(r"\b(?:const|let|var)\s+[\w$]+\b[^=;]*=\s*")
STYLED_CALL = re.compile(r"\bstyled\s*\(")
SUPPRESSION = re.compile(r"vertigis-rule-disable(-file)?\s+([A-Z_]+)\s*--\s*\S")


# ---------------------------------------------------------------- lexical helpers

def blank_comments(text: str) -> str:
    """Replace // and /* */ comments with spaces, keeping offsets and newlines."""
    out, i, n, quote = list(text), 0, len(text), None
    while i < n:
        c, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if quote is None and c == "/" and nxt and nxt in "*/":
            end = text.find("*/", i + 2) + 2 if nxt == "*" else text.find("\n", i)
            end = n if end < (2 if nxt == "*" else 0) else end
            for k in range(i, end):
                if out[k] != "\n":
                    out[k] = " "
            i = end
            continue
        if quote is None and c in "\"'`":
            quote = c
        elif quote is not None and c == "\\":
            i += 1
        elif c == quote or (c == "\n" and quote not in (None, "`")):
            quote = None
        i += 1
    return "".join(out)


def skip_string(text: str, i: int) -> int:
    quote, j = text[i], i + 1
    while j < len(text) and text[j] != quote:
        j += 2 if text[j] == "\\" else 1
    return j + 1


def matching_close(text: str, open_index: int) -> int:
    """Index of the bracket closing text[open_index]; -1 if unbalanced."""
    pairs, stack, i = {"{": "}", "(": ")", "[": "]"}, [], open_index
    while i < len(text):
        c = text[i]
        if c in "\"'`":
            i = skip_string(text, i)
            continue
        if c in pairs:
            stack.append(pairs[c])
        elif stack and c == stack[-1]:
            stack.pop()
            if not stack:
                return i
        i += 1
    return -1


def split_top(text: str, base: int) -> list[tuple[int, str]]:
    """Split on top-level commas; returns (absolute offset, stripped part)."""
    parts, depth, start, i = [], 0, 0, 0
    while i <= len(text):
        c = text[i] if i < len(text) else ","
        if c in "\"'`" and i < len(text):
            i = skip_string(text, i)
            continue
        if c in "{([":
            depth += 1
        elif c in "})]":
            depth -= 1
        elif c == "," and depth == 0:
            chunk = text[start:i]
            if chunk.strip():
                parts.append((base + start + len(chunk) - len(chunk.lstrip()), chunk.strip()))
            start = i + 1
        i += 1
    return parts


def object_literals(code: str, start: int, end: int):
    """Yield (open_index, close_index) of the outermost {...} literals in code[start:end]."""
    i = start
    while i < end:
        c = code[i]
        if c in "\"'`":
            i = skip_string(code, i)
            continue
        if c == "{":
            close = matching_close(code, i)
            if close < 0:
                return
            yield i, close
            i = close
        i += 1


# ---------------------------------------------------------------- value checks

def strip_var_calls(text: str) -> str:
    previous = None
    while previous != text:
        previous, text = text, VAR_CALL.sub("", text)
    return text


def off_grid(number: str) -> bool:
    return abs(float(number)) not in ALLOWED_SPACING_STEPS


def spacing_problem(value: str) -> str | None:
    """Why a spacing value breaks the 8px grid, or None when it is fine or not statically known."""
    v = value.strip().rstrip(";").strip()
    if re.search(r"\bSPACING\.\w+", v):
        return None
    if v.startswith(("[", "{")) and matching_close(v, 0) == len(v) - 1:
        items = [p for _, p in split_top(v[1:-1], 0)]
        items = [ENTRY.fullmatch(p).group(5) if v[0] == "{" and ENTRY.fullmatch(p) else p for p in items]
        return next((problem for problem in map(spacing_problem, items) if problem), None)
    if NUMBER.fullmatch(v):
        return f"{v} is not a grid step {ALLOWED_SPACING_STEPS}" if off_grid(v) else None
    quoted = QUOTED.fullmatch(v)
    if quoted:
        text = quoted.group(2).strip()
        if text in SPACING_KEYWORDS:
            return None
        if any(float(n) != 0 for n, _ in LENGTH.findall(strip_var_calls(text))) or NUMBER.fullmatch(text):
            return f"raw length {v}; use a grid step number {ALLOWED_SPACING_STEPS}"
        return None
    for call in SPACING_CALL.finditer(v):
        bad = [n for n in re.split(r"\s*,\s*", call.group(1).strip()) if NUMBER.fullmatch(n) and off_grid(n)]
        if bad:
            return f"spacing({call.group(1)}) is off the grid"
    return None


def walk_object(code: str, open_index: int, close_index: int, found: list) -> None:
    """Check every key of an sx/style object literal, descending into selectors, breakpoints and spreads."""
    for offset, part in split_top(code[open_index + 1:close_index], open_index + 1):
        entry = ENTRY.fullmatch(part)
        if not entry:
            if IDENT.fullmatch(part) and part in BANNED_COSMETIC_PROPERTIES:
                found.append(("NO_COSMETIC_SX", offset, f"{part} (shorthand)"))
            else:
                walk_expression(code, offset, offset + len(part), found)
            continue
        key, value = entry.group(2) if entry.group(1) else entry.group(4), entry.group(5).strip()
        value_start = offset + len(part) - len(value)
        if key in BANNED_COSMETIC_PROPERTIES:
            found.append(("NO_COSMETIC_SX", offset, f"{key}: {value[:60]}"))
        elif key in SPACING_PROPERTIES:
            problem = spacing_problem(value)
            if problem:
                found.append(("STANDARDIZED_SPACING", offset, f"{key}: {problem}"))
        else:
            walk_expression(code, value_start, offset + len(part), found)


def walk_expression(code: str, start: int, end: int, found: list) -> None:
    for open_index, close_index in object_literals(code, start, end):
        walk_object(code, open_index, close_index, found)


# ---------------------------------------------------------------- JSX helpers

def jsx_tags(code: str):
    """Yield (name, start, end, attrs) for opening and self-closing JSX tags."""
    for m in TAG_START.finditer(code):
        i = m.start()
        if i and (code[i - 1].isalnum() or code[i - 1] in "_$."):
            continue
        j, depth = m.end(), 0
        while j < len(code) and j - i < 20000:
            c = code[j]
            if c in "\"'`":
                j = skip_string(code, j)
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == ">" and depth == 0:
                break
            elif c == ";" and depth == 0:
                j = len(code)
                break
            j += 1
        if j < len(code):
            yield m.group(1), i, j, code[m.end():j]


def blank_nested(text: str) -> str:
    """Blank string and {...} contents so only top-level attribute names stay visible."""
    out, i = list(text), 0
    while i < len(text):
        if text[i] in "\"'`{":
            close = skip_string(text, i) - 1 if text[i] != "{" else matching_close(text, i)
            close = len(text) - 1 if close < 0 else close
            for k in range(i + 1, close):
                out[k] = " "
            i = close
        i += 1
    return "".join(out)


def attribute(attrs: str, name: str) -> tuple[int, str] | None:
    """(offset, value) of a JSX attribute; braces are stripped from {expr}."""
    m = re.search(rf"(?<![\w$.-]){re.escape(name)}\s*=\s*", blank_nested(attrs))
    if not m:
        return None
    k = m.end()
    if attrs[k:k + 1] == "{":
        close = matching_close(attrs, k)
        return (k + 1, attrs[k + 1:close]) if close > 0 else None
    if attrs[k:k + 1] in ("\"", "'"):
        return k, attrs[k:skip_string(attrs, k)]
    return None


def check_jsx(code: str, found: list) -> None:
    tags = list(jsx_tags(code))
    events = [(start, "open", (name, end, attrs)) for name, start, end, attrs in tags]
    events += [(m.start(), "close", m.group(1)) for m in CLOSE_TAG.finditer(code)]
    stack: list[str] = []
    for start, kind, item in sorted(events, key=lambda e: e[0]):
        if kind == "close":
            if item in stack:
                del stack[len(stack) - 1 - stack[::-1].index(item):]
            continue
        name, end, attrs = item
        if name in NON_MUI_ELEMENTS and (not stack or stack[-1] not in MUI_CONTAINERS):
            parent = stack[-1] if stack else "no parent in this file"
            found.append(("NON_MUI_CONTAINMENT", start, f"<{name}> inside <{parent}>; wrap it in <Paper variant=\"outlined\"> or <Card>"))
        if name in SYSTEM_PROP_TAGS:
            for prop in sorted(SPACING_ATTRIBUTES):
                attr = attribute(attrs, prop)
                problem = spacing_problem(attr[1]) if attr else None
                if problem:
                    found.append(("STANDARDIZED_SPACING", start + len(name) + 1 + attr[0], f"<{name} {prop}>: {problem}"))
        if name == "Stack":
            for m_prop in ("m", "mt", "mb", "my", "mx", "ml", "mr"):
                if attribute(attrs, m_prop):
                    found.append(("MARGIN_LEAKAGE", start, f"<Stack {m_prop}>: external margin on Stack; manage spacing on the parent container"))
            sx_attr = attribute(attrs, "sx")
            if sx_attr:
                for m_prop in ("m", "mt", "mb", "my", "mx", "ml", "mr"):
                    if re.search(rf"(?<![\w$]){m_prop}\s*:", sx_attr[1]):
                        found.append(("MARGIN_LEAKAGE", start, f"<Stack sx.{{{m_prop}}}>: external margin on Stack; manage spacing on the parent container"))
        if name == "Divider" and stack and stack[-1] == "Stack":
            for m_prop in ("m", "mt", "mb", "my"):
                if attribute(attrs, m_prop):
                    found.append(("MARGIN_LEAKAGE", start, f"<Divider {m_prop}>: vertical margin on Divider inside Stack; parent Stack spacing manages separation"))
            sx_attr = attribute(attrs, "sx")
            if sx_attr:
                for m_prop in ("m", "mt", "mb", "my"):
                    if re.search(rf"(?<![\w$]){m_prop}\s*:", sx_attr[1]):
                        found.append(("MARGIN_LEAKAGE", start, f"<Divider sx.{{{m_prop}}}>: vertical margin on Divider inside Stack; parent Stack spacing manages separation"))
        if not code[end - 1] == "/":
            stack.append(name)


# ---------------------------------------------------------------- entry points

def expression_end(code: str, i: int) -> int:
    """Index just past the expression starting at i (stops at a top-level , ; or closing bracket)."""
    depth = 0
    while i < len(code):
        c = code[i]
        if c in "\"'`":
            i = skip_string(code, i)
            continue
        if c in "{([":
            depth += 1
        elif c in "})]":
            if depth == 0:
                return i
            depth -= 1
        elif c in ",;" and depth == 0:
            return i
        i += 1
    return len(code)


def check_source(code: str, rel: str) -> list[tuple[str, int, str]]:
    """Return (rule, index, detail) for comment-blanked TS/TSX source outside src/tokens/."""
    found: list = []
    for m in STYLE_ATTR.finditer(code):
        close = matching_close(code, m.end())
        if close > 0:
            walk_expression(code, m.end() + 1, close, found)
    dictionaries = ANY_CONST if rel.endswith((".styles.ts", ".styles.tsx")) else STYLE_DICT
    for pattern in (SX_PROPERTY, dictionaries):
        for m in pattern.finditer(code):
            walk_expression(code, m.end(), expression_end(code, m.end()), found)
    for m in STYLED_CALL.finditer(code):
        first_close = matching_close(code, m.end() - 1)
        if first_close > 0 and code[first_close + 1:first_close + 2] == "(":
            walk_expression(code, first_close + 1, matching_close(code, first_close + 1), found)
    if rel.endswith(".tsx"):
        check_jsx(code, found)
    unique = {(rule, index): (rule, index, detail) for rule, index, detail in found}
    return sorted(unique.values(), key=lambda v: v[1])


def suppressed(raw: str, rule: str, line: int) -> bool:
    for m in SUPPRESSION.finditer(raw):
        if m.group(2) == rule and (m.group(1) or raw.count("\n", 0, m.start()) + 1 in (line, line - 1)):
            return True
    return False


def source_files(root: Path):
    if root.is_file():
        yield root, root.name
        return
    scan = root / "src" if (root / "src").is_dir() else root
    for dirpath, dirnames, filenames in os.walk(scan):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and d != "tokens")
        for name in sorted(filenames):
            rel = (Path(dirpath) / name).relative_to(root).as_posix()
            if name.endswith((".ts", ".tsx")) and not name.endswith(".d.ts") \
                    and not re.search(r"\.(test|spec)\.tsx?$|(^|/)__tests__/", rel):
                yield Path(dirpath) / name, rel


def main(argv: list[str]) -> int:
    root = Path(argv[0] if argv else ".")
    if not root.exists():
        print(f"path not found: {root}", file=sys.stderr)
        return 2
    violations = []
    for path, rel in source_files(root):
        raw = path.read_text(encoding="utf-8", errors="replace")
        for rule, index, detail in check_source(blank_comments(raw), rel):
            line = raw.count("\n", 0, index) + 1
            if not suppressed(raw, rule, line):
                violations.append(f"{rel}:{line}  {rule}  {detail}")
    if violations:
        print(f"FAIL  Zero-Cosmetic-SX audit: {len(violations)} violation(s)")
        print("\n".join(f"  {v}" for v in violations))
        print("fix: cosmetics -> src/tokens/muiTheme.ts styleOverrides (data-status for state); "
              f"spacing -> grid steps {ALLOWED_SPACING_STEPS}; canvas/img/iframe -> <Paper variant=\"outlined\">.")
        return 1
    print("PASS  Zero-Cosmetic-SX audit: layout-only sx, 8px-grid spacing, non-MUI elements contained.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
