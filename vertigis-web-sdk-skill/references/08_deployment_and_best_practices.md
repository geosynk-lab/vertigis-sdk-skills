# VertiGIS Studio Web SDK: Deployment & Best Practices

## Overview
Once custom components, services, or workflow activities have been developed and tested locally, they must be bundled and deployed to VertiGIS Studio Web.

---

## 1. Building the Library Package

Compile the production bundle using npm:

```bash
# In the custom library root
npm run build
```

This generates the production output in the `dist/` directory, typically including:
- `main.js`: The bundled JavaScript / AMD library.
- `main.css`: Combined CSS styles.
- `package.json`: Library metadata and version info.

---

## 2. Deployment Options

### Option A: Hosting on a Public or Internal Web Server / CDN
1. Upload the `dist/` folder contents to a web server accessible by your users (e.g., `https://cdn.example.com/vertigis/my-custom-lib/`).
2. Ensure CORS headers (`Access-Control-Allow-Origin: *` or allowed origins) are enabled on the server.
3. In VertiGIS Studio Web Designer or `app-config.json`, add the library URL under `libraries`:
```json
{
  "libraries": [
    "https://cdn.example.com/vertigis/my-custom-lib/main.js"
  ]
}
```

### Option B: Hosting in ArcGIS Online / ArcGIS Enterprise Portal
1. Zip the `dist/` folder.
2. Add the `.zip` file as an Item in ArcGIS Online / Enterprise with type **Web Experience Extension** or **Code Attachment**.
3. Reference the item ID in your VertiGIS Web application configuration.

---

## 3. Best Practices

### A. Performance & Lazy Loading
- Avoid heavy computation in constructors or synchronous rendering loops.
- Use `_load()` and `_unload()` lifecycle hooks to defer heavy resource initialization until components become active.

### B. Decoupled Communication
- Prefer using **Commands and Operations** over tightly coupling components with direct model references where possible.
- Use custom namespaces for your commands/operations (e.g. `myorg.inspection.start`) to avoid collision with core VertiGIS APIs.

### C. State Management
- Use `@serializable` only for properties that should be persisted in `app-config.json`.
- Keep runtime transient state as regular MobX `@observable` fields.
- Clean up event subscriptions and intervals in `_onDestroy()`.

### D. Third-Party Dependencies & Webpack Externals
- **Externals provided by VertiGIS runtime**: The host application already provides core libraries. NEVER bundle duplicate copies of:
  - `@vertigis/web`
  - `@arcgis/core`
  - `react` / `react-dom`
  - `@mui/material`
- **Bundling Utility Libraries**: For pure JavaScript utilities (e.g. `papaparse`, `canvas-confetti`, `qrcode`, `jspdf`), install them via `npm install <package>` and import them directly. They will be bundled into your `dist/main.js` output.
- **Dynamic / Lazy Imports**: For heavy libraries (e.g. Chart.js, PDF generators), use dynamic `import()` to load them on demand only when the user opens the relevant widget or executes the action:
  ```typescript
  async function generateQRCode(text: string): Promise<string> {
      const QRCode = await import("qrcode");
      return QRCode.toDataURL(text);
  }
  ```

### E. Strict Component Modularity & File Size Discipline
- **Strict File Size Limits**: Target **150 lines** per file (soft limit); enforce a **250-line hard ceiling**. Files exceeding 250 lines fail code quality reviews and should be decomposed immediately.
- **Standard 7-Folder Directory Blueprint**: For non-trivial components, decompose code into dedicated directories:
  - `components/`: Presentational sub-components and UI fragments (< 100–150 lines each).
  - `hooks/`: Custom React hooks encapsulating stateful logic, event subscriptions, and queries.
  - `services/`: Component-scoped API clients or service integrators.
  - `utils/`: Zero-dependency pure functions (formatting, date calculations, math) for 100% testability.
  - `helpers/`: Specialized mapping or geometry helper functions.
  - `tokens/`: Component-level token overrides or aliases.
  - `types/`: Type definitions, interfaces, and DTO contracts.
- **Model vs View Separation**:
  - **MobX Models (`*Model.ts`)**: Extend `ComponentModelBase`. Handle data persistence (`@serializable`), state (`@observable`), service injection (`@inject`), and lifecycle hooks (`_onInitialize`, `_onDestroy`). Strictly prohibited from importing React, JSX, or accessing DOM APIs.
  - **React Views (`*.tsx`)**: High-level coordinators wrapped in `observer()`. Render layout slots (`<LayoutElement>`), provide error containment (`<ErrorBoundary>`), and compose sub-components. Delegate stateful workflows to custom hooks.
- **Actionable Extraction Heuristics**:
  - If a JSX block exceeds 50 lines or represents an independent UI section (header, modal, table), extract it into `components/`.
  - If multiple hooks (`useState`, `useEffect`, `useWatch`) coordinate a feature, extract them into a custom hook in `hooks/`.
  - If logic is pure calculation or formatting, isolate it into a pure function in `utils/`.
- For complete directory structure blueprints, MobX vs View boundary rules, and before/after refactoring examples, see [Design Tokens & Theming Guide](./11_design_tokens_and_theming.md#component-modularity).

### F. Design Token Fallbacks & Dual-Theme Safety
- **Safe Default Fallbacks**: Always provide WCAG AA compliant fallback values when referencing CSS variables (e.g. `var(--primaryBackground, #ffffff)` or `var(--primaryForeground, #212121)`). This ensures robust rendering in offline unit tests (Vitest/Jest), Storybook sandboxes, and initial shell mounting before the `branding` service injects theme variables.
- **Dynamic Color Mixing**: Use `color-mix(in srgb, ...)` (or `alphaMix()` / `surfaceMix()` helpers) for derived tints, hover states, muted borders, and transparent overlays. Never use static RGBA values like `rgba(0, 0, 0, 0.08)`, which fail in dark themes.
- **Dual-Context Theme Detection**:
  - In React components: Use the reactive `useIsDarkTheme()` hook to track DOM theme mutations and OS preferences.
  - In non-CSS contexts (Plotly charts, HTML5 Canvas, SVG generators, jsPDF exports): Call the standalone `isDarkTheme()` synchronous utility to inspect theme classes, background luminance, and OS media queries.
- **MUI Theme Harmonization**: Wrap composite MUI controls (`<Slider>`, `<Switch>`, `<DatePicker>`, `<Select>`) in `VertiGisThemeProvider` (or configure via `createVertiGisMuiTheme`) so internal SVG icons, canvas elements, and surfaces synchronize with VertiGIS branding rather than default MUI blues.
- For complete token dictionaries, helper implementations, theme hook source code, and MUI theme setup, see the [Design Tokens & Theming Guide](./11_design_tokens_and_theming.md).
