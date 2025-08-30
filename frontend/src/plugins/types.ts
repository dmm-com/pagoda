import { ReactNode } from "react";
import { NavigateOptions } from "react-router";

// Basic plugin interface
export interface Plugin {
  // Basic information
  id: string;
  name: string;
  version: string;
  description?: string;

  // Dependencies
  dependencies?: string[];
  peerDependencies?: string[];

  // Lifecycle hooks
  initialize?(api: PluginAPI): Promise<void> | void;
  activate?(): Promise<void> | void;
  deactivate?(): Promise<void> | void;

  // Feature extensions
  routes?: PluginRoute[];
  components?: PluginComponent[];

  // Configuration
  config?: Record<string, any>;
  priority?: number; // For route priority control (smaller values = higher priority)
}

// Plugin route interface
export interface PluginRoute {
  path: string;
  element: ReactNode | (() => ReactNode);
  priority?: number;
  override?: boolean; // 既存ルートをオーバーライドするか
  layout?: "default" | "minimal" | "custom";
  guards?: RouteGuard[]; // 認証・認可チェック
}

// Route guard
export interface RouteGuard {
  check(context: RouteContext): boolean | Promise<boolean>;
  fallback?: ReactNode;
}

export interface RouteContext {
  params: Record<string, string>;
  search: URLSearchParams;
  pathname: string;
}

// Plugin UI component
export interface PluginComponent {
  id: string;
  component: ReactNode | (() => ReactNode);
  trigger: ComponentTrigger;
  position?: ComponentPosition;
}

export interface ComponentTrigger {
  type: "button" | "menu" | "hook" | "event";
  target?: string; // 配置対象の識別子
  condition?: (context: any) => boolean;
}

export interface ComponentPosition {
  location: "header" | "sidebar" | "footer" | "modal" | "inline";
  order?: number;
}

// Plugin API (core service access)
export interface PluginAPI {
  // Core service access
  services: PluginServices;

  // UI extensions
  ui: PluginUIAPI;

  // Routing
  routing: PluginRoutingAPI;

  // Data access
  data: PluginDataAPI;

  // Configuration management
  config: PluginConfigAPI;
}

export interface PluginServices {
  // Access to API client, router, theme, i18n, notification services
  apiClient: any; // Actual types will be specified later
  router: any;
  theme: any;
  i18n: any;
  notification: any;
}

export interface PluginUIAPI {
  registerComponent(component: PluginComponent): void;
  unregisterComponent(id: string): void;
  showModal(content: ReactNode, options?: ModalOptions): void;
  showNotification(message: string, type?: NotificationType): void;
}

export interface ModalOptions {
  title?: string;
  maxWidth?: "xs" | "sm" | "md" | "lg" | "xl";
  fullWidth?: boolean;
  disableBackdropClick?: boolean;
}

export type NotificationType = "success" | "error" | "warning" | "info";

export interface PluginRoutingAPI {
  registerRoute(route: PluginRoute): void;
  unregisterRoute(path: string): void;
  navigate(path: string, options?: NavigateOptions): void;
}

export interface PluginDataAPI {
  get(endpoint: string, params?: any): Promise<any>;
  post(endpoint: string, data?: any): Promise<any>;
  put(endpoint: string, data?: any): Promise<any>;
  delete(endpoint: string): Promise<any>;
}

export interface PluginConfigAPI {
  get(key: string): any;
  set(key: string, value: any): void;
}

// Plugin registry interface
export interface PluginRegistry {
  // Plugin registration
  registerPlugin(plugin: Plugin): void;

  // Plugin retrieval
  getPlugin(id: string): Plugin | undefined;

  // Get all plugins
  getAllPlugins(): Plugin[];

  // Get enabled plugins
  getEnabledPlugins(): Plugin[];

  // Plugin initialization
  initializePlugins(): Promise<void>;

  // Plugin deactivation
  disablePlugin(id: string): void;

  // Get plugin routes (ordered by priority)
  getRoutes(): PluginRoute[];

  // Get plugin components
  getComponents(location?: ComponentPosition["location"]): PluginComponent[];
}

// Plugin configuration
export interface PluginConfig {
  plugins: {
    [pluginId: string]: {
      enabled: boolean;
      version?: string;
      config?: Record<string, any>;
      priority?: number;
    };
  };

  // Global configuration
  global: {
    maxPlugins?: number;
    timeout?: number;
  };
}

// Error handling
export interface PluginError {
  pluginId: string;
  type: "load" | "init" | "runtime" | "dependency" | "permission";
  message: string;
  error?: Error;
  context?: any;
}

export interface PluginErrorHandler {
  onLoadError(plugin: Plugin, error: Error): void;
  onInitError(plugin: Plugin, error: Error): void;
  onRuntimeError(plugin: Plugin, error: Error, context: any): void;
  onDependencyError(plugin: Plugin, missingDeps: string[]): void;
  onPermissionError(plugin: Plugin, action: string): void;
}

// Types for compatibility with existing customRoutes
export interface CustomRoute {
  path: string;
  element: ReactNode;
}

// Extended props
export interface ExtendedAppBaseProps {
  customRoutes?: CustomRoute[];
  plugins?: Plugin[];
}

// Helper type for plugin developers
export interface PluginDefinition {
  id: string;
  name: string;
  version: string;
  description?: string;
  dependencies?: string[];
  priority?: number;
  initialize?: (api: PluginAPI) => Promise<void> | void;
  activate?: () => Promise<void> | void;
  deactivate?: () => Promise<void> | void;
  routes?: PluginRoute[];
  config?: Record<string, any>;
}

// Plugin factory function type
export type PluginFactory = (config?: any) => Plugin;
