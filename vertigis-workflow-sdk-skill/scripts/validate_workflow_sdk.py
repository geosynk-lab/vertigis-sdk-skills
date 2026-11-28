#!/usr/bin/env python3
"""Validate a VertiGIS Studio Workflow SDK project against the rules in rules.json.

Usage:
    python3 validate_workflow_sdk.py --path <project> [--format ansi|json|markdown] [--output FILE] [--strict]
    python3 validate_workflow_sdk.py --self-test

Exit code 1 on any Critical violation (or any Major with --strict); 0 otherwise.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main("validate_workflow_sdk.py"))
