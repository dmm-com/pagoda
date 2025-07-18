import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditNoteIcon from "@mui/icons-material/EditNote";
import GroupIcon from "@mui/icons-material/Group";
import {
  Box,
  Button,
  Checkbox,
  IconButton,
  MenuItem,
  Select,
  TableCell,
  TextField,
  Autocomplete,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useMemo, useState } from "react";
import { Control, Controller, useWatch } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";
import { Link } from "react-router";

import { AttributeNoteModal } from "./AttributeNoteModal";
import { Schema } from "./EntityFormSchema";

import { aclPath } from "routes/Routes";
import { AttributeTypes } from "services/Constants";

const StyledBox = styled(Box)(({ theme }) => ({
  margin: theme.spacing(1),
  display: "flex",
  flexDirection: "column",
  gap: "8px",
}));

// Define the custom display order for attribute types
const ATTRIBUTE_TYPE_ORDER = [
  "string",
  "array_string",
  "object",
  "array_object",
  "named_object",
  "array_named_object",
  "group",
  "array_group",
  "role",
  "array_role",
  "text",
  "boolean",
  "number",
  "array_number",
  "date",
  "datetime",
];

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  maxIndex: number;
  referralEntities: Entity[];
  handleAppendAttribute: (index: number) => void;
  handleDeleteAttribute: (index: number) => void;
  handleChangeOrderAttribute: (index: number, order: number) => void;
  attrId?: number;
  index?: number;
}

export const AttributeField: FC<Props> = ({
  control,
  setValue,
  maxIndex,
  referralEntities,
  handleAppendAttribute,
  handleDeleteAttribute,
  handleChangeOrderAttribute,
  attrId,
  index,
}) => {
  const attrType = useWatch({
    control,
    name: `attrs.${index ?? -1}.type`,
  });

  const isWritable = useWatch({
    control,
    name: `attrs.${index ?? -1}.isWritable`,
  });

  const [openModal, setOpenModal] = useState(false);

  const attributeTypeMenuItems = useMemo(() => {
    return ATTRIBUTE_TYPE_ORDER.map((key) => (
      <MenuItem key={key} value={AttributeTypes[key].type}>
        {AttributeTypes[key].name}
      </MenuItem>
    ));
  }, []);

  const isObjectLikeType = ((attrType ?? 0) & AttributeTypes.object.type) > 0;

  const handleCloseModal = () => setOpenModal(false);

  return index != null ? (
    <>
      <TableCell>
        <Controller
          name={`attrs.${index}.name`}
          control={control}
          defaultValue=""
          render={({ field, fieldState: { error } }) => (
            <TextField
              {...field}
              id="attr-name"
              required
              disabled={!isWritable}
              placeholder="属性名"
              error={error != null}
              helperText={error?.message}
              size="small"
              fullWidth
            />
          )}
        />
      </TableCell>

      <TableCell>
        <IconButton onClick={() => setOpenModal(true)}>
          <EditNoteIcon />
        </IconButton>
      </TableCell>

      <TableCell>
        <StyledBox>
          <Controller
            name={`attrs.${index}.type`}
            control={control}
            defaultValue={0}
            render={({ field }) => (
              <Select
                {...field}
                id="attr_type"
                size="small"
                fullWidth
                disabled={attrId != null}
              >
                {attributeTypeMenuItems}
              </Select>
            )}
          />
          {isObjectLikeType && (
            <Controller
              name={`attrs.${index}.referral`}
              control={control}
              defaultValue={[]}
              render={({ field }) => (
                <Autocomplete
                  {...field}
                  options={referralEntities}
                  getOptionLabel={(option: { id: number; name: string }) =>
                    option.name
                  }
                  isOptionEqualToValue={(
                    option: { id: number; name: string },
                    value: { id: number; name: string },
                  ) => option.id === value.id}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      variant="outlined"
                      placeholder="モデルを選択"
                      disabled={!isWritable}
                    />
                  )}
                  onChange={(_e, value: { id: number; name: string }[]) =>
                    setValue(`attrs.${index}.referral`, value, {
                      shouldDirty: true,
                      shouldValidate: true,
                    })
                  }
                  size="small"
                  multiple
                />
              )}
            />
          )}
        </StyledBox>
      </TableCell>

      <TableCell>
        <Controller
          name={`attrs.${index}.defaultValue`}
          control={control}
          render={({ field }) => {
            // Check if this attribute type supports default values
            const isDefaultValueSupported =
              attrType === AttributeTypes.string.type ||
              attrType === AttributeTypes.text.type ||
              attrType === AttributeTypes.boolean.type ||
              attrType === AttributeTypes.number.type;

            // Boolean type gets a checkbox
            if (attrType === AttributeTypes.boolean.type) {
              return (
                <Checkbox
                  checked={Boolean(field.value) ?? false}
                  onChange={(e) => field.onChange(e.target.checked)}
                  disabled={!isWritable}
                />
              );
            }

            // Number type gets a number input
            if (attrType === AttributeTypes.number.type) {
              return (
                <TextField
                  {...field}
                  type="number"
                  value={field.value ?? ""}
                  placeholder="デフォルト値"
                  size="small"
                  fullWidth
                  disabled={!isWritable}
                />
              );
            }

            // Text input for supported string types or disabled for unsupported types
            return (
              <TextField
                {...field}
                value={field.value ?? ""}
                placeholder={
                  isDefaultValueSupported
                    ? "デフォルト値"
                    : "この型では未サポート"
                }
                size="small"
                fullWidth
                disabled={!isWritable || !isDefaultValueSupported}
              />
            );
          }}
        />
      </TableCell>

      <TableCell>
        <Controller
          name={`attrs.${index}.isMandatory`}
          control={control}
          defaultValue={false}
          render={({ field }) => (
            <Checkbox
              id="mandatory"
              disabled={!isWritable}
              checked={field.value}
              onChange={(e) => field.onChange(e.target.checked)}
            />
          )}
        />
      </TableCell>

      <TableCell>
        <Controller
          name={`attrs.${index}.isDeleteInChain`}
          control={control}
          defaultValue={false}
          render={({ field }) => (
            <Checkbox
              id="delete_in_chain"
              disabled={!isWritable}
              checked={field.value}
              onChange={(e) => field.onChange(e.target.checked)}
            />
          )}
        />
      </TableCell>

      <TableCell>
        <Box display="flex" flexDirection="column">
          <IconButton
            disabled={index === 0 || !isWritable}
            onClick={() => handleChangeOrderAttribute(index, 1)}
          >
            <ArrowUpwardIcon />
          </IconButton>

          <IconButton
            disabled={index === maxIndex || !isWritable}
            onClick={() => handleChangeOrderAttribute(index, -1)}
          >
            <ArrowDownwardIcon />
          </IconButton>
        </Box>
      </TableCell>

      <TableCell>
        <IconButton
          onClick={() => handleDeleteAttribute(index)}
          disabled={!isWritable}
        >
          <DeleteOutlineIcon />
        </IconButton>
      </TableCell>

      <TableCell>
        <IconButton onClick={() => handleAppendAttribute(index ?? 0)}>
          <AddIcon />
        </IconButton>
      </TableCell>

      <TableCell>
        <Button
          variant="contained"
          color="primary"
          startIcon={<GroupIcon />}
          component={Link}
          to={aclPath(attrId ?? 0)}
          disabled={attrId == null || !isWritable}
        />
      </TableCell>

      {openModal && (
        <AttributeNoteModal
          index={index}
          handleCloseModal={handleCloseModal}
          control={control}
        />
      )}
    </>
  ) : (
    <>
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell>
        <IconButton onClick={() => handleAppendAttribute(index ?? 0)}>
          <AddIcon />
        </IconButton>
      </TableCell>
      <TableCell />
    </>
  );
};
