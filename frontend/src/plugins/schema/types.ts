/**
 * Entity structure types for plugin schema validation
 *
 * These types represent the structure of an entity that plugins can validate
 * against to ensure the entity meets their requirements.
 */

/**
 * Attribute information in object form.
 * Converted from the attrs array for easy Zod schema validation.
 */
interface AttrInfo {
  type: number;
  isMandatory: boolean;
  referral: string[]; // Simplified to names only
}

/**
 * Attribute record - key is attribute name, value is attribute info.
 * This is the format that plugins validate against using Zod schemas.
 *
 * @example
 * ```typescript
 * // Converted from entity.attrs array:
 * {
 *   hostname: { type: 2, isMandatory: true, referral: [] },
 *   location: { type: 1, isMandatory: false, referral: ["DC1", "DC2"] }
 * }
 * ```
 */
export interface AttrRecord {
  [attrName: string]: AttrInfo;
}

/**
 * AttrType constants mirroring airone/lib/types.py
 *
 * These values are used to identify attribute types in the entity structure.
 * Combined types use bitwise OR operations.
 */
export const AttrType = {
  // Base types
  OBJECT: 1, // 1 << 0
  STRING: 2, // 1 << 1
  TEXT: 4, // 1 << 2
  BOOLEAN: 8, // 1 << 3
  GROUP: 16, // 1 << 4
  DATE: 32, // 1 << 5
  ROLE: 64, // 1 << 6
  DATETIME: 128, // 1 << 7
  NUMBER: 256, // 1 << 8

  // Modifier flags (internal use)
  _ARRAY: 1024, // 1 << 10
  _NAMED: 2048, // 1 << 11

  // Combined types
  NAMED_OBJECT: 2049, // _NAMED | OBJECT
  ARRAY_OBJECT: 1025, // _ARRAY | OBJECT
  ARRAY_STRING: 1026, // _ARRAY | STRING
  ARRAY_NUMBER: 1280, // _ARRAY | NUMBER
  ARRAY_NAMED_OBJECT: 3073, // _ARRAY | _NAMED | OBJECT
  ARRAY_NAMED_OBJECT_BOOLEAN: 3081, // Special type
  ARRAY_GROUP: 1040, // _ARRAY | GROUP
  ARRAY_ROLE: 1088, // _ARRAY | ROLE
} as const;
