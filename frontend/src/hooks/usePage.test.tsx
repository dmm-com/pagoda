/**
 * @jest-environment jsdom
 */

import { renderHook, act } from "@testing-library/react";
import { FC, ReactNode } from "react";
import { MemoryRouter } from "react-router";

import { usePage } from "./usePage";

function createWrapper(
  initialEntries: string[] = ["/"],
): FC<{ children: ReactNode }> {
  const Wrapper: FC<{ children: ReactNode }> = ({ children }) => (
    <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
  );
  Wrapper.displayName = "TestWrapper";
  return Wrapper;
}

describe("usePage", () => {
  describe("initial state", () => {
    test("should return default page 1 when no page param in URL", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/"]),
      });

      expect(result.current.page).toBe(1);
    });

    test("should return empty query when no query param in URL", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/"]),
      });

      expect(result.current.query).toBe("");
    });

    test("should parse page number from URL", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?page=5"]),
      });

      expect(result.current.page).toBe(5);
    });

    test("should parse query from URL", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?query=test"]),
      });

      expect(result.current.query).toBe("test");
    });

    test("should parse both page and query from URL", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?page=3&query=search"]),
      });

      expect(result.current.page).toBe(3);
      expect(result.current.query).toBe("search");
    });

    test("should return page 1 for invalid page number", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?page=invalid"]),
      });

      expect(result.current.page).toBe(1);
    });

    test("should decode URL-encoded query", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?query=%E3%83%86%E3%82%B9%E3%83%88"]),
      });

      expect(result.current.query).toBe("テスト");
    });
  });

  describe("changePage", () => {
    test("should be a function", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/"]),
      });

      expect(typeof result.current.changePage).toBe("function");
    });

    test("should update page when changePage is called", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/"]),
      });

      act(() => {
        result.current.changePage(5);
      });

      expect(result.current.page).toBe(5);
    });

    test("should preserve existing query when changing page", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?query=test"]),
      });

      act(() => {
        result.current.changePage(2);
      });

      expect(result.current.page).toBe(2);
      expect(result.current.query).toBe("test");
    });
  });

  describe("changeQuery", () => {
    test("should be a function", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/"]),
      });

      expect(typeof result.current.changeQuery).toBe("function");
    });

    test("should update query when changeQuery is called", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/"]),
      });

      act(() => {
        result.current.changeQuery("newquery");
      });

      expect(result.current.query).toBe("newquery");
    });

    test("should reset page to 1 when changing query", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?page=5"]),
      });

      act(() => {
        result.current.changeQuery("search");
      });

      expect(result.current.page).toBe(1);
      expect(result.current.query).toBe("search");
    });

    test("should handle empty query", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/?query=test"]),
      });

      act(() => {
        result.current.changeQuery("");
      });

      expect(result.current.query).toBe("");
    });

    test("should URL-encode query with special characters", () => {
      const { result } = renderHook(() => usePage(), {
        wrapper: createWrapper(["/"]),
      });

      act(() => {
        result.current.changeQuery("テスト");
      });

      expect(result.current.query).toBe("テスト");
    });
  });
});
