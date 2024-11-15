import { Checkbox } from "@mui/material";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntryFormSchema";

interface Props {
  attrId: number;
  control: Control<Schema>;
  isDisabled?: boolean;
}

export const BooleanAttributeValueField: FC<Props> = ({
  attrId,
  control,
  isDisabled = false,
}) => {
  return (
    <Controller
      name={`attrs.${attrId}.value.asBoolean`}
      control={control}
      defaultValue={false}
      render={({ field }) => (
        <Checkbox
          checked={field.value}
          onChange={(e) => field.onChange(e.target.checked)}
          disabled={isDisabled}
        />
      )}
    />
  );
};
