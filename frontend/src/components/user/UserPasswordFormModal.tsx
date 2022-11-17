import { Box, Button, Input, Modal, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useMemo, useState } from "react";
import { useHistory } from "react-router-dom";

import { DjangoContext } from "../../utils/DjangoContext";

import { topPath, usersPath } from "Routes";
import {
  updateUserPassword,
  updateUserPasswordAsSuperuser,
} from "utils/AironeAPIClient";

const useStyles = makeStyles<Theme>((theme) => ({
  modal: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  paper: {
    backgroundColor: theme.palette.background.paper,
    border: "1px solid #000",
    boxShadow: theme.shadows[5],
    padding: theme.spacing(2, 4, 2),
    width: "50%",
  },
  passwordField: {
    marginTop: theme.spacing(4),
    marginBottom: theme.spacing(4),
  },
  passwordFieldLabel: {
    color: "#90A4AE",
  },
  passwordFieldInput: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  buttons: {
    display: "flex",
    justifyContent: "flex-end",
  },
}));

interface Props {
  userId: number;
  openModal: boolean;
  onClose: () => void;
  onSubmit: () => void;
}

export const UserPasswordFormModal: FC<Props> = ({
  userId,
  openModal,
  onClose,
  onSubmit,
}) => {
  const classes = useStyles();
  const history = useHistory();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [checkPassword, setCheckPassword] = useState("");

  const asSuperuser = useMemo(() => {
    return DjangoContext.getInstance().user.isSuperuser;
  }, []);

  const handleSubmit = async () => {
    if (asSuperuser) {
      await updateUserPasswordAsSuperuser(userId, newPassword, checkPassword);
    } else {
      await updateUserPassword(userId, oldPassword, newPassword, checkPassword);
    }

    // This calls event handler, which is specified by caller component
    onSubmit();

    history.replace(topPath());
    history.replace(usersPath());
  };

  return (
    <Modal className={classes.modal} open={openModal} onClose={onClose}>
      <Box className={classes.paper}>
        <Typography variant="h6">パスワード編集</Typography>

        {!asSuperuser && (
          <Box className={classes.passwordField}>
            <Box>
              <label className={classes.passwordFieldLabel}>
                今まで使用していたパスワードをご入力ください。
              </label>
            </Box>
            <Input
              className={classes.passwordFieldInput}
              type="password"
              placeholder="Old password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
            />
          </Box>
        )}

        <Box className={classes.passwordField}>
          <Box>
            <label className={classes.passwordFieldLabel}>
              新しいパスワードをご入力ください。
            </label>
          </Box>
          <Input
            className={classes.passwordFieldInput}
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </Box>
        <Box className={classes.passwordField}>
          <Box>
            <label className={classes.passwordFieldLabel}>
              確認のためもう一度、新しいパスワードをご入力ください。
            </label>
          </Box>
          <Input
            className={classes.passwordFieldInput}
            type="password"
            placeholder="Confirm new password"
            value={checkPassword}
            onChange={(e) => setCheckPassword(e.target.value)}
          />
        </Box>

        <Box className={classes.buttons}>
          <Button
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
        </Box>
      </Box>
    </Modal>
  );
};
