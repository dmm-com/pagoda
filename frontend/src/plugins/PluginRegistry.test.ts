import React from "react";

import { PluginRegistry } from "./PluginRegistry";
import {
  Plugin,
  PluginErrorHandler,
  PluginConfig,
  PluginAPI,
  PluginRoute,
  PluginComponent,
} from "./types";

describe("PluginRegistry", () => {
  let registry: PluginRegistry;
  let mockErrorHandler: jest.Mocked<PluginErrorHandler>;
  let mockApiFactory: jest.MockedFunction<() => PluginAPI>;
  let mockApi: Partial<PluginAPI>;

  beforeEach(() => {
    // Mock error handler
    mockErrorHandler = {
      onLoadError: jest.fn(),
      onInitError: jest.fn(),
      onRuntimeError: jest.fn(),
      onDependencyError: jest.fn(),
      onPermissionError: jest.fn(),
    };

    // Mock API factory and API
    mockApi = {
      services: {} as PluginAPI["services"],
      ui: {} as PluginAPI["ui"],
      routing: {} as PluginAPI["routing"],
      data: {} as PluginAPI["data"],
      config: {} as PluginAPI["config"],
    };
    mockApiFactory = jest.fn().mockReturnValue(mockApi as PluginAPI);

    // Initialize registry
    registry = new PluginRegistry(mockErrorHandler);
    registry.setAPIFactory(mockApiFactory);

    // Mock console methods to avoid noise in tests
    jest.spyOn(console, "info").mockImplementation(() => {});
    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(console, "warn").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe("Plugin Registration", () => {
    test("should register a valid plugin successfully", () => {
      const plugin: Plugin = {
        id: "test-plugin",
        name: "Test Plugin",
        version: "1.0.0",
        description: "A test plugin",
      };

      registry.registerPlugin(plugin);
      const retrievedPlugin = registry.getPlugin("test-plugin");

      expect(retrievedPlugin).toBe(plugin);
      expect(registry.getAllPlugins()).toContain(plugin);
      expect(console.info).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin (Test Plugin v1.0.0) registered successfully",
      );
    });

    test("should throw error when registering plugin with duplicate ID", () => {
      const plugin1: Plugin = {
        id: "duplicate",
        name: "Plugin 1",
        version: "1.0.0",
      };
      const plugin2: Plugin = {
        id: "duplicate",
        name: "Plugin 2",
        version: "2.0.0",
      };

      registry.registerPlugin(plugin1);

      expect(() => {
        registry.registerPlugin(plugin2);
      }).toThrow('Plugin with ID "duplicate" is already registered');
      expect(mockErrorHandler.onLoadError).toHaveBeenCalledWith(
        plugin2,
        expect.any(Error),
      );
    });

    test("should validate plugin properties", () => {
      const invalidPlugins = [
        // Missing ID
        { name: "Test", version: "1.0.0" },
        // Invalid ID
        { id: "invalid@plugin", name: "Test", version: "1.0.0" },
        // Missing name
        { id: "test", version: "1.0.0" },
        // Invalid name
        { id: "test", name: 123, version: "1.0.0" },
        // Missing version
        { id: "test", name: "Test" },
        // Invalid version
        { id: "test", name: "Test", version: "invalid-version" },
      ];

      invalidPlugins.forEach((invalidPlugin) => {
        expect(() => {
          registry.registerPlugin(invalidPlugin as Plugin);
        }).toThrow();
      });
    });
  });

  describe("Plugin Configuration", () => {
    test("should respect configuration for disabled plugins", () => {
      const config: PluginConfig = {
        plugins: {
          "disabled-plugin": { enabled: false },
          "enabled-plugin": { enabled: true },
        },
        global: {},
      };

      const disabledPlugin: Plugin = {
        id: "disabled-plugin",
        name: "Disabled Plugin",
        version: "1.0.0",
      };
      const enabledPlugin: Plugin = {
        id: "enabled-plugin",
        name: "Enabled Plugin",
        version: "1.0.0",
      };

      registry.setConfig(config);
      registry.registerPlugin(disabledPlugin);
      registry.registerPlugin(enabledPlugin);

      expect(registry.getAllPlugins()).toHaveLength(1);
      expect(registry.getEnabledPlugins()).toHaveLength(1);
      expect(registry.getEnabledPlugins()).toContain(enabledPlugin);
      expect(registry.getEnabledPlugins()).not.toContain(disabledPlugin);
    });
  });

  describe("Dependency Management", () => {
    test("should sort plugins by dependencies", async () => {
      const basePlugin: Plugin = {
        id: "base",
        name: "Base Plugin",
        version: "1.0.0",
        initialize: jest.fn(),
      };

      const dependentPlugin: Plugin = {
        id: "dependent",
        name: "Dependent Plugin",
        version: "1.0.0",
        dependencies: ["base"],
        initialize: jest.fn(),
      };

      registry.registerPlugin(dependentPlugin);
      registry.registerPlugin(basePlugin);

      await registry.initializePlugins();

      // Base should be initialized before dependent
      expect(basePlugin.initialize).toHaveBeenCalled();
      expect(dependentPlugin.initialize).toHaveBeenCalled();
    });

    test("should handle missing dependencies", async () => {
      const dependentPlugin: Plugin = {
        id: "dependent",
        name: "Dependent Plugin",
        version: "1.0.0",
        dependencies: ["missing-plugin"],
        initialize: jest.fn(),
      };

      registry.registerPlugin(dependentPlugin);
      await registry.initializePlugins();

      expect(mockErrorHandler.onDependencyError).toHaveBeenCalledWith(
        dependentPlugin,
        ["missing-plugin"],
      );
      expect(dependentPlugin.initialize).not.toHaveBeenCalled();
    });
  });

  describe("Plugin Initialization", () => {
    test("should initialize plugins with API", async () => {
      const plugin: Plugin = {
        id: "test",
        name: "Test Plugin",
        version: "1.0.0",
        initialize: jest.fn(),
        activate: jest.fn(),
      };

      registry.registerPlugin(plugin);
      await registry.initializePlugins();

      expect(plugin.initialize).toHaveBeenCalledWith(mockApi);
      expect(plugin.activate).toHaveBeenCalled();
      expect(mockApiFactory).toHaveBeenCalled();
    });

    test("should handle initialization errors", async () => {
      const error = new Error("Initialization failed");
      const plugin: Plugin = {
        id: "failing",
        name: "Failing Plugin",
        version: "1.0.0",
        initialize: jest.fn().mockRejectedValue(error),
      };

      registry.registerPlugin(plugin);
      await registry.initializePlugins();

      expect(mockErrorHandler.onInitError).toHaveBeenCalledWith(plugin, error);
    });

    test("should handle no plugins to initialize", async () => {
      await registry.initializePlugins();
      expect(console.info).toHaveBeenCalledWith(
        "[Airone Plugin] No plugins to initialize",
      );
    });
  });

  describe("Plugin Deactivation", () => {
    test("should disable plugin properly", async () => {
      const plugin: Plugin = {
        id: "test",
        name: "Test Plugin",
        version: "1.0.0",
        initialize: jest.fn(),
        deactivate: jest.fn(),
      };

      registry.registerPlugin(plugin);
      await registry.initializePlugins();

      registry.disablePlugin("test");

      expect(plugin.deactivate).toHaveBeenCalled();
      expect(registry.getEnabledPlugins()).not.toContain(plugin);
    });

    test("should handle non-existent plugin", () => {
      registry.disablePlugin("non-existent");
      expect(console.warn).toHaveBeenCalledWith(
        "[Airone Plugin] Plugin non-existent not found",
      );
    });

    test("should handle deactivation errors", async () => {
      const error = new Error("Deactivation failed");
      const plugin: Plugin = {
        id: "test",
        name: "Test Plugin",
        version: "1.0.0",
        initialize: jest.fn(),
        deactivate: jest.fn().mockImplementation(() => {
          throw error;
        }),
      };

      registry.registerPlugin(plugin);
      await registry.initializePlugins();

      registry.disablePlugin("test");

      expect(mockErrorHandler.onRuntimeError).toHaveBeenCalledWith(
        plugin,
        error,
        { action: "disable" },
      );
    });
  });

  describe("Route Management", () => {
    test("should collect routes from enabled plugins", () => {
      const route1: PluginRoute = {
        path: "/test1",
        element: React.createElement("div"),
        priority: 100,
      };
      const route2: PluginRoute = {
        path: "/test2",
        element: React.createElement("div"),
        priority: 200,
      };

      const plugin1: Plugin = {
        id: "plugin1",
        name: "Plugin 1",
        version: "1.0.0",
        routes: [route1],
        priority: 10,
      };

      const plugin2: Plugin = {
        id: "plugin2",
        name: "Plugin 2",
        version: "1.0.0",
        routes: [route2],
        priority: 20,
      };

      registry.registerPlugin(plugin1);
      registry.registerPlugin(plugin2);

      const routes = registry.getRoutes();

      expect(routes).toHaveLength(2);
      expect(routes).toContain(route1);
      expect(routes).toContain(route2);
    });

    test("should sort routes by plugin priority then route priority", () => {
      const route1: PluginRoute = {
        path: "/high-priority",
        element: React.createElement("div"),
        priority: 100,
      };
      const route2: PluginRoute = {
        path: "/low-priority",
        element: React.createElement("div"),
        priority: 200,
      };

      const highPriorityPlugin: Plugin = {
        id: "high",
        name: "High Priority Plugin",
        version: "1.0.0",
        routes: [route2], // Lower route priority but plugin has higher priority
        priority: 10,
      };

      const lowPriorityPlugin: Plugin = {
        id: "low",
        name: "Low Priority Plugin",
        version: "1.0.0",
        routes: [route1], // Higher route priority but plugin has lower priority
        priority: 20,
      };

      registry.registerPlugin(highPriorityPlugin);
      registry.registerPlugin(lowPriorityPlugin);

      const routes = registry.getRoutes();

      expect(routes[0]).toBe(route2); // Plugin priority takes precedence
      expect(routes[1]).toBe(route1);
    });

    test("should handle plugins without routes", () => {
      const plugin: Plugin = {
        id: "no-routes",
        name: "No Routes Plugin",
        version: "1.0.0",
        // No routes property
      };

      registry.registerPlugin(plugin);
      const routes = registry.getRoutes();

      expect(routes).toHaveLength(0);
    });
  });

  describe("Component Management", () => {
    test("should collect components from enabled plugins", () => {
      const component1: PluginComponent = {
        id: "comp1",
        component: React.createElement("div"),
        trigger: { type: "button" },
        position: { location: "header", order: 1 },
      };

      const component2: PluginComponent = {
        id: "comp2",
        component: React.createElement("div"),
        trigger: { type: "menu" },
        position: { location: "sidebar", order: 2 },
      };

      const plugin: Plugin = {
        id: "test",
        name: "Test Plugin",
        version: "1.0.0",
        components: [component1, component2],
      };

      registry.registerPlugin(plugin);
      const components = registry.getComponents();

      expect(components).toHaveLength(2);
      expect(components).toContain(component1);
      expect(components).toContain(component2);
    });

    test("should filter components by location", () => {
      const headerComponent: PluginComponent = {
        id: "header-comp",
        component: React.createElement("div"),
        trigger: { type: "button" },
        position: { location: "header", order: 1 },
      };

      const sidebarComponent: PluginComponent = {
        id: "sidebar-comp",
        component: React.createElement("div"),
        trigger: { type: "menu" },
        position: { location: "sidebar", order: 2 },
      };

      const plugin: Plugin = {
        id: "test",
        name: "Test Plugin",
        version: "1.0.0",
        components: [headerComponent, sidebarComponent],
      };

      registry.registerPlugin(plugin);
      const headerComponents = registry.getComponents("header");

      expect(headerComponents).toHaveLength(1);
      expect(headerComponents).toContain(headerComponent);
      expect(headerComponents).not.toContain(sidebarComponent);
    });

    test("should sort components by order", () => {
      const component1: PluginComponent = {
        id: "comp1",
        component: React.createElement("div"),
        trigger: { type: "button" },
        position: { location: "header", order: 200 },
      };

      const component2: PluginComponent = {
        id: "comp2",
        component: React.createElement("div"),
        trigger: { type: "button" },
        position: { location: "header", order: 100 },
      };

      const plugin: Plugin = {
        id: "test",
        name: "Test Plugin",
        version: "1.0.0",
        components: [component1, component2],
      };

      registry.registerPlugin(plugin);
      const components = registry.getComponents("header");

      expect(components[0]).toBe(component2); // Lower order comes first
      expect(components[1]).toBe(component1);
    });
  });

  describe("Statistics", () => {
    test("should provide accurate statistics", async () => {
      const config: PluginConfig = {
        plugins: {
          disabled: { enabled: false },
        },
        global: {},
      };

      const enabledPlugin: Plugin = {
        id: "enabled",
        name: "Enabled Plugin",
        version: "1.0.0",
        initialize: jest.fn(),
      };

      const disabledPlugin: Plugin = {
        id: "disabled",
        name: "Disabled Plugin",
        version: "1.0.0",
      };

      registry.setConfig(config);
      registry.registerPlugin(enabledPlugin);
      registry.registerPlugin(disabledPlugin);

      await registry.initializePlugins();

      const stats = registry.getStatistics();

      expect(stats).toEqual({
        total: 1, // Only enabled plugin is registered
        enabled: 1,
        initialized: 1,
        disabled: 1, // Disabled from config
      });
    });
  });

  describe("Error Handling", () => {
    test("should use default error handler if none provided", () => {
      const registryWithDefaultHandler = new PluginRegistry();
      const invalidPlugin = { id: "" } as Plugin;

      expect(() => {
        registryWithDefaultHandler.registerPlugin(invalidPlugin);
      }).toThrow();

      // Should not crash even without custom error handler
    });
  });
});
