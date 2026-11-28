"""Tests for .vertigis-rules.json overrides and the .vertigis-baseline.json ratchet.

Run: python3 tests/test_project.py   (exit 0 when all pass). Identical copy in both VertiGIS SDK skills.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from cli import CHECKS  # noqa: E402
from engine import run  # noqa: E402
from report import exit_code  # noqa: E402

BAD_CSS = ".Widget-body { color: #ff0000; }\n"


def project(files: dict, config: dict | None = None) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    if config is not None:
        (root / ".vertigis-rules.json").write_text(json.dumps(config), encoding="utf-8")
    return root


def validate(root: Path, update: bool = False) -> dict:
    return run(root, HERE / "rules.json", CHECKS, root / ".vertigis-baseline.json", update)


def rules(result: dict) -> list[str]:
    return sorted(v.rule for v in result["violations"])


def test_override_hides_and_is_counted():
    root = project({"src/demo/Widget.css": BAD_CSS},
                   {"overrides": [{"files": ["src/demo/**"], "off": ["HARDCODED_COLOR"], "reason": "demo data"}]})
    result = validate(root)
    assert "HARDCODED_COLOR" not in rules(result), rules(result)
    assert result["overrides"][0]["hidden"] == 1


def test_override_without_reason_is_invalid():
    root = project({"src/demo/Widget.css": BAD_CSS},
                   {"overrides": [{"files": ["src/demo/**"], "off": ["HARDCODED_COLOR"]}]})
    result = validate(root)
    assert "INVALID_SUPPRESSION" in rules(result) and "HARDCODED_COLOR" in rules(result), rules(result)
    assert exit_code(result, False) == 1


def test_override_unknown_rule_is_invalid():
    root = project({"src/a.css": BAD_CSS}, {"overrides": [{"files": ["**"], "off": ["NOPE"], "reason": "x"}]})
    assert "INVALID_SUPPRESSION" in rules(validate(root))


def test_baseline_passes_known_and_fails_new():
    root = project({"src/Widget.css": BAD_CSS})
    assert exit_code(validate(root), False) == 1
    assert exit_code(validate(root, update=True), False) == 0
    result = validate(root)
    assert exit_code(result, False) == 0 and len(result["baselined"]) == 1
    (root / "src/Other.css").write_text(".Other-x { color: #00ff00; }\n", encoding="utf-8")
    result = validate(root)
    assert exit_code(result, False) == 1 and [v.file for v in result["violations"]] == ["src/Other.css"]


def test_baseline_survives_moved_line_and_reports_fixed():
    root = project({"src/Widget.css": BAD_CSS})
    validate(root, update=True)
    (root / "src/Widget.css").write_text("/* header */\n\n" + BAD_CSS, encoding="utf-8")
    assert exit_code(validate(root), False) == 0
    (root / "src/Widget.css").write_text(".Widget-body { color: inherit; }\n", encoding="utf-8")
    result = validate(root)
    assert exit_code(result, False) == 0 and len(result["fixed"]) == 1


def test_baseline_counts_duplicates():
    root = project({"src/Widget.css": BAD_CSS})
    validate(root, update=True)
    (root / "src/Widget.css").write_text(BAD_CSS + BAD_CSS, encoding="utf-8")
    assert exit_code(validate(root), False) == 1


def main() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except AssertionError as err:
                failures += 1
                print(f"FAIL {name}: {err}")
    print("all project tests pass" if not failures else f"{failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
