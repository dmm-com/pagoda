import { useEffect, useState } from "react";

interface AsyncState<T> {
  value?: T;
  loading: boolean;
  error?: Error;
}

export function useAsync<T>(
  fn: () => Promise<T>,
  deps?: unknown[],
): AsyncState<T> {
  const [state, setState] = useState<AsyncState<T>>({ loading: true });
  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true }));
    fn()
      .then((value) => {
        if (!cancelled) setState({ value, loading: false });
      })
      .catch((error) => {
        if (!cancelled) setState({ error, loading: false });
      });
    return () => {
      cancelled = true;
    };
    // This generic hook intentionally delegates dependency management to the
    // caller (same API as react-use's useAsync), so `fn` is deliberately
    // excluded and the deps array cannot be a static literal.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps ?? []);
  return state;
}
