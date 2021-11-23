import { Breadcrumbs } from "@material-ui/core";
import { grey } from "@material-ui/core/colors";
import { makeStyles } from "@material-ui/core/styles";
import React, { FC } from "react";

const useStyles = makeStyles((theme) => ({
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
