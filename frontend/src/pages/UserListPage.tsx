import { Box, Button, Container, Typography } from "@mui/material";
import React, { FC, useCallback, useState } from "react";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { UserImportModal } from "components/user/UserImportModal";
import { UserList } from "components/user/UserList";
import { usePageTitle } from "hooks/usePageTitle";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";

export const UserListPage: FC = () => {
  const [openImportModal, setOpenImportModal] = useState(false);

  const handleExport = useCallback(async () => {
    await aironeApiClient.exportUsers("user.yaml");
  }, []);

  usePageTitle(TITLE_TEMPLATES.userList);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ユーザ管理</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="ユーザ管理">
        <Box display="flex" alignItems="center">
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
          <UserImportModal
            openImportModal={openImportModal}
            closeImportModal={() => setOpenImportModal(false)}
          />
        </Box>
      </PageHeader>

      <Container>
        <UserList />
      </Container>
    </Box>
  );
};
