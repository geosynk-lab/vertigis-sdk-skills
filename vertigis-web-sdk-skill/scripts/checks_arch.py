"""Architecture, lifecycle and Workflow structure checks. Identical copy in both VertiGIS SDK skills."""
from __future__ import annotations

import posixpath
import re

from engine import Context, matching_close

RULE_IDS = {
    "HANDLES_FIELD_DECLARED", "LIFECYCLE_SUPER_ORDER", "MODEL_VIEW_SEPARATION", "OBSERVER_WRAPPING",
    "LAYOUT_ELEMENT_WRAPPER", "ACTIVE_PROP_HIDING", "ERROR_BOUNDARY", "DESIGNER_EMPTY_ATTRIBUTE",
    "FILE_LENGTH_TARGET", "FILE_LENGTH_CEILING", "FORM_PROPS_WIRING", "ACTIVITY_HANDLER_PATTERN",
    "BARREL_EXPORT_NAMING",
}

MODEL_BASE = re.compile(r"\bclass\s+\w+[^{]*\bextends\s+(ComponentModelBase|ModelBase)\b")
HANDLES_FIELD = re.compile(
    r"^[ \t]*(?:(?:private|protected|public|readonly|declare|override|static)\s+)*_handles\s*[?!]?\s*[:=;]", re.M)
FORM_CONTROLS = re.compile(r"<(TextField|Select|Checkbox|Radio|Switch|DatePicker|TimePicker|Button|IconButton|"
                           r"Autocomplete|Slider)\b")
VISIBLE_GUARD = re.compile(r"if\s*\(\s*!\s*(?:props\.)?visible\s*\)\s*\{?\s*return\s+null|"
                           r"(?:props\.)?visible\s*===\s*false\s*\)\s*\{?\s*return\s+null|"
                           r"!\s*(?:props\.)?visible\s*\?\s*null")


def method_body(code: str, name: str):
    m = re.search(rf"(?<![.\w]){name}\s*\([^)]*\)\s*(?::\s*[^{{=;]+)?\{{", code)
    if not m:
        return None, None
    close = matching_close(code, m.end() - 1)
    return m.start(), (code[m.end():close] if close > 0 else "")


def check_model(ctx: Context, src) -> None:
    code = src.code
    if not MODEL_BASE.search(code):
        return
    for m in HANDLES_FIELD.finditer(code):
        ctx.add("HANDLES_FIELD_DECLARED", src, m.start(), m.group(0).strip())
    index, body = method_body(code, "_onInitialize")
    if body is not None and not re.match(r"\s*(await\s+)?super\._onInitialize\(", body):
        ctx.add("LIFECYCLE_SUPER_ORDER", src, index, "super._onInitialize() is not the first statement")
    index, body = method_body(code, "_onDestroy")
    if body is not None and not re.search(r"(await\s+|return\s+)?super\._onDestroy\(\s*\)\s*;?\s*\}?\s*$", body):
        ctx.add("LIFECYCLE_SUPER_ORDER", src, index, "super._onDestroy() is not the last statement")
    if src.kind == "tsx":
        ctx.add("MODEL_VIEW_SEPARATION", src, MODEL_BASE.search(code).start(), "model class defined in a .tsx file")


def check_web_view(ctx: Context, src) -> None:
    code = src.code
    for m in re.finditer(r"import\s*\{[^}]*\bobserver\b[^}]*\}\s*from\s*[\"']([^\"']+)[\"']", code):
        if m.group(1) != "mobx-react-lite":
            ctx.add("OBSERVER_WRAPPING", src, m.start(), f"observer imported from {m.group(1)}")
    if src.kind != "tsx":
        return
    is_view = "LayoutElementProperties" in code and re.search(r"return\s*\(?\s*<", code)
    if is_view and "<LayoutElement" not in code:
        ctx.add("LAYOUT_ELEMENT_WRAPPER", src, code.find("LayoutElementProperties"), "no <LayoutElement {...props}>")
    if is_view and re.search(r"\bmodel\b", code) and not re.search(r"\bobserver\(|\buseWatchAndRerender\(", code):
        ctx.add("OBSERVER_WRAPPING", src, code.find("LayoutElementProperties"), "view reads the model without observer()")
    if "<LayoutElement" in code and "ErrorBoundary" not in code:
        ctx.add("ERROR_BOUNDARY", src, code.find("<LayoutElement"), "no <ErrorBoundary>")
    for m in re.finditer(r"props\.active\s*===\s*false|!\s*props\.active\b|\bactive\s*===\s*false", code):
        if "return" in code[m.end():m.end() + 120].split(";")[0]:
            ctx.add("ACTIVE_PROP_HIDING", src, m.start(), m.group(0))


def check_form_elements(ctx: Context) -> None:
    for reg in [f for f in ctx.files if f.kind == "tsx" and "FormElementRegistration" in f.code]:
        folder = posixpath.dirname(reg.rel)
        group = [f for f in ctx.files if f.kind == "tsx" and not f.is_test
                 and (f.rel.startswith(folder + "/") or posixpath.dirname(f.rel) == folder)]
        joined = "\n".join(f.code for f in group)
        index = reg.code.find("FormElementRegistration")
        if not VISIBLE_GUARD.search(joined):
            ctx.add("FORM_PROPS_WIRING", reg, index, "no `if (!visible) return null` guard")
        if FORM_CONTROLS.search(joined) and not re.search(r"disabled=\{\s*!\s*(?:props\.)?enabled\s*\}", joined):
            ctx.add("FORM_PROPS_WIRING", reg, index, "controls not wired with disabled={!enabled}")
        if "<FormElementErrorBoundary" not in joined:
            ctx.add("ERROR_BOUNDARY", reg, index, "no <FormElementErrorBoundary>")
        for f in group:
            for m in re.finditer(r"disabled=\{[^}]*\breadOnly\b", f.code):
                ctx.add("FORM_PROPS_WIRING", f, m.start(), "readOnly mapped to disabled; use slotProps.input.readOnly")


def check_activity(ctx: Context, src) -> None:
    code = src.code
    cls = re.search(r"\bclass\s+\w+([^{]*)\{", code)
    if not cls or not re.search(r"\bexecute\s*\(", code):
        return
    if "IActivityHandler" not in cls.group(1):
        ctx.add("ACTIVITY_HANDLER_PATTERN", src, cls.start(), "class does not implement IActivityHandler")
    index, body = method_body(code, "execute")
    if body is not None and not (re.search(r"\btry\s*\{", body) and re.search(r"\bcatch\b", body)):
        ctx.add("ACTIVITY_HANDLER_PATTERN", src, index, "execute body is not wrapped in try/catch")
    for m in re.finditer(r"\btype\s+(\w+)\s*=\s*[\"'][^\"']*[\"']\s*\|", code):
        if re.search(rf":\s*{m.group(1)}\b", code):
            ctx.add("ACTIVITY_HANDLER_PATTERN", src, m.start(), f"input union declared as type alias {m.group(1)}")


def check_barrel(ctx: Context, src) -> None:
    for m in re.finditer(r"export\s*\{\s*default\s+as\s+(\w+)\s*\}", src.code):
        if not m.group(1).endswith(("Activity", "Registration")):
            ctx.add("BARREL_EXPORT_NAMING", src, m.start(), m.group(1))


def check_arch(ctx: Context) -> None:
    for src in ctx.files:
        if src.kind not in ("ts", "tsx") or src.is_test:
            continue
        lines = len(src.raw.splitlines())
        if lines > 250:
            ctx.add_line("FILE_LENGTH_CEILING", src.rel, 1, f"{lines} lines")
        elif lines > 150:
            ctx.add_line("FILE_LENGTH_TARGET", src.rel, 1, f"{lines} lines")
        for m in re.finditer(r"attributes\.set\(\s*[^,()]+,\s*(\"\"|''|``)\s*\)", src.code):
            ctx.add("DESIGNER_EMPTY_ATTRIBUTE", src, m.start(), m.group(0))
        if ctx.sdk == "web":
            check_model(ctx, src)
            check_web_view(ctx, src)
        else:
            if re.search(r"(^|/)activities/", src.rel):
                check_activity(ctx, src)
            if re.fullmatch(r"(src/)?index\.ts", src.rel):
                check_barrel(ctx, src)
    if ctx.sdk == "workflow":
        check_form_elements(ctx)


CHECKS = [check_arch]
