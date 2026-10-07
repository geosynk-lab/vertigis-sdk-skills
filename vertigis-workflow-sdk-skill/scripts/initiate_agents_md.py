#!/usr/bin/env python3
"""
initiate_agents_md.py - Configure AGENTS.md in target repositories with VertiGIS Studio Workflow SDK directives.

Supports injecting into an existing AGENTS.md (scoped between comment markers) or generating
a fresh AGENTS.md file in the target repository.
"""

import argparse
import os
import re
import sys
from pathlib import Path

START_MARKER = "<!-- vertigis-workflow-sdk:start -->"
END_MARKER = "<!-- vertigis-workflow-sdk:end -->"

DIRECTIVES_BODY = """# VertiGIS Studio Workflow SDK Development Directives

> **Mandatory Agent Directive**: Whenever you make any change to or create any custom workflow activity or custom form element (Web or Mobile) in this repository, ALWAYS check and verify it against VertiGIS Workflow SDK standards (standard props wiring `enabled`/`visible`/`readOnly`, MobX/React patterns, MUI components with sx tokens, zero hardcoded colors, design token architecture, safe fallbacks, dual-theme adaptation, strict 150–250 line component modularity, state persistence in `setValue`/`setProperty`, and ErrorBoundary wrappers).

## 1. Typography System & Shell Inheritance
- **Strict ban on raw HTML text elements**: Never use raw `<span>`, `<p>`, `<h1>`-`<h6>`, or `<label>` tags.
- **MUI Typography Component**: Always use `@mui/material` `<Typography variant="...">`:
  - `h6`: Form header, section titles, and top-level card titles.
  - `subtitle1`, `subtitle2`: Fieldset headings, group labels, and subheadings.
  - `body1`, `body2`: Standard form labels, values, instructions, and descriptions.
  - `caption`, `overline`: Helper microcopy, field validation hints, units, and timestamps.
- **Semantic Typography Palette Props**: Primary text has no `color` prop: it inherits the host foreground (`color="text.primary"` is redundant). Use `color="text.secondary"` (captions, subtitles, helper microcopy), `color="inherit"` (inside a coloured surface that sets its own foreground), and `color="error"` (validation). NEVER write bespoke inline `sx={{ color: ... }}` solely to set secondary/helper text colors.
- **Top-Level Package Exports Only**: Always import directly from package roots (`import { Box, Typography } from "@mui/material"`; `import { createTheme, ThemeProvider } from "@mui/material/styles"`). Deep imports (e.g. `@mui/material/styles/createTheme`) are deprecated in MUI v7 and break under modern bundlers.
- **Zero `font-family` (No Exceptions)**: Typography and font family are inherited natively from the host shell (`.vsw-app` / Workflow host). NEVER declare `font-family`, the `font:` shorthand, or `fontFamily` anywhere (CSS, `sx`, `style`, token files). The single allowed line is `typography: { fontFamily: "inherit" }` in the `createTheme` theme provider. Using `<Typography>` deletes boilerplate font-size and line-height declarations.
- **Mobile & Field Form Readability**: Ensure minimum text sizing (at least 14px / `body2` on mobile screens) and comfortable line-height for readability in high-glare outdoor environments.

## 2. Host-Governed Styling (Zero Cosmetic `sx`)
- **Six Principles**:
  1. **Host governs cosmetics**: The host (VertiGIS Studio Web / Mobile runtime) supplies MUI theme + CSS custom properties (portal branding). Form elements inherit surface, elevation, borders and typography.
  2. **Zero cosmetic properties in component `sx`, `style`, `styles` dictionaries and `styled()`**: Banned: `border*`, `outline*`, `borderRadius*`, `background*`, `bgcolor`, `backdropFilter`, `boxShadow`, `textShadow`, `filter`, `color`, `textColor`, `textDecoration`, `textTransform`, `fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `letterSpacing`. These live ONLY in `src/tokens/muiTheme.ts` (`createTheme` `components.*.styleOverrides`) or are inherited. Text uses `<Typography variant>` and `color="text.secondary"`. Standard form controls (`TextField`, `Select`, `Button`) get states natively via `error`, `disabled={!enabled}`, and `helperText`.
  3. **Canonical layout, gap over margin**: 1D -> `<Stack direction spacing alignItems justifyContent>`. 2D -> `<Box sx={{ display: "flex", flexDirection, gap, alignItems }}>` or `<Grid container spacing>`. Space siblings via parent `gap` or `Stack spacing`, never child `margin`. Allowed `sx` keys: display, flex*, align*, justify*, grid*, spacing keys, sizing (width/height/min/max), positioning (position/top/bottom/left/right/zIndex), and overflow*.
  4. **8px grid spacing**: All spacing (`p*`, `m*`, `gap`, `spacing`) must use canonical 8px grid steps: `0, 0.5, 1, 1.5, 2, 2.5, 3, 4` (negatives, `"auto"`, and responsive objects allowed). Raw pixel strings (`"13px"`) and arbitrary decimals (`0.35`) are banned. Do NOT set `spacing: 5` in createTheme.
  5. **Declarative state via data attributes**: Express dynamic status via `<Card data-status={status}>`. Style `&[data-status="..."]` centrally in `src/tokens/muiTheme.ts`.
  6. **Containment**: `<canvas>` (signature pads), `<img>` (QR codes), `<iframe>` (captcha) must have `Paper`, `Card`, `CardContent`, `CardMedia` or `CardActionArea` as nearest JSX parent (e.g. `<Paper variant="outlined">`); child keeps only functional sizing (`style={{ width: "100%" }}`).
- **No Custom CSS**: NEVER generate `*.css` or `*.module.css` files in Workflow form elements. Form elements run across Web and Mobile runtimes; cosmetics come from `VertiGisThemeProvider` (`src/tokens/muiTheme.ts`), and component `sx` carries layout only.
- **Zero Hardcoded Colors & Shapes**: Strict ban on hardcoded hex (`#ffffff`), RGB (`rgb(...)`), or HSL color values, and hardcoded corner radii (e.g. `4px`). Always reference unified shape tokens: `var(--borderRadius, 4px)` (standard), `var(--borderRadiusSm, 2px)` (micro), `var(--borderRadiusLarge, 8px)` / `var(--borderRadiusLg, 8px)` (cards/dialogs), and `50%` / `9999px` (pills/rounds).
- **Crash Prevention**: NEVER pass raw `var(...)` strings (including any `UI_TOKENS.*` value) into `palette.primary.main` or `palette.error.main` (causes MUI `augmentColor()` to crash). Attach CSS variables via component `styleOverrides` (e.g. `MuiRadio: { styleOverrides: { root: { "&.Mui-checked": { color: "var(--primaryAccent, #007ac2)" } } } }`). Use `color-mix(in srgb, ...)` instead of `alpha()`, and configure `MuiLink` `styleOverrides` in `src/tokens/muiTheme.ts`.
- **Strict Ban on `<CssBaseline />`**: NEVER mount `<CssBaseline />` under `VertiGisThemeProvider` or anywhere in form elements.
- **MUI v7 `slotProps` Standardization**: Use `slotProps` for composite controls (`<TextField slotProps={{ input: { readOnly } }}>`).

## 3. Strict Component Modularity & Anti-God-Component Architecture
- **Strict File Size Thresholds**: Max 150–250 lines per file. Any file exceeding 250 lines MUST be refactored and decomposed.
- **JSX Only in `.tsx`**: Any file containing JSX MUST use the `.tsx` extension; never put JSX in a `.ts` file.
- **Standard Directory Blueprint**: Decompose complex form elements into:
  - `components/`: Presentational, stateless sub-components using MUI.
  - `hooks/`: Custom React hooks for state, lifecycle subscriptions, and workflow event handling.
  - `tokens/`: Centralized design token definitions and theme utilities.
  - `utils/`: Pure helper functions, defaults, and geometry algorithms.
  - `types/`: Domain models and prop interfaces.
- **Defensive Error Boundaries**: Wrap all custom form elements in a `<FormElementErrorBoundary>` to prevent layout crashes from bubbling up to the host application.

## 4. Mobile & Multi-Host Form Element Guidelines
- **Multi-Host Consistency**: Workflow form elements run across VertiGIS Studio Web (desktop), VertiGIS Studio Mobile (iOS, Android, Windows), and ArcGIS Experience Builder. UI must be responsive and adaptive.
- **Mobile Touch Targets**: All interactive controls (buttons, inputs, toggles, icon triggers) must maintain a minimum touch target size of 44x44px (WCAG 2.5.5 / 2.5.8).
- **Field Contrast & Sunlight Readability**: Outdoor field workers require strict WCAG AA contrast (minimum 4.5:1 for standard text, 3:1 for graphical elements and large headings) across both light and dark host themes.
- **State Token Wiring**:
  - `enabled`: Map `!enabled` to `disabled={!enabled}` on MUI controls.
  - `readOnly`: Display with a subtle non-editable background distinctly different from disabled (`readOnly` remains legible and selectable).
  - Validation errors: Wire via `error` and `helperText` on MUI controls.

## 5. Architecture & State Persistence
- **State Persistence (Surviving Tab Remounts)**: Form element state MUST be saved via `props.setValue()` or `props.setProperty()`. NEVER rely on ephemeral local React `useState` for critical business data, as form elements unmount and remount when users navigate between form tabs or workflow steps.
- **Defensive Activities**: Workflow Activities MUST wrap core execution logic in `try/catch` blocks and throw structured `Error` objects so the workflow engine can handle failures gracefully.

## 6. Verification & Rule Validator Gate
- After every code edit, run all of these and report each exit code. A passing build and lint is NOT a passing gate. Skip a step only when its script does not exist in `package.json`, and say so:
  1. `tsc --noEmit` (clean types).
  2. `npm run lint` (zero errors).
  3. `npm run verify:styles` (= `python3 scripts/verify_zero_cosmetic_sx.py`) MUST exit 0.
  4. `npm test` (all tests pass).
  5. `npm run build` (clean compilation).
  6. `python3 <skill-dir>/scripts/validate_workflow_sdk.py --path .` MUST exit 0, where `<skill-dir>` is the installed `vertigis-workflow-sdk-skill` folder (e.g. `~/.agents/skills/vertigis-workflow-sdk-skill`). Suppress a rule only with a written reason: `// vertigis-rule-disable RULE_ID -- <reason>`."""

VERTIGIS_DIRECTIVES = f"{START_MARKER}\n{DIRECTIVES_BODY}\n{END_MARKER}"


def initiate_agents_md(target_dir: Path, force: bool = False) -> None:
    """Inject or update the VertiGIS Workflow SDK directives block in AGENTS.md."""
    target_dir.mkdir(parents=True, exist_ok=True)
    agents_file = target_dir / "AGENTS.md"

    if not agents_file.exists():
        # Create fresh AGENTS.md
        initial_content = f"# Repository Agent Directives\n\n{VERTIGIS_DIRECTIVES}\n"
        agents_file.write_text(initial_content, encoding="utf-8")
        print(f"Created {agents_file} with VertiGIS Studio Workflow SDK directives.")
        return

    content = agents_file.read_text(encoding="utf-8")
    marker_pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL
    )

    if marker_pattern.search(content):
        if not force:
            print(
                f"Notice: VertiGIS Studio Workflow SDK directives already exist in {agents_file}.\n"
                f"Use --force to overwrite the existing block."
            )
            return
        # Replace existing block
        updated_content = marker_pattern.sub(VERTIGIS_DIRECTIVES, content)
        agents_file.write_text(updated_content, encoding="utf-8")
        print(f"Updated existing VertiGIS Studio Workflow SDK directives in {agents_file}.")
    else:
        # Append block to existing file
        separator = "\n\n" if not content.endswith("\n\n") else ""
        if content.endswith("\n") and not content.endswith("\n\n"):
            separator = "\n"
        elif not content.endswith("\n"):
            separator = "\n\n"

        updated_content = f"{content}{separator}{VERTIGIS_DIRECTIVES}\n"
        agents_file.write_text(updated_content, encoding="utf-8")
        print(f"Appended VertiGIS Studio Workflow SDK directives to {agents_file}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Configure or update AGENTS.md with VertiGIS Studio Workflow SDK development directives."
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
        help="Force overwrite of existing VertiGIS Workflow SDK directives block in AGENTS.md",
    )
    parser.add_argument(
        "--skills",
        "--install-skill",
        dest="install_skill",
        action="store_true",
        default=None,
        help="Install the vertigis-workflow-sdk-skill into the target project via npx skills add",
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
                    "\n? Would you like to install the VertiGIS Workflow SDK AI Skill into this project repository? [Y/n]: "
                ).strip().lower()
                should_install = response == "" or response.startswith("y")
            except (KeyboardInterrupt, EOFError):
                should_install = False
        else:
            print("\n[INFO] To install the AI skill, run: npx skills add geosynk-lab/vertigis-sdk-skills --skill vertigis-workflow-sdk-skill")

    if should_install:
        print("\n[SKILLS] Installing vertigis-workflow-sdk-skill via npx skills add...")
        import subprocess
        try:
            subprocess.run(
                ["npx", "--yes", "skills", "add", "geosynk-lab/vertigis-sdk-skills", "--skill", "vertigis-workflow-sdk-skill", "-y"],
                cwd=str(target_path),
                check=True,
            )
            print("✔ Skill installed successfully into .agents/skills/\n")
        except Exception as e:
            print(f"[WARN] Failed to install skill automatically: {e}")
            print("[INFO] You can run manually: npx skills add geosynk-lab/vertigis-sdk-skills --skill vertigis-workflow-sdk-skill\n")


if __name__ == "__main__":
    main()
