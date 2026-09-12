# VertiGIS Studio Workflow SDK: React Component Decomposition & Anti-God-Component Architecture

## Overview & Architecture

When developing custom form elements for VertiGIS Studio Workflow (such as feature inspection forms, spatial query builders, defect checklists, or geometry sketch editors), components quickly degrade into monolithic "god components" exceeding 300–800 lines if state, UI, API calls, and styling are bundled into a single file.

Monolithic form elements introduce critical problems:
1. **Unmaintainable State & Remount Loss**: When workflow steps or form tabs switch, un-encapsulated state is easily lost or desynchronized from `props.setValue()`.
2. **Review & Test Fragility**: Large files intermix React state hooks with presentation rendering, preventing isolated unit testing of business logic.
3. **Theming & Mobile Failure**: When styling is inlined across hundreds of JSX lines, dark theme adaptation and 44x44px touch targets are inconsistently implemented.

To guarantee maintainability, testability, and resilience across Web and Mobile hosts, all custom form elements must adhere to the **7-directory decomposition blueprint** and strict file size ceilings.

---

## 1. File Size Ceilings & Heuristics

- **Target Line Count**: Keep all source files under **150 lines**.
- **Hard Ceiling**: **250 lines absolute maximum** for any single file. Any file approaching 250 lines MUST be refactored into sub-components, custom hooks, or utility modules.

### Extraction Heuristics

| Smell in Form Element | Extraction Action | Destination |
| :--- | :--- | :--- |
| File exceeds 200 lines | Extract visual sub-sections into stateless presentational components | `components/` |
| Multiple `useState`, `useEffect`, or SDK subscriptions | Extract stateful logic, debounce timers, or workflow listeners into a custom hook | `hooks/` |
| Inline styling calculations or color constants | Centralize into design token definitions with safe fallbacks | `tokens/` |
| Pure data transformations, math, geometry, or formatters | Extract to pure functions with zero React dependencies | `utils/` |
| Shared prop interfaces, union types, domain models | Extract into dedicated type definitions | `types/` |

---

## 2. Standard 7-Directory Blueprint

```text
src/elements/<ElementName>/
├── main.tsx                  ← Orchestrator (max 150 lines): wires hooks + renders sub-components + registration
├── hooks/                    ← State management, event listeners, SDK effects
│   ├── index.ts              ← Barrel export
│   ├── useIsDarkTheme.ts     ← Reactive dark/light theme detection hook
│   └── useSketchLogic.ts     ← Stateful form element business logic
├── components/               ← Focused, stateless presentational sub-components using MUI (max 150 lines each)
│   ├── index.ts              ← Barrel export
│   ├── FormElementErrorBoundary.tsx ← Crash protection wrapper
│   ├── StatusBar.tsx         ← State/status pill presentation
│   └── ActionButtons.tsx     ← Mobile touch-friendly action bar
├── tokens/                   ← Design tokens with safe fallbacks & theme bridge
│   ├── index.ts              ← Barrel export & color-mix utilities
│   ├── ui.ts                 ← Semantic surfaces, borders, text, status tokens
│   └── typography.ts         ← Font family, scale, and line-height tokens
├── utils/                    ← Pure helper functions, defaults, formatters
│   ├── defaults.ts           ← Initial configuration constants
│   └── formatters.ts         ← Unit conversion and display helpers
├── services/                 ← External API clients, storage, or query services (if needed)
└── types/                    ← Domain models, props, and schema definitions
    ├── index.ts
    └── types.ts
```

---

## 3. Pillar 1: Custom Hooks (`hooks/`)

Extract complex stateful logic, asynchronous calls, and ArcGIS/VertiGIS subscriptions out of JSX into testable React hooks:

```typescript
// src/elements/SketchWidget/hooks/useSketchLogic.ts
import * as React from "react";

export interface UseSketchLogicReturn {
    activeTool: string;
    setActiveTool: (tool: string) => void;
    featureCount: number;
    handleDrawComplete: (geometry: Record<string, unknown>) => void;
    handleClear: () => void;
}

export function useSketchLogic(
    initialValue: string | undefined,
    onValueChange: (val: string) => void
): UseSketchLogicReturn {
    const [activeTool, setActiveTool] = React.useState<string>("polygon");
    const [featureCount, setFeatureCount] = React.useState<number>(0);

    const handleDrawComplete = React.useCallback(
        (geometry: Record<string, unknown>) => {
            setFeatureCount((prev) => prev + 1);
            onValueChange(JSON.stringify(geometry));
        },
        [onValueChange]
    );

    const handleClear = React.useCallback(() => {
        setFeatureCount(0);
        onValueChange("");
    }, [onValueChange]);

    return {
        activeTool,
        setActiveTool,
        featureCount,
        handleDrawComplete,
        handleClear,
    };
}
```

---

## 4. Pillar 2: Presentation Sub-Components (`components/`)

Break large JSX templates into single-responsibility, stateless presentation components using MUI (`@mui/material`) and centralized tokens:

```tsx
// src/elements/SketchWidget/components/StatusBar.tsx
import * as React from "react";
import { Stack, Typography, LinearProgress } from "@mui/material";
import { tokens } from "../tokens";

export interface StatusBarProps {
    statusText: string;
    isProcessing: boolean;
}

export function StatusBar({ statusText, isProcessing }: StatusBarProps) {
    return (
        <Stack
            spacing={1}
            sx={{
                p: 1.5,
                backgroundColor: tokens.ui.surface.secondary,
                border: `1px solid ${tokens.ui.border.primary}`,
                borderRadius: tokens.ui.shape.borderRadius,
            }}
        >
            <Typography
                variant="caption"
                sx={{
                    color: tokens.ui.text.secondary,
                    fontFamily: tokens.typography.fontFamily.primary,
                    fontWeight: tokens.typography.fontWeight.medium,
                }}
            >
                {statusText}
            </Typography>
            {isProcessing && <LinearProgress color="primary" sx={{ borderRadius: 1 }} />}
        </Stack>
    );
}
```

```tsx
// src/elements/SketchWidget/components/ActionButtons.tsx
import * as React from "react";
import { Stack, Button } from "@mui/material";
import { tokens } from "../tokens";

export interface ActionButtonsProps {
    enabled: boolean;
    readOnly: boolean;
    onClear: () => void;
    onSubmit: () => void;
}

export function ActionButtons({ enabled, readOnly, onClear, onSubmit }: ActionButtonsProps) {
    const isInteractive = enabled && !readOnly;

    return (
        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Button
                variant="outlined"
                disabled={!isInteractive}
                onClick={onClear}
                sx={{
                    borderColor: tokens.ui.border.primary,
                    color: tokens.ui.text.primary,
                    minHeight: tokens.ui.touch.minHeight, // 44px mobile touch target
                    "&:hover": {
                        borderColor: tokens.ui.accent.primary,
                        backgroundColor: tokens.alphaMix(tokens.ui.accent.primary, 8),
                    },
                }}
            >
                Clear Sketch
            </Button>
            <Button
                variant="contained"
                disabled={!isInteractive}
                onClick={onSubmit}
                sx={{
                    backgroundColor: tokens.ui.control.buttonBackground,
                    color: tokens.ui.control.buttonForeground,
                    minHeight: tokens.ui.touch.minHeight,
                    "&:hover": {
                        backgroundColor: tokens.ui.accent.hover,
                    },
                }}
            >
                Accept Geometry
            </Button>
        </Stack>
    );
}
```

Always include a clean barrel export `components/index.ts`:
```typescript
export * from "./StatusBar";
export * from "./ActionButtons";
export * from "./FormElementErrorBoundary";
```

---

## 5. Pillar 3: Error Boundary Wrapper (`components/FormElementErrorBoundary.tsx`)

In enterprise workflow forms, an unhandled exception inside a custom element must never crash the entire host application or discard user data in other steps:

```tsx
import * as React from "react";
import { Box, Typography, Button } from "@mui/material";
import { tokens } from "../tokens";

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    hasError: boolean;
    errorMessage: string;
}

export class FormElementErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, errorMessage: "" };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, errorMessage: error?.message || "Unknown error occurred" };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
        console.error("Custom FormElement error:", error, errorInfo);
    }

    handleReset = (): void => {
        this.setState({ hasError: false, errorMessage: "" });
    };

    render(): React.ReactNode {
        if (this.state.hasError) {
            return (
                <Box
                    sx={{
                        p: 2,
                        backgroundColor: tokens.ui.status.errorBg,
                        border: `1px solid ${tokens.ui.status.errorBorder}`,
                        borderRadius: tokens.ui.shape.borderRadius,
                    }}
                >
                    <Typography variant="subtitle2" sx={{ color: tokens.ui.status.errorFg, fontWeight: "bold" }}>
                        Widget Display Error
                    </Typography>
                    <Typography variant="caption" sx={{ color: tokens.ui.text.primary, display: "block", my: 1 }}>
                        {this.state.errorMessage}
                    </Typography>
                    <Button
                        size="small"
                        variant="outlined"
                        onClick={this.handleReset}
                        sx={{ color: tokens.ui.status.errorFg, borderColor: tokens.ui.status.errorBorder }}
                    >
                        Retry Widget
                    </Button>
                </Box>
            );
        }
        return this.props.children;
    }
}
```

---

## 6. Pillar 4: Orchestration in `main.tsx`

`main.tsx` serves purely as an orchestrator (typically under 100 lines). It wires custom hooks, renders decomposed presentation sub-components inside `<FormElementErrorBoundary>`, and registers the element with the workflow engine:

```tsx
// src/elements/SketchWidget/main.tsx
import * as React from "react";
import { FormElementRegistration } from "@vertigis/workflow";
import { Box } from "@mui/material";
import { tokens } from "./tokens";
import { useSketchLogic } from "./hooks";
import { StatusBar, ActionButtons, FormElementErrorBoundary } from "./components";
import { SketchWidgetProps } from "./types";

function SketchWidgetView(props: SketchWidgetProps): React.ReactElement | null {
    const { value, setValue, enabled = true, visible = true, readOnly = false } = props;
    const { activeTool, setActiveTool, featureCount, handleClear } = useSketchLogic(value, setValue);

    if (!visible) {
        return null;
    }

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
            <StatusBar
                statusText={`Active Tool: ${activeTool} (${featureCount} features drawn)`}
                isProcessing={false}
            />
            <ActionButtons
                enabled={enabled}
                readOnly={readOnly}
                onClear={handleClear}
                onSubmit={() => setValue(JSON.stringify({ activeTool, featureCount }))}
            />
        </Box>
    );
}

export function SketchWidget(props: SketchWidgetProps): React.ReactElement {
    return (
        <FormElementErrorBoundary>
            <SketchWidgetView {...props} />
        </FormElementErrorBoundary>
    );
}

const SketchWidgetRegistration: FormElementRegistration<SketchWidgetProps> = {
    component: SketchWidget,
    id: "SketchWidget",
    getInitialProperties: () => ({
        value: undefined,
        enabled: true,
        visible: true,
        readOnly: false,
    }),
};

export default SketchWidgetRegistration;
```
