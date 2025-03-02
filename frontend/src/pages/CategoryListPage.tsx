import { Box, Typography } from "@mui/material";
import React, { FC } from "react";

import { AironeLink } from "components";
import { CategoryList } from "components/category/CategoryList";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { topPath } from "routes/Routes";

export const CategoryListPage: FC = () => {
  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">カテゴリ一覧</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={"カテゴリ一覧"}></PageHeader>
      <CategoryList isEdit />
    </Box>
  );
};
