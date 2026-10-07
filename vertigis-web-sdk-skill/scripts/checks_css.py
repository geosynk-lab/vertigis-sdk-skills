"""CSS checks. Identical copy in both VertiGIS SDK skills."""
from __future__ import annotations

import re

from engine import TOKEN_VAR, Context, color_literal, in_tokens_dir, normalize_hex, string_literals, strip_var_calls

RULE_IDS = {
    "CSS_ROOT_SCOPE", "TOKEN_REALIAS", "FONT_FAMILY", "HARDCODED_RADIUS", "HARDCODED_COLOR",
    "TOKEN_FALLBACK_DRIFT", "CSS_GENERIC_CLASS", "CSS_MUI_OVERRIDE", "CSS_IMPORTANT",
    "CSS_ORPHAN_CLASS", "CSS_DUPLICATE_CLASS", "WORKFLOW_CSS_FILE", "REDUNDANT_DECLARATION", "HARDCODED_SPACING",
    "EMPTY_CSS_FILE",
}

SELECTOR = re.compile(r"([^{};]+)\{")
DECLARATION = re.compile(r"([\w-]+)\s*:\s*([^;{}]+)(?=[;}])")
CLASS_NAME = re.compile(r"\.(-?[_a-zA-Z][\w-]*)")
RADIUS_PROP = re.compile(r"border(-(top|bottom)-(left|right))?-radius")
SPACING_PROP = re.compile(r"(margin|padding)(-(top|right|bottom|left|inline|block)(-(start|end))?)?|(row-|column-)?gap")
LENGTH_LITERAL = re.compile(r"(?<![\w.-])-?(\d*\.\d+|\d+)(px|rem|em|%|vh|vw|vmin|vmax|ch|ex|pt)(?![\w.%])")
RULE_BLOCK = re.compile(r"\{([^{}]*)\}")


def check_selectors(ctx: Context, src, classes: dict, top_level: dict) -> None:
    for m in SELECTOR.finditer(src.code):
        selector = m.group(1).strip()
        index = m.start(1) + m.group(1).find(selector)
        if selector.startswith("@") or re.match(r"^(from|to|[\d.]+%)\b", selector):
            continue
        if re.search(r":root\b", selector):
            ctx.add("CSS_ROOT_SCOPE", src, index, selector)
        for cls in CLASS_NAME.findall(selector):
            if cls.startswith("Mui"):
                ctx.add("CSS_MUI_OVERRIDE", src, index, selector)
                continue
            if re.fullmatch(r"[a-z]+", cls):
                ctx.add("CSS_GENERIC_CLASS", src, index, "." + cls)
            classes.setdefault(cls, []).append((src.rel, src.line_of(index)))
        for part in selector.split(","):
            top = re.match(r"^\.([\w-]+)(::?[\w-]+)*$", part.strip())
            if top:
                top_level.setdefault(top.group(1), {}).setdefault(src.rel, src.line_of(index))


def check_declarations(ctx: Context, src) -> None:
    tokens_file = in_tokens_dir(src.rel)
    for m in DECLARATION.finditer(src.code):
        prop, value = m.group(1), m.group(2).strip()
        index = m.start()
        if prop.startswith("--") and value.startswith("var("):
            ctx.add("TOKEN_REALIAS", src, index, f"{prop}: {value}")
        if "!important" in value and not (prop == "display" and value.startswith("none")):
            ctx.add("CSS_IMPORTANT", src, index, f"{prop}: {value}")
        if prop in ("font-family", "font"):
            ctx.add("FONT_FAMILY", src, index, f"{prop}: {value}")
        if tokens_file:
            continue
        if RADIUS_PROP.fullmatch(prop):
            if any(px != "9999px" for px in re.findall(r"\b[1-9][\d.]*px", strip_var_calls(value))):
                ctx.add("HARDCODED_RADIUS", src, index, f"{prop}: {value}")
        if SPACING_PROP.fullmatch(prop):
            if any(float(n) != 0 for n, _ in LENGTH_LITERAL.findall(strip_var_calls(value))):
                ctx.add("HARDCODED_SPACING", src, index, f"{prop}: {value}")
        if color_literal(value):
            ctx.add("HARDCODED_COLOR", src, index, f"{prop}: {value}")


def check_redundant(ctx: Context, src) -> None:
    for block in RULE_BLOCK.finditer(src.code):
        decl = {m.group(1): (m.group(2).strip(), block.start(1) + m.start())
                for m in DECLARATION.finditer(block.group(1) + ";")}
        if "min-height" in decl and decl["min-height"][0] == decl.get("height", ("",))[0]:
            ctx.add("REDUNDANT_DECLARATION", src, decl["min-height"][1], "min-height equals height")
        spacing = re.fullmatch(r"(-?\d*\.?\d+)(em|rem|px)?", decl.get("letter-spacing", ("",))[0])
        if spacing and abs(float(spacing.group(1))) <= (0.5 if spacing.group(2) in (None, "px") else 0.02):
            ctx.add("REDUNDANT_DECLARATION", src, decl["letter-spacing"][1],
                    f"letter-spacing: {spacing.group(0)} is imperceptible")


def check_fallback_drift(ctx: Context, src) -> None:
    for m in TOKEN_VAR.finditer(src.code):
        expected = ctx.canonical.get(m.group(1))
        if expected and expected != normalize_hex(m.group(2)) and not src.rel.endswith("tokens/ui.ts"):
            ctx.add("TOKEN_FALLBACK_DRIFT", src, m.start(), f"{m.group(0)} (canonical {expected})")


def check_css(ctx: Context) -> None:
    classes: dict = {}
    top_level: dict = {}
    css_files = [f for f in ctx.files if f.kind == "css" and not f.is_test]
    for src in css_files:
        if re.search(r"(^|/)elements/", src.rel):
            ctx.add_line("WORKFLOW_CSS_FILE", src.rel, 1, src.rel)
        clean = re.sub(r"/\*.*?\*/", "", src.code, flags=re.S).strip()
        if not clean or not SELECTOR.search(clean):
            ctx.add_line("EMPTY_CSS_FILE", src.rel, 1, f"{src.rel} has no CSS rules; remove file and imports")
            continue
        check_selectors(ctx, src, classes, top_level)
        check_declarations(ctx, src)
        check_redundant(ctx, src)
        check_fallback_drift(ctx, src)
    sources = [f for f in ctx.files if f.kind in ("ts", "tsx") and not f.is_test]
    if sources:
        used = set()
        for src in sources:
            for _, text in string_literals(src.code):
                used.update(t for t in re.split(r"[^\w-]+", text) if t)
        for cls, locations in classes.items():
            if cls not in used:
                rel, line = locations[0]
                ctx.add_line("CSS_ORPHAN_CLASS", rel, line, "." + cls)
    for cls, per_file in top_level.items():
        if len(per_file) > 1:
            names = ", ".join(sorted(per_file))
            for rel, line in per_file.items():
                ctx.add_line("CSS_DUPLICATE_CLASS", rel, line, f".{cls} in {names}")


CHECKS = [check_css]
