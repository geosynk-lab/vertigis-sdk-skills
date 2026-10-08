# VertiGIS Studio Web SDK: Design Tokens & Dynamic Theming Architecture

## Table of Contents
- [Introduction & Architectural Overview](#introduction--architectural-overview)
  - [The Shell Theming Mechanism](#the-shell-theming-mechanism)
  - [The Critical Need for a Type-Safe Token Subsystem](#the-critical-need-for-a-type-safe-token-subsystem)
- [Design Token Architecture](#design-token-architecture)
  - [1. Safe Fallbacks & Zero Hardcoded Colors Rule](#1-safe-fallbacks--zero-hardcoded-colors-rule)
  - [2. UI Design Tokens (`src/tokens/ui.ts`)](#2-ui-design-tokens-srctokensuits)
  - [3. Typography Tokens (`src/tokens/typography.ts`)](#3-typography-tokens-srctokenstypographyts)
  - [4. Color-Mix Utilities & Unified Barrel Export (`src/tokens/index.ts`)](#4-color-mix-utilities--unified-barrel-export-srctokensindexts)
- [Dynamic Dual-Theme System](#dynamic-dual-theme-system)
  - [1. Standalone Synchronous Theme Detection (`src/utils/isDarkTheme.ts`)](#1-standalone-synchronous-theme-detection-srcutilsisdarkthemets)
  - [2. Canonical Reactive Hook (`src/hooks/useIsDarkTheme.ts`)](#2-canonical-reactive-hook-srchooksuseisdarkthemets)
  - [3. Host-Owned Theming & Elimination of ThemeProviders](#3-host-owned-theming--elimination-of-themeproviders)
  - [4. Co-Located Namespaced CSS Architecture (`ComponentName.css`)](#4-co-located-namespaced-css-architecture-componentnamecss)
  - [5. Non-CSS Renderers Integration Patterns](#5-non-css-renderers-integration-patterns)
- [Component Modularity Architecture](#component-modularity-architecture)
  - [1. Standard 7-Directory Blueprint](#1-standard-7-directory-blueprint)
  - [2. File Size Thresholds & Enforcement Rules](#2-file-size-thresholds--enforcement-rules)
  - [3. Actionable Extraction Heuristics](#3-actionable-extraction-heuristics)
  - [4. Concrete Before / After Refactoring Demonstration](#4-concrete-before--after-refactoring-demonstration)
- [Pre-Review Audit Checklist](#pre-review-audit-checklist)

---

## Introduction & Architectural Overview

VertiGIS Studio Web provides an enterprise web mapping runtime built on React, MobX, TypeScript, and the ArcGIS API for JavaScript. In this architecture, visual presentation and brand identity are governed by an extensible **design token subsystem** injected dynamically into the host DOM by the VertiGIS shell.

### The Shell Theming Mechanism

When a VertiGIS Studio Web application boots, the host layout engine wraps all components inside a root container element (typically `.vsw-app`). The application's configuration (`app-config.json`) defines a `branding` service with an active theme (`"light"` or `"dark"`), brand accent colors, and custom color dictionaries:

```json
{
  "schemaVersion": "1.0.0",
  "items": {
    "branding": {
      "service": "branding",
      "properties": {
        "template": "dark",
        "accentColor": "#007ac2",
        "colors": {
          "primaryBackground": "#1e1e1e",
          "primaryForeground": "#f5f5f5"
        }
      }
    }
  }
}
```

Every property configured in the `branding` service is transformed into a CSS custom property (e.g., `--primaryBackground`, `--primaryForeground`, `--primaryAccent`) and injected as inline styles on the `.vsw-app` root element.

### The Critical Need for a Type-Safe Token Subsystem

While direct consumption of CSS variables via strings (`var(--primaryBackground)`) works in standard runtime scenarios, it introduces severe enterprise failure points:

1. **Test & Storybook Degradation**: In isolated unit tests (Vitest, Jest), component previews, or Storybook sandboxes, the VertiGIS shell is not present. Unqualified CSS variables resolve to empty strings (`""`), resulting in invisible text, transparent cards, and layout collapse.
2. **Theme Switching Flashes**: When an application transitions between light and dark themes at runtime, hardcoded alpha calculations or un-tokenized controls fail to recalculate.
3. **Non-CSS Rendering Engines**: Advanced GIS widgets frequently render data using non-CSS pipelines—such as HTML5 `<canvas>`, WebGL, Plotly.js charts, and client-side PDF generators (jsPDF). These engines cannot inspect CSS stylesheets and require programmatic access to theme state.
4. **MUI Composite Control Desynchronization**: Complex composite controls from `@mui/material` (Sliders, Switches, Pickers, Paper surfaces) rely on internal SVG paths, canvas shaders, and theme palettes that default to standard MUI colors (such as `#1976d2`) rather than VertiGIS tokens.

The design token architecture codified in this reference solves these challenges by providing:
- Guaranteed WCAG AA fallback values for offline/preview resilience.
- Modern CSS `color-mix()` blending helpers for adaptive overlays and hover states.
- 3-tier dynamic dark/light theme detection for both React and non-CSS contexts.
- An enterprise MUI `ThemeProvider` bridge.
- Strict component modularity standards to eliminate monolithic "god components".

---

<span id="design-token-architecture"></span>
## Design Token Architecture

The design token subsystem is organized into a dedicated `tokens/` directory within the extension or component source tree:

```
src/tokens/
├── ui.ts             # Surface, text, border, accent, control, status, and shape tokens
├── typography.ts     # Font stacks, font scale, weights, and line heights
└── index.ts          # Central barrel export and color-mix runtime utilities
```

### 1. Safe Fallbacks & Zero Hardcoded Colors Rule

#### Safe Fallback Resilience
Every token reference **must** include a safe fallback value conforming to WCAG AA contrast standards. For example:
- `var(--primaryBackground, #ffffff)`
- `var(--primaryForeground, #212121)`
- `var(--primaryAccent, #007ac2)`

If the host shell has not yet injected styles, or if a component is rendered in an automated test environment, the browser or test runner immediately falls back to the guaranteed default value, preventing silent visual regressions.

#### Strict Zero Hardcoded Colors Policy
- **Prohibited**: Hardcoded hex strings (`#ffffff`, `#000000`, `#1976d2`), static RGB/RGBA functions (`rgba(0, 0, 0, 0.5)`), or static HSL literals.
- **Mandatory**: All color declarations must resolve through `UI_TOKENS` or dynamic CSS `color-mix()` utilities.

---

### 2. UI Design Tokens (`src/tokens/ui.ts`)

The `UI_TOKENS` dictionary catalogs all standard VertiGIS CSS variables, grouped into semantic categories with safe WCAG AA fallbacks:

```typescript
/**
 * UI Design Tokens for VertiGIS Studio Web SDK
 * Maps official VertiGIS CSS custom properties with safe WCAG AA fallbacks.
 *
 * All tokens provide guaranteed defaults for isolated testing, Storybook,
 * and initial shell boot before the branding service injects runtime variables.
 */

export const UI_TOKENS = {
    // Surface & Background Colors
    surface: {
        /** Main panel, drawer, dialog, and container background */
        primary: "var(--primaryBackground, #ffffff)",
        /** Disabled container / control background */
        primaryDisabled: "var(--primaryBackgroundDisabled, #ebebeb)",
        /** Nested cards, zebra-striping, inset panels, and table headers */
        secondary: "var(--secondaryBackground, #ebebeb)",
        /** Semi-transparent modal backdrop overlay */
        overlay: "var(--overlayBackground, rgba(0, 0, 0, 0.5))",
        /** Inverted high-contrast surface for tooltips and snackbars */
        inverse: "var(--primaryForeground, #323232)",
        /** Default map background behind tile layers */
        mapBackground: "var(--defaultMapBackground, #ebebeb)",
        /** Transparent / None placeholder */
        none: "var(--none, rgba(0, 0, 0, 0.00))",
    },

    // Foreground & Typography Colors
    text: {
        /** Primary body copy, headers, and high-contrast labels */
        primary: "var(--primaryForeground, #323232)",
        /** Secondary captions, subtitles, helper text, and muted labels */
        secondary: "var(--secondaryForeground, #575757)",
        /** Inactive controls, placeholder copy, and disabled text */
        disabled: "var(--primaryForegroundDisabled, #a1a1a1)",
        /** Inverted high-contrast text on accent or dark backgrounds */
        inverse: "var(--primaryBackground, #ffffff)",
        /** Splash screen foreground text */
        splashScreen: "var(--splashScreenForeground, #ffffff)",
    },

    // Borders & Structural Dividers
    border: {
        /** Outer panel borders, card outlines, and standard dividers */
        primary: "var(--primaryBorder, #c6c6c6)",
        /** Subtle inner dividers, grid lines, and nested borders */
        secondary: "var(--secondaryBorder, #a1a1a1)",
        /** Main application shell panel border */
        panel: "var(--panelBorder, #a1a1a1)",
        /** High-visibility border for keyboard focus rings and active selections */
        focus: "var(--focusBorder, #1a72c4)",
    },

    // Brand Accents & Interactive Highlights
    accent: {
        /** Primary enterprise brand color, active tabs, and primary buttons */
        primary: "var(--primaryAccent, #1a72c4)",
        /** Hover state for brand buttons, active links, and selection rings */
        hover: "var(--primaryAccentHover, #2c2c2c)",
        /** Disabled state for primary brand accent */
        disabled: "var(--primaryAccentDisabled, #7c7c7c)",
        /** Large brand accent elements */
        large: "var(--primaryAccentLarge, #1a72c4)",
        /** Subtle background tint for selected rows or badge highlights */
        light: "var(--primaryAccentLight, #e3eff9)",
        /** Contrasting text color rendered on top of accent fills */
        contrastText: "var(--emphasizedButtonForeground, #ffffff)",
    },

    // Interactive Controls & Form Elements
    control: {
        /** Form input border (MuiOutlinedInput notchedOutline) */
        inputBorder: "var(--inputBorder, #575757)",
        /** Disabled form input border */
        inputBorderDisabled: "var(--inputBorderDisabled, #a1a1a1)",

        /** Standard button background */
        buttonBackground: "var(--buttonBackground, #ffffff)",
        /** Standard button background on hover */
        buttonBackgroundHover: "var(--buttonBackgroundHover, #1a72c4)",
        /** Standard button background when disabled */
        buttonBackgroundDisabled: "var(--buttonBackgroundDisabled, #c6c6c6)",

        /** Standard button border */
        buttonBorder: "var(--buttonBorder, #2c2c2c)",
        /** Standard button border on hover */
        buttonBorderHover: "var(--buttonBorderHover, #ffffff)",
        /** Standard button border when disabled */
        buttonBorderDisabled: "var(--buttonBorderDisabled, #7c7c7c)",

        /** Standard button foreground text */
        buttonForeground: "var(--buttonForeground, #1a72c4)",
        /** Standard button foreground text on hover */
        buttonForegroundHover: "var(--buttonForegroundHover, #ffffff)",
        /** Standard button foreground text when disabled */
        buttonForegroundDisabled: "var(--buttonForegroundDisabled, #575757)",

        /** Standard button icon */
        buttonIcon: "var(--buttonIcon, #1a72c4)",
        /** Standard button icon on hover */
        buttonIconHover: "var(--buttonIconHover, #ffffff)",
        /** Standard button icon when disabled */
        buttonIconDisabled: "var(--buttonIconDisabled, #575757)",

        /** Background fill for emphasized call-to-action buttons */
        emphasizedButtonBackground: "var(--emphasizedButtonBackground, #1a72c4)",
        /** Emphasized button background on hover */
        emphasizedButtonBackgroundHover: "var(--emphasizedButtonBackgroundHover, #e3eff9)",
        /** Emphasized button background when disabled */
        emphasizedButtonBackgroundDisabled: "var(--emphasizedButtonBackgroundDisabled, #b5d3ee)",

        /** Emphasized button border */
        emphasizedButtonBorder: "var(--emphasizedButtonBorder, #1a72c4)",
        /** Emphasized button border on hover */
        emphasizedButtonBorderHover: "var(--emphasizedButtonBorderHover, #1a72c4)",
        /** Emphasized button border when disabled */
        emphasizedButtonBorderDisabled: "var(--emphasizedButtonBorderDisabled, #b5d3ee)",

        /** Foreground text within emphasized buttons */
        emphasizedButtonForeground: "var(--emphasizedButtonForeground, #ffffff)",
        /** Emphasized button foreground on hover */
        emphasizedButtonForegroundHover: "var(--emphasizedButtonForegroundHover, #135593)",
        /** Emphasized button foreground when disabled */
        emphasizedButtonForegroundDisabled: "var(--emphasizedButtonForegroundDisabled, #135593)",

        /** Emphasized button icon */
        emphasizedButtonIcon: "var(--emphasizedButtonIcon, #ffffff)",
        /** Emphasized button icon on hover */
        emphasizedButtonIconHover: "var(--emphasizedButtonIconHover, #1a72c4)",
        /** Emphasized button icon when disabled */
        emphasizedButtonIconDisabled: "var(--emphasizedButtonIconDisabled, #135593)",

        /** Hover background for list items, menu rows, and clickable cells */
        itemHover: "var(--itemHoverBackground, #89b8e4)",
        /** Selected background for active list rows, navigation items, and tree nodes */
        itemSelected: "var(--itemSelectedBackground, #e3eff9)",

        /** Loading bar track fill */
        loadingBarBackground: "var(--loadingBarBackground, #b5d3ee)",
    },

    // Icons
    icon: {
        accentBackground: "var(--accentIconBackground, #ffffff)",
        accentBackgroundHover: "var(--accentIconBackgroundHover, #ffffff)",
        accentBorder: "var(--accentIconBorder, #2c2c2c)",
        accentBorderHover: "var(--accentIconBorderHover, #2c2c2c)",
        accentForeground: "var(--accentIconForeground, #1a72c4)",
        accentForegroundHover: "var(--accentIconForegroundHover, #1a72c4)",
        disabledFill: "var(--disabledIconFill, #323232)",
    },

    // Tabs
    tabs: {
        primaryForeground: "var(--tabPrimaryForeground, #191919)",
        secondaryForeground: "var(--tabSecondaryForeground, #1a72c4)",
    },

    // Inline Table / Grid
    table: {
        headerBackground: "var(--inlineTableHeaderBackground, #c6c6c6)",
        rowBackground: "var(--inlineTableRowBackground, #ebebeb)",
        border: "var(--inlineTableBorder, #a1a1a1)",
        rowSelectedBackground: "var(--attributeTableRowSelectedBackground, #1a72c4)",
        rowSelectedHoverBackground: "var(--attributeTableRowSelectedHoverBackground, #3c88cf)",
        rowSelectedHoverForeground: "var(--attributeTableRowSelectedHoverForeground, #ffffff)",
    },

    // Status Feedback & Validation Alerts
    status: {
        // Red / Error
        errorBg: "var(--alertRedBackground, #b22222)",
        errorBgHover: "var(--alertRedBackgroundHover, #ffffff)",
        errorBorder: "var(--alertRedBorder, #b22222)",
        errorBorderHover: "var(--alertRedBorderHover, #b22222)",
        errorFg: "var(--alertRedForeground, #ffffff)",
        errorFgHover: "var(--alertRedForegroundHover, #b22222)",
        errorIcon: "var(--alertRedIcon, #ffffff)",
        errorIconHover: "var(--alertRedIconHover, #b22222)",

        // Amber / Warning
        warningBg: "var(--alertAmberBackground, #bf5300)",
        warningBgHover: "var(--alertAmberBackgroundHover, #ffffff)",
        warningBorder: "var(--alertAmberBorder, #bf5300)",
        warningBorderHover: "var(--alertAmberBorderHover, #bf5300)",
        warningFg: "var(--alertAmberForeground, #ffffff)",
        warningFgHover: "var(--alertAmberForegroundHover, #bf5300)",
        warningIcon: "var(--alertAmberIcon, #ffffff)",
        warningIconHover: "var(--alertAmberIconHover, #bf5300)",

        // Green / Success
        successBg: "var(--alertGreenBackground, #008040)",
        successBgHover: "var(--alertGreenBackgroundHover, #ffffff)",
        successBorder: "var(--alertGreenBorder, #008040)",
        successBorderHover: "var(--alertGreenBorderHover, #008040)",
        successFg: "var(--alertGreenForeground, #ffffff)",
        successFgHover: "var(--alertGreenForegroundHover, #008040)",
        successIcon: "var(--alertGreenIcon, #ffffff)",
        successIconHover: "var(--alertGreenIconHover, #008040)",

        // Gray / Info
        infoBg: "var(--alertGrayBackground, #2c2c2c)",
        infoBgHover: "var(--alertGrayBackgroundHover, #ffffff)",
        infoBorder: "var(--alertGrayBorder, #2c2c2c)",
        infoBorderHover: "var(--alertGrayBorderHover, #2c2c2c)",
        infoFg: "var(--alertGrayForeground, #ffffff)",
        infoFgHover: "var(--alertGrayForegroundHover, #2c2c2c)",
        infoIcon: "var(--alertGrayIcon, #ffffff)",
        infoIconHover: "var(--alertGrayIconHover, #2c2c2c)",

        // Alert Disabled State
        disabledBg: "var(--alertBackgroundDisabled, #2c2c2c)",
        disabledBorder: "var(--alertBorderDisabled, #2c2c2c)",
        disabledFg: "var(--alertForegroundDisabled, #a1a1a1)",
        disabledIcon: "var(--alertIconDisabled, #a1a1a1)",

        // Error Helper Text & Icon
        errorHelperTextBg: "var(--errorHelperTextBackground, #ffffff)",
        errorHelperTextFg: "var(--errorHelperTextForeground, #b22222)",
        errorIconBg: "var(--errorIconBackground, #b22222)",
        errorIconFg: "var(--errorIconForeground, #ffffff)",
    },

    // Geometry & Shape Tokens
    shape: {
        /** Standard corner radius for buttons, input fields, chips, and list items */
        borderRadius: "var(--borderRadius, 4px)",
        /** Micro corner radius for small badges, tags, and inner items */
        borderRadiusSm: "var(--borderRadiusSm, 2px)",
        /** Extended corner radius for cards, floating panels, and dialogs */
        borderRadiusLarge: "var(--borderRadiusLarge, 8px)",
        /** Alias for borderRadiusLarge */
        borderRadiusLg: "var(--borderRadiusLg, 8px)",
        /** Fully rounded circular avatar or round button radius */
        borderRadiusRound: "50%",
        /** Pill radius for status capsules and rounded badges */
        borderRadiusPill: "9999px",
    },
    spacing: {
        xxs: "var(--spacingXxs, 2px)", xs: "var(--spacingXs, 4px)", sm: "var(--spacingSm, 8px)",
        md: "var(--spacingMd, 12px)", lg: "var(--spacingLg, 16px)", xl: "var(--spacingXl, 24px)",
    },
} as const;

export type UiTokens = typeof UI_TOKENS;
```

---

### 3. Typography Tokens (`src/tokens/typography.ts`)

Typography tokens standardize font stacks, scale, line heights, and weights across both VertiGIS Web components and Workflow form elements.

#### Host Shell Inheritance & Zero Redundant CSS Declarations
The host application shell (`.vsw-app`) strictly owns and injects the global font stack (`var(--defaultFont)`).
- **Prohibited**: NEVER declare `font-family: var(--defaultFont);` on child component CSS classes (e.g. `.Item-title`, `.Item-caption`). It is inherited by default from the shell; repeating it creates CSS bloat and specificity noise.
- **MUI `<Typography>` Deletes Boilerplate**: Prefer `@mui/material` `<Typography variant="...">` (`caption`, `body2`, `subtitle2`, etc.) in JSX. Doing so automatically adopts shell font inheritance, line-height, and font scaling without writing a single line of custom CSS for text.

```typescript
/**
 * Typography Tokens for VertiGIS Studio Web SDK
 * Provides standardized font stacks, modular scales, weights, and line heights.
 */

export const TYPOGRAPHY_TOKENS = {
    // Modular Font Scale (Rem-based) with MUI Variant & T-Shirt Aliases
    fontSize: {
        // Standard MUI variants
        caption: "0.75rem",
        body2: "0.875rem",
        body1: "1rem",
        subtitle2: "0.875rem",
        subtitle1: "1.25rem",
        h6: "1.25rem",
        h5: "1.5rem",
        overline: "0.625rem",

        // T-shirt size aliases
        xs: "0.75rem",
        sm: "0.875rem",
        base: "1rem",
        lg: "1.25rem",
        xl: "1.5rem",
        xxl: "2rem",
    },

    // Font Weights
    fontWeight: {
        /** Regular copy */
        regular: 400,
        /** Form labels, table headers, emphasized buttons */
        medium: 500,
        /** Headers, card titles, active tab states */
        semibold: 600,
        /** Major headers, metric figures, alert callouts */
        bold: 700,
    },

    // Line Heights
    lineHeight: {
        /** Compact headings, table titles */
        tight: 1.2,
        /** Standard reading body text */
        normal: 1.5,
        /** Long-form documentation and instructions */
        relaxed: 1.75,
    },
} as const;

export type TypographyTokens = typeof TYPOGRAPHY_TOKENS;
```

---

### 4. Color-Mix Utilities & Unified Barrel Export (`src/tokens/index.ts`)

The CSS Color Module Level 5 `color-mix()` specification provides native browser capability to blend colors dynamically. In VertiGIS applications, this enables:
1. **Adaptive Overlays**: Generating a 12% opacity accent fill for selected table rows that automatically adapts whether the underlying accent is blue, green, or orange, in both light and dark themes.
2. **Dynamic Hover States**: Lightening or darkening a surface without hardcoding an arbitrary hex shade.

```typescript
/**
 * Unified Design Tokens and Theming Utilities Barrel Export
 */

export * from "./ui";
export * from "./typography";

/**
 * Generates a CSS color-mix() string blending a base token with transparency.
 * Ideal for dynamic hover overlays, active selection fills, and focus halos.
 *
 * @example
 * // Returns: "color-mix(in srgb, var(--primaryAccent, #007ac2) 15%, transparent)"
 * backgroundColor: alphaMix(UI_TOKENS.accent.primary, 15)
 *
 * @param token - The CSS variable or color string
 * @param opacityPercent - The target opacity percentage (0 - 100)
 * @returns CSS color-mix string supported by modern browsers
 */
export function alphaMix(token: string, opacityPercent: number): string {
    const clamped = Number.isFinite(opacityPercent)
        ? Math.max(0, Math.min(100, Math.round(opacityPercent)))
        : 0;
    return `color-mix(in srgb, ${token} ${clamped}%, transparent)`;
}

/**
 * Generates a CSS color-mix() string blending two tokens together.
 * Ideal for creating tinted surfaces, card backgrounds, or muted hover states.
 *
 * @example
 * // Returns: "color-mix(in srgb, var(--primaryAccent, #007ac2) 8%, var(--primaryBackground, #ffffff))"
 * backgroundColor: surfaceMix(UI_TOKENS.surface.primary, UI_TOKENS.accent.primary, 8)
 *
 * @param baseToken - The base surface token
 * @param overlayToken - The tinting color token
 * @param tintPercent - The weight of the overlay color (0 - 100)
 * @returns CSS color-mix string supported by modern browsers
 */
export function surfaceMix(baseToken: string, overlayToken: string, tintPercent: number): string {
    const clamped = Number.isFinite(tintPercent)
        ? Math.max(0, Math.min(100, Math.round(tintPercent)))
        : 0;
    return `color-mix(in srgb, ${overlayToken} ${clamped}%, ${baseToken})`;
}
```

#### Applied Component Styling Example
```tsx
import * as React from "react";
import { Box, Typography, Button, Stack } from "@mui/material";
import { UI_TOKENS, alphaMix } from "../tokens";
import "./FeatureCard.css";

export function FeatureCard({ title, description, isSelected }: { title: string; description: string; isSelected: boolean }) {
    return (
        <Box className={isSelected ? "FeatureCard FeatureCard--selected" : "FeatureCard"}>
            <Stack spacing={1}>
                <Typography variant="h6">
                    {title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    {description}
                </Typography>
                <Button variant="contained" color="primary">
                    View Details
                </Button>
            </Stack>
        </Box>
    );
}
```


The card's layout and states live in `FeatureCard.css`; `color-mix()` tints the inherited surface:

```css
.FeatureCard {
    padding: var(--spacingLg, 16px);
    border: 1px solid var(--primaryBorder, #e0e0e0);
    border-radius: var(--borderRadius, 4px);
    transition: background-color 150ms ease, border-color 150ms ease;
}

.FeatureCard:hover {
    border-color: var(--primaryAccentHover, #005a91);
    background-color: color-mix(in srgb, var(--primaryAccent, #007ac2) 5%, transparent);
}

.FeatureCard--selected {
    border-color: var(--primaryAccent, #007ac2);
    background-color: color-mix(in srgb, var(--primaryAccent, #007ac2) 10%, transparent);
}
```

---

<span id="dynamic-dual-theme-system"></span>
## Dynamic Dual-Theme System

While CSS variables automatically update visual styles in CSS-in-JS and MUI `sx` props, complex applications require **programmatic theme awareness**:
- **Plotly.js Charts**: Require setting `template: "plotly_dark"` vs `"plotly_white"`, coordinate font fills, and axis line colors.
- **HTML5 Canvas & GIS Overlays**: Elevation profile charts, custom symbol renderers, and heatmaps render via 2D canvas context (`ctx.fillStyle`, `ctx.strokeStyle`), which cannot parse CSS stylesheets.
- **Client-Side PDF Exports (jsPDF)**: Generating vector or tabular PDF reports requires static RGB/hex colors matching the active theme.
- **Conditional Layout Rendering**: Altering imagery assets, vector map basemaps, or icon variants based on theme mode.

---

### 1. Standalone Synchronous Theme Detection (`src/utils/isDarkTheme.ts`)

For non-React, non-CSS contexts (such as web workers, canvas generators, and export services), `isDarkTheme()` provides a robust, 3-tier cascade:

1. **Tier 1: DOM Attribute & Class Inspection**: Inspects `.vsw-app`, `document.documentElement`, and `document.body` for official VertiGIS and enterprise theme markers (`theme-dark`, `vsw-theme-dark`, `data-theme="dark"`).
2. **Tier 2: Shell Token then Background Luminance**: Reads computed `--primaryBackground` first, then the host root's computed background color, and calculates perceived luminance using the ITU-R BT.709 standard (`(0.2126*R + 0.7152*G + 0.0722*B) / 255 < 0.5`). This prevents an OS dark preference from overriding a light VertiGIS shell.
3. **Tier 3: OS / Media Query Preference**: Falls back to the user's operating system preference `(prefers-color-scheme: dark)`.

```typescript
/**
 * Standalone synchronous utility to detect if the active VertiGIS application theme is dark.
 * Usable in non-React and non-CSS contexts (e.g., Plotly charts, HTML Canvas, jsPDF, Web Workers).
 *
 * @returns boolean - true if the active theme is dark, false if light.
 */
export function isDarkTheme(): boolean {
    // 0. Guard against SSR or headless environments without DOM access
    if (typeof window === "undefined" || typeof document === "undefined") {
        return false;
    }

    // 1. Tier 1: Check classes and data-theme attributes on VertiGIS root or body
    const rootElement = document.querySelector(".vsw-app") || document.documentElement || document.body;

    if (
        rootElement.classList.contains("theme-dark") ||
        rootElement.classList.contains("vsw-theme-dark") ||
        rootElement.getAttribute("data-theme") === "dark" ||
        document.body.classList.contains("theme-dark") ||
        document.body.getAttribute("data-theme") === "dark"
    ) {
        return true;
    }

    if (
        rootElement.classList.contains("theme-light") ||
        rootElement.classList.contains("vsw-theme-light") ||
        rootElement.getAttribute("data-theme") === "light" ||
        document.body.classList.contains("theme-light") ||
        document.body.getAttribute("data-theme") === "light"
    ) {
        return false;
    }

    // 2. Tier 2: Prefer the shell token, then sample the computed root background
    try {
        const styles = window.getComputedStyle(rootElement);
        const tokenTheme = inferDarkColor(styles.getPropertyValue("--primaryBackground"));
        if (tokenTheme !== undefined) return tokenTheme;

        const backgroundTheme = inferDarkColor(styles.backgroundColor);
        if (backgroundTheme !== undefined) return backgroundTheme;
    } catch {
        // Fallback to media query if DOM inspection encounters permission/context issues
    }

    // 3. Tier 3: Fallback to OS / browser color scheme preference
    return Boolean(window.matchMedia?.("(prefers-color-scheme: dark)").matches);
}

function inferDarkColor(value: string): boolean | undefined {
    const color = value.trim();
    const hex = color.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i)?.[1];
    const rgb = color.match(/^rgba?\(\s*([\d.]+)[, ]+\s*([\d.]+)[, ]+\s*([\d.]+)/i);
    const channels = hex
        ? [0, 2, 4].map(index => parseInt((hex.length === 3 ? [...hex].map(c => c + c).join("") : hex).slice(index, index + 2), 16))
        : rgb?.slice(1, 4).map(Number);
    if (!channels?.every(Number.isFinite)) return undefined;
    const [r, g, b] = channels;
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 < 0.5;
}
```

---

### 2. Canonical Reactive Hook (`src/hooks/useIsDarkTheme.ts`)

In React components, theme switches must trigger immediate re-renders. The `useIsDarkTheme` hook combines `MutationObserver` on the root container with media query listeners:

```typescript
import { useState, useEffect } from "react";
import { isDarkTheme } from "../utils/isDarkTheme";

/**
 * Reactive React hook that tracks the VertiGIS application theme.
 * Listens to DOM mutations on .vsw-app / body and OS media query changes.
 *
 * @returns boolean - true if the active theme is dark, false if light.
 */
export function useIsDarkTheme(): boolean {
    const [isDark, setIsDark] = useState<boolean>(() => isDarkTheme());

    useEffect(() => {
        const updateTheme = () => {
            const current = isDarkTheme();
            setIsDark(prev => (prev !== current ? current : prev));
        };

        // Run initial check on mount
        updateTheme();

        // 1. MutationObserver on root container for class, data-theme, and style changes
        const targetNode = document.querySelector(".vsw-app") || document.documentElement || document.body;
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (
                    mutation.type === "attributes" &&
                    (mutation.attributeName === "class" ||
                     mutation.attributeName === "data-theme" ||
                     mutation.attributeName === "style")
                ) {
                    updateTheme();
                    break;
                }
            }
        });

        observer.observe(targetNode, {
            attributes: true,
            attributeFilter: ["class", "data-theme", "style"],
        });

        // If targetNode is not document.body, also observe document.body
        if (targetNode !== document.body && document.body) {
            observer.observe(document.body, {
                attributes: true,
                attributeFilter: ["class", "data-theme"],
            });
        }

        // 2. Listen to system preference changes (safely guarded for headless test runners and SSR)
        const mediaQuery =
            typeof window !== "undefined" && typeof window.matchMedia === "function"
                ? window.matchMedia("(prefers-color-scheme: dark)")
                : null;
        const handleMediaChange = () => updateTheme();

        if (mediaQuery) {
            if (mediaQuery.addEventListener) {
                mediaQuery.addEventListener("change", handleMediaChange);
            } else if ("addListener" in mediaQuery) {
                // Support for legacy WebView interfaces
                (mediaQuery as { addListener: (cb: () => void) => void }).addListener(handleMediaChange);
            }
        }

        // 3. Cleanup observer and listeners on unmount
        return () => {
            observer.disconnect();
            if (mediaQuery) {
                if (mediaQuery.removeEventListener) {
                    mediaQuery.removeEventListener("change", handleMediaChange);
                } else if ("removeListener" in mediaQuery) {
                    (mediaQuery as { removeListener: (cb: () => void) => void }).removeListener(handleMediaChange);
                }
            }
        };
    }, []);

    return isDark;
}
```

---

### 3. Two-Tier Theming Architecture: VertiGisThemeProvider & Host Design Tokens

In VertiGIS Studio Web, branding and visual identity are owned by the **host application shell** (`.vsw-app`) via the `branding` service in `app-config.json` and Designer. The host governs cosmetics: components inherit surface, elevation, borders and typography through MUI's `ThemeProvider` and the host CSS custom properties, and keep their own `sx` / `style` to layout, geometry and 8px-grid spacing (SKILL.md Rule 2).

#### Tier 1: Standard Material UI Controls (`VertiGisThemeProvider`)
Standard MUI controls (`<Radio>`, `<Checkbox>`, `<Button>`, `<Typography>`, `<Dialog>`, `<Switch>`, `<TextField>`, `<Select>`, `<Card>`, `<Paper>`) must be wrapped in a shared or scoped `VertiGisThemeProvider` driven by `useIsDarkTheme()`. `src/tokens/muiTheme.ts` is the single home for cosmetic styling: component defaults and state styles live in `components.*.styleOverrides`, consuming `UI_TOKENS.*` CSS-variable tokens. Leave `spacing` unset so MUI's default 8px unit applies (`p: 1` = 8px).

`src/tokens/muiTheme.ts`
```ts
import { createTheme, type Theme } from "@mui/material/styles";

import { UI_TOKENS } from "./ui";

export function getVertiGisPortalContainer(): HTMLElement | null {
    if (typeof document === "undefined") return null;
    return document.querySelector<HTMLElement>(".vsw-app") ?? document.body;
}

/**
 * The only home for cosmetic styling. Components keep sx to layout, geometry and 8px-grid spacing,
 * inherit everything else from the host shell's CSS custom properties, and express state as
 * data attributes (e.g. <Card data-status={status}>) that are styled here.
 */
export function createVertiGisTheme(isDark: boolean): Theme {
    return createTheme({
        palette: { mode: isDark ? "dark" : "light" },
        typography: { fontFamily: "inherit" },
        components: {
            MuiPopover: {
                defaultProps: { container: getVertiGisPortalContainer },
            },
            MuiCheckbox: {
                defaultProps: { size: "small" },
                styleOverrides: { root: { "&.Mui-checked": { color: UI_TOKENS.accent.primary } } },
            },
            MuiRadio: {
                defaultProps: { size: "small" },
                styleOverrides: { root: { "&.Mui-checked": { color: UI_TOKENS.accent.primary } } },
            },
            MuiButton: {
                defaultProps: { size: "small" },
                styleOverrides: { root: { textTransform: "none", fontWeight: 600 } },
            },
            MuiCard: {
                defaultProps: { variant: "outlined" },
                styleOverrides: {
                    root: {
                        position: "relative",
                        borderRadius: UI_TOKENS.shape.borderRadiusLarge,
                        backgroundColor: UI_TOKENS.surface.primary,
                        border: `1px solid ${UI_TOKENS.border.primary}`,
                        borderLeftWidth: 4,
                        borderLeftColor: "transparent",
                        boxShadow: "none",
                        '&.StatusCard-root[data-status="Open"], &.StatusCard-root[data-status="Opened"]': { borderLeftColor: UI_TOKENS.status.warningFg },
                        '&.StatusCard-root[data-status="In Progress"]': { borderLeftColor: UI_TOKENS.accent.primary },
                        '&.StatusCard-root[data-status="Completed"]': { borderLeftColor: UI_TOKENS.status.successFg },
                        '&.StatusCard-root[data-status="Closed"], &.StatusCard-root[data-status="Archived"]': { borderLeftColor: UI_TOKENS.text.secondary },
                    },
                },
            },
            MuiPaper: {
                styleOverrides: {
                    root: { backgroundImage: "none" },
                    outlined: { borderColor: UI_TOKENS.border.primary, borderRadius: UI_TOKENS.shape.borderRadius },
                },
            },
        },
    });
}

export default createVertiGisTheme;
```

`src/tokens/VertiGisThemeProvider.tsx`
```tsx
import * as React from "react";
import { ThemeProvider } from "@mui/material/styles";

import { useIsDarkTheme } from "../hooks/useIsDarkTheme";
import { createVertiGisTheme } from "./muiTheme";

/** Applies src/tokens/muiTheme.ts, following the shell's light/dark mode. */
export function VertiGisThemeProvider({ children }: { children: React.ReactNode }): React.ReactElement {
    const isDark = useIsDarkTheme();
    const theme = React.useMemo(() => createVertiGisTheme(isDark), [isDark]);
    return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}

export default VertiGisThemeProvider;
```

##### Declarative State via Data Attributes
Components describe state, the theme decides how it looks. Put the value on the element as a data attribute; the matching `&[data-status="..."]` selector lives in `muiTheme.ts` (see `MuiCard` above):

```tsx fragment
<Card data-status={record.status}>
    <CardContent>
        <Stack spacing={0.5}>
            <Typography variant="subtitle2">{record.title}</Typography>
            <Typography variant="caption" color="text.secondary">{record.status}</Typography>
        </Stack>
    </CardContent>
</Card>
```

`MuiPopover` containment is mandatory because MUI menus render through portals. Keeping the portal inside `.vsw-app` preserves VertiGIS token inheritance and stacking context. Menu text, hover, and selected states should remain semantic MUI palette states; never force token colours with `!important`.

##### The Crash Anti-Pattern: Why `augmentColor()` Fails
Passing raw CSS variables into `palette.primary.main` or `palette.error.main` causes MUI to crash:
```typescript bad
// ❌ CRASH ANTI-PATTERN: Passing CSS variables into palette.*.main
export function createBrokenMuiTheme(): Theme {
    return createTheme({
        palette: {
            primary: { main: "var(--primaryAccent, #007ac2)" }, // CRASHES!
        },
    });
}
```
**Why this crashes**: Material UI's `createTheme()` runs `augmentColor()` to automatically compute hover and focus shades using mathematical color calculations (`decomposeColor` -> `lighten`/`darken`). Because `var(...)` is an unresolvable string in JavaScript, `decomposeColor()` throws:
```text
Error: MUI: Unsupported `var(--primaryAccent, #007ac2)` color.
The following formats are supported: #nnn, #nnnnnn, rgb(), rgba(), hsl(), hsla(), color().
```
**The Fix**: Keep `palette.mode: isDark ? "dark" : "light"` clean, and attach CSS custom properties to component `styleOverrides` (e.g. `MuiRadio: { styleOverrides: { root: { "&.Mui-checked": { color: "var(--primaryAccent)" } } } }`).

##### MUI v7 Modern Conventions & Host Shell Safety
1. **Strict Ban on `<CssBaseline />`**: Never mount `<CssBaseline />` inside custom extensions or under `VertiGisThemeProvider`. Doing so injects global CSS resets (`* { box-sizing: border-box; }`, `body { margin: 0; }`, font resets) that collide with `.vsw-app`, break Esri map canvas pan/zoom calculations, and cause host layout regressions.
2. **Standardized `slotProps` API**: MUI v7 deprecated nested component props (`PaperProps`, `inputProps`, `BackdropProps`). Always use standardized `slotProps`:
   ```tsx
   // ✅ Standardized MUI v7 slotProps:
   <Dialog slotProps={{ paper: { className: "MonitoringReportDialog-paper" } }} ... />
   <TextField label="Report title" slotProps={{ input: { readOnly: true } }} ... />
   ```
3. **Semantic Palette Props over Custom CSS**: Leverage built-in typography palette awareness rather than micro-injecting CSS classes:
   ```tsx
   // ✅ Automatically flips between light/dark secondary colors:
   <Typography variant="caption" color="text.secondary">Subtitle text</Typography>
   ```
4. **Type-Safe Layout Dictionaries (`SxProps<Theme>`)**: When custom MUI layout properties are needed beyond standard Stack spacing, isolate them into typed dictionaries at the top of the file. Cosmetics belong on the container component (`<Paper variant="outlined">`) or in `muiTheme.ts`, not in `styles`:
   ```typescript
   import type { SxProps, Theme } from "@mui/material/styles";

   const styles: Record<string, SxProps<Theme>> = {
       progressBox: {
           display: "flex",
           alignItems: "center",
           gap: 1.5,
           p: 1.5,
       },
   };
   ```

#### Tier 2: Non-MUI Chrome & Custom Layout Containers
For non-MUI DOM elements (`div`, `header`, `aside`, card chrome, borders, scroll containers), consume official host CSS design tokens directly in co-located namespaced CSS (`ComponentName.css`):
```css
.MonitoringCard {
    border: var(--borderWidth, 1px) solid var(--primaryBorder, #e0e0e0);
    border-radius: var(--borderRadius, 4px);
}
```

#### Tier 3: Non-CSS Rendering Pipelines (Charts & PDF)
Standalone renderers (Nivo Line charts, Plotly, HTML5 Canvas, jsPDF) read JavaScript token values directly via `UI_TOKENS` and synchronize with `useIsDarkTheme()` or `isDarkTheme()`.

#### Why `@vertigis/web/ui` Controls Crash Outside the Shell
Attempting to import UI controls (`Button`, `Typography`, `DynamicIcon`, `Box`, `TitleBar`) from `@vertigis/web/ui` introduces a separate critical vulnerability:
* These internal components call `useUIContext()` under the hood.
* In **unit tests (`vitest run`)**, custom modals, detached portal roots, or before the host shell fully mounts, `UIContext` is `undefined`.
* The component immediately crashes with:
  ```text
  TypeError: Cannot read properties of undefined (reading 'translate')
  ```
* Never import UI controls from `@vertigis/web/ui`. Use standard `@mui/material` controls wrapped in `VertiGisThemeProvider`.

---

### 4. Co-Located Namespaced CSS Architecture (`ComponentName.css`)

The gold standard for styling custom VertiGIS Studio Web extensions aligns with the official SDK starter template architecture (as seen in `template/src/components/PointsOfInterest/PointsOfInterest.css`).

#### 1. Co-Location Pattern
Every React view (`ComponentName.tsx`) is accompanied by a co-located CSS file (`ComponentName.css`) in the same folder:
```
src/components/ListHeader/
├── ListHeader.tsx        # Pure JSX layout and component logic
├── ListHeader.css        # Focused, namespaced component styling
└── index.ts
```

#### 2. Strict Class Namespacing (Host Shell Safety)
The VertiGIS Web SDK Webpack pipeline compiles CSS using `style-loader` and `css-loader` without CSS Modules class hashing. This means **every CSS rule is injected directly into `<head><style>` as a global page style**.

* **Strictly Prohibited (Generic Class Names)**:
  `.header`, `.title`, `.item`, `.button`, `.card`, `.active`, `.disabled`, `.content`.
  *(These collide with the VertiGIS host shell `.vsw-app`, ArcGIS JS API widgets, or other custom libraries).*
* **Mandatory (Component-Namespaced Class Names)**:
  Prefix every class with the component name or BEM convention:
  `.ListHeader`, `.ListHeader-title`, `.ListHeader-toolbar`, `.ListHeader-button`
  *(or BEM: `.list-header`, `.list-header__title`, `.list-header__button--active`)*.

#### 3. Minimal Style Injection & Clean Separation
* Keep JSX clean and declarative:
  ```tsx
  // ✅ Clean, readable JSX free from inline sx bloat
  import * as React from "react";
  import "./ListHeader.css";

  export function ListHeader({ title, count }: { title: string; count: number }) {
      return (
          <header className="ListHeader">
              <h3 className="ListHeader-title">{title}</h3>
              <span className="ListHeader-badge">{count}</span>
          </header>
      );
  }
  ```
* Consume VertiGIS design tokens directly in the co-located CSS file:
  ```css
  /* ListHeader.css */
  .ListHeader {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--spacingMd, 12px) var(--spacingLg, 16px);
      border-bottom: 1px solid var(--primaryBorder, #e0e0e0);
  }

  .ListHeader-title {
      margin: 0;
      font-size: 1rem;
      font-weight: 500;
  }

  .ListHeader-badge {
      display: inline-flex;
      align-items: center;
      padding: var(--spacingXxs, 2px) var(--spacingSm, 8px);
      font-size: 0.75rem;
      border-radius: var(--borderRadius, 4px);
      background-color: var(--secondaryBackground, #f5f5f5);
      color: var(--secondaryForeground, #666666);
  }
  ```

#### 4. When to Use Native `style={{ ... }}` vs. CSS Classes
| Styling Need | Mechanism | Example |
| :--- | :--- | :--- |
| **Component chrome, padding, colors, borders, hover states** | **Co-located `.css`** | `.ListHeader { background: var(--primaryBackground); }` |
| **Dynamic runtime calculations** (pixel coords, percentages) | **Native `style={{ ... }}`** | `<div style={{ width: `${percentComplete}%` }} />` |
| **Theme colors & dynamic dark/light values** | **CSS Variables** | `var(--primaryBackground, #ffffff)` with safe fallback |
| **Derived tints and overlays** | **`color-mix()`** | `color-mix(in srgb, var(--primaryAccent) 15%, transparent)` |
| **Inline `sx` sprawl** | **STRICTLY BANNED** | Avoid scattering verbose `sx={{ ... }}` objects on general elements. |

#### 5. Strict Ban on Token Re-Aliasing & Global `:root` Pollution

##### The Anti-Pattern: Shadow Tokens & Multi-Hop Indirection
A common pitfall when authoring custom widget CSS is creating local shadow variables or re-aliasing official VertiGIS design tokens through intermediate layers:

```css bad
/* ❌ DANGEROUS ANTI-PATTERN: Multi-hop indirection & global :root pollution */
:root {
    --color-background: var(--primaryBackground);
    --color-foreground: var(--primaryForeground);
    --color-card: var(--secondaryBackground);
    
    /* Layer 2 indirection */
    --monitoring-bg: var(--color-background);
    --monitoring-surface: var(--color-card);
    --monitoring-text: var(--primaryForeground);
}

.monitoring-card {
    background: var(--monitoring-bg);
    color: var(--monitoring-text);
}
```

##### Why This Is Harmful
1. **Triple Indirection & Cognitive Friction**: To find out what color `--monitoring-bg` resolves to, a developer must trace `--monitoring-bg` → `--color-background` → `var(--primaryBackground)` → host `.vsw-app`. This unnecessary hop makes stylesheets difficult to read, audit, and refactor.
2. **Design System Fragmentation**: When intermediate aliases exist, developers and AI agents invent conflicting names (`--monitoring-text`, `--color-foreground`, `--card-text`). Different components in the same codebase end up consuming different alias layers, breaking consistent theming across light and dark modes.
3. **Global Scope Pollution via `:root`**: Custom libraries are embedded guest widgets running inside a host VertiGIS Studio Web shell (`.vsw-app`). Injecting a `:root { ... }` block in a custom library's CSS injects global variables at the `<html>` document root, risking collisions or unwanted overrides with the host shell or other third-party extensions.
4. **DevTools Obfuscation**: In browser DevTools, inspecting an element displays a deep chain of uncomputed CSS variables instead of the active design token and its computed value.

##### The Clean Architecture: Direct Host Token Consumption
Consume the official VertiGIS host CSS variables directly in component rules, always accompanied by a WCAG AA fallback value:

```css
/* ✅ CLEAN ARCHITECTURE: Direct token consumption in namespaced CSS */
.MonitoringCard {
    border: 1px solid var(--primaryBorder, #e0e0e0);
    border-radius: var(--borderRadius, 4px);
}

.MonitoringCard-secondary {
    background: var(--secondaryBackground, #f5f5f5);
    color: var(--secondaryForeground, #666666);
}
```

##### Permissible vs. Prohibited CSS Custom Properties
| Category | Allowed? | Rule & Proper Usage |
| :--- | :---: | :--- |
| **Direct Host Tokens** | ✅ **Mandatory** | Reference directly in properties: `var(--primaryBackground, #ffffff)`, `var(--primaryForeground, #212121)`. |
| **Color Shadow Aliases** (`--color-*`, `--mycomp-bg`) | ❌ **Banned** | Never create intermediate alias layers that mirror host tokens. |
| **Global `:root` Injection** | ❌ **Banned** | Never declare `:root { ... }` in custom library CSS files. |
| **Component Layout Variables** | ✅ **Permissible** | Scoped strictly to the component selector (e.g. `.MonitoringTable { --row-height: 36px; }`), strictly for layout/dimension calculations, never for colors. |

---

### 6. Non-CSS Renderers Integration Patterns

#### A. Plotly.js Dynamic Theming
When embedding charting in GIS widgets, synchronize the chart template, axes, and background colors with `useIsDarkTheme()`. Renderer colors live in a token map, keyed by theme mode:

`src/tokens/chart.ts`
```ts
export const CHART_TOKENS = {
    light: {
        font: "#212121",
        grid: "#e0e0e0",
        axisLine: "#cccccc",
        series: "#007ac2",
        canvasSurface: "#ffffff",
        canvasGrid: "#eeeeee",
        canvasSeries: "#007ac2",
        canvasLabel: "#666666",
    },
    dark: {
        font: "#f5f5f5",
        grid: "#333333",
        axisLine: "#555555",
        series: "#29b6f6",
        canvasSurface: "#1e1e1e",
        canvasGrid: "#333333",
        canvasSeries: "#4fc3f7",
        canvasLabel: "#aaaaaa",
    },
} as const;
```

```tsx
import * as React from "react";
import Plot from "react-plotly.js";
import { useIsDarkTheme } from "../hooks/useIsDarkTheme";
import { CHART_TOKENS } from "../tokens/chart";

interface ElevationChartProps {
    distances: number[];
    elevations: number[];
}

export function ElevationChart({ distances, elevations }: ElevationChartProps): React.ReactElement {
    const isDark = useIsDarkTheme();
    const colors = isDark ? CHART_TOKENS.dark : CHART_TOKENS.light;

    const layout = React.useMemo(() => ({
        template: isDark ? "plotly_dark" : "plotly_white",
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        margin: { t: 24, r: 20, l: 40, b: 36 },
        font: {
            color: colors.font,
            family: "Roboto, Helvetica, Arial, sans-serif",
            size: 12,
        },
        xaxis: {
            gridcolor: colors.grid,
            linecolor: colors.axisLine,
            title: "Distance (m)",
        },
        yaxis: {
            gridcolor: colors.grid,
            linecolor: colors.axisLine,
            title: "Elevation (m)",
        },
    }), [isDark, colors]);

    return (
        <Plot
            data={[{
                x: distances,
                y: elevations,
                type: "scatter",
                mode: "lines",
                line: { color: colors.series, width: 2 },
            }]}
            layout={layout}
            useResizeHandler
            style={{ width: "100%", height: "100%" }}
        />
    );
}
```

#### B. HTML5 Canvas Dynamic Theming
Canvas graphics cannot read CSS custom properties. Use `isDarkTheme()` to sample theme state before drawing:

```typescript
import { isDarkTheme } from "../utils/isDarkTheme";
import { CHART_TOKENS } from "../tokens/chart";

export function renderProfileCanvas(
    canvas: HTMLCanvasElement,
    profilePoints: Array<{ x: number; y: number }>
): void {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const colors = isDarkTheme() ? CHART_TOKENS.dark : CHART_TOKENS.light;
    const { width, height } = canvas;

    // 1. Clear with transparent or surface fill
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = colors.canvasSurface;
    ctx.fillRect(0, 0, width, height);

    // 2. Draw coordinate gridlines
    ctx.strokeStyle = colors.canvasGrid;
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }

    // 3. Draw GIS profile path
    ctx.strokeStyle = colors.canvasSeries;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    profilePoints.forEach((pt, idx) => {
        if (idx === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
    });
    ctx.stroke();

    // 4. Render axis labels
    ctx.fillStyle = colors.canvasLabel;
    ctx.font = "11px Roboto, sans-serif";
    ctx.fillText("0 m", 8, height - 8);
    ctx.fillText(`${width} m`, width - 40, height - 8);
}
```

#### C. Client-Side PDF Export (jsPDF)
```typescript
import { jsPDF } from "jspdf";
import { isDarkTheme } from "../utils/isDarkTheme";

export function exportInspectionPdf(title: string, records: Array<Record<string, string>>): void {
    const doc = new jsPDF();
    const isDark = isDarkTheme();

    // In PDF exports, enterprise standards typically favor a printable light palette,
    // but executive summary reports can match user preference:
    const bgColor = isDark ? [30, 30, 30] : [255, 255, 255];
    const textColor = isDark ? [240, 240, 240] : [33, 33, 33];
    const accentColor = [0, 122, 194]; // VertiGIS Brand Accent

    doc.setFillColor(bgColor[0], bgColor[1], bgColor[2]);
    doc.rect(0, 0, 210, 297, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.setTextColor(accentColor[0], accentColor[1], accentColor[2]);
    doc.text(title, 14, 22);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.setTextColor(textColor[0], textColor[1], textColor[2]);
    doc.text(`Generated: ${new Date().toLocaleString()} (Theme: ${isDark ? "Dark" : "Light"})`, 14, 30);

    // Format table records...
    doc.save(`Inspection-Report-${Date.now()}.pdf`);
}
```

---

<span id="component-modularity"></span>
## Component Modularity Architecture

Complex web GIS extensions can quickly devolve into massive, unmaintainable "god components" containing 500 to 1,000 lines of mixed concerns: MobX state subscriptions, ArcGIS layer queries, date formatting, tabular layouts, modal popups, and inline styles.

The VertiGIS Web SDK strictly mandates an **anti-god-component decomposition standard**.

### 1. Standard 7-Directory Blueprint

Every production VertiGIS component exceeding trivial complexity should follow the 7-directory structure:

```
src/components/InspectionDashboard/
├── InspectionDashboardModel.ts       # MobX Model (Data, lifecycle, service injections)
├── main.tsx                          # Top-level React View (LayoutElement, ErrorBoundary, < 150 lines)
├── components/                       # Decomposed presentational sub-components
│   ├── DashboardHeader.tsx           # Title, status chips, close actions (< 100 lines)
│   ├── FilterPanel.tsx               # Filter inputs, dropdowns, date pickers (< 120 lines)
│   ├── ResultsTable.tsx              # Tabular results, pagination (< 150 lines)
│   └── ExportDialog.tsx              # Export options modal (< 100 lines)
├── hooks/                            # Custom React hooks for business/UI logic
│   ├── useDashboardData.ts           # Data loading, pagination state, polling (< 100 lines)
│   └── useLayerFilter.ts             # Map layer filtering and highlight sync (< 100 lines)
├── services/                         # Component-scoped services or API clients
│   └── inspectionApiClient.ts        # REST/GraphQL fetch logic (< 150 lines)
├── utils/                            # Zero-dependency pure functions (100% testable)
│   ├── dateCalculations.ts           # Date math, relative time formatting (< 80 lines)
│   └── tableFormatters.ts            # Cell formatting, currency/unit strings (< 80 lines)
├── helpers/                          # ArcGIS API / geometry helpers
│   └── featureGeometryHelpers.ts     # Extent computation, zoom-to-feature logic (< 100 lines)
├── tokens/                           # Component-specific token aliases (if needed)
│   └── dashboardTokens.ts
└── types/                            # Type definitions, interfaces, DTOs
    └── dashboardTypes.ts             # Record types, filter criteria interfaces
```

---

### 2. File Size Thresholds & Enforcement Rules

1. **Advisory Soft Target**: **150 lines** per file. A file approaching 150 lines signals the need to look for extraction opportunities.
2. **Hard Ceiling Threshold**: **250 lines maximum** per file. Any file exceeding 250 lines represents an architectural violation and will be flagged as **Critical (🔴)** during code reviews and automated CI checks.
3. **MobX Model vs React View Architectural Separation**:
   - **MobX Model (`*Model.ts`)**:
     - Extends `ComponentModelBase`.
     - Handles `@serializable` config properties, `@observable` reactive state, `@action` mutations, and `@inject` service dependencies.
     - Implements `_onInitialize()` and `_onDestroy()` lifecycle methods.
     - **Strict Rule**: Models are **strictly banned** from importing React, JSX, or accessing the DOM.
   - **React View (`main.tsx`)**:
     - Serves as a high-level UI coordinator.
     - Extends `LayoutElementProperties<TModel>`.
     - Wraps children in `<LayoutElement {...props}>` and `<ErrorBoundary>`, laid out with `<Stack>` / `<Box>` and layout-only `sx`.
     - Keeps coordinator logic minimal (< 100 lines), delegating UI trees to `components/` and business workflows to `hooks/`.

---

### 3. Actionable Extraction Heuristics

When designing or refactoring a VertiGIS component, use the following heuristic decision matrix:

| Code Smell / Trigger Condition | Refactoring Action | Target Destination |
| :--- | :--- | :--- |
| **JSX return tree exceeds 50 lines** or contains distinct sections (header, table, filter drawer, dialog) | Extract into a focused presentational sub-component wrapped with `observer` if reading MobX models | `components/<SubComponent>.tsx` |
| **Coordinated State**: Multiple `useState`, `useEffect`, or MobX watchers managing a single feature | Extract into a cohesive custom React hook with a clean interface | `hooks/use<Feature>.ts` |
| **Data Formatting**: String manipulation, date calculations, currency formatting, or unit conversions | Extract into zero-dependency pure functions that can be tested in isolation | `utils/<domain>Utils.ts` |
| **ArcGIS API Logic**: Geometry buffers, spatial queries, coordinate projections, or symbol creation | Isolate into pure mapping helper functions accepting SDK instances as parameters | `helpers/<mapping>Helpers.ts` |
| **External REST/GraphQL APIs**: Direct `fetch` calls or third-party service communication | Encapsulate into a typed service client class or module | `services/<name>Client.ts` |
| **Shared Contracts**: Type declarations, interfaces, enums, or DTO definitions | Move into an explicit types file | `types/<component>Types.ts` |

---

### 4. Concrete Before / After Refactoring Demonstration

#### Monolithic Anti-Pattern (`main.tsx` ~ 400 lines)

The following example illustrates the common anti-pattern where layout, state, API calls, geometry calculations, modal dialogs, and styling are crammed into a single 400-line file:

```tsx bad
// ❌ ANTI-PATTERN: Monolithic "God Component" (~400 lines)
// Everything crammed into a single file: state, fetch, formatting, modals, and JSX.
import * as React from "react";
import { useState, useEffect } from "react";
import { observer } from "mobx-react-lite";
import { Box, Typography, Button, TextField, Table, TableBody, TableCell, TableHead, TableRow, Dialog, DialogTitle, DialogContent, DialogActions } from "@mui/material";
import { LayoutElement, LayoutElementProperties } from "@vertigis/web/components";
import { InspectionDashboardModel } from "./InspectionDashboardModel";

export default observer(function InspectionDashboard(props: LayoutElementProperties<InspectionDashboardModel>) {
    const { model } = props;
    const [records, setRecords] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [filterText, setFilterText] = useState("");
    const [selectedRecord, setSelectedRecord] = useState<any>(null);
    const [exportOpen, setExportOpen] = useState(false);
    const [exportFormat, setExportFormat] = useState("csv");

    // 50 lines of data fetching and geometry calculations...
    useEffect(() => {
        setLoading(true);
        fetch(`/api/inspections?site=${model.siteId}`)
            .then(res => res.json())
            .then(data => {
                setRecords(data);
                setLoading(false);
            });
    }, [model.siteId]);

    // 40 lines of formatting helpers embedded directly in the view...
    const formatDate = (iso: string) => {
        const d = new Date(iso);
        return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
    };

    const calculateSeverityColor = (score: number) => {
        if (score > 80) return "#d32f2f"; // Hardcoded color anti-pattern!
        if (score > 50) return "#ed6c02";
        return "#2e7d32";
    };

    // 250+ lines of deeply nested JSX...
    return (
        <LayoutElement {...props}>
            <Box sx={{ p: 2, height: "100%", display: "flex", flexDirection: "column", backgroundColor: "var(--primaryBackground)" }}>
                {/* Header */}
                <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
                    <Typography variant="h6" sx={{ color: "var(--primaryForeground)" }}>
                        {model.title}
                    </Typography>
                    <Button variant="contained" onClick={() => setExportOpen(true)} sx={{ backgroundColor: "#007ac2" }}>
                        Export
                    </Button>
                </Box>

                {/* Filter */}
                <TextField
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                    placeholder="Filter records..."
                    size="small"
                    sx={{ mb: 2 }}
                />

                {/* Table */}
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>Date</TableCell>
                            <TableCell>Severity</TableCell>
                            <TableCell>Actions</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {records.filter(r => r.name.includes(filterText)).map(r => (
                            <TableRow key={r.id} onClick={() => setSelectedRecord(r)}>
                                <TableCell>{r.id}</TableCell>
                                <TableCell>{formatDate(r.date)}</TableCell>
                                <TableCell sx={{ color: calculateSeverityColor(r.score) }}>{r.score}</TableCell>
                                <TableCell>
                                    <Button size="small" onClick={() => model.zoomToFeature(r.geometry)}>Zoom</Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>

                {/* Export Dialog */}
                <Dialog open={exportOpen} onClose={() => setExportOpen(false)}>
                    <DialogTitle>Export Inspections</DialogTitle>
                    <DialogContent>
                        {/* 50 lines of dialog controls */}
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setExportOpen(false)}>Cancel</Button>
                        <Button onClick={() => { /* Export logic */ setExportOpen(false); }}>Download</Button>
                    </DialogActions>
                </Dialog>
            </Box>
        </LayoutElement>
    );
});
```

---

#### Refactored Clean Architecture (< 100 lines coordinator view)

By applying the 7-directory blueprint and extraction heuristics, the component is refactored into focused, single-responsibility modules:

##### 1. Clean Coordinator View (`main.tsx` < 70 lines)
```tsx
// ✅ PRODUCTION PATTERN: Clean Orchestrator View (< 70 lines)
import * as React from "react";
import { observer } from "mobx-react-lite";
import { Stack } from "@mui/material";
import { LayoutElement, LayoutElementProperties } from "@vertigis/web/components";
import { ErrorBoundary } from "../../utils/ErrorBoundary";
import { InspectionDashboardModel } from "./InspectionDashboardModel";
import { DashboardHeader } from "./components/DashboardHeader";
import { FilterPanel } from "./components/FilterPanel";
import { ResultsTable } from "./components/ResultsTable";
import { ExportDialog } from "./components/ExportDialog";
import { useDashboardData } from "./hooks/useDashboardData";

export const InspectionDashboard = observer(function InspectionDashboard(
    props: LayoutElementProperties<InspectionDashboardModel>
): React.ReactElement {
    const { model } = props;
    const {
        records,
        isLoading,
        filterText,
        setFilterText,
        exportOpen,
        setExportOpen,
        handleExport,
    } = useDashboardData(model);

    return (
        <LayoutElement {...props}>
            <ErrorBoundary fallbackMessage="Failed to render inspection dashboard.">
                <Stack spacing={2} sx={{ height: "100%", p: 2 }}>
                    <DashboardHeader
                        title={model.title}
                        onExportClick={() => setExportOpen(true)}
                    />
                    <FilterPanel
                        filterText={filterText}
                        onFilterChange={setFilterText}
                    />
                    <ResultsTable
                        records={records}
                        isLoading={isLoading}
                        onZoomToFeature={(geom) => model.zoomToFeature(geom)}
                    />
                    <ExportDialog
                        open={exportOpen}
                        onClose={() => setExportOpen(false)}
                        onExport={handleExport}
                    />
                </Stack>
            </ErrorBoundary>
        </LayoutElement>
    );
});

export default InspectionDashboard;
```

##### 2. Custom Business Hook (`hooks/useDashboardData.ts` < 80 lines)
```typescript
import { useState, useEffect, useCallback, useMemo } from "react";
import { InspectionDashboardModel } from "../InspectionDashboardModel";
import { InspectionRecord } from "../types/dashboardTypes";
import { fetchSiteInspections } from "../services/inspectionApiClient";

export function useDashboardData(model: InspectionDashboardModel) {
    const [rawRecords, setRawRecords] = useState<InspectionRecord[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [filterText, setFilterText] = useState<string>("");
    const [exportOpen, setExportOpen] = useState<boolean>(false);

    useEffect(() => {
        let isMounted = true;
        setIsLoading(true);

        fetchSiteInspections(model.siteId)
            .then(data => {
                if (isMounted) setRawRecords(data);
            })
            .catch(err => {
                model.messages?.error(`Failed to load inspections: ${err.message}`);
            })
            .finally(() => {
                if (isMounted) setIsLoading(false);
            });

        return () => {
            isMounted = false;
        };
    }, [model.siteId, model.messages]);

    const records = useMemo(() => {
        if (!filterText.trim()) return rawRecords;
        const lower = filterText.toLowerCase();
        return rawRecords.filter(r => r.name.toLowerCase().includes(lower));
    }, [rawRecords, filterText]);

    const handleExport = useCallback((format: string) => {
        // Execute export logic...
        setExportOpen(false);
    }, []);

    return {
        records,
        isLoading,
        filterText,
        setFilterText,
        exportOpen,
        setExportOpen,
        handleExport,
    };
}
```

##### 3. Header Sub-Component (`components/DashboardHeader.tsx` < 50 lines)
```tsx
import * as React from "react";
import { Button, Stack, Typography } from "@mui/material";

interface DashboardHeaderProps {
    title: string;
    onExportClick: () => void;
}

export function DashboardHeader({ title, onExportClick }: DashboardHeaderProps): React.ReactElement {
    return (
        <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
                {title}
            </Typography>
            <Button variant="contained" color="primary" onClick={onExportClick}>
                Export
            </Button>
        </Stack>
    );
}
```

The parent `Stack spacing={2}` separates the header from the next section, so the header carries no bottom margin.

##### 4. Pure Formatting Utility (`utils/tableFormatters.ts` < 40 lines)
```typescript
/**
 * Formats an ISO date string into a user-facing localized timestamp.
 */
export function formatTimestamp(isoString: string): string {
    if (!isoString) return "-";
    const date = new Date(isoString);
    return isNaN(date.getTime()) ? "-" : `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

/**
 * Maps an inspection severity score to a `data-severity` value; the row colour for
 * `&[data-severity="high"]` etc. lives in src/tokens/muiTheme.ts (MuiTableRow styleOverrides).
 */
export function getSeverityLevel(score: number): "high" | "medium" | "low" {
    if (score >= 80) return "high";
    if (score >= 50) return "medium";
    return "low";
}
```

---

## Pre-Review Audit Checklist

Before submitting a VertiGIS component or extension for code review, verify adherence against this checklist:

| Category | Check Item | Pass Criteria |
| :--- | :--- | :--- |
| **Tokens & Fallbacks** | No bare CSS variables | Every CSS variable includes a safe WCAG AA fallback (e.g. `var(--primaryBackground, #ffffff)`). |
| | Zero hardcoded colors | No raw hex (`#...`), static RGB, or HSL strings in component files. |
| | Color mixing | Opacity and surface blends use `alphaMix()` or `surfaceMix()` via CSS `color-mix()`. |
| **Dual-Theme Safety** | Reactive theme awareness | Components needing theme state in React use `useIsDarkTheme()`. |
| | Host Theme & Namespaced CSS | Components inherit host theme natively via tokens; all CSS classes (optional files) are strictly namespaced (e.g. `.ListHeader`). |
| **Styling** | Zero cosmetic `sx` | `sx` / `style` / style dictionaries hold layout, geometry and spacing only; cosmetics live in `src/tokens/muiTheme.ts` (`NO_COSMETIC_SX`). |
| | 8px grid | Spacing values are `0, 0.5, 1, 1.5, 2, 2.5, 3, 4`; siblings are spaced by parent `gap` / `Stack spacing` (`STANDARDIZED_SPACING`). |
| | Declarative state & containment | State is a data attribute (`data-status`) styled in the theme; `<canvas>`, `<img>`, `<iframe>` sit inside `Paper` / `Card` (`NON_MUI_CONTAINMENT`). `npm run verify:styles` exits 0. |
| | UI Library Safety | Never import UI controls from `@vertigis/web/ui` (causes fatal UIContext crash outside shell). |
| **Modularity & Architecture** | File size compliance | Every file is under 150 lines (target) and strictly below 250 lines (ceiling). |
| | Directory blueprint | Complex components use `components/`, `hooks/`, `utils/`, and `types/` sub-directories. |
| | Model / View isolation | MobX Model (`*Model.ts`) contains zero JSX, React hooks, or DOM references. |
| | View resilience | React View wraps children in `<LayoutElement>` and `<ErrorBoundary>`. |
