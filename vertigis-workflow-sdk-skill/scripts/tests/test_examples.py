"""Run the validator on every fenced ts/tsx/css block in SKILL.md and references/*.md.

Blocks must produce no critical or major findings. Blocks that deliberately show a wrong
pattern are tagged ```tsx bad (or ts/css) and must produce at least one. Partial snippets
tagged ```tsx fragment skip the checks that need a whole file (WHOLE_FILE_RULES).
When the two lines above a block name a file in backticks (e.g. `src/tokens/ui.ts`),
the block is validated at that path. Each block runs next to the canonical tokens/ui.ts (the first
`export const UI_TOKENS` block in the docs), so UI_TOKENS.* references resolve for TOKEN_PAIRING and
TOKEN_CONTRAST; only findings in the block's own file count. Identical copy in both VertiGIS SDK skills.
"""
from __future__ import annotations

import re
import sys
import tempfile
import textwrap
from pathlib import Path

FENCE = re.compile(r"^([ \t]*)```(tsx|ts|typescript|jsx|css)([^\n]*)\n(.*?)^\1```", re.M | re.S)
LANG = {"typescript": "ts", "jsx": "tsx"}
PATH_HINT = re.compile(r"`((?:[\w.<>-]+/)*[\w.<>-]+\.(?:tsx?|css))`")
WHOLE_FILE_RULES = {"ERROR_BOUNDARY", "FORM_PROPS_WIRING", "OBSERVER_WRAPPING", "LAYOUT_ELEMENT_WRAPPER",
                    "MODEL_VIEW_SEPARATION"}


def example_path(text: str, start: int, lang: str) -> str:
    above = [line for line in text[:start].splitlines() if line.strip()][-2:]
    for line in reversed(above):
        hint = PATH_HINT.findall(line)
        if hint and hint[-1].endswith("." + lang):
            return re.sub(r"[<>]", "", hint[-1])
    return f"example.{lang}"


def canonical_ui_tokens(docs: list[Path]) -> str | None:
    for doc in docs:
        for m in FENCE.finditer(doc.read_text(encoding="utf-8")):
            if "bad" not in m.group(3).split() and "export const UI_TOKENS" in m.group(4):
                return textwrap.dedent(m.group(4))
    return None


def tokens_path(root: Path, rel: str) -> Path:
    """Next to an example in a tokens/ folder (it imports "./ui"), else at [src/]tokens/ui.ts.

    Use src/ only when the example is under src/: the engine scans only src/ when it exists.
    """
    example = root / rel
    if example.parent.name == "tokens":
        return example.parent / "ui.ts"
    return root / ("src/tokens/ui.ts" if rel.startswith("src/") else "tokens/ui.ts")


def example_errors(skill_dir: Path, checks: list) -> list[str]:
    from engine import run, severity_of

    rules = skill_dir / "scripts" / "rules.json"
    docs = [skill_dir / "SKILL.md"] + sorted((skill_dir / "references").glob("*.md"))
    ui_tokens = canonical_ui_tokens(docs)
    errors = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for m in FENCE.finditer(text):
            lang = LANG.get(m.group(2), m.group(2))
            tags = m.group(3).split()
            expect_bad = "bad" in tags
            skipped = WHOLE_FILE_RULES if "fragment" in tags else set()
            with tempfile.TemporaryDirectory() as tmp:
                rel = example_path(text, m.start(), lang)
                path = Path(tmp) / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(textwrap.dedent(m.group(4)), encoding="utf-8")
                tokens = tokens_path(Path(tmp), rel)
                if ui_tokens and not rel.endswith("tokens/ui.ts"):
                    tokens.parent.mkdir(parents=True, exist_ok=True)
                    tokens.write_text(ui_tokens, encoding="utf-8")
                result = run(Path(tmp), rules, checks)
            hits = sorted({v.rule for v in result["violations"] if v.rule not in skipped and v.file == rel
                           and severity_of(result["catalog"][v.rule], result["sdk"]) in ("critical", "major")})
            where = f"{doc.relative_to(skill_dir)}:{text.count(chr(10), 0, m.start()) + 1}"
            if expect_bad and not hits:
                errors.append(f"{where}: tagged bad but produced no critical/major finding")
            elif not expect_bad and hits:
                errors.append(f"{where}: {', '.join(hits)}")
    return errors


if __name__ == "__main__":
    scripts = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(scripts))
    from cli import CHECKS

    problems = example_errors(scripts.parent, CHECKS)
    print("\n".join(problems) or "all examples pass")
    sys.exit(1 if problems else 0)
