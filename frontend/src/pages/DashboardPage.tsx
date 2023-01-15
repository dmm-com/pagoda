import { Box, Typography, TypographyTypeMap } from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { useSimpleSearch } from "../hooks/useSimpleSearch";

import { entityEntriesPath, entryDetailsPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";

const Container = styled(Box)(({}) => ({
  display: "flex",
  width: "100%",
  flexDirection: "column",
  alignItems: "center",
}));

const Dashboard = styled(Box)(({ theme }) => ({
  width: theme.breakpoints.values.lg,
  marginTop: "256px",
}));

const ResultBox = styled(Box)(({}) => ({
  marginTop: "80px",
  display: "flex",
  flexWrap: "wrap",
  gap: "32px",
}));

const Result = styled(Typography)(({ theme }) => ({
  color: theme.palette.primary.main,
  textDecoration: "none",
  flexGrow: 1,
  maxWidth: theme.breakpoints.values.lg,
  overflow: "hidden",
  textOverflow: "ellipsis",
})) as OverridableComponent<TypographyTypeMap>;

const ResultEntityForEntry = styled(Typography)(({ theme }) => ({
  color: "gray",
}));

export const DashboardPage: FC = () => {
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

      <Container>
        <Dashboard>
          <SearchBox
            placeholder="Search"
            defaultValue={query}
            onKeyPress={(e) => {
              e.key === "Enter" && submitQuery(e.target.value);
            }}
            autoFocus
          />
          {entries.loading ? (
            <Loading />
          ) : entries.value ? (
            <ResultBox>
              {entries.value.map((entry) => (
                <Box key={entry.id}>
                  <Result
                    component={Link}
                    to={entryDetailsPath(entry.schema.id, entry.id)}
                  >
                    {entry.name}
                  </Result>
                  <ResultEntityForEntry>
                    {entry.schema?.name}
                  </ResultEntityForEntry>
                </Box>
              ))}
            </ResultBox>
          ) : entities.loading ? (
            <Loading />
          ) : (
            <ResultBox>
              {entities.value?.results?.map((entity) => (
                <Result
                  key={entity.id}
                  component={Link}
                  to={entityEntriesPath(entity.id)}
                >
                  {entity.name}
                </Result>
              ))}
            </ResultBox>
          )}
        </Dashboard>
      </Container>
    </Box>
  );
};
