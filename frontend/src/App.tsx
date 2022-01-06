import { createTheme, ThemeProvider } from "@mui/material/styles";
import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "./AppRouter";
import { ErrorHandler } from "./ErrorHandler";

const App: FC = () => {
  const theme = createTheme({
    palette: {
      primary: {
        main: "#607D8B",
      },
      secondary: {
        main: "#90CAF9",
      },
      background: {
        default: "#607D8B",
      },
    },
  });
  return (
    <ThemeProvider theme={theme}>
      <ErrorHandler>
        <AppRouter />
      </ErrorHandler>
    </ThemeProvider>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
