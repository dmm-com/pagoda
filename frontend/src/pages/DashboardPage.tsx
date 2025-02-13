import {
  Box,
  Container,
  Grid,
  List,
  ListItem,
  ListItemText,
  Typography,
  TypographyTypeMap
} from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { CategoryListHeader } from "components/category/CategoryListHeader";
import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { usePage } from "hooks/usePage";
import { useSimpleSearch } from "hooks/useSimpleSearch";
import { aironeApiClient } from "repository/AironeApiClient";
import { entityEntriesPath, entryDetailsPath } from "routes/Routes";
import { EntityListParam } from "services/Constants";

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

const ResultEntityForEntry = styled(Typography)(({ }) => ({
  color: "gray",
}));

export const DashboardPage: FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // variable to store search query for Category
  const params = new URLSearchParams(location.search);
  const [queryCategory, setQueryCategory] = useState<string>(params.get("query") ?? "");
  const [page, changePage] = usePage();

  // variable to store search query for Searching Entry
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
    navigate(
      entryDetailsPath(entries.value[0].schema?.id ?? 0, entries.value[0].id)
    );
  }

  const [toggle, setToggle] = useState(false);

  // request handler when user specify query
  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQueryCategory(newQuery ?? "");

    navigate({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const categories = useAsyncWithThrow(async () => {
    return await aironeApiClient.getCategories(page, queryCategory);
  }, [page, query, toggle]);

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>

      <StyledContainer>

        {/* Context of Category */}
        <>
          <Grid container spacing={3}>
            {categories.value?.results.map((category) => (
              <Grid item md={4} key={category.id}>
                <List
                  subheader={
                    <CategoryListHeader
                      category={category}
                      setToggle={() => setToggle(!toggle)}
                    />
                  }
                >
                  <Box sx={{ overflowY: "scroll", maxHeight: 300 }}>
                    {category.models.map((models) => (
                      <ListItem
                        button
                        key={models.id}
                        component={Link}
                        to={entityEntriesPath(models.id)}
                      >
                        <ListItemText primary={models.name} />
                      </ListItem>
                    ))}
                  </Box>
                </List>
              </Grid>
            ))}
          </Grid>
          <PaginationFooter
            count={categories.value?.count ?? 0}
            maxRowCount={EntityListParam.MAX_ROW_COUNT}
            page={page}
            changePage={changePage}
          />
        </>

        {/* Models that are configured to be shown at the top page */}
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
