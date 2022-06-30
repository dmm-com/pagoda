import { Box, Container, TextField, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

interface Props {
  entries: string;
  setEntries: (entries: string) => void;
}

const useStyles = makeStyles<Theme>((theme) => ({
  sampleBox: {
    width: "100%",
    margin: "80px 0",
    backgroundColor: "#607D8B0A",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
}));

export const CopyForm: FC<Props> = ({ entries, setEntries }) => {
  const classes = useStyles();

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
      <Box display="flex" className={classes.sampleBox}>
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
      </Box>
    </Container>
  );
};
