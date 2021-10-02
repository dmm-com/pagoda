import {
  Card,
  Checkbox,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
} from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React, { useReducer } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { getEntities, getEntityAttrs } from "../utils/AironeAPIClient";

export function AdvancedSearch({}) {
  const [selectedEntityIds, toggleSelectedEntityIds] = useReducer(
    (state, value) => {
      return state.indexOf(value) === -1
        ? [...state, value]
        : state.filter((v) => v !== value);
    },
    []
  );
  const [selectedAttrs, toggleSelectedAttrs] = useReducer((state, value) => {
    return state.indexOf(value) === -1
      ? [...state, value]
      : state.filter((v) => v !== value);
  }, []);

  const entities = useAsync(async () => {
    return getEntities()
      .then((resp) => resp.json())
      .then((data) => data.entities);
  });

  // TODO should be better to fetch all the values once, then filter it
  const attrs = useAsync(async () => {
    if (selectedEntityIds.length > 0) {
      return getEntityAttrs(selectedEntityIds)
        .then((resp) => resp.json())
        .then((data) => data.result);
    } else {
      return Promise.resolve([]);
    }
  }, [selectedEntityIds]);

  const searchParams = new URLSearchParams({
    entity: selectedEntityIds,
    attrinfo: JSON.stringify(
      selectedAttrs.map((attr) => {
        return { name: attr };
      })
    ),
  });

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">高度な検索</Typography>
      </AironeBreadcrumbs>

      <Typography variant="h5" className={classes.description}>
        検索条件:
      </Typography>

      <Card variant="outlined" className={classes.entitySelector}>
        <List subheader={<ListSubheader>検索するエンティティ</ListSubheader>}>
          {!entities.loading &&
            entities.value.map((entity) => (
              <ListItem
                key={entity.id}
                dense
                button
                divider
                onClick={() => toggleSelectedEntityIds(entity.id)}
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={selectedEntityIds.indexOf(entity.id) !== -1}
                    tabIndex={-1}
                    disableRipple
                  />
                </ListItemIcon>
                <ListItemText primary={entity.name} />
              </ListItem>
            ))}
        </List>
      </Card>

      <Card variant="outlined" className={classes.attrSelector}>
        <List subheader={<ListSubheader>検索する属性</ListSubheader>}>
          {!attrs.loading &&
            attrs.value.map((attr) => (
              <ListItem
                key={attr}
                dense
                button
                divider
                onClick={() => toggleSelectedAttrs(attr)}
              >
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={selectedAttrs.indexOf(attr) !== -1}
                    tabIndex={-1}
                    disableRipple
                  />
                </ListItemIcon>
                <ListItemText primary={attr} />
              </ListItem>
            ))}
        </List>
      </Card>

      <Grid container justify="flex-end">
        <Grid item xs={1}>
          <Button
            variant="contained"
            component={Link}
            to={`/new-ui/search?${searchParams}`}
          >
            検索
          </Button>
        </Grid>
      </Grid>
    </div>
  );
}
