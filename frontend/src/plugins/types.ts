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
  config?: Record<string, unknown>;
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
  condition?: (context: unknown) => boolean;
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

// Temporary type definitions for services
export interface APIClient {
  get: (url: string, config?: unknown) => Promise<unknown>;
  post: (url: string, data?: unknown, config?: unknown) => Promise<unknown>;
  put: (url: string, data?: unknown, config?: unknown) => Promise<unknown>;
  delete: (url: string, config?: unknown) => Promise<unknown>;
}

export interface Router {
  navigate: (path: string, options?: NavigateOptions) => void;
  location?: {
    pathname: string;
    search: string;
    hash: string;
    state: unknown;
    key?: string;
  };
}

export interface Theme {
  palette: unknown;
  spacing: (value: number) => string;
}

export interface I18n {
  t: (key: string, options?: unknown) => string;
  changeLanguage: (lng: string) => Promise<void>;
}

export interface NotificationService {
  success: (message: string) => void;
  error: (message: string) => void;
  warning: (message: string) => void;
  info: (message: string) => void;
}

export interface PluginServices {
  // Access to API client, router, theme, i18n, notification services
  apiClient: APIClient;
  router: Router;
  theme: Theme;
  i18n: I18n;
  notification: NotificationService;
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
  get<T = unknown>(endpoint: string, params?: unknown): Promise<T>;
  post<T = unknown>(endpoint: string, data?: unknown): Promise<T>;
  put<T = unknown>(endpoint: string, data?: unknown): Promise<T>;
  delete<T = unknown>(endpoint: string): Promise<T>;
}

export interface PluginConfigAPI {
  get<T = unknown>(key: string): T;
  set(key: string, value: unknown): void;
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
      config?: Record<string, unknown>;
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
  context?: unknown;
}

export interface PluginErrorHandler {
  onLoadError(plugin: Plugin, error: Error): void;
  onInitError(plugin: Plugin, error: Error): void;
  onRuntimeError(plugin: Plugin, error: Error, context: unknown): void;
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
  config?: Record<string, unknown>;
}

// Plugin factory function type
export type PluginFactory = (config?: unknown) => Plugin;
