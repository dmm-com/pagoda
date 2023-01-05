import { Box, Modal, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { ImportForm } from "components/common/ImportForm";

const useStyles = makeStyles<Theme>((theme) => ({
  modal: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  paper: {
    display: "flex",
    flexDirection: "column",
    backgroundColor: theme.palette.background.paper,
    border: "2px solid #000",
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 3, 1),
    width: "50%",
  },
}));

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const EntryImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const classes = useStyles();

  return (
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.modal}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <Box className={classes.paper}>
        <Typography variant={"h6"} my="8px">
          エントリのインポート
        </Typography>
        <Typography variant={"body2"} my="4px">
          インポートするファイルを選択してください。
        </Typography>
        <Typography variant={"caption"} my="4px">
          ※CSV形式のファイルは選択できません。
        </Typography>
        <ImportForm
          handleImport={(data: string | ArrayBuffer) =>
            aironeApiClientV2.importEntries(data)
          }
          handleCancel={closeImportModal}
        />
      </Box>
    </Modal>
  );
};
