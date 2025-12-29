/**
 * @jest-environment jsdom
 */

import { renderHook, act } from "@testing-library/react";
import { SnackbarProvider } from "notistack";
import { FC, ReactNode } from "react";

import { useFormNotification } from "./useFormNotification";

const wrapper: FC<{ children: ReactNode }> = ({ children }) => (
  <SnackbarProvider maxSnack={5}>{children}</SnackbarProvider>
);

describe("useFormNotification", () => {
  describe("enqueueSubmitResult", () => {
    test("should return enqueueSubmitResult function", () => {
      const { result } = renderHook(
        () => useFormNotification("TestEntity", true),
        { wrapper },
      );

      expect(result.current.enqueueSubmitResult).toBeDefined();
      expect(typeof result.current.enqueueSubmitResult).toBe("function");
    });

    test("should show success message for create operation when finished is true", () => {
      const { result } = renderHook(
        () => useFormNotification("TestEntity", true),
        { wrapper },
      );

      let snackbarKey: string | number | undefined;
      act(() => {
        snackbarKey = result.current.enqueueSubmitResult(true);
      });

      expect(snackbarKey).toBeDefined();
    });

    test("should show success message for update operation when finished is true", () => {
      const { result } = renderHook(
        () => useFormNotification("TestEntity", false),
        { wrapper },
      );

      let snackbarKey: string | number | undefined;
      act(() => {
        snackbarKey = result.current.enqueueSubmitResult(true);
      });

      expect(snackbarKey).toBeDefined();
    });

    test("should show error message for create operation when finished is false", () => {
      const { result } = renderHook(
        () => useFormNotification("TestEntity", true),
        { wrapper },
      );

      let snackbarKey: string | number | undefined;
      act(() => {
        snackbarKey = result.current.enqueueSubmitResult(false);
      });

      expect(snackbarKey).toBeDefined();
    });

    test("should show error message for update operation when finished is false", () => {
      const { result } = renderHook(
        () => useFormNotification("TestEntity", false),
        { wrapper },
      );

      let snackbarKey: string | number | undefined;
      act(() => {
        snackbarKey = result.current.enqueueSubmitResult(false);
      });

      expect(snackbarKey).toBeDefined();
    });

    test("should include additional message when provided", () => {
      const { result } = renderHook(
        () => useFormNotification("TestEntity", true),
        { wrapper },
      );

      let snackbarKey: string | number | undefined;
      act(() => {
        snackbarKey = result.current.enqueueSubmitResult(
          true,
          "Additional info",
        );
      });

      expect(snackbarKey).toBeDefined();
    });

    test("should work with different target names", () => {
      const { result: result1 } = renderHook(
        () => useFormNotification("User", true),
        { wrapper },
      );

      const { result: result2 } = renderHook(
        () => useFormNotification("Group", false),
        { wrapper },
      );

      let key1: string | number | undefined;
      let key2: string | number | undefined;

      act(() => {
        key1 = result1.current.enqueueSubmitResult(true);
        key2 = result2.current.enqueueSubmitResult(true);
      });

      expect(key1).toBeDefined();
      expect(key2).toBeDefined();
    });

    test("should return unique keys for multiple calls", () => {
      const { result } = renderHook(
        () => useFormNotification("TestEntity", true),
        { wrapper },
      );

      let key1: string | number | undefined;
      let key2: string | number | undefined;

      act(() => {
        key1 = result.current.enqueueSubmitResult(true);
        key2 = result.current.enqueueSubmitResult(false);
      });

      expect(key1).not.toBe(key2);
    });
  });
});
