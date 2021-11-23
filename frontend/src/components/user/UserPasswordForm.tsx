import { Table, TableBody, TableCell, TableRow } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { usersPath } from "../../Routes";
import {
  updateUserPassword,
  updateUserPasswordAsSuperuser,
} from "../../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  passwordField: {
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(1),
  },
}));

interface Props {
  user: {
    id: number;
    username: string;
  };
  asSuperuser: boolean;
}

export const UserPasswordForm: FC<Props> = ({ user, asSuperuser = false }) => {
  const classes = useStyles();
  const history = useHistory();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [checkPassword, setCheckPassword] = useState("");

  const handleSubmit = (event) => {
    if (asSuperuser) {
      updateUserPasswordAsSuperuser(user.id, newPassword, checkPassword).then(
        () => history.replace(usersPath())
      );
    } else {
      updateUserPassword(user.id, oldPassword, newPassword, checkPassword).then(
        () => history.replace(usersPath())
      );
    }

    event.preventDefault();
  };

  return (
    <form onSubmit={handleSubmit}>
      <Typography>ユーザ編集</Typography>
      <Button
        className={classes.button}
        type="submit"
        variant="contained"
        color="secondary"
      >
        保存
      </Button>
      <Table className="table table-bordered">
        <TableBody>
          <TableRow>
            <TableCell>
              <Typography>名前</Typography>
            </TableCell>
            <TableCell>
              <Typography>{user.username}</Typography>
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography>パスワード</Typography>
            </TableCell>
            <TableCell>
              {!asSuperuser && (
                <div className={classes.passwordField}>
                  <dt>
                    <label htmlFor="new_password">Old password</label>
                  </dt>
                  <input
                    type="password"
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                  />
                </div>
              )}
              <div className={classes.passwordField}>
                <dt>
                  <label htmlFor="new_password">New password</label>
                </dt>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div className={classes.passwordField}>
                <dt>
                  <label htmlFor="chk_password">Confirm new password</label>
                </dt>
                <input
                  type="password"
                  value={checkPassword}
                  onChange={(e) => setCheckPassword(e.target.value)}
                />
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </form>
  );
};
