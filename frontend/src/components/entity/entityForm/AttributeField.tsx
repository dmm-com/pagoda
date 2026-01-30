import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import BadgeIcon from "@mui/icons-material/Badge";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditNoteIcon from "@mui/icons-material/EditNote";
import GroupIcon from "@mui/icons-material/Group";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Autocomplete,
  Box,
  Checkbox,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Select,
  TableCell,
  TextField,
  Tooltip,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useMemo, useState } from "react";
import { Control, Controller, useWatch } from "react-hook-form";
import { UseFormSetValue } from "react-hook-form/dist/types/form";
import { Link } from "react-router";

import { AttributeAutoNameConfigModal } from "./AttributeAutoNameConfigModal";
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
  const [openAutoNameConfigModal, setOpenAutoNameConfigModal] = useState(false);
  const [attrMenuElem, setAttrMenuElem] = useState<HTMLButtonElement | null>(
    null,
  );

  const attributeTypeMenuItems = useMemo(() => {
    return ATTRIBUTE_TYPE_ORDER.map((key) => (
      <MenuItem key={key} value={AttributeTypes[key].type}>
        {AttributeTypes[key].name}
      </MenuItem>
    ));
  }, []);

  const isObjectLikeType = ((attrType ?? 0) & AttributeTypes.object.type) > 0;

  const handleCloseModal = () => setOpenModal(false);
  const handleCloseAutoNameConfigModal = () =>
    setOpenAutoNameConfigModal(false);

  return index != null ? (
    <>
      {/* Attribute Name */}
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

      {/* Attribute type */}
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

      {/* Default value */}
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

      {/* Change Attribute order to be shown at Item detail page */}
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

      {/* Delete target Attribute */}
      <TableCell>
        <IconButton
          onClick={() => handleDeleteAttribute(index)}
          disabled={!isWritable}
        >
          <DeleteOutlineIcon />
        </IconButton>
      </TableCell>

      {/* Add another Attribute button */}
      <TableCell>
        <IconButton onClick={() => handleAppendAttribute(index ?? 0)}>
          <AddIcon />
        </IconButton>
      </TableCell>

      {/* Icon other settings */}
      <TableCell>
        <Tooltip title="詳細">
          <IconButton
            onClick={(e) => {
              setAttrMenuElem(e.currentTarget);
            }}
          >
            <MoreVertIcon />
          </IconButton>
        </Tooltip>
        <Menu
          open={Boolean(attrMenuElem)}
          onClose={() => setAttrMenuElem(null)}
          anchorEl={attrMenuElem}
        >
          <List
            sx={{ width: "100%", maxWidth: 360, bgcolor: "background.paper" }}
          >
            {/* Open modal for setting Attribute description */}
            <ListItemButton onClick={() => setOpenModal(true)}>
              <ListItemIcon>
                <EditNoteIcon />
              </ListItemIcon>
              <ListItemText primary="属性説明" secondary="属性の説明文を設定" />
            </ListItemButton>

            {/* Open modal for setting Attribute auto-naming configuration */}
            <ListItemButton onClick={() => setOpenAutoNameConfigModal(true)}>
              <ListItemIcon>
                <BadgeIcon />
              </ListItemIcon>
              <ListItemText
                primary="自動命名"
                secondary="属性値からアイテム名を自動設定"
              />
            </ListItemButton>

            {/* Button ACL Configuration */}
            <ListItemButton
              component={Link}
              to={aclPath(attrId ?? 0)}
              disabled={attrId == null || !isWritable}
            >
              <ListItemIcon>
                <GroupIcon />
              </ListItemIcon>
              <ListItemText primary="ACL設定" secondary="属性の権限を設定" />
            </ListItemButton>

            <Divider />

            {/* Set mandatory Attribute */}
            <ListItem>
              <ListItemIcon>
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
              </ListItemIcon>
              <ListItemText
                primary="必須設定"
                secondary="属性値の設定を必須化"
              />
            </ListItem>

            {/* Checkbox delete Item when related Item is deleted */}
            <ListItem>
              <ListItemIcon>
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
              </ListItemIcon>
              <ListItemText
                primary="関連削除"
                secondary="参照アイテムの削除に連動"
              />
            </ListItem>
          </List>
        </Menu>
      </TableCell>

      {openModal && (
        <AttributeNoteModal
          index={index}
          handleCloseModal={handleCloseModal}
          control={control}
        />
      )}
      {openAutoNameConfigModal && (
        <AttributeAutoNameConfigModal
          index={index}
          handleCloseModal={handleCloseAutoNameConfigModal}
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
      <TableCell>
        <IconButton onClick={() => handleAppendAttribute(index ?? 0)}>
          <AddIcon />
        </IconButton>
      </TableCell>
      <TableCell />
    </>
  );
};
