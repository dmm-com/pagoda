import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import React, { FC } from "react";
import { Control } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { BooleanAttributeValueField } from "./BooleanAttributeValueField";
import { DateAttributeValueField } from "./DateAttributeValueField";
import { DateTimeAttributeValueField } from "./DateTimeAttributeValueField";
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

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  type: number;
  schemaId: number;
  isDisabled?: boolean;
}

export const AttributeValueField: FC<Props> = ({
  control,
  setValue,
  type,
  schemaId,
  isDisabled = false,
}) => {
  switch (type) {
    case EntryAttributeTypeTypeEnum.STRING:
      return (
        <StringAttributeValueField
          control={control}
          attrId={schemaId}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.TEXT:
      return (
        <StringAttributeValueField
          control={control}
          attrId={schemaId}
          isDisabled={isDisabled}
          multiline
        />
      );

    case EntryAttributeTypeTypeEnum.DATE:
      return (
        <DateAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.DATETIME:
      return (
        <DateTimeAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return (
        <BooleanAttributeValueField
          attrId={schemaId}
          control={control}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <ObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.GROUP:
      return (
        <GroupAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.ROLE:
      return (
        <RoleAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <NamedObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      return (
        <ObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
          multiple
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_GROUP:
      return (
        <GroupAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
          multiple
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_ROLE:
      return (
        <RoleAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
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
          isDisabled={isDisabled}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT_BOOLEAN:
      return (
        <ArrayNamedObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          isDisabled={isDisabled}
          withBoolean
        />
      );

    default:
      throw new Error(`Unknown attribute type: ${type}`);
  }
};
