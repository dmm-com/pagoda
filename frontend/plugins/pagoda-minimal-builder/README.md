# Pagoda Minimal Builder

This is a minimal builder example that demonstrates how to integrate Pagoda Core with external plugins to create a standalone UI application.

> **Important**: This is the **officially recommended plugin integration method**. Pagoda Core itself does not include any plugins.

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

2. **Configurable Plugin System**: Plugins are configured in `plugins.config.js`
   ```javascript
   // plugins.config.js
   module.exports = {
     plugins: [
       'pagoda-plugin-hello-world',
       'pagoda-plugin-dashboard',
       'pagoda-plugin-custom-example',  // Add third-party plugin
     ]
   };
   ```

3. **Automatic Import Generation**: Import statements are automatically generated at build time
   - `scripts/generate-plugin-imports.js` runs when `npm run build` is executed
   - `src/generatedPlugins.ts` is auto-generated
   - Add or remove plugins without editing source code

4. **Bundle Generation**: Webpack creates a single `ui.js` file containing everything needed

## Adding Third-Party Plugins

Steps to add a new plugin:

1. **Install the plugin**
   ```bash
   npm install your-plugin-name
   # Or for local development
   npm link your-plugin-name
   ```

2. **Edit `plugins.config.js`**
   ```javascript
   module.exports = {
     plugins: [
       'pagoda-plugin-hello-world',
       'pagoda-plugin-dashboard',
       'your-plugin-name',  // ← Add here
     ]
   };
   ```

3. **Build**
   ```bash
   npm run build
   ```

**No source code editing required!** Simply modify the configuration file to add plugins.

## Replicating in External Repositories

To use this pattern in your own repository:

1. Copy this directory structure
2. Update `package.json` dependencies to point to published npm packages
3. Edit `plugins.config.js` to include your desired plugins
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