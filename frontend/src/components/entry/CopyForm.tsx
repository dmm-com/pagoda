import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, TextField, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const SampleBox = styled(Box)({
  width: "100%",
  margin: "80px 0",
  backgroundColor: "#607D8B0A",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
});

const SampleTextField = styled(TextField)({
  margin: "8px 0",
  width: "95%",
});

export interface CopyFormProps {
  entries: string;
  setEntries: (entries: string) => void;
  templateEntry: EntryRetrieve;
}

export const CopyForm: FC<CopyFormProps> = ({
  entries,
  setEntries,
  templateEntry,
}) => {
  return (
    <>
      <Typography>
        {"入力した各行ごとに " +
          templateEntry.name.substring(0, 50) +
          " と同じ属性を持つ別のエントリを作成"}
      </Typography>
      <TextField
        id="copy-name"
        fullWidth
        minRows={6}
        maxRows={15}
        placeholder="コピーするエントリ名"
        multiline
        value={entries}
        onChange={(e) => setEntries(e.target.value)}
      />
      <SampleBox display="flex">
        <Typography variant="h6" mt="24px" color="primary">
          SAMPLE
        </Typography>
        <Typography color="primary">
          (Vm0001、vm0002、…vm006の6エントリを作成する場合)
        </Typography>
        <SampleTextField
          multiline
          disabled
          label="コピーするエントリ名"
          value="vm0001
vm0002
vm0003
vm0004
vm0005
vm0006"
        />
      </SampleBox>
    </>
  );
};
