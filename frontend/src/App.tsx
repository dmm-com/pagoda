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
      background: {
        default: "primary",
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
