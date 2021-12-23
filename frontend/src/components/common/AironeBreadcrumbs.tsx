import { Breadcrumbs, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

const useStyles = makeStyles<Theme>((theme) => ({
  breadcrumbs: {
    padding: theme.spacing(1),
    marginBottom: theme.spacing(1),
  },
}));

export const AironeBreadcrumbs: FC = ({ children }) => {
  const classes = useStyles();

  return (
    <Breadcrumbs aria-label="breadcrumb" className={classes.breadcrumbs}>
      {children}
    </Breadcrumbs>
  );
};
