import { ThemeProvider } from "@mui/material/styles";
import { SnackbarProvider } from "notistack";
import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "AppRouter";
import { ErrorHandler } from "ErrorHandler";
import { theme } from "Theme";

const App: FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <ErrorHandler>
        {/* TODO does it unable to apply custom styles? reimplement it ourselves? */}
        <SnackbarProvider maxSnack={3}>
          <AppRouter />
        </SnackbarProvider>
      </ErrorHandler>
    </ThemeProvider>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
