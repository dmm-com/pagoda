import ErrorOutlineIcon from "@mui/material/internal/svg-icons/ErrorOutline";
import SuccessOutlinedIcon from "@mui/material/internal/svg-icons/SuccessOutlined";
import { Theme } from "@mui/material/styles";
import { createStyles, makeStyles } from "@mui/styles";
import { SnackbarProvider } from "notistack";
import React, { FC } from "react";

const useStyles = makeStyles<Theme>((theme) =>
  createStyles({
    // Specify "!important" to increase the priority
    variantSuccess: {
      backgroundColor: theme.palette.success.main + "!important",
    },
    variantError: {
      backgroundColor: theme.palette.error.main + "!important",
    },
  })
);

export const AironeSnackbarProvider: FC = ({ children }) => {
  const classes = useStyles();
  return (
    <SnackbarProvider
      maxSnack={3}
      iconVariant={{
        success: <SuccessOutlinedIcon sx={{ fontSize: "20px", mr: "8px" }} />,
        error: <ErrorOutlineIcon sx={{ fontSize: "20px", mr: "8px" }} />,
      }}
      classes={classes}
    >
      {children}
    </SnackbarProvider>
  );
};
