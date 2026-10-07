# VertiGIS Studio Workflow Web SDK: Custom Activities & Form Elements

## Overview
VertiGIS Studio Workflow allows business workflows to be executed inside VertiGIS Studio Web. The Workflow Web SDK enables building:
1. **Custom Activities**: Custom backend/client execution blocks.
2. **Custom Form Elements**: Custom UI widgets embedded inside workflow forms (e.g. Star ratings, QR code scanners, Captcha, signatures).

---

## 1. Creating a Custom Workflow Activity

Activities implement `IActivityHandler`.

```typescript
// src/activities/CalculateBufferActivity/main.ts
import type { IActivityHandler } from "@vertigis/workflow";

export interface CalculateBufferInputs {
    /**
     * @displayName Input Geometry
     * @description The input geometry to buffer.
     * @required
     */
    geometry: __esri.Geometry;

    /**
     * @displayName Buffer Distance
     * @description The buffer distance in meters.
     * @required
     */
    distance: number;

    /**
     * @displayName Run Activity
     * @description Whether to run the activity. Defaults to true.
     */
    runActivity?: boolean;
}

export interface CalculateBufferOutputs {
    /**
     * @description The resulting polygon geometry.
     */
    result: __esri.Polygon | null;
}

/**
 * @displayName Calculate Buffer
 * @category Geometry Operations
 * @description Calculates a spatial buffer for given geometry.
 * @clientOnly
 * @supportedApps VSW, EXB
 */
export default class CalculateBufferActivity implements IActivityHandler {
    async execute(inputs: CalculateBufferInputs): Promise<CalculateBufferOutputs> {
        const runActivity = inputs.runActivity !== undefined ? inputs.runActivity : true;
        if (!runActivity) {
            return { result: null };
        }

        try {
            if (!inputs.geometry) {
                throw new Error("Geometry input is required.");
            }

            // Use geometryEngine for buffer calculation
            const distance = inputs.distance || 100;

            return {
                result: null // Replace with actual buffer logic
            };
        } catch (error) {
            console.error("CalculateBufferActivity failed:", error);
            throw new Error(`CalculateBufferActivity failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
}
```

---

## 2. Creating a Custom Form Element (MUI Required)

Form elements provide interactive widgets in VertiGIS Workflow forms. **Always use MUI components and VertiGIS CSS variable tokens.**

```tsx
// src/elements/RatingElement/main.tsx
import * as React from "react";
import { FormElementProps, FormElementRegistration } from "@vertigis/workflow";
import { Stack, IconButton, Typography } from "@mui/material";

export interface RatingElementProps extends FormElementProps<number> {
    maxRating?: number;
}

const styles = { root: { py: 1 } };

function RatingElement(props: RatingElementProps): React.ReactElement {
    const {
        value = 0,
        setValue,
        maxRating = 5,
        enabled = true,
        visible = true,
        readOnly = false,
    } = props;

    if (!visible) return <></>;

    const handleSelect = (rating: number) => {
        if (!enabled || readOnly) return;
        setValue(rating);
    };

    return (
        <Stack direction="row" spacing={0.5} alignItems="center" sx={styles.root} role="group" aria-label="Star Rating">
            {Array.from({ length: maxRating }).map((_, index) => {
                const starNumber = index + 1;
                const isActive = starNumber <= (value ?? 0);
                return (
                    <IconButton
                        key={starNumber}
                        disabled={!enabled || readOnly}
                        onClick={() => handleSelect(starNumber)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault();
                                handleSelect(starNumber);
                            }
                        }}
                        aria-label={`Rate ${starNumber} out of ${maxRating} stars`}
                        aria-pressed={isActive}
                        sx={{
                            color: isActive ? "var(--primaryAccent)" : "var(--primaryBorder)",
                            "&:hover": {
                                transform: enabled && !readOnly ? "scale(1.1)" : "none",
                            }
                        }}
                    >
                        ★
                    </IconButton>
                );
            })}
            <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }} aria-live="polite">
                {value ? `${value} / ${maxRating}` : "Unrated"}
            </Typography>
        </Stack>
    );
}

const RatingElementRegistration: FormElementRegistration<RatingElementProps> = {
    component: RatingElement,
    id: "RatingElement",
    getInitialProperties: () => ({
        value: 0,
        enabled: true,
        visible: true,
        readOnly: false,
        maxRating: 5,
    }),
};

export default RatingElementRegistration;
```

---

## 3. Integrating the ArcGIS API for JavaScript

VertiGIS Studio Web and Workflow share the ArcGIS API for JavaScript (`@arcgis/core`):

### Import Rules
| Module Type | Examples | Correct Import |
| :--- | :--- | :--- |
| **Class Modules** (Default Export) | `Graphic`, `Polygon`, `Point`, `FeatureLayer` | `import Graphic from "@arcgis/core/Graphic";` |
| **Utility / Function Modules** (No Default Export) | `projection`, `geometryEngine` | `import * as projection from "@arcgis/core/geometry/projection";` |

> ⚠️ **NEVER** use `import projection from "..."` or `import { load, project } from "..."` for utility modules — these cause `Unsupported AMD module` runtime errors.

### Example: Creating a Map Graphic
```typescript
import Graphic from "@arcgis/core/Graphic";
import Point from "@arcgis/core/geometry/Point";
import SimpleMarkerSymbol from "@arcgis/core/symbols/SimpleMarkerSymbol";

export async function createMarker(x: number, y: number, spatialReference: __esri.SpatialReference): Promise<Graphic> {
    const point = new Point({ x, y, spatialReference });

    const symbol = new SimpleMarkerSymbol({
        color: [226, 119, 40],   // Note: Map symbol colors are ArcGIS renderer values, not UI tokens
        outline: { color: [255, 255, 255], width: 2 }
    });

    return new Graphic({ geometry: point, symbol });
}
```
