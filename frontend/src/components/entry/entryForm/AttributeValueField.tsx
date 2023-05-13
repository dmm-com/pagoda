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

import { DjangoContext } from "services/DjangoContext";

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
  const djangoContext = DjangoContext.getInstance();

  switch (type) {
    case djangoContext?.attrTypeValue.string:
      return <StringAttributeValueField control={control} attrId={schemaId} />;

    case djangoContext?.attrTypeValue.text:
      return (
        <StringAttributeValueField
          control={control}
          attrId={schemaId}
          multiline
        />
      );

    case djangoContext?.attrTypeValue.date:
      return (
        <DateAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.boolean:
      return <BooleanAttributeValueField attrId={schemaId} control={control} />;

    case djangoContext?.attrTypeValue.object:
      return (
        <ObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.group:
      return (
        <GroupAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.role:
      return (
        <RoleAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.named_object:
      return (
        <NamedObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.array_object:
      return (
        <ObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_group:
      return (
        <GroupAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_role:
      return (
        <RoleAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_string:
      return (
        <ArrayStringAttributeValueField control={control} attrId={schemaId} />
      );

    case djangoContext?.attrTypeValue.array_named_object:
      return (
        <ArrayNamedObjectAttributeValueField
          attrId={schemaId}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.array_named_object_boolean:
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
