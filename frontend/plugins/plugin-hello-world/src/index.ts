// @airone/plugin-hello-world - Main Export
// This is an example of an external npm package plugin for Airone

import React from "react";
import type { Plugin } from "@dmm-com/pagoda-core";
import HelloWorldPage from "./components/HelloWorldPage";

// Simple Hello World plugin with type safety
const helloWorldPlugin = {
  id: "hello-world-plugin",
  name: "Hello World Plugin",
  version: "1.0.0",

  // Routes provided by this plugin
  routes: [
    {
      path: "/ui/hello-world",
      element: React.createElement(HelloWorldPage),
    },
  ],
} satisfies Plugin;

// Export the plugin as default
export default helloWorldPlugin;
