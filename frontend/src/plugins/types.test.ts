import React from "react";

import {
  Plugin,
  PluginRoute,
  PluginComponent,
  PluginAPI,
  PluginConfig,
  PluginErrorHandler,
  PluginError,
  ComponentPosition,
  RouteGuard,
  RouteContext,
  PluginDefinition,
  PluginFactory,
  CustomRoute,
  ExtendedAppBaseProps,
  ModalOptions,
  NotificationType,
} from "./types";

describe("Plugin Types", () => {
  describe("Plugin Interface", () => {
    test("should allow creating a plugin with required properties", () => {
      const plugin: Plugin = {
        id: "test-plugin",
        name: "Test Plugin",
        version: "1.0.0",
      };

      expect(plugin.id).toBe("test-plugin");
      expect(plugin.name).toBe("Test Plugin");
      expect(plugin.version).toBe("1.0.0");
    });

    test("should allow creating a plugin with all properties", () => {
      const plugin: Plugin = {
        id: "full-plugin",
        name: "Full Plugin",
        version: "2.0.0",
        description: "A complete plugin",
        dependencies: ["dep1", "dep2"],
        peerDependencies: ["peer1"],
        initialize: async (api: PluginAPI) => {
          await api.data.get("/test");
        },
        activate: async () => {
          console.log("Activated");
        },
        deactivate: () => {
          console.log("Deactivated");
        },
        routes: [],
        components: [],
        config: { setting: "value" },
        priority: 100,
      };

      expect(plugin.id).toBe("full-plugin");
      expect(plugin.description).toBe("A complete plugin");
      expect(plugin.dependencies).toEqual(["dep1", "dep2"]);
      expect(plugin.peerDependencies).toEqual(["peer1"]);
      expect(typeof plugin.initialize).toBe("function");
      expect(typeof plugin.activate).toBe("function");
      expect(typeof plugin.deactivate).toBe("function");
      expect(plugin.priority).toBe(100);
    });
  });

  describe("PluginRoute Interface", () => {
    test("should allow creating routes with different element types", () => {
      // ReactNode element
      const routeWithElement: PluginRoute = {
        path: "/element",
        element: React.createElement("div", {}, "Element route"),
      };

      // Function element
      const routeWithFunction: PluginRoute = {
        path: "/function",
        element: () => React.createElement("div", {}, "Function route"),
      };

      expect(routeWithElement.path).toBe("/element");
      expect(routeWithFunction.path).toBe("/function");
      expect(typeof routeWithFunction.element).toBe("function");
    });

    test("should allow creating routes with all optional properties", () => {
      const guard: RouteGuard = {
        check: (context: RouteContext) => context.pathname.startsWith("/admin"),
        fallback: React.createElement("div", {}, "Access denied"),
      };

      const route: PluginRoute = {
        path: "/admin/settings",
        element: React.createElement("div", {}, "Settings"),
        priority: 50,
        override: true,
        layout: "minimal",
        guards: [guard],
      };

      expect(route.priority).toBe(50);
      expect(route.override).toBe(true);
      expect(route.layout).toBe("minimal");
      expect(route.guards).toHaveLength(1);
    });
  });

  describe("PluginComponent Interface", () => {
    test("should allow creating components with different trigger types", () => {
      const buttonComponent: PluginComponent = {
        id: "button-comp",
        component: React.createElement("button", {}, "Click me"),
        trigger: { type: "button" },
      };

      const menuComponent: PluginComponent = {
        id: "menu-comp",
        component: React.createElement("div", {}, "Menu item"),
        trigger: { type: "menu", target: "main-menu" },
      };

      const hookComponent: PluginComponent = {
        id: "hook-comp",
        component: React.createElement("div", {}, "Hook component"),
        trigger: {
          type: "hook",
          condition: (context: unknown) => Boolean(context),
        },
      };

      const eventComponent: PluginComponent = {
        id: "event-comp",
        component: React.createElement("div", {}, "Event component"),
        trigger: { type: "event", target: "entity-updated" },
      };

      expect(buttonComponent.trigger.type).toBe("button");
      expect(menuComponent.trigger.type).toBe("menu");
      expect(menuComponent.trigger.target).toBe("main-menu");
      expect(hookComponent.trigger.type).toBe("hook");
      expect(typeof hookComponent.trigger.condition).toBe("function");
      expect(eventComponent.trigger.type).toBe("event");
      expect(eventComponent.trigger.target).toBe("entity-updated");
    });

    test("should allow creating components with position", () => {
      const positions: ComponentPosition[] = [
        { location: "header", order: 1 },
        { location: "sidebar", order: 2 },
        { location: "footer", order: 3 },
        { location: "modal" },
        { location: "inline" },
      ];

      positions.forEach((position, index) => {
        const component: PluginComponent = {
          id: `comp-${index}`,
          component: React.createElement("div"),
          trigger: { type: "button" },
          position,
        };

        expect(component.position).toBe(position);
      });
    });
  });

  describe("PluginAPI Interface", () => {
    test("should define correct structure for PluginAPI", () => {
      // This test ensures the interface structure is correct
      const mockApi: PluginAPI = {
        services: {
          apiClient: {
            get: async <T = unknown>() => ({}) as T,
            post: async <T = unknown>() => ({}) as T,
            put: async <T = unknown>() => ({}) as T,
            delete: async <T = unknown>() => ({}) as T,
          },
          router: {
            navigate: () => {},
            location: {
              pathname: "/",
              search: "",
              hash: "",
              state: null,
            },
          },
          theme: {
            palette: {},
            spacing: (value: number) => `${value}px`,
          },
          i18n: {
            t: (key: string) => key,
            changeLanguage: async () => {},
          },
          notification: {
            success: () => {},
            error: () => {},
            warning: () => {},
            info: () => {},
          },
        },
        ui: {
          registerComponent: () => {},
          unregisterComponent: () => {},
          showModal: () => "modal-id",
          showNotification: () => {},
        },
        routing: {
          registerRoute: () => {},
          unregisterRoute: () => {},
          navigate: () => {},
        },
        data: {
          get: async <T = unknown>() => ({}) as T,
          post: async <T = unknown>() => ({}) as T,
          put: async <T = unknown>() => ({}) as T,
          delete: async <T = unknown>() => ({}) as T,
        },
        config: {
          get: <T>() => undefined as T,
          set: () => {},
        },
      };

      expect(mockApi.services).toBeDefined();
      expect(mockApi.ui).toBeDefined();
      expect(mockApi.routing).toBeDefined();
      expect(mockApi.data).toBeDefined();
      expect(mockApi.config).toBeDefined();
    });
  });

  describe("PluginConfig Interface", () => {
    test("should allow creating plugin configuration", () => {
      const config: PluginConfig = {
        plugins: {
          plugin1: {
            enabled: true,
            version: "1.0.0",
            config: { setting: "value" },
            priority: 100,
          },
          plugin2: {
            enabled: false,
          },
        },
        global: {
          maxPlugins: 10,
          timeout: 5000,
        },
      };

      expect(config.plugins["plugin1"].enabled).toBe(true);
      expect(config.plugins["plugin2"].enabled).toBe(false);
      expect(config.global.maxPlugins).toBe(10);
    });
  });

  describe("Error Handling Types", () => {
    test("should define correct PluginError structure", () => {
      const errors: PluginError[] = [
        {
          pluginId: "test-plugin",
          type: "load",
          message: "Failed to load plugin",
          error: new Error("Load error"),
          context: { stage: "initialization" },
        },
        {
          pluginId: "test-plugin",
          type: "init",
          message: "Failed to initialize plugin",
        },
        {
          pluginId: "test-plugin",
          type: "runtime",
          message: "Runtime error occurred",
        },
        {
          pluginId: "test-plugin",
          type: "dependency",
          message: "Missing dependencies",
        },
        {
          pluginId: "test-plugin",
          type: "permission",
          message: "Permission denied",
        },
      ];

      errors.forEach((error) => {
        expect(error.pluginId).toBe("test-plugin");
        expect(typeof error.message).toBe("string");
        expect([
          "load",
          "init",
          "runtime",
          "dependency",
          "permission",
        ]).toContain(error.type);
      });
    });

    test("should define correct PluginErrorHandler interface", () => {
      const errorHandler: PluginErrorHandler = {
        onLoadError: (plugin: Plugin, error: Error) => {
          console.error(`Load error in ${plugin.id}:`, error);
        },
        onInitError: (plugin: Plugin, error: Error) => {
          console.error(`Init error in ${plugin.id}:`, error);
        },
        onRuntimeError: (plugin: Plugin, error: Error, context: unknown) => {
          console.error(`Runtime error in ${plugin.id}:`, error, context);
        },
        onDependencyError: (plugin: Plugin, missingDeps: string[]) => {
          console.error(`Missing dependencies in ${plugin.id}:`, missingDeps);
        },
        onPermissionError: (plugin: Plugin, action: string) => {
          console.error(`Permission error in ${plugin.id} for action:`, action);
        },
      };

      expect(typeof errorHandler.onLoadError).toBe("function");
      expect(typeof errorHandler.onInitError).toBe("function");
      expect(typeof errorHandler.onRuntimeError).toBe("function");
      expect(typeof errorHandler.onDependencyError).toBe("function");
      expect(typeof errorHandler.onPermissionError).toBe("function");
    });
  });

  describe("Utility Types", () => {
    test("should define notification types correctly", () => {
      const types: NotificationType[] = ["success", "error", "warning", "info"];

      types.forEach((type) => {
        expect(["success", "error", "warning", "info"]).toContain(type);
      });
    });

    test("should define modal options correctly", () => {
      const options: ModalOptions = {
        title: "Test Modal",
        maxWidth: "lg",
        fullWidth: true,
        disableBackdropClick: false,
      };

      expect(options.title).toBe("Test Modal");
      expect(options.maxWidth).toBe("lg");
      expect(options.fullWidth).toBe(true);
      expect(options.disableBackdropClick).toBe(false);
    });
  });

  describe("Route Guard Types", () => {
    test("should define route context correctly", () => {
      const context: RouteContext = {
        params: { id: "123" },
        search: new URLSearchParams("?filter=active"),
        pathname: "/entities/123",
      };

      expect(context.params.id).toBe("123");
      expect(context.search.get("filter")).toBe("active");
      expect(context.pathname).toBe("/entities/123");
    });

    test("should allow synchronous and asynchronous route guards", () => {
      const syncGuard: RouteGuard = {
        check: (context: RouteContext) => context.pathname.startsWith("/admin"),
        fallback: React.createElement("div", {}, "Access denied"),
      };

      const asyncGuard: RouteGuard = {
        check: async (context: RouteContext) => {
          return Promise.resolve(context.params.id === "123");
        },
      };

      expect(typeof syncGuard.check).toBe("function");
      expect(typeof asyncGuard.check).toBe("function");
    });
  });

  describe("Factory and Definition Types", () => {
    test("should define plugin definition correctly", () => {
      const definition: PluginDefinition = {
        id: "factory-plugin",
        name: "Factory Plugin",
        version: "1.0.0",
        description: "Created via factory",
        dependencies: ["base"],
        priority: 50,
      };

      expect(definition.id).toBe("factory-plugin");
      expect(definition.name).toBe("Factory Plugin");
    });

    test("should define plugin factory correctly", () => {
      const factory: PluginFactory = (config?: unknown) => {
        return {
          id: "generated-plugin",
          name: "Generated Plugin",
          version: "1.0.0",
          config: config as Record<string, unknown>,
        };
      };

      const plugin = factory({ setting: "value" });

      expect(plugin.id).toBe("generated-plugin");
      expect(plugin.config).toEqual({ setting: "value" });
    });
  });

  describe("Legacy Compatibility Types", () => {
    test("should support custom route compatibility", () => {
      const customRoute: CustomRoute = {
        path: "/legacy",
        element: React.createElement("div", {}, "Legacy route"),
      };

      expect(customRoute.path).toBe("/legacy");
      expect(React.isValidElement(customRoute.element)).toBe(true);
    });

    test("should support extended app base props", () => {
      const customRoutes: CustomRoute[] = [
        { path: "/route1", element: React.createElement("div") },
        { path: "/route2", element: React.createElement("div") },
      ];

      const plugins: Plugin[] = [
        { id: "plugin1", name: "Plugin 1", version: "1.0.0" },
      ];

      const props: ExtendedAppBaseProps = {
        customRoutes,
        plugins,
      };

      expect(props.customRoutes).toHaveLength(2);
      expect(props.plugins).toHaveLength(1);
    });
  });

  describe("Type Compatibility", () => {
    test("should ensure Plugin extends PluginDefinition", () => {
      const definition: PluginDefinition = {
        id: "test",
        name: "Test",
        version: "1.0.0",
      };

      // Plugin should be compatible with PluginDefinition
      const plugin: Plugin = {
        ...definition,
        components: [], // Additional property required by Plugin
      };

      expect(plugin.id).toBe(definition.id);
      expect(plugin.name).toBe(definition.name);
      expect(plugin.version).toBe(definition.version);
    });
  });
});
