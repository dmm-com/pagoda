import {
  Autocomplete,
  Box,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useEffect, useState } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { aironeApiClient } from "../../../repository/AironeApiClient";

import { Schema } from "./EntryFormSchema";

import { getStagedErrorStyle } from "utils/styleUtils";

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

type RoleOption = { id: number; name: string };

export const RoleAttributeValueField: FC<Props> = ({
  multiple = false,
  attrId,
  control,
  setValue,
  isDisabled = false,
}) => {
  const [options, setOptions] = useState<RoleOption[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchRoles = async () => {
      setLoading(true);
      try {
        const roles = await aironeApiClient.getRoles(inputValue);
        setOptions(roles.map((r) => ({ id: r.id, name: r.name })));
      } finally {
        setLoading(false);
      }
    };
    fetchRoles();
  }, [inputValue]);

  const handleChange = (value: RoleOption | RoleOption[] | null) => {
    if (multiple) {
      setValue(
        `attrs.${attrId}.value.asArrayRole`,
        (value as RoleOption[]) ?? [],
        {
          shouldDirty: true,
          shouldValidate: true,
        },
      );
    } else {
      setValue(`attrs.${attrId}.value.asRole`, (value as RoleOption) ?? null, {
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
            multiple
              ? `attrs.${attrId}.value.asArrayRole`
              : `attrs.${attrId}.value.asRole`
          }
          control={control}
          render={({ field, fieldState: { error, isDirty } }) => (
            <Autocomplete<RoleOption, boolean>
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
                  sx={getStagedErrorStyle(!!error, isDirty)}
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
