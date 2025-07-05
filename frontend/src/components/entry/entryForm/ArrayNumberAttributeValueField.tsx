import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { Box, IconButton, List, ListItem, TextField } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Control, useFieldArray, Controller } from "react-hook-form";

import { Schema } from "./EntryFormSchema";

const StyledList = styled(List)(({}) => ({
  padding: "0",
}));

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  width: "100%",
  gap: "0 12px",
}));

interface CommonProps {
  attrId: number;
  index?: number;
  control: Control<Schema>;
  isDisabled?: boolean;
}

export const NumberAttributeValueFieldForArray: FC<
  CommonProps & {
    handleClickDeleteListItem?: (index: number) => void;
    handleClickAddListItem?: (index: number) => void;
  }
> = ({
  attrId,
  index,
  control,
  handleClickDeleteListItem,
  handleClickAddListItem,
  isDisabled = false,
}) => {
  return (
    <StyledBox>
      <Controller
        name={`attrs.${attrId}.value.asArrayNumber.${index}.value`}
        control={control}
        defaultValue={null}
        render={({ field, fieldState: { error } }) => (
          <TextField
            {...field}
            type="number"
            variant="standard"
            error={error != null}
            helperText={error?.message}
            fullWidth
            disabled={isDisabled}
            value={field.value ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              field.onChange(value === "" ? null : Number(value));
            }}
          />
        )}
      />
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
    </StyledBox>
  );
};

export const ArrayNumberAttributeValueField: FC<CommonProps> = ({
  attrId,
  control,
}) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: `attrs.${attrId}.value.asArrayNumber`,
  });

  const handleClickAddListItem = (index: number) => {
    insert(index + 1, { value: null });
  };

  const handleClickDeleteListItem = (index: number) => {
    remove(index);
    fields.length === 1 && handleClickAddListItem(0);
  };

  return (
    <StyledList>
      {fields.map((field, index) => (
        <ListItem key={field.id} disablePadding={true}>
          <NumberAttributeValueFieldForArray
            control={control}
            attrId={attrId}
            index={index}
            handleClickDeleteListItem={handleClickDeleteListItem}
            handleClickAddListItem={handleClickAddListItem}
          />
        </ListItem>
      ))}
    </StyledList>
  );
};
