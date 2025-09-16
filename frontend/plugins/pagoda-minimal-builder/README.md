# Pagoda Minimal Builder

A simplified plugin integration tool for the Airone frontend that **"just connects routing with React Components"** without complex lifecycle management.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server  
npm run start

# Build for production
npm run build
```

## What's Included

- **Hello World Plugin**: Basic plugin demonstration at `/ui/hello-world`
- **Dashboard Plugin**: Enhanced dashboard at `/ui/dashboard` 
- **Configuration-based setup**: Manage plugins via `plugins.config.js`
- **Type safety**: Full TypeScript support with `satisfies Plugin`

## Adding Plugins

1. **Install plugin**: `npm install pagoda-plugin-name`
2. **Configure**: Add to `plugins.config.js`
3. **Build**: `npm run build`

```javascript
// plugins.config.js
export default {
  plugins: [
    "pagoda-plugin-hello-world",
    "pagoda-plugin-dashboard", 
    "pagoda-plugin-your-name", // Add here
  ],
};
```

## Plugin Development

### Minimal Plugin Example

```typescript
import React from "react";
import type { Plugin } from "@dmm-com/pagoda-core";

const myPlugin = {
  id: "my-plugin",
  name: "My Plugin", 
  version: "1.0.0",
  routes: [{
    path: "/ui/my-plugin",
    element: React.createElement("div", {}, "Hello from my plugin!")
  }],
} satisfies Plugin;

export default myPlugin;
```

## Documentation

For detailed documentation on:
- **Plugin development**: See `docs/content/advanced/plugin_development.md`
- **Architecture details**: Architecture diagrams and technical details
- **Advanced features**: Multi-route plugins, state management, troubleshooting
- **Best practices**: Development guidelines and examples

## Bundle Size

- **With plugins**: ~9.04 MiB (includes Pagoda Core + React + MUI + Plugins)
- **Production ready**: Self-contained deployable bundle