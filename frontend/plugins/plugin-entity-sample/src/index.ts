// @airone/plugin-entity-sample - Entity View Sample Plugin
// Demonstrates entity-specific page routing with schema validation

import React, { FC, ReactNode } from "react";
import { z } from "zod";

import SampleEntryListPage from "./pages/SampleEntryListPage";

// ============================================================================
// Type definitions (matching @dmm-com/pagoda-core)
// In a real plugin, these would be imported from @dmm-com/pagoda-core
// ============================================================================

type EntityPageType = "entry.list";

interface PluginRoute {
  path: string;
  element: ReactNode;
}

interface EntityViewPlugin {
  id: string;
  name: string;
  version: string;
  routes: PluginRoute[];
  entityPages?: Partial<Record<EntityPageType, FC>>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  attrSchema?: z.ZodType<any>;
}

// ============================================================================
// AttrType constants (matching airone/lib/types.py)
// In a real plugin, these would be imported from @dmm-com/pagoda-core
// ============================================================================

const AttrType = {
  OBJECT: 1,
  STRING: 2,
  TEXT: 4,
  BOOLEAN: 8,
  GROUP: 16,
  DATE: 32,
  ROLE: 64,
  DATETIME: 128,
  NUMBER: 256,
  NAMED_OBJECT: 2049,
  ARRAY_OBJECT: 1025,
  ARRAY_STRING: 1026,
  ARRAY_NUMBER: 1280,
  ARRAY_NAMED_OBJECT: 3073,
  ARRAY_GROUP: 1040,
  ARRAY_ROLE: 1088,
} as const;

// ============================================================================
// Entity Attribute Schema Definition (Simplified!)
// ============================================================================

/**
 * Sample attribute schema demonstrating attribute requirements
 *
 * This schema requires the entity to have a "name" attribute of STRING type.
 * When this schema validation fails, the plugin page will not be rendered
 * and an error page will be shown instead.
 *
 * With the new simplified approach, you just define the required attributes
 * as a pure Zod schema - no helper functions needed!
 *
 * Example requirements you might add:
 * - Required attributes: hostname, ip_address, status
 * - Specific attribute types: STRING, OBJECT, ARRAY_STRING
 */
const sampleAttrSchema = z.object({
  // Require "hostname" attribute with STRING type
  // This will fail for entities without this attribute
  hostname: z.object({
    type: z.literal(AttrType.STRING),
  }),
});

// ============================================================================
// Plugin Definition
// ============================================================================

/**
 * Sample plugin that provides entity-specific entry list page
 *
 * This plugin demonstrates:
 * 1. Entity page overrides (entry.list)
 * 2. Entity attribute schema validation (attrSchema)
 *
 * The attrSchema ensures the target entity has the required attributes
 * before the plugin page is rendered.
 */
const sampleEntityPlugin: EntityViewPlugin = {
  id: "sample",
  name: "Sample Entity View Plugin",
  version: "1.0.0",

  // No custom routes (we use entityPages instead)
  routes: [],

  // Entity-specific pages
  entityPages: {
    "entry.list": () => React.createElement(SampleEntryListPage),
  },

  // Entity attribute schema validation (simplified!)
  attrSchema: sampleAttrSchema,
};

export default sampleEntityPlugin;

// Export schema and AttrType for testing/documentation purposes
export { sampleAttrSchema, AttrType };
