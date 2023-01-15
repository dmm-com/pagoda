import ErrorOutlinedIcon from "@mui/icons-material/ErrorOutlined";
import SuccessOutlinedIcon from "@mui/material/internal/svg-icons/SuccessOutlined";
import { styled } from "@mui/material/styles";
import { SnackbarProvider } from "notistack";
import React, { FC } from "react";

const StyledSnackbarProvider = styled(SnackbarProvider)(({ theme }) => ({
  variantSuccess: {
    backgroundColor: theme.palette.success.main + "!important",
  },
  variantError: {
    backgroundColor: theme.palette.error.main + "!important",
  },
}));

export const AironeSnackbarProvider: FC = ({ children }) => {
  return (
    <StyledSnackbarProvider
      maxSnack={3}
      iconVariant={{
        success: <SuccessOutlinedIcon sx={{ fontSize: "20px", mr: "8px" }} />,
        error: <ErrorOutlinedIcon sx={{ fontSize: "20px", mr: "8px" }} />,
      }}
    >
      {children}
    </StyledSnackbarProvider>
  );
};
