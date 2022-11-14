import EastOutlinedIcon from "@mui/icons-material/EastOutlined";
import { Box, Button, Container, Typography } from "@mui/material";
import React, { FC, useCallback, useState } from "react";
import { Link } from "react-router-dom";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { RoleImportModal } from "../components/role/RoleImportModal";
import { RoleList } from "../components/role/RoleList";

import { newRolePath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";

export const RolePage: FC = () => {
  const [openImportModal, setOpenImportModal] = useState(false);

  const handleExport = useCallback(async () => {
    await aironeApiClientV2.exportRoles("role.yaml");
  }, []);

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
            <Box mx="8px">
              <Button
                variant="contained"
                color="info"
                sx={{ margin: "0 4px" }}
                onClick={handleExport}
              >
                エクスポート
              </Button>
              <Button
                variant="contained"
                color="info"
                sx={{ margin: "0 4px" }}
                onClick={() => setOpenImportModal(true)}
              >
                インポート
              </Button>
              <RoleImportModal
                openImportModal={openImportModal}
                closeImportModal={() => setOpenImportModal(false)}
              />
            </Box>
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
