import { UserRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, Button, Input, Modal, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import React, { FC, useCallback, useState } from "react";

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

  const [ldapPassword, setLdapPassword] = useState("");

  const handleSubmit = useCallback(async () => {
    try {
      await aironeApiClient.updateUserAuth(user.id, ldapPassword);
      enqueueSnackbar("認証方法の変更に成功しました", {
        variant: "success",
      });
      closeModal();
    } catch (e) {
      enqueueSnackbar("認証方法の変更に失敗しました", {
        variant: "error",
      });
    }
  }, [user, ldapPassword, closeModal]);

  return (
    <StyledModal open={openModal} onClose={closeModal}>
      <Paper>
        <Typography variant={"h6"} my="8px">
          LDAP への認証方法の変更
        </Typography>
        <Typography variant={"caption"} my="4px">
          認証を LDAP のパスワードで行うことができます。（注：ユーザ &quot;
          {user.username}&quot; が LDAPに登録されていない場合は変更できません）
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
