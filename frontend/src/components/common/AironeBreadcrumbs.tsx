import { Box, Breadcrumbs, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

const useStyles = makeStyles<Theme>((theme) => ({
  frame: {
    width: "100%",
    height: "56px",
  },
  fixed: {
    position: "fixed",
    zIndex: 2,
    width: "100%",
    backgroundColor: "white",
    display: "flex",
    justifyContent: "center",
  },
  breadcrumb: {
    width: theme.breakpoints.values.lg,
    "& nav": {
      display: "flex",
      height: "56px",
      padding: "0px 24px",
    },
    "& li": {
      maxWidth: "300px",
      textOverflow: "ellipsis",
      overflow: "hidden",
      whiteSpace: "nowrap",
    },
    "& li > p": {
      textOverflow: "ellipsis",
      overflow: "hidden",
    },
  },
}));

export const AironeBreadcrumbs: FC = ({ children }) => {
  const classes = useStyles();

  return (
    <Box className={classes.frame}>
      <Box className={classes.fixed}>
        <Box className={classes.breadcrumb}>
          <Breadcrumbs aria-label="breadcrumb">{children}</Breadcrumbs>
        </Box>
      </Box>
    </Box>
  );
};
