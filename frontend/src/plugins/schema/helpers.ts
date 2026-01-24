/**
 * Helper functions for creating entity schema validations
 *
 * These helpers simplify common validation patterns when defining
 * entity schema requirements for plugins.
 */

import { z } from "zod";

import { AttrTypeNames, EntityAttrStructure } from "./types";

/**
 * Options for requireAttr helper
 */
interface RequireAttrOptions {
  /** If true, the attribute must be marked as mandatory */
  mustBeMandatory?: boolean;
  /** Custom error message */
  message?: string;
}

/**
 * Create a refinement function that checks for a required attribute
 *
 * @param name - The attribute name to check for
 * @param type - The expected attribute type(s)
 * @param options - Additional validation options
 * @returns A function suitable for use with Zod's .refine()
 *
 * @example
 * ```typescript
 * const schema = baseEntitySchema.extend({
 *   attrs: z.array(entityAttrSchema)
 *     .refine(requireAttr("hostname", AttrType.STRING), {
 *       message: "hostname attribute (STRING type) is required",
 *     })
 * });
 * ```
 */
export const requireAttr =
  (
    name: string,
    type: number | number[],
    options?: RequireAttrOptions,
  ): ((attrs: EntityAttrStructure[]) => boolean) =>
  (attrs: EntityAttrStructure[]) => {
    const types = Array.isArray(type) ? type : [type];
    const attr = attrs.find((a) => a.name === name);

    if (!attr) return false;
    if (!types.includes(attr.type)) return false;
    if (options?.mustBeMandatory && !attr.isMandatory) return false;

    return true;
  };

/**
 * Options for requireReferral helper
 */
interface RequireReferralOptions {
  /** Custom error message */
  message?: string;
  /** If true, requires ALL entity names to be present. If false, requires ANY. Default: true */
  requireAll?: boolean;
}

/**
 * Create a refinement function that checks for required referral entities
 *
 * @param attrName - The attribute name to check
 * @param entityNames - The entity names that should be in the referral list
 * @param options - Additional validation options
 * @returns A function suitable for use with Zod's .refine()
 *
 * @example
 * ```typescript
 * const schema = baseEntitySchema.extend({
 *   attrs: z.array(entityAttrSchema)
 *     .refine(requireReferral("location", ["Location", "DataCenter"]), {
 *       message: "location must reference Location and DataCenter entities",
 *     })
 * });
 * ```
 */
export const requireReferral =
  (
    attrName: string,
    entityNames: string[],
    options?: RequireReferralOptions,
  ): ((attrs: EntityAttrStructure[]) => boolean) =>
  (attrs: EntityAttrStructure[]) => {
    const attr = attrs.find((a) => a.name === attrName);
    if (!attr) return false;

    const requireAll = options?.requireAll !== false; // Default to true

    if (requireAll) {
      return entityNames.every((name) =>
        attr.referral.some((r) => r.name === name),
      );
    } else {
      return entityNames.some((name) =>
        attr.referral.some((r) => r.name === name),
      );
    }
  };

/**
 * Generate a human-readable error message for missing attribute
 */
export const missingAttrMessage = (
  name: string,
  type: number | number[],
): string => {
  const types = Array.isArray(type) ? type : [type];
  const typeNames = types.map((t) => AttrTypeNames[t] ?? `type ${t}`).join("/");
  return `Attribute "${name}" (${typeNames}) is required`;
};

/**
 * Generate a human-readable error message for missing referral
 */
export const missingReferralMessage = (
  attrName: string,
  entityNames: string[],
): string => {
  return `Attribute "${attrName}" must reference: ${entityNames.join(", ")}`;
};

/**
 * Base Zod schema for entity referral
 */
const entityReferralSchema = z.object({
  id: z.number(),
  name: z.string(),
});

/**
 * Base Zod schema for entity attribute structure
 */
const entityAttrSchema = z.object({
  id: z.number(),
  name: z.string(),
  type: z.number(),
  isMandatory: z.boolean(),
  referral: z.array(entityReferralSchema),
});

/**
 * Base Zod schema for entity structure
 *
 * This provides a starting point for plugin schema definitions.
 * Extend this schema with .refine() to add custom validation rules.
 *
 * @example
 * ```typescript
 * const myEntitySchema = baseEntitySchema
 *   .refine(
 *     (entity) => requireAttr("hostname", AttrType.STRING)(entity.attrs),
 *     { message: "hostname attribute is required" }
 *   );
 * ```
 */
export const baseEntitySchema = z.object({
  id: z.number(),
  name: z.string(),
  attrs: z.array(entityAttrSchema),
});

/**
 * Helper to create a complete entity schema with attribute requirements
 *
 * @param requirements - Array of attribute requirements
 * @returns A Zod schema with all requirements applied
 *
 * @example
 * ```typescript
 * const networkDeviceSchema = createEntitySchema([
 *   { name: "hostname", type: AttrType.STRING },
 *   { name: "ip_address", type: AttrType.STRING },
 *   { name: "location", type: AttrType.OBJECT, referrals: ["Location"] },
 * ]);
 * ```
 */
interface AttrRequirement {
  name: string;
  type: number | number[];
  mustBeMandatory?: boolean;
  referrals?: string[];
  message?: string;
}

export const createEntitySchema = (
  requirements: AttrRequirement[],
): z.ZodType => {
  // We use z.ZodType as the intermediate type because .refine() creates
  // nested ZodEffects types that are difficult to express statically.
  // The return type ensures proper type safety for consumers.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let schema: z.ZodType<any> = baseEntitySchema;

  for (const req of requirements) {
    const attrMessage = req.message ?? missingAttrMessage(req.name, req.type);

    schema = schema.refine(
      (entity) =>
        requireAttr(req.name, req.type, {
          mustBeMandatory: req.mustBeMandatory,
        })(entity.attrs),
      { message: attrMessage },
    );

    if (req.referrals && req.referrals.length > 0) {
      const referralMessage = missingReferralMessage(req.name, req.referrals);
      schema = schema.refine(
        (entity) => requireReferral(req.name, req.referrals!)(entity.attrs),
        { message: referralMessage },
      );
    }
  }

  return schema;
};
