# pagoda-plugin-hello-world

A simple Hello World plugin demonstrating the new simplified plugin architecture for Airone.

## Overview

- **Route**: `/ui/hello-world`
- **Type Safety**: Uses `satisfies Plugin` for compile-time validation
- **Simple Interface**: Only requires id, name, version, and routes

## Quick Example

```typescript
import React from "react";
import type { Plugin } from "@dmm-com/pagoda-core";
import HelloWorldPage from "./components/HelloWorldPage";

const helloWorldPlugin = {
  id: "hello-world-plugin",
  name: "Hello World Plugin", 
  version: "1.0.0",
  routes: [{
    path: "/ui/hello-world",
    element: React.createElement(HelloWorldPage),
  }],
} satisfies Plugin;

export default helloWorldPlugin;
```

## Usage

Add to `pagoda-minimal-builder/plugins.config.js`:

```javascript
export default {
  plugins: [
    "pagoda-plugin-hello-world", // This plugin
    // Other plugins...
  ],
};
```

Then run:
```bash
npm run build && npm run start
```

## Documentation

For comprehensive plugin development documentation, see:
- **Plugin Development Guide**: `docs/content/advanced/plugin_development.md`
- **Architecture & Examples**: Detailed technical documentation
- **Best Practices**: Development patterns and troubleshooting

## License

MIT