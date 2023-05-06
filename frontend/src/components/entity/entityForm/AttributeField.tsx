import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
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
  TableRow,
  Typography,
  ButtonTypeMap,
  TextField,
  Autocomplete,
} from "@mui/material";
import { ExtendButtonBaseTypeMap } from "@mui/material/ButtonBase/ButtonBase";
import { IconButtonTypeMap } from "@mui/material/IconButton/IconButton";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import React, { FC, useMemo } from "react";
import { Control, Controller, useWatch } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";
import { Link } from "react-router-dom";

import { Schema } from "../EntityFormSchema";

import { aclPath } from "Routes";
import { AttributeTypes } from "services/Constants";

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  margin: theme.spacing(1),
})) as OverridableComponent<ExtendButtonBaseTypeMap<IconButtonTypeMap>>;

const StyledButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(1),
})) as OverridableComponent<ExtendButtonBaseTypeMap<ButtonTypeMap>>;

const NormalTableRow = styled(TableRow)(({}) => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "white",
  },
  "&:nth-of-type(even)": {
    backgroundColor: "#607D8B0A",
  },
}));

const HighlightedTableRow = styled(TableRow)(({}) => ({
  "@keyframes highlighted": {
    from: {
      backgroundColor: "#6B8998",
    },
    to: {
      "&:nth-of-type(odd)": {
        backgroundColor: "white",
      },
      "&:nth-of-type(even)": {
        backgroundColor: "#607D8B0A",
      },
    },
  },
  animation: "highlighted 2s ease infinite",
}));

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  maxIndex: number;
  referralEntities: Entity[];
  latestChangedIndex: number | null;
  setLatestChangedIndex: (latestChangedIndex: number | null) => void;
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
  latestChangedIndex,
  setLatestChangedIndex,
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

  const attributeTypeMenuItems = useMemo(() => {
    return Object.keys(AttributeTypes).map((typename, index) => (
      <MenuItem key={index} value={AttributeTypes[typename].type}>
        {AttributeTypes[typename].name}
      </MenuItem>
    ));
  }, []);

  const StyledTableRow =
    index != null && index === latestChangedIndex
      ? HighlightedTableRow
      : NormalTableRow;

  const isObjectLikeType = ((attrType ?? 0) & AttributeTypes.object.type) > 0;

  return (
    <StyledTableRow onAnimationEnd={() => setLatestChangedIndex(null)}>
      {index != null ? (
        <>
          <TableCell>
            <Controller
              name={`attrs.${index}.name`}
              control={control}
              defaultValue=""
              render={({ field, fieldState: { error } }) => (
                <TextField
                  {...field}
                  required
                  placeholder="属性名"
                  error={error != null}
                  helperText={error?.message}
                  sx={{ width: "100%" }}
                />
              )}
            />
          </TableCell>

          <TableCell>
            <Box>
              <Box minWidth={100} marginX={1}>
                <Controller
                  name={`attrs.${index}.type`}
                  control={control}
                  defaultValue={0}
                  render={({ field, fieldState: { error } }) => (
                    <Select
                      {...field}
                      fullWidth={true}
                      disabled={attrId != null}
                    >
                      {attributeTypeMenuItems}
                    </Select>
                  )}
                />
              </Box>
              {isObjectLikeType && (
                <Box minWidth={100} marginX={1}>
                  <Typography>エンティティを選択</Typography>

                  <Controller
                    name={`attrs.${index}.referral`}
                    control={control}
                    defaultValue={[]}
                    render={({ field, fieldState: { error } }) => (
                      <Autocomplete
                        {...field}
                        options={referralEntities}
                        getOptionLabel={(option: {
                          id: number;
                          name: string;
                        }) => option.name}
                        isOptionEqualToValue={(
                          option: { id: number; name: string },
                          value: { id: number; name: string }
                        ) => option.id === value.id}
                        renderInput={(params) => (
                          <TextField {...params} variant="outlined" />
                        )}
                        onChange={(_e, value: { id: number; name: string }[]) =>
                          setValue(`attrs.${index}.referral`, value, {
                            shouldDirty: true,
                            shouldValidate: true,
                          })
                        }
                        multiple
                      />
                    )}
                  />
                </Box>
              )}
            </Box>
          </TableCell>

          <TableCell>
            <Controller
              name={`attrs.${index}.isMandatory`}
              control={control}
              defaultValue={false}
              render={({ field, fieldState: { error } }) => (
                <Checkbox
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
              render={({ field, fieldState: { error } }) => (
                <Checkbox
                  checked={field.value}
                  onChange={(e) => field.onChange(e.target.checked)}
                />
              )}
            />
          </TableCell>

          <TableCell>
            <Box display="flex" flexDirection="column">
              <StyledIconButton
                disabled={index === 0}
                onClick={() => handleChangeOrderAttribute(index, 1)}
              >
                <ArrowUpwardIcon />
              </StyledIconButton>

              <StyledIconButton
                disabled={index === maxIndex}
                onClick={() => handleChangeOrderAttribute(index, -1)}
              >
                <ArrowDownwardIcon />
              </StyledIconButton>
            </Box>
          </TableCell>

          <TableCell>
            <StyledIconButton onClick={() => handleDeleteAttribute(index)}>
              <DeleteOutlineIcon />
            </StyledIconButton>
          </TableCell>

          {/* This is a button to add new Attribute */}
          <TableCell>
            <StyledIconButton onClick={() => handleAppendAttribute(index ?? 0)}>
              <AddIcon />
            </StyledIconButton>
          </TableCell>

          <TableCell>
            <StyledButton
              variant="contained"
              color="primary"
              startIcon={<GroupIcon />}
              component={Link}
              to={aclPath(attrId ?? 0)}
              disabled={attrId == null}
            >
              ACL
            </StyledButton>
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
            <StyledIconButton onClick={() => handleAppendAttribute(index ?? 0)}>
              <AddIcon />
            </StyledIconButton>
          </TableCell>
          <TableCell />
        </>
      )}
    </StyledTableRow>
  );
};
