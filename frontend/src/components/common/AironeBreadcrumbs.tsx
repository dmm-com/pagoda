import { Breadcrumbs, Theme } from "@mui/material";
import { grey } from "@mui/material/colors";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

const useStyles = makeStyles<Theme>((theme) => ({
  breadcrumbs: {
    padding: theme.spacing(1),
    marginBottom: theme.spacing(1),
    backgroundColor: grey[300],
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
