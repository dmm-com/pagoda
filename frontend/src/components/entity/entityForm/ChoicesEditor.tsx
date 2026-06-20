import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  Button,
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { FC } from "react";
import { Control, Controller, useFieldArray, useWatch } from "react-hook-form";

import { Schema } from "./EntityFormSchema";

interface Props {
  control: Control<Schema>;
  index: number;
  disabled?: boolean;
}

export const ChoicesEditor: FC<Props> = ({
  control,
  index,
  disabled = false,
}) => {
  const { fields, append, remove } = useFieldArray({
    control,
    name: `attrs.${index}.choices` as const,
  });

  const choicesInUse =
    useWatch({
      control,
      name: `attrs.${index}.choicesInUse` as const,
    }) ?? [];

  // Watch the live choices values so the "in use" disable state stays in sync
  // with what the user is currently typing.
  const watchedChoices =
    useWatch({
      control,
      name: `attrs.${index}.choices` as const,
    }) ?? [];

  const handleAppend = () => append({ value: "", label: "" });

  return (
    <Box>
      <Typography variant="caption" color="textSecondary">
        選択肢 (value: 内部識別子 / label: 表示名)
      </Typography>
      <Stack spacing={1} mt={0.5}>
        {fields.map((field, i) => {
          const currentValue = watchedChoices[i]?.value ?? "";
          const isUsed = choicesInUse.includes(currentValue);
          return (
            <Stack
              direction="row"
              spacing={1}
              key={field.id}
              alignItems="center"
            >
              <Controller
                name={`attrs.${index}.choices.${i}.value` as const}
                control={control}
                render={({ field: f, fieldState: { error } }) => (
                  <TextField
                    {...f}
                    placeholder="value"
                    size="small"
                    disabled={disabled || isUsed}
                    error={error != null}
                    helperText={error?.message}
                  />
                )}
              />
              <Controller
                name={`attrs.${index}.choices.${i}.label` as const}
                control={control}
                render={({ field: f, fieldState: { error } }) => (
                  <TextField
                    {...f}
                    placeholder="label"
                    size="small"
                    disabled={disabled}
                    error={error != null}
                    helperText={error?.message}
                  />
                )}
              />
              <Tooltip
                title={
                  isUsed
                    ? "この選択肢は既存のアイテムで使用中のため削除できません"
                    : ""
                }
              >
                <span>
                  <IconButton
                    aria-label="delete-choice"
                    onClick={() => remove(i)}
                    disabled={disabled || isUsed}
                  >
                    <DeleteOutlineIcon />
                  </IconButton>
                </span>
              </Tooltip>
            </Stack>
          );
        })}
      </Stack>
      <Button
        startIcon={<AddIcon />}
        size="small"
        onClick={handleAppend}
        disabled={disabled}
        sx={{ mt: 1 }}
      >
        選択肢を追加
      </Button>
    </Box>
  );
};
