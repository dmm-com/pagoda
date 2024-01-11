import { Box, Button, Input } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";

import { aironeApiClientV2 } from "../../repository/AironeApiClientV2";
import { AironeModal } from "../common/AironeModal";

interface Props {
  openModal: boolean;
  closeModal: () => void;
  uidb64: string;
  token: string;
}

export const PasswordResetConfirmModal: FC<Props> = ({
  openModal,
  closeModal,
  uidb64,
  token,
}) => {
  const { enqueueSnackbar } = useSnackbar();

  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const handleSubmit = async () => {
    try {
      await aironeApiClientV2.confirmResetPassword(
        uidb64,
        token,
        password,
        passwordConfirmation
      );
      enqueueSnackbar("パスワードリセットに成功しました", {
        variant: "success",
      });
      closeModal();
    } catch {
      enqueueSnackbar("パスワードリセットに失敗しました", {
        variant: "error",
      });
    }
  };

  return (
    <AironeModal
      title={"パスワードリセット"}
      description={"新しいパスワードを入力してください。"}
      open={openModal}
      onClose={closeModal}
    >
      <Input
        type="password"
        placeholder="New password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <Input
        type="password"
        placeholder="Re-type password"
        value={passwordConfirmation}
        onChange={(e) => setPasswordConfirmation(e.target.value)}
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
