# VertiGIS Studio Web SDK: Interactive Scaffolding, Code Reviews & Tooling

## Overview
When interacting with a developer, the agent follows an interactive consultation protocol ("Grill-Me" mode) to discover project requirements, verify SSL certificates, and audit existing code with categorized severity levels.

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
        D2[Configure AGENTS.md Directives ('initiate')]
        D3[Add New Component / Service]
        D4[Generate Tooling Scripts]
    end

    subgraph E [Grill-Me Discovery]
        E1[Target Component vs Service]
        E2[Name & Custom Namespace]
        E3[HTTPS SSL Strategy]
        E4[Scaffold Project, AGENTS.md & Scripts]
    end
```

---

## 2. Categorized Code Review Audit Framework

When performing a code review or when asked to **"Review my code"**, audit the codebase according to the specific extension type and categorize findings by severity level:

### 🧩 A. Web Component Review (`ComponentModelBase` + React View)

#### 🔴 Critical (Breaking Issues & Runtime Failures)
- **Monolithic God-Component Violation (> 250 Lines)**: Any component file (`*.tsx`, `*Model.ts`, etc.) exceeding 250 lines violates enterprise modularity standards. Monolithic files break reactivity boundaries, hinder testing, and create unmaintainable code. Decompose the file immediately into `components/`, `hooks/`, and `utils/`.
- **`<LayoutElement>` Wrapper**: React view MUST wrap all JSX inside `<LayoutElement {...props}>`. Omitting this breaks SDK layout slotting, sizing, and Designer drag-and-drop.
- **MobX `observer()`**: React view MUST be wrapped with `observer()` from `mobx-react-lite` if reading model properties. Without it, model observable changes will not trigger re-renders.
- **Designer Integration & Settings Schema Protocol**: Props interface MUST extend `LayoutElementProperties<TModel>`, AND when configurable properties are exposed in Designer, the component manifest MUST implement the Designer Settings Schema Protocol (`getLayoutDesignerSettingsSchema`, `getLayoutDesignerSettings`, and `applyLayoutDesignerSettings`) with live `model.updateConfig(...)` synchronization.
- **Typography System Violations (Ban on Raw HTML Text)**: NEVER use raw HTML text tags (`<span>`, `<p>`, `<h1>`-`<h6>`, `<strong>`, `<em>`). All text MUST use `@mui/material` `<Typography variant="...">` paired with semantic foreground tokens (`var(--primaryForeground, #1e1e1e)`, `var(--secondaryForeground, #666666)`). Raw text tags fail theme adaptation and break typography consistency.
- **Color Token Violations (Ban on Hardcoded Colors)**: NEVER use hardcoded hex (`#ffffff`, `#hex`), RGB (`rgb(...)`), or HSL (`hsl(...)`) colors for UI chrome, backgrounds, text, and borders in JSX, inline styles, or MUI `sx` props. All styling must map to VertiGIS CSS variable tokens with safe fallbacks (`var(--primaryBackground, #ffffff)`, `var(--primaryBorder, #e0e0e0)`, `var(--primaryAccent, #007ac2)`). Hardcoded colors break in dark mode, fail WCAG contrast requirements, and cause theme crashes.
- **ArcGIS AMD Star Imports**: Utility/function modules (`projection`, `geometryEngine`) must use star imports (`import * as projection from "@arcgis/core/geometry/projection"`). Default imports cause `Unsupported AMD module` errors.
- **Host Peer Dependencies**: NEVER bundle duplicate copies of `@vertigis/web`, `@arcgis/core`, `react`, or `@mui/material`.

#### 🟡 Warnings (Architectural & State Deficiencies)
- **File Size Warning (150–250 lines)**: Files between 150 and 250 lines are approaching the god-component ceiling. Proactively decompose presentational sub-views and extract hooks to prevent breaching the 250-line hard limit.
- **Unorganized Component Structure**: Flag components that do not follow the standard 7-directory blueprint (`components/`, `hooks/`, `services/`, `utils/`, `helpers/`, `tokens/`, `types/`). Monolithic flat folders lead to architecture drift.
- **Missing Tokens Architecture**: Flag custom components defining inline or component-level styling without a dedicated `tokens/` directory (`tokens/ui.ts`, `tokens/typography.ts`, `tokens/index.ts`).
- **Missing CSS Token Fallbacks**: Flag any CSS variable token used without a default fallback value (e.g., `var(--primaryBackground)` instead of `var(--primaryBackground, #ffffff)`). Missing fallbacks cause blank/transparent rendering in isolated unit tests, Storybook sandboxes, and during initial shell boot.
- **Theme Adaptation Violations**: Flag manual CSS theme class toggling (e.g. `.dark-mode` overrides) instead of modern `color-mix(in srgb, ...)`. Flag missing `useIsDarkTheme()` hook or lack of `isDarkTheme()` utility when integrating non-CSS rendering engines (Plotly charts, HTML Canvas, WebGL, or PDF exports).
- **Missing Error Boundary**: Custom widget contents should be wrapped in an `<ErrorBoundary>` to prevent a single component crash from breaking the entire application layout.
- **CSS Modules / Custom CSS**: Avoid creating `.css` or `.module.css` files. Use MUI's `sx` prop referencing CSS tokens and `color-mix()` helpers.
- **Token Role Mismatch**: Ensure proper tokens are used according to role (e.g. `var(--secondaryForeground, #666666)` for subtitles/captions, `var(--primaryAccentHover, #005a91)` on hover states, `var(--primaryBorder, #e0e0e0)` on card outlines).
- **Resource Leaks in Lifecycle**: Any event subscriptions, background intervals, or MobX reactions created in `_onInitialize()` MUST be disposed in `_onDestroy()`.
- **Complex `@serializable` Types**: Non-primitive properties (like `Date` or custom classes) in `@serializable` must have explicit `{ serializer, deserializer }` definitions.

#### 🔵 Recommendations (Cleanliness, Maintainability & a11y)
- **Component Decomposition & Extraction Heuristics**:
  - Extract sub-views to `components/` when JSX nesting exceeds 3 levels or discrete visual cards/sections emerge.
  - Extract state, timers, DOM event listeners, and MobX reactions to `hooks/`.
  - Extract calculations, data transformations, geometry helpers, and pure algorithms into zero-dependency `utils/`.
- **Prefer MUI Component Equivalents**: Where available, use `@mui/material` components (`<Box>`, `<Stack>`, `<Typography>`, `<Button>`, `<TextField>`) instead of bare unstyled HTML tags (`<button>`, `<input>`) to inherit VertiGIS themes and WCAG accessibility automatically. Plain structural `<div>` containers for layout/refs are acceptable.
- **Typography Hierarchy**: Adhere strictly to the Typography variant hierarchy (`h5`/`h6` for widget titles, `subtitle1`/`subtitle2` for section headers, `body1`/`body2` for content, `caption`/`overline` for microcopy/badges).
- **Accessibility (a11y)**: Interactive MUI elements (`IconButton`, `Button`, `TextField`) should include `aria-label` or `aria-labelledby`.
- **JSDoc Documentation**: Decorate model and props interface properties with `@displayName` and `@description`.


---

### ⚙️ B. Web Service Review (`ServiceBase` Singletons)

#### 🔴 Critical (Breaking Issues & Runtime Failures)
- **Registration**: Service must be registered in `src/index.ts` via `registry.registerService({ id, getService })`.
- **Unique Service ID**: Service identifier must not collide with core VertiGIS service IDs.

#### 🟡 Warnings (Architectural & State Deficiencies)
- **Memory Management**: Timers, polling loops, or event bus subscriptions must be cleared in `_onDestroy()`.
- **Decoupled Messaging**: Prefer invoking commands and operations via `this.messages.commands` / `this.messages.operations` over hard-coding direct references to other models.

#### 🔵 Recommendations (Cleanliness & Maintainability)
- **Dependency Injection**: Use `@inject("serviceName")` with strict interface typing when consuming other services.
- **Helper Extraction**: Move heavy calculation or domain logic into `utils/<domain>Helpers.ts`.

---

## 3. HTTPS Certificate Generation (OpenSSL)

VertiGIS Studio Web development requires running the local dev server over HTTPS (port 3000).

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
    "start": "vertigis-web-sdk start --https --key ./certs/key.pem --cert ./certs/cert.pem"
  }
}
```

---

## 4. Helper Scripts Templates

### `start.bat` (Windows Port 3000 Killer & Starter)
```cmd
@echo off
set PORT=3000
echo Checking if port %PORT% is in use...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%PORT%') do (
    echo Killing stale process on port %PORT% (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
)
echo Starting VertiGIS Web SDK development server...
npm start
```

### `build.bat` (Windows Build Script)
```cmd
@echo off
echo Building production VertiGIS Web SDK library bundle...
npm run build
if %ERRORLEVEL% EQU 0 (
    echo Build completed successfully in dist/ directory.
) else (
    echo Build failed with error code %ERRORLEVEL%.
)
```

### `start.sh` (Linux / macOS Port 3000 Killer & Starter)
```bash
#!/bin/bash
PORT=3000
echo "Checking if port $PORT is in use..."
PID=$(lsof -ti :$PORT)
if [ ! -z "$PID" ]; then
    echo "Killing stale process on port $PORT (PID: $PID)..."
    kill -9 $PID 2>/dev/null
fi
echo "Starting VertiGIS Web SDK development server..."
npm start
```

### `build.sh` (Linux / macOS Build Script)
```bash
#!/bin/bash
echo "Building production VertiGIS Web SDK library bundle..."
npm run build
```

---

### `initiate_agents_md.py` (Automated `AGENTS.md` Directives Injection)

The `initiate` command configures or updates the target repository's `AGENTS.md` with official VertiGIS Studio Web SDK directives. It wraps directives inside scoped comment markers (`<!-- vertigis-web-sdk:start -->` and `<!-- vertigis-web-sdk:end -->`), preserving any existing rules or instructions in the target file.

#### Usage
```bash
# Run in current repository directory
python3 vertigis-web-sdk-skill/scripts/initiate_agents_md.py

# Specify custom target directory
python3 vertigis-web-sdk-skill/scripts/initiate_agents_md.py --target-dir /path/to/my-web-extension

# Force update an existing VertiGIS directives block
python3 vertigis-web-sdk-skill/scripts/initiate_agents_md.py --target-dir /path/to/my-web-extension --force
```

#### Injected Directive Template
```markdown
<!-- vertigis-web-sdk:start -->
# VertiGIS Studio Web SDK Development Directives

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
- **Persisting Changes (`applyLayoutDesignerSettings`)**: Write updated attributes back to `args.node.attributes.set(...)` and propagate configuration changes to the live model via `model.updateConfig(...)`.
<!-- vertigis-web-sdk:end -->
```
