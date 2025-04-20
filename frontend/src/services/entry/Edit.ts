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

// zodの型推論を使ってEditableEntryAttrsの型を定義
type SchemaAttrs = Schema["attrs"] extends Record<string, infer U> ? U : never;

// 属性値の型定義（テストでも使用するためにエクスポート）
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
          attrType: EntryAttributeTypeTypeEnum,
          value: EntryAttributeValue | undefined,
        ): EditableEntryAttrValue {
          if (!value) {
            return {
              asString: "",
              asBoolean: false,
              asArrayString: [],
              asArrayObject: [],
              asArrayGroup: [],
              asArrayRole: [],
              asArrayNamedObject: [],
              asObject: null,
              asGroup: null,
              asRole: null,
              asNamedObject: { name: "", object: null },
            };
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

              return result;
          }
        }

        const value = entry?.attrs.find((a) => a.schema.id == attr.id)?.value;

        acc[String(attr.id)] = {
          index: attr.index,
          type: attr.type as EntryAttributeTypeTypeEnum,
          isMandatory: attr.isMandatory,
          schema: {
            id: attr.id,
            name: attr.name,
          },
          value: getAttrValue(attr.type as EntryAttributeTypeTypeEnum, value),
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
      attrType: EntryAttributeTypeTypeEnum,
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
