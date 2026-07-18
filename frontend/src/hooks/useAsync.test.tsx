/**
 * @jest-environment jsdom
 */

import { act, renderHook, waitFor } from "@testing-library/react";

import { useAsync } from "./useAsync";

const deferred = <T,>() => {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
};

describe("useAsync", () => {
  test("resolves a value and clears loading", async () => {
    const request = deferred<string>();
    const { result } = renderHook(() => useAsync(() => request.promise));

    expect(result.current).toEqual({ loading: true });
    act(() => request.resolve("done"));

    await waitFor(() =>
      expect(result.current).toEqual({ value: "done", loading: false }),
    );
  });

  test("exposes request errors", async () => {
    const request = deferred<string>();
    const { result } = renderHook(() => useAsync(() => request.promise));
    const error = new Error("request failed");

    act(() => request.reject(error));

    await waitFor(() =>
      expect(result.current).toEqual({ error, loading: false }),
    );
  });

  test("ignores a stale request after dependencies change", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    const requests = [first, second];
    const { result, rerender } = renderHook(
      ({ requestIndex }) =>
        useAsync(() => requests[requestIndex].promise, [requestIndex]),
      { initialProps: { requestIndex: 0 } },
    );

    rerender({ requestIndex: 1 });
    act(() => second.resolve("new"));
    await waitFor(() => expect(result.current.value).toBe("new"));

    act(() => first.resolve("stale"));
    await act(async () => Promise.resolve());
    expect(result.current).toEqual({ value: "new", loading: false });
  });

  test("ignores a rejected request after unmount", async () => {
    const request = deferred<string>();
    const { unmount } = renderHook(() => useAsync(() => request.promise));

    unmount();
    act(() => request.reject(new Error("late failure")));
    await act(async () => Promise.resolve());
  });
});
