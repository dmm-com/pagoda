# pagoda-plugin-dashboard

An enhanced dashboard plugin for the Airone plugin system. Overrides the existing dashboard route to provide a feature-rich dashboard experience.

## Overview

- **Route**: `/ui/dashboard` (overrides default dashboard)
- **Features**: Real-time metrics, activity logs, quick actions
- **Modern Design**: Material-UI components with responsive layout

## Key Features

- Real-time system metrics display
- Recent activity tracking  
- Quick action buttons
- Plugin status indicators
- Route override demonstration

## Usage

Add to `pagoda-minimal-builder/plugins.config.js`:

```javascript
export default {
  plugins: [
    "pagoda-plugin-dashboard", // This plugin
    // Other plugins...
  ],
};
```

Then run:
```bash
npm run build && npm run start
```

Access at: http://localhost:3000/ui/dashboard

## Plugin Implementation

```typescript
import React from "react";
import type { Plugin } from "@dmm-com/pagoda-core";
import EnhancedDashboard from "./components/EnhancedDashboard";

const dashboardPlugin = {
  id: "dashboard-plugin",
  name: "Enhanced Dashboard Plugin",
  version: "1.0.0",
  routes: [{
    path: "/ui/dashboard", // Override existing route
    element: React.createElement(EnhancedDashboard),
  }],
} satisfies Plugin;

export default dashboardPlugin;
```

## Documentation

For comprehensive plugin development documentation, see:
- **Plugin Development Guide**: `docs/content/advanced/plugin_development.md`
- **Route Overrides**: How to override existing application routes
- **Component Development**: Best practices for React components in plugins

## License

MIT