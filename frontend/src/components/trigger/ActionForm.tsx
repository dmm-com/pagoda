import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  GetEntryAttrReferral,
  TriggerAction,
  TriggerActionValue,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Checkbox,
  IconButton,
  List,
  ListItem,
  MenuItem,
  Select,
  TableCell,
  TableRow,
  TextField,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";

import { Schema } from "./TriggerFormSchema";

import { ReferralsAutocomplete } from "components/entry/entryForm/ReferralsAutocomplete";
import { isSupportedType } from "services/trigger/Edit";

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
  actionValue: TriggerActionValue;
}

interface PropsActionValueComponentWithAttrId
  extends PropsActionValueComponent {
  attrId: number;
}

interface PropsActionValueComponentWithEntity
  extends PropsActionValueComponent {
  entity: EntityDetail;
  actionField: TriggerAction;
  handleAddInputValue: (index: number) => void;
  handleDelInputValue: (index: number) => void;
}

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  width: "100%",
  gap: "0 12px",
}));

const NamedObjectBox = styled(Box)(({}) => ({
  display: "flex",
  alignItems: "flex-end",
  gap: "0 12px",
  width: "100%",
}));
const FlexBox = styled(Box)(({}) => ({
  display: "flex",
  flexDirection: "column",
}));
const NameBox = styled(Box)(({}) => ({
  width: "150px",
}));
const StyledList = styled(List)(({}) => ({
  padding: "0",
}));

const StyledListItem = styled(ListItem)(({}) => ({
  padding: "0",
}));

const ActionValueAsString: FC<PropsActionValueComponent> = ({
  indexAction,
  indexActionValue,
  control,
  actionValue,
}) => {
  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionValue}.strCond`}
      defaultValue={actionValue.strCond ?? ""}
      control={control}
      render={({ field }) => {
        return <TextField {...field} variant="standard" fullWidth />;
      }}
    />
  );
};

const ActionValueAsBoolean: FC<PropsActionValueComponent> = ({
  indexAction,
  indexActionValue,
  control,
  actionValue,
}) => {
  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionValue}.boolCond`}
      defaultValue={actionValue.boolCond}
      control={control}
      render={({ field }) => (
        <Checkbox
          checked={field.value}
          onChange={(e) => field.onChange(e.target.checked)}
        />
      )}
    />
  );
};

const ActionValueAsObject: FC<PropsActionValueComponentWithAttrId> = ({
  indexAction,
  indexActionValue,
  control,
  actionValue,
  attrId,
}) => {
  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionValue}.refCond`}
      control={control}
      defaultValue={actionValue.refCond}
      render={({ field }) => (
        <ReferralsAutocomplete
          attrId={attrId}
          value={actionValue.refCond}
          handleChange={(v) => {
            field.onChange({
              id: (v as GetEntryAttrReferral).id,
              name: (v as GetEntryAttrReferral).name,
              schema: {
                id: 0,
                name: "",
              },
            });
          }}
          multiple={false}
        />
      )}
    />
  );
};

const ActionValueAsName: FC<PropsActionValueComponentWithAttrId> = ({
  indexAction,
  indexActionValue,
  control,
  actionValue,
  attrId,
}) => {
  return (
    <NamedObjectBox>
      <FlexBox>
        <NameBox>
          <Controller
            name={`actions.${indexAction}.values.${indexActionValue}.strCond`}
            defaultValue={actionValue.strCond ?? ""}
            control={control}
            render={({ field }) => {
              return <TextField {...field} variant="standard" fullWidth />;
            }}
          />
        </NameBox>
      </FlexBox>
      <Box flexGrow={1}>
        <Controller
          name={`actions.${indexAction}.values.${indexActionValue}.refCond`}
          control={control}
          defaultValue={actionValue.refCond}
          render={({ field }) => (
            <ReferralsAutocomplete
              attrId={attrId}
              value={actionValue.refCond}
              handleChange={(v) => {
                field.onChange({
                  id: (v as GetEntryAttrReferral).id,
                  name: (v as GetEntryAttrReferral).name,
                  schema: {
                    id: 0,
                    name: "",
                  },
                });
              }}
              multiple={false}
            />
          )}
        />
      </Box>
    </NamedObjectBox>
  );
};

const ActionValueInputForm: FC<PropsActionValueComponentWithEntity> = ({
  indexAction,
  indexActionValue,
  control,
  actionField,
  actionValue,
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
          actionValue={actionValue}
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return (
        <StyledBox>
          <ActionValueAsString
            actionValue={actionValue}
            indexAction={indexAction}
            indexActionValue={indexActionValue}
            control={control}
          />
          <IconButton onClick={() => handleDelInputValue(indexActionValue)}>
            <CancelIcon />
          </IconButton>
          <IconButton onClick={() => handleAddInputValue(indexActionValue)}>
            <AddCircleIcon />
          </IconButton>
        </StyledBox>
      );

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return (
        <ActionValueAsBoolean
          actionValue={actionValue}
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <ActionValueAsObject
          attrId={actionField.attr.id}
          actionValue={actionValue}
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <ActionValueAsName
          attrId={actionField.attr.id}
          actionValue={actionValue}
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      return (
        <StyledBox>
          <ActionValueAsObject
            attrId={actionField.attr.id}
            actionValue={actionValue}
            indexAction={indexAction}
            indexActionValue={indexActionValue}
            control={control}
          />
          <IconButton onClick={() => handleDelInputValue(indexActionValue)}>
            <CancelIcon />
          </IconButton>
          <IconButton onClick={() => handleAddInputValue(indexActionValue)}>
            <AddCircleIcon />
          </IconButton>
        </StyledBox>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
      return (
        <StyledBox>
          <>
            <ActionValueAsName
              attrId={actionField.attr.id}
              actionValue={actionValue}
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
  }
};

const ActionValue: FC<PropsActionValue> = ({
  indexAction,
  control,
  actionField,
  entity,
}) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: `actions.${indexAction}.values`,
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const handleAddActionValue = (index: number) => {
    insert(index + 1, {
      id: 0,
      strCond: "",
      refCond: null,
    });
  };
  const handleDelActionValue = (index: number) => {
    remove(index);

    fields.length === 1 && handleAddActionValue(0);
  };

  return (
    <StyledList>
      {fields.map((actionValueField, indexActionValue) => {
        return (
          <StyledListItem key={actionValueField.key}>
            <ActionValueInputForm
              indexAction={indexAction}
              indexActionValue={indexActionValue}
              control={control}
              actionField={actionField}
              actionValue={actionValueField}
              entity={entity}
              handleAddInputValue={handleAddActionValue}
              handleDelInputValue={handleDelActionValue}
            />
          </StyledListItem>
        );
      })}
    </StyledList>
  );
};

export const ActionForm: FC<Props> = ({
  control,
  entity,
  resetActionValues,
}) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: "actions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const handleAppendAction = (index: number) => {
    insert(index, {
      id: 0,
      attr: {
        id: 0,
        name: "",
        type: 0,
      },
      values: [
        {
          id: 0,
          strCond: "",
          refCond: null,
          boolCond: undefined,
        },
      ],
    });
  };

  return (
    <>
      {fields.map((actionField, index) => (
        <TableRow key={actionField.key}>
          <Controller
            name={`actions.${index}.attr.id`}
            control={control}
            defaultValue={actionField.attr.id}
            render={({ field }) => (
              <>
                <TableCell>
                  <Select
                    {...field}
                    size="small"
                    fullWidth
                    onChange={(e) => {
                      field.onChange(e);

                      // clear all action values when attribute is changed
                      resetActionValues(index);
                    }}
                  >
                    <MenuItem key={0} value={0} disabled hidden />
                    {entity.attrs
                      .filter((attr) => isSupportedType(attr))
                      .map((attr) => (
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
              </>
            )}
          />
          <TableCell>
            {" "}
            <IconButton onClick={() => remove(index)}>
              <DeleteOutlineIcon />
            </IconButton>
          </TableCell>
          <TableCell>
            <IconButton onClick={() => handleAppendAction(index)}>
              <AddIcon />
            </IconButton>
          </TableCell>
        </TableRow>
      ))}
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
