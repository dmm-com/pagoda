import { UserRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, Button, Input, Modal, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import { FC, useCallback, useState } from "react";

import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

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
  user: UserRetrieve;
  openModal: boolean;
  closeModal: () => void;
}

export const ChangeUserAuthModal: FC<Props> = ({
  user,
  openModal,
  closeModal,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();

  const [ldapPassword, setLdapPassword] = useState("");

  const handleSubmit = useCallback(async () => {
    try {
      await aironeApiClient.updateUserAuth(user.id, ldapPassword);
      enqueueSnackbar(t("user.changeAuthModal.updateSuccess"), {
        variant: "success",
      });
      closeModal();
    } catch (e) {
      enqueueSnackbar(t("user.changeAuthModal.updateFailure"), {
        variant: "error",
      });
    }
  }, [user, ldapPassword, closeModal, enqueueSnackbar, t]);

  return (
    <StyledModal open={openModal} onClose={closeModal}>
      <Paper>
        <Typography variant={"h6"} my="8px">
          {t("user.changeAuthModal.title")}
        </Typography>
        <Typography variant={"caption"} my="4px">
          {t("user.changeAuthModal.description", { username: user.username })}
        </Typography>
        <Input
          placeholder="Password for LDAP user"
          value={ldapPassword}
          onChange={(e) => setLdapPassword(e.target.value)}
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
      </Paper>
    </StyledModal>
  );
};
