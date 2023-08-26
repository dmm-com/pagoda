import React, { FC } from "react";
import { Control } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { BooleanAttributeValueField } from "./BooleanAttributeValueField";
import { DateAttributeValueField } from "./DateAttributeValueField";
import { Schema } from "./EntryFormSchema";
import { GroupAttributeValueField } from "./GroupAttributeValueField";
import {
  ArrayNamedObjectAttributeValueField,
  NamedObjectAttributeValueField,
  ObjectAttributeValueField,
} from "./ObjectAttributeValueField";
import { RoleAttributeValueField } from "./RoleAttributeValueField";
import {
  ArrayStringAttributeValueField,
  StringAttributeValueField,
} from "./StringAttributeValueField";

import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  type: number;
  schemaId: number;
}

export const AttributeValueField: FC<Props> = ({
  control,
  setValue,
  type,
  schemaId,
}) => {
  switch (type) {
    case EntryAttributeTypeTypeEnum.STRING:
      return <StringAttributeValueField control={control} attrId={schemaId} />;

    case EntryAttributeTypeTypeEnum.TEXT:
      return (
        <StringAttributeValueField
          control={control}
          attrId={schemaId}
          multiline
        />
      );

    case EntryAttributeTypeTypeEnum.DATE:
      return (
        <DateAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return <BooleanAttributeValueField attrId={schemaId} control={control} />;

    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <ObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case EntryAttributeTypeTypeEnum.GROUP:
      return (
        <GroupAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case EntryAttributeTypeTypeEnum.ROLE:
      return (
        <RoleAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <NamedObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      return (
        <ObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
      return (
        <GroupAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
      return (
        <RoleAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return (
        <ArrayStringAttributeValueField control={control} attrId={schemaId} />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
      return (
        <ArrayNamedObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT_BOOLEAN:
      return (
        <ArrayNamedObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          withBoolean
        />
      );

    default:
      throw new Error(`Unknown attribute type: ${type}`);
  }
};
