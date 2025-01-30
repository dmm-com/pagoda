import { Box, Button, Container, Grid, List, ListItem, ListItemText, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import React, { FC, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { useTypedParams } from "../hooks/useTypedParams";
import { usePage } from "hooks/usePage";

import { SearchBox } from "components/common/SearchBox";
import { PageHeader } from "components/common/PageHeader";
import { topPath } from "routes/Routes";
import { newCategoryPath } from "routes/Routes";
import { normalizeToMatch } from "services/StringUtil";

interface Props {
}

export const ListCategoryPage: FC<Props> = ({ }) => {
  const navigate = useNavigate();
  const { categoryId } = useTypedParams<{ categoryId: number }>();

  const [categoryAnchorEl, setcategoryAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  // variable to store search query
  const [query, setQuery] = useState("");
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

  /*
  const category = useAsyncWithThrow(async () => {
    return await aironeApiClient.getcategory(categoryId);
  });
  */

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">カテゴリ一覧</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={"カテゴリ一覧"}
      >
      </PageHeader>
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

        {/* Context of Category 
          FIXME: This should be replaced with actual category context
        */}
        <Grid container spacing={3}>
          <Grid item md={4}>
            <List
              subheader={
                <Typography variant="h6" component="div">
                  インフラ機器
                </Typography>
              }
            >
              <ListItem button component={Link} to={`/categories/${categoryId}/entities`}>
                <ListItemText primary="サーバ" />
              </ListItem>
              <ListItem button component={Link} to={`/categories/${categoryId}/entities`}>
                <ListItemText primary="switch" />
              </ListItem>
            </List>
          </Grid>
          <Grid item md={4}>
            <List
              subheader={
                <Typography variant="h6" component="div">
                  インフラ機器
                </Typography>
              }
            >
              <ListItem button component={Link} to={`/categories/${categoryId}/entities`}>
                <ListItemText primary="サーバ" />
              </ListItem>
              <ListItem button component={Link} to={`/categories/${categoryId}/entities`}>
                <ListItemText primary="switch" />
              </ListItem>
            </List>
          </Grid>
          <Grid item md={4}>
            <List
              subheader={
                <Typography variant="h6" component="div">
                  インフラ機器
                </Typography>
              }
            >
              <ListItem button component={Link} to={`/categories/${categoryId}/entities`}>
                <ListItemText primary="サーバ" />
              </ListItem>
              <ListItem button component={Link} to={`/categories/${categoryId}/entities`}>
                <ListItemText primary="switch" />
              </ListItem>
            </List>
          </Grid>
        </Grid>

      </Container>
    </Box>
  );
};


