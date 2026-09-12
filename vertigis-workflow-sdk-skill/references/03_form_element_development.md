# VertiGIS Studio Workflow SDK: Form Element Development

## 1. Form Element Canonical Pattern (MUI & Design Tokens Required)

A single `main.tsx` file defines both the component view and its registration object. **ALWAYS use MUI components (e.g., `<TextField>`, `<Box>`, `<Typography>`), centralized design tokens with guaranteed safe fallbacks, minimum 44x44px mobile touch targets, and `<FormElementErrorBoundary>` encapsulation.**

For complex elements, refer to [React Component Decomposition](./04_react_component_decomposition.md) to decompose state into `hooks/`, UI into `components/`, and tokens into `tokens/`.

```tsx
// src/elements/<Name>/main.tsx
import * as React from "react";
import { FormElementProps, FormElementRegistration } from "@vertigis/workflow";
import { Box, TextField, Typography } from "@mui/material";
import { tokens } from "./tokens";
import { FormElementErrorBoundary } from "./components/FormElementErrorBoundary";

/**
 * Interface defining the element's public props and state.
 * T is the type of primary value the element produces.
 */
export interface MyElementProps extends FormElementProps<string> {
    /** Custom configurable property */
    customPlaceholder?: string;
    /** Secondary public output property */
    secondaryStatus?: string;
}

/**
 * @displayName My Element Display Name
 * @description Configurable custom input element for Workflow forms.
 */
function MyElementView(props: MyElementProps): React.ReactElement | null {
    const {
        value,
        setValue,
        setProperty,
        customPlaceholder = "Enter value...",
        enabled = true,   // Always destructure with safe default
        visible = true,   // Always destructure with safe default
        readOnly = false, // Always destructure with safe default
    } = props;

    // 1. Respect visible prop
    if (!visible) {
        return null;
    }

    const handleChange = (newVal: string) => {
        setValue(newVal);
        // Update secondary public property accessible in workflow
        setProperty("secondaryStatus", newVal.length >= 6 ? "Valid" : "Too short");
    };

    // 2. Render UI with Typography variants, tokenized container, mobile touch targets & standard prop wiring
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
            {/* Header section showcasing Typography System */}
            <Box>
                <Typography
                    variant="subtitle1"
                    sx={{
                        color: tokens.ui.text.primary,
                        fontFamily: tokens.typography.fontFamily.primary,
                        fontWeight: tokens.typography.fontWeight.semibold,
                    }}
                >
                    Custom Inspection Field
                </Typography>
                <Typography
                    variant="body2"
                    sx={{
                        color: tokens.ui.text.secondary,
                        fontFamily: tokens.typography.fontFamily.primary,
                    }}
                >
                    Enter the field inspection value. Changes persist across workflow form tabs.
                </Typography>
            </Box>

            {/* Input Field with Mobile Touch Target (minHeight: 44px) and State Wiring */}
            <TextField
                fullWidth
                variant="outlined"
                placeholder={customPlaceholder}
                value={value ?? ""}
                disabled={!enabled}
                helperText={
                    <Typography
                        variant="caption"
                        sx={{
                            color: !enabled
                                ? tokens.ui.text.disabled
                                : tokens.ui.text.secondary,
                        }}
                    >
                        Required minimum 6 characters for valid status.
                    </Typography>
                }
                inputProps={{
                    readOnly,
                    "aria-label": "Custom Input Field",
                    style: { minHeight: "24px" },
                }}
                onChange={(e) => handleChange(e.currentTarget.value)}
                sx={{
                    backgroundColor: readOnly
                        ? tokens.ui.surface.secondary
                        : tokens.ui.surface.primary,
                    borderRadius: tokens.ui.shape.borderRadius,
                    "& .MuiInputBase-root": {
                        minHeight: tokens.ui.touch.minHeight, // Mobile 44x44px touch target compliance
                    },
                    "& .MuiInputBase-input": {
                        color: !enabled
                            ? tokens.ui.text.disabled
                            : tokens.ui.text.primary,
                        fontFamily: tokens.typography.fontFamily.primary,
                        fontSize: tokens.typography.fontSize.body2, // Minimum 14px for outdoor readability
                    },
                    "& .MuiOutlinedInput-root": {
                        "& fieldset": {
                            borderColor: tokens.ui.border.primary,
                        },
                        "&:hover fieldset": {
                            borderColor: tokens.ui.accent.primary,
                        },
                        "&.Mui-focused fieldset": {
                            borderColor: tokens.ui.accent.primary,
                        },
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

---

## 2. Managing Multiple Public Outputs (`props.setProperty`)

In addition to the primary `value` (updated via `props.setValue()`), form elements can expose multiple custom properties accessible to the workflow runtime:

```tsx
interface DateRangePickerProps extends FormElementProps<string> {
    startDate?: string;
    endDate?: string;
    durationDays?: number;
}

function DateRangePicker(props: DateRangePickerProps) {
    const { setValue, setProperty, enabled } = props;

    const handleSelectRange = (start: string, end: string, days: number) => {
        // 1. Set primary output string
        setValue(`${start} to ${end}`);

        // 2. Set individual named public properties
        setProperty("startDate", start);
        setProperty("endDate", end);
        setProperty("durationDays", days);
    };

    // ...
}
```
In the Workflow Designer, you can read these secondary values at any time using the **Get Form Element Property** activity by specifying property name (e.g. `"startDate"`).

---

## 3. Firing Custom Events (`raiseEvent` with Structured Payload)

If your form element needs to trigger custom logic or branching in the workflow (e.g. a "Scan Barcode" or "Calculate Route" button), use `props.raiseEvent("custom", eventData)`.

```tsx
import * as React from "react";
import { FormElementProps, FormElementRegistration } from "@vertigis/workflow";
import { Button } from "@mui/material";
import { tokens } from "./tokens";

export interface ScannerProps extends FormElementProps<string> {}

/**
 * @displayName Barcode Scanner
 * @description A custom scanner element.
 * @event custom Fired when a barcode scan completes.
 */
function ScannerElement(props: ScannerProps) {
    const { raiseEvent, setValue, enabled } = props;

    const handleScanComplete = async (scannedCode: string) => {
        setValue(scannedCode);

        // Raise structured custom event for Workflow Designer branching
        await raiseEvent("custom", {
            customEventType: "scanCompleted",
            barcode: scannedCode,
            timestamp: new Date().toISOString(),
        });
    };

    return (
        <Button
            variant="contained"
            disabled={!enabled}
            onClick={() => handleScanComplete("123456789")}
            sx={{
                minHeight: tokens.ui.touch.minHeight, // Minimum 44x44px mobile touch target
                backgroundColor: tokens.ui.control.buttonBackground,
                color: tokens.ui.control.buttonForeground,
                "&:hover": {
                    backgroundColor: tokens.ui.accent.hover,
                },
            }}
        >
            Simulate Scan
        </Button>
    );
}
```

---

## 4. Form Element Props API Reference

| Prop / Callback | Type | Purpose |
| :--- | :--- | :--- |
| `value` | `T` | The primary public value (retrieved via *Get Form Element Property*). |
| `setValue(v: T)` | `(v: T) => void` | Updates the primary public value in workflow runtime. |
| `setProperty(name, v)` | `(k: string, v: any) => void` | Updates named secondary public properties. |
| `raiseEvent(name, data)` | `(name: string, data: any) => void` | Fires a custom event to the workflow runtime. |
| `enabled` | `boolean` | Interactivity toggle (*Set Form Element* → `enabled`). |
| `visible` | `boolean` | Visibility toggle (*Set Form Element* → `visible`). |
| `readOnly` | `boolean` | Read-only mode toggle (*Set Form Element* → `readOnly`). |

---

## 5. State Separation: Local State (`useState`) vs Public State (`setValue` / `setProperty`)

- **Use Local State (`useState`)**: For transient UI interactions only (e.g. `isDropdownOpen`, `activeTab`, `hoveredIndex`, `tempSearchQuery`). This state does NOT need to be seen by the workflow.
- **Use Public State (`setValue` / `setProperty`)**: For data that workflow steps or other form elements need to inspect (e.g. `selectedFeatureId`, `formData`, `status`).

---

## 6. CRITICAL — Wiring Standard Props to MUI

The workflow runtime injects `enabled`, `visible`, and `readOnly` automatically. You MUST forward them to the UI:

| Prop | Target HTML / MUI Prop | Rule |
| :--- | :--- | :--- |
| `enabled` | `disabled={!enabled}` | Inverted boolean for standard HTML / MUI |
| `readOnly` | `inputProps={{ readOnly }}` | Forwarded to `inputProps` on MUI components |
| `visible` | `if (!visible) return null;` | Conditionally hides DOM element |

---

## 7. CRITICAL — Surviving Tab Changes & Remounts

When workflow forms switch tabs or reload steps, form elements unmount and remount.
1. **Always persist critical state in `setValue(...)` or `setProperty(...)`** instead of keeping it strictly in local `useState`.
2. **Rehydrate on mount**: On initial render/mount, initialize state from `props.value` before falling back to initial defaults.
3. **Never overwrite saved state with initial defaults** on remount.
