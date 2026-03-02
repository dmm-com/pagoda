/**
 * @jest-environment jsdom
 */

import { act, renderHook, waitFor } from "@testing-library/react";
import { FC, ReactNode, Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { SWRConfig } from "swr";

import { usePagodaSWR } from "./usePagodaSWR";

const wrapper: FC<{ children: ReactNode }> = ({ children }) => (
  <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
    {children}
  </SWRConfig>
);

describe("usePagodaSWR", () => {
  describe("successful data fetching", () => {
    test("should return data after fetch resolves", async () => {
      const expected = { id: 1, name: "test" };
      const fetcher = () => Promise.resolve(expected);

      const { result } = renderHook(() => usePagodaSWR(["test", 1], fetcher), {
        wrapper,
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
        expect(result.current.data).toEqual(expected);
      });
    });

    test("should return array data", async () => {
      const expected = [1, 2, 3];
      const fetcher = () => Promise.resolve(expected);

      const { result } = renderHook(
        () => usePagodaSWR(["test-array"], fetcher),
        { wrapper },
      );

      await waitFor(() => {
        expect(result.current.data).toEqual(expected);
      });
    });
  });

  describe("conditional fetching", () => {
    test("should not fetch when key is null", async () => {
      const fetcher = jest.fn(() => Promise.resolve("data"));

      const { result } = renderHook(() => usePagodaSWR(null, fetcher), {
        wrapper,
      });

      // Wait a tick to ensure no fetch happens
      await new Promise((r) => setTimeout(r, 50));

      expect(fetcher).not.toHaveBeenCalled();
      expect(result.current.data).toBeUndefined();
      expect(result.current.isLoading).toBe(false);
    });

    test("should not fetch when fetcher is null", async () => {
      const { result } = renderHook(
        () => usePagodaSWR(["test-null-fetcher"], null),
        { wrapper },
      );

      await new Promise((r) => setTimeout(r, 50));

      expect(result.current.data).toBeUndefined();
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe("error handling", () => {
    test("should throw non-ResponseError errors", async () => {
      const testError = new Error("Test error");
      const fetcher = () => Promise.reject(testError);
      let caughtError: Error | null = null;

      const errorWrapper: FC<{ children: ReactNode }> = ({ children }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <ErrorBoundary
            fallbackRender={({ error }) => {
              caughtError = error;
              return <div>error</div>;
            }}
          >
            {children}
          </ErrorBoundary>
        </SWRConfig>
      );

      renderHook(() => usePagodaSWR(["test-error"], fetcher), {
        wrapper: errorWrapper,
      });

      await waitFor(() => {
        expect(caughtError).toBe(testError);
      });
    });

    test("should throw ForbiddenError for 403 ResponseError", async () => {
      const responseError = Object.assign(new Error("ResponseError"), {
        name: "ResponseError",
        response: new Response(null, { status: 403 }),
      });
      const fetcher = () => Promise.reject(responseError);
      let caughtError: Error | null = null;

      const errorWrapper: FC<{ children: ReactNode }> = ({ children }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <ErrorBoundary
            fallbackRender={({ error }) => {
              caughtError = error;
              return <div>error</div>;
            }}
          >
            {children}
          </ErrorBoundary>
        </SWRConfig>
      );

      renderHook(() => usePagodaSWR(["test-403"], fetcher), {
        wrapper: errorWrapper,
      });

      await waitFor(() => {
        expect(caughtError).not.toBeNull();
        expect(caughtError!.name).toBe("ForbiddenError");
      });
    });

    test("should throw NotFoundError for 404 ResponseError", async () => {
      const responseError = Object.assign(new Error("ResponseError"), {
        name: "ResponseError",
        response: new Response(null, { status: 404 }),
      });
      const fetcher = () => Promise.reject(responseError);
      let caughtError: Error | null = null;

      const errorWrapper: FC<{ children: ReactNode }> = ({ children }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <ErrorBoundary
            fallbackRender={({ error }) => {
              caughtError = error;
              return <div>error</div>;
            }}
          >
            {children}
          </ErrorBoundary>
        </SWRConfig>
      );

      renderHook(() => usePagodaSWR(["test-404"], fetcher), {
        wrapper: errorWrapper,
      });

      await waitFor(() => {
        expect(caughtError).not.toBeNull();
        expect(caughtError!.name).toBe("NotFoundError");
      });
    });
  });

  describe("revalidation", () => {
    test("should revalidate data with mutate", async () => {
      let callCount = 0;
      const fetcher = () => {
        callCount++;
        return Promise.resolve(callCount);
      };

      const { result } = renderHook(
        () => usePagodaSWR(["test-mutate"], fetcher),
        { wrapper },
      );

      await waitFor(() => {
        expect(result.current.data).toBe(1);
      });

      await result.current.mutate();

      await waitFor(() => {
        expect(result.current.data).toBe(2);
      });
    });
  });
});

describe("usePagodaSWR with suspense: true", () => {
  describe("successful data fetching", () => {
    test("should return data (data is always T, never undefined)", async () => {
      const expected = { id: 1, name: "test-suspense" };
      const fetcher = () => Promise.resolve(expected);

      const suspenseWrapper: FC<{ children: ReactNode }> = ({ children }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <Suspense fallback={<div>loading</div>}>{children}</Suspense>
        </SWRConfig>
      );

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let hookResult: any;
      await act(async () => {
        hookResult = renderHook(
          () => usePagodaSWR(["test-suspense-1"], fetcher, { suspense: true }),
          { wrapper: suspenseWrapper },
        );
      });

      expect(hookResult.result.current.data).toEqual(expected);
    });

    test("should return array data", async () => {
      const expected = [10, 20, 30];
      const fetcher = () => Promise.resolve(expected);

      const suspenseWrapper: FC<{ children: ReactNode }> = ({ children }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <Suspense fallback={<div>loading</div>}>{children}</Suspense>
        </SWRConfig>
      );

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let hookResult: any;
      await act(async () => {
        hookResult = renderHook(
          () =>
            usePagodaSWR(["test-suspense-array"], fetcher, { suspense: true }),
          { wrapper: suspenseWrapper },
        );
      });

      expect(hookResult.result.current.data).toEqual(expected);
    });
  });

  describe("error handling", () => {
    test("should throw ForbiddenError for 403 ResponseError via ErrorBoundary", async () => {
      const responseError = Object.assign(new Error("ResponseError"), {
        name: "ResponseError",
        response: new Response(null, { status: 403 }),
      });
      const fetcher = () => Promise.reject(responseError);
      let caughtError: Error | null = null;

      const errorSuspenseWrapper: FC<{ children: ReactNode }> = ({
        children,
      }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <ErrorBoundary
            fallbackRender={({ error }) => {
              caughtError = error;
              return <div>error</div>;
            }}
          >
            <Suspense fallback={<div>loading</div>}>{children}</Suspense>
          </ErrorBoundary>
        </SWRConfig>
      );

      await act(async () => {
        renderHook(
          () =>
            usePagodaSWR(["test-suspense-403"], fetcher, { suspense: true }),
          {
            wrapper: errorSuspenseWrapper,
          },
        );
      });

      expect(caughtError).not.toBeNull();
      expect(caughtError!.name).toBe("ForbiddenError");
    });

    test("should throw NotFoundError for 404 ResponseError via ErrorBoundary", async () => {
      const responseError = Object.assign(new Error("ResponseError"), {
        name: "ResponseError",
        response: new Response(null, { status: 404 }),
      });
      const fetcher = () => Promise.reject(responseError);
      let caughtError: Error | null = null;

      const errorSuspenseWrapper: FC<{ children: ReactNode }> = ({
        children,
      }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <ErrorBoundary
            fallbackRender={({ error }) => {
              caughtError = error;
              return <div>error</div>;
            }}
          >
            <Suspense fallback={<div>loading</div>}>{children}</Suspense>
          </ErrorBoundary>
        </SWRConfig>
      );

      await act(async () => {
        renderHook(
          () =>
            usePagodaSWR(["test-suspense-404"], fetcher, { suspense: true }),
          {
            wrapper: errorSuspenseWrapper,
          },
        );
      });

      expect(caughtError).not.toBeNull();
      expect(caughtError!.name).toBe("NotFoundError");
    });

    test("should throw non-ResponseError errors via ErrorBoundary", async () => {
      const testError = new Error("Suspense test error");
      const fetcher = () => Promise.reject(testError);
      let caughtError: Error | null = null;

      const errorSuspenseWrapper: FC<{ children: ReactNode }> = ({
        children,
      }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <ErrorBoundary
            fallbackRender={({ error }) => {
              caughtError = error;
              return <div>error</div>;
            }}
          >
            <Suspense fallback={<div>loading</div>}>{children}</Suspense>
          </ErrorBoundary>
        </SWRConfig>
      );

      await act(async () => {
        renderHook(
          () =>
            usePagodaSWR(["test-suspense-error"], fetcher, { suspense: true }),
          { wrapper: errorSuspenseWrapper },
        );
      });

      expect(caughtError).toBe(testError);
    });
  });

  describe("revalidation", () => {
    test("should revalidate data with mutate", async () => {
      let callCount = 0;
      const fetcher = () => {
        callCount++;
        return Promise.resolve(callCount);
      };

      const suspenseWrapper: FC<{ children: ReactNode }> = ({ children }) => (
        <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
          <Suspense fallback={<div>loading</div>}>{children}</Suspense>
        </SWRConfig>
      );

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let hookResult: any;
      await act(async () => {
        hookResult = renderHook(
          () =>
            usePagodaSWR(["test-suspense-mutate"], fetcher, { suspense: true }),
          { wrapper: suspenseWrapper },
        );
      });

      expect(hookResult.result.current.data).toBe(1);

      await act(async () => {
        await hookResult.result.current.mutate();
      });

      expect(hookResult.result.current.data).toBe(2);
    });
  });
});
