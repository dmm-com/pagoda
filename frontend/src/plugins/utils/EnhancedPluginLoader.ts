import type { Plugin } from "../types";

/**
 * External Plugin Loader
 *
 * Loads external npm modules as plugins only
 * Automatically discovers plugins using multiple strategies:
 * 1. External npm plugins: node_modules/airone-plugin-{name}/index.js
 * 2. Scoped npm plugins: node_modules/@{scope}/airone-plugin-{name}/index.js
 */
export class EnhancedPluginLoader {
  private static instance: EnhancedPluginLoader | null = null;
  private plugins: Plugin[] = [];
  private loaded = false;

  private constructor() {}

  static getInstance(): EnhancedPluginLoader {
    if (!EnhancedPluginLoader.instance) {
      EnhancedPluginLoader.instance = new EnhancedPluginLoader();
    }
    return EnhancedPluginLoader.instance;
  }

  /**
   * Load plugins from multiple sources
   */
  async loadPlugins(): Promise<Plugin[]> {
    if (this.loaded) {
      return this.plugins;
    }

    try {
      console.log(
        "[ExternalPluginLoader] Starting external plugin discovery...",
      );

      // Load plugins from external npm modules only
      const [npmPlugins, scopedPlugins] = await Promise.all([
        this.loadNpmPlugins(),
        this.loadScopedNpmPlugins(),
      ]);

      // Combine and deduplicate plugins
      const allPlugins = [...npmPlugins, ...scopedPlugins];
      const uniquePlugins = this.deduplicatePlugins(allPlugins);

      // Sort plugins by priority (higher priority first)
      uniquePlugins.sort((a, b) => {
        const priorityA = a.priority || 0;
        const priorityB = b.priority || 0;
        return priorityB - priorityA;
      });

      console.log(
        `[ExternalPluginLoader] Successfully loaded ${uniquePlugins.length} unique external plugins:`,
        uniquePlugins.map((p) => ({
          id: p.id,
          name: p.name,
          version: p.version,
          priority: p.priority,
          source: this.getPluginSource(p),
        })),
      );

      this.plugins = uniquePlugins;
      this.loaded = true;

      return this.plugins;
    } catch (error) {
      console.error(
        "[ExternalPluginLoader] Failed to load external plugins:",
        error,
      );
      return [];
    }
  }

  /**
   * Load npm plugins using static imports
   */
  private async loadNpmPlugins(): Promise<Plugin[]> {
    const plugins: Plugin[] = [];

    try {
      // Static imports to ensure webpack bundles correctly
      console.log(
        "[ExternalPluginLoader] Loading npm plugin: pagoda-plugin-hello-world",
      );
      const helloWorldPlugin = require("pagoda-plugin-hello-world");
      const plugin1 = helloWorldPlugin.default || helloWorldPlugin;

      if (this.isValidPlugin(plugin1)) {
        plugin1._source = "npm";
        plugins.push(plugin1 as Plugin);
      }
    } catch (error) {
      console.warn(
        "[ExternalPluginLoader] Failed to load pagoda-plugin-hello-world:",
        error,
      );
    }

    try {
      console.log(
        "[ExternalPluginLoader] Loading npm plugin: pagoda-plugin-dashboard",
      );
      const dashboardPlugin = require("pagoda-plugin-dashboard");
      const plugin2 = dashboardPlugin.default || dashboardPlugin;

      if (this.isValidPlugin(plugin2)) {
        plugin2._source = "npm";
        plugins.push(plugin2 as Plugin);
      }
    } catch (error) {
      console.warn(
        "[ExternalPluginLoader] Failed to load pagoda-plugin-dashboard:",
        error,
      );
    }

    return plugins;
  }

  /**
   * Load scoped npm plugins using dynamic imports
   */
  private async loadScopedNpmPlugins(): Promise<Plugin[]> {
    const plugins: Plugin[] = [];

    // List of known scoped plugins (in real scenario, this could be from config)
    const scopedPluginNames: string[] = []; // Add scoped plugin names here if any

    for (const pluginName of scopedPluginNames) {
      try {
        console.log(
          `[ExternalPluginLoader] Loading scoped npm plugin: ${pluginName}`,
        );
        const pluginModule = await import(pluginName);
        const plugin = pluginModule.default || pluginModule;

        if (this.isValidPlugin(plugin)) {
          plugin._source = "scoped-npm"; // Mark source
          plugins.push(plugin as Plugin);
        }
      } catch (error) {
        console.warn(
          `[ExternalPluginLoader] Failed to load scoped npm plugin ${pluginName}:`,
          error,
        );
      }
    }

    return plugins;
  }

  /**
   * Validate plugin structure
   */
  private isValidPlugin(plugin: any): boolean {
    // eslint-disable-line @typescript-eslint/no-explicit-any
    return (
      plugin &&
      typeof plugin === "object" &&
      plugin.id &&
      typeof plugin.id === "string" &&
      plugin.name &&
      typeof plugin.name === "string"
    );
  }

  /**
   * Remove duplicate plugins based on ID
   */
  private deduplicatePlugins(plugins: Plugin[]): Plugin[] {
    const seen = new Set<string>();
    return plugins.filter((plugin) => {
      if (seen.has(plugin.id)) {
        console.warn(
          `[ExternalPluginLoader] Duplicate plugin ID detected: ${plugin.id} - skipping`,
        );
        return false;
      }
      seen.add(plugin.id);
      return true;
    });
  }

  /**
   * Get plugin source type
   */
  private getPluginSource(plugin: any): string {
    // eslint-disable-line @typescript-eslint/no-explicit-any
    return plugin._source || "unknown";
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
   * Reset loader state (mainly for testing)
   */
  reset(): void {
    this.plugins = [];
    this.loaded = false;
  }
}

/**
 * Convenience function to load all plugins (enhanced version)
 */
export async function loadAllPluginsEnhanced(): Promise<Plugin[]> {
  const loader = EnhancedPluginLoader.getInstance();
  return await loader.loadPlugins();
}

/**
 * Get all loaded plugins (enhanced version)
 */
export function getLoadedPluginsEnhanced(): Plugin[] {
  const loader = EnhancedPluginLoader.getInstance();
  return loader.getPlugins();
}
