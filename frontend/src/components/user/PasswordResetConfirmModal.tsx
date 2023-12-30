import { Box, Button, Input, Modal, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";

import { aironeApiClient } from "../../repository/AironeApiClient";

const StyledModal = styled(Modal)(({}) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
}));

const Paper = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  backgroundColor: theme.palette.background.paper,
  border: "2px solid #000",
  boxShadow: theme.shadows[5],
  padding: theme.spacing(2, 3, 1),
  width: "50%",
}));

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
      await aironeApiClient.confirmResetPassword(
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
    <StyledModal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      open={openModal}
    >
      <Paper>
        <Typography variant={"h6"} my="8px">
          パスワードリセット
        </Typography>
        <Typography variant={"caption"} my="4px">
          新しいパスワードを入力してください。
        </Typography>
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
      </Paper>
    </StyledModal>
  );
};
