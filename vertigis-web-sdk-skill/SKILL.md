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

1. **Typography System**: Strict ban on raw HTML text elements (`<span>`, `<p>`, `<h1>`-`<h6>`, `<strong>`, `<em>`). All text MUST use `@mui/material` `<Typography variant="...">` (`h5`, `h6` for widget titles; `subtitle1`, `subtitle2` for section headers; `body1`, `body2` for primary/secondary content; `caption`, `overline` for microcopy/status badges). Always pair with semantic text color tokens (`var(--primaryForeground, #1e1e1e)`, `var(--secondaryForeground, #666666)`, `var(--disabledForeground, #9e9e9e)`) and font token `var(--defaultFont)`.
2. **Color & Design Tokens Subsystem**: Strict ban on hardcoded hex (`#ffffff`, `#1976d2`), RGB (`rgb(...)`), or HSL colors for UI chrome, backgrounds, text, and borders. ALWAYS provide safe fallbacks for CSS variable tokens (e.g., `var(--primaryBackground, #ffffff)`, `var(--primaryBorder, #e0e0e0)`) to ensure resilient rendering in headless, disconnected, or preview environments. Structure component styling around a standardized `tokens/` directory (`ui.ts`, `typography.ts`, `index.ts`). Use `color-mix(in srgb, ...)` for derived tints, hover states, muted borders, and transparent overlays to adapt automatically to light and dark themes without manual CSS overrides. For non-CSS contexts (Plotly, canvas renderers, third-party iframe bridges, PDF exports), use the standalone `isDarkTheme()` utility. In React contexts, use the reactive `useIsDarkTheme()` hook and apply MUI `createTheme` overrides with `ThemeProvider` for composite controls. Keep UI chrome neutral so the GIS map remains the primary focus. Ensure WCAG AA contrast compliance (minimum 4.5:1 for normal text, 3:1 for large text) across both themes.
3. **No Custom CSS / CSS Modules**: NEVER generate `*.css` or `*.module.css` files. Minimize injected CSS. Inherit from parent styles natively via tokens and MUI `sx`.
4. **Strict Component Modularity & Anti-God-Component Architecture**: NEVER write massive monolithic "god components". Adhere to strict file size thresholds (target max 150 lines, hard ceiling of 250 lines per file; any file > 250 lines MUST be refactored). Decompose complex components using the standard 7-directory blueprint: `components/` (stateless, presentational sub-views), `hooks/` (custom React hooks for state, timers, and event subscriptions), `services/` (component-level services), `utils/` and `helpers/` (pure functions and zero-dependency helpers), `tokens/` (design tokens and theme mappings), and `types/` (interfaces and serialization models). Maintain strict separation between MobX Component Models (`*Model.ts` managing state, observables, and lifecycle hooks `_onInitialize()` / `_onDestroy()` without JSX or DOM elements) and React Views (`*.tsx` handling layout rendering, `observer()`, and `<ErrorBoundary>`). Apply extraction heuristics: decompose when JSX nesting exceeds 3 levels, extract subscriptions/listeners to hooks, and isolate pure data algorithms to utils.
5. **Exposing Properties to Designer**: To expose configuration parameters to the VertiGIS Web Designer, the React component's props interface MUST extend `LayoutElementProperties<TModel>`.
6. **LayoutElement Wrapper**: Every component view MUST wrap its content inside `<LayoutElement {...props}>` (imported from `@vertigis/web/components`) for layout slotting and Designer support.
7. **MobX Observer**: Every React component that reads model properties MUST be wrapped with `observer()` from `mobx-react-lite`.
8. **ArcGIS Import Rules**: Use default imports for class modules (`import Graphic from "@arcgis/core/Graphic"`). Use star imports for utility/function modules to avoid AMD errors (`import * as projection from "@arcgis/core/geometry/projection"`).
9. **Enterprise Reliability & Theme Safety**: Wrap custom React widgets in `ErrorBoundary` components to prevent layout crashes. All subscriptions, intervals, and MobX reactions initialized in `_onInitialize()` MUST be cleanly disposed in `_onDestroy()`. Wrap Workflow Activity `execute` blocks in `try/catch` and throw structured errors. Add `aria-label` to interactive MUI components. Ensure theme safety across dynamic light/dark switches.

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
| **Interactive Tooling** | [Scaffolding & Scripts](./references/10_interactive_scaffolding_and_tooling.md) | Discovery flow, `initiate` command (`AGENTS.md` injection), code audit checklist, SSL certificates, `start.bat`, `build.bat`. |
| **Architecture & CLI** | [Overview & Concepts](./references/01_overview_and_concepts.md) | System model, CLI scaffolding, project structure, `src/index.ts`. |
| **Custom Components** | [Components Guide](./references/02_components.md) | Component models (`*Model.ts`), React views (`*.tsx`), `LayoutElement`, `observer()`, MUI usage. |
| **Custom Services** | [Services Guide](./references/03_services.md) | Singletons, `ServiceBase`, state management, background timers, service injection. |
| **Commands & Operations** | [Commands & Operations](./references/04_commands_and_operations.md) | `registerCommandHandler`, `registerOperationHandler`, `canExecute`, built-in commands reference. |
| **Events & Observability** | [Events & Observability](./references/05_events_and_observability.md) | Lifecycle events (`app.initialized`, `map.click`), MobX observables, event subscriptions. |
| **Layout & App Config** | [Layout & Configuration](./references/06_layout_and_config.md) | `app.json` layout hierarchy, `app-config.json` model binding (`$ref`, `$eval`), theming, i18n. |
| **Workflow Web SDK** | [Workflow Web SDK](./references/07_workflow_web_sdk.md) | Custom workflow activities (`IActivityHandler`), custom form elements, ArcGIS JS API integration. |
| **Deployment** | [Deployment & Best Practices](./references/08_deployment_and_best_practices.md) | `npm run build`, hosting on CDN/SaaS, ArcGIS Enterprise items, CORS, bundling. |
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

@serializable
export class CustomWidgetModel extends ComponentModelBase {
    @serializable
    title: string = "Default Title";

    @importModel("map-extension")
    map: MapModel | undefined;

    protected async _onInitialize(): Promise<void> {
        await super._onInitialize();
    }
}
```

#### React View (`src/components/CustomWidget/main.tsx`)
```tsx
import * as React from "react";
import { observer } from "mobx-react-lite";
import { Box, Typography } from "@mui/material";
import {
    LayoutElement,
    LayoutElementProperties,
} from "@vertigis/web/components";
import { CustomWidgetModel } from "./CustomWidgetModel";

interface CustomWidgetProps extends LayoutElementProperties<CustomWidgetModel> {}

const CustomWidget = observer(function CustomWidget(props: CustomWidgetProps) {
    const { model } = props;
    return (
        <LayoutElement {...props}>
            <Box
                sx={{
                    p: 2,
                    backgroundColor: "var(--primaryBackground, #ffffff)",
                    border: "1px solid var(--primaryBorder, #e0e0e0)",
                    borderRadius: "var(--borderRadius, 4px)",
                }}
            >
                {/* Header with Typography System */}
                <Typography
                    variant="h6"
                    sx={{
                        color: "var(--primaryForeground, #212121)",
                        fontFamily: "var(--defaultFont)",
                        mb: 0.5,
                    }}
                >
                    {model.title}
                </Typography>

                <Typography
                    variant="subtitle2"
                    sx={{ color: "var(--secondaryForeground, #666666)", mb: 1.5 }}
                >
                    Component Overview & State
                </Typography>

                {/* Nested Surface with Design Tokens */}
                <Box
                    sx={{
                        p: 1.5,
                        backgroundColor: "var(--secondaryBackground, #f5f5f5)",
                        border: "1px solid var(--primaryBorder, #e0e0e0)",
                        borderRadius: "var(--borderRadius, 4px)",
                        mb: 1.5,
                    }}
                >
                    <Typography variant="body1" sx={{ color: "var(--primaryForeground, #212121)", mb: 0.5 }}>
                        Primary content description.
                    </Typography>
                    <Typography variant="body2" sx={{ color: "var(--secondaryForeground, #666666)" }}>
                        Secondary helper details and configuration info.
                    </Typography>
                </Box>

                {model.map && (
                    <Typography variant="caption" sx={{ color: "var(--secondaryForeground, #666666)", display: "block" }}>
                        Attached Map ID: {model.map.id}
                    </Typography>
                )}
            </Box>
        </LayoutElement>
    );
});

export default CustomWidget;
```

---

## 3. Tooling & Automation Scripts

This skill includes automated Python utilities in `scripts/`:
- `scripts/initiate_agents_md.py`: Automatically creates or updates the target repository's `AGENTS.md` with official VertiGIS Studio Web SDK directives enclosed between `<!-- vertigis-web-sdk:start -->` and `<!-- vertigis-web-sdk:end -->`.
- `scripts/crawl_vertigis_docs.py`: Crawl4AI script to refresh crawled documentation directly from the VertiGIS Developer Center.
