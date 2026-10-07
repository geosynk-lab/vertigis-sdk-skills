# VertiGIS Studio Web SDK: Events & Observability

## Overview
VertiGIS Studio Web provides an event system for listening to application milestones, user actions, and state changes, as well as MobX-backed reactive data binding.

---

## 1. Application Lifecycle Events

During initialization and runtime, the application emits lifecycle events:

```
[app.initializing]
       │
       ▼
[auth.signed-in] (or anonymous session)
       │
       ▼
[map.initializing] ──► [map.initialized]
       │
       ▼
[app.initialized]
       │
       ▼
[app.loaded] (UI rendered and interactive)
```

### Key Core Events

| Event Name | Emitted When | Payload |
| :--- | :--- | :--- |
| `app.initializing` | Application starts booting | App metadata |
| `app.initialized` | All components and services registered | App instance |
| `map.initialized` | A map model has finished loading its webmap | `{ map: MapModel }` |
| `map.click` | User clicks on the map | `{ map: MapModel, geometry: Point }` |
| `ui.activated` | A UI component is opened / focused | `{ target: string }` |
| `auth.signed-in` | User successfully authenticates | `{ user: UserProfile }` |

---

## 2. Subscribing to Events in Custom Code

Use the `messages.events` bus to subscribe and unsubscribe:

```typescript
import { ComponentModelBase } from "@vertigis/web/models";
import { UnsubscribeHandle } from "@vertigis/web/events";

export class MapWatcherModel extends ComponentModelBase {
    private _clickSubscription: UnsubscribeHandle | undefined;

    protected async _onInitialize(): Promise<void> {
        await super._onInitialize();

        // Subscribe to map click event
        this._clickSubscription = this.messages.events.map.click.subscribe((eventArgs) => {
            console.log("Map clicked at coordinate:", eventArgs.geometry.x, eventArgs.geometry.y);
            this.handleMapClick(eventArgs);
        });
    }

    private handleMapClick(args: any): void {
        // Run custom logic on map click
    }

    protected async _onDestroy(): Promise<void> {
        // Always clean up subscriptions
        if (this._clickSubscription) {
            this._clickSubscription();
        }
        await super._onDestroy();
    }
}
```

---

## 3. Subscribing to Events via App Config (`app-config.json`)

You can wire events directly to commands declaratively without writing code:

```json
{
  "id": "event-subscriber-config",
  "itemType": "event-subscription",
  "event": "map.click",
  "action": {
    "name": "ui.display-notification",
    "arguments": {
      "message": "You clicked on the map!",
      "status": "info"
    }
  }
}
```

---

## 4. State Observability (MobX)

VertiGIS models use MobX observables. React components re-render automatically when observable properties change:

```typescript
import { ComponentModelBase, serializable } from "@vertigis/web/models";
import { observable, action } from "mobx";

export class LiveDataModel extends ComponentModelBase {
    @observable
    public items: string[] = [];

    @action
    public addItem(item: string): void {
        this.items.push(item);
    }
}
```

### CRITICAL — React Views Must Use `observer()`

For React components to re-render when MobX `@observable` or `@serializable` properties change, you MUST wrap the component function with `observer()` from `mobx-react-lite`:

```tsx
import { observer } from "mobx-react-lite";
import { LayoutElement, LayoutElementProperties } from "@vertigis/web/components";
import { ErrorBoundary } from "../../utils/ErrorBoundary";
import { LiveDataModel } from "./LiveDataModel";
import { Typography, List, ListItem, ListItemText } from "@mui/material";

interface LiveDataWidgetProps extends LayoutElementProperties<LiveDataModel> {}

const LiveDataWidget = observer(function LiveDataWidget(props: LiveDataWidgetProps) {
    const { model } = props;
    return (
        <LayoutElement {...props}>
            <ErrorBoundary fallbackMessage="Live data widget failed to load.">
                <Typography variant="h6">
                    Live Items ({model.items.length})
                </Typography>
                <List>
                    {model.items.map((item, i) => (
                        <ListItem key={i}>
                            <ListItemText primary={item} />
                        </ListItem>
                    ))}
                </List>
            </ErrorBoundary>
        </LayoutElement>
    );
});

export default LiveDataWidget;
```

> ⚠️ Without `observer()`, the component will NOT re-render when `model.items` changes.

---

## 5. Reactive Side-Effects in Models & Services (`reaction`, `when`, `autorun`)

In models and background services, you can trigger side-effects in response to observable state changes without relying on a React view:

```typescript
import { ComponentModelBase } from "@vertigis/web/models";
import { observable, reaction, when, IReactionDisposer } from "mobx";

export class DataSyncModel extends ComponentModelBase {
    @observable
    isOnline: boolean = false;

    @observable
    syncIntervalSeconds: number = 60;

    private _disposers: IReactionDisposer[] = [];

    protected async _onInitialize(): Promise<void> {
        await super._onInitialize();

        // 1. reaction: Run side-effect when a specific property changes
        const intervalReaction = reaction(
            () => this.syncIntervalSeconds,
            (newInterval) => {
                console.log(`Sync interval changed to ${newInterval}s. Resetting timer.`);
                this.restartTimer(newInterval);
            }
        );
        this._disposers.push(intervalReaction);

        // 2. when: Run one-shot side-effect once a condition becomes true
        when(
            () => this.isOnline,
            () => {
                console.log("Device came online. Flushing queue...");
                this.flushOfflineQueue();
            }
        );
    }

    protected async _onDestroy(): Promise<void> {
        // Clean up all MobX reactions
        this._disposers.forEach((dispose) => dispose());
        await super._onDestroy();
    }

    private restartTimer(interval: number): void { /* ... */ }
    private flushOfflineQueue(): void { /* ... */ }
}
```
