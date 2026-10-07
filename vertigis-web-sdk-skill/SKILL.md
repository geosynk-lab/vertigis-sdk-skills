---
name: vertigis-web-sdk-skill
description: >-
  Comprehensive guide and reference for developing custom components, services,
  commands, operations, layouts, and workflows using the VertiGIS Studio Web SDK
  and ArcGIS API for JavaScript. Use this skill whenever building or reviewing VertiGIS
  Studio Web (VSW) libraries, React component models and views, MobX state,
  LayoutElement wrappers, design tokens, dynamic light/dark theming, or when running
  "initiate", setting up AGENTS.md, or initializing VertiGIS project rules.
---

# VertiGIS Studio Web SDK Skill

## 1. Role
You are an expert GIS Developer and Enterprise React Architect specializing in the VertiGIS Studio Web SDK. 

## 2. Objective
Generate flawless, production-ready, enterprise-grade code for VertiGIS Studio Web (VSW) extensions. You build custom components (Models/Views), services, commands, and operations that perfectly align with VertiGIS SDK architecture, React best practices, and WCAG accessibility standards.

## 3. Rules (CRITICAL AGENT DIRECTIVES)
You MUST adhere to the following rules without exception:

1. **Typography System & Shell Inheritance**:
   - **Banned Imports from `@vertigis/web/ui`**: Strict ban on importing UI controls (`Button`, `Typography`, `DynamicIcon`, `Box`, `TitleBar`, etc.) from `@vertigis/web/ui`. These internal shell components depend on `useUIContext()`, which is undefined in unit tests (`vitest run`), detached React portals, or custom modals, causing fatal `TypeError: Cannot read properties of undefined (reading 'translate')` crashes. Reserve `@vertigis/web/ui` strictly for non-UI SDK hooks when needed (e.g. `useWatchAndRerender`).
   - **Typography Components & Semantic Palette Props**: Prefer `@mui/material` `<Typography variant="...">` (`h5`/`h6` for titles, `subtitle1`/`subtitle2` for headers, `body1`/`body2` for reading text, `caption`/`overline` for metadata/badges). Primary text has no `color` prop: it inherits the host foreground (`color="text.primary"` is redundant and is flagged). Use `color="text.secondary"` (captions/helpers/microcopy), `color="inherit"` (inside a coloured surface that sets its own foreground), and `color="error"` (validation). NEVER write bespoke CSS text classes or inline `sx={{ color: ... }}` solely to set secondary/helper text colors.
   - **Zero `font-family` (No Exceptions)**: The host application shell (`.vsw-app`) strictly owns and injects the global font stack. **NEVER declare `font-family`, the `font:` shorthand, or `fontFamily` anywhere**: CSS, `sx`, `style`, token files (no font-stack tokens, including `var(--codeFont)`/monospace stacks). The single allowed line is `typography: { fontFamily: "inherit" }` in the `createTheme` theme provider (or a Tier 3 chart library theme such as Nivo): MUI and chart libraries otherwise apply their own default font (Roboto / sans-serif) instead of the host font.
   - **Top-Level Package Exports Only**: Always import directly from package roots (`import { Box, Typography, Dialog } from "@mui/material"`; `import { createTheme, ThemeProvider } from "@mui/material/styles"`). Deep imports (e.g. `@mui/material/styles/createTheme`, `@mui/material/Box`) are deprecated in MUI v7 and break under modern bundlers. Import style-dictionary types from the root too (`import type { SxProps, Theme } from "@mui/material"`); `@mui/material/styles` triggers the SDK `no-restricted-imports` lint warning, so reserve it for the theme provider file.
   - **No Theme-Level Typography Colour**: NEVER set `color` inside `components.MuiTypography.styleOverrides` in `createTheme`. It overrides every `<Typography color="...">` prop and silently disables semantic palette props.
2. **Two-Tier Styling Architecture (VertiGisThemeProvider for MUI & Direct Token Consumption for Non-MUI)**:
   - **Tier 1 (MUI Controls: Radio, Checkbox, Button, Typography, Dialog, Switch, Form Controls)**: Standard MUI controls MUST be wrapped in a shared `VertiGisThemeProvider` (or scoped dialog/modal wrapper) driven by `useIsDarkTheme()`, setting `palette: { mode: isDark ? "dark" : "light" }` with Meridian compact defaults and dynamic brand checked overrides.
     - **Shell Token Theme Detection Precedence**: Determine the active theme from explicit `.vsw-app` class/data markers first, then infer luminance from the computed `--primaryBackground` shell token, then from the computed root background. Use `(prefers-color-scheme: dark)` only as the final fallback. The operating-system preference must never override an already-rendered VertiGIS shell theme.
     - **MUI Portal Containment**: Configure `MuiPopover.defaultProps.container` with a function that returns `.vsw-app` (falling back to `document.body`). Menus, selects, and popovers must mount inside the shell so they inherit host tokens and remain in the same stacking/theme context. Do not force menu text or surface colours with `!important`; use MUI semantic palette states (`text.primary`, `action.hover`, `action.selected`).
     - **Inheritance-First / Zero Color Injection Rule for MUI**: Never micro-inject CSS classes (`.MuiRadio-root`, `.MuiCheckbox-root`, `.MuiTypography-root`, etc.) or inline `sx` color overrides to force theme colors onto standard MUI controls. MUI handles light/dark states, hover, focus rings, disabled opacity, and text contrast natively via the theme provider. Only customize via CSS or `sx` if a control intentionally requires non-standard visual divergence.
     - **Strict Ban on `<CssBaseline />`**: NEVER mount `<CssBaseline />` under `VertiGisThemeProvider` or anywhere in extensions. Custom libraries are guest widgets running inside `.vsw-app`. `<CssBaseline />` injects global CSS resets (`html`, `body`, scrollbars, box-sizing) that clobber the host application shell, corrupt Esri map canvas viewports, and reset host layout rules.
     - **MUI v7 `slotProps` Standardization**: Standardize on `slotProps` for composite controls. Legacy nested props (`PaperProps`, `InputProps`, `BackdropProps`) are deprecated. For example, use `<Dialog slotProps={{ paper: { className: "..." } }}>` and `<TextField slotProps={{ input: { readOnly } }}>`. In modals, use `onClose` instead of deprecated `onBackdropClick`.
     - **Type-Safe Style Dictionaries (`Record<string, SxProps<Theme>>`)**: When custom MUI styles are genuinely necessary beyond theme defaults, do not scatter verbose inline `sx={{ ... }}` objects across markup. Define type-safe dictionaries at the top of the file: `const styles: Record<string, SxProps<Theme>> = { ... }` (or `ComponentName.styles.ts` for files >= 100 lines).
     - **The `augmentColor` Crash Prevention**: Passing raw `var(...)` strings (including any `UI_TOKENS.*` value) into `palette.primary.main` or `palette.error.main` crashes MUI (`Error: MUI: Unsupported var(...) color`). All CSS variable integrations MUST be attached via component `styleOverrides` (e.g. `MuiRadio: { styleOverrides: { root: { "&.Mui-checked": { color: "var(--primaryAccent, #007ac2)" } } } }`), NEVER in `palette.*.main`. The same error is thrown when a token is passed to MUI colour math: `alpha()`, `darken()`, `lighten()`, `emphasize()`, `getContrastRatio()`, `theme.palette.augmentColor()`, and the `color` prop of `<Link>` (which calls `alpha()` for the underline). Use `alphaMix()` / `color-mix(in srgb, ...)` instead of `alpha()`, and `sx={{ color: token }}` instead of `<Link color={token}>`.
   - **Tier 2 (Non-MUI Chrome & Custom Layout Containers)**: Plain HTML elements (`div`, `header`, `aside`, card borders, dividers, split containers) are styled in co-located namespaced CSS (`ComponentName.css`) consuming official host CSS design tokens with safe fallbacks (`var(--primaryBorder, #e0e0e0)`, `var(--secondaryBackground, #ebebeb)` for a nested card).
   - **Inherit, Don't Restate (Minimal CSS Injection)**: Widgets render inside the host panel, which already supplies text colour, background and font. NEVER restate them: no `color: var(--primaryForeground)`, no `background: var(--primaryBackground)` (a transparent element already shows the panel), no `<Typography color="text.primary">`, and no wrapper element whose only job is to set colours for its children. Set a colour token ONLY where the element deliberately differs from its parent (status banner, accent badge, nested card). Exceptions: opaque layers that cover other content (`position: sticky|fixed|absolute` or `z-index`), the `createTheme` provider, and content rendered outside the shell (portals), which must carry a `vertigis-rule-disable REDUNDANT_INHERITED_TOKEN -- <reason>` comment.
   - **Token Pairing & Contrast (Validated)**: When an element sets a background, it MUST set the foreground from the same pair in the same CSS rule or `sx` object: `XBackground` with `XForeground` (e.g. `--alertRedBackground` with `--alertRedForeground`), accent fills (`--primaryAccent`) with `--emphasizedButtonForeground`. Text on panel surfaces (`--primaryBackground`, `--secondaryBackground`, `--primaryAccentLight`, item hover/selected) uses only `--primaryForeground` (inherited), `--secondaryForeground`, `--primaryAccent`, `--errorHelperTextForeground` or a disabled token. NEVER use a `*Foreground` token as a background or a `*Background` token as text (the inverse pair `--primaryForeground` / `--primaryBackground` is the only exception). Text must reach WCAG AA 4.5:1 against its background, computed from the `src/tokens/ui.ts` fallbacks (disabled text exempt). The host regenerates each pair together for dark themes, so pairing protects dark mode where fallback-based contrast cannot. The validator enforces `REDUNDANT_INHERITED_TOKEN`, `TOKEN_PAIRING` and `TOKEN_CONTRAST`.
   - **Zero Hardcoded Colours**: NEVER write hex (`#ffffff`), `rgb()`/`rgba()`, or `hsl()`/`hsla()` colour literals in CSS, TS, or TSX, including `createTheme` palettes. The only places a colour literal may appear are `src/tokens/` and the fallback slot of `var(--token, <fallback>)`.
   - **Tier 3 (Non-CSS Renderers: Nivo/Plotly Charts, HTML5 Canvas, jsPDF)**: Standalone renderers consume tokens programmatically via JavaScript constants from `src/tokens/` (`UI_TOKENS`, chart token maps such as `CHART_TOKENS`) + `useIsDarkTheme()` / `isDarkTheme()`.
   - **Shape Tokens & Border Radius**: NEVER hardcode pixel corner radii (e.g. `border-radius: 4px;`) in CSS or components. Always reference unified shape tokens: `var(--borderRadius, 4px)` (standard), `var(--borderRadiusSm, 2px)` (micro), `var(--borderRadiusLarge, 8px)` / `var(--borderRadiusLg, 8px)` (cards/dialogs), and `50%` / `9999px` (pills/rounds).
   - **Spacing Tokens (Validated)**: NEVER write literal lengths for `margin*`, `padding*` or `gap` / `row-gap` / `column-gap` in CSS files (e.g. `padding: 12px;`, `margin-bottom: 1rem;`). Use spacing tokens with fallbacks: `var(--spacingXxs, 2px)`, `var(--spacingXs, 4px)`, `var(--spacingSm, 8px)`, `var(--spacingMd, 12px)`, `var(--spacingLg, 16px)`, `var(--spacingXl, 24px)` (`UI_TOKENS.spacing.*` in TS). Only `0`, `auto` and keywords may be written literally; `calc()` over tokens is allowed. The validator enforces `HARDCODED_SPACING`.
   - **Host-Owned Branding Principle**: The host application shell (`.vsw-app`) strictly owns and manages all branding and themes via CSS custom properties configured in `app-config.json` / Designer. Components must NEVER create independent brands or redefine app branding.
   - **Strict Ban on Token Re-Aliasing & Intermediate Indirection**: NEVER invent intermediate alias variables or custom color indirection layers (e.g., `--color-background: var(--primaryBackground)`, `--monitoring-bg: var(--color-background)`, `--monitoring-text: var(--primaryForeground)`). Components MUST directly consume official VertiGIS host CSS tokens with safe fallbacks (e.g., `var(--primaryBackground, #ffffff)`, `var(--primaryForeground, #212121)`, `var(--primaryBorder, #e0e0e0)`). Creating shadow token systems introduces multi-hop indirection, breaks DevTools inspectability, causes team confusion, and fragments the design system.
3. **Co-Located Component CSS & Minimal Style Injection**:
   - **Co-Located CSS Pattern**: Pair every component view (`ComponentName.tsx`) with a co-located CSS file (`ComponentName.css`), following the official `@vertigis/web-sdk` starter template architecture (`PointsOfInterest.css`). This applies to every `.tsx` that returns JSX, with no size exception; an empty `ComponentName.css` is allowed. The validator enforces `COMPONENT_CSS_PAIR`.
   - **Strict Ban on Global `:root` Injection**: NEVER declare `:root { ... }` rules in component CSS. Custom libraries are guest extensions running inside the host shell (`.vsw-app`). Declaring `:root` in library CSS pollutes the global document scope, risks overriding host variables, and leaks across unrelated widgets. If component-scoped CSS variables are needed for layout math (e.g. `--row-height: 36px`), declare them strictly on the namespaced component selector (e.g. `.ListHeader { --row-height: 36px; }`), never on `:root`, and never for color re-aliasing.
   - **Strict Class Namespacing (Host Shell Safety)**: Because the SDK Webpack pipeline compiles CSS via `style-loader` without CSS Modules hashing, all classes in `*.css` are injected globally into the host `<head>`. All classes MUST be strictly namespaced with the component name or BEM (e.g. `.ListHeader`, `.ListHeader-title` or `.list-header__title`). Strictly BANNED: generic classes like `.header`, `.title`, `.item`, `.button`, `.card`, `.active`.
   - **Minimal Style Injection & Style Hierarchy**: (1) Co-located `ComponentName.css` for static layouts, cards, hover states, and structural chrome (using `var(--borderRadius, 4px)` and zero redundant `font-family`). (2) Native `style={{ ... }}` ONLY for purely dynamic runtime calculations (e.g. calculated widths or coordinates). (3) Strict ban on scattering loose, repetitive `sx={{ ... }}` objects across markup. Rely on parent inheritance and tokens.
   - **One Styling Method Per Element**: NEVER combine `className` with a static `style={{ ... }}` on the same element. Inline styles silently win over the CSS rule and block its hover/focus states. When migrating such an element, move the value that was actually rendered (the inline one) into the CSS, not the shadowed CSS value.
   - **Zero Dead or Shared CSS**: Every class in a `*.css` file MUST be referenced in source (no orphan classes), and a top-level class MUST be defined in exactly one CSS file. Every `animation:` name MUST have a matching `@keyframes` in the same bundle. Shared MUI style dictionaries used by several components live in one `*Styles.ts` file, not copied per component.
   - **`!important` Only for Host Overrides**: The only accepted `!important` is `display: none !important` hiding a closed widget against host-shell inline display styles. Never use it to fight MUI or your own CSS.
   - **Canonical Token Fallbacks & Token Roles**: Every `var(--token, #fallback)` MUST use the same fallback as `src/tokens/ui.ts` (fallback drift renders different colours in tests and before shell boot). Outside `src/tokens/`, consume colours through `UI_TOKENS` in TS/TSX or through co-located CSS, never as raw `var(...)` string literals. Respect token roles: pale `--alert*Background` tokens are tints, never strong fills behind white text; chart series derive from foreground/accent tokens (`--primaryAccent`, `--alertGreenForeground`, `--alertRedForeground`), not border tokens.
4. **Strict Component Modularity & Anti-God-Component Architecture**: NEVER write massive monolithic "god components". Adhere to strict file size thresholds (target max 150 lines, hard ceiling of 250 lines per file; any file > 250 lines MUST be refactored). Decompose complex components using the standard 7-directory blueprint: `components/` (stateless, presentational sub-views), `hooks/` (custom React hooks for state, timers, and event subscriptions), `services/` (component-level services), `utils/` and `helpers/` (pure functions and zero-dependency helpers), `tokens/` (design tokens and theme mappings), and `types/` (interfaces and serialization models). Maintain strict separation between MobX Component Models (`*Model.ts` managing state, observables, and lifecycle hooks `_onInitialize()` / `_onDestroy()` without JSX or DOM elements) and React Views (`*.tsx` handling layout rendering, `observer()`, and `<ErrorBoundary>`). Any file containing JSX MUST use the `.tsx` extension; JSX in a `.ts` file is banned (`JSX_IN_TS`). Apply extraction heuristics: decompose when JSX nesting exceeds 3 levels, extract subscriptions/listeners to hooks, and isolate pure data algorithms to utils.
5. **Exposing Properties to Designer (Settings Schema Protocol & Attribute Lifecycle)**: To expose configurable parameters to VertiGIS Studio Web Designer, the component's React props MUST extend `LayoutElementProperties<TModel>`, AND the component manifest in `registry.registerComponent` MUST implement the **Designer Settings Schema Protocol**:
   - **Safe Trimming & Explicit Attribute Deletion**: When persisting settings in `applyLayoutDesignerSettings`, NEVER write empty strings (`node.attributes.set(key, "")`). Writing empty strings creates sticky XML attributes that resurrect default values on reload. Always trim string inputs (`safeTrim`); if a value is present, call `node.attributes.set(kebabKey, val)`; if empty or cleared, call `node.attributes.delete(kebabKey)`.
   - **Three-Way Casing Synchronization**: XML attributes in `layout.xml` are strictly **kebab-case** (`telemetry-layout-id`, `layout-id`). Component model properties and React props are **camelCase** (`telemetryLayoutId`, `layoutId`). The component props (`LayoutElementProperties`) MUST declare BOTH kebab-case and camelCase forms, and `getLayoutDesignerSettings` must inspect both (`attr("telemetry-layout-id") ?? attr("telemetryLayoutId")`).
   - **Lifecycle Initialization from XML Node**: In `_onInitialize()`, component models must read `(this as any).node?.attributes` to guarantee that attributes declared in `layout.xml` are loaded immediately on startup even before the designer inspector is opened.
6. **LayoutElement Wrapper & Host Layout Shell Hierarchy**:
   - Every component view MUST wrap its content inside `<LayoutElement {...props}>` (imported from `@vertigis/web/components`) for layout slotting and Designer support.
   - **Strict Ban on Hiding via `props.active === false`**: Never return `<LayoutElement style={{ display: "none" }} />` or an empty placeholder when `props.active === false`. In `<tab-container>` and `<tabs>`, background tabs receive `active="false"`. Hiding the component makes the tab panel render blank white when selected by the user. Let the host tab container manage DOM visibility.
   - **Panels vs Bare Split Components**: Inside a `<panel>`, manage activation/closing via `ui.activate` and `ui.deactivate` targeting the **panel's layout ID**. When bare inside a `<split>`, manage visibility internally and invoke `ui.activate`/`ui.deactivate` on the **component ID**.
   - **Dialogs & Full-Height Stretches**: Custom dialog views MUST use `<LayoutElement {...props} stretch style={{ height: "100%", width: "100%", display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>`. STRICT BAN on injecting `<GlobalStyles>` targeting `div[role="dialog"]` or overriding host `.MuiDialogContent-root` with `!important`. Dialog dimensions are controlled declaratively in `app.json` or `layout.xml`.
7. **MobX Observer**: Every React component that reads model properties MUST be wrapped with `observer()` from `mobx-react-lite`.
8. **ArcGIS Import Rules**: Use default imports for class modules (`import Graphic from "@arcgis/core/Graphic"`). Use star imports for utility/function modules to avoid AMD errors (`import * as projection from "@arcgis/core/geometry/projection"`).
9. **Enterprise Reliability & Theme Safety**: Wrap custom React widgets in `ErrorBoundary` components to prevent layout crashes. All subscriptions, intervals, and MobX reactions initialized in `_onInitialize()` MUST be cleanly disposed in `_onDestroy()`. Wrap Workflow Activity `execute` blocks in `try/catch` and throw structured errors. Add `aria-label` to interactive MUI components. Ensure theme safety across dynamic light/dark switches.
10. **Lifecycle Contract & Reserved Property Protection (`_handles` Safety)**: Subclasses of `ComponentModelBase` and `ModelBase` MUST strictly adhere to the symmetric lifecycle contract: (1) In `_onInitialize()`, ALWAYS invoke `await super._onInitialize()` **first** before initializing component-specific resources, subscriptions, or layers. (2) In `_onDestroy()`, ALWAYS clean up component-specific resources, subscriptions, event listeners, sketch view models, and map graphics **first**, and invoke `await super._onDestroy()` **last** (symmetric teardown). (3) **Strict ban on declaring a custom `_handles` field**: Ancestor `InitializableBase` incorporates `HandlesMixin` (`@vertigis/arcgis-extensions/support/HandlesMixin.js`), which instantiates `this._handles` as an `@arcgis/core/core/Handles` instance and calls `this._handles.destroy()` on disposal. Under ES2022+ class field semantics (`useDefineForClassFields: true`), declaring a custom field named `_handles` (e.g., `private _handles: any[] = []`) silently overwrites the parent's `Handles` instance with a plain Array. When VertiGIS Studio Web Designer tears down models during app deployment or publishing packaging, `model.destroy()` triggers `super.destroy()`, crashing with `TypeError: this._handles.destroy is not a function`. Custom handle collections MUST use domain-specific names (e.g., `_eventHandles`, `_sketchHandles`, `_disposables`) or cleanly register into the inherited base `this._handles.add(...)`.
11. **Gradual Verification Protocol & Mandatory Micro-Gates**:
    - Never treat verification as a single end-of-task formality. Enforce the **6-Tier Gradual Verification Gate** after every code edit. Run every tier, including the Rule Validator; a passing build and lint is NOT a passing gate. Report the exit code of each tier. Skip a tier only when its script does not exist in `package.json`, and say so:
      1. *Fast Typecheck*: `tsc --noEmit` (clean types).
      2. *Lint*: `npm run lint` (zero errors).
      3. *Unit & Contract Tests*: Test component logic AND Designer attribute persistence (asserting that empty strings delete XML attributes and kebab-case attributes map to camelCase). Theme integration tests MUST prove that the computed shell `--primaryBackground` outranks OS preference, MUI popovers resolve their container to `.vsw-app`, and no global `MuiTypography` colour override exists. The suite MUST include the static styling audit (`src/utils/stylingAudit.test.ts`, installed via `scripts/install_styling_audit.py`), which enforces Rules 1–4 with per-rule ratchet ceilings.
      4. *Dead Code & Hygiene Gate*: `knip` (zero unused exports, dead files, or orphan CSS).
      5. *Production Build*: `npm run build` or `pnpm run build` (clean compilation).
      6. *Rule Validator*: `python3 <skill-dir>/scripts/validate_web_sdk.py --path <project>` MUST exit 0, where `<skill-dir>` is this skill's installed folder (e.g. `~/.agents/skills/vertigis-web-sdk-skill`) (zero Critical violations). A rule may be suppressed only with a written reason: `// vertigis-rule-disable RULE_ID -- <reason>` (next line) or `/* vertigis-rule-disable-file RULE_ID -- <reason> */` (whole file). Suppressions without a reason, with `*`, or with an unknown rule ID fail the gate.
    - **2-Strike Halt Gate**: If a fix fails verification twice on the same step, STOP. Report what was tried, what failed, and ask for guidance.
12. **Ponytail Code Minimization & Zero-Garbage Invariant**:
    - **Native Platform & MUI First**: Use native MUI controls (`IconButton`, `Typography`, `Radio`, `Checkbox`, `Box`, `Alert`) with `VertiGisThemeProvider`. NEVER write 30+ lines of custom CSS with `!important` targeting `.MuiRadio-root`, `.MuiCheckbox-root`, `.MuiButton-root`, or `.MuiFormControlLabel-label` to force dark mode colors. Wrap controls in `VertiGisThemeProvider` and let MUI handle states natively.
    - **Deletion-First Refactoring**: When replacing an implementation or abandoning an API, delete the old implementation and all unused helper files FIRST. Verify with `knip` before authoring new code.
    - **Zero Untracked Garbage**: Never leave experimental scrapers, orphan test fixtures, or dead wrappers in the codebase.
13. **Feature Actions, Commands, & Arcade Scripting Protocol**:
    - **Layer Filtering via `arcade.run`**: When configuring feature actions in Web Designer to trigger custom commands, always wrap the execution filter in `arcade.run` with a robust `canExecuteScript` using `HasKey($feature, 'Field')`:
      ```json
      [
        {
          "name": "arcade.run",
          "arguments": {
            "canExecuteScript": "(HasKey($feature, 'GFID') || HasKey($feature, 'gfid'))"
          }
        },
        "your-command.display"
      ]
      ```
    - **Command Execution Contract**: Custom commands registered via `registerCommandHandler` must gracefully accept either an ArcGIS Graphic/Feature object (`target.attributes`) or a plain parameter map (`target.id`).

## 4. Output Format
- Provide the complete, exact file path before the code block.
- Output clean, uncommented code (except for standard JSDoc block tags).
- If multiple files are needed (e.g. Model, View, index.ts), separate them logically.

## 5. Interactive Consultation Protocol (Grill-Me Mode)
When the user triggers this skill or enters `initiate`:
1. **`initiate` Command**: When the user types `initiate` or asks to initialize/configure AGENTS.md, run or offer `python3 vertigis-web-sdk-skill/scripts/initiate_agents_md.py [--target-dir <path>]` to inject or update official VertiGIS Studio Web SDK directives enclosed in `<!-- vertigis-web-sdk:start -->` and `<!-- vertigis-web-sdk:end -->` without touching existing instructions.
2. **Detect Project**: Scan the workspace to check if an existing VertiGIS project exists (`package.json`, `@vertigis/*`, `app/app.json`).
3. **If Existing Project Found**: Ask whether the user wants to **[Configure AGENTS.md Directives (`initiate`)]**, **[Review Code]** (categorized by Critical Errors, Architectural Warnings, and Cleanliness Recommendations), **[Add New Component]**, **[Add New Service]**, or **[Generate Scripts]**.
4. **If New / Uninitialized Workspace**: Conduct an interactive interview:
   - Ask for extension type (Component vs Service) and custom namespace.
   - Configure `AGENTS.md` directives via `initiate_agents_md.py`.
   - Ask for HTTPS Certificate strategy (generate with OpenSSL vs custom paths).
   - Generate `start.bat` / `start.sh` (which kills stale port 3000 processes and runs `npm start`) and `build.bat` / `build.sh`.

---

## Quick Reference & Table of Contents

| Topic | Reference Guide | Key Focus Areas |
| :--- | :--- | :--- |
| **Interactive Tooling** | [Scaffolding & Scripts](./references/10_interactive_scaffolding_and_tooling.md) | Discovery flow, `initiate` command (`AGENTS.md` injection), code audit checklist, static styling audit test (`install_styling_audit.py`), SSL certificates, `start.bat`, `build.bat`. |
| **Architecture & CLI** | [Overview & Concepts](./references/01_overview_and_concepts.md) | System model, CLI scaffolding, project structure, `src/index.ts`. |
| **Custom Components** | [Components Guide](./references/02_components.md) | Component models (`*Model.ts`), React views (`*.tsx`), `LayoutElement`, `observer()`, MUI usage, symmetric lifecycle contracts (`_onInitialize` first, `_onDestroy` last), and `_handles` clobbering prevention. |
| **Custom Services** | [Services Guide](./references/03_services.md) | Singletons, `ServiceBase`, state management, background timers, service injection. |
| **Commands & Operations** | [Commands & Operations](./references/04_commands_and_operations.md) | `registerCommandHandler`, `registerOperationHandler`, `canExecute`, built-in commands reference. |
| **Events & Observability** | [Events & Observability](./references/05_events_and_observability.md) | Lifecycle events (`app.initialized`, `map.click`), MobX observables, event subscriptions. |
| **Layout & App Config** | [Layout & Configuration](./references/06_layout_and_config.md) | `app.json` layout hierarchy, `app-config.json` model binding (`$ref`, `$eval`), theming, i18n. |
| **Workflow Web SDK** | [Workflow Web SDK](./references/07_workflow_web_sdk.md) | Custom workflow activities (`IActivityHandler`), custom form elements, ArcGIS JS API integration. |
| **Deployment** | [Deployment & Best Practices](./references/08_deployment_and_best_practices.md) | `npm run build`, hosting on CDN/SaaS, ArcGIS Enterprise items, CORS, bundling, and Designer deployment packaging lifecycle crash prevention. |
| **Tutorials & Recipes** | [Tutorials & Recipes](./references/09_tutorials_and_recipes.md) | Custom map click handling, configurable widgets, triggering workflows. |
| **Design Tokens & Theming** | [Design Tokens & Theming](./references/11_design_tokens_and_theming.md) | Design token subsystem (`tokens/ui.ts`, `tokens/typography.ts`, `tokens/index.ts`), safe fallbacks (`var(--primaryBackground, #ffffff)`), dynamic dual-theming (`color-mix`), `useIsDarkTheme` hook, standalone `isDarkTheme()`, MUI `ThemeProvider`, anti-god-component modularity standards (150–250 lines ceiling, 7-directory blueprint, extraction heuristics). |

---

## 1. Getting Started with a New Library

To initialize a new custom VertiGIS Studio Web library:

```bash
# Create a new library directory
npx @vertigis/web-sdk@latest create <library-name>

# Navigate into library directory
cd <library-name>

# Start development server with live reload
npm start
```

---

## 2. Core Development Workflow

### A. Registering Extensions (`src/index.ts`)
All components, services, and commands must be registered in the library entry point:

```typescript
import { LibraryRegistry } from "@vertigis/web/config";
import CustomWidget, { CustomWidgetModel } from "./components/CustomWidget/main";
import CustomService from "./services/CustomService";

export default function (registry: LibraryRegistry): void {
    // 1. Register Component
    registry.registerComponent({
        name: "custom-widget",
        namespace: "your.custom.namespace",
        getComponentType: () => CustomWidget,
        itemType: "custom-widget-model",
        getItemType: () => CustomWidgetModel,
        title: "Custom Widget"
    });

    // 2. Register Service
    registry.registerService({
        id: "custom-service",
        getService: (config) => new CustomService(config)
    });
}
```

### B. Standard Component Pattern (MUI + LayoutElement + observer)
Every UI widget consists of a paired **Model** and **React View**:

#### Model (`src/components/CustomWidget/CustomWidgetModel.ts`)
```typescript
import { ComponentModelBase, serializable, importModel } from "@vertigis/web/models";
import { MapModel } from "@vertigis/web/mapping";

export interface CustomHandle {
    remove(): void;
}

@serializable
export class CustomWidgetModel extends ComponentModelBase {
    @serializable
    title: string = "Default Title";

    @importModel("map-extension")
    map: MapModel | undefined;

    // RULE 10: NEVER name this `_handles` (would overwrite parent HandlesMixin and crash destroy())
    private _eventHandles: CustomHandle[] = [];

    // Lifecycle: Base FIRST
    protected async _onInitialize(): Promise<void> {
        await super._onInitialize();
        // Register subscriptions or handles
    }

    // Lifecycle: Child cleanup FIRST, super LAST
    protected async _onDestroy(): Promise<void> {
        for (const handle of this._eventHandles) {
            handle.remove();
        }
        this._eventHandles = [];
        await super._onDestroy();
    }
}
```

#### React View (`src/components/CustomWidget/main.tsx`)
```tsx
import * as React from "react";
import { observer } from "mobx-react-lite";
import {
    LayoutElement,
    LayoutElementProperties,
} from "@vertigis/web/components";
import { ErrorBoundary } from "../../utils/ErrorBoundary";
import { CustomWidgetModel } from "./CustomWidgetModel";
import "./CustomWidget.css";

interface CustomWidgetProps extends LayoutElementProperties<CustomWidgetModel> {}

const CustomWidget = observer(function CustomWidget(props: CustomWidgetProps) {
    const { model } = props;
    return (
        <LayoutElement {...props}>
            <ErrorBoundary fallbackMessage="Custom widget failed to load.">
                <div className="CustomWidget">
                    {/* Header with Semantic Markup & Namespaced CSS */}
                    <h2 className="CustomWidget-title">{model.title}</h2>
                    <p className="CustomWidget-subtitle">Component Overview & State</p>

                    {/* Nested Surface with Design Tokens */}
                    <div className="CustomWidget-card">
                        <p className="CustomWidget-body">Primary content description.</p>
                        <p className="CustomWidget-caption">
                            Secondary helper details and configuration info.
                        </p>
                    </div>

                    {model.map && (
                        <span className="CustomWidget-meta">
                            Attached Map ID: {model.map.id}
                        </span>
                    )}
                </div>
            </ErrorBoundary>
        </LayoutElement>
    );
});

export default CustomWidget;
```

#### Co-Located Component CSS (`src/components/CustomWidget/CustomWidget.css`)
```css
.CustomWidget {
    padding: var(--spacingLg, 16px);
    border: 1px solid var(--primaryBorder, #e0e0e0);
    border-radius: var(--borderRadius, 4px);
}

.CustomWidget-title {
    margin: 0 0 var(--spacingXs, 4px) 0;
    font-size: 1.25rem;
    font-weight: 500;
}

.CustomWidget-subtitle {
    margin: 0 0 var(--spacingLg, 16px) 0;
    font-size: 0.875rem;
    color: var(--secondaryForeground, #666666);
}

.CustomWidget-card {
    padding: var(--spacingMd, 12px);
    margin-bottom: var(--spacingLg, 16px);
    background-color: var(--secondaryBackground, #f5f5f5);
    border: 1px solid var(--primaryBorder, #e0e0e0);
    border-radius: var(--borderRadius, 4px);
}

.CustomWidget-body {
    margin: 0 0 var(--spacingXs, 4px) 0;
    font-size: 0.875rem;
}

.CustomWidget-caption {
    margin: 0;
    color: var(--secondaryForeground, #666666);
    font-size: 0.75rem;
}

.CustomWidget-meta {
    display: block;
    font-size: 0.75rem;
    color: var(--secondaryForeground, #666666);
}
```

### C. Exposing Properties to Designer (Settings Schema Protocol)
VertiGIS Studio Web Designer renders its component settings panel dynamically based on the schema returned by `getLayoutDesignerSettingsSchema`. When exposing customizable component properties to the Designer inspector:

```typescript
// src/index.ts
import { LibraryRegistry } from "@vertigis/web/config";
import {
    applyLayoutDesignerSettings,
    getLayoutDesignerSettings,
    getLayoutDesignerSettingsSchema,
    GetLayoutDesignerSettingsArgs,
    ApplyLayoutDesignerSettingsArgs,
    SettingsSchema,
} from "@vertigis/web/designer";
import CustomWidget, { CustomWidgetModel } from "./components/CustomWidget/main";

interface CustomWidgetLayoutSettings {
    title?: string;
    refreshInterval?: number;
    showBorder?: boolean;
}

export default function (registry: LibraryRegistry): void {
    registry.registerComponent({
        name: "custom-widget",
        namespace: "your.custom.namespace",
        getComponentType: () => CustomWidget,
        itemType: "custom-widget-model",
        getItemType: () => CustomWidgetModel,
        title: "Custom Widget",

        // 1. Schema Declaration: Informs Designer of field IDs, types, and tooltips
        getLayoutDesignerSettingsSchema: async (
            args: GetLayoutDesignerSettingsArgs
        ): Promise<SettingsSchema<CustomWidgetLayoutSettings>> => {
            const baseSchema = await getLayoutDesignerSettingsSchema(args);
            return {
                ...baseSchema,
                settings: [
                    ...(baseSchema.settings || []),
                    {
                        id: "title",
                        type: "text",
                        displayName: "Widget Title",
                        description: "Header title displayed on the widget card",
                    },
                    {
                        id: "refreshInterval",
                        type: "number",
                        displayName: "Refresh Interval (s)",
                        description: "Data polling interval in seconds",
                        min: 5,
                        max: 3600,
                    },
                    {
                        id: "showBorder",
                        type: "checkbox",
                        displayName: "Show Card Border",
                        description: "Render decorative card border",
                    },
                ],
            };
        },

        // 2. Current Value Extraction: Reads XML attributes into Designer form state
        getLayoutDesignerSettings: async (
            args: GetLayoutDesignerSettingsArgs
        ): Promise<CustomWidgetLayoutSettings> => {
            const baseSettings = await getLayoutDesignerSettings(args);
            const model = args.node.model as CustomWidgetModel | undefined;
            const attr = (k: string) => args.node.attributes.get(k);

            return {
                ...baseSettings,
                title: String(attr("title") ?? model?.title ?? "Default Title"),
                refreshInterval: Number(attr("refresh-interval") ?? model?.refreshInterval ?? 30),
                showBorder: attr("show-border") !== undefined ? attr("show-border") === "true" : Boolean(model?.showBorder),
            };
        },

        // 3. Persisting Changes: Writes back attributes, deletes empty ones, and updates live model
        applyLayoutDesignerSettings: async (
            args: ApplyLayoutDesignerSettingsArgs<CustomWidgetLayoutSettings>
        ): Promise<void> => {
            await applyLayoutDesignerSettings(args);
            const { node, settings } = args;

            const safeTrim = (val: unknown): string | undefined => {
                if (typeof val === "string") {
                    const trimmed = val.trim();
                    return trimmed.length > 0 ? trimmed : undefined;
                }
                return undefined;
            };

            // Rule 5: Explicitly DELETE cleared attributes to avoid sticky defaults
            if (settings.title !== undefined) {
                const val = safeTrim(settings.title);
                if (val) {
                    node.attributes.set("title", val);
                } else {
                    node.attributes.delete("title");
                }
            }

            if (settings.refreshInterval !== undefined) {
                if (settings.refreshInterval > 0) {
                    node.attributes.set("refresh-interval", String(settings.refreshInterval));
                } else {
                    node.attributes.delete("refresh-interval");
                }
            }

            if (settings.showBorder !== undefined) {
                node.attributes.set("show-border", String(settings.showBorder));
            }

            // Propagate updated configuration into the live model instance
            const model = node.model as CustomWidgetModel | undefined;
            if (model && typeof model.updateConfig === "function") {
                model.updateConfig({
                    title: safeTrim(settings.title),
                    refreshInterval: settings.refreshInterval,
                    showBorder: settings.showBorder,
                });
            }
        },
    });
}
```

---

## 3. Tooling & Automation Scripts

This skill includes automated Python utilities in `scripts/`:
- `scripts/initiate_agents_md.py`: Automatically creates or updates the target repository's `AGENTS.md` with official VertiGIS Studio Web SDK directives enclosed between `<!-- vertigis-web-sdk:start -->` and `<!-- vertigis-web-sdk:end -->`.
- `scripts/crawl_vertigis_docs.py`: Crawl4AI script to refresh crawled documentation directly from the VertiGIS Developer Center.
- `scripts/validate_web_sdk.py --path <project> [--format ansi|json|markdown] [--output <file>] [--strict] [--self-test]`: Standalone rule validator (Python 3.10+, standard library only). Every rule ID, severity, and remediation lives in `scripts/rules.json`; each entry cites the rule above it enforces. Exits 1 on any Critical violation (or any Major with `--strict`). `--self-test` runs the rule fixtures in `scripts/tests/` and checks that every code example in this skill passes.
- `scripts/install_styling_audit.py [--target-dir <path>] [--force]`: Copies the static styling audit (`scripts/styling-audit/stylingAudit.ts` + `stylingAudit.test.ts`) into `<target>/src/utils/`. Requires `typescript` and `vitest` in the target project.

### Styling Audit Test (`src/utils/stylingAudit.test.ts`)
A Vitest suite that parses every TS/TSX file with the TypeScript compiler API and scans every CSS file under `src/`, checking 19 rules:

| Group | Rules |
| :--- | :--- |
| Inline styling | `inline-static-style`, `mixed-class-and-style`, `inline-sx`, `typography-color-override`, `hardcoded-radius` |
| Tokens | `inline-token-literal`, `token-fallback-drift` (compared against `src/tokens/ui.ts`) |
| CSS hygiene | `orphan-css-class`, `duplicate-css-class`, `css-important`, `css-root-scope`, `css-mui-override`, `css-font-family`, `css-hardcoded-radius` |
| MUI hygiene | `css-baseline`, `deep-mui-import`, `deprecated-input-props`, `theme-hardcoded-palette` |
| Modularity | `file-too-large` (> 250 lines) |

Workflow:
1. **Install**: `python3 vertigis-web-sdk-skill/scripts/install_styling_audit.py --target-dir <repo>`.
2. **Baseline**: `STYLE_AUDIT_REPORT=1 npx vitest run src/utils/stylingAudit.test.ts -t "prints a report"` prints counts per rule; set each `BASELINE` ceiling to its count. Counts may only go down.
3. **Migrate**: add `STYLE_AUDIT_FILE=<path>` to list one file's or folder's violations with line numbers. Fix, re-run, then lower the ceilings.
4. **Lock**: when only justified violations remain, list them in `KNOWN_EXCEPTIONS` (file → rules, each with a one-line reason) and set `ENFORCE_EXCEPTIONS_ONLY = true`, so any new violation in any file fails `pnpm test`.
5. **Extend**: when adding a rule, add a fixture assertion in the `stylingAudit rule detectors` block first, then a `BASELINE` entry.
