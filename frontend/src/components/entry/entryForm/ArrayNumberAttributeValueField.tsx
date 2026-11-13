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

export const NumberAttributeValueFieldForArray: FC<
  CommonProps & {
    handleClickDeleteListItem?: (index: number) => void;
  }
> = ({
  attrId,
  index,
  control,
  handleClickDeleteListItem,
  isDisabled = false,
}) => {
  const { t } = useTranslation();

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

export const ArrayNumberAttributeValueField: FC<CommonProps> = ({
  attrId,
  control,
  attrName,
}) => {
  const { fields, insert, remove, replace } = useFieldArray({
    control,
    name: `attrs.${attrId}.value.asArrayNumber`,
  });
  const { t } = useTranslation();
  const listId = `array-number-${attrId}`;
  const focusInsertedRow = useInsertedRowFocus(listId);

  const handleInsertListItem = (index: number) => {
    insert(index, { value: null });
    focusInsertedRow(index);
  };

  // Keep at least one (empty) row. This must not run during render: it
  // updates form state owned by the parent form component. `replace` keeps
  // it idempotent when StrictMode runs the effect twice.
  useEffect(() => {
    if (fields.length === 0) {
      replace([{ value: null }]);
    }
  }, [fields.length, replace]);

  return (
    <StyledList data-testid={`array-number-list-${attrId}`}>
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
            <NumberAttributeValueFieldForArray
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
