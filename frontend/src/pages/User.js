import { Box } from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { importUsersPath, newUserPath, topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { CreateButton } from "../components/common/CreateButton";
import { UserList } from "../components/user/UserList";
import { downloadExportedUsers, getUsers } from "../utils/AironeAPIClient";

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
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ユーザ管理</Typography>
      </AironeBreadcrumbs>

      <Box className="row">
        <Box className="col">
          <Box className="float-left">
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
          </Box>
          <Box className="float-right"></Box>
        </Box>
      </Box>

      {!users.loading && <UserList users={users.value} />}
    </Box>
  );
}
