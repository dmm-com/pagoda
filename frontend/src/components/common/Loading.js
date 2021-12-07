import { CircularProgress } from "@material-ui/core";
import Box from "@material-ui/core/Box";
import Typography from "@material-ui/core/Typography";
import { makeStyles } from "@material-ui/core/styles";
import React from "react";

const useStyles = makeStyles((theme) => ({
  loading: {
    margin: "auto",
    padding: theme.spacing(1),
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  text: {
    padding: theme.spacing(1),
  },
}));

export function Loading() {
  const classes = useStyles();

  return (
    <Box data-testid="loading">
      <Box className={classes.loading}>
        <CircularProgress />
        <Typography className={classes.text}>Loading...</Typography>
      </Box>
    </Box>
  );
}
