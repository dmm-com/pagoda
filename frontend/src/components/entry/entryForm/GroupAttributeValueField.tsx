import {
  Autocomplete,
  Box,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useEffect, useState } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { aironeApiClient } from "../../../repository/AironeApiClient";

import { Schema } from "./EntryFormSchema";

const StyledTypography = styled(Typography)(() => ({
  color: "rgba(0, 0, 0, 0.6)",
}));

const StyledBox = styled(Box)(() => ({
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

type GroupOption = { id: number; name: string };

export const GroupAttributeValueField: FC<Props> = ({
  attrId,
  control,
  setValue,
  multiple = false,
  isDisabled = false,
}) => {
  const [options, setOptions] = useState<GroupOption[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchGroups = async () => {
      setLoading(true);
      try {
        const result = await aironeApiClient.getGroups(1, inputValue);
        setOptions(
          result.results?.map((g) => ({ id: g.id, name: g.name })) ?? [],
        );
      } finally {
        setLoading(false);
      }
    };

    fetchGroups();
  }, [inputValue]);

  const handleChange = (value: GroupOption | GroupOption[] | null) => {
    if (multiple) {
      setValue(
        `attrs.${attrId}.value.asArrayGroup`,
        (value as GroupOption[]) ?? [],
        {
          shouldDirty: true,
          shouldValidate: true,
        },
      );
    } else {
      setValue(
        `attrs.${attrId}.value.asGroup`,
        (value as GroupOption) ?? null,
        {
          shouldDirty: true,
          shouldValidate: true,
        },
      );
    }
  };

  return (
    <Box>
      <StyledTypography variant="caption">グループを選択</StyledTypography>
      <StyledBox>
        <Controller
          name={
            multiple
              ? `attrs.${attrId}.value.asArrayGroup`
              : `attrs.${attrId}.value.asGroup`
          }
          control={control}
          render={({ field, fieldState: { error } }) => (
            <Autocomplete<GroupOption, boolean, false, false>
              fullWidth
              multiple={multiple}
              loading={loading}
              options={options}
              value={field.value ?? (multiple ? [] : null)}
              getOptionLabel={(option) => option.name}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              onChange={(_, value) => handleChange(value)}
              onInputChange={(_, value) => setInputValue(value)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  error={!!error}
                  helperText={error?.message}
                  size="small"
                  placeholder={multiple ? "" : "-NOT SET-"}
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {loading ? <CircularProgress size={20} /> : null}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  }}
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
