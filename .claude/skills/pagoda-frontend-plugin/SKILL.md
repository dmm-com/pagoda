---
name: pagoda-frontend-plugin
description: |
  Development guide for Pagoda/AirOne frontend plugins. Use when developing the plugin system under frontend/src/plugins/ or individual plugins under frontend/plugins/. Covers plugin route definitions, entity page overrides, Zod schema validation, and plugin type definitions. Trigger on requests like "create a frontend plugin", "add plugin UI", "override an entity page", "plugin component", or any frontend plugin development task.
---

# Pagoda Frontend Plugin Development Guide

Pagoda frontend plugins customize and extend the core UI. The main extension points are page overrides and custom route additions.

## Architecture

### Plugin System (frontend/src/plugins/)
- `index.ts` — Plugin type definitions (`Plugin`, `EntityViewPlugin`, `EntityPluginMapping`)
- `schema/types.ts` — Entity attribute type constants (`AttrType`: STRING=2, OBJECT=1, BOOLEAN=8, etc.)
- `schema/converter.ts` — Converts API EntityDetail to validation-ready AttrRecord

### Plugin Location (frontend/plugins/)
Each plugin is placed as an independent package under `frontend/plugins/`.

### Host Integration
```
AppBase.tsx
  → Receives plugins array
  → extractRoutes(plugins) extracts routes
  → Builds pluginMap (id → plugin mapping)
  → Passes custom routes and plugin map to AppRouter
```

**EntityPageType (currently supported):**
- `"entry.list"` — Entry list page override

**ServerContext configuration:**
```typescript
frontendPluginEntityOverrides: {
  "<entity_id>": {
    plugin: "my-plugin",
    pages: ["entry.list"]
  }
}
```

## Development Workflow

### 1. Create a Plugin

**Plugin structure:**
```
frontend/plugins/my-plugin/
  ├── package.json      # peerDependencies: @dmm-com/pagoda-core, react, @mui/material
  ├── tsconfig.json     # TypeScript configuration
  ├── src/
  │   ├── index.ts      # Plugin entry point (exports Plugin object)
  │   └── pages/        # Page components
  │       └── EntryListPage.tsx
  └── tests/
```

**Minimal structure:**
```typescript
import { EntityViewPlugin } from "@dmm-com/pagoda-core/plugins";
import { EntryListPage } from "./pages/EntryListPage";

const plugin: EntityViewPlugin = {
  id: "my-plugin",
  name: "My Plugin",
  version: "0.1.0",
  routes: [],
  entityPages: {
    "entry.list": EntryListPage,
  },
};

export default plugin;
```

**Writing page components:**
- Same patterns as core: functional components + MUI styled() + hooks
- Can import core parts from `@dmm-com/pagoda-core`
- Use Zod schemas for entity attribute validation

**Zod schema (attribute validation):**
```typescript
import { AttrType } from "@dmm-com/pagoda-core/plugins";
import { z } from "zod";

// Define entity attribute schema
const entitySchema = z.object({
  name: z.literal("MyEntity"),
  attrs: z.object({
    title: z.object({ type: z.literal(AttrType.STRING) }),
    category: z.object({ type: z.literal(AttrType.OBJECT) }),
  }),
});
```

### 2. Run Static Analysis

**Plugin code:**
```bash
# ESLint (plugin directory)
npx eslint frontend/plugins/<plugin-name>/src/

# Biome formatter
npx biome format frontend/plugins/<plugin-name>/src/

# Auto-fix
npx eslint --fix frontend/plugins/<plugin-name>/src/
npx biome format --write frontend/plugins/<plugin-name>/src/
```

**Core plugin system (frontend/src/plugins/) changes:**
```bash
# Same rules as core
npx eslint frontend/src/plugins/
npx biome format frontend/src/plugins/
npx knip
```

ESLint and Biome rules are identical to core frontend (no `any`, import order, 2-space indent, double quotes, semicolons).

### 3. Run Tests

**Frontend plugin tests require both full core tests + individual plugin tests.**

```bash
# Core tests (full run to check plugin system impact)
npm run test

# Individual plugin tests (if the plugin has its own tests)
cd frontend/plugins/<plugin-name>
npm test
```

**Writing tests:**
- Same as core: Jest + @testing-library/react
- Use `TestWrapper` from core for provider setup
- Mock props received by the plugin
- Mock entity data using AttrType constants

### 4. Verify Backend and Core Integration

Frontend plugins depend on both the core frontend and backend plugins, making the verification scope the broadest.

**Points to verify:**

1. **Backend plugin consistency:**
   - Backend override config (`BACKEND_PLUGIN_ENTITY_OVERRIDES`) and frontend config (`frontendPluginEntityOverrides`) must correspond
   - Frontend correctly processes the data structures returned by the backend
   - Overridden API response types match expectations

2. **Core frontend consistency:**
   - Types and components imported from `@dmm-com/pagoda-core` are up to date
   - Plugin peerDependencies match the core version
   - Check if new page types have been added to `EntityPageType`

3. **Routing:**
   - Plugin custom routes do not conflict with core routes
   - Routes are correctly extracted by `extractRoutes()`

### 5. Build Verification

```bash
# Plugin build (if the plugin has its own build)
cd frontend/plugins/<plugin-name>
npm run build

# Core build (when plugin system is modified)
npm run build
```

### 6. Quality Checklist

Before completing changes:
1. ESLint + Biome — both plugin code and core plugin system pass
2. `npm run test` — all core tests pass
3. Individual plugin tests — pass
4. `npm run build` — build succeeds
5. Comments are in English
6. No `any` types used
7. Backend configuration consistency verified

## Important Notes

- Plugins declare `@dmm-com/pagoda-core` as a peerDependency (do not bundle it)
- `frontend/plugins/` is excluded from Knip scanning (configured in `knip.jsonc`)
- Use AttrType constants from `schema/types.ts` (no magic numbers)
- Plugin entry point must export a Plugin object
- Currently only `"entry.list"` is supported as an EntityPageType (more planned)
