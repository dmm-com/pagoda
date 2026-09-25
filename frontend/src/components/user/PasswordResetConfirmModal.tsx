import { Box, Button, Input } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useState } from "react";

import { aironeApiClient } from "../../repository/AironeApiClient";
import { AironeModal } from "../common/AironeModal";

import { useTranslation } from "hooks/useTranslation";

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
  const { t } = useTranslation();

  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const handleSubmit = async () => {
    try {
      await aironeApiClient.confirmResetPassword(
        uidb64,
        token,
        password,
        passwordConfirmation,
      );
      enqueueSnackbar(t("user.passwordResetConfirmModal.resetSuccess"), {
        variant: "success",
      });
      closeModal();
    } catch {
      enqueueSnackbar(t("user.passwordResetConfirmModal.resetFailure"), {
        variant: "error",
      });
    }
  };

  return (
    <AironeModal
      title={t("user.passwordResetConfirmModal.title")}
      description={t("user.passwordResetConfirmModal.description")}
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
            {t("common.submit")}
          </Button>
          <Button
            variant="contained"
            color="info"
            onClick={closeModal}
            sx={{ m: "4px" }}
          >
            {t("common.cancel")}
          </Button>
        </Box>
      </Box>
    </AironeModal>
  );
};
