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

// Convert Entry information from server-side value to presentation format.
// (NOTE) It might be needed to be refactored because if server returns proper format with frontend, this is not necessary.
export function formalizeEntryInfo(
  entry: EntryRetrieve | undefined,
  entity: EntityDetail,
  excludeAttrs: string[]
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
      .reduce((acc: Record<string, any>, attr) => {
        function getAttrValue(
          attrType: number,
          value: EntryAttributeValue | undefined
        ) {
          if (!value) {
            return {
              asString: "",
              asBoolean: false,
              asObject: undefined,
              asGroup: undefined,
              asRole: undefined,
              asNamedObject: { name: "", object: null },
              asArrayString: [],
              asArrayObject: [],
              asArrayGroup: [],
              asArrayRole: [],
              asArrayNamedObject: [],
            };
          }

          switch (attrType) {
            case EntryAttributeTypeTypeEnum.ARRAY_STRING:
              return value?.asArrayString?.length ?? 0 > 0
                ? {
                    asArrayString: value.asArrayString?.map((value) => {
                      return { value: value };
                    }),
                  }
                : { asArrayString: [{ value: "" }] };
            case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
            case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT_BOOLEAN:
              return value?.asArrayNamedObject?.length ?? 0 > 0
                ? value
                : {
                    asArrayNamedObject: [
                      { name: "", object: null, _boolean: false },
                    ],
                  };
            default:
              return value;
          }
        }

        const value = entry?.attrs.find((a) => a.schema.id == attr.id)?.value;

        acc[String(attr.id)] = {
          index: attr.index,
          type: attr.type,
          isMandatory: attr.isMandatory,
          schema: {
            id: attr.id,
            name: attr.name,
          },
          value: getAttrValue(attr.type, value),
        };
        return acc;
      }, {}),
  };
}

export function convertAttrsFormatCtoS(
  attrs: Record<string, EditableEntryAttrs>
): AttributeData[] {
  return Object.entries(attrs).map(([{}, attr]) => {
    function getAttrValue(attrType: number, attrValue: EditableEntryAttrValue) {
      switch (attrType) {
        case EntryAttributeTypeTypeEnum.STRING:
        case EntryAttributeTypeTypeEnum.TEXT:
        case EntryAttributeTypeTypeEnum.DATE:
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
