import { ReactNode } from "react";
import { NavigateOptions, Location as RouterLocation } from "react-router";

import {
  PluginAPI as IPluginAPI,
  PluginServices,
  PluginUIAPI,
  PluginRoutingAPI,
  PluginDataAPI,
  PluginConfigAPI,
  PluginRoute,
  PluginComponent,
  ModalOptions,
  NotificationType,
  APIClient,
  Theme,
  I18n,
} from "./types";

// Plugin configuration management
class PluginConfigManager implements PluginConfigAPI {
  private storage: Record<string, unknown> = {};
  private pluginId: string;

  constructor(pluginId: string) {
    this.pluginId = pluginId;
  }

  get<T = unknown>(key: string): T {
    const fullKey = `plugin_${this.pluginId}_${key}`;
    // First try to get from localStorage, if not available get from memory
    try {
      const stored = localStorage.getItem(fullKey);
      return (stored ? JSON.parse(stored) : this.storage[key]) as T;
    } catch {
      return this.storage[key] as T;
    }
  }

  set(key: string, value: unknown): void {
    const fullKey = `plugin_${this.pluginId}_${key}`;
    this.storage[key] = value;
    // Also persist to localStorage
    try {
      localStorage.setItem(fullKey, JSON.stringify(value));
    } catch {
      // Memory only if localStorage is not available
      console.warn(
        `[Airone Plugin] Cannot save config to localStorage for plugin ${this.pluginId}`,
      );
    }
  }
}

// Modal management (for future extension)
class ModalManager {
  private static modals: Set<string> = new Set();

  static showModal(content: ReactNode, options?: ModalOptions): string {
    const modalId = `modal_${Date.now()}_${Math.random()}`;
    this.modals.add(modalId);

    // TODO: Actual modal display logic (future implementation)
    console.log("[Airone Plugin] Modal would be shown:", {
      modalId,
      content,
      options,
    });

    return modalId;
  }

  static closeModal(modalId: string): void {
    this.modals.delete(modalId);
    console.log("[Airone Plugin] Modal would be closed:", modalId);
  }
}

// PluginAPI implementation
export class PluginAPI implements IPluginAPI {
  public services: PluginServices;
  public ui: PluginUIAPI;
  public routing: PluginRoutingAPI;
  public data: PluginDataAPI;
  public config: PluginConfigAPI;

  private pluginId: string;
  private registeredComponents: Map<string, PluginComponent> = new Map();
  private registeredRoutes: Map<string, PluginRoute> = new Map();

  constructor(
    pluginId: string,
    coreServices: {
      navigate?: (to: string, options?: NavigateOptions) => void;
      enqueueSnackbar?: (
        message: string,
        options?: Record<string, unknown>,
      ) => unknown;
      theme?: Record<string, unknown>;
      i18n?: Record<string, unknown>;
      apiClient?: Record<string, unknown>;
    } = {},
  ) {
    this.pluginId = pluginId;
    this.config = new PluginConfigManager(pluginId);

    // Setup services
    this.services = {
      apiClient: (coreServices.apiClient as unknown as APIClient) || {
        get: async () => {
          throw new Error("API client not configured");
        },
        post: async () => {
          throw new Error("API client not configured");
        },
        put: async () => {
          throw new Error("API client not configured");
        },
        delete: async () => {
          throw new Error("API client not configured");
        },
      },
      router: {
        navigate:
          coreServices.navigate ||
          (() => {
            console.warn("Navigation not configured");
          }),
        location: {
          pathname: "/",
          search: "",
          hash: "",
          state: null,
          key: "default",
        } as RouterLocation,
      },
      theme: (coreServices.theme as unknown as Theme) || {
        palette: {},
        spacing: (value: number) => `${value * 8}px`,
      },
      i18n: (coreServices.i18n as unknown as I18n) || {
        t: (key: string) => key,
        changeLanguage: async () => {},
      },
      notification: {
        success: (message: string) => {
          console.log("Success:", message);
        },
        error: (message: string) => {
          console.error("Error:", message);
        },
        warning: (message: string) => {
          console.warn("Warning:", message);
        },
        info: (message: string) => {
          console.info("Info:", message);
        },
      },
    };

    // Setup UI API
    this.ui = {
      registerComponent: (component: PluginComponent) => {
        this.registeredComponents.set(component.id, component);
        console.info(
          `[Airone Plugin] ${this.pluginId}: Component ${component.id} registered`,
        );
      },

      unregisterComponent: (id: string) => {
        this.registeredComponents.delete(id);
        console.info(
          `[Airone Plugin] ${this.pluginId}: Component ${id} unregistered`,
        );
      },

      showModal: (content: ReactNode, options?: ModalOptions) => {
        return ModalManager.showModal(content, options);
      },

      showNotification: (message: string, type: NotificationType = "info") => {
        if (coreServices.enqueueSnackbar) {
          return coreServices.enqueueSnackbar(message, { variant: type });
        } else {
          // Use the notification service directly
          switch (type) {
            case "success":
              this.services.notification.success(message);
              break;
            case "error":
              this.services.notification.error(message);
              break;
            case "warning":
              this.services.notification.warning(message);
              break;
            case "info":
            default:
              this.services.notification.info(message);
              break;
          }
        }
      },
    };

    // Setup routing API
    this.routing = {
      registerRoute: (route: PluginRoute) => {
        this.registeredRoutes.set(route.path, route);
        console.info(
          `[Airone Plugin] ${this.pluginId}: Route ${route.path} registered`,
        );
      },

      unregisterRoute: (path: string) => {
        this.registeredRoutes.delete(path);
        console.info(
          `[Airone Plugin] ${this.pluginId}: Route ${path} unregistered`,
        );
      },

      navigate: (path: string, options?: NavigateOptions) => {
        if (coreServices.navigate) {
          coreServices.navigate(path, options);
        } else {
          console.log(
            `[Airone Plugin] ${this.pluginId}: Navigation to ${path} requested`,
          );
        }
      },
    };

    // Setup data API
    this.data = {
      get: async <T = unknown>(endpoint: string, params?: unknown) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.get === "function"
        ) {
          return coreServices.apiClient.get(endpoint, params) as Promise<T>;
        }
        console.warn(
          `[Airone Plugin] ${this.pluginId}: API client not available for GET ${endpoint}`,
        );
        throw new Error("API client not available");
      },

      post: async <T = unknown>(endpoint: string, data?: unknown) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.post === "function"
        ) {
          return coreServices.apiClient.post(endpoint, data) as Promise<T>;
        }
        console.warn(
          `[Airone Plugin] ${this.pluginId}: API client not available for POST ${endpoint}`,
        );
        throw new Error("API client not available");
      },

      put: async <T = unknown>(endpoint: string, data?: unknown) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.put === "function"
        ) {
          return coreServices.apiClient.put(endpoint, data) as Promise<T>;
        }
        console.warn(
          `[Airone Plugin] ${this.pluginId}: API client not available for PUT ${endpoint}`,
        );
        throw new Error("API client not available");
      },

      delete: async <T = unknown>(endpoint: string) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.delete === "function"
        ) {
          return coreServices.apiClient.delete(endpoint) as Promise<T>;
        }
        console.warn(
          `[Airone Plugin] ${this.pluginId}: API client not available for DELETE ${endpoint}`,
        );
        throw new Error("API client not available");
      },
    };
  }

  // Get registered components (internal use)
  getRegisteredComponents(): PluginComponent[] {
    return Array.from(this.registeredComponents.values());
  }

  // Get registered routes (internal use)
  getRegisteredRoutes(): PluginRoute[] {
    return Array.from(this.registeredRoutes.values());
  }
}

// PluginAPI factory function
export function createPluginAPI(
  pluginId: string,
  coreServices: {
    navigate?: (to: string, options?: NavigateOptions) => void;
    enqueueSnackbar?: (
      message: string,
      options?: Record<string, unknown>,
    ) => unknown;
    theme?: Record<string, unknown>;
    i18n?: Record<string, unknown>;
    apiClient?: Record<string, unknown>;
  } = {},
): PluginAPI {
  return new PluginAPI(pluginId, coreServices);
}
