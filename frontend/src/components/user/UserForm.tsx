import {
  Box,
  Button,
  Checkbox,
  Input,
  Link,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { usersPath } from "Routes";
import {
  createUser,
  refreshAccessToken,
  updateUser,
} from "utils/AironeAPIClient";
import { DjangoContext } from "utils/DjangoContext";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  tokenLifetime: {
    display: "flex",
  },
}));

interface Props {
  user?: {
    id: number;
    username: string;
    email: string;
    is_superuser: boolean;
    token?: string;
    token_lifetime?: number;
    token_created?: string;
    token_expire?: string;
  };
}

export const UserForm: FC<Props> = ({ user }) => {
  const classes = useStyles();
  const history = useHistory();

  const isCreateMode = user?.id === undefined;
  const [username, setUsername] = useState(user?.username ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [password, setPassword] = useState(isCreateMode ? "" : undefined);
  const [isSuperuser, setIsSuperuser] = useState<boolean>(
    user?.is_superuser ?? false
  );
  const [tokenLifetime, setTokenLifetime] = useState(user?.token_lifetime);

  const djangoContext = DjangoContext.getInstance();

  const handleSubmit = (event) => {
    if (isCreateMode) {
      createUser(username, email, password, isSuperuser, tokenLifetime).then(
        () => history.replace(usersPath())
      );
    } else {
      updateUser(user.id, username, email, isSuperuser, tokenLifetime).then(
        () => history.replace(usersPath())
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
              {djangoContext.user.isSuperuser ? (
                <Input
                  type="text"
                  name="name"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
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
              {djangoContext.user.isSuperuser ? (
                <Input
                  type="email"
                  name="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              ) : (
                <Typography>{email}</Typography>
              )}
            </TableCell>
          </TableRow>
          {djangoContext.user?.isSuperuser ? (
            <TableRow>
              <TableCell>
                <Typography>管理者権限を付与</Typography>
              </TableCell>
              <TableCell>
                <Checkbox
                  name="is_superuser"
                  checked={isSuperuser}
                  onChange={(e) => setIsSuperuser(e.target.checked)}
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
                <Input
                  type="password"
                  name="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
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
                    <Link id="access_token">{user.token}</Link>
                    <Button
                      type="button"
                      id="refresh_token"
                      className="btn btn-primary btn-sm"
                      onChange={handleRefreshAccessToken}
                    >
                      Refresh
                    </Button>
                  </TableCell>
                </TableRow>
              ) : null}
              <TableRow>
                <TableCell>
                  <Typography>AccessToken の有効期間 [sec]</Typography>
                </TableCell>
                <TableCell>
                  <Box className={classes.tokenLifetime}>
                    <Input
                      type="text"
                      name="token_lifetime"
                      value={tokenLifetime}
                      onChange={(e) => setTokenLifetime(Number(e.target.value))}
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
};
