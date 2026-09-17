import {
  Autocomplete,
  Box,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useState } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form";

import { usePagodaSWR } from "../../../hooks/usePagodaSWR";
import { aironeApiClient } from "../../../repository/AironeApiClient";

import { Schema } from "./EntryFormSchema";

import { fuzzyMatch } from "services/StringUtil";
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
  const [inputValue, setInputValue] = useState("");

  const { data: options = [], isLoading: loading } = usePagodaSWR(
    ["roleOptions", inputValue],
    async () => {
      const roles = await aironeApiClient.getRoles(inputValue);
      if (roles.length === 0 && inputValue) {
        return (await aironeApiClient.getRoles()).map((r) => ({
          id: r.id,
          name: r.name,
        }));
      }
      return roles.map((r) => ({ id: r.id, name: r.name }));
    },
    // revalidateOnFocus is disabled so a transient failure of a background
    // refetch cannot crash the entry form the user is editing.
    { keepPreviousData: true, revalidateOnFocus: false },
  );

  const handleChange = (value: RoleOption | RoleOption[] | null) => {
    if (!multiple && value != null && !Array.isArray(value)) {
      setInputValue(value.name);
    } else if (multiple) {
      setInputValue("");
    }
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
              selectOnFocus
              clearOnBlur={false}
              loading={loading}
              options={options}
              filterOptions={(options, state) =>
                options.filter((option) =>
                  fuzzyMatch(option.name, state.inputValue),
                )
              }
              value={field.value ?? (multiple ? [] : null)}
              inputValue={
                inputValue ||
                (!multiple && field.value != null && !Array.isArray(field.value)
                  ? field.value.name
                  : "")
              }
              getOptionLabel={(option) => option.name}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              onChange={(_, value) => handleChange(value)}
              onInputChange={(_, value, reason) => {
                if (reason === "input" || reason === "clear") {
                  setInputValue(value);
                }
              }}
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
