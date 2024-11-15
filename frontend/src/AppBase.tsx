import { ThemeProvider } from "@mui/material/styles";
import React, { FC, StrictMode } from "react";

import { AironeSnackbarProvider } from "AironeSnackbarProvider";
import { ErrorHandler } from "ErrorHandler";
import { theme } from "Theme";
import { CheckTerms } from "components/common/CheckTerms";
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
    <StrictMode>
      <ThemeProvider theme={theme}>
        <AironeSnackbarProvider>
          <ErrorHandler>
            <CheckTerms>
              <AppRouter customRoutes={customRoutes} />
            </CheckTerms>
          </ErrorHandler>
        </AironeSnackbarProvider>
      </ThemeProvider>
    </StrictMode>
  );
};
