import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  TriggerCondition,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  IconButton,
  MenuItem,
  Select,
  TableCell,
  TableRow,
  TextField,
} from "@mui/material";
import React, { FC } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";

import { Schema } from "./TriggerFormSchema";

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
}

interface PropsConditionValue {
  index: number;
  control: Control<Schema>;
  field: TriggerCondition;
  entity: EntityDetail;
}

interface PropsConditionValueComponent {
  index: number;
  control: Control<Schema>;
  field: TriggerCondition;
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
        <TextField {...field} variant="standard" fullWidth />
      )}
    />
  );
};

const ConditionValue: FC<PropsConditionValue> = ({
  index,
  control,
  field,
  entity,
}) => {
  // This is DEBUG code
  const attrType = EntryAttributeTypeTypeEnum.STRING; // TODO: get proper entity attr from entity object
  switch (attrType) {
    case EntryAttributeTypeTypeEnum.STRING:
      return (
        <ConditionValueAsString index={index} control={control} field={field} />
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
};

export const Conditions: FC<Props> = ({ control, entity }) => {
  const { fields, insert, remove, swap } = useFieldArray({
    control,
    name: "conditions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  console.log("[onix] entity: ", entity);

  const handleAppendCondition = (index: number) => {
    insert(index, {
      id: 0,
      attr: {
        id: 0,
        name: "",
      },
      strCond: "",
      refCond: null,
      boolCond: undefined,
    });
  };

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
            <TableCell>
              {" "}
              <IconButton onClick={() => remove(index)}>
                <DeleteOutlineIcon />
              </IconButton>
            </TableCell>
            <TableCell>
              <IconButton onClick={() => handleAppendCondition(index + 1)}>
                <AddIcon />
              </IconButton>
            </TableCell>
          </TableRow>
        );
      })}
      {fields.length === 0 && (
        <TableRow>
          <TableCell />
          <TableCell />
          <TableCell />
          <TableCell>
            <IconButton onClick={() => handleAppendCondition(0)}>
              <AddIcon />
            </IconButton>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};
