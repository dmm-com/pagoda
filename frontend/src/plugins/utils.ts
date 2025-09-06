import { ReactNode } from "react";

import {
  Plugin,
  PluginRoute,
  PluginDefinition,
  PluginComponent,
  ComponentTrigger,
  ComponentPosition,
} from "./types";

/**
 * Helper function for creating plugins
 */
export function createPlugin(config: PluginDefinition): Plugin {
  return {
    ...config,
    components: [], // Empty array by default
  };
}

/**
 * Helper function for creating plugin routes
 */
export function createPluginRoute(config: {
  path: string;
  element: ReactNode | (() => ReactNode);
  priority?: number;
  override?: boolean;
  layout?: "default" | "minimal" | "custom";
}): PluginRoute {
  return {
    priority: 1000, // Default priority
    override: false, // Do not override by default
    layout: "default", // Default layout
    ...config,
  };
}

/**
 * Helper function for creating plugin components
 */
export function createPluginComponent(config: {
  id: string;
  component: ReactNode | (() => ReactNode);
  trigger: ComponentTrigger;
  position?: ComponentPosition;
}): PluginComponent {
  return {
    ...config,
  };
}
