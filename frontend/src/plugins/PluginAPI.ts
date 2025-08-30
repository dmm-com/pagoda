import { ReactNode } from "react";
import { NavigateOptions } from "react-router";

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
} from "./types";

// Plugin configuration management
class PluginConfigManager implements PluginConfigAPI {
  private storage: Record<string, any> = {};
  private pluginId: string;

  constructor(pluginId: string) {
    this.pluginId = pluginId;
  }

  get(key: string): any {
    const fullKey = `plugin_${this.pluginId}_${key}`;
    // First try to get from localStorage, if not available get from memory
    try {
      const stored = localStorage.getItem(fullKey);
      return stored ? JSON.parse(stored) : this.storage[key];
    } catch {
      return this.storage[key];
    }
  }

  set(key: string, value: any): void {
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
      enqueueSnackbar?: (message: string, options?: any) => any;
      theme?: any;
      i18n?: any;
      apiClient?: any;
    } = {},
  ) {
    this.pluginId = pluginId;
    this.config = new PluginConfigManager(pluginId);

    // Setup services
    this.services = {
      apiClient: coreServices.apiClient,
      router: { navigate: coreServices.navigate },
      theme: coreServices.theme,
      i18n: coreServices.i18n,
      notification: { enqueueSnackbar: coreServices.enqueueSnackbar },
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
          console.log(
            `[Airone Plugin] ${this.pluginId}: Notification (${type}):`,
            message,
          );
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
      get: async (endpoint: string, params?: any) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.get === "function"
        ) {
          return coreServices.apiClient.get(endpoint, params);
        }
        console.warn(
          `[Airone Plugin] ${this.pluginId}: API client not available for GET ${endpoint}`,
        );
        throw new Error("API client not available");
      },

      post: async (endpoint: string, data?: any) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.post === "function"
        ) {
          return coreServices.apiClient.post(endpoint, data);
        }
        console.warn(
          `[Airone Plugin] ${this.pluginId}: API client not available for POST ${endpoint}`,
        );
        throw new Error("API client not available");
      },

      put: async (endpoint: string, data?: any) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.put === "function"
        ) {
          return coreServices.apiClient.put(endpoint, data);
        }
        console.warn(
          `[Airone Plugin] ${this.pluginId}: API client not available for PUT ${endpoint}`,
        );
        throw new Error("API client not available");
      },

      delete: async (endpoint: string) => {
        if (
          coreServices.apiClient &&
          typeof coreServices.apiClient.delete === "function"
        ) {
          return coreServices.apiClient.delete(endpoint);
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
    enqueueSnackbar?: (message: string, options?: any) => any;
    theme?: any;
    i18n?: any;
    apiClient?: any;
  } = {},
): PluginAPI {
  return new PluginAPI(pluginId, coreServices);
}

// Factory for React environment use (future extension)
function createReactPluginAPI(
  pluginId: string,
  hooks: {
    useNavigate?: () => (to: string, options?: NavigateOptions) => void;
    useSnackbar?: () => {
      enqueueSnackbar: (message: string, options?: any) => any;
    };
    useTheme?: () => any;
    useTranslation?: () => any;
  } = {},
): PluginAPI {
  const coreServices: any = {};

  try {
    if (hooks.useNavigate) {
      coreServices.navigate = hooks.useNavigate();
    }
    if (hooks.useSnackbar) {
      const snackbar = hooks.useSnackbar();
      coreServices.enqueueSnackbar = snackbar.enqueueSnackbar;
    }
    if (hooks.useTheme) {
      coreServices.theme = hooks.useTheme();
    }
    if (hooks.useTranslation) {
      const translation = hooks.useTranslation();
      coreServices.i18n = translation.i18n;
    }
  } catch (error) {
    console.warn(
      `[Airone Plugin] ${pluginId}: React hooks not available, creating limited PluginAPI`,
    );
  }

  return new PluginAPI(pluginId, coreServices);
}
