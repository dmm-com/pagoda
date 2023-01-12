import { Box, Container, TextField, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

interface Props {
  entries: string;
  setEntries: (entries: string) => void;
}

const SampleBox = styled(Box)(({ theme }) => ({
  width: "100%",
  margin: "80px 0",
  backgroundColor: "#607D8B0A",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
}));

export const CopyForm: FC<Props> = ({ entries, setEntries }) => {
  return (
    <Container>
      <TextField
        sx={{ mt: "64px" }}
        fullWidth
        minRows={2}
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
          (Vm0001、vm0002、…vm006の6エントリを作成する場合）
        </Typography>
        <TextField
          sx={{ my: "16px", width: "95%" }}
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
    </Container>
  );
};
