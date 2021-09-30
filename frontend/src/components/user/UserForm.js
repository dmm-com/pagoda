import {
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@material-ui/core";
import { makeStyles } from "@material-ui/core/styles";
import PropTypes from "prop-types";
import React, { useState } from "react";
import { useHistory } from "react-router-dom";

import {
  createUser,
  refreshAccessToken,
  updateUser,
} from "../../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  tokenLifetime: {
    display: "flex",
  },
}));

export function UserForm({ user }) {
  const classes = useStyles();
  const history = useHistory();

  const isCreateMode = user?.id === undefined;
  const [username, setUsername] = useState(user?.username ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [password, setPassword] = useState(isCreateMode ? "" : undefined);
  const [isSuperuser, setIsSuperuser] = useState(user?.is_superuser ?? false);
  const [tokenLifetime, setTokenLifetime] = useState(user?.token_lifetime);

  const handleSubmit = (event) => {
    if (isCreateMode) {
      createUser(username, email, password, isSuperuser, tokenLifetime).then(
        () => history.replace("/new-ui/users")
      );
    } else {
      updateUser(user.id, username, email, isSuperuser, tokenLifetime).then(
        () => history.replace("/new-ui/users")
      );
    }
    event.preventDefault();
  };

  const handleRefreshAccessToken = () => {
    refreshAccessToken().then(() => history.go(0));
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
              {django_context.user.is_superuser ? (
                <input
                  type="text"
                  name="name"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required="required"
                />
              ) : (
                <Typography>{username}</Typography>
              )}
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography>メールアドレス</Typography>
            </TableCell>
            <TableCell>
              {django_context.user.is_superuser ? (
                <input
                  type="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required="required"
                />
              ) : (
                <Typography>{email}</Typography>
              )}
            </TableCell>
          </TableRow>
          {django_context.user.is_superuser ? (
            <TableRow>
              <TableCell>
                <Typography>管理者権限を付与</Typography>
              </TableCell>
              <TableCell>
                <input
                  type="checkbox"
                  name="is_superuser"
                  value={isSuperuser}
                  onChange={(e) => setIsSuperuser(e.target.value)}
                />
              </TableCell>
            </TableRow>
          ) : null}
          {isCreateMode ? (
            <TableRow>
              <TableCell>
                <Typography>パスワード</Typography>
              </TableCell>
              <TableCell>
                <input
                  type="password"
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required="required"
                />
              </TableCell>
            </TableRow>
          ) : (
            <>
              {user?.token !== undefined && user?.token !== "" ? (
                <TableRow>
                  <TableCell>
                    <Typography>AccessToken</Typography>
                  </TableCell>
                  <TableCell>
                    <p id="access_token">{user.token}</p>
                    <button
                      type="button"
                      id="refresh_token"
                      className="btn btn-primary btn-sm"
                      onChange={handleRefreshAccessToken}
                    >
                      Refresh
                    </button>
                  </TableCell>
                </TableRow>
              ) : null}
              <TableRow>
                <TableCell>
                  <Typography>AccessToken の有効期間 [sec]</Typography>
                </TableCell>
                <TableCell>
                  <Box className={classes.tokenLifetime}>
                    <input
                      type="text"
                      name="token_lifetime"
                      value={tokenLifetime}
                      onChange={(e) => setTokenLifetime(e.target.value)}
                    />
                    <Typography>
                      0 ~ 10^8
                      の範囲の整数を指定してください。0を入力した場合は期限は無期限になります
                    </Typography>
                  </Box>
                  {user?.token_created !== undefined && (
                    <Typography>作成日：{user.token_created}</Typography>
                  )}
                  {user?.token_expire !== undefined && (
                    <Typography>有効期限：{user.token_expire}</Typography>
                  )}
                </TableCell>
              </TableRow>
            </>
          )}
        </TableBody>
      </Table>
    </form>
  );
}

UserForm.propTypes = {
  user: PropTypes.shape({
    id: PropTypes.number.isRequired,
    username: PropTypes.string.isRequired,
    email: PropTypes.string.isRequired,
    is_superuser: PropTypes.bool,
    token: PropTypes.string,
    token_lifetime: PropTypes.number,
    token_created: PropTypes.string,
    token_expire: PropTypes.string,
  }),
};
