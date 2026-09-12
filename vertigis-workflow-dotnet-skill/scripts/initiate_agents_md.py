#!/usr/bin/env python3
"""
initiate_agents_md.py - Configure AGENTS.md in target repositories with VertiGIS Studio Workflow .NET SDK directives.

Supports injecting into an existing AGENTS.md (scoped between comment markers) or generating
a fresh AGENTS.md file in the target repository.
"""

import argparse
import os
import re
import sys
from pathlib import Path

START_MARKER = "<!-- vertigis-workflow-dotnet:start -->"
END_MARKER = "<!-- vertigis-workflow-dotnet:end -->"

DIRECTIVES_BODY = """# VertiGIS Studio Workflow .NET SDK Development Directives

> **Mandatory Agent Directive**: Whenever you make any change to or create any custom .NET workflow activity or Mobile form element in this repository, ALWAYS check and verify it against VertiGIS Workflow .NET SDK standards (strict `IActivityHandler` implementation, defensive `TryGetValue` input parsing, `QueuedTask.Run` for ArcGIS Pro, zero sync-over-async, XAML `ContentComponent` for Mobile, and static `Action` registration).

## 1. Core Architecture & Activity Implementation
- **Strict `IActivityHandler` Signature**: All custom workflow activities must implement `VertiGIS.Workflow.Runtime.IActivityHandler` and the signature:
  `public async Task<IDictionary<string, object?>> Execute(IDictionary<string, object?> inputs, IActivityContext context)`
- **Static Action Identifier**: Every activity must define a public static Action string property (e.g., `public static string Action { get; } = "uuid:<namespace>::<ActivityName>";`).
- **Defensive Input Parsing**: Never directly index into inputs dictionaries (`inputs["key"]`). Always use `inputs.TryGetValue("paramName", out var value)` with null-checks to prevent runtime `KeyNotFoundException`.
- **Structured Error Handling**: Wrap execution logic in `try/catch` blocks and throw descriptive exceptions with actionable diagnostic messages so the workflow engine surfaces meaningful error states.

## 2. Asynchronous Execution & Threading Safety
- **No Sync-Over-Async**: NEVER call `.Result`, `.Wait()`, or `.GetAwaiter().GetResult()` on asynchronous tasks. Always `await` operations or return `Task.FromResult(...)` to prevent deadlocks in host execution runtimes.
- **ArcGIS Pro Threading (`QueuedTask.Run`)**: When targeting VertiGIS Studio Desktop (ArcGIS Pro), all calls to ArcGIS Pro SDK internal objects, geometries, and mapping APIs must run inside `await QueuedTask.Run(...)` on the main CIM thread.

## 3. Platform Scoping Rules
- **Platform UI Restrictions**: Form elements (interactive controls) are ONLY supported in **VertiGIS Studio Mobile** (VSM). VertiGIS Studio Desktop (ArcGIS Pro) and VertiGIS Studio Workflow Server (VSS) are headless runtimes supporting **Activities only**.
- **Mobile Form Element Blueprint**:
  - Custom UI views must inherit from `VertiGIS.Mobile.Forms.ContentComponent` using XAML and C# code-behind.
  - Every custom form element must be paired with a registration activity inheriting from `RegisterCustomFormElementBase`.
  - Controls must maintain a minimum touch target size of 44x44px and provide accessible labels for field device touchscreens.

## 4. Workflow Designer Stubs
- When providing TypeScript declaration stubs for the Workflow Designer toolbox, use standard JSDoc tags:
  - `@action`: Must match the C# static `Action` identifier exactly.
  - `@supportedApps`: Define target apps, e.g. `VSM, VSD, VSS`.
  - Dropdown parameters: Use inline union types (e.g., `mode: 'OptionA' | 'OptionB' | string;`) rather than external type aliases so the Designer inspector renders a dropdown select."""

VERTIGIS_DIRECTIVES = f"{START_MARKER}\n{DIRECTIVES_BODY}\n{END_MARKER}"


def initiate_agents_md(target_dir: Path, force: bool = False) -> None:
    """Inject or update the VertiGIS Workflow .NET SDK directives block in AGENTS.md."""
    target_dir.mkdir(parents=True, exist_ok=True)
    agents_file = target_dir / "AGENTS.md"

    if not agents_file.exists():
        initial_content = f"# Repository Agent Directives\n\n{VERTIGIS_DIRECTIVES}\n"
        agents_file.write_text(initial_content, encoding="utf-8")
        print(f"Created {agents_file} with VertiGIS Studio Workflow .NET SDK directives.")
        return

    content = agents_file.read_text(encoding="utf-8")
    marker_pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL
    )

    if marker_pattern.search(content):
        if not force:
            print(
                f"Notice: VertiGIS Studio Workflow .NET SDK directives already exist in {agents_file}.\n"
                f"Use --force to overwrite the existing block."
            )
            return
        new_content = marker_pattern.sub(VERTIGIS_DIRECTIVES, content)
        agents_file.write_text(new_content, encoding="utf-8")
        print(f"Updated VertiGIS Studio Workflow .NET SDK directives in {agents_file}.")
    else:
        new_content = f"{content.rstrip()}\n\n{VERTIGIS_DIRECTIVES}\n"
        agents_file.write_text(new_content, encoding="utf-8")
        print(f"Injected VertiGIS Studio Workflow .NET SDK directives into {agents_file}.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject or update VertiGIS Studio Workflow .NET SDK directives in AGENTS.md"
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory containing or to contain AGENTS.md (default: current working directory)"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing VertiGIS Studio Workflow .NET SDK directives block if present"
    )
    args = parser.parse_args()

    try:
        initiate_agents_md(args.target_dir.resolve(), force=args.force)
        return 0
    except Exception as e:
        print(f"Error configuring AGENTS.md: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
