import {
  Box,
  Button,
  Container,
  TextareaAutosize,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { entityEntriesPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";

interface Props {
  entityId: number;
  entryId: number;
}

const useStyles = makeStyles<Theme>((theme) => ({
  sampleBox: {
    padding: "10px 50px",
  },
}));

export const CopyForm: FC<Props> = ({ entityId, entryId }) => {
  const classes = useStyles();
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();

  // newline delimited string value, not string[]
  const [entries, setEntries] = useState<string>("");

  const handleCopy = async () => {
    await aironeApiClientV2
      .copyEntry(entryId, entries.split("\n"))
      .then((resp) => {
        enqueueSnackbar("エントリコピーのジョブ登録が成功しました", {
          variant: "success",
        });
        history.replace(entityEntriesPath(entityId));
      })
      .catch((error) => {
        enqueueSnackbar("エントリコピーのジョブ登録が失敗しました", {
          variant: "error",
        });
      });
  };

  const handleCancel = () => {
    history.goBack();
  };

  return (
    <Container>
      <TextareaAutosize
        minRows={2}
        placeholder="コピーするエントリ名"
        style={{ width: "100%", marginTop: 60 }}
        value={entries}
        onChange={(e) => setEntries(e.target.value)}
      />
      <Box display="flex" justifyContent="center" mt="16px">
        <Box mx="8px">
          <Button
            type="submit"
            variant="contained"
            color="secondary"
            onClick={handleCopy}
          >
            コピー
          </Button>
        </Box>
        <Box mx="8px">
          <Button variant="outlined" onClick={handleCancel}>
            キャンセル
          </Button>
        </Box>
      </Box>
      <Box mt="72px" bgcolor="#607D8B0A" width="100%">
        <Box sx={{ paddingTop: "24px" }}>
          <Typography variant="h6" textAlign="center" color="primary">
            SAMPLE
          </Typography>
          <Typography textAlign="center" color="primary">
            (Vm0001、vm0002、…vm006の6エントリを作成する場合）
          </Typography>
        </Box>
        <Box paddingX="16px">
          <Box position="relative" height="200px" mt="30px" width="100%">
            <Typography
              position="absolute"
              left="16px"
              zIndex={1}
              bgcolor="#FAFBFB"
            >
              コピーするエントリ名
            </Typography>
            <Box
              bgcolor="white"
              position="absolute"
              top="16px"
              width="100%"
              border={0.5}
            >
              <pre className={classes.sampleBox}>
                {`vm0001
vm0002
vm0003
vm0004
vm0005
vm0006`}
              </pre>
            </Box>
          </Box>
        </Box>
      </Box>
    </Container>
  );
};
function enqueueSnackbar(arg0: string, arg1: { variant: string }) {
  throw new Error("Function not implemented.");
}
