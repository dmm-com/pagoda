import { Box, Typography, Container } from "@mui/material";
import React, { FC, useMemo, useState } from "react";
import { useHistory, useLocation, Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { EntityList as ConstEntityList } from "../utils/Constants";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { EntityList } from "components/entity/EntityList";

export const EntityPage: FC = () => {
  const location = useLocation();
  const history = useHistory();

  const params = new URLSearchParams(location.search);
  const [page, setPage] = useState<number>(
    params.has("page") ? Number(params.get("page")) : 1
  );
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

  const handleChangePage = (newPage: number) => {
    setPage(newPage);

    history.push({
      pathname: location.pathname,
      search: `?page=${newPage}` + (query ? `&query=${query}` : ""),
    });
  };

  const handleChangeQuery = (newQuery?: string) => {
    setPage(1);
    setQuery(newQuery);

    history.push({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">エンティティ一覧</Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        <Box mb="64px">
          <Typography variant="h2" align="center">
            エンティティ一覧
          </Typography>
        </Box>

        {entities.loading ? (
          <Loading />
        ) : (
          <EntityList
            entities={entities.value.results}
            page={page}
            query={query}
            maxPage={maxPage}
            handleChangePage={handleChangePage}
            handleChangeQuery={handleChangeQuery}
          />
        )}
      </Container>
    </Box>
  );
};
