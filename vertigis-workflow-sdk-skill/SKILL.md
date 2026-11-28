---
name: vertigis-workflow-sdk-skill
description: >-
  Comprehensive guide and reference for developing custom activities and form
  elements using the VertiGIS Studio Workflow SDK and ArcGIS API for JavaScript.
  Use this skill whenever developing, reviewing, or refactoring TypeScript workflow
  activities, custom React form elements, MUI typography and design tokens,
  7-directory component decomposition, or when running "initiate" and configuring AGENTS.md.
---

# VertiGIS Studio Workflow SDK Skill

## 1. Role
You are an expert GIS Developer and Enterprise React Architect specializing in the VertiGIS Studio Workflow SDK.

## 2. Objective
Generate flawless, production-ready, enterprise-grade code for VertiGIS Studio Workflow extensions. You build custom activities (backend logic) and custom form elements (React/MUI widgets) that perfectly align with VertiGIS SDK architecture, React best practices, multi-host adaptability (Web & Mobile), design token subsystems, dynamic light/dark theming, strict component modularity, and WCAG accessibility standards.

## 3. Rules (CRITICAL AGENT DIRECTIVES)
You MUST adhere to the following rules without exception:

1. **Typography System & Shell Inheritance**: Strict ban on raw HTML text elements (`<span>`, `<p>`, `<h1>`-`<h6>`, `<label>`). All textual content in Form Elements MUST use `@mui/material` `<Typography variant="...">` (`h6` headers, `subtitle1`/`subtitle2` group titles, `body1`/`body2` field labels and descriptions, `caption`/`overline` validation hints and badges).
   - **Semantic Typography Palette Props**: Primary text has no `color` prop: it inherits the host foreground (`color="text.primary"` is redundant and is flagged). Use `color="text.secondary"` (captions, subtitles, helper microcopy), `color="inherit"` (inside a coloured surface that sets its own foreground), and `color="error"` (validation). NEVER write bespoke inline `sx={{ color: ... }}` solely to set secondary/helper text colors.
   - **Zero `font-family` (No Exceptions)**: Typography and font-family are inherited natively from the host shell (`.vsw-app` / Workflow runner). NEVER declare `font-family`, the `font:` shorthand, or `fontFamily` anywhere: CSS, `sx`, `style`, token files (no font-stack tokens, including monospace/code stacks). The single allowed line is `typography: { fontFamily: "inherit" }` in the `createTheme` theme provider (or a chart library theme): MUI and chart libraries otherwise apply their own default font (Roboto / sans-serif) instead of the host font. Using `<Typography>` deletes boilerplate font-size and line-height declarations. Ensure minimum 14px text size (`body2`) for mobile and outdoor field readability.
   - **Top-Level Package Exports Only**: Always import directly from package roots (`import { Box, Typography } from "@mui/material"`; `import { createTheme, ThemeProvider } from "@mui/material/styles"`). Deep imports (e.g. `@mui/material/styles/createTheme`) are deprecated in MUI v7 and break under modern bundlers.
2. **Two-Tier Styling Architecture (Pure Theme Inheritance & Zero Color Injection)**: Strict ban on hardcoded hex (`#ffffff`, `#1976d2`), RGB, or HSL colors for UI chrome, backgrounds, text, and borders. ALWAYS provide safe fallbacks for CSS variable tokens (e.g. `var(--primaryBackground, #ffffff)`). Group tokens under a dedicated `tokens/` directory (`ui.ts`, `typography.ts`, `index.ts`).
   - **Inheritance-First / Zero Color Injection Rule**: Standard MUI controls (e.g., `DatePicker`, `TimePicker`, `TextField`, `Select`, `Button`, `Checkbox`, `Radio`, `Switch`, `Tabs`) MUST inherit their colors, borders, typography, and interactive states (`:hover`, `:focus-visible`, `:disabled`, `:selected`) natively from the host theme via `VertiGisThemeProvider` / `createVertiGisWorkflowMuiTheme`. Strictly prohibit micro-injecting inline color overrides (`sx={{ color, bgcolor, borderColor }}`) onto standard form inputs, pickers, or buttons.
   - **Inherit, Don't Restate (Minimal CSS Injection)**: Form elements render inside the host panel, which already supplies text colour, background and font. NEVER restate them: no `color: var(--primaryForeground)`, no `background: var(--primaryBackground)` (a transparent element already shows the panel), no `<Typography color="text.primary">`, and no wrapper element whose only job is to set colours for its children. Set a colour token ONLY where the element deliberately differs from its parent (status banner, accent badge, nested card). Exceptions: opaque layers that cover other content (`position: sticky|fixed|absolute` or `z-index`), the `createTheme` provider, and content rendered outside the shell (portals), which must carry a `vertigis-rule-disable REDUNDANT_INHERITED_TOKEN -- <reason>` comment.
   - **Token Pairing & Contrast (Validated)**: When an element sets a background, it MUST set the foreground from the same pair in the same rule or `sx` object: `XBackground` with `XForeground` (e.g. `--alertRedBackground` with `--alertRedForeground`), accent fills (`--primaryAccent`) with `--emphasizedButtonForeground`. Text on panel surfaces (`--primaryBackground`, `--secondaryBackground`, `--primaryAccentLight`, item hover/selected) uses only `--primaryForeground` (inherited), `--secondaryForeground`, `--primaryAccent`, `--errorHelperTextForeground` or a disabled token. NEVER use a `*Foreground` token as a background or a `*Background` token as text (the inverse pair `--primaryForeground` / `--primaryBackground` is the only exception). Text must reach WCAG AA 4.5:1 against its background, computed from the `tokens/ui.ts` fallbacks (disabled text exempt). The validator enforces `REDUNDANT_INHERITED_TOKEN`, `TOKEN_PAIRING` and `TOKEN_CONTRAST`.
   - **Strict Ban on `<CssBaseline />`**: NEVER mount `<CssBaseline />` under `VertiGisThemeProvider` or anywhere in form elements. Custom form elements execute as guest widgets inside the host shell (`.vsw-app` or Mobile container). `<CssBaseline />` injects global CSS resets (`html`, `body`, scrollbars, box-sizing) that clobber the host application shell, corrupt mobile viewport scaling, and break Esri map layouts.
   - **MUI v7 `slotProps` Standardization**: Standardize on `slotProps` for composite controls. Legacy nested props (`PaperProps`, `inputProps`, `InputProps`, `BackdropProps`) are deprecated. For example, use `<TextField slotProps={{ input: { readOnly } }}>` and `<Dialog slotProps={{ paper: { className: "..." } }}>`. In modals, use `onClose` instead of deprecated `onBackdropClick`.
   - **Type-Safe Style Dictionaries (`Record<string, SxProps<Theme>>`)**: When custom MUI styles are genuinely necessary beyond theme defaults, do not scatter verbose inline `sx={{ ... }}` objects across markup. Define type-safe dictionaries at the top of the file: `const styles: Record<string, SxProps<Theme>> = { ... }` (or `ComponentName.styles.ts` for files >= 100 lines).
   - **Canonical Token Fallbacks**: Every `var(--token, #fallback)` MUST use the same fallback as the element's `tokens/ui.ts`. Colour literals may appear only in `tokens/` and in the fallback slot of `var(--token, <fallback>)`.
   - **Crash Prevention**: NEVER pass raw `var(...)` strings into `palette.primary.main` or `palette.error.main` (causes MUI `augmentColor()` to crash). Attach CSS variables via component `styleOverrides` (e.g. `MuiRadio: { styleOverrides: { root: { "&.Mui-checked": { color: "var(--primaryAccent, #007ac2)" } } } }`).
   - **Shape Tokens & Border Radius**: NEVER hardcode pixel corner radii (e.g. `4px`). Always reference unified shape tokens: `var(--borderRadius, 4px)` (standard), `var(--borderRadiusSm, 2px)` (micro), `var(--borderRadiusLarge, 8px)` / `var(--borderRadiusLg, 8px)` (cards/dialogs), and `50%` / `9999px` (pills/rounds).
   - **Spacing Tokens (Validated)**: In any CSS file, NEVER write literal lengths for `margin*`, `padding*` or `gap` (e.g. `padding: 12px;`). Use spacing tokens with fallbacks: `var(--spacingXxs, 2px)`, `var(--spacingXs, 4px)`, `var(--spacingSm, 8px)`, `var(--spacingMd, 12px)`, `var(--spacingLg, 16px)`, `var(--spacingXl, 24px)`. Only `0`, `auto` and keywords may be written literally. The validator enforces `HARDCODED_SPACING`.
   - **Strict Exception Criteria (When Token Injection is Allowed)**: Direct token injection (`var(--...)` or `UI_TOKENS.*`) is permitted ONLY for: (1) Custom alert/status banners outside standard MUI palettes (e.g., `var(--alertAmberBackground)`), (2) Derived dynamic tints and overlays using `color-mix(in srgb, ...)`, (3) Structural container dividers (`1px solid var(--primaryBorder)`), and (4) Non-CSS contexts (Plotly, Canvas renderers, signature pads, barcode viewfinders, PDF exports, SVG vector paths).
   - **Mobile & Multi-Host Theming**: For dynamic surfaces and tints, use `color-mix(in srgb, ...)`. For non-CSS contexts, utilize the canonical `useIsDarkTheme()` hook or `isDarkTheme()` utility. For mobile form elements, enforce minimum 44x44px touch targets. Ensure WCAG AA contrast (4.5:1 text, 3:1 graphical elements) across light and dark host themes.
3. **No Custom CSS / CSS Modules**: NEVER generate `*.css` or `*.module.css` files in Workflow form elements. Form elements run across Web and Mobile runtimes; styling is driven by `VertiGisThemeProvider` and token-backed MUI `sx` dictionaries. Standard MUI form inputs must never have redundant inline style overrides.
4. **Strict Component Modularity & Anti-God-Component Architecture**: Strive for under **150 lines** per file with a **hard ceiling of 250 lines**. Any file exceeding 250 lines MUST be refactored and decomposed into `components/` (stateless presentation), `hooks/` (state/logic/subscriptions), `tokens/` (design tokens & theme bridges), and `utils/` (pure helpers/types). Wrap form elements in `<FormElementErrorBoundary>`. Any file containing JSX MUST use the `.tsx` extension; JSX in a `.ts` file is banned (`JSX_IN_TS`).
5. **Wire Standard Props & State Persistence**: You MUST destructure and wire `enabled`, `visible`, and `readOnly` to the underlying MUI components (e.g., `disabled={!enabled}`, `slotProps={{ input: { readOnly } }}`). Critical workflow state MUST be saved via `props.setValue()` or `props.setProperty()`, NEVER ephemeral local `useState` (which is lost when switching form tabs).
6. **Activity Dropdown Inputs**: For workflow activity inputs to appear as dropdowns in the designer, the union type must be defined INLINE (e.g., `inputType: 'a' | 'b' | string;`). Never extract it to an external type alias.
7. **Enterprise Reliability**: Wrap Workflow Activity `execute` blocks in `try/catch` and throw structured errors to the workflow runtime. Add `aria-label` and `onKeyDown` to interactive MUI components in Form Elements to ensure WCAG accessibility.
8. **ArcGIS Import Rules**: Use default imports for class modules (`import Graphic from "@arcgis/core/Graphic"`). Use star imports for utility/function modules to avoid AMD errors (`import * as projection from "@arcgis/core/geometry/projection"`). Use ambient `__esri.*` types.
9. **Rule Validator Gate**: After every code edit, run `python3 vertigis-workflow-sdk-skill/scripts/validate_workflow_sdk.py --path <project>`; it MUST exit 0 (zero Critical violations; `--strict` also fails on Major). Supports `--format ansi|json|markdown`, `--output <file>` and `--self-test`. A rule may be suppressed only with a written reason: `// vertigis-rule-disable RULE_ID -- <reason>`.

## 4. Output Format
- Provide the complete, exact file path before the code block.
- Output clean, uncommented code (except for standard JSDoc block tags).
- If multiple files are needed, separate them logically.

## 5. Interactive Consultation Protocol (Grill-Me Mode)
When the user triggers this skill or enters `initiate`:
1. **`initiate` Command**: When the user types `initiate` or asks to initialize/configure AGENTS.md, run or offer `python3 vertigis-workflow-sdk-skill/scripts/initiate_agents_md.py [--target-dir <path>]` to inject or update official VertiGIS Studio Workflow SDK directives enclosed in `<!-- vertigis-workflow-sdk:start -->` and `<!-- vertigis-workflow-sdk:end -->` without touching existing instructions.
2. **Detect Project**: Scan the workspace to check if an existing VertiGIS Workflow project exists (`package.json`, `@vertigis/workflow`, `src/activities`, `src/elements`).
3. **If Existing Project Found**: Ask whether the user wants to **[Configure AGENTS.md Directives (`initiate`)]**, **[Review Code]** (categorized by Critical Errors, Architectural Warnings, and Cleanliness Recommendations), **[Add New Activity]**, **[Add New Form Element]**, or **[Generate Scripts]**.
4. **If New / Uninitialized Workspace**: Conduct an interactive interview:
   - Ask for target extension type (Activity vs Form Element), name, category, and display name.
   - Configure `AGENTS.md` directives via `initiate_agents_md.py`.
   - Ask for HTTPS Certificate strategy (generate with OpenSSL vs custom paths).
   - Generate `start.bat` / `start.sh` (which kills stale port 5000 processes and runs `npm start`) and `build.bat` / `build.sh`.

---

## Quick Reference & Table of Contents

| Topic | Reference Document | Key Focus Areas |
| :--- | :--- | :--- |
| **Interactive Tooling** | [Scaffolding & Scripts](./references/10_interactive_scaffolding_and_tooling.md) | Discovery flow, `initiate` command (`AGENTS.md` injection), code audit checklist, OpenSSL SSL certificates, `start.bat`, `build.bat`. |
| **Project Structure** | [Project Structure & Rules](./references/01_project_structure_and_rules.md) | Standard folders (`activities/`, `elements/`), naming rules, top-level barrel `src/index.ts`. |
| **Activity Development** | [Activity Development Guide](./references/02_activity_development.md) | Canonical pattern, I/O interfaces, `runActivity` skip logic, `showLogger`, `utils/` folder splitting. |
| **Form Element Development** | [Form Element Guide](./references/03_form_element_development.md) | Canonical `main.tsx`, props API, wiring standard props (`enabled`, `visible`, `readOnly`), token integration, error boundaries. |
| **React Component Decomposition** | [React Decomposition](./references/04_react_component_decomposition.md) | Anti-god-component architecture (150–250 lines), 7-directory blueprint, extracting hooks, presentation subcomponents, and error boundaries. |
| **MapProvider & ArcGIS** | [MapProvider & ArcGIS](./references/05_map_provider_and_arcgis.md) | `@activate(MapProvider)` pattern, `await mapProvider.load()`, ambient `__esri.*` types, default vs named `@arcgis/core` imports. |
| **Block Tags Reference** | [Block Tags Cheat-Sheet](./references/06_block_tags_reference.md) | `@displayName`, `@category`, `@required`, `@clientOnly`, `@supportedApps` (`VSW`, `EXB`, etc.). |
| **Styling & Design Tokens** | [Styling & Theming](./references/07_styling_and_theming.md) | Centralized token architecture (`tokens/`), safe fallbacks, `color-mix` surface derivation, dynamic dual-theme detection (`useIsDarkTheme`, `isDarkTheme`), 44x44px touch targets, and MUI theme setup. |
| **Debugging & Deployment** | [Debugging & Deployment](./references/08_debugging_and_deployment.md) | Terminal compiler diagnostics, `npm start`, `npm run build`, registering `activitypack.json`. |
| **Recipes & Templates** | [Practical Recipes](./references/09_practical_recipes.md) | Full code templates for activities and form elements using MUI. |

---

## 1. Project Directory Structure

```text
src/
├── index.ts                          ← Barrel export: exports ALL activities + elements
├── activities/
│   └── <ActivityName>/
│       ├── main.ts                   ← ONLY class + I/O interfaces + JSDoc tags (max 150 lines)
│       └── utils/                    ← Required when main.ts > ~150 lines or domain logic is distinct
│           ├── types.ts              ← Interfaces, type aliases, constants
│           └── <domain>Helpers.ts   ← Pure/async helper functions per logical domain
└── elements/
    └── <ElementName>/
        ├── main.tsx                  ← Orchestrator (max 150 lines): wires hooks + renders sub-components + registration
        ├── hooks/                    ← Custom hooks for state/effects (useIsDarkTheme.ts, useMyLogic.ts)
        ├── components/               ← Sub-components for UI decomposition (StatusBar.tsx, FormElementErrorBoundary.tsx)
        ├── tokens/                   ← Centralized design tokens (ui.ts, typography.ts, index.ts)
        ├── utils/                    ← Pure helper functions, defaults, formatters
        └── types/                    ← Domain models, schemas, and element prop types
```

**Naming Rules:**
- Activity class: `<PascalCase>Activity` (e.g. `PDFMapGeneratorActivity`).
- Element registration id: matches element display name (e.g. `"FeatureInformation"`).
- Barrel exports in `src/index.ts`:
  - Activities end with `Activity` (e.g. `export { default as MyActivityActivity } from "./activities/MyActivity/main";`).
  - Elements end with `Registration` (e.g. `export { default as MyElementRegistration } from "./elements/MyElement/main";`).

---

## 2. Activity Canonical Pattern (`src/activities/<Name>/main.ts`)

```typescript
import type { IActivityHandler } from "@vertigis/workflow";

interface MyActivityInputs {
  /**
   * @displayName Required Input
   * @description Full description of what this input does.
   * @required
   */
  requiredInput: string;

  /**
   * @displayName Run Activity
   * @description Whether to run the activity. Defaults to true.
   */
  runActivity?: boolean;

  /**
   * @displayName Show Logger
   * @description Enable console debug output. Defaults to false.
   */
  showLogger?: boolean;
}

interface MyActivityOutputs {
  /**
   * @description The primary result returned to the workflow.
   */
  result: string;
}

/**
 * @displayName My Activity Display Name
 * @defaultName MyActivity
 * @category Custom Utilities
 * @description Description shown in Workflow Designer toolbox.
 * @helpUrl https://docs.vertigisstudio.com/workflow/latest/help/
 * @clientOnly
 * @supportedApps VSW, EXB
 */
export default class MyActivity implements IActivityHandler {
  async execute(inputs: MyActivityInputs): Promise<MyActivityOutputs> {
    try {
      const { showLogger = false } = inputs;

      const runActivity = inputs.runActivity !== undefined ? inputs.runActivity : true;
      if (!runActivity) {
        if (showLogger) console.log("MyActivity skipped.");
        return { result: "" };
      }

      if (showLogger) {
        console.log("MyActivity executing with inputs:", inputs);
      }

      if (!inputs.requiredInput) {
        throw new Error("requiredInput is required");
      }

      return { result: "done" };
    } catch (error) {
      throw new Error(`MyActivity failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}
```

---

## 3. Form Element Canonical Pattern (MUI & Design Tokens) (`src/elements/<Name>/main.tsx`)

```tsx
import * as React from "react";
import { FormElementProps, FormElementRegistration } from "@vertigis/workflow";
import { Box, TextField, Typography } from "@mui/material";
import { tokens } from "./tokens";
import { FormElementErrorBoundary } from "./components/FormElementErrorBoundary";

export interface MyElementProps extends FormElementProps<string> {
  customPlaceholder?: string;
  secondaryStatus?: string;
}

function MyElementView(props: MyElementProps): React.ReactElement | null {
  const {
    value,
    setValue,
    setProperty,
    customPlaceholder = "Enter value...",
    enabled = true,
    visible = true,
    readOnly = false,
  } = props;

  if (!visible) return null;

  const handleChange = (newVal: string) => {
    setValue(newVal);
    setProperty("secondaryStatus", newVal.length >= 6 ? "Valid" : "Too short");
  };

  return (
    <Box
      sx={{
        p: 2,
        backgroundColor: tokens.ui.surface.secondary,
        border: `1px solid ${tokens.ui.border.primary}`,
        borderRadius: tokens.ui.shape.borderRadius,
        boxShadow: tokens.ui.shape.shadowPrimary,
        display: "flex",
        flexDirection: "column",
        gap: 1.5,
      }}
    >
      <Box>
        <Typography variant="subtitle1">
          Custom Inspection Field
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Enter the field inspection value. Changes persist across workflow form tabs.
        </Typography>
      </Box>

      <TextField
        fullWidth
        variant="outlined"
        placeholder={customPlaceholder}
        value={value ?? ""}
        disabled={!enabled}
        helperText="Required minimum 6 characters for valid status."
        slotProps={{
          input: { readOnly },
          htmlInput: {
            "aria-label": "Custom Input Field",
            style: { minHeight: "24px" },
          },
        }}
        onChange={(e) => handleChange(e.currentTarget.value)}
        sx={{
          borderRadius: tokens.ui.shape.borderRadius,
          "& .MuiInputBase-root": {
            minHeight: tokens.ui.touch.minHeight, // Mobile 44x44px touch target compliance
          },
          "& .MuiInputBase-input": {
            fontSize: tokens.typography.fontSize.body2, // Mobile outdoor readability (14px)
          },
        }}
      />
    </Box>
  );
}

export function MyElement(props: MyElementProps): React.ReactElement {
  return (
    <FormElementErrorBoundary>
      <MyElementView {...props} />
    </FormElementErrorBoundary>
  );
}

const MyElementRegistration: FormElementRegistration<MyElementProps> = {
  component: MyElement,
  id: "MyElement", // MUST match Custom Type in Workflow Designer
  getInitialProperties: () => ({
    value: undefined,
    enabled: true,
    visible: true,
    readOnly: false,
    customPlaceholder: "Enter text...",
    secondaryStatus: undefined,
  }),
};

export default MyElementRegistration;
```
