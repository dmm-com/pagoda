import { ReactNode } from "react";

// Simple plugin interface
export interface Plugin {
  id: string;
  name: string;
  version: string;
  routes: PluginRoute[];
}

// Plugin route interface
export interface PluginRoute {
  path: string;
  element: ReactNode;
}

// Types for compatibility with existing customRoutes
export interface CustomRoute {
  path: string;
  element: ReactNode;
}

// Extended props for AppBase
export interface ExtendedAppBaseProps {
  customRoutes?: CustomRoute[];
  plugins?: Plugin[];
}

// Plugin utility functions
export const extractRoutes = (plugins: Plugin[]): CustomRoute[] => {
  return plugins.flatMap((plugin) => plugin.routes);
};
