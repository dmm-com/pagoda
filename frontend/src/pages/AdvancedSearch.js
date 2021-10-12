import {
  Card,
  CardHeader,
  Checkbox,
  FormControlLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
} from "@material-ui/core";
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";
import Typography from "@material-ui/core/Typography";
import { alpha, makeStyles } from "@material-ui/core/styles";
import React, { useReducer, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { Loading } from "../components/common/Loading";
import { getEntities, getEntityAttrs } from "../utils/AironeAPIClient";

const useStyles = makeStyles((theme) => ({
  description: {
    margin: theme.spacing(1),
  },

  entitySelector: {
    margin: theme.spacing(2),
  },

  entityList: {
    maxHeight: 300,
    overflow: "auto",
  },

  entityFilter: {
    margin: theme.spacing(1),
    minWidth: 500,
  },

  attrSelector: {
    margin: theme.spacing(2),
  },

  attrList: {
    maxHeight: 300,
    overflow: "auto",
  },

  attrFilter: {
    margin: theme.spacing(1),
    minWidth: 500,
  },
}));

export function AdvancedSearch({}) {
  const classes = useStyles();

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

  const [entityNameFilter, setEntityNameFilter] = useState("");
  const [attrNameFilter, setAttrNameFilter] = useState("");

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

  const handleToggleEntityAll = (e) => {
    e.target.checked
      ? !entities.loading &&
        entities.value
          .filter(
            (entity) =>
              entity.name
                .toLowerCase()
                .indexOf(entityNameFilter.toLowerCase()) !== -1 &&
              selectedEntityIds.indexOf(entity.id) === -1
          )
          .map((entity) => toggleSelectedEntityIds(entity.id))
      : selectedEntityIds.map((entityId) => toggleSelectedEntityIds(entityId));
  };

  const handleToggleAttrAll = (e) => {
    e.target.checked
      ? !attrs.loading &&
        attrs.value
          .filter(
            (attr) =>
              attr.toLowerCase().indexOf(attrNameFilter.toLowerCase()) !== -1 &&
              selectedAttrs.indexOf(attr) === -1
          )
          .map((attr) => toggleSelectedAttrs(attr))
      : selectedAttrs.map((attr) => toggleSelectedAttrs(attr));
  };

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
        <Grid container spacing={2}>
          <CardHeader subheader="検索するエンティティを選択" />
          <FormControlLabel
            control={<Checkbox onChange={handleToggleEntityAll} />}
            label="全選択"
          />
        </Grid>
        <List className={classes.entityList}>
          {!entities.loading ? (
            <>
              {entities.value
                .filter(
                  (entity) =>
                    entity.name
                      .toLowerCase()
                      .indexOf(entityNameFilter.toLowerCase()) !== -1
                )
                .map((entity) => (
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
            </>
          ) : (
            <Loading />
          )}
        </List>
        <input
          text="text"
          className={classes.entityFilter}
          placeholder="エンティティ名で絞り込む"
          value={entityNameFilter}
          onChange={(e) => setEntityNameFilter(e.target.value)}
        />
      </Card>

      <Card variant="outlined" className={classes.attrSelector}>
        <Grid container spacing={2}>
          <CardHeader subheader="検索する属性を選択" />
          <FormControlLabel
            control={<Checkbox onChange={handleToggleAttrAll} />}
            label="全選択"
          />
        </Grid>
        <List className={classes.attrList}>
          {!attrs.loading ? (
            <>
              {attrs.value
                .filter(
                  (attr) =>
                    attr.toLowerCase().indexOf(attrNameFilter.toLowerCase()) !==
                    -1
                )
                .map((attr) => (
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
            </>
          ) : (
            <Loading />
          )}
        </List>
        <input
          text="text"
          className={classes.attrFilter}
          placeholder="属性名で絞り込む"
          value={attrNameFilter}
          onChange={(e) => setAttrNameFilter(e.target.value)}
        />
      </Card>

      <Grid container justifyContent="flex-end">
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
