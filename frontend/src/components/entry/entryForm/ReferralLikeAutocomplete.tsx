import { Autocomplete, TextField } from "@mui/material";
import React from "react";

interface Props<T extends { id: number; name: string }> {
  options: T[];
  value: T | T[] | null;
  handleChange: (value: T | T[] | null) => void;
  setKeyword?: (value: string) => void;
  multiple?: boolean;
  disabled?: boolean;
  error?: { message?: string };
}

export const ReferralLikeAutocomplete = <
  T extends { id: number; name: string }
>({
  multiple,
  options,
  value,
  handleChange,
  setKeyword,
  disabled,
  error,
}: Props<T>) => {
  const _handleChange = (value: T | T[] | null) => {
    const isArray = Array.isArray(value);
    if (value != null) {
      if (multiple && !isArray) {
        throw new Error("multiple values expected, but single value is given");
      }
      if (!multiple && isArray) {
        throw new Error("single value expected, but multiple values are given");
      }
    }
    handleChange(value);
  };

  return (
    <Autocomplete
      sx={{ width: "280px" }}
      multiple={multiple}
      disabled={disabled}
      options={options ?? []}
      value={value}
      getOptionLabel={(option) => option?.name ?? "-NOT SET-"}
      isOptionEqualToValue={(option, value) => option.id === value.id}
      onChange={(_e, value) => _handleChange(value)}
      onInputChange={(e, value) =>
        // To run only if the user changes
        e != null && setKeyword != null && setKeyword(value)
      }
      renderInput={(params) => (
        <TextField
          {...params}
          error={error != null}
          helperText={error?.message}
          size="small"
          placeholder={multiple ? "" : "-NOT SET-"}
        />
      )}
    />
  );
};
