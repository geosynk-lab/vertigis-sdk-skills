# VertiGIS Studio Workflow SDK: Styling, Design Tokens & Dynamic Theming

## Table of Contents
- [Introduction & Architectural Overview](#introduction--architectural-overview)
- [1. Typography System for Form Elements](#1-typography-system-for-form-elements)
  - [MUI Typography Variant Reference for Form Elements](#mui-typography-variant-reference-for-form-elements)
  - [Typography Rules & Best Practices](#typography-rules--best-practices)
- [2. Centralized Design Token Architecture](#2-centralized-design-token-architecture)
  - [Safe Fallbacks & Zero Hardcoded Colors Rule](#safe-fallbacks--zero-hardcoded-colors-rule)
  - [UI Design Tokens (`tokens/ui.ts`)](#ui-design-tokens-tokensuits)
  - [Typography Tokens (`tokens/typography.ts`)](#typography-tokens-tokenstypographyts)
  - [Central Barrel Export & `color-mix` Utilities (`tokens/index.ts`)](#central-barrel-export--color-mix-utilities-tokensindexts)
- [3. Dynamic Dual-Theme System (Light / Dark Mode Adaptation)](#3-dynamic-dual-theme-system-light--dark-mode-adaptation)
  - [1. The Reactive Theme Hook (`src/hooks/useIsDarkTheme.ts`)](#1-the-reactive-theme-hook-srchooksuseisdarkthemets)
  - [2. Standalone Theme Utility (`src/utils/themeDetection.ts`)](#2-standalone-theme-utility-srcutilsthemedetectionts)
- [4. Material UI Theme Integration (`tokens/muiTheme.ts`)](#4-material-ui-theme-integration-tokensmuithemet)
- [5. Mobile Touch Targets & Outdoor Field Guidelines](#5-mobile-touch-targets--outdoor-field-guidelines)
  - [Mobile Touch Targets (Minimum 44x44px)](#mobile-touch-targets-minimum-44x44px)
  - [Outdoor Field Contrast & Sunlight Readability](#outdoor-field-contrast--sunlight-readability)
- [6. State Token Wiring: `enabled`, `readOnly`, and Validation Errors](#6-state-token-wiring-enabled-readonly-and-validation-errors)
- [7. Complete Canonical Form Element with Design Tokens](#7-complete-canonical-form-element-with-design-tokens)

---

## Introduction & Architectural Overview

VertiGIS Studio Workflow forms execute across heterogeneous environments:
- **VertiGIS Studio Web (VSW)**: Desktop browsers inside side panels, dialog modals, or workflow drawers.
- **VertiGIS Studio Mobile (VSM)**: Native iOS, Android, and Windows tablets/smartphones utilized by field workers in outdoor, high-glare conditions.
- **ArcGIS Experience Builder (ExB)**: Embedded widgets within Esri web applications.

In all host environments, custom form elements must never use hardcoded colors or custom CSS stylesheets (`.css` / `.module.css`). They must participate natively in the host shell's design system using Material UI (MUI) components, centralized design tokens, and VertiGIS runtime CSS variables.

---

## 1. Typography System for Form Elements

All text rendered inside custom form elements must use `@mui/material` `<Typography>` components. **Raw HTML text elements (`<span>`, `<p>`, `<h1>`-`<h6>`, `<label>`) are strictly prohibited.**

### MUI Typography Variant Reference for Form Elements

| Variant | Semantic Role in Forms | Example Form Elements | Standard Foreground Token |
| :--- | :--- | :--- | :--- |
| `h6` | Form header & major section title | Form title bar, major collapsible section header | `var(--primaryForeground, #212121)` |
| `subtitle1` | Group / Fieldset heading | Card group titles, step indicators, category dividers | `var(--primaryForeground, #212121)` |
| `subtitle2` | Input field group subtitle | Secondary grouping title, sub-label | `var(--secondaryForeground, #666666)` |
| `body1` | Primary form text & interactive labels | Checkbox labels, radio option text, primary values | `var(--primaryForeground, #212121)` |
| `body2` | Secondary field text & instructions | Helper text, instructions, secondary field data | `var(--secondaryForeground, #666666)` |
| `caption` | Validation hints & metadata microcopy | Character count, units (e.g. "meters"), field hints | `var(--secondaryForeground, #666666)` / `var(--alertRedForeground, #d32f2f)` |
| `overline` | Badges & category caps | "REQUIRED", "OPTIONAL", status indicators | `var(--primaryForeground, #212121)` / Status tokens |

### Typography Rules & Best Practices

1. **Zero Raw HTML Text Elements**:
   - Replace `<p>` with `<Typography variant="body1">` or `<Typography variant="body2">`.
   - Replace `<span>` or `<label>` with `<Typography variant="body2">`, `<Typography variant="caption">`, or `<Typography variant="subtitle2">`.
   - Replace headings (`<h1>`-`<h6>`) with `<Typography variant="h6">` or `<Typography variant="subtitle1">`.
2. **Font Family Token**:
   - Always reference `fontFamily: "var(--defaultFont, sans-serif)"` (inherited automatically via MUI theme).
3. **Semantic Text Color Tokens**:
   - Always pair Typography variants with semantic foreground tokens via `sx`:
     - Primary text: `sx={{ color: "var(--primaryForeground, #212121)" }}`
     - Secondary / Muted / Helper text: `sx={{ color: "var(--secondaryForeground, #666666)" }}`
     - Disabled / Inactive text: `sx={{ color: "var(--disabledForeground, #9e9e9e)" }}`
     - Validation error text: `sx={{ color: "var(--alertRedForeground, #d32f2f)" }}`
4. **Mobile & Outdoor Field Readability**:
   - Field crews use Workflow forms outdoors on rugged tablets and smartphones in direct sunlight.
   - Set a minimum font size of at least **14px** (`body2` or larger) for readable field instructions and input labels on mobile screens.
   - Maintain generous line-height (`lineHeight: 1.4` to `1.5`) so text remains legible through glare and screen protectors.

---

<span id="design-token-architecture"></span>
## 2. Centralized Design Token Architecture

The design token subsystem is organized into a dedicated `tokens/` directory within each form element or shared library:

```
src/elements/<ElementName>/tokens/
├── ui.ts             # Surface, text, border, accent, control, status, and touch tokens
├── typography.ts     # Font stacks, font scale, weights, and line heights
├── muiTheme.ts       # MUI Theme factory and VertiGisThemeProvider bridge
└── index.ts          # Central barrel export and color-mix runtime utilities
```

### Safe Fallbacks & Zero Hardcoded Colors Rule

1. **Resilient Safe Fallbacks**: Every CSS variable **must** include a safe fallback value:
   - `var(--primaryBackground, #ffffff)`
   - `var(--primaryForeground, #212121)`
   - `var(--primaryAccent, #007ac2)`
   This guarantees that if the component renders in isolated unit tests, Storybook sandboxes, or during initial shell boot before the host branding service injects runtime variables, the UI remains perfectly legible.
2. **Strict Zero Hardcoded Colors Policy**:
   - Prohibited: Static hex (`#ffffff`, `#1976d2`), static RGB (`rgba(0, 0, 0, 0.5)`), or static HSL values.
   - Mandatory: All styling must map through `UI_TOKENS` or dynamic CSS `color-mix()` utilities.

---

### UI Design Tokens (`tokens/ui.ts`)

```typescript
/**
 * UI Design Tokens for VertiGIS Studio Workflow Form Elements.
 * Maps official VertiGIS CSS custom properties with safe WCAG AA fallbacks.
 *
 * All tokens provide guaranteed defaults for isolated testing, Storybook,
 * and initial shell boot before the branding service injects runtime variables.
 */

export const UI_TOKENS = {
    // Surface & Background Colors
    surface: {
        /** Main form canvas, panel, dialog, and container background */
        primary: "var(--primaryBackground, #ffffff)",
        /** Disabled container / control background */
        primaryDisabled: "var(--primaryBackgroundDisabled, #ebebeb)",
        /** Nested cards, input fieldsets, zebra-striping, and inset panels */
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

    // Geometry & Layout Spacing
    shape: {
        /** Standard border radius for cards, inputs, and buttons */
        borderRadius: "var(--borderRadius, 4px)",
        /** Small border radius for badges and micro-chips */
        borderRadiusSm: "var(--borderRadiusSm, 2px)",
        /** Large border radius for modals and dialogs */
        borderRadiusLg: "var(--borderRadiusLg, 8px)",
        /** Pill radius for status chips and round action buttons */
        borderRadiusPill: "9999px",
        /** Primary container elevation shadow */
        shadowPrimary: "var(--shadowPrimary, 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24))",
        /** Elevated overlay / dialog shadow */
        shadowElevated: "var(--shadowElevated, 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23))",
    },

    // Mobile Field Touch Dimensions (WCAG 2.5.5 / 2.5.8)
    touch: {
        /** Minimum target height for mobile inputs, buttons, and toggles */
        minHeight: "44px",
        /** Minimum target width for mobile touch triggers */
        minWidth: "44px",
    },
} as const;

export default UI_TOKENS;
```

---

### Typography Tokens (`tokens/typography.ts`)

```typescript
/**
 * Typography Tokens for VertiGIS Studio Workflow Form Elements.
 * Centralizes font families, scale ratios, font weights, and line heights.
 */

export const TYPOGRAPHY_TOKENS = {
    fontFamily: {
        /** Primary UI font stack inherited from the VertiGIS shell */
        primary: "var(--defaultFont, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif)",
        /** Monospace stack for coordinates, JSON payloads, and identifiers */
        mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
    },
    fontSize: {
        h6: "1.25rem",        // 20px
        subtitle1: "1rem",     // 16px
        subtitle2: "0.875rem", // 14px
        body1: "1rem",         // 16px
        body2: "0.875rem",     // 14px (minimum for mobile field readability)
        caption: "0.75rem",    // 12px
        overline: "0.625rem",  // 10px
    },
    fontWeight: {
        regular: 400,
        medium: 500,
        semibold: 600,
        bold: 700,
    },
    lineHeight: {
        tight: 1.25,
        normal: 1.5,
        relaxed: 1.625,
    },
} as const;

export default TYPOGRAPHY_TOKENS;
```

---

### Central Barrel Export & `color-mix` Utilities (`tokens/index.ts`)

```typescript
/**
 * Central Tokens Barrel & Modern CSS Color-Mix Utilities
 */

import { UI_TOKENS } from "./ui";
import { TYPOGRAPHY_TOKENS } from "./typography";

export { UI_TOKENS } from "./ui";
export { TYPOGRAPHY_TOKENS } from "./typography";

/**
 * Derives a dynamic transparent alpha tint using CSS color-mix().
 * Automatically adapts across light and dark themes without hardcoding hex values.
 *
 * @param token - Base CSS variable (e.g. UI_TOKENS.accent.primary)
 * @param opacityPercent - Desired opacity percentage (0-100)
 */
export function alphaMix(token: string, opacityPercent: number): string {
    const clamped = Math.max(0, Math.min(100, opacityPercent));
    return `color-mix(in srgb, ${token} ${clamped}%, transparent)`;
}

/**
 * Blends a foreground token into a background surface token.
 * Generates subtle borders, hover fills, and zebra striping dynamically.
 *
 * @param fgToken - Foreground color token
 * @param bgToken - Background surface token
 * @param weightPercent - Percentage weight of foreground (e.g. 8% for subtle hover)
 */
export function surfaceMix(fgToken: string, bgToken: string, weightPercent: number): string {
    const clamped = Math.max(0, Math.min(100, weightPercent));
    return `color-mix(in srgb, ${fgToken} ${clamped}%, ${bgToken})`;
}

export const tokens = {
    ui: UI_TOKENS,
    typography: TYPOGRAPHY_TOKENS,
    alphaMix,
    surfaceMix,
};

export default tokens;
```

---

<span id="dynamic-theming-system"></span>
## 3. Dynamic Dual-Theme System (Light / Dark Mode Adaptation)

Workflow forms frequently render non-CSS graphical elements:
- **HTML5 `<canvas>` & Signature Pads**: Capture field signatures or hand-drawn sketches.
- **Photo Annotation & Markup**: Draw measurements or hazard circles on captured camera images.
- **Barcode & QR Scanners**: Render scanner viewfinders and detection reticles.
- **Third-Party Charting & Analytics**: Render telemetry or sensor inspection data.
- **PDF Report Generators**: Export form data client-side.

These elements cannot directly consume CSS variables (`var(--primaryBackground, #ffffff)`). They require programmatic theme detection.

### 1. The Reactive Theme Hook (`src/hooks/useIsDarkTheme.ts`)

This hook reactively tracks theme switches by observing DOM attributes, host shell classes, and computed background luminance:

```typescript
import * as React from "react";
import { useTheme } from "@mui/material/styles";
import { isDarkTheme } from "../utils/themeDetection";

/**
 * React hook to reactively track whether the active VertiGIS / application theme is dark mode.
 * Evaluates MUI theme mode, VertiGIS CSS variables, DOM classes/attributes, and system preferences.
 */
export function useIsDarkTheme(): boolean {
    const theme = useTheme();
    const [isDark, setIsDark] = React.useState<boolean>(() => {
        if (theme?.palette?.mode === "dark") return true;
        if (theme?.palette?.mode === "light") return false;
        return isDarkTheme();
    });

    React.useEffect(() => {
        if (theme?.palette?.mode === "dark") {
            setIsDark(true);
            return;
        }
        if (theme?.palette?.mode === "light") {
            setIsDark(false);
            return;
        }

        const updateDark = () => {
            setIsDark(isDarkTheme());
        };

        updateDark();

        // 1. Listen for OS media query changes
        const mql = typeof window !== "undefined" && window.matchMedia
            ? window.matchMedia("(prefers-color-scheme: dark)")
            : null;
        mql?.addEventListener?.("change", updateDark);

        // 2. Observe DOM attribute and class mutations on shell containers
        let observer: MutationObserver | null = null;
        if (typeof MutationObserver !== "undefined" && typeof document !== "undefined") {
            observer = new MutationObserver(updateDark);
            const obsConfig = {
                attributes: true,
                attributeFilter: ["data-theme", "class", "style"],
            };
            if (document.documentElement) {
                observer.observe(document.documentElement, obsConfig);
            }
            if (document.body) {
                observer.observe(document.body, obsConfig);
            }
            const vswApp = document.querySelector(".vsw-app");
            if (vswApp) {
                observer.observe(vswApp, obsConfig);
            }
        }

        return () => {
            mql?.removeEventListener?.("change", updateDark);
            observer?.disconnect();
        };
    }, [theme?.palette?.mode]);

    return isDark;
}

export default useIsDarkTheme;
```

---

### 2. Standalone Theme Utility (`src/utils/themeDetection.ts`)

Used in non-React helper functions, canvas drawing loops, and export generators:

```typescript
/**
 * Standalone Theme Detection Utility
 * Inspects DOM markers, computed CSS custom properties, and calculates
 * ITU-R BT.709 perceived luminance to determine light or dark mode.
 */

/**
 * Calculates ITU-R BT.709 relative perceived luminance from an sRGB color.
 * Returns a value between 0.0 (pure black) and 1.0 (pure white).
 */
export function calculatePerceivedLuminance(r: number, g: number, b: number): number {
    const normalize = (val: number) => {
        const s = val / 255;
        return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * normalize(r) + 0.7152 * normalize(g) + 0.0722 * normalize(b);
}

/**
 * Parses a CSS color string (hex or rgb/rgba) into RGB components.
 */
export function parseRgbComponents(colorStr: string): [number, number, number] | null {
    if (!colorStr) return null;
    const clean = colorStr.trim().toLowerCase();

    // Parse Hex #RGB or #RRGGBB
    if (clean.startsWith("#")) {
        const hex = clean.slice(1);
        if (hex.length === 3) {
            const r = parseInt(hex[0] + hex[0], 16);
            const g = parseInt(hex[1] + hex[1], 16);
            const b = parseInt(hex[2] + hex[2], 16);
            return [r, g, b];
        }
        if (hex.length >= 6) {
            const r = parseInt(hex.slice(0, 2), 16);
            const g = parseInt(hex.slice(2, 4), 16);
            const b = parseInt(hex.slice(4, 6), 16);
            return [r, g, b];
        }
    }

    // Parse rgb(r, g, b) or rgba(r, g, b, a)
    const match = clean.match(/rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)/);
    if (match) {
        // Ignore fully transparent roots
        if (match[4] !== undefined && parseFloat(match[4]) === 0) {
            return null;
        }
        return [parseInt(match[1], 10), parseInt(match[2], 10), parseInt(match[3], 10)];
    }

    return null;
}

/**
 * Detects whether the current execution context is in dark theme mode.
 */
export function isDarkTheme(): boolean {
    if (typeof window === "undefined" || typeof document === "undefined") {
        return false;
    }

    const docEl = document.documentElement;
    const body = document.body;

    // 1. Check explicit DOM attributes
    if (docEl.getAttribute("data-theme") === "dark" || body.getAttribute("data-theme") === "dark") {
        return true;
    }

    // 2. Check known class markers
    const darkClasses = ["dark", "theme-dark", "vsw-theme-dark", "vsm-theme-dark"];
    for (const cls of darkClasses) {
        if (docEl.classList.contains(cls) || body.classList.contains(cls)) {
            return true;
        }
    }

    // 3. Evaluate computed CSS variable luminance
    try {
        const testTarget = document.querySelector(".vsw-app") || document.querySelector(".vsm-app") || body || docEl;
        const style = window.getComputedStyle(testTarget);
        const bgVal = style.getPropertyValue("--primaryBackground").trim();
        if (bgVal) {
            const rgb = parseRgbComponents(bgVal);
            if (rgb) {
                return calculatePerceivedLuminance(rgb[0], rgb[1], rgb[2]) < 0.5;
            }
        }
    } catch {
        // Fall through on non-standard environments
    }

    // 4. Fall back to OS prefers-color-scheme
    if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
        return true;
    }

    return false;
}
```

---

<span id="mui-theme-integration"></span>
## 4. Material UI Theme Integration (`tokens/muiTheme.ts`)

To ensure standard MUI composite controls (Sliders, DatePickers, ToggleButtons, AutoCompletes) automatically adopt VertiGIS shell colors without verbose `sx` overrides on every leaf node, use a theme factory:

```typescript
import { createTheme, Theme, ThemeProvider } from "@mui/material/styles";
import * as React from "react";
import { UI_TOKENS } from "./ui";
import { TYPOGRAPHY_TOKENS } from "./typography";

/**
 * Creates an enterprise Material UI Theme aligned with VertiGIS shell tokens.
 */
export function createVertiGisWorkflowMuiTheme(isDark: boolean): Theme {
    return createTheme({
        palette: {
            mode: isDark ? "dark" : "light",
            primary: {
                main: UI_TOKENS.accent.primary,
                contrastText: UI_TOKENS.accent.contrastText,
            },
            background: {
                default: UI_TOKENS.surface.primary,
                paper: UI_TOKENS.surface.secondary,
            },
            text: {
                primary: UI_TOKENS.text.primary,
                secondary: UI_TOKENS.text.secondary,
                disabled: UI_TOKENS.text.disabled,
            },
            divider: UI_TOKENS.border.primary,
            error: {
                main: UI_TOKENS.status.errorFg,
            },
            success: {
                main: UI_TOKENS.status.successFg,
            },
            warning: {
                main: UI_TOKENS.status.warningFg,
            },
            info: {
                main: UI_TOKENS.status.infoFg,
            },
            action: {
                hover: UI_TOKENS.control.itemHover,
                selected: UI_TOKENS.control.itemSelected,
                disabledBackground: UI_TOKENS.control.buttonBackgroundDisabled,
                disabled: UI_TOKENS.text.disabled,
            },
        },
        typography: {
            fontFamily: TYPOGRAPHY_TOKENS.fontFamily.primary,
            fontSize: 14, // Minimum 14px for outdoor field readability
        },
        shape: {
            borderRadius: 4,
        },
        components: {
            MuiPaper: {
                styleOverrides: {
                    root: {
                        // CRITICAL: Disable MUI default dark elevation overlay tint
                        backgroundImage: "none",
                    },
                },
            },
            MuiButton: {
                styleOverrides: {
                    root: {
                        textTransform: "none",
                        fontWeight: 600,
                        minHeight: UI_TOKENS.touch.minHeight, // Mobile 44x44px touch target
                    },
                },
            },
            MuiOutlinedInput: {
                styleOverrides: {
                    root: {
                        minHeight: UI_TOKENS.touch.minHeight,
                        "& .MuiOutlinedInput-notchedOutline": {
                            borderColor: UI_TOKENS.control.inputBorder,
                        },
                        "&:hover .MuiOutlinedInput-notchedOutline": {
                            borderColor: UI_TOKENS.accent.primary,
                        },
                        "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                            borderColor: UI_TOKENS.accent.primary,
                        },
                        "&.Mui-disabled .MuiOutlinedInput-notchedOutline": {
                            borderColor: UI_TOKENS.control.inputBorderDisabled,
                        },
                    },
                },
            },
            MuiInputLabel: {
                styleOverrides: {
                    root: {
                        color: UI_TOKENS.text.secondary,
                        "&.Mui-focused": {
                            color: UI_TOKENS.accent.primary,
                        },
                    },
                },
            },
        },
    });
}

export interface VertiGisThemeProviderProps {
    children: React.ReactNode;
    isDark?: boolean;
}

/**
 * ThemeProvider wrapper ensuring all nested MUI components inherit VertiGIS design tokens.
 */
export function VertiGisThemeProvider({ children, isDark = false }: VertiGisThemeProviderProps) {
    const theme = React.useMemo(() => createVertiGisWorkflowMuiTheme(isDark), [isDark]);
    return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}
```

---

### Pure Theme Inheritance & Zero Color Injection Rule (Form Elements)

#### The Rule: Never Inject Colors into Standard MUI Form Elements
When developing custom workflow form elements with MUI (`DatePicker`, `TimePicker`, `DateTimePicker`, `TextField`, `Select`, `Button`, `Checkbox`, `Switch`, `Slider`, `RadioGroup`), **never inject inline color styles** via `sx={{ color, backgroundColor, borderColor }}` or CSS classes.

#### Why Micro-Injecting Colors Hurts Form Elements
1. **Destroys Dynamic Pseudo-States**: Manual `sx` overrides clobber native `:hover`, `:focus-visible`, `:disabled`, `:selected`, and touch feedback states.
2. **Breaks Theme Synchronization**: When mobile or desktop users switch between light and dark themes, hardcoded styles cause severe readability and contrast bugs in outdoor field conditions.
3. **Bloats Code with Brittle Selectors**: Composite controls like `<DatePicker>` comprise calendar modals, header arrows, year grids, and day buttons. Micro-styling them via CSS selectors creates brittle boilerplate that breaks across MUI releases.

#### What NOT to Do (Anti-Pattern)
```tsx
// ❌ WRONG: Micro-injecting tokens into internal MUI subcomponents
<DatePicker
    value={value}
    onChange={setValue}
    sx={{
        backgroundColor: "var(--primaryBackground)",
        color: "var(--primaryForeground)",
        "& .MuiOutlinedInput-notchedOutline": {
            borderColor: "var(--inputBorder)",
        },
        "& .MuiSvgIcon-root": {
            color: "var(--accentIconForeground)",
        },
    }}
/>
```

#### What to Do (Inheritance-First)
Wrap your form element in `VertiGisThemeProvider`. Standard MUI controls inherit all colors, borders, and interaction states natively:

```tsx
// ✅ CORRECT: Zero color injection. Inherits seamlessly from VertiGisThemeProvider.
<VertiGisThemeProvider isDark={isDark}>
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <DatePicker
            value={value}
            onChange={(newVal) => props.setValue(newVal)}
            slotProps={{
                textField: {
                    size: "small",
                    fullWidth: true,
                    disabled: !props.enabled,
                    inputProps: { readOnly: props.readOnly },
                },
            }}
        />
        <TextField
            label={props.label || "Inspection Notes"}
            value={props.value ?? ""}
            onChange={(e) => props.setValue(e.target.value)}
            size="small"
            fullWidth
            disabled={!props.enabled}
            inputProps={{ readOnly: props.readOnly }}
        />
    </Box>
</VertiGisThemeProvider>
```

#### Strict Boundary: When IS Token Injection Allowed?
| UI Element | Styling Approach | Allowed Styling |
| :--- | :--- | :--- |
| **Standard Form Controls** (`DatePicker`, `TextField`, `Select`) | **Pure Theme Inheritance** | Layout and sizing only (`size`, `margin`, `fullWidth`, `minHeight: 44px`). **Zero color or border overrides**. |
| **Standard Buttons & Toggles** (`Button`, `Switch`, `Checkbox`) | **Pure Theme Inheritance** | Variant only (`variant="contained"`, `variant="outlined"`). Inherits accent and focus states. |
| **MUI Typography** (`Typography`) | **Variant-Driven** | `variant="h6"`, `variant="body1"`. Colors inherit from `theme.palette.text`. |
| **Custom Status / Alert Banners** | **Explicit Semantic Tokens** | `var(--alertAmberBackground)`, `var(--alertRedForeground)`, `var(--alertGreenBorder)`. |
| **Subtle Tints & Overlays** | **Dynamic `color-mix()`** | `color-mix(in srgb, var(--primaryAccent) 12%, transparent)` for row highlights. |
| **Non-CSS Canvas / Signatures / Barcodes** | **Programmatic Access** | Canvas stroke fills using `isDarkTheme()`, SVG `fill="var(--accentIconForeground)"`. |

---

## 5. Mobile Touch Targets & Outdoor Field Guidelines

### Mobile Touch Targets (Minimum 44x44px)
For all interactive controls (buttons, checkboxes, toggle switches, icon action triggers, dropdown selectors):
- Ensure touch targets satisfy a minimum size of **44x44px** (per WCAG 2.5.5 / 2.5.8).
- Use `minHeight: "44px"` and `minWidth: "44px"` on interactive containers so mobile operators wearing gloves or working in wet field conditions can tap accurately.

### Outdoor Field Contrast & Sunlight Readability
- Outdoor field workers frequently view forms in bright sunlight and harsh ambient light.
- Adhere strictly to **WCAG AA contrast ratios**:
  - Minimum **4.5:1** for normal text against its background.
  - Minimum **3:1** for large text (18px+ or 14px bold) and graphical elements / interactive boundaries.
- Pairing `var(--primaryForeground, #212121)` with `var(--primaryBackground, #ffffff)` or `var(--secondaryBackground, #f5f5f5)` guarantees compliant contrast across all VertiGIS light and dark themes.

---

## 6. State Token Wiring: `enabled`, `readOnly`, and Validation Errors

Form elements receive standard props from the workflow engine. Map them cleanly to tokens:

1. **`enabled` (Interactivity State)**:
   - When `!enabled`, apply `disabled` styles:
     - Input text and border: `color: "var(--disabledForeground, #9e9e9e)"`, `borderColor: "var(--disabledForeground, #9e9e9e)"`
     - Background: muted or transparent.
2. **`readOnly` (Inspection State)**:
   - Must be distinctly visually different from `disabled`.
   - `readOnly` elements remain selectable and fully legible in high contrast (`color: "var(--primaryForeground, #212121)"`), with a subtle non-editable background (`backgroundColor: "var(--secondaryBackground, #f5f5f5)"`).
3. **Validation Errors**:
   - When input validation fails, highlight borders with `var(--alertRedForeground, #d32f2f)` and render the error message with `<Typography variant="caption" sx={{ color: "var(--alertRedForeground, #d32f2f)" }}>`.

---

## 7. Complete Canonical Form Element with Design Tokens

Below is a complete, production-grade custom form element combining MUI Typography, the design token subsystem, `useIsDarkTheme`, state persistence, and standard props wiring:

```tsx
import * as React from "react";
import { Box, Stack, Button, TextField, Typography } from "@mui/material";
import { FormElementProps } from "@vertigis/workflow";
import { tokens } from "./tokens";
import { useIsDarkTheme } from "./hooks/useIsDarkTheme";
import { FormElementErrorBoundary } from "./components/FormElementErrorBoundary";

export interface InspectionNotesProps extends FormElementProps<string> {
    label?: string;
    placeholder?: string;
    maxLength?: number;
}

function InspectionNotesView(props: InspectionNotesProps) {
    const {
        value = "",
        setValue,
        enabled = true,
        readOnly = false,
        visible = true,
        label = "Inspection Observations",
        placeholder = "Enter site defect observations...",
        maxLength = 500,
    } = props;

    const isDark = useIsDarkTheme();
    const [localText, setLocalText] = React.useState<string>(value);

    // Sync external workflow value updates
    React.useEffect(() => {
        setLocalText(value || "");
    }, [value]);

    if (!visible) {
        return null;
    }

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const text = e.target.value;
        setLocalText(text);
        // Persist to workflow state so data survives tab remounts
        setValue(text);
    };

    const isOverLimit = localText.length > maxLength;

    return (
        <Box
            sx={{
                p: 2,
                backgroundColor: tokens.ui.surface.primary,
                border: `1px solid ${tokens.ui.border.primary}`,
                borderRadius: tokens.ui.shape.borderRadius,
                boxShadow: tokens.ui.shape.shadowPrimary,
            }}
        >
            {/* Form Element Header */}
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                <Typography
                    variant="subtitle1"
                    sx={{
                        color: tokens.ui.text.primary,
                        fontFamily: tokens.typography.fontFamily.primary,
                        fontWeight: tokens.typography.fontWeight.semibold,
                    }}
                >
                    {label}
                </Typography>
                <Typography
                    variant="caption"
                    sx={{
                        color: isOverLimit ? tokens.ui.status.errorFg : tokens.ui.text.secondary,
                        fontWeight: tokens.typography.fontWeight.medium,
                    }}
                >
                    {localText.length} / {maxLength}
                </Typography>
            </Stack>

            {/* Main Input Field */}
            <TextField
                multiline
                rows={4}
                fullWidth
                disabled={!enabled}
                value={localText}
                onChange={handleChange}
                placeholder={placeholder}
                InputProps={{
                    readOnly,
                    sx: {
                        color: tokens.ui.text.primary,
                        backgroundColor: readOnly
                            ? tokens.ui.surface.secondary
                            : tokens.surfaceMix(tokens.ui.text.primary, tokens.ui.surface.primary, isDark ? 4 : 0),
                        minHeight: tokens.ui.touch.minHeight,
                    },
                }}
            />

            {/* Validation Feedback */}
            {isOverLimit && (
                <Typography
                    variant="caption"
                    sx={{
                        display: "block",
                        mt: 0.5,
                        color: tokens.ui.status.errorFg,
                    }}
                >
                    Character limit exceeded. Please shorten your notes before submitting.
                </Typography>
            )}
        </Box>
    );
}

export default function InspectionNotes(props: InspectionNotesProps) {
    return (
        <FormElementErrorBoundary>
            <InspectionNotesView {...props} />
        </FormElementErrorBoundary>
    );
}
```
