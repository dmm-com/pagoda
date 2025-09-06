import React from "react";

import { PluginDefinition } from "./types";
import {
  createPlugin,
  createPluginRoute,
  createPluginComponent,
} from "./utils";

describe("Plugin Utilities", () => {
  describe("createPlugin", () => {
    test("should create a plugin with required properties", () => {
      const config: PluginDefinition = {
        id: "test-plugin",
        name: "Test Plugin",
        version: "1.0.0",
      };

      const plugin = createPlugin(config);

      expect(plugin.id).toBe("test-plugin");
      expect(plugin.name).toBe("Test Plugin");
      expect(plugin.version).toBe("1.0.0");
      expect(plugin.components).toEqual([]); // Default empty array
    });

    test("should create a plugin with optional properties", () => {
      const config: PluginDefinition = {
        id: "advanced-plugin",
        name: "Advanced Plugin",
        version: "2.0.0",
        description: "An advanced plugin for testing",
        dependencies: ["base-plugin"],
        priority: 10,
      };

      const plugin = createPlugin(config);

      expect(plugin.id).toBe("advanced-plugin");
      expect(plugin.name).toBe("Advanced Plugin");
      expect(plugin.version).toBe("2.0.0");
      expect(plugin.description).toBe("An advanced plugin for testing");
      expect(plugin.dependencies).toEqual(["base-plugin"]);
      expect(plugin.priority).toBe(10);
      expect(plugin.components).toEqual([]);
    });

    test("should create a plugin with lifecycle hooks", () => {
      const initializeHook = jest.fn();
      const activateHook = jest.fn();
      const deactivateHook = jest.fn();

      const config: PluginDefinition = {
        id: "lifecycle-plugin",
        name: "Lifecycle Plugin",
        version: "1.0.0",
        initialize: initializeHook,
        activate: activateHook,
        deactivate: deactivateHook,
      };

      const plugin = createPlugin(config);

      expect(plugin.initialize).toBe(initializeHook);
      expect(plugin.activate).toBe(activateHook);
      expect(plugin.deactivate).toBe(deactivateHook);
    });

    test("should create a plugin with routes and config", () => {
      const testRoute = {
        path: "/test",
        element: React.createElement("div"),
      };

      const config: PluginDefinition = {
        id: "config-plugin",
        name: "Config Plugin",
        version: "1.0.0",
        routes: [testRoute],
        config: { setting: "value" },
      };

      const plugin = createPlugin(config);

      expect(plugin.routes).toEqual([testRoute]);
      expect(plugin.config).toEqual({ setting: "value" });
    });
  });

  describe("createPluginRoute", () => {
    test("should create a route with required properties", () => {
      const element = React.createElement("div", {}, "Test Route");
      const config = {
        path: "/test",
        element,
      };

      const route = createPluginRoute(config);

      expect(route.path).toBe("/test");
      expect(route.element).toBe(element);
      expect(route.priority).toBe(1000); // Default priority
      expect(route.override).toBe(false); // Default override
      expect(route.layout).toBe("default"); // Default layout
    });

    test("should create a route with custom properties", () => {
      const element = React.createElement("div", {}, "Custom Route");
      const config = {
        path: "/custom",
        element,
        priority: 100,
        override: true,
        layout: "minimal" as const,
      };

      const route = createPluginRoute(config);

      expect(route.path).toBe("/custom");
      expect(route.element).toBe(element);
      expect(route.priority).toBe(100);
      expect(route.override).toBe(true);
      expect(route.layout).toBe("minimal");
    });

    test("should create a route with function element", () => {
      const elementFunction = () =>
        React.createElement("div", {}, "Function Route");
      const config = {
        path: "/function",
        element: elementFunction,
      };

      const route = createPluginRoute(config);

      expect(route.path).toBe("/function");
      expect(route.element).toBe(elementFunction);
    });

    test("should create a route with custom layout", () => {
      const element = React.createElement("div", {}, "Custom Layout Route");
      const config = {
        path: "/custom-layout",
        element,
        layout: "custom" as const,
      };

      const route = createPluginRoute(config);

      expect(route.layout).toBe("custom");
    });

    test("should override default values with provided config", () => {
      const element = React.createElement("div", {}, "Override Route");
      const config = {
        path: "/override",
        element,
        priority: 500,
        override: true,
        layout: "minimal" as const,
      };

      const route = createPluginRoute(config);

      // Should use provided values instead of defaults
      expect(route.priority).toBe(500);
      expect(route.override).toBe(true);
      expect(route.layout).toBe("minimal");
    });
  });

  describe("createPluginComponent", () => {
    test("should create a component with required properties", () => {
      const component = React.createElement("button", {}, "Test Button");
      const trigger = { type: "button" as const };

      const config = {
        id: "test-component",
        component,
        trigger,
      };

      const pluginComponent = createPluginComponent(config);

      expect(pluginComponent.id).toBe("test-component");
      expect(pluginComponent.component).toBe(component);
      expect(pluginComponent.trigger).toBe(trigger);
      expect(pluginComponent.position).toBeUndefined();
    });

    test("should create a component with position", () => {
      const component = React.createElement("div", {}, "Header Component");
      const trigger = { type: "menu" as const };
      const position = { location: "header" as const, order: 1 };

      const config = {
        id: "header-component",
        component,
        trigger,
        position,
      };

      const pluginComponent = createPluginComponent(config);

      expect(pluginComponent.id).toBe("header-component");
      expect(pluginComponent.component).toBe(component);
      expect(pluginComponent.trigger).toBe(trigger);
      expect(pluginComponent.position).toBe(position);
    });

    test("should create a component with function component", () => {
      const componentFunction = () =>
        React.createElement("span", {}, "Function Component");
      const trigger = { type: "hook" as const };

      const config = {
        id: "function-component",
        component: componentFunction,
        trigger,
      };

      const pluginComponent = createPluginComponent(config);

      expect(pluginComponent.id).toBe("function-component");
      expect(pluginComponent.component).toBe(componentFunction);
      expect(pluginComponent.trigger).toBe(trigger);
    });

    test("should create a component with complex trigger", () => {
      const component = React.createElement("div", {}, "Complex Component");
      const trigger = {
        type: "event" as const,
        target: "entity-list",
        condition: (context: unknown) => Boolean(context),
      };

      const config = {
        id: "complex-component",
        component,
        trigger,
      };

      const pluginComponent = createPluginComponent(config);

      expect(pluginComponent.trigger.type).toBe("event");
      expect(pluginComponent.trigger.target).toBe("entity-list");
      expect(typeof pluginComponent.trigger.condition).toBe("function");
      if (pluginComponent.trigger.condition) {
        expect(pluginComponent.trigger.condition(true)).toBe(true);
        expect(pluginComponent.trigger.condition(false)).toBe(false);
      }
    });

    test("should create a component with full position configuration", () => {
      const component = React.createElement("aside", {}, "Sidebar Component");
      const trigger = { type: "button" as const };
      const position = {
        location: "sidebar" as const,
        order: 5,
      };

      const config = {
        id: "sidebar-component",
        component,
        trigger,
        position,
      };

      const pluginComponent = createPluginComponent(config);

      expect(pluginComponent.position?.location).toBe("sidebar");
      expect(pluginComponent.position?.order).toBe(5);
    });
  });

  describe("Type Safety", () => {
    test("should enforce correct types for plugin config", () => {
      // This test ensures TypeScript compilation catches type errors
      const validConfig: PluginDefinition = {
        id: "type-test",
        name: "Type Test Plugin",
        version: "1.0.0",
      };

      const plugin = createPlugin(validConfig);

      expect(plugin.id).toBe("type-test");
      expect(plugin.name).toBe("Type Test Plugin");
      expect(plugin.version).toBe("1.0.0");
    });

    test("should enforce correct types for route config", () => {
      const validElement = React.createElement("div");

      const validConfig = {
        path: "/valid",
        element: validElement,
        priority: 100,
        override: true,
        layout: "default" as const,
      };

      const route = createPluginRoute(validConfig);

      expect(route.path).toBe("/valid");
      expect(route.element).toBe(validElement);
      expect(route.priority).toBe(100);
      expect(route.override).toBe(true);
      expect(route.layout).toBe("default");
    });

    test("should enforce correct types for component config", () => {
      const validComponent = React.createElement("button");
      const validTrigger = { type: "button" as const };
      const validPosition = { location: "header" as const, order: 1 };

      const validConfig = {
        id: "valid-component",
        component: validComponent,
        trigger: validTrigger,
        position: validPosition,
      };

      const component = createPluginComponent(validConfig);

      expect(component.id).toBe("valid-component");
      expect(component.component).toBe(validComponent);
      expect(component.trigger).toBe(validTrigger);
      expect(component.position).toBe(validPosition);
    });
  });
});
