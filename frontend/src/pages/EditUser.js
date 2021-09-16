import React, { useEffect, useState } from "react";
import { makeStyles } from "@material-ui/core/styles";
import Button from "@material-ui/core/Button";
import { Link, useParams } from "react-router-dom";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import { getUser } from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function EditUser({}) {
  const classes = useStyles();
  const { userId } = useParams();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [token, setToken] = useState("");
  const [tokenLifetime, setTokenLifetime] = useState(0);
  const [tokenExpire, setTokenExpire] = useState("");

  useEffect(() => {
    if (userId) {
      getUser(userId)
        .then((resp) => resp.json())
        .then((data) => {
          setName(data.username);
          setEmail(data.email);
          setIsSuperuser(data.is_superuser);
          setToken(data.token);
          setTokenLifetime(data.token_lifetime);
          setTokenExpire(data.token_expire);
        });
    }
  }, []);

  const onSubmit = (event) => {
    event.preventDefault();
  };

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to="/new-ui/users">
          ユーザ管理
        </Typography>
        <Typography color="textPrimary">ユーザ編集</Typography>
      </AironeBreadcrumbs>

      {/* TODO split it as an another component */}
      <form onSubmit={onSubmit}>
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
              <TableCell>名前</TableCell>
              <TableCell>
                {django_context.user.is_superuser ? (
                  <input
                    type="text"
                    name="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required="required"
                  />
                ) : (
                  <Typography>{name}</Typography>
                )}
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>メールアドレス</TableCell>
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
            {django_context.user.is_superuser && (
              <TableRow>
                <TableCell>管理者権限を付与</TableCell>
                <TableCell>
                  <input
                    type="checkbox"
                    name="is_superuser"
                    value={isSuperuser}
                    onChange={(e) => setIsSuperuser(e.target.checked)}
                  />
                </TableCell>
              </TableRow>
            )}
            {token && (
              <TableRow>
                <TableCell>AccessToken</TableCell>
                <TableCell>
                  <p id="access_token">{token}</p>
                  <button
                    type="button"
                    id="refresh_token"
                    className="btn btn-primary btn-sm"
                  >
                    Refresh
                  </button>
                </TableCell>
              </TableRow>
            )}
            <TableRow>
              <TableCell>AccessTokenの有効期間[sec]</TableCell>
              <TableCell>
                <p>
                  <input
                    type="text"
                    name="token_lifetime"
                    value={tokenLifetime}
                    onChange={(e) => setTokenLifetime(e.target.value)}
                  />
                  (0 ~ 10^8 の範囲の整数を指定してください(0
                  を入力した場合は期限は無期限になります))
                </p>
                有効期限：{tokenExpire}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </form>
    </div>
  );
}
