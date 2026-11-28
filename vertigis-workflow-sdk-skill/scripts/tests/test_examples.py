"""Run the validator on every fenced ts/tsx/css block in SKILL.md and references/*.md.

Blocks must produce no critical or major findings. Blocks that deliberately show a wrong
pattern are tagged ```tsx bad (or ts/css) and must produce at least one. Partial snippets
tagged ```tsx fragment skip the checks that need a whole file (WHOLE_FILE_RULES).
When the two lines above a block name a file in backticks (e.g. `src/tokens/ui.ts`),
the block is validated at that path. Identical copy in both VertiGIS SDK skills.
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
CROSS_FILE_RULES = {"COMPONENT_CSS_PAIR"}


def example_path(text: str, start: int, lang: str) -> str:
    above = [line for line in text[:start].splitlines() if line.strip()][-2:]
    for line in reversed(above):
        hint = PATH_HINT.findall(line)
        if hint and hint[-1].endswith("." + lang):
            return re.sub(r"[<>]", "", hint[-1])
    return f"example.{lang}"


def example_errors(skill_dir: Path, checks: list) -> list[str]:
    from engine import run, severity_of

    rules = skill_dir / "scripts" / "rules.json"
    docs = [skill_dir / "SKILL.md"] + sorted((skill_dir / "references").glob("*.md"))
    errors = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for m in FENCE.finditer(text):
            lang = LANG.get(m.group(2), m.group(2))
            tags = m.group(3).split()
            expect_bad = "bad" in tags
            skipped = CROSS_FILE_RULES | (WHOLE_FILE_RULES if "fragment" in tags else set())
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / example_path(text, m.start(), lang)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(textwrap.dedent(m.group(4)), encoding="utf-8")
                result = run(Path(tmp), rules, checks)
            hits = sorted({v.rule for v in result["violations"] if v.rule not in skipped
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
