import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { importUsersPath, newUserPath, topPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { CreateButton } from "../components/common/CreateButton.tsx";
import { UserList } from "../components/user/UserList.tsx";
import { downloadExportedUsers, getUsers } from "../utils/AironeAPIClient.ts";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function User({}) {
  const classes = useStyles();

  const users = useAsync(async () => {
    const resp = await getUsers();
    const data = await resp.json();

    return django_context.user.is_superuser
      ? data
      : data.filter((d) => d.id === django_context.user.id);
  });

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ユーザ管理</Typography>
      </AironeBreadcrumbs>

      <div className="row">
        <div className="col">
          <div className="float-left">
            <CreateButton to={newUserPath()}>新規作成</CreateButton>
            <Button
              className={classes.button}
              variant="outlined"
              color="secondary"
              onClick={() => downloadExportedUsers("user.yaml")}
            >
              エクスポート
            </Button>
            <Button
              className={classes.button}
              variant="outlined"
              color="secondary"
              component={Link}
              to={importUsersPath()}
            >
              インポート
            </Button>
          </div>
          <div className="float-right"></div>
        </div>
      </div>

      {!users.loading && <UserList users={users.value} />}
    </div>
  );
}
