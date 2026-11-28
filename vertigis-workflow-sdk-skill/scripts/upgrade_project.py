#!/usr/bin/env python3
"""Upgrade a project made with a Geosynk VertiGIS skill to this version of the skill.

Identical copy in both VertiGIS SDK skills; the skill is the folder this script lives in.

    python3 <skill>/scripts/upgrade_project.py [--path DIR] [--dry-run] [--allow-dirty]
    npx -y github:geosynk-lab/vertigis-sdk-skills vertigis-web upgrade

What it refreshes (only what the project already uses, except the AGENTS.md block):
  1. the project-local skill copy in .agents/skills/<skill>
  2. the skill's block in AGENTS.md (text outside the markers is kept)
  3. scripts/verify_zero_cosmetic_sx.py and its verify:styles npm script
  4. a geosynk:upgrade npm script, so the next upgrade is one command
  5. the vsw-ui validator profile, when the project uses @geosynk/vsw-ui (web)
Then it runs the new validator and reports the result. It stops on a dirty git tree so the upgrade is one reviewable
diff (--allow-dirty to override). Exit 0 when the upgrade ran, 1 when it could not run.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
SKILL = SKILL_DIR.name
SDK = json.loads((HERE / "rules.json").read_text(encoding="utf-8"))["sdk"]
CLI_NAME = {"web": "vertigis-web", "workflow": "vertigis-workflow"}[SDK]
SDK_PACKAGES = {"web": ("@vertigis/web", "@vertigis/web-sdk"), "workflow": ("@vertigis/workflow", "@vertigis/workflow-sdk")}[SDK]
SKIP = shutil.ignore_patterns(".venv", "__pycache__", "node_modules", "raw", ".tgrep")
UPGRADE_SCRIPT = f"npx -y github:geosynk-lab/vertigis-sdk-skills {CLI_NAME} upgrade"


def load(module: str):
    spec = importlib.util.spec_from_file_location(f"{SKILL}_{module}", HERE / f"{module}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    spec.loader.exec_module(mod)
    return mod


def git_dirty(root: Path) -> bool:
    out = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
    return out.returncode == 0 and bool(out.stdout.strip())


def plan(root: Path, pkg: dict) -> list[tuple[str, object]]:
    steps: list[tuple[str, object]] = []
    local = root / ".agents" / "skills" / SKILL
    if local.is_symlink():
        steps.append((f"skip .agents/skills/{SKILL}: it is a symlink ({local.resolve()}); update its target instead", None))
    elif local.is_dir():
        steps.append((f"refresh .agents/skills/{SKILL} from this version", ("skill", local)))
    steps.append(("refresh the skill block in AGENTS.md (text outside the markers is kept)", ("agents", None)))
    styles = root / "scripts" / "verify_zero_cosmetic_sx.py"
    scripts = pkg.get("scripts") or {}
    if styles.is_file():
        steps.append(("refresh scripts/verify_zero_cosmetic_sx.py", ("styles", styles)))
        if "verify:styles" not in scripts:
            steps.append(("add npm script verify:styles", ("npm", ("verify:styles", "python3 scripts/verify_zero_cosmetic_sx.py"))))
    if scripts.get("geosynk:upgrade") != UPGRADE_SCRIPT:
        steps.append(("add npm script geosynk:upgrade", ("npm", ("geosynk:upgrade", UPGRADE_SCRIPT))))
    return steps


def apply(root: Path, steps: list, pkg_path: Path, pkg: dict) -> None:
    for _, action in steps:
        if action is None:
            continue
        kind, arg = action
        if kind == "skill":
            shutil.rmtree(arg)
            shutil.copytree(SKILL_DIR, arg, ignore=SKIP)
        elif kind == "agents":
            init = load("initiate_agents_md")
            if SDK == "web":
                init.initiate_agents_md(root, force=True, ui="auto")  # also writes the vsw-ui profile when needed
            else:
                init.initiate_agents_md(root, force=True)
        elif kind == "styles":
            shutil.copyfile(HERE / "verify_zero_cosmetic_sx.py", arg)
        elif kind == "npm":
            name, command = arg
            pkg.setdefault("scripts", {})[name] = command
    text = pkg_path.read_text(encoding="utf-8")
    indent = 4 if '\n    "' in text else 2
    pkg_path.write_text(json.dumps(pkg, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def validate(root: Path) -> None:
    validator = HERE / f"validate_{SDK}_sdk.py"
    out = subprocess.run([sys.executable, str(validator), "--path", str(root)], capture_output=True, text=True)
    plain = [re.sub(r"\x1b\[[\d;]*m", "", line) for line in out.stdout.splitlines()]
    summary = [line for line in plain if line.startswith(("PASS", "FAIL"))]
    print(f"\nValidator ({SKILL}): {summary[-1] if summary else 'no summary'}")
    if out.returncode:
        print(f"  Not a failed upgrade: these are findings under the new rules. Run: python3 {validator} --path {root}")
        print("  Existing debt can be recorded with --update-baseline; areas like a dev harness go in .vertigis-rules.json.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=f"{CLI_NAME} upgrade", description=__doc__.split("\n\n")[0])
    parser.add_argument("--path", default=".", help="Project root (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="List what would change; write nothing")
    parser.add_argument("--allow-dirty", action="store_true", help="Run even with uncommitted git changes")
    parser.add_argument("--no-validate", action="store_true", help="Skip the validator run at the end")
    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    pkg_path = root / "package.json"
    if not pkg_path.is_file():
        print(f"error: no package.json in {root}", file=sys.stderr)
        return 1
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {}), **(pkg.get("peerDependencies") or {})}
    if not any(p in deps for p in SDK_PACKAGES):
        print(f"error: {root} does not depend on {' or '.join(SDK_PACKAGES)}; is this a {CLI_NAME} project?", file=sys.stderr)
        return 1
    if not args.dry_run and not args.allow_dirty and git_dirty(root):
        print("error: uncommitted changes; commit or stash them so the upgrade is one reviewable diff "
              "(or pass --allow-dirty)", file=sys.stderr)
        return 1
    steps = plan(root, pkg)
    print(f"{CLI_NAME} upgrade: {root}")
    for label, _ in steps:
        print(f"  - {label}")
    if args.dry_run:
        print("Dry run: nothing written.")
        return 0
    apply(root, steps, pkg_path, pkg)
    print("Done. Review the changes with: git diff")
    if not args.no_validate:
        validate(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
