import { Box, List, ListItem, ListItemText } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { entityPath } from "../Routes";
import { getEntities } from "../utils/AironeAPIClient";
import { EntityStatus } from "../utils/Constants";

const useStyles = makeStyles(() => ({
  LeftMenu: {
    backgroundColor: "#d2d4d5",
    height: "100vh",
  },
}));

export const LeftMenu: FC = () => {
  const classes = useStyles();

  const entities = useAsync(async () => {
    const resp = await getEntities();
    const data = await resp.json();
    return data.entities.filter((e) => e.status & EntityStatus.TOP_LEVEL);
  });

  return (
    <Box className={classes.LeftMenu}>
      <List>
        {!entities.loading &&
          entities.value.map((entity) => {
            return (
              <ListItem
                key={entity.id}
                component={Link}
                to={entityPath(entity.id)}
              >
                <ListItemText primary={entity.name} />
              </ListItem>
            );
          })}
      </List>
    </Box>
  );
};
