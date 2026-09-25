import { Entity } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  DraggableAttributes,
  DraggableSyntheticListeners,
} from "@dnd-kit/core";
import AddIcon from "@mui/icons-material/Add";
import BadgeIcon from "@mui/icons-material/Badge";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import DragIndicatorIcon from "@mui/icons-material/DragIndicator";
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
import { UseFormSetValue } from "react-hook-form";
import { Link } from "react-router";

import { AttributeAutoNameConfigModal } from "./AttributeAutoNameConfigModal";
import { AttributeNoteModal } from "./AttributeNoteModal";
import { ChoicesEditor } from "./ChoicesEditor";
import { DefaultObjectValueField } from "./DefaultObjectValueField";
import { Schema } from "./EntityFormSchema";

import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { aclPath } from "routes/Routes";
import { AttributeTypes } from "services/Constants";
import { fuzzyMatch } from "services/StringUtil";

const StyledBox = styled(Box)(({ theme }) => ({
  margin: theme.spacing(1),
  display: "flex",
  flexDirection: "column",
  gap: "8px",
}));

// Attribute types that support autoname (mirrors backend Entity.ITEM_NAME_SELECTABLE_TYPES)
const AUTONAME_SELECTABLE_TYPES = [
  AttributeTypes.string.type,
  AttributeTypes.object.type,
  AttributeTypes.number.type,
  AttributeTypes.date.type,
];

// Attribute types eligible as display_attr on a referred entry (mirrors backend
// entry.api_v2.serializers._DISPLAY_LABEL_ALLOWED_TYPES). Array / named / group
// / role are intentionally excluded — backend returns null for those.
const DISPLAY_ATTR_ALLOWED_TYPES: ReadonlySet<number> = new Set([
  AttributeTypes.string.type,
  AttributeTypes.text.type,
  AttributeTypes.number.type,
  AttributeTypes.boolean.type,
  AttributeTypes.date.type,
  AttributeTypes.datetime.type,
  AttributeTypes.object.type,
]);

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
  "select",
  "multi_select",
  "date",
  "datetime",
];

// Props forwarded from the sortable row wrapper so this cell can host the
// drag handle (pointer + keyboard activation) for reordering attributes.
interface AttributeDragHandleProps {
  setActivatorNodeRef: (element: HTMLElement | null) => void;
  attributes: DraggableAttributes;
  listeners: DraggableSyntheticListeners;
  isDragging: boolean;
}

interface Props {
  control: Control<Schema>;
  setValue: UseFormSetValue<Schema>;
  referralEntities: Entity[];
  handleAppendAttribute: (index: number) => void;
  handleDeleteAttribute: (index: number) => void;
  dragHandleProps?: AttributeDragHandleProps;
  attrId?: number;
  index?: number;
}

export const AttributeField: FC<Props> = ({
  control,
  setValue,
  referralEntities,
  handleAppendAttribute,
  handleDeleteAttribute,
  dragHandleProps,
  attrId,
  index,
}) => {
  const { t } = useTranslation();
  const attrType = useWatch({
    control,
    name: `attrs.${index ?? -1}.type`,
  });
  const attrName = useWatch({
    control,
    name: `attrs.${index ?? -1}.name`,
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
  const isSelectLikeType = ((attrType ?? 0) & AttributeTypes.select.type) > 0;
  const isAutoNameSupported = AUTONAME_SELECTABLE_TYPES.includes(attrType ?? 0);

  // Watch selected referral entities so display_attr candidates can be
  // narrowed to the attrs those entities actually declare.
  const referral = useWatch({
    control,
    name: `attrs.${index ?? -1}.referral`,
  });
  const referralIds = useMemo(
    () => (referral ?? []).map((r: { id: number }) => r.id),
    [referral],
  );
  // Candidate fetching is optional UX — a fetch failure must never crash the
  // entity edit form (usePagodaSWR re-throws errors in render). Swallow errors
  // in the fetcher so SWR sees success-with-empty-list on failure.
  const { data: refEntityAttrs, isLoading: displayAttrLoading } = usePagodaSWR(
    isObjectLikeType && referralIds.length > 0
      ? (["displayAttrCandidates", referralIds] as const)
      : null,
    async () => {
      try {
        return await aironeApiClient.getEntityAttrs(referralIds, false);
      } catch {
        return [];
      }
    },
  );
  const displayAttrOptions = useMemo(() => {
    const names = new Set<string>();
    (refEntityAttrs ?? []).forEach((a: { name: string; type: number }) => {
      if (DISPLAY_ATTR_ALLOWED_TYPES.has(a.type)) {
        names.add(a.name);
      }
    });
    return Array.from(names).sort();
  }, [refEntityAttrs]);

  const handleCloseModal = () => setOpenModal(false);
  const handleCloseAutoNameConfigModal = () =>
    setOpenAutoNameConfigModal(false);

  return index != null ? (
    <>
      {/* Drag handle to reorder attributes (pointer & keyboard) */}
      <TableCell>
        <Box display="flex" alignItems="center" justifyContent="center">
          <Tooltip title={t("entity.form.dragReorderTooltip")}>
            {/* span keeps the tooltip working while the button is disabled */}
            <span>
              <IconButton
                ref={dragHandleProps?.setActivatorNodeRef}
                disabled={!isWritable || dragHandleProps == null}
                aria-label={t("entity.form.dragReorderAriaLabel", {
                  index: index + 1,
                })}
                data-testid="attr-drag-handle"
                sx={{
                  cursor: dragHandleProps?.isDragging ? "grabbing" : "grab",
                  touchAction: "none",
                }}
                {...(dragHandleProps?.attributes ?? {})}
                {...(dragHandleProps?.listeners ?? {})}
              >
                <DragIndicatorIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </TableCell>

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
              placeholder={t("entity.form.attrNameHeader")}
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
                inputProps={{
                  "aria-label": t("entity.form.attrTypeAriaLabel", {
                    name: attrName || t("entity.form.unnamedAttribute"),
                  }),
                }}
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
                  filterOptions={(options, state) =>
                    options.filter((option) =>
                      fuzzyMatch(option.name, state.inputValue),
                    )
                  }
                  isOptionEqualToValue={(
                    option: { id: number; name: string },
                    value: { id: number; name: string },
                  ) => option.id === value.id}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      variant="outlined"
                      placeholder={t("entity.form.selectEntityPlaceholder")}
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
          {isObjectLikeType && (
            <Controller
              name={`attrs.${index}.displayAttr`}
              control={control}
              defaultValue=""
              render={({ field }) => (
                <Autocomplete
                  freeSolo
                  options={displayAttrOptions}
                  value={field.value ?? ""}
                  onChange={(_e, v) =>
                    field.onChange(typeof v === "string" ? v : (v ?? ""))
                  }
                  onInputChange={(_e, v, reason) => {
                    if (reason === "input" || reason === "clear") {
                      field.onChange(v);
                    }
                  }}
                  size="small"
                  fullWidth
                  disabled={!isWritable}
                  loading={displayAttrLoading}
                  noOptionsText={
                    referralIds.length === 0
                      ? t("entity.form.selectEntityFirstOption")
                      : t("entity.form.noMatchingAttrOption")
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      id="display_attr"
                      placeholder={t("entity.form.displayAttrPlaceholder")}
                      inputProps={{
                        ...params.inputProps,
                        "data-1p-ignore": true,
                      }}
                    />
                  )}
                />
              )}
            />
          )}
          {isSelectLikeType && (
            <ChoicesEditor
              control={control}
              index={index}
              disabled={!isWritable}
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
            if (
              attrType === AttributeTypes.object.type ||
              attrType === AttributeTypes.array_object.type
            ) {
              return (
                <DefaultObjectValueField
                  value={field.value as number | number[] | null | undefined}
                  referralEntityIds={referralIds}
                  multiple={attrType === AttributeTypes.array_object.type}
                  disabled={!isWritable || referralIds.length === 0}
                  ariaLabel={t("entity.form.defaultValueAriaLabel", {
                    index: index + 1,
                  })}
                  onChange={field.onChange}
                />
              );
            }

            // Check if this attribute type supports default values
            const isDefaultValueSupported =
              attrType === AttributeTypes.string.type ||
              attrType === AttributeTypes.text.type ||
              attrType === AttributeTypes.boolean.type ||
              attrType === AttributeTypes.number.type ||
              attrType === AttributeTypes.select.type;

            // Boolean type gets a checkbox
            if (attrType === AttributeTypes.boolean.type) {
              return (
                <Checkbox
                  checked={Boolean(field.value) ?? false}
                  onChange={(e) => field.onChange(e.target.checked)}
                  disabled={!isWritable}
                  inputProps={{
                    "aria-label": t("entity.form.defaultValueAriaLabel", {
                      index: index + 1,
                    }),
                  }}
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
                  placeholder={t("entity.form.defaultValueHeader")}
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
                    ? t("entity.form.defaultValueHeader")
                    : t("entity.form.defaultValueUnsupported")
                }
                size="small"
                fullWidth
                disabled={!isWritable || !isDefaultValueSupported}
              />
            );
          }}
        />
      </TableCell>

      {/* Delete target Attribute */}
      <TableCell>
        <IconButton
          aria-label={t("entity.form.deleteAttrAriaLabel", {
            index: index + 1,
          })}
          onClick={() => handleDeleteAttribute(index)}
          disabled={!isWritable}
        >
          <DeleteOutlineIcon />
        </IconButton>
      </TableCell>

      {/* Add another Attribute button */}
      <TableCell>
        <IconButton
          aria-label={t("entity.form.appendAttrAriaLabel", {
            index: index + 1,
          })}
          onClick={() => handleAppendAttribute(index ?? 0)}
        >
          <AddIcon />
        </IconButton>
      </TableCell>

      {/* Icon other settings */}
      <TableCell>
        <Tooltip title={t("common.details")}>
          <IconButton
            aria-label={t("entity.form.attrMenuAriaLabel", {
              index: index + 1,
            })}
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
              <ListItemText
                primary={t("entity.form.attrDescriptionMenuTitle")}
                secondary={t("entity.form.attrDescriptionMenuSubtitle")}
              />
            </ListItemButton>

            {/* Open modal for setting Attribute auto-naming configuration */}
            <ListItemButton
              onClick={() => setOpenAutoNameConfigModal(true)}
              disabled={!isAutoNameSupported}
            >
              <ListItemIcon>
                <BadgeIcon />
              </ListItemIcon>
              <ListItemText
                primary={t("entity.form.autoNameMenuTitle")}
                secondary={t("entity.form.autoNameMenuSubtitle")}
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
              <ListItemText
                primary={t("entity.form.aclMenuTitle")}
                secondary={t("entity.form.aclMenuSubtitle")}
              />
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
                      inputProps={{
                        "aria-label": t("entity.form.mandatoryAriaLabel", {
                          index: index + 1,
                        }),
                      }}
                      disabled={!isWritable}
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                    />
                  )}
                />
              </ListItemIcon>
              <ListItemText
                primary={t("entity.form.mandatoryMenuTitle")}
                secondary={t("entity.form.mandatoryMenuSubtitle")}
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
                      inputProps={{
                        "aria-label": t("entity.form.deleteInChainAriaLabel", {
                          index: index + 1,
                        }),
                      }}
                      disabled={!isWritable}
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                    />
                  )}
                />
              </ListItemIcon>
              <ListItemText
                primary={t("entity.form.deleteInChainMenuTitle")}
                secondary={t("entity.form.deleteInChainMenuSubtitle")}
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
        <IconButton
          aria-label={t("entity.form.addAttrAriaLabel")}
          onClick={() => handleAppendAttribute(index ?? 0)}
        >
          <AddIcon />
        </IconButton>
      </TableCell>
      <TableCell />
    </>
  );
};
