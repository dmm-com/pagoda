import React from "react";
import { createPlugin, createPluginRoute } from "@dmm-com/pagoda-core/plugins";
import EnhancedDashboard from "./components/EnhancedDashboard";

const dashboardPlugin = createPlugin({
  id: "dashboard-plugin",
  name: "Enhanced Dashboard Plugin",
  version: "1.0.0",
  description:
    "Enhanced dashboard plugin that overrides the default dashboard route with extended functionality",

  routes: [
    createPluginRoute({
      path: "/ui/dashboard", // Full path with Django prefix
      element: React.createElement(EnhancedDashboard),
      priority: 100, // High priority to override default dashboard route
      override: true,
    }),
  ],

  initialize: async (api) => {
    console.log("[Enhanced Dashboard Plugin] Initializing...", api);

    // Temporarily disable UI notifications to fix API error
    // if (api.ui?.showNotification) {
    //   api.ui.showNotification('Enhanced Dashboard Plugin initialized', 'success');
    // }

    // Store plugin configuration
    if (api.config) {
      await api.config.set("dashboard-plugin.initialized", true);
      await api.config.set("dashboard-plugin.version", "1.0.0");
    }

    console.log("[Enhanced Dashboard Plugin] Initialized successfully");
  },

  activate: async (api) => {
    console.log("[Enhanced Dashboard Plugin] Activating...", api);

    // Temporarily disable UI notifications to fix API error
    // if (api.ui?.showNotification) {
    //   api.ui.showNotification('Enhanced Dashboard Plugin has been activated', 'info');
    // }

    console.log("[Enhanced Dashboard Plugin] Activated successfully");
  },

  deactivate: async (api) => {
    console.log("[Enhanced Dashboard Plugin] Deactivating...", api);

    // Temporarily disable UI notifications to fix API error
    // if (api.ui?.showNotification) {
    //   api.ui.showNotification('Enhanced Dashboard Plugin has been deactivated', 'warning');
    // }

    console.log("[Enhanced Dashboard Plugin] Deactivated successfully");
  },

  priority: 100, // High priority plugin
});

export default dashboardPlugin;

// Named exports for advanced usage
export { EnhancedDashboard };
export const createDashboardPlugin = (config?: Record<string, unknown>) => ({
  ...dashboardPlugin,
  ...config,
});
