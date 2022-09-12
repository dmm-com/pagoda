import { Box, Container, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { UserList } from "components/user/UserList";
import { DjangoContext } from "utils/DjangoContext";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export const UserPage: FC = () => {
  const classes = useStyles();
  const djangoContext = DjangoContext.getInstance();

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ユーザ管理</Typography>
      </AironeBreadcrumbs>

      {/*
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
      */}

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        <Box
          sx={{ borderBottom: 1, borderColor: "gray", mb: "64px", pb: "64px" }}
        >
          <Typography variant="h2" align="center">
            ユーザ管理
          </Typography>
          <Typography variant="h4" align="center">
            ユーザ一覧
          </Typography>
        </Box>

        <UserList />
      </Container>
    </Box>
  );
};
