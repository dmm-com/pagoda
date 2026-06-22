import CheckCircleOutlineOutlinedIcon from "@mui/icons-material/CheckCircleOutlineOutlined";
import ErrorOutlinedIcon from "@mui/icons-material/ErrorOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode } from "react";

export const AironeSnackbarProvider: FC<{ children: ReactNode }> = ({
  children,
}) => {
  return (
    <SnackbarProvider
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
    </SnackbarProvider>
  );
};
