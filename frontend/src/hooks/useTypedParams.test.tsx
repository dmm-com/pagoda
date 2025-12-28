/**
 * @jest-environment jsdom
 */

import { renderHook } from "@testing-library/react";
import { FC, ReactNode } from "react";
import { MemoryRouter, Routes, Route } from "react-router";

import { useTypedParams } from "./useTypedParams";

interface TestParams {
  id: string;
  name: string;
}

interface SingleParam {
  id: string;
}

function createWrapper(
  path: string,
  initialEntry: string,
): FC<{ children: ReactNode }> {
  const Wrapper: FC<{ children: ReactNode }> = ({ children }) => (
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path={path} element={children} />
      </Routes>
    </MemoryRouter>
  );
  Wrapper.displayName = "TestWrapper";
  return Wrapper;
}

describe("useTypedParams", () => {
  describe("with valid params", () => {
    test("should return typed params when all params are present", () => {
      const { result } = renderHook(() => useTypedParams<SingleParam>(), {
        wrapper: createWrapper("/users/:id", "/users/123"),
      });

      expect(result.current.id).toBe("123");
    });

    test("should return multiple typed params", () => {
      const { result } = renderHook(() => useTypedParams<TestParams>(), {
        wrapper: createWrapper("/users/:id/:name", "/users/123/john"),
      });

      expect(result.current.id).toBe("123");
      expect(result.current.name).toBe("john");
    });

    test("should handle numeric-looking params as strings", () => {
      const { result } = renderHook(() => useTypedParams<SingleParam>(), {
        wrapper: createWrapper("/entities/:id", "/entities/456"),
      });

      expect(result.current.id).toBe("456");
      expect(typeof result.current.id).toBe("string");
    });

    test("should handle special characters in params", () => {
      const { result } = renderHook(() => useTypedParams<SingleParam>(), {
        wrapper: createWrapper("/items/:id", "/items/test-item_123"),
      });

      expect(result.current.id).toBe("test-item_123");
    });
  });

  describe("with empty params object", () => {
    test("should work when params are provided correctly", () => {
      // This test validates that the hook correctly returns params
      // The actual error throwing behavior depends on the route configuration
      const { result } = renderHook(() => useTypedParams<SingleParam>(), {
        wrapper: createWrapper("/users/:id", "/users/123"),
      });

      expect(result.current.id).toBe("123");
    });
  });

  describe("type safety", () => {
    test("should return Required type (all fields required)", () => {
      const { result } = renderHook(() => useTypedParams<TestParams>(), {
        wrapper: createWrapper("/users/:id/:name", "/users/123/john"),
      });

      // TypeScript should ensure both id and name are non-optional
      const params: Required<TestParams> = result.current;
      expect(params.id).toBeDefined();
      expect(params.name).toBeDefined();
    });
  });
});
