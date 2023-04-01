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
  attrName: string;
  attrInfo: EditableEntryAttrs;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const AttributeValueFields: FC<Props> = ({
  attrName,
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
          attrName={attrName}
          attrType={attrInfo.type}
          isMandatory={attrInfo.isMandatory}
        />
      );

    case djangoContext?.attrTypeValue.text:
      return (
        <StringAttributeValueField
          control={control}
          attrName={attrName}
          attrType={attrInfo.type}
          isMandatory={attrInfo.isMandatory}
          multiline
        />
      );

    case djangoContext?.attrTypeValue.date:
      return (
        <DateAttributeValueField
          attrName={attrName}
          isMandatory={attrInfo.isMandatory}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.boolean:
      return (
        <BooleanAttributeValueField
          attrName={attrName}
          isMandatory={attrInfo.isMandatory}
          control={control}
        />
      );

    case djangoContext?.attrTypeValue.object:
      return (
        <ObjectAttributeValueField
          attrName={attrName}
          control={control}
          setValue={setValue}
          schemaId={attrInfo.schema.id}
        />
      );

    case djangoContext?.attrTypeValue.group:
      return (
        <GroupAttributeValueField
          attrName={attrName}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.role:
      return (
        <RoleAttributeValueField
          attrName={attrName}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.named_object:
      return (
        <NamedObjectAttributeValueField
          attrName={attrName}
          schemaId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.array_object:
      return (
        <ObjectAttributeValueField
          attrName={attrName}
          schemaId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_group:
      return (
        <GroupAttributeValueField
          attrName={attrName}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_role:
      return (
        <RoleAttributeValueField
          attrName={attrName}
          control={control}
          setValue={setValue}
          multiple
        />
      );

    case djangoContext?.attrTypeValue.array_string:
      return (
        <ArrayStringAttributeValueField
          control={control}
          attrName={attrName}
          attrType={attrInfo.type}
          isMandatory={attrInfo.isMandatory}
        />
      );

    case djangoContext?.attrTypeValue.array_named_object:
      return (
        <ArrayNamedObjectAttributeValueField
          attrName={attrName}
          schemaId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
        />
      );

    case djangoContext?.attrTypeValue.array_named_object_boolean:
      return (
        <ArrayNamedObjectAttributeValueField
          attrName={attrName}
          schemaId={attrInfo.schema.id}
          control={control}
          setValue={setValue}
          withBoolean
        />
      );

    default:
      throw new Error(`Unknown attribute type: ${attrInfo.type}`);
  }
};
