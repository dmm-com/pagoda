import { Box, Button, Input } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useCallback, useState } from "react";

import { AironeModal } from "../common/AironeModal";

import { aironeApiClientV2 } from "repository/AironeApiClientV2";

interface Props {
  openModal: boolean;
  closeModal: () => void;
}

export const PasswordResetModal: FC<Props> = ({ openModal, closeModal }) => {
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
    }
  }, [username, closeModal]);

  return (
    <AironeModal
      title={"パスワードリセット"}
      description={
        "パスワードリセットをメールで案内します。ユーザ名を入力してください。"
      }
      open={openModal}
      onClose={closeModal}
    >
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
    </AironeModal>
  );
};
