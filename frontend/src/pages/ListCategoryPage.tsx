import { Box, Container, Grid, List, ListItem, ListItemText, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { useTypedParams } from "../hooks/useTypedParams";

import { PageHeader } from "components/common/PageHeader";
import { topPath } from "routes/Routes";

interface Props {
}

export const ListCategoryPage: FC<Props> = ({ }) => {
  const { categoryId } = useTypedParams<{ categoryId: number }>();

  const [categoryAnchorEl, setcategoryAnchorEl] =
    useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

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


