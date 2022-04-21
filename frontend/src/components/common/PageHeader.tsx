import { Box, Button, Divider, Grid, Typography } from "@mui/material";
import React, { FC } from "react";

export const PageHeader: FC = ({ children }) => {
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
              <Box display="flex" justifyContent="center" my="32px">
                <Box mx="4px">
                  <Button variant="contained" color="secondary">
                    保存
                  </Button>
                </Box>
                <Box mx="4px">
                  <Button variant="outlined" color="primary">
                    キャンセル
                  </Button>
                </Box>
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
