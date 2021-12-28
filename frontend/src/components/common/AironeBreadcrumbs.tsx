import { Breadcrumbs, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Toolbar } from "@mui/material";

const useStyles = makeStyles<Theme>((theme) => ({
  breadcrumbs: {
    paddingLeft: "10%",
    paddingRight: "10%",
  },
}));

export const AironeBreadcrumbs: FC = ({ children }) => {
  const classes = useStyles();

  return (
    <Toolbar>
      <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
        {children}
      </Breadcrumbs>
    </Toolbar>
  );
};
