import AddIcon from "@mui/icons-material/Add";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
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
import React, { FC, useMemo } from "react";
import { Control, Controller, useWatch } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";
import { Link } from "react-router-dom";

import { Schema } from "./EntityFormSchema";

import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import { aclPath } from "Routes";
import { AttributeTypes } from "services/Constants";

const StyledBox = styled(Box)(({ theme }) => ({
  margin: theme.spacing(1),
  display: "flex",
  flexDirection: "column",
  gap: "8px",
}));

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

  const attributeTypeMenuItems = useMemo(() => {
    return Object.keys(AttributeTypes).map((typename, index) => (
      <MenuItem key={index} value={AttributeTypes[typename].type}>
        {AttributeTypes[typename].name}
      </MenuItem>
    ));
  }, []);

  const isObjectLikeType = ((attrType ?? 0) & AttributeTypes.object.type) > 0;

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
                    value: { id: number; name: string }
                  ) => option.id === value.id}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      variant="outlined"
                      placeholder="エンティティを選択"
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

      {/* This is a button to add new Attribute */}
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
    </>
  ) : (
    <>
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell />
      <TableCell />
      {/* This is a button to add new Attribute */}
      <TableCell>
        <IconButton onClick={() => handleAppendAttribute(index ?? 0)}>
          <AddIcon />
        </IconButton>
      </TableCell>
      <TableCell />
    </>
  );
};
