import {
  Autocomplete,
  Box,
  Chip,
  FormControl,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useMemo } from "react";
import { Control, Controller } from "react-hook-form";

import { Schema } from "./EntryFormSchema";

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  width: "100%",
  gap: "0 12px",
}));

type Choice = { value: string; label: string };

interface CommonProps {
  attrId: number;
  control: Control<Schema>;
  choices: Choice[];
  isDisabled?: boolean;
}

export const SelectAttributeValueField: FC<CommonProps> = ({
  attrId,
  control,
  choices,
  isDisabled = false,
}) => {
  const menuItems = useMemo(
    () =>
      choices.map((c) => (
        <MenuItem key={c.value} value={c.value}>
          {c.label}
        </MenuItem>
      )),
    [choices],
  );

  return (
    <StyledBox>
      <Controller
        name={`attrs.${attrId}.value.asSelect`}
        control={control}
        render={({ field, fieldState: { error } }) => {
          const currentValue =
            field.value && typeof field.value === "object"
              ? ((field.value as { value?: string }).value ?? "")
              : "";
          return (
            <FormControl fullWidth error={error != null} variant="standard">
              <Select
                value={currentValue}
                onChange={(e) => {
                  const v = e.target.value as string;
                  const found = choices.find((c) => c.value === v);
                  field.onChange(
                    found ? { value: found.value, label: found.label } : null,
                  );
                }}
                displayEmpty
                disabled={isDisabled}
              >
                <MenuItem value="">
                  <em>未選択</em>
                </MenuItem>
                {menuItems}
              </Select>
            </FormControl>
          );
        }}
      />
    </StyledBox>
  );
};

export const ArraySelectAttributeValueField: FC<CommonProps> = ({
  attrId,
  control,
  choices,
  isDisabled = false,
}) => {
  return (
    <StyledBox>
      <Controller
        name={`attrs.${attrId}.value.asArraySelect`}
        control={control}
        defaultValue={[]}
        render={({ field, fieldState: { error } }) => {
          const value = Array.isArray(field.value) ? field.value : [];
          const selectedValues = value.map((v) => v.value);
          // Surface entries that hold a value no longer in the schema's choices
          // — without this, choices.filter() drops them and a single user
          // interaction permanently deletes the data.
          const staleSelected = value.filter(
            (v) => !choices.some((c) => c.value === v.value),
          );
          const renderedValue = [
            ...choices.filter((c) => selectedValues.includes(c.value)),
            ...staleSelected,
          ];
          return (
            <Autocomplete
              multiple
              options={choices}
              getOptionLabel={(option) => option.label}
              isOptionEqualToValue={(opt, v) => opt.value === v.value}
              value={renderedValue}
              onChange={(_e, newValue) =>
                field.onChange(
                  newValue.map((c) => ({ value: c.value, label: c.label })),
                )
              }
              disabled={isDisabled}
              renderTags={(tagValue, getTagProps) =>
                tagValue.map((option, idx) => (
                  <Chip
                    label={option.label}
                    {...getTagProps({ index: idx })}
                    key={option.value}
                  />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="standard"
                  placeholder="選択肢を選んでください"
                  error={error != null}
                  helperText={error?.message}
                />
              )}
              fullWidth
            />
          );
        }}
      />
    </StyledBox>
  );
};
