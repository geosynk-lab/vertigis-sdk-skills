# VertiGIS Studio Web SDK: Commands & Operations Reference

## Overview
Commands and Operations form the primary decoupled message bus across VertiGIS Studio Web:

- **Command**: Performs an action or side-effect. Asynchronous, returns `Promise<void>`.
- **Operation**: Calculates or retrieves data. Returns a typed value `Promise<TOutput>`.

---

## 1. Invoking Built-in Commands & Operations in Code

In any Component Model (`ComponentModelBase`, `ItemModelBase`) or Service (`ServiceBase`), use `this.messages`:

### A. Strongly-Typed Built-in Namespaces
```typescript
// 1. Command execution (void return)
await this.messages.commands.ui.displayNotification.execute({
    title: "Layer Loaded",
    message: "Inspection layer successfully refreshed.",
    status: "success"
});

// 2. Operation execution (with expected return value)
const didConfirm: boolean = await this.messages.operations.ui.confirm.execute({
    title: "Delete Feature",
    message: "Are you sure you want to delete this record?"
});

if (didConfirm) {
    await this.messages.commands.edit.deleteFeatures.execute({
        layer: inspectionLayer,
        features: [selectedFeature]
    });
}
```

### B. Generic Execution by String ID
When invoking custom commands/operations or ones without direct SDK typings:
```typescript
// Execute custom Command by string ID
await this.messages.command<MyInputType>("custom.my-command").execute(inputArgs);

// Execute custom Operation by string ID with <InputType, OutputType>
const result: MyOutputType = await this.messages.operation<MyInputType, MyOutputType>(
    "custom.my-calculation"
).execute(inputArgs);
```

---

## 2. Comprehensive Built-in Operations (with Expected Output)

Operations produce output data that can be consumed in code or passed to subsequent commands in a pipeline.

| Operation Name | Namespace | Description | Expected Input Arguments | Expected Output Type |
| :--- | :--- | :--- | :--- | :--- |
| `ui.confirm` | `ui` | Displays a confirmation modal dialog | `{ title?: string, message: string, okText?: string, cancelText?: string }` | `boolean` (true = confirmed, false = cancelled) |
| `ui.prompt` | `ui` | Displays an input prompt dialog | `{ title?: string, message: string, defaultValue?: string }` | `string \| null` |
| `arcgis.query-features` | `arcgis` | Executes a feature query against ArcGIS REST / FeatureLayer | `{ url: string, where?: string, geometry?: __esri.Geometry, outFields?: string[], spatialRelationship?: string }` | `__esri.FeatureSet` (`{ features: __esri.Graphic[] }`) |
| `arcgis.get-portal-item` | `arcgis` | Fetches metadata for an ArcGIS Portal/AGOL item | `{ id: string, portalUrl?: string }` | `__esri.PortalItem` |
| `results.convert-to-csv` | `results` | Serializes a set of features into CSV format | `{ features: __esri.Graphic[], columns?: string[] }` | `Blob \| string` |
| `results.get-selected` | `results` | Retrieves currently selected items from results panel | `{}` | `__esri.Graphic[]` |
| `map.get-visible-extent` | `map` | Gets current visible extent bounding box | `{ map?: MapModel }` | `__esri.Extent` |
| `map.get-scale` | `map` | Gets current map scale ratio | `{ map?: MapModel }` | `number` (e.g. `24000`) |
| `auth.get-user` | `auth` | Retrieves current authenticated Portal user profile | `{}` | `__esri.PortalUser \| null` |
| `geometry.buffer` | `geometry` | Computes spatial buffer around geometries | `{ geometry: __esri.Geometry, distance: number, unit?: string }` | `__esri.Polygon \| __esri.Polygon[]` |
| `geometry.project` | `geometry` | Projects geometries into a target spatial reference | `{ geometries: __esri.Geometry[], outSpatialReference: __esri.SpatialReference }` | `__esri.Geometry[]` |

---

## 3. Comprehensive Built-in Commands (Side-Effects)

Commands perform actions and side-effects.

### UI Namespace (`ui.*`)
| Command Name | Description | Expected Arguments |
| :--- | :--- | :--- |
| `ui.activate` | Activates a component, tab, or view container | `{ target: string }` |
| `ui.deactivate` | Deactivates a component or closes view | `{ target: string }` |
| `ui.toggle` | Toggles component active state | `{ target: string }` |
| `ui.display-notification` | Shows a toast notification message | `{ title?: string, message: string, status?: "info"\|"success"\|"warning"\|"error" }` |
| `ui.display-alert` | Shows a modal alert dialog | `{ title?: string, message: string }` |
| `ui.set-theme` | Sets application theme mode | `"light" \| "dark" \| string` |
| `ui.open-panel` | Opens a specific side panel or drawer | `{ target: string }` |
| `ui.close-panel` | Closes an active side panel | `{ target?: string }` |

### Map Namespace (`map.*`)
| Command Name | Description | Expected Arguments |
| :--- | :--- | :--- |
| `map.zoom-to-viewpoint` | Zooms map to an Esri Viewpoint object | `{ maps?: MapModel[], viewpoint: __esri.Viewpoint }` |
| `map.zoom-to-extent` | Zooms map to an envelope/extent | `{ maps?: MapModel[], target: __esri.Extent \| object }` |
| `map.zoom-to-features` | Centers and zooms map to fit graphics | `{ maps?: MapModel[], features: __esri.Graphic[] }` |
| `map.zoom-to-initial-viewpoint` | Resets map to initial configured extent | `{ maps?: MapModel[] }` |
| `map.zoom-in` | Zooms map in one increment level | `{ maps?: MapModel[] }` |
| `map.zoom-out` | Zooms map out one increment level | `{ maps?: MapModel[] }` |
| `map.center-at` | Centers map at a target Point geometry | `{ maps?: MapModel[], geometry: __esri.Point }` |
| `map.draw-graphic` | Draws temporary graphic on temporary map layer | `{ maps?: MapModel[], geometry: __esri.Geometry, symbol?: __esri.Symbol, attributes?: Record<string, any> }` |
| `map.clear-graphics` | Clears all temporary graphics from map | `{ maps?: MapModel[] }` |
| `map.set-layer-visibility` | Sets visibility on/off for a layer | `{ layerId: string, visible: boolean }` |
| `map.refresh-layer` | Forces redraw/refresh of a dynamic layer | `{ layerId: string }` |

### Highlights Namespace (`highlights.*`)
| Command Name | Description | Expected Arguments |
| :--- | :--- | :--- |
| `highlights.pulse` | Pulses / flashes visual highlight on features | `{ maps?: MapModel[], features: __esri.Graphic[] }` |
| `highlights.add` | Adds features to persistent highlight layer | `{ maps?: MapModel[], features: __esri.Graphic[] }` |
| `highlights.remove` | Removes specific features from highlights | `{ maps?: MapModel[], features: __esri.Graphic[] }` |
| `highlights.clear` | Clears all active highlights | `{ maps?: MapModel[] }` |

### Results Namespace (`results.*`)
| Command Name | Description | Expected Arguments |
| :--- | :--- | :--- |
| `results.display-details` | Opens feature detail card/pane | `{ features: __esri.Graphic[] }` |
| `results.remove` | Removes features from active results list | `{ features: __esri.Graphic[] }` |
| `results.clear` | Clears all results from results view | `{}` |
| `results.highlight` | Highlights results on the active map | `{ features: __esri.Graphic[] }` |

### Workflow Namespace (`workflow.*`)
| Command Name | Description | Expected Arguments |
| :--- | :--- | :--- |
| `workflow.run` | Executes a VertiGIS Studio Workflow | `{ id?: string, url?: string, inputs?: Record<string, any> }` |

### Edit Namespace (`edit.*`)
| Command Name | Description | Expected Arguments |
| :--- | :--- | :--- |
| `edit.add-feature` | Adds a new feature graphic to a feature layer | `{ layer: __esri.FeatureLayer, feature: __esri.Graphic }` |
| `edit.update-feature` | Updates an existing feature graphic | `{ layer: __esri.FeatureLayer, feature: __esri.Graphic }` |
| `edit.delete-features` | Deletes feature graphics from layer | `{ layer: __esri.FeatureLayer, features: __esri.Graphic[] }` |

### System & Auth Namespaces (`system.*`, `auth.*`)
| Command Name | Description | Expected Arguments |
| :--- | :--- | :--- |
| `auth.sign-in` | Initiates ArcGIS / Portal authentication | `{ provider?: string }` |
| `auth.sign-out` | Signs out the current user session | `{}` |
| `system.download-file` | Triggers browser file download from Blob/string | `{ data: Blob \| string, fileName: string, mimeType?: string }` |
| `system.open-url` | Navigates to a URL | `{ url: string, target?: "_blank" \| "_self" }` |
| `system.copy-to-clipboard` | Copies text string to user clipboard | `{ text: string }` |

---

## 4. Implementing Custom Commands & Operations

### Decorator Pattern in Models & Services
```typescript
import { ComponentModelBase, serializable } from "@vertigis/web/models";
import { command, operation, canExecute } from "@vertigis/web/messaging";

@serializable
export class InspectionModel extends ComponentModelBase {
    // 1. Custom Command Implementation
    @command("custom.start-inspection", { targetInactive: true })
    protected async _handleStartInspection(args: { inspectionId: string }): Promise<void> {
        console.log("Starting inspection:", args.inspectionId);
    }

    // 2. canExecute Guard for the Command
    @canExecute("custom.start-inspection")
    protected _canStartInspection(args: { inspectionId: string }): boolean {
        return Boolean(args?.inspectionId);
    }

    // 3. Custom Operation Implementation (returns value)
    @operation("custom.calculate-score")
    protected _calculateScore(args: { answers: number[] }): number {
        return args.answers.reduce((acc, curr) => acc + curr, 0);
    }
}
```

### Registration in `src/index.ts`
```typescript
import { LibraryRegistry } from "@vertigis/web/config";

export default function (registry: LibraryRegistry): void {
    // Register command handler directly or associate with model itemType
    registry.registerCommandHandler({
        name: "custom.standalone-command",
        canExecute: (args) => Boolean(args?.id),
        execute: async (args) => {
            // Standalone command execution
        }
    });

    registry.registerOperationHandler({
        name: "custom.standalone-operation",
        execute: async (args) => {
            return { result: "calculated value" };
        }
    });
}
```

### Intercepting a Host Command (Built-in Command Hooks)

Use this pattern when your component must react to a built-in command (for example `layer-comparison.set-mode`) and the host must still run its own handler. Your handler runs first, and `context.next(args)` calls the host handler.

```typescript
import { ComponentModelBase, serializable } from "@vertigis/web/models";
import { command } from "@vertigis/web/messaging";

type SetModeArgs = { active?: boolean } | boolean | undefined;
type ChainContext = { next?: (args?: unknown) => Promise<unknown> };

@serializable
export class BasemapPickerModel extends ComponentModelBase {
    compareEnabled = false;

    // targetInactive: true -> the handler also runs when the component is inactive
    // (inside a collapsed <expand>, a closed panel or an inactive tab).
    @command("layer-comparison.set-mode", { targetInactive: true })
    protected async _onLayerComparisonSetMode(args: SetModeArgs, context?: ChainContext): Promise<void> {
        // 1. Forward the SAME args to the host handler. Never call context.next() without args.
        await context?.next?.(args);
        // 2. Then update this component. Accept both payload shapes: true/false and { active }.
        const active = typeof args === "boolean" ? args : args?.active;
        this.compareEnabled = typeof active === "boolean" ? active : !this.compareEnabled;
    }

    // To change the host state from your own code, execute the command. Do not change the host directly.
    async exitCompareMode(): Promise<void> {
        if (this.messages?.hasCommand("layer-comparison.set-mode")) {
            await this.messages.commands.layerComparison.setMode.execute({ active: false });
        }
    }
}
```

In `src/index.ts`, the basemap library also declares the host command for the item type of its model:

```typescript
registry.registerCommand({
    name: "layer-comparison.set-mode",
    itemType: "etsa-basemap-picker-model",
});
```

| Pitfall | What happens | Fix |
| :--- | :--- | :--- |
| No `{ targetInactive: true }` on `@command(...)` | The handler does not run while the component is inactive, for example inside a collapsed `<expand>` or a closed panel. The host command runs, but your component does not change. | Always pass `{ targetInactive: true }` for a component that can be inactive. |
| `await context.next()` without `args` | The host handler gets `undefined` in place of its arguments. With `layer-comparison.set-mode`, VertiGIS crashes (seen in the basemap library, Issue #3). | Always forward the same object: `await context?.next?.(args)`. |
| Own state changed before `next(args)` | Your state and the host state can be different if the host handler fails. | Call `await context?.next?.(args)` first, then update your state. |
| Only one payload shape accepted | Host commands can be called with `true` / `false` or with `{ active }`. | Accept both shapes, as in the example. |

---

## 5. Declarative Pipelines & Command Chaining in `app-config.json`

Commands and operations can be chained sequentially in `app-config.json`. The output of an operation is automatically passed as input to the next command/operation in the chain:

```json
{
  "id": "export-button",
  "$type": "menu-item",
  "title": "Export Selected Features",
  "action": [
    "results.get-selected",
    "results.convert-to-csv",
    {
      "name": "system.download-file",
      "arguments": {
        "fileName": "exported_features.csv"
      }
    }
  ]
}
```
