/**
 * Converter functions to transform API responses to validation-ready structures
 */

import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";

import { AttrRecord } from "./types";

/**
 * Convert an EntityDetail API response to an AttrRecord for validation
 *
 * This function transforms the attrs array into an object keyed by attribute name,
 * which allows plugins to define simple Zod schemas for validation.
 *
 * @param entity - The EntityDetail from the API
 * @returns AttrRecord suitable for Zod schema validation
 *
 * @example
 * ```typescript
 * // Input: entity with attrs array
 * {
 *   id: 1,
 *   name: "Server",
 *   attrs: [
 *     { name: "hostname", type: 2, isMandatory: true, referral: [] },
 *     { name: "location", type: 1, isMandatory: false, referral: [{id:1, name:"DC1"}] }
 *   ]
 * }
 *
 * // Output: object keyed by attribute name
 * {
 *   hostname: { type: 2, isMandatory: true, referral: [] },
 *   location: { type: 1, isMandatory: false, referral: ["DC1"] }
 * }
 * ```
 */
export function toAttrRecord(entity: EntityDetail): AttrRecord {
  const record: AttrRecord = {};

  for (const attr of entity.attrs) {
    record[attr.name] = {
      type: attr.type,
      isMandatory: attr.isMandatory,
      referral: (attr.referral ?? []).map((r) => r.name),
    };
  }

  return record;
}
