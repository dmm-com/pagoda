import { Box, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { DesktopDatePicker } from "@mui/x-date-pickers/DesktopDatePicker";
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

export const DateAttributeValueField: FC<Props> = ({
  attrId,
  control,
  setValue,
  isDisabled = false,
}) => {
  return (
    <StyledBox>
      <StyledTypography variant="caption">月日を選択</StyledTypography>
      <Controller
        name={`attrs.${attrId}.value.asString`}
        control={control}
        defaultValue=""
        render={({ field, fieldState: { error } }) => (
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DesktopDatePicker
              format="yyyy/MM/dd"
              value={field.value ? new Date(field.value) : null}
              onChange={(date: Date | null) => {
                let settingDateValue = "";
                if (date !== null) {
                  settingDateValue = `${date.getFullYear()}-${
                    date.getMonth() + 1
                  }-${date.getDate()}`;
                }
                setValue(`attrs.${attrId}.value.asString`, settingDateValue, {
                  shouldDirty: true,
                  shouldValidate: true,
                });
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
