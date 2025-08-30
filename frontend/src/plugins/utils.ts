import { ReactNode } from "react";

import { Plugin, PluginRoute, PluginAPI, PluginDefinition } from "./types";

/**
 * Helper function for creating plugins
 */
export function createPlugin(config: PluginDefinition): Plugin {
  return {
    ...config,
    components: [], // Empty array by default
  };
}

/**
 * Helper function for creating plugin routes
 */
export function createPluginRoute(config: {
  path: string;
  element: ReactNode | (() => ReactNode);
  priority?: number;
  override?: boolean;
  layout?: "default" | "minimal" | "custom";
}): PluginRoute {
  return {
    priority: 1000, // Default priority
    override: false, // Do not override by default
    layout: "default", // Default layout
    ...config,
  };
}

/**
 * Helper function for creating plugin components
 */
export function createPluginComponent(config: {
  id: string;
  component: ReactNode | (() => ReactNode);
  position?: string;
  priority?: number;
}): any {
  return {
    priority: 1000,
    position: "default",
    ...config,
  };
}

/**
 * Utility for checking plugin dependencies
 */
function validatePluginDependencies(
  plugin: Plugin,
  availablePlugins: Plugin[],
): { isValid: boolean; missingDependencies: string[] } {
  if (!plugin.dependencies || plugin.dependencies.length === 0) {
    return { isValid: true, missingDependencies: [] };
  }

  const availablePluginIds = new Set(availablePlugins.map((p) => p.id));
  const missingDependencies = plugin.dependencies.filter(
    (dep) => !availablePluginIds.has(dep),
  );

  return {
    isValid: missingDependencies.length === 0,
    missingDependencies,
  };
}

/**
 * Plugin version comparison utility
 */
function compareVersions(version1: string, version2: string): number {
  const v1Parts = version1.split(".").map(Number);
  const v2Parts = version2.split(".").map(Number);

  const maxLength = Math.max(v1Parts.length, v2Parts.length);

  for (let i = 0; i < maxLength; i++) {
    const v1Part = v1Parts[i] || 0;
    const v2Part = v2Parts[i] || 0;

    if (v1Part > v2Part) return 1;
    if (v1Part < v2Part) return -1;
  }

  return 0;
}

/**
 * Plugin configuration validation utility
 */
function validatePluginConfig(plugin: Plugin): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!plugin.id || typeof plugin.id !== "string") {
    errors.push("Plugin ID is required and must be a string");
  }

  if (!plugin.name || typeof plugin.name !== "string") {
    errors.push("Plugin name is required and must be a string");
  }

  if (!plugin.version || typeof plugin.version !== "string") {
    errors.push("Plugin version is required and must be a string");
  }

  // ID format check (alphanumeric, hyphen, underscore only)
  if (plugin.id && !/^[a-zA-Z0-9_-]+$/.test(plugin.id)) {
    errors.push(
      "Plugin ID must contain only alphanumeric characters, hyphens, and underscores",
    );
  }

  // Version format check (semantic versioning)
  if (
    plugin.version &&
    !/^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$/.test(plugin.version)
  ) {
    errors.push(
      "Plugin version must follow semantic versioning format (e.g., 1.0.0)",
    );
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Utility for outputting plugin debug information
 */
function debugPlugin(plugin: Plugin): void {
  if (process.env.NODE_ENV !== "development") {
    return;
  }

  console.group(`🔌 [Airone Plugin] Debug: ${plugin.name} (${plugin.id})`);
  console.log("Version:", plugin.version);
  console.log("Description:", plugin.description || "No description");
  console.log("Dependencies:", plugin.dependencies || "None");
  console.log("Priority:", plugin.priority || "Default (1000)");
  console.log("Routes:", plugin.routes?.length || 0);
  console.log("Components:", plugin.components?.length || 0);
  console.log("Config:", plugin.config || "None");
  console.groupEnd();
}

/**
 * Plugin performance measurement utility
 */
function measurePluginPerformance<T>(
  pluginId: string,
  operation: string,
  fn: () => T,
): T {
  if (process.env.NODE_ENV !== "development") {
    return fn();
  }

  const startTime = performance.now();
  const result = fn();
  const endTime = performance.now();

  console.log(
    `⏱️  [Airone Plugin] ${pluginId} - ${operation}: ${(endTime - startTime).toFixed(2)}ms`,
  );

  return result;
}

/**
 * Utility for asynchronous plugin initialization
 */
async function safePluginInitialize(
  plugin: Plugin,
  api: PluginAPI,
  timeout: number = 5000,
): Promise<{ success: boolean; error?: Error }> {
  if (!plugin.initialize) {
    return { success: true };
  }

  try {
    await Promise.race([
      plugin.initialize(api),
      new Promise((_, reject) =>
        setTimeout(
          () => reject(new Error("Plugin initialization timeout")),
          timeout,
        ),
      ),
    ]);

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error as Error,
    };
  }
}

/**
 * Plugin compatibility check utility
 */
function checkPluginCompatibility(
  plugin: Plugin,
  coreVersion: string,
): { compatible: boolean; reason?: string } {
  // Basic compatibility check
  if (!plugin.version) {
    return { compatible: false, reason: "Plugin version not specified" };
  }

  // TODO: More detailed compatibility check logic
  // Currently only basic validation
  const pluginVersionParts = plugin.version.split(".");
  const coreVersionParts = coreVersion.split(".");

  if (pluginVersionParts.length !== 3 || coreVersionParts.length !== 3) {
    return { compatible: false, reason: "Invalid version format" };
  }

  return { compatible: true };
}

/**
 * Utility for retrieving plugin statistics
 */
function getPluginStatistics(plugins: Plugin[]): {
  totalPlugins: number;
  pluginsByCategory: Record<string, number>;
  averagePriority: number;
  routesCount: number;
  componentsCount: number;
} {
  const totalPlugins = plugins.length;
  const pluginsByCategory: Record<string, number> = {};
  let totalPriority = 0;
  let routesCount = 0;
  let componentsCount = 0;

  plugins.forEach((plugin) => {
    // Category classification (using first part of ID)
    const category = plugin.id.split("-")[0] || "other";
    pluginsByCategory[category] = (pluginsByCategory[category] || 0) + 1;

    totalPriority += plugin.priority || 1000;
    routesCount += plugin.routes?.length || 0;
    componentsCount += plugin.components?.length || 0;
  });

  return {
    totalPlugins,
    pluginsByCategory,
    averagePriority: totalPlugins > 0 ? totalPriority / totalPlugins : 0,
    routesCount,
    componentsCount,
  };
}
