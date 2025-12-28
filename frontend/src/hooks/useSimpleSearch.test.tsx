/**
 * @jest-environment jsdom
 */

import { renderHook, act } from "@testing-library/react";
import { FC, ReactNode } from "react";
import { MemoryRouter } from "react-router";

import { useSimpleSearch } from "./useSimpleSearch";

function createWrapper(
  initialEntries: string[] = ["/"],
): FC<{ children: ReactNode }> {
  const Wrapper: FC<{ children: ReactNode }> = ({ children }) => (
    <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
  );
  Wrapper.displayName = "TestWrapper";
  return Wrapper;
}

describe("useSimpleSearch", () => {
  describe("query value", () => {
    test("should return undefined when no query in URL", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper(["/"]),
      });

      const [query] = result.current;
      expect(query).toBeUndefined();
    });

    test("should return query value from URL", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper(["/?simple_search_query=test"]),
      });

      const [query] = result.current;
      expect(query).toBe("test");
    });

    test("should return query value when other params present", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper([
          "/?page=1&simple_search_query=search&other=value",
        ]),
      });

      const [query] = result.current;
      expect(query).toBe("search");
    });

    test("should handle empty query string", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper(["/?simple_search_query="]),
      });

      const [query] = result.current;
      expect(query).toBe("");
    });
  });

  describe("submitQuery function", () => {
    test("should return submitQuery function", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper(["/"]),
      });

      const [, submitQuery] = result.current;
      expect(typeof submitQuery).toBe("function");
    });

    test("should update query when submitQuery is called", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper(["/"]),
      });

      act(() => {
        const [, submitQuery] = result.current;
        submitQuery("newquery");
      });

      const [query] = result.current;
      expect(query).toBe("newquery");
    });

    test("should clear query when submitQuery is called with undefined", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper(["/?simple_search_query=test"]),
      });

      act(() => {
        const [, submitQuery] = result.current;
        submitQuery(undefined);
      });

      const [query] = result.current;
      expect(query).toBeUndefined();
    });

    test("should handle query with special characters", () => {
      const { result } = renderHook(() => useSimpleSearch(), {
        wrapper: createWrapper(["/"]),
      });

      act(() => {
        const [, submitQuery] = result.current;
        submitQuery("test query");
      });

      const [query] = result.current;
      expect(query).toBe("test query");
    });
  });
});
