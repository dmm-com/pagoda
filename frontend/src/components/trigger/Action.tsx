import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  GetEntryAttrReferral,
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
import { Control, Controller, useFieldArray, useWatch } from "react-hook-form";

import { Schema } from "./TriggerFormSchema";

import { ReferralsAutocomplete } from "components/entry/entryForm/ReferralsAutocomplete";
import { isSupportedType } from "services/trigger/Edit";

interface Props {
  index: number;
  control: Control<Schema>;
  remove: (index: number) => void;
  handleAppendAction: (index: number) => void;
  entity: EntityDetail;
}

interface PropsActionValue {
  indexAction: number;
  control: Control<Schema>;
  entity: EntityDetail;
  attrId: number;
}

interface PropsActionValueComponent {
  // The 'indexAction' indicatates what number of action column
  indexAction: number;
  // The 'indexActionValue' indicatates what number of input form in the action column
  indexActionValue: number;
  control: Control<Schema>;
}

interface PropsActionValueObjectValueComponent
  extends PropsActionValueComponent {
  attrId: number;
}

interface PropsActionValueInputForm
  extends PropsActionValueObjectValueComponent {
  entity: EntityDetail;
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
}) => {
  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionValue}.strCond`}
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
}) => {
  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionValue}.boolCond`}
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

const ActionValueAsObject: FC<PropsActionValueObjectValueComponent> = ({
  indexAction,
  indexActionValue,
  control,
  attrId,
}) => {
  return (
    <Controller
      name={`actions.${indexAction}.values.${indexActionValue}.refCond`}
      control={control}
      render={({ field }) => (
        <ReferralsAutocomplete
          attrId={attrId}
          value={field.value}
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

const ActionValueAsName: FC<PropsActionValueObjectValueComponent> = ({
  indexAction,
  indexActionValue,
  control,
  attrId,
}) => {
  return (
    <NamedObjectBox>
      <FlexBox>
        <NameBox>
          <Controller
            name={`actions.${indexAction}.values.${indexActionValue}.strCond`}
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
          render={({ field }) => (
            <ReferralsAutocomplete
              attrId={attrId}
              value={field.value}
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

const ActionValueInputForm: FC<PropsActionValueInputForm> = ({
  indexAction,
  indexActionValue,
  control,
  entity,
  attrId,
  handleAddInputValue,
  handleDelInputValue,
}) => {
  const attrInfo = entity.attrs.find((attr) => attr.id === attrId);
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
          <ActionValueAsString
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
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <ActionValueAsObject
          attrId={attrId}
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <ActionValueAsName
          attrId={attrId}
          indexAction={indexAction}
          indexActionValue={indexActionValue}
          control={control}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
      return (
        <StyledBox>
          <ActionValueAsObject
            attrId={attrId}
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
              attrId={attrId}
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
  entity,
  attrId,
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
              entity={entity}
              attrId={attrId}
              handleAddInputValue={handleAddActionValue}
              handleDelInputValue={handleDelActionValue}
            />
          </StyledListItem>
        );
      })}
    </StyledList>
  );
};

export const Action: FC<Props> = ({
  index,
  control,
  remove,
  handleAppendAction,
  entity,
}) => {
  const attrId = useWatch({
    control,
    name: `actions.${index}.attr.id`,
  });
  return (
    <TableRow>
      <TableCell>
        <Controller
          name={`actions.${index}.attr.id`}
          control={control}
          render={({ field }) => (
            <Select {...field} size="small" fullWidth>
              <MenuItem key={0} value={0} disabled hidden />
              {entity.attrs
                .filter((attr) => isSupportedType(attr))
                .map((attr) => (
                  <MenuItem key={attr.id} value={attr.id}>
                    {attr.name}
                  </MenuItem>
                ))}
            </Select>
          )}
        />
      </TableCell>
      <TableCell>
        <ActionValue
          indexAction={index}
          control={control}
          attrId={attrId}
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
        <IconButton onClick={() => handleAppendAction(index)}>
          <AddIcon />
        </IconButton>
      </TableCell>
    </TableRow>
  );
};
