import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React from "react";
import { Link } from "react-router-dom";

import {
  advancedSearchPath,
  entitiesPath,
  groupsPath,
  usersPath,
} from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";

const useStyles = makeStyles((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  links: {
    display: "flex",
    justifyContent: "center",
  },
}));

export function Dashboard({}) {
  const classes = useStyles();

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>

      <div className={classes.links}>
        <Button
          className={classes.button}
          variant="contained"
          color="primary"
          component={Link}
          to={entitiesPath()}
        >
          エンティティ・エントリ一覧 &#x000bb;
        </Button>

        <Button
          className={classes.button}
          variant="contained"
          color="primary"
          component={Link}
          to={advancedSearchPath()}
        >
          高度な検索 &#x000bb;
        </Button>

        <Button
          className={classes.button}
          variant="contained"
          color="primary"
          component={Link}
          to={usersPath()}
        >
          ユーザ管理 &#x000bb;
        </Button>

        <Button
          className={classes.button}
          variant="contained"
          color="primary"
          component={Link}
          to={groupsPath()}
        >
          グループ管理 &#x000bb;
        </Button>
      </div>
    </div>
  );
}
