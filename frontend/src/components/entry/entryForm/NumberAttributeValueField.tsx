import { TextField } from "@mui/material";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntryFormSchema";

interface Props {
  attrId: number;
  control: Control<Schema>;
  isDisabled?: boolean;
}

export const NumberAttributeValueField: FC<Props> = ({
  attrId,
  control,
  isDisabled = false,
}) => {
  return (
    <Controller
      name={`attrs.${attrId}.value.asNumber`}
      control={control}
      defaultValue={null}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          type="number"
          variant="standard"
          error={error != null}
          helperText={error?.message}
          fullWidth
          disabled={isDisabled}
          value={field.value ?? ""}
          onChange={(e) => {
            const value = e.target.value;
            field.onChange(value === "" ? null : Number(value));
          }}
        />
      )}
    />
  );
};
