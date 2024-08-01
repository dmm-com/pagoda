import { GetEntryAttrReferral } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Checkbox,
  IconButton,
  List,
  ListItem,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useEffect } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";

import { Schema } from "./EntryFormSchema";
import { ReferralsAutocomplete } from "./ReferralsAutocomplete";

const StyledList = styled(List)(({}) => ({
  padding: "0",
}));

const StyledTypography = styled(Typography)(({}) => ({
  color: "rgba(0, 0, 0, 0.6)",
}));

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  alignItems: "center",
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
  width: "280px",
}));

const BooleanBox = styled(Box)(({}) => ({
  display: "flex",
  flexDirection: "column",
  width: "60px",
}));

interface CommonProps {
  attrId: number;
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
}

export const ObjectAttributeValueField: FC<
  CommonProps & {
    multiple?: boolean;
  }
> = ({ multiple, attrId, control, setValue }) => {
  const handleChange = (
    value: GetEntryAttrReferral | GetEntryAttrReferral[] | null
  ) => {
    const newValue = (() => {
      if (value == null) {
        return null;
      }
      if (multiple === true) {
        const _value = value as GetEntryAttrReferral[];
        return _value.map((v) => ({
          ...v,
          _boolean: false,
        }));
      } else {
        const _value = value as GetEntryAttrReferral;
        return {
          ..._value,
          _boolean: false,
        };
      }
    })();

    setValue(
      multiple
        ? `attrs.${attrId}.value.asArrayObject`
        : `attrs.${attrId}.value.asObject`,
      newValue as never,
      {
        shouldDirty: true,
        shouldValidate: true,
      }
    );
  };

  return (
    <Box>
      <StyledTypography variant="caption">アイテムを選択</StyledTypography>
      <StyledBox>
        <Controller
          name={
            multiple
              ? `attrs.${attrId}.value.asArrayObject`
              : `attrs.${attrId}.value.asObject`
          }
          control={control}
          render={({ field, fieldState: { error } }) => (
            <ReferralsAutocomplete
              attrId={attrId}
              value={field.value ?? null}
              handleChange={handleChange}
              multiple={multiple}
              error={error}
            />
          )}
        />
      </StyledBox>
    </Box>
  );
};

export const NamedObjectAttributeValueField: FC<
  CommonProps & {
    index?: number;
    handleClickDeleteListItem?: (index: number) => void;
    handleClickAddListItem?: (index: number) => void;
    withBoolean?: boolean;
  }
> = ({
  attrId,
  index,
  control,
  setValue,
  handleClickAddListItem,
  handleClickDeleteListItem,
  withBoolean,
}) => {
  const handleChange = (
    value: GetEntryAttrReferral | GetEntryAttrReferral[] | null
  ) => {
    const newValue = (() => {
      if (Array.isArray(value)) {
        throw new Error("Array typed value is not supported for named object.");
      }

      if (value == null) {
        return null;
      } else {
        const _value = value as GetEntryAttrReferral;
        return {
          ..._value,
          _boolean: false,
        };
      }
    })();

    setValue(
      index != null
        ? `attrs.${attrId}.value.asArrayNamedObject.${index}.object`
        : `attrs.${attrId}.value.asNamedObject.object`,
      newValue as never,
      {
        shouldDirty: true,
        shouldValidate: true,
      }
    );
  };

  return (
    <NamedObjectBox>
      <FlexBox>
        <StyledTypography variant="caption">name</StyledTypography>
        <NameBox>
          <Controller
            name={
              index != null
                ? `attrs.${attrId}.value.asArrayNamedObject.${index}.name`
                : `attrs.${attrId}.value.asNamedObject.name`
            }
            control={control}
            defaultValue=""
            render={({ field }) => (
              <TextField {...field} variant="standard" fullWidth />
            )}
          />
        </NameBox>
      </FlexBox>
      {withBoolean === true && (
        <BooleanBox>
          <StyledTypography variant="caption">使用不可</StyledTypography>
          <Controller
            name={`attrs.${attrId}.value.asArrayNamedObject.${index}._boolean`}
            control={control}
            render={({ field }) => (
              <Checkbox
                checked={field.value ?? false}
                onChange={(e) => field.onChange(e.target.checked)}
              />
            )}
          />
        </BooleanBox>
      )}
      <Box flexGrow={1}>
        <StyledTypography variant="caption">アイテムを選択</StyledTypography>
        <Controller
          name={
            index != null
              ? `attrs.${attrId}.value.asArrayNamedObject.${index}.object`
              : `attrs.${attrId}.value.asNamedObject.object`
          }
          control={control}
          render={({ field, fieldState: { error } }) => (
            <ReferralsAutocomplete
              attrId={attrId}
              value={field.value ?? null}
              handleChange={handleChange}
              error={error}
            />
          )}
        />
      </Box>
      {index !== undefined && (
        <>
          {handleClickDeleteListItem != null && (
            <IconButton
              id="del_button"
              onClick={() => handleClickDeleteListItem(index)}
            >
              <DeleteOutlineIcon />
            </IconButton>
          )}
          {handleClickAddListItem != null && (
            <IconButton
              id="add_button"
              onClick={() => handleClickAddListItem(index)}
            >
              <AddIcon />
            </IconButton>
          )}
        </>
      )}
    </NamedObjectBox>
  );
};

export const ArrayNamedObjectAttributeValueField: FC<
  CommonProps & {
    withBoolean?: boolean;
  }
> = ({ attrId, control, setValue, withBoolean }) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: `attrs.${attrId}.value.asArrayNamedObject`,
  });

  useEffect(() => {
    if (fields.length === 0) {
      handleClickAddListItem(0);
    }
  }, []);

  const handleClickAddListItem = (index: number) => {
    insert(index + 1, { name: "", object: null, _boolean: false });
  };

  const handleClickDeleteListItem = (index: number) => {
    remove(index);
    fields.length === 1 && handleClickAddListItem(0);
  };

  return (
    <StyledList>
      {fields.map((field, index) => (
        <ListItem key={field.id} disablePadding={true}>
          <NamedObjectAttributeValueField
            control={control}
            setValue={setValue}
            attrId={attrId}
            index={index}
            handleClickDeleteListItem={handleClickDeleteListItem}
            handleClickAddListItem={handleClickAddListItem}
            withBoolean={withBoolean}
          />
        </ListItem>
      ))}
    </StyledList>
  );
};
