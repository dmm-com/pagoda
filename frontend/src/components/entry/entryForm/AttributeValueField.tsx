import React, { FC } from "react";
import { Control } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { BooleanAttributeValueField } from "./BooleanAttributeValueField";
import { DateAttributeValueField } from "./DateAttributeValueField";
import { EditableEntryAttrs } from "./EditableEntry";
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
  attrInfo: EditableEntryAttrs;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const AttributeValueField: FC<Props> = ({
  attrInfo,
  control,
  setValue,
}) => {
  const djangoContext = DjangoContext.getInstance();

  switch (attrInfo.type) {
    case djangoContext?.attrTypeValue.string:
      return (
        <StringAttributeValueField
          control={control}
          attrId={attrInfo.schema.id}
        />
      );

    case djangoContext?.attrTypeValue.text:
      return (
        <StringAttributeValueField
          control={control}
          attrId={attrInfo.schema.id}
          multiline
        />
      );

    case djangoContext?.attrTypeValue.date:
      return (
        <DateAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.boolean:
      return (
        <BooleanAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
        />
      );

    case djangoContext?.attrTypeValue.object:
      return (
        <ObjectAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.group:
      return (
        <GroupAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.role:
      return (
        <RoleAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.named_object:
      return (
        <NamedObjectAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.array_object:
      return (
        <ObjectAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_group:
      return (
        <GroupAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_role:
      return (
        <RoleAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_string:
      return (
        <ArrayStringAttributeValueField
          control={control}
          attrId={attrInfo.schema.id}
        />
      );

    case djangoContext?.attrTypeValue.array_named_object:
      return (
        <ArrayNamedObjectAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.array_named_object_boolean:
      return (
        <ArrayNamedObjectAttributeValueField
          attrId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
          withBoolean
        />
      );

    default:
      throw new Error(`Unknown attribute type: ${attrInfo.type}`);
  }
};
