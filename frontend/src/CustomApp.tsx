import { createTheme, ThemeProvider } from "@mui/material/styles";
import React from "react";
import { FC } from "react";
import ReactDOM from "react-dom";

import { AppRouter } from "./AppRouter";
import { ErrorHandler } from "./ErrorHandler";
import { entityPath } from "./Routes";
import { NetworkEntity } from "./pages/Entity";

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

  // Get path statically or dynamically???
  // NOTE dummy routing config
  const customRoutes = [
    {
      path: entityPath("100"), // 100 is network
      component: NetworkEntity,
    },
  ];

  return (
    <ThemeProvider theme={theme}>
      <ErrorHandler>
        <AppRouter customRoutes={customRoutes} />
      </ErrorHandler>
    </ThemeProvider>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
