# VertiGIS Studio Workflow SDK: Interactive Scaffolding, Code Reviews & Tooling

## Overview
When interacting with a developer, the agent follows an interactive consultation protocol ("Grill-Me" mode) to discover project requirements, verify SSL certificates, configure `AGENTS.md` directives via `initiate`, and audit existing code with categorized severity levels.

---

## 1. Interactive Onboarding & Discovery Flow

```mermaid
flowchart TD
    A[Skill Triggered / 'initiate' command] --> B[Scan Workspace for Project Files]

    B --> C{Workspace State}

    C -->|Existing Project| D
    C -->|Empty / New| E

    subgraph D [Existing Workspace]
        D1[Review Code Categorized]
        D2[Configure AGENTS.md ('initiate')]
        D3[Add New Activity]
        D4[Add New Form Element]
        D5[Generate Tooling Scripts]
    end

    subgraph E [Grill-Me Discovery]
        E1[Target Activity vs Form Element]
        E2[Name, Category & Display Name]
        E3[HTTPS SSL Strategy]
        E4[Scaffold Project, AGENTS.md & Scripts]
    end
```

---

## 2. Categorized Code Review Audit Framework

When performing a code review or when asked to **"Review my code"**, audit the codebase according to the specific extension type and categorize findings by severity level:

### ⚡ A. Workflow Activity Review (`IActivityHandler`)

#### 🔴 Critical (Breaking Issues & Runtime Failures)
- **Defensive `try/catch` Error Handling**: The `execute()` method MUST wrap core execution logic in a `try/catch` block and throw structured `Error` instances. Uncaught exceptions crash the workflow execution runtime.
- **Inline Dropdown Literals**: Input properties intended as dropdowns in Workflow Designer MUST use inline string literal unions (e.g. `type: 'a' | 'b' | string;`). Extracting to external type aliases breaks Designer dropdown recognition.
- **ArcGIS AMD Star Imports**: Utility/function modules (`projection`, `geometryEngine`) must use star imports (`import * as projection from "@arcgis/core/geometry/projection"`).
- **Strict Return Types**: `execute()` must return a strictly typed `Promise<TOutputs>` interface, NEVER `any` or `Promise<any>`.
- **Barrel Export**: Activity must be exported from `src/index.ts` with a name ending in `Activity`.

#### 🟡 Warnings (Execution & Resilience Deficiencies)
- **Missing `runActivity` Guard**: Activities should check `inputs.runActivity !== false` and return safe empty defaults if bypassed.
- **Missing `@required` Tags**: Mandatory input parameters must be annotated with `@required`.
- **Missing Toolbox Metadata**: The class must include `@category`, `@defaultName`, `@helpUrl`, and `@supportedApps`.
- **Blocking Operations**: Avoid synchronous blocking loops; use asynchronous helpers for I/O and heavy computations.

#### 🔵 Recommendations (Cleanliness, Maintainability & Debuggability)
- **Debug Flag (`showLogger`)**: Include optional `showLogger?: boolean` input for conditional console logging.
- **Helper Extraction**: If `main.ts` exceeds ~150 lines, split domain helpers into `utils/<domain>Helpers.ts`.
- **JSDoc Documentation**: Annotate all input and output fields with `@displayName` and `@description`.

---

### 🎨 B. Workflow Form Element Review (`FormElementProps` + `FormElementRegistration`)

#### 🔴 Critical (Breaking Issues & Architectural Failures)
- **Wiring Standard Props**: MUST destructure and wire `enabled`, `visible`, and `readOnly` to underlying components (`disabled={!enabled}`, `inputProps={{ readOnly }}`).
- **Typography System Violations**: Strict ban on raw HTML text elements (`<span>`, `<p>`, `<h1>`-`<h6>`, `<label>`). All textual content MUST use `@mui/material` `<Typography variant="...">` paired with semantic foreground tokens.
- **Color Token Violations**: Strict ban on hardcoded hex (`#ffffff`), RGB, or HSL color values. All colors MUST map to official VertiGIS CSS variable tokens (`var(--primaryBackground, #ffffff)`).
- **Missing Safe Fallbacks**: Every CSS variable token declaration MUST include a guaranteed fallback value (e.g., `var(--primaryBackground, #ffffff)`). Declarations without fallbacks cause catastrophic failures in test runners and Storybook previews.
- **File Size Ceiling Violation (Anti-God-Component)**: Any single source file exceeding **250 lines** is a critical architectural violation. Monolithic files MUST be decomposed into `components/`, `hooks/`, `tokens/`, `utils/`, and `types/`.
- **Missing Error Boundary**: Custom form elements MUST be wrapped in a `<FormElementErrorBoundary>` to prevent component rendering exceptions from crashing the host workflow runner.
- **Registration ID Match**: `FormElementRegistration.id` MUST match the Custom Type name in Workflow Designer.
- **ArcGIS AMD Star Imports**: Any ArcGIS utility/function modules used in the element MUST use star imports (`import * as projection from "@arcgis/core/geometry/projection"`).
- **Barrel Export**: Form element must be exported from `src/index.ts` with a name ending in `Registration`.

#### 🟡 Warnings (State, Modularity & Theming Deficiencies)
- **State Persistence (Tab Remounts)**: Critical workflow state MUST be saved in `props.setValue()` or `props.setProperty()` rather than local React `useState`. State stored only in `useState` is lost when navigating between form tabs.
- **Missing `tokens/` Directory**: Complex form elements must define a dedicated `tokens/` directory (`ui.ts`, `typography.ts`, `index.ts`) rather than scattering raw CSS variable strings across JSX.
- **Dynamic Theming Deficiencies**: If the element renders non-CSS graphical elements (canvas, signature pads, barcode scanners, charts), it MUST utilize `useIsDarkTheme()` or `isDarkTheme()` to dynamically adapt colors.
- **Mobile Touch Target Deficiencies**: Interactive controls (buttons, inputs, toggles, icon triggers) must maintain a minimum touch target size of 44x44px for field workers on mobile devices.
- **CSS Modules / Custom CSS**: Avoid creating `.css` or `.module.css` files. Use MUI's `sx` prop referencing CSS tokens.
- **Token Role Mismatch**: Ensure proper tokens are used according to role (e.g. `var(--secondaryForeground, #666666)` for subtitles/captions, `var(--primaryAccentHover, #005a91)` on hover states, `var(--alertRed*)` for validation errors).
- **Multiple Output Handling**: When producing secondary outputs, use `props.setProperty("propName", value)` so they are accessible via *Get Form Element Property*.

#### 🔵 Recommendations (Accessibility & Decomposition)
- **Prefer MUI Component Equivalents**: Where available, use `@mui/material` components (`<Box>`, `<Stack>`, `<Typography>`, `<Button>`, `<TextField>`) instead of bare unstyled HTML tags (`<button>`, `<input>`) to inherit VertiGIS themes and WCAG accessibility automatically.
- **Typography Hierarchy & Outdoor Readability**: Adhere strictly to the Typography variant hierarchy (`h6` for form headers, `subtitle1`/`subtitle2` for group headers, `body1`/`body2` for labels/content, `caption`/`overline` for validation hints/badges). Ensure at least 14px text size (`body2`) for sunlight readability on mobile devices.
- **Component File Size Target**: Strive for less than **150 lines** per file.
- **WCAG Accessibility (a11y)**: Add `aria-label`, `aria-pressed`, and keyboard event handlers (`onKeyDown` for Space/Enter keys) on interactive components. Ensure WCAG AA contrast (4.5:1 text, 3:1 graphical elements).
- **Structured Custom Events**: Dispatch custom events using structured payloads: `props.raiseEvent("custom", { customEventType: "eventName", data: ... })`.

---

## 3. HTTPS Certificate Generation (OpenSSL)

Workflow SDK local development server runs on HTTPS (`https://localhost:5000/activitypack.json`).

### Option A — Generate Self-Signed Certificate via OpenSSL
```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"
```

### Option B — Custom Certificate Path
Configure `package.json`:
```json
{
  "scripts": {
    "start": "vertigis-workflow-sdk start --https --key ./certs/key.pem --cert ./certs/cert.pem"
  }
}
```

---

## 4. Helper Scripts Templates

### `initiate_agents_md.py` (Automated `AGENTS.md` Directives Injection)

The `initiate` command configures or updates the target repository's `AGENTS.md` with official VertiGIS Studio Workflow SDK directives. It wraps directives inside scoped comment markers (`<!-- vertigis-workflow-sdk:start -->` and `<!-- vertigis-workflow-sdk:end -->`), preserving any existing rules or instructions in the target file.

#### Usage
```bash
# Run in current repository directory
python3 vertigis-workflow-sdk-skill/scripts/initiate_agents_md.py

# Specify custom target directory
python3 vertigis-workflow-sdk-skill/scripts/initiate_agents_md.py --target-dir /path/to/my-workflow-project

# Force update an existing VertiGIS directives block
python3 vertigis-workflow-sdk-skill/scripts/initiate_agents_md.py --target-dir /path/to/my-workflow-project --force
```

#### Injected Directive Template
```markdown
<!-- vertigis-workflow-sdk:start -->
# VertiGIS Studio Workflow SDK Development Directives

> **Mandatory Agent Directive**: Whenever you make any change to or create any custom workflow activity or custom form element (Web or Mobile) in this repository, ALWAYS check and verify it against VertiGIS Workflow SDK standards (standard props wiring `enabled`/`visible`/`readOnly`, MobX/React patterns, MUI components with sx tokens, zero hardcoded colors, design token architecture, safe fallbacks, dual-theme adaptation, strict 150–250 line component modularity, state persistence in `setValue`/`setProperty`, and ErrorBoundary wrappers).

## 1. Typography System
- **Strict ban on raw HTML text elements**: Never use raw `<span>`, `<p>`, `<h1>`-`<h6>`, or `<label>` tags.
- **MUI Typography Component**: Always use `@mui/material` `<Typography variant="...">`:
  - `h6`: Form header, section titles, and top-level card titles.
  - `subtitle1`, `subtitle2`: Fieldset headings, group labels, and subheadings.
  - `body1`, `body2`: Standard form labels, values, instructions, and descriptions.
  - `caption`, `overline`: Helper microcopy, field validation hints, units, and timestamps.
- **Semantic Text Color Tokens**: Always pair Typography variants with semantic foreground tokens via `sx`:
  - Primary text: `color: "var(--primaryForeground, #212121)"`
  - Secondary / muted text: `color: "var(--secondaryForeground, #666666)"`
  - Inactive / disabled text: `color: "var(--disabledForeground, #9e9e9e)"`
  - Validation error text: `color: "var(--alertRedForeground, #d32f2f)"`
- **Font Family**: Use `fontFamily: "var(--defaultFont, sans-serif)"` (inherited automatically via MUI theme).
- **Mobile & Field Form Readability**: Ensure minimum text sizing (at least 14px / `body2` on mobile screens) and comfortable line-height for readability in high-glare outdoor environments.

## 2. Color & Design Tokens Subsystem
- **Zero Hardcoded Colors**: Strict ban on hardcoded hex (`#ffffff`), RGB (`rgb(...)`), or HSL color values for UI chrome, backgrounds, text, and borders.
- **Safe Fallback Requirement**: ALWAYS provide safe fallbacks for CSS variable tokens (e.g., `var(--primaryBackground, #ffffff)`) to ensure resilient rendering in headless, disconnected, or preview environments.
- **Standardized Token Architecture**: Group all tokens under a `tokens/` directory:
  - `tokens/ui.ts`: Surface, border, foreground, accent, interactive, status, and touch tokens.
  - `tokens/typography.ts`: Typography hierarchy, font families, and weights.
  - `tokens/index.ts`: Central barrel export and `color-mix()` dynamic tinting utilities.
- **Dynamic Dual-Theme Adaptation**:
  - Use `color-mix(in srgb, ...)` for derived tints, hover states, muted borders, and transparent overlays to adapt automatically to light and dark themes without manual CSS overrides.
  - Use the canonical reactive `useIsDarkTheme()` hook for DOM/shell theme detection.
  - Use `isDarkTheme()` standalone utility for non-CSS contexts (Plotly, canvas renderers, signature pads, barcode viewfinders, PDF exports).
- **MUI Theme Integration**: Apply `createTheme` overrides and `ThemeProvider` to align composite controls (sliders, toggle buttons, pickers) with VertiGIS shell branding.
- **GIS Visual Hierarchy**: Keep UI chrome neutral and subdued so the GIS map and form content remain legible. Ensure WCAG AA contrast compliance (minimum 4.5:1 for normal text, 3:1 for large text).

## 3. Strict Component Modularity & Anti-God-Component Architecture
- **Strict File Size Thresholds**: Max 150–250 lines per file. Any file exceeding 250 lines MUST be refactored and decomposed.
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
  - `enabled`: Map `!enabled` to `disabled` styling with `color: "var(--disabledForeground, #9e9e9e)"`.
  - `readOnly`: Display with a subtle non-editable background distinctly different from disabled (`readOnly` remains legible and selectable).
  - Validation errors: Display error borders and messages using `var(--alertRedForeground, #d32f2f)`.

## 5. Architecture & State Persistence
- **State Persistence (Surviving Tab Remounts)**: Form element state MUST be saved via `props.setValue()` or `props.setProperty()`. NEVER rely on ephemeral local React `useState` for critical business data, as form elements unmount and remount when users navigate between form tabs or workflow steps.
- **Defensive Activities**: Workflow Activities MUST wrap core execution logic in `try/catch` blocks and throw structured `Error` objects so the workflow engine can handle failures gracefully.
<!-- vertigis-workflow-sdk:end -->
```

---

### `start.bat` (Windows Port 5000 Killer & Starter)
```cmd
@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   VertiGIS Studio Workflow SDK Development Server
echo ========================================================

set PORT=5000

echo Checking for stale processes on port %PORT%...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    echo Terminating PID %%a on port %PORT%...
    taskkill /F /PID %%a >nul 2>&1
)

echo Starting Workflow SDK development server (npm start)...
npm start
```

---

### `build.bat` (Windows Production Bundle Generator)
```cmd
@echo off
setlocal

echo ========================================================
echo   VertiGIS Studio Workflow SDK Production Build
echo ========================================================

echo Running production compilation (npm run build)...
call npm run build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed with exit code %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Production activity pack generated successfully in dist/
```
