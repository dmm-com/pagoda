import {
  EntryAttributeValue,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";

export const getEntryAttributeValue = (
  type: number,
  value?: any,
): EntryAttributeValue => {
  const respValue: EntryAttributeValue = {} as EntryAttributeValue;

  switch (type) {
    case EntryAttributeTypeTypeEnum.OBJECT:
      respValue.asObject = value;

    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.TEXT:
    case EntryAttributeTypeTypeEnum.DATE:
    case EntryAttributeTypeTypeEnum.DATETIME:
      respValue.asString = value;

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      respValue.asBoolean = value;

    case EntryAttributeTypeTypeEnum.NUMBER:
      respValue.asNumber = value;

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      respValue.asNamedObject = value;

    case EntryAttributeTypeTypeEnum.GROUP:
      respValue.asGroup = value;

    case EntryAttributeTypeTypeEnum.ROLE:
      respValue.asRole = value;

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      respValue.asArrayObject = value;

    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      respValue.asArrayString = value;

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
      respValue.asArrayNamedObject = value;

    case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
      respValue.asArrayGroup = value;

    case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
      respValue.asArrayRole = value;

    case EntryAttributeTypeTypeEnum.ARRAY_NUMBER:
      respValue.asArrayNumber = value;
  }

  return respValue;
};
