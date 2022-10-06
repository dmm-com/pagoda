import EastOutlinedIcon from "@mui/icons-material/EastOutlined";
import { Box, Button, Container, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { RoleList } from "../components/role/RoleList";

import { newRolePath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { DjangoContext } from "utils/DjangoContext";

export const RolePage: FC = () => {
  const djangoContext = DjangoContext.getInstance();

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ロール管理</Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        <Box
          display="flex"
          justifyContent="space-between"
          sx={{ borderBottom: 1, borderColor: "gray", mb: "64px", pb: "64px" }}
        >
          <Typography variant="h2">ロール管理</Typography>
          <Box display="flex" alignItems="flex-end">
            <Button
              variant="contained"
              color="secondary"
              component={Link}
              to={newRolePath()}
              sx={{ height: "48px", borderRadius: "24px" }}
            >
              <EastOutlinedIcon /> 新規ロールを作成
            </Button>
          </Box>
        </Box>

        <RoleList />
      </Container>
    </Box>
  );
};
