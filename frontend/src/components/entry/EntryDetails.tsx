import { Box, Grid, Typography } from "@mui/material";
import React, { FC } from "react";

import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryReferral } from "components/entry/EntryReferral";

interface Props {
  entry: any;
  referredEntries: any;
}

export const EntryDetails: FC<Props> = ({ entry, referredEntries }) => {
  return (
    <Grid
      container
      flexGrow="1"
      columns={6}
      sx={{ borderTop: 1, borderColor: "#0000008A" }}
    >
      <Grid
        item
        xs={1}
        sx={{
          px: "16px",
          py: "64px",
          borderRight: 1,
          borderColor: "#0000008A",
        }}
      >
        <EntryReferral referredEntries={referredEntries} />
      </Grid>
      <Grid item xs={4}>
        <Box p="32px">
          <Typography p="32px" fontSize="32px" align="center">
            項目一覧
          </Typography>
          <EntryAttributes attributes={entry.attrs} />
        </Box>
      </Grid>
      <Grid item xs={1} />
    </Grid>
  );
};
