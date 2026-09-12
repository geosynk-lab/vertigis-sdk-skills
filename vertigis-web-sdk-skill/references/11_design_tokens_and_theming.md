# VertiGIS Studio Web SDK: Design Tokens & Dynamic Theming Architecture

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
├── muiTheme.ts       # MUI Theme factory and VertiGisThemeProvider bridge
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
        /** Nested cards, zebra-striping, inset panels, and table headers */
        secondary: "var(--secondaryBackground, #f5f5f5)",
        /** Semi-transparent modal backdrop overlay */
        overlay: "var(--overlayBackground, rgba(0, 0, 0, 0.5))",
        /** Inverted high-contrast surface for tooltips and snackbars */
        inverse: "var(--primaryForeground, #212121)",
    },

    // Foreground & Typography Colors
    text: {
        /** Primary body copy, headers, and high-contrast labels */
        primary: "var(--primaryForeground, #212121)",
        /** Secondary captions, subtitles, helper text, and muted labels */
        secondary: "var(--secondaryForeground, #666666)",
        /** Inactive controls, placeholder copy, and disabled text */
        disabled: "var(--disabledForeground, #9e9e9e)",
        /** Inverted high-contrast text on accent or dark backgrounds */
        inverse: "var(--primaryBackground, #ffffff)",
    },

    // Borders & Structural Dividers
    border: {
        /** Outer panel borders, card outlines, and standard dividers */
        primary: "var(--primaryBorder, #e0e0e0)",
        /** Subtle inner dividers, grid lines, and nested borders */
        secondary: "var(--secondaryBorder, #eeeeee)",
        /** High-visibility border for keyboard focus rings and active selections */
        focus: "var(--focusBorder, #007ac2)",
    },

    // Brand Accents & Interactive Highlights
    accent: {
        /** Primary enterprise brand color, active tabs, and primary buttons */
        primary: "var(--primaryAccent, #007ac2)",
        /** Hover state for brand buttons, active links, and selection rings */
        hover: "var(--primaryAccentHover, #005a91)",
        /** Subtle background tint for selected rows or badge highlights */
        light: "var(--primaryAccentLight, #e1f5fe)",
        /** Contrasting text color rendered on top of accent fills */
        contrastText: "var(--buttonForeground, #ffffff)",
    },

    // Interactive Controls & Form Elements
    control: {
        /** Background fill for emphasized call-to-action buttons */
        buttonBackground: "var(--emphasizedButtonBackground, var(--primaryAccent, #007ac2))",
        /** Foreground text and icon color within emphasized buttons */
        buttonForeground: "var(--buttonForeground, #ffffff)",
        /** Hover background for list items, menu rows, and clickable cells */
        itemHover: "var(--itemHoverBackground, rgba(0, 0, 0, 0.04))",
        /** Selected background for active list rows, navigation items, and tree nodes */
        itemSelected: "var(--itemSelectedBackground, rgba(0, 122, 194, 0.12))",
    },

    // Status Feedback & Validation Alerts
    status: {
        /** Error alert surface */
        errorBg: "var(--alertRedBackground, #fdecea)",
        /** Error alert text and icons */
        errorFg: "var(--alertRedForeground, #d32f2f)",
        /** Error alert border outline */
        errorBorder: "var(--alertRedBorder, #f5c2c7)",

        /** Success alert surface */
        successBg: "var(--alertGreenBackground, #edf7ed)",
        /** Success alert text and icons */
        successFg: "var(--alertGreenForeground, #2e7d32)",
        /** Success alert border outline */
        successBorder: "var(--alertGreenBorder, #badbcc)",

        /** Warning alert surface */
        warningBg: "var(--alertAmberBackground, #fff4e5)",
        /** Warning alert text and icons */
        warningFg: "var(--alertAmberForeground, #ed6c02)",
        /** Warning alert border outline */
        warningBorder: "var(--alertAmberBorder, #ffecb5)",

        /** Neutral/Informational alert surface */
        infoBg: "var(--alertGrayBackground, #f4f4f4)",
        /** Neutral/Informational alert text and icons */
        infoFg: "var(--alertGrayForeground, #616161)",
        /** Neutral/Informational alert border outline */
        infoBorder: "var(--alertGrayBorder, #e0e0e0)",
    },

    // Geometry & Shape Tokens
    shape: {
        /** Standard corner radius for buttons, input fields, and chips */
        borderRadius: "var(--borderRadius, 4px)",
        /** Extended corner radius for cards, floating panels, and dialogs */
        borderRadiusLarge: "var(--borderRadiusLarge, 8px)",
        /** Fully rounded pill or circular avatar radius */
        borderRadiusRound: "50%",
    },
} as const;

export type UiTokens = typeof UI_TOKENS;
```

---

### 3. Typography Tokens (`src/tokens/typography.ts`)

Typography tokens standardize font stacks, scale, line heights, and weights:

```typescript
/**
 * Typography Tokens for VertiGIS Studio Web SDK
 * Provides standardized font stacks, modular scales, weights, and line heights.
 */

export const TYPOGRAPHY_TOKENS = {
    // Font Family Stacks
    fontFamily: {
        /** Standard user interface typography stack */
        default: 'var(--defaultFont, "Roboto", "Helvetica", "Arial", sans-serif)',
        /** Monospace stack for coordinates, code snippets, and JSON payloads */
        monospace: 'var(--codeFont, "Roboto Mono", "Courier New", monospace)',
    },

    // Modular Font Scale (Rem-based)
    fontSize: {
        /** 12px - Captions, overlines, legal copy, and micro-badges */
        xs: "0.75rem",
        /** 14px - Body2, compact table cells, helper tooltips */
        sm: "0.875rem",
        /** 16px - Base body1, standard inputs, buttons */
        base: "1rem",
        /** 20px - Subtitle1, panel titles, section headers */
        lg: "1.25rem",
        /** 24px - H5, widget main titles */
        xl: "1.5rem",
        /** 32px - H4, primary dashboard KPIs */
        xxl: "2rem",
    },

    // Font Weights
    fontWeight: {
        /** Regular copy */
        regular: 400,
        /** Form labels, table headers, emphasized buttons */
        medium: 500,
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
export * from "./muiTheme";

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
import { Box, Typography, Button } from "@mui/material";
import { UI_TOKENS, TYPOGRAPHY_TOKENS, alphaMix, surfaceMix } from "../tokens";

export function FeatureCard({ title, description, isSelected }: { title: string; description: string; isSelected: boolean }) {
    return (
        <Box
            sx={{
                p: 2,
                borderRadius: UI_TOKENS.shape.borderRadius,
                border: `1px solid ${isSelected ? UI_TOKENS.accent.primary : UI_TOKENS.border.primary}`,
                backgroundColor: isSelected
                    ? surfaceMix(UI_TOKENS.surface.primary, UI_TOKENS.accent.primary, 10)
                    : UI_TOKENS.surface.primary,
                "&:hover": {
                    backgroundColor: surfaceMix(UI_TOKENS.surface.primary, UI_TOKENS.accent.primary, 5),
                    borderColor: UI_TOKENS.accent.hover,
                },
                transition: "background-color 150ms ease, border-color 150ms ease",
            }}
        >
            <Typography
                variant="h6"
                sx={{
                    fontFamily: TYPOGRAPHY_TOKENS.fontFamily.default,
                    fontSize: TYPOGRAPHY_TOKENS.fontSize.lg,
                    fontWeight: TYPOGRAPHY_TOKENS.fontWeight.medium,
                    color: UI_TOKENS.text.primary,
                    mb: 1,
                }}
            >
                {title}
            </Typography>
            <Typography
                variant="body2"
                sx={{
                    fontFamily: TYPOGRAPHY_TOKENS.fontFamily.default,
                    fontSize: TYPOGRAPHY_TOKENS.fontSize.sm,
                    color: UI_TOKENS.text.secondary,
                    mb: 2,
                }}
            >
                {description}
            </Typography>
            <Button
                variant="contained"
                sx={{
                    backgroundColor: UI_TOKENS.control.buttonBackground,
                    color: UI_TOKENS.control.buttonForeground,
                    borderRadius: UI_TOKENS.shape.borderRadius,
                    "&:hover": {
                        backgroundColor: UI_TOKENS.accent.hover,
                        boxShadow: `0 0 0 3px ${alphaMix(UI_TOKENS.accent.primary, 25)}`,
                    },
                }}
            >
                View Details
            </Button>
        </Box>
    );
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
2. **Tier 2: Computed Background Color Luminance**: Computes the host root's background color via `window.getComputedStyle` and calculates perceived luminance using the ITU-R BT.709 standard (`(0.2126*R + 0.7152*G + 0.0722*B) / 255 < 0.5`).
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

    // 2. Tier 2: Sample computed background color of root and measure ITU-R BT.709 luminance
    try {
        const computedBg = window.getComputedStyle(rootElement).backgroundColor;
        if (computedBg && computedBg !== "transparent") {
            const rgbaMatch = computedBg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/i);
            if (rgbaMatch) {
                const alpha = rgbaMatch[4] !== undefined ? parseFloat(rgbaMatch[4]) : 1;
                // Transparent or near-transparent backgrounds must not be evaluated as black;
                // safely skip Tier 2 luminance measurement and fall through to Tier 3 media query
                if (alpha >= 0.05) {
                    const r = parseInt(rgbaMatch[1], 10);
                    const g = parseInt(rgbaMatch[2], 10);
                    const b = parseInt(rgbaMatch[3], 10);

                    // ITU-R BT.709 relative perceived luminance formula
                    const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
                    return luminance < 0.5;
                }
            }
        }
    } catch {
        // Fallback to media query if DOM inspection encounters permission/context issues
    }

    // 3. Tier 3: Fallback to OS / browser color scheme preference
    return Boolean(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
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

### 3. MUI Theme Overrides & `VertiGisThemeProvider` Bridge (`src/tokens/muiTheme.ts`)

Composite controls in `@mui/material` (such as `<Slider>`, `<Switch>`, `<Select>`, `<DatePicker>`, `<Tabs>`, and `<Paper>`) contain deep internal elements that query the MUI `theme.palette` object. Without an explicit `ThemeProvider`, these controls fall back to default MUI blue (`#1976d2`) and default light/dark elevation backgrounds.

`createVertiGisMuiTheme` bridges VertiGIS design tokens to MUI internals and disables MUI's default dark-mode elevation paper tint:

```tsx
import * as React from "react";
import { createTheme, ThemeProvider, Theme } from "@mui/material/styles";
import { UI_TOKENS } from "./ui";
import { TYPOGRAPHY_TOKENS } from "./typography";
import { useIsDarkTheme } from "../hooks/useIsDarkTheme";

/**
 * Creates an MUI Theme configured to align with VertiGIS Studio Web design tokens.
 *
 * @param isDark - Whether the theme is currently in dark mode.
 * @returns Configured Material UI Theme object.
 */
export function createVertiGisMuiTheme(isDark: boolean): Theme {
    return createTheme({
        palette: {
            mode: isDark ? "dark" : "light",
            primary: {
                main: UI_TOKENS.accent.primary,
                light: UI_TOKENS.accent.light,
                dark: UI_TOKENS.accent.hover,
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
            warning: {
                main: UI_TOKENS.status.warningFg,
            },
            success: {
                main: UI_TOKENS.status.successFg,
            },
            info: {
                main: UI_TOKENS.status.infoFg,
            },
        },
        typography: {
            fontFamily: TYPOGRAPHY_TOKENS.fontFamily.default,
            fontSize: 14,
        },
        shape: {
            borderRadius: 4,
        },
        components: {
            MuiPaper: {
                styleOverrides: {
                    root: {
                        // CRITICAL: Disable MUI default dark elevation overlay tint
                        // which adds an unwanted white overlay gradient in dark mode
                        backgroundImage: "none",
                    },
                },
            },
            MuiButton: {
                styleOverrides: {
                    root: {
                        borderRadius: UI_TOKENS.shape.borderRadius,
                        textTransform: "none", // Align with VertiGIS modern typography
                        fontWeight: TYPOGRAPHY_TOKENS.fontWeight.medium,
                    },
                },
            },
            MuiSlider: {
                styleOverrides: {
                    root: {
                        color: UI_TOKENS.accent.primary,
                    },
                },
            },
            MuiSwitch: {
                styleOverrides: {
                    switchBase: {
                        "&.Mui-checked": {
                            color: UI_TOKENS.accent.primary,
                            "& + .MuiSwitch-track": {
                                backgroundColor: UI_TOKENS.accent.primary,
                            },
                        },
                    },
                },
            },
        },
    });
}

export interface VertiGisThemeProviderProps {
    children: React.ReactNode;
}

/**
 * Reactive ThemeProvider wrapper for composite MUI controls in VertiGIS extensions.
 * Automatically synchronizes with the host shell theme via useIsDarkTheme().
 */
export function VertiGisThemeProvider({ children }: VertiGisThemeProviderProps): React.ReactElement {
    const isDark = useIsDarkTheme();
    const theme = React.useMemo(() => createVertiGisMuiTheme(isDark), [isDark]);

    return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}
```

---

### 4. Non-CSS Renderers Integration Patterns

#### A. Plotly.js Dynamic Theming
When embedding charting in GIS widgets, synchronize the chart template, axes, and background colors with `useIsDarkTheme()`:

```tsx
import * as React from "react";
import Plot from "react-plotly.js";
import { useIsDarkTheme } from "../hooks/useIsDarkTheme";

interface ElevationChartProps {
    distances: number[];
    elevations: number[];
}

export function ElevationChart({ distances, elevations }: ElevationChartProps): React.ReactElement {
    const isDark = useIsDarkTheme();

    const layout = React.useMemo(() => ({
        template: isDark ? "plotly_dark" : "plotly_white",
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        margin: { t: 24, r: 20, l: 40, b: 36 },
        font: {
            color: isDark ? "#f5f5f5" : "#212121",
            family: "Roboto, Helvetica, Arial, sans-serif",
            size: 12,
        },
        xaxis: {
            gridcolor: isDark ? "#333333" : "#e0e0e0",
            linecolor: isDark ? "#555555" : "#cccccc",
            title: "Distance (m)",
        },
        yaxis: {
            gridcolor: isDark ? "#333333" : "#e0e0e0",
            linecolor: isDark ? "#555555" : "#cccccc",
            title: "Elevation (m)",
        },
    }), [isDark]);

    return (
        <Plot
            data={[{
                x: distances,
                y: elevations,
                type: "scatter",
                mode: "lines",
                line: { color: isDark ? "#29b6f6" : "#007ac2", width: 2 },
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

export function renderProfileCanvas(
    canvas: HTMLCanvasElement,
    profilePoints: Array<{ x: number; y: number }>
): void {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const isDark = isDarkTheme();
    const { width, height } = canvas;

    // 1. Clear with transparent or surface fill
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = isDark ? "#1e1e1e" : "#ffffff";
    ctx.fillRect(0, 0, width, height);

    // 2. Draw coordinate gridlines
    ctx.strokeStyle = isDark ? "#333333" : "#eeeeee";
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
    }

    // 3. Draw GIS profile path
    ctx.strokeStyle = isDark ? "#4fc3f7" : "#007ac2";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    profilePoints.forEach((pt, idx) => {
        if (idx === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
    });
    ctx.stroke();

    // 4. Render axis labels
    ctx.fillStyle = isDark ? "#aaaaaa" : "#666666";
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
     - Wraps children in `<LayoutElement {...props}>`, `<ErrorBoundary>`, and `<VertiGisThemeProvider>`.
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

```tsx
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
import { Box } from "@mui/material";
import { LayoutElement, LayoutElementProperties } from "@vertigis/web/components";
import { ErrorBoundary } from "../../utils/ErrorBoundary";
import { VertiGisThemeProvider } from "../../tokens/muiTheme";
import { UI_TOKENS } from "../../tokens";
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
                <VertiGisThemeProvider>
                    <Box
                        sx={{
                            p: 2,
                            height: "100%",
                            display: "flex",
                            flexDirection: "column",
                            backgroundColor: UI_TOKENS.surface.primary,
                            color: UI_TOKENS.text.primary,
                        }}
                    >
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
                    </Box>
                </VertiGisThemeProvider>
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
import { Box, Typography, Button } from "@mui/material";
import { UI_TOKENS, TYPOGRAPHY_TOKENS } from "../../../tokens";

interface DashboardHeaderProps {
    title: string;
    onExportClick: () => void;
}

export function DashboardHeader({ title, onExportClick }: DashboardHeaderProps): React.ReactElement {
    return (
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
            <Typography
                variant="h6"
                sx={{
                    fontFamily: TYPOGRAPHY_TOKENS.fontFamily.default,
                    fontSize: TYPOGRAPHY_TOKENS.fontSize.lg,
                    fontWeight: TYPOGRAPHY_TOKENS.fontWeight.bold,
                    color: UI_TOKENS.text.primary,
                }}
            >
                {title}
            </Typography>
            <Button
                variant="contained"
                onClick={onExportClick}
                sx={{
                    backgroundColor: UI_TOKENS.control.buttonBackground,
                    color: UI_TOKENS.control.buttonForeground,
                    borderRadius: UI_TOKENS.shape.borderRadius,
                    "&:hover": {
                        backgroundColor: UI_TOKENS.accent.hover,
                    },
                }}
            >
                Export
            </Button>
        </Box>
    );
}
```

##### 4. Pure Formatting Utility (`utils/tableFormatters.ts` < 40 lines)
```typescript
import { UI_TOKENS } from "../../tokens";

/**
 * Formats an ISO date string into a user-facing localized timestamp.
 */
export function formatTimestamp(isoString: string): string {
    if (!isoString) return "-";
    const date = new Date(isoString);
    return isNaN(date.getTime()) ? "-" : `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

/**
 * Computes the semantic token color corresponding to an inspection severity score.
 */
export function getSeverityColor(score: number): string {
    if (score >= 80) return UI_TOKENS.status.errorFg;
    if (score >= 50) return UI_TOKENS.status.warningFg;
    return UI_TOKENS.status.successFg;
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
| | Non-CSS renderers | Canvas, Plotly, or PDF export routines query `isDarkTheme()`. |
| | Composite MUI controls | Sliders, switches, pickers, and paper elements are wrapped in `<VertiGisThemeProvider>`. |
| **Modularity & Architecture** | File size compliance | Every file is under 150 lines (target) and strictly below 250 lines (ceiling). |
| | Directory blueprint | Complex components use `components/`, `hooks/`, `utils/`, and `types/` sub-directories. |
| | Model / View isolation | MobX Model (`*Model.ts`) contains zero JSX, React hooks, or DOM references. |
| | View resilience | React View wraps children in `<LayoutElement>` and `<ErrorBoundary>`. |
