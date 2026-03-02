import AddIcon from "@mui/icons-material/Add";
import { Box, Button, Container, List, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { FC, Suspense } from "react";
import { Link } from "react-router";

import { CategoryListHeader } from "components/category/CategoryListHeader";
import { AironeLink, Loading } from "components/common";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { usePage } from "hooks/usePage";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { aironeApiClient } from "repository";
import { entityEntriesPath, newCategoryPath } from "routes/Routes";
import { EntityListParam } from "services/Constants";
import { normalizeToMatch } from "services/StringUtil";

interface Props {
  isEdit?: boolean;
}

const CategoryListContent: FC<Props> = ({ isEdit = false }) => {
  const { page, query, changeQuery, changePage } = usePage();

  // request handler when user specify query
  const handleChangeQuery = (newQuery?: string) => {
    changeQuery(newQuery ?? "");
  };

  const { data: categories, mutate: refreshCategories } = usePagodaSWR(
    ["categories", page, query],
    () => aironeApiClient.getCategories(page, query),
    { suspense: true },
  );

  return (
    <Container>
      {/* Show control menus to filter and create category */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width="600px">
          <SearchBox
            placeholder="カテゴリを絞り込む"
            defaultValue={query}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  normalizeToMatch((e.target as HTMLInputElement).value ?? ""),
                );
            }}
          />
        </Box>
        {isEdit && (
          <Button
            variant="contained"
            color="secondary"
            component={Link}
            to={newCategoryPath()}
            sx={{ height: "48px", borderRadius: "24px" }}
          >
            <AddIcon /> 新規カテゴリを作成
          </Button>
        )}
      </Box>

      {/* Context of Category */}
      <Grid container spacing={3}>
        {categories.results.map((category) => (
          <Grid size={4} key={category.id}>
            <List
              subheader={
                <CategoryListHeader
                  category={category}
                  setToggle={() => refreshCategories()}
                  isEdit={isEdit}
                />
              }
            >
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  //overflowY: "scroll",
                  //maxHeight: 300,
                  ml: "40px",
                }}
              >
                {category.models.map((models) => (
                  <Typography
                    key={models.id}
                    component={AironeLink}
                    to={entityEntriesPath(models.id)}
                    variant="body2"
                  >
                    {models.name}
                  </Typography>
                ))}
              </Box>
            </List>
          </Grid>
        ))}
      </Grid>
      <PaginationFooter
        count={categories.count ?? 0}
        maxRowCount={EntityListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Container>
  );
};

export const CategoryList: FC<Props> = ({ isEdit = false }) => {
  return (
    <Suspense fallback={<Loading />}>
      <CategoryListContent isEdit={isEdit} />
    </Suspense>
  );
};
