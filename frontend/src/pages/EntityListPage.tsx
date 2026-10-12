import { Box, Button, Container, Typography } from "@mui/material";
import { FC, Suspense, useCallback, useState } from "react";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityImportModal } from "components/entity/EntityImportModal";
import { EntityList } from "components/entity/EntityList";
import { usePage } from "hooks/usePage";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";
import { ServerContext, TITLE_TEMPLATES } from "services";

const EntityListContent: FC = () => {
  const { page, query, changePage, changeQuery } = usePage();

  const { data: entities, mutate: refreshEntities } = usePagodaSWR(
    ["entities", page, query],
    () => aironeApiClient.getEntities(page, query),
    { suspense: true },
  );

  usePageTitle(TITLE_TEMPLATES.entityList);

  return (
    <Container>
      <EntityList
        entities={entities}
        page={page}
        changePage={changePage}
        query={query}
        handleChangeQuery={changeQuery}
        setToggle={() => refreshEntities()}
      />
    </Container>
  );
};

export const EntityListPage: FC = () => {
  const { t } = useTranslation();
  const [openImportModal, setOpenImportModal] = useState(false);

  const isReadonly = ServerContext.getInstance()?.user?.isReadonly ?? false;

  const handleExport = useCallback(async () => {
    await aironeApiClient.exportEntities("entity.yaml");
  }, []);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">
          {t("entity.list.pageTitle")}
        </Typography>
      </AironeBreadcrumbs>

      <PageHeader title={t("entity.list.pageTitle")}>
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
          <EntityImportModal
            openImportModal={openImportModal}
            closeImportModal={() => setOpenImportModal(false)}
          />
        </Box>
      </PageHeader>

      <Suspense fallback={<Loading />}>
        <EntityListContent />
      </Suspense>
    </Box>
  );
};
