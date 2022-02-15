import { Grid } from "@mui/material";
import React, { FC } from "react";

import { EntryAttributes } from "./EntryAttributes";
import { EntryReferral } from "./EntryReferral";

interface Props {
  entry: any;
  referredEntries: any;
}

export const EntryDetails: FC<Props> = ({ entry, referredEntries }) => {
  return (
    <Grid container sx={{ borderTop: 1, borderColor: "gray" }}>
      <Grid
        item
        xs={2.4}
        sx={{
          px: "16px",
          py: "64px",
          borderRight: 1,
          borderColor: "gray",
          minHeight: 500,
        }}
      >
        <EntryReferral referredEntries={referredEntries} />
      </Grid>
      <Grid item xs={9.6}>
        <EntryAttributes attributes={entry.attrs} />
      </Grid>
    </Grid>
  );
};
