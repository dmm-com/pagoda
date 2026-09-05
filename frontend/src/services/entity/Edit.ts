import { BaseAttributeTypes } from "services/Constants";

// number[] carries the OBJECT / ARRAY_OBJECT defaults, which are entry ids.
type EntityAttrDefaultValue =
  | string
  | number
  | boolean
  | number[]
  | null
  | undefined;

// Convert the form's attr.defaultValue to the API payload value.
//
// An emptied input means "no default value" and must be sent as null so the
// backend clears the stored default. Note that Number("") is 0 (not NaN), so
// an empty string must be handled explicitly, otherwise clearing the field
// silently stores 0 as the default value.
export function processAttrDefaultValue(
  attrType: number,
  defaultValue: EntityAttrDefaultValue,
): EntityAttrDefaultValue {
  if (defaultValue == null || defaultValue === "") {
    return null;
  }

  if (attrType === BaseAttributeTypes.number) {
    const numValue = Number(defaultValue);
    return isNaN(numValue) ? null : numValue;
  }
  if (attrType === BaseAttributeTypes.bool) {
    return Boolean(defaultValue);
  }
  if (
    attrType === BaseAttributeTypes.string ||
    attrType === BaseAttributeTypes.text
  ) {
    return String(defaultValue);
  }

  return defaultValue;
}
