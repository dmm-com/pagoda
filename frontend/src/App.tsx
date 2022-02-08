import { ThemeProvider } from "@mui/material/styles";
import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "./AppRouter";
import { ErrorHandler } from "./ErrorHandler";
import { theme } from "./Theme";

const App: FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <ErrorHandler>
        <AppRouter />
      </ErrorHandler>
    </ThemeProvider>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
