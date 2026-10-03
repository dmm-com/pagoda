import { Box, Button, Input } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useCallback, useState } from "react";

import { AironeModal } from "../common/AironeModal";

import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  openModal: boolean;
  closeModal: () => void;
}

export const PasswordResetModal: FC<Props> = ({ openModal, closeModal }) => {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();

  const [username, setUsername] = useState("");

  const handleSubmit = useCallback(async () => {
    try {
      await aironeApiClient.resetPassword(username);
      enqueueSnackbar(t("user.passwordResetModal.sendSuccess"), {
        variant: "success",
      });
      closeModal();
    } catch (e) {
      enqueueSnackbar(t("user.passwordResetModal.sendFailure"), {
        variant: "error",
      });
    }
  }, [username, closeModal, enqueueSnackbar, t]);

  return (
    <AironeModal
      title={t("user.passwordResetModal.title")}
      description={t("user.passwordResetModal.description")}
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
