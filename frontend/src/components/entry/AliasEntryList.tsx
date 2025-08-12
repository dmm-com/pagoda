import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import { Chip, Stack, TextField } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const StyledTextField = styled(TextField)({
  background: "#F4F4F4",
  "& fieldset": {
    borderColor: "white",
  },
});

interface Props {
  entry: EntryBase;
  handleCreate: (entryId: number, target: HTMLInputElement) => void;
  handleDelete: (id: number) => void;
}

export const AliasEntryList: FC<Props> = ({
  entry,
  handleCreate,
  handleDelete,
}) => {
  const [isEdit, setIsEdit] = React.useState(false);

  return (
    <Stack direction="row" spacing={1} alignItems="center" height="40px">
      {entry.aliases.map((alias) => (
        <Chip
          key={alias.id}
          label={alias.name}
          onDelete={() => handleDelete(alias.id)}
        />
      ))}
      {isEdit ? (
        <StyledTextField
          size="small"
          placeholder="エイリアスを追加"
          onKeyDown={(e) => {
            e.key === "Enter" &&
              handleCreate(entry.id, e.target as HTMLInputElement);
          }}
        />
      ) : (
        <Chip label={<AddIcon />} onClick={() => setIsEdit(true)} />
      )}
    </Stack>
  );
};
