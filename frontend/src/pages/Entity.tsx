import { Box, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { Loading } from "../components/common/Loading";
import { EntityList } from "../components/entity/EntityList";
import { getEntities } from "../utils/AironeAPIClient";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  contextBox: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
}));

export const Entity: FC = () => {
  const classes = useStyles();

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

      <Box className={classes.contextBox}>
        <Box my="50px">
          <Typography variant="h2">エンティティ一覧</Typography>
        </Box>
      </Box>

      {/*
      <Box className="row">
        <Box className="col">
          <Box className="float-left">
            <CreateButton to={newEntityPath()}>エンティティ作成</CreateButton>
            <Button
              className={classes.button}
              variant="outlined"
              color="secondary"
              onClick={() => downloadExportedEntities("entity.yaml")}
            >
              エクスポート
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              className={classes.button}
              component={Link}
              to={importEntitiesPath()}
            >
              インポート
            </Button>
          </Box>
          <Box className="float-right" />
        </Box>
      </Box>
      */}

      {entities.loading ? (
        <Loading />
      ) : (
        <EntityList entities={entities.value} />
      )}
    </Box>
  );
};
