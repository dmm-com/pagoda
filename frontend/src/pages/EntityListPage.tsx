import { Box, Button, Container, Typography } from "@mui/material";
import React, { FC, useCallback, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityImportModal } from "components/entity/EntityImportModal";
import { EntityList } from "components/entity/EntityList";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";

export const EntityListPage: FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [page, changePage] = usePage();

  const [openImportModal, setOpenImportModal] = useState(false);

  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [toggle, setToggle] = useState(false);

  const entities = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntities(page, query);
  }, [page, query, toggle]);

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    navigate({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const handleExport = useCallback(async () => {
    await aironeApiClient.exportEntities("entity.yaml");
  }, []);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
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
            handleChangeQuery={handleChangeQuery}
            setToggle={() => setToggle(!toggle)}
          />
        </Container>
      )}
    </Box>
  );
};
