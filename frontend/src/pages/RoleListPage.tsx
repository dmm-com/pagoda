import AddIcon from "@mui/icons-material/Add";
import { Box, Button, Container, Typography } from "@mui/material";
import React, { FC, useCallback, useState } from "react";
import { Link } from "react-router";

import { RoleImportModal } from "../components/role/RoleImportModal";
import { RoleList } from "../components/role/RoleList";
import { aironeApiClient } from "../repository/AironeApiClient";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { newRolePath, topPath } from "routes/Routes";

export const RoleListPage: FC = () => {
  const [openImportModal, setOpenImportModal] = useState(false);

  const handleExport = useCallback(async () => {
    await aironeApiClient.exportRoles("role.yaml");
  }, []);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ロール管理</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="ロール管理">
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
        <Button
          variant="contained"
          color="secondary"
          component={Link}
          to={newRolePath()}
          sx={{ height: "48px", borderRadius: "24px", ml: "16px" }}
        >
          <AddIcon /> 新規ロールを作成
        </Button>
      </PageHeader>

      <Container>
        <RoleList />
      </Container>
    </Box>
  );
};
