import { makeStyles } from "@material-ui/core/styles";
import React from "react";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import Button from "@material-ui/core/Button";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { getGroups } from "../utils/AironeAPIClient";
import CreateButton from "../components/common/CreateButton";
import { useAsync } from "react-use";
import GroupList from "../components/group/GroupList";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  entityName: {
    margin: theme.spacing(1),
  },
}));

export default function Group({}) {
  const classes = useStyles();

  const groups = useAsync(async () => {
    return getGroups().then((resp) => resp.json());
  });

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">グループ管理</Typography>
      </AironeBreadcrumbs>

      <div className="row">
        <div className="col">
          <div className="float-left">
            <CreateButton to={`/new-ui/groups/new`}>新規作成</CreateButton>
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
          <div className="float-right"></div>
        </div>
      </div>

      {!groups.loading && <GroupList groups={groups.value} />}
    </div>
  );
}
