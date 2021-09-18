import PropTypes from "prop-types";
import Typography from "@material-ui/core/Typography";
import Button from "@material-ui/core/Button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@material-ui/core";
import React, { useState } from "react";
import { makeStyles } from "@material-ui/core/styles";
import {
  updateUserPassword,
  updateUserPasswordAsSuperuser,
} from "../../utils/AironeAPIClient";
import { useHistory } from "react-router-dom";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  passwordField: {
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(1),
  },
}));

export function UserPasswordForm({ user, asSuperuser }) {
  const classes = useStyles();
  const history = useHistory();

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [checkPassword, setCheckPassword] = useState("");

  const handleSubmit = (event) => {
    if (asSuperuser) {
      updateUserPasswordAsSuperuser(user.id, newPassword, checkPassword).then(
        () => history.replace("/new-ui/users")
      );
    } else {
      updateUserPassword(user.id, oldPassword, newPassword, checkPassword).then(
        () => history.replace("/new-ui/users")
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
            <TableHead>名前</TableHead>
            <TableCell>
              <Typography>{user.username}</Typography>
            </TableCell>
          </TableRow>
          <TableRow>
            <TableHead>パスワード</TableHead>
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
}

UserPasswordForm.propTypes = {
  user: PropTypes.objectOf({
    id: PropTypes.number.isRequired,
    username: PropTypes.string.isRequired,
  }),
  asSuperuser: PropTypes.bool.isRequired,
};
