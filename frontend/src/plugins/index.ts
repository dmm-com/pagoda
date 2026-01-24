import { FC, ReactNode } from "react";
import { z } from "zod";

import { EntityStructure } from "./schema/types";

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

// ============================================================================
// Entity View Plugin Types (Phase 1: entry.list only)
// ============================================================================

/**
 * Page types that can be overridden by plugins
 * Phase 1: Only "entry.list" is supported
 */
export type EntityPageType = "entry.list";

/**
 * Configuration for a single entity-to-plugin mapping
 * Key is entityId (as string) for O(1) lookup
 */
export interface EntityPluginMapping {
  plugin: string;
  pages: EntityPageType[];
}

/**
 * Full configuration object for entity plugin views
 * Key is the entity ID (as string) for direct O(1) lookup
 */
export type EntityPluginViewsConfig = Record<string, EntityPluginMapping>;

/**
 * Extended plugin interface with entity page support
 */
export interface EntityViewPlugin extends Plugin {
  entityPages?: Partial<Record<EntityPageType, FC>>;
  /**
   * Zod schema for validating entity structure requirements.
   *
   * When provided, the entity structure will be validated against this schema
   * before rendering the plugin's page. If validation fails, an error page
   * will be displayed instead of the plugin component.
   *
   * @example
   * ```typescript
   * import { baseEntitySchema, requireAttr, AttrType } from "plugins/schema";
   *
   * const myPlugin: EntityViewPlugin = {
   *   entitySchema: baseEntitySchema.refine(
   *     (entity) => requireAttr("hostname", AttrType.STRING)(entity.attrs),
   *     { message: "hostname attribute is required" }
   *   ),
   *   // ...
   * };
   * ```
   */
  entitySchema?: z.ZodType<EntityStructure>;
}

/**
 * Type guard to check if a plugin has entity page support
 */
export function isEntityViewPlugin(plugin: Plugin): plugin is EntityViewPlugin {
  return "entityPages" in plugin && plugin.entityPages !== undefined;
}
