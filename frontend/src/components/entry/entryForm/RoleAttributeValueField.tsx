import { Autocomplete, Box, TextField, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { useAsyncWithThrow } from "../../../hooks/useAsyncWithThrow";
import { aironeApiClient } from "../../../repository/AironeApiClient";

import { Schema } from "./EntryFormSchema";

const StyledTypography = styled(Typography)(({}) => ({
  color: "rgba(0, 0, 0, 0.6)",
}));

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  alignItems: "center",
}));

interface Props {
  attrId: number;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  multiple?: boolean;
  isDisabled?: boolean;
}

export const RoleAttributeValueField: FC<Props> = ({
  multiple,
  attrId,
  control,
  setValue,
  isDisabled = false,
}) => {
  const roles = useAsyncWithThrow(async () => {
    const _roles = await aironeApiClient.getRoles();
    return _roles.map((g) => ({ id: g.id, name: g.name }));
  }, []);

  const handleChange = (
    value: { id: number; name: string } | { id: number; name: string }[] | null
  ) => {
    if (multiple === true) {
      if (value != null && !Array.isArray(value)) {
        throw new Error("value must be an array");
      }
      setValue(`attrs.${attrId}.value.asArrayRole`, value ?? [], {
        shouldDirty: true,
        shouldValidate: true,
      });
    } else {
      if (value != null && Array.isArray(value)) {
        throw new Error("value must not be an array");
      }
      setValue(`attrs.${attrId}.value.asRole`, value, {
        shouldDirty: true,
        shouldValidate: true,
      });
    }
  };

  return (
    <Box>
      <StyledTypography variant="caption">ロールを選択</StyledTypography>
      <StyledBox>
        <Controller
          name={
            multiple === true
              ? `attrs.${attrId}.value.asArrayRole`
              : `attrs.${attrId}.value.asRole`
          }
          control={control}
          render={({ field, fieldState: { error } }) => (
            <Autocomplete
              fullWidth
              multiple={multiple}
              loading={roles.loading}
              options={roles.value ?? []}
              value={field.value}
              getOptionLabel={(option: { id: number; name: string }) =>
                option.name
              }
              isOptionEqualToValue={(option, value) => option.id === value.id}
              onChange={(_e, value) => handleChange(value)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  error={error != null}
                  helperText={error?.message}
                  size="small"
                  placeholder={multiple ? "" : "-NOT SET-"}
                  disabled={isDisabled}
                />
              )}
              disabled={isDisabled}
            />
          )}
        />
      </StyledBox>
    </Box>
  );
};
