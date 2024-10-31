import {
  EntityDetail,
  EntryAttributeTypeTypeEnum,
  GetEntryAttrReferral,
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
import { Control, Controller, useWatch } from "react-hook-form";

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
  index: number;
  control: Control<Schema>;
  remove: (index: number) => void;
  handleAppendCondition: (index: number) => void;
  entity: EntityDetail;
}

interface PropsConditionValueComponent {
  index: number;
  control: Control<Schema>;
}

interface PropsConditionObjectValueComponent
  extends PropsConditionValueComponent {
  attrId: number;
}

interface PropsConditionValue extends PropsConditionObjectValueComponent {
  entity: EntityDetail;
}

const ConditionValueAsString: FC<PropsConditionValueComponent> = ({
  index,
  control,
}) => {
  return (
    <Controller
      name={`conditions.${index}.strCond`}
      control={control}
      render={({ field }) => (
        <TextField {...field} variant="standard" fullWidth />
      )}
    />
  );
};

const ConditionValueAsBoolean: FC<PropsConditionValueComponent> = ({
  index,
  control,
}) => {
  return (
    <Controller
      name={`conditions.${index}.boolCond`}
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

const ConditionValueAsObject: FC<PropsConditionObjectValueComponent> = ({
  index,
  control,
  attrId,
}) => {
  return (
    <Controller
      name={`conditions.${index}.refCond`}
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

const ConditionValueAsName: FC<PropsConditionObjectValueComponent> = ({
  index,
  control,
  attrId,
}) => {
  return (
    <NamedObjectBox>
      <FlexBox>
        <NameBox>
          <Controller
            name={`conditions.${index}.strCond`}
            control={control}
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

const ConditionValue: FC<PropsConditionValue> = ({
  index,
  control,
  entity,
  attrId,
}) => {
  const attrInfo = entity.attrs.find((attr) => attr.id === attrId);
  switch (attrInfo?.type) {
    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return <ConditionValueAsString index={index} control={control} />;

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return <ConditionValueAsBoolean index={index} control={control} />;

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <ConditionValueAsObject
          index={index}
          control={control}
          attrId={attrId}
        />
      );

    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
      return (
        <ConditionValueAsName index={index} control={control} attrId={attrId} />
      );
  }
};

export const Condition: FC<Props> = ({
  index,
  control,
  remove,
  handleAppendCondition,
  entity,
}) => {
  const attrId = useWatch({
    control,
    name: `conditions.${index}.attr.id`,
  });

  return (
    <TableRow>
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
        <IconButton onClick={() => handleAppendCondition(index + 1)}>
          <AddIcon />
        </IconButton>
      </TableCell>
    </TableRow>
  );
};
