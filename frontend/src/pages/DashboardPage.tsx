import { Box, Container, Typography, TypographyTypeMap } from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { entityEntriesPath, entryDetailsPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";
import { useSimpleSearch } from "hooks/useSimpleSearch";
import { aironeApiClient } from "repository/AironeApiClient";

const StyledContainer = styled(Container)({
  marginTop: "16px",
});

const ResultBox = styled(Box)({
  marginTop: "40px",
  display: "flex",
  flexWrap: "wrap",
  gap: "32px",
});

const Result = styled(Typography)(({ theme }) => ({
  color: theme.palette.primary.main,
  textDecoration: "none",
  flexGrow: 1,
  maxWidth: theme.breakpoints.values.lg,
  overflow: "hidden",
  textOverflow: "ellipsis",
})) as OverridableComponent<TypographyTypeMap>;

const ResultEntityForEntry = styled(Typography)(({}) => ({
  color: "gray",
}));

export const DashboardPage: FC = () => {
  const history = useHistory();
  const location = useLocation();

  const [query, submitQuery] = useSimpleSearch();

  const entries = useAsyncWithThrow(async () => {
    if (query != null) {
      return await aironeApiClient.getSearchEntries(query);
    }
  }, [location, query]);

  const entities = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntities(undefined, undefined, true);
  });

  // If there is only one search result, move to entry details page.
  if (!entries.loading && entries.value?.length === 1) {
    history.push(
      entryDetailsPath(entries.value[0].schema?.id ?? 0, entries.value[0].id)
    );
  }

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>

      <StyledContainer>
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
          <ResultBox id="entry_list">
            {entries.value.map((entry) => (
              <Box id="entry" key={entry.id}>
                <Result
                  component={Link}
                  to={entryDetailsPath(entry.schema?.id ?? 0, entry.id)}
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
          <ResultBox id="entity_list">
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
      </StyledContainer>
    </Box>
  );
};
