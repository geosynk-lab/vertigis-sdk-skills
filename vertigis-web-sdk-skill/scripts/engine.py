"""Shared engine for the VertiGIS SDK rule validators.

Identical copy in vertigis-web-sdk-skill/scripts and vertigis-workflow-sdk-skill/scripts;
the SDK is selected by the "sdk" field of the sibling rules.json.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "build", "coverage", ".git", ".tgrep", ".venv", "__pycache__"}
SOURCE_EXT = (".ts", ".tsx", ".css")
SEVERITIES = ("critical", "major", "minor")
TEST_FILE_RULES = {"DEEP_MUI_IMPORT", "BANNED_WEB_UI_IMPORT", "INVALID_SUPPRESSION"}
UNSUPPRESSIBLE = {"INVALID_SUPPRESSION"}
TOKEN_VAR = re.compile(r"var\(\s*--([\w-]+)\s*,\s*(#[0-9a-fA-F]{3,8})\s*\)")
SUPPRESSION = re.compile(r"vertigis-rule-disable(-file)?([^\n]*)")
SUPPRESSION_BODY = re.compile(r"^\s+([A-Za-z0-9_*]+)\s*(?:--\s*(.*\S))?\s*$")


@dataclass
class Violation:
    rule: str
    file: str
    line: int
    detail: str = ""


@dataclass
class Suppression:
    rule: str
    file: str
    line: int
    reason: str
    scope: str


@dataclass
class SourceFile:
    rel: str
    raw: str
    code: str
    kind: str
    is_test: bool

    def line_of(self, index: int) -> int:
        return self.raw.count("\n", 0, max(index, 0)) + 1


@dataclass
class Context:
    sdk: str
    catalog: dict
    files: list
    canonical: dict = field(default_factory=dict)
    violations: list = field(default_factory=list)
    single_file: bool = False

    def add(self, rule: str, src: SourceFile, index: int, detail: str = "") -> None:
        self.violations.append(Violation(rule, src.rel, src.line_of(index), detail))

    def add_line(self, rule: str, rel: str, line: int, detail: str = "") -> None:
        self.violations.append(Violation(rule, rel, line, detail))


def load_catalog(path: Path) -> tuple[str, dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["sdk"], {r["id"]: r for r in data["rules"]}


def severity_of(entry: dict, sdk: str) -> str:
    sev = entry["severity"]
    return sev[sdk] if isinstance(sev, dict) else sev


def blank_comments(text: str, css: bool = False) -> str:
    """Replace comment characters with spaces, keeping offsets and newlines intact."""
    out = list(text)
    i, n, quote = 0, len(text), None
    while i < n:
        c = text[i]
        if quote is None:
            nxt = text[i + 1] if i + 1 < n else ""
            if c == "/" and nxt == "*":
                end = text.find("*/", i + 2)
                end = n if end < 0 else end + 2
            elif c == "/" and nxt == "/" and not css:
                end = text.find("\n", i)
                end = n if end < 0 else end
            else:
                if c in "\"'`":
                    quote = c
                i += 1
                continue
            for k in range(i, end):
                if out[k] != "\n":
                    out[k] = " "
            i = end
            continue
        if c == "\\":
            i += 2
            continue
        if c == quote or (c == "\n" and quote != "`"):
            quote = None
        i += 1
    return "".join(out)


def string_literals(code: str):
    """Yield (start_index, content) for quoted and template string literals."""
    for m in re.finditer(r"\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`", code):
        yield m.start() + 1, m.group(0)[1:-1]


def matching_close(text: str, open_index: int) -> int:
    """Index of the bracket closing text[open_index], skipping strings; -1 if unbalanced."""
    pairs = {"{": "}", "(": ")", "[": "]"}
    stack, i, n = [], open_index, len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            continue
        if c in pairs:
            stack.append(pairs[c])
        elif stack and c == stack[-1]:
            stack.pop()
            if not stack:
                return i
        i += 1
    return -1


def split_top_level(text: str, sep: str = ",") -> list[str]:
    parts, depth, start, i, n = [], 0, 0, 0, len(text)
    while i < n:
        c = text[i]
        if c in "\"'`":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            continue
        if c in "{([":
            depth += 1
        elif c in "})]":
            depth -= 1
        elif c == sep and depth == 0:
            parts.append(text[start:i])
            start = i + 1
        i += 1
    parts.append(text[start:])
    return [p.strip() for p in parts if p.strip()]


def in_tokens_dir(rel: str) -> bool:
    return "/tokens/" in "/" + rel


VAR_CALL = re.compile(r"var\((?:[^()]|\([^()]*\))*\)")
COLOR_LITERAL = re.compile(r"#[0-9a-fA-F]{3,8}(?![\w-])|\b(?:rgba?|hsla?)\(")


def strip_var_calls(text: str) -> str:
    """Remove var(...) calls so colour literals in their fallback slot are ignored."""
    previous = None
    while previous != text:
        previous, text = text, VAR_CALL.sub("", text)
    return text


def color_literal(text: str) -> str | None:
    m = COLOR_LITERAL.search(strip_var_calls(text))
    return m.group(0) if m else None


def collect_files(root: Path) -> list[SourceFile]:
    root = Path(root)
    if root.is_file():
        pairs = [(root, root.name)]
    else:
        scan = root / "src" if (root / "src").is_dir() else root
        pairs = []
        for dirpath, dirnames, filenames in os.walk(scan):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if name.endswith(SOURCE_EXT) and not name.endswith(".d.ts"):
                    path = Path(dirpath) / name
                    pairs.append((path, path.relative_to(root).as_posix()))
    files = []
    for path, rel in pairs:
        raw = path.read_text(encoding="utf-8", errors="replace")
        kind = rel.rsplit(".", 1)[-1]
        is_test = bool(re.search(r"\.(test|spec)\.tsx?$|(^|/)__tests__/", rel))
        files.append(SourceFile(rel, raw, blank_comments(raw, css=kind == "css"), kind, is_test))
    return files


def canonical_fallbacks(files: list[SourceFile]) -> dict:
    canonical: dict = {}
    for src in files:
        if re.search(r"(^|/)tokens/ui\.ts$", src.rel):
            for name, hex_value in TOKEN_VAR.findall(src.code):
                canonical.setdefault(name, normalize_hex(hex_value))
    return canonical


def normalize_hex(value: str) -> str:
    h = value.lower()
    return "#" + "".join(ch * 2 for ch in h[1:]) if len(h) == 4 else h


def parse_suppressions(ctx: Context) -> list[Suppression]:
    found = []
    for src in ctx.files:
        for m in SUPPRESSION.finditer(src.raw):
            if src.code[m.start()] != " ":
                continue
            body = m.group(2).split("*/", 1)[0]
            parsed = SUPPRESSION_BODY.match(body)
            rule, reason = (parsed.group(1), parsed.group(2)) if parsed else ("", None)
            line = src.line_of(m.start())
            if not rule or "*" in rule or rule not in ctx.catalog or rule in UNSUPPRESSIBLE or not reason:
                ctx.add_line("INVALID_SUPPRESSION", src.rel, line, m.group(0).strip())
                continue
            found.append(Suppression(rule, src.rel, line, reason, "file" if m.group(1) else "line"))
    return found


def is_suppressed(v: Violation, suppressions: list[Suppression], used: set) -> bool:
    if v.rule in UNSUPPRESSIBLE:
        return False
    for i, s in enumerate(suppressions):
        if s.rule == v.rule and s.file == v.file and (s.scope == "file" or v.line in (s.line, s.line + 1)):
            used.add(i)
            return True
    return False


def run(root: Path, catalog_path: Path, checks: list) -> dict:
    sdk, catalog = load_catalog(catalog_path)
    files = collect_files(root)
    ctx = Context(sdk, catalog, files, canonical_fallbacks(files), single_file=Path(root).is_file())
    suppressions = parse_suppressions(ctx)
    for check in checks:
        check(ctx)
    tests = {f.rel for f in files if f.is_test}
    used: set = set()
    kept, seen = [], set()
    for v in ctx.violations:
        key = (v.rule, v.file, v.line, v.detail)
        if v.rule not in catalog or key in seen:
            continue
        seen.add(key)
        if v.file in tests and v.rule not in TEST_FILE_RULES:
            continue
        if not is_suppressed(v, suppressions, used):
            kept.append(v)
    kept.sort(key=lambda v: (SEVERITIES.index(severity_of(catalog[v.rule], sdk)), v.file, v.line))
    return {
        "sdk": sdk,
        "catalog": catalog,
        "files": len(files),
        "violations": kept,
        "suppressions": [s for i, s in enumerate(suppressions) if i in used],
    }
