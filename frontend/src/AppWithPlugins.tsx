import { ThemeProvider } from "@mui/material";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Import plugins directly - same approach as pagoda-minimal-builder
import helloWorldPlugin from "pagoda-plugin-hello-world";
import dashboardPlugin from "pagoda-plugin-dashboard";

import type { Plugin } from "plugins";

import { AironeSnackbarProvider } from "AironeSnackbarProvider";
import { AppBase } from "AppBase";
import { theme } from "Theme";

console.log("🚀 [AppWithPlugins] Loading - WITH DIRECT PLUGIN IMPORTS");

const container = document.getElementById("app");
if (container == null) {
  throw new Error("failed to initializer React app.");
}

// Direct Plugin Component - simplified approach
function AppWithDirectPlugins() {
  // Use directly imported plugins - same as pagoda-minimal-builder
  const plugins = [helloWorldPlugin, dashboardPlugin].filter(Boolean) as Plugin[];
  
  console.log(
    "[Airone] Loaded plugins directly:",
    plugins.map((p: Plugin) => ({
      id: p.id,
      name: p.name,
      version: p.version,
      priority: p.priority,
    })),
  );

  return (
    <StrictMode>
      <ThemeProvider theme={theme}>
        <AironeSnackbarProvider>
          <AppBase plugins={plugins} />
        </AironeSnackbarProvider>
      </ThemeProvider>
    </StrictMode>
  );
}

const root = createRoot(container);
root.render(<AppWithDirectPlugins />);
