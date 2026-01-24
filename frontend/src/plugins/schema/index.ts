/**
 * Entity Schema Validation Module
 *
 * This module provides types and utilities for plugins to define
 * entity structure requirements using Zod schemas.
 *
 * @example
 * ```typescript
 * import {
 *   AttrType,
 *   baseEntitySchema,
 *   requireAttr,
 *   validateEntityStructure,
 *   toEntityStructure,
 * } from "plugins/schema";
 *
 * // Define entity requirements
 * const mySchema = baseEntitySchema
 *   .refine(
 *     (entity) => requireAttr("hostname", AttrType.STRING)(entity.attrs),
 *     { message: "hostname attribute is required" }
 *   );
 *
 * // Use in plugin
 * const plugin: EntityViewPlugin = {
 *   entitySchema: mySchema,
 *   // ...
 * };
 * ```
 */

// Types;

;

// Helpers;

;
;

// Converter
export { toEntityStructure } from "./converter";

// Validator;

export {
  validateEntityStructure,
  
  
} from "./validator";
