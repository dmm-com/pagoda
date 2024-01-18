import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  TriggerAction,
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
import { Control, Controller, useFieldArray, UseFieldArrayInsert } from "react-hook-form";

import { Schema } from "./TriggerFormSchema";

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
}

interface PropsActionValue {
  index: number;
  control: Control<Schema>;
  entity: EntityDetail;
  field: TriggerAction;
}

interface PropsActionValueComponent {
  // The 'indexAction' indicatates what number of action column
  indexAction: number;
  // The 'indexActionInput' indicatates what number of input form in the action column
  indexActionInput: number;
  control: Control<Schema>;
  field: TriggerAction;
  insert: any;
}

const ActionValueAsString: FC<PropsActionValueComponent> = ({
  indexAction,
  indexActionInput,
  control,
  field,
  insert
}) => {

  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionInput}.strCond`}
      control={control}
      render={({ field }) => (
        <TextField {...field} variant="standard" fullWidth
        />
      )}
    />
  );
};

const ActionValue: FC<PropsActionValue> = ({
  index,
  control,
  field,
  entity,
}) => {
  /* to manupirate values in actions this useFieldArray() is necessary,
     but, this must be declared in the proper scope */

  const { fields, insert, remove, swap } = useFieldArray({
    control,
    name: `actions.${index}.values`,
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  // debug processing
  insert(0, {
    id: 0,
    strCond: "",
    refCond: null,
  });

  // This is DEBUG code
  const attrType = EntryAttributeTypeTypeEnum.STRING; // TODO: get proper entity attr from entity object
  switch (attrType) {
    case EntryAttributeTypeTypeEnum.STRING:
      return (
        <ActionValueAsString indexAction={index} indexActionInput={0} control={control} field={field} insert={insert} />
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

export const ActionForm: FC<Props> = ({ control, entity }) => {
  const { fields, insert, remove, swap } = useFieldArray({
    control,
    name: "actions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const handleAppendAction = (index: number) => {
    insert(index + 1, {
      id: 0,
      attr: {
        id: 0,
        name: "",
      },
      values: [{
        id: 0,
        strCond: "",
        refCond: null,
        boolCond: false,
      }]
    })
  };

  return (
    <>
      {fields.map((field, index) => {
        return (
          <TableRow key={field.key}>
            <TableCell>
              <Controller
                name={`actions.${index}.attr.id`}
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
              {/** This raise an exception
              <ActionValue
                index={index}
                control={control}
                field={field}
                entity={entity}
              />
              */}
            </TableCell>
            <TableCell>
              {" "}
              <IconButton onClick={() => remove(index)}>
                <DeleteOutlineIcon />
              </IconButton>
            </TableCell>
            <TableCell>
              <IconButton onClick={() => handleAppendAction(index + 1)}>
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
            <IconButton onClick={() => handleAppendAction(0)}>
              <AddIcon />
            </IconButton>
          </TableCell>
        </TableRow>
      )}
    </>
  );
};
