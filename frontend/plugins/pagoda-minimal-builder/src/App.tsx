import React from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider } from "@mui/material";
import { SnackbarProvider } from "notistack";

import { AppBase } from "@dmm-com/pagoda-core";
import { theme } from "@dmm-com/pagoda-core";
import { configuredPlugins } from "./generatedPlugins";

// Render app
const container = document.getElementById("app");
if (container == null) {
  throw new Error("failed to initialize React app.");
}

const root = createRoot(container);
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <SnackbarProvider>
        <AppBase plugins={configuredPlugins} />
      </SnackbarProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
