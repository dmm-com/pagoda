import { Box, Typography } from "@mui/material";
import { FC } from "react";

import { AironeLink } from "components";
import { CategoryList } from "components/category/CategoryList";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { useTranslation } from "hooks/useTranslation";
import { topPath } from "routes/Routes";

export const ListCategoryPage: FC = () => {
  const { t } = useTranslation();

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">{t("category.list.title")}</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={t("category.list.title")}></PageHeader>
      <CategoryList />
    </Box>
  );
};
