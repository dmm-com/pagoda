import React, { useState } from "react";
import { Select } from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import Button from "@material-ui/core/Button";
import Grid from "@material-ui/core/Grid";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { useAsync } from "react-use";
import { getEntities, getEntityAttrs } from "../utils/AironeAPIClient";

function multipleSelectedValues(event) {
  return Array.from(event.target.options, (o) => o)
    .filter((o) => o.selected)
    .map((o) => o.value);
}

export default function AdvancedSearch({}) {
  const [selectedEntityIds, setSelectedEntityIds] = useState([]);
  const [selectedAttrs, setSelectedAttrs] = useState([]);

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

      <Typography variant="h5">検索条件:</Typography>

      <div className="row">
        <div className="col">
          <Typography>検索するエンティティ</Typography>
          <Select
            multiple
            native
            variant="outlined"
            onChange={(e) => setSelectedEntityIds(multipleSelectedValues(e))}
          >
            {!entities.loading &&
              entities.value.map((entity) => (
                <option key="entities" value={entity.id}>
                  {entity.name}
                </option>
              ))}
          </Select>
        </div>
      </div>

      <div className="row">
        <div className="col">
          <Typography>検索する属性</Typography>
          <Select
            multiple
            native
            variant="outlined"
            onChange={(e) => setSelectedAttrs(multipleSelectedValues(e))}
          >
            {!attrs.loading &&
              attrs.value.map((attr) => (
                <option key="attribute" value={attr}>
                  {attr}
                </option>
              ))}
          </Select>
        </div>
      </div>

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
