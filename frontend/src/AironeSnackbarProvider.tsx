import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";
import ErrorOutlinedIcon from "@mui/icons-material/ErrorOutlined";
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

export const AironeSnackbarProvider: FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  return (
    <StyledSnackbarProvider
      maxSnack={3}
      iconVariant={{
        success: (
          <CheckCircleOutlineOutlinedIcon
            sx={{ fontSize: "20px", mr: "8px" }}
          />
        ),
        error: <ErrorOutlinedIcon sx={{ fontSize: "20px", mr: "8px" }} />,
      }}
    >
      {children}
    </StyledSnackbarProvider>
  );
};
