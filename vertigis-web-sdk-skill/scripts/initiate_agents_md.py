#!/usr/bin/env python3
"""
initiate_agents_md.py - Configure AGENTS.md in target repositories with VertiGIS Studio Web SDK directives.

Supports injecting into an existing AGENTS.md (scoped between comment markers) or generating
a fresh AGENTS.md file in the target repository.
"""

import argparse
import os
import re
import sys
from pathlib import Path

START_MARKER = "<!-- vertigis-web-sdk:start -->"
END_MARKER = "<!-- vertigis-web-sdk:end -->"

DIRECTIVES_BODY = """# VertiGIS Studio Web SDK Development Directives

> **Mandatory Agent Directive**: Whenever you make any change to or create any web component in this repository, ALWAYS check and verify it against VertiGIS Web SDK standards (LayoutElement wrapper, MobX observer, MUI components with sx tokens, zero hardcoded colors, design token architecture, dual-theme adaptation, strict 150–250 line component modularity, and ErrorBoundary wrapper).

## 1. Typography System
- **Strict ban on raw HTML text elements**: Never use raw `<span>`, `<p>`, or `<h1>`-`<h6>` tags.
- **MUI Typography Component**: Always use `@mui/material` `<Typography variant="...">`:
  - `h5`, `h6`: Widget titles and primary container headers.
  - `subtitle1`, `subtitle2`: Section headers, grouping titles, and card subheadings.
  - `body1`, `body2`: Primary and secondary descriptive body text.
  - `caption`, `overline`: Microcopy, timestamps, metadata labels, and status badges.
- **Semantic Text Color Tokens**: Always pair Typography variants with semantic foreground tokens via `sx`:
  - Primary text: `color: "var(--primaryForeground, #1e1e1e)"`
  - Secondary/muted text: `color: "var(--secondaryForeground, #666666)"`
  - Inactive/disabled text: `color: "var(--disabledForeground, #9e9e9e)"`
- **Font Family**: Use `fontFamily: "var(--defaultFont)"` (inherited automatically through MUI components).

## 2. Color & Design Tokens Subsystem
- **Zero Hardcoded Colors**: Strict ban on hardcoded hex (`#ffffff`), RGB (`rgb(...)`), or HSL color values for UI chrome, backgrounds, text, and borders.
- **Safe Fallback Requirement**: ALWAYS provide safe fallbacks for CSS variable tokens (e.g., `var(--primaryBackground, #ffffff)`) to ensure resilient rendering in headless, disconnected, or preview environments.
- **Standardized Token Architecture**: Group all tokens under a `tokens/` directory:
  - `tokens/ui.ts`: Surface, border, foreground, accent, interactive, and alert tokens.
  - `tokens/typography.ts`: Typography hierarchy, font families, and weights.
  - `tokens/index.ts`: Central barrel export.
- **Dynamic Dual-Theme Adaptation**:
  - Use `color-mix(in srgb, ...)` for derived tints, hover states, muted borders, and transparent overlays to adapt automatically to light and dark themes without manual CSS overrides.
  - Use the canonical reactive `useIsDarkTheme()` hook for DOM/shell theme detection.
  - Use `isDarkTheme()` standalone utility for non-CSS contexts (Plotly, canvas renderers, third-party iframe bridges, PDF exports).
- **MUI Theme Integration**: Apply `createTheme` overrides and `ThemeProvider` to align composite controls (sliders, toggle buttons, pickers) with VertiGIS shell branding.
- **GIS Visual Hierarchy**: Keep UI chrome neutral and subdued so the GIS map canvas remains the focal point. Ensure WCAG AA contrast compliance (minimum 4.5:1 for normal text, 3:1 for large text).

## 3. Strict Component Modularity & Anti-God-Component Architecture
- **Strict File Size Thresholds**: Max 150–250 lines per file. Any file exceeding 250 lines MUST be refactored and decomposed.
- **Standard Directory Blueprint**: Decompose complex components into:
  - `components/`: Presentational, stateless sub-components.
  - `hooks/`: Custom React hooks for state, lifecycle subscriptions, and business logic.
  - `services/`: Component-level services and integrations.
  - `utils/` / `helpers/`: Pure functions, calculations, and zero-dependency helpers.
  - `tokens/`: Design tokens and theme mappings.
  - `types/`: Type contracts, interfaces, and serialization models.
- **Model vs View Separation**:
  - MobX Component Models (`*Model.ts`): State, observables, service injection, and lifecycle hooks (`_onInitialize()`, `_onDestroy()`).
  - React Views (`*.tsx`): Visual rendering, layout slotting wrapped in `<LayoutElement {...props}>`, `observer()`, and `<ErrorBoundary>`.
- **Extraction Heuristics**:
  - Extract sub-views when JSX nesting exceeds 3 levels or individual visual sections emerge.
  - Extract event listeners, timers, and data operations into custom hooks.
  - Extract data formatting and business logic into pure, testable utility functions.

## 4. Component Architecture & Lifecycle
- **`<LayoutElement {...props}>` Root**: Every React component view MUST wrap all JSX within `<LayoutElement {...props}>` from `@vertigis/web/components` for layout slotting and Designer support.
- **MobX `observer()`**: Wrap all React views that read model observables with `observer()` from `mobx-react-lite`.
- **`<ErrorBoundary>` Wrapping**: Wrap custom widget contents in an `<ErrorBoundary>` component to isolate runtime faults and protect host application stability.
- **Lifecycle Cleanup**: All subscriptions, intervals, and MobX reactions initialized in `_onInitialize()` MUST be cleanly disposed in `_onDestroy()`.

## 5. Web Designer Settings Schema Protocol
When exposing customizable component properties to the VertiGIS Studio Web Designer inspector panel:
- **Schema Declaration (`getLayoutDesignerSettingsSchema`)**: Return a `SettingsSchema` declaring setting fields (`id`, `type` such as `text`, `number`, `checkbox`, `select`, `displayName`, `description`).
- **Current Value Extraction (`getLayoutDesignerSettings`)**: Read XML attributes from layout node (`args.node.attributes.get(...)`) and map them to the Designer settings form state.
- **Persisting Changes (`applyLayoutDesignerSettings`)**: Write updated attributes back to `args.node.attributes.set(...)` and propagate configuration changes to the live model via `model.updateConfig(...)`."""

VERTIGIS_DIRECTIVES = f"{START_MARKER}\n{DIRECTIVES_BODY}\n{END_MARKER}"


def initiate_agents_md(target_dir: Path, force: bool = False) -> None:
    """Inject or update the VertiGIS Web SDK directives block in AGENTS.md."""
    target_dir.mkdir(parents=True, exist_ok=True)
    agents_file = target_dir / "AGENTS.md"

    if not agents_file.exists():
        # Create fresh AGENTS.md
        initial_content = f"# Repository Agent Directives\n\n{VERTIGIS_DIRECTIVES}\n"
        agents_file.write_text(initial_content, encoding="utf-8")
        print(f"Created {agents_file} with VertiGIS Studio Web SDK directives.")
        return

    content = agents_file.read_text(encoding="utf-8")
    marker_pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL
    )

    if marker_pattern.search(content):
        if not force:
            print(
                f"Notice: VertiGIS Studio Web SDK directives already exist in {agents_file}.\n"
                f"Use --force to overwrite the existing block."
            )
            return
        # Replace existing block
        updated_content = marker_pattern.sub(VERTIGIS_DIRECTIVES, content)
        agents_file.write_text(updated_content, encoding="utf-8")
        print(f"Updated existing VertiGIS Studio Web SDK directives in {agents_file}.")
    else:
        # Append block to existing file
        separator = "\n\n" if not content.endswith("\n\n") else ""
        if content.endswith("\n") and not content.endswith("\n\n"):
            separator = "\n"
        elif not content.endswith("\n"):
            separator = "\n\n"

        updated_content = f"{content}{separator}{VERTIGIS_DIRECTIVES}\n"
        agents_file.write_text(updated_content, encoding="utf-8")
        print(f"Appended VertiGIS Studio Web SDK directives to {agents_file}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure or update AGENTS.md with VertiGIS Studio Web SDK development directives."
    )
    parser.add_argument(
        "target_dir_pos",
        nargs="?",
        default=None,
        metavar="TARGET_DIR",
        help="Target directory where AGENTS.md should be created or updated (default: current directory)",
    )
    parser.add_argument(
        "-t",
        "--target-dir",
        dest="target_dir_opt",
        metavar="TARGET_DIR",
        default=None,
        help="Target directory (overrides positional argument)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of existing VertiGIS Web SDK directives block in AGENTS.md",
    )
    parser.add_argument(
        "--skills",
        "--install-skill",
        dest="install_skill",
        action="store_true",
        default=None,
        help="Install the vertigis-web-sdk-skill into the target project via npx skills add",
    )
    parser.add_argument(
        "--no-skills",
        dest="no_skills",
        action="store_true",
        help="Skip skill installation prompt",
    )

    args = parser.parse_args()
    target_path = Path(args.target_dir_opt or args.target_dir_pos or ".").resolve()
    initiate_agents_md(target_path, force=args.force)

    # Prompt to install skill via npx skills add
    should_install = args.install_skill
    if should_install is None and not args.no_skills:
        if sys.stdin.isatty():
            try:
                response = input(
                    "\n? Would you like to install the VertiGIS Web SDK AI Skill into this project repository? [Y/n]: "
                ).strip().lower()
                should_install = response == "" or response.startswith("y")
            except (KeyboardInterrupt, EOFError):
                should_install = False
        else:
            print("\n[INFO] To install the AI skill, run: npx skills add geosynk-lab/vertigis-sdk-skills --skill vertigis-web-sdk-skill")

    if should_install:
        print("\n[SKILLS] Installing vertigis-web-sdk-skill via npx skills add...")
        import subprocess
        try:
            subprocess.run(
                ["npx", "--yes", "skills", "add", "geosynk-lab/vertigis-sdk-skills", "--skill", "vertigis-web-sdk-skill", "-y"],
                cwd=str(target_path),
                check=True,
            )
            print("✔ Skill installed successfully into .agents/skills/\n")
        except Exception as e:
            print(f"[WARN] Failed to install skill automatically: {e}")
            print("[INFO] You can run manually: npx skills add geosynk-lab/vertigis-sdk-skills --skill vertigis-web-sdk-skill\n")


if __name__ == "__main__":
    main()
