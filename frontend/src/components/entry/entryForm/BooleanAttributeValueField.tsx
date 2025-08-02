import { Box, Checkbox, FormHelperText } from "@mui/material";
import { FC } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntryFormSchema";

import { getStagedHelperTextStyle } from "utils/styleUtils";

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
      render={({ field, fieldState: { error, isDirty } }) => (
        <Box>
          <Checkbox
            checked={field.value}
            onChange={(e) => field.onChange(e.target.checked)}
            disabled={isDisabled}
          />
          {error && (
            <FormHelperText
              error
              sx={getStagedHelperTextStyle(!!error, isDirty)}
            >
              {error.message}
            </FormHelperText>
          )}
        </Box>
      )}
    />
  );
};
