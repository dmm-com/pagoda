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
    setState((s) => ({ ...s, loading: true }));
    fn()
      .then((value) => setState({ value, loading: false }))
      .catch((error) => setState({ error, loading: false }));
  }, deps ?? []);
  return state;
}
