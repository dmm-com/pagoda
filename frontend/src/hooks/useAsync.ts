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
  }, deps ?? []);
  return state;
}
