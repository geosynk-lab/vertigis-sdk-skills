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

> **Mandatory Agent Directive**: Whenever you make any change to or create any web component in this repository, ALWAYS check and verify it against VertiGIS Web SDK standards (LayoutElement wrapper, MobX observer, semantic HTML with co-located namespaced CSS, host theme inheritance, zero custom ThemeProviders, zero @vertigis/web/ui UI controls, strict 150–250 line component modularity, and ErrorBoundary wrapper).

## 1. Typography System & Shell Inheritance
- **Typography Components vs Raw CSS Bloat**: Prefer `@mui/material` `<Typography variant="...">` (`h5`/`h6` for titles, `subtitle1`/`subtitle2` for section headers, `body1`/`body2` for reading text, `caption`/`overline` for metadata/badges) paired with semantic text color tokens (`var(--primaryForeground, #212121)`, `var(--secondaryForeground, #666666)`). Using `<Typography>` completely eliminates the need to invent repetitive CSS text classes (`.Component-title`, `.Component-type`, etc.) and deletes boilerplate font-size, line-height, and font-family declarations.
- **Strict Ban on `@vertigis/web/ui` UI Controls**: NEVER import UI controls (`Button`, `Typography`, `DynamicIcon`, `Box`, `TitleBar`, etc.) from `@vertigis/web/ui`. These internal components depend on `useUIContext()`, which is undefined in unit tests (`vitest run`), detached React portals, or custom modals, causing fatal `TypeError: Cannot read properties of undefined (reading 'translate')` crashes. Reserve `@vertigis/web/ui` strictly for non-UI SDK hooks when needed (e.g. `useWatchAndRerender`).
- **Host Shell Font Inheritance (Zero Redundant `font-family`)**: The host application shell (`.vsw-app`) strictly owns and injects the global font stack. **NEVER declare `font-family: var(--defaultFont)` on child component classes, titles, or text elements in CSS.** It is fully inherited by default. Reserve `font-family` overrides strictly for alternative font stacks (e.g. monospace code blocks via `var(--codeFont)`).
- **Semantic Text Color Tokens**: Pair text elements with semantic foreground tokens:
  - Primary text: `color: "var(--primaryForeground, #212121)"`
  - Secondary/muted text: `color: "var(--secondaryForeground, #666666)"`
  - Inactive/disabled text: `color: "var(--disabledForeground, #9e9e9e)"`

## 2. Color & Design Tokens Subsystem (Host Theme Inheritance & Zero Custom ThemeProviders)
- **Zero Hardcoded Colors & Shapes**: Strict ban on hardcoded hex (`#ffffff`), RGB (`rgb(...)`), or HSL color values, and hardcoded corner radii (e.g. `border-radius: 4px;`). Always use unified shape tokens: `var(--borderRadius, 4px)` (standard), `var(--borderRadiusSm, 2px)` (micro), `var(--borderRadiusLarge, 8px)` / `var(--borderRadiusLg, 8px)` (cards/dialogs), and `50%` / `9999px` (pills/rounds).
- **Safe Fallback Requirement**: ALWAYS provide safe fallbacks for CSS variable tokens (e.g., `var(--primaryBackground, #ffffff)`, `var(--primaryBorder, #e0e0e0)`, `var(--borderRadius, 4px)`) to ensure resilient rendering in headless, disconnected, or preview environments.
- **Host-Owned Branding Principle**: The host application shell (`.vsw-app`) strictly owns and manages all branding and themes via CSS custom properties configured in `app-config.json` / Designer. Components must NEVER create independent brands or redefine app branding.
- **Strict Ban on Custom Theme Providers**: NEVER wrap custom widgets in a custom `VertiGisThemeProvider` / `createVertiGisMuiTheme` attempting to pass CSS variables to MUI `createTheme()`. Passing `var(...)` strings without explicit color decomposition parameters causes MUI's `augmentColor()` to crash across browsers with `Error: MUI: Unsupported var(...) color`. Custom widgets natively inherit the host theme via CSS custom properties on `.vsw-app`.
- **Strict Ban on Token Re-Aliasing & Intermediate Indirection**: NEVER invent intermediate alias variables or custom color indirection layers (e.g., `--color-background: var(--primaryBackground)`, `--monitoring-bg: var(--color-background)`, `--monitoring-text: var(--primaryForeground)`). Components MUST directly consume official VertiGIS host CSS tokens with safe fallbacks (e.g., `var(--primaryBackground, #ffffff)`, `var(--primaryForeground, #212121)`, `var(--primaryBorder, #e0e0e0)`). Creating shadow token systems introduces multi-hop indirection, breaks DevTools inspectability, causes team confusion, and fragments the design system.
- **Co-Located Component CSS Architecture**:
  - Pair every component view (`ComponentName.tsx`) with a co-located CSS file (`ComponentName.css`), following official `@vertigis/web-sdk` template conventions (`PointsOfInterest.css`).
  - **Strict Ban on Global `:root` Injection**: NEVER declare `:root { ... }` rules in component CSS. Custom libraries are guest extensions running inside the host shell (`.vsw-app`). Declaring `:root` in library CSS pollutes the global document scope, risks overriding host variables, and leaks across unrelated widgets. If component-scoped CSS variables are needed for layout math (e.g. `--row-height: 36px`), declare them strictly on the namespaced component selector (e.g. `.ListHeader { --row-height: 36px; }`), never on `:root`, and never for color re-aliasing.
  - **Strict Class Namespacing**: Because Webpack compiles CSS via `style-loader` without CSS Modules hashing, all classes in `*.css` are injected into global `<head>`. All classes MUST be strictly namespaced with the component name (e.g. `.ListHeader`, `.ListHeader-title` or `.list-header__title`). Strictly BANNED: generic classes like `.header`, `.title`, `.item`, `.button`, `.card`, `.active`.
  - **Minimal Style Injection & Style Hierarchy**: (1) Co-located `ComponentName.css` for static layouts, cards, hover states, and structural chrome (using `var(--borderRadius, 4px)` and zero redundant `font-family`). (2) Native `style={{ ... }}` ONLY for purely dynamic runtime calculations (e.g. calculated widths or coordinates). (3) Strict ban on scattering loose, repetitive `sx={{ ... }}` objects across markup. Rely on parent inheritance and tokens.
- **Standardized Token Architecture**: Group all tokens under a `tokens/` directory:
  - `tokens/ui.ts`: Surface, border, foreground, accent, interactive, and unified shape tokens (`borderRadius`, `borderRadiusSm`, `borderRadiusLarge`, `borderRadiusLg`, `borderRadiusRound`, `borderRadiusPill`).
  - `tokens/typography.ts`: Typography hierarchy, font families, and weights.
  - `tokens/index.ts`: Central barrel export (never export `muiTheme`).
- **Dynamic Dual-Theme Adaptation**:
  - Use `color-mix(in srgb, ...)` for derived tints, hover states, muted borders, and transparent overlays to adapt automatically to light and dark themes without manual CSS overrides.
  - Chart/Canvas Theming: Standalone renderers (Nivo, Plotly, HTML5 Canvas) should read CSS variables or token constants directly without requiring complex reactive hooks (`useIsDarkTheme`).
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
- **Symmetric Lifecycle Sequencing**: In `_onInitialize()`, ALWAYS call `await super._onInitialize()` FIRST before setting up component resources. In `_onDestroy()`, ALWAYS clean up child subscriptions, intervals, and map layers FIRST, and invoke `await super._onDestroy()` LAST.
- **Strict Ban on Custom `_handles` Property**: NEVER declare a property named `_handles` (e.g., `private _handles = []`). Base `InitializableBase` / `HandlesMixin` initializes `this._handles` as an `@arcgis/core/core/Handles` instance. Declaring `_handles` in derived classes clobbers the base instance under ES2022 class field semantics, causing `TypeError: this._handles.destroy is not a function` during Designer unmount or deployment packaging. Use domain-specific names (e.g., `_eventHandles`, `_sketchHandles`, `_disposables`) or use inherited `this._handles.add(...)`.

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
