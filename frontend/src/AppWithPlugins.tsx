import { ThemeProvider } from "@mui/material";
import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { loadAllPlugins } from "./plugins/utils/DynamicPluginLoader";

import type { Plugin } from "plugins";

import { AironeSnackbarProvider } from "AironeSnackbarProvider";
import { AppBase } from "AppBase";
import { theme } from "Theme";

console.log("🚀 [AppWithPlugins] Loading - PLUGIN VERSION ACTIVE");

const container = document.getElementById("app");
if (container == null) {
  throw new Error("failed to initializer React app.");
}

// Dynamic Plugin Loader Component
function AppWithDynamicPlugins() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPlugins = async () => {
      try {
        console.log("[Airone] Starting dynamic plugin discovery...");
        console.log(
          "[Airone] loadAllPlugins function type:",
          typeof loadAllPlugins,
        );
        console.log("[Airone] loadAllPlugins function:", loadAllPlugins);

        const discoveredPlugins = await loadAllPlugins();

        console.log(
          "[Airone] Successfully loaded plugins:",
          discoveredPlugins.map((p) => ({
            id: p.id,
            name: p.name,
            version: p.version,
            priority: p.priority,
          })),
        );

        setPlugins(discoveredPlugins);
      } catch (error) {
        console.error("[Airone] Failed to load plugins:", error);
        console.error("[Airone] Error details:", error.stack);
        // Continue with empty plugins array
        setPlugins([]);
      } finally {
        setLoading(false);
      }
    };

    console.log("[Airone] AppWithDynamicPlugins component mounted");
    loadPlugins();
  }, []);

  if (loading) {
    // Show loading state while discovering plugins
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <div>
          <div>Loading plugins...</div>
          <div style={{ fontSize: "0.8em", color: "#666", marginTop: "8px" }}>
            Scanning frontend/packages/ for available plugins
          </div>
        </div>
      </div>
    );
  }

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
root.render(<AppWithDynamicPlugins />);
