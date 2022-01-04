import { Box, Typography } from "@mui/material";
import { alpha, TextField, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";

const useStyles = makeStyles<Theme>((theme) => ({
  container: {
    display: "flex",
    width: "100%",
    justifyContent: "center",
  },
  search: {
    display: "flex",
    borderRadius: theme.shape.borderRadius,
    backgroundColor: alpha(theme.palette.common.white, 0.15),
    "&:hover": {
      backgroundColor: alpha(theme.palette.common.white, 0.25),
    },
    margin: theme.spacing(0, 1),
    [theme.breakpoints.up("sm")]: {
      width: "auto",
    },
    width: "600px",
  },
  searchTextFieldInput: {
    background: "#0000000B",
    "&::placeholder": {
      color: "white",
    },
  },
}));

export const Dashboard: FC = () => {
  const classes = useStyles();

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography color="textPrimary">Top</Typography>
      </AironeBreadcrumbs>

      <Box className={classes.container}>
        <Box className={classes.search} mt="200px">
          <TextField
            //InputProps={{
            //  classes: { input: classes.searchTextFieldInput },
            //}}
            variant="outlined"
            size="small"
            placeholder="Search"
            sx={{
              background: "#0000000B",
            }}
            fullWidth={true}
          />
        </Box>
      </Box>
    </Box>
  );
};
