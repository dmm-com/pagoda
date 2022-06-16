import { Box, Divider, Grid, Typography } from "@mui/material";
import React, { FC, ReactElement } from "react";

interface Props {
  componentSubmits: ReactElement<any>;
  componentControl?: ReactElement<any>;
}

export const PageHeader: FC<Props> = ({
  componentControl,
  componentSubmits,
  children,
}) => {
  return (
    <>
      <Box
        sx={{
          position: "fixed",
          width: "100%",
          zIndex: 1,
          backgroundColor: "white",
        }}
      >
        <Box mt="64px" sx={{ width: "78%", mx: "auto" }}>
          <Grid container>
            <Grid item xs={10}>
              <Typography variant="h2">{children}</Typography>
            </Grid>

            <Grid item xs={2}>
              <Box display="flex" alignItems="flex-end" flexDirection="column">
                {componentControl && componentControl}

                {componentSubmits}
              </Box>
            </Grid>
          </Grid>
        </Box>

        <Divider sx={{ marginTop: "32px", borderColor: "black" }} />
      </Box>
      {/* This component is a virtual component for above fixed component */}
      <Box sx={{ width: "100%", height: "169px" }} />
    </>
  );
};
