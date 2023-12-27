import { Autocomplete, Box, TextField, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../../../repository/AironeApiClientV2";

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
}

export const GroupAttributeValueField: FC<Props> = ({
  multiple,
  attrId,
  control,
  setValue,
}) => {
  const groups = useAsync(async () => {
    const _groups = await aironeApiClientV2.getGroups();
    return _groups.results?.map((g) => ({ id: g.id, name: g.name }));
  }, []);

  const handleChange = (
    value: { id: number; name: string } | { id: number; name: string }[] | null,
  ) => {
    if (multiple === true) {
      if (value != null && !Array.isArray(value)) {
        throw new Error("value must be an array");
      }
      setValue(`attrs.${attrId}.value.asArrayGroup`, value ?? [], {
        shouldDirty: true,
        shouldValidate: true,
      });
    } else {
      if (value != null && Array.isArray(value)) {
        throw new Error("value must not be an array");
      }
      setValue(`attrs.${attrId}.value.asGroup`, value, {
        shouldDirty: true,
        shouldValidate: true,
      });
    }
  };

  return (
    <Box>
      <StyledTypography variant="caption">グループを選択</StyledTypography>
      <StyledBox>
        <Controller
          name={
            multiple === true
              ? `attrs.${attrId}.value.asArrayGroup`
              : `attrs.${attrId}.value.asGroup`
          }
          control={control}
          render={({ field, fieldState: { error } }) => (
            <Autocomplete
              fullWidth
              multiple={multiple}
              loading={groups.loading}
              options={groups.value ?? []}
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
                />
              )}
            />
          )}
        />
      </StyledBox>
    </Box>
  );
};
