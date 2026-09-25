import { renderHook } from "@testing-library/react";
import { FC, ReactNode } from "react";
import { MemoryRouter, Route, Routes } from "react-router";

import { NotFoundError } from "../services/Exceptions";

import { useIdParams } from "./useIdParams";

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

describe("useIdParams", () => {
  test("should convert required params to numbers", () => {
    const { result } = renderHook(
      () => useIdParams({ required: ["entityId", "entryId"] }),
      {
        wrapper: createWrapper(
          "/entities/:entityId/:entryId",
          "/entities/1/23",
        ),
      },
    );

    expect(result.current).toEqual({ entityId: 1, entryId: 23 });
  });

  test("should return undefined for absent optional params", () => {
    const { result } = renderHook(
      () => useIdParams({ required: ["entityId"], optional: ["entryId"] }),
      { wrapper: createWrapper("/entities/:entityId/new", "/entities/1/new") },
    );

    expect(result.current).toEqual({ entityId: 1, entryId: undefined });
  });

  test("should convert present optional params to numbers", () => {
    const { result } = renderHook(
      () => useIdParams({ optional: ["groupId"] }),
      { wrapper: createWrapper("/groups/:groupId", "/groups/5") },
    );

    expect(result.current.groupId).toBe(5);
  });

  test("should throw NotFoundError for a missing required param", () => {
    expect(() =>
      renderHook(() => useIdParams({ required: ["entryId"] }), {
        wrapper: createWrapper("/entities/:entityId", "/entities/1"),
      }),
    ).toThrow(NotFoundError);
  });

  test.each([
    "abc",
    "1.5",
    "-1",
    "1e3",
  ])("should throw NotFoundError for a non-numeric param (%s)", (raw) => {
    expect(() =>
      renderHook(() => useIdParams({ required: ["entityId"] }), {
        wrapper: createWrapper("/entities/:entityId", `/entities/${raw}`),
      }),
    ).toThrow(NotFoundError);
  });
});
