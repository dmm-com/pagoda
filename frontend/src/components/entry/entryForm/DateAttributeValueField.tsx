import { TextField } from "@mui/material";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { DesktopDatePicker } from "@mui/x-date-pickers/DesktopDatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { Schema } from "./EntryFormSchema";

interface Props {
  attrId: number;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const DateAttributeValueField: FC<Props> = ({
  attrId,
  control,
  setValue,
}) => {
  return (
    <Controller
      name={`attrs.${attrId}.value.asString`}
      control={control}
      defaultValue=""
      render={({ field, fieldState: { error } }) => (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DesktopDatePicker
            label="月日を選択"
            inputFormat="yyyy/MM/dd"
            value={field.value}
            onChange={(date: Date | null) => {
              let settingDateValue = "";
              if (date !== null) {
                settingDateValue = `${date.getFullYear()}-${
                  date.getMonth() + 1
                }-${date.getDate()}`;
              }
              setValue(`attrs.${attrId}.value.asString`, settingDateValue);
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                error={error != null}
                helperText={error?.message}
              />
            )}
          />
        </LocalizationProvider>
      )}
    />
  );
};
