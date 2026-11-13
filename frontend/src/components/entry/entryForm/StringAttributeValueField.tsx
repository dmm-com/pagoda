import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { Box, IconButton, List, ListItem, TextField } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, Fragment, useEffect } from "react";
import { Control, Controller, useFieldArray } from "react-hook-form";

import { Schema } from "./EntryFormSchema";

import {
  AddRowButton,
  InsertBand,
  useInsertedRowFocus,
} from "components/common/RowInsertion";
import { useTranslation } from "hooks/useTranslation";
import { getStagedErrorStyle } from "utils/styleUtils";

const StyledList = styled(List)(({}) => ({
  padding: "0",
}));

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  width: "100%",
  gap: "0 12px",
  alignItems: "center",
}));

interface CommonProps {
  attrId: number;
  index?: number;
  control: Control<Schema>;
  isDisabled?: boolean;
  /** Shown in accessible names so repeated lists stay distinguishable. */
  attrName?: string;
}

export const StringAttributeValueField: FC<
  CommonProps & {
    handleClickDeleteListItem?: (index: number) => void;
    multiline?: boolean;
  }
> = ({
  attrId,
  index,
  control,
  handleClickDeleteListItem,
  multiline,
  isDisabled = false,
}) => {
  const { t } = useTranslation();

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
        render={({ field, fieldState: { error, isDirty } }) => (
          <TextField
            {...field}
            variant="standard"
            error={error != null}
            helperText={error?.message}
            fullWidth
            multiline={multiline}
            minRows={multiline === true ? 5 : 1}
            disabled={isDisabled}
            sx={getStagedErrorStyle(!!error, isDirty)}
          />
        )}
      />
      {index !== undefined && handleClickDeleteListItem != null && (
        <IconButton
          data-testid={`delete-row-${attrId}-${index}`}
          aria-label={t("entryForm.array.deleteRow", { row: index + 1 })}
          onClick={() => handleClickDeleteListItem(index)}
        >
          <DeleteOutlineIcon />
        </IconButton>
      )}
    </StyledBox>
  );
};

export const ArrayStringAttributeValueField: FC<CommonProps> = ({
  attrId,
  control,
  attrName,
}) => {
  const { fields, insert, remove, replace } = useFieldArray({
    control,
    name: `attrs.${attrId}.value.asArrayString`,
  });
  const { t } = useTranslation();
  const listId = `array-string-${attrId}`;
  const focusInsertedRow = useInsertedRowFocus(listId);

  const handleInsertListItem = (index: number) => {
    insert(index, { value: "" });
    focusInsertedRow(index);
  };

  // Keep at least one (empty) row. This must not run during render: it
  // updates form state owned by the parent form component. `replace` keeps
  // it idempotent when StrictMode runs the effect twice.
  useEffect(() => {
    if (fields.length === 0) {
      replace([{ value: "" }]);
    }
  }, [fields.length, replace]);

  return (
    <StyledList data-testid={`array-string-list-${attrId}`}>
      {fields.map((field, index) => (
        <Fragment key={field.id}>
          <ListItem disablePadding>
            <InsertBand
              index={index}
              ariaLabel={
                attrName != null
                  ? t("entryForm.array.insertBefore", {
                      name: attrName,
                      row: index + 1,
                    })
                  : t("entryForm.array.insertBeforeNoName", { row: index + 1 })
              }
              onInsert={handleInsertListItem}
              testId={`insert-band-${attrId}-${index}`}
              dense
            />
          </ListItem>
          <ListItem disablePadding data-list-id={listId} data-row-index={index}>
            <StringAttributeValueField
              control={control}
              attrId={attrId}
              index={index}
              handleClickDeleteListItem={remove}
            />
          </ListItem>
        </Fragment>
      ))}
      <ListItem disablePadding>
        <AddRowButton
          onAdd={() => handleInsertListItem(fields.length)}
          label={t("entryForm.array.appendNoName")}
          ariaLabel={
            attrName != null
              ? t("entryForm.array.append", { name: attrName })
              : undefined
          }
          testId={`append-row-${attrId}`}
        />
      </ListItem>
    </StyledList>
  );
};
