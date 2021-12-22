import { createTheme, ThemeProvider } from "@mui/material/styles";
import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "./AppRouter";
import { ErrorHandler } from "./ErrorHandler";

const App: FC = () => {
  const theme = createTheme();
  return (
    <ThemeProvider theme={theme}>
      <ErrorHandler>
        <AppRouter />
      </ErrorHandler>
    </ThemeProvider>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
