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

import { useTranslation } from "hooks/useTranslation";
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

type GroupOption = { id: number; name: string };

export const GroupAttributeValueField: FC<Props> = ({
  attrId,
  control,
  setValue,
  multiple = false,
  isDisabled = false,
}) => {
  const { t } = useTranslation();
  const [inputValue, setInputValue] = useState("");

  const { data: options = [], isLoading: loading } = usePagodaSWR(
    ["groupOptions", inputValue],
    async () => {
      const result = await aironeApiClient.getGroups(1, inputValue);
      if ((result.results?.length ?? 0) === 0 && inputValue) {
        return (
          (await aironeApiClient.getGroups(1)).results?.map((g) => ({
            id: g.id,
            name: g.name,
          })) ?? []
        );
      }
      return result.results?.map((g) => ({ id: g.id, name: g.name })) ?? [];
    },
    // revalidateOnFocus is disabled so a transient failure of a background
    // refetch cannot crash the entry form the user is editing.
    { keepPreviousData: true, revalidateOnFocus: false },
  );

  const handleChange = (value: GroupOption | GroupOption[] | null) => {
    if (!multiple && value != null && !Array.isArray(value)) {
      setInputValue(value.name);
    } else if (multiple) {
      setInputValue("");
    }
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
      <StyledTypography variant="caption">
        {t("entryForm.groupField.selectGroup")}
      </StyledTypography>
      <StyledBox>
        <Controller
          name={
            multiple
              ? `attrs.${attrId}.value.asArrayGroup`
              : `attrs.${attrId}.value.asGroup`
          }
          control={control}
          render={({ field, fieldState: { error, isDirty } }) => (
            <Autocomplete<GroupOption, boolean, false, false>
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
