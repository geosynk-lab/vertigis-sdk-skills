#!/usr/bin/env python3
"""
install_styling_audit.py - Install the VertiGIS Web SDK static styling audit into a target repository.

Copies scripts/styling-audit/stylingAudit.ts and stylingAudit.test.ts into <target>/src/utils/.
The test runs as part of the normal Vitest suite (`pnpm test` / `npm test`) and enforces the
styling rules of this skill with per-rule ratchet ceilings.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent / "styling-audit"
FILES = ("stylingAudit.ts", "stylingAudit.test.ts")
REQUIRED_DEV_DEPS = ("typescript", "vitest")


def missing_dependencies(target_dir: Path) -> list[str]:
    package_json = target_dir / "package.json"
    if not package_json.exists():
        return list(REQUIRED_DEV_DEPS)
    data = json.loads(package_json.read_text(encoding="utf-8"))
    declared = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return [dep for dep in REQUIRED_DEV_DEPS if dep not in declared]


def install(target_dir: Path, force: bool) -> int:
    if not (target_dir / "src").is_dir():
        print(f"Error: {target_dir / 'src'} not found. Run this from a VertiGIS Web library root.", file=sys.stderr)
        return 1

    dest_dir = target_dir / "src" / "utils"
    existing = [name for name in FILES if (dest_dir / name).exists()]
    if existing and not force:
        print(f"Skipped: {', '.join(existing)} already exist in {dest_dir}. Use --force to overwrite.")
        return 0

    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copyfile(SOURCE_DIR / name, dest_dir / name)
        print(f"Installed {dest_dir / name}")

    missing = missing_dependencies(target_dir)
    if missing:
        print(f"Warning: missing dev dependencies {', '.join(missing)}. Ask before adding them.")

    if not (target_dir / "src" / "tokens" / "ui.ts").exists():
        print("Note: src/tokens/ui.ts not found; the token-fallback-drift rule stays inactive until it exists.")

    print(
        "\nNext steps:\n"
        "  1. Print the current counts:\n"
        "       STYLE_AUDIT_REPORT=1 npx vitest run src/utils/stylingAudit.test.ts -t \"prints a report\"\n"
        "  2. Set each BASELINE ceiling in stylingAudit.test.ts to the count found.\n"
        "  3. Migrate files and lower the ceilings as counts drop.\n"
        "     List one file's violations with STYLE_AUDIT_FILE=<path> added to the command above.\n"
        "  4. When only justified violations remain, list them in KNOWN_EXCEPTIONS\n"
        "     and set ENFORCE_EXCEPTIONS_ONLY = true."
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the VertiGIS Web SDK styling audit test into a repository.")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path.cwd(),
        help="Library root containing src/ (default: current directory)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing audit files")
    args = parser.parse_args()
    sys.exit(install(args.target_dir.resolve(), args.force))


if __name__ == "__main__":
    main()
