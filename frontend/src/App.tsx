import { ThemeProvider } from "@mui/material/styles";
import React from "react";
import { FC } from "react";
import { createRoot } from "react-dom/client";

import { AironeSnackbarProvider } from "AironeSnackbarProvider";
import { AppRouter } from "AppRouter";
import { ErrorHandler } from "ErrorHandler";
import { theme } from "Theme";

const App: FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <ErrorHandler>
        <AironeSnackbarProvider>
          <AppRouter />
        </AironeSnackbarProvider>
      </ErrorHandler>
    </ThemeProvider>
  );
};

const container = document.getElementById("app");
const root = createRoot(container);
root.render(<App />);
