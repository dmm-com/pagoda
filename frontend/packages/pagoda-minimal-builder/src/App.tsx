import React from "react";
import { createRoot } from "react-dom/client";
import { ThemeProvider } from "@mui/material";
import { SnackbarProvider } from "notistack";

// Import from @dmm-com/pagoda-core
import { AppBase } from "@dmm-com/pagoda-core";
import { theme } from "@dmm-com/pagoda-core";

// Import plugins directly
import helloWorldPlugin from "pagoda-plugin-hello-world";
import dashboardPlugin from "pagoda-plugin-dashboard";

console.log("📦 [Pagoda Minimal Builder] Loading - WITH DIRECT PLUGIN IMPORTS");

// Initialize with direct plugin imports
const initializeApp = async () => {
  try {
    // Use directly imported plugins
    const plugins = [helloWorldPlugin, dashboardPlugin].filter(Boolean);
    console.log(
      `[Pagoda Minimal Builder] Loaded ${plugins.length} plugins:`,
      plugins.map((p) => ({ id: p.id, name: p.name })),
    );

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
