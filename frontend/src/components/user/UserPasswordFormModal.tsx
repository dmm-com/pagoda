import { Box, Button, TextField, Modal, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import React, { FC, useMemo, useState } from "react";
import { useHistory } from "react-router-dom";

import { aironeApiClientV2 } from "../../apiclient/AironeApiClientV2";
import { DjangoContext } from "../../services/DjangoContext";

import { loginPath, topPath, usersPath } from "Routes";

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

const PasswordField = styled(Box)(({ theme }) => ({
  marginTop: theme.spacing(4),
  marginBottom: theme.spacing(4),
}));

const PasswordFieldLabel = styled("label")(({ theme }) => ({
  color: "#90A4AE",
}));

const PasswordFieldInput = styled(TextField)(({ theme }) => ({
  width: "100%",
  marginTop: theme.spacing(2),
  marginBottom: theme.spacing(2),
}));

const Buttons = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-end",
}));

interface Props {
  userId: number;
  openModal: boolean;
  onClose: () => void;
}

export const UserPasswordFormModal: FC<Props> = ({
  userId,
  openModal,
  onClose,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [checkPassword, setCheckPassword] = useState("");
  const [isUnmatch, setIsUnmatch] = useState(false);

  const asSuperuser = useMemo(() => {
    return DjangoContext.getInstance()?.user?.isSuperuser ?? false;
  }, []);

  const handleSubmit = async () => {
    if (newPassword != checkPassword) {
      // abort to submit password
      setIsUnmatch(true);
      return;
    }

    try {
      if (asSuperuser) {
        await aironeApiClientV2.updateUserPasswordAsSuperuser(
          userId,
          newPassword,
          checkPassword
        );
      } else {
        await aironeApiClientV2.updateUserPassword(
          userId,
          oldPassword,
          newPassword,
          checkPassword
        );
      }

      if (DjangoContext.getInstance()?.user?.id == userId) {
        history.replace(loginPath());
      } else {
        history.replace(topPath());
        history.replace(usersPath());
      }
    } catch (e) {
      enqueueSnackbar(
        "パスワードリセットに失敗しました。入力項目を見直してください",
        {
          variant: "error",
        }
      );
      // TODO show error causes
    }
  };

  return (
    <StyledModal open={openModal} onClose={onClose}>
      <Paper>
        <Typography variant="h6">パスワード編集</Typography>

        {!asSuperuser && (
          <PasswordField>
            <Box>
              <PasswordFieldLabel>
                今まで使用していたパスワードをご入力ください。
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
              新しいパスワードをご入力ください。
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
              確認のためもう一度、新しいパスワードをご入力ください。
            </PasswordFieldLabel>
          </Box>
          <PasswordFieldInput
            error={isUnmatch}
            variant={"standard"}
            type="password"
            placeholder="Confirm new password"
            value={checkPassword}
            helperText={
              isUnmatch ? "新しいパスワードと、入力内容が一致しません" : ""
            }
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
            保存
          </Button>
          <Button
            type="submit"
            variant="contained"
            color="info"
            onClick={onClose}
            sx={{ m: 1 }}
          >
            キャンセル
          </Button>
        </Buttons>
      </Paper>
    </StyledModal>
  );
};
