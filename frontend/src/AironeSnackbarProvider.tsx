import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";
import ErrorOutlinedIcon from "@mui/icons-material/ErrorOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import { styled } from "@mui/material/styles";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode } from "react";

const StyledSnackbarProvider = styled(SnackbarProvider)(({ theme }) => ({
  variantSuccess: {
    backgroundColor: theme.palette.success.main + "!important",
  },
  variantError: {
    backgroundColor: theme.palette.error.main + "!important",
  },
  variantWarning: {
    backgroundColor: theme.palette.warning.main + "!important",
  },
  variantInfo: {
    backgroundColor: theme.palette.info.main + "!important",
  },
}));

export const AironeSnackbarProvider: FC<{ children: ReactNode }> = ({
  children,
}) => {
  return (
    <StyledSnackbarProvider
      maxSnack={5}
      iconVariant={{
        success: (
          <CheckCircleOutlineOutlinedIcon
            sx={{ fontSize: "20px", mr: "8px" }}
          />
        ),
        error: <ErrorOutlinedIcon sx={{ fontSize: "20px", mr: "8px" }} />,
        warning: (
          <WarningAmberOutlinedIcon sx={{ fontSize: "20px", mr: "8px" }} />
        ),
        info: <InfoOutlinedIcon sx={{ fontSize: "20px", mr: "8px" }} />,
      }}
    >
      {children}
    </StyledSnackbarProvider>
  );
};
