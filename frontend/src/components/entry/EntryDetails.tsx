import { Box, Grid, Typography } from "@mui/material";
import React, { FC } from "react";
import { useLocation } from "react-router-dom";

import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryReferral } from "components/entry/EntryReferral";

interface Props {
  entry: any;
  referredEntries: any;
}

export const EntryDetails: FC<Props> = ({ entry, referredEntries }) => {
  const location = useLocation();

  const refAttrList = React.createRef<HTMLSpanElement>();

  React.useEffect(() => {
    console.log("location.hash", location.hash);
    switch (location.hash) {
      case "#attr_list":
        refAttrList.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
    }
  }, [location.hash]);

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
          py: "64px",
          borderRight: 1,
          borderColor: "#0000008A",
        }}
      >
        <EntryReferral referredEntries={referredEntries} />
      </Grid>
      <Grid item xs={4}>
        <Box p="32px">
          <Typography p="32px" fontSize="32px" align="center" ref={refAttrList}>
            項目一覧
          </Typography>
          <EntryAttributes attributes={entry.attrs} />
        </Box>
      </Grid>
      <Grid item xs={1} />
    </Grid>
  );
};
