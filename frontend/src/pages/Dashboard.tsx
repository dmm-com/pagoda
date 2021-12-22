import { Box, Button, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import {
  advancedSearchPath,
  entitiesPath,
  groupsPath,
  usersPath,
} from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";

const useStyles = makeStyles<Theme>((theme) => ({
  button: {
    margin: theme.spacing(1),
  },
  links: {
    display: "flex",
    justifyContent: "center",
  },
}));

export const Dashboard: FC = () => {
  const classes = useStyles();

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>

      <Box className={classes.links}>
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
      </Box>
    </Box>
  );
};
