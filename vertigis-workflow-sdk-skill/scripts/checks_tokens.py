"""Colour-token inheritance, pairing and contrast checks. Identical copy in both VertiGIS SDK skills."""
from __future__ import annotations

import re

from engine import Context, in_tokens_dir, matching_close, split_top_level

RULE_IDS = {"REDUNDANT_INHERITED_TOKEN", "TOKEN_PAIRING", "TOKEN_CONTRAST", "SPACING_TOKENS_DECLARED"}
REQUIRED_SPACING_ROLES = {"inlineGap", "controlGap", "fieldGap", "sectionGap", "cardPadding", "panelPadding"}

INHERITED_TEXT = "primaryForeground"
INHERITED_SURFACE = "primaryBackground"
SURFACES = {
    "primaryBackground", "secondaryBackground", "primaryBackgroundDisabled", "itemHoverBackground",
    "itemSelectedBackground", "primaryAccentLight", "inlineTableRowBackground", "inlineTableHeaderBackground",
    "defaultMapBackground", "loadingBarBackground", "errorHelperTextBackground",
}
SURFACE_TEXT = {
    "primaryForeground", "secondaryForeground", "primaryForegroundDisabled", "disabledForeground",
    "primaryAccent", "primaryAccentLarge", "errorHelperTextForeground", "tabPrimaryForeground",
    "tabSecondaryForeground", "accentIconForeground", "buttonForeground",
}
ON_STRONG = {"emphasizedButtonForeground", "primaryBackground"}
STRONG_BACKGROUNDS = {"primaryAccent", "primaryAccentLarge", "primaryAccentHover"}
MIN_TEXT_CONTRAST = 4.5

TEXT_KEYS = {"color"}
SURFACE_KEYS = {"background", "background-color", "backgroundColor", "bgcolor"}
CSS_VAR = re.compile(r"var\(\s*--([\w-]+)\s*(?:,\s*([^()]*(?:\([^()]*\))?[^()]*))?\)")
TOKEN_REF = re.compile(r"\b(?:UI_TOKENS|tokens\.ui)\.([\w.]+)")
COLOR_KEY = re.compile(r"(?<![\w-])[\"']?(color|bgcolor|backgroundColor|background(?:-color)?)[\"']?\s*:")
LAYERED = re.compile(r"(?<![\w-])[\"']?(position[\"']?\s*:\s*[\"']?(sticky|fixed|absolute)|z-?[iI]ndex[\"']?\s*:)")


def token_paths(ctx: Context) -> dict:
    """Map 'text.primary' style paths in tokens/ui.ts to (css variable, fallback)."""
    paths: dict = {}
    for src in ctx.files:
        if not re.search(r"(^|/)tokens/ui\.ts$", src.rel):
            continue
        stack: list = []
        for m in re.finditer(r"(\w+)\s*:\s*\{|\}|(\w+)\s*:\s*[\"'`]var\(--([\w-]+)\s*,\s*([^)\"'`]+\)?)\)", src.code):
            if m.group(1):
                stack.append(m.group(1))
            elif m.group(0) == "}":
                stack = stack[:-1]
            else:
                paths.setdefault(".".join(stack + [m.group(2)]), (m.group(3), m.group(4).strip()))
    return paths


def resolve(value: str, paths: dict):
    if re.search(r"color-mix\(|alpha\(|gradient\(", value):
        return None
    m = CSS_VAR.search(value)
    if m:
        return m.group(1), (m.group(2) or "").strip()
    m = TOKEN_REF.search(value)
    if m and m.group(1) in paths:
        return paths[m.group(1)]
    return None


def luminance(value: str) -> float | None:
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", value.strip())
    if not m:
        return None
    h = m.group(1) if len(m.group(1)) == 6 else "".join(c * 2 for c in m.group(1))
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(fg: str, bg: str) -> float | None:
    a, b = luminance(fg), luminance(bg)
    if a is None or b is None:
        return None
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def is_strong(bg: str) -> bool:
    return bg in STRONG_BACKGROUNDS or (bg not in SURFACES and "Background" in bg)


def pairing_problem(fg: str, bg: str) -> str | None:
    if bg in SURFACES:
        if fg in SURFACE_TEXT or not re.search(r"Foreground|Background", fg):
            return None
        return f"{fg} is not a text token for surface {bg}; use primaryForeground, secondaryForeground or errorHelperTextForeground"
    if "Foreground" in bg:
        return None if bg == INHERITED_TEXT and fg == INHERITED_SURFACE else f"foreground token {bg} used as a background"
    if not is_strong(bg):
        return None
    partner = bg.replace("Background", "Foreground")
    allowed = ({partner} if partner != bg else set()) | ON_STRONG
    return None if fg in allowed else f"{fg} on {bg}; use {' or '.join(sorted(allowed))}"


def analyse(ctx: Context, src, index: int, decls: dict, parent_bg, layered: bool, theme_file: bool) -> None:
    """decls maps property -> (css variable, fallback); parent_bg is the nearest enclosing background."""
    fg = next((decls[k] for k in TEXT_KEYS if k in decls), None)
    bg = next((decls[k] for k in SURFACE_KEYS if k in decls), None)
    surface = bg or parent_bg or (INHERITED_SURFACE, "")
    if not theme_file:
        if fg and fg[0] == INHERITED_TEXT and surface[0] in SURFACES:
            ctx.add("REDUNDANT_INHERITED_TOKEN", src, index, f"color: var(--{INHERITED_TEXT}) is inherited")
        if bg and bg[0] == INHERITED_SURFACE and not layered:
            ctx.add("REDUNDANT_INHERITED_TOKEN", src, index, f"background: var(--{INHERITED_SURFACE}) is the host panel")
    if bg and not fg:
        if "Foreground" in bg[0]:
            ctx.add("TOKEN_PAIRING", src, index, f"foreground token {bg[0]} used as a background")
        elif is_strong(bg[0]):
            ctx.add("TOKEN_PAIRING", src, index, f"background {bg[0]} set without its matching foreground")
        return
    if not fg:
        return
    problem = pairing_problem(fg[0], surface[0])
    if problem:
        ctx.add("TOKEN_PAIRING", src, index, problem)
        return
    if "isabled" in fg[0]:
        return
    value_of = lambda tok: ctx.canonical.get(tok[0]) or tok[1]
    ratio = contrast(value_of(fg), value_of(surface)) if value_of(surface) else None
    if ratio is not None and ratio < MIN_TEXT_CONTRAST:
        ctx.add("TOKEN_CONTRAST", src, index, f"{fg[0]} on {surface[0]} = {ratio:.2f}:1 (< {MIN_TEXT_CONTRAST}:1)")


def css_blocks(code: str):
    """Yield (selector, body_start, body) for innermost CSS rule blocks."""
    for m in re.finditer(r"\{", code):
        close = matching_close(code, m.start())
        body = code[m.start() + 1:close] if close > 0 else ""
        if close < 0 or "{" in body:
            continue
        head = re.split(r"[{};]", code[:m.start()])[-1].strip()
        yield head, m.start() + 1, body


def css_decls(body: str, paths: dict) -> dict:
    decls = {}
    for m in re.finditer(r"([\w-]+)\s*:\s*([^;]+)", body):
        token = resolve(m.group(2), paths)
        if token and m.group(1) in TEXT_KEYS | SURFACE_KEYS:
            decls[m.group(1)] = token
    return decls


def css_parent_bg(selector: str, backgrounds: dict):
    """Nearest earlier rule whose class is a BEM/descendant prefix of this selector."""
    first = re.match(r"\.([\w-]+)", selector.split(",")[0].strip())
    if not first:
        return None
    best = None
    for cls, bg in backgrounds.items():
        if selector.strip() != "." + cls and re.match(rf"\.{re.escape(cls)}(?:[-_]|\s|:|\.|$)", selector.strip()):
            best = bg if best is None or len(cls) > len(best[0]) else best
    return best[1] if best else None


def check_css_tokens(ctx: Context, src, paths: dict) -> None:
    backgrounds: dict = {}
    for selector, start, body in css_blocks(src.code):
        decls = css_decls(body, paths)
        bg = next((decls[k] for k in SURFACE_KEYS if k in decls), None)
        top = re.fullmatch(r"\.([\w-]+)", selector)
        if bg and top:
            backgrounds[top.group(1)] = (top.group(1), bg)
        if decls:
            analyse(ctx, src, start, decls, css_parent_bg(selector, backgrounds), bool(LAYERED.search(body)), False)


def enclosing_open(code: str, index: int) -> int:
    depth = 0
    for i in range(index - 1, -1, -1):
        if code[i] == "}":
            depth += 1
        elif code[i] == "{":
            if depth == 0:
                return i
            depth -= 1
    return -1


def object_decls(inner: str, paths: dict) -> dict:
    decls = {}
    for part in split_top_level(inner):
        key, _, value = part.partition(":")
        key = key.strip().strip("\"'")
        token = resolve(value, paths) if key in TEXT_KEYS | SURFACE_KEYS else None
        if token:
            decls[key] = token
    return decls


def check_tsx_tokens(ctx: Context, src, paths: dict) -> None:
    code, seen = src.code, set()
    theme_file = bool(re.search(r"\bcreateTheme\s*\(", code))
    for m in COLOR_KEY.finditer(code):
        open_index = enclosing_open(code, m.start())
        if open_index < 0 or open_index in seen:
            continue
        seen.add(open_index)
        close = matching_close(code, open_index)
        inner = code[open_index + 1:close] if close > 0 else ""
        decls = object_decls(inner, paths)
        if not decls:
            continue
        parent_bg, outer = None, open_index
        for _ in range(3):
            outer = enclosing_open(code, outer)
            if outer < 0:
                break
            outer_decls = object_decls(code[outer + 1:matching_close(code, outer)], paths)
            parent_bg = next((outer_decls[k] for k in SURFACE_KEYS if k in outer_decls), None)
            if parent_bg:
                break
        analyse(ctx, src, open_index, decls, parent_bg, bool(LAYERED.search(inner)), theme_file)
    if not theme_file:
        for m in re.finditer(r"<Typography\b[^>]*?\scolor\s*=\s*[\"']text\.primary[\"']", code):
            ctx.add("REDUNDANT_INHERITED_TOKEN", src, m.start(), 'color="text.primary" overrides the inherited host colour')


def check_spacing_tokens(ctx: Context) -> None:
    if ctx.single_file:
        return
    tokens_dir_files = [f for f in ctx.files if in_tokens_dir(f.rel) and not f.is_test]
    if not tokens_dir_files:
        return
    has_full_tokens = any(f.rel.endswith("tokens/index.ts") for f in tokens_dir_files)
    spacing_file = next((f for f in tokens_dir_files if f.rel.endswith("tokens/spacing.ts")), None)
    if has_full_tokens and not spacing_file:
        ref_file = tokens_dir_files[0]
        ctx.add_line("SPACING_TOKENS_DECLARED", ref_file.rel, 1, "missing src/tokens/spacing.ts; declare SPACING tokens")
        return
    if spacing_file:
        code = spacing_file.code
        if not re.search(r"\bexport\s+const\s+SPACING\b", code):
            ctx.add_line("SPACING_TOKENS_DECLARED", spacing_file.rel, 1, "SPACING constant is not exported")
            return
        missing = [role for role in REQUIRED_SPACING_ROLES if not re.search(rf"\b{role}\s*:", code)]
        if missing:
            ctx.add_line("SPACING_TOKENS_DECLARED", spacing_file.rel, 1, f"SPACING missing required roles: {', '.join(sorted(missing))}")


def check_tokens(ctx: Context) -> None:
    paths = token_paths(ctx)
    for src in ctx.files:
        if src.is_test or (in_tokens_dir(src.rel) and not re.search(r"\bcreateTheme\s*\(", src.code)):
            continue
        if src.kind == "css":
            check_css_tokens(ctx, src, paths)
        elif src.kind in ("ts", "tsx"):
            check_tsx_tokens(ctx, src, paths)


CHECKS = [check_tokens, check_spacing_tokens]
