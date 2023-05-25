import { Box, Container, Typography, TypographyTypeMap } from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { useAsync } from "react-use";

import { useSimpleSearch } from "../hooks/useSimpleSearch";
import { aironeApiClientV2 } from "../repository/AironeApiClientV2";

import { entityEntriesPath, entryDetailsPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";

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
          <ResultBox>
            {entries.value.map((entry) => (
              <Box key={entry.id}>
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
      </StyledContainer>
    </Box>
  );
};
