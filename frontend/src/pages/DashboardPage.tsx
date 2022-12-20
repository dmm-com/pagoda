import { Box, Typography } from "@mui/material";
import { Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { useSimpleSearch } from "../hooks/useSimpleSearch";

import { entityEntriesPath, entryDetailsPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";

const useStyles = makeStyles<Theme>((theme) => ({
  container: {
    display: "flex",
    width: "100%",
    flexDirection: "column",
    alignItems: "center",
  },
  dashboard: {
    width: theme.breakpoints.values.lg,
    marginTop: "256px",
  },
  resultBox: {
    marginTop: "80px",
    display: "flex",
    flexWrap: "wrap",
    gap: "32px",
  },
  result: {
    color: theme.palette.primary.main,
    textDecoration: "none",
    flexGrow: 1,
    maxWidth: theme.breakpoints.values.lg,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
}));

export const DashboardPage: FC = () => {
  const classes = useStyles();
  const history = useHistory();
  const location = useLocation();

  const [query, submitQuery] = useSimpleSearch();

  const entries = useAsync(async () => {
    if (query != null) {
      return await aironeApiClientV2.getSearchEntries(query);
    }
  }, [location, query]);

  const entities = useAsync(async () => {
    return await aironeApiClientV2.getEntities(undefined, undefined, true);
  });

  // If there is only one search result, move to entry details page.
  if (!entries.loading && entries.value?.length === 1) {
    history.push(
      entryDetailsPath(entries.value[0].schema.id, entries.value[0].id)
    );
  }

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>

      <Box className={classes.container}>
        <Box className={classes.dashboard}>
          <SearchBox
            placeholder="Search"
            defaultValue={query}
            onKeyPress={(e) => {
              e.key === "Enter" && submitQuery(e.target.value);
            }}
          />
          {entries.loading ? (
            <Loading />
          ) : entries.value ? (
            <Box className={classes.resultBox}>
              {entries.value.map((entry) => (
                <Typography
                  key={entry.id}
                  className={classes.result}
                  component={Link}
                  to={entryDetailsPath(entry.schema.id, entry.id)}
                >
                  {entry.name}
                </Typography>
              ))}
            </Box>
          ) : entities.loading ? (
            <Loading />
          ) : (
            <Box className={classes.resultBox}>
              {entities.value.results.map((entity) => (
                <Typography
                  key={entity.id}
                  className={classes.result}
                  component={Link}
                  to={entityEntriesPath(entity.id)}
                >
                  {entity.name}
                </Typography>
              ))}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};
