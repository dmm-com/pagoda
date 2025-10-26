import React from "react";
import type { Plugin } from "@dmm-com/pagoda-core";
import EnhancedDashboard from "./components/EnhancedDashboard";

const dashboardPlugin = {
  id: "dashboard-plugin",
  name: "Enhanced Dashboard Plugin",
  version: "1.0.0",

  routes: [
    {
      path: "/ui/dashboard",
      element: React.createElement(EnhancedDashboard),
    },
  ],
} satisfies Plugin;

export default dashboardPlugin;
