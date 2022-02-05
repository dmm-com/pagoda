import { Box, Breadcrumbs, Theme } from "@mui/material";
import { Toolbar } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

const useStyles = makeStyles<Theme>(() => ({
  wrapper: {
    paddingLeft: "10%",
    paddingRight: "10%",
    width: "100%",
  },
}));

export const AironeBreadcrumbs: FC = ({ children }) => {
  const classes = useStyles();

  return (
    <Box className={classes.wrapper}>
      {/* to align paddings with above AppBar */}
      <Toolbar>
        <Breadcrumbs aria-label="breadcrumb">{children}</Breadcrumbs>
      </Toolbar>
    </Box>
  );
};
