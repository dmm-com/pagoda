import { Box, Typography } from "@mui/material";
import React, { FC } from "react";
import { Control, Controller } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../../../apiclient/AironeApiClientV2";

import { Schema } from "./EntryFormSchema";
import { ReferralLikeAutocomplete } from "./ReferralLikeAutocomplete";

interface Props {
  attrName: string;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  multiple?: boolean;
}

export const RoleAttributeValueField: FC<Props> = ({
  multiple,
  attrName,
  control,
  setValue,
}) => {
  const roles = useAsync(async () => {
    const _roles = await aironeApiClientV2.getRoles();
    return _roles.map((g) => ({ id: g.id, name: g.name }));
  }, []);

  const handleChange = (
    value: { id: number; name: string } | { id: number; name: string }[] | null
  ) => {
    if (multiple === true) {
      if (value != null && !Array.isArray(value)) {
        throw new Error("value must be an array");
      }
      setValue(`attrs.${attrName}.value.asArrayRole`, value ?? [], {
        shouldDirty: true,
        shouldValidate: true,
      });
    } else {
      if (value != null && Array.isArray(value)) {
        throw new Error("value must not be an array");
      }
      setValue(`attrs.${attrName}.value.asRole`, value, {
        shouldDirty: true,
        shouldValidate: true,
      });
    }
  };

  return (
    <Box>
      <Typography variant="caption" color="rgba(0, 0, 0, 0.6)">
        ロールを選択
      </Typography>
      <Box display="flex" alignItems="center">
        <Controller
          name={
            multiple === true
              ? `attrs.${attrName}.value.asArrayRole`
              : `attrs.${attrName}.value.asRole`
          }
          control={control}
          render={({ field, fieldState: { error } }) => (
            <ReferralLikeAutocomplete
              multiple={multiple}
              options={roles.value ?? []}
              value={field.value ?? null}
              handleChange={handleChange}
            />
          )}
        />
      </Box>
    </Box>
  );
};
