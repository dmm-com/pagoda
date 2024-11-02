import { ThemeProvider } from "@mui/material/styles";
import React, { FC } from "react";

import { AironeSnackbarProvider } from "AironeSnackbarProvider";
import { CheckTermsService } from "CheckTermsService";
import { ErrorHandler } from "ErrorHandler";
import { theme } from "Theme";
import { AppRouter } from "routes/AppRouter";
import "i18n/config";

interface Props {
  customRoutes?: {
    path: string;
    element: React.ReactNode;
  }[];
}

export const AppBase: FC<Props> = ({ customRoutes }) => {
  return (
    <ThemeProvider theme={theme}>
      <AironeSnackbarProvider>
        <ErrorHandler>
          <CheckTermsService>
            <AppRouter customRoutes={customRoutes} />
          </CheckTermsService>
        </ErrorHandler>
      </AironeSnackbarProvider>
    </ThemeProvider>
  );
};
