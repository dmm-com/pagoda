/**
 * Converter functions to transform API responses to validation-ready structures
 */

import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";

import { EntityStructure, EntityAttrStructure, EntityReferral } from "./types";

/**
 * Convert an EntityDetail API response to an EntityStructure for validation
 *
 * This function extracts only the fields needed for schema validation
 * from the full API response.
 *
 * @param entity - The EntityDetail from the API
 * @returns EntityStructure suitable for Zod schema validation
 */
export function toEntityStructure(entity: EntityDetail): EntityStructure {
  return {
    id: entity.id,
    name: entity.name,
    attrs: entity.attrs.map((attr): EntityAttrStructure => {
      // Handle referral which may be undefined/null in the API response
      const referral: EntityReferral[] = (attr.referral ?? []).map((ref) => ({
        id: ref.id,
        name: ref.name,
      }));

      return {
        id: attr.id,
        name: attr.name,
        type: attr.type,
        isMandatory: attr.isMandatory,
        referral,
      };
    }),
  };
}
