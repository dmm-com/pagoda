import { ThemeProvider } from "@mui/material/styles";
import React, { FC } from "react";
import { createRoot } from "react-dom/client";

import { AironeSnackbarProvider } from "AironeSnackbarProvider";
import { AppRouter } from "AppRouter";
import { CheckTermsService } from "CheckTermsService";
import { ErrorHandler } from "ErrorHandler";
import { theme } from "Theme";
import "i18n/config";

const App: FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <AironeSnackbarProvider>
        <ErrorHandler>
          <CheckTermsService>
            <AppRouter />
          </CheckTermsService>
        </ErrorHandler>
      </AironeSnackbarProvider>
    </ThemeProvider>
  );
};

const container = document.getElementById("app");
if (container == null) {
  throw new Error("failed to initializer React app.");
}
const root = createRoot(container);
root.render(<App />);
