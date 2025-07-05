import {
  AttributeData,
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  EntryAttributeValue,
  EntryAttributeValueObject,
  EntryRetrieve,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  EditableEntryAttrValue,
  EditableEntryAttrs,
} from "components/entry/entryForm/EditableEntry";
import { Schema } from "components/entry/entryForm/EntryFormSchema";

type SchemaAttrs = Schema["attrs"] extends Record<string, infer U> ? U : never;

export type EntryAttributeValueType =
  | string
  | boolean
  | number
  | null
  | undefined
  | Array<string>
  | Array<number>
  | { id: number | null; name: string }
  | Array<{ id: number | null; name: string }>
  | Array<{ id: number | null; name: string; _boolean: boolean }>;

// Convert Entry information from server-side value to presentation format.
// (NOTE) It might be needed to be refactored because if server returns proper format with frontend, this is not necessary.
export function formalizeEntryInfo(
  entry: EntryRetrieve | undefined,
  entity: EntityDetail,
  excludeAttrs: string[],
): Schema {
  return {
    name: entry ? entry.name : "",
    schema: {
      id: entity.id,
      name: entity.name,
    },
    attrs: entity.attrs
      .filter((attr) => !excludeAttrs.includes(attr.name))
      .filter((attr) => attr.id != 0)
      .reduce((acc: Record<string, SchemaAttrs>, attr) => {
        function getAttrValue(
          attrType: typeof EntryAttributeTypeTypeEnum[keyof typeof EntryAttributeTypeTypeEnum],
          value: EntryAttributeValue | undefined,
          attrDetail: EntityDetail["attrs"][0],
        ): EditableEntryAttrValue {
          if (!value) {
            // Use defaultValue from EntityAttr if available
            // Backend returns raw primitive values (string, boolean, null)
            // Auto-generated types show it as object but it's actually scalar values
            const defaultValue = attrDetail.defaultValue;
            
            // Default values for when no default is specified
            const defaults = {
              asString: "",
              asBoolean: false,
              asArrayString: [{ value: "" }],
              asArrayObject: [],
              asArrayGroup: [],
              asArrayRole: [],
              asArrayNamedObject: [{ name: "", object: null, _boolean: false }],
              asObject: null,
              asGroup: null,
              asRole: null,
              asNamedObject: { name: "", object: null },
              asNumber: null,
            };

            // Apply defaultValue for supported types (backend returns raw primitive values)
            if (defaultValue !== null && defaultValue !== undefined) {
              switch (attrType) {
                case EntryAttributeTypeTypeEnum.STRING:
                case EntryAttributeTypeTypeEnum.TEXT:
                  // Handle both string values and potential object wrappers
                  if (typeof defaultValue === "string") {
                    defaults.asString = defaultValue;
                  } else if (typeof defaultValue === "object" && defaultValue !== null && "asString" in defaultValue) {
                    defaults.asString = (defaultValue as { asString: string }).asString;
                  }
                  break;
                case EntryAttributeTypeTypeEnum.BOOLEAN:
                  // Handle both boolean values and potential object wrappers
                  if (typeof defaultValue === "boolean") {
                    defaults.asBoolean = defaultValue;
                  } else if (typeof defaultValue === "object" && defaultValue !== null && "asBoolean" in defaultValue) {
                    defaults.asBoolean = (defaultValue as { asBoolean: boolean }).asBoolean;
                  }
                  break;
                case EntryAttributeTypeTypeEnum.NUMBER:
                  // Handle both number values and potential object wrappers
                  if (typeof defaultValue === "number") {
                    (defaults as any).asNumber = defaultValue;
                  } else if (typeof defaultValue === "object" && defaultValue !== null && "asNumber" in defaultValue) {
                    (defaults as any).asNumber = (defaultValue as { asNumber: number }).asNumber;
                  }
                  break;
              }
            }

            return defaults;
          }

          switch (attrType) {
            case EntryAttributeTypeTypeEnum.ARRAY_STRING:
              return (value?.asArrayString?.length ?? 0 > 0)
                ? {
                    asArrayString: value.asArrayString?.map((value) => {
                      return { value: value };
                    }),
                  }
                : { asArrayString: [{ value: "" }] };
            case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
            case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT_BOOLEAN:
              return (value?.asArrayNamedObject?.length ?? 0 > 0)
                ? {
                    asArrayNamedObject: value.asArrayNamedObject?.map(
                      (item) => ({
                        name: item.name,
                        object: item.object,
                        _boolean: item._boolean,
                      }),
                    ),
                  }
                : {
                    asArrayNamedObject: [
                      { name: "", object: null, _boolean: false },
                    ],
                  };
            default:
              // u4ed6u306eu578bu306eu5834u5408u306fu9069u5207u306bu5909u63db
              const result: EditableEntryAttrValue = {};

              if (value.asBoolean !== undefined) {
                result.asBoolean = value.asBoolean;
              }

              if (value.asString !== undefined) {
                result.asString = value.asString;
              }

              if (value.asObject !== undefined) {
                result.asObject = value.asObject;
              }

              if (value.asGroup !== undefined) {
                result.asGroup = value.asGroup;
              }

              if (value.asRole !== undefined) {
                result.asRole = value.asRole;
              }

              if (value.asNamedObject !== undefined) {
                result.asNamedObject = value.asNamedObject;
              }

              if (value.asArrayObject !== undefined) {
                result.asArrayObject = value.asArrayObject;
              }

              if (value.asArrayGroup !== undefined) {
                result.asArrayGroup = value.asArrayGroup;
              }

              if (value.asArrayRole !== undefined) {
                result.asArrayRole = value.asArrayRole;
              }

              if (value.asNumber !== undefined) {
                result.asNumber = value.asNumber;
              }

              return result;
          }
        }

        const value = entry?.attrs.find((a) => a.schema.id == attr.id)?.value;

        acc[String(attr.id)] = {
          index: attr.index,
          type: attr.type as typeof EntryAttributeTypeTypeEnum[keyof typeof EntryAttributeTypeTypeEnum],
          isMandatory: attr.isMandatory,
          schema: {
            id: attr.id,
            name: attr.name,
          },
          value: getAttrValue(attr.type as typeof EntryAttributeTypeTypeEnum[keyof typeof EntryAttributeTypeTypeEnum], value, attr),
        };
        return acc;
      }, {}),
  };
}

export function convertAttrsFormatCtoS(
  attrs: Record<string, EditableEntryAttrs>,
): AttributeData[] {
  return Object.entries(attrs).map(([{}, attr]) => {
    function getAttrValue(
      attrType: typeof EntryAttributeTypeTypeEnum[keyof typeof EntryAttributeTypeTypeEnum],
      attrValue: EditableEntryAttrValue,
    ): EntryAttributeValueType {
      switch (attrType) {
        case EntryAttributeTypeTypeEnum.STRING:
        case EntryAttributeTypeTypeEnum.TEXT:
        case EntryAttributeTypeTypeEnum.DATE:
        case EntryAttributeTypeTypeEnum.DATETIME:
          return attrValue.asString;

        case EntryAttributeTypeTypeEnum.BOOLEAN:
          return attrValue.asBoolean;

        case EntryAttributeTypeTypeEnum.NUMBER:
          return attrValue.asNumber;

        case EntryAttributeTypeTypeEnum.OBJECT:
          return attrValue.asObject?.id ?? null;

        case EntryAttributeTypeTypeEnum.GROUP:
          return attrValue.asGroup?.id ?? null;

        case EntryAttributeTypeTypeEnum.ROLE:
          return attrValue.asRole?.id ?? null;

        case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
          return {
            id: attrValue.asNamedObject?.object?.id ?? null,
            name: attrValue.asNamedObject?.name ?? "",
          };

        case EntryAttributeTypeTypeEnum.ARRAY_STRING:
          return attrValue.asArrayString?.map((x) => x.value);

        case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
          return attrValue.asArrayObject?.map((x) => x.id);

        case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
          return attrValue.asArrayGroup?.map((x) => x.id);

        case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
          return attrValue.asArrayRole?.map((x) => x.id);

        case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
          return attrValue.asArrayNamedObject?.map((x) => {
            return {
              id: x.object?.id ?? null,
              name: x.name,
            };
          });

        case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT_BOOLEAN:
          return (
            attrValue.asArrayNamedObject as {
              name: string;
              object: EntryAttributeValueObject;
              _boolean: boolean;
            }[]
          )?.map((x) => {
            return {
              id: x.object?.id ?? null,
              name: x.name,
              boolean: x._boolean,
            };
          });

        default:
          throw new Error(`unknown attribute type ${attrType}`);
      }
    }

    return {
      id: attr.schema.id,
      value: getAttrValue(attr.type, attr.value),
    };
  });
}
