"""--self-test: catalog consistency, per-rule fixtures and SKILL.md examples. Identical copy in both skills."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from engine import SEVERITIES, load_catalog, run

REQUIRED_FIELDS = {"id", "sdk", "pillar", "severity", "skill_ref", "audit_id", "summary", "remediation"}


def catalog_errors(here: Path, implemented: set) -> list[str]:
    errors = []
    sdk, catalog = load_catalog(here / "rules.json")
    audit_ts = here / "styling-audit" / "stylingAudit.ts"
    audit_text = audit_ts.read_text(encoding="utf-8") if audit_ts.exists() else None
    for rule_id, entry in catalog.items():
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            errors.append(f"{rule_id}: missing fields {sorted(missing)}")
        if sdk not in entry.get("sdk", []):
            errors.append(f"{rule_id}: sdk list does not include {sdk}")
        sev = entry.get("severity")
        sevs = sev.values() if isinstance(sev, dict) else [sev]
        if any(s not in SEVERITIES for s in sevs):
            errors.append(f"{rule_id}: invalid severity {sev}")
        if rule_id not in implemented:
            errors.append(f"{rule_id}: no check implements this rule")
        audit = entry.get("audit_id")
        for aid in ([audit] if isinstance(audit, str) else audit or []):
            if audit_text is not None and f'"{aid}":' not in audit_text:
                errors.append(f"{rule_id}: audit_id {aid} not in stylingAudit.ts RULES")
    other = "workflow" if sdk == "web" else "web"
    sibling = here.parent.parent / f"vertigis-{other}-sdk-skill" / "scripts" / "rules.json"
    if sibling.exists():
        _, other_catalog = load_catalog(sibling)
        for rule_id, entry in catalog.items():
            if other in entry["sdk"] and other_catalog.get(rule_id) != entry:
                errors.append(f"{rule_id}: entry differs from {sibling}")
    return errors


def fixture_target(folder: Path, name: str) -> Path | None:
    if (folder / name).is_dir():
        return folder / name
    found = sorted(folder.glob(f"{name}.*"))
    return found[0] if found else None


def fixture_errors(here: Path, checks: list) -> list[str]:
    errors = []
    _, catalog = load_catalog(here / "rules.json")
    root = here / "tests" / "fixtures"
    folders = {p.name: p for p in root.iterdir() if p.is_dir()} if root.is_dir() else {}
    for extra in sorted(set(folders) - set(catalog)):
        errors.append(f"fixtures/{extra}: not a rule in rules.json")
    for rule_id in sorted(catalog):
        folder = folders.get(rule_id)
        if folder is None:
            errors.append(f"{rule_id}: no fixture folder")
            continue
        expected_file = folder / "expected.txt"
        expected = set(expected_file.read_text().split()) if expected_file.exists() else {rule_id}
        for name, want in (("bad", expected), ("good", set())):
            target = fixture_target(folder, name)
            if target is None:
                errors.append(f"{rule_id}: missing {name} fixture")
                continue
            got = {v.rule for v in run(target, here / "rules.json", checks)["violations"]}
            if got != want:
                errors.append(f"{rule_id}/{target.name}: expected {sorted(want)}, got {sorted(got)}")
    return errors


def self_test(here: Path, checks: list, implemented: set) -> int:
    sys.path.insert(0, str(here / "tests"))
    from test_examples import example_errors

    sections = [
        ("catalog", catalog_errors(here, implemented)),
        ("fixtures", fixture_errors(here, checks)),
        ("examples", example_errors(here.parent, checks)),
    ]
    failed = 0
    for name, errors in sections:
        print(f"{'PASS' if not errors else 'FAIL'}  {name}" + (f" ({len(errors)} problems)" if errors else ""))
        for e in errors:
            print(f"      {e}")
        failed += len(errors)
    print(json.dumps({"self_test": "pass" if not failed else "fail", "problems": failed}))
    return 1 if failed else 0
