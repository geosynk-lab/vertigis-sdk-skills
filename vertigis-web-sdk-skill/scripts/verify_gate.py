#!/usr/bin/env python3
"""Hard Gateway for VertiGIS Studio Web and Workflow SDKs.

Provides strict, file-by-file and repository-wide enforcement of all SDK architecture,
theming, layout, and component rules.

Usage:
    python3 verify_gate.py [--file FILE | --path DIR | --git] [--strict] [--json]

Exit codes:
    0: Gate passed (all files conform to standards)
    1: Gate rejected (one or more rule violations detected)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import checks_arch
import checks_css
import checks_tokens
import checks_tsx
from engine import collect_files, run, severity_of
from report import counts, exit_code, score

CHECKS = checks_tsx.CHECKS + checks_css.CHECKS + checks_tokens.CHECKS + checks_arch.CHECKS
RESET, BOLD, GREEN, RED, YELLOW, CYAN, DIM = (
    "\033[0m", "\033[1m", "\033[32;1m", "\033[31;1m", "\033[33;1m", "\033[36m", "\033[2m"
)


def get_git_changed_files(repo_root: Path) -> list[Path]:
    """Get list of modified, added, or untracked .ts, .tsx, .css files from git."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception as err:
        print(f"{YELLOW}Warning: git status failed: {err}; scanning directory instead.{RESET}", file=sys.stderr)
        return []

    changed = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        # Format is 'XY path' or 'XY orig -> path'
        parts = line[2:].strip().split(" -> ")
        filepath = repo_root / parts[-1].strip()
        if filepath.suffix in (".ts", ".tsx", ".css") and not filepath.name.endswith(".d.ts"):
            if filepath.exists() and filepath.is_file():
                changed.append(filepath)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify_gate.py",
        description="Hard Gateway validator for VertiGIS SDK projects (file-by-file or repo-wide)."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--file", help="Audit a single source file.")
    group.add_argument("--path", default=".", help="Audit a directory (defaults to current working directory).")
    group.add_argument("--git", action="store_true", help="Audit all git-modified and untracked files.")

    parser.add_argument("--rules", default=str(HERE / "rules.json"), help="Rule catalog path.")
    parser.add_argument("--strict", action="store_true", default=True,
                        help="Fail on any Critical or Major violation (default: True).")
    parser.add_argument("--no-strict", dest="strict", action="store_false",
                        help="Fail only on Critical violations.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")

    args = parser.parse_args(argv)
    rules_path = Path(args.rules).resolve()
    if not rules_path.exists():
        print(f"{RED}Error: rules file not found: {rules_path}{RESET}", file=sys.stderr)
        return 1

    # 1. Determine files to audit
    target_files: list[Path] = []
    if args.file:
        file_path = Path(args.file).resolve()
        if not file_path.exists():
            print(f"{RED}Error: file not found: {file_path}{RESET}", file=sys.stderr)
            return 1
        target_files = [file_path]
    elif args.git:
        repo_root = Path.cwd().resolve()
        target_files = get_git_changed_files(repo_root)
        if not target_files:
            print(f"{GREEN}No git-modified or untracked .ts/.tsx/.css files to audit.{RESET}")
            return 0
    else:
        scan_dir = Path(args.path).resolve()
        if not scan_dir.exists():
            print(f"{RED}Error: path not found: {scan_dir}{RESET}", file=sys.stderr)
            return 1
        # Collect via engine logic
        src_files = collect_files(scan_dir)
        target_files = [scan_dir / f.rel if (scan_dir / f.rel).exists() else scan_dir / f.raw for f in src_files]

    # 2. Run engine against targets
    # For repo/path scans, running engine on the directory gives full cross-file context
    # For single files, running engine on the file evaluates file-level rules
    if args.file:
        result = run(target_files[0], rules_path, CHECKS)
    else:
        root_dir = Path(args.path).resolve() if not args.git else Path.cwd().resolve()
        result = run(root_dir, rules_path, CHECKS)

    # 3. Group violations by file
    violations_by_file: dict[str, list] = {}
    for v in result["violations"]:
        violations_by_file.setdefault(v.file, []).append(v)

    c = counts(result)
    gate_failed = exit_code(result, args.strict) != 0

    if args.json:
        payload = {
            "sdk": result["sdk"],
            "passed": not gate_failed,
            "total_files": result["files"],
            "counts": c,
            "score": score(result),
            "files": [
                {
                    "file": f_rel,
                    "passed": f_rel not in violations_by_file,
                    "violations": [
                        {
                            "rule": v.rule,
                            "severity": severity_of(result["catalog"][v.rule], result["sdk"]),
                            "line": v.line,
                            "detail": v.detail,
                            "summary": result["catalog"][v.rule]["summary"],
                            "remediation": result["catalog"][v.rule]["remediation"],
                        }
                        for v in violations_by_file.get(f_rel, [])
                    ],
                }
                for f_rel in sorted({v.file for v in result["violations"]} | {f.name for f in target_files})
            ],
        }
        print(json.dumps(payload, indent=2))
        return 1 if gate_failed else 0

    # 4. Render human-friendly table
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}  VERTI-GIS SDK HARD GATEWAY AUDIT ({result['sdk'].upper()} SDK){RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

    # If single file
    if args.file:
        f_rel = target_files[0].name
        file_violations = result["violations"]
        if not file_violations:
            print(f"  {GREEN}[PASS]{RESET} {BOLD}{target_files[0]}{RESET} (0 violations)")
        else:
            print(f"  {RED}[FAIL]{RESET} {BOLD}{target_files[0]}{RESET} ({len(file_violations)} violations)")
            for v in file_violations:
                entry = result["catalog"][v.rule]
                sev = severity_of(entry, result["sdk"])
                sev_color = RED if sev == "critical" else (YELLOW if sev == "major" else CYAN)
                print(f"    Line {v.line:<4}  {sev_color}{v.rule:<26}{RESET} {sev:<8} {entry['summary']}")
                if v.detail:
                    print(f"      {DIM}{v.detail}{RESET}")
                print(f"      {DIM}fix: {entry['remediation']}{RESET}")
    else:
        # Multi-file audit
        all_reported = sorted(violations_by_file.keys())
        clean_count = max(0, result["files"] - len(all_reported))
        if all_reported:
            print(f"{BOLD}Violating Files:{RESET}")
            for f_rel in all_reported:
                f_viols = violations_by_file[f_rel]
                print(f"\n  {RED}[FAIL]{RESET} {BOLD}{f_rel}{RESET} ({len(f_viols)} violations)")
                for v in f_viols:
                    entry = result["catalog"][v.rule]
                    sev = severity_of(entry, result["sdk"])
                    sev_color = RED if sev == "critical" else (YELLOW if sev == "major" else CYAN)
                    print(f"    Line {v.line:<4}  {sev_color}{v.rule:<26}{RESET} {sev:<8} {entry['summary']}")
                    if v.detail:
                        print(f"      {DIM}{v.detail}{RESET}")
                    print(f"      {DIM}fix: {entry['remediation']}{RESET}")
            print()

        if clean_count > 0:
            print(f"  {GREEN}Clean Files:{RESET} {clean_count} files passed with 0 violations.\n")

    print(f"{BOLD}{'-' * 80}{RESET}")
    print(f"  Files: {result['files']} | Critical: {c['critical']} | Major: {c['major']} | Minor: {c['minor']} | Score: {score(result)}/100")
    if gate_failed:
        print(f"  {RED}{BOLD}GATE STATUS: REJECTED{RESET} (Strict mode enabled: 0 Critical / 0 Major permitted)")
        print(f"{BOLD}{'=' * 80}{RESET}\n")
        return 1
    else:
        print(f"  {GREEN}{BOLD}GATE STATUS: APPROVED{RESET} (All standards satisfied)")
        print(f"{BOLD}{'=' * 80}{RESET}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
