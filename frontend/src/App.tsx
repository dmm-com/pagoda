import { ThemeProvider } from "@mui/material";
import React, { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AironeSnackbarProvider } from "AironeSnackbarProvider";
import { AppBase } from "AppBase";
import { theme } from "Theme";

const container = document.getElementById("app");
if (container == null) {
  throw new Error("failed to initializer React app.");
}
const root = createRoot(container);
root.render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <AironeSnackbarProvider>
        <AppBase />
      </AironeSnackbarProvider>
    </ThemeProvider>
  </StrictMode>,
);
