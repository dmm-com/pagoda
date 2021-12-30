import { Box, Typography } from "@mui/material";
import React, { FC } from "react";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";

export const Dashboard: FC = () => {
  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>
    </Box>
  );
};
