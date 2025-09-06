import React from "react";

import { PluginAPI, createPluginAPI } from "./PluginAPI";
import { PluginComponent, PluginRoute } from "./types";

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("PluginAPI", () => {
  let mockCoreServices: {
    navigate?: jest.MockedFunction<(to: string, options?: unknown) => void>;
    enqueueSnackbar?: jest.MockedFunction<
      (message: string, options?: Record<string, unknown>) => unknown
    >;
    theme?: Record<string, unknown>;
    i18n?: Record<string, unknown>;
    apiClient?: {
      get: jest.MockedFunction<(...args: unknown[]) => Promise<unknown>>;
      post: jest.MockedFunction<(...args: unknown[]) => Promise<unknown>>;
      put: jest.MockedFunction<(...args: unknown[]) => Promise<unknown>>;
      delete: jest.MockedFunction<(...args: unknown[]) => Promise<unknown>>;
    };
  };
  let pluginAPI: PluginAPI;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);

    // Mock core services
    mockCoreServices = {
      navigate: jest.fn(),
      enqueueSnackbar: jest.fn(),
      theme: {
        palette: { primary: "#1976d2" },
        spacing: (value: number) => `${value * 8}px`,
      },
      i18n: {
        t: jest.fn((key: string) => key),
        changeLanguage: jest.fn(),
      },
      apiClient: {
        get: jest.fn(),
        post: jest.fn(),
        put: jest.fn(),
        delete: jest.fn(),
      },
    };

    pluginAPI = new PluginAPI("test-plugin", mockCoreServices);

    // Mock console methods
    jest.spyOn(console, "info").mockImplementation(() => {});
    jest.spyOn(console, "warn").mockImplementation(() => {});
    jest.spyOn(console, "log").mockImplementation(() => {});
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe("Constructor and Services", () => {
    test("should initialize with core services", () => {
      expect(pluginAPI.services.router.navigate).toBeDefined();
      expect(pluginAPI.services.theme).toBe(mockCoreServices.theme);
      expect(pluginAPI.services.i18n).toBe(mockCoreServices.i18n);
      expect(pluginAPI.services.apiClient).toBe(mockCoreServices.apiClient);
    });

    test("should initialize with default services when not provided", () => {
      const apiWithoutServices = new PluginAPI("test-plugin");

      expect(apiWithoutServices.services.router.navigate).toBeDefined();
      expect(apiWithoutServices.services.theme.spacing(2)).toBe("16px");
      expect(apiWithoutServices.services.i18n.t("test")).toBe("test");
    });

    test("should initialize API factory", () => {
      const api = createPluginAPI("test-plugin", mockCoreServices);
      expect(api).toBeInstanceOf(PluginAPI);
    });
  });

  describe("Configuration Management", () => {
    test("should store and retrieve configuration", () => {
      const testValue = { setting: "value" };

      pluginAPI.config.set("test-key", testValue);
      const retrieved = pluginAPI.config.get("test-key");

      expect(retrieved).toEqual(testValue);
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "plugin_test-plugin_test-key",
        JSON.stringify(testValue),
      );
    });

    test("should retrieve from localStorage if available", () => {
      const storedValue = { stored: "value" };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(storedValue));

      const retrieved = pluginAPI.config.get("stored-key");

      expect(retrieved).toEqual(storedValue);
      expect(localStorageMock.getItem).toHaveBeenCalledWith(
        "plugin_test-plugin_stored-key",
      );
    });

    test("should handle localStorage errors gracefully", () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error("Storage full");
      });

      pluginAPI.config.set("test-key", "test-value");

      expect(console.warn).toHaveBeenCalledWith(
        "[Airone Plugin] Cannot save config to localStorage for plugin test-plugin",
      );
    });

    test("should handle JSON parsing errors in localStorage", () => {
      localStorageMock.getItem.mockReturnValue("invalid-json");

      // Should fallback to memory storage
      pluginAPI.config.set("test-key", "memory-value");
      const retrieved = pluginAPI.config.get("test-key");

      expect(retrieved).toBe("memory-value");
    });
  });

  describe("UI API", () => {
    test("should register and unregister components", () => {
      const component: PluginComponent = {
        id: "test-component",
        component: React.createElement("div", {}, "Test Component"),
        trigger: { type: "button" },
        position: { location: "header" },
      };

      pluginAPI.ui.registerComponent(component);
      expect(pluginAPI.getRegisteredComponents()).toContain(component);
      expect(console.info).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: Component test-component registered",
      );

      pluginAPI.ui.unregisterComponent("test-component");
      expect(pluginAPI.getRegisteredComponents()).not.toContain(component);
      expect(console.info).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: Component test-component unregistered",
      );
    });

    test("should show modal", () => {
      const content = React.createElement("div", {}, "Modal content");
      const options = { title: "Test Modal", maxWidth: "md" as const };

      const modalId = pluginAPI.ui.showModal(content, options);

      expect(typeof modalId).toBe("string");
      expect(modalId).toMatch(/^modal_\d+_\d/);
    });

    test("should show notifications using snackbar service", () => {
      pluginAPI.ui.showNotification("Success message", "success");

      expect(mockCoreServices.enqueueSnackbar).toHaveBeenCalledWith(
        "Success message",
        { variant: "success" },
      );
    });

    test("should fall back to console notification when snackbar not available", () => {
      const apiWithoutSnackbar = new PluginAPI("test-plugin", {
        ...mockCoreServices,
        enqueueSnackbar: undefined,
      });

      apiWithoutSnackbar.ui.showNotification("Error message", "error");

      expect(console.error).toHaveBeenCalledWith("Error:", "Error message");
    });

    test("should handle different notification types", () => {
      const apiWithoutSnackbar = new PluginAPI("test-plugin", {});

      apiWithoutSnackbar.ui.showNotification("Success", "success");
      apiWithoutSnackbar.ui.showNotification("Warning", "warning");
      apiWithoutSnackbar.ui.showNotification("Info", "info");
      apiWithoutSnackbar.ui.showNotification("Default");

      expect(console.log).toHaveBeenCalledWith("Success:", "Success");
      expect(console.warn).toHaveBeenCalledWith("Warning:", "Warning");
      expect(console.info).toHaveBeenCalledWith("Info:", "Info");
      expect(console.info).toHaveBeenCalledWith("Info:", "Default");
    });
  });

  describe("Routing API", () => {
    test("should register and unregister routes", () => {
      const route: PluginRoute = {
        path: "/test-route",
        element: React.createElement("div", {}, "Test Route"),
        priority: 100,
      };

      pluginAPI.routing.registerRoute(route);
      expect(pluginAPI.getRegisteredRoutes()).toContain(route);
      expect(console.info).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: Route /test-route registered",
      );

      pluginAPI.routing.unregisterRoute("/test-route");
      expect(pluginAPI.getRegisteredRoutes()).not.toContain(route);
      expect(console.info).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: Route /test-route unregistered",
      );
    });

    test("should navigate using core service", () => {
      const path = "/test-path";
      const options = { replace: true };

      pluginAPI.routing.navigate(path, options);

      expect(mockCoreServices.navigate).toHaveBeenCalledWith(path, options);
    });

    test("should handle navigation when core service not available", () => {
      const apiWithoutNavigation = new PluginAPI("test-plugin", {});

      apiWithoutNavigation.routing.navigate("/test");

      expect(console.log).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: Navigation to /test requested",
      );
    });
  });

  describe("Data API", () => {
    test("should make GET requests", async () => {
      const mockResponse = { data: "test" };
      mockCoreServices.apiClient!.get.mockResolvedValue(mockResponse);

      const result = await pluginAPI.data.get("/api/test", { param: "value" });

      expect(mockCoreServices.apiClient!.get).toHaveBeenCalledWith(
        "/api/test",
        {
          param: "value",
        },
      );
      expect(result).toBe(mockResponse);
    });

    test("should make POST requests", async () => {
      const mockResponse = { id: 1 };
      const postData = { name: "test" };
      mockCoreServices.apiClient!.post.mockResolvedValue(mockResponse);

      const result = await pluginAPI.data.post("/api/test", postData);

      expect(mockCoreServices.apiClient!.post).toHaveBeenCalledWith(
        "/api/test",
        postData,
      );
      expect(result).toBe(mockResponse);
    });

    test("should make PUT requests", async () => {
      const mockResponse = { updated: true };
      const putData = { name: "updated" };
      mockCoreServices.apiClient!.put.mockResolvedValue(mockResponse);

      const result = await pluginAPI.data.put("/api/test/1", putData);

      expect(mockCoreServices.apiClient!.put).toHaveBeenCalledWith(
        "/api/test/1",
        putData,
      );
      expect(result).toBe(mockResponse);
    });

    test("should make DELETE requests", async () => {
      const mockResponse = { deleted: true };
      mockCoreServices.apiClient!.delete.mockResolvedValue(mockResponse);

      const result = await pluginAPI.data.delete("/api/test/1");

      expect(mockCoreServices.apiClient!.delete).toHaveBeenCalledWith(
        "/api/test/1",
      );
      expect(result).toBe(mockResponse);
    });

    test("should handle API client not available for GET", async () => {
      const apiWithoutClient = new PluginAPI("test-plugin", {});

      await expect(apiWithoutClient.data.get("/api/test")).rejects.toThrow(
        "API client not available",
      );
      expect(console.warn).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: API client not available for GET /api/test",
      );
    });

    test("should handle API client not available for POST", async () => {
      const apiWithoutClient = new PluginAPI("test-plugin", {});

      await expect(apiWithoutClient.data.post("/api/test")).rejects.toThrow(
        "API client not available",
      );
      expect(console.warn).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: API client not available for POST /api/test",
      );
    });

    test("should handle API client not available for PUT", async () => {
      const apiWithoutClient = new PluginAPI("test-plugin", {});

      await expect(apiWithoutClient.data.put("/api/test")).rejects.toThrow(
        "API client not available",
      );
      expect(console.warn).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: API client not available for PUT /api/test",
      );
    });

    test("should handle API client not available for DELETE", async () => {
      const apiWithoutClient = new PluginAPI("test-plugin", {});

      await expect(apiWithoutClient.data.delete("/api/test")).rejects.toThrow(
        "API client not available",
      );
      expect(console.warn).toHaveBeenCalledWith(
        "[Airone Plugin] test-plugin: API client not available for DELETE /api/test",
      );
    });

    test("should handle invalid API client methods", async () => {
      const apiWithInvalidClient = new PluginAPI("test-plugin", {
        apiClient: { get: "not-a-function" },
      });

      await expect(apiWithInvalidClient.data.get("/api/test")).rejects.toThrow(
        "API client not available",
      );
    });
  });

  describe("Service Integration", () => {
    test("should provide router location information", () => {
      const location = pluginAPI.services.router.location;

      expect(location).toBeDefined();
      expect(location?.pathname).toBe("/");
      expect(location?.search).toBe("");
      expect(location?.hash).toBe("");
      expect(location?.state).toBe(null);
      expect(location?.key).toBe("default");
    });

    test("should provide theme spacing function", () => {
      const spacing = pluginAPI.services.theme.spacing(2);
      expect(spacing).toBe("16px");
    });

    test("should provide i18n translation function", () => {
      const translation = pluginAPI.services.i18n.t("test.key");
      expect(translation).toBe("test.key");
    });

    test("should provide notification services", () => {
      pluginAPI.services.notification.success("Success message");
      pluginAPI.services.notification.error("Error message");
      pluginAPI.services.notification.warning("Warning message");
      pluginAPI.services.notification.info("Info message");

      expect(console.log).toHaveBeenCalledWith("Success:", "Success message");
      expect(console.error).toHaveBeenCalledWith("Error:", "Error message");
      expect(console.warn).toHaveBeenCalledWith("Warning:", "Warning message");
      expect(console.info).toHaveBeenCalledWith("Info:", "Info message");
    });
  });

  describe("Error Handling", () => {
    test("should handle errors gracefully when core services throw", async () => {
      mockCoreServices.apiClient!.get.mockRejectedValue(
        new Error("Network error"),
      );

      await expect(pluginAPI.data.get("/api/test")).rejects.toThrow(
        "Network error",
      );
    });

    test("should handle navigation errors gracefully", () => {
      mockCoreServices.navigate!.mockImplementation(() => {
        throw new Error("Navigation error");
      });

      // Should not crash the plugin
      expect(() => {
        pluginAPI.routing.navigate("/test");
      }).toThrow("Navigation error");
    });
  });
});
