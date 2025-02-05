import AddIcon from "@mui/icons-material/Add";
import {
  Box,
  Button,
  Container,
  Grid,
  List,
  ListItem,
  ListItemText,
  Typography,
} from "@mui/material";
import React, { FC, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { CategoryListHeader } from "components/category/CategoryListHeader";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { useAsyncWithThrow } from "hooks";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository";
import { entityEntriesPath, newCategoryPath, topPath } from "routes/Routes";
import { EntityListParam } from "services/Constants";
import { normalizeToMatch } from "services/StringUtil";

export const ListCategoryPage: FC = () => {
  const navigate = useNavigate();
  const [toggle, setToggle] = useState(false);

  // variable to store search query
  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [page, changePage] = usePage();

  // request handler when user specify query
  const handleChangeQuery = (newQuery?: string) => {
    changePage(1);
    setQuery(newQuery ?? "");

    navigate({
      pathname: location.pathname,
      search: newQuery ? `?query=${newQuery}` : "",
    });
  };

  const categories = useAsyncWithThrow(async () => {
    return await aironeApiClient.getCategories(page, query);
  }, [page, query, toggle]);

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">カテゴリ一覧</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={"カテゴリ一覧"}></PageHeader>
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
                    normalizeToMatch((e.target as HTMLInputElement).value ?? "")
                  );
              }}
            />
          </Box>
          <Button
            variant="contained"
            color="secondary"
            component={Link}
            to={newCategoryPath()}
            sx={{ height: "48px", borderRadius: "24px" }}
          >
            <AddIcon /> 新規カテゴリを作成
          </Button>
        </Box>

        {/* Context of Category */}
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
      </Container>
    </Box>
  );
};
