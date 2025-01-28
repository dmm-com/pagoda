import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton, Typography } from "@mui/material";
import { Link } from "react-router-dom";
import React, { FC, useState } from "react";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { EntityControlMenu } from "../components/entity/EntityControlMenu";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { EntryList } from "components/entry/EntryList";
import { aironeApiClient } from "repository/AironeApiClient";
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
        <>TBD: Main Context</>
      </Container>
    </Box>
  );
};


