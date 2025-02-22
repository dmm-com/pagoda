import { Box, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { DateTimePicker } from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { Schema } from "./EntryFormSchema";

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
}));

const StyledTypography = styled(Typography)(({}) => ({
  color: "rgba(0, 0, 0, 0.6)",
}));

interface Props {
  attrId: number;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  isDisabled?: boolean;
}

export const DateTimeAttributeValueField: FC<Props> = ({
  attrId,
  control,
  setValue,
  isDisabled = false,
}) => {
  return (
    <StyledBox>
      <StyledTypography variant="caption">日時を選択</StyledTypography>
      <Controller
        name={`attrs.${attrId}.value.asString`}
        control={control}
        defaultValue=""
        render={({ field, fieldState: { error } }) => (
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DateTimePicker
              format="yyyy/MM/dd HH:mm:ss"
              value={field.value ? new Date(field.value) : null}
              onChange={(date: Date | null) => {
                setValue(
                  `attrs.${attrId}.value.asString`,
                  date != null && !isNaN(date.getTime()) // if the date is valid
                    ? date.toISOString()
                    : "",
                  {
                    shouldDirty: true,
                    shouldValidate: true,
                  }
                );
              }}
              slotProps={{
                textField: {
                  error: error != null,
                  helperText: error?.message,
                  size: "small",
                  fullWidth: false,
                },
              }}
              disabled={isDisabled}
            />
          </LocalizationProvider>
        )}
      />
    </StyledBox>
  );
};
