import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { importEntitiesPath, newEntityPath, topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { CreateButton } from "../components/common/CreateButton";
import { Loading } from "../components/common/Loading";
import { EntityList } from "../components/entity/EntityList";
import {
  downloadExportedEntities,
  getEntities,
} from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export function Entity({}) {
  const classes = useStyles();

  const entities = useAsync(async () => {
    return getEntities()
      .then((resp) => resp.json())
      .then((data) => data.entities);
  });

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">エンティティ一覧</Typography>
      </AironeBreadcrumbs>

      <div className="row">
        <div className="col">
          <div className="float-left">
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
          </div>
          <div className="float-right" />
        </div>
      </div>

      {entities.loading ? (
        <Loading />
      ) : (
        <EntityList entities={entities.value} />
      )}
    </div>
  );
}
