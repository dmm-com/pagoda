import {
  Plugin,
  PluginRegistry as IPluginRegistry,
  PluginRoute,
  PluginComponent,
  PluginConfig,
  PluginErrorHandler,
  ComponentPosition,
  PluginAPI,
} from "./types";

class DefaultPluginErrorHandler implements PluginErrorHandler {
  onLoadError(plugin: Plugin, error: Error): void {
    console.error(`[Airone Plugin] ${plugin.id} failed to load:`, error);
  }

  onInitError(plugin: Plugin, error: Error): void {
    console.error(`[Airone Plugin] ${plugin.id} failed to initialize:`, error);
  }

  onRuntimeError(plugin: Plugin, error: Error, context: unknown): void {
    console.error(
      `[Airone Plugin] ${plugin.id} runtime error:`,
      error,
      context,
    );
  }

  onDependencyError(plugin: Plugin, missingDeps: string[]): void {
    console.error(
      `[Airone Plugin] ${plugin.id} missing dependencies:`,
      missingDeps,
    );
  }

  onPermissionError(plugin: Plugin, action: string): void {
    console.error(
      `[Airone Plugin] ${plugin.id} permission denied for action:`,
      action,
    );
  }
}

export class PluginRegistry implements IPluginRegistry {
  private plugins = new Map<string, Plugin>();
  private disabledPlugins = new Set<string>();
  private initializedPlugins = new Set<string>();
  private config: PluginConfig | null = null;
  private errorHandler: PluginErrorHandler;
  private apiFactory?: () => PluginAPI;

  constructor(errorHandler?: PluginErrorHandler) {
    this.errorHandler = errorHandler || new DefaultPluginErrorHandler();
  }

  setConfig(config: PluginConfig): void {
    this.config = config;
  }

  setAPIFactory(factory: () => PluginAPI): void {
    this.apiFactory = factory;
  }

  registerPlugin(plugin: Plugin): void {
    try {
      // Check for duplicate plugin ID
      if (this.plugins.has(plugin.id)) {
        throw new Error(`Plugin with ID "${plugin.id}" is already registered`);
      }

      // Basic validation
      this.validatePlugin(plugin);

      // Determine enabled/disabled based on configuration
      if (this.config?.plugins[plugin.id]?.enabled === false) {
        this.disabledPlugins.add(plugin.id);
        console.info(
          `[Airone Plugin] ${plugin.id} is disabled by configuration`,
        );
        return;
      }

      // Register the plugin
      this.plugins.set(plugin.id, plugin);

      console.info(
        `[Airone Plugin] ${plugin.id} (${plugin.name} v${plugin.version}) registered successfully`,
      );
    } catch (error) {
      this.errorHandler.onLoadError(plugin, error as Error);
      throw error;
    }
  }

  getPlugin(id: string): Plugin | undefined {
    return this.plugins.get(id);
  }

  getAllPlugins(): Plugin[] {
    return Array.from(this.plugins.values());
  }

  getEnabledPlugins(): Plugin[] {
    return Array.from(this.plugins.values()).filter(
      (plugin) => !this.disabledPlugins.has(plugin.id),
    );
  }

  async initializePlugins(): Promise<void> {
    const enabledPlugins = this.getEnabledPlugins();

    if (enabledPlugins.length === 0) {
      console.info("[Airone Plugin] No plugins to initialize");
      return;
    }

    // Sort by dependency order
    const sortedPlugins = this.sortPluginsByDependencies(enabledPlugins);

    console.info(
      `[Airone Plugin] Initializing ${sortedPlugins.length} plugins...`,
    );

    for (const plugin of sortedPlugins) {
      try {
        // Check dependencies
        if (plugin.dependencies) {
          const missingDeps = plugin.dependencies.filter(
            (depId) =>
              !this.plugins.has(depId) || this.disabledPlugins.has(depId),
          );

          if (missingDeps.length > 0) {
            this.errorHandler.onDependencyError(plugin, missingDeps);
            this.disabledPlugins.add(plugin.id);
            continue;
          }
        }

        // Initialize process
        if (plugin.initialize && this.apiFactory) {
          const api = this.apiFactory();
          await plugin.initialize(api);
        }

        // Activate process
        if (plugin.activate) {
          await plugin.activate();
        }

        this.initializedPlugins.add(plugin.id);
        console.info(`[Airone Plugin] ${plugin.id} initialized successfully`);
      } catch (error) {
        this.errorHandler.onInitError(plugin, error as Error);
        this.disabledPlugins.add(plugin.id);
      }
    }

    const successCount = this.initializedPlugins.size;
    console.info(
      `[Airone Plugin] Plugin initialization completed: ${successCount}/${enabledPlugins.length} plugins initialized`,
    );
  }

  disablePlugin(id: string): void {
    const plugin = this.plugins.get(id);
    if (!plugin) {
      console.warn(`[Airone Plugin] Plugin ${id} not found`);
      return;
    }

    try {
      // Deactivate process
      if (plugin.deactivate && this.initializedPlugins.has(id)) {
        plugin.deactivate();
      }

      this.disabledPlugins.add(id);
      this.initializedPlugins.delete(id);
      console.info(`[Airone Plugin] ${id} disabled`);
    } catch (error) {
      this.errorHandler.onRuntimeError(plugin, error as Error, {
        action: "disable",
      });
    }
  }

  getRoutes(): PluginRoute[] {
    console.log("[PluginRegistry] 🛣️  Getting all plugin routes...");
    const routes: PluginRoute[] = [];

    const enabledPlugins = this.getEnabledPlugins();
    console.log(
      "[PluginRegistry] 📋 Enabled plugins:",
      enabledPlugins.map((p) => ({
        id: p.id,
        name: p.name,
        hasRoutes: !!p.routes,
        routeCount: p.routes?.length || 0,
      })),
    );

    for (const plugin of enabledPlugins) {
      if (plugin.routes) {
        console.log(
          `[PluginRegistry] 📍 Adding ${plugin.routes.length} routes from plugin: ${plugin.id}`,
        );
        plugin.routes.forEach((route, index) => {
          console.log(
            `[PluginRegistry]   Route ${index + 1}: ${route.path} (priority: ${route.priority || "default"})`,
          );
        });
        routes.push(...plugin.routes);
      } else {
        console.log(`[PluginRegistry] ❌ Plugin ${plugin.id} has no routes`);
      }
    }

    console.log(`[PluginRegistry] 🔢 Total routes collected: ${routes.length}`);

    // Sort by priority (plugin priority → route priority)
    const sortedRoutes = routes.sort((a, b) => {
      const aPluginPriority = this.getPluginByRoute(a)?.priority || 1000;
      const bPluginPriority = this.getPluginByRoute(b)?.priority || 1000;

      if (aPluginPriority !== bPluginPriority) {
        return aPluginPriority - bPluginPriority;
      }

      return (a.priority || 1000) - (b.priority || 1000);
    });

    console.log(
      "[PluginRegistry] ✅ Final sorted routes:",
      sortedRoutes.map((r) => ({ path: r.path, priority: r.priority })),
    );
    return sortedRoutes;
  }

  getComponents(location?: ComponentPosition["location"]): PluginComponent[] {
    const components: PluginComponent[] = [];

    for (const plugin of this.getEnabledPlugins()) {
      if (plugin.components) {
        let pluginComponents = plugin.components;

        // Filter by location
        if (location) {
          pluginComponents = pluginComponents.filter(
            (comp) => comp.position?.location === location,
          );
        }

        components.push(...pluginComponents);
      }
    }

    // Sort by order
    return components.sort((a, b) => {
      return (a.position?.order || 1000) - (b.position?.order || 1000);
    });
  }

  private validatePlugin(plugin: Plugin): void {
    if (!plugin.id || typeof plugin.id !== "string") {
      throw new Error("Plugin must have a valid string ID");
    }

    if (!plugin.name || typeof plugin.name !== "string") {
      throw new Error("Plugin must have a valid name");
    }

    if (!plugin.version || typeof plugin.version !== "string") {
      throw new Error("Plugin must have a valid version");
    }

    // Check ID format (alphanumeric, hyphen, underscore only)
    if (!/^[a-zA-Z0-9_-]+$/.test(plugin.id)) {
      throw new Error(
        "Plugin ID must contain only alphanumeric characters, hyphens, and underscores",
      );
    }

    // Check version format (semantic versioning)
    if (
      !/^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$/.test(
        plugin.version,
      )
    ) {
      throw new Error(
        "Plugin version must follow semantic versioning format (e.g., 1.0.0)",
      );
    }
  }

  private sortPluginsByDependencies(plugins: Plugin[]): Plugin[] {
    const sorted: Plugin[] = [];
    const visited = new Set<string>();
    const visiting = new Set<string>();

    const visit = (plugin: Plugin): void => {
      if (visiting.has(plugin.id)) {
        console.error(
          `[Airone Plugin] Circular dependency detected for plugin ${plugin.id}`,
        );
        return;
      }

      if (visited.has(plugin.id)) {
        return;
      }

      visiting.add(plugin.id);

      // Process dependencies first
      if (plugin.dependencies) {
        for (const depId of plugin.dependencies) {
          const depPlugin = plugins.find((p) => p.id === depId);
          if (depPlugin) {
            visit(depPlugin);
          }
        }
      }

      visiting.delete(plugin.id);
      visited.add(plugin.id);
      sorted.push(plugin);
    };

    for (const plugin of plugins) {
      visit(plugin);
    }

    return sorted;
  }

  private getPluginByRoute(route: PluginRoute): Plugin | undefined {
    for (const plugin of this.getEnabledPlugins()) {
      if (plugin.routes?.includes(route)) {
        return plugin;
      }
    }
    return undefined;
  }

  // Get plugin statistics
  getStatistics(): {
    total: number;
    enabled: number;
    initialized: number;
    disabled: number;
  } {
    return {
      total: this.plugins.size,
      enabled: this.getEnabledPlugins().length,
      initialized: this.initializedPlugins.size,
      disabled: this.disabledPlugins.size,
    };
  }
}
