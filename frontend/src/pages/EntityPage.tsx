import AddIcon from "@mui/icons-material/Add";
import { Box, Typography, Container, Button } from "@mui/material";
import React, { FC, useCallback, useMemo, useState } from "react";
import { useHistory, useLocation, Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { EntityImportModal } from "../components/entity/EntityImportModal";
import { usePage } from "../hooks/usePage";
import { EntityList as ConstEntityList } from "../utils/Constants";

import { newEntityPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { EntityList } from "components/entity/EntityList";

export const EntityPage: FC = () => {
  const location = useLocation();
  const history = useHistory();

  const [page, changePage] = usePage();

  const [openImportModal, setOpenImportModal] = useState(false);

  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(
    params.has("query") ? params.get("query") : undefined
  );

  const entities = useAsync(async () => {
    return await aironeApiClientV2.getEntities(page, query);
  }, [page, query]);

  const maxPage = useMemo(() => {
    if (entities.loading) {
      return 0;
    }
    return Math.ceil(entities.value.count / ConstEntityList.MAX_ROW_COUNT);
  }, [entities.loading, entities.value?.count]);

  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery);

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

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        <Box
          display="flex"
          justifyContent="space-between"
          sx={{ borderBottom: 1, borderColor: "gray", mb: "64px", pb: "64px" }}
        >
          <Typography variant="h2">エンティティ一覧</Typography>
          <Box display="flex" alignItems="flex-end">
            <Box display="flex" alignItems="center">
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
                <EntityImportModal
                  openImportModal={openImportModal}
                  closeImportModal={() => setOpenImportModal(false)}
                />
              </Box>
              <Button
                variant="contained"
                color="secondary"
                component={Link}
                to={newEntityPath()}
                sx={{ height: "48px", borderRadius: "24px" }}
              >
                <AddIcon /> 新規作成
              </Button>
            </Box>
          </Box>
        </Box>

        {entities.loading ? (
          <Loading />
        ) : (
          <EntityList
            entities={entities.value.results}
            page={page}
            query={query}
            maxPage={maxPage}
            handleChangePage={changePage}
            handleChangeQuery={handleChangeQuery}
          />
        )}
      </Container>
    </Box>
  );
};
