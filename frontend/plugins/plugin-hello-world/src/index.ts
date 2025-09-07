// @airone/plugin-hello-world - Main Export
// This is an example of an external npm package plugin for Airone

import React from "react";
import { createPlugin, createPluginRoute } from "@dmm-com/pagoda-core/plugins";
import type { PluginAPI } from "@dmm-com/pagoda-core/plugins";
import HelloWorldPage from "./components/HelloWorldPage";

// Plugin initialization function
const initializePlugin = async (api: PluginAPI) => {
  // Save plugin configuration
  api.config.set("lastInitialized", new Date().toISOString());
  api.config.set("features", [
    "route-override",
    "notifications",
    "npm-package",
  ]);
  api.config.set("clickCount", 0);

  // Show initialization notification
  try {
    api.ui.showNotification(
      "Hello World Plugin initialized successfully!",
      "success",
    );
  } catch (error) {
    // Notification not available
  }
};

// Plugin activation function
const activatePlugin = async () => {
  // Plugin activated
};

// Plugin deactivation function
const deactivatePlugin = async () => {
  // Plugin deactivated
};

// Create the Hello World plugin
const helloWorldPlugin = createPlugin({
  id: "hello-world-plugin",
  name: "Hello World Plugin",
  version: "1.0.0",
  description:
    "Demo sample plugin for plugin system (external npm package version)",
  priority: 10, // High priority

  // Lifecycle hooks
  initialize: initializePlugin,
  activate: activatePlugin,
  deactivate: deactivatePlugin,

  // Routes provided by this plugin
  routes: [
    createPluginRoute({
      path: "/ui/hello-world", // Full path with Django prefix
      element: React.createElement(HelloWorldPage),
      priority: 1, // High priority
      layout: "default",
    }),
  ],

  // Plugin configuration
  config: {
    debugMode: true,
    theme: "default",
    packageType: "npm-external",
    features: {
      notifications: true,
      routing: true,
      theming: true,
      storage: true,
    },
  },
});

// Export the plugin as default
export default helloWorldPlugin;

// Also export as named export for flexibility
export { helloWorldPlugin };

// Export plugin metadata for introspection
export const metadata = {
  id: "hello-world-plugin",
  name: "Hello World Plugin",
  version: "1.0.0",
  packageName: "@airone/plugin-hello-world",
  description:
    "Demo sample plugin for plugin system (external npm package version)",
  author: "Airone Team",
  repository: "https://github.com/dmm-com/airone",
  license: "MIT",
  tags: ["demo", "example", "hello-world", "sample"],
  compatibility: {
    core: "^1.0.0",
    react: "^18.0.0",
  },
};

// Export components for advanced usage
export { default as HelloWorldPage } from "./components/HelloWorldPage";

// Plugin factory function for custom configurations
export function createHelloWorldPlugin(customConfig?: Record<string, unknown>) {
  return createPlugin({
    ...helloWorldPlugin,
    config: {
      ...helloWorldPlugin.config,
      ...customConfig,
    },
  });
}
