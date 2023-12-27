import { Box, Typography, Container, Button } from "@mui/material";
import React, { FC, useCallback, useMemo, useState } from "react";
import { useHistory, useLocation, Link } from "react-router-dom";
import { useAsync } from "react-use";

import { EntityImportModal } from "../components/entity/EntityImportModal";
import { usePage } from "../hooks/usePage";
import { aironeApiClientV2 } from "../repository/AironeApiClientV2";
import { EntityList as ConstEntityList } from "../services/Constants";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityList } from "components/entity/EntityList";

export const EntityListPage: FC = () => {
  const location = useLocation();
  const history = useHistory();

  const [page, changePage] = usePage();

  const [openImportModal, setOpenImportModal] = useState(false);

  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [toggle, setToggle] = useState(false);

  const entities = useAsync(async () => {
    return await aironeApiClientV2.getEntities(page, query);
  }, [page, query, toggle]);

  const maxPage = useMemo(() => {
    if (entities.loading) {
      return 0;
    }
    return Math.ceil(
      (entities.value?.count ?? 0) / ConstEntityList.MAX_ROW_COUNT,
    );
  }, [entities.loading, entities.value?.count]);

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    history.push({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const handleExport = useCallback(async () => {
    await aironeApiClientV2.exportEntities("entity.yaml");
  }, []);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">エンティティ一覧</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="エンティティ一覧">
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

      {entities.loading ? (
        <Loading />
      ) : (
        <Container>
          <EntityList
            entities={entities.value?.results ?? []}
            page={page}
            query={query}
            maxPage={maxPage}
            handleChangePage={changePage}
            handleChangeQuery={handleChangeQuery}
            setToggle={() => setToggle(!toggle)}
          />
        </Container>
      )}
    </Box>
  );
};
