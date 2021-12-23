import { Box, CircularProgress, Theme, Typography } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

const useStyles = makeStyles<Theme>((theme) => ({
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

export const Loading: FC = () => {
  const classes = useStyles();

  return (
    <Box data-testid="loading">
      <Box className={classes.loading}>
        <CircularProgress />
        <Typography className={classes.text}>Loading...</Typography>
      </Box>
    </Box>
  );
};
