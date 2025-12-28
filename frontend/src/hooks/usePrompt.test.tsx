/**
 * @jest-environment jsdom
 */

import { renderHook } from "@testing-library/react";
import { FC, ReactNode } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";

import { usePrompt } from "./usePrompt";

function createWrapper(
  initialEntries: string[] = ["/page1"],
): FC<{ children: ReactNode }> {
  const Wrapper: FC<{ children: ReactNode }> = ({ children }) => {
    const router = createMemoryRouter(
      [
        {
          path: "*",
          element: children,
        },
      ],
      { initialEntries },
    );
    return <RouterProvider router={router} />;
  };
  Wrapper.displayName = "TestWrapper";
  return Wrapper;
}

describe("usePrompt", () => {
  const originalConfirm = window.confirm;

  beforeEach(() => {
    window.confirm = jest.fn();
  });

  afterEach(() => {
    window.confirm = originalConfirm;
  });

  describe("when condition is false", () => {
    test("should not block navigation", () => {
      const { result } = renderHook(() => usePrompt(false, "Are you sure?"), {
        wrapper: createWrapper(["/page1"]),
      });

      // Hook should render without issues
      expect(result.current).toBeUndefined();
    });

    test("should not show confirm dialog", () => {
      renderHook(() => usePrompt(false, "Are you sure?"), {
        wrapper: createWrapper(["/page1"]),
      });

      expect(window.confirm).not.toHaveBeenCalled();
    });
  });

  describe("when condition is true", () => {
    test("should render without error", () => {
      const { result } = renderHook(
        () => usePrompt(true, "You have unsaved changes. Leave anyway?"),
        { wrapper: createWrapper(["/page1"]) },
      );

      // Hook should render without issues
      expect(result.current).toBeUndefined();
    });

    test("should accept message parameter", () => {
      const message = "Custom warning message";

      const { result } = renderHook(() => usePrompt(true, message), {
        wrapper: createWrapper(["/page1"]),
      });

      expect(result.current).toBeUndefined();
    });
  });

  describe("condition changes", () => {
    test("should handle condition change from false to true", () => {
      const wrapper = createWrapper(["/page1"]);

      const { rerender } = renderHook(
        ({ when }) => usePrompt(when, "Warning"),
        {
          wrapper,
          initialProps: { when: false },
        },
      );

      // Should not throw when changing condition
      expect(() => {
        rerender({ when: true });
      }).not.toThrow();
    });

    test("should handle condition change from true to false", () => {
      const wrapper = createWrapper(["/page1"]);

      const { rerender } = renderHook(
        ({ when }) => usePrompt(when, "Warning"),
        {
          wrapper,
          initialProps: { when: true },
        },
      );

      // Should not throw when changing condition
      expect(() => {
        rerender({ when: false });
      }).not.toThrow();
    });
  });

  describe("message changes", () => {
    test("should handle message change", () => {
      const wrapper = createWrapper(["/page1"]);

      const { rerender } = renderHook(
        ({ message }) => usePrompt(true, message),
        {
          wrapper,
          initialProps: { message: "Initial message" },
        },
      );

      expect(() => {
        rerender({ message: "Updated message" });
      }).not.toThrow();
    });
  });
});
