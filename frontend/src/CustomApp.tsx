import { createTheme, ThemeProvider } from "@mui/material/styles";
import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

import { CustomAppRouter } from "./CustomAppRouter";
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
    breakpoints: {
      values: {
        xs: 0,
        sm: 600,
        md: 900,
        lg: 1064,
        xl: 1536,
      },
    },
    typography: {
      fontFamily: "Noto Sans JP",
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
