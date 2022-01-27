import { Box, Container, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { useParams, Link } from "react-router-dom";
import { useAsync } from "react-use";

import { entitiesPath, topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { Loading } from "../components/common/Loading";
import { EntryList as Entry } from "../components/entry/EntryList";
import { getEntries, getEntity } from "../utils/AironeAPIClient";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entryName: {
    margin: theme.spacing(1),
  },
}));

export const EntryList: FC = () => {
  const classes = useStyles();
  const { entityId } = useParams<{ entityId: number }>();

  const entity = useAsync(async () => {
    const resp = await getEntity(entityId);
    return await resp.json();
  });

  const entries = useAsync(async () => {
    const resp = await getEntries(entityId, true);
    const data = await resp.json();
    return data.results;
  });

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        <Typography color="textPrimary">
          {entity.loading ? "" : entity.value.name}
        </Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ marginTop: "111px" }}>
        <Box mb="64px">
          <Typography variant="h2" align="center">
            エントリ一覧
          </Typography>
        </Box>

        {entries.loading ? (
          <Loading />
        ) : (
          <Entry
            entityId={entityId}
            entries={entries.value}
            restoreMode={false}
          />
        )}
      </Container>
    </Box>
  );
};
