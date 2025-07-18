import { Box, Button, Container, Typography } from "@mui/material";
import React, { FC, useCallback, useState } from "react";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityImportModal } from "components/entity/EntityImportModal";
import { EntityList } from "components/entity/EntityList";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { usePage } from "hooks/usePage";
import { usePageTitle } from "hooks/usePageTitle";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";

export const EntityListPage: FC = () => {
  const { page, query, changePage, changeQuery } = usePage();

  const [openImportModal, setOpenImportModal] = useState(false);
  const [toggle, setToggle] = useState(false);

  const entities = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntities(page, query);
  }, [page, query, toggle]);

  const handleExport = useCallback(async () => {
    await aironeApiClient.exportEntities("entity.yaml");
  }, []);

  usePageTitle(TITLE_TEMPLATES.entityList);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">モデル一覧</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="モデル一覧">
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
          <EntityImportModal
            openImportModal={openImportModal}
            closeImportModal={() => setOpenImportModal(false)}
          />
        </Box>
      </PageHeader>

      {entities.loading || !entities.value ? (
        <Loading />
      ) : (
        <Container>
          <EntityList
            entities={entities.value}
            page={page}
            changePage={changePage}
            query={query}
            handleChangeQuery={changeQuery}
            setToggle={() => setToggle(!toggle)}
          />
        </Container>
      )}
    </Box>
  );
};
