import type { Plugin } from "../types";

/**
 * Dynamic Plugin Loader
 * Automatically discovers and loads all plugins from frontend/packages/
 */
export class DynamicPluginLoader {
  private static instance: DynamicPluginLoader | null = null;
  private plugins: Plugin[] = [];
  private loaded = false;

  private constructor() {}

  static getInstance(): DynamicPluginLoader {
    if (!DynamicPluginLoader.instance) {
      DynamicPluginLoader.instance = new DynamicPluginLoader();
    }
    return DynamicPluginLoader.instance;
  }

  /**
   * Dynamically load all plugins from frontend/packages/
   */
  async loadPlugins(): Promise<Plugin[]> {
    if (this.loaded) {
      return this.plugins;
    }

    try {
      console.log("[DynamicPluginLoader] Starting plugin discovery...");

      const plugins: Plugin[] = [];

      // Load hello-world plugin
      try {
        const helloWorldContext = (require as any).context(
          // eslint-disable-line @typescript-eslint/no-explicit-any
          "../../../packages/plugin-hello-world/src",
          false,
          /index\.ts$/,
        );

        const keys = helloWorldContext.keys();
        if (keys.length > 0) {
          const pluginModule = helloWorldContext(keys[0]);
          const plugin = pluginModule.default || pluginModule;
          if (plugin && plugin.id) {
            console.log(
              `[DynamicPluginLoader] Found hello-world plugin: ${plugin.id}`,
            );
            plugins.push(plugin as Plugin);
          }
        }
      } catch (error) {
        console.warn(
          "[DynamicPluginLoader] Hello-world plugin not available:",
          error,
        );
      }

      // Load dashboard plugin
      try {
        const dashboardContext = (require as any).context(
          // eslint-disable-line @typescript-eslint/no-explicit-any
          "../../../packages/plugin-dashboard/src",
          false,
          /index\.ts$/,
        );

        const keys = dashboardContext.keys();
        if (keys.length > 0) {
          const pluginModule = dashboardContext(keys[0]);
          const plugin = pluginModule.default || pluginModule;
          if (plugin && plugin.id) {
            console.log(
              `[DynamicPluginLoader] Found dashboard plugin: ${plugin.id}`,
            );
            plugins.push(plugin as Plugin);
          }
        }
      } catch (error) {
        console.warn(
          "[DynamicPluginLoader] Dashboard plugin not available:",
          error,
        );
      }

      // Sort plugins by priority
      plugins.sort((a, b) => {
        const priorityA = a.priority || 0;
        const priorityB = b.priority || 0;
        return priorityB - priorityA;
      });

      console.log(
        `[DynamicPluginLoader] Successfully loaded ${plugins.length} plugins:`,
        plugins.map((p) => ({ id: p.id, name: p.name, version: p.version })),
      );

      this.plugins = plugins;
      this.loaded = true;

      return this.plugins;
    } catch (error) {
      console.error("[DynamicPluginLoader] Failed to load plugins:", error);
      return [];
    }
  }

  /**
   * Get all loaded plugins
   */
  getPlugins(): Plugin[] {
    return this.plugins;
  }

  /**
   * Get plugin by ID
   */
  getPlugin(id: string): Plugin | undefined {
    return this.plugins.find((p) => p.id === id);
  }

  /**
   * Reset loader state
   */
  reset(): void {
    this.plugins = [];
    this.loaded = false;
  }
}

/**
 * Convenience function to load all plugins
 */
export async function loadAllPlugins(): Promise<Plugin[]> {
  const loader = DynamicPluginLoader.getInstance();
  return await loader.loadPlugins();
}

/**
 * Get all loaded plugins
 */
export function getLoadedPlugins(): Plugin[] {
  const loader = DynamicPluginLoader.getInstance();
  return loader.getPlugins();
}
