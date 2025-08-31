import { FC, ReactNode, useState, useEffect } from "react";

import { ErrorHandler } from "ErrorHandler";
import { CheckTerms } from "components/common/CheckTerms";
import { PluginRegistry, PluginErrorBoundary, createPluginAPI } from "plugins";
import { AppRouter } from "routes/AppRouter";
import "i18n/config";

interface Props {
  customRoutes?: {
    path: string;
    element: ReactNode;
  }[];
  plugins?: any[]; // External plugins to load
}

export const AppBase: FC<Props> = ({ customRoutes, plugins = [] }) => {
  const [pluginRoutes, setPluginRoutes] = useState<
    { path: string; element: ReactNode }[]
  >([]);
  const [pluginsLoaded, setPluginsLoaded] = useState(false);

  useEffect(() => {
    const initializePlugins = async () => {
      if (plugins.length === 0) {
        setPluginsLoaded(true);
        return;
      }

      try {
        // Create plugin registry
        const registry = new PluginRegistry();

        // Set up API factory for plugins
        registry.setAPIFactory(() =>
          createPluginAPI("pagoda-core", {
            navigate: (to: string) => {
              // In a real implementation, this would use react-router navigation
              console.log("[Plugin Navigation]:", to);
            },
            enqueueSnackbar: (message: string) => {
              // In a real implementation, this would use notistack
              console.log("[Plugin Notification]:", message);
            },
          }),
        );

        // Register external plugins
        plugins.forEach((plugin) => {
          registry.registerPlugin(plugin);
        });

        // Initialize plugins
        await registry.initializePlugins();

        // Convert plugin routes to React Router format
        console.log("[AppBase] 🔍 Getting routes from registry...");
        const pluginRouteData = registry.getRoutes();
        console.log(
          "[AppBase] 📋 Raw plugin route data from registry:",
          pluginRouteData,
        );

        const routes = pluginRouteData.map((route: any) => ({
          path: route.path,
          element: route.element,
        }));

        console.log("[AppBase] 🛣️  Converted routes for React Router:", routes);

        setPluginRoutes(routes);
        setPluginsLoaded(true);

        console.log(
          `[Pagoda Core] Initialized ${plugins.length} plugins with ${routes.length} routes`,
        );
      } catch (error) {
        console.error("[Pagoda Core] Failed to initialize plugins:", error);
        setPluginsLoaded(true);
      }
    };

    initializePlugins();
  }, [plugins]);

  if (!pluginsLoaded) {
    return (
      <ErrorHandler>
        <div>Loading plugins...</div>
      </ErrorHandler>
    );
  }

  // Combine custom routes with plugin routes
  console.log(
    "[AppBase] Plugin routes:",
    pluginRoutes.map((r) => ({
      path: r.path,
      priority: (r as any).priority,
      layout: (r as any).layout,
      componentName: (r.element as any)?.name || "Unknown",
    })),
  );

  const allCustomRoutes = [...(customRoutes || []), ...pluginRoutes];

  console.log(
    "[AppBase] All custom routes:",
    allCustomRoutes.length,
    "routes total",
  );

  return (
    <ErrorHandler>
      <CheckTerms>
        <PluginErrorBoundary>
          <AppRouter customRoutes={allCustomRoutes} />
        </PluginErrorBoundary>
      </CheckTerms>
    </ErrorHandler>
  );
};
