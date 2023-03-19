import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { Box, IconButton, List, ListItem, TextField } from "@mui/material";
import React, { FC } from "react";
import { Control, useFieldArray, useWatch, Controller } from "react-hook-form";

import { Schema } from "../EntryFormSchema";

interface CommonProps {
  attrName: string;
  // TODO remove it?
  attrType: number;
  isMandatory: boolean;
  index?: number;
}

export const StringAttributeValueField: FC<
  CommonProps & {
    handleClickDeleteListItem?: (index: number) => void;
    handleClickAddListItem?: (index: number) => void;
    multiline?: boolean;
    control: Control<Schema>;
  }
> = ({
  attrName,
  // FIXME should use it
  isMandatory,
  index,
  handleClickDeleteListItem,
  handleClickAddListItem,
  multiline,
  control,
}) => {
  const value = useWatch({
    control,
    name:
      index != null
        ? `attrs.${attrName}.value.asArrayString.${index}`
        : `attrs.${attrName}.value.asString`,
  });

  const disabledToAppend = index === 0 && value === "";

  return (
    <Box display="flex" width="100%">
      <Controller
        name={
          index != null
            ? `attrs.${attrName}.value.asArrayString.${index}`
            : `attrs.${attrName}.value.asString`
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
          />
        )}
      />
      {index !== undefined && (
        <>
          {handleClickDeleteListItem != null && (
            <IconButton
              disabled={disabledToAppend}
              sx={{ mx: "20px" }}
              onClick={() => handleClickDeleteListItem(index)}
            >
              <DeleteOutlineIcon />
            </IconButton>
          )}
          {handleClickAddListItem != null && (
            <IconButton onClick={() => handleClickAddListItem(index)}>
              <AddIcon />
            </IconButton>
          )}
        </>
      )}
    </Box>
  );
};

export const ArrayStringAttributeValueField: FC<
  CommonProps & {
    attrValue?: Array<string>;
    multiline?: boolean;
    control: Control<Schema>;
  }
> = ({ attrName, attrType, isMandatory, multiline, control }) => {
  const { fields, insert, remove } = useFieldArray({
    control,
    name: `attrs.${attrName}.value.asArrayString` as "attrs.${string}.value.asArrayObject",
  });

  const handleClickAddListItem = (index: number) => {
    // TODO fix the type error; its misrecognizing the type of fields as object-like type
    // @ts-ignore
    insert(index + 1, "");
  };

  const handleClickDeleteListItem = (index: number) => {
    remove(index);
    fields.length === 1 && handleClickAddListItem(0);
  };

  return (
    <Box>
      <List>
        {fields.map((field, index) => (
          <ListItem key={field.id}>
            <StringAttributeValueField
              control={control}
              attrName={attrName}
              attrType={attrType}
              isMandatory={isMandatory}
              index={index}
              handleClickDeleteListItem={handleClickDeleteListItem}
              handleClickAddListItem={handleClickAddListItem}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
