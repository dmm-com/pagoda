/**
 * Plugin Configuration File
 *
 * Define the plugins to include in your build.
 * To add a new plugin, follow these steps:
 *
 * 1. Install the plugin with npm install
 *    Example: npm install pagoda-plugin-analytics
 *
 * 2. Add it to the plugins array in this file
 *
 * 3. Run npm run build
 */

export default {
  plugins: [
    // Default plugins
    "pagoda-plugin-hello-world",
    // 'pagoda-plugin-dashboard',

    // Add custom plugins here
    // "pagoda-plugin-custom-example", // Third-party plugin example (uncomment when installed)

    // Other examples:
    // 'pagoda-plugin-analytics',
    // 'pagoda-plugin-custom-charts',
    // '@my-company/pagoda-plugin-internal',
  ],
};
