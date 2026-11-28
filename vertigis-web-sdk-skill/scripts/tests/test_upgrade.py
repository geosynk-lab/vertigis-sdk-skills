"""Tests for upgrade_project.py on a throwaway project made with an older skill.

Run: python3 tests/test_upgrade.py   (exit 0 when all pass). Identical copy in both VertiGIS SDK skills.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SDK = json.loads((HERE / "rules.json").read_text())["sdk"]
SKILL = HERE.parent.name
DEP = {"web": "@vertigis/web", "workflow": "@vertigis/workflow"}[SDK]
MARK = {"web": "vertigis-web-sdk", "workflow": "vertigis-workflow-sdk"}[SDK]


def old_project() -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "package.json").write_text(json.dumps({"name": "old", "dependencies": {DEP: "*"}}, indent=4) + "\n")
    (root / "AGENTS.md").write_text(f"# Mine\n\nKeep me.\n\n<!-- {MARK}:start -->\nold rules\n<!-- {MARK}:end -->\n\nKeep me too.\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "verify_zero_cosmetic_sx.py").write_text("# old copy\n")
    (root / ".agents" / "skills" / SKILL).mkdir(parents=True)
    (root / ".agents" / "skills" / SKILL / "SKILL.md").write_text("old skill\n")
    git(root, "init", "-q")
    commit(root)
    return root


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True).stdout


def commit(root: Path) -> None:
    git(root, "add", "-A")
    git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c")


def upgrade(root: Path, *args: str) -> int:
    return subprocess.run([sys.executable, str(HERE / "upgrade_project.py"), "--path", str(root), "--no-validate", *args],
                          capture_output=True, text=True).returncode


def test_dry_run_writes_nothing():
    root = old_project()
    assert upgrade(root, "--dry-run") == 0 and git(root, "status", "--porcelain") == ""


def test_refuses_dirty_tree():
    root = old_project()
    (root / "AGENTS.md").write_text("edited\n")
    assert upgrade(root) == 1


def test_refuses_other_project():
    root = Path(tempfile.mkdtemp())
    (root / "package.json").write_text('{"name": "x"}\n')
    assert upgrade(root, "--dry-run") == 1


def test_upgrade_refreshes_and_keeps_own_text():
    root = old_project()
    assert upgrade(root) == 0
    agents = (root / "AGENTS.md").read_text()
    assert "Keep me." in agents and "Keep me too." in agents and "old rules" not in agents
    assert (root / "scripts" / "verify_zero_cosmetic_sx.py").read_text() == (HERE / "verify_zero_cosmetic_sx.py").read_text()
    assert (root / ".agents" / "skills" / SKILL / "SKILL.md").read_text() == (HERE.parent / "SKILL.md").read_text()
    scripts = json.loads((root / "package.json").read_text())["scripts"]
    assert "geosynk:upgrade" in scripts and "verify:styles" in scripts


def test_second_run_changes_nothing():
    root = old_project()
    upgrade(root)
    commit(root)
    upgrade(root)
    assert git(root, "status", "--porcelain") == ""


def main() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except AssertionError as err:
                failures += 1
                print(f"FAIL {name}: {err}")
    print("all upgrade tests pass" if not failures else f"{failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
