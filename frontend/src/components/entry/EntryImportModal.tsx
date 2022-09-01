import { Box, Modal, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { entitiesPath } from "Routes";
import { ImportForm } from "components/common/ImportForm";
import { importEntries } from "utils/AironeAPIClient";

const useStyles = makeStyles<Theme>((theme) => ({
  modal: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  paper: {
    display: "flex",
    backgroundColor: theme.palette.background.paper,
    border: "2px solid #000",
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 4, 3),
    width: "50%",
  },
}));

interface Props {
  openImportModal: boolean;
}

export const EntryImportModal: FC<Props> = ({ openImportModal }) => {
  const classes = useStyles();

  return (
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.modal}
      open={openImportModal}
    >
      <Box className={classes.paper}>
        <Typography variant={"h6"}>エントリのインポート</Typography>
        <Typography variant={"caption"}>
          インポートするファイルを選択してください。
        </Typography>

        <ImportForm
          importFunc={aironeApiClientV2.importEntries}
          redirectPath={entitiesPath()}
        />
      </Box>
    </Modal>
  );
};
