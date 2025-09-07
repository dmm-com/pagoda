import React from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider } from "@mui/material";
import { SnackbarProvider } from "notistack";

// Import from @dmm-com/pagoda-core
import { AppBase } from "@dmm-com/pagoda-core";
import { theme } from "@dmm-com/pagoda-core";

// Import generated plugin list
import { configuredPlugins } from "./generatedPlugins";

// Initialize with configurable plugins
const initializeApp = async () => {
  try {
    // Use plugins from generated imports
    const plugins = configuredPlugins;

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
            <AppBase plugins={plugins} />
          </SnackbarProvider>
        </ThemeProvider>
      </React.StrictMode>,
    );
  } catch (error) {
    console.error("[Pagoda Minimal Builder] Failed to initialize app:", error);
  }
};

// Initialize app
initializeApp();
