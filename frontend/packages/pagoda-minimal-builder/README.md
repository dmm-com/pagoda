# Pagoda Minimal Builder

This is a minimal builder example that demonstrates how to integrate Pagoda Core with external plugins to create a standalone UI application.

## Features

- **Standalone Integration**: Uses `@dmm-com/pagoda-core` as an external npm package
- **Plugin Support**: Automatically loads external plugins (pagoda-plugin-hello-world, pagoda-plugin-dashboard)
- **Minimal Configuration**: Simple webpack config and minimal dependencies
- **External Repository Ready**: Can be copied to any external repository for custom builds

## Files Structure

```
pagoda-minimal-builder/
├── src/
│   └── App.tsx          # Main application entry point
├── dist/
│   └── ui.js           # Generated bundle (9.04 MiB with plugins)
├── package.json        # Dependencies: @dmm-com/pagoda-core + plugins
├── webpack.config.js   # Simple webpack configuration
├── tsconfig.json      # TypeScript configuration
├── index.html         # HTML template for development
└── README.md          # This file
```

## Usage

### 1. Install Dependencies

```bash
npm install
```

### 2. Build

```bash
npm run build
```

This generates `dist/ui.js` containing:
- Pagoda Core functionality
- External plugin integrations
- React application bundle

### 3. Development Server

```bash
npm run start
```

## How It Works

1. **External Dependencies**: All functionality comes from external npm packages
   - `@dmm-com/pagoda-core`: Core application framework
   - `pagoda-plugin-hello-world`: Sample hello world plugin
   - `pagoda-plugin-dashboard`: Sample dashboard plugin

2. **Direct Plugin Imports**: Plugins are imported directly in `src/App.tsx`:
   ```typescript
   import helloWorldPlugin from "pagoda-plugin-hello-world";
   import dashboardPlugin from "pagoda-plugin-dashboard";
   
   const plugins = [helloWorldPlugin, dashboardPlugin].filter(Boolean);
   ```

3. **Bundle Generation**: Webpack creates a single `ui.js` file containing everything needed

## Replicating in External Repositories

To use this pattern in your own repository:

1. Copy this directory structure
2. Update `package.json` dependencies to point to published npm packages
3. Customize `src/App.tsx` as needed
4. Run `npm install && npm run build`

The result is a completely standalone `ui.js` that can be deployed anywhere.

## Testing

### Quick Test
1. Open `test.html` in your browser
2. Check the browser console for plugin loading messages:
   ```
   📦 [Pagoda Minimal Builder] Loading - WITH DIRECT PLUGIN IMPORTS
   [Pagoda Minimal Builder] Loaded 2 plugins: [{id: 'hello-world', name: 'Hello World Plugin'}, ...]
   ```
3. The app should render with plugin routes accessible

### Expected Behavior
- ✅ Core functionality loads from `@dmm-com/pagoda-core`
- ✅ External plugins are directly imported and bundled
- ✅ Plugin routes are available (e.g., `/ui/hello-world`)
- ✅ No React useState errors or module resolution issues
- ✅ Generated ui.js is self-contained and deployable

## Generated Bundle Size

- With plugins: ~9.04 MiB
- Contains: Pagoda Core + React + MUI + Plugin code
- Ready for production deployment