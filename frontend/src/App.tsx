import { ThemeProvider } from "@mui/material/styles";
import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

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

ReactDOM.render(<App />, document.getElementById("app"));
