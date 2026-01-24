/**
 * Validation utilities for entity schema checking
 */

import { z } from "zod";

import { EntityStructure } from "./types";

/**
 * Result of a schema validation operation
 */
interface ValidationResult {
  /** Whether the validation passed */
  success: boolean;
  /** Array of validation errors (empty if success is true) */
  errors: z.ZodIssue[];
}

/**
 * Validate an entity structure against a Zod schema
 *
 * This is the main entry point for runtime validation of entities
 * against plugin-defined schemas.
 *
 * @param entity - The entity structure to validate
 * @param schema - The Zod schema to validate against
 * @returns ValidationResult containing success status and any errors
 *
 * @example
 * ```typescript
 * const result = validateEntityStructure(entity, plugin.entitySchema);
 * if (!result.success) {
 *   console.error("Validation failed:", result.errors);
 * }
 * ```
 */
export function validateEntityStructure(
  entity: EntityStructure,
  schema: z.ZodType<EntityStructure>,
): ValidationResult {
  const result = schema.safeParse(entity);

  if (result.success) {
    return { success: true, errors: [] };
  }

  return {
    success: false,
    errors: result.error.issues,
  };
}

/**
 * Format Zod validation errors into human-readable strings
 *
 * @param errors - Array of Zod issues from validation
 * @returns Array of formatted error messages
 *
 * @example
 * ```typescript
 * const messages = formatValidationErrors(result.errors);
 * // ["attrs: hostname attribute (STRING type) is required"]
 * ```
 */
export function formatValidationErrors(errors: z.ZodIssue[]): string[] {
  return errors.map((issue) => {
    const path = issue.path.join(".");
    return path ? `${path}: ${issue.message}` : issue.message;
  });
}

/**
 * Create a detailed validation error report
 *
 * @param errors - Array of Zod issues from validation
 * @returns Object with structured error information
 */
interface ValidationErrorReport {
  summary: string;
  details: Array<{
    path: string;
    message: string;
    code: string;
  }>;
}

export function createValidationErrorReport(
  errors: z.ZodIssue[],
): ValidationErrorReport {
  return {
    summary: `${errors.length} validation error${errors.length !== 1 ? "s" : ""} found`,
    details: errors.map((issue) => ({
      path: issue.path.join(".") || "(root)",
      message: issue.message,
      code: issue.code,
    })),
  };
}
