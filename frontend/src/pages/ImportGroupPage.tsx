import { Box, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { newGroupPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { ImportForm } from "components/common/ImportForm";
import { importGroups } from "utils/AironeAPIClient";

export const ImportGroupPage: FC = () => {
  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={newGroupPath()}>
          グループ管理
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <ImportForm importFunc={importGroups} />
    </Box>
  );
};
