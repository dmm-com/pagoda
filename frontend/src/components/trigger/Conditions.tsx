import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  GetEntryAttrReferral,
  TriggerCondition,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Checkbox,
  IconButton,
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

interface Props {
  control: Control<Schema>;
  entity: EntityDetail;
}

interface PropsConditionValueComponent {
  index: number;
  control: Control<Schema>;
  condField: TriggerCondition;
}

interface PropsConditionValuePlusEntity extends PropsConditionValueComponent {
  entity: EntityDetail;
}

const ConditionValueAsString: FC<PropsConditionValueComponent> = ({
  index,
  control,
  condField,
}) => {
  return (
    <Controller
      name={`conditions.${index}.strCond`}
      control={control}
      defaultValue={condField.strCond ?? ""}
      render={({ field }) => (
        <TextField {...field} variant="standard" fullWidth />
      )}
    />
  );
};

const ConditionValueAsBoolean: FC<PropsConditionValueComponent> = ({
  index,
  control,
  condField,
}) => {
  return (
    <Controller
      name={`conditions.${index}.boolCond`}
      control={control}
      defaultValue={condField.boolCond}
      render={({ field }) => (
        <Checkbox
          checked={field.value}
          onChange={(e) => field.onChange(e.target.checked)}
        />
      )}
    />
  );
};

const ConditionValueAsObject: FC<PropsConditionValueComponent> = ({
  index,
  control,
  condField,
}) => {
  return (
    <Controller
      name={`conditions.${index}.refCond`}
      control={control}
      defaultValue={condField.refCond}
      render={({ field }) => (
        <ReferralsAutocomplete
          attrId={condField.attr.id}
          value={condField.refCond}
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

const ConditionValueAsName: FC<PropsConditionValueComponent> = ({
  index,
  control,
  condField,
}) => {
  return (
    <NamedObjectBox>
      <FlexBox>
        <NameBox>
          <Controller
            name={`conditions.${index}.strCond`}
            control={control}
            defaultValue={condField.strCond ?? ""}
            render={({ field }) => (
              <TextField {...field} variant="standard" fullWidth />
            )}
          />
        </NameBox>
      </FlexBox>

      <Box flexGrow={1}>
        <Controller
          name={`conditions.${index}.refCond`}
          control={control}
          defaultValue={condField.refCond}
          render={({ field }) => (
            <ReferralsAutocomplete
              attrId={condField.attr.id}
              value={condField.refCond}
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

const ConditionValue: FC<PropsConditionValuePlusEntity> = ({
  index,
  control,
  condField,
  entity,
}) => {
  const attrInfo = entity.attrs.find((attr) => attr.id === condField.attr.id);
  switch (attrInfo?.type) {
    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return (
        <ConditionValueAsString
          index={index}
          control={control}
          condField={condField}
        />
      );

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return (
        <ConditionValueAsBoolean
          index={index}
          control={control}
          condField={condField}
        />
      );

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <ConditionValueAsObject
          index={index}
          control={control}
          condField={condField}
        />
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
      return (
        <ConditionValueAsName
          index={index}
          control={control}
          condField={condField}
        />
      );
  }
};

export const Conditions: FC<Props> = ({ control, entity }) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: "conditions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const handleAppendCondition = (index: number) => {
    insert(index, {
      id: 0,
      attr: {
        id: 0,
        name: "",
        type: 0,
      },
      strCond: "",
      refCond: null,
      boolCond: undefined,
    });
  };

  return (
    <>
      {fields.map((condField, index) => {
        return (
          <TableRow key={condField.key}>
            <TableCell>
              <Controller
                name={`conditions.${index}.attr.id`}
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
              <ConditionValue
                index={index}
                control={control}
                condField={condField}
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
