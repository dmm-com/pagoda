import { ExpandLess, ExpandMore } from "@mui/icons-material";
import { Alert, Box, Button, Collapse, Paper, Typography } from "@mui/material";
import React, { Component, ErrorInfo, ReactNode } from "react";

import { Plugin, PluginError, PluginErrorHandler } from "./types";

interface Props {
  children: ReactNode;
  plugin?: Plugin;
  fallback?: ReactNode;
  onError?: PluginErrorHandler;
  showErrorDetails?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  showDetails: boolean;
}

/**
 * Plugin-specific error boundary component
 * Catches plugin errors and handles them appropriately without breaking the main application
 */
export class PluginErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Notify plugin error handler
    if (this.props.onError && this.props.plugin) {
      const pluginError: PluginError = {
        pluginId: this.props.plugin.id,
        type: "runtime",
        message: error.message,
        error,
        context: errorInfo,
      };

      this.props.onError.onRuntimeError(this.props.plugin, error, errorInfo);
    }

    // Also output details to console
    console.error("[Airone Plugin] Error Boundary caught an error:", {
      plugin: this.props.plugin?.id || "unknown",
      pluginName: this.props.plugin?.name || "Unknown Plugin",
      pluginVersion: this.props.plugin?.version || "Unknown",
      error,
      errorInfo,
    });
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false,
    });
  };

  handleToggleDetails = () => {
    this.setState((prevState) => ({
      showDetails: !prevState.showDetails,
    }));
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error display
      const pluginName = this.props.plugin?.name || "Unknown Plugin";
      const pluginId = this.props.plugin?.id || "unknown";
      const pluginVersion = this.props.plugin?.version || "unknown";

      return (
        <Paper elevation={1} sx={{ p: 2, m: 1, border: "1px solid #ffeb3b" }}>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              プラグインエラー
            </Typography>
            <Typography variant="body2" color="text.secondary">
              プラグイン "{pluginName}" (ID: {pluginId}, Version:{" "}
              {pluginVersion}) でエラーが発生しました。
              メインアプリケーションは正常に動作を続行します。
            </Typography>
          </Alert>

          <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
            <Button variant="outlined" size="small" onClick={this.handleRetry}>
              再試行
            </Button>

            {this.props.showErrorDetails && (
              <Button
                variant="text"
                size="small"
                onClick={this.handleToggleDetails}
                startIcon={
                  this.state.showDetails ? <ExpandLess /> : <ExpandMore />
                }
              >
                エラー詳細
              </Button>
            )}
          </Box>

          <Collapse in={this.state.showDetails}>
            <Paper variant="outlined" sx={{ p: 2, backgroundColor: "#f5f5f5" }}>
              <Typography variant="subtitle2" gutterBottom>
                エラー詳細:
              </Typography>
              <Typography
                variant="body2"
                component="pre"
                sx={{
                  fontSize: "0.75rem",
                  fontFamily: "monospace",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {this.state.error?.message}
                {this.state.error?.stack &&
                  "\n\nStack trace:\n" + this.state.error.stack}
                {this.state.errorInfo?.componentStack &&
                  "\n\nComponent stack:" + this.state.errorInfo.componentStack}
              </Typography>
            </Paper>
          </Collapse>
        </Paper>
      );
    }

    return this.props.children;
  }
}

/**
 * HOC that wraps plugin components with error boundary
 */
function withPluginErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  plugin?: Plugin,
  fallback?: ReactNode,
  onError?: PluginErrorHandler,
) {
  const ComponentWithErrorBoundary: React.FC<P> = (props) => {
    return (
      <PluginErrorBoundary
        plugin={plugin}
        fallback={fallback}
        onError={onError}
        showErrorDetails={process.env.NODE_ENV === "development"}
      >
        <WrappedComponent {...props} />
      </PluginErrorBoundary>
    );
  };

  ComponentWithErrorBoundary.displayName = `withPluginErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;

  return ComponentWithErrorBoundary;
}

/**
 * Error boundary component specifically for plugin routes
 */
interface PluginRouteErrorBoundaryProps {
  children: ReactNode;
  plugin?: Plugin;
  routePath?: string;
  onError?: PluginErrorHandler;
}

const PluginRouteErrorBoundary: React.FC<PluginRouteErrorBoundaryProps> = ({
  children,
  plugin,
  routePath,
  onError,
}) => {
  const fallback = (
    <Box sx={{ p: 4, textAlign: "center" }}>
      <Alert severity="error" sx={{ mb: 2, maxWidth: 600, mx: "auto" }}>
        <Typography variant="h6" gutterBottom>
          ページの読み込みに失敗しました
        </Typography>
        <Typography variant="body2">
          プラグイン "{plugin?.name || "Unknown"}" のルート "{routePath}"
          で問題が発生しました。
          <br />
          プラグインID: {plugin?.id || "unknown"}
          <br />
          バージョン: {plugin?.version || "unknown"}
        </Typography>
      </Alert>
      <Button
        variant="contained"
        onClick={() => window.location.reload()}
        sx={{ mr: 2 }}
      >
        ページを再読み込み
      </Button>
      <Button variant="outlined" onClick={() => window.history.back()}>
        戻る
      </Button>
    </Box>
  );

  return (
    <PluginErrorBoundary
      plugin={plugin}
      fallback={fallback}
      onError={onError}
      showErrorDetails={process.env.NODE_ENV === "development"}
    >
      {children}
    </PluginErrorBoundary>
  );
};
