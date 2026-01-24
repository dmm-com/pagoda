/**
 * Entity structure types for plugin schema validation
 *
 * These types represent the structure of an entity that plugins can validate
 * against to ensure the entity meets their requirements.
 */

/**
 * Simplified entity structure for validation purposes.
 * This is derived from the API EntityDetail response but contains only
 * the fields needed for schema validation.
 */
export interface EntityStructure {
  id: number;
  name: string;
  attrs: EntityAttrStructure[];
}

/**
 * Simplified entity attribute structure for validation.
 */
export interface EntityAttrStructure {
  id: number;
  name: string;
  type: number;
  isMandatory: boolean;
  referral: EntityReferral[];
}

/**
 * Entity referral structure for attributes that reference other entities.
 */
export interface EntityReferral {
  id: number;
  name: string;
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

/**
 * Type representing all possible AttrType values
 */
type AttrTypeValue = (typeof AttrType)[keyof typeof AttrType];

/**
 * Human-readable names for attribute types
 */
export const AttrTypeNames: Record<number, string> = {
  [AttrType.OBJECT]: "Object",
  [AttrType.STRING]: "String",
  [AttrType.TEXT]: "Text",
  [AttrType.BOOLEAN]: "Boolean",
  [AttrType.GROUP]: "Group",
  [AttrType.DATE]: "Date",
  [AttrType.ROLE]: "Role",
  [AttrType.DATETIME]: "DateTime",
  [AttrType.NUMBER]: "Number",
  [AttrType.NAMED_OBJECT]: "Named Object",
  [AttrType.ARRAY_OBJECT]: "Array of Objects",
  [AttrType.ARRAY_STRING]: "Array of Strings",
  [AttrType.ARRAY_NUMBER]: "Array of Numbers",
  [AttrType.ARRAY_NAMED_OBJECT]: "Array of Named Objects",
  [AttrType.ARRAY_NAMED_OBJECT_BOOLEAN]: "Array of Named Objects with Boolean",
  [AttrType.ARRAY_GROUP]: "Array of Groups",
  [AttrType.ARRAY_ROLE]: "Array of Roles",
};
