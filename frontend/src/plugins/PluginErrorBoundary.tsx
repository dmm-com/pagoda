import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import { Alert, Box, Button, Collapse, Paper, Typography } from "@mui/material";
import React, { Component, ErrorInfo, ReactNode } from "react";

import { Plugin, PluginErrorHandler } from "./types";

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
              プラグイン &quot;{pluginName}&quot; (ID: {pluginId}, Version:{" "}
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
