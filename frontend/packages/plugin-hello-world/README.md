# @airone/plugin-hello-world

Hello World plugin for Airone - demonstrates basic plugin functionality as an external npm package.

## Installation

```bash
npm install @airone/plugin-hello-world
```

## Usage

### Basic Usage

```typescript
import { AironeCore } from '@airone/core';
import helloWorldPlugin from '@airone/plugin-hello-world';

// Create core instance
const core = new AironeCore();

// Register the plugin
await core.registerPlugins([helloWorldPlugin]);

// Initialize
await core.initialize();
```

### Advanced Usage

```typescript
import { createHelloWorldPlugin } from '@airone/plugin-hello-world';

// Create plugin with custom configuration
const customPlugin = createHelloWorldPlugin({
  customFeature: true,
  debugMode: false
});
```

### Integration Example

```typescript
// In your main application
import React from 'react';
import { PluginProvider } from '@airone/core/components';
import { PluginRegistry } from '@airone/core/plugins';
import helloWorldPlugin from '@airone/plugin-hello-world';

function App() {
  const [registry] = React.useState(() => {
    const reg = new PluginRegistry();
    reg.registerPlugin(helloWorldPlugin);
    return reg;
  });

  React.useEffect(() => {
    registry.initializePlugins();
  }, [registry]);

  return (
    <PluginProvider registry={registry}>
      <YourAppRouter />
    </PluginProvider>
  );
}
```

## Features

- ✅ External npm package distribution
- ✅ Custom route registration (`/hello-world`)
- ✅ Plugin API integration (notifications, navigation)
- ✅ Material-UI theme integration
- ✅ Error handling and fallbacks
- ✅ TypeScript support
- ✅ Development tools integration

## Plugin Information

- **Plugin ID**: `hello-world-plugin`
- **Version**: `1.0.0`
- **Priority**: `10` (high priority)
- **Layout**: `default`

## Routes

| Path | Component | Description |
|------|-----------|-------------|
| `/hello-world` | `HelloWorldPage` | Main plugin demonstration page |

## Configuration

The plugin accepts the following configuration options:

```typescript
{
  debugMode: boolean;        // Enable debug logging
  theme: string;             // Theme preference  
  packageType: string;       // Package distribution type
  features: {
    notifications: boolean;  // Enable notifications
    routing: boolean;        // Enable routing
    theming: boolean;        // Enable theming
    storage: boolean;        // Enable storage
  }
}
```

## API Usage

The plugin uses the following Airone Core APIs:

```typescript
// Notifications
api.ui.showNotification(message, type);

// Navigation
api.routing.navigate(path);

// Configuration storage
api.config.set(key, value);
api.config.get(key);
```

## Development

### Building

```bash
npm run build
```

### Testing

```bash
npm test
```

### Development Mode

```bash
npm run build:dev
```

### Linting

```bash
npm run lint
```

## Requirements

- **@airone/core**: `^1.0.0`
- **React**: `^18.0.0`
- **@mui/material**: `^6.0.0`

## Browser Support

This plugin supports all modern browsers that support:

- ES2020
- React 18+
- Material-UI v6+

## License

MIT

## Contributing

This is a demonstration plugin. For contributing to the Airone project, please visit the main repository.

## Changelog

### 1.0.0

- Initial release
- Basic plugin functionality
- External npm package support
- Route registration
- Plugin API integration

## Support

For issues related to this plugin or the Airone plugin system, please file an issue in the main Airone repository.