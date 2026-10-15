import { Box, Container, Typography, TypographyTypeMap } from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import { FC } from "react";
import { Link, useNavigate } from "react-router";

import { Loading, SearchBox } from "components";
import { CategoryList } from "components/category/CategoryList";
import { useSimpleSearch } from "hooks";
import { useAsync } from "hooks/useAsync";
import { aironeApiClient } from "repository";
import { entryDetailsPath } from "routes";

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
  const navigate = useNavigate();
  const [query, submitQuery] = useSimpleSearch();

  const entries = useAsync(async () => {
    if (query != null) {
      return await aironeApiClient.getSearchEntries(query);
    }
    return undefined;
  }, [query]);

  // If there is only one search result, move to entry details page.
  const firstEntry = entries.value?.length === 1 ? entries.value[0] : undefined;
  if (!entries.loading && firstEntry != null) {
    navigate(entryDetailsPath(firstEntry.schema?.id ?? 0, firstEntry.id));
  }

  return (
    <StyledContainer>
      {entries.loading ? (
        <Loading />
      ) : entries.value ? (
        <>
          <SearchBox
            placeholder="Search"
            defaultValue={query}
            onKeyPress={(e, value) => {
              e.key === "Enter" && submitQuery(value);
            }}
            autoFocus
          />
          <ResultBox id="entry_list">
            {entries.value &&
              entries.value.map((entry) => (
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
        </>
      ) : (
        <CategoryList />
      )}
    </StyledContainer>
  );
};
