import { Box, Button, Divider, Grid } from "@mui/material";
import React, { FC } from "react";

interface Props {
  isSubmittable: boolean;
  handleSubmit: (args?: object) => void;
  handleCancel: (args?: object) => void;
}

export const PageHeader: FC<Props> = ({
  isSubmittable,
  handleSubmit,
  handleCancel,
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
              {children}
            </Grid>

            <Grid item xs={2}>
              <Box display="flex" justifyContent="center" my="32px">
                <Box mx="4px">
                  <Button
                    variant="contained"
                    color="secondary"
                    disabled={!isSubmittable}
                    onClick={handleSubmit}
                  >
                    保存
                  </Button>
                </Box>
                <Box mx="4px">
                  <Button
                    variant="outlined"
                    color="primary"
                    onClick={handleCancel}
                  >
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
