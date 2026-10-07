"""Command-line entry point shared by validate_web_sdk.py and validate_workflow_sdk.py."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import checks_arch
import checks_css
import checks_tokens
import checks_tsx
from engine import run
from report import RENDERERS, exit_code

HERE = Path(__file__).resolve().parent
CHECKS = checks_tsx.CHECKS + checks_css.CHECKS + checks_tokens.CHECKS + checks_arch.CHECKS
IMPLEMENTED = (checks_tsx.RULE_IDS | checks_css.RULE_IDS | checks_tokens.RULE_IDS | checks_arch.RULE_IDS
               | {"INVALID_SUPPRESSION"})


def main(prog: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=prog, description="Validate a project against the VertiGIS SDK skill rules.")
    parser.add_argument("--path", help="Project root (scans <path>/src when present) or a single file.")
    parser.add_argument("--format", choices=sorted(RENDERERS), default="ansi")
    parser.add_argument("--output", help="Write the report to this file instead of stdout.")
    parser.add_argument("--rules", default=str(HERE / "rules.json"), help="Rule catalog (default: sibling rules.json).")
    parser.add_argument("--strict", action="store_true", help="Also fail on Major violations.")
    parser.add_argument("--self-test", action="store_true", help="Run rule fixtures, example and catalog checks.")
    args = parser.parse_args(argv)
    if args.self_test:
        from selftest import self_test
        return self_test(HERE, CHECKS, IMPLEMENTED)
    if not args.path:
        parser.error("--path is required (or use --self-test)")
    if not Path(args.path).exists():
        parser.error(f"path not found: {args.path}")
    result = run(Path(args.path), Path(args.rules), CHECKS)
    text = RENDERERS[args.format](result, args.strict)
    if args.output:
        Path(args.output).write_text(re.sub(r"\033\[[\d;]*m", "", text), encoding="utf-8")
        print(f"report written to {args.output}; {len(result['violations'])} violations")
    else:
        print(text)
    return exit_code(result, args.strict)


if __name__ == "__main__":
    sys.exit(main("cli.py"))
