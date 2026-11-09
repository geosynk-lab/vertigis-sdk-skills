# VertiGIS Studio Web SDK: Overview & Key Concepts

## Introduction
VertiGIS Studio Web is a modern, extensible web mapping framework built on TypeScript, React, MobX, and the ArcGIS API for JavaScript. It provides a configurable, modular runtime environment where applications are defined by configuration and layout JSON files, while custom capabilities are developed using the VertiGIS Studio Web SDK.

---

## Core Architecture Pillars

VertiGIS Studio Web applications are structured around five foundational elements:

```
┌─────────────────────────────────────────────────────────────┐
│                      VertiGIS Application                   │
│                                                             │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │   Layout (app.json)   │       │ AppConfig(config.json)│  │
│  └───────────┬───────────┘       └───────────┬───────────┘  │
│              │                               │              │
│              ▼                               ▼              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Component Model                     │  │
│  │  ┌────────────────────┐       ┌────────────────────┐  │  │
│  │  │  React View (UI)   │◄─────►│    Model Class     │  │  │
│  │  └────────────────────┘       └─────────┬──────────┘  │  │
│  └─────────────────────────────────────────┼─────────────┘  │
│                                            │                │
│                                            ▼                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Commands, Operations & Event Bus            │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Services (Singletons)               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

1. **Components**:
   - Power the interactive user interface.
   - Split into a **React Component** (presentation) and a **Model Class** (state and logic).
   - Instantiated hierarchically as defined in the layout.

2. **Services**:
   - Application-wide singleton classes without UI.
   - Manage shared state, business logic, network communication, authentication, theming, and background operations.

3. **Commands & Operations**:
   - Decoupled execution bus connecting components, services, configuration, and workflows.
   - **Commands**: Asynchronous actions (fire-and-forget / side-effects) such as `ui.activate`, `map.zoom-to-extent`.
   - **Operations**: Synchronous/asynchronous functions that take input and return a computed result, such as `auth.get-token`.

4. **Events & Observability**:
   - Event bus for broadcasting system lifecycle state and component notifications.
   - State reactivity powered by MobX decorators (`@observable`, `@subscribable`). Config is loaded through the `@serializable` class decorator plus `_getSerializableProperties()`.

5. **Layout & App Configuration**:
   - **Layout (`app.json`)**: Declares the visual hierarchy, docking slots, splits, and UI components.
   - **App Config (`config.json`)**: Configures property values, model bindings, service settings, and event-to-command mappings.

---

## SDK Project Setup & Tooling

### Prerequisites
- Node.js LTS (v18+ or v20+)
- npm or yarn

### Quick Start
Generate a new custom library project using the official CLI:

```bash
# Create a new library directory
npx @vertigis/web-sdk@latest create <library-name>

# Navigate into the project
cd <library-name>

# Start the local development server with hot-reload
npm start
```

### Project Directory Structure (Best Practice)
When building complex components, use a decomposed React architecture rather than monolithic files:

```text
<library-name>/
├── app/                          # Dev sandbox application
│   ├── app.json                  # Sandbox layout definition
│   ├── app-config.json           # Sandbox configuration
│   └── index.html                # HTML entry point for local dev
├── src/                          # Custom extension code
│   ├── components/               # Custom UI components
│   │   └── SampleComponent/
│   │       ├── main.tsx                  # Main React orchestrator
│   │       ├── SampleComponentModel.ts   # MobX Model Class
│   │       ├── hooks/                    # Custom React Hooks
│   │       ├── components/               # Stateless MUI sub-components
│   │       └── utils/                    # Pure functions and constants
│   ├── services/                 # Custom services
│   │   └── SampleService.ts
│   └── index.ts                  # Library registration entry point
├── package.json
├── tsconfig.json
└── webpack.config.js
```

---

## Library Registration (`src/index.ts`)

The SDK bundles all components, services, commands, and operations into a deployable library via the registration callback:

```typescript
import { LibraryRegistry } from "@vertigis/web/config";
import CustomComponent, { CustomComponentModel } from "./components/CustomComponent/main";
import CustomService from "./services/CustomService";

export default function (registry: LibraryRegistry): void {
    // 1. Register Custom Component
    registry.registerComponent({
        name: "custom-widget",
        namespace: "your.custom.namespace",
        getComponentType: () => CustomComponent,
        itemType: "custom-widget-model",
        getItemType: () => CustomComponentModel,
        title: "Custom Widget",
    });

    // 2. Register Custom Model (if standalone without UI)
    registry.registerModel({
        itemType: "custom-widget-model",
        getItemType: () => CustomComponentModel,
    });

    // 3. Register Custom Service (Singleton)
    registry.registerService({
        id: "custom-data-service",
        getService: (config) => new CustomService(config),
    });

    // 4. Register Custom Command
    registry.registerCommandHandler({
        name: "custom.do-something",
        execute: async (args) => {
            console.log("Command executed with args:", args);
        },
    });
}
```

---

## 4. ArcGIS API for JavaScript Import Rules (AMD vs ES Modules)

The VertiGIS Web runtime uses an AMD module loader for ArcGIS modules. You MUST follow these import rules:

| Module Type | Import Pattern | Example | Why? |
| :--- | :--- | :--- | :--- |
| **Classes / Constructors** | Default Import | `import Graphic from "@arcgis/core/Graphic";`<br>`import Point from "@arcgis/core/geometry/Point";` | Classes have a default constructor export. |
| **Utility / Function-Only Modules** | **Star Import (`* as`)** | `import * as projection from "@arcgis/core/geometry/projection";`<br>`import * as geometryEngine from "@arcgis/core/geometry/geometryEngine";` | These modules have no default export; default import triggers runtime `Unsupported AMD module` errors. |
| **TypeScript Types** | Ambient `__esri.*` | `geometry: __esri.Geometry;`<br>`layer: __esri.FeatureLayer;` | Do not import types as values. |

