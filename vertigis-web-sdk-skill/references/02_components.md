# VertiGIS Studio Web SDK: Custom Components

## Overview
A VertiGIS Web component consists of two synchronized parts:
1. **The Model (`*Model.ts`)**: A class extending `ComponentModelBase` (or `ItemModelBase`) that handles business logic, state, and serialization.
2. **The View (`main.tsx`)**: A React functional component wrapped in `observer()` that renders inside a `<LayoutElement>` wrapper using Material UI (MUI).

---

## 1. Creating the Component Model

The model manages the component's state, participates in app configuration, and executes actions.

```typescript
// src/components/MyWidget/MyWidgetModel.ts
import { ComponentModelBase, serializable, importModel, exportModel } from "@vertigis/web/models";
import { MapModel } from "@vertigis/web/mapping";

// Mark with @exportModel if child components need to import this model
@exportModel
@serializable
export class MyWidgetModel extends ComponentModelBase {
    // 1. Serializable properties (configurable in app-config.json)
    @serializable(String)
    greetingText: string = "Hello VertiGIS!";

    @serializable(Number)
    refreshInterval: number = 30;

    @serializable(Boolean)
    autoStart: boolean = true;

    // 2. Observable runtime state (not saved in config)
    count: number = 0;

    // 3. Inject built-in models (e.g. MapModel)
    @importModel("map-extension")
    map: MapModel | undefined;

    // Lifecycle Hook: Initialization
    protected async _onInitialize(): Promise<void> {
        await super._onInitialize();
        console.log("MyWidgetModel initialized with text:", this.greetingText);
    }

    public increment(): void {
        this.count++;
    }

    // Lifecycle Hook: Destruction / Cleanup
    protected async _onDestroy(): Promise<void> {
        await super._onDestroy();
    }
}
```

### Advanced `@serializable` Options
You can provide type constructors or custom serializer/deserializer functions for complex properties:
```typescript
@serializable(Array)
selectedIds: string[] = [];

// Custom Serializer for Date objects
@serializable({
    serializer: (val: Date) => val?.toISOString(),
    deserializer: (raw: string) => raw ? new Date(raw) : undefined
})
lastInspectedDate?: Date;
```

---

## 2. Creating the React View (MUI + LayoutElement Required)

> 📐 **Enterprise Modularity Standard**: For enterprise components, keep `main.tsx` under 150 lines (hard ceiling of 250 lines). Decompose UI elements into `components/`, stateful logic and event subscriptions into `hooks/`, and zero-dependency helpers into `utils/`. See [Design Tokens & Theming Guide](./11_design_tokens_and_theming.md#component-modularity) for the complete directory blueprint and extraction heuristics.

Views MUST:
- Use MUI components (`@mui/material`) — **NEVER use standard HTML text tags (`<span>`, `<p>`, `<h1>`-`<h6>`)**
- Use VertiGIS CSS variable tokens — **NEVER hardcode hex/RGB colors**
- Extend `LayoutElementProperties<TModel>` in props to expose parameters to the Designer
- Wrap all content inside `<LayoutElement {...props}>` — this is **REQUIRED** by the SDK
- Wrap the component function with `observer()` from MobX to enable reactive re-rendering when model observables change

### 💡 Exposing Configuration Parameters to VertiGIS Web Designer
If you want to expose configuration parameters that appear in the **VertiGIS Studio Web Designer**, you MUST extend `LayoutElementProperties<TModel>` in your React component's props interface.

```tsx
// src/components/MyWidget/main.tsx
import * as React from "react";
import { observer } from "mobx-react-lite";
import { Box, Typography, Button, Stack } from "@mui/material";
import {
    LayoutElement,
    LayoutElementProperties,
} from "@vertigis/web/components";
import { useUIContext, useService } from "@vertigis/web/ui";
import { I18nService } from "@vertigis/web/i18n";
import { ErrorBoundary } from "../../utils/ErrorBoundary";
import { MyWidgetModel } from "./MyWidgetModel";

interface MyWidgetProps extends LayoutElementProperties<MyWidgetModel> {
    /**
     * @displayName Custom Config Property
     * @description This property will automatically show up in the Web Designer.
     */
    customConfigParam?: string;
}

const MyWidget = observer(function MyWidget(props: MyWidgetProps): React.ReactElement {
    const { model, customConfigParam = "Default" } = props;

    // Direct access to UI Context commands & services in React views
    const { commands } = useUIContext();
    const i18n = useService<I18nService>("i18n");

    const handleAction = async () => {
        await commands.ui.displayNotification.execute({
            title: i18n?.translate("widget-title") || "Action",
            message: `Count incremented to ${model.count + 1}`,
            status: "info"
        });
        model.increment();
    };

    return (
        <LayoutElement {...props}>
            <ErrorBoundary fallbackMessage="Widget failed to load.">
                <Box
                    sx={{
                        p: 2,
                        backgroundColor: "var(--primaryBackground, #ffffff)",
                        borderRadius: "var(--borderRadius, 4px)",
                        border: "1px solid var(--primaryBorder, #e0e0e0)",
                    }}
                >
                    {/* Widget Title with MUI Typography */}
                    <Typography
                        variant="h6"
                        sx={{
                            color: "var(--primaryForeground, #212121)",
                            fontFamily: 'var(--defaultFont, "Roboto", "Helvetica", "Arial", sans-serif)',
                            mb: 0.5,
                        }}
                    >
                        {model.greetingText}
                    </Typography>

                    {/* Section Subtitle */}
                    <Typography
                        variant="subtitle2"
                        sx={{ color: "var(--secondaryForeground, #666666)", mb: 1.5 }}
                    >
                        Interactive Counter & Diagnostics
                    </Typography>

                    {/* Nested Container Surface */}
                    <Box
                        sx={{
                            p: 1.5,
                            mb: 2,
                            backgroundColor: "var(--secondaryBackground, #f5f5f5)",
                            border: "1px solid var(--primaryBorder, #e0e0e0)",
                            borderRadius: "var(--borderRadius, 4px)",
                        }}
                    >
                        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
                            <Typography variant="body1" sx={{ color: "var(--primaryForeground, #212121)" }}>
                                Current Count: <strong>{model.count}</strong>
                            </Typography>
                            <Typography
                                variant="overline"
                                sx={{
                                    px: 1,
                                    py: 0.25,
                                    borderRadius: "4px",
                                    backgroundColor: "var(--alertGreenBackground, #edf7ed)",
                                    color: "var(--alertGreenForeground, #2e7d32)",
                                    fontWeight: "bold",
                                }}
                            >
                                ACTIVE
                            </Typography>
                        </Stack>

                        <Typography variant="body2" sx={{ color: "var(--secondaryForeground, #666666)", mb: 1.5 }}>
                            Configuration parameter: {customConfigParam}
                        </Typography>

                        <Button
                            variant="contained"
                            onClick={handleAction}
                            sx={{
                                backgroundColor: "var(--emphasizedButtonBackground, var(--primaryAccent, #007ac2))",
                                color: "var(--buttonForeground, #ffffff)",
                                "&:hover": {
                                    backgroundColor: "var(--primaryAccentHover, #005a91)",
                                },
                            }}
                        >
                            Increment Count
                        </Button>
                    </Box>

                    {/* Microcopy / Caption Metadata */}
                    {model.map && (
                        <Typography variant="caption" sx={{ color: "var(--secondaryForeground, #666666)", display: "block" }}>
                            Attached Map ID: {model.map.id}
                        </Typography>
                    )}
                </Box>
            </ErrorBoundary>
        </LayoutElement>
    );
});

export default MyWidget;
```

---

## 3. Creating and Registering Custom SVG Icons

VertiGIS Studio Web SDK supports registering custom SVG icons for use in toolbars, menus, and components.

### 1. Define Icon (`src/icons/CustomArrowIcon.tsx`)
```tsx
import React from "react";
import createSvgIcon from "@vertigis/web/ui/icons/utils/createSvgIcon";

export default createSvgIcon(
    <path d="M20 11H7.8l5.6-5.6L12 4l-8 8 8 8 1.4-1.4L7.8 13H20v-2z" />
);
```

### 2. Register Icon in `src/index.ts`
```typescript
import { LibraryRegistry } from "@vertigis/web/config";
import CustomArrowIcon from "./icons/CustomArrowIcon";

export default function (registry: LibraryRegistry): void {
    registry.registerIcon({
        id: "myorg-custom-arrow",
        getComponentType: () => CustomArrowIcon
    });
}
```

### 3. Using Custom Icons in Views or App Config
- **In React Views**:
  ```tsx
  import DynamicIcon from "@vertigis/web/ui/DynamicIcon";
  <DynamicIcon src="myorg-custom-arrow" />
  ```
- **In `app-config.json` menus / buttons**:
  ```json
  {
    "id": "my-tool-button",
    "$type": "menu-item",
    "title": "Custom Tool",
    "icon": "myorg-custom-arrow",
    "action": "custom.my-command"
  }
  ```

---

## 4. Styling and Theming Rules

VertiGIS Studio Web enforces a strict, tokenized design architecture. Custom components must never hardcode styling values or bundle isolated CSS style sheets; they must participate directly in the host application's design system across light and dark modes.

### 4.1 Typography System

All textual content in VertiGIS Web components must be rendered through `@mui/material` `<Typography>` components. **Raw HTML text tags (`<span>`, `<p>`, `<h1>`-`<h6>`, `<strong>`, `<em>`) are strictly prohibited.**

#### MUI Typography Variant Reference
| Variant | Semantic Purpose | Typical Usage | Standard Foreground Token |
| :--- | :--- | :--- | :--- |
| `h5`, `h6` | Top-level container & widget headers | Widget titles, modal headlines, primary card headers | `var(--primaryForeground, #212121)` / `var(--primaryAccent, #007ac2)` |
| `subtitle1`, `subtitle2` | Section & group headings | Panel section titles, group headers, card subheadings | `var(--secondaryForeground, #666666)` |
| `body1` | Primary body text | Main descriptions, form labels, list item text | `var(--primaryForeground, #212121)` |
| `body2` | Secondary body text | Explanatory notes, auxiliary content, secondary descriptions | `var(--secondaryForeground, #666666)` |
| `caption` | Microcopy & metadata | Timestamps, coordinate values, data source attributions | `var(--secondaryForeground, #666666)` |
| `overline` | Status badges & category tags | Uppercase category labels, status badges, chip text | `var(--primaryForeground, #212121)` / Alert foregrounds |

#### Typography Rules & Best Practices
1. **Zero Raw HTML Text Elements**: Always replace `<p>` with `<Typography variant="body1">` or `<Typography variant="body2">`, `<span>` with `<Typography variant="caption">` or appropriate variant, and `<h1>`-`<h6>` with `<Typography variant="h5">` or `<Typography variant="h6">`.
2. **Font Family Token**: Always inherit typography via `var(--defaultFont, "Roboto", "Helvetica", "Arial", sans-serif)` (configured automatically across MUI components in the host shell).
3. **Semantic Text Color Tokens**: Pair every Typography variant with semantic foreground tokens via `sx`:
   - High-contrast text: `sx={{ color: "var(--primaryForeground, #212121)" }}`
   - Secondary / muted text: `sx={{ color: "var(--secondaryForeground, #666666)" }}`
   - Inactive / disabled text: `sx={{ color: "var(--disabledForeground, #9e9e9e)" }}`
4. **Layout Wrappers**: Use `<Box>` and `<Stack>` to arrange typography elements instead of unstructured text containers.

---

### 4.2 Color & Design Tokens System

VertiGIS Studio Web utilizes CSS custom properties (variables) dynamically injected by the host shell. These tokens automatically adapt when users switch between light and dark themes, or when custom organization branding is applied in the VertiGIS Studio Web Designer.

> 🎨 **Design Token Subsystem**: Instead of relying on raw CSS variable strings without fallbacks, import type-safe tokens from `src/tokens`:
> ```tsx
> import { UI_TOKENS, alphaMix } from "../../tokens";
> <Box sx={{ backgroundColor: UI_TOKENS.surface.primary, border: `1px solid ${UI_TOKENS.border.primary}` }} />
> ```
> For full token implementations, safe fallbacks (e.g., `var(--primaryBackground, #ffffff)`), `color-mix()` patterns, dynamic dark theme detection (`useIsDarkTheme`), and MUI `ThemeProvider` integration, see the dedicated [Design Tokens & Theming Guide](./11_design_tokens_and_theming.md).

#### Complete Token Reference Catalogue
| Token Category | CSS Variable | Semantic Usage |
| :--- | :--- | :--- |
| **Surfaces & Backgrounds** | `var(--primaryBackground, #ffffff)` | Main surface for panels, drawers, widgets, and dialogs. |
| | `var(--secondaryBackground, #f5f5f5)` | Nested cards, group containers, zebra striping, and inset areas. |
| **Borders & Dividers** | `var(--primaryBorder, #e0e0e0)` | Structural container borders, dividers, and card outlines. |
| **Foregrounds & Text** | `var(--primaryForeground, #212121)` | High-contrast text, primary icon fills, and active labels. |
| | `var(--secondaryForeground, #666666)` | Secondary text, subheadings, captions, and muted icons. |
| | `var(--disabledForeground, #9e9e9e)` | Inactive text, disabled actions, and placeholder copy. |
| **Accents & Highlights** | `var(--primaryAccent, #007ac2)` | Primary brand highlight, active tab indicators, selected item accents. |
| | `var(--primaryAccentHover, #005a91)` | Hover state for accent buttons, links, and actionable highlights. |
| **Controls & Buttons** | `var(--emphasizedButtonBackground, var(--primaryAccent, #007ac2))` | Primary CTA button background fill. |
| | `var(--buttonForeground, #ffffff)` | High-contrast text and icon color within buttons. |
| | `var(--itemHoverBackground, rgba(0, 0, 0, 0.04))` | Hover background for list items, menu items, and clickable rows. |
| | `var(--itemSelectedBackground, rgba(0, 122, 194, 0.12))` | Active or selected background for list items and tree nodes. |
| **Alerts & Status Feedback** | `var(--alertRedBackground, #fdecea)` / `var(--alertRedForeground, #d32f2f)` | Critical errors, destructive actions, failure notifications. |
| | `var(--alertGreenBackground, #edf7ed)` / `var(--alertGreenForeground, #2e7d32)` | Success confirmations, online indicators, valid states. |
| | `var(--alertAmberBackground, #fff4e5)` / `var(--alertAmberForeground, #ed6c02)` | Warnings, caveats, pending/in-progress indicators. |
| | `var(--alertGrayBackground, #f4f4f4)` / `var(--alertGrayForeground, #616161)` | Informational badges, neutral notifications, muted tags. |
| **Typography & Radius** | `var(--defaultFont, "Roboto", "Helvetica", "Arial", sans-serif)` | System font stack inherited across all typography elements. |
| | `var(--borderRadius, 4px)` | Standard corner radius for cards, buttons, and panels (default: 4px). |

#### GIS Color Selection Principles
- **Map-First Visual Hierarchy**: Keep UI chrome and panels subdued (`--primaryBackground` and `--secondaryBackground` with neutral `--primaryBorder`) so that spatial map layers, vector symbology, and GIS overlays remain the dominant visual focus.
- **Strict Zero Hardcoded Colors Rule**: NEVER use hex (`#ffffff`, `#1976d2`), RGB (`rgb(...)`), or HSL colors in components. Hardcoded colors break in dark mode, clash with custom customer branding themes, and violate enterprise theme requirements.
- **Automatic Light & Dark Theme Adaptation**: Because all tokens are dynamically defined on the root application shell, components built with CSS variable tokens transition seamlessly between light and dark themes without custom media queries (`@media (prefers-color-scheme)`) or state checks.
- **WCAG AA Contrast Compliance**: Always maintain at least a 4.5:1 contrast ratio for normal text and 3:1 for large text or graphical boundaries. Combining `--primaryForeground` with `--primaryBackground` guarantees compliance in all official VertiGIS themes.
- **No CSS Modules or External CSS**: Do NOT create `.css` or `.module.css` files. Apply token styles exclusively through MUI's `sx` prop or styled components referencing these variables.

---

## 5. Component Lifecycle Hooks

| Hook | Timing | Purpose |
| :--- | :--- | :--- |
| `_onInitialize()` | After constructor and property assignment | Async setup, subscribing to events/services, loading external data. |
| `_load()` | When component becomes active / visible | Lazy loading of heavy resources. |
| `_unload()` | When component is hidden / deactivated | Releasing temporary listeners or pausing timers. |
| `_onDestroy()` | When component is permanently removed | Tear down subscriptions, free memory. |

---

## 6. UI Context and Component Services Injection

Components can access application services and contexts in two ways:

### A. In Models via `@inject`
```typescript
import { inject } from "@vertigis/web/services";
import { I18nService } from "@vertigis/web/i18n";
import { NotificationService } from "@vertigis/web/ui";

export class MyWidgetModel extends ComponentModelBase {
    @inject("i18n")
    i18n: I18nService | undefined;

    @inject("notification")
    notification: NotificationService | undefined;

    public showNotification(): void {
        this.notification?.show({
            title: "Success",
            message: this.i18n?.translate("my-message-key") || "Operation completed.",
            status: "success"
        });
    }
}
```

### B. In React Functional Views via `useService` / `useUIContext`
```tsx
import { useService, useUIContext } from "@vertigis/web/ui";
import { I18nService } from "@vertigis/web/i18n";

export function HeaderView() {
    const i18n = useService<I18nService>("i18n");
    const { commands } = useUIContext();
    // ...
}
```

---

## 7. React Error Boundaries (Enterprise Pattern)

Wrap custom widget contents in an Error Boundary (`src/utils/ErrorBoundary.tsx`) to prevent a crashing component from taking down the VertiGIS Web application:

```tsx
// src/utils/ErrorBoundary.tsx
import * as React from "react";
import { Box, Typography } from "@mui/material";

interface Props {
    children: React.ReactNode;
    fallbackMessage?: string;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
        console.error("Widget Error:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <Box sx={{ p: 2, backgroundColor: "var(--alertRedBackground, #fdecea)", color: "var(--alertRedForeground, #d32f2f)", borderRadius: "var(--borderRadius, 4px)" }}>
                    <Typography variant="subtitle2">
                        {this.props.fallbackMessage || "This widget encountered an error."}
                    </Typography>
                    <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
                        {this.state.error?.message}
                    </Typography>
                </Box>
            );
        }
        return this.props.children;
    }
}
```

---

## 8. VertiGIS Web Component Hooks (`@vertigis/web/ui`)

In addition to MobX `observer()`, VertiGIS Studio Web provides dedicated React hooks for granular property watching, collection observation, and event bus subscriptions:

| Hook | Purpose | Example |
| :--- | :--- | :--- |
| `useWatchAndRerender(target, prop \| props[])` | Watches one or more observable model properties and triggers a re-render when they change. | `useWatchAndRerender(model, "hidden");`<br>`useWatchAndRerender(model, ["count", "status"]);` |
| `useWatchCollectionAndRerender(collection)` | Watches an ArcGIS `Collection` (`__esri.Collection`) for add/remove/reorder events and triggers a re-render. | `useWatchCollectionAndRerender(model.map.layers);` |
| `useWatch(target, prop, callback)` | Watches an observable property for mutations and executes a side-effect callback. | `useWatch(model, "selectedId", (newId, oldId) => { fetchDetails(newId); });` |
| `useWatchInit(target, prop, callback)` | Same as `useWatch`, but also runs immediately upon initial mount. | `useWatchInit(model, "activeFilter", (filter) => { applyFilter(filter); });` |
| `useSubscribeAndRerender(event)` | Subscribes to an application event bus event and triggers a re-render when fired. | `useSubscribeAndRerender(messages.events.map.click);` |
| `useSubscribe(event, callback)` | Subscribes to an event bus event and executes a callback function. | `useSubscribe(messages.events.auth.signedIn, (user) => { initUser(user); });` |

### Example: Using `useWatchAndRerender` in a Functional View
```tsx
import React from "react";
import { LayoutElement, LayoutElementProperties } from "@vertigis/web/components";
import { useWatchAndRerender } from "@vertigis/web/ui";
import { Box, Typography, Button } from "@mui/material";
import { MyWidgetModel } from "./MyWidgetModel";

export default function MyWidget(props: LayoutElementProperties<MyWidgetModel>) {
    const { model } = props;

    // Granularly watch specific model property for re-renders
    useWatchAndRerender(model, "hidden");

    return (
        <LayoutElement {...props}>
            {!model.hidden ? (
                <Box sx={{ p: 2, backgroundColor: "var(--primaryBackground, #ffffff)" }}>
                    <Typography variant="body1">Content is visible!</Typography>
                    <Button variant="contained" onClick={() => (model.hidden = true)}>
                        Hide
                    </Button>
                </Box>
            ) : (
                <Button variant="outlined" onClick={() => (model.hidden = false)}>
                    Show
                </Button>
            )}
        </LayoutElement>
    );
}
```
