"""TS/TSX styling, import and theme checks. Identical copy in both VertiGIS SDK skills."""
from __future__ import annotations

import re
from dataclasses import dataclass

import verify_zero_cosmetic_sx as zero_cosmetic
from engine import (TOKEN_VAR, COLOR_LITERAL, Context, color_literal, in_tokens_dir, matching_close,
                    normalize_hex, split_top_level, string_literals)

RULE_IDS = {
    "NO_CSS_BASELINE", "RAW_HTML_TEXT", "MIXED_CLASS_AND_STYLE", "LEGACY_SLOT_PROPS", "MISSING_A11Y",
    "DIALOG_GLOBAL_OVERRIDE", "HARDCODED_COLOR", "INLINE_TOKEN_LITERAL", "TOKEN_FALLBACK_DRIFT",
    "FONT_FAMILY", "HARDCODED_RADIUS", "PALETTE_CSS_VAR", "THEME_HARDCODED_PALETTE", "THEME_DYNAMIC_HOOK",
    "DEEP_MUI_IMPORT", "BANNED_WEB_UI_IMPORT", "ARCGIS_IMPORT_STYLE", "REDUNDANT_DECLARATION",
} | set(zero_cosmetic.RULES)

RAW_TEXT_TAGS = {"p", "span", "label", "h1", "h2", "h3", "h4", "h5", "h6"}
PHRASING_TAGS = {"b", "strong", "i", "em", "u"}
MARGIN_PROPS = {"m", "mx", "my", "mt", "mb", "ml", "mr", "margin", "marginTop", "marginBottom", "marginLeft", "marginRight", "marginX", "marginY"}
CLICKABLE_TAGS = {"div", "span", "Box", "Stack", "Paper", "Card"}
LEGACY_PROPS = re.compile(r"(?<![\w-])(InputProps|inputProps|PaperProps|BackdropProps|onBackdropClick)\s*=")
STATIC_VALUE = re.compile(r"^([\"'][^\"'$]*[\"']|`[^`$]*`|-?\d+(\.\d+)?|true|false|[A-Z_]+_TOKENS(\.\w+)+)$")
TAG_START = re.compile(r"<([A-Za-z][\w.]*)")
CLOSE_TAG = re.compile(r"</([A-Za-z][\w.]*)\s*>")
FLEX_DISPLAY = {"flex", "inline-flex", "grid", "inline-grid"}


@dataclass
class Tag:
    name: str
    start: int
    end: int
    attrs: str
    top: str
    self_closing: bool

    def value(self, name: str) -> str | None:
        m = re.search(rf"(?<![\w-]){re.escape(name)}\s*=\s*", self.top)
        if not m:
            return None
        k = m.end()
        if k >= len(self.attrs):
            return None
        if self.attrs[k] == "{":
            close = matching_close(self.attrs, k)
            return self.attrs[k + 1:close] if close > 0 else None
        end = self.attrs.find(self.attrs[k], k + 1)
        return self.attrs[k:end + 1]

    def has(self, name: str) -> bool:
        return re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", self.top) is not None


def blank_braces(text: str) -> str:
    """Blank the contents of top-level {...} so nested JSX does not count as attributes."""
    out, i = list(text), 0
    while i < len(text):
        if text[i] == "{":
            close = matching_close(text, i)
            close = len(text) - 1 if close < 0 else close
            for k in range(i + 1, close):
                out[k] = " "
            i = close
        i += 1
    return "".join(out)


def jsx_tags(code: str):
    n = len(code)
    for m in TAG_START.finditer(code):
        i = m.start()
        if i and (code[i - 1].isalnum() or code[i - 1] in "_$."):
            continue
        j, depth = m.end(), 0
        while j < n and j - i < 20000:
            c = code[j]
            if c in "\"'`":
                k = j + 1
                while k < n and code[k] != c:
                    k += 2 if code[k] == "\\" else 1
                j = k + 1
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            elif c == ">" and depth == 0:
                break
            elif c == ";" and depth == 0:
                j = n
                break
            j += 1
        if j >= n:
            continue
        attrs = code[m.end():j]
        yield Tag(m.group(1), i, j, attrs, blank_braces(attrs), code[j - 1] == "/")


def inline_object(tag: Tag, name: str) -> str | None:
    expr = tag.value(name)
    if expr is None:
        return None
    expr = expr.strip()
    return expr[1:-1] if expr.startswith("{") and expr.endswith("}") else None


def style_declarations(code: str, tag: Tag) -> dict:
    """Merge the sx and style objects of a tag; a styles.key reference is resolved within the file."""
    objects = []
    for name in ("sx", "style"):
        expr = (tag.value(name) or "").strip()
        if expr.startswith("{") and expr.endswith("}"):
            objects.append(expr[1:-1])
            continue
        ref = re.fullmatch(r"[\w$]+\.([\w$]+)", expr)
        if ref:
            objects += [b[1:-1] for _, b in block_after(code, rf"(?<![\w.$]){re.escape(ref.group(1))}\s*:\s*\{{")][:1]
    out = {}
    for obj in objects:
        for part in split_top_level(obj):
            if ":" in part:
                key, value = part.split(":", 1)
                out[key.strip().strip("\"'")] = value.strip()
    return out


def plain(value: str) -> str:
    value = value.strip().strip("\"'`")
    return value[:-2] if re.fullmatch(r"-?[\d.]+px", value) else value


def check_tag(ctx: Context, src, tag: Tag, decl: dict) -> None:
    add = lambda rule, detail="": ctx.add(rule, src, tag.start, detail or f"<{tag.name}>")
    if tag.name == "CssBaseline":
        add("NO_CSS_BASELINE")
    if tag.name in RAW_TEXT_TAGS and not tag.self_closing:
        rest = src.code[tag.end + 1:]
        child = rest[:rest.find("<")] if "<" in rest else rest
        if child.strip():
            add("RAW_HTML_TEXT")
    if "minHeight" in decl and plain(decl.get("height", "")) == plain(decl["minHeight"]):
        add("REDUNDANT_DECLARATION", f"<{tag.name}> minHeight equals height")
    style_obj = inline_object(tag, "style")
    if style_obj is not None and tag.has("className") and any(
            ":" in p and STATIC_VALUE.match(p.split(":", 1)[1].strip()) for p in split_top_level(style_obj)):
        add("MIXED_CLASS_AND_STYLE")
    for m in LEGACY_PROPS.finditer(tag.top):
        add("LEGACY_SLOT_PROPS", f"<{tag.name}> {m.group(1)}")
    if tag.name == "IconButton" and not tag.has("aria-label"):
        add("MISSING_A11Y", "<IconButton> without aria-label")
    if tag.name == "TextField" and not tag.has("label") and "aria-label" not in tag.attrs:
        add("MISSING_A11Y", "<TextField> without label or aria-label")
    if ctx.sdk == "workflow" and tag.name in CLICKABLE_TAGS and tag.has("onClick") and not tag.has("onKeyDown"):
        add("MISSING_A11Y", f"<{tag.name}> onClick without onKeyDown")
    if tag.name == "GlobalStyles" and re.search(r"role=\\?[\"']?dialog|MuiDialogContent-root", tag.attrs):
        add("DIALOG_GLOBAL_OVERRIDE")


def check_nesting(ctx: Context, src, tags: list) -> None:
    """Flag child declarations that repeat what the parent already provides in the same file."""
    events = [(t[0].start, "open", t) for t in tags] + [(m.start(), "close", m.group(1))
                                                    for m in CLOSE_TAG.finditer(src.code)]
    stack: list = []
    for _, kind, item in sorted(events, key=lambda e: e[0]):
        if kind == "close":
            names = [t.name for t, _ in stack]
            if item in names:
                del stack[len(names) - 1 - names[::-1].index(item):]
            continue
        tag, decl = item
        if stack:
            parent = stack[-1][1]
            parent_tag = stack[-1][0]
            if plain(parent.get("display", "")) in FLEX_DISPLAY and plain(decl.get("display", "")) == "block":
                ctx.add("REDUNDANT_DECLARATION", src, tag.start, f"<{tag.name}> display: block inside a flex/grid parent")
            if parent_tag.name == "Stack" and tag.name == "Divider":
                if any(k in decl or tag.has(k) for k in ("my", "mt", "mb", "margin", "marginTop", "marginBottom", "marginY")):
                    ctx.add("MARGIN_LEAKAGE", src, tag.start, "<Divider> inside <Stack> has vertical margin; parent Stack spacing manages separation")
        if tag.name == "Stack":
            if any(k in decl or tag.has(k) for k in MARGIN_PROPS):
                ctx.add("MARGIN_LEAKAGE", src, tag.start, "<Stack> declares external margin; manage spacing on the parent container")
        if tag.name in PHRASING_TAGS and not tag.self_closing:
            ancestors = [t.name for t, _ in stack]
            if "Typography" not in ancestors:
                rest = src.code[tag.end + 1:]
                child = rest[:rest.find("<")] if "<" in rest else rest
                if child.strip():
                    ctx.add("RAW_HTML_TEXT", src, tag.start, f"<{tag.name}> outside <Typography>; use <Typography variant=\"...\"> or wrap inline phrasing inside <Typography>")
        if not tag.self_closing:
            stack.append((tag, decl))


def block_after(code: str, pattern: str):
    """Yield (index, text) of each {...} block opened right after a regex match."""
    for m in re.finditer(pattern, code):
        open_index = m.end() - 1
        close = matching_close(code, open_index)
        if close > 0:
            yield m.start(), code[open_index:close + 1]


def check_strings(ctx: Context, src) -> None:
    tokens_file = in_tokens_dir(src.rel)
    for index, text in string_literals(src.code):
        if not tokens_file and color_literal(text):
            ctx.add("HARDCODED_COLOR", src, index, text[:80])
        for m in TOKEN_VAR.finditer(text):
            if not tokens_file:
                ctx.add("INLINE_TOKEN_LITERAL", src, index, m.group(0))
            expected = ctx.canonical.get(m.group(1))
            if expected and expected != normalize_hex(m.group(2)) and not src.rel.endswith("tokens/ui.ts"):
                ctx.add("TOKEN_FALLBACK_DRIFT", src, index, f"{m.group(0)} (canonical {expected})")


def check_properties(ctx: Context, src) -> None:
    code = src.code
    renderer = re.search(r"\bcreateTheme\s*\(|[\"'](@nivo/[\w-]+|plotly[\w.-]*|react-plotly\.js|jspdf)[\"']|"
                         r"getContext\(\s*[\"']2d", code)
    for m in re.finditer(r"\bfontFamily\s*:\s*([^,}\n]+)", code):
        if not (renderer and re.fullmatch(r"[\"'`]inherit[\"'`]", m.group(1).strip())):
            ctx.add("FONT_FAMILY", src, m.start(), m.group(0).strip())
    if not in_tokens_dir(src.rel):
        for m in re.finditer(r"\bborderRadius\s*:\s*([^,}\n]+)", code):
            value = m.group(1).strip()
            if re.fullmatch(r"[1-9][\d.]*|[\"'`][1-9][\d.]*px[\"'`]", value) and "9999px" not in value:
                ctx.add("HARDCODED_RADIUS", src, m.start(), m.group(0).strip())
        for index, block in block_after(code, r"\bpalette\s*:\s*\{"):
            if any(COLOR_LITERAL.search(text) for _, text in string_literals(block)):
                ctx.add("THEME_HARDCODED_PALETTE", src, index, "palette contains hardcoded colours")
    for index, block in block_after(code, r"\bpalette\s*:\s*\{"):
        for m in re.finditer(r"\b(main|light|dark|contrastText)\s*:\s*[^,}\n]*var\(", block):
            ctx.add("PALETTE_CSS_VAR", src, index, m.group(0).strip())
    for index, block in block_after(code, r"\bMuiTypography\s*:\s*\{"):
        if re.search(r"(?<![\w-])color\s*:", block):
            ctx.add("THEME_HARDCODED_PALETTE", src, index, "MuiTypography color override blocks color= props")
    if renderer and not re.search(r"\b(useIsDarkTheme|useDarkTheme|isDarkTheme|isDark)\b", code):
        ctx.add("THEME_DYNAMIC_HOOK", src, renderer.start(), renderer.group(0))


def check_imports(ctx: Context, src) -> None:
    code = src.code
    for m in re.finditer(r"^[ \t]*(?:import\b|export\s+(?:type\s+)?[*{])[^;]*?\bfrom\s+[\"'](@mui/material/(?!styles[\"'])[^\"']+|"
                         r"@mui/styles(?:/[^\"']*)?)[\"']", code, re.M):
        ctx.add("DEEP_MUI_IMPORT", src, m.start(), m.group(1))
    for m in re.finditer(r"^[ \t]*import\s+(type\s+)?([^;]*?)\s+from\s+[\"']@vertigis/web/ui[\"']", code, re.M):
        if m.group(1):
            continue
        clause = m.group(2)
        names = re.findall(r"[\w$]+(?:\s+as\s+[\w$]+)?", clause.strip("{} ")) if "{" in clause else [clause]
        banned = [n.split()[0] for n in names if not re.match(r"(type\s+)?use[A-Z]", n) and n != "type"
                  and not re.search(r"(Service|Context)$", n.split()[0])]
        banned = [n for n in banned if not re.search(rf"\btype\s+{re.escape(n)}\b", clause)]
        if banned:
            ctx.add("BANNED_WEB_UI_IMPORT", src, m.start(), ", ".join(banned))
    for m in re.finditer(r"^[ \t]*import\s+\*\s+as\s+\w+\s+from\s+[\"']@arcgis/core/(?:[\w-]+/)*([A-Z]\w*)[\"']",
                         code, re.M):
        ctx.add("ARCGIS_IMPORT_STYLE", src, m.start(), m.group(0))


def check_tsx(ctx: Context) -> None:
    for src in ctx.files:
        if src.kind not in ("ts", "tsx"):
            continue
        check_imports(ctx, src)
        if src.is_test:
            continue
        check_strings(ctx, src)
        check_properties(ctx, src)
        if not in_tokens_dir(src.rel):
            for rule, index, detail in zero_cosmetic.check_source(src.code, src.rel):
                ctx.add(rule, src, index, detail)
        if src.kind == "tsx":
            tags = [(tag, style_declarations(src.code, tag)) for tag in jsx_tags(src.code)]
            for tag, decl in tags:
                check_tag(ctx, src, tag, decl)
            check_nesting(ctx, src, tags)


CHECKS = [check_tsx]

