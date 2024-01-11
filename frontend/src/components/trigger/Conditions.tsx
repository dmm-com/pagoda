import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { EntityDetail, TriggerCondition } from "@dmm-com/airone-apiclient-typescript-fetch";
import { MenuItem, Select, TableRow, TableCell, TextField } from "@mui/material";
import React, { FC } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";
import { Schema } from "./TriggerFormSchema";

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
}

interface PropsConditionValue {
  index: number,
  control: Control<Schema>,
  field: TriggerCondition,
  entity: EntityDetail;
}

interface PropsConditionValueComponent {
  index: number,
  control: Control<Schema>,
  field: TriggerCondition,
}

const ConditionValueAsString: FC<PropsConditionValueComponent> = ({
  index,
  control,
  field,
}) => {
  return (
    <Controller
      name={`conditions.${index}.strCond`}
      control={control}
      defaultValue={field.strCond}
      render={({ field }) => (
        <TextField {...field}
          variant="standard"
          fullWidth
        />
      )}
    />
  );
}

const ConditionValue: FC<PropsConditionValue> = ({
  index,
  control,
  field,
  entity,
}) => {
  // This is DEBUG code
  const attrType = EntryAttributeTypeTypeEnum.STRING // TODO: get proper entity attr from entity object
  switch (attrType) {
    case EntryAttributeTypeTypeEnum.STRING:
      return (
        <ConditionValueAsString
          index={index}
          control={control}
          field={field}
        />
      );

    /* 
    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <></>
      );

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return (
        <></>
      );
    */
  }
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

  console.log("[onix] entity: ", entity);

  return (
    <>
      {fields.map((field, index) => {
        return (
          <TableRow key={field.key}>
            <TableCell>
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
            </TableCell>
            <TableCell>
              <ConditionValue
                index={index}
                control={control}
                field={field}
                entity={entity}
              />
            </TableCell>
          </TableRow>
        );
      })}
    </>
  )

};