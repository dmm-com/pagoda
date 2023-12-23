import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { Box, IconButton, List, ListItem, TextField } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useEffect } from "react";
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
}

export const StringAttributeValueField: FC<
  CommonProps & {
    handleClickDeleteListItem?: (index: number) => void;
    handleClickAddListItem?: (index: number) => void;
    multiline?: boolean;
  }
> = ({
  attrId,
  index,
  control,
  handleClickDeleteListItem,
  handleClickAddListItem,
  multiline,
}) => {
  return (
    <StyledBox>
      <Controller
        name={
          index != null
            ? `attrs.${attrId}.value.asArrayString.${index}.value`
            : `attrs.${attrId}.value.asString`
        }
        control={control}
        defaultValue=""
        render={({ field, fieldState: { error } }) => (
          <TextField
            {...field}
            variant="standard"
            error={error != null}
            helperText={error?.message}
            fullWidth
            multiline={multiline}
            minRows={multiline === true ? 5 : 1}
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

export const ArrayStringAttributeValueField: FC<CommonProps> = ({
  attrId,
  control,
}) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: `attrs.${attrId}.value.asArrayString`,
  });

  useEffect(() => {
    if (fields.length === 0) {
      handleClickAddListItem(0);
    }
  }, []);

  const handleClickAddListItem = (index: number) => {
    // TODO fix the type error; its misrecognizing the type of fields as object-like type
    insert(index + 1, { value: "" });
  };

  const handleClickDeleteListItem = (index: number) => {
    remove(index);
    fields.length === 1 && handleClickAddListItem(0);
  };

  return (
    <StyledList>
      {fields.map((field, index) => (
        <ListItem key={field.id} disablePadding={true}>
          <StringAttributeValueField
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
