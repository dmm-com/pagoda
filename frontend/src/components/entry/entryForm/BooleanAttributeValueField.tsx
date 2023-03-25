import { Checkbox } from "@mui/material";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntryFormSchema";

interface Props {
  attrName: string;
  isMandatory: boolean;
  control: Control<Schema>;
}

export const BooleanAttributeValueField: FC<Props> = ({
  attrName,
  control,
}) => {
  return (
    <Controller
      name={`attrs.${attrName}.value.asBoolean`}
      control={control}
      defaultValue={false}
      render={({ field }) => (
        <Checkbox
          checked={field.value}
          onChange={(e) => field.onChange(e.target.checked)}
        />
      )}
    />
  );
};
