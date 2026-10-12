import { Box, Button, Container, Typography } from "@mui/material";
import { FC, useCallback, useState } from "react";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { UserImportModal } from "components/user/UserImportModal";
import { UserList } from "components/user/UserList";
import { usePageTitle } from "hooks/usePageTitle";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";
import { ServerContext, TITLE_TEMPLATES } from "services";

export const UserListPage: FC = () => {
  const { t } = useTranslation();
  const [openImportModal, setOpenImportModal] = useState(false);

  const isReadonly = ServerContext.getInstance()?.user?.isReadonly ?? false;

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
        <Typography color="textPrimary">{t("user.list.pageTitle")}</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={t("user.list.pageTitle")}>
        <Box display="flex" alignItems="center">
          <Button
            variant="contained"
            color="info"
            sx={{ margin: "0 4px" }}
            onClick={handleExport}
          >
            {t("common.export")}
          </Button>
          <Button
            variant="contained"
            color="info"
            sx={{ margin: "0 4px" }}
            onClick={() => setOpenImportModal(true)}
            disabled={isReadonly}
          >
            {t("common.import")}
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
