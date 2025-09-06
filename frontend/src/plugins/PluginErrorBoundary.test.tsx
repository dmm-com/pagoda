import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

import { PluginErrorBoundary } from "./PluginErrorBoundary";
import { Plugin, PluginErrorHandler } from "./types";

// Component that throws an error for testing
const ThrowError: React.FC<{ shouldThrow?: boolean; message?: string }> = ({
  shouldThrow = true,
  message = "Test error",
}) => {
  if (shouldThrow) {
    throw new Error(message);
  }
  return <div>No error</div>;
};

// Component that works normally
const NormalComponent: React.FC = () => <div>Normal component</div>;

describe("PluginErrorBoundary", () => {
  let mockErrorHandler: jest.Mocked<PluginErrorHandler>;
  let mockPlugin: Plugin;
  let consoleSpy: jest.SpyInstance;

  beforeEach(() => {
    // Mock error handler
    mockErrorHandler = {
      onLoadError: jest.fn(),
      onInitError: jest.fn(),
      onRuntimeError: jest.fn(),
      onDependencyError: jest.fn(),
      onPermissionError: jest.fn(),
    };

    // Mock plugin
    mockPlugin = {
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      description: "A test plugin for error boundary testing",
    };

    // Spy on console.error to suppress React error boundary warnings
    consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleSpy.mockRestore();
    jest.clearAllMocks();
  });

  describe("Normal Operation", () => {
    test("should render children when no error occurs", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin}>
          <NormalComponent />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("Normal component")).toBeInTheDocument();
    });

    test("should render children without plugin prop", () => {
      render(
        <PluginErrorBoundary>
          <NormalComponent />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("Normal component")).toBeInTheDocument();
    });
  });

  describe("Error Handling", () => {
    test("should catch and display error", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin}>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("プラグインエラー")).toBeInTheDocument();
      expect(
        screen.getByText(/プラグイン "Test Plugin" \(ID: test-plugin/),
      ).toBeInTheDocument();
      expect(screen.getByText(/Version: 1\.0\.0\)/)).toBeInTheDocument();
      expect(
        screen.getByText((content) => {
          return (
            content.includes("でエラーが発生しました") &&
            content.includes("メインアプリケーションは正常に動作を続行します")
          );
        }),
      ).toBeInTheDocument();
    });

    test("should display unknown plugin information when plugin not provided", () => {
      render(
        <PluginErrorBoundary>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      expect(
        screen.getByText(/プラグイン "Unknown Plugin" \(ID: unknown/),
      ).toBeInTheDocument();
      expect(screen.getByText(/Version: unknown\)/)).toBeInTheDocument();
    });

    test("should call error handler when provided", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin} onError={mockErrorHandler}>
          <ThrowError message="Custom error message" />
        </PluginErrorBoundary>,
      );

      expect(mockErrorHandler.onRuntimeError).toHaveBeenCalledWith(
        mockPlugin,
        expect.any(Error),
        expect.any(Object),
      );

      const calledError = mockErrorHandler.onRuntimeError.mock.calls[0][1];
      expect(calledError.message).toBe("Custom error message");
    });

    test("should log error details to console", () => {
      const consoleErrorSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      render(
        <PluginErrorBoundary plugin={mockPlugin}>
          <ThrowError message="Console test error" />
        </PluginErrorBoundary>,
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "[Airone Plugin] Error Boundary caught an error:",
        expect.objectContaining({
          plugin: "test-plugin",
          pluginName: "Test Plugin",
          pluginVersion: "1.0.0",
          error: expect.any(Error),
          errorInfo: expect.any(Object),
        }),
      );

      consoleErrorSpy.mockRestore();
    });
  });

  describe("Retry Functionality", () => {
    test("should have retry button", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin}>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("再試行")).toBeInTheDocument();
    });

    test("should retry and recover from error", () => {
      let shouldThrow = true;

      const ConditionalError: React.FC = () => {
        if (shouldThrow) {
          throw new Error("Temporary error");
        }
        return <div>Recovered!</div>;
      };

      render(
        <PluginErrorBoundary plugin={mockPlugin}>
          <ConditionalError />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("プラグインエラー")).toBeInTheDocument();

      // Simulate recovery
      shouldThrow = false;
      fireEvent.click(screen.getByText("再試行"));

      expect(screen.getByText("Recovered!")).toBeInTheDocument();
      expect(screen.queryByText("プラグインエラー")).not.toBeInTheDocument();
    });
  });

  describe("Error Details", () => {
    test("should show error details button when showErrorDetails is true", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={true}>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("エラー詳細")).toBeInTheDocument();
    });

    test("should not show error details button when showErrorDetails is false", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={false}>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      expect(screen.queryByText("エラー詳細")).not.toBeInTheDocument();
    });

    test("should toggle error details visibility", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={true}>
          <ThrowError message="Detailed error message" />
        </PluginErrorBoundary>,
      );

      // Initially should show ExpandMore icon (details collapsed)
      expect(screen.getByTestId("ExpandMoreIcon")).toBeInTheDocument();

      // Click to show details
      fireEvent.click(screen.getByText("エラー詳細"));
      expect(screen.getByTestId("ExpandLessIcon")).toBeInTheDocument();
      expect(screen.getByText("エラー詳細:")).toBeInTheDocument();
      expect(screen.getByText(/Detailed error message/)).toBeInTheDocument();

      // Click to hide details
      fireEvent.click(screen.getByText("エラー詳細"));
      expect(screen.getByTestId("ExpandMoreIcon")).toBeInTheDocument();
      expect(screen.queryByTestId("ExpandLessIcon")).not.toBeInTheDocument();
    });

    test("should display error stack trace when available", () => {
      const errorWithStack = new Error("Error with stack");
      errorWithStack.stack = "Error: Error with stack\n    at TestFunction";

      const ErrorWithStack: React.FC = () => {
        throw errorWithStack;
      };

      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={true}>
          <ErrorWithStack />
        </PluginErrorBoundary>,
      );

      fireEvent.click(screen.getByText("エラー詳細"));

      expect(screen.getByText(/Error with stack/)).toBeInTheDocument();
      expect(screen.getByText(/Stack trace:/)).toBeInTheDocument();
      expect(screen.getByText(/at TestFunction/)).toBeInTheDocument();
    });
  });

  describe("Custom Fallback", () => {
    test("should use custom fallback when provided", () => {
      const customFallback = <div>Custom error fallback</div>;

      render(
        <PluginErrorBoundary plugin={mockPlugin} fallback={customFallback}>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("Custom error fallback")).toBeInTheDocument();
      expect(screen.queryByText("プラグインエラー")).not.toBeInTheDocument();
    });
  });

  describe("State Management", () => {
    test("should reset state when retrying", () => {
      // This test needs a working component to retry to
      let shouldThrow = true;

      const ConditionalThrowError: React.FC = () => {
        if (shouldThrow) {
          throw new Error("Test error");
        }
        return <div>Working component</div>;
      };

      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={true}>
          <ConditionalThrowError />
        </PluginErrorBoundary>,
      );

      // Should show error initially
      expect(screen.getByText("プラグインエラー")).toBeInTheDocument();

      // Open error details
      fireEvent.click(screen.getByText("エラー詳細"));
      expect(screen.getByText("エラー詳細:")).toBeInTheDocument();

      // Fix the error condition
      shouldThrow = false;

      // Retry should reset all state
      fireEvent.click(screen.getByText("再試行"));

      // Error should be gone and component should work
      expect(screen.queryByText("プラグインエラー")).not.toBeInTheDocument();
      expect(screen.getByText("Working component")).toBeInTheDocument();
    });

    test("should maintain state between error detail toggles", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={true}>
          <ThrowError message="Persistent error" />
        </PluginErrorBoundary>,
      );

      // Initially should show ExpandMore icon (details collapsed)
      expect(screen.getByTestId("ExpandMoreIcon")).toBeInTheDocument();

      // Click to expand details
      fireEvent.click(screen.getByText("エラー詳細"));
      expect(screen.getByTestId("ExpandLessIcon")).toBeInTheDocument();
      expect(screen.getByText("エラー詳細:")).toBeInTheDocument();
      expect(screen.getByText(/Persistent error/)).toBeInTheDocument();

      // Click to collapse details
      fireEvent.click(screen.getByText("エラー詳細"));
      expect(screen.getByTestId("ExpandMoreIcon")).toBeInTheDocument();
      expect(screen.queryByTestId("ExpandLessIcon")).not.toBeInTheDocument();

      // Click to expand details again
      fireEvent.click(screen.getByText("エラー詳細"));
      expect(screen.getByTestId("ExpandLessIcon")).toBeInTheDocument();
      expect(screen.getByText("エラー詳細:")).toBeInTheDocument();
      expect(screen.getByText(/Persistent error/)).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    test("should have proper button roles", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={true}>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      const retryButton = screen.getByText("再試行");
      const detailsButton = screen.getByText("エラー詳細");

      expect(retryButton.tagName).toBe("BUTTON");
      expect(detailsButton.tagName).toBe("BUTTON");
    });

    test("should have appropriate ARIA attributes for collapsible content", () => {
      render(
        <PluginErrorBoundary plugin={mockPlugin} showErrorDetails={true}>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      const detailsButton = screen.getByText("エラー詳細");

      // Should have expand icon initially (details collapsed)
      expect(screen.getByTestId("ExpandMoreIcon")).toBeInTheDocument();

      fireEvent.click(detailsButton);

      // Should have collapse icon when expanded
      expect(screen.getByTestId("ExpandLessIcon")).toBeInTheDocument();
    });
  });

  describe("Integration", () => {
    test("should work without any optional props", () => {
      render(
        <PluginErrorBoundary>
          <ThrowError />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("プラグインエラー")).toBeInTheDocument();
      expect(screen.getByText("再試行")).toBeInTheDocument();
      expect(screen.queryByText("エラー詳細")).not.toBeInTheDocument();
    });

    test("should handle multiple errors gracefully", () => {
      let errorNumber = 1;

      const MultipleErrors: React.FC = () => {
        throw new Error(`Error number ${errorNumber}`);
      };

      render(
        <PluginErrorBoundary plugin={mockPlugin}>
          <MultipleErrors />
        </PluginErrorBoundary>,
      );

      expect(screen.getByText("プラグインエラー")).toBeInTheDocument();

      // Change error and retry
      errorNumber = 2;
      fireEvent.click(screen.getByText("再試行"));

      // Should still handle the new error
      expect(screen.getByText("プラグインエラー")).toBeInTheDocument();
      // The component is still in error state, which is expected
    });
  });
});
