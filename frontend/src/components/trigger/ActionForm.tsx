import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  TriggerAction,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import CancelIcon from '@mui/icons-material/Cancel';
import AddIcon from "@mui/icons-material/Add";
import AddCircleIcon from '@mui/icons-material/AddCircle';
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  IconButton,
  MenuItem,
  Select,
  TableCell,
  TableRow,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller, useFieldArray, UseFieldArrayInsert } from "react-hook-form";

import { Schema } from "./TriggerFormSchema";

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
  resetActionValues: (index: number) => void;
}

interface PropsActionValue {
  indexAction: number;
  control: Control<Schema>;
  entity: EntityDetail;
  actionField: TriggerAction;
}

interface PropsActionValueComponent {
  // The 'indexAction' indicatates what number of action column
  indexAction: number;
  // The 'indexActionValue' indicatates what number of input form in the action column
  indexActionValue: number;
  control: Control<Schema>;
}

interface PropsActionValueComponentWithEntity extends PropsActionValueComponent {
  entity: EntityDetail;
  actionField: TriggerAction;
  handleAddInputValue: (index: number) => void;
  handleDelInputValue: (index: number) => void;
}

const StyledBox = styled(Box)(({ }) => ({
  display: "flex",
  width: "100%",
  gap: "0 12px",
}));

const ActionValueAsString: FC<PropsActionValueComponent> = ({
  indexAction,
  indexActionValue,
  control,
}) => {
  console.log("[onix/ActionValueAsString(01)] indexActionValue: ", indexActionValue);

  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionValue}.strCond`}
      defaultValue=""
      control={control}
      render={({ field }) => (
        <TextField {...field} variant="standard" fullWidth
        />
      )}
    />
  );
};

const ActionValueInputForm: FC<PropsActionValueComponentWithEntity> = ({
  indexAction,
  indexActionValue,
  control,
  actionField,
  entity,
  handleAddInputValue,
  handleDelInputValue,
}) => {

  const attrInfo = entity.attrs.find((attr) => attr.id === actionField.attr.id);
  switch (attrInfo?.type) {
    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.TEXT:
      return (
        <ActionValueAsString
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return (
        <StyledBox>
          <>
            <ActionValueAsString
              indexAction={indexAction}
              indexActionValue={indexActionValue}
              control={control}
            />
          </>
          <IconButton onClick={() => handleDelInputValue(indexActionValue)}>
            <CancelIcon />
          </IconButton>
          <IconButton onClick={() => handleAddInputValue(indexActionValue)}>
            <AddCircleIcon />
          </IconButton>
        </StyledBox>
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

const ActionValue: FC<PropsActionValue> = ({
  indexAction,
  control,
  actionField,
  entity,
}) => {
  const { fields, insert, remove, swap } = useFieldArray({
    control,
    name: `actions.${indexAction}.values`,
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const handleAddActionValue = (index: number) => {
    console.log("[onix/handleAddActionValue(01)] index: ", index);
    insert(index + 1, {
      id: 0,
      strCond: "",
      refCond: null,
      boolCond: undefined,
    });
  }
  const handleDelActionValue = (index: number) => {
    console.log("[onix/handleDelActionValue(01)] index: ", index);
    remove(index);

    fields.length === 1 && handleAddActionValue(0);
  }

  return (
    <>
      {fields.map((actionValueField, indexActionValue) => {
        return (
          <ActionValueInputForm
            indexAction={indexAction}
            indexActionValue={indexActionValue}
            control={control}
            actionField={actionField}
            entity={entity}
            handleAddInputValue={handleAddActionValue}
            handleDelInputValue={handleDelActionValue}
          />
        );
      })}
    </>
  );
};

export const ActionForm: FC<Props> = ({
  control,
  entity,
  resetActionValues,
}) => {
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
        boolCond: undefined,
      }]
    })
  };

  return (
    <>
      {fields.map((actionField, index) => {
        return (
          <Controller key={actionField.key}
            name={`actions.${index}.attr.id`}
            control={control}
            defaultValue={actionField.attr.id}
            render={({ field }) => (
              <TableRow>
                <TableCell>
                  <Select {...field}
                    size="small"
                    fullWidth
                    onChange={(e) => {
                      field.onChange(e);

                      // clear all action values when attribute is changed
                      resetActionValues(index);
                    }}
                  >
                    {entity.attrs.map((attr) => (
                      <MenuItem key={attr.id} value={attr.id}>
                        {attr.name}
                      </MenuItem>
                    ))}
                  </Select>
                </TableCell>
                <TableCell>
                  <ActionValue
                    indexAction={index}
                    control={control}
                    actionField={actionField}
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
                  <IconButton onClick={() => handleAppendAction(index + 1)}>
                    <AddIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            )}
          />
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
