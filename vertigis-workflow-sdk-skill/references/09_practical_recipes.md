# VertiGIS Studio Workflow SDK: Practical Recipes & Templates

## Recipe 1: Complex Map Activity with Geometry Projection

An activity that accepts an input geometry, projects it to Web Mercator (WKID 3857), and adds it to the active map using `MapProvider`.

### `src/activities/AddProjectedGraphic/tokens/symbols.ts`
```typescript
export const GRAPHIC_SYMBOL_TOKENS = {
  fill: "rgba(0, 120, 255, 0.4)",
  outline: [0, 80, 200, 1],
  outlineWidth: 1.5,
};
```

### `src/activities/AddProjectedGraphic/main.ts`
```typescript
import { MapProvider } from "@vertigis/workflow/activities/arcgis/MapProvider";
import { activate } from "@vertigis/workflow/Hooks";
import type { IActivityHandler, IActivityContext } from "@vertigis/workflow/IActivityHandler";
import * as projection from "@arcgis/core/geometry/projection";
import Graphic from "@arcgis/core/Graphic";
import SimpleFillSymbol from "@arcgis/core/symbols/SimpleFillSymbol";
import SpatialReference from "@arcgis/core/geometry/SpatialReference";
import { GRAPHIC_SYMBOL_TOKENS } from "./tokens/symbols";

interface AddProjectedGraphicInputs {
  /**
   * @displayName Input Geometry
   * @description The ArcGIS geometry to project and draw.
   * @required
   */
  geometry: __esri.Geometry;

  /**
   * @displayName Fill Color
   * @description Color of the drawn graphic fill (e.g. 'rgba(0, 120, 255, 0.5)').
   */
  fillColor?: string;

  /**
   * @displayName Run Activity
   * @description Whether to execute this activity. Defaults to true.
   */
  runActivity?: boolean;

  /**
   * @displayName Show Logger
   * @description Enable debug logging in the browser console.
   */
  showLogger?: boolean;
}

interface AddProjectedGraphicOutputs {
  /**
   * @description Whether the graphic was successfully added to the map.
   */
  success: boolean;
}

/**
 * @displayName Add Projected Graphic
 * @category Mapping Utilities
 * @description Projects geometry to Web Mercator and displays it on the active map.
 * @clientOnly
 * @supportedApps VSW, EXB
 */
@activate(MapProvider)
export default class AddProjectedGraphicActivity implements IActivityHandler {
  async execute(
    inputs: AddProjectedGraphicInputs,
    _context: IActivityContext,
    type: typeof MapProvider
  ): Promise<AddProjectedGraphicOutputs> {
    try {
      const { showLogger = false, fillColor = GRAPHIC_SYMBOL_TOKENS.fill } = inputs;

      const runActivity = inputs.runActivity !== undefined ? inputs.runActivity : true;
      if (!runActivity) {
        if (showLogger) console.log("AddProjectedGraphicActivity skipped.");
        return { success: false };
      }

      if (!inputs.geometry) {
        throw new Error("Input geometry is required.");
      }

      // Load projection engine
      await projection.load();

      const targetSR = new SpatialReference({ wkid: 3857 });
      const projectedGeom = projection.project(inputs.geometry, targetSR) as __esri.Geometry;

      const mapProvider = type.create();
      await mapProvider.load();

      const view = mapProvider.view as __esri.MapView;
      if (!view) {
        throw new Error("Active MapView is not available.");
      }

      const graphic = new Graphic({
        geometry: projectedGeom,
        symbol: new SimpleFillSymbol({
          color: fillColor as any,
          outline: { color: GRAPHIC_SYMBOL_TOKENS.outline, width: GRAPHIC_SYMBOL_TOKENS.outlineWidth },
        }),
      });

      view.graphics.add(graphic);
      if (showLogger) console.log("Graphic successfully added to map view.");

      return { success: true };
    } catch (error) {
      throw new Error(`AddProjectedGraphicActivity failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}
```

---

## Recipe 2: Decomposed Form Element with MUI and Props Wiring

A production-quality Star Rating form element respecting `enabled`, `visible`, and `readOnly`, with state recovery across tab changes, built entirely with MUI components.

### `src/elements/StarRating/main.tsx`
```tsx
import * as React from "react";
import { FormElementProps, FormElementRegistration } from "@vertigis/workflow";
import { Stack, IconButton, Typography } from "@mui/material";
import { FormElementErrorBoundary } from "./components/FormElementErrorBoundary";
// Note: In a real project, you would import icons from @mui/icons-material
// e.g., import StarIcon from '@mui/icons-material/Star';
// For this example, we use a simple text character inside the icon button.

export interface StarRatingProps extends FormElementProps<number> {
  /** Maximum number of stars */
  maxStars?: number;
}

function StarRatingView(props: StarRatingProps): React.ReactElement | null {
  const {
    value = 0,
    setValue,
    maxStars = 5,
    enabled = true,
    visible = true,
    readOnly = false,
  } = props;

  if (!visible) return null;

  const handleSelect = (starIndex: number) => {
    if (!enabled || readOnly) return;
    setValue(starIndex);
  };

  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 1 }} role="group" aria-label="Star Rating">
      <Stack direction="row" spacing={0.5}>
        {Array.from({ length: maxStars }).map((_, i) => {
          const starNumber = i + 1;
          const isActive = starNumber <= (value ?? 0);
          return (
            <IconButton
              key={starNumber}
              disabled={!enabled}
              onClick={() => handleSelect(starNumber)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleSelect(starNumber);
                }
              }}
              aria-label={`Rate ${starNumber} out of ${maxStars} stars`}
              aria-pressed={isActive}
              sx={{
                color: isActive ? "var(--primaryAccent)" : "var(--primaryBorder)",
                transition: "transform 0.1s ease",
                "&:hover": {
                  transform: enabled && !readOnly ? "scale(1.1)" : "none",
                }
              }}
            >
              ★
            </IconButton>
          );
        })}
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }} aria-live="polite">
        {value ? `${value} / ${maxStars}` : "Unrated"}
      </Typography>
    </Stack>
  );
}

export function StarRating(props: StarRatingProps): React.ReactElement {
  return (
    <FormElementErrorBoundary>
      <StarRatingView {...props} />
    </FormElementErrorBoundary>
  );
}

const StarRatingRegistration: FormElementRegistration<StarRatingProps> = {
  component: StarRating,
  id: "StarRating",
  getInitialProperties: () => ({
    value: 0,
    enabled: true,
    visible: true,
    readOnly: false,
    maxStars: 5,
  }),
};

export default StarRatingRegistration;
```
