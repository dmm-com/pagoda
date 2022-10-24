import { Box, Container, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { UserList } from "components/user/UserList";

export const UserPage: FC = () => {
  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ユーザ管理</Typography>
      </AironeBreadcrumbs>

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
