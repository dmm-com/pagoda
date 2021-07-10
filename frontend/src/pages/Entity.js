import React from "react";
import { Link } from "react-router-dom";
import Typography from "@material-ui/core/Typography";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { getEntities } from "../utils/AironeAPIClient";
import { useAsync } from "react-use";
import EntityList from "../components/entity/EntityList";
import CreateButton from "../components/common/CreateButton";
import Button from "@material-ui/core/Button";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
}));

export default function Entity({}) {
  const classes = useStyles();

  const entities = useAsync(async () => {
    return getEntities()
      .then((resp) => resp.json())
      .then((data) => data.entities);
  });

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">エンティティ一覧</Typography>
      </AironeBreadcrumbs>

      <div className="row">
        <div className="col">
          <div className="float-left">
            <CreateButton to={`/new-ui/entities/new`}>
              エンティティ作成
            </CreateButton>
            <Button
              className={classes.button}
              variant="outlined"
              color="secondary"
            >
              エクスポート
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              className={classes.button}
              component={Link}
              to={`/new-ui/import`}
            >
              インポート
            </Button>
          </div>
          <div className="float-right" />
        </div>
      </div>

      {!entities.loading && <EntityList entities={entities.value} />}
    </div>
  );
}
