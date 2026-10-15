import {
  Box,
  Container,
  Pagination,
  Stack,
  Typography,
  TypographyTypeMap,
} from "@mui/material";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import { FC } from "react";
import { Link, useNavigate } from "react-router";

import { Loading, SearchBox } from "components";
import { CategoryList } from "components/category/CategoryList";
import { useSimpleSearch } from "hooks";
import { useAsync } from "hooks/useAsync";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository";
import { entryDetailsPath } from "routes";

const SEARCH_PAGE_SIZE = 20;

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
  const { t } = useTranslation();
  const [query, page, submitQuery, changePage] = useSimpleSearch();

  const entries = useAsync(async () => {
    if (query != null) {
      return await aironeApiClient.getSearchEntries(
        query,
        (page - 1) * SEARCH_PAGE_SIZE,
        SEARCH_PAGE_SIZE + 1,
      );
    }
    return undefined;
  }, [query, page]);

  const hasMore = (entries.value?.length ?? 0) > SEARCH_PAGE_SIZE;
  const visibleEntries = entries.value?.slice(0, SEARCH_PAGE_SIZE) ?? [];
  const firstEntry =
    page === 1 && !hasMore && visibleEntries.length === 1
      ? visibleEntries[0]
      : undefined;
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
            {visibleEntries.map((entry) => (
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
          <Stack spacing={1} alignItems="center" mt={3}>
            <Typography>
              {t("simpleSearch.range", {
                from: SEARCH_PAGE_SIZE * (page - 1) + 1,
                to: SEARCH_PAGE_SIZE * (page - 1) + visibleEntries.length,
                more: hasMore ? t("simpleSearch.more") : "",
              })}
            </Typography>
            <Pagination
              count={page + (hasMore ? 1 : 0)}
              page={page}
              onChange={(_, newPage) => changePage(newPage)}
              siblingCount={1}
              boundaryCount={1}
              color="primary"
            />
          </Stack>
        </>
      ) : (
        <CategoryList />
      )}
    </StyledContainer>
  );
};
