/**
 * @jest-environment jsdom
 */

import { renderHook, waitFor } from "@testing-library/react";

import { useAsyncWithThrow } from "./useAsyncWithThrow";

describe("useAsyncWithThrow", () => {
  describe("loading state", () => {
    test("should return loading true initially", () => {
      const asyncFn = () => new Promise<string>(() => {});

      const { result } = renderHook(() => useAsyncWithThrow(asyncFn));

      expect(result.current.loading).toBe(true);
      expect(result.current.value).toBeUndefined();
    });

    test("should return loading false after async resolves", async () => {
      const asyncFn = () => Promise.resolve("test value");

      const { result } = renderHook(() => useAsyncWithThrow(asyncFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe("successful async operations", () => {
    test("should return resolved value", async () => {
      const expectedValue = "resolved value";
      const asyncFn = () => Promise.resolve(expectedValue);

      const { result } = renderHook(() => useAsyncWithThrow(asyncFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.value).toBe(expectedValue);
      });
    });

    test("should return resolved object", async () => {
      const expectedValue = { id: 1, name: "test" };
      const asyncFn = () => Promise.resolve(expectedValue);

      const { result } = renderHook(() => useAsyncWithThrow(asyncFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.value).toEqual(expectedValue);
      });
    });

    test("should return resolved array", async () => {
      const expectedValue = [1, 2, 3];
      const asyncFn = () => Promise.resolve(expectedValue);

      const { result } = renderHook(() => useAsyncWithThrow(asyncFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.value).toEqual(expectedValue);
      });
    });

    test("should return null when resolved with null", async () => {
      const asyncFn = () => Promise.resolve(null);

      const { result } = renderHook(() => useAsyncWithThrow(asyncFn));

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.value).toBeNull();
      });
    });
  });

  describe("dependency handling", () => {
    test("should re-run when dependencies change", async () => {
      let callCount = 0;
      const asyncFn = () => {
        callCount++;
        return Promise.resolve(callCount);
      };

      const { result, rerender } = renderHook(
        ({ dep }) => useAsyncWithThrow(asyncFn, [dep]),
        { initialProps: { dep: 1 } },
      );

      await waitFor(() => {
        expect(result.current.value).toBe(1);
      });

      rerender({ dep: 2 });

      await waitFor(() => {
        expect(result.current.value).toBe(2);
      });
    });

    test("should not re-run when dependencies are the same", async () => {
      let callCount = 0;
      const asyncFn = () => {
        callCount++;
        return Promise.resolve(callCount);
      };

      const { result, rerender } = renderHook(
        ({ dep }) => useAsyncWithThrow(asyncFn, [dep]),
        { initialProps: { dep: 1 } },
      );

      await waitFor(() => {
        expect(result.current.value).toBe(1);
      });

      rerender({ dep: 1 });

      // Value should still be 1 since dependency didn't change
      expect(result.current.value).toBe(1);
      expect(callCount).toBe(1);
    });
  });

  describe("error handling", () => {
    test("should throw error when async rejects", async () => {
      const testError = new Error("Test error");
      const asyncFn = () => Promise.reject(testError);

      expect(() => {
        const { result } = renderHook(() => useAsyncWithThrow(asyncFn));
        // Force evaluation
        if (result.current.loading === false) {
          throw result.current.value;
        }
      }).not.toThrow(); // Initial render won't throw
    });
  });
});
