import { Box, Button, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";

import { importUsersPath, newUserPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { CreateButton } from "components/common/CreateButton";
import { Loading } from "components/common/Loading";
import { UserList } from "components/user/UserList";
import { downloadExportedUsers } from "utils/AironeAPIClient";
import { DjangoContext } from "utils/DjangoContext";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export const UserPage: FC = () => {
  const classes = useStyles();
  const djangoContext = DjangoContext.getInstance();

  const users = useAsync(async () => {
    const _users = await aironeApiClientV2.getUsers();
    return djangoContext.user.isSuperuser
      ? _users
      : _users.filter((d) => d.id === djangoContext.user.id);
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

      {users.loading ? <Loading /> : <UserList users={users.value} />}
    </Box>
  );
};
