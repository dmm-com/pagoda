import { Box, Button, TextField } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import { FC, useMemo, useState } from "react";

import { aironeApiClient } from "../../repository/AironeApiClient";
import { AironeModal } from "../common/AironeModal";

import { useTranslation } from "hooks/useTranslation";
import { ServerContext } from "services/ServerContext";

const PasswordField = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(4),
  marginBottom: theme.spacing(4),
}));

const PasswordFieldLabel = styled("label")(({}) => ({
  color: "#90A4AE",
}));

const PasswordFieldInput = styled(TextField)(({ theme }) => ({
  width: "100%",
  marginTop: theme.spacing(2),
  marginBottom: theme.spacing(2),
}));

const Buttons = styled(Box)(({}) => ({
  display: "flex",
  justifyContent: "flex-end",
}));

interface Props {
  userId: number;
  openModal: boolean;
  onClose: () => void;
  onSubmitSuccess?: () => void;
}

export const UserPasswordFormModal: FC<Props> = ({
  userId,
  openModal,
  onClose,
  onSubmitSuccess,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();
  // const navigate = useNavigate();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [checkPassword, setCheckPassword] = useState("");
  const [isUnmatch, setIsUnmatch] = useState(false);

  const asSuperuser = useMemo(() => {
    return ServerContext.getInstance()?.user?.isSuperuser ?? false;
  }, []);

  const handleSubmit = async () => {
    if (newPassword != checkPassword) {
      // abort to submit password
      setIsUnmatch(true);
      return;
    }

    try {
      if (asSuperuser) {
        await aironeApiClient.updateUserPasswordAsSuperuser(
          userId,
          newPassword,
          checkPassword,
        );
      } else {
        await aironeApiClient.updateUserPassword(
          userId,
          oldPassword,
          newPassword,
          checkPassword,
        );
      }
      onSubmitSuccess?.();
    } catch (e) {
      enqueueSnackbar(t("user.passwordFormModal.resetFailure"), {
        variant: "error",
      });
      // TODO show error causes
    }
  };

  return (
    <AironeModal
      title={t("user.passwordFormModal.title")}
      open={openModal}
      onClose={onClose}
    >
      {!asSuperuser && (
        <PasswordField>
          <Box>
            <PasswordFieldLabel>
              {t("user.passwordFormModal.oldPasswordLabel")}
            </PasswordFieldLabel>
          </Box>
          <PasswordFieldInput
            variant={"standard"}
            type="password"
            placeholder="Old password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
          />
        </PasswordField>
      )}

      <PasswordField>
        <Box>
          <PasswordFieldLabel>
            {t("user.passwordFormModal.newPasswordLabel")}
          </PasswordFieldLabel>
        </Box>
        <PasswordFieldInput
          variant={"standard"}
          type="password"
          placeholder="New password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
      </PasswordField>
      <PasswordField>
        <Box>
          <PasswordFieldLabel>
            {t("user.passwordFormModal.confirmPasswordLabel")}
          </PasswordFieldLabel>
        </Box>
        <PasswordFieldInput
          error={isUnmatch}
          variant={"standard"}
          type="password"
          placeholder="Confirm new password"
          value={checkPassword}
          helperText={isUnmatch ? t("user.passwordFormModal.mismatch") : ""}
          onChange={(e) => {
            setCheckPassword(e.target.value);
            setIsUnmatch(false);
          }}
        />
      </PasswordField>

      <Buttons>
        <Button
          disabled={
            (asSuperuser && (!newPassword.length || !checkPassword.length)) ||
            (!asSuperuser &&
              (!oldPassword.length ||
                !newPassword.length ||
                !checkPassword.length))
          }
          type="submit"
          variant="contained"
          color="secondary"
          onClick={handleSubmit}
          sx={{ m: 1 }}
        >
          {t("common.save")}
        </Button>
        <Button
          type="submit"
          variant="contained"
          color="info"
          onClick={onClose}
          sx={{ m: 1 }}
        >
          {t("common.cancel")}
        </Button>
      </Buttons>
    </AironeModal>
  );
};
