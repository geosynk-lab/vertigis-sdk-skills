# VertiGIS Studio Web SDK: Common Tutorials & Recipes

This guide contains complete recipes for common VertiGIS Studio Web customization tasks.

---

## Recipe 1: Changing Default Map Click Behavior

Intercept map clicks to perform a custom query or custom action instead of default identify.

### Model Implementation
```typescript
import { ComponentModelBase, importModel } from "@vertigis/web/models";
import { MapModel } from "@vertigis/web/mapping";
import { UnsubscribeHandle } from "@vertigis/web/events";

export class CustomMapClickHandlerModel extends ComponentModelBase {
    @importModel("map-extension")
    map: MapModel | undefined;

    private _mapClickSub: UnsubscribeHandle | undefined;

    protected async _onInitialize(): Promise<void> {
        await super._onInitialize();

        // Subscribe to map clicks
        this._mapClickSub = this.messages.events.map.click.subscribe(async (args) => {
            if (args.map === this.map) {
                console.log("Clicked at coordinate:", args.geometry);
                
                // Show notification with coordinates
                await this.messages.commands.ui.displayNotification.execute({
                    title: "Coordinates",
                    message: `Lat: ${args.geometry.y.toFixed(4)}, Lon: ${args.geometry.x.toFixed(4)}`,
                    status: "info"
                });
            }
        });
    }

    protected async _onDestroy(): Promise<void> {
        this._mapClickSub?.();
        await super._onDestroy();
    }
}
```

---

## Recipe 2: Custom Component with Configurable App-Config Properties

Create a widget whose title and refresh rate can be edited in VertiGIS Designer or `app-config.json`. **Notice the use of MUI and VertiGIS tokens.**

### 1. Model
```typescript
// src/components/DashboardWidget/DashboardWidgetModel.ts
import { ComponentModelBase, serializable } from "@vertigis/web/models";

@serializable
export class DashboardWidgetModel extends ComponentModelBase {
    @serializable
    title: string = "Operational Dashboard";

    @serializable
    refreshIntervalSeconds: number = 30;
}
```

### 2. React View (MUI + LayoutElement + observer)
```tsx
// src/components/DashboardWidget/main.tsx
import * as React from "react";
import { observer } from "mobx-react-lite";
import { Box, Typography, Divider } from "@mui/material";
import {
    LayoutElement,
    LayoutElementProperties,
} from "@vertigis/web/components";
import { ErrorBoundary } from "../../utils/ErrorBoundary";
import { DashboardWidgetModel } from "./DashboardWidgetModel";
import "./DashboardWidget.css";

interface DashboardWidgetProps extends LayoutElementProperties<DashboardWidgetModel> {}

const DashboardWidget = observer(function DashboardWidget(props: DashboardWidgetProps) {
    const { model } = props;
    return (
        <LayoutElement {...props}>
            <ErrorBoundary fallbackMessage="Dashboard widget failed to load.">
                <Box className="DashboardWidget">
                    <Typography variant="h6" sx={{ mb: 1 }}>
                        {model.title}
                    </Typography>
                    <Divider sx={{ borderColor: "var(--primaryBorder)", my: 1 }} />
                    <Typography variant="body2" color="text.secondary">
                        Auto-refresh interval: {model.refreshIntervalSeconds}s
                    </Typography>
                </Box>
            </ErrorBoundary>
        </LayoutElement>
    );
});

export default DashboardWidget;
```

```css
/* src/components/DashboardWidget/DashboardWidget.css */
.DashboardWidget {
    padding: var(--spacingLg, 16px);
    border-top: 4px solid var(--primaryAccent, #007ac2);
    border-radius: var(--borderRadius, 4px);
    background-color: var(--secondaryBackground, #f5f5f5);
}
```

### 3. Registration (`src/index.ts`)
```typescript
registry.registerComponent({
    name: "dashboard-widget",
    namespace: "custom.analytics",
    getComponentType: () => DashboardWidget,
    itemType: "dashboard-widget-model",
    getItemType: () => DashboardWidgetModel,
    title: "Dashboard Widget"
});
```

---

## Recipe 3: Running a Workflow Programmatically from Code

Execute a VertiGIS Workflow and pass input parameters:

```typescript
export async function runInspectionWorkflow(
    messages: any,
    workflowId: string,
    facilityId: string
): Promise<void> {
    await messages.commands.workflow.run.execute({
        id: workflowId,
        inputs: {
            FacilityID: facilityId,
            Source: "SDK Custom Component"
        }
    });
}
```
