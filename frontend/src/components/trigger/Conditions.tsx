import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import { MenuItem, Select, TableRow } from "@mui/material";
import React, { FC } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";
import { Schema } from "./TriggerFormSchema";

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
}

export const Conditions: FC<Props> = ({
  control,
  entity,
}) => {

  const { fields, insert, remove, swap } = useFieldArray({
    control,
    name: "conditions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  return (
    <>
      {fields.map((field, index) => {
        return (
          <TableRow key={field.key}>
            <Controller
              name={`conditions.${index}.attr.id`}
              control={control}
              defaultValue={field.attr.id}
              render={({ field }) => (
                <Select {...field} size="small" fullWidth>
                  {entity.attrs.map((attr) => (
                    <MenuItem key={attr.id} value={attr.id}>
                      {attr.name}
                    </MenuItem>
                  ))}
                </Select>
              )}
            />
          </TableRow>
        );
      })}
    </>
  )

};