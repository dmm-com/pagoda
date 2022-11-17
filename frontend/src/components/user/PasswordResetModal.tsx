import { Box, Button, Input, Modal, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import { useSnackbar } from "notistack";
import React, { FC, useCallback, useState } from "react";

import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";

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
  openModal: boolean;
  closeModal: () => void;
}

export const PasswordResetModal: FC<Props> = ({ openModal, closeModal }) => {
  const classes = useStyles();
  const { enqueueSnackbar } = useSnackbar();

  const [username, setUsername] = useState("");

  const handleSubmit = useCallback(async () => {
    try {
      await aironeApiClientV2.resetPassword(username);
      enqueueSnackbar("パスワードリセットメールの送信に成功しました", {
        variant: "success",
      });
      closeModal();
    } catch (e) {
      enqueueSnackbar("パスワードリセットメールの送信に失敗しました", {
        variant: "error",
      });
      console.log(e);
    }
  }, [username, closeModal]);

  return (
    <Modal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      className={classes.modal}
      open={openModal}
      onClose={closeModal}
    >
      <Box className={classes.paper}>
        <Typography variant={"h6"} my="8px">
          パスワードリセット
        </Typography>
        <Typography variant={"caption"} my="4px">
          パスワードリセットをメールで案内します。ユーザ名を入力してください。
        </Typography>
        <Input
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <Box display="flex" flexDirection="column">
          <Box display="flex" justifyContent="flex-end">
            <Button
              type="submit"
              variant="contained"
              color="secondary"
              onClick={handleSubmit}
              sx={{ m: "4px" }}
            >
              送信
            </Button>
            <Button
              variant="contained"
              color="info"
              onClick={closeModal}
              sx={{ m: "4px" }}
            >
              キャンセル
            </Button>
          </Box>
        </Box>
      </Box>
    </Modal>
  );
};
