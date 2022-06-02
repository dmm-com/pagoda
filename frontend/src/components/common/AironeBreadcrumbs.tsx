import { Box, Breadcrumbs, Theme } from "@mui/material";
import { Toolbar } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

const useStyles = makeStyles<Theme>(() => ({
  wrapper: {
    paddingLeft: "10%",
    paddingRight: "10%",
    width: "80%",
  },
}));

export const AironeBreadcrumbs: FC = ({ children }) => {
  const classes = useStyles();

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
        <Box className={classes.wrapper}>
          {/* to align paddings with above AppBar */}
          <Toolbar>
            <Breadcrumbs aria-label="breadcrumb">{children}</Breadcrumbs>
          </Toolbar>
        </Box>
      </Box>

      {/* This component is a virtual component for above fixed component */}
      <Box sx={{ width: "100%", height: "64px" }} />
    </>
  );
};
