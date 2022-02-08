import { Box, Typography, Container } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { EntityList } from "components/entity/EntityList";
import { getEntities } from "utils/AironeAPIClient";

export const Entity: FC = () => {
  const entities = useAsync(async () => {
    const resp = await getEntities();
    const data = await resp.json();
    return data.entities;
  });

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
          <EntityList entities={entities.value} />
        )}
      </Container>
    </Box>
  );
};
