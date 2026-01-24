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

interface EntityReferral {
  id: number;
  name: string;
}

interface EntityAttrStructure {
  id: number;
  name: string;
  type: number;
  isMandatory: boolean;
  referral: EntityReferral[];
}

interface EntityStructure {
  id: number;
  name: string;
  attrs: EntityAttrStructure[];
}

interface EntityViewPlugin {
  id: string;
  name: string;
  version: string;
  routes: PluginRoute[];
  entityPages?: Partial<Record<EntityPageType, FC>>;
  entitySchema?: z.ZodType<EntityStructure>;
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
// Schema helpers
// ============================================================================

/**
 * Helper: Check if entity has an attribute with specific name and type
 */
const hasAttr =
  (name: string, type: number | number[]) =>
  (attrs: EntityAttrStructure[]): boolean => {
    const types = Array.isArray(type) ? type : [type];
    return attrs.some((a) => a.name === name && types.includes(a.type));
  };

// ============================================================================
// Entity Schema Definition
// ============================================================================

/**
 * Base schema for entity attributes
 */
const entityAttrSchema = z.object({
  id: z.number(),
  name: z.string(),
  type: z.number(),
  isMandatory: z.boolean(),
  referral: z.array(
    z.object({
      id: z.number(),
      name: z.string(),
    }),
  ),
});

/**
 * Sample entity schema demonstrating attribute requirements
 *
 * This schema requires the entity to have a "name" attribute of STRING type.
 * When this schema validation fails, the plugin page will not be rendered
 * and an error page will be shown instead.
 *
 * Example requirements you might add:
 * - Required attributes: hostname, ip_address, status
 * - Specific attribute types: STRING, OBJECT, ARRAY_STRING
 * - Referral requirements: location must reference "Datacenter" entity
 */
const sampleEntitySchema = z
  .object({
    id: z.number(),
    name: z.string(),
    attrs: z.array(entityAttrSchema),
  })
  .refine((entity) => hasAttr("name", AttrType.STRING)(entity.attrs), {
    message: 'Required attribute "name" (STRING type) is missing',
  });

// ============================================================================
// Plugin Definition
// ============================================================================

/**
 * Sample plugin that provides entity-specific entry list page
 *
 * This plugin demonstrates:
 * 1. Entity page overrides (entry.list)
 * 2. Entity schema validation (entitySchema)
 *
 * The entitySchema ensures the target entity has the required structure
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

  // Entity schema validation
  entitySchema: sampleEntitySchema,
};

export default sampleEntityPlugin;

// Export schema and helpers for testing/documentation purposes
export { sampleEntitySchema, AttrType, hasAttr };
